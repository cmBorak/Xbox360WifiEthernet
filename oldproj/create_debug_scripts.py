#!/usr/bin/env python3
"""
Create debug_dwc2.py and fix_dwc2.py scripts if they don't exist
This ensures the GUI has the referenced scripts available
"""

from pathlib import Path

def create_debug_script():
    """Create debug_dwc2.py script"""
    debug_script = Path("debug_dwc2.py")
    if not debug_script.exists():
        with open(debug_script, 'w') as f:
            f.write('''#!/usr/bin/env python3
"""
DWC2 Module Debug Script for Xbox 360 WiFi Emulator
Diagnoses and fixes DWC2 loading issues on Raspberry Pi
"""

import subprocess
import os
import sys
from pathlib import Path

class DWC2Debugger:
    def __init__(self):
        self.is_pi = self._detect_pi()
        self.is_bookworm = self._detect_bookworm()
        
    def _detect_pi(self):
        """Detect if running on Raspberry Pi"""
        try:
            with open('/proc/cpuinfo', 'r') as f:
                return 'Raspberry Pi' in f.read()
        except:
            return False
    
    def _detect_bookworm(self):
        """Detect if running Bookworm OS"""
        return Path('/boot/firmware/config.txt').exists()
    
    def _run_command(self, cmd, capture=True):
        """Run command and return output"""
        try:
            if capture:
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                return result.returncode == 0, result.stdout, result.stderr
            else:
                return subprocess.run(cmd, shell=True).returncode == 0, "", ""
        except Exception as e:
            return False, "", str(e)
    
    def check_system_info(self):
        """Check basic system information"""
        print("🔍 System Information")
        print("=" * 30)
        
        # Check if we're on Pi
        if not self.is_pi:
            print("❌ Not running on Raspberry Pi")
            print("   This script should be run on the Pi itself")
            return False
        else:
            print("✅ Running on Raspberry Pi")
        
        # Check OS version
        success, output, _ = self._run_command("cat /etc/os-release | grep VERSION")
        if success:
            print(f"📋 OS Version: {output.strip()}")
        
        if self.is_bookworm:
            print("✅ Detected Bookworm OS - using /boot/firmware/")
        else:
            print("✅ Detected legacy OS - using /boot/")
        
        return True
    
    def check_boot_config(self):
        """Check boot configuration files"""
        print("\\n🔧 Boot Configuration")
        print("=" * 25)
        
        # Determine config paths
        if self.is_bookworm:
            config_path = "/boot/firmware/config.txt"
            cmdline_path = "/boot/firmware/cmdline.txt"
        else:
            config_path = "/boot/config.txt" 
            cmdline_path = "/boot/cmdline.txt"
        
        # Check config.txt
        if Path(config_path).exists():
            print(f"✅ Found config.txt: {config_path}")
            
            # Check for dwc2 overlay
            with open(config_path, 'r') as f:
                content = f.read()
                
            if "dtoverlay=dwc2" in content:
                print("✅ dwc2 overlay found in config.txt")
                
                # Check the exact configuration
                for line in content.split('\\n'):
                    if 'dtoverlay=dwc2' in line:
                        print(f"   📄 {line.strip()}")
            else:
                print("❌ dwc2 overlay NOT found in config.txt")
                return False
        else:
            print(f"❌ config.txt not found at {config_path}")
            return False
        
        # Check cmdline.txt
        if Path(cmdline_path).exists():
            print(f"✅ Found cmdline.txt: {cmdline_path}")
            
            with open(cmdline_path, 'r') as f:
                cmdline = f.read().strip()
                
            if "modules-load=dwc2" in cmdline:
                print("✅ dwc2 module loading found in cmdline.txt")
                print(f"   📄 {cmdline}")
            else:
                print("❌ dwc2 module loading NOT found in cmdline.txt")
                return False
        else:
            print(f"❌ cmdline.txt not found at {cmdline_path}")
            return False
        
        return True
    
    def check_kernel_modules(self):
        """Check kernel module status"""
        print("\\n🧩 Kernel Modules")
        print("=" * 20)
        
        modules_to_check = ["dwc2", "libcomposite", "udc_core", "g_ether"]
        
        # Check loaded modules
        success, lsmod_output, _ = self._run_command("lsmod")
        if not success:
            print("❌ Failed to get module list")
            return False
        
        for module in modules_to_check:
            if module in lsmod_output:
                print(f"✅ {module}: LOADED")
            else:
                print(f"❌ {module}: NOT LOADED")
        
        return True
    
    def check_usb_gadget_support(self):
        """Check USB gadget support"""
        print("\\n🔌 USB Gadget Support")
        print("=" * 23)
        
        # Check for UDC (USB Device Controller)
        udc_path = Path("/sys/class/udc/")
        if udc_path.exists():
            udcs = list(udc_path.glob("*"))
            if udcs:
                print("✅ USB Device Controllers found:")
                for udc in udcs:
                    print(f"   📱 {udc.name}")
            else:
                print("❌ No USB Device Controllers found")
                print("   This indicates dwc2 is not working as USB device")
                return False
        else:
            print("❌ /sys/class/udc/ not found")
            return False
        
        # Check configfs
        configfs_path = Path("/sys/kernel/config/usb_gadget/")
        if configfs_path.exists():
            print("✅ ConfigFS USB gadget support available")
        else:
            print("❌ ConfigFS USB gadget support not available")
        
        return True
    
    def run_full_diagnosis(self):
        """Run complete diagnosis"""
        print("🕵️  Xbox 360 WiFi Emulator - DWC2 Debug Tool")
        print("=" * 50)
        
        if not self.check_system_info():
            return
        
        config_ok = self.check_boot_config()
        self.check_kernel_modules()
        gadget_ok = self.check_usb_gadget_support()
        
        print("\\n" + "=" * 50)
        
        if config_ok and gadget_ok:
            print("✅ System appears to be configured correctly")
            print("   If Xbox still doesn't detect adapter, try reboot")
        else:
            print("❌ Issues found - run fix_dwc2.py to fix")

if __name__ == "__main__":
    debugger = DWC2Debugger()
    debugger.run_full_diagnosis()
''')
        debug_script.chmod(0o755)
        print(f"Created {debug_script}")

def create_fix_script():
    """Create fix_dwc2.py script"""
    fix_script = Path("fix_dwc2.py")
    if not fix_script.exists():
        with open(fix_script, 'w') as f:
            f.write('''#!/usr/bin/env python3
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
        print(f"\\n🔧 Fixing Boot Configuration")
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
        lines = config_content.split('\\n')
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
            f.write('\\n'.join(cleaned_lines + dwc2_config) + '\\n')
        
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
            f.write(cmdline + '\\n')
        
        print("✅ Updated cmdline.txt with module loading")
        return True
    
    def run_comprehensive_fix(self):
        """Run all fixes"""
        print("🛠️  Xbox 360 WiFi Emulator - DWC2 Comprehensive Fix")
        print("=" * 55)
        
        if not self.check_prerequisites():
            return False
        
        # Apply fixes
        try:
            self.fix_boot_config()
        except Exception as e:
            print(f"❌ Boot configuration fix failed: {e}")
        
        print("\\n" + "=" * 55)
        print("🎯 Fix Complete!")
        print("\\n📋 Next Steps:")
        print("1. 🔄 Reboot your Pi: sudo reboot")
        print("2. 🔍 After reboot, check status: python3 debug_dwc2.py")
        print("3. 🎮 Test with Xbox 360 connection")
        
        print("\\n💡 If issues persist:")
        print("- Check hardware: ensure proper USB-C cable")
        print("- Verify Pi model: DWC2 works best on Pi 4")
        print("- Check power: Pi needs adequate power supply")
        
        return True

if __name__ == "__main__":
    fixer = DWC2Fixer()
    fixer.run_comprehensive_fix()
''')
        fix_script.chmod(0o755)
        print(f"Created {fix_script}")

if __name__ == "__main__":
    print("🔧 Creating debug and fix scripts...")
    create_debug_script()
    create_fix_script()
    print("✅ Scripts created successfully!")