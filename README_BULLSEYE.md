# 🎮 Xbox 360 WiFi Module Emulator - Pi OS Bullseye ARM64

**Complete rewrite optimized for Raspberry Pi OS Bullseye 64-bit**

## 🎯 Overview

This project emulates an Xbox 360 WiFi module using a Raspberry Pi, allowing wireless connectivity for original Xbox 360 consoles. This version has been completely rewritten and optimized for **Pi OS Bullseye ARM64** to address all compatibility issues with the newer operating system.

## ✅ System Requirements

### **Required:**
- **Raspberry Pi 4 Model B** (recommended) or newer
- **Pi OS Bullseye ARM64** (64-bit version)
- **2GB+ RAM** (4GB+ recommended)
- **MicroSD card** (16GB+ Class 10)
- **USB-C power supply** (official Pi power supply recommended)

### **Verified Compatible:**
- Pi OS Bullseye 64-bit (2023-05-03 or newer)
- Kernel 5.15+ with ARM64 architecture
- Python 3.9+ with tkinter support

## 🚀 Quick Start

### **🎯 One-Click Setup (Recommended)**
```bash
cd Xbox360WifiEthernet
python3 one_click_bullseye_setup.py
```
**Or use the shell version:**
```bash
./setup_bullseye.sh
```

### **📋 Manual Setup (Advanced)**
If you prefer to run each step manually:

1. **Validate Your System**
   ```bash
   python3 validate_bullseye_system.py
   ```

2. **Run Comprehensive Fix (if needed)**
   ```bash
   python3 comprehensive_bullseye_fix.py
   ```

3. **Setup Desktop Integration**
   ```bash
   python3 fix_desktop_paths_bullseye.py
   ```

4. **Install Xbox 360 Emulator**
   ```bash
   python3 installer.py
   ```

5. **Reboot (Required)**
   ```bash
   sudo reboot
   ```

6. **Launch Emulator**
   ```bash
   ./launch_bullseye_comprehensive.sh
   ```

## 📁 Project Structure

### **Core Scripts**
- `installer.py` - Main installer optimized for Bullseye ARM64
- `comprehensive_bullseye_fix.py` - Comprehensive system fix for Bullseye
- `validate_bullseye_system.py` - System validation and testing
- `fix_desktop_paths_bullseye.py` - Desktop integration for Bullseye

### **One-Click Setup**
- `one_click_bullseye_setup.py` - Automated Python setup with GUI support
- `setup_bullseye.sh` - Simple shell script for automated setup

### **Desktop Integration**
- `Xbox360-Emulator-Bullseye.desktop` - GUI launcher
- `Xbox360-Emulator-Bullseye-Terminal.desktop` - Terminal launcher  
- `Xbox360-Emulator-Bullseye-Comprehensive.desktop` - Full launcher
- `Xbox360-Emulator-Bullseye-Fix.desktop` - Fix script launcher

### **Launch Scripts**
- `launch_bullseye_comprehensive.sh` - Comprehensive launcher with diagnostics

### **Legacy Files**
- `oldproj/` - Contains previous version files for reference

## 🔧 Bullseye-Specific Optimizations

### **Boot Configuration**
- **Correct paths**: Uses `/boot/config.txt` (not `/boot/firmware/`)
- **DWC2 optimization**: Enhanced overlay configuration for ARM64
- **Memory tuning**: Optimized GPU memory split for gadget mode
- **OTG mode**: Proper dual-role device configuration

### **Python Environment** 
- **System packages**: Uses apt packages instead of pip
- **No virtual env conflicts**: Handles externally-managed-environment
- **Bullseye libraries**: Compatible with Bullseye Python 3.9+

### **USB Gadget Configuration**
- **Bullseye modules**: Optimized module loading sequence
- **initramfs integration**: Early boot module loading
- **Network configuration**: SystemD and NetworkManager integration

### **Desktop Integration**
- **Bullseye paths**: Uses correct desktop directory structure
- **Multiple launchers**: GUI, terminal, comprehensive, and fix options
- **Proper permissions**: Automatic executable permissions

## 🔍 Validation and Testing

### **System Validation**
The validation script checks:
- ✅ Pi OS Bullseye version confirmation
- ✅ ARM64 architecture verification  
- ✅ Raspberry Pi hardware detection
- ✅ Python environment compatibility
- ✅ Boot configuration correctness
- ✅ USB module availability
- ✅ Network configuration status
- ✅ Project files integrity

### **Validation Results**
- **EXCELLENT**: Fully optimized system
- **GOOD**: Ready with minor optimizations available
- **NEEDS_FIXES**: Run comprehensive fix script
- **CRITICAL**: Multiple issues requiring attention

## 🛠️ Troubleshooting

### **Common Issues and Solutions**

#### **"externally-managed-environment" Error**
```bash
# Run the comprehensive fix
python3 comprehensive_bullseye_fix.py
```

#### **DWC2 Module Not Loading**
```bash
# Check module status
lsmod | grep dwc2

# If missing, run fix and reboot
python3 comprehensive_bullseye_fix.py
sudo reboot
```

#### **Desktop Files Not Working**
```bash
# Fix desktop integration
python3 fix_desktop_paths_bullseye.py

# Make executable manually if needed
chmod +x ~/desktop/Xbox360-Emulator-Bullseye*.desktop
```

#### **USB Device Controllers Missing**
```bash
# Check controllers
ls /sys/class/udc/

# If empty, reboot after running fix
python3 comprehensive_bullseye_fix.py
sudo reboot
```

### **Validation Commands**
```bash
# Quick system check
python3 installer.py --status

# Comprehensive validation
python3 validate_bullseye_system.py

# Check Bullseye version
grep bullseye /etc/os-release

# Check ARM64 architecture  
uname -m  # Should show: aarch64

# Check USB modules
lsmod | grep -E '(dwc2|libcomposite)'
```

## 📂 Logging System

All operations are logged to timestamped files in the debuglogs directory:

### **Log Locations**
- `~/desktop/debuglogs/` (primary)
- `~/Desktop/debuglogs/` (fallback)

### **Log Types**
- `bullseye_install_YYYYMMDD_HHMMSS.log` - Installation logs
- `bullseye_comprehensive_fix_YYYYMMDD_HHMMSS.log` - Fix operation logs
- `bullseye_validation_YYYYMMDD_HHMMSS.log` - Validation results
- `bullseye_desktop_fix_YYYYMMDD_HHMMSS.log` - Desktop integration logs
- `bullseye_launch_YYYYMMDD_HHMMSS.log` - Launch session logs

## 🔄 Migration from Previous Versions

If upgrading from a previous version:

1. **Backup existing configuration**:
   ```bash
   sudo cp /boot/config.txt /boot/config.txt.backup
   ```

2. **Run system validation**:
   ```bash
   python3 validate_bullseye_system.py
   ```

3. **Apply Bullseye optimizations**:
   ```bash
   python3 comprehensive_bullseye_fix.py
   ```

4. **Update desktop integration**:
   ```bash
   python3 fix_desktop_paths_bullseye.py
   ```

5. **Reboot to apply changes**:
   ```bash
   sudo reboot
   ```

## 📋 Feature Differences from Previous Versions

### **New in Bullseye Version**
- ✨ Complete ARM64 optimization
- ✨ Bullseye-specific boot configuration
- ✨ Enhanced system validation
- ✨ Improved error handling and logging
- ✨ Multiple desktop launcher options
- ✨ Comprehensive fix automation
- ✨ Better Python environment handling

### **Removed/Changed**
- ❌ Bookworm `/boot/firmware/` paths
- ❌ Legacy 32-bit optimizations  
- ❌ pip-based dependency installation
- ❌ Manual configuration steps

## 🔐 Security Considerations

- **System packages**: Uses official Debian packages
- **No external downloads**: All dependencies from official repositories
- **Minimal privileges**: Runs with least required permissions
- **Sandboxed operation**: USB gadget mode isolation

## 🤝 Contributing

When contributing to the Bullseye version:

1. **Test on actual Bullseye ARM64** hardware
2. **Follow Bullseye conventions** (paths, packages, etc.)
3. **Update validation script** for new features
4. **Maintain logging standards** with comprehensive debugging
5. **Document ARM64-specific** optimizations

## 📝 License

This project is released under the MIT License. See LICENSE file for details.

## 🆘 Support

### **Before Asking for Help**
1. Run `python3 validate_bullseye_system.py`
2. Check logs in `~/desktop/debuglogs/`
3. Try `python3 comprehensive_bullseye_fix.py`
4. Verify you're running Pi OS Bullseye ARM64

### **Reporting Issues**
Include the following information:
- Pi model and OS version (`cat /etc/os-release`)
- Architecture (`uname -m`)
- Validation report output
- Relevant log files from debuglogs/

---

**🎮 Xbox 360 WiFi Module Emulator - Pi OS Bullseye ARM64 Edition**  
*Optimized for Raspberry Pi OS Bullseye 64-bit*