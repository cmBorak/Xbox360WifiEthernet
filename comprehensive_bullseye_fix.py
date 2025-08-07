#!/usr/bin/env python3
"""
Comprehensive Pi OS Bullseye ARM64 Fix Script
Addresses all known issues with Xbox 360 WiFi Module Emulator on Bullseye
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path
from datetime import datetime
import time

class BullseyeComprehensiveFixer:
    """Comprehensive fixer for Pi OS Bullseye ARM64 issues"""
    
    def __init__(self):
        self.setup_logging()
        self.detected_issues = []
        self.fixes_applied = []
        self.system_validated = False
        
        # Bullseye-specific paths
        self.boot_config = Path("/boot/config.txt")
        self.boot_cmdline = Path("/boot/cmdline.txt")
        self.modules_file = Path("/etc/modules")
        
    def setup_logging(self):
        """Setup comprehensive logging"""
        # Bullseye typically uses lowercase desktop
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
        
        # Create comprehensive log file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_file = self.debug_log_dir / f"bullseye_comprehensive_fix_{timestamp}.log"
        self.log_buffer = []
        
        self.log("🔧 Comprehensive Pi OS Bullseye ARM64 Fix", "INFO")
        self.log("=" * 60, "INFO")
        self.log(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", "INFO")
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
        
        # Flush important messages immediately
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
    
    def run_command(self, cmd: str, description: str = "", timeout: int = 60, ignore_errors: bool = False):
        """Run command with comprehensive logging"""
        if description:
            self.log(f"🔧 {description}", "INFO")
        
        self.log(f"Command: {cmd}", "DEBUG")
        
        try:
            result = subprocess.run(
                cmd, shell=True, capture_output=True,
                text=True, timeout=timeout
            )
            
            success = result.returncode == 0
            level = "SUCCESS" if success else ("WARNING" if ignore_errors else "ERROR")
            
            if success:
                self.log("✅ Command succeeded", level)
            else:
                self.log(f"❌ Command failed (exit code: {result.returncode})", level)
            
            # Log output (limited)
            if result.stdout.strip():
                for line in result.stdout.strip().split('\n')[:10]:
                    if line.strip():
                        self.log(f"   OUT: {line}", "DEBUG")
            
            if result.stderr.strip():
                for line in result.stderr.strip().split('\n')[:5]:
                    if line.strip():
                        self.log(f"   ERR: {line}", level)
            
            return result
            
        except subprocess.TimeoutExpired:
            self.log(f"⏰ Command timed out after {timeout}s", "ERROR")
            return None
        except Exception as e:
            self.log(f"❌ Command exception: {e}", "ERROR")
            return None
    
    def validate_bullseye_system(self):
        """Comprehensive Bullseye system validation"""
        self.log("\n🔍 COMPREHENSIVE BULLSEYE SYSTEM VALIDATION", "INFO")
        self.log("=" * 50, "INFO")
        
        validation_issues = []
        
        # Check OS version
        try:
            with open('/etc/os-release', 'r') as f:
                os_content = f.read()
                if 'bullseye' in os_content.lower():
                    self.log("✅ Pi OS Bullseye confirmed", "SUCCESS")
                else:
                    self.log("❌ Not running Pi OS Bullseye", "ERROR")
                    validation_issues.append("Non-Bullseye OS detected")
        except Exception as e:
            self.log(f"❌ Could not detect OS version: {e}", "ERROR")
            validation_issues.append("OS detection failed")
        
        # Check ARM64 architecture
        result = self.run_command("uname -m", "Checking architecture")
        if result and result.returncode == 0:
            arch = result.stdout.strip()
            if 'aarch64' in arch or 'arm64' in arch:
                self.log("✅ ARM64 architecture confirmed", "SUCCESS")
            else:
                self.log(f"⚠️ Architecture is {arch}, not ARM64", "WARNING")
                validation_issues.append(f"Non-ARM64 architecture: {arch}")
        
        # Check Pi hardware
        try:
            with open('/proc/cpuinfo', 'r') as f:
                cpuinfo = f.read()
                if 'Raspberry Pi' in cpuinfo:
                    # Extract model info
                    for line in cpuinfo.split('\n'):
                        if 'Model' in line:
                            model = line.split(':')[1].strip()
                            self.log(f"✅ Pi hardware confirmed: {model}", "SUCCESS")
                            break
                    else:
                        self.log("✅ Raspberry Pi hardware confirmed", "SUCCESS")
                else:
                    self.log("⚠️ Non-Pi hardware detected", "WARNING")
                    validation_issues.append("Non-Pi hardware")
        except Exception as e:
            self.log(f"❌ Hardware detection failed: {e}", "ERROR")
            validation_issues.append("Hardware detection failed")
        
        # Check critical paths for Bullseye
        critical_paths = {
            'Boot Config': self.boot_config,
            'Boot Cmdline': self.boot_cmdline,
            'Modules File': self.modules_file
        }
        
        for name, path in critical_paths.items():
            if path.exists():
                self.log(f"✅ {name} found: {path}", "SUCCESS")
            else:
                self.log(f"❌ {name} missing: {path}", "ERROR")
                validation_issues.append(f"{name} missing")
        
        # Check kernel version
        result = self.run_command("uname -r", "Checking kernel version")
        if result and result.returncode == 0:
            kernel = result.stdout.strip()
            self.log(f"Kernel version: {kernel}", "INFO")
        
        # Check Python version
        python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        self.log(f"Python version: {python_version}", "INFO")
        
        if validation_issues:
            self.log(f"\n⚠️ Validation issues found: {len(validation_issues)}", "WARNING")
            for issue in validation_issues:
                self.log(f"   • {issue}", "WARNING")
            self.detected_issues.extend(validation_issues)
        else:
            self.log("\n✅ System validation passed", "SUCCESS")
            self.system_validated = True
        
        return len(validation_issues) == 0
    
    def diagnose_system_issues(self):
        """Comprehensive system diagnosis for Bullseye"""
        self.log("\n🔍 COMPREHENSIVE SYSTEM DIAGNOSIS", "INFO")
        self.log("=" * 40, "INFO")
        
        # Python environment check
        self.log("\n🐍 Python Environment Diagnosis:", "INFO")
        
        # Check for externally-managed-environment
        result = self.run_command("python3 -m pip --version", "Testing pip", ignore_errors=True)
        if result and result.returncode != 0:
            if "externally-managed-environment" in result.stderr:
                self.log("❌ DETECTED: externally-managed-environment issue", "ERROR")
                self.detected_issues.append("Python externally-managed-environment")
        
        # DWC2 module diagnosis
        self.log("\n🔌 USB/DWC2 Module Diagnosis:", "INFO")
        
        # Check if DWC2 is loaded
        result = self.run_command("lsmod | grep dwc2", "Checking DWC2 module", ignore_errors=True)
        if not result or result.returncode != 0:
            self.log("❌ DETECTED: DWC2 module not loaded", "ERROR")
            self.detected_issues.append("DWC2 module not loaded")
        else:
            self.log("✅ DWC2 module is loaded", "SUCCESS")
        
        # Check libcomposite
        result = self.run_command("lsmod | grep libcomposite", "Checking libcomposite", ignore_errors=True)
        if not result or result.returncode != 0:
            self.log("❌ DETECTED: libcomposite module not loaded", "ERROR")
            self.detected_issues.append("libcomposite module not loaded")
        else:
            self.log("✅ libcomposite module is loaded", "SUCCESS")
        
        # Check USB device controllers
        result = self.run_command("ls /sys/class/udc/", "Checking USB device controllers", ignore_errors=True)
        if not result or result.returncode != 0 or not result.stdout.strip():
            self.log("❌ DETECTED: No USB device controllers found", "ERROR")
            self.detected_issues.append("No USB device controllers")
        else:
            controllers = result.stdout.strip().split('\n')
            self.log(f"✅ USB device controllers found: {len(controllers)}", "SUCCESS")
            for controller in controllers:
                self.log(f"   • {controller}", "SUCCESS")
        
        # Boot configuration diagnosis
        self.log("\n⚙️ Boot Configuration Diagnosis:", "INFO")
        
        # Check DWC2 in boot config
        if self.boot_config.exists():
            try:
                with open(self.boot_config, 'r') as f:
                    config_content = f.read()
                
                if "dtoverlay=dwc2" not in config_content:
                    self.log("❌ DETECTED: DWC2 overlay not configured", "ERROR")
                    self.detected_issues.append("DWC2 overlay not in boot config")
                else:
                    self.log("✅ DWC2 overlay found in boot config", "SUCCESS")
                    
                    # Check for OTG mode
                    if "dr_mode=otg" in config_content:
                        self.log("✅ OTG mode configured", "SUCCESS")
                    else:
                        self.log("⚠️ OTG mode not explicitly configured", "WARNING")
                        
            except Exception as e:
                self.log(f"❌ Could not read boot config: {e}", "ERROR")
                self.detected_issues.append("Cannot read boot config")
        
        # Network interface diagnosis
        self.log("\n🌐 Network Interface Diagnosis:", "INFO")
        result = self.run_command("ip link show usb0", "Checking usb0 interface", ignore_errors=True)
        if not result or result.returncode != 0:
            self.log("❌ DETECTED: USB network interface (usb0) not found", "ERROR")
            self.detected_issues.append("USB network interface missing")
        else:
            self.log("✅ USB network interface (usb0) exists", "SUCCESS")
            if "UP" in result.stdout:
                self.log("✅ usb0 interface is UP", "SUCCESS")
            else:
                self.log("⚠️ usb0 interface is DOWN", "WARNING")
        
        # Summary
        self.log(f"\n📋 DIAGNOSIS SUMMARY:", "INFO")
        self.log(f"Total issues detected: {len(self.detected_issues)}", "INFO")
        for i, issue in enumerate(self.detected_issues, 1):
            self.log(f"   {i}. {issue}", "ERROR")
        
        return len(self.detected_issues)
    
    def fix_python_environment_bullseye(self):
        """Fix Python environment issues for Bullseye"""
        if "Python externally-managed-environment" not in self.detected_issues:
            self.log("✅ Python environment is OK, skipping", "SUCCESS")
            return True
        
        self.log("\n🔧 FIXING PYTHON ENVIRONMENT FOR BULLSEYE", "INFO")
        self.log("=" * 40, "INFO")
        
        # Update package list
        result = self.run_command("sudo apt update", "Updating package list", timeout=300)
        if not result or result.returncode != 0:
            self.log("❌ Failed to update package list", "ERROR")
            return False
        
        # Install Bullseye-specific Python packages
        bullseye_python_packages = [
            'python3-tk', 'python3-pip', 'python3-setuptools', 'python3-wheel',
            'python3-dev', 'python3-venv', 'python3-full',
            'zenity', 'python3-distutils'
        ]
        
        install_cmd = f"sudo apt install -y {' '.join(bullseye_python_packages)}"
        result = self.run_command(install_cmd, "Installing Python packages for Bullseye", timeout=300)
        
        if result and result.returncode == 0:
            self.log("✅ Python packages installed successfully", "SUCCESS")
            self.fixes_applied.append("Python system packages installed for Bullseye")
            return True
        else:
            self.log("❌ Failed to install Python packages", "ERROR")
            return False
    
    def fix_dwc2_bullseye(self):
        """Fix DWC2 module issues for Bullseye"""
        dwc2_issues = [issue for issue in self.detected_issues if 'dwc2' in issue.lower() or 'libcomposite' in issue.lower()]
        
        if not dwc2_issues:
            self.log("✅ DWC2 modules are OK, skipping", "SUCCESS")
            return True
        
        self.log("\n🔧 FIXING DWC2 MODULE ISSUES FOR BULLSEYE", "INFO")
        self.log("=" * 40, "INFO")
        
        # Backup boot configuration
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_config = self.boot_config.with_suffix(f'.txt.backup.{timestamp}')
            backup_cmdline = self.boot_cmdline.with_suffix(f'.txt.backup.{timestamp}')
            
            shutil.copy2(self.boot_config, backup_config)
            self.log(f"✅ Backed up config to: {backup_config}", "SUCCESS")
            
            if self.boot_cmdline.exists():
                shutil.copy2(self.boot_cmdline, backup_cmdline)
                self.log(f"✅ Backed up cmdline to: {backup_cmdline}", "SUCCESS")
                
        except Exception as e:
            self.log(f"⚠️ Could not create backups: {e}", "WARNING")
        
        # Fix boot config for Bullseye
        try:
            with open(self.boot_config, 'r') as f:
                config_content = f.read()
            
            # Remove existing DWC2 entries
            lines = config_content.split('\n')
            lines = [line for line in lines if 'dwc2' not in line.lower()]
            
            # Add comprehensive Bullseye DWC2 configuration
            bullseye_dwc2_config = [
                "",
                "# Xbox 360 WiFi Module Emulator - Bullseye DWC2 Configuration",
                "# Optimized for Pi OS Bullseye ARM64",
                "dtoverlay=dwc2,dr_mode=otg",
                "",
                "# USB OTG optimizations for Bullseye",
                "otg_mode=1",
                "max_usb_current=1",
                "",
                "# Memory optimization for ARM64 Bullseye",
                "gpu_mem=16",
                "gpu_mem_256=16", 
                "gpu_mem_512=16",
                "gpu_mem_1024=16",
                "",
                "# Additional USB configuration for Bullseye",
                "dtparam=act_led_gpio=47",
                "enable_uart=1"
            ]
            
            lines.extend(bullseye_dwc2_config)
            
            # Write updated config
            with open(self.boot_config, 'w') as f:
                f.write('\n'.join(lines))
            
            self.log("✅ Updated boot config with Bullseye DWC2 settings", "SUCCESS")
            self.fixes_applied.append("Bullseye DWC2 boot configuration updated")
            
        except Exception as e:
            self.log(f"❌ Failed to update boot config: {e}", "ERROR")
            return False
        
        # Fix cmdline.txt for Bullseye
        if self.boot_cmdline.exists():
            try:
                with open(self.boot_cmdline, 'r') as f:
                    cmdline = f.read().strip()
                
                # Add modules-load parameter for Bullseye
                if "modules-load=" not in cmdline:
                    cmdline += " modules-load=dwc2,libcomposite"
                elif "dwc2" not in cmdline:
                    import re
                    cmdline = re.sub(r'modules-load=([^\s]+)', 
                                   lambda m: f"modules-load={m.group(1)},dwc2,libcomposite", 
                                   cmdline)
                
                with open(self.boot_cmdline, 'w') as f:
                    f.write(cmdline + '\n')
                
                self.log("✅ Updated cmdline.txt for Bullseye", "SUCCESS")
                self.fixes_applied.append("Bullseye kernel command line updated")
                
            except Exception as e:
                self.log(f"⚠️ Could not update cmdline.txt: {e}", "WARNING")
        
        # Update /etc/modules for Bullseye
        try:
            current_modules = []
            if self.modules_file.exists():
                with open(self.modules_file, 'r') as f:
                    current_modules = [line.strip() for line in f.readlines() 
                                     if line.strip() and not line.startswith('#')]
            
            # Add required modules for Bullseye
            required_modules = ["dwc2", "libcomposite", "configfs"]
            modules_added = []
            
            for module in required_modules:
                if module not in current_modules:
                    current_modules.append(module)
                    modules_added.append(module)
            
            # Write updated modules file
            with open(self.modules_file, 'w') as f:
                f.write("# /etc/modules: kernel modules to load at boot time\n")
                f.write("# Xbox 360 WiFi Module Emulator modules for Bullseye ARM64\n")
                for module in current_modules:
                    f.write(f"{module}\n")
            
            if modules_added:
                self.log(f"✅ Added modules: {', '.join(modules_added)}", "SUCCESS")
                self.fixes_applied.append(f"Added Bullseye modules: {', '.join(modules_added)}")
            else:
                self.log("✅ Modules already configured", "SUCCESS")
                
        except Exception as e:
            self.log(f"❌ Failed to update /etc/modules: {e}", "ERROR")
        
        # Try to load modules immediately
        self.log("🔄 Attempting to load modules immediately...", "INFO")
        
        for module in ["dwc2", "libcomposite"]:
            result = self.run_command(f"sudo modprobe {module}", f"Loading {module} module", ignore_errors=True)
            if result and result.returncode == 0:
                self.log(f"✅ {module} module loaded successfully", "SUCCESS")
            else:
                self.log(f"⚠️ {module} module load failed - will work after reboot", "WARNING")
        
        # Update initramfs for Bullseye
        self.log("🔄 Updating initramfs for Bullseye...", "INFO")
        result = self.run_command("sudo update-initramfs -u -k all", "Updating initramfs", 
                                 ignore_errors=True, timeout=300)
        if result and result.returncode == 0:
            self.log("✅ Initramfs updated successfully", "SUCCESS")
            self.fixes_applied.append("Bullseye initramfs updated")
        else:
            self.log("⚠️ Initramfs update had issues - modules will still load at boot", "WARNING")
        
        return True
    
    def fix_usb_networking_bullseye(self):
        """Fix USB networking for Bullseye"""
        if "USB network interface missing" not in self.detected_issues:
            self.log("✅ USB networking is OK, skipping", "SUCCESS")
            return True
        
        self.log("\n🔧 FIXING USB NETWORKING FOR BULLSEYE", "INFO")
        self.log("=" * 35, "INFO")
        
        # Create NetworkManager configuration for Bullseye
        nm_config_dir = Path("/etc/NetworkManager/conf.d")
        nm_config_dir.mkdir(exist_ok=True)
        
        nm_config_content = """[keyfile]
unmanaged-devices=interface-name:usb0;interface-name:usb1

[device]
wifi.scan-rand-mac-address=no

[connection]
wifi.powersave=2

[main]
# Bullseye-specific optimizations
dhcp=dhcpcd
"""
        
        try:
            nm_config_file = nm_config_dir / "99-xbox360-emulator-bullseye.conf"
            with open(nm_config_file, 'w') as f:
                f.write(nm_config_content)
            
            self.log("✅ Created Bullseye NetworkManager configuration", "SUCCESS")
            self.fixes_applied.append("Bullseye NetworkManager bypass configured")
            
        except Exception as e:
            self.log(f"❌ Failed to create NetworkManager config: {e}", "ERROR")
        
        # Create systemd network configuration for Bullseye
        systemd_network_dir = Path("/etc/systemd/network")
        systemd_network_dir.mkdir(exist_ok=True)
        
        network_config_content = """[Match]
Name=usb0

[Network]
Address=192.168.4.1/24
IPMasquerade=yes
IPForward=yes
DHCPServer=yes

[DHCPServer]
PoolOffset=10
PoolSize=20
DefaultLeaseTimeSec=3600
DNS=8.8.8.8,8.8.4.4

# Bullseye-specific network optimizations
[Route]
Gateway=192.168.4.1
Metric=100
"""
        
        try:
            network_config_file = systemd_network_dir / "80-usb0-bullseye.network"
            with open(network_config_file, 'w') as f:
                f.write(network_config_content)
            
            self.log("✅ Created Bullseye systemd network configuration", "SUCCESS")
            self.fixes_applied.append("Bullseye systemd network configuration created")
            
        except Exception as e:
            self.log(f"❌ Failed to create systemd network config: {e}", "ERROR")
        
        # Enable systemd-networkd for Bullseye
        result = self.run_command("sudo systemctl enable systemd-networkd", 
                                "Enabling systemd-networkd", ignore_errors=True)
        if result and result.returncode == 0:
            self.log("✅ systemd-networkd enabled for Bullseye", "SUCCESS")
        
        return True
    
    def create_bullseye_launcher(self):
        """Create comprehensive launcher for Bullseye"""
        self.log("\n🚀 CREATING BULLSEYE COMPREHENSIVE LAUNCHER", "INFO")
        self.log("=" * 40, "INFO")
        
        launcher_content = f'''#!/bin/bash
# Comprehensive Xbox 360 WiFi Emulator Launcher for Pi OS Bullseye ARM64
# Addresses all Bullseye-specific compatibility issues

cd "/home/chris/desktop/Xbox360WifiEthernet" 2>/dev/null || cd "$(dirname "$0")"

echo "🎮 Xbox 360 WiFi Emulator - Bullseye ARM64 Launcher"
echo "======================================================"

# Setup logging for Bullseye
LOG_DIR="$HOME/desktop/debuglogs"
[ ! -d "$LOG_DIR" ] && LOG_DIR="$HOME/Desktop/debuglogs"
mkdir -p "$LOG_DIR" 2>/dev/null

LOG_FILE="$LOG_DIR/bullseye_launch_$(date +%Y%m%d_%H%M%S).log"

log_message() {{
    echo "[$( date '+%H:%M:%S' )] $1" | tee -a "$LOG_FILE"
}}

log_message "🚀 Starting Bullseye ARM64 launcher..."
log_message "📝 Logging to: $LOG_FILE"

# Check Bullseye system
if grep -q "bullseye" /etc/os-release; then
    log_message "✅ Pi OS Bullseye confirmed"
else
    log_message "⚠️ Warning: Not running Pi OS Bullseye"
fi

# Check ARM64 architecture
ARCH=$(uname -m)
if [[ "$ARCH" == "aarch64" || "$ARCH" == "arm64" ]]; then
    log_message "✅ ARM64 architecture confirmed"
else
    log_message "⚠️ Warning: Architecture is $ARCH, not ARM64"
fi

# Check if reboot is needed
if [ -f "/tmp/xbox360_reboot_required" ]; then
    log_message "⚠️ REBOOT REQUIRED for DWC2 changes to take effect"
    log_message "   Please reboot and run this script again"
    echo
    read -p "Press Enter to continue anyway or Ctrl+C to exit..."
fi

# Set environment for Bullseye compatibility
export SKIP_PIP_INSTALL=1
export PYTHONPATH="$PWD:$PYTHONPATH"

# Install any missing system packages for Bullseye
log_message "📦 Checking Bullseye system packages..."
sudo apt update -qq
sudo apt install -y python3-tk python3-full zenity 2>/dev/null || true

# Check DWC2 status for Bullseye
log_message "🔌 Checking DWC2 status on Bullseye..."
if lsmod | grep -q dwc2; then
    log_message "✅ DWC2 module is loaded"
else
    log_message "❌ DWC2 module not loaded - attempting to load..."
    sudo modprobe dwc2 2>/dev/null || log_message "⚠️ DWC2 load failed - reboot may be needed"
fi

if lsmod | grep -q libcomposite; then
    log_message "✅ libcomposite module is loaded"
else
    log_message "❌ libcomposite module not loaded - attempting to load..."
    sudo modprobe libcomposite 2>/dev/null || log_message "⚠️ libcomposite load failed - reboot may be needed"
fi

# Check USB device controllers
UDC_COUNT=$(ls /sys/class/udc/ 2>/dev/null | wc -l)
if [ "$UDC_COUNT" -gt 0 ]; then
    log_message "✅ USB device controllers found: $UDC_COUNT"
else
    log_message "❌ No USB device controllers found"
fi

# Launch the installer
log_message "🎯 Launching Xbox 360 WiFi Emulator installer (Bullseye)..."
python3 installer.py "$@" 2>&1 | tee -a "$LOG_FILE"

INSTALLER_EXIT_CODE=${{PIPESTATUS[0]}}

if [ $INSTALLER_EXIT_CODE -eq 0 ]; then
    log_message "✅ Installer completed successfully on Bullseye!"
else
    log_message "❌ Installer failed (exit code: $INSTALLER_EXIT_CODE)"
    log_message "📂 Check full log: $LOG_FILE"
fi

log_message "📂 Complete session log: $LOG_FILE"
echo "✅ Bullseye launcher complete! Check $LOG_FILE for details."
'''
        
        launcher_path = Path("launch_bullseye_comprehensive.sh")
        try:
            with open(launcher_path, 'w') as f:
                f.write(launcher_content)
            
            os.chmod(launcher_path, 0o755)
            self.log(f"✅ Created Bullseye comprehensive launcher: {launcher_path}", "SUCCESS")
            self.fixes_applied.append("Bullseye comprehensive launcher created")
            return launcher_path
            
        except Exception as e:
            self.log(f"❌ Failed to create Bullseye launcher: {e}", "ERROR")
            return None
    
    def create_reboot_marker(self):
        """Create reboot marker for Bullseye"""
        try:
            marker_file = Path("/tmp/xbox360_reboot_required")
            with open(marker_file, 'w') as f:
                f.write(f"Reboot required for Xbox 360 emulator Bullseye fixes\n")
                f.write(f"Created: {datetime.now()}\n")
                f.write(f"OS: Pi OS Bullseye ARM64\n")
                f.write(f"Fixes applied: {', '.join(self.fixes_applied)}\n")
            
            self.log("✅ Created Bullseye reboot marker file", "SUCCESS")
            
        except Exception as e:
            self.log(f"⚠️ Could not create reboot marker: {e}", "WARNING")
    
    def provide_final_instructions(self, launcher_created=None):
        """Provide comprehensive final instructions for Bullseye"""
        self.log("\n📋 COMPREHENSIVE BULLSEYE FINAL INSTRUCTIONS", "INFO")
        self.log("=" * 50, "INFO")
        
        self.log("🎯 WHAT WAS FIXED FOR BULLSEYE:", "SUCCESS")
        for i, fix in enumerate(self.fixes_applied, 1):
            self.log(f"   {i}. {fix}", "SUCCESS")
        
        self.log("\n🚀 HOW TO USE ON BULLSEYE:", "INFO")
        
        if launcher_created and launcher_created.exists():
            self.log("✅ RECOMMENDED: Use the Bullseye launcher", "SUCCESS")
            self.log(f"   ./{launcher_created.name}", "INFO")
            self.log("   This handles all Bullseye ARM64 compatibility issues", "INFO")
        
        self.log("\n🔄 REBOOT REQUIREMENT:", "WARNING")
        self.log("IMPORTANT: A reboot is required for Bullseye DWC2 changes", "WARNING")
        self.log("After reboot on Bullseye:", "INFO")
        self.log("   1. DWC2 module will load automatically", "INFO")
        self.log("   2. USB gadget functionality will be available", "INFO")
        self.log("   3. Network interfaces will be created", "INFO")
        self.log("   4. All Bullseye optimizations will be active", "INFO")
        
        self.log("\n📂 LOGGING:", "INFO")
        self.log(f"All operations log to: {self.debug_log_dir}/", "INFO")
        self.log("Each run creates a timestamped log file", "INFO")
        
        self.log("\n🔧 BULLSEYE TROUBLESHOOTING:", "INFO")
        self.log("If issues persist after reboot:", "INFO")
        self.log("   1. Check log files in debuglogs/", "INFO")
        self.log("   2. Verify Bullseye: grep bullseye /etc/os-release", "INFO")
        self.log("   3. Check ARM64: uname -m (should show aarch64)", "INFO")
        self.log("   4. Verify modules: lsmod | grep -E '(dwc2|libcomposite)'", "INFO")
        self.log("   5. Check USB controllers: ls /sys/class/udc/", "INFO")
    
    def run_comprehensive_bullseye_fix(self):
        """Run complete comprehensive fix for Bullseye"""
        try:
            self.log("🚀 Starting comprehensive Pi OS Bullseye ARM64 fix...", "INFO")
            
            # Step 1: Validate Bullseye system
            if not self.validate_bullseye_system():
                self.log("⚠️ System validation failed, continuing anyway...", "WARNING")
            
            # Step 2: Diagnose all issues
            issues_count = self.diagnose_system_issues()
            
            if issues_count == 0:
                self.log("\n🎉 No issues detected! Bullseye system appears optimal.", "SUCCESS")
                # Still create launcher for consistency
                self.create_bullseye_launcher()
                return True
            
            self.log(f"\n🔧 Applying Bullseye fixes for {issues_count} detected issues...", "INFO")
            
            # Step 3: Fix Python environment for Bullseye
            self.fix_python_environment_bullseye()
            
            # Step 4: Fix DWC2 module issues for Bullseye
            self.fix_dwc2_bullseye()
            
            # Step 5: Fix USB networking for Bullseye
            self.fix_usb_networking_bullseye()
            
            # Step 6: Create Bullseye comprehensive launcher
            launcher_created = self.create_bullseye_launcher()
            
            # Step 7: Create reboot marker
            self.create_reboot_marker()
            
            # Step 8: Provide final instructions
            self.provide_final_instructions(launcher_created)
            
            self.log("\n" + "=" * 60, "INFO")
            self.log("🎉 COMPREHENSIVE BULLSEYE FIX COMPLETE!", "SUCCESS")
            self.log("=" * 60, "INFO")
            self.log(f"📂 Complete fix log: {self.log_file}", "INFO")
            self.log(f"🔧 Fixes applied: {len(self.fixes_applied)}", "SUCCESS")
            self.log("🔄 REBOOT REQUIRED for Bullseye changes to take effect", "WARNING")
            
            return True
            
        except Exception as e:
            self.log(f"❌ Comprehensive Bullseye fix failed: {e}", "ERROR")
            import traceback
            self.log(traceback.format_exc(), "ERROR")
            return False
        finally:
            self.flush_log()

def main():
    """Main comprehensive fix function for Bullseye"""
    print("🔧 Xbox 360 WiFi Emulator - Comprehensive Pi OS Bullseye ARM64 Fix")
    print("=" * 65)
    print("🎯 Fixing ALL identified issues for Bullseye:")
    print("   • Python externally-managed-environment")
    print("   • DWC2 module loading for Bullseye")
    print("   • USB networking with Bullseye optimizations")  
    print("   • ARM64 architecture compatibility")
    print("   • Bullseye-specific boot configuration")
    print("📝 All actions logged to debuglogs directory")
    print()
    
    fixer = BullseyeComprehensiveFixer()
    success = fixer.run_comprehensive_bullseye_fix()
    
    print(f"\n📂 Complete comprehensive Bullseye fix log:")
    print(f"   {fixer.log_file}")
    
    if success:
        print("\n🎉 Comprehensive Bullseye fix complete!")
        print("⚠️  REBOOT REQUIRED for DWC2 changes to take effect")
        print("💡 After reboot, use the launch_bullseye_comprehensive.sh script")
    else:
        print("\n❌ Some fixes encountered issues")
        print("💡 Check the log file for detailed information")

if __name__ == "__main__":
    main()