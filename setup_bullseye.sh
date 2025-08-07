#!/bin/bash
# Xbox 360 WiFi Module Emulator - One-Click Bullseye Setup Script
# Simple shell wrapper for the complete setup process

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Function to print colored output
print_step() {
    echo -e "${BLUE}[$(date '+%H:%M:%S')] $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${CYAN}ℹ️ $1${NC}"
}

# Banner
echo -e "${CYAN}"
echo "🎮 Xbox 360 WiFi Module Emulator - One-Click Bullseye Setup"
echo "═══════════════════════════════════════════════════════════"
echo -e "${NC}"

print_info "This script automates the complete setup process:"
echo "  1. System validation"
echo "  2. Apply Bullseye fixes"
echo "  3. Desktop integration"
echo "  4. Install emulator"
echo "  5. Reboot prompt"
echo

# Check if we're in the right directory
if [[ ! -f "installer.py" ]] || [[ ! -f "comprehensive_bullseye_fix.py" ]]; then
    print_error "Required files not found!"
    print_error "Make sure you're in the Xbox360WifiEthernet directory"
    exit 1
fi

# Check for Python
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 not found!"
    print_error "Please install Python 3: sudo apt install python3"
    exit 1
fi

# Check OS version
if [[ -f /etc/os-release ]]; then
    if ! grep -qi "bullseye" /etc/os-release; then
        print_warning "This script is optimized for Pi OS Bullseye"
        print_warning "Current OS may not be fully supported"
        read -p "Continue anyway? [y/N]: " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            print_info "Setup cancelled"
            exit 0
        fi
    fi
else
    print_warning "Could not detect OS version"
    read -p "Continue anyway? [y/N]: " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_info "Setup cancelled"
        exit 0
    fi
fi

# Confirmation prompt
echo -e "${YELLOW}"
echo "⚠️  IMPORTANT:"
echo "   • This process takes 10-15 minutes"
echo "   • Your Pi will need to reboot at the end"
echo "   • Internet connection required"
echo "   • sudo privileges needed"
echo -e "${NC}"

read -p "🚀 Ready to start the automated setup? [Y/n]: " -n 1 -r
echo
if [[ $REPLY =~ ^[Nn]$ ]]; then
    print_info "Setup cancelled"
    exit 0
fi

# Setup logging
LOG_DIR="$HOME/desktop/debuglogs"
if [[ ! -d "$HOME/desktop" ]]; then
    LOG_DIR="$HOME/Desktop/debuglogs"
fi
mkdir -p "$LOG_DIR"

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_FILE="$LOG_DIR/one_click_shell_setup_$TIMESTAMP.log"

echo "🎮 Xbox 360 WiFi Emulator - One-Click Shell Setup" > "$LOG_FILE"
echo "Started: $(date)" >> "$LOG_FILE"
echo "=========================================" >> "$LOG_FILE"

print_info "Setup log: $LOG_FILE"
echo

# Function to run a step and handle errors
run_step() {
    local step_num=$1
    local step_name="$2"
    local command="$3"
    
    print_step "[$step_num/5] $step_name"
    echo "[$step_num/5] $step_name - $(date)" >> "$LOG_FILE"
    echo "Command: $command" >> "$LOG_FILE"
    
    if eval "$command" 2>&1 | tee -a "$LOG_FILE"; then
        print_success "$step_name completed"
        echo "✅ $step_name completed - $(date)" >> "$LOG_FILE"
        echo "" >> "$LOG_FILE"
        return 0
    else
        print_error "$step_name failed"
        echo "❌ $step_name failed - $(date)" >> "$LOG_FILE"
        echo "" >> "$LOG_FILE"
        
        read -p "Continue with remaining steps? [y/N]: " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            print_warning "Continuing despite failure"
            return 0
        else
            print_error "Setup stopped"
            return 1
        fi
    fi
}

# Run the setup workflow
echo -e "${CYAN}🚀 Starting automated setup...${NC}"
echo

# Step 1: Validate system
if ! run_step 1 "System Validation" "python3 validate_bullseye_system.py"; then
    exit 1
fi

# Step 2: Apply fixes
if ! run_step 2 "Apply Bullseye Fixes" "python3 comprehensive_bullseye_fix.py"; then
    exit 1
fi

# Step 3: Desktop integration
if ! run_step 3 "Desktop Integration" "python3 fix_desktop_paths_bullseye.py"; then
    exit 1
fi

# Step 4: Install emulator
if ! run_step 4 "Install Xbox Emulator" "python3 installer.py"; then
    exit 1
fi

# Step 5: Reboot prompt
print_step "[5/5] Reboot Prompt"
echo "[5/5] Reboot Prompt - $(date)" >> "$LOG_FILE"

print_success "Installation complete!"
print_warning "A reboot is required for USB gadget functionality"

echo -e "${YELLOW}"
echo "🔄 REBOOT REQUIRED"
echo "=================="
echo "Installation is complete, but a reboot is required for"
echo "USB gadget functionality to work properly."
echo -e "${NC}"

read -p "Reboot now? [Y/n]: " -n 1 -r
echo

if [[ ! $REPLY =~ ^[Nn]$ ]]; then
    print_step "Rebooting system now..."
    echo "Rebooting system - $(date)" >> "$LOG_FILE"
    sudo reboot
else
    print_warning "Reboot postponed - remember to reboot manually"
    echo "Reboot postponed - $(date)" >> "$LOG_FILE"
fi

# Completion message
echo -e "${GREEN}"
echo "🎉 Xbox 360 WiFi Emulator Setup Complete!"
echo "═══════════════════════════════════════════"
echo -e "${NC}"

print_info "Setup log saved to: $LOG_FILE"
echo

print_info "After reboot, you can launch the emulator using:"
echo "  • Double-click desktop files, or"
echo "  • Run: ./launch_bullseye_comprehensive.sh"
echo

print_info "Desktop files created:"
echo "  • Xbox360-Emulator-Bullseye.desktop (GUI)"
echo "  • Xbox360-Emulator-Bullseye-Terminal.desktop (Terminal)"
echo "  • Xbox360-Emulator-Bullseye-Comprehensive.desktop (Full launcher)"
echo "  • Xbox360-Emulator-Bullseye-Fix.desktop (Fix issues)"
echo

print_info "Troubleshooting commands:"
echo "  • Check status: python3 installer.py --status"
echo "  • Validate system: python3 validate_bullseye_system.py"
echo "  • Apply fixes: python3 comprehensive_bullseye_fix.py"
echo

echo "✅ Setup complete! Reboot when ready to use the emulator."