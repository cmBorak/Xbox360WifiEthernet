#!/bin/bash
# Xbox 360 WiFi Module Emulator - Debug Installation Script
# Diagnoses and fixes installation issues

set -e

echo "🔍 Xbox 360 WiFi Module Emulator - Installation Diagnostics"
echo "============================================================"

# Get current directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo "📁 Script directory: $SCRIPT_DIR"

# Check if running as root
echo "👤 User check:"
if [[ $EUID -eq 0 ]]; then
    echo "✅ Running as root"
else
    echo "❌ Not running as root (need: sudo $0)"
    echo "   Current user: $(whoami)"
    echo "   UID: $EUID"
    exit 1
fi

# Check system type
echo ""
echo "💻 System check:"
if [ -f "/proc/cpuinfo" ]; then
    if grep -q "Raspberry Pi" /proc/cpuinfo; then
        PI_MODEL=$(grep "Model" /proc/cpuinfo | cut -d: -f2 | xargs)
        echo "✅ Detected: $PI_MODEL"
        if grep -q "Raspberry Pi 4" /proc/cpuinfo; then
            echo "✅ Raspberry Pi 4 confirmed"
        else
            echo "⚠️  Not Raspberry Pi 4 - may have compatibility issues"
        fi
    else
        echo "⚠️  Not detected as Raspberry Pi"
        echo "   Running on: $(uname -m)"
    fi
else
    echo "❌ Cannot detect system type (/proc/cpuinfo missing)"
fi

# Check required directories and files
echo ""
echo "📂 File structure check:"
REQUIRED_FILES=(
    "src/xbox360_emulator.py"
    "src/xbox360_gadget.py" 
    "src/network_bridge.py"
    "tests/test_xbox360_emulator.py"
    "install.sh"
)

for file in "${REQUIRED_FILES[@]}"; do
    if [ -f "$SCRIPT_DIR/$file" ]; then
        echo "✅ Found: $file"
    else
        echo "❌ Missing: $file"
    fi
done

# Check Python requirements
echo ""
echo "🐍 Python environment check:"
if command -v python3 >/dev/null 2>&1; then
    PYTHON_VERSION=$(python3 --version)
    echo "✅ Python3 available: $PYTHON_VERSION"
else
    echo "❌ Python3 not found"
fi

if command -v pip3 >/dev/null 2>&1; then
    echo "✅ pip3 available"
else
    echo "❌ pip3 not found"
fi

# Check system utilities
echo ""
echo "🔧 System utilities check:"
REQUIRED_COMMANDS=(
    "systemctl"
    "brctl"
    "iptables"
    "modprobe"
)

for cmd in "${REQUIRED_COMMANDS[@]}"; do
    if command -v "$cmd" >/dev/null 2>&1; then
        echo "✅ Found: $cmd"
    else
        echo "❌ Missing: $cmd"
    fi
done

# Check kernel support
echo ""
echo "🔌 Kernel support check:"
if [ -d "/sys/kernel/config" ]; then
    echo "✅ configfs mounted"
else
    echo "⚠️  configfs not mounted - attempting to mount..."
    if mount -t configfs none /sys/kernel/config 2>/dev/null; then
        echo "✅ configfs mounted successfully"
    else
        echo "❌ Failed to mount configfs"
    fi
fi

# Check for USB gadget support
if [ -d "/sys/class/udc" ]; then
    UDC_COUNT=$(ls /sys/class/udc | wc -l)
    if [ $UDC_COUNT -gt 0 ]; then
        echo "✅ USB Device Controller found: $(ls /sys/class/udc)"
    else
        echo "⚠️  No USB Device Controllers found"
    fi
else
    echo "❌ USB gadget support not available"
fi

# Test module loading
echo ""
echo "📦 Kernel modules check:"
REQUIRED_MODULES=(
    "libcomposite"
    "dwc2"
)

for module in "${REQUIRED_MODULES[@]}"; do
    if lsmod | grep -q "$module"; then
        echo "✅ Module loaded: $module"
    else
        echo "⚠️  Module not loaded: $module - attempting to load..."
        if modprobe "$module" 2>/dev/null; then
            echo "✅ Successfully loaded: $module"
        else
            echo "❌ Failed to load: $module"
        fi
    fi
done

# Check boot configuration
echo ""
echo "🚀 Boot configuration check:"
if [ -f "/boot/config.txt" ]; then
    if grep -q "dtoverlay=dwc2" /boot/config.txt; then
        echo "✅ dwc2 overlay configured in /boot/config.txt"
    else
        echo "⚠️  dwc2 overlay not found in /boot/config.txt"
    fi
else
    echo "❌ /boot/config.txt not found"
fi

if [ -f "/boot/cmdline.txt" ]; then
    if grep -q "modules-load=dwc2" /boot/cmdline.txt; then
        echo "✅ dwc2 module loading configured in /boot/cmdline.txt"
    else
        echo "⚠️  dwc2 module loading not found in /boot/cmdline.txt"
    fi
else
    echo "❌ /boot/cmdline.txt not found"
fi

# Check if service already exists
echo ""
echo "🔧 Service status check:"
SERVICE_FILE="/etc/systemd/system/xbox360-emulator.service"
if [ -f "$SERVICE_FILE" ]; then
    echo "⚠️  Service file already exists: $SERVICE_FILE"
    echo "   Status: $(systemctl is-active xbox360-emulator 2>/dev/null || echo 'inactive')"
    echo "   Enabled: $(systemctl is-enabled xbox360-emulator 2>/dev/null || echo 'disabled')"
else
    echo "✅ No existing service file found"
fi

# Provide installation guidance
echo ""
echo "🎯 Installation Guidance:"
echo "========================="

# Count issues
ERRORS=0
WARNINGS=0

# Simple error counting (you'd implement actual checks here)
if ! command -v python3 >/dev/null 2>&1; then
    ((ERRORS++))
    echo "❌ CRITICAL: Install Python3 first: sudo apt update && sudo apt install python3 python3-pip"
fi

if ! command -v systemctl >/dev/null 2>&1; then
    ((ERRORS++))
    echo "❌ CRITICAL: systemd not available - manual installation required"
fi

if [ ! -f "$SCRIPT_DIR/src/xbox360_emulator.py" ]; then
    ((ERRORS++))
    echo "❌ CRITICAL: Source files missing - re-download the project"
fi

if [ $ERRORS -eq 0 ]; then
    echo "✅ System ready for installation!"
    echo ""
    echo "To install:"
    echo "1. cd $SCRIPT_DIR"
    echo "2. sudo ./install.sh"
    echo ""
    echo "If installation fails, run:"
    echo "sudo ./debug_install.sh"
else
    echo "❌ Found $ERRORS critical issues - fix these before installing"
fi

if [ $WARNINGS -gt 0 ]; then
    echo "⚠️  Found $WARNINGS warnings - installation may work but check after install"
fi

echo ""
echo "📝 For installation logs, check:"
echo "   - journalctl -u xbox360-emulator"
echo "   - /var/log/xbox360-emulator/"
echo "   - dmesg | grep -i usb"