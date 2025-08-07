# Xbox 360 WiFi Module Emulator - Troubleshooting Guide

## 🚨 Docker Issues - Try These First!

### **Option 1: Simple Docker Test (Recommended)**
```bash
# Linux/WSL
./test_simple.sh

# Windows  
TEST_SIMPLE.bat
```

### **Option 2: Local Testing (No Docker Required)**
```bash
python3 test_local.py
```

### **Option 3: Direct GUI Testing**
```bash
python3 installer_ui.py
```

## 🐳 Docker Build/Start Problems

### **Problem: "Docker build failed"**
**Solutions:**
```bash
# Check Docker daemon
sudo systemctl status docker
sudo systemctl start docker

# Check disk space
docker system df
docker system prune

# Try simple build
docker build -f docker/Dockerfile.simple -t xbox360-test .
```

### **Problem: "Permission denied"**
**Solutions:**
```bash
# Add user to docker group (then logout/login)
sudo usermod -aG docker $USER

# Or use sudo
sudo ./test_simple.sh
```

### **Problem: "Cannot connect to Docker daemon"**
**Solutions:**
```bash
# Start Docker service
sudo systemctl start docker

# Check Docker Desktop is running (Windows/Mac)
# Restart Docker Desktop if needed
```

## 🐍 Python/GUI Issues

### **Problem: "tkinter not found"**
**Solutions:**
```bash
# Ubuntu/Debian
sudo apt-get install python3-tk

# CentOS/RHEL
sudo yum install tkinter

# macOS
brew install python-tk
```

### **Problem: "GUI won't display"**
**Solutions:**
```bash
# Linux: Enable X11 forwarding
export DISPLAY=:0
xhost +local:docker

# WSL: Install VcXsrv or X410
# Windows: Use VNC option instead

# Test X11
xeyes  # Should show eyes following cursor
```

### **Problem: "Module import errors"**
**Solutions:**
```bash
# Check Python path
python3 -c "import sys; print('\n'.join(sys.path))"

# Install missing packages
pip3 install pyusb

# Run from correct directory
cd "/path/to/Xbox360WifiEthernet"
python3 installer_ui.py
```

## 🔧 Installation Script Issues

### **Problem: "Syntax errors in scripts"**
**Solutions:**
```bash
# Test all scripts
bash -n install_fully_automated.sh
bash -n launch_installer.sh
python3 -m py_compile installer_ui.py

# Run local test
python3 test_local.py
```

### **Problem: "Permission denied on scripts"**
**Solutions:**
```bash
# Make scripts executable
chmod +x *.sh
chmod +x test_local.py

# Check file permissions
ls -la *.sh
```

## 🎮 System-Specific Solutions

### **Windows Users:**
1. **Use WSL** for best compatibility:
   ```cmd
   wsl --install
   wsl bash -c "cd '/mnt/c/path/to/project' && ./test_simple.sh"
   ```

2. **Docker Desktop** must be running
3. **Use batch files**: `TEST_SIMPLE.bat`

### **Linux Users:**
1. **Install dependencies**:
   ```bash
   sudo apt-get update
   sudo apt-get install python3 python3-tk docker.io
   ```

2. **Start Docker**:
   ```bash
   sudo systemctl start docker
   sudo usermod -aG docker $USER
   ```

### **macOS Users:**
1. **Install via Homebrew**:
   ```bash
   brew install python3 python-tk docker
   ```

2. **Use Docker Desktop** for GUI apps

## 🧪 Testing Strategies

### **Strategy 1: Minimal Testing**
```bash
# Just test if components work
python3 test_local.py
```

### **Strategy 2: Docker Testing**
```bash
# Simple container test
./test_simple.sh build
./test_simple.sh run
```

### **Strategy 3: Direct Testing**
```bash
# Test GUI directly
python3 installer_ui.py

# Test installation script
sudo ./install_fully_automated.sh
```

## 🔍 Debug Information

### **Collect Debug Info:**
```bash
# System info
uname -a
python3 --version
docker --version

# Check files
ls -la *.sh *.py
file installer_ui.py

# Test basic functionality
python3 -c "import tkinter; print('GUI available')"
bash -c "echo 'Bash works'"
```

### **Check Logs:**
```bash
# Docker logs
docker logs xbox360-test 2>&1

# System logs
sudo journalctl -xe

# Check permissions
ls -la /opt/xbox360-emulator/ 2>/dev/null || echo "Not installed yet"
```

## 🎯 Quick Fixes

### **Can't build Docker?**
```bash
# Use the simple version
./test_simple.sh
```

### **GUI won't start?**
```bash
# Test without GUI
sudo ./install_fully_automated.sh
```

### **Nothing works?**
```bash
# Start with local test
python3 test_local.py
```

### **Still stuck?**
1. Run: `python3 test_local.py` and share the output
2. Check which specific error message you're getting
3. Try the simplest approach first: `python3 installer_ui.py`

## 📞 Common Error Messages

| Error | Solution |
|-------|----------|
| `Docker build failed` | `sudo systemctl start docker` |
| `tkinter not found` | `sudo apt-get install python3-tk` |
| `Permission denied` | `chmod +x *.sh` and `sudo` |
| `Module not found` | `cd` to correct directory |
| `Syntax error` | Run `python3 test_local.py` |
| `Display not found` | `export DISPLAY=:0` |

**The key is to start simple and work up to more complex solutions!** 🚀