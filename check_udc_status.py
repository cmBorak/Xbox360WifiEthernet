#!/usr/bin/env python3
"""
Quick UDC (USB Device Controller) Status Checker
Run this to check if your Pi 4 is properly configured for USB gadget mode
"""

import os
import subprocess
from pathlib import Path

def run_command(cmd):
    """Run command and return output"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)

def main():
    print("🔍 USB Device Controller (UDC) Status Check")
    print("=" * 50)
    
    # Check if running on Pi 4
    print("\n1. Hardware Check:")
    try:
        with open('/proc/cpuinfo', 'r') as f:
            cpuinfo = f.read()
            if 'Raspberry Pi 4' in cpuinfo:
                print("✅ Raspberry Pi 4 detected")
            else:
                print("❌ Not a Raspberry Pi 4")
                print("   This functionality requires Pi 4 hardware")
    except:
        print("❌ Cannot read CPU info")
    
    # Check boot configuration
    print("\n2. Boot Configuration:")
    boot_files = ['/boot/config.txt', '/boot/firmware/config.txt']
    config_found = False
    
    for boot_file in boot_files:
        if Path(boot_file).exists():
            config_found = True
            print(f"✅ Found boot config: {boot_file}")
            
            with open(boot_file, 'r') as f:
                config_content = f.read()
                
            if 'dtoverlay=dwc2' in config_content:
                print("✅ dwc2 overlay enabled in boot config")
            else:
                print("❌ dwc2 overlay NOT found in boot config")
                print("   Add 'dtoverlay=dwc2' to your boot config")
            break
    
    if not config_found:
        print("❌ Boot config file not found")
    
    # Check kernel modules
    print("\n3. Kernel Modules:")
    modules_to_check = ['dwc2', 'libcomposite', 'configfs']
    
    for module in modules_to_check:
        success, stdout, _ = run_command(f"lsmod | grep {module}")
        if success:
            print(f"✅ {module} module is loaded")
        else:
            print(f"❌ {module} module not loaded")
            
            # Try to load it
            print(f"   Attempting to load {module}...")
            success, _, stderr = run_command(f"sudo modprobe {module}")
            if success:
                print(f"   ✅ Successfully loaded {module}")
            else:
                print(f"   ❌ Failed to load {module}: {stderr}")
    
    # Check UDC directory
    print("\n4. USB Device Controller Check:")
    udc_path = Path("/sys/class/udc")
    
    if udc_path.exists():
        print("✅ UDC path exists")
        
        udc_list = list(udc_path.glob("*"))
        if udc_list:
            print(f"✅ Found UDC controllers: {[udc.name for udc in udc_list]}")
            
            # Check for DWC2 specifically
            for udc in udc_list:
                if 'dwc2' in udc.name or 'fe980000' in udc.name:
                    print(f"✅ DWC2 controller available: {udc.name}")
                    break
            else:
                print("⚠️ No DWC2 controller found in UDC list")
        else:
            print("❌ No UDC controllers found")
            print("   CRITICAL: This means USB gadget mode is not available")
            print("   Check your hardware and configuration")
    else:
        print("❌ UDC path does not exist")
        print("   This indicates USB gadget support is not available")
    
    # Check USB cable connection
    print("\n5. USB Connection Status:")
    print("⚠️ IMPORTANT: For USB gadget mode to work:")
    print("   • Pi 4 must be connected to a host computer via USB-C port")
    print("   • Use a USB-C DATA cable (not power-only)")
    print("   • The Pi should appear as a USB device on the host")
    print("   • UDC controllers only appear when properly connected")
    
    # Check if configfs is mounted
    print("\n6. ConfigFS Status:")
    success, stdout, _ = run_command("mount | grep configfs")
    if success:
        print("✅ configfs is mounted")
        
        # Check if gadget directory exists
        gadget_path = Path("/sys/kernel/config/usb_gadget")
        if gadget_path.exists():
            print("✅ USB gadget configfs directory exists")
        else:
            print("❌ USB gadget configfs directory missing")
    else:
        print("❌ configfs not mounted")
        print("   Attempting to mount...")
        success, _, stderr = run_command("sudo mount -t configfs none /sys/kernel/config")
        if success:
            print("   ✅ configfs mounted successfully")
        else:
            print(f"   ❌ Failed to mount configfs: {stderr}")
    
    # Summary and recommendations
    print("\n" + "=" * 50)
    print("📋 SUMMARY AND RECOMMENDATIONS:")
    print("=" * 50)
    
    if not udc_path.exists() or not list(udc_path.glob("*")):
        print("❌ CRITICAL ISSUE: No USB Device Controllers found")
        print("\n🔧 REQUIRED ACTIONS:")
        print("1. Ensure you're using a Raspberry Pi 4")
        print("2. Connect Pi 4 to host computer via USB-C DATA cable")
        print("3. Add 'dtoverlay=dwc2' to /boot/config.txt")
        print("4. Add 'modules-load=dwc2' to /boot/cmdline.txt") 
        print("5. Reboot the Pi")
        print("6. Run this check again")
        print("\n⚠️ Without UDC, USB gadget functionality will not work")
    else:
        print("✅ USB Device Controllers found - gadget mode should work!")
        
    print("\n🧪 To test full functionality, run:")
    print("   sudo python3 test_pi_functionality.py")

if __name__ == "__main__":
    main()