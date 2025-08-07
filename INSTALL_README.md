# 🚀 One-Click Xbox 360 Emulation System Installer

## ⚡ **Zero-Configuration Installation for Raspberry Pi 4**

This installer sets up a **complete automated testing and monitoring system** for your Xbox 360 emulation project with **zero user interaction required**.

---

## 🎯 **One Command Install**

```bash
# Download and run the installer
curl -fsSL https://raw.githubusercontent.com/yourusername/Xbox360WifiEthernet/main/one_click_install.sh | sudo bash
```

**OR** if you have the files locally:

```bash
sudo ./one_click_install.sh
```

**That's it!** Everything else is automatic.

---

## 🏗️ **What Gets Installed (Automatically)**

### **✅ System Components**
- **Docker & Docker Compose** - Containerized application environment
- **Python 3.11 Environment** - Complete testing framework
- **System Services** - Auto-starting monitoring and dashboard
- **Web Dashboard** - Real-time monitoring interface
- **Automated Testing** - Continuous validation system
- **Health Monitoring** - 5-minute system health checks
- **Log Management** - Automatic cleanup and rotation

### **✅ Directory Structure**
```
/opt/xbox360-emulator/          # Main installation
├── xbox360_emulator.py         # Core application
├── monitoring_daemon.py        # Health monitoring
├── web_dashboard.py            # Web interface  
├── tests/                      # Test suite
├── venv/                       # Python environment
└── manage.sh                   # Management commands

/var/lib/xbox360-emulator/      # Data directory
├── test-results/               # Test outputs
├── logs/                       # Application logs
├── debug-data/                 # Debug information
└── backup/                     # System backups

/var/log/xbox360-emulator/      # System logs
```

### **✅ System Services**
- **xbox360-monitoring** - Background health monitoring
- **xbox360-dashboard** - Web dashboard service
- **Automatic startup** - Services start on boot
- **Service recovery** - Auto-restart on failure

---

## 📊 **Instant Access After Install**

### **Web Dashboard**
- **URL**: `http://PI_IP_ADDRESS:8080`
- **Features**: Real-time monitoring, test results, system metrics
- **Auto-refresh**: Updates every 30 seconds

### **Management Commands**
```bash
# Check system status
sudo /opt/xbox360-emulator/manage.sh status

# View live logs  
sudo /opt/xbox360-emulator/manage.sh logs

# Run tests manually
sudo /opt/xbox360-emulator/manage.sh test

# Restart services
sudo /opt/xbox360-emulator/manage.sh restart

# Get dashboard URL
sudo /opt/xbox360-emulator/manage.sh dashboard
```

---

## ⚙️ **System Requirements**

### **Hardware Requirements**
- ✅ **Raspberry Pi 4** (any RAM size, 4GB+ recommended)
- ✅ **32GB+ SD Card** (Class 10 or better)
- ✅ **Internet Connection** (for installation)
- ✅ **USB Cable** (for Xbox 360 emulation)

### **Software Requirements**
- ✅ **Raspberry Pi OS** (Bullseye or newer)
- ✅ **Root/sudo access** (required for installation)
- ✅ **SSH enabled** (optional, for remote management)

---

## 🔧 **Advanced Configuration (Optional)**

### **Environment Variables**
You can customize the installation by setting environment variables:

```bash
# Custom installation directory
export INSTALL_DIR="/home/pi/xbox360-emulator"

# Custom dashboard port
export DASHBOARD_PORT="9090"

# Skip auto-start of services
export AUTO_START="false"

# Run the installer
sudo -E ./one_click_install.sh
```

### **Available Options**
```bash
PROJECT_NAME="xbox360-emulator"           # Project name
INSTALL_DIR="/opt/xbox360-emulator"       # Installation directory  
DATA_DIR="/var/lib/xbox360-emulator"     # Data directory
LOG_DIR="/var/log/xbox360-emulator"      # Log directory
DASHBOARD_PORT="8080"                     # Web dashboard port
AUTO_START="true"                         # Auto-start services
```

---

## 📈 **What Happens During Installation**

### **Phase 1: System Validation** *(30 seconds)*
- ✅ Verify Raspberry Pi 4 hardware
- ✅ Check system resources (memory, disk, internet)
- ✅ Validate root permissions

### **Phase 2: Package Installation** *(3-5 minutes)*
- ✅ Install Docker and Docker Compose
- ✅ Install Python development environment
- ✅ Install system utilities and dependencies

### **Phase 3: Application Setup** *(2-3 minutes)*
- ✅ Create directory structure
- ✅ Generate application files
- ✅ Setup Python virtual environment
- ✅ Install Python packages

### **Phase 4: Service Configuration** *(1-2 minutes)*
- ✅ Create systemd services
- ✅ Configure system settings
- ✅ Setup log rotation
- ✅ Configure permissions

### **Phase 5: Service Startup** *(30 seconds)*
- ✅ Start monitoring daemon  
- ✅ Start web dashboard
- ✅ Run initial system tests
- ✅ Verify service health

**Total Installation Time: 7-10 minutes**

---

## 🚨 **Troubleshooting**

### **Installation Issues**

**"Not running on Raspberry Pi 4"**
```bash
# Check your hardware
cat /proc/cpuinfo | grep "Raspberry Pi"
```

**"Insufficient memory/disk space"**
```bash
# Check resources
free -h
df -h
```

**"No internet connectivity"**
```bash
# Test internet
ping -c 3 google.com
```

### **Service Issues**

**Services won't start:**
```bash
# Check service status
sudo systemctl status xbox360-monitoring xbox360-dashboard

# View detailed logs
sudo journalctl -u xbox360-monitoring -u xbox360-dashboard

# Restart services
sudo /opt/xbox360-emulator/manage.sh restart
```

**Dashboard not accessible:**
```bash
# Check if service is running
sudo systemctl status xbox360-dashboard

# Check if port is open
sudo netstat -tlnp | grep 8080

# Get Pi IP address
hostname -I
```

### **Recovery Commands**

**Complete service restart:**
```bash
sudo systemctl restart xbox360-monitoring xbox360-dashboard
```

**Reinstall services:**
```bash
sudo systemctl disable xbox360-monitoring xbox360-dashboard
sudo ./one_click_install.sh
```

**View installation log:**
```bash
cat /tmp/xbox360_install.log
```

---

## 🎉 **Post-Installation**

### **Immediate Next Steps**
1. **Visit Dashboard**: Open `http://PI_IP:8080` in your browser
2. **Check Status**: Run `sudo /opt/xbox360-emulator/manage.sh status`
3. **Run Tests**: Execute `sudo /opt/xbox360-emulator/manage.sh test`
4. **Read Guide**: Check `/opt/xbox360-emulator/QUICK_START.md`

### **What's Running Automatically**
- 🔄 **Health checks every 5 minutes**
- 📊 **Real-time web dashboard**
- 🧪 **Automated testing framework**
- 📝 **Automatic log management**
- 🔧 **Service monitoring and recovery**

### **System Monitoring**
The system now automatically:
- ✅ Monitors CPU, memory, temperature
- ✅ Runs basic functionality tests
- ✅ Detects and logs system issues
- ✅ Provides web-based status dashboard
- ✅ Rotates and manages log files

---

## 🆘 **Getting Help**

### **Log Files**
- Installation: `/tmp/xbox360_install.log`
- System logs: `sudo journalctl -u xbox360-*`
- Application logs: `/var/log/xbox360-emulator/`

### **Status Commands**
```bash
# Complete system overview
sudo /opt/xbox360-emulator/manage.sh status

# Service health check
sudo systemctl status xbox360-monitoring xbox360-dashboard

# Resource usage
htop
```

### **Common Solutions**
- **Reboot the Pi**: `sudo reboot`
- **Restart services**: `sudo /opt/xbox360-emulator/manage.sh restart`
- **Check dashboard**: Visit `http://PI_IP:8080`
- **Run tests**: `sudo /opt/xbox360-emulator/manage.sh test`

---

## 🔮 **What You Get**

After running the one-click installer, you have:

- ✅ **Complete Xbox 360 emulation testing system**
- ✅ **Web-based monitoring dashboard**
- ✅ **Automated health monitoring**
- ✅ **Continuous testing framework**
- ✅ **Professional logging and management**
- ✅ **Zero-maintenance operation**

**Your Xbox 360 emulation project will never silently fail again!** 🚀

---

*Installation tested on Raspberry Pi 4 with Raspberry Pi OS Bullseye/Bookworm*