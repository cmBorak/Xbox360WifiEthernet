#!/bin/bash
# Xbox 360 USB Sniffing Setup Script
# Installs and configures USB sniffing tools for Xbox 360 wireless adapter protocol analysis

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}❌ ERROR:${NC} $1" >&2
}

warning() {
    echo -e "${YELLOW}⚠️  WARNING:${NC} $1"
}

success() {
    echo -e "${GREEN}✅${NC} $1"
}

echo "🕵️  Xbox 360 USB Sniffing Setup"
echo "=============================="

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   error "This script must be run as root for USB access"
   echo "Usage: sudo $0"
   exit 1
fi

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}\")\" && pwd)"
TOOLS_DIR="$SCRIPT_DIR/usb_sniffing_tools"

log "Creating tools directory..."
mkdir -p "$TOOLS_DIR"

# Update system packages
log "Updating system packages..."
apt-get update -qq

# Install dependencies
log "Installing USB sniffing dependencies..."
PACKAGES=(
    "git"
    "build-essential"
    "libusb-1.0-0-dev"
    "pkg-config"
    "python3"
    "python3-pip"
    "wireshark"
    "tshark"
)

for package in "${PACKAGES[@]}"; do
    if ! dpkg -l | grep -q "^ii.*$package "; then
        log "Installing $package..."
        if ! apt-get install -y "$package"; then
            error "Failed to install $package"
            exit 1
        fi
    else
        success "$package already installed"
    fi
done

# Install Python dependencies for analysis
log "Installing Python analysis tools..."
pip3 install --upgrade pip
pip3 install pyusb

# Setup USB-Sniffify
log "Setting up USB-Sniffify..."
cd "$TOOLS_DIR"

if [ ! -d "usb-sniffify" ]; then
    log "Cloning USB-Sniffify repository..."
    git clone https://github.com/blegas78/usb-sniffify.git
else
    log "USB-Sniffify already cloned, updating..."
    cd usb-sniffify
    git pull
    cd ..
fi

cd usb-sniffify

log "Building USB-Sniffify..."
if make; then
    success "USB-Sniffify built successfully"
else
    error "Failed to build USB-Sniffify"
    exit 1
fi

# Check for raw_gadget kernel module
log "Checking kernel modules..."
if ! lsmod | grep -q "raw_gadget"; then
    log "Loading raw_gadget module..."
    if modprobe raw_gadget; then
        success "raw_gadget module loaded"
    else
        warning "Failed to load raw_gadget module - may need kernel rebuild"
    fi
else
    success "raw_gadget module already loaded"
fi

# Setup usbmon
log "Setting up usbmon..."
if ! lsmod | grep -q "usbmon"; then
    log "Loading usbmon module..."
    modprobe usbmon
fi

# Create usbmon access directory
if [ ! -d "/sys/kernel/debug/usb/usbmon" ]; then
    warning "usbmon debug interface not available"
    warning "You may need to mount debugfs: mount -t debugfs none /sys/kernel/debug"
else
    success "usbmon interface available"
fi

# Set up permissions for USB sniffing
log "Setting up USB permissions..."
if [ -d "/dev/bus/usb" ]; then
    chmod -R 666 /dev/bus/usb/*/*
    success "USB device permissions configured"
fi

# Create capture directories
log "Creating capture directories..."
mkdir -p "$SCRIPT_DIR/captures"
mkdir -p "$SCRIPT_DIR/captures/enumeration"
mkdir -p "$SCRIPT_DIR/captures/authentication"
mkdir -p "$SCRIPT_DIR/captures/network_ops"
mkdir -p "$SCRIPT_DIR/captures/analysis"

# Create USB sniffing helper scripts
log "Creating helper scripts..."

# USB-Sniffify helper
cat > "$SCRIPT_DIR/capture_with_usbsniffify.sh" << 'EOF'
#!/bin/bash
# USB-Sniffify capture helper for Xbox 360 wireless adapter

TOOLS_DIR="$(dirname "$0")/usb_sniffing_tools"
CAPTURE_DIR="$(dirname "$0")/captures"

if [ $# -lt 2 ]; then
    echo "Usage: $0 <scenario> <duration_seconds>"
    echo "Scenarios: enumeration, authentication, network_ops"
    exit 1
fi

SCENARIO="$1"
DURATION="$2"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
OUTPUT_FILE="$CAPTURE_DIR/$SCENARIO/xbox_${SCENARIO}_${TIMESTAMP}.log"

echo "🕵️  Starting USB-Sniffify capture for $SCENARIO scenario"
echo "   Duration: ${DURATION}s"
echo "   Output: $OUTPUT_FILE"

cd "$TOOLS_DIR/usb-sniffify"
timeout "$DURATION" ./usb-sniffify --mode capture --log "$OUTPUT_FILE" || true

echo "✅ Capture completed: $OUTPUT_FILE"
echo "   Run analysis: python3 ../xbox_capture_analyzer.py '$OUTPUT_FILE' -o '${OUTPUT_FILE%.log}_analysis.md'"
EOF

chmod +x "$SCRIPT_DIR/capture_with_usbsniffify.sh"

# usbmon helper
cat > "$SCRIPT_DIR/capture_with_usbmon.sh" << 'EOF'
#!/bin/bash
# usbmon capture helper for Xbox 360 wireless adapter

CAPTURE_DIR="$(dirname "$0")/captures"

if [ $# -lt 2 ]; then
    echo "Usage: $0 <scenario> <duration_seconds> [bus_number]"
    echo "Scenarios: enumeration, authentication, network_ops"
    echo "If bus_number not provided, will auto-detect Xbox adapter"
    exit 1
fi

SCENARIO="$1"
DURATION="$2"
BUS_NUMBER="$3"

# Auto-detect Xbox adapter bus if not provided
if [ -z "$BUS_NUMBER" ]; then
    echo "🔍 Auto-detecting Xbox 360 wireless adapter..."
    XBOX_LINE=$(lsusb | grep -i "045e:02a8")
    if [ -n "$XBOX_LINE" ]; then
        BUS_NUMBER=$(echo "$XBOX_LINE" | sed 's/Bus \([0-9]*\).*/\1/')
        echo "   Found on bus $BUS_NUMBER"
    else
        echo "❌ Xbox 360 wireless adapter not found"
        echo "   Connect adapter and try again, or specify bus number manually"
        exit 1
    fi
fi

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
OUTPUT_FILE="$CAPTURE_DIR/$SCENARIO/xbox_${SCENARIO}_${TIMESTAMP}_bus${BUS_NUMBER}.log"

echo "🕵️  Starting usbmon capture for $SCENARIO scenario"
echo "   Bus: $BUS_NUMBER"
echo "   Duration: ${DURATION}s"
echo "   Output: $OUTPUT_FILE"

mkdir -p "$(dirname "$OUTPUT_FILE")"

# Start capture in background
timeout "$DURATION" cat "/sys/kernel/debug/usb/usbmon/${BUS_NUMBER}u" > "$OUTPUT_FILE" &
CAPTURE_PID=$!

echo "   Capturing... (PID: $CAPTURE_PID)"
wait $CAPTURE_PID

echo "✅ Capture completed: $OUTPUT_FILE"
echo "   Lines captured: $(wc -l < "$OUTPUT_FILE")"
echo "   Run analysis: python3 ../src/xbox_capture_analyzer.py '$OUTPUT_FILE' -o '${OUTPUT_FILE%.log}_analysis.md'"
EOF

chmod +x "$SCRIPT_DIR/capture_with_usbmon.sh"

# Create analysis helper
cat > "$SCRIPT_DIR/analyze_capture.sh" << 'EOF'
#!/bin/bash
# USB capture analysis helper

SCRIPT_DIR="$(dirname "$0")"

if [ $# -lt 1 ]; then
    echo "Usage: $0 <capture_file> [output_report]"
    exit 1
fi

CAPTURE_FILE="$1"
OUTPUT_REPORT="$2"

if [ -z "$OUTPUT_REPORT" ]; then
    OUTPUT_REPORT="${CAPTURE_FILE%.log}_analysis.md"
fi

echo "🔍 Analyzing capture: $CAPTURE_FILE"
echo "   Report will be saved to: $OUTPUT_REPORT"

python3 "$SCRIPT_DIR/src/xbox_capture_analyzer.py" "$CAPTURE_FILE" --output "$OUTPUT_REPORT" --verbose

if [ -f "$OUTPUT_REPORT" ]; then
    echo "✅ Analysis complete: $OUTPUT_REPORT"
    echo ""
    echo "📊 Summary:"
    grep -E "^- " "$OUTPUT_REPORT" | head -5
else
    echo "❌ Analysis failed"
    exit 1
fi
EOF

chmod +x "$SCRIPT_DIR/analyze_capture.sh"

# Create comprehensive capture script
cat > "$SCRIPT_DIR/capture_xbox_protocol.sh" << 'EOF'
#!/bin/bash
# Comprehensive Xbox 360 protocol capture script

SCRIPT_DIR="$(dirname "$0")"

echo "🎮 Xbox 360 Wireless Adapter Protocol Capture"
echo "============================================="
echo ""
echo "This script will capture the complete Xbox 360 wireless adapter protocol."
echo "Follow the prompts to capture different scenarios."
echo ""

# Check if Xbox adapter is connected
if ! lsusb | grep -q "045e:02a8"; then
    echo "❌ Xbox 360 wireless adapter not detected"
    echo "   Please connect the adapter and try again"
    exit 1
fi

echo "✅ Xbox 360 wireless adapter detected"
echo ""

read -p "Press Enter to start enumeration capture (disconnect/reconnect adapter when prompted)..."

echo "📋 Phase 1: Device Enumeration"
echo "   Disconnect the Xbox adapter now..."
read -p "   Press Enter when adapter is disconnected..."

echo "   Starting enumeration capture..."
"$SCRIPT_DIR/capture_with_usbmon.sh" enumeration 30 &
CAPTURE_PID=$!

sleep 2
echo "   Connect the Xbox adapter now..."
read -p "   Press Enter when adapter is connected and enumerated..."

wait $CAPTURE_PID
echo "   ✅ Enumeration capture complete"
echo ""

read -p "Press Enter to start authentication capture (connect Xbox console when prompted)..."

echo "📋 Phase 2: Xbox Authentication"
echo "   Starting authentication capture..."
"$SCRIPT_DIR/capture_with_usbmon.sh" authentication 60 &
CAPTURE_PID=$!

sleep 2
echo "   Connect Xbox 360 console to adapter now..."
echo "   Wait for Xbox to show network settings..."
read -p "   Press Enter when authentication is complete..."

wait $CAPTURE_PID
echo "   ✅ Authentication capture complete"
echo ""

read -p "Press Enter to start network operations capture..."

echo "📋 Phase 3: Network Operations"
echo "   Starting network operations capture..."
"$SCRIPT_DIR/capture_with_usbmon.sh" network_ops 120 &
CAPTURE_PID=$!

sleep 2
echo "   On Xbox 360:"
echo "   1. Scan for wireless networks"
echo "   2. Connect to a network"
echo "   3. Test network connection"
echo "   4. Disconnect from network"
read -p "   Press Enter when network operations are complete..."

wait $CAPTURE_PID
echo "   ✅ Network operations capture complete"
echo ""

echo "🔍 Analyzing all captures..."
find "$SCRIPT_DIR/captures" -name "*.log" -type f -exec "$SCRIPT_DIR/analyze_capture.sh" {} \;

echo ""
echo "🎯 Protocol capture complete!"
echo "   Check the captures/ directory for all files"
echo "   Each capture has a corresponding _analysis.md report"
echo ""
echo "Next steps:"
echo "1. Review analysis reports for protocol details"
echo "2. Update FunctionFS implementation with captured data"
echo "3. Test emulator with Xbox 360 console"
EOF

chmod +x "$SCRIPT_DIR/capture_xbox_protocol.sh"

# Final status and instructions
echo ""
success "USB sniffing setup complete!"
echo ""
echo "📁 Tools installed in: $TOOLS_DIR"
echo "📁 Captures will be saved to: $SCRIPT_DIR/captures"
echo ""
echo "🚀 Quick Start:"
echo "   1. Connect Xbox 360 wireless adapter to Pi"
echo "   2. Run: sudo $SCRIPT_DIR/capture_xbox_protocol.sh"
echo "   3. Follow prompts to capture complete protocol"
echo "   4. Review analysis reports in captures/ directory"
echo ""
echo "🔧 Manual Tools:"
echo "   - USB-Sniffify: $SCRIPT_DIR/capture_with_usbsniffify.sh"
echo "   - usbmon: $SCRIPT_DIR/capture_with_usbmon.sh"
echo "   - Analysis: $SCRIPT_DIR/analyze_capture.sh"
echo ""
echo "📚 Documentation: docs/USB_SNIFFING_GUIDE.md"

# Add tools to PATH if requested
echo ""
read -p "Add capture tools to system PATH? (y/N): " -r
if [[ $REPLY =~ ^[Yy]$ ]]; then
    cat > /etc/profile.d/xbox-usb-sniffing.sh << EOF
# Xbox 360 USB Sniffing Tools
export PATH="\$PATH:$SCRIPT_DIR"
EOF
    success "Tools added to system PATH"
    echo "   Reload shell or run: source /etc/profile.d/xbox-usb-sniffing.sh"
fi

echo ""
echo "🎮 Ready to capture Xbox 360 wireless adapter protocol!"
echo "   Run the comprehensive capture script to get started."