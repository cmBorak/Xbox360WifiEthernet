#!/bin/bash
# Xbox 360 WiFi Module Emulator - Simple One-Click GUI Launcher
# Double-click this file to launch the emulator installer

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colors for terminal output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Simple one-click launcher
echo -e "${BLUE}🎮 Xbox 360 WiFi Module Emulator - One-Click Launcher${NC}"
echo "====================================================="

# Check if installer exists
if [ ! -f "installer.py" ]; then
    echo -e "${RED}❌ installer.py not found${NC}"
    echo "Make sure you're running this from the Xbox360WifiEthernet directory"
    read -p "Press Enter to exit..."
    exit 1
fi

echo -e "${GREEN}✅ Starting Xbox 360 WiFi Module Emulator...${NC}"
echo ""

# Try GUI first, fall back to CLI if needed
if [ -n "$DISPLAY" ] || [ -n "$WAYLAND_DISPLAY" ]; then
    echo "🖥️  GUI environment detected, starting graphical installer..."
    
    # Check if we need sudo
    if [[ $EUID -eq 0 ]]; then
        # Already root
        python3 installer.py
    else
        # Try GUI sudo first
        if command -v pkexec >/dev/null 2>&1; then
            echo "🔐 Requesting administrator privileges..."
            pkexec env DISPLAY=$DISPLAY XAUTHORITY=$XAUTHORITY python3 installer.py
        else
            # Fallback to regular GUI
            python3 installer.py
            
            # If that fails, suggest sudo
            if [ $? -ne 0 ]; then
                echo ""
                echo -e "${YELLOW}⚠️  Installation may need administrator privileges${NC}"
                read -p "Run with sudo? (y/N): " -r
                if [[ $REPLY =~ ^[Yy]$ ]]; then
                    sudo python3 installer.py
                fi
            fi
        fi
    fi
else
    echo "💻 Terminal environment detected, starting CLI installer..."
    
    # Check if we need sudo
    if [[ $EUID -eq 0 ]]; then
        python3 installer.py --cli
    else
        echo "🔐 This installer needs administrator privileges"
        sudo python3 installer.py --cli
    fi
fi

echo ""
echo -e "${BLUE}🎯 Installation process completed${NC}"

# Keep window open if run from desktop
if [ -t 0 ]; then
    # Running from terminal
    echo "Press Ctrl+C to exit or Enter to run system status check..."
    read -r
    if [ $? -eq 0 ]; then
        python3 installer.py --status 2>/dev/null || echo "Status check not available"
    fi
else
    # Running from desktop, keep window open
    read -p "Press Enter to close..."
fi