#!/bin/bash
# Xbox 360 WiFi Module Emulator - Desktop App Setup
# Creates a one-click desktop application for Raspberry Pi

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Get current directory
CURRENT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo -e "${BLUE}🎮 Xbox 360 WiFi Module Emulator - Desktop App Setup${NC}"
echo "=================================================="

# Check if we're in a desktop environment
if [ -z "$DISPLAY" ] && [ -z "$WAYLAND_DISPLAY" ]; then
    echo -e "${YELLOW}⚠️  No desktop environment detected${NC}"
    echo "This script creates desktop shortcuts for GUI environments"
    echo "For command-line use, just run: ./install.sh"
    echo ""
    read -p "Continue anyway? (y/N): " -r
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 0
    fi
fi

# Check if installer.py exists
if [ ! -f "$CURRENT_DIR/installer.py" ]; then
    echo -e "${RED}❌ installer.py not found in current directory${NC}"
    echo "Make sure you're running this from the Xbox360WifiEthernet directory"
    exit 1
fi

echo -e "${GREEN}✅ Found installer.py${NC}"

# Create desktop file with correct path
DESKTOP_FILE="$CURRENT_DIR/Xbox360-Emulator.desktop"

cat > "$DESKTOP_FILE" << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=Xbox 360 WiFi Emulator
Comment=Install and manage Xbox 360 WiFi Module Emulator
Exec=bash -c 'cd "$CURRENT_DIR" && if command -v zenity >/dev/null 2>&1; then python3 installer.py || zenity --error --text="Installation failed. Check terminal for details."; else x-terminal-emulator -e "python3 installer.py; read -p \"Press Enter to close...\""; fi'
Path=$CURRENT_DIR
Icon=network-wireless
Terminal=false
Categories=System;Network;
StartupNotify=true

[Desktop Action Install]
Name=Install with Sudo
Exec=bash -c 'cd "$CURRENT_DIR" && if command -v pkexec >/dev/null 2>&1; then pkexec env DISPLAY=\$DISPLAY XAUTHORITY=\$XAUTHORITY python3 installer.py; else x-terminal-emulator -e "sudo python3 installer.py; read -p \"Press Enter to close...\""; fi'

[Desktop Action Status] 
Name=Check Status
Exec=bash -c 'cd "$CURRENT_DIR" && x-terminal-emulator -e "python3 installer.py --status; read -p \"Press Enter to close...\""'

[Desktop Action Test]
Name=Test System
Exec=bash -c 'cd "$CURRENT_DIR" && x-terminal-emulator -e "python3 test.py --quick; read -p \"Press Enter to close...\""'

[Desktop Action CLI]
Name=Command Line Install
Exec=bash -c 'cd "$CURRENT_DIR" && x-terminal-emulator -e "sudo python3 installer.py --cli; read -p \"Press Enter to close...\""'

Actions=Install;Status;Test;CLI;
EOF

# Make desktop file executable
chmod +x "$DESKTOP_FILE"
echo -e "${GREEN}✅ Created desktop file: $DESKTOP_FILE${NC}"

# Install to user desktop if it exists
USER_DESKTOP="$HOME/Desktop"
if [ -d "$USER_DESKTOP" ]; then
    cp "$DESKTOP_FILE" "$USER_DESKTOP/"
    chmod +x "$USER_DESKTOP/Xbox360-Emulator.desktop"
    echo -e "${GREEN}✅ Copied to desktop: $USER_DESKTOP/Xbox360-Emulator.desktop${NC}"
fi

# Install to applications menu if possible
APPLICATIONS_DIR="$HOME/.local/share/applications"
if [ -d "$APPLICATIONS_DIR" ] || mkdir -p "$APPLICATIONS_DIR" 2>/dev/null; then
    cp "$DESKTOP_FILE" "$APPLICATIONS_DIR/"
    echo -e "${GREEN}✅ Installed to applications menu${NC}"
    
    # Update desktop database if available
    if command -v update-desktop-database >/dev/null 2>&1; then
        update-desktop-database "$APPLICATIONS_DIR" 2>/dev/null || true
    fi
fi

# Create a simple GUI launcher script
GUI_LAUNCHER="$CURRENT_DIR/xbox360_gui.sh"
cat > "$GUI_LAUNCHER" << 'EOF'
#!/bin/bash
# Xbox 360 WiFi Module Emulator - Simple GUI Launcher

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colors for terminal output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}🎮 Xbox 360 WiFi Module Emulator${NC}"
echo "=================================="

# Check if installer exists
if [ ! -f "installer.py" ]; then
    if command -v zenity >/dev/null 2>&1; then
        zenity --error --text="installer.py not found in current directory"
    else
        echo -e "${RED}❌ installer.py not found${NC}"
        read -p "Press Enter to exit..."
    fi
    exit 1
fi

# Show menu if zenity is available
if command -v zenity >/dev/null 2>&1; then
    CHOICE=$(zenity --list --title="Xbox 360 WiFi Module Emulator" \
        --text="Choose an action:" \
        --column="Action" --column="Description" \
        "install" "Install Xbox 360 Emulator (needs sudo)" \
        "install-gui" "Install with GUI (recommended)" \
        "status" "Check system status" \
        "test" "Test system compatibility" \
        --width=500 --height=300)
    
    case "$CHOICE" in
        "install")
            if command -v pkexec >/dev/null 2>&1; then
                pkexec env DISPLAY=$DISPLAY XAUTHORITY=$XAUTHORITY python3 installer.py --cli
            else
                x-terminal-emulator -e "sudo python3 installer.py --cli; read -p 'Press Enter to close...'"
            fi
            ;;
        "install-gui")
            if command -v pkexec >/dev/null 2>&1; then
                pkexec env DISPLAY=$DISPLAY XAUTHORITY=$XAUTHORITY python3 installer.py
            else
                python3 installer.py || zenity --error --text="Installation failed. Try running with sudo."
            fi
            ;;
        "status")
            x-terminal-emulator -e "python3 installer.py --status; read -p 'Press Enter to close...'"
            ;;
        "test")
            x-terminal-emulator -e "python3 test.py --quick; read -p 'Press Enter to close...'"
            ;;
        *)
            exit 0
            ;;
    esac
else
    # Fallback to terminal menu
    echo ""
    echo "Choose an action:"
    echo "1) Install Xbox 360 Emulator (GUI)"
    echo "2) Install Xbox 360 Emulator (CLI)"  
    echo "3) Check system status"
    echo "4) Test system compatibility"
    echo "5) Exit"
    echo ""
    read -p "Enter choice (1-5): " choice
    
    case $choice in
        1)
            echo -e "${GREEN}Starting GUI installer...${NC}"
            python3 installer.py
            ;;
        2)
            echo -e "${GREEN}Starting CLI installer...${NC}"
            sudo python3 installer.py --cli
            ;;
        3)
            echo -e "${GREEN}Checking system status...${NC}"
            python3 installer.py --status
            read -p "Press Enter to continue..."
            ;;
        4)
            echo -e "${GREEN}Testing system...${NC}"
            python3 test.py --quick
            read -p "Press Enter to continue..."
            ;;
        5)
            exit 0
            ;;
        *)
            echo "Invalid choice"
            exit 1
            ;;
    esac
fi
EOF

chmod +x "$GUI_LAUNCHER"
echo -e "${GREEN}✅ Created GUI launcher: $GUI_LAUNCHER${NC}"

# Install dependencies for better desktop integration
echo ""
echo -e "${BLUE}📦 Installing desktop integration tools...${NC}"

# Check if we can install packages
if command -v apt-get >/dev/null 2>&1; then
    # Install zenity for GUI dialogs if not present
    if ! command -v zenity >/dev/null 2>&1; then
        echo "Installing zenity for GUI dialogs..."
        if sudo apt-get update -qq && sudo apt-get install -y zenity; then
            echo -e "${GREEN}✅ Zenity installed${NC}"
        else
            echo -e "${YELLOW}⚠️  Could not install zenity (GUI dialogs may not work)${NC}"
        fi
    else
        echo -e "${GREEN}✅ Zenity already installed${NC}"
    fi
    
    # Install policykit for GUI sudo if not present
    if ! command -v pkexec >/dev/null 2>&1; then
        echo "Installing policykit for GUI sudo..."
        if sudo apt-get install -y policykit-1; then
            echo -e "${GREEN}✅ PolicyKit installed${NC}"
        else
            echo -e "${YELLOW}⚠️  Could not install policykit (may need terminal sudo)${NC}"
        fi
    else
        echo -e "${GREEN}✅ PolicyKit already installed${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  Package manager not available, skipping dependency installation${NC}"
fi

echo ""
echo "=============================================="
echo -e "${GREEN}🎉 Desktop app setup complete!${NC}"
echo "=============================================="
echo ""
echo -e "${BLUE}📱 How to use:${NC}"
echo ""
echo "1. 🖱️  Double-click the desktop icon: Xbox360-Emulator"
echo "2. 📂 Or run the GUI launcher: ./xbox360_gui.sh"
echo "3. 🖥️  Or use the applications menu (look for 'Xbox 360 WiFi Emulator')"
echo ""
echo -e "${BLUE}🎯 Available actions:${NC}"
echo "• Install Emulator (with GUI or CLI)"
echo "• Check System Status"
echo "• Test System Compatibility"
echo "• Right-click for more options"
echo ""
echo -e "${YELLOW}💡 Tip: The desktop icon will show a menu with different options!${NC}"