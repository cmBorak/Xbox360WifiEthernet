# Xbox 360 USB Sniffing Guide

This guide explains how to use USB sniffing tools to capture and analyze real Xbox 360 wireless adapter communication for perfect protocol emulation.

## 🎯 Goals

1. **Capture Real Protocol**: Record authentic Xbox 360 wireless adapter communication
2. **Extract Authentication**: Get exact XSM3 authentication sequence
3. **Analyze Timing**: Understand request/response timing requirements
4. **Perfect Emulation**: Update our FunctionFS implementation with real data

## 🛠️ USB Sniffing Tools

### Option 1: USB-Sniffify (Recommended for Pi 4)
**Source**: https://github.com/blegas78/usb-sniffify

**Advantages**:
- Designed specifically for Raspberry Pi 4
- Real-time USB interception and logging
- Can act as USB proxy between Xbox and adapter
- Uses raw-gadget for precise control

**Setup**:
```bash
# Clone USB-Sniffify
git clone https://github.com/blegas78/usb-sniffify.git
cd usb-sniffify

# Install dependencies
sudo apt-get update
sudo apt-get install libusb-1.0-0-dev build-essential

# Compile
make

# Enable raw-gadget kernel module
sudo modprobe raw_gadget
```

### Option 2: Linux usbmon
**Built into Linux kernel**

**Advantages**:
- Already available on most Linux systems
- Lightweight, kernel-level capture
- Good for bulk analysis

**Setup**:
```bash
# Enable usbmon
sudo modprobe usbmon

# Find USB bus for Xbox adapter
lsusb | grep -i microsoft
# Example output: Bus 001 Device 005: ID 045e:02a8 Microsoft Corp.

# Capture traffic on specific bus (replace '1' with actual bus number)
sudo cat /sys/kernel/debug/usb/usbmon/1u > xbox_capture.log
```

### Option 3: Wireshark with USBPcap (Windows)
**For Windows analysis**

**Setup**:
1. Install Wireshark
2. Install USBPcap plugin
3. Capture USB traffic from Xbox 360 wireless adapter

## 📋 Capture Strategy

### Phase 1: Hardware Setup
```
PC/Xbox ←─ USB ─→ [Pi 4 with USB-Sniffify] ←─ USB ─→ Xbox 360 Wireless Adapter
                         ↓
                    Capture Logs
```

### Phase 2: Capture Scenarios

#### Scenario 1: Device Enumeration
```bash
# Start capture before connecting adapter
sudo ./usb-sniffify --mode capture --log enumeration.log

# Connect Xbox 360 wireless adapter
# Wait for enumeration to complete
# Stop capture
```

**Expected Data**:
- Device descriptor requests
- Configuration descriptor requests
- String descriptor requests
- Interface/endpoint setup

#### Scenario 2: Xbox Connection
```bash
# Start capture with adapter already connected
sudo ./usb-sniffify --mode capture --log xbox_connect.log

# Connect Xbox 360 console to adapter
# Wait for authentication to complete
# Stop capture when Xbox shows network settings
```

**Expected Data**:
- XSM3 authentication sequence
- Identification requests (0x01)
- Challenge requests (0x02)  
- Verification requests (0x04)
- Network scanning commands

#### Scenario 3: Network Operations
```bash
# Start capture with Xbox already authenticated
sudo ./usb-sniffify --mode capture --log network_ops.log

# On Xbox: Scan for wireless networks
# On Xbox: Connect to a network
# Generate some network traffic
# Disconnect from network
```

**Expected Data**:
- Network scan commands
- Connection establishment
- DHCP requests
- Network data packets
- Disconnection sequence

## 🔍 Analysis Process

### Step 1: Parse Capture Files
```bash
# Create analysis script
python3 xbox_capture_analyzer.py enumeration.log --output enumeration_report.md
python3 xbox_capture_analyzer.py xbox_connect.log --output auth_report.md
python3 xbox_capture_analyzer.py network_ops.log --output network_report.md
```

### Step 2: Extract Key Information

#### Device Descriptors
```python
# From enumeration capture
EXACT_DEVICE_DESCRIPTOR = {
    'idVendor': 0x045E,
    'idProduct': 0x02A8,
    'bcdDevice': 0x0202,  # Verify exact version
    'bDeviceClass': 0xFF,
    'bDeviceSubClass': 0x00,
    'bDeviceProtocol': 0x00,
    'bMaxPacketSize0': 64,  # Verify actual size
    'manufacturer': "Microsoft Corp.",
    'product': "Wireless Network Adapter Boot",
    'serial': "ACTUAL_SERIAL_FROM_CAPTURE"
}
```

#### Authentication Sequence
```python
# From Xbox connection capture
AUTHENTICATION_REQUESTS = [
    {
        'bmRequestType': 0xC0,  # Actual values from capture
        'bRequest': 0x01,       # Identification
        'wValue': 0x0000,
        'wIndex': 0x0000,
        'expected_response': b'\x41\x03\x62\x91\x33\x26\x08...'  # Real response
    },
    {
        'bmRequestType': 0xC0,
        'bRequest': 0x02,       # Challenge
        'wValue': 0x0000,
        'wIndex': 0x0000,
        'expected_response': b'\x...'  # Real challenge response
    }
    # ... more requests
]
```

#### Network Commands
```python
# From network operations capture
NETWORK_COMMANDS = {
    'scan_networks': {
        'request': b'\x...',
        'response_format': 'SSID_list_format'
    },
    'connect_network': {
        'request_format': 'connection_request_format',
        'response': 'connection_response'
    }
}
```

### Step 3: Validate Timing
```bash
# Extract timing information
grep -E "timestamp|delay" auth_report.md

# Look for:
# - Delay between requests
# - Response timeout values
# - Retry patterns
```

## 🔧 Implementation Updates

### Update USB Descriptors
```python
# In xbox_functionfs.py, update with exact captured values
def _create_usb_descriptors(self):
    device_desc = struct.pack('<BBHBBBBHHHBBBB',
        18,         # bLength
        1,          # bDescriptorType
        0x0200,     # bcdUSB
        0xFF,       # bDeviceClass (confirmed from capture)
        0x00,       # bDeviceSubClass (confirmed from capture)
        0x00,       # bDeviceProtocol (confirmed from capture)
        64,         # bMaxPacketSize0 (verify from capture)
        0x045E,     # idVendor
        0x02A8,     # idProduct  
        0x0202,     # bcdDevice (verify exact version from capture)
        1, 2, 3,    # String descriptor indices
        1           # bNumConfigurations
    )
```

### Update Authentication Handler
```python
# In xbox_auth.py, replace with captured authentication data
def handle_identification_request(self):
    # Use exact response from capture
    real_response = bytes.fromhex("41036291332608260033196341...")
    return self._create_packet(0x01, real_response)

def handle_challenge_request(self):
    # Use actual challenge algorithm from capture analysis
    real_challenge_response = self._calculate_real_challenge(self.device_serial)
    return self._create_packet(0x02, real_challenge_response)
```

### Update Network Emulation
```python
# In virtual_wireless.py, use real network command formats
def simulate_wireless_scan(self):
    # Use actual scan command format from capture
    real_scan_response = self._format_real_scan_response([
        {"ssid": "PI-Net", "signal": 95, "security": "WPA2-PSK"}
    ])
    return real_scan_response
```

## 📊 Expected Capture Results

### Device Enumeration (enumeration.log)
```
GET_DESCRIPTOR Device
GET_DESCRIPTOR Configuration
GET_DESCRIPTOR String[0] (Language)
GET_DESCRIPTOR String[1] (Manufacturer)
GET_DESCRIPTOR String[2] (Product)
GET_DESCRIPTOR String[3] (Serial)
SET_CONFIGURATION 1
```

### Xbox Authentication (xbox_connect.log)
```
VENDOR_REQUEST 0x01 (Identification)
  Response: Device serial, category, vendor ID
VENDOR_REQUEST 0x02 (Challenge)
  Response: Challenge response based on serial
VENDOR_REQUEST 0x04 (Verification)
  Response: Verification data with console key
Additional verification rounds...
```

### Network Operations (network_ops.log)
```
NETWORK_SCAN_REQUEST
  Response: Available networks list
NETWORK_CONNECT_REQUEST (SSID: "HomeNetwork")
  Response: Connection status
BULK_TRANSFER (Network data packets)
NETWORK_DISCONNECT_REQUEST
  Response: Disconnection confirmation
```

## 🎮 Testing Methodology

### Phase 1: Baseline Capture
1. Use real Xbox 360 wireless adapter
2. Connect to Xbox 360 console
3. Perform all network operations
4. Capture complete session

### Phase 2: Emulation Testing
1. Implement findings in our FunctionFS code
2. Test with Xbox 360 console
3. Compare behavior with baseline
4. Iterate until identical

### Phase 3: Validation
1. Side-by-side comparison
2. Timing analysis
3. Protocol compliance verification
4. Network functionality testing

## 🔍 Troubleshooting Captures

### USB-Sniffify Issues
```bash
# Check raw_gadget module
lsmod | grep raw_gadget

# Verify USB permissions
sudo chmod 666 /dev/bus/usb/*/*

# Test with simple device first
sudo ./usb-sniffify --test
```

### usbmon Issues
```bash
# Check if usbmon is available
ls /sys/kernel/debug/usb/usbmon/

# Fix permissions
sudo chmod +r /sys/kernel/debug/usb/usbmon/*

# Find correct bus number
cat /sys/kernel/debug/usb/devices | grep -A5 -B5 "045e"
```

### Analysis Script Issues
```bash
# Test with minimal capture
python3 xbox_capture_analyzer.py --help

# Debug parsing
python3 xbox_capture_analyzer.py sample.log --verbose
```

## 📈 Success Metrics

**Perfect Capture Includes**:
1. ✅ Complete device enumeration sequence
2. ✅ Full XSM3 authentication protocol  
3. ✅ Network scanning and connection commands
4. ✅ Bulk data transfer patterns
5. ✅ Error handling and retry logic

**Implementation Success**:
1. ✅ Xbox 360 recognizes our emulated adapter
2. ✅ Authentication passes without errors
3. ✅ Network scanning works identically
4. ✅ Connection establishment succeeds
5. ✅ Network traffic flows properly

## 🚀 Integration Plan

1. **Capture Phase**: Use USB-Sniffify to capture real adapter behavior
2. **Analysis Phase**: Extract protocol details with analyzer script
3. **Implementation Phase**: Update FunctionFS code with real data
4. **Testing Phase**: Validate against Xbox 360 console
5. **Refinement Phase**: Iterate based on testing results

This USB sniffing approach will give us the **exact protocol implementation** needed to create a perfect Xbox 360 wireless adapter emulator! 🕵️‍♂️📡