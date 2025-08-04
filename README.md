# Xbox 360 WiFi Module Emulator & USB Passthrough 🎮

Turn your **Raspberry Pi 4** into an Xbox 360 wireless adapter with **20x faster gigabit ethernet** OR use it as a **USB passthrough monitor** to sniff real Xbox adapter traffic.

## 🚀 **Quick Start - One Command Installation**

### **Linux/Raspberry Pi:**
```bash
./xbox360_gui.sh          # GUI launcher
./install.sh              # Legacy script
```

### **Windows:**
```powershell
.\xbox360.ps1             # PowerShell launcher
.\xbox360-admin.ps1       # Auto-elevating admin version
xbox360.bat               # Batch file launcher
```

### **Manual Installation:**
```bash
python3 installer.py      # Universal installer
```

## 🎯 **Two Operation Modes**

### **Mode 1: Xbox Adapter Emulation**
- Pi **emulates** the Xbox wireless adapter
- Xbox sees Pi as "wireless adapter" showing "PI-Net" network
- Traffic flows through Pi's gigabit ethernet (20x faster!)

### **Mode 2: USB Passthrough & Sniffing** 
- Pi acts as **USB passthrough** with real Xbox adapter
- **Captures all USB traffic** between Xbox and real adapter
- Perfect for **protocol analysis** and **reverse engineering**

## 📋 **What This Does**

- **Emulates Xbox 360 wireless adapter** via USB OTG gadget mode
- **USB passthrough monitoring** of real Xbox adapter traffic
- **Bookworm-compatible** configuration (Pi OS 12+)
- **Desktop capture directories** for easy file management
- **Comprehensive USB analysis tools** (tshark, wireshark, usbmon)
- **Cross-platform launchers** (Windows, Linux, Mac)
- **NetworkManager bypass** for stable USB gadget networking

## 🎯 **System Requirements**

- **Raspberry Pi 4** (recommended) with Pi OS Bookworm or compatible Linux
- **Python 3.8+** with tkinter for GUI
- **USB-C cable** to connect Pi to Xbox 360 (OTG mode)
- **Xbox 360 Wireless Adapter** (for passthrough mode)
- **Ethernet connection** on Pi for internet access
- **Root/sudo access** for installation

## ✨ **Bookworm OS Compatibility**

This installer **automatically detects** and configures:
- **Boot file locations**: `/boot/firmware/` (Bookworm) vs `/boot/` (legacy)
- **NetworkManager bypass**: Prevents USB gadget interface conflicts
- **OTG mode configuration**: `dr_mode=otg` for both host and device capabilities

## 🔧 **Installation Options**

### **Option 1: GUI Installer (Recommended)**
```bash
# Auto-detects best interface (GUI or CLI)
python3 installer.py

# Force GUI mode
python3 installer.py --gui

# Force CLI mode  
python3 installer.py --cli
```

### **Option 2: One-Click Launchers**
```bash
# Linux/Mac
./install.sh

# Windows (WSL)
xbox360.bat
```

### **Option 3: Test First**
```bash
# Quick compatibility test
python3 test.py

# Comprehensive test with Docker
python3 test.py --comprehensive
```

## 📊 **Installation Process**

The installer handles **10 automated steps**:

1. ✅ **System Check** - Verify Pi, Python, permissions
2. ✅ **Install Dependencies** - Python packages, build tools, USB libraries  
3. ✅ **Configure USB Gadget** - DWC2 overlay, kernel modules
4. ✅ **Install Emulator** - Copy source files, create directories
5. ✅ **Setup USB Sniffing** - usbmon, capture tools
6. ✅ **Create Services** - systemd service for autostart
7. ✅ **Configure Networking** - Bridge setup, virtual wireless
8. ✅ **Create Helper Scripts** - Status checking, USB capture
9. ✅ **Test Installation** - Verify all components work
10. ✅ **Finalize Setup** - Permissions, completion marker

## 🎮 **How It Works**

### **Normal Xbox 360 Wireless Adapter:**
```
Xbox 360 ←─ 54Mbps WiFi ─→ Router ←─ Internet
```

### **Pi WiFi Module Emulator:**
```
Xbox 360 ←─ USB ─→ Pi 4 ←─ Gigabit Ethernet ─→ Router ←─ Internet
           (thinks it's wireless)    (20x faster!)
```

## 🕵️ **USB Passthrough & Protocol Capture**

### **Setup USB Passthrough:**
```bash
# Configure system for passthrough mode
sudo python3 start_passthrough.py --setup

# Check passthrough status
sudo python3 start_passthrough.py --status
```

### **Capture Real Xbox Adapter Traffic:**
```bash
# Start live capture with Xbox adapter plugged into Pi
sudo python3 usb_passthrough.py

# Analyze captured traffic
python3 analyze_usb_capture.py ~/Desktop/captures/passthrough/xbox_adapter_*.pcap
```

### **Manage Capture Files:**
```bash
# List all captures
python3 manage_captures.py --list

# Copy to USB drive
python3 manage_captures.py --copy-usb

# Create archive
python3 manage_captures.py --archive
```

**📁 Capture Location:** `~/Desktop/captures/` (organized by type)

## 📊 **System Status & Management**

### **Check System Status:**
```bash
# Quick status check
python3 installer.py --status

# Detailed system information
./system_status.py
```

### **Service Management:**
```bash
# Start emulator service
sudo systemctl start xbox360-emulator

# Stop emulator service
sudo systemctl stop xbox360-emulator

# Check service status
sudo systemctl status xbox360-emulator

# View logs
sudo journalctl -u xbox360-emulator -f
```

## 🔧 **After Installation**

1. **Reboot Required** - USB gadget mode needs DWC2 at boot
2. **Connect Xbox 360** - Use USB cable (Pi to Xbox)
3. **Xbox detects "wireless adapter"** - Should appear in network settings
4. **Scan for networks** - Xbox will see "PI-Net" as available network
5. **Connect to PI-Net** - Traffic flows through Pi's ethernet

## 🧪 **Testing & Development**

### **Quick Compatibility Test:**
```bash
python3 test.py --quick
```

### **Comprehensive Testing:**
```bash
python3 test.py --comprehensive
```

### **Test Specific Components:**
```bash
python3 test.py --system    # System requirements only
python3 test.py --docker    # Docker environment only
```

## 📁 **Project Structure**

```
Xbox360WifiEthernet/
├── installer.py              # 🎯 Universal installer (GUI + CLI)
│
├── 🚀 Cross-Platform Launchers
├── install.sh                # 🐧 Linux/Mac launcher  
├── xbox360_gui.sh            # 🖥️ Linux GUI launcher
├── xbox360.ps1               # 🪟 Windows PowerShell launcher
├── xbox360-admin.ps1         # 🛡️ Windows admin launcher
├── xbox360.bat               # 🪟 Windows batch launcher
│
├── 🧪 Testing & Management
├── test.py                   # 🧪 Universal testing script
├── system_status.py          # 📊 System status checker
├── manage_captures.py        # 📁 Capture file management
│
├── 🕵️ USB Passthrough Tools
├── usb_passthrough.py        # 📡 USB traffic capture
├── analyze_usb_capture.py    # 🔍 Traffic analysis
├── start_passthrough.py      # 🔧 Passthrough setup helper
│
├── src/                      # 📦 Source code
│   ├── xbox360_emulator.py   # Main emulator
│   ├── xbox_functionfs.py    # FunctionFS USB implementation
│   ├── xbox_auth.py          # Xbox authentication (XSM3)
│   ├── virtual_wireless.py   # Virtual wireless networking
│   └── xbox_capture_analyzer.py # Protocol analysis
│
├── captures/                 # 📁 Symlink to ~/Desktop/captures/
│   ├── passthrough/          # USB passthrough captures
│   ├── enumeration/          # Device enumeration logs
│   ├── authentication/       # Auth protocol captures
│   └── analysis/             # Processed analysis files
│
└── 📚 Documentation
    ├── README.md             # This file
    ├── WINDOWS_USERS.md      # Windows-specific guide
    └── setup_desktop_app.sh  # Desktop integration
```

## 🚨 **Troubleshooting**

### **DWC2 Module Not Loading:**
- **"dwc2 module not found"** → Run `sudo python3 fix_dwc2.py` for comprehensive fix
- **"No USB Device Controllers"** → Check `ls /sys/class/udc/` after reboot
- **Bookworm DWC2 issues** → Auto-fixed with proper `/boot/firmware/` configuration

### **Bookworm OS Issues:**
- **"Config files not found"** → Installer auto-detects `/boot/firmware/` vs `/boot/`
- **"USB gadget not working"** → NetworkManager bypass created automatically
- **"dwc2 overlay fails"** → OTG mode (`dr_mode=otg`) configured for compatibility

### **Windows Launcher Issues:**
- **"Installation failed: must run as root"** → Use `xbox360-admin.ps1` for auto-elevation
- **WSL path errors** → Launchers automatically convert Windows paths to WSL paths
- **PowerShell execution policy** → Run `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`

### **USB Passthrough Issues:**
- **"Xbox adapter not found"** → Check with `lsusb | grep 045e`
- **"usbip daemon failed"** → Run `sudo python3 start_passthrough.py --setup`
- **"Capture files empty"** → Verify usbmon module loaded: `lsmod | grep usbmon`

### **Installation Issues:**
- **"Permission denied"** → Use `sudo python3 installer.py`
- **"Python not found"** → Install Python 3.8+
- **"tkinter not found"** → `sudo apt-get install python3-tk`

### **Capture File Management:**
- **Files not in Desktop** → Check with `python3 manage_captures.py --info`
- **Can't copy to USB** → Use `python3 manage_captures.py --copy-usb /path/to/usb`
- **Archive creation fails** → Ensure sufficient disk space

### **Get Help:**
```bash
# Fix DWC2 module loading issues
sudo python3 fix_dwc2.py

# Debug DWC2 status (run on Pi)
python3 debug_dwc2.py

# Comprehensive system check
python3 test.py

# USB passthrough status
sudo python3 start_passthrough.py --status

# View logs
sudo journalctl -u xbox360-emulator -f
```

## 🔬 **Technical Details**

### **USB OTG Configuration:**
- **Mode:** OTG (`dr_mode=otg`) for both host and device capabilities
- **Vendor ID:** 045E (Microsoft)  
- **Product ID:** 02A8 (Xbox 360 Wireless Adapter)
- **Protocol:** FunctionFS with vendor-specific control transfers
- **Authentication:** Xbox Security Method 3 (XSM3)

### **Bookworm Compatibility:**
- **Boot Config:** Auto-detects `/boot/firmware/` (Bookworm) vs `/boot/` (legacy)
- **NetworkManager:** Bypassed via `/etc/network/interfaces.d/usb0`
- **Systemd Network:** Backup configuration in `/etc/systemd/network/`

### **USB Passthrough Architecture:**
- **USBIP:** USB over IP for device forwarding
- **usbmon:** Kernel USB traffic monitoring  
- **tcpdump/tshark:** Packet capture and analysis
- **Capture Format:** PCAP files compatible with Wireshark

### **Virtual Wireless (Emulation Mode):**
- **Network Name:** PI-Net
- **Connection Type:** Virtual (USB traffic, not actual WiFi)
- **IP Assignment:** 192.168.4.1 (Pi), dynamic for Xbox
- **Traffic Routing:** USB → Pi ethernet → internet

### **Performance:**
- **Original adapter:** 54 Mbps WiFi
- **Pi emulator:** 1000 Mbps ethernet (20x faster!)
- **Passthrough:** Captures at USB 2.0 speeds (480 Mbps)

## 🎯 **Use Cases**

### **Emulation Mode:**
- **Faster Xbox Live** - 20x bandwidth improvement over WiFi
- **Stable connection** - No WiFi interference or dropout
- **LAN gaming** - Reliable wired connection for tournaments
- **Legacy system support** - Keep old Xbox 360s online

### **Passthrough Mode:**
- **Protocol reverse engineering** - Capture real Xbox adapter communication
- **Security research** - Analyze XSM3 authentication protocols
- **Hardware analysis** - Understand Xbox wireless adapter behavior
- **Educational purposes** - Learn USB device communication patterns

## 📜 **License & Credits**

This project emulates Xbox 360 hardware for educational and compatibility purposes.

- **Xbox 360 Protocol Research:** [oct0xor.github.io](https://oct0xor.github.io/2017/05/03/xsm3/)
- **USB-Sniffify:** [blegas78/usb-sniffify](https://github.com/blegas78/usb-sniffify)
- **Linux USB Gadget Framework:** libcomposite, FunctionFS

## 🤝 **Contributing**

1. **Test the installer:** `python3 test.py`
2. **Report issues:** Include output from test.py
3. **Capture protocols:** Help analyze Xbox 360 authentication
4. **Improve documentation:** Fix errors, add examples

## 🆕 **Recent Updates (v2.0)**

- **✅ Raspberry Pi OS Bookworm support** - Auto-detects boot config paths
- **✅ USB passthrough mode** - Capture real Xbox adapter traffic  
- **✅ Desktop capture directories** - Files saved to `~/Desktop/captures/`
- **✅ Cross-platform launchers** - Windows PowerShell, Linux GUI, batch files
- **✅ NetworkManager bypass** - Stable USB gadget networking
- **✅ OTG mode configuration** - Supports both host and device modes
- **✅ Comprehensive capture tools** - tshark, wireshark, usbmon integration
- **✅ Auto-elevating Windows scripts** - No manual admin mode required

---

**🎮 Ready to emulate Xbox adapters or sniff real traffic? Choose your launcher and get started!**

**Emulation:** `./xbox360_gui.sh` or `.\xbox360.ps1`  
**Passthrough:** `sudo python3 start_passthrough.py --setup`