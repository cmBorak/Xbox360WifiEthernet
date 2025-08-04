#!/bin/bash
# Launch Xbox 360 WiFi Module Emulator GUI Installer

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🎮 Xbox 360 WiFi Module Emulator - GUI Installer${NC}"
echo "=================================================="

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Check if Python3 and tkinter are available
echo "Checking requirements..."

if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python3 not found${NC}"
    echo "Installing Python3..."
    sudo apt-get update -qq
    sudo apt-get install -y python3 python3-pip python3-tk
fi

# Check for tkinter
if ! python3 -c "import tkinter" 2>/dev/null; then
    echo -e "${RED}❌ Python3-tkinter not found${NC}"
    echo "Installing Python3-tkinter..."
    sudo apt-get install -y python3-tk
fi

echo -e "${GREEN}✅ Requirements satisfied${NC}"

# Check if we need to run with sudo for installation features
if [[ $EUID -ne 0 ]]; then
    echo ""
    echo -e "${BLUE}ℹ️  For full functionality (installation), run with sudo:${NC}"
    echo "   sudo bash $0"
    echo "" 
    echo "Starting GUI without sudo (status/capture features limited)..."
    echo ""
fi

# Launch the GUI
echo "Launching installer GUI..."
cd "$SCRIPT_DIR"

if python3 installer_ui.py; then
    echo -e "${GREEN}✅ GUI installer closed normally${NC}"
else
    echo -e "${RED}❌ GUI installer encountered an error${NC}"
    exit 1
fi