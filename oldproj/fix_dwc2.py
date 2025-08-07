#!/usr/bin/env python3
"""
DWC2 Fix Script - Wrapper for Comprehensive Fix
Calls the comprehensive fix script with better error handling
"""

import os
import sys
import subprocess
from pathlib import Path

def main():
    # Check if running as root
    if os.geteuid() != 0:
        print("❌ This script must be run as root")
        print("💡 Please run: sudo python3 fix_dwc2.py")
        sys.exit(1)
    
    print("🛠️  Xbox 360 WiFi Emulator - DWC2 Fix")
    print("=" * 40)
    
    # Check if comprehensive fix script exists
    comprehensive_script = Path("fix_dwc2_comprehensive.py")
    if comprehensive_script.exists():
        print("🚀 Running comprehensive DWC2 fix...")
        try:
            result = subprocess.run([sys.executable, str(comprehensive_script)], 
                                  check=True, cwd=os.getcwd())
            print("✅ Comprehensive fix completed successfully!")
        except subprocess.CalledProcessError as e:
            print(f"❌ Comprehensive fix failed: {e}")
            sys.exit(1)
    else:
        print("⚠️  Comprehensive fix script not found, running basic fix...")
        basic_fix()

def basic_fix():
    """Basic DWC2 fix if comprehensive script not available"""
    print("\n🔧 Running Basic DWC2 Configuration")
    print("=" * 38)
    
    # Detect Raspberry Pi OS version
    is_bookworm = Path("/boot/firmware").exists()
    boot_config = "/boot/firmware/config.txt" if is_bookworm else "/boot/config.txt"
    
    print(f"📋 Detected: {'Bookworm' if is_bookworm else 'Legacy'} Raspberry Pi OS")
    print(f"📂 Boot config: {boot_config}")
    
    # Check if boot config exists
    if not Path(boot_config).exists():
        print(f"❌ Boot config not found: {boot_config}")
        return
    
    # Read current config
    with open(boot_config, 'r') as f:
        config_content = f.read()
    
    # Check if DWC2 overlay already exists
    if "dtoverlay=dwc2" in config_content:
        print("✅ DWC2 overlay already configured")
    else:
        print("🔧 Adding DWC2 overlay to boot config...")
        with open(boot_config, 'a') as f:
            f.write("\n# Xbox 360 WiFi Module Emulator - DWC2 Configuration\n")
            f.write("dtoverlay=dwc2,dr_mode=otg\n")
        print("✅ DWC2 overlay added")
    
    # Add modules to /etc/modules
    modules_file = "/etc/modules"
    with open(modules_file, 'r') as f:
        modules_content = f.read()
    
    modules_to_add = ["dwc2", "libcomposite"]
    modules_added = []
    
    for module in modules_to_add:
        if module not in modules_content:
            with open(modules_file, 'a') as f:
                f.write(f"{module}\n")
            modules_added.append(module)
    
    if modules_added:
        print(f"✅ Added modules: {', '.join(modules_added)}")
    else:
        print("✅ Modules already configured")
    
    print("\n🔄 REBOOT REQUIRED for changes to take effect")
    print("💡 After reboot, check with: lsmod | grep dwc2")

if __name__ == "__main__":
    main()