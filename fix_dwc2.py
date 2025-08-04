#!/usr/bin/env python3
"""
DWC2 Fix Script for Xbox 360 WiFi Emulator
Comprehensive fix for DWC2 module loading issues on Raspberry Pi OS Bookworm
"""

import subprocess
import os
import sys
import shutil
from pathlib import Path
import time

class DWC2Fixer:
    def __init__(self):
        self.is_pi = self._detect_pi()
        self.is_bookworm = Path('/boot/firmware/config.txt').exists()
        
        if self.is_bookworm:
            self.config_path = "/boot/firmware/config.txt"
            self.cmdline_path = "/boot/firmware/cmdline.txt"
        else:
            self.config_path = "/boot/config.txt"
            self.cmdline_path = "/boot/cmdline.txt"
    
    def _detect_pi(self):
        """Detect if running on Raspberry Pi"""
        try:
            with open('/proc/cpuinfo', 'r') as f:
                return 'Raspberry Pi' in f.read()
        except:
            return False
    
    def _run_command(self, cmd):
        """Run command safely"""
        try:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            return result.returncode == 0, result.stdout, result.stderr
        except Exception as e:
            return False, "", str(e)
    
    def _backup_file(self, filepath):
        """Create backup of file"""
        if Path(filepath).exists():
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            backup_path = f"{filepath}.backup.{timestamp}"
            shutil.copy2(filepath, backup_path)
            print(f"✅ Backed up {filepath} to {backup_path}")
            return backup_path
        return None
    
    def check_prerequisites(self):
        """Check if we can run the fix"""
        print("🔍 Checking Prerequisites")
        print("=" * 30)
        
        if os.geteuid() != 0:
            print("❌ Must run as root")
            print("   Run with: sudo python3 fix_dwc2.py")
            return False
        
        if not self.is_pi:
            print("❌ Not running on Raspberry Pi")
            print("   This script must be run on the Pi")
            return False
        
        print("✅ Running as root on Raspberry Pi")
        
        if self.is_bookworm:
            print("✅ Detected Bookworm OS")
            print(f"   Using config path: {self.config_path}")
        else:
            print("✅ Detected legacy Pi OS")
            print(f"   Using config path: {self.config_path}")
        
        return True
    
    def fix_boot_config(self):
        """Fix boot configuration files"""
        print(f"\n🔧 Fixing Boot Configuration")
        print("=" * 32)
        
        # Fix config.txt
        print(f"📝 Updating {self.config_path}")
        
        if not Path(self.config_path).exists():
            print(f"❌ {self.config_path} not found!")
            return False
        
        # Backup config.txt
        self._backup_file(self.config_path)
        
        # Read current config
        with open(self.config_path, 'r') as f:
            config_content = f.read()
        
        # Remove any existing dwc2 overlays
        lines = config_content.split('\n')
        cleaned_lines = [line for line in lines if not line.strip().startswith('dtoverlay=dwc2')]
        
        # Add our DWC2 configuration
        dwc2_config = [
            "",
            "# Xbox 360 WiFi Module Emulator - DWC2 Configuration",
            "# Enable DWC2 in OTG mode for both host and device capabilities",
            "dtoverlay=dwc2,dr_mode=otg"
        ]
        
        # Write updated config
        with open(self.config_path, 'w') as f:
            f.write('\n'.join(cleaned_lines + dwc2_config) + '\n')
        
        print("✅ Updated config.txt with OTG mode")
        
        # Fix cmdline.txt
        print(f"📝 Updating {self.cmdline_path}")
        
        if not Path(self.cmdline_path).exists():
            print(f"❌ {self.cmdline_path} not found!")
            return False
        
        # Backup cmdline.txt
        self._backup_file(self.cmdline_path)
        
        # Read current cmdline
        with open(self.cmdline_path, 'r') as f:
            cmdline = f.read().strip()
        
        # Remove existing modules-load parameters
        import re
        cmdline = re.sub(r' modules-load=[^ ]*', '', cmdline)
        
        # Add our modules-load parameter
        cmdline += " modules-load=dwc2,g_ether"
        
        # Write updated cmdline
        with open(self.cmdline_path, 'w') as f:
            f.write(cmdline + '\n')
        
        print("✅ Updated cmdline.txt with module loading")
        return True
    
    def fix_module_configuration(self):
        """Fix module loading configuration"""
        print("\n🧩 Fixing Module Configuration")
        print("=" * 33)
        
        # Create modules-load.d configuration
        modules_dir = Path("/etc/modules-load.d")
        modules_dir.mkdir(exist_ok=True)
        
        # Xbox emulator modules
        xbox_modules_file = modules_dir / "xbox360-emulator.conf"
        with open(xbox_modules_file, 'w') as f:
            f.write("""# Xbox 360 WiFi Module Emulator - Required Modules
libcomposite
dwc2
usbmon
""")
        print(f"✅ Created {xbox_modules_file}")
        
        # DWC2 specific configuration
        dwc2_modules_file = modules_dir / "dwc2.conf"
        with open(dwc2_modules_file, 'w') as f:
            f.write("""# DWC2 USB OTG Controller
dwc2
""")
        print(f"✅ Created {dwc2_modules_file}")
        
        return True
    
    def fix_udev_rules(self):
        """Create udev rules for USB gadget"""
        print("\n📋 Creating Udev Rules")
        print("=" * 25)
        
        udev_rules_dir = Path("/etc/udev/rules.d")
        udev_rules_dir.mkdir(exist_ok=True)
        
        # USB gadget udev rules
        udev_file = udev_rules_dir / "99-xbox360-usb-gadget.rules"
        with open(udev_file, 'w') as f:
            f.write("""# Xbox 360 WiFi Module Emulator - USB Gadget Rules
# Ensure proper permissions for USB gadget devices

# DWC2 USB Device Controller
SUBSYSTEM=="udc", ACTION=="add", RUN+="/bin/chmod 666 /sys/class/udc/%k/uevent"

# USB gadget configfs
SUBSYSTEM=="configfs", ACTION=="add", RUN+="/bin/chmod -R 775 /sys/kernel/config/usb_gadget/"

# USB gadget functions
KERNEL=="g_*", MODE="0666"
""")
        print(f"✅ Created {udev_file}")
        
        return True
    
    def fix_systemd_services(self):
        """Fix systemd service configuration"""
        print("\n🔧 Fixing Systemd Services")
        print("=" * 28)
        
        # Create a service to ensure DWC2 loads properly
        service_file = Path("/etc/systemd/system/dwc2-setup.service")
        with open(service_file, 'w') as f:
            f.write("""[Unit]
Description=DWC2 USB OTG Setup for Xbox 360 Emulator
After=multi-user.target
Before=xbox360-emulator.service

[Service]
Type=oneshot
RemainAfterExit=yes
ExecStart=/bin/bash -c 'modprobe dwc2 && modprobe libcomposite && sleep 2'
ExecStart=/bin/bash -c 'echo "DWC2 modules loaded for Xbox 360 emulator"'

[Install]
WantedBy=multi-user.target
""")
        print(f"✅ Created {service_file}")
        
        # Enable the service
        success, _, _ = self._run_command("systemctl enable dwc2-setup.service")
        if success:
            print("✅ Enabled dwc2-setup service")
        else:
            print("❌ Failed to enable dwc2-setup service")
        
        return True
    
    def test_module_loading(self):
        """Test manual module loading"""
        print("\n🧪 Testing Module Loading")
        print("=" * 27)
        
        modules = ["dwc2", "libcomposite", "g_ether"]
        
        for module in modules:
            print(f"🔄 Loading {module}...")
            success, output, error = self._run_command(f"modprobe {module}")
            if success:
                print(f"✅ {module} loaded successfully")
            else:
                print(f"❌ Failed to load {module}: {error}")
        
        # Check if modules are actually loaded
        print("\n🔍 Checking loaded modules:")
        success, lsmod_output, _ = self._run_command("lsmod")
        if success:
            for module in modules:
                if module in lsmod_output:
                    print(f"✅ {module}: LOADED")
                else:
                    print(f"❌ {module}: NOT LOADED")
        
        return True
    
    def check_usb_controllers(self):
        """Check USB device controllers"""
        print("\n🔌 Checking USB Controllers")
        print("=" * 28)
        
        udc_path = Path("/sys/class/udc/")
        if udc_path.exists():
            udcs = list(udc_path.glob("*"))
            if udcs:
                print("✅ USB Device Controllers found:")
                for udc in udcs:
                    print(f"   📱 {udc.name}")
                return True
            else:
                print("❌ No USB Device Controllers found")
                print("   This indicates DWC2 is not functioning")
        else:
            print("❌ /sys/class/udc/ directory not found")
        
        return False
    
    def apply_bookworm_specific_fixes(self):
        """Apply Bookworm-specific fixes"""
        if not self.is_bookworm:
            return True
            
        print("\n🔧 Applying Bookworm-Specific Fixes")
        print("=" * 38)
        
        # NetworkManager bypass (already in installer)
        interfaces_file = Path("/etc/network/interfaces.d/usb0")
        if not interfaces_file.exists():
            interfaces_file.parent.mkdir(parents=True, exist_ok=True)
            with open(interfaces_file, 'w') as f:
                f.write("""# Xbox 360 WiFi Module Emulator - USB Gadget Interface
allow-hotplug usb0
iface usb0 inet static
    address 192.168.4.1
    netmask 255.255.255.0
auto usb0
""")
            print("✅ Created NetworkManager bypass")
        
        # Disable conflicting services
        services_to_disable = ["ModemManager"]
        for service in services_to_disable:
            success, _, _ = self._run_command(f"systemctl disable {service}")
            if success:
                print(f"✅ Disabled {service}")
        
        return True
    
    def run_comprehensive_fix(self):
        """Run all fixes"""
        print("🛠️  Xbox 360 WiFi Emulator - DWC2 Comprehensive Fix")
        print("=" * 55)
        
        if not self.check_prerequisites():
            return False
        
        # Apply all fixes
        steps = [
            ("Boot Configuration", self.fix_boot_config),
            ("Module Configuration", self.fix_module_configuration),
            ("Udev Rules", self.fix_udev_rules),
            ("Systemd Services", self.fix_systemd_services),
            ("Bookworm Fixes", self.apply_bookworm_specific_fixes),
            ("Test Module Loading", self.test_module_loading),
            ("Check USB Controllers", self.check_usb_controllers)
        ]
        
        for step_name, step_func in steps:
            try:
                step_func()
            except Exception as e:
                print(f"❌ {step_name} failed: {e}")
        
        print("\n" + "=" * 55)
        print("🎯 Fix Complete!")
        print("\n📋 Next Steps:")
        print("1. 🔄 Reboot your Pi: sudo reboot")
        print("2. 🔍 After reboot, check status: python3 debug_dwc2.py")
        print("3. 🎮 Test with Xbox 360 connection")
        
        print("\n💡 If issues persist:")
        print("- Check hardware: ensure proper USB-C cable")
        print("- Verify Pi model: DWC2 works best on Pi 4")
        print("- Check power: Pi needs adequate power supply")
        
        return True

if __name__ == "__main__":
    fixer = DWC2Fixer()
    fixer.run_comprehensive_fix()