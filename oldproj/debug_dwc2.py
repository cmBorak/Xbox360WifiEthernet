#!/usr/bin/env python3
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
        print("\n🔧 Boot Configuration")
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
                for line in content.split('\n'):
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
        print("\n🧩 Kernel Modules")
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
        print("\n🔌 USB Gadget Support")
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
    
    def check_dmesg_errors(self):
        """Check dmesg for DWC2 related errors"""
        print("\n📋 System Messages (dmesg)")
        print("=" * 28)
        
        # Check for dwc2 messages
        success, output, _ = self._run_command("dmesg | grep -i dwc2")
        if success and output:
            print("🔍 DWC2-related messages:")
            for line in output.split('\n'):
                if line.strip():
                    if 'error' in line.lower() or 'fail' in line.lower():
                        print(f"   ❌ {line.strip()}")
                    else:
                        print(f"   ℹ️  {line.strip()}")
        else:
            print("❌ No DWC2 messages found in dmesg")
            print("   This suggests dwc2 overlay is not loading at boot")
        
        # Check for USB gadget messages
        success, output, _ = self._run_command("dmesg | grep -i 'usb.*gadget'")
        if success and output:
            print("\n🔍 USB Gadget messages:")
            for line in output.split('\n'):
                if line.strip():
                    print(f"   ℹ️  {line.strip()}")
    
    def try_manual_module_load(self):
        """Try to manually load DWC2 module"""
        print("\n🔧 Manual Module Loading")
        print("=" * 25)
        
        if os.geteuid() != 0:
            print("❌ Must run as root to load modules")
            print("   Run with: sudo python3 debug_dwc2.py")
            return False
        
        modules = ["dwc2", "libcomposite", "g_ether"]
        
        for module in modules:
            print(f"🔄 Attempting to load {module}...")
            success, _, error = self._run_command(f"modprobe {module}")
            if success:
                print(f"✅ {module} loaded successfully")
            else:
                print(f"❌ Failed to load {module}: {error}")
        
        # Check if modules loaded
        self.check_kernel_modules()
        return True
    
    def suggest_fixes(self):
        """Suggest fixes based on findings"""
        print("\n🛠️  Suggested Fixes")
        print("=" * 20)
        
        print("1. 🔄 **Reboot Required**")
        print("   USB gadget mode requires reboot after config changes")
        print("   Command: sudo reboot")
        
        print("\n2. 🔧 **Manual Module Loading**")
        print("   Try loading modules manually:")
        print("   sudo modprobe dwc2")
        print("   sudo modprobe libcomposite")
        
        print("\n3. 📝 **Check Boot Configuration**")
        if self.is_bookworm:
            print("   Bookworm config location: /boot/firmware/config.txt")
            print("   Should contain: dtoverlay=dwc2,dr_mode=otg")
        else:
            print("   Legacy config location: /boot/config.txt")
            print("   Should contain: dtoverlay=dwc2,dr_mode=otg")
        
        print("\n4. 🎯 **Re-run Installer**")
        print("   Run the installer to fix configuration:")
        print("   sudo python3 installer.py")
        
        print("\n5. 🔍 **Hardware Check**")
        print("   Ensure using proper USB-C cable")
        print("   Some cables are power-only, need data cables")
    
    def run_full_diagnosis(self):
        """Run complete diagnosis"""
        print("🕵️  Xbox 360 WiFi Emulator - DWC2 Debug Tool")
        print("=" * 50)
        
        if not self.check_system_info():
            return
        
        config_ok = self.check_boot_config()
        self.check_kernel_modules()
        gadget_ok = self.check_usb_gadget_support()
        self.check_dmesg_errors()
        
        if os.geteuid() == 0:
            self.try_manual_module_load()
        
        print("\n" + "=" * 50)
        
        if config_ok and gadget_ok:
            print("✅ System appears to be configured correctly")
            print("   If Xbox still doesn't detect adapter, try reboot")
        else:
            print("❌ Issues found - see suggested fixes below")
        
        self.suggest_fixes()

if __name__ == "__main__":
    debugger = DWC2Debugger()
    debugger.run_full_diagnosis()