#!/usr/bin/env python3
"""
Bullseye System Validator and Testing Script
Comprehensive validation for Pi OS Bullseye ARM64 Xbox 360 WiFi Emulator
"""

import os
import sys
import subprocess
import platform
from pathlib import Path
from datetime import datetime
import json

class BullseyeSystemValidator:
    """Comprehensive system validator for Pi OS Bullseye ARM64"""
    
    def __init__(self):
        self.setup_logging()
        self.validation_results = {}
        self.system_info = {}
        self.recommendations = []
        
    def setup_logging(self):
        """Setup validation logging"""
        # Bullseye logging paths
        possible_log_dirs = [
            Path.home() / "desktop" / "debuglogs",
            Path.home() / "Desktop" / "debuglogs",
            Path("/home/pi/desktop/debuglogs"),
            Path("/home/pi/Desktop/debuglogs"),
            Path.home() / "debuglogs"
        ]
        
        self.debug_log_dir = None
        for path in possible_log_dirs:
            if path.parent.exists():
                self.debug_log_dir = path
                break
        
        if not self.debug_log_dir:
            self.debug_log_dir = Path.home() / "desktop" / "debuglogs"
        
        self.debug_log_dir.mkdir(parents=True, exist_ok=True)
        
        # Create validation log
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_file = self.debug_log_dir / f"bullseye_validation_{timestamp}.log"
        self.log_buffer = []
        
        self.log("🔍 Pi OS Bullseye ARM64 System Validation", "INFO")
        self.log("=" * 60, "INFO")
        self.log(f"Validation started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", "INFO")
        self.log(f"Log file: {self.log_file}", "INFO")
        self.log("=" * 60, "INFO")
    
    def log(self, message: str, level: str = "INFO"):
        """Enhanced logging with colors"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] [{level}] {message}"
        self.log_buffer.append(log_entry + "\n")
        
        # Console colors
        colors = {
            "INFO": "\033[0;36m",      # Cyan
            "SUCCESS": "\033[0;32m",   # Green
            "WARNING": "\033[1;33m",   # Yellow
            "ERROR": "\033[0;31m",     # Red
            "DEBUG": "\033[0;37m",     # White
            "CRITICAL": "\033[1;35m"   # Magenta
        }
        
        color = colors.get(level, "\033[0m")
        print(f"{color}[{timestamp}] {message}\033[0m")
        
        # Flush important messages
        if len(self.log_buffer) >= 5 or level in ['ERROR', 'SUCCESS', 'CRITICAL']:
            self.flush_log()
    
    def flush_log(self):
        """Write log buffer to file"""
        try:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.writelines(self.log_buffer)
            self.log_buffer = []
        except Exception as e:
            print(f"Warning: Could not write to log file: {e}")
    
    def run_command(self, cmd: str, description: str = "", timeout: int = 30):
        """Run command and return result"""
        if description:
            self.log(f"🔧 {description}", "DEBUG")
        
        try:
            result = subprocess.run(
                cmd, shell=True, capture_output=True,
                text=True, timeout=timeout
            )
            return result
        except subprocess.TimeoutExpired:
            self.log(f"⏰ Command timed out: {cmd}", "WARNING")
            return None
        except Exception as e:
            self.log(f"❌ Command failed: {cmd} - {e}", "ERROR")
            return None
    
    def validate_os_version(self):
        """Validate Pi OS Bullseye"""
        self.log("\n🔍 VALIDATING PI OS VERSION", "INFO")
        self.log("-" * 30, "INFO")
        
        try:
            with open('/etc/os-release', 'r') as f:
                os_content = f.read()
            
            is_bullseye = 'bullseye' in os_content.lower()
            is_raspberry_pi_os = 'raspberry pi os' in os_content.lower()
            
            # Extract version info
            os_info = {}
            for line in os_content.split('\n'):
                if '=' in line:
                    key, value = line.split('=', 1)
                    os_info[key] = value.strip('"')
            
            self.system_info['os_info'] = os_info
            
            if is_bullseye and is_raspberry_pi_os:
                self.log("✅ Pi OS Bullseye confirmed", "SUCCESS")
                self.validation_results['os_version'] = "PASS"
            elif is_bullseye:
                self.log("⚠️ Bullseye detected but may not be Pi OS", "WARNING")
                self.validation_results['os_version'] = "WARNING"
                self.recommendations.append("Ensure you're running official Raspberry Pi OS")
            else:
                self.log("❌ Not running Pi OS Bullseye", "ERROR")
                self.validation_results['os_version'] = "FAIL"
                self.recommendations.append("Install Pi OS Bullseye for best compatibility")
            
            # Log version details
            pretty_name = os_info.get('PRETTY_NAME', 'Unknown')
            version_id = os_info.get('VERSION_ID', 'Unknown')
            self.log(f"OS: {pretty_name}", "INFO")
            self.log(f"Version ID: {version_id}", "INFO")
            
        except Exception as e:
            self.log(f"❌ Could not read OS version: {e}", "ERROR")
            self.validation_results['os_version'] = "ERROR"
            self.recommendations.append("Check OS installation integrity")
    
    def validate_architecture(self):
        """Validate ARM64 architecture"""
        self.log("\n🔍 VALIDATING ARCHITECTURE", "INFO")
        self.log("-" * 25, "INFO")
        
        arch = platform.machine()
        self.system_info['architecture'] = arch
        
        if arch in ['aarch64', 'arm64']:
            self.log(f"✅ ARM64 architecture confirmed: {arch}", "SUCCESS")
            self.validation_results['architecture'] = "PASS"
        elif 'arm' in arch.lower():
            self.log(f"⚠️ ARM architecture detected but not 64-bit: {arch}", "WARNING")
            self.validation_results['architecture'] = "WARNING"
            self.recommendations.append("Consider upgrading to 64-bit Pi OS for better performance")
        else:
            self.log(f"❌ Non-ARM architecture: {arch}", "ERROR")
            self.validation_results['architecture'] = "FAIL"
            self.recommendations.append("This software is designed for ARM-based Raspberry Pi")
        
        # Additional architecture info
        result = self.run_command("uname -a", "Getting kernel info")
        if result and result.returncode == 0:
            kernel_info = result.stdout.strip()
            self.system_info['kernel'] = kernel_info
            self.log(f"Kernel: {kernel_info}", "INFO")
    
    def validate_hardware(self):
        """Validate Raspberry Pi hardware"""
        self.log("\n🔍 VALIDATING HARDWARE", "INFO")
        self.log("-" * 20, "INFO")
        
        try:
            with open('/proc/cpuinfo', 'r') as f:
                cpuinfo = f.read()
            
            if 'Raspberry Pi' in cpuinfo:
                # Extract model info
                for line in cpuinfo.split('\n'):
                    if 'Model' in line:
                        model = line.split(':')[1].strip()
                        self.system_info['pi_model'] = model
                        self.log(f"✅ Pi hardware confirmed: {model}", "SUCCESS")
                        
                        # Check if it's a Pi 4 or newer for best compatibility
                        if 'Pi 4' in model or 'Pi 5' in model:
                            self.validation_results['hardware'] = "PASS"
                        else:
                            self.validation_results['hardware'] = "WARNING"
                            self.recommendations.append("Pi 4 or newer recommended for optimal performance")
                        break
                else:
                    self.log("✅ Raspberry Pi hardware confirmed (model unknown)", "SUCCESS")
                    self.validation_results['hardware'] = "PASS"
            else:
                self.log("⚠️ Non-Pi hardware detected", "WARNING")
                self.validation_results['hardware'] = "WARNING"
                self.recommendations.append("Testing on non-Pi hardware may have limitations")
            
            # Check memory
            with open('/proc/meminfo', 'r') as f:
                for line in f:
                    if 'MemTotal' in line:
                        mem_kb = int(line.split()[1])
                        mem_gb = round(mem_kb / 1024 / 1024, 1)
                        self.system_info['memory_gb'] = mem_gb
                        self.log(f"Memory: {mem_gb} GB", "INFO")
                        
                        if mem_gb < 2:
                            self.recommendations.append("2GB+ RAM recommended for stable operation")
                        break
                        
        except Exception as e:
            self.log(f"❌ Hardware detection failed: {e}", "ERROR")
            self.validation_results['hardware'] = "ERROR"
    
    def validate_python_environment(self):
        """Validate Python environment for Bullseye"""
        self.log("\n🔍 VALIDATING PYTHON ENVIRONMENT", "INFO")
        self.log("-" * 35, "INFO")
        
        # Python version
        python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        self.system_info['python_version'] = python_version
        self.log(f"Python version: {python_version}", "INFO")
        
        if sys.version_info >= (3, 9):
            self.log("✅ Python version is compatible", "SUCCESS")
            python_status = "PASS"
        else:
            self.log("⚠️ Python version may be too old", "WARNING")
            python_status = "WARNING"
            self.recommendations.append("Python 3.9+ recommended")
        
        # Test pip (externally-managed-environment check) 
        result = self.run_command("python3 -m pip --version", "Testing pip")
        if result and result.returncode == 0:
            self.log("✅ pip is working", "SUCCESS")
        else:
            if result and "externally-managed-environment" in result.stderr:
                self.log("⚠️ externally-managed-environment detected (normal for Bullseye)", "WARNING")
                self.recommendations.append("Use system packages (apt) or virtual environments")
            else:
                self.log("❌ pip issues detected", "ERROR")
                python_status = "FAIL"
        
        # Test tkinter
        try:
            import tkinter
            self.log("✅ tkinter available (GUI support)", "SUCCESS")
        except ImportError:
            self.log("❌ tkinter not available", "ERROR")
            python_status = "FAIL"
            self.recommendations.append("Install python3-tk package")
        
        self.validation_results['python'] = python_status
    
    def validate_boot_configuration(self):
        """Validate boot configuration for Bullseye"""
        self.log("\n🔍 VALIDATING BOOT CONFIGURATION", "INFO")
        self.log("-" * 35, "INFO")
        
        # Bullseye uses /boot/ not /boot/firmware/
        boot_config = Path("/boot/config.txt")
        boot_cmdline = Path("/boot/cmdline.txt")
        
        boot_status = "PASS"
        
        # Check config.txt
        if boot_config.exists():
            self.log(f"✅ Boot config found: {boot_config}", "SUCCESS")
            
            try:
                with open(boot_config, 'r') as f:
                    config_content = f.read()
                
                # Check for DWC2 configuration
                if "dtoverlay=dwc2" in config_content:
                    self.log("✅ DWC2 overlay configured", "SUCCESS")
                else:
                    self.log("⚠️ DWC2 overlay not configured", "WARNING")
                    boot_status = "WARNING"
                    self.recommendations.append("Run comprehensive Bullseye fix to configure DWC2")
                
                # Check for OTG mode
                if "dr_mode=otg" in config_content:
                    self.log("✅ OTG mode configured", "SUCCESS")
                else:
                    self.log("⚠️ OTG mode not configured", "WARNING")
                    
            except Exception as e:
                self.log(f"❌ Could not read boot config: {e}", "ERROR")
                boot_status = "ERROR"
        else:
            self.log(f"❌ Boot config not found: {boot_config}", "ERROR")
            boot_status = "FAIL"
            self.recommendations.append("Check Bullseye installation - boot config missing")
        
        # Check cmdline.txt
        if boot_cmdline.exists():
            self.log(f"✅ Boot cmdline found: {boot_cmdline}", "SUCCESS")
        else:
            self.log(f"⚠️ Boot cmdline not found: {boot_cmdline}", "WARNING")
        
        self.validation_results['boot_config'] = boot_status
    
    def validate_usb_modules(self):
        """Validate USB module availability"""
        self.log("\n🔍 VALIDATING USB MODULES", "INFO")
        self.log("-" * 25, "INFO")
        
        # Check if modules are loaded
        result = self.run_command("lsmod", "Checking loaded modules")
        if result and result.returncode == 0:
            loaded_modules = result.stdout
            
            dwc2_loaded = 'dwc2' in loaded_modules
            libcomposite_loaded = 'libcomposite' in loaded_modules
            
            if dwc2_loaded:
                self.log("✅ DWC2 module is loaded", "SUCCESS")
            else:
                self.log("⚠️ DWC2 module not loaded", "WARNING")
            
            if libcomposite_loaded:
                self.log("✅ libcomposite module is loaded", "SUCCESS")
            else:
                self.log("⚠️ libcomposite module not loaded", "WARNING")
            
            if dwc2_loaded and libcomposite_loaded:
                self.validation_results['usb_modules'] = "PASS"
            elif dwc2_loaded or libcomposite_loaded:
                self.validation_results['usb_modules'] = "WARNING"
                self.recommendations.append("Reboot may be needed for all USB modules to load")
            else:
                self.validation_results['usb_modules'] = "FAIL"
                self.recommendations.append("Run comprehensive Bullseye fix to configure USB modules")
        
        # Check USB device controllers
        udc_path = Path('/sys/class/udc/')
        if udc_path.exists():
            udcs = list(udc_path.glob('*'))
            if udcs:
                self.log(f"✅ USB device controllers found: {len(udcs)}", "SUCCESS")
                for udc in udcs:
                    self.log(f"   • {udc.name}", "SUCCESS")
            else:
                self.log("⚠️ No USB device controllers found", "WARNING")
                self.recommendations.append("USB gadget functionality may not be available")
        else:
            self.log("❌ USB device controller path missing", "ERROR")
    
    def validate_network_configuration(self):
        """Validate network configuration"""
        self.log("\n🔍 VALIDATING NETWORK CONFIGURATION", "INFO")  
        self.log("-" * 35, "INFO")
        
        # Check for usb0 interface
        result = self.run_command("ip link show usb0", "Checking usb0 interface")
        if result and result.returncode == 0:
            if "UP" in result.stdout:
                self.log("✅ usb0 interface is UP", "SUCCESS")
                self.validation_results['network'] = "PASS"
            else:
                self.log("⚠️ usb0 interface is DOWN", "WARNING")
                self.validation_results['network'] = "WARNING"
        else:
            self.log("⚠️ usb0 interface not found (normal if not configured)", "WARNING")
            self.validation_results['network'] = "WARNING"
            self.recommendations.append("usb0 interface will be created after proper configuration")
        
        # Check NetworkManager configuration
        nm_config = Path("/etc/NetworkManager/conf.d/99-xbox360-emulator-bullseye.conf")
        if nm_config.exists():
            self.log("✅ NetworkManager configuration found", "SUCCESS")
        else:
            self.log("⚠️ NetworkManager configuration not found", "WARNING")
    
    def validate_project_files(self):
        """Validate project files presence"""
        self.log("\n🔍 VALIDATING PROJECT FILES", "INFO")
        self.log("-" * 30, "INFO")
        
        current_dir = Path.cwd()
        self.log(f"Current directory: {current_dir}", "INFO")
        
        # Check for required files
        required_files = [
            "installer.py",
            "comprehensive_bullseye_fix.py", 
            "fix_desktop_paths_bullseye.py"
        ]
        
        project_status = "PASS"
        
        for filename in required_files:
            file_path = current_dir / filename
            if file_path.exists():
                self.log(f"✅ Found: {filename}", "SUCCESS")
            else:
                self.log(f"❌ Missing: {filename}", "ERROR")
                project_status = "FAIL"
        
        # Check for desktop files
        desktop_files = list(current_dir.glob("*Bullseye*.desktop"))
        if desktop_files:
            self.log(f"✅ Found {len(desktop_files)} Bullseye desktop files", "SUCCESS")
        else:
            self.log("⚠️ No Bullseye desktop files found", "WARNING")
            self.recommendations.append("Run fix_desktop_paths_bullseye.py to create desktop files")
        
        self.validation_results['project_files'] = project_status
    
    def generate_validation_report(self):
        """Generate comprehensive validation report"""
        self.log("\n📊 VALIDATION REPORT SUMMARY", "INFO")
        self.log("=" * 50, "INFO")
        
        # Count results
        pass_count = sum(1 for result in self.validation_results.values() if result == "PASS")
        warning_count = sum(1 for result in self.validation_results.values() if result == "WARNING")
        fail_count = sum(1 for result in self.validation_results.values() if result == "FAIL")
        error_count = sum(1 for result in self.validation_results.values() if result == "ERROR")
        
        total_checks = len(self.validation_results)
        
        self.log(f"Total validation checks: {total_checks}", "INFO")
        self.log(f"✅ Passed: {pass_count}", "SUCCESS")
        self.log(f"⚠️ Warnings: {warning_count}", "WARNING")
        self.log(f"❌ Failed: {fail_count}", "ERROR")
        self.log(f"💥 Errors: {error_count}", "ERROR")
        
        # Overall status
        if fail_count == 0 and error_count == 0:
            if warning_count == 0:
                overall_status = "EXCELLENT"
                self.log("\n🎉 OVERALL STATUS: EXCELLENT", "SUCCESS")
                self.log("System is fully optimized for Bullseye!", "SUCCESS")
            else:
                overall_status = "GOOD"
                self.log("\n✅ OVERALL STATUS: GOOD", "SUCCESS")
                self.log("System is ready with minor optimizations available", "SUCCESS")
        elif fail_count <= 2:
            overall_status = "NEEDS_FIXES"
            self.log("\n⚠️ OVERALL STATUS: NEEDS FIXES", "WARNING")
            self.log("Run comprehensive Bullseye fix to resolve issues", "WARNING")
        else:
            overall_status = "CRITICAL"
            self.log("\n❌ OVERALL STATUS: CRITICAL", "ERROR")
            self.log("Multiple critical issues found", "ERROR")
        
        # Detailed results
        self.log("\n📋 DETAILED VALIDATION RESULTS:", "INFO")
        for check, result in self.validation_results.items():
            status_icon = {
                "PASS": "✅",
                "WARNING": "⚠️", 
                "FAIL": "❌",
                "ERROR": "💥"
            }.get(result, "❓")
            
            self.log(f"   {status_icon} {check.replace('_', ' ').title()}: {result}", "INFO")
        
        # Recommendations
        if self.recommendations:
            self.log(f"\n💡 RECOMMENDATIONS ({len(self.recommendations)}):", "INFO")
            for i, recommendation in enumerate(self.recommendations, 1):
                self.log(f"   {i}. {recommendation}", "INFO")
        
        return {
            'overall_status': overall_status,
            'total_checks': total_checks,
            'pass_count': pass_count,
            'warning_count': warning_count,
            'fail_count': fail_count,
            'error_count': error_count,
            'validation_results': self.validation_results,
            'system_info': self.system_info,
            'recommendations': self.recommendations
        }
    
    def save_validation_report(self, report):
        """Save validation report to JSON"""
        try:
            report_file = self.debug_log_dir / f"bullseye_validation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(report_file, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            
            self.log(f"\n📄 Validation report saved: {report_file}", "SUCCESS")
            return report_file
        except Exception as e:
            self.log(f"⚠️ Could not save validation report: {e}", "WARNING")
            return None
    
    def run_comprehensive_validation(self):
        """Run all validation checks"""
        try:
            self.log("🚀 Starting comprehensive Bullseye validation...", "INFO")
            
            # Run all validation checks
            self.validate_os_version()
            self.validate_architecture() 
            self.validate_hardware()
            self.validate_python_environment()
            self.validate_boot_configuration()
            self.validate_usb_modules()
            self.validate_network_configuration()
            self.validate_project_files()
            
            # Generate report
            report = self.generate_validation_report()
            
            # Save report
            report_file = self.save_validation_report(report)
            
            self.log("\n" + "=" * 60, "INFO")
            self.log("🎯 COMPREHENSIVE BULLSEYE VALIDATION COMPLETE!", "SUCCESS")
            self.log("=" * 60, "INFO")
            
            return report
            
        except Exception as e:
            self.log(f"❌ Validation failed: {e}", "ERROR")
            import traceback
            self.log(traceback.format_exc(), "ERROR")
            return None
        finally:
            self.flush_log()

def main():
    """Main validation function"""
    print("🔍 Xbox 360 WiFi Emulator - Pi OS Bullseye ARM64 System Validation")
    print("=" * 70)
    print("🎯 Comprehensive validation for optimal Bullseye compatibility")
    print("📝 All results logged to debuglogs directory")
    print()
    
    validator = BullseyeSystemValidator()
    report = validator.run_comprehensive_validation()
    
    print(f"\n📂 Complete validation log: {validator.log_file}")
    
    if report:
        overall = report['overall_status']
        if overall == "EXCELLENT":
            print("\n🎉 System validation: EXCELLENT!")
            print("💡 Your Bullseye system is fully optimized")
        elif overall == "GOOD":
            print("\n✅ System validation: GOOD!")
            print("💡 Minor optimizations available - check recommendations")
        elif overall == "NEEDS_FIXES":
            print("\n⚠️ System validation: NEEDS FIXES")
            print("💡 Run: python3 comprehensive_bullseye_fix.py")
        else:
            print("\n❌ System validation: CRITICAL ISSUES")
            print("💡 Multiple issues found - check log for details")
    else:
        print("\n❌ Validation failed - check log file for details")

if __name__ == "__main__":
    main()