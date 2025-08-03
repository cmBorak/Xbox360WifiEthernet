#!/bin/bash
# Xbox 360 USB Sniffing Setup Script (usbmon only)
# Lightweight alternative that only uses built-in Linux usbmon

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

echo "🕵️  Xbox 360 USB Sniffing Setup (usbmon only)"
echo "============================================="

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   error "This script must be run as root for USB access"
   echo "Usage: sudo $0"
   exit 1
fi

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

log "Setting up USB monitoring with usbmon..."

# Load usbmon module
log "Loading usbmon kernel module..."
if modprobe usbmon; then
    success "usbmon module loaded"
else
    error "Failed to load usbmon module"
    error "Your kernel may not have usbmon support"
    exit 1
fi

# Check usbmon interface
if [ -d "/sys/kernel/debug/usb/usbmon" ]; then
    success "usbmon interface available at /sys/kernel/debug/usb/usbmon"
else
    warning "usbmon debug interface not found"
    warning "Attempting to mount debugfs..."
    
    if mount -t debugfs none /sys/kernel/debug 2>/dev/null; then
        success "debugfs mounted"
        if [ -d "/sys/kernel/debug/usb/usbmon" ]; then
            success "usbmon interface now available"
        else
            error "usbmon interface still not available after mounting debugfs"
            exit 1
        fi
    else
        error "Failed to mount debugfs"
        error "You may need to enable debugfs in your kernel config"
        exit 1
    fi
fi

# Install basic dependencies
log "Installing basic dependencies..."
apt-get update -qq
apt-get install -y python3 python3-pip

# Install Python analysis tools
log "Installing Python analysis tools..."
pip3 install --upgrade pip
pip3 install pyusb

# Create directories
log "Creating capture directories..."
mkdir -p "$SCRIPT_DIR/captures"
mkdir -p "$SCRIPT_DIR/captures/enumeration"
mkdir -p "$SCRIPT_DIR/captures/authentication"
mkdir -p "$SCRIPT_DIR/captures/network_ops"
mkdir -p "$SCRIPT_DIR/captures/analysis"

# Create usbmon capture helper
log "Creating usbmon capture helper..."
cat > "$SCRIPT_DIR/capture_xbox_usbmon.sh" << 'EOF'
#!/bin/bash
# Simple usbmon capture for Xbox 360 wireless adapter

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

# Auto-detect Xbox adapter if not specified
if [ -z "$BUS_NUMBER" ]; then
    echo "🔍 Auto-detecting Xbox 360 wireless adapter..."
    XBOX_LINE=$(lsusb | grep -i "045e:02a8")
    if [ -n "$XBOX_LINE" ]; then
        BUS_NUMBER=$(echo "$XBOX_LINE" | sed 's/Bus \([0-9]*\).*/\1/')
        echo "   Found Xbox adapter on bus $BUS_NUMBER"
    else
        echo "❌ Xbox 360 wireless adapter not found (045e:02a8)"
        echo "   Available devices:"
        lsusb | grep -i microsoft
        echo ""
        echo "   Connect the adapter or specify bus number manually"
        exit 1
    fi
fi

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
OUTPUT_FILE="$CAPTURE_DIR/$SCENARIO/xbox_${SCENARIO}_${TIMESTAMP}_bus${BUS_NUMBER}.log"

echo "🕵️  Starting usbmon capture"
echo "   Scenario: $SCENARIO"
echo "   Bus: $BUS_NUMBER"
echo "   Duration: ${DURATION}s"
echo "   Output: $OUTPUT_FILE"

mkdir -p "$(dirname "$OUTPUT_FILE")"

# Check if usbmon interface exists
USBMON_PATH="/sys/kernel/debug/usb/usbmon/${BUS_NUMBER}u"
if [ ! -r "$USBMON_PATH" ]; then
    echo "❌ Cannot read usbmon interface: $USBMON_PATH"
    echo "   Available interfaces:"
    ls -la /sys/kernel/debug/usb/usbmon/ | grep "^-"
    exit 1
fi

# Start capture
echo "   Starting capture... (Press Ctrl+C to stop early)"
timeout "$DURATION" cat "$USBMON_PATH" > "$OUTPUT_FILE" 2>/dev/null || true

# Check results
if [ -f "$OUTPUT_FILE" ] && [ -s "$OUTPUT_FILE" ]; then
    LINES=$(wc -l < "$OUTPUT_FILE")
    echo "✅ Capture completed: $OUTPUT_FILE"
    echo "   Lines captured: $LINES"
    
    if [ "$LINES" -gt 0 ]; then
        echo "   Run analysis: python3 $(dirname "$0")/src/xbox_capture_analyzer.py '$OUTPUT_FILE' -o '${OUTPUT_FILE%.log}_analysis.md'"
    else
        echo "⚠️  No data captured - check if Xbox adapter is active on bus $BUS_NUMBER"
    fi
else
    echo "❌ Capture failed - no data collected"
    echo "   Check if Xbox adapter is connected and active"
fi
EOF

chmod +x "$SCRIPT_DIR/capture_xbox_usbmon.sh"

# Create simple analysis helper
log "Creating analysis helper..."
cat > "$SCRIPT_DIR/analyze_xbox_capture.sh" << 'EOF'
#!/bin/bash
# Simple Xbox capture analysis

SCRIPT_DIR="$(dirname "$0")"

if [ $# -lt 1 ]; then
    echo "Usage: $0 <capture_file> [output_report]"
    exit 1
fi

CAPTURE_FILE="$1"
OUTPUT_REPORT="$2"

if [ ! -f "$CAPTURE_FILE" ]; then
    echo "❌ Capture file not found: $CAPTURE_FILE"
    exit 1
fi

if [ -z "$OUTPUT_REPORT" ]; then
    OUTPUT_REPORT="${CAPTURE_FILE%.log}_analysis.md"
fi

echo "🔍 Analyzing Xbox capture: $CAPTURE_FILE"

# Check if analyzer exists
ANALYZER="$SCRIPT_DIR/src/xbox_capture_analyzer.py"
if [ ! -f "$ANALYZER" ]; then
    echo "❌ Analyzer not found: $ANALYZER"
    echo "   Basic analysis using grep:"
    echo ""
    
    # Basic analysis with standard tools
    echo "📊 Capture Statistics:"
    echo "   Total lines: $(wc -l < "$CAPTURE_FILE")"
    echo "   Control transfers (ep 00): $(grep " 00 " "$CAPTURE_FILE" | wc -l)"
    echo "   Bulk transfers: $(grep -E " (01|02|81|82) " "$CAPTURE_FILE" | wc -l)"
    
    echo ""
    echo "🔍 Xbox-related transfers:"
    grep -E "(045e|02a8)" "$CAPTURE_FILE" | head -10
    
    echo ""
    echo "For detailed analysis, ensure xbox_capture_analyzer.py exists in src/"
    exit 1
fi

echo "   Using: $ANALYZER"
echo "   Report: $OUTPUT_REPORT"

if python3 "$ANALYZER" "$CAPTURE_FILE" --output "$OUTPUT_REPORT" --verbose; then
    echo "✅ Analysis complete: $OUTPUT_REPORT"
    
    if [ -f "$OUTPUT_REPORT" ]; then
        echo ""
        echo "📋 Quick Summary:"
        grep -E "^- " "$OUTPUT_REPORT" | head -5
    fi
else
    echo "❌ Analysis failed"
    exit 1
fi
EOF

chmod +x "$SCRIPT_DIR/analyze_xbox_capture.sh"

# Create quick test script
log "Creating quick test script..."
cat > "$SCRIPT_DIR/test_xbox_detection.sh" << 'EOF'
#!/bin/bash
# Quick test to detect Xbox 360 wireless adapter

echo "🔍 Xbox 360 Wireless Adapter Detection"
echo "====================================="

echo ""
echo "📋 USB Devices:"
lsusb

echo ""
echo "🎮 Looking for Xbox 360 Wireless Adapter (045e:02a8):"
XBOX_DEVICES=$(lsusb | grep "045e:02a8")
if [ -n "$XBOX_DEVICES" ]; then
    echo "✅ Found Xbox 360 Wireless Adapter:"
    echo "$XBOX_DEVICES"
    
    # Extract bus and device numbers
    BUS=$(echo "$XBOX_DEVICES" | sed 's/Bus \([0-9]*\) Device \([0-9]*\).*/\1/')
    DEVICE=$(echo "$XBOX_DEVICES" | sed 's/Bus \([0-9]*\) Device \([0-9]*\).*/\2/')
    
    echo ""
    echo "📍 Location: Bus $BUS, Device $DEVICE"
    echo "   usbmon interface: /sys/kernel/debug/usb/usbmon/${BUS}u"
    
    # Check if usbmon interface is accessible
    USBMON_PATH="/sys/kernel/debug/usb/usbmon/${BUS}u"
    if [ -r "$USBMON_PATH" ]; then
        echo "✅ usbmon interface accessible"
        echo ""
        echo "🚀 Ready to capture! Run:"
        echo "   sudo $(dirname "$0")/capture_xbox_usbmon.sh authentication 30 $BUS"
    else
        echo "❌ usbmon interface not accessible"
        echo "   Try: sudo modprobe usbmon"
        echo "   Or: sudo mount -t debugfs none /sys/kernel/debug"
    fi
else
    echo "❌ Xbox 360 Wireless Adapter not found"
    echo ""
    echo "🔍 Looking for other Microsoft devices:"
    lsusb | grep -i microsoft
    
    echo ""
    echo "💡 Make sure the Xbox 360 Wireless Adapter is connected"
    echo "   It should show as: ID 045e:02a8 Microsoft Corp."
fi

echo ""
echo "🛠️  usbmon Status:"
if lsmod | grep -q usbmon; then
    echo "✅ usbmon kernel module loaded"
else
    echo "❌ usbmon kernel module not loaded"
    echo "   Run: sudo modprobe usbmon"
fi

if [ -d "/sys/kernel/debug/usb/usbmon" ]; then
    echo "✅ usbmon interface available"
    echo "   Available buses: $(ls /sys/kernel/debug/usb/usbmon/ | grep 'u$' | tr '\n' ' ')"
else
    echo "❌ usbmon interface not available"
    echo "   Run: sudo mount -t debugfs none /sys/kernel/debug"
fi
EOF

chmod +x "$SCRIPT_DIR/test_xbox_detection.sh"

# Final setup
log "Setting up permissions..."
chmod -R 644 /sys/kernel/debug/usb/usbmon/* 2>/dev/null || true

echo ""
success "USB monitoring setup complete!"
echo ""
echo "📁 Captures will be saved to: $SCRIPT_DIR/captures/"
echo ""
echo "🚀 Quick Start:"
echo "   1. Test detection: sudo $SCRIPT_DIR/test_xbox_detection.sh"
echo "   2. Capture protocol: sudo $SCRIPT_DIR/capture_xbox_usbmon.sh authentication 30"
echo "   3. Analyze results: $SCRIPT_DIR/analyze_xbox_capture.sh captures/authentication/xbox_*.log"
echo ""
echo "🔧 Tools created:"
echo "   - $SCRIPT_DIR/capture_xbox_usbmon.sh"
echo "   - $SCRIPT_DIR/analyze_xbox_capture.sh"
echo "   - $SCRIPT_DIR/test_xbox_detection.sh"
echo ""
echo "💡 This setup uses only built-in Linux usbmon (no external dependencies)"
echo "   More reliable than USB-Sniffify but captures at kernel level"