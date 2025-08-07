#!/usr/bin/env python3
"""
Comprehensive DWC2 Fix Script for Xbox 360 WiFi Emulator
Handles all known DWC2 loading issues on Raspberry Pi
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path
import re

class DWC2ComprehensiveFixer:
    def __init__(self):
        self.is_bookworm = self._detect_bookworm()
        self.boot_config_path = "/boot/firmware/config.txt" if self.is_bookworm else "/boot/config.txt"
        self.cmdline_path = "/boot/firmware/cmdline.txt" if self.is_bookworm else "/boot/cmdline.txt"
        
        # Check if running as root
        if os.geteuid() != 0:
            print("❌ This script must be run as root")
            print("💡 Please run: sudo python3 fix_dwc2_comprehensive.py")
            sys.exit(1)
    
    def _detect_bookworm(self):
        """Detect if this is Raspberry Pi OS Bookworm"""
        try:
            with open('/etc/os-release', 'r') as f:
                content = f.read()
                return 'bookworm' in content.lower()
        except:
            return Path("/boot/firmware").exists()
    
    def _run_command(self, cmd, check=True):
        """Run command and return result"""
        try:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, check=check)
            return result
        except subprocess.CalledProcessError as e:
            print(f"❌ Command failed: {cmd}")
            print(f"   Error: {e.stderr}")
            return e
    
    def _backup_file(self, filepath):
        """Create backup of file"""
        backup_path = f"{filepath}.backup"
        if Path(filepath).exists() and not Path(backup_path).exists():
            shutil.copy2(filepath, backup_path)
            print(f"📁 Backed up {filepath} to {backup_path}")
    
    def fix_boot_config(self):
        """Fix boot configuration"""
        print(f"\n🔧 Fixing Boot Configuration")
        print("=" * 32)
        
        self._backup_file(self.boot_config_path)
        
        # Read current config
        if not Path(self.boot_config_path).exists():
            print(f"❌ Boot config not found: {self.boot_config_path}")
            return False
        
        with open(self.boot_config_path, 'r') as f:
            config_lines = f.readlines()
        
        # Remove existing DWC2 configurations
        config_lines = [line for line in config_lines if not any(
            keyword in line.lower() for keyword in ['dwc2', 'libcomposite', 'g_ether']
        )]
        
        # Add comprehensive DWC2 configuration
        dwc2_config = [
            "\n# Xbox 360 WiFi Module Emulator - DWC2 Configuration\n",
            "# Enable DWC2 in OTG mode for both host and device capabilities\n",
            "dtoverlay=dwc2,dr_mode=otg\n",
            "\n# USB OTG Configuration\n",
            "# Enable USB OTG mode\n",
            "otg_mode=1\n",
            "\n# Additional USB configuration for better compatibility\n",
            "# Increase USB current limit\n",
            "max_usb_current=1\n",
            "\n# GPU memory split (more memory for CPU)\n",
            "gpu_mem=16\n"
        ]
        
        config_lines.extend(dwc2_config)
        
        # Write updated config
        with open(self.boot_config_path, 'w') as f:
            f.writelines(config_lines)
        
        print(f"✅ Updated {self.boot_config_path}")
        return True
    
    def fix_cmdline(self):
        """Fix cmdline.txt for module loading"""
        print(f"\n🔧 Fixing Kernel Command Line")
        print("=" * 32)
        
        self._backup_file(self.cmdline_path)
        
        if not Path(self.cmdline_path).exists():
            print(f"❌ Cmdline not found: {self.cmdline_path}")
            return False
        
        with open(self.cmdline_path, 'r') as f:
            cmdline = f.read().strip()
        
        # Add modules-load parameter if not present
        modules_to_add = ["dwc2", "libcomposite"]
        current_modules = []
        
        # Extract existing modules-load parameter
        modules_match = re.search(r'modules-load=([^\s]+)', cmdline)
        if modules_match:
            current_modules = modules_match.group(1).split(',')
            # Remove the old modules-load parameter
            cmdline = re.sub(r'modules-load=[^\s]+', '', cmdline)
        
        # Add our required modules
        for module in modules_to_add:
            if module not in current_modules:
                current_modules.append(module)
        
        # Add updated modules-load parameter
        if current_modules:
            modules_param = f"modules-load={','.join(current_modules)}"
            cmdline = f"{cmdline.strip()} {modules_param}"
        
        # Clean up extra spaces
        cmdline = ' '.join(cmdline.split())
        
        with open(self.cmdline_path, 'w') as f:
            f.write(cmdline + '\n')
        
        print(f"✅ Updated {self.cmdline_path}")
        print(f"   Modules to load: {','.join(current_modules)}")
        return True
    
    def fix_modules_config(self):
        """Fix /etc/modules configuration"""
        print(f"\n🔧 Fixing Modules Configuration")
        print("=" * 32)
        
        modules_file = "/etc/modules"
        self._backup_file(modules_file)
        
        # Read current modules
        current_modules = []
        if Path(modules_file).exists():
            with open(modules_file, 'r') as f:
                current_modules = [line.strip() for line in f.readlines() if line.strip() and not line.startswith('#')]
        
        # Add required modules
        required_modules = ["dwc2", "libcomposite"]
        modules_added = []
        
        for module in required_modules:
            if module not in current_modules:
                current_modules.append(module)
                modules_added.append(module)
        
        # Write updated modules file
        with open(modules_file, 'w') as f:
            f.write("# /etc/modules: kernel modules to load at boot time.\n")
            f.write("# This file contains the names of kernel modules that should be loaded\n")
            f.write("# at boot time, one per line. Lines beginning with \"#\" are ignored.\n\n")
            f.write("# Xbox 360 WiFi Module Emulator modules\n")
            for module in current_modules:
                f.write(f"{module}\n")
        
        if modules_added:
            print(f"✅ Added modules to {modules_file}: {', '.join(modules_added)}")
        else:
            print(f"✅ Modules already configured in {modules_file}")
        
        return True
    
    def fix_modprobe_config(self):
        """Create modprobe configuration for better module loading"""
        print(f"\n🔧 Creating Modprobe Configuration")
        print("=" * 35)
        
        modprobe_dir = Path("/etc/modprobe.d")
        modprobe_dir.mkdir(exist_ok=True)
        
        dwc2_conf = modprobe_dir / "dwc2.conf"
        
        with open(dwc2_conf, 'w') as f:
            f.write("# DWC2 configuration for Xbox 360 WiFi Emulator\n")
            f.write("# Force DWC2 to load in OTG mode\n")
            f.write("options dwc2 otg_cap=3\n")
            f.write("\n# libcomposite configuration\n")
            f.write("# Load libcomposite automatically\n")
            f.write("install libcomposite /sbin/modprobe --ignore-install libcomposite\n")
        
        print(f"✅ Created {dwc2_conf}")
        return True
    
    def fix_systemd_modules(self):
        """Create systemd module loading service"""
        print(f"\n🔧 Creating Systemd Module Service")
        print("=" * 35)
        
        systemd_dir = Path("/etc/systemd/system")
        service_file = systemd_dir / "xbox360-modules.service"
        
        service_content = """[Unit]
Description=Xbox 360 WiFi Emulator - Load Required Modules
After=local-fs.target
Before=network-pre.target

[Service]
Type=oneshot
RemainAfterExit=yes
ExecStart=/bin/bash -c 'modprobe dwc2 && modprobe libcomposite'
ExecStop=/bin/bash -c 'rmmod libcomposite || true; rmmod dwc2 || true'

[Install]
WantedBy=multi-user.target
"""
        
        with open(service_file, 'w') as f:
            f.write(service_content)
        
        # Enable the service
        self._run_command("systemctl daemon-reload")
        self._run_command("systemctl enable xbox360-modules.service")
        
        print(f"✅ Created and enabled {service_file}")
        return True
    
    def test_current_status(self):
        """Test current DWC2 status"""
        print(f"\n🔍 Testing Current DWC2 Status")
        print("=" * 32)
        
        # Check if modules are loaded
        lsmod_result = self._run_command("lsmod | grep -E '(dwc2|libcomposite)'", check=False)
        if lsmod_result.returncode == 0 and lsmod_result.stdout:
            print("✅ DWC2 modules currently loaded:")
            print(f"   {lsmod_result.stdout}")
        else:
            print("❌ DWC2 modules not currently loaded")
        
        # Check USB controllers
        udc_result = self._run_command("ls /sys/class/udc/ 2>/dev/null", check=False)
        if udc_result.returncode == 0 and udc_result.stdout.strip():
            print("✅ USB Device Controllers found:")
            for controller in udc_result.stdout.strip().split('\n'):
                print(f"   {controller}")
        else:
            print("❌ No USB Device Controllers found")
        
        # Check DWC2 device
        dwc2_device = Path("/sys/devices/platform/soc/3f980000.usb")
        if dwc2_device.exists():
            print("✅ DWC2 device found at /sys/devices/platform/soc/3f980000.usb")
        else:
            print("❌ DWC2 device not found")
        
        # Try manual module loading
        print("\n🔄 Attempting manual module loading...")
        modprobe_dwc2 = self._run_command("modprobe dwc2", check=False)
        if modprobe_dwc2.returncode == 0:
            print("✅ DWC2 module loaded successfully")
        else:
            print(f"❌ Failed to load DWC2 module: {modprobe_dwc2.stderr}")
        
        modprobe_libcomposite = self._run_command("modprobe libcomposite", check=False)
        if modprobe_libcomposite.returncode == 0:
            print("✅ libcomposite module loaded successfully")
        else:
            print(f"❌ Failed to load libcomposite module: {modprobe_libcomposite.stderr}")
    
    def fix_firmware_issues(self):
        """Fix potential firmware issues and update initramfs"""
        print(f"\n🔧 Checking Firmware Issues")
        print("=" * 30)
        
        # Update firmware packages
        print("📦 Updating firmware packages...")
        self._run_command("apt update -qq", check=False)
        self._run_command("apt install -y raspberrypi-kernel-headers linux-headers-$(uname -r)", check=False)
        
        # Check for firmware files
        firmware_paths = [
            "/lib/firmware",
            "/usr/share/rpikernelhack"
        ]
        
        for fw_path in firmware_paths:
            if Path(fw_path).exists():
                print(f"✅ Firmware directory found: {fw_path}")
            else:
                print(f"⚠️  Firmware directory not found: {fw_path}")
    
    def update_initramfs(self):
        """Update initramfs to include module changes"""
        print(f"\n🔄 Updating Initramfs")
        print("=" * 25)
        
        # Check if update-initramfs is available
        if not shutil.which("update-initramfs"):
            print("⚠️  update-initramfs not found, trying alternative methods...")
            
            # Try mkinitcpio (Arch-based) 
            if shutil.which("mkinitcpio"):
                print("🔧 Using mkinitcpio...")
                result = self._run_command("mkinitcpio -P", check=False)
                if result.returncode == 0:
                    print("✅ Initramfs updated with mkinitcpio")
                    return True
            
            # Try dracut (Red Hat-based)
            if shutil.which("dracut"):
                print("🔧 Using dracut...")
                result = self._run_command("dracut --force", check=False)
                if result.returncode == 0:
                    print("✅ Initramfs updated with dracut")
                    return True
            
            print("⚠️  No initramfs update tool found - modules will load from /etc/modules")
            return False
        
        print("🔧 Updating initramfs for all kernels...")
        print("   This may take a few minutes...")
        
        # Update initramfs for all kernels
        result = self._run_command("update-initramfs -u -k all", check=False)
        
        if result.returncode == 0:
            print("✅ Initramfs updated successfully")
            print("   DWC2 modules will be available during boot")
            return True
        else:
            print(f"⚠️  Initramfs update had issues: {result.stderr}")
            print("   Continuing with boot-time module loading...")
            return False
    
    def update_module_dependencies(self):
        """Update module dependencies"""
        print(f"\n🔧 Updating Module Dependencies")
        print("=" * 35)
        
        # Update module dependencies
        result = self._run_command("depmod -a", check=False)
        if result.returncode == 0:
            print("✅ Module dependencies updated")
        else:
            print(f"⚠️  depmod warning: {result.stderr}")
        
        # Regenerate module dependency files
        modules_dep_path = Path("/lib/modules") / os.uname().release / "modules.dep"
        if modules_dep_path.exists():
            print(f"✅ Module dependencies file exists: {modules_dep_path}")
        else:
            print(f"⚠️  Module dependencies file not found: {modules_dep_path}")
            print("   Running depmod again...")
            self._run_command("depmod -a $(uname -r)", check=False)
    
    def create_test_script(self):
        """Create a test script for verifying the fix"""
        print(f"\n📝 Creating Test Script")
        print("=" * 23)
        
        test_script = Path("test_dwc2_fix.py")
        
        test_content = '''#!/usr/bin/env python3
"""
Test script to verify DWC2 fix
"""
import subprocess
import sys
from pathlib import Path

def test_modules():
    """Test if modules are loaded"""
    print("🔍 Testing DWC2 Module Status")
    print("=" * 30)
    
    # Check lsmod
    result = subprocess.run(["lsmod"], capture_output=True, text=True)
    if "dwc2" in result.stdout:
        print("✅ DWC2 module is loaded")
    else:
        print("❌ DWC2 module not loaded")
    
    if "libcomposite" in result.stdout:
        print("✅ libcomposite module is loaded")
    else:
        print("❌ libcomposite module not loaded")
    
    # Check USB Device Controllers
    udc_path = Path("/sys/class/udc/")
    if udc_path.exists():
        controllers = list(udc_path.iterdir())
        if controllers:
            print(f"✅ Found {len(controllers)} USB Device Controller(s):")
            for controller in controllers:
                print(f"   {controller.name}")
        else:
            print("❌ No USB Device Controllers found")
    else:
        print("❌ /sys/class/udc/ not found")
    
    # Check boot config
    boot_configs = ["/boot/firmware/config.txt", "/boot/config.txt"]
    for config_path in boot_configs:
        if Path(config_path).exists():
            with open(config_path, 'r') as f:
                content = f.read()
                if "dtoverlay=dwc2" in content:
                    print(f"✅ DWC2 overlay found in {config_path}")
                else:
                    print(f"❌ DWC2 overlay not found in {config_path}")
            break

if __name__ == "__main__":
    test_modules()
    print("\\n💡 If modules are not loaded, reboot and run this test again")
'''
        
        with open(test_script, 'w') as f:
            f.write(test_content)
        
        test_script.chmod(0o755)
        print(f"✅ Created test script: {test_script}")
    
    def run_comprehensive_fix(self):
        """Run all fixes"""
        print("🛠️  Xbox 360 WiFi Emulator - Comprehensive DWC2 Fix")
        print("=" * 55)
        print(f"📋 Running on: {'Bookworm' if self.is_bookworm else 'Legacy'} Raspberry Pi OS")
        print(f"📂 Boot config: {self.boot_config_path}")
        print(f"📂 Cmdline: {self.cmdline_path}")
        
        try:
            # Run all fixes
            self.fix_boot_config()
            self.fix_cmdline()
            self.fix_modules_config()
            self.fix_modprobe_config()
            self.fix_systemd_modules()
            self.fix_firmware_issues()
            self.update_module_dependencies()
            self.update_initramfs()
            self.create_test_script()
            
            print(f"\n✅ Comprehensive DWC2 Fix Completed!")
            print("=" * 40)
            print("🔄 REBOOT REQUIRED for changes to take effect")
            print("💡 After reboot, run: python3 test_dwc2_fix.py")
            print("🎯 Or use the installer GUI debug tools")
            
            # Test current status
            self.test_current_status()
            
        except Exception as e:
            print(f"\n❌ Fix failed with error: {e}")
            return False
        
        return True

if __name__ == "__main__":
    fixer = DWC2ComprehensiveFixer()
    fixer.run_comprehensive_fix()