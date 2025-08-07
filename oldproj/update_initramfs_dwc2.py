#!/usr/bin/env python3
"""
Standalone Initramfs Update Script for DWC2 Modules
Updates initramfs to ensure DWC2 modules are available during boot
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def main():
    # Check if running as root
    if os.geteuid() != 0:
        print("❌ This script must be run as root")
        print("💡 Please run: sudo python3 update_initramfs_dwc2.py")
        sys.exit(1)
    
    print("🔄 DWC2 Initramfs Update Script")
    print("=" * 35)
    
    # Update module dependencies first
    print("🔧 Updating module dependencies...")
    result = subprocess.run(["depmod", "-a"], capture_output=True, text=True)
    if result.returncode == 0:
        print("✅ Module dependencies updated")
    else:
        print(f"⚠️  depmod warning: {result.stderr}")
    
    # Check if update-initramfs is available
    if not shutil.which("update-initramfs"):
        print("⚠️  update-initramfs not found")
        
        # Try alternative methods
        if shutil.which("mkinitcpio"):
            print("🔧 Using mkinitcpio instead...")
            result = subprocess.run(["mkinitcpio", "-P"], capture_output=True, text=True)
            if result.returncode == 0:
                print("✅ Initramfs updated with mkinitcpio")
                print_completion_message()
                return
        
        if shutil.which("dracut"):
            print("🔧 Using dracut instead...")
            result = subprocess.run(["dracut", "--force"], capture_output=True, text=True)
            if result.returncode == 0:
                print("✅ Initramfs updated with dracut")
                print_completion_message()
                return
        
        print("❌ No initramfs update tool found")
        print("   DWC2 modules will load from /etc/modules at boot")
        return
    
    print("🔧 Updating initramfs for all kernels...")
    print("   This may take several minutes...")
    
    # Run the update command
    result = subprocess.run(["update-initramfs", "-u", "-k", "all"], 
                          capture_output=True, text=True)
    
    if result.returncode == 0:
        print("✅ Initramfs updated successfully!")
        print("   DWC2 and libcomposite modules are now included in initramfs")
        
        if result.stdout:
            print("📄 Output:")
            print(result.stdout)
        
        print_completion_message()
    else:
        print("❌ Initramfs update failed!")
        print(f"   Error: {result.stderr}")
        
        # Try to give helpful advice
        if "No space left on device" in result.stderr:
            print("\n💡 Troubleshooting: No space left on device")
            print("   - Check disk space: df -h")
            print("   - Clean old kernels: apt autoremove")
            print("   - Clear package cache: apt clean")
        
        elif "Permission denied" in result.stderr:
            print("\n💡 Troubleshooting: Permission denied")
            print("   - Make sure you're running as root: sudo python3 update_initramfs_dwc2.py")
        
        else:
            print("\n💡 Troubleshooting: Try manual update")
            print("   - Run: sudo update-initramfs -u")
            print("   - Or: sudo update-initramfs -c -k $(uname -r)")

def print_completion_message():
    """Print completion message"""
    print("\n" + "=" * 50)
    print("🎉 Initramfs Update Complete!")
    print("=" * 50)
    print("📋 What happens next:")
    print("   1. 🔄 Reboot your Raspberry Pi")
    print("   2. 🔍 Check if modules load: lsmod | grep dwc2")
    print("   3. 🧪 Run test: python3 test_dwc2_fix.py")
    print("\n💡 The DWC2 modules should now be available earlier in the boot process")

if __name__ == "__main__":
    main()