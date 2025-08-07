#!/bin/bash
# Xbox 360 WiFi Module Emulator - Universal Launcher
# Replaces all previous installation scripts

set -e

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo -e "${BLUE}🎮 Xbox 360 WiFi Module Emulator${NC}"
echo "================================="

# Check if installer exists
if [ ! -f "$SCRIPT_DIR/installer.py" ]; then
    echo -e "${RED}❌ installer.py not found${NC}"
    exit 1
fi

# Check for Python 3
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 not found${NC}"
    echo "Please install Python 3 first"
    exit 1
fi

# Check if we need sudo
if [[ $EUID -ne 0 ]] && [[ "${1}" != "--test" ]] && [[ "${1}" != "--status" ]] && [[ "${1}" != "--capture" ]]; then
    echo -e "${YELLOW}🔐 This installer requires sudo privileges${NC}"
    exec sudo "$0" "$@"
fi

# Run the Python installer
echo -e "${GREEN}🚀 Starting installer...${NC}"
echo ""

cd "$SCRIPT_DIR"
python3 installer.py "$@"