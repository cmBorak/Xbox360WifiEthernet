#!/bin/bash
# Xbox 360 WiFi Module Emulator - Docker Testing Script
# Run the emulator in a containerized Raspberry Pi environment

set -e

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
PURPLE='\033[0;35m'
NC='\033[0m'

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo -e "${PURPLE}🐳 Xbox 360 WiFi Module Emulator - Docker Testing${NC}"
echo "=================================================="

# Function to check if Docker is installed
check_docker() {
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}❌ Docker not found${NC}"
        echo "Please install Docker first:"
        echo "  Linux: sudo apt-get install docker.io"
        echo "  Windows/Mac: Install Docker Desktop"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        echo -e "${RED}❌ Docker Compose not found${NC}"
        echo "Please install Docker Compose first:"
        echo "  Linux: sudo apt-get install docker-compose"
        echo "  Or use: pip install docker-compose"
        exit 1
    fi
    
    echo -e "${GREEN}✅ Docker and Docker Compose found${NC}"
}

# Function to set up X11 forwarding for GUI (Linux only)
setup_x11() {
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        echo "Setting up X11 forwarding for GUI..."
        xhost +local:docker 2>/dev/null || echo -e "${YELLOW}⚠️  X11 forwarding may not work${NC}"
        export DISPLAY=${DISPLAY:-:0}
        echo -e "${GREEN}✅ X11 forwarding configured${NC}"
    else
        echo -e "${YELLOW}⚠️  Not on Linux - GUI will use VNC (see option 3)${NC}"
    fi
}

# Function to build the Docker image
build_image() {
    echo -e "${BLUE}🔨 Building Raspberry Pi emulator Docker image...${NC}"
    
    cd "$SCRIPT_DIR"
    
    if docker-compose -f docker/docker-compose.yml build pi-emulator; then
        echo -e "${GREEN}✅ Docker image built successfully${NC}"
    else
        echo -e "${RED}❌ Failed to build Docker image${NC}"
        exit 1
    fi
}

# Function to run the emulator container
run_container() {
    echo -e "${BLUE}🚀 Starting Raspberry Pi emulator container...${NC}"
    
    cd "$SCRIPT_DIR"
    
    # Start the container
    docker-compose -f docker/docker-compose.yml up -d pi-emulator
    
    echo -e "${GREEN}✅ Container started${NC}"
    echo ""
    echo -e "${BLUE}📋 Container is ready for testing!${NC}"
    echo ""
    echo "Available testing options:"
    echo "  1. Interactive shell: docker exec -it xbox360-pi-emulator bash"
    echo "  2. Run GUI installer: docker exec -it xbox360-pi-emulator sudo python3 installer_ui.py"
    echo "  3. Test installation: docker exec -it xbox360-pi-emulator sudo ./launch_installer.sh"
    echo ""
}

# Function to run VNC server for GUI access
run_vnc() {
    echo -e "${BLUE}🖥️  Starting VNC server for GUI access...${NC}"
    
    cd "$SCRIPT_DIR"
    
    # Start VNC server
    docker-compose -f docker/docker-compose.yml --profile vnc up -d vnc-server
    
    echo -e "${GREEN}✅ VNC server started${NC}"
    echo ""
    echo -e "${BLUE}🌐 VNC Access:${NC}"
    echo "  Web browser: http://localhost:6080"
    echo "  VNC client: localhost:5900"
    echo "  Password: xbox360"
    echo ""
    echo "The Xbox 360 emulator files are in /opt/xbox360-emulator"
}

# Function to show testing menu
show_menu() {
    echo ""
    echo -e "${PURPLE}🧪 Testing Options:${NC}"
    echo "1. Build Docker image"
    echo "2. Start Pi emulator container" 
    echo "3. Start VNC server (for GUI on Windows/Mac)"
    echo "4. Run interactive shell in container"
    echo "5. Test GUI installer in container"
    echo "6. Test command-line installer"
    echo "7. Check system status in container"
    echo "8. Stop all containers"
    echo "9. Clean up (remove containers and images)"
    echo "0. Exit"
    echo ""
    read -p "Choose an option (0-9): " choice
    
    case $choice in
        1)
            build_image
            ;;
        2)
            run_container
            ;;
        3)
            run_vnc
            ;;
        4)
            echo -e "${BLUE}🖥️  Opening interactive shell...${NC}"
            docker exec -it xbox360-pi-emulator bash
            ;;
        5)
            echo -e "${BLUE}🎮 Testing GUI installer...${NC}"
            echo "Note: GUI may not work without X11 forwarding or VNC"
            docker exec -it xbox360-pi-emulator sudo python3 installer_ui.py
            ;;
        6)
            echo -e "${BLUE}📋 Testing command-line installer...${NC}"
            docker exec -it xbox360-pi-emulator sudo ./install_fully_automated.sh
            ;;
        7)
            echo -e "${BLUE}📊 Checking system status...${NC}"
            docker exec -it xbox360-pi-emulator ./system_status.sh
            ;;
        8)
            echo -e "${BLUE}🛑 Stopping containers...${NC}"
            docker-compose -f docker/docker-compose.yml down
            docker-compose -f docker/docker-compose.yml --profile vnc down
            echo -e "${GREEN}✅ Containers stopped${NC}"
            ;;
        9)
            echo -e "${BLUE}🧹 Cleaning up...${NC}"
            docker-compose -f docker/docker-compose.yml down --rmi all --volumes
            docker-compose -f docker/docker-compose.yml --profile vnc down --rmi all --volumes
            echo -e "${GREEN}✅ Cleanup complete${NC}"
            ;;
        0)
            echo -e "${GREEN}👋 Goodbye!${NC}"
            exit 0
            ;;
        *)
            echo -e "${RED}❌ Invalid option${NC}"
            ;;
    esac
}

# Function to show container status
show_status() {
    echo -e "${BLUE}📊 Container Status:${NC}"
    docker-compose -f docker/docker-compose.yml ps
    echo ""
}

# Main execution
main() {
    check_docker
    setup_x11
    
    echo ""
    echo -e "${GREEN}🎯 Docker Testing Environment Ready!${NC}"
    echo ""
    echo "This creates a containerized Raspberry Pi 4 environment for testing"
    echo "the Xbox 360 WiFi Module Emulator without needing real hardware."
    echo ""
    
    # Show current status
    show_status
    
    # Main menu loop
    while true; do
        show_menu
        echo ""
        read -p "Press Enter to continue..." 
        clear
        show_status
    done
}

# Handle script arguments
case "${1:-menu}" in
    "build")
        check_docker
        build_image
        ;;
    "start")
        check_docker
        setup_x11
        run_container
        ;;
    "vnc")
        check_docker
        run_vnc 
        ;;
    "shell")
        docker exec -it xbox360-pi-emulator bash
        ;;
    "gui")
        setup_x11
        docker exec -it xbox360-pi-emulator sudo python3 installer_ui.py
        ;;
    "install")
        docker exec -it xbox360-pi-emulator sudo ./install_fully_automated.sh
        ;;
    "status")
        docker exec -it xbox360-pi-emulator ./system_status.sh
        ;;
    "stop")
        docker-compose -f docker/docker-compose.yml down
        docker-compose -f docker/docker-compose.yml --profile vnc down
        ;;
    "clean")
        docker-compose -f docker/docker-compose.yml down --rmi all --volumes
        docker-compose -f docker/docker-compose.yml --profile vnc down --rmi all --volumes
        ;;
    *)
        main
        ;;
esac