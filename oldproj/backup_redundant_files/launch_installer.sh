#!/bin/bash
# Xbox 360 WiFi Module Emulator - One-Click Launcher
# This script launches the GUI installer with proper sudo privileges

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo -e "${BLUE}🎮 Xbox 360 WiFi Module Emulator - Launcher${NC}"
echo "=============================================="

# Function to check if running in GUI environment
check_gui() {
    if [ -n "$DISPLAY" ] || [ -n "$WAYLAND_DISPLAY" ]; then
        return 0
    else
        return 1
    fi
}

# Function to install dependencies
install_deps() {
    echo "Installing required packages..."
    
    # Update package list
    if ! apt-get update -qq >/dev/null 2>&1; then
        echo -e "${YELLOW}⚠️  Package update failed, continuing...${NC}"
    fi
    
    # Install required packages
    PACKAGES=("python3" "python3-tk" "python3-pip" "policykit-1")
    
    for package in "${PACKAGES[@]}"; do
        if ! dpkg -l | grep -q "^ii.*$package "; then
            echo "Installing $package..."
            if apt-get install -y "$package" >/dev/null 2>&1; then
                echo -e "${GREEN}✅ $package installed${NC}"
            else
                echo -e "${RED}❌ Failed to install $package${NC}"
            fi
        fi
    done
}

# Function to create desktop shortcut
create_desktop_shortcut() {
    DESKTOP_FILE="$HOME/Desktop/Xbox360_Installer.desktop"
    
    cat > "$DESKTOP_FILE" << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=Xbox 360 WiFi Emulator Installer
Comment=Install Xbox 360 WiFi Module Emulator with GUI
Exec=bash -c 'cd "$SCRIPT_DIR" && ./launch_installer.sh'
Path=$SCRIPT_DIR
Icon=network-wireless
Terminal=true
Categories=System;Network;
StartupNotify=true
EOF
    
    chmod +x "$DESKTOP_FILE"
    echo -e "${GREEN}✅ Desktop shortcut created${NC}"
}

# Function to launch GUI with proper privileges
launch_gui() {
    cd "$SCRIPT_DIR"
    
    echo "Launching Xbox 360 WiFi Module Emulator GUI..."
    echo ""
    echo -e "${YELLOW}📋 The installer will request administrator privileges${NC}"
    echo -e "${YELLOW}   This is required for system installation${NC}"
    echo ""
    
    # Try different methods to run with elevated privileges
    if command -v pkexec >/dev/null 2>&1; then
        # Use pkexec (PolicyKit) - best for GUI
        echo "Using PolicyKit for authentication..."
        pkexec env DISPLAY="$DISPLAY" XAUTHORITY="$XAUTHORITY" python3 "$SCRIPT_DIR/installer_ui.py"
    elif command -v gksudo >/dev/null 2>&1; then
        # Use gksudo if available
        echo "Using gksudo for authentication..."
        gksudo python3 "$SCRIPT_DIR/installer_ui.py"
    elif command -v kdesu >/dev/null 2>&1; then
        # Use kdesu for KDE
        echo "Using kdesu for authentication..."
        kdesu python3 "$SCRIPT_DIR/installer_ui.py"
    else
        # Fallback to terminal sudo
        echo "Using terminal sudo for authentication..."
        echo -e "${YELLOW}⚠️  Please enter your password when prompted:${NC}"
        sudo python3 "$SCRIPT_DIR/installer_ui.py"
    fi
}

# Main execution
main() {
    # Check if installer files exist
    if [ ! -f "$SCRIPT_DIR/installer_ui.py" ]; then
        echo -e "${RED}❌ installer_ui.py not found in $SCRIPT_DIR${NC}"
        exit 1
    fi
    
    if [ ! -f "$SCRIPT_DIR/install_fully_automated.sh" ]; then
        echo -e "${RED}❌ install_fully_automated.sh not found in $SCRIPT_DIR${NC}"
        exit 1
    fi
    
    # Check if running as root (if so, no elevation needed)
    if [[ $EUID -eq 0 ]]; then
        echo -e "${GREEN}✅ Running as root${NC}"
        cd "$SCRIPT_DIR"
        python3 installer_ui.py
        exit 0
    fi
    
    # Install dependencies if needed (requires sudo)
    echo "Checking dependencies..."
    if ! python3 -c "import tkinter" 2>/dev/null; then
        echo -e "${YELLOW}⚠️  Missing dependencies, requesting sudo to install...${NC}"
        sudo bash -c "$(declare -f install_deps); install_deps"
    else
        echo -e "${GREEN}✅ Dependencies satisfied${NC}"
    fi
    
    # Create desktop shortcut if in GUI environment and desktop exists
    if check_gui && [ -d "$HOME/Desktop" ]; then
        if [ ! -f "$HOME/Desktop/Xbox360_Installer.desktop" ]; then
            echo "Creating desktop shortcut..."
            create_desktop_shortcut
        fi
    fi
    
    # Launch the GUI
    if check_gui; then
        launch_gui
    else
        echo -e "${RED}❌ No GUI environment detected${NC}"
        echo "Please run this in a desktop environment (X11/Wayland)"
        exit 1
    fi
}

# Run main function
main "$@"