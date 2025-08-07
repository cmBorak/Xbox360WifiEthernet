#!/bin/bash
# Install Scripts from GitHub Repository
# Downloads and runs the Xbox 360 emulation and xRDP fix scripts

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Repository information
GITHUB_REPO="cmBorak/Xbox360WifiEthernet"
GITHUB_BRANCH="main"
BASE_URL="https://raw.githubusercontent.com/$GITHUB_REPO/$GITHUB_BRANCH"

echo -e "${BLUE}🚀 Xbox 360 Emulation & xRDP Setup${NC}"
echo -e "${BLUE}Downloading from: https://github.com/$GITHUB_REPO${NC}"
echo

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}❌ This script must be run as root${NC}"
    echo "Usage: sudo $0"
    exit 1
fi

# Check internet connection
if ! ping -c 1 google.com &> /dev/null; then
    echo -e "${RED}❌ No internet connection${NC}"
    exit 1
fi

# Create temporary directory
TEMP_DIR=$(mktemp -d)
cd "$TEMP_DIR"

echo -e "${YELLOW}📥 Downloading installation scripts...${NC}"

# Download scripts
download_file() {
    local filename=$1
    local url="$BASE_URL/$filename"
    
    echo -e "   Downloading $filename..."
    if curl -fsSL "$url" -o "$filename"; then
        chmod +x "$filename"
        echo -e "   ${GREEN}✅ $filename downloaded${NC}"
    else
        echo -e "   ${RED}❌ Failed to download $filename${NC}"
        return 1
    fi
}

# Download all required scripts
download_file "one_click_install.sh" || exit 1
download_file "xrdp_quick_fix.sh" || exit 1
download_file "fix_xrdp.sh" || exit 1

echo
echo -e "${BLUE}📋 What would you like to install?${NC}"
echo
echo -e "${YELLOW}1)${NC} Xbox 360 Emulation System (complete automated testing & monitoring)"
echo -e "${YELLOW}2)${NC} xRDP Remote Desktop Fix (quick fix for common issues)"  
echo -e "${YELLOW}3)${NC} xRDP Remote Desktop Fix (comprehensive repair)"
echo -e "${YELLOW}4)${NC} Install Everything (Xbox 360 system + xRDP)"
echo -e "${YELLOW}5)${NC} Exit"
echo

read -p "Enter your choice (1-5): " choice

case $choice in
    1)
        echo -e "${GREEN}🎮 Installing Xbox 360 Emulation System...${NC}"
        ./one_click_install.sh
        ;;
    2)
        echo -e "${GREEN}🖥️ Running xRDP Quick Fix...${NC}"
        ./xrdp_quick_fix.sh
        ;;
    3)
        echo -e "${GREEN}🔧 Running xRDP Comprehensive Fix...${NC}"
        ./fix_xrdp.sh
        ;;
    4)
        echo -e "${GREEN}🚀 Installing Everything...${NC}"
        echo -e "${BLUE}Step 1/2: Installing Xbox 360 Emulation System${NC}"
        ./one_click_install.sh
        echo
        echo -e "${BLUE}Step 2/2: Setting up xRDP Remote Desktop${NC}"
        ./xrdp_quick_fix.sh
        ;;
    5)
        echo -e "${YELLOW}👋 Goodbye!${NC}"
        exit 0
        ;;
    *)
        echo -e "${RED}❌ Invalid choice${NC}"
        exit 1
        ;;
esac

# Cleanup
cd /
rm -rf "$TEMP_DIR"

echo
echo -e "${GREEN}✅ Installation completed!${NC}"

# Show connection information
PI_IP=$(hostname -I | awk '{print $1}')
echo
echo -e "${BLUE}📋 Your Pi Connection Information:${NC}"
echo -e "   🌐 IP Address: ${YELLOW}$PI_IP${NC}"
echo -e "   🎮 Xbox Dashboard: ${YELLOW}http://$PI_IP:8080${NC}"
echo -e "   🖥️ Remote Desktop: ${YELLOW}$PI_IP:3389${NC}"
echo
echo -e "${GREEN}🎉 Your Raspberry Pi 4 is ready to use!${NC}"