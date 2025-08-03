#!/usr/bin/env python3
"""
Xbox 360 WiFi Module Emulator - Advanced USB Gadget Manager
Handles USB gadget configuration with Xbox 360 specific protocols
"""

import os
import sys
import time
import logging
import subprocess
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class Xbox360Gadget:
    """Xbox 360 WiFi Adapter USB Gadget Manager"""
    
    def __init__(self, gadget_name="xbox360"):
        self.gadget_name = gadget_name
        self.gadget_path = Path(f"/sys/kernel/config/usb_gadget/{gadget_name}")
        self.is_configured = False
        
        # Xbox 360 Wireless Network Adapter specifications
        self.usb_specs = {
            'idVendor': '0x045e',      # Microsoft Corporation
            'idProduct': '0x0292',     # Xbox 360 Wireless Network Adapter
            'bcdDevice': '0x0100',     # Device version 1.0
            'bcdUSB': '0x0200',        # USB 2.0
            'bDeviceClass': '0xFF',    # Vendor-specific (like original)
            'bDeviceSubClass': '0xFF', # Vendor-specific
            'bDeviceProtocol': '0xFF', # Vendor-specific
        }
        
        # String descriptors
        self.strings = {
            'manufacturer': 'Microsoft Corp.',
            'product': 'Xbox 360 Wireless Network Adapter',
            'serialnumber': self._get_serial_number()
        }
    
    def _get_serial_number(self):
        """Get unique serial number from Pi hardware"""
        try:
            with open('/proc/cpuinfo', 'r') as f:
                for line in f:
                    if line.startswith('Serial'):
                        return line.split(':')[1].strip()
        except Exception:
            pass
        return "00000000"
    
    def _run_command(self, cmd, check=True):
        """Run shell command with error handling"""
        try:
            result = subprocess.run(cmd, shell=True, check=check, 
                                  capture_output=True, text=True)
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            logger.error(f"Command failed: {cmd}")
            logger.error(f"Error: {e.stderr}")
            raise
    
    def _write_file(self, path, value):
        """Write value to sysfs file"""
        try:
            with open(path, 'w') as f:
                f.write(str(value))
            logger.debug(f"Written {value} to {path}")
        except Exception as e:
            logger.error(f"Failed to write {value} to {path}: {e}")
            raise
    
    def check_prerequisites(self):
        """Check system prerequisites for USB gadget mode"""
        logger.info("Checking prerequisites...")
        
        # Check if running on Pi 4
        try:
            with open('/proc/cpuinfo', 'r') as f:
                if 'Raspberry Pi 4' not in f.read():
                    raise RuntimeError("This requires Raspberry Pi 4")
        except FileNotFoundError:
            raise RuntimeError("Unable to detect Raspberry Pi hardware")
        
        # Check if configfs is mounted
        if not os.path.exists('/sys/kernel/config'):
            raise RuntimeError("configfs not mounted")
        
        # Check if libcomposite is loaded
        result = self._run_command("lsmod | grep libcomposite", check=False)
        if not result:
            logger.info("Loading libcomposite module...")
            self._run_command("modprobe libcomposite")
        
        # Check if dwc2 is loaded
        result = self._run_command("lsmod | grep dwc2", check=False)
        if not result:
            logger.warning("dwc2 module not loaded - USB gadget may not work")
        
        logger.info("✅ Prerequisites check passed")
    
    def create_gadget(self):
        """Create USB gadget with Xbox 360 specifications"""
        logger.info(f"Creating Xbox 360 USB gadget: {self.gadget_name}")
        
        # Create gadget directory
        os.makedirs(self.gadget_path, exist_ok=True)
        os.chdir(self.gadget_path)
        
        # Set USB device descriptor values
        for attr, value in self.usb_specs.items():
            self._write_file(attr, value)
            logger.debug(f"Set {attr} = {value}")
        
        # Create string descriptors
        strings_path = self.gadget_path / "strings" / "0x409"
        os.makedirs(strings_path, exist_ok=True)
        
        for attr, value in self.strings.items():
            self._write_file(strings_path / attr, value)
            logger.debug(f"Set string {attr} = {value}")
        
        # Create configuration
        config_path = self.gadget_path / "configs" / "c.1"
        os.makedirs(config_path, exist_ok=True)
        
        # Set configuration attributes
        self._write_file(config_path / "MaxPower", "500")  # 500mA
        
        # Create configuration strings
        config_strings_path = config_path / "strings" / "0x409"
        os.makedirs(config_strings_path, exist_ok=True)
        self._write_file(config_strings_path / "configuration", 
                        "Xbox 360 WiFi Configuration")
        
        logger.info("✅ USB gadget structure created")
    
    def create_network_function(self, function_type="ncm"):
        """Create network function (NCM is most modern)"""
        logger.info(f"Creating {function_type} network function...")
        
        function_path = self.gadget_path / f"functions" / f"{function_type}.usb0"
        os.makedirs(function_path, exist_ok=True)
        
        # Get host MAC address (from eth0)
        try:
            host_mac = self._run_command("cat /sys/class/net/eth0/address")
        except:
            host_mac = "b8:27:eb:12:34:56"  # Default Pi MAC pattern
        
        # Set MAC addresses
        self._write_file(function_path / "host_addr", host_mac)
        self._write_file(function_path / "dev_addr", "02:22:82:12:34:56")
        
        # Link function to configuration
        config_path = self.gadget_path / "configs" / "c.1"
        link_path = config_path / f"{function_type}.usb0"
        
        # Remove existing link if it exists
        if link_path.exists():
            os.unlink(link_path)
        
        # Create symlink
        os.symlink(f"../../functions/{function_type}.usb0", link_path)
        
        logger.info(f"✅ {function_type.upper()} network function created")
    
    def activate_gadget(self):
        """Activate the USB gadget"""
        logger.info("Activating USB gadget...")
        
        # Find UDC (USB Device Controller)
        udc_list = os.listdir("/sys/class/udc")
        if not udc_list:
            raise RuntimeError("No USB Device Controller found")
        
        udc_name = udc_list[0]
        logger.info(f"Using UDC: {udc_name}")
        
        # Activate gadget
        self._write_file(self.gadget_path / "UDC", udc_name)
        
        # Wait for activation
        time.sleep(2)
        
        # Verify activation
        if self.is_active():
            logger.info("✅ USB gadget activated successfully")
            self.is_configured = True
        else:
            raise RuntimeError("Failed to activate USB gadget")
    
    def deactivate_gadget(self):
        """Deactivate the USB gadget"""
        logger.info("Deactivating USB gadget...")
        
        try:
            self._write_file(self.gadget_path / "UDC", "")
            self.is_configured = False
            logger.info("✅ USB gadget deactivated")
        except Exception as e:
            logger.warning(f"Error deactivating gadget: {e}")
    
    def is_active(self):
        """Check if gadget is active"""
        try:
            udc_file = self.gadget_path / "UDC"
            if udc_file.exists():
                with open(udc_file, 'r') as f:
                    return bool(f.read().strip())
        except:
            pass
        return False
    
    def get_status(self):
        """Get detailed gadget status"""
        status = {
            'configured': self.is_configured,
            'active': self.is_active(),
            'usb_interface': None,
            'lsusb_detected': False
        }
        
        # Check if USB interface exists
        if os.path.exists('/sys/class/net/usb0'):
            status['usb_interface'] = 'usb0'
        
        # Check if detected by lsusb
        try:
            result = self._run_command("lsusb | grep '045e:0292'", check=False)
            status['lsusb_detected'] = bool(result)
        except:
            pass
        
        return status
    
    def setup_complete_gadget(self):
        """Complete gadget setup process"""
        logger.info("🎮 Setting up Xbox 360 WiFi Module Emulator...")
        
        try:
            self.check_prerequisites()
            self.create_gadget()
            self.create_network_function("ncm")  # NCM is most modern
            self.activate_gadget()
            
            logger.info("🎮 Xbox 360 WiFi Adapter emulator ready!")
            return True
            
        except Exception as e:
            logger.error(f"Setup failed: {e}")
            return False


def main():
    """Main function for standalone execution"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Xbox 360 WiFi Adapter USB Gadget Manager')
    parser.add_argument('action', choices=['setup', 'start', 'stop', 'status', 'restart'],
                       help='Action to perform')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Enable verbose logging')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    gadget = Xbox360Gadget()
    
    try:
        if args.action == 'setup':
            success = gadget.setup_complete_gadget()
            sys.exit(0 if success else 1)
            
        elif args.action == 'start':
            if not gadget.is_active():
                gadget.activate_gadget()
            else:
                logger.info("Gadget already active")
                
        elif args.action == 'stop':
            if gadget.is_active():
                gadget.deactivate_gadget()
            else:
                logger.info("Gadget already inactive")
                
        elif args.action == 'restart':
            if gadget.is_active():
                gadget.deactivate_gadget()
            time.sleep(1)
            gadget.activate_gadget()
            
        elif args.action == 'status':
            status = gadget.get_status()
            print("Xbox 360 Gadget Status:")
            print(f"  Configured: {status['configured']}")
            print(f"  Active: {status['active']}")
            print(f"  USB Interface: {status['usb_interface']}")
            print(f"  Detected by lsusb: {status['lsusb_detected']}")
            
    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()