# Xbox 360 Authentication & FunctionFS Implementation

This document explains the Xbox 360 Security Method 3 (XSM3) authentication system and our FunctionFS-based implementation to bypass it.

## 🔐 Xbox Security Method 3 (XSM3) Overview

Based on research from https://oct0xor.github.io/2017/05/03/xsm3/, Xbox 360 wireless adapters use a complex authentication protocol:

### Authentication Stages
1. **Identification Protocol**: Device provides serial number, category, and vendor ID
2. **Challenge Protocol**: Xbox sends cryptographic challenge, device responds
3. **Verification Protocol**: Multiple verification steps using per-console keys

### Technical Details
- **USB Control Transfers**: Authentication uses vendor-specific USB control requests
- **Packet Structure**: 5-byte header + data payload + 1-byte XOR checksum
- **Encryption**: Uses device serial number with console-specific keys from key vault (KV)
- **Hardware Security**: Original adapters use Infineon TPM chips

### Why Standard USB Functions Fail
- **Fixed Interface Classes**: ConfigFS functions like NCM have fixed `bInterfaceClass` (cannot be set to 0xFF)
- **No Control Transfer Handling**: Standard functions don't handle vendor-specific control requests
- **Missing Authentication**: Xbox 360 won't recognize device without proper XSM3 authentication

## 🛠️ FunctionFS Solution

### Why FunctionFS?
FunctionFS allows implementing custom USB functions in userspace with:
- **Custom USB Descriptors**: Full control over device/interface descriptors
- **Control Transfer Handling**: Can process vendor-specific USB control requests
- **Vendor-Specific Class**: Can set `bInterfaceClass=0xFF` as required by Xbox

### Architecture
```
Xbox 360 ←─ USB Control Requests ─→ FunctionFS ep0 ←─→ Xbox Auth Handler
    │                                       │
    └─── Bulk Data Transfers ──→ FunctionFS ep1/ep2 ←─→ Network Handler
```

## 📋 Implementation Details

### USB Descriptors (Exact Match)
```python
# Device Descriptor
idVendor:     0x045E  # Microsoft Corporation  
idProduct:    0x02A8  # Xbox 360 Wireless Network Adapter
bcdDevice:    0x0202  # Device version 2.02
bDeviceClass: 0xFF    # Vendor-specific
bDeviceSubClass: 0x00
bDeviceProtocol: 0x00

# Interface Descriptor  
bInterfaceClass:    0xFF  # Vendor-specific (required for Xbox)
bInterfaceSubClass: 0x00
bInterfaceProtocol: 0x00
bNumEndpoints:      2     # IN and OUT bulk endpoints

# String Descriptors
Manufacturer: "Microsoft Corp."
Product:      "Wireless Network Adapter Boot" 
Serial:       Device-specific 16-hex-digit serial
```

### Authentication Protocol Implementation

#### 1. Identification Request (Vendor Request 0x01)
```python
def handle_identification_request(self):
    # Return device serial, category, vendor ID
    identification_data = struct.pack('<QHH', 
                                    self.device_serial,     # 8-byte serial
                                    0x01,                   # Category (wireless adapter)
                                    0x045E)                 # Vendor ID (Microsoft)
    return self._create_packet(0x01, identification_data)
```

#### 2. Challenge Request (Vendor Request 0x02)  
```python
def handle_challenge_request(self):
    # Generate challenge response based on device serial
    challenge_response = bytearray(16)
    serial_bytes = struct.pack('<Q', self.device_serial)
    
    # Obfuscate serial for challenge response
    for i in range(8):
        challenge_response[i] = serial_bytes[i]
        challenge_response[i + 8] = serial_bytes[i] ^ 0xAA
    
    return self._create_packet(0x02, bytes(challenge_response))
```

#### 3. Verification Request (Vendor Request 0x04)
```python
def handle_verification_request(self):
    # Create verification response (simplified bypass)
    verification_response = bytearray(32)
    serial_bytes = struct.pack('<Q', self.device_serial)
    
    # Mix serial with constants to create believable response
    for i in range(32):
        if i < 8:
            verification_response[i] = serial_bytes[i] ^ 0x55
        # ... additional obfuscation patterns
    
    return self._create_packet(0x04, bytes(verification_response))
```

### Packet Format
```
Packet Structure:
[Command:1][Header:4][Data:N][Checksum:1]

Checksum Calculation:
checksum = 0
for byte in packet[:-1]:  # All bytes except checksum
    checksum ^= byte
return checksum & 0xFF
```

### FunctionFS Integration

#### 1. Mount FunctionFS
```bash
mkdir -p /dev/xbox360_ffs
mount -t functionfs xbox360_ffs /dev/xbox360_ffs
```

#### 2. Initialize Endpoints
```python
# Write descriptors to ep0
os.write(self.ep0_fd, self.descriptors)
os.write(self.ep0_fd, self.strings)

# Open bulk endpoints
self.ep_in_fd = os.open("/dev/xbox360_ffs/ep1", os.O_RDWR)   # IN endpoint
self.ep_out_fd = os.open("/dev/xbox360_ffs/ep2", os.O_RDWR)  # OUT endpoint
```

#### 3. Handle Control Transfers
```python
def handle_control_transfers(self):
    while self.is_running:
        # Monitor ep0 for control requests
        ready, _, _ = select.select([self.ep0_fd], [], [], 1.0)
        
        if ready:
            # Read USB setup packet
            setup_data = os.read(self.ep0_fd, 8)
            bmRequestType, bRequest, wValue, wIndex, wLength = struct.unpack('<BBHHH', setup_data)
            
            # Handle Xbox authentication requests
            if (bmRequestType & 0x60) == 0x40:  # Vendor request
                response = self.auth_handler.handle_usb_control_transfer(
                    bmRequestType, bRequest, wValue, wIndex
                )
                if response:
                    os.write(self.ep0_fd, response)
```

## 🔧 Configuration & Setup

### ConfigFS Gadget Structure
```bash
cd /sys/kernel/config/usb_gadget/
mkdir xbox360
cd xbox360

# Set USB IDs (exact match for Xbox 360 wireless adapter)
echo 0x045E > idVendor
echo 0x02A8 > idProduct
echo 0x0202 > bcdDevice

# Create FunctionFS function
mkdir functions/ffs.xbox360
mkdir configs/c.1
ln -s functions/ffs.xbox360 configs/c.1/

# Note: UDC activation happens when FunctionFS writes descriptors
```

### FunctionFS Mount in systemd
```ini
[Unit]
Description=Xbox 360 FunctionFS Mount
Before=xbox360-emulator.service

[Service]
Type=oneshot
ExecStart=/bin/mkdir -p /dev/xbox360_ffs
ExecStart=/bin/mount -t functionfs xbox360_ffs /dev/xbox360_ffs
ExecStop=/bin/umount /dev/xbox360_ffs
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
```

## 🧪 Testing & Validation

### 1. USB Descriptor Verification
```bash
# After FunctionFS starts, check if device appears
lsusb | grep "045e:02a8"
# Should show: Microsoft Corp. Wireless Network Adapter Boot

# Check device details
lsusb -d 045e:02a8 -v
# Verify all descriptors match Xbox 360 expectations
```

### 2. Authentication Testing
```bash
# Test authentication handler standalone
python3 /opt/xbox360-emulator/src/xbox_auth.py test

# Monitor authentication attempts
journalctl -u xbox360-emulator -f | grep -i auth
```

### 3. Control Transfer Monitoring
```bash
# Monitor USB traffic (requires usbmon)
cat /sys/kernel/debug/usb/usbmon/0u | grep -i "045e:02a8"

# Check FunctionFS status
python3 /opt/xbox360-emulator/src/xbox_functionfs.py status
```

## 🚨 Known Limitations

### Authentication Bypass
- **Simplified Implementation**: Our auth handler uses simplified responses, not full XSM3 crypto
- **Per-Console Keys**: Real XSM3 uses console-specific keys from key vault - we use generic responses
- **Security**: This is a functional bypass, not cryptographically secure authentication

### Xbox Compatibility
- **Console Variations**: Different Xbox 360 models may have slightly different authentication requirements
- **Dashboard Updates**: Xbox Live updates might change authentication requirements
- **Region Differences**: PAL/NTSC Xbox 360s might have different key requirements

### FunctionFS Limitations
- **Root Required**: FunctionFS mount and USB operations require root privileges
- **Single Instance**: Only one FunctionFS gadget can be active per function name
- **Kernel Support**: Requires modern Linux kernel with FunctionFS support

## 🔄 Troubleshooting

### Device Not Recognized
```bash
# Check if gadget structure exists
ls /sys/kernel/config/usb_gadget/xbox360/

# Verify FunctionFS mount
mount | grep functionfs

# Check UDC status
cat /sys/kernel/config/usb_gadget/xbox360/UDC
```

### Authentication Failures
```bash
# Monitor control transfers
python3 /opt/xbox360-emulator/src/xbox_functionfs.py start --verbose

# Check authentication state
python3 /opt/xbox360-emulator/src/xbox_auth.py status

# Reset authentication
python3 /opt/xbox360-emulator/src/xbox_auth.py reset
```

### FunctionFS Errors
```bash
# Check kernel modules
lsmod | grep libcomposite
lsmod | grep configfs

# Verify permissions
ls -la /dev/xbox360_ffs/

# Restart FunctionFS
systemctl restart xbox360-emulator
```

## 📚 References

- [Xbox Security Method 3 Research](https://oct0xor.github.io/2017/05/03/xsm3/)
- [Linux USB Gadget ConfigFS](https://docs.kernel.org/usb/gadget_configfs.html)
- [FunctionFS Documentation](https://www.kernel.org/doc/html/latest/usb/functionfs.html)
- [USB Gadget API](https://www.kernel.org/doc/html/latest/driver-api/usb/gadget.html)

## 🎯 Success Indicators

When working correctly, you should see:

1. **USB Recognition**: `lsusb` shows Microsoft device with correct VID:PID
2. **Authentication Flow**: Logs show identification → challenge → verification sequence
3. **Xbox Connection**: Xbox 360 recognizes wireless adapter and shows network options
4. **Network Function**: Xbox can scan for and connect to virtual networks

The key breakthrough is using **FunctionFS** instead of standard ConfigFS functions, allowing full control over USB descriptors and handling of Xbox-specific authentication protocol! 🎮🔐