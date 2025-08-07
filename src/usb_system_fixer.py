#!/usr/bin/env python3
"""
USB System Diagnostic and Fixer
Diagnoses and fixes common USB gadget, raw-gadget, and usb0 interface issues
"""

import os
import sys
import subprocess
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional

logger = logging.getLogger(__name__)

class USBSystemFixer:
    """Diagnose and fix USB system issues"""
    
    def __init__(self):
        self.issues = []
        self.fixes_applied = []
        self.system_status = {}
        
    def run_command(self, cmd: str, description: str = "") -> Tuple[bool, str, str]:
        """Run command and return success, stdout, stderr"""
        try:
            if description:
                logger.info(f"🔧 {description}")
            
            logger.debug(f"Running: {cmd}")
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
            
            success = result.returncode == 0
            if success:
                logger.debug(f"✅ Command succeeded")
            else:
                logger.warning(f"❌ Command failed (exit code: {result.returncode})")
                if result.stderr.strip():
                    logger.warning(f"   Error: {result.stderr.strip()}")
            
            return success, result.stdout, result.stderr
            
        except subprocess.TimeoutExpired:
            logger.error(f"⏰ Command timed out: {cmd}")
            return False, "", "Command timeout"
        except Exception as e:
            logger.error(f"💥 Command exception: {e}")
            return False, "", str(e)
    
    def check_kernel_modules(self) -> Dict[str, bool]:
        """Check if required kernel modules are available/loaded"""
        logger.info("🔍 Checking kernel modules...")
        
        modules = {
            'dwc2': False,
            'libcomposite': False,
            'configfs': False,
            'raw_gadget': False,
            'g_ether': False,
            'usbmon': False
        }
        
        # Check loaded modules
        success, stdout, _ = self.run_command("lsmod")
        if success:
            loaded_modules = stdout.lower()
            for module in modules:
                if module in loaded_modules:
                    modules[module] = True
                    logger.info(f"✅ {module} is loaded")
                else:
                    logger.warning(f"❌ {module} is not loaded")
        
        # Try to load missing critical modules
        critical_modules = ['dwc2', 'libcomposite', 'configfs']
        for module in critical_modules:
            if not modules[module]:
                success, _, stderr = self.run_command(f"sudo modprobe {module}", f"Loading {module}")
                if success:
                    modules[module] = True
                    self.fixes_applied.append(f"Loaded {module} module")
                    logger.info(f"✅ Successfully loaded {module}")
                else:
                    self.issues.append(f"Cannot load {module} module: {stderr}")
                    logger.error(f"❌ Failed to load {module}: {stderr}")
        
        return modules
    
    def check_filesystem_mounts(self) -> Dict[str, bool]:
        """Check if required filesystems are mounted"""
        logger.info("🔍 Checking filesystem mounts...")
        
        mounts = {
            'configfs': False,
            'debugfs': False
        }
        
        # Check current mounts
        success, stdout, _ = self.run_command("mount")
        if success:
            mount_output = stdout.lower()
            
            if 'configfs' in mount_output and '/sys/kernel/config' in mount_output:
                mounts['configfs'] = True
                logger.info("✅ configfs is mounted")
            else:
                logger.warning("❌ configfs is not mounted")
                
            if 'debugfs' in mount_output and '/sys/kernel/debug' in mount_output:
                mounts['debugfs'] = True  
                logger.info("✅ debugfs is mounted")
            else:
                logger.warning("❌ debugfs is not mounted")
        
        # Try to mount missing filesystems
        if not mounts['configfs']:
            success, _, stderr = self.run_command("sudo mount -t configfs none /sys/kernel/config", "Mounting configfs")
            if success:
                mounts['configfs'] = True
                self.fixes_applied.append("Mounted configfs")
                logger.info("✅ Successfully mounted configfs")
            else:
                self.issues.append(f"Cannot mount configfs: {stderr}")
                
        if not mounts['debugfs']:
            success, _, stderr = self.run_command("sudo mount -t debugfs none /sys/kernel/debug", "Mounting debugfs")
            if success:
                mounts['debugfs'] = True
                self.fixes_applied.append("Mounted debugfs")
                logger.info("✅ Successfully mounted debugfs")
            else:
                self.issues.append(f"Cannot mount debugfs: {stderr}")
        
        return mounts
    
    def check_usb_controllers(self) -> Dict[str, bool]:
        """Check USB device controllers"""
        logger.info("🔍 Checking USB device controllers...")
        
        controllers = {
            'udc_available': False,
            'dwc2_controller': False
        }
        
        # Check for UDC (USB Device Controller)
        udc_path = Path("/sys/class/udc")
        if udc_path.exists():
            udc_list = list(udc_path.glob("*"))
            if udc_list:
                controllers['udc_available'] = True
                logger.info(f"✅ Found USB Device Controllers: {[udc.name for udc in udc_list]}")
                
                # Check if any are DWC2
                for udc in udc_list:
                    if 'dwc2' in udc.name:
                        controllers['dwc2_controller'] = True
                        logger.info(f"✅ DWC2 controller available: {udc.name}")
                        break
            else:
                logger.warning("❌ No USB Device Controllers found")
                self.issues.append("No USB Device Controllers available")
        else:
            logger.warning("❌ UDC path does not exist")
            self.issues.append("UDC path missing - USB device mode not supported")
        
        return controllers
    
    def check_raw_gadget_support(self) -> Dict[str, bool]:
        """Check raw-gadget kernel support"""
        logger.info("🔍 Checking raw-gadget support...")
        
        raw_gadget = {
            'module_available': False,
            'device_node': False,
            'permissions_ok': False
        }
        
        # Check if raw-gadget module exists
        success, _, _ = self.run_command("modinfo raw_gadget")
        if success:
            raw_gadget['module_available'] = True
            logger.info("✅ raw-gadget module is available")
            
            # Try to load it
            success, _, stderr = self.run_command("sudo modprobe raw_gadget", "Loading raw-gadget")
            if success:
                self.fixes_applied.append("Loaded raw-gadget module")
                logger.info("✅ raw-gadget module loaded")
            else:
                logger.warning(f"⚠️ Failed to load raw-gadget: {stderr}")
        else:
            logger.warning("❌ raw-gadget module not available")
            self.issues.append("raw-gadget kernel module not available - compile kernel with CONFIG_USB_RAW_GADGET=m")
        
        # Check device node
        raw_gadget_dev = Path("/dev/raw-gadget")
        if raw_gadget_dev.exists():
            raw_gadget['device_node'] = True
            logger.info("✅ /dev/raw-gadget device node exists")
            
            # Check permissions
            try:
                stat_info = raw_gadget_dev.stat()
                # Check if readable/writable by current user or group
                current_uid = os.getuid()
                current_gid = os.getgid()
                
                if stat_info.st_uid == current_uid or stat_info.st_gid == current_gid:
                    raw_gadget['permissions_ok'] = True
                    logger.info("✅ raw-gadget permissions OK")
                else:
                    logger.warning("⚠️ raw-gadget permissions may need adjustment")
                    # Try to fix permissions
                    success, _, _ = self.run_command("sudo chmod 666 /dev/raw-gadget", "Fixing raw-gadget permissions")
                    if success:
                        raw_gadget['permissions_ok'] = True
                        self.fixes_applied.append("Fixed raw-gadget permissions")
                        logger.info("✅ Fixed raw-gadget permissions")
                        
            except Exception as e:
                logger.warning(f"⚠️ Could not check raw-gadget permissions: {e}")
        else:
            logger.warning("❌ /dev/raw-gadget device node missing")
            self.issues.append("/dev/raw-gadget device missing - raw-gadget module not loaded or supported")
        
        return raw_gadget
    
    def setup_usb_gadget(self) -> bool:
        """Setup basic USB gadget to create usb0 interface"""
        logger.info("🔧 Setting up USB gadget for usb0 interface...")
        
        try:
            # Import and use our gadget setup
            from xbox360_gadget import Xbox360Gadget
            
            gadget = Xbox360Gadget("xbox360-test")
            success = gadget.setup_complete_gadget(create_network=True, create_functionfs=False)
            
            if success:
                logger.info("✅ USB gadget setup successful")
                self.fixes_applied.append("Created USB gadget with network function")
                
                # Wait a moment for interface to appear
                import time
                time.sleep(3)
                
                # Check if usb0 interface was created
                if Path("/sys/class/net/usb0").exists():
                    logger.info("✅ usb0 interface created successfully")
                    self.fixes_applied.append("usb0 network interface created")
                    
                    # Configure the interface
                    success, _, _ = self.run_command("sudo ip addr add 192.168.100.1/24 dev usb0", "Configuring usb0 IP")
                    if success:
                        success, _, _ = self.run_command("sudo ip link set usb0 up", "Bringing up usb0")
                        if success:
                            logger.info("✅ usb0 interface configured and up")
                            self.fixes_applied.append("Configured usb0 interface")
                            return True
                else:
                    logger.warning("⚠️ usb0 interface not created")
                    self.issues.append("USB gadget activated but usb0 interface not created")
            else:
                self.issues.append("USB gadget setup failed")
                
        except Exception as e:
            logger.error(f"❌ USB gadget setup failed: {e}")
            self.issues.append(f"USB gadget setup exception: {e}")
        
        return False
    
    def check_usb_interface(self) -> Dict[str, bool]:
        """Check if usb0 interface exists and is configured"""
        logger.info("🔍 Checking usb0 interface...")
        
        interface = {
            'exists': False,
            'is_up': False,
            'has_ip': False
        }
        
        usb0_path = Path("/sys/class/net/usb0")
        if usb0_path.exists():
            interface['exists'] = True
            logger.info("✅ usb0 interface exists")
            
            # Check if interface is up
            success, stdout, _ = self.run_command("ip link show usb0")
            if success and 'UP' in stdout:
                interface['is_up'] = True
                logger.info("✅ usb0 interface is UP")
            else:
                logger.warning("❌ usb0 interface is DOWN")
            
            # Check if interface has IP
            success, stdout, _ = self.run_command("ip addr show usb0")
            if success and 'inet ' in stdout:
                interface['has_ip'] = True
                logger.info("✅ usb0 interface has IP address")
            else:
                logger.warning("❌ usb0 interface has no IP address")
                
        else:
            logger.warning("❌ usb0 interface does not exist")
            self.issues.append("usb0 interface missing - USB gadget not properly configured")
        
        return interface
    
    def diagnose_and_fix(self) -> Dict:
        """Run complete diagnosis and apply fixes"""
        logger.info("🩺 Starting USB system diagnosis and fixes...")
        
        self.system_status = {
            'modules': self.check_kernel_modules(),
            'mounts': self.check_filesystem_mounts(), 
            'controllers': self.check_usb_controllers(),
            'raw_gadget': self.check_raw_gadget_support(),
            'usb_interface': self.check_usb_interface()
        }
        
        # If usb0 doesn't exist, try to create it
        if not self.system_status['usb_interface']['exists']:
            logger.info("🔧 usb0 interface missing - attempting to create...")
            self.setup_usb_gadget()
            # Re-check interface status
            self.system_status['usb_interface'] = self.check_usb_interface()
        
        # Generate summary
        summary = {
            'issues_found': len(self.issues),
            'fixes_applied': len(self.fixes_applied),
            'issues': self.issues,
            'fixes': self.fixes_applied,
            'system_status': self.system_status
        }
        
        logger.info(f"🎯 Diagnosis complete: {len(self.issues)} issues found, {len(self.fixes_applied)} fixes applied")
        
        return summary
    
    def print_report(self, summary: Dict):
        """Print detailed diagnostic report"""
        print("\n" + "="*60)
        print("🩺 USB System Diagnostic Report")
        print("="*60)
        
        print(f"\n📊 Summary:")
        print(f"   Issues found: {summary['issues_found']}")
        print(f"   Fixes applied: {summary['fixes_applied']}")
        
        if summary['fixes']:
            print(f"\n✅ Fixes Applied:")
            for fix in summary['fixes']:
                print(f"   • {fix}")
        
        if summary['issues']:
            print(f"\n❌ Issues Remaining:")
            for issue in summary['issues']:
                print(f"   • {issue}")
        
        print(f"\n🔍 System Status:")
        status = summary['system_status']
        
        print("   Kernel Modules:")
        for module, loaded in status['modules'].items():
            status_icon = "✅" if loaded else "❌"
            print(f"     {status_icon} {module}")
        
        print("   Filesystems:")
        for fs, mounted in status['mounts'].items():
            status_icon = "✅" if mounted else "❌"
            print(f"     {status_icon} {fs}")
        
        print("   USB Controllers:")
        for controller, available in status['controllers'].items():
            status_icon = "✅" if available else "❌"
            print(f"     {status_icon} {controller}")
        
        print("   Raw-gadget Support:")
        for component, available in status['raw_gadget'].items():
            status_icon = "✅" if available else "❌"
            print(f"     {status_icon} {component}")
        
        print("   USB Interface (usb0):")
        for component, available in status['usb_interface'].items():
            status_icon = "✅" if available else "❌"
            print(f"     {status_icon} {component}")
        
        print("\n" + "="*60)
        
        # Recommendations
        if summary['issues']:
            print("💡 Recommendations:")
            
            if any('kernel' in issue.lower() or 'module' in issue.lower() for issue in summary['issues']):
                print("   • Check kernel configuration and rebuild with USB gadget support")
                print("   • Ensure CONFIG_USB_DWC2=m and CONFIG_USB_GADGET=m are enabled")
                
            if any('raw-gadget' in issue.lower() for issue in summary['issues']):
                print("   • Enable CONFIG_USB_RAW_GADGET=m in kernel configuration")
                print("   • Recompile and install kernel with raw-gadget support")
                
            if any('usb0' in issue.lower() for issue in summary['issues']):
                print("   • Check USB cable connection (use USB-C data cable, not power-only)")
                print("   • Verify Pi is connected to host computer via USB-C port")
                print("   • Ensure dtoverlay=dwc2 is in /boot/config.txt")
        else:
            print("🎉 All systems are working correctly!")


def main():
    """Main entry point"""
    import argparse
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    parser = argparse.ArgumentParser(description='USB System Diagnostic and Fixer')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose logging')
    parser.add_argument('--fix', action='store_true', help='Apply fixes automatically')
    parser.add_argument('--report-only', action='store_true', help='Only generate report, do not apply fixes')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    fixer = USBSystemFixer()
    
    try:
        if args.report_only:
            # Just diagnose, don't fix
            fixer.system_status = {
                'modules': fixer.check_kernel_modules(),
                'mounts': fixer.check_filesystem_mounts(),
                'controllers': fixer.check_usb_controllers(), 
                'raw_gadget': fixer.check_raw_gadget_support(),
                'usb_interface': fixer.check_usb_interface()
            }
            summary = {
                'issues_found': len(fixer.issues),
                'fixes_applied': 0,
                'issues': fixer.issues,
                'fixes': [],
                'system_status': fixer.system_status
            }
        else:
            # Full diagnosis and fix
            summary = fixer.diagnose_and_fix()
        
        fixer.print_report(summary)
        
        # Exit with appropriate code
        sys.exit(0 if summary['issues_found'] == 0 else 1)
        
    except KeyboardInterrupt:
        print("\n⚠️ Operation cancelled by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"💥 Diagnostic failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()