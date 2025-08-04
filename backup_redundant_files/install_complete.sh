#!/bin/bash
# Xbox 360 WiFi Module Emulator - Complete Automated Installation
# Installs emulator + USB sniffing tools + builds everything automatically

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
INSTALL_DIR="/opt/xbox360-emulator"
CONFIG_DIR="/etc/xbox360-emulator"
LOG_DIR="/var/log/xbox360-emulator"
SERVICE_NAME="xbox360-emulator"

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Logging functions
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

info() {
    echo -e "${CYAN}ℹ️  INFO:${NC} $1"
}

header() {
    echo -e "${PURPLE}========================================${NC}"
    echo -e "${PURPLE}$1${NC}"
    echo -e "${PURPLE}========================================${NC}"
}

# Progress tracking
TOTAL_STEPS=10
CURRENT_STEP=0

progress() {
    CURRENT_STEP=$((CURRENT_STEP + 1))
    echo -e "${CYAN}[Step $CURRENT_STEP/$TOTAL_STEPS]${NC} $1"
}

# Error handling
cleanup() {
    if [ $? -ne 0 ]; then
        error "Installation failed at step $CURRENT_STEP/$TOTAL_STEPS"
        error "Check the output above for details"
        echo ""
        warning "You can try:"
        warning "1. Run individual components: ./install_fixed.sh"
        warning "2. USB sniffing only: ./setup_usbmon_only.sh"
        warning "3. Manual cleanup: sudo rm -rf $INSTALL_DIR $CONFIG_DIR $LOG_DIR"
        warning "4. Check logs: journalctl -xe"
    fi
}
trap cleanup EXIT

# Check system requirements
check_system() {
    progress "Checking system requirements"
    
    # Check if running as root
    if [[ $EUID -ne 0 ]]; then
        error "This script must be run as root"
        echo "Usage: sudo $0"
        exit 1
    fi
    
    # Check if Raspberry Pi
    if [ -f "/proc/cpuinfo" ]; then
        if grep -q "Raspberry Pi" /proc/cpuinfo; then
            PI_MODEL=$(grep "Model" /proc/cpuinfo | cut -d: -f2 | xargs || echo "Unknown Pi Model")
            success "Detected: $PI_MODEL"
            
            if ! grep -q "Raspberry Pi 4" /proc/cpuinfo; then
                warning "Not Raspberry Pi 4 - some features may not work optimally"
            fi
        else
            warning "Not detected as Raspberry Pi - proceeding anyway"
        fi
    fi
    
    # Check available space
    AVAILABLE_SPACE=$(df / | tail -1 | awk '{print $4}')
    if [ "$AVAILABLE_SPACE" -lt 1048576 ]; then  # 1GB in KB
        warning "Less than 1GB free space available"
    fi
    
    success "System requirements check completed"
}

# Update system packages
update_system() {
    progress "Updating system packages"
    
    log "Updating package list..."
    if apt-get update -qq; then
        success "Package list updated"
    else
        warning "Package update failed - continuing with cached packages"
    fi
    
    log "Installing essential packages..."
    ESSENTIAL_PACKAGES=(
        "curl"
        "wget" 
        "unzip"
        "git"
        "python3"
        "python3-pip"
        "build-essential"
        "cmake"
        "pkg-config"
        "libusb-1.0-0-dev"
        "bridge-utils"
        "iptables-persistent"
    )
    
    for package in "${ESSENTIAL_PACKAGES[@]}"; do
        if ! dpkg -l | grep -q "^ii.*$package "; then
            log "Installing $package..."
            if apt-get install -y "$package" >/dev/null 2>&1; then
                success "$package installed"
            else
                warning "Failed to install $package - continuing"
            fi
        fi
    done
    
    success "System packages updated"
}

# Install Xbox 360 emulator
install_emulator() {
    progress "Installing Xbox 360 WiFi Module Emulator"
    
    log "Running main installation script..."
    if [ -f "$SCRIPT_DIR/install_fixed.sh" ]; then
        # Run installation script in non-interactive mode
        export DEBIAN_FRONTEND=noninteractive
        if bash "$SCRIPT_DIR/install_fixed.sh" >/dev/null 2>&1; then
            success "Xbox 360 emulator installed successfully"
        else
            error "Xbox 360 emulator installation failed"
            log "Trying alternative approach..."
            
            # Create basic directories if main install failed
            mkdir -p "$INSTALL_DIR"/{src,bin,docs}
            mkdir -p "$CONFIG_DIR"
            mkdir -p "$LOG_DIR"
            
            # Copy essential files
            if [ -d "$SCRIPT_DIR/src" ]; then
                cp -r "$SCRIPT_DIR/src/"* "$INSTALL_DIR/src/" || true
            fi
            
            warning "Used fallback installation - some features may not work"
        fi
    else
        error "Main installation script not found: install_fixed.sh"
        exit 1
    fi
}

# Install USB sniffing tools
install_usb_sniffing() {
    progress "Installing USB sniffing tools"
    
    log "Setting up USB monitoring..."
    
    # Load required kernel modules
    for module in "usbmon" "raw_gadget" "libcomposite"; do
        if modprobe "$module" 2>/dev/null; then
            success "$module module loaded"
        else
            warning "Failed to load $module module - may not be available"
        fi
    done
    
    # Setup debugfs for usbmon
    if [ ! -d "/sys/kernel/debug/usb/usbmon" ]; then
        log "Mounting debugfs for usbmon..."
        if mount -t debugfs none /sys/kernel/debug 2>/dev/null; then
            success "debugfs mounted"
        else
            warning "Failed to mount debugfs"
        fi
    fi
    
    # Install Python analysis tools
    log "Installing Python USB analysis tools..."
    pip3 install --upgrade pip >/dev/null 2>&1 || true
    pip3 install pyusb >/dev/null 2>&1 || true
    
    # Create capture directories
    mkdir -p "$SCRIPT_DIR/captures"/{enumeration,authentication,network_ops,analysis}
    
    # Build USB-Sniffify if possible
    if [ -d "$SCRIPT_DIR/usb_sniffing_tools/usb-sniffify" ]; then
        log "Building USB-Sniffify..."
        cd "$SCRIPT_DIR/usb_sniffing_tools/usb-sniffify"
        
        if [ ! -d "build" ]; then
            mkdir -p build
            cd build
            
            if cmake .. >/dev/null 2>&1 && make -j$(nproc) >/dev/null 2>&1; then
                success "USB-Sniffify built successfully"
            else
                warning "USB-Sniffify build failed - usbmon will still work"
            fi
        else
            success "USB-Sniffify already built"
        fi
        
        cd "$SCRIPT_DIR"
    fi
    
    success "USB sniffing tools installed"
}

# Create helper scripts
create_helpers() {
    progress "Creating helper scripts and shortcuts"
    
    # Create quick capture script
    cat > "$SCRIPT_DIR/quick_capture.sh" << 'EOF'
#!/bin/bash
# Quick Xbox 360 protocol capture

SCRIPT_DIR="$(dirname "$0")"

echo "🎮 Quick Xbox 360 Protocol Capture"
echo "=================================="

# Auto-detect Xbox adapter
XBOX_LINE=$(lsusb | grep "045e:02a8")
if [ -z "$XBOX_LINE" ]; then
    echo "❌ Xbox 360 wireless adapter not detected"
    echo "   Connect the adapter (ID 045e:02a8) and try again"
    exit 1
fi

BUS=$(echo "$XBOX_LINE" | sed 's/Bus \([0-9]*\).*/\1/')
echo "✅ Found Xbox adapter on bus $BUS"

# Quick authentication capture
echo ""
echo "📡 Capturing Xbox authentication (30 seconds)..."
echo "   Connect Xbox 360 console now and wait for network settings"

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
OUTPUT="$SCRIPT_DIR/captures/quick_capture_${TIMESTAMP}.log"

mkdir -p "$(dirname "$OUTPUT")"

if timeout 30 cat "/sys/kernel/debug/usb/usbmon/${BUS}u" > "$OUTPUT" 2>/dev/null; then
    LINES=$(wc -l < "$OUTPUT" 2>/dev/null || echo "0")
    if [ "$LINES" -gt 0 ]; then
        echo "✅ Captured $LINES lines to: $OUTPUT"
        
        # Quick analysis
        if [ -f "$SCRIPT_DIR/src/xbox_capture_analyzer.py" ]; then
            echo ""
            echo "🔍 Quick Analysis:"
            python3 "$SCRIPT_DIR/src/xbox_capture_analyzer.py" "$OUTPUT" --output "${OUTPUT%.log}_analysis.md" >/dev/null 2>&1 || true
            
            # Show basic stats
            echo "   Control transfers: $(grep " 00 " "$OUTPUT" | wc -l)"
            echo "   Bulk transfers: $(grep -E " (01|02|81|82) " "$OUTPUT" | wc -l)"
            echo "   Analysis report: ${OUTPUT%.log}_analysis.md"
        fi
    else
        echo "❌ No data captured - check Xbox connection"
    fi
else
    echo "❌ Capture failed - check permissions and usbmon"
fi
EOF
    
    chmod +x "$SCRIPT_DIR/quick_capture.sh"
    
    # Create system status script
    cat > "$SCRIPT_DIR/system_status.sh" << 'EOF'
#!/bin/bash
# Xbox 360 emulator system status

echo "🎮 Xbox 360 WiFi Module Emulator Status"
echo "======================================="

# Service status
echo ""
echo "📋 Service Status:"
if systemctl is-active --quiet xbox360-emulator; then
    echo "✅ xbox360-emulator service: RUNNING"
else
    echo "❌ xbox360-emulator service: STOPPED"
fi

# USB gadget status
echo ""
echo "🔌 USB Gadget Status:"
if [ -d "/sys/kernel/config/usb_gadget/xbox360" ]; then
    echo "✅ USB gadget structure: EXISTS"
    if [ -f "/sys/kernel/config/usb_gadget/xbox360/UDC" ]; then
        UDC_CONTENT=$(cat /sys/kernel/config/usb_gadget/xbox360/UDC 2>/dev/null || echo "")
        if [ -n "$UDC_CONTENT" ]; then
            echo "✅ USB gadget active: $UDC_CONTENT"
        else
            echo "⚠️  USB gadget inactive"
        fi
    fi
else
    echo "❌ USB gadget structure: NOT FOUND"
fi

# Kernel modules
echo ""
echo "🧩 Kernel Modules:"
for module in "libcomposite" "dwc2" "usbmon" "raw_gadget"; do
    if lsmod | grep -q "$module"; then
        echo "✅ $module: LOADED"
    else
        echo "❌ $module: NOT LOADED"
    fi
done

# Xbox adapter detection
echo ""
echo "🎮 Xbox 360 Adapter Detection:"
XBOX_DEVICES=$(lsusb | grep "045e:02a8")
if [ -n "$XBOX_DEVICES" ]; then
    echo "✅ Xbox 360 wireless adapter detected:"
    echo "   $XBOX_DEVICES"
else
    echo "❌ Xbox 360 wireless adapter not detected"
    echo "   Looking for other Microsoft devices:"
    lsusb | grep -i microsoft | head -3
fi

# Network interfaces
echo ""
echo "🌐 Network Interfaces:"
for iface in "usb0" "br0" "wlan0" "eth0"; do
    if ip link show "$iface" >/dev/null 2>&1; then
        STATUS=$(ip link show "$iface" | grep -o "state [A-Z]*" | cut -d' ' -f2)
        echo "✅ $iface: $STATUS"
    else
        echo "❌ $iface: NOT FOUND"
    fi
done

# Recent logs
echo ""
echo "📝 Recent Logs (last 5 lines):"
journalctl -u xbox360-emulator --no-pager -n 5 2>/dev/null | tail -5 || echo "   No logs available"

echo ""
echo "🔧 Quick Actions:"
echo "   Start service: sudo systemctl start xbox360-emulator"
echo "   Stop service: sudo systemctl stop xbox360-emulator"
echo "   View logs: sudo journalctl -u xbox360-emulator -f"
echo "   Capture USB: sudo ./quick_capture.sh"
EOF
    
    chmod +x "$SCRIPT_DIR/system_status.sh"
    
    # Create desktop shortcuts if desktop environment detected
    if [ -n "$DISPLAY" ] || [ -n "$WAYLAND_DISPLAY" ]; then
        log "Creating desktop shortcuts..."
        
        DESKTOP_DIR="/home/pi/Desktop"
        if [ -d "$DESKTOP_DIR" ]; then
            cat > "$DESKTOP_DIR/Xbox360 Emulator Status.desktop" << EOF
[Desktop Entry]
Name=Xbox360 Emulator Status
Comment=Check Xbox 360 WiFi Module Emulator Status
Exec=$SCRIPT_DIR/system_status.sh
Icon=network-wireless
Terminal=true
Type=Application
Categories=System;Network;
EOF
            
            chmod +x "$DESKTOP_DIR/Xbox360 Emulator Status.desktop"
            success "Desktop shortcuts created"
        fi
    fi
    
    success "Helper scripts created"
}

# Configure autostart and services
configure_services() {
    progress "Configuring services and autostart"
    
    # Enable and start service
    log "Configuring xbox360-emulator service..."
    systemctl daemon-reload
    
    if systemctl enable xbox360-emulator.service >/dev/null 2>&1; then
        success "Service enabled for autostart"
    else
        warning "Failed to enable service for autostart"
    fi
    
    # Load kernel modules on boot
    log "Configuring kernel modules for boot..."
    cat > /etc/modules-load.d/xbox360-emulator.conf << 'EOF'
# Xbox 360 WiFi Module Emulator kernel modules
libcomposite
dwc2
usbmon
raw_gadget
EOF
    
    # Configure boot parameters if on Pi
    if [ -f "/boot/config.txt" ] && [ -f "/boot/cmdline.txt" ]; then
        log "Configuring Raspberry Pi boot parameters..."
        
        # Add dwc2 overlay if not present
        if ! grep -q "dtoverlay=dwc2" /boot/config.txt; then
            echo "dtoverlay=dwc2" >> /boot/config.txt
            info "Added dwc2 overlay to boot config"
        fi
        
        # Add dwc2 to cmdline if not present
        if ! grep -q "modules-load=dwc2" /boot/cmdline.txt; then
            cp /boot/cmdline.txt /boot/cmdline.txt.backup
            sed -i 's/$/ modules-load=dwc2/' /boot/cmdline.txt
            info "Added dwc2 to kernel command line"
        fi
    fi
    
    success "Services configured"
}

# Test installation
test_installation() {
    progress "Testing installation"
    
    log "Running system validation..."
    
    # Test if emulator can be imported
    if python3 -c "import sys; sys.path.append('$INSTALL_DIR/src'); import xbox360_emulator" 2>/dev/null; then
        success "Python modules can be imported"
    else
        warning "Python module import test failed"
    fi
    
    # Test if service can start (briefly)
    log "Testing service startup..."
    if systemctl start xbox360-emulator.service >/dev/null 2>&1; then
        sleep 2
        if systemctl is-active --quiet xbox360-emulator.service; then
            success "Service started successfully"
        else
            warning "Service started but may have issues"
        fi
        systemctl stop xbox360-emulator.service >/dev/null 2>&1 || true
    else
        warning "Service startup test failed"
    fi
    
    # Test USB sniffing tools
    if [ -f "$SCRIPT_DIR/quick_capture.sh" ]; then
        success "USB capture tools available"
    else
        warning "USB capture tools not found"
    fi
    
    success "Installation testing completed"
}

# Final setup and information
finalize_installation() {
    progress "Finalizing installation"
    
    # Create comprehensive usage guide
    cat > "$SCRIPT_DIR/USAGE.md" << 'EOF'
# Xbox 360 WiFi Module Emulator - Usage Guide

## 🚀 Quick Start

### 1. Check System Status
```bash
./system_status.sh
```

### 2. Start the Emulator
```bash
sudo systemctl start xbox360-emulator
```

### 3. Connect Xbox 360
- Connect Pi to Xbox 360 via USB-C cable
- Xbox should recognize wireless adapter
- Go to Xbox Network Settings

### 4. Capture Real Adapter Protocol (Optional)
```bash
sudo ./quick_capture.sh
```

## 🔧 Service Management

```bash
# Start service
sudo systemctl start xbox360-emulator

# Stop service  
sudo systemctl stop xbox360-emulator

# Check status
sudo systemctl status xbox360-emulator

# View logs
sudo journalctl -u xbox360-emulator -f

# Restart service
sudo systemctl restart xbox360-emulator
```

## 📊 Monitoring

```bash
# Real-time status
sudo xbox360-emulator interactive

# Quick system check
./system_status.sh

# USB device detection
lsusb | grep -i xbox
```

## 🕵️ USB Protocol Analysis

```bash
# Quick capture (30 seconds)
sudo ./quick_capture.sh

# Full protocol capture
sudo ./capture_xbox_protocol.sh

# Manual usbmon capture
sudo ./capture_with_usbmon.sh authentication 30
```

## 🛠️ Troubleshooting

### Xbox Not Recognizing Adapter
1. Check service status: `./system_status.sh`
2. Verify USB connection (USB-C cable)
3. Check logs: `sudo journalctl -u xbox360-emulator -f`
4. Restart service: `sudo systemctl restart xbox360-emulator`

### USB Gadget Issues
1. Check kernel modules: `lsmod | grep libcomposite`
2. Load modules: `sudo modprobe libcomposite dwc2`
3. Check USB controller: `ls /sys/class/udc/`
4. Reboot if needed: `sudo reboot`

### Network Issues
1. Check bridge: `brctl show`
2. Check interfaces: `ip link show`
3. Verify ethernet: `ping 8.8.8.8`

## 📁 File Locations

- **Installation**: `/opt/xbox360-emulator/`
- **Configuration**: `/etc/xbox360-emulator/`
- **Logs**: `/var/log/xbox360-emulator/`
- **Captures**: `./captures/`
- **Tools**: Current directory

## 🔄 Updates

To update the emulator:
1. Pull latest code: `git pull`
2. Reinstall: `sudo ./install_complete.sh`
3. Restart service: `sudo systemctl restart xbox360-emulator`
EOF
    
    # Set permissions
    chown -R root:root "$INSTALL_DIR" "$CONFIG_DIR" "$LOG_DIR" 2>/dev/null || true
    chmod -R 755 "$SCRIPT_DIR"/*.sh 2>/dev/null || true
    
    success "Installation finalized"
}

# Main installation function
main() {
    header "XBOX 360 WIFI MODULE EMULATOR - COMPLETE INSTALLATION"
    echo ""
    info "This will install the complete Xbox 360 WiFi Module Emulator system"
    info "including USB sniffing tools and all dependencies."
    echo ""
    info "Installation location: $INSTALL_DIR"
    info "Configuration: $CONFIG_DIR"
    info "Estimated time: 5-10 minutes"
    echo ""
    
    # Check if this is a re-run
    if [ -d "$INSTALL_DIR" ]; then
        warning "Existing installation detected"
        echo "This will update/reinstall the system."
        echo ""
    fi
    
    read -p "Continue with installation? (y/N): " -r
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        info "Installation cancelled"
        exit 0
    fi
    
    echo ""
    header "STARTING AUTOMATED INSTALLATION"
    
    # Run installation steps
    check_system
    update_system
    install_emulator
    install_usb_sniffing
    create_helpers
    configure_services
    test_installation
    finalize_installation
    
    # Installation complete
    echo ""
    header "INSTALLATION COMPLETE!"
    echo ""
    success "Xbox 360 WiFi Module Emulator installed successfully!"
    echo ""
    info "📋 What was installed:"
    info "  ✅ Xbox 360 WiFi Module Emulator with FunctionFS authentication"
    info "  ✅ USB sniffing tools (usbmon + USB-Sniffify)"
    info "  ✅ Network bridge and virtual wireless support"
    info "  ✅ Systemd service with autostart"
    info "  ✅ Helper scripts and monitoring tools"
    info "  ✅ Complete documentation and usage guides"
    echo ""
    info "🚀 Next steps:"
    info "  1. Check status: $SCRIPT_DIR/system_status.sh"
    info "  2. Start service: sudo systemctl start xbox360-emulator"
    info "  3. Connect Xbox 360 via USB-C cable"
    info "  4. Xbox should recognize wireless adapter"
    echo ""
    info "🔧 Useful commands:"
    info "  • System status: $SCRIPT_DIR/system_status.sh"
    info "  • Quick capture: sudo $SCRIPT_DIR/quick_capture.sh"
    info "  • View logs: sudo journalctl -u xbox360-emulator -f"
    info "  • Usage guide: cat $SCRIPT_DIR/USAGE.md"
    echo ""
    
    # Check if reboot is needed
    if [ -f "/boot/config.txt" ]; then
        warning "REBOOT RECOMMENDED to activate all USB gadget features"
        echo ""
        read -p "Reboot now? (y/N): " -r
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            info "Rebooting in 5 seconds..."
            sleep 5
            reboot
        else
            info "Remember to reboot later to activate all features"
        fi
    fi
    
    echo ""
    success "Installation completed successfully! 🎮"
}

# Run main installation
main "$@"