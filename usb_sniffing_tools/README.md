# Xbox 360 USB Sniffing Tools

This directory contains tools for capturing and analyzing Xbox 360 wireless adapter USB communication.

## 📁 Directory Contents

- **usb-sniffify/**: Complete USB-Sniffify source code for Pi 4 USB interception
- **README.md**: This file

## 🚀 Quick Start

### Option 1: Full Setup (USB-Sniffify + usbmon)
```bash
# Run the complete setup (includes building USB-Sniffify)
sudo ../setup_usb_sniffing.sh
```

### Option 2: usbmon Only (More Reliable)
```bash
# Just set up usbmon - simpler and more stable
sudo ../setup_usbmon_only.sh
```

### Option 3: Manual USB-Sniffify Build
```bash
# Build just USB-Sniffify
sudo ../build_usb_sniffify.sh
```

## 🔧 Building USB-Sniffify

USB-Sniffify is included as source code and needs to be compiled:

```bash
cd usb-sniffify
mkdir -p build
cd build
cmake ..
make -j$(nproc)
```

Requirements:
- cmake
- build-essential
- libusb-1.0-dev
- pkg-config

## 🎮 Xbox 360 Capture Workflow

1. **Connect Hardware**:
   ```
   PC/Xbox ←─ USB ─→ [Pi 4 with USB-Sniffify] ←─ USB ─→ Xbox 360 Wireless Adapter
   ```

2. **Capture Scenarios**:
   - **Enumeration**: Device connection and USB descriptor exchange
   - **Authentication**: Xbox Security Method 3 (XSM3) protocol
   - **Network Operations**: Wireless scanning, connection, data transfer

3. **Analysis**: 
   - Extract exact USB descriptors
   - Decode authentication sequences
   - Understand network command protocols

## 📊 Expected Results

After successful captures, you'll have:
- Exact USB device descriptors from real Xbox 360 adapter
- Complete XSM3 authentication request/response sequences  
- Network scanning and connection command protocols
- Timing information for proper emulation

## 🛠️ Tools Available

After running setup scripts:
- `../capture_with_usbsniffify.sh`: USB-Sniffify capture helper
- `../capture_with_usbmon.sh`: usbmon capture helper
- `../analyze_capture.sh`: Capture analysis tool
- `../capture_xbox_protocol.sh`: Complete 3-phase capture workflow

## 💡 Tips

- **usbmon is more reliable** than USB-Sniffify for most use cases
- **USB-Sniffify** is better for real-time modification/injection
- Start with **usbmon** if you just need to capture protocol data
- Use **USB-Sniffify** if you need to modify USB traffic on-the-fly

## 🔍 Troubleshooting

### USB-Sniffify Build Issues
```bash
# Install missing dependencies
sudo apt-get install cmake build-essential libusb-1.0-dev pkg-config

# Check kernel modules
sudo modprobe raw_gadget
sudo modprobe libcomposite
```

### usbmon Issues
```bash
# Load usbmon module
sudo modprobe usbmon

# Mount debugfs if needed
sudo mount -t debugfs none /sys/kernel/debug
```

### General USB Issues
```bash
# List USB devices
lsusb | grep -i xbox

# Check USB permissions
ls -la /dev/bus/usb/*/*
```

## 📚 References

- [USB-Sniffify Repository](https://github.com/blegas78/usb-sniffify)
- [Linux usbmon Documentation](https://www.kernel.org/doc/html/latest/usb/usbmon.html)
- [Xbox Security Method 3 Research](https://oct0xor.github.io/2017/05/03/xsm3/)

This toolchain enables capturing the exact USB protocol from real Xbox 360 wireless adapters to perfect the FunctionFS emulation!