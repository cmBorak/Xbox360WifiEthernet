#!/bin/bash
# Xbox 360 WiFi Module Emulator - Installation Script
# Optimized for Pi OS Bullseye ARM64

set -e

echo "🎮 Xbox 360 WiFi Module Emulator - Installer"
echo "============================================="
echo "Optimized for Pi OS Bullseye ARM64"
echo ""

# Check if running as root
if [[ $EUID -eq 0 ]]; then
    echo "⚠️  Running as root. This is recommended for installation."
else
    echo "ℹ️  Not running as root. Some operations may require sudo."
fi

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not found"
    echo "   Install with: sudo apt install python3"
    exit 1
fi

echo "✅ Python 3 found: $(python3 --version)"

# Check for tkinter
if ! python3 -c "import tkinter" 2>/dev/null; then
    echo "⚠️  tkinter not found. Installing..."
    if command -v apt &> /dev/null; then
        sudo apt update
        sudo apt install -y python3-tk
    else
        echo "❌ Cannot install tkinter automatically. Please install python3-tk manually."
        exit 1
    fi
fi

echo "✅ tkinter available"

# Parse command line arguments
GUI_MODE=false
TEST_MODE=false
STATUS_MODE=false
DEV_MODE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --gui)
            GUI_MODE=true
            shift
            ;;
        --test)
            TEST_MODE=true
            shift
            ;;
        --status)
            STATUS_MODE=true
            shift
            ;;
        --dev)
            DEV_MODE=true
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [options]"
            echo "Options:"
            echo "  --gui     Launch GUI installer"
            echo "  --test    Run compatibility test"
            echo "  --status  Show system status"
            echo "  --dev     Development mode (use local directories)"
            echo "  --help    Show this help"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Check if installer.py exists
if [[ ! -f "installer.py" ]]; then
    echo "❌ installer.py not found in $SCRIPT_DIR"
    exit 1
fi

echo "✅ Found installer.py"

# Build command with flags
INSTALL_CMD="python3 installer.py"
if [[ "$DEV_MODE" == true ]]; then
    INSTALL_CMD="$INSTALL_CMD --dev"
fi

# Run appropriate mode
if [[ "$TEST_MODE" == true ]]; then
    echo ""
    echo "🧪 Running compatibility test..."
    python3 test.py
elif [[ "$STATUS_MODE" == true ]]; then
    echo ""
    echo "📊 Checking system status..."
    if [[ "$DEV_MODE" == true ]]; then
        python3 installer.py --status --dev
    else
        python3 installer.py --status
    fi
elif [[ "$GUI_MODE" == true ]]; then
    echo ""
    echo "🖥️  Launching GUI installer..."
    if [[ "$DEV_MODE" == true ]]; then
        python3 installer.py --gui --dev
    else
        python3 installer.py --gui
    fi
else
    echo ""
    if [[ "$DEV_MODE" == true ]]; then
        echo "🔧 Starting installation in development mode..."
        echo "   Using local directories instead of system paths"
    else
        echo "🚀 Starting installation..."
        echo "   Use --gui for graphical interface"
        echo "   Use --dev for development mode"
    fi
    echo "   Use --test to run compatibility test first"
    echo ""
    read -p "Continue with installation? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        eval "$INSTALL_CMD"
    else
        echo "Installation cancelled."
        exit 0
    fi
fi