#!/bin/bash
# Xbox 360 WiFi Module Emulator - Setup Script
# Configures Raspberry Pi 4 for USB gadget mode and Xbox 360 emulation

set -e

echo "🎮 Xbox 360 WiFi Module Emulator Setup"
echo "======================================="

# Check if running on Raspberry Pi 4
if ! grep -q "Raspberry Pi 4" /proc/cpuinfo 2>/dev/null; then
    echo "❌ Error: This script requires Raspberry Pi 4"
    exit 1
fi

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   echo "❌ Error: This script must be run as root (use sudo)"
   exit 1
fi

echo "✅ Raspberry Pi 4 detected"

# Update system
echo "📦 Updating system packages..."
apt-get update -qq
apt-get upgrade -y -qq

# Install required packages
echo "📦 Installing required packages..."
apt-get install -y \
    git \
    python3 \
    python3-pip \
    bridge-utils \
    iptables-persistent \
    dnsmasq \
    hostapd

# Enable required kernel modules
echo "🔧 Configuring kernel modules..."
echo "dwc2" >> /etc/modules
echo "libcomposite" >> /etc/modules

# Configure boot options for USB gadget mode
echo "🔧 Configuring boot options..."
if ! grep -q "dtoverlay=dwc2" /boot/config.txt; then
    echo "dtoverlay=dwc2" >> /boot/config.txt
fi

if ! grep -q "modules-load=dwc2" /boot/cmdline.txt; then
    sed -i 's/$/ modules-load=dwc2/' /boot/cmdline.txt
fi

# Create USB gadget configuration
echo "🔧 Creating USB gadget configuration..."
cat > /usr/local/bin/xbox360-gadget.sh << 'EOF'
#!/bin/bash
# Xbox 360 WiFi Adapter USB Gadget Configuration

cd /sys/kernel/config/usb_gadget/
mkdir -p xbox360
cd xbox360

# USB Device Descriptor - Xbox 360 Wireless Network Adapter
echo 0x045e > idVendor        # Microsoft Corporation
echo 0x0292 > idProduct       # Xbox 360 Wireless Network Adapter
echo 0x0100 > bcdDevice       # Device version 1.0
echo 0x0200 > bcdUSB          # USB 2.0

# Device class set to vendor-specific (like original)
echo 0xFF > bDeviceClass      # Vendor-specific
echo 0xFF > bDeviceSubClass   # Vendor-specific  
echo 0xFF > bDeviceProtocol   # Vendor-specific

# String descriptors
mkdir -p strings/0x409        # English (US)
echo "Microsoft Corp." > strings/0x409/manufacturer
echo "Xbox 360 Wireless Network Adapter" > strings/0x409/product
echo "$(cat /proc/cpuinfo | grep Serial | cut -d' ' -f2)" > strings/0x409/serialnumber

# Configuration
mkdir -p configs/c.1
echo 500 > configs/c.1/MaxPower
mkdir -p configs/c.1/strings/0x409
echo "Xbox 360 Configuration" > configs/c.1/strings/0x409/configuration

# Network function (NCM - most modern protocol)
mkdir -p functions/ncm.usb0
echo "$(cat /sys/class/net/eth0/address)" > functions/ncm.usb0/host_addr
echo "02:22:82:12:34:56" > functions/ncm.usb0/dev_addr

# Link function to configuration
ln -s functions/ncm.usb0 configs/c.1/

# Enable gadget
echo "$(ls /sys/class/udc)" > UDC

echo "✅ Xbox 360 USB gadget configured successfully"
EOF

chmod +x /usr/local/bin/xbox360-gadget.sh

# Create network bridge configuration
echo "🌐 Creating network bridge configuration..."
cat > /usr/local/bin/setup-bridge.sh << 'EOF'
#!/bin/bash
# Network Bridge Setup for Xbox 360 Emulator

# Create bridge interface
brctl addbr br0

# Add ethernet to bridge
brctl addif br0 eth0

# Add USB gadget interface to bridge (will be available after gadget is up)
sleep 2
if ip link show usb0 >/dev/null 2>&1; then
    brctl addif br0 usb0
    echo "✅ USB gadget interface added to bridge"
fi

# Configure bridge IP (use DHCP or static)
dhclient br0

# Enable IP forwarding
echo 1 > /proc/sys/net/ipv4/ip_forward

# Setup NAT rules for Xbox traffic
iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE
iptables -A FORWARD -i br0 -o eth0 -j ACCEPT
iptables -A FORWARD -i eth0 -o br0 -m state --state RELATED,ESTABLISHED -j ACCEPT

echo "✅ Network bridge configured successfully"
EOF

chmod +x /usr/local/bin/setup-bridge.sh

# Create systemd service for automatic startup
echo "🔧 Creating systemd services..."
cat > /etc/systemd/system/xbox360-gadget.service << 'EOF'
[Unit]
Description=Xbox 360 WiFi Adapter USB Gadget
After=network.target

[Service]
Type=oneshot
ExecStart=/usr/local/bin/xbox360-gadget.sh
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
EOF

cat > /etc/systemd/system/xbox360-bridge.service << 'EOF'
[Unit]
Description=Xbox 360 Network Bridge
After=xbox360-gadget.service
Requires=xbox360-gadget.service

[Service]
Type=oneshot
ExecStart=/usr/local/bin/setup-bridge.sh
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
EOF

# Enable services
systemctl daemon-reload
systemctl enable xbox360-gadget.service
systemctl enable xbox360-bridge.service

# Create validation script
echo "🧪 Creating validation scripts..."
cat > /usr/local/bin/validate-xbox360.sh << 'EOF'
#!/bin/bash
# Xbox 360 WiFi Emulator Validation Script

echo "🧪 Xbox 360 WiFi Emulator Validation"
echo "===================================="

# Check USB gadget is active
if lsusb | grep -q "045e:0292"; then
    echo "✅ USB gadget active (Xbox 360 WiFi Adapter detected)"
else
    echo "❌ USB gadget not detected"
    exit 1
fi

# Check network interfaces
if ip link show br0 >/dev/null 2>&1; then
    echo "✅ Bridge interface active"
else
    echo "❌ Bridge interface not found"
    exit 1
fi

# Check if gadget interface exists
if ip link show usb0 >/dev/null 2>&1; then
    echo "✅ USB gadget network interface active"
else
    echo "⚠️  USB gadget interface not connected (normal if Xbox not plugged in)"
fi

# Test internet connectivity
if ping -c 1 8.8.8.8 >/dev/null 2>&1; then
    echo "✅ Internet connectivity working"
else
    echo "❌ No internet connectivity"
    exit 1
fi

# Check services
if systemctl is-active --quiet xbox360-gadget.service; then
    echo "✅ Xbox 360 gadget service running"
else
    echo "❌ Xbox 360 gadget service not running"
    exit 1
fi

echo ""
echo "🎮 Setup complete! Connect Xbox 360 via USB-C cable"
echo "    Then configure network in Xbox 360 settings"
EOF

chmod +x /usr/local/bin/validate-xbox360.sh

echo ""
echo "🎮 Setup Complete!"
echo "=================="
echo ""
echo "✅ USB gadget mode configured"
echo "✅ Network bridge ready"
echo "✅ Services installed and enabled"
echo ""
echo "⚠️  REBOOT REQUIRED to activate USB gadget mode"
echo ""
echo "After reboot:"
echo "1. Run: sudo validate-xbox360.sh"
echo "2. Connect Xbox 360 via USB-C cable"
echo "3. Configure network in Xbox 360 settings"
echo ""
echo "Reboot now? (y/n)"
read -r response
if [[ "$response" =~ ^[Yy]$ ]]; then
    reboot
fi