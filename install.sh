#!/bin/bash
# Xbox 360 WiFi Module Emulator - Production Installation Script
# Installs the complete system with systemd services and production configuration

set -e

INSTALL_DIR="/opt/xbox360-emulator"
CONFIG_DIR="/etc/xbox360-emulator"
LOG_DIR="/var/log/xbox360-emulator"
SERVICE_NAME="xbox360-emulator"

echo "🎮 Xbox 360 WiFi Module Emulator - Production Installation"
echo "=========================================================="

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   echo "❌ Error: This script must be run as root (use sudo)"
   exit 1
fi

# Check if running on Raspberry Pi 4
if ! grep -q "Raspberry Pi 4" /proc/cpuinfo 2>/dev/null; then
    echo "❌ Error: This installer requires Raspberry Pi 4"
    exit 1
fi

echo "✅ Raspberry Pi 4 detected"

# Create directories
echo "📁 Creating directories..."
mkdir -p "$INSTALL_DIR"/{src,bin,docs}
mkdir -p "$CONFIG_DIR"
mkdir -p "$LOG_DIR"

# Install system dependencies
echo "📦 Installing system dependencies..."
apt-get update -qq
apt-get install -y \
    python3 \
    python3-pip \
    bridge-utils \
    iptables-persistent \
    dnsmasq \
    hostapd \
    systemd

# Install Python dependencies (if any future ones are needed)
pip3 install --upgrade pip

# Copy source files
echo "📋 Installing source files..."
cp -r src/* "$INSTALL_DIR/src/"
chmod +x "$INSTALL_DIR/src/"*.py

# Create main executable
cat > "$INSTALL_DIR/bin/xbox360-emulator" << 'EOF'
#!/bin/bash
# Xbox 360 WiFi Module Emulator main executable
cd /opt/xbox360-emulator/src
exec python3 xbox360_emulator.py "$@"
EOF
chmod +x "$INSTALL_DIR/bin/xbox360-emulator"

# Create symlink in system PATH
ln -sf "$INSTALL_DIR/bin/xbox360-emulator" /usr/local/bin/xbox360-emulator

# Create default configuration
echo "⚙️  Creating default configuration..."
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

# Configure boot options for USB gadget mode
echo "🔧 Configuring boot options..."
if ! grep -q "dtoverlay=dwc2" /boot/config.txt; then
    echo "dtoverlay=dwc2" >> /boot/config.txt
    echo "✅ Added dwc2 overlay to boot config"
fi

if ! grep -q "modules-load=dwc2" /boot/cmdline.txt; then
    sed -i 's/$/ modules-load=dwc2/' /boot/cmdline.txt
    echo "✅ Added dwc2 to kernel command line"
fi

# Enable required kernel modules at boot
echo "🔧 Configuring kernel modules..."
if ! grep -q "dwc2" /etc/modules; then
    echo "dwc2" >> /etc/modules
fi
if ! grep -q "libcomposite" /etc/modules; then
    echo "libcomposite" >> /etc/modules
fi

# Create systemd service
echo "🔧 Creating systemd service..."
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
ExecReload=/bin/kill -HUP \$MAINPID
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

# Create logrotate configuration
echo "📝 Setting up log rotation..."
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

# Create validation script
echo "🧪 Installing validation script..."
cat > "$INSTALL_DIR/bin/validate" << 'EOF'
#!/bin/bash
# Xbox 360 WiFi Module Emulator - Validation Script
cd /opt/xbox360-emulator/src
exec python3 ../tests/test_xbox360_emulator.py validate
EOF
chmod +x "$INSTALL_DIR/bin/validate"

# Create status script
echo "📊 Installing status script..."
cat > "$INSTALL_DIR/bin/status" << 'EOF'
#!/bin/bash
# Xbox 360 WiFi Module Emulator - Status Script
cd /opt/xbox360-emulator/src
exec python3 xbox360_emulator.py status --config /etc/xbox360-emulator/config.json
EOF
chmod +x "$INSTALL_DIR/bin/status"

# Create aliases for convenience
cat > "/etc/profile.d/xbox360-emulator.sh" << 'EOF'
# Xbox 360 WiFi Module Emulator aliases
alias xbox360='xbox360-emulator'
alias xbox360-status='systemctl status xbox360-emulator'
alias xbox360-logs='journalctl -u xbox360-emulator -f'
alias xbox360-validate='/opt/xbox360-emulator/bin/validate'
EOF

# Set proper permissions
chown -R root:root "$INSTALL_DIR"
chown -R root:root "$CONFIG_DIR"
chown -R root:root "$LOG_DIR"
chmod 755 "$INSTALL_DIR"
chmod 644 "$CONFIG_DIR/config.json"

# Reload systemd and enable service
echo "🔧 Enabling systemd service..."
systemctl daemon-reload
systemctl enable "${SERVICE_NAME}.service"

# Copy documentation
echo "📚 Installing documentation..."
cp README.md "$INSTALL_DIR/docs/"
if [ -d "docs" ]; then
    cp -r docs/* "$INSTALL_DIR/docs/"
fi

# Create uninstall script
echo "🗑️  Creating uninstall script..."
cat > "$INSTALL_DIR/bin/uninstall" << 'EOF'
#!/bin/bash
# Xbox 360 WiFi Module Emulator - Uninstall Script

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

# Remove boot configuration (commented out for safety)
# sed -i '/dtoverlay=dwc2/d' /boot/config.txt
# sed -i 's/ modules-load=dwc2//g' /boot/cmdline.txt

echo "✅ Uninstall complete"
echo "⚠️  Boot configuration left intact (manual removal required)"
echo "⚠️  Reboot recommended to clear kernel modules"
EOF
chmod +x "$INSTALL_DIR/bin/uninstall"

echo ""
echo "🎉 Installation Complete!"
echo "========================"
echo ""
echo "📁 Installation directory: $INSTALL_DIR"
echo "⚙️  Configuration file: $CONFIG_DIR/config.json"
echo "📝 Log directory: $LOG_DIR"
echo ""
echo "🚀 Quick Start Commands:"
echo "   sudo xbox360-emulator start     # Start emulator"
echo "   sudo systemctl start xbox360-emulator   # Start as service"
echo "   xbox360-validate                # Run validation tests"
echo "   systemctl status xbox360-emulator       # Check service status"
echo "   journalctl -u xbox360-emulator -f       # View live logs"
echo ""
echo "🔧 Service Management:"
echo "   sudo systemctl enable xbox360-emulator  # Auto-start on boot (already done)"
echo "   sudo systemctl start xbox360-emulator   # Start service"
echo "   sudo systemctl stop xbox360-emulator    # Stop service"
echo "   sudo systemctl status xbox360-emulator  # Check status"
echo ""
echo "⚠️  REBOOT REQUIRED to activate USB gadget mode"
echo ""
echo "After reboot:"
echo "1. Run: sudo xbox360-validate"
echo "2. Start service: sudo systemctl start xbox360-emulator"
echo "3. Connect Xbox 360 via USB-C cable"
echo "4. Configure network in Xbox 360 settings"
echo ""
echo "📚 Documentation: $INSTALL_DIR/docs/"
echo "🗑️  To uninstall: sudo $INSTALL_DIR/bin/uninstall"
echo ""

# Offer to reboot
echo "Would you like to reboot now to activate USB gadget mode? (y/n)"
read -r response
if [[ "$response" =~ ^[Yy]$ ]]; then
    echo "🔄 Rebooting in 5 seconds..."
    sleep 5
    reboot
else
    echo "⚠️  Remember to reboot before using the emulator!"
fi