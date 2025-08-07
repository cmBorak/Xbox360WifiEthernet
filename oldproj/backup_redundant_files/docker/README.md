# Xbox 360 WiFi Module Emulator - Docker Testing Environment

This Docker setup creates a containerized Raspberry Pi 4 environment for testing the Xbox 360 WiFi Module Emulator without needing real hardware.

## 🚀 Quick Start

### Option 1: Interactive Menu
```bash
./test_in_docker.sh
```

### Option 2: Direct Commands
```bash
# Build the environment
./test_in_docker.sh build

# Start the container
./test_in_docker.sh start

# Test the GUI installer
./test_in_docker.sh gui

# Test command-line installer  
./test_in_docker.sh install

# Check system status
./test_in_docker.sh status
```

## 🐳 What's Included

The Docker environment emulates:

- **Raspberry Pi 4 Model B** hardware identification
- **USB gadget controller** support (`/sys/class/udc/`)
- **Mock Xbox 360 adapter** detection (045e:02a8)
- **Systemd services** and proper init system
- **USB monitoring** capabilities (`usbmon`)
- **All required dependencies** pre-installed

## 🖥️ GUI Testing Options

### Linux (X11 Forwarding)
```bash
# Enable X11 forwarding
xhost +local:docker

# Run GUI installer
./test_in_docker.sh gui
```

### Windows/Mac (VNC Server)
```bash
# Start VNC server
./test_in_docker.sh vnc

# Access via web browser
open http://localhost:6080
# Password: xbox360
```

## 🧪 Testing Scenarios

### 1. Installation Testing
```bash
# Test GUI installer
./test_in_docker.sh gui

# Test automated installer
./test_in_docker.sh install

# Check results
./test_in_docker.sh status
```

### 2. System Status Testing
```bash
# Get interactive shell
./test_in_docker.sh shell

# Check system components
./system_status.sh

# Test service creation
sudo systemctl status xbox360-emulator
```

### 3. USB Protocol Testing
```bash
# Test USB capture tools
sudo ./quick_capture.sh

# Check mock Xbox adapter detection
lsusb | grep Xbox

# Test USB monitoring
ls -la /sys/kernel/debug/usb/usbmon/
```

## 📁 Container Structure

```
/opt/xbox360-emulator/          # Project files (mounted from host)
├── installer_ui.py             # GUI installer
├── install_fully_automated.sh  # Automated installer
├── system_status.sh            # Status checker
└── quick_capture.sh            # USB capture tool

/boot/                          # Mock Pi boot directory
├── config.txt                  # Pi configuration
└── cmdline.txt                 # Kernel command line

/sys/class/udc/                 # Mock USB Device Controllers
/sys/kernel/debug/usb/usbmon/   # USB monitoring interface
/proc/cpuinfo                   # Pi 4 hardware identification
```

## 🔧 Manual Container Management

```bash
# Build image manually
docker-compose -f docker/docker-compose.yml build

# Start container
docker-compose -f docker/docker-compose.yml up -d pi-emulator

# Get shell access
docker exec -it xbox360-pi-emulator bash

# Stop containers
docker-compose -f docker/docker-compose.yml down

# Clean up everything
docker-compose -f docker/docker-compose.yml down --rmi all --volumes
```

## 🎯 Testing Checklist

- [ ] **Container builds successfully**
- [ ] **Pi hardware emulation works** (`cat /proc/cpuinfo`)
- [ ] **USB gadget support detected** (`ls /sys/class/udc/`)
- [ ] **Xbox adapter mock works** (`lsusb | grep Xbox`)
- [ ] **GUI installer launches** (with X11 or VNC)
- [ ] **Installation completes** without errors
- [ ] **System status shows green** for all components
- [ ] **Service can be created** and managed
- [ ] **USB capture tools work** (mock data)

## 🚨 Troubleshooting

### Container Won't Start
```bash
# Check Docker status
sudo systemctl status docker

# Check build logs
docker-compose -f docker/docker-compose.yml logs pi-emulator
```

### GUI Won't Display
```bash
# Linux: Enable X11 forwarding
xhost +local:docker
export DISPLAY=:0

# Windows/Mac: Use VNC
./test_in_docker.sh vnc
# Then open http://localhost:6080
```

### Installation Fails
```bash
# Check container logs
docker logs xbox360-pi-emulator

# Get detailed shell access
docker exec -it xbox360-pi-emulator bash
sudo ./install_fully_automated.sh
```

This Docker environment provides a safe, reproducible way to test the Xbox 360 WiFi Module Emulator installation and functionality!