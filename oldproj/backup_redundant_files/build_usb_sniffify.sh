#!/bin/bash
# Build USB-Sniffify from included source

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}❌ ERROR:${NC} $1" >&2
}

warning() {
    echo -e "${YELLOW}⚠️  WARNING:${NC} $1"
}

success() {
    echo -e "${GREEN}✅${NC} $1"
}

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
USB_SNIFFIFY_DIR="$SCRIPT_DIR/usb_sniffing_tools/usb-sniffify"

echo "🔨 Building USB-Sniffify"
echo "======================="

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   error "This script should be run as root for proper permissions"
   echo "Usage: sudo $0"
   exit 1
fi

# Check if USB-Sniffify source exists
if [ ! -d "$USB_SNIFFIFY_DIR" ]; then
    error "USB-Sniffify source not found at: $USB_SNIFFIFY_DIR"
    error "Run: git clone https://github.com/blegas78/usb-sniffify.git $USB_SNIFFIFY_DIR"
    exit 1
fi

log "Found USB-Sniffify source at: $USB_SNIFFIFY_DIR"

# Install build dependencies
log "Installing build dependencies..."
apt-get update -qq
apt-get install -y build-essential cmake libusb-1.0-0-dev pkg-config

# Change to USB-Sniffify directory
cd "$USB_SNIFFIFY_DIR"

# Create build directory
log "Creating build directory..."
mkdir -p build
cd build

# Configure with CMake
log "Configuring with CMake..."
if cmake ..; then
    success "CMake configuration successful"
else
    error "CMake configuration failed"
    warning "Common issues:"
    warning "  - Missing libusb-1.0-dev package"
    warning "  - Missing cmake package"
    warning "  - Incompatible compiler version"
    exit 1
fi

# Build with make
log "Building USB-Sniffify..."
if make -j$(nproc); then
    success "USB-Sniffify built successfully"
else
    error "Build failed"
    warning "Check build output above for specific errors"
    exit 1
fi

# Check if executable was created
if [ -f "usb-sniffify" ]; then
    success "USB-Sniffify executable created: $(pwd)/usb-sniffify"
    
    # Make it executable
    chmod +x usb-sniffify
    
    # Check if it runs
    log "Testing USB-Sniffify..."
    if ./usb-sniffify --help >/dev/null 2>&1; then
        success "USB-Sniffify is working"
    else
        warning "USB-Sniffify built but may have runtime issues"
        warning "You may need to load kernel modules:"
        warning "  sudo modprobe raw_gadget"
        warning "  sudo modprobe libcomposite"
    fi
else
    error "USB-Sniffify executable not found after build"
    exit 1
fi

# Load required kernel modules
log "Loading required kernel modules..."
if modprobe raw_gadget 2>/dev/null; then
    success "raw_gadget module loaded"
else
    warning "Failed to load raw_gadget module"
    warning "Your kernel may not support raw_gadget"
    warning "USB-Sniffify may not work without this module"
fi

if modprobe libcomposite 2>/dev/null; then
    success "libcomposite module loaded"
else
    warning "Failed to load libcomposite module"
fi

echo ""
success "USB-Sniffify build complete!"
echo ""
echo "📁 Executable location: $USB_SNIFFIFY_DIR/build/usb-sniffify"
echo ""
echo "🚀 Test it with:"
echo "   cd $USB_SNIFFIFY_DIR/build"
echo "   sudo ./usb-sniffify --help"
echo ""
echo "🔧 For Xbox 360 capture:"
echo "   sudo ./usb-sniffify --mode capture --device xbox360"