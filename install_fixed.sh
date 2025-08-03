#!/bin/bash
# Xbox 360 WiFi Module Emulator - Fixed Installation Script
# Addresses common installation issues and provides better error handling

set -e

# Configuration
INSTALL_DIR="/opt/xbox360-emulator"
CONFIG_DIR="/etc/xbox360-emulator"
LOG_DIR="/var/log/xbox360-emulator"
SERVICE_NAME="xbox360-emulator"

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
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

# Error handling
cleanup() {
    if [ $? -ne 0 ]; then
        error "Installation failed. Check the output above for details."
        echo ""
        echo "For help:"
        echo "1. Run: sudo $SCRIPT_DIR/debug_install.sh"
        echo "2. Check logs: journalctl -xe"
        echo "3. Manual cleanup: sudo rm -rf $INSTALL_DIR $CONFIG_DIR $LOG_DIR"
    fi
}
trap cleanup EXIT

echo "🎮 Xbox 360 WiFi Module Emulator - Fixed Installation"
echo "====================================================="

# Preliminary checks
log "Performing preliminary checks..."

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   error "This script must be run as root"
   echo "Usage: sudo $0"
   exit 1
fi
success "Running as root"

# Check if source files exist
REQUIRED_FILES=(
    "src/xbox360_emulator.py"
    "src/xbox360_gadget.py"
    "src/network_bridge.py"
    "tests/test_xbox360_emulator.py"
)

for file in "${REQUIRED_FILES[@]}"; do
    if [ ! -f "$SCRIPT_DIR/$file" ]; then
        error "Required file missing: $file"
        error "Make sure you're running this from the correct directory"
        exit 1
    fi
done
success "All required source files found"

# Check system type (more permissive)
if [ -f "/proc/cpuinfo" ]; then
    if grep -q "Raspberry Pi" /proc/cpuinfo; then
        PI_MODEL=$(grep "Model" /proc/cpuinfo | cut -d: -f2 | xargs || echo "Unknown Pi Model")
        success "Detected: $PI_MODEL"
        if ! grep -q "Raspberry Pi 4" /proc/cpuinfo; then
            warning "Not Raspberry Pi 4 - USB gadget mode may not work"
            echo "Continue anyway? (y/N)"
            read -r response
            if [[ ! "$response" =~ ^[Yy]$ ]]; then
                exit 1
            fi
        fi
    else
        warning "Not detected as Raspberry Pi - USB gadget mode will not work"
        echo "Continue for testing/development? (y/N)"
        read -r response
        if [[ ! "$response" =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
else
    warning "Cannot detect system type"
fi

# Stop existing service if running
log "Checking for existing installation..."
if systemctl is-active --quiet "$SERVICE_NAME" 2>/dev/null; then
    log "Stopping existing service..."
    systemctl stop "$SERVICE_NAME" || true
fi

if systemctl is-enabled --quiet "$SERVICE_NAME" 2>/dev/null; then
    log "Disabling existing service..."
    systemctl disable "$SERVICE_NAME" || true
fi

# Remove existing service file
if [ -f "/etc/systemd/system/${SERVICE_NAME}.service" ]; then
    log "Removing existing service file..."
    rm -f "/etc/systemd/system/${SERVICE_NAME}.service"
    systemctl daemon-reload
fi

# Create directories with proper error handling
log "Creating directories..."
if ! mkdir -p "$INSTALL_DIR"/{src,bin,docs}; then
    error "Failed to create install directory: $INSTALL_DIR"
    exit 1
fi

if ! mkdir -p "$CONFIG_DIR"; then
    error "Failed to create config directory: $CONFIG_DIR"
    exit 1
fi

if ! mkdir -p "$LOG_DIR"; then
    error "Failed to create log directory: $LOG_DIR"
    exit 1
fi
success "Directories created"

# Update package list
log "Updating package list..."
if ! apt-get update -qq; then
    warning "Package update failed - continuing with cached packages"
fi

# Install system dependencies with error handling
log "Installing system dependencies..."
PACKAGES=(
    "python3"
    "python3-pip"
    "bridge-utils"
    "iptables-persistent"
)

# Install packages one by one for better error handling
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

# Note: No additional packages needed for virtual wireless

# Upgrade pip
log "Upgrading pip..."
if ! python3 -m pip install --upgrade pip; then
    warning "Failed to upgrade pip - continuing"
fi

# Copy source files
log "Installing source files..."
if ! cp -r "$SCRIPT_DIR/src/"* "$INSTALL_DIR/src/"; then
    error "Failed to copy source files"
    exit 1
fi

# Make Python scripts executable
chmod +x "$INSTALL_DIR/src/"*.py || true
success "Source files installed"

# Create main executable
log "Creating main executable..."
cat > "$INSTALL_DIR/bin/xbox360-emulator" << 'EOF'
#!/bin/bash
# Xbox 360 WiFi Module Emulator main executable
cd /opt/xbox360-emulator/src
exec python3 xbox360_emulator.py "$@"
EOF

if ! chmod +x "$INSTALL_DIR/bin/xbox360-emulator"; then
    error "Failed to create main executable"
    exit 1
fi

# Create symlink in system PATH
if ! ln -sf "$INSTALL_DIR/bin/xbox360-emulator" /usr/local/bin/xbox360-emulator; then
    warning "Failed to create system PATH symlink"
fi
success "Executable created"

# Create default configuration
log "Creating configuration..."
cat > "$CONFIG_DIR/config.json" << 'EOF'
{
  "gadget": {
    "name": "xbox360",
    "auto_start": true
  },
  "bridge": {
    "name": "br0",
    "eth_interface": "eth0",
    "usb_interface": "usb0",
    "use_dhcp": true,
    "static_ip": null
  },
  "virtual_wireless": {
    "enabled": true,
    "auto_connect": true,
    "network_name": "PI-Net"
  },
  "monitoring": {
    "status_check_interval": 30,
    "connection_monitor": true,
    "auto_recovery": true
  },
  "logging": {
    "level": "INFO",
    "file": "/var/log/xbox360-emulator/emulator.log"
  }
}
EOF
success "Configuration created"

# Configure boot options (with checks)
log "Configuring boot options..."
BOOT_CONFIG_MODIFIED=false
CMDLINE_MODIFIED=false

if [ -f "/boot/config.txt" ]; then
    if ! grep -q "dtoverlay=dwc2" /boot/config.txt; then
        echo "dtoverlay=dwc2" >> /boot/config.txt
        BOOT_CONFIG_MODIFIED=true
        success "Added dwc2 overlay to boot config"
    else
        success "dwc2 overlay already configured"
    fi
else
    warning "/boot/config.txt not found - boot configuration skipped"
fi

if [ -f "/boot/cmdline.txt" ]; then
    if ! grep -q "modules-load=dwc2" /boot/cmdline.txt; then
        # Backup original cmdline.txt
        cp /boot/cmdline.txt /boot/cmdline.txt.backup
        sed -i 's/$/ modules-load=dwc2/' /boot/cmdline.txt
        CMDLINE_MODIFIED=true
        success "Added dwc2 to kernel command line"
    else
        success "dwc2 module loading already configured"
    fi
else
    warning "/boot/cmdline.txt not found - boot configuration skipped"
fi

# Configure kernel modules
log "Configuring kernel modules..."
if [ -f "/etc/modules" ]; then
    for module in "dwc2" "libcomposite"; do
        if ! grep -q "^$module$" /etc/modules; then
            echo "$module" >> /etc/modules
            success "Added $module to /etc/modules"
        else
            success "$module already in /etc/modules"
        fi
    done
else
    warning "/etc/modules not found - module configuration skipped"
fi

# Create systemd service
log "Creating systemd service..."
cat > "/etc/systemd/system/${SERVICE_NAME}.service" << EOF
[Unit]
Description=Xbox 360 WiFi Module Emulator
Documentation=file://$INSTALL_DIR/docs/
After=network.target
Wants=network-online.target

[Service]
Type=exec
ExecStart=$INSTALL_DIR/bin/xbox360-emulator start --daemon --config $CONFIG_DIR/config.json
ExecStop=$INSTALL_DIR/bin/xbox360-emulator stop
Restart=always
RestartSec=10
User=root
Group=root
WorkingDirectory=$INSTALL_DIR
StandardOutput=journal
StandardError=journal
SyslogIdentifier=xbox360-emulator

# Security settings
NoNewPrivileges=false
PrivateTmp=false
ProtectSystem=false
ProtectHome=false

[Install]
WantedBy=multi-user.target
EOF

# Create additional utility scripts
log "Creating utility scripts..."

# Validation script
cat > "$INSTALL_DIR/bin/validate" << 'EOF'
#!/bin/bash
cd /opt/xbox360-emulator/src
exec python3 ../tests/test_xbox360_emulator.py validate
EOF
chmod +x "$INSTALL_DIR/bin/validate"

# Status script
cat > "$INSTALL_DIR/bin/status" << 'EOF'
#!/bin/bash
cd /opt/xbox360-emulator/src
exec python3 xbox360_emulator.py status --config /etc/xbox360-emulator/config.json
EOF
chmod +x "$INSTALL_DIR/bin/status"

# Quick start script
cat > "$INSTALL_DIR/bin/quickstart" << 'EOF'
#!/bin/bash
echo "🎮 Xbox 360 WiFi Module Emulator - Quick Start"
echo "=============================================="
echo ""
echo "1. Validation:"
/opt/xbox360-emulator/bin/validate
echo ""
echo "2. Starting service:"
systemctl start xbox360-emulator
echo ""
echo "3. Service status:"
systemctl status xbox360-emulator --no-pager
echo ""
echo "✅ Ready! Connect Xbox 360 via USB-C cable"
EOF
chmod +x "$INSTALL_DIR/bin/quickstart"

# Create logrotate configuration
if [ -d "/etc/logrotate.d" ]; then
    log "Setting up log rotation..."
    cat > "/etc/logrotate.d/xbox360-emulator" << EOF
$LOG_DIR/*.log {
    daily
    missingok
    rotate 7
    compress
    delaycompress
    notifempty
    create 0644 root root
    postrotate
        systemctl reload xbox360-emulator || true
    endscript
}
EOF
    success "Log rotation configured"
fi

# Set proper permissions
log "Setting permissions..."
chown -R root:root "$INSTALL_DIR"
chown -R root:root "$CONFIG_DIR"
chown -R root:root "$LOG_DIR"
chmod 755 "$INSTALL_DIR"
chmod 644 "$CONFIG_DIR/config.json"

# Reload systemd and enable service
log "Enabling systemd service..."
systemctl daemon-reload
if ! systemctl enable "${SERVICE_NAME}.service"; then
    error "Failed to enable systemd service"
    exit 1
fi
success "Service enabled"

# Copy documentation
log "Installing documentation..."
if [ -d "$SCRIPT_DIR/docs" ]; then
    cp -r "$SCRIPT_DIR/docs/"* "$INSTALL_DIR/docs/" || true
fi
cp "$SCRIPT_DIR/README.md" "$INSTALL_DIR/docs/" 2>/dev/null || true

# Create aliases
cat > "/etc/profile.d/xbox360-emulator.sh" << 'EOF'
# Xbox 360 WiFi Module Emulator aliases
alias xbox360='xbox360-emulator'
alias xbox360-status='systemctl status xbox360-emulator'
alias xbox360-logs='journalctl -u xbox360-emulator -f'
alias xbox360-validate='/opt/xbox360-emulator/bin/validate'
alias xbox360-quickstart='/opt/xbox360-emulator/bin/quickstart'
EOF

# Create uninstall script
cat > "$INSTALL_DIR/bin/uninstall" << 'EOF'
#!/bin/bash
echo "🗑️  Uninstalling Xbox 360 WiFi Module Emulator..."

# Stop and disable service
systemctl stop xbox360-emulator || true
systemctl disable xbox360-emulator || true

# Remove systemd service
rm -f /etc/systemd/system/xbox360-emulator.service
systemctl daemon-reload

# Remove files
rm -rf /opt/xbox360-emulator
rm -rf /etc/xbox360-emulator
rm -rf /var/log/xbox360-emulator
rm -f /usr/local/bin/xbox360-emulator
rm -f /etc/logrotate.d/xbox360-emulator
rm -f /etc/profile.d/xbox360-emulator.sh

echo "✅ Uninstall complete"
echo "⚠️  Boot configuration left intact (manual removal required)"
echo "⚠️  To remove boot config:"
echo "   Remove 'dtoverlay=dwc2' from /boot/config.txt"
echo "   Remove 'modules-load=dwc2' from /boot/cmdline.txt"
echo "⚠️  Reboot recommended"
EOF
chmod +x "$INSTALL_DIR/bin/uninstall"

# Final status
echo ""
success "Installation completed successfully!"
echo ""
echo "📁 Installation directory: $INSTALL_DIR"
echo "⚙️  Configuration file: $CONFIG_DIR/config.json"
echo "📝 Log directory: $LOG_DIR"
echo ""
echo "🚀 Quick Start:"
echo "   sudo $INSTALL_DIR/bin/quickstart"
echo ""
echo "🔧 Service Management:"
echo "   sudo systemctl start xbox360-emulator"
echo "   sudo systemctl status xbox360-emulator"
echo "   sudo journalctl -u xbox360-emulator -f"
echo ""
echo "🧪 Validation:"
echo "   sudo xbox360-validate"
echo ""

# Check if reboot is needed
REBOOT_NEEDED=false
if [ "$BOOT_CONFIG_MODIFIED" = true ] || [ "$CMDLINE_MODIFIED" = true ]; then
    REBOOT_NEEDED=true
fi

if [ "$REBOOT_NEEDED" = true ]; then
    echo "⚠️  REBOOT REQUIRED to activate USB gadget mode"
    echo ""
    echo "After reboot:"
    echo "1. Run: sudo xbox360-validate"
    echo "2. Start: sudo systemctl start xbox360-emulator"
    echo "3. Connect Xbox 360 via USB-C cable"
    echo ""
    echo "Reboot now? (y/N)"
    read -r response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        echo "🔄 Rebooting in 5 seconds..."
        sleep 5
        reboot
    fi
else
    echo "✅ No reboot required - you can start using the emulator now!"
    echo ""
    echo "To test:"
    echo "1. sudo xbox360-validate"
    echo "2. sudo systemctl start xbox360-emulator"
fi

echo ""
echo "📚 Documentation: $INSTALL_DIR/docs/"
echo "🗑️  To uninstall: sudo $INSTALL_DIR/bin/uninstall"
echo "🔍 For troubleshooting: sudo $SCRIPT_DIR/debug_install.sh"