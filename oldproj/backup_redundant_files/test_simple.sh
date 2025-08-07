#!/bin/bash
# Xbox 360 WiFi Module Emulator - Simple Docker Test
# Simplified version that should work reliably

set -e

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo -e "${BLUE}🐳 Xbox 360 WiFi Module Emulator - Simple Docker Test${NC}"
echo "===================================================="

# Check if Docker is available
check_docker() {
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}❌ Docker not found${NC}"
        echo "Please install Docker first"
        exit 1
    fi
    echo -e "${GREEN}✅ Docker found${NC}"
}

# Build the simple container
build_container() {
    echo -e "${BLUE}🔨 Building simple test container...${NC}"
    
    cd "$SCRIPT_DIR"
    
    if docker build -f docker/Dockerfile.simple -t xbox360-test .; then
        echo -e "${GREEN}✅ Container built successfully${NC}"
    else
        echo -e "${RED}❌ Container build failed${NC}"
        echo ""
        echo "Common issues:"
        echo "1. Docker daemon not running: sudo systemctl start docker"
        echo "2. Permission issues: sudo usermod -aG docker \$USER (then logout/login)"
        echo "3. Disk space: docker system prune"
        exit 1
    fi
}

# Run the container
run_container() {
    echo -e "${BLUE}🚀 Starting test container...${NC}"
    
    # Remove existing container if it exists
    docker rm -f xbox360-test 2>/dev/null || true
    
    # Run container with interactive terminal
    echo -e "${GREEN}✅ Container started${NC}"
    echo ""
    echo -e "${YELLOW}📋 You are now in the Xbox 360 emulator test environment!${NC}"
    echo ""
    echo "Available commands:"
    echo "  sudo python3 installer_ui.py          # GUI installer (if X11 works)"
    echo "  sudo ./install_fully_automated.sh     # Command-line installer"
    echo "  ./system_status.sh                    # Check system status"
    echo "  lsusb                                  # See mock Xbox adapter"
    echo "  cat /proc/cpuinfo                     # Check Pi emulation"
    echo "  exit                                  # Leave container"
    echo ""
    
    docker run -it --rm \
        --name xbox360-test \
        -v "$SCRIPT_DIR:/opt/xbox360-emulator" \
        -w /opt/xbox360-emulator \
        xbox360-test bash
}

# Test specific functionality
test_installer() {
    echo -e "${BLUE}🧪 Testing installer in container...${NC}"
    
    docker run --rm \
        -v "$SCRIPT_DIR:/opt/xbox360-emulator" \
        -w /opt/xbox360-emulator \
        xbox360-test \
        bash -c "echo 'Testing installer...' && sudo python3 -c 'import installer_ui; print(\"GUI installer module loads successfully\")'"
    
    echo -e "${GREEN}✅ Installer test completed${NC}"
}

# Show usage
show_usage() {
    echo "Usage: $0 [command]"
    echo ""
    echo "Commands:"
    echo "  build     - Build the Docker container"
    echo "  run       - Run interactive container"
    echo "  test      - Test installer functionality"
    echo "  shell     - Quick shell access"
    echo "  clean     - Remove container and image"
    echo ""
    echo "Examples:"
    echo "  $0 build && $0 run"
    echo "  $0 shell"
}

# Main logic
case "${1:-run}" in
    "build")
        check_docker
        build_container
        ;;
    "run")
        check_docker
        # Build if image doesn't exist
        if ! docker images xbox360-test | grep -q xbox360-test; then
            build_container
        fi
        run_container
        ;;
    "test")
        check_docker
        if ! docker images xbox360-test | grep -q xbox360-test; then
            build_container
        fi
        test_installer
        ;;
    "shell")
        check_docker
        if ! docker images xbox360-test | grep -q xbox360-test; then
            build_container
        fi
        echo -e "${BLUE}🐚 Quick shell access...${NC}"
        docker run -it --rm \
            -v "$SCRIPT_DIR:/opt/xbox360-emulator" \
            xbox360-test bash
        ;;
    "clean")
        echo -e "${BLUE}🧹 Cleaning up...${NC}"
        docker rm -f xbox360-test 2>/dev/null || true
        docker rmi -f xbox360-test 2>/dev/null || true
        echo -e "${GREEN}✅ Cleanup complete${NC}"
        ;;
    "help"|"-h"|"--help")
        show_usage
        ;;
    *)
        echo -e "${YELLOW}⚡ Quick start: Building and running container...${NC}"
        check_docker
        build_container
        run_container
        ;;
esac