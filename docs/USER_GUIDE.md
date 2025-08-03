# Xbox 360 WiFi Module Emulator - User Guide

## Overview

The Xbox 360 WiFi Module Emulator transforms your Raspberry Pi 4 into a high-performance network adapter for Xbox 360 consoles, providing gigabit ethernet speeds through USB gadget mode emulation.

## Features

- **20x Performance**: 1000Mbps vs 54Mbps original adapter
- **Cost Effective**: ~$35 vs $50-100 for original adapters
- **Perfect Compatibility**: Emulates official Xbox 360 WiFi adapter (VID:0x045E, PID:0x0292)
- **Easy Setup**: Automated installation and configuration
- **Monitoring**: Real-time status monitoring and auto-recovery

## Quick Start

### 1. Hardware Setup

**Required:**
- Raspberry Pi 4 (USB-C OTG support required)
- MicroSD card (16GB minimum)
- USB-C to USB-A cable
- Ethernet connection to your router

**Connections:**
```
Internet → Router → [Ethernet] Pi 4 [USB-C] → Xbox 360
```

### 2. Software Installation

1. **Flash Raspberry Pi OS** to your SD card
2. **Enable SSH** (optional) by creating empty file named `ssh` on boot partition
3. **Boot Pi** and connect to network
4. **Download and install:**
   ```bash
   git clone https://github.com/your-repo/xbox360-wifi-emulator
   cd xbox360-wifi-emulator
   sudo ./install.sh
   ```

### 3. Initial Setup

1. **Reboot Pi** (required for USB gadget mode):
   ```bash
   sudo reboot
   ```

2. **Validate installation:**
   ```bash
   sudo xbox360-validate
   ```

3. **Start the emulator:**
   ```bash
   sudo systemctl start xbox360-emulator
   ```

### 4. Xbox 360 Configuration

1. **Connect USB cable** from Pi 4 USB-C port to Xbox 360 USB port
2. **Go to Xbox Settings** → Network Settings
3. **Select "Xbox 360 Wireless Network Adapter"**
4. **Configure your network settings** (DHCP recommended)
5. **Test Xbox Live connection**

## Usage

### Service Management

**Start/Stop Service:**
```bash
sudo systemctl start xbox360-emulator   # Start
sudo systemctl stop xbox360-emulator    # Stop
sudo systemctl restart xbox360-emulator # Restart
```

**Auto-start on boot:**
```bash
sudo systemctl enable xbox360-emulator  # Enable (already done by installer)
sudo systemctl disable xbox360-emulator # Disable
```

**Check status:**
```bash
systemctl status xbox360-emulator       # Service status
journalctl -u xbox360-emulator -f       # Live logs
```

### Manual Operation

**Interactive mode:**
```bash
sudo xbox360-emulator interactive
```

**One-time start:**
```bash
sudo xbox360-emulator start
```

**Get status:**
```bash
xbox360-emulator status
```

### Monitoring

**Real-time status:**
```bash
sudo xbox360-emulator interactive
```

**Check logs:**
```bash
sudo journalctl -u xbox360-emulator -f  # Live logs
sudo cat /var/log/xbox360-emulator/emulator.log  # Log file
```

**Validation tests:**
```bash
sudo xbox360-validate
```

## Configuration

### Configuration File

Located at: `/etc/xbox360-emulator/config.json`

```json
{
  "gadget": {
    "name": "xbox360",
    "auto_start": true
  },
  "bridge": {
    "name": "br0",
    "eth_interface": "eth0",
    "usb_interface": "usb0",
    "use_dhcp": true,
    "static_ip": null
  },
  "monitoring": {
    "status_check_interval": 30,
    "connection_monitor": true,
    "auto_recovery": true
  },
  "logging": {
    "level": "INFO",
    "file": "/var/log/xbox360-emulator/emulator.log"
  }
}
```

### Network Configuration

**DHCP (Recommended):**
```json
"bridge": {
  "use_dhcp": true,
  "static_ip": null
}
```

**Static IP:**
```json
"bridge": {
  "use_dhcp": false,
  "static_ip": "192.168.1.100/24"
}
```

## Troubleshooting

### Common Issues

**1. Xbox doesn't detect adapter**
```bash
# Check USB gadget status
lsusb | grep "045e:0292"

# Restart USB gadget
sudo systemctl restart xbox360-emulator

# Check for hardware issues
dmesg | grep -i usb
```

**2. No internet connectivity**
```bash
# Check bridge status
brctl show br0

# Test internet from Pi
ping 8.8.8.8

# Check NAT rules
sudo iptables -t nat -L
```

**3. Poor performance**
```bash
# Check network optimization
cat /proc/sys/net/ipv4/tcp_congestion_control  # Should be "bbr"
cat /proc/sys/net/ipv4/ip_forward              # Should be "1"

# Test bandwidth
iperf3 -c speedtest.net
```

**4. Service won't start**
```bash
# Check service status
systemctl status xbox360-emulator

# Check system requirements
sudo xbox360-validate

# Check logs
journalctl -u xbox360-emulator --no-pager
```

### Validation Commands

**System requirements:**
```bash
sudo xbox360-validate
```

**USB gadget test:**
```bash
sudo python3 /opt/xbox360-emulator/src/xbox360_gadget.py status
```

**Network bridge test:**
```bash
sudo python3 /opt/xbox360-emulator/src/network_bridge.py status
```

### Performance Optimization

**Network settings:**
```bash
# Check current settings
cat /proc/sys/net/ipv4/tcp_congestion_control
cat /proc/sys/net/core/rmem_max
cat /proc/sys/net/core/wmem_max

# Manual optimization (done automatically)
echo 'bbr' > /proc/sys/net/ipv4/tcp_congestion_control
echo '134217728' > /proc/sys/net/core/rmem_max
echo '134217728' > /proc/sys/net/core/wmem_max
```

## Advanced Usage

### Custom Configuration

**Multiple Xbox consoles:**
```json
"bridge": {
  "name": "br0",
  "eth_interface": "eth0",
  "usb_interface": "usb0"
}
```

**WiFi bridge mode:**
```json
"bridge": {
  "eth_interface": "wlan0"
}
```

### Development Mode

**Run from source:**
```bash
cd /opt/xbox360-emulator/src
sudo python3 xbox360_emulator.py start --verbose
```

**Debug mode:**
```bash
sudo xbox360-emulator start --verbose
```

## Support

### Getting Help

**Status information:**
```bash
xbox360-emulator status
sudo xbox360-validate
systemctl status xbox360-emulator
```

**Log files:**
- Service logs: `journalctl -u xbox360-emulator`
- Application logs: `/var/log/xbox360-emulator/emulator.log`
- System logs: `/var/log/syslog`

### Reporting Issues

When reporting issues, include:

1. **System information:**
   ```bash
   cat /proc/cpuinfo | grep "Raspberry Pi"
   uname -a
   ```

2. **Service status:**
   ```bash
   systemctl status xbox360-emulator
   ```

3. **Validation results:**
   ```bash
   sudo xbox360-validate
   ```

4. **Recent logs:**
   ```bash
   journalctl -u xbox360-emulator --since "1 hour ago"
   ```

## Uninstalling

**Complete removal:**
```bash
sudo /opt/xbox360-emulator/bin/uninstall
```

**Manual cleanup:**
```bash
sudo systemctl stop xbox360-emulator
sudo systemctl disable xbox360-emulator
sudo rm -rf /opt/xbox360-emulator
sudo rm -rf /etc/xbox360-emulator
sudo rm -rf /var/log/xbox360-emulator
```

**Boot configuration cleanup:**
```bash
# Remove from /boot/config.txt:
dtoverlay=dwc2

# Remove from /boot/cmdline.txt:
modules-load=dwc2
```

## Safety and Security

### Security Considerations

- **Root privileges required** for USB gadget mode
- **Network bridge access** to your local network
- **Xbox Live compliance** - no modification of Xbox Live traffic
- **Local operation only** - no remote access capabilities

### Safety Features

- **Auto-recovery** from connection failures
- **Health monitoring** with automatic restart
- **Safe shutdown** procedures
- **Log rotation** to prevent disk space issues
- **Validation gates** to ensure system integrity

## FAQ

**Q: Will this work with Xbox One/Series X?**
A: No, this is specifically designed for Xbox 360 wireless network adapter emulation.

**Q: Can I use WiFi instead of ethernet?**
A: Yes, change `eth_interface` to `wlan0` in the configuration.

**Q: Does this modify Xbox Live traffic?**
A: No, this only provides network connectivity. All Xbox Live traffic passes through unchanged.

**Q: Can I use this for other devices?**
A: This is specifically designed for Xbox 360. Other devices would require different USB descriptors.

**Q: What's the maximum bandwidth?**
A: Limited by your Pi 4's gigabit ethernet port (~940Mbps practical).

**Q: Is this legal?**
A: Yes, this is hardware emulation for compatibility purposes, similar to using ethernet adapters.

---

*For additional support and updates, visit the project repository.*