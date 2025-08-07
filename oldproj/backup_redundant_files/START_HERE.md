# Xbox 360 WiFi Module Emulator - Start Here! 🎮

## 🚀 **One-Click Installation Options**

Choose the method that works best for your system:

### **Option 1: Linux/Raspberry Pi (Recommended)**
**Just double-click this file:**
```
launch_installer.sh
```
- ✅ Opens GUI installer automatically
- ✅ Requests sudo privileges as needed  
- ✅ Creates desktop shortcut
- ✅ Progress bars and live status

### **Option 2: Windows (WSL)**
**Just double-click this file:**
```
INSTALL_XBOX360.bat
```
- ✅ Automatically launches WSL
- ✅ Runs Linux installer in WSL environment
- ✅ No Linux commands needed

### **Option 3: Desktop Shortcut (Linux)**
After running once, you'll have a desktop shortcut:
```
Xbox360_Installer.desktop
```
- ✅ Double-click to launch
- ✅ No terminal needed
- ✅ Automatic privilege elevation

## 📋 **What the Installer Does**

The GUI installer provides:

1. **🚀 Install Button** - Complete automated installation
2. **📊 Check Status** - Monitor all system components  
3. **🕵️ USB Capture** - Capture Xbox 360 protocol data
4. **🔄 Reboot** - Restart system to activate features

## ⚡ **Installation Progress**

You'll see real-time progress through 12 steps:
1. ✅ Checking system requirements
2. ✅ Updating system packages
3. ✅ Configuring USB gadget support
4. ✅ Creating directories
5. ✅ Installing Python dependencies
6. ✅ Installing emulator source files
7. ✅ Creating systemd service
8. ✅ Installing USB sniffing tools
9. ✅ Creating helper scripts
10. ✅ Testing installation
11. ✅ Creating documentation
12. ✅ Finalizing installation

## 🔧 **After Installation**

1. **System automatically reboots** to activate USB gadget mode
2. **Connect Pi to Xbox 360** via USB cable
3. **Xbox detects wireless adapter** 
4. **Use GUI to check status** and capture protocols

## 🆘 **Need Help?**

- **GUI won't start?** Try: `sudo python3 installer_ui.py`
- **Missing dependencies?** The launcher installs them automatically
- **Installation fails?** Check the colored output log in the GUI
- **Xbox not detecting?** Use the Status button to check all components

## 📁 **Files Overview**

- `launch_installer.sh` - **Main launcher (Linux/Pi)**
- `INSTALL_XBOX360.bat` - **Main launcher (Windows)**
- `installer_ui.py` - GUI installer application
- `install_fully_automated.sh` - Backend installation script
- `Xbox360_Installer.desktop` - Desktop shortcut (auto-created)

---

**🎯 Just double-click `launch_installer.sh` (Linux) or `INSTALL_XBOX360.bat` (Windows) to get started!**