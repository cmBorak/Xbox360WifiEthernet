#!/bin/bash
# SSH Setup Script for Raspberry Pi 4
# Enables SSH server and configures secure access

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🔐 SSH Setup for Raspberry Pi${NC}"
echo

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}❌ This script must be run as root${NC}"
    echo "Usage: sudo $0"
    exit 1
fi

echo -e "${YELLOW}📦 Installing SSH server...${NC}"

# Update package lists
apt-get update -qq

# Install OpenSSH server
apt-get install -y openssh-server

echo -e "${YELLOW}⚙️ Configuring SSH...${NC}"

# Backup original SSH config
cp /etc/ssh/sshd_config /etc/ssh/sshd_config.backup.$(date +%Y%m%d_%H%M%S)

# Configure SSH for security and usability
cat > /etc/ssh/sshd_config << 'EOF'
# SSH Configuration for Raspberry Pi
Port 22
Protocol 2

# Authentication
PermitRootLogin no
PasswordAuthentication yes
PubkeyAuthentication yes
AuthorizedKeysFile %h/.ssh/authorized_keys

# Security settings
MaxAuthTries 3
MaxSessions 2
ClientAliveInterval 300
ClientAliveCountMax 2

# Disable unused features
X11Forwarding yes
PrintMotd no
AcceptEnv LANG LC_*

# Subsystems
Subsystem sftp /usr/lib/openssh/sftp-server
EOF

echo -e "${YELLOW}🔧 Enabling SSH service...${NC}"

# Enable SSH service
systemctl enable ssh
systemctl restart ssh

# Enable SSH through systemctl if using systemd
if command -v raspi-config >/dev/null 2>&1; then
    echo -e "${YELLOW}🔓 Enabling SSH via raspi-config...${NC}"
    raspi-config nonint do_ssh 0
fi

# Add SSH to firewall if UFW is active
if command -v ufw >/dev/null 2>&1 && ufw status | grep -q "Status: active"; then
    echo -e "${YELLOW}🛡️ Configuring firewall...${NC}"
    ufw allow ssh
    ufw allow 22/tcp
fi

echo -e "${YELLOW}🔐 Setting up SSH keys directory for pi user...${NC}"

# Create SSH directory for pi user
if id "pi" &>/dev/null; then
    PI_HOME=$(eval echo ~pi)
    mkdir -p "$PI_HOME/.ssh"
    chmod 700 "$PI_HOME/.ssh"
    touch "$PI_HOME/.ssh/authorized_keys"
    chmod 600 "$PI_HOME/.ssh/authorized_keys"
    chown -R pi:pi "$PI_HOME/.ssh"
    echo -e "${GREEN}✅ SSH keys directory created for pi user${NC}"
fi

echo -e "${YELLOW}🧪 Testing SSH service...${NC}"

# Test SSH service
if systemctl is-active --quiet ssh; then
    echo -e "${GREEN}✅ SSH service is running${NC}"
else
    echo -e "${RED}❌ SSH service failed to start${NC}"
    systemctl status ssh --no-pager
    exit 1
fi

# Get Pi IP address
PI_IP=$(hostname -I | awk '{print $1}')

echo
echo -e "${GREEN}🎉 SSH Setup Complete!${NC}"
echo
echo -e "${BLUE}📋 Connection Information:${NC}"
echo -e "   🌐 IP Address: ${YELLOW}$PI_IP${NC}"
echo -e "   🔌 SSH Port: ${YELLOW}22${NC}"
echo -e "   👤 Username: ${YELLOW}pi${NC} (or your username)"
echo -e "   🔑 Password: ${YELLOW}[your pi password]${NC}"
echo
echo -e "${BLUE}💡 How to connect:${NC}"
echo -e "   From Windows: ${YELLOW}ssh pi@$PI_IP${NC}"
echo -e "   From Linux/Mac: ${YELLOW}ssh pi@$PI_IP${NC}"
echo -e "   With PuTTY: Host=${YELLOW}$PI_IP${NC}, Port=${YELLOW}22${NC}"
echo
echo -e "${BLUE}🔐 Optional: Set up SSH key authentication${NC}"
echo "   1. On your computer, generate keys:"
echo -e "      ${YELLOW}ssh-keygen -t rsa -b 4096${NC}"
echo "   2. Copy public key to Pi:"
echo -e "      ${YELLOW}ssh-copy-id pi@$PI_IP${NC}"
echo "   3. Or manually copy your public key to:"
echo -e "      ${YELLOW}$PI_HOME/.ssh/authorized_keys${NC}"
echo
echo -e "${BLUE}🛠️ Useful SSH commands:${NC}"
echo -e "   Check status: ${YELLOW}sudo systemctl status ssh${NC}"
echo -e "   Restart SSH: ${YELLOW}sudo systemctl restart ssh${NC}"
echo -e "   View SSH logs: ${YELLOW}sudo tail -f /var/log/auth.log${NC}"
echo
echo -e "${GREEN}🚀 SSH is ready! You can now connect remotely to your Pi.${NC}"