#!/bin/bash
# Quick xRDP Fix for Common Issues
# Fast resolution of the most common xRDP problems

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🔧 Quick xRDP Fix for Raspberry Pi${NC}"
echo

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}❌ This script must be run as root${NC}"
    echo "Usage: sudo $0"
    exit 1
fi

echo -e "${YELLOW}🔍 Diagnosing xRDP issues...${NC}"

# Quick diagnosis
if ! dpkg -l | grep -q xrdp; then
    echo -e "${YELLOW}📦 Installing xRDP...${NC}"
    apt-get update -qq
    apt-get install -y xrdp
fi

# Stop conflicting services
echo -e "${YELLOW}🛑 Stopping conflicting services...${NC}"
systemctl stop vncserver-x11-serviced 2>/dev/null || true
systemctl disable vncserver-x11-serviced 2>/dev/null || true

# Fix most common configuration issue
echo -e "${YELLOW}⚙️ Fixing configuration...${NC}"

# Create proper startwm.sh
cat > /etc/xrdp/startwm.sh << 'EOF'
#!/bin/sh
if test -r /etc/profile; then
    . /etc/profile
fi

export XDG_CURRENT_DESKTOP=LXDE
export XDG_SESSION_DESKTOP=LXDE
export XDG_SESSION_TYPE=x11

if command -v startlxde >/dev/null 2>&1; then
    exec startlxde
else
    exec /usr/bin/x-window-manager
fi
EOF

chmod +x /etc/xrdp/startwm.sh

# Fix permissions
echo -e "${YELLOW}🔐 Fixing permissions...${NC}"
usermod -a -G ssl-cert xrdp
usermod -a -G video pi
usermod -a -G audio pi

# Configure xRDP for console session (most common fix)
echo -e "${YELLOW}🖥️ Configuring console session...${NC}"
sed -i 's/port=ask-1/port=-1/' /etc/xrdp/xrdp.ini 2>/dev/null || true

# Restart services
echo -e "${YELLOW}🔄 Restarting xRDP...${NC}"
systemctl enable xrdp
systemctl restart xrdp

# Wait and test
sleep 3

if systemctl is-active --quiet xrdp; then
    PI_IP=$(hostname -I | awk '{print $1}')
    echo
    echo -e "${GREEN}✅ xRDP Fixed Successfully!${NC}"
    echo
    echo -e "${BLUE}📋 Connection Details:${NC}"
    echo -e "   🌐 IP Address: ${YELLOW}$PI_IP${NC}"
    echo -e "   🔌 Port: ${YELLOW}3389${NC}"
    echo -e "   👤 Username: ${YELLOW}pi${NC}"
    echo -e "   🔑 Password: ${YELLOW}[your pi password]${NC}"
    echo
    echo -e "${BLUE}💡 Connection Instructions:${NC}"
    echo "   1. Open Remote Desktop Connection"
    echo "   2. Enter: $PI_IP"
    echo "   3. Login with pi username and password"
    echo
    echo -e "${GREEN}🎉 You can now connect to your Pi via RDP!${NC}"
else
    echo -e "${RED}❌ xRDP failed to start${NC}"
    echo "Run the comprehensive fix: sudo ./fix_xrdp.sh"
fi