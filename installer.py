#!/usr/bin/env python3
"""
Xbox 360 WiFi Module Emulator - Pi OS Bullseye ARM64 Installer
Optimized for Raspberry Pi OS Bullseye 64-bit
"""

import os
import sys
import subprocess
import platform
import shutil
import json
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple

# GUI imports with fallback
try:
    import tkinter as tk
    from tkinter import ttk, scrolledtext, messagebox, filedialog
    import threading
    import queue
    GUI_AVAILABLE = True
except ImportError:
    GUI_AVAILABLE = False
    print("⚠️ GUI not available. Install with: sudo apt install python3-tk")

class BullseyeXboxInstaller:
    """Xbox 360 WiFi Emulator installer optimized for Pi OS Bullseye ARM64"""
    
    def __init__(self, dev_mode=False):
        self.dev_mode = dev_mode  # Development mode uses local directories
        self.setup_logging()
        self.setup_system_info()
        self.setup_paths()
        
        # Installation state
        self.installation_complete = False
        self.reboot_required = False
        self.current_step = 0
        self.total_steps = 10
        
        # Installation steps optimized for Bullseye
        self.steps = [
            ("System Validation", self._validate_bullseye_system),
            ("Install Dependencies", self._install_bullseye_dependencies),
            ("Configure USB Gadget", self._configure_bullseye_usb),
            ("Setup DWC2 Module", self._setup_bullseye_dwc2),
            ("Install Xbox Emulator", self._install_emulator_core),
            ("Configure Network", self._setup_bullseye_networking),
            ("Create SystemD Services", self._create_bullseye_services),
            ("Setup USB Sniffing", self._setup_usb_tools),
            ("Create Helper Scripts", self._create_helper_scripts),
            ("Finalize Installation", self._finalize_bullseye_setup)
        ]
    
    def setup_logging(self):
        """Setup centralized logging for Bullseye"""
        # Bullseye uses lowercase desktop by default
        possible_log_dirs = [
            Path.home() / "Desktop" / "debuglogs",
            Path.home() / "desktop" / "debuglogs", 
            Path("/home/pi/Desktop/debuglogs"),
            Path("/home/pi/desktop/debuglogs"),
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
        
        # Create session log
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_file = self.debug_log_dir / f"bullseye_install_{timestamp}.log"
        self.log_buffer = []
        
        self.log("🎯 Xbox 360 WiFi Emulator - Pi OS Bullseye ARM64 Installer", "INFO")
        self.log("=" * 60, "INFO")
        self.log(f"Session started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", "INFO")
        self.log(f"Log file: {self.log_file}", "INFO")
        self.log("=" * 60, "INFO")
    
    def log(self, message: str, level: str = "INFO"):
        """Log message with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] [{level}] {message}"
        self.log_buffer.append(log_entry + "\n")
        
        # Console output with colors
        colors = {
            "INFO": "\033[0;34m",
            "SUCCESS": "\033[0;32m", 
            "WARNING": "\033[1;33m",
            "ERROR": "\033[0;31m",
            "DEBUG": "\033[0;37m"
        }
        
        color = colors.get(level, "\033[0m")
        print(f"{color}[{timestamp}] {message}\033[0m")
        
        # Flush log periodically
        if len(self.log_buffer) >= 5 or level in ['ERROR', 'SUCCESS']:
            self.flush_log()
    
    def flush_log(self):
        """Write log buffer to file"""
        try:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.writelines(self.log_buffer)
            self.log_buffer = []
        except Exception as e:
            print(f"Warning: Could not write to log file: {e}")
    
    def setup_system_info(self):
        """Detect Bullseye ARM64 system information"""
        self.system_info = {
            'os': platform.system(),
            'arch': platform.machine(),
            'python_version': f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            'is_bullseye': False,
            'is_arm64': False,
            'is_pi': False,
            'kernel_version': platform.release()
        }
        
        # Check for Bullseye
        try:
            with open('/etc/os-release', 'r') as f:
                content = f.read()
                if 'bullseye' in content.lower():
                    self.system_info['is_bullseye'] = True
                    self.log("✅ Detected Pi OS Bullseye", "SUCCESS")
        except:
            pass
        
        # Check architecture
        if 'aarch64' in self.system_info['arch'] or 'arm64' in self.system_info['arch']:
            self.system_info['is_arm64'] = True
            self.log("✅ Detected ARM64 architecture", "SUCCESS")
        
        # Check for Raspberry Pi
        try:
            with open('/proc/cpuinfo', 'r') as f:
                if 'Raspberry Pi' in f.read():
                    self.system_info['is_pi'] = True
                    self.log("✅ Detected Raspberry Pi hardware", "SUCCESS")
        except:
            pass
    
    def setup_paths(self):
        """Setup Bullseye-specific paths"""
        # Bullseye uses /boot/ not /boot/firmware/
        self.boot_config = Path("/boot/config.txt")
        self.boot_cmdline = Path("/boot/cmdline.txt") 
        self.modules_file = Path("/etc/modules")
        
        # Installation directories - use local paths in dev mode
        if self.dev_mode:
            self.script_dir = Path.cwd()
            self.install_dir = self.script_dir / "build" / "xbox360-emulator"
            self.config_dir = self.script_dir / "build" / "config"
            self.log_dir = self.script_dir / "build" / "logs"
            self.log("🔧 Development mode: using local directories", "INFO")
        else:
            self.install_dir = Path("/opt/xbox360-emulator")
            self.config_dir = Path("/etc/xbox360-emulator") 
            self.log_dir = Path("/var/log/xbox360-emulator")
            self.script_dir = Path.cwd()
            self.log("🏗️ Production mode: using system directories", "INFO")
        
        self.log(f"Boot config: {self.boot_config}", "INFO")
        self.log(f"Install directory: {self.install_dir}", "INFO")
        self.log(f"Script directory: {self.script_dir}", "INFO")
    
    def run_command(self, cmd: str, description: str = "", timeout: int = 60) -> Tuple[bool, str, str]:
        """Run command and return success, stdout, stderr"""
        if description:
            self.log(f"🔧 {description}", "INFO")
        
        self.log(f"Command: {cmd}", "DEBUG")
        
        try:
            result = subprocess.run(
                cmd, shell=True, capture_output=True, 
                text=True, timeout=timeout
            )
            
            success = result.returncode == 0
            level = "SUCCESS" if success else "ERROR"
            
            if success:
                self.log("✅ Command succeeded", level)
            else:
                self.log(f"❌ Command failed (exit code: {result.returncode})", level)
            
            if result.stdout.strip():
                for line in result.stdout.strip().split('\n')[:10]:
                    if line.strip():
                        self.log(f"   OUT: {line}", "DEBUG")
            
            if result.stderr.strip():
                for line in result.stderr.strip().split('\n')[:5]:
                    if line.strip():
                        self.log(f"   ERR: {line}", level)
            
            return success, result.stdout, result.stderr
            
        except subprocess.TimeoutExpired:
            self.log(f"⏰ Command timed out after {timeout}s", "ERROR")
            return False, "", "Command timeout"
        except Exception as e:
            self.log(f"❌ Command exception: {e}", "ERROR")
            return False, "", str(e)
    
    def _validate_bullseye_system(self) -> bool:
        """Validate this is a proper Bullseye ARM64 Pi system"""
        self.log("\n🔍 VALIDATING SYSTEM COMPATIBILITY", "INFO")
        self.log("=" * 35, "INFO")
        
        validation_passed = True
        
        if self.dev_mode:
            self.log("🔧 Development mode - relaxed validation", "INFO")
            # In dev mode, just check basics
            self.log(f"OS: {self.system_info['os']}", "INFO")
            self.log(f"Architecture: {self.system_info['arch']}", "INFO")
            self.log(f"Python: {self.system_info['python_version']}", "INFO")
            self.log("✅ Development mode validation passed", "SUCCESS")
            return True
        
        # Production mode - strict validation
        # Check OS version
        if not self.system_info['is_bullseye']:
            self.log("❌ Not running Pi OS Bullseye", "ERROR")
            validation_passed = False
        else:
            self.log("✅ Pi OS Bullseye confirmed", "SUCCESS")
        
        # Check architecture
        if not self.system_info['is_arm64']:
            self.log("❌ Not running ARM64 architecture", "ERROR") 
            validation_passed = False
        else:
            self.log("✅ ARM64 architecture confirmed", "SUCCESS")
        
        # Check hardware
        if not self.system_info['is_pi']:
            self.log("⚠️ Non-Pi hardware detected", "WARNING")
        else:
            self.log("✅ Raspberry Pi hardware confirmed", "SUCCESS")
        
        # Check kernel version
        self.log(f"Kernel: {self.system_info['kernel_version']}", "INFO")
        
        # Check Python version 
        self.log(f"Python: {self.system_info['python_version']}", "INFO")
        
        # Check critical paths
        if not self.boot_config.exists():
            self.log(f"❌ Boot config not found: {self.boot_config}", "ERROR")
            validation_passed = False
        else:
            self.log(f"✅ Boot config found: {self.boot_config}", "SUCCESS")
        
        # Check for root/sudo access
        success, _, _ = self.run_command("sudo -n true", "Testing sudo access")
        if not success:
            self.log("⚠️ Sudo access required for installation", "WARNING")
        
        return validation_passed
    
    def _install_bullseye_dependencies(self) -> bool:
        """Install dependencies optimized for Bullseye"""
        self.log("\n📦 INSTALLING BULLSEYE DEPENDENCIES", "INFO")
        self.log("=" * 35, "INFO")
        
        # Update package list
        success, _, _ = self.run_command("sudo apt update", "Updating package list", timeout=300)
        if not success:
            self.log("❌ Failed to update package list", "ERROR")
            return False
        
        # Core system packages for Bullseye
        bullseye_packages = [
            # Python and GUI
            'python3-tk', 'python3-pip', 'python3-setuptools', 'python3-wheel',
            'python3-dev', 'python3-venv',
            
            # System tools
            'git', 'curl', 'wget', 'build-essential', 'pkg-config',
            
            # USB and networking
            'usbutils', 'iproute2', 'iptables', 'dnsmasq', 'hostapd',
            
            # Development tools
            'cmake', 'make', 'gcc', 'g++',
            
            # USB monitoring and debugging
            'usbip', 'tcpdump', 'wireshark-common', 'tshark',
            'libusb-1.0-0-dev', 'libudev-dev',
            
            # GUI and desktop
            'zenity', 'desktop-file-utils',
            
            # Network tools
            'net-tools', 'bridge-utils', 'wireless-tools'
        ]
        
        # Install packages in chunks to avoid timeout
        chunk_size = 5
        for i in range(0, len(bullseye_packages), chunk_size):
            chunk = bullseye_packages[i:i+chunk_size]
            cmd = f"sudo apt install -y {' '.join(chunk)}"
            success, _, stderr = self.run_command(cmd, f"Installing packages: {', '.join(chunk)}", timeout=300)
            
            if not success:
                self.log(f"⚠️ Some packages in chunk failed: {stderr}", "WARNING")
        
        # Verify critical packages
        critical_packages = ['python3-tk', 'usbutils', 'git']
        for package in critical_packages:
            success, _, _ = self.run_command(f"dpkg -l | grep -q {package}", f"Verifying {package}")
            if success:
                self.log(f"✅ {package} installed", "SUCCESS") 
            else:
                self.log(f"❌ {package} missing", "ERROR")
        
        return True
    
    def _configure_bullseye_usb(self) -> bool:
        """Configure USB gadget support for Bullseye"""
        self.log("\n🔌 CONFIGURING USB GADGET FOR BULLSEYE", "INFO")
        self.log("=" * 40, "INFO")
        
        # Backup boot config
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_config = self.boot_config.with_suffix(f'.txt.backup.{timestamp}')
            shutil.copy2(self.boot_config, backup_config)
            self.log(f"✅ Backed up config to: {backup_config}", "SUCCESS")
        except Exception as e:
            self.log(f"⚠️ Could not backup config: {e}", "WARNING")
        
        # Read current config
        try:
            with open(self.boot_config, 'r') as f:
                config_content = f.read()
        except Exception as e:
            self.log(f"❌ Could not read boot config: {e}", "ERROR")
            return False
        
        # Remove existing DWC2 entries
        lines = config_content.split('\n')
        lines = [line for line in lines if 'dwc2' not in line.lower()]
        
        # Add Bullseye-optimized DWC2 configuration
        bullseye_dwc2_config = [
            "",
            "# Xbox 360 WiFi Emulator - Bullseye DWC2 Configuration",
            "# Enable DWC2 USB gadget mode for Xbox 360 emulation",
            "dtoverlay=dwc2,dr_mode=otg",
            "",
            "# USB OTG optimizations for Bullseye",
            "otg_mode=1",
            "max_usb_current=1",
            "",
            "# Memory optimization for gadget mode",
            "gpu_mem=16",
            "gpu_mem_256=16",
            "gpu_mem_512=16",
            "gpu_mem_1024=16"
        ]
        
        lines.extend(bullseye_dwc2_config)
        
        # Write updated config
        try:
            with open(self.boot_config, 'w') as f:
                f.write('\n'.join(lines))
            self.log("✅ Updated boot config with Bullseye DWC2 settings", "SUCCESS")
        except Exception as e:
            self.log(f"❌ Failed to update boot config: {e}", "ERROR")
            return False
        
        return True
    
    def _setup_bullseye_dwc2(self) -> bool:
        """Setup DWC2 module loading for Bullseye"""
        self.log("\n🔧 SETTING UP DWC2 MODULE FOR BULLSEYE", "INFO")
        self.log("=" * 40, "INFO")
        
        # Update cmdline.txt for Bullseye
        if self.boot_cmdline.exists():
            try:
                with open(self.boot_cmdline, 'r') as f:
                    cmdline = f.read().strip()
                
                # Add modules-load for early loading
                if "modules-load=" not in cmdline:
                    cmdline += " modules-load=dwc2,libcomposite"
                else:
                    # Update existing modules-load
                    import re
                    if "dwc2" not in cmdline:
                        cmdline = re.sub(r'modules-load=([^\s]+)', 
                                       lambda m: f"modules-load={m.group(1)},dwc2,libcomposite", 
                                       cmdline)
                
                with open(self.boot_cmdline, 'w') as f:
                    f.write(cmdline + '\n')
                
                self.log("✅ Updated cmdline.txt for Bullseye", "SUCCESS")
            except Exception as e:
                self.log(f"⚠️ Could not update cmdline.txt: {e}", "WARNING")
        
        # Update /etc/modules
        try:
            current_modules = []
            if self.modules_file.exists():
                with open(self.modules_file, 'r') as f:
                    current_modules = [line.strip() for line in f.readlines() 
                                     if line.strip() and not line.startswith('#')]
            
            # Add required modules
            required_modules = ["dwc2", "libcomposite", "configfs"]
            modules_added = []
            
            for module in required_modules:
                if module not in current_modules:
                    current_modules.append(module)
                    modules_added.append(module)
            
            # Write updated modules file
            with open(self.modules_file, 'w') as f:
                f.write("# /etc/modules: kernel modules to load at boot time\n")
                f.write("# Xbox 360 WiFi Emulator modules for Bullseye\n")
                for module in current_modules:
                    f.write(f"{module}\n")
            
            if modules_added:
                self.log(f"✅ Added modules: {', '.join(modules_added)}", "SUCCESS")
            else:
                self.log("✅ Modules already configured", "SUCCESS")
                
        except Exception as e:
            self.log(f"❌ Failed to update /etc/modules: {e}", "ERROR")
        
        # Try to load modules immediately
        for module in ["dwc2", "libcomposite"]:
            success, _, _ = self.run_command(f"sudo modprobe {module}", f"Loading {module} module")
            if success:
                self.log(f"✅ {module} loaded successfully", "SUCCESS")
            else:
                self.log(f"⚠️ {module} will load after reboot", "WARNING")
        
        # Update initramfs for early module loading
        success, _, _ = self.run_command("sudo update-initramfs -u", "Updating initramfs", timeout=300)
        if success:
            self.log("✅ Initramfs updated for early module loading", "SUCCESS")
        else:
            self.log("⚠️ Initramfs update had issues", "WARNING")
        
        return True
    
    def _install_emulator_core(self) -> bool:
        """Install Xbox 360 emulator core files"""
        self.log("\n🎮 INSTALLING XBOX 360 EMULATOR CORE", "INFO")
        self.log("=" * 35, "INFO")
        
        # Create installation directories
        for directory in [self.install_dir, self.config_dir, self.log_dir]:
            try:
                directory.mkdir(parents=True, exist_ok=True)
                self.log(f"✅ Created directory: {directory}", "SUCCESS")
            except Exception as e:
                self.log(f"❌ Failed to create {directory}: {e}", "ERROR")
                return False
        
        # Copy source files
        src_dir = self.script_dir / "src"
        if src_dir.exists():
            try:
                shutil.copytree(src_dir, self.install_dir / "src", dirs_exist_ok=True)
                self.log("✅ Copied source files", "SUCCESS")
            except Exception as e:
                self.log(f"❌ Failed to copy source files: {e}", "ERROR")
        
        # Create main emulator script
        emulator_script = self.install_dir / "xbox360_emulator.py"
        emulator_content = '''#!/usr/bin/env python3
"""
Xbox 360 WiFi Module Emulator - Main Script
Optimized for Pi OS Bullseye ARM64
"""

import sys
import os
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

try:
    from xbox360_emulator import Xbox360Emulator
    
    def main():
        print("🎮 Xbox 360 WiFi Module Emulator - Bullseye ARM64")
        print("=" * 50)
        
        emulator = Xbox360Emulator()
        emulator.start()
        
    if __name__ == "__main__":
        main()
        
except ImportError as e:
    print(f"❌ Failed to import emulator modules: {e}")
    print("💡 Please ensure all dependencies are installed")
    sys.exit(1)
'''
        
        try:
            with open(emulator_script, 'w') as f:
                f.write(emulator_content)
            os.chmod(emulator_script, 0o755)
            self.log("✅ Created main emulator script", "SUCCESS")
        except Exception as e:
            self.log(f"❌ Failed to create emulator script: {e}", "ERROR")
        
        return True
    
    def _setup_bullseye_networking(self) -> bool:
        """Setup networking for Bullseye"""
        self.log("\n🌐 SETTING UP BULLSEYE NETWORKING", "INFO")
        self.log("=" * 35, "INFO")
        
        # Create NetworkManager configuration
        nm_config_dir = Path("/etc/NetworkManager/conf.d")
        nm_config_dir.mkdir(exist_ok=True)
        
        nm_config_content = """[keyfile]
unmanaged-devices=interface-name:usb0;interface-name:usb1

[device]
wifi.scan-rand-mac-address=no

[connection]
wifi.powersave=2
"""
        
        try:
            nm_config_file = nm_config_dir / "99-xbox360-emulator.conf"
            with open(nm_config_file, 'w') as f:
                f.write(nm_config_content)
            self.log("✅ Created NetworkManager configuration", "SUCCESS")
        except Exception as e:
            self.log(f"❌ Failed to create NetworkManager config: {e}", "ERROR")
        
        # Create systemd network configuration for usb0
        systemd_network_dir = Path("/etc/systemd/network")
        systemd_network_dir.mkdir(exist_ok=True)
        
        usb0_network_config = """[Match]
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
"""
        
        try:
            usb0_config_file = systemd_network_dir / "80-usb0.network"
            with open(usb0_config_file, 'w') as f:
                f.write(usb0_network_config)
            self.log("✅ Created systemd network configuration", "SUCCESS")
        except Exception as e:
            self.log(f"❌ Failed to create systemd network config: {e}", "ERROR")
        
        # Enable systemd-networkd
        success, _, _ = self.run_command("sudo systemctl enable systemd-networkd", "Enabling systemd-networkd")
        if success:
            self.log("✅ systemd-networkd enabled", "SUCCESS")
        
        return True
    
    def _create_bullseye_services(self) -> bool:
        """Create SystemD services for Bullseye"""
        self.log("\n⚙️ CREATING SYSTEMD SERVICES", "INFO")
        self.log("=" * 30, "INFO")
        
        # Main Xbox 360 emulator service
        service_content = f"""[Unit]
Description=Xbox 360 WiFi Module Emulator
After=network.target systemd-modules-load.service
Wants=systemd-modules-load.service

[Service]
Type=simple
User=root
WorkingDirectory={self.install_dir}
ExecStart=/usr/bin/python3 {self.install_dir}/xbox360_emulator.py
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

# Environment variables
Environment=PYTHONPATH={self.install_dir}/src
Environment=XBOX360_CONFIG_DIR={self.config_dir}
Environment=XBOX360_LOG_DIR={self.log_dir}

[Install]
WantedBy=multi-user.target
"""
        
        service_file = Path("/etc/systemd/system/xbox360-emulator.service")
        try:
            with open(service_file, 'w') as f:
                f.write(service_content)
            self.log("✅ Created Xbox 360 emulator service", "SUCCESS")
        except Exception as e:
            self.log(f"❌ Failed to create service file: {e}", "ERROR")
            return False
        
        # Enable service
        success, _, _ = self.run_command("sudo systemctl daemon-reload", "Reloading systemd")
        if success:
            success, _, _ = self.run_command("sudo systemctl enable xbox360-emulator", "Enabling Xbox service")
            if success:
                self.log("✅ Xbox 360 emulator service enabled", "SUCCESS")
        
        return True
    
    def _setup_usb_tools(self) -> bool:
        """Setup USB sniffing and monitoring tools"""
        self.log("\n🔍 SETTING UP USB MONITORING TOOLS", "INFO")
        self.log("=" * 35, "INFO")
        
        # Create captures directory
        captures_dir = Path.home() / "Desktop" / "captures"
        captures_dir.mkdir(parents=True, exist_ok=True)
        self.log(f"✅ Created captures directory: {captures_dir}", "SUCCESS")
        
        # Run USB system diagnosis and fixes
        self.log("🩺 Running USB system diagnosis...", "INFO")
        try:
            # Import and run the USB system fixer
            sys.path.insert(0, str(self.script_dir / "src"))
            from usb_system_fixer import USBSystemFixer
            
            fixer = USBSystemFixer()
            summary = fixer.diagnose_and_fix()
            
            # Log results
            self.log(f"USB diagnosis: {summary['issues_found']} issues, {summary['fixes_applied']} fixes", "INFO")
            
            for fix in summary['fixes']:
                self.log(f"✅ {fix}", "SUCCESS")
                
            for issue in summary['issues']:
                self.log(f"⚠️ {issue}", "WARNING")
                
            if summary['system_status']['usb_interface']['exists']:
                self.log("✅ usb0 interface is available", "SUCCESS")
            else:
                self.log("⚠️ usb0 interface not available", "WARNING")
                
        except Exception as e:
            self.log(f"⚠️ USB system diagnosis failed: {e}", "WARNING")
        
        # Build USB-Sniffify tools if available
        sniffify_dir = self.script_dir / "usb_sniffing_tools" / "usb-sniffify"
        if sniffify_dir.exists():
            self.log("🔧 Building USB-Sniffify tools...", "INFO")
            build_dir = sniffify_dir / "build"
            build_dir.mkdir(exist_ok=True)
            
            # Check if already built
            if not (build_dir / "raw-gadget-passthrough").exists():
                # Install build dependencies
                deps = ["build-essential", "cmake", "libusb-1.0-0-dev", "libudev-dev", "pkg-config"]
                for dep in deps:
                    success, _, _ = self.run_command(f"sudo apt install -y {dep}", f"Installing {dep}")
                
                # Change to build directory and run CMake
                original_cwd = os.getcwd()
                try:
                    os.chdir(build_dir)
                    success, stdout, stderr = self.run_command("cmake ..", "Running CMake", timeout=120)
                    if success:
                        self.log("✅ CMake configuration successful", "SUCCESS")
                        success, stdout, stderr = self.run_command("make -j$(nproc)", "Building tools", timeout=300)
                        if success:
                            self.log("✅ USB-Sniffify tools built successfully", "SUCCESS")
                        else:
                            self.log(f"⚠️ USB-Sniffify build failed: {stderr}", "WARNING")
                    else:
                        self.log(f"⚠️ CMake configuration failed: {stderr}", "WARNING")
                finally:
                    os.chdir(original_cwd)
            else:
                self.log("✅ USB-Sniffify tools already built", "SUCCESS")
        
        # Create USB passthrough manager configuration
        usb_config = self.config_dir / "usb_config.json"
        try:
            import json
            config = {
                "capture_directory": str(captures_dir),
                "auto_analyze": True,
                "supported_devices": {
                    "045e:02a8": "Xbox 360 Wireless Network Adapter",
                    "045e:0292": "Xbox 360 Wireless Gaming Receiver",
                    "045e:028e": "Xbox 360 Controller"
                },
                "capture_settings": {
                    "default_duration": 30,
                    "auto_stop_on_disconnect": True,
                    "generate_reports": True
                }
            }
            
            with open(usb_config, 'w') as f:
                json.dump(config, f, indent=2)
            
            self.log(f"✅ USB configuration created: {usb_config}", "SUCCESS")
            
        except Exception as e:
            self.log(f"⚠️ Could not create USB config: {e}", "WARNING")
        
        return True
    
    def _create_helper_scripts(self) -> bool:
        """Create helper scripts for Bullseye"""
        self.log("\n📜 CREATING HELPER SCRIPTS", "INFO")
        self.log("=" * 30, "INFO")
        
        # Create start script
        start_script = self.install_dir / "start_emulator.sh"
        start_content = f'''#!/bin/bash
# Xbox 360 WiFi Emulator Start Script - Bullseye
cd "{self.install_dir}"

echo "🎮 Starting Xbox 360 WiFi Module Emulator (Bullseye)"
echo "=" * 50

# Check modules
echo "Checking USB gadget modules..."
sudo modprobe dwc2 2>/dev/null || echo "⚠️ DWC2 module load failed"
sudo modprobe libcomposite 2>/dev/null || echo "⚠️ libcomposite module load failed"

# Start emulator
python3 xbox360_emulator.py
'''
        
        try:
            with open(start_script, 'w') as f:
                f.write(start_content)
            os.chmod(start_script, 0o755)
            self.log("✅ Created start script", "SUCCESS")
        except Exception as e:
            self.log(f"❌ Failed to create start script: {e}", "ERROR")
        
        # Create USB capture script
        capture_script = self.install_dir / "capture_usb.sh"
        capture_content = f'''#!/bin/bash
# Xbox 360 USB Capture Script - Bullseye
cd "{self.install_dir}"

echo "🔍 Xbox 360 USB Capture Tool"
echo "=" * 40

# Check if USB passthrough manager is available
if [ ! -f "src/usb_passthrough_manager.py" ]; then
    echo "❌ USB passthrough manager not found"
    exit 1
fi

# Show usage options
if [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
    echo "Usage: $0 [scan|capture|passthrough|status] [options]"
    echo ""
    echo "Commands:"
    echo "  scan        - Scan for Xbox 360 devices"
    echo "  capture     - Capture USB traffic (30 seconds)"
    echo "  passthrough - Start USB passthrough"
    echo "  status      - Show system status"
    echo ""
    echo "Options:"
    echo "  --duration N  - Capture duration in seconds (default: 30)"
    echo "  --device DEV  - Specific device for passthrough"
    echo "  --verbose     - Enable verbose output"
    exit 0
fi

# Default to status if no command given
CMD=${{1:-status}}

# Load required modules
sudo modprobe usbmon 2>/dev/null
sudo modprobe raw_gadget 2>/dev/null

# Mount debugfs if needed
if [ ! -d "/sys/kernel/debug/usb/usbmon" ]; then
    sudo mount -t debugfs none /sys/kernel/debug 2>/dev/null
fi

# Run the USB manager
python3 src/usb_passthrough_manager.py "$CMD" "$@"
'''
        
        try:
            with open(capture_script, 'w') as f:
                f.write(capture_content)
            os.chmod(capture_script, 0o755)
            self.log("✅ Created USB capture script", "SUCCESS")
        except Exception as e:
            self.log(f"❌ Failed to create capture script: {e}", "ERROR")
        
        # Create desktop launcher for USB tools
        if not self.dev_mode:
            desktop_dirs = [
                Path.home() / "Desktop",
                Path.home() / "desktop",
                Path("/home/pi/Desktop"),
                Path("/home/pi/desktop")
            ]
            
            for desktop_dir in desktop_dirs:
                if desktop_dir.exists():
                    launcher_file = desktop_dir / "Xbox360-USB-Tools.desktop"
                    launcher_content = f'''[Desktop Entry]
Version=1.0
Type=Application
Name=Xbox 360 USB Tools
Comment=Xbox 360 USB capture and passthrough tools
Exec=x-terminal-emulator -e "{capture_script}"
Icon=input-gaming
Terminal=true
Categories=System;
'''
                    try:
                        with open(launcher_file, 'w') as f:
                            f.write(launcher_content)
                        os.chmod(launcher_file, 0o755)
                        self.log(f"✅ Created desktop launcher: {launcher_file}", "SUCCESS")
                        break
                    except Exception as e:
                        self.log(f"⚠️ Could not create desktop launcher: {e}", "WARNING")
        
        return True
    
    def _finalize_bullseye_setup(self) -> bool:
        """Finalize installation for Bullseye"""
        self.log("\n🎯 FINALIZING BULLSEYE SETUP", "INFO")
        self.log("=" * 30, "INFO")
        
        # Create completion marker
        completion_marker = Path(".installation_complete")
        try:
            with open(completion_marker, 'w') as f:
                f.write(f"Xbox 360 WiFi Emulator installation completed\n")
                f.write(f"Timestamp: {datetime.now()}\n")
                f.write(f"OS: Pi OS Bullseye ARM64\n")
                f.write(f"Version: 1.0\n")
            self.log("✅ Created installation completion marker", "SUCCESS")
        except Exception as e:
            self.log(f"⚠️ Could not create completion marker: {e}", "WARNING")
        
        # Create reboot marker
        reboot_marker = Path(".reboot_required")
        try:
            with open(reboot_marker, 'w') as f:
                f.write("Reboot required for DWC2 and USB gadget configuration\n")
                f.write(f"Created: {datetime.now()}\n")
            self.reboot_required = True
            self.log("✅ Created reboot requirement marker", "SUCCESS")
        except Exception as e:
            self.log(f"⚠️ Could not create reboot marker: {e}", "WARNING")
        
        # Set installation complete
        self.installation_complete = True
        
        return True
    
    def install(self) -> bool:
        """Run complete installation process"""
        try:
            self.log("🚀 Starting Xbox 360 WiFi Emulator installation for Pi OS Bullseye ARM64", "INFO")
            
            for i, (step_name, step_func) in enumerate(self.steps, 1):
                self.current_step = i
                self.log(f"\n[Step {i}/{self.total_steps}] {step_name}", "INFO")
                self.log("-" * 50, "INFO")
                
                success = step_func()
                if not success:
                    self.log(f"❌ Step {i} failed: {step_name}", "ERROR")
                    return False
                
                self.log(f"✅ Step {i} completed: {step_name}", "SUCCESS")
            
            self.log("\n" + "=" * 60, "INFO")
            self.log("🎉 INSTALLATION COMPLETED SUCCESSFULLY!", "SUCCESS") 
            self.log("=" * 60, "INFO")
            
            if self.reboot_required:
                self.log("⚠️ REBOOT REQUIRED for USB gadget functionality", "WARNING")
                self.log("Run 'sudo reboot' to complete the installation", "INFO")
            
            return True
            
        except Exception as e:
            self.log(f"❌ Installation failed: {e}", "ERROR")
            import traceback
            self.log(traceback.format_exc(), "ERROR")
            return False
        finally:
            self.flush_log()
    
    def check_status(self) -> Dict[str, str]:
        """Check system status"""
        status = {}
        
        # Check DWC2 module
        success, stdout, _ = self.run_command("lsmod | grep dwc2", "")
        status['dwc2'] = "✅ Loaded" if success and stdout.strip() else "❌ Not Loaded"
        
        # Check USB controllers
        udc_path = Path('/sys/class/udc/')
        if udc_path.exists():
            udcs = list(udc_path.glob('*'))
            status['udc'] = f"✅ {len(udcs)} Found" if udcs else "❌ None Found"
        else:
            status['udc'] = "❌ Path Missing"
        
        # Check service
        success, stdout, _ = self.run_command("systemctl is-active xbox360-emulator", "")
        if success and 'active' in stdout:
            status['service'] = "✅ Running"
        else:
            status['service'] = "⏹️ Stopped"
        
        # Check network interface
        success, stdout, _ = self.run_command("ip link show usb0", "")
        if success:
            status['network'] = "✅ Up" if 'UP' in stdout else "⏸️ Down"
        else:
            status['network'] = "❌ Missing"
        
        return status

def main():
    """Main entry point"""
    print("🎮 Xbox 360 WiFi Module Emulator - Pi OS Bullseye ARM64")
    print("=" * 55)
    
    # Parse command line arguments
    dev_mode = False
    status_mode = False
    gui_mode = False
    
    if len(sys.argv) > 1:
        if "--status" in sys.argv:
            status_mode = True
        if "--dev" in sys.argv:
            dev_mode = True
            print("🔧 Development mode enabled - using local directories")
        if "--gui" in sys.argv:
            gui_mode = True
            print("🖥️ GUI mode enabled")
    
    installer = BullseyeXboxInstaller(dev_mode=dev_mode)
    
    if status_mode:
        status = installer.check_status()
        print("\n📊 System Status:")
        for component, state in status.items():
            print(f"   {component.upper()}: {state}")
        return
    
    if gui_mode:
        if not GUI_AVAILABLE:
            print("❌ GUI not available. Install with: sudo apt install python3-tk")
            return
        
        # Launch GUI
        gui = XboxInstallerGUI(dev_mode=dev_mode)
        gui.run()
        return
    
    if not installer.system_info['is_bullseye'] and not dev_mode:
        print("❌ This installer is optimized for Pi OS Bullseye")
        print("   Current OS may not be fully supported")
        print("   Use --dev flag for development/testing mode")
        input("Press Enter to continue anyway or Ctrl+C to exit...")
    
    success = installer.install()
    
    print(f"\n📂 Complete installation log: {installer.log_file}")
    
    if success:
        print("\n🎉 Installation completed successfully!")
        if installer.reboot_required:
            print("⚠️ REBOOT REQUIRED - Run 'sudo reboot' to complete setup")
    else:
        print("\n❌ Installation failed - check log file for details")

# Compatibility aliases for old test scripts
XboxInstallerCore = BullseyeXboxInstaller

# Full-featured GUI installer
class XboxInstallerGUI:
    """Complete GUI installer for Xbox 360 WiFi Emulator"""
    
    def __init__(self, dev_mode=False):
        if not GUI_AVAILABLE:
            raise ImportError("GUI not available - install python3-tk")
        
        self.dev_mode = dev_mode
        self.installer = BullseyeXboxInstaller(dev_mode=dev_mode)
        self.root = None
        self.progress_var = None
        self.status_var = None
        self.log_text = None
        self.install_button = None
        self.installation_running = False
        self.install_thread = None
    
    def run(self):
        """Run the GUI application"""
        self.create_gui()
        self.root.mainloop()
    
    def create_gui(self):
        """Create the complete GUI interface"""
        self.root = tk.Tk()
        self.root.title("Xbox 360 WiFi Emulator - Installer")
        self.root.geometry("800x600")
        self.root.resizable(True, True)
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(4, weight=1)
        
        # Header
        header_frame = ttk.Frame(main_frame)
        header_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Label(header_frame, text="🎮 Xbox 360 WiFi Module Emulator", 
                 font=('Arial', 16, 'bold')).pack()
        ttk.Label(header_frame, text="Raspberry Pi OS Bullseye ARM64 Installer", 
                 font=('Arial', 10)).pack()
        
        if self.dev_mode:
            ttk.Label(header_frame, text="🔧 Development Mode - Local Installation", 
                     font=('Arial', 10), foreground='blue').pack()
        
        # System info frame
        info_frame = ttk.LabelFrame(main_frame, text="System Information", padding="5")
        info_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        info_frame.columnconfigure(1, weight=1)
        
        system_info = self.installer.system_info
        info_items = [
            ("OS:", f"{system_info['os']} ({system_info['arch']})"),
            ("Python:", system_info['python_version']),
            ("Bullseye:", "✅ Yes" if system_info['is_bullseye'] else "❌ No"),
            ("ARM64:", "✅ Yes" if system_info['is_arm64'] else "❌ No"),
            ("Raspberry Pi:", "✅ Yes" if system_info['is_pi'] else "❌ No")
        ]
        
        for i, (label, value) in enumerate(info_items):
            ttk.Label(info_frame, text=label).grid(row=i, column=0, sticky=tk.W, padx=(0, 10))
            ttk.Label(info_frame, text=value).grid(row=i, column=1, sticky=tk.W)
        
        # Control frame
        control_frame = ttk.Frame(main_frame)
        control_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.install_button = ttk.Button(control_frame, text="Start Installation", 
                                       command=self._start_installation)
        self.install_button.pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(control_frame, text="Check Status", 
                  command=self._check_status).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(control_frame, text="USB Tools", 
                  command=self._open_usb_tools).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(control_frame, text="View Logs", 
                  command=self._view_logs).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(control_frame, text="Exit", 
                  command=self._exit_app).pack(side=tk.RIGHT)
        
        # Progress frame
        progress_frame = ttk.Frame(main_frame)
        progress_frame.grid(row=3, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        progress_frame.columnconfigure(0, weight=1)
        
        self.status_var = tk.StringVar(value="Ready to install")
        ttk.Label(progress_frame, textvariable=self.status_var).grid(row=0, column=0, sticky=tk.W)
        
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var, 
                                          maximum=100, length=400)
        self.progress_bar.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(5, 0))
        
        # Log frame
        log_frame = ttk.LabelFrame(main_frame, text="Installation Log", padding="5")
        log_frame.grid(row=4, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, width=80, height=20, 
                                                state=tk.DISABLED)
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure text tags for colored output
        self.log_text.tag_configure("INFO", foreground="black")
        self.log_text.tag_configure("SUCCESS", foreground="green")
        self.log_text.tag_configure("WARNING", foreground="orange")
        self.log_text.tag_configure("ERROR", foreground="red")
        
        self._log_message("GUI initialized. Ready to start installation.", "INFO")
    
    def _log_message(self, message, level="INFO"):
        """Add message to log text widget"""
        if self.log_text:
            self.log_text.config(state=tk.NORMAL)
            timestamp = datetime.now().strftime("%H:%M:%S")
            self.log_text.insert(tk.END, f"[{timestamp}] {message}\n", level)
            self.log_text.see(tk.END)
            self.log_text.config(state=tk.DISABLED)
            self.root.update_idletasks()
    
    def _start_installation(self):
        """Start the installation process in a separate thread"""
        if self.installation_running:
            messagebox.showwarning("Installation Running", 
                                 "Installation is already in progress!")
            return
        
        # Confirm installation
        if not self.dev_mode:
            if not messagebox.askyesno("Confirm Installation", 
                                     "This will install Xbox 360 WiFi Emulator on your system.\n\n"
                                     "The installation will:\n"
                                     "• Modify system configuration files\n"
                                     "• Install system packages\n"
                                     "• Create system services\n"
                                     "• May require a reboot\n\n"
                                     "Continue?"):
                return
        
        self.installation_running = True
        self.install_button.config(state=tk.DISABLED)
        self.status_var.set("Starting installation...")
        self.progress_var.set(0)
        
        # Start installation in separate thread
        self.install_thread = threading.Thread(target=self._run_installation, daemon=True)
        self.install_thread.start()
    
    def _run_installation(self):
        """Run the installation process"""
        try:
            self._log_message("Starting Xbox 360 WiFi Emulator installation", "INFO")
            
            # Hook into installer logging
            original_log = self.installer.log
            def gui_log(message, level="INFO"):
                original_log(message, level)
                self._log_message(message, level)
                
                # Update progress based on step
                step_progress = (self.installer.current_step / self.installer.total_steps) * 100
                self.progress_var.set(step_progress)
                self.status_var.set(f"Step {self.installer.current_step}/{self.installer.total_steps}: {message}")
            
            self.installer.log = gui_log
            
            # Run installation
            success = self.installer.install()
            
            if success:
                self.progress_var.set(100)
                self.status_var.set("Installation completed successfully!")
                self._log_message("🎉 Installation completed successfully!", "SUCCESS")
                
                if self.installer.reboot_required:
                    self._log_message("⚠️ REBOOT REQUIRED - System needs to be rebooted", "WARNING")
                    messagebox.showinfo("Installation Complete", 
                                      "Installation completed successfully!\n\n"
                                      "A system reboot is required to complete the setup.\n"
                                      "Run 'sudo reboot' when ready.")
                else:
                    messagebox.showinfo("Installation Complete", 
                                      "Installation completed successfully!")
            else:
                self.status_var.set("Installation failed!")
                self._log_message("❌ Installation failed - check log for details", "ERROR")
                messagebox.showerror("Installation Failed", 
                                   "Installation failed. Please check the log for details.")
                
        except Exception as e:
            self.status_var.set("Installation error!")
            self._log_message(f"❌ Installation error: {e}", "ERROR")
            messagebox.showerror("Installation Error", f"Installation error: {e}")
            
        finally:
            self.installation_running = False
            self.install_button.config(state=tk.NORMAL)
    
    def _check_status(self):
        """Check system status"""
        self._log_message("Checking system status...", "INFO")
        status = self.installer.check_status()
        
        status_window = tk.Toplevel(self.root)
        status_window.title("System Status")
        status_window.geometry("400x300")
        
        frame = ttk.Frame(status_window, padding="10")
        frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(frame, text="System Status", font=('Arial', 14, 'bold')).pack(pady=(0, 10))
        
        for component, state in status.items():
            status_frame = ttk.Frame(frame)
            status_frame.pack(fill=tk.X, pady=2)
            ttk.Label(status_frame, text=f"{component.upper()}:").pack(side=tk.LEFT)
            ttk.Label(status_frame, text=state).pack(side=tk.RIGHT)
        
        ttk.Button(frame, text="Close", command=status_window.destroy).pack(pady=(10, 0))
    
    def _open_usb_tools(self):
        """Open USB tools window"""
        usb_window = tk.Toplevel(self.root)
        usb_window.title("Xbox 360 USB Tools")
        usb_window.geometry("600x500")
        
        main_frame = ttk.Frame(usb_window, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(main_frame, text="🔍 Xbox 360 USB Tools", font=('Arial', 14, 'bold')).pack(pady=(0, 10))
        
        # Device scanning section
        scan_frame = ttk.LabelFrame(main_frame, text="Device Scanner", padding="5")
        scan_frame.pack(fill=tk.X, pady=(0, 10))
        
        devices_text = tk.Text(scan_frame, height=4, width=60)
        devices_text.pack(fill=tk.X, pady=(0, 5))
        
        scan_button = ttk.Button(scan_frame, text="Scan for Xbox Devices", 
                               command=lambda: self._scan_devices(devices_text))
        scan_button.pack()
        
        # USB capture section
        capture_frame = ttk.LabelFrame(main_frame, text="USB Capture", padding="5")
        capture_frame.pack(fill=tk.X, pady=(0, 10))
        
        duration_frame = ttk.Frame(capture_frame)
        duration_frame.pack(fill=tk.X, pady=(0, 5))
        ttk.Label(duration_frame, text="Duration (seconds):").pack(side=tk.LEFT)
        duration_var = tk.StringVar(value="30")
        duration_entry = ttk.Entry(duration_frame, textvariable=duration_var, width=10)
        duration_entry.pack(side=tk.LEFT, padx=(5, 0))
        
        capture_button = ttk.Button(capture_frame, text="Start USB Capture", 
                                  command=lambda: self._start_capture(int(duration_var.get())))
        capture_button.pack(pady=(5, 0))
        
        # Passthrough section
        passthrough_frame = ttk.LabelFrame(main_frame, text="USB Passthrough", padding="5")
        passthrough_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(passthrough_frame, text="⚠️ Advanced feature - requires Xbox device connected").pack()
        passthrough_button = ttk.Button(passthrough_frame, text="Setup Passthrough", 
                                      command=self._setup_passthrough)
        passthrough_button.pack(pady=(5, 0))
        
        # Status section
        status_frame = ttk.LabelFrame(main_frame, text="USB System Status", padding="5")
        status_frame.pack(fill=tk.BOTH, expand=True)
        
        status_text = scrolledtext.ScrolledText(status_frame, height=8, width=60)
        status_text.pack(fill=tk.BOTH, expand=True, pady=(0, 5))
        
        refresh_button = ttk.Button(status_frame, text="Refresh Status", 
                                  command=lambda: self._refresh_usb_status(status_text))
        refresh_button.pack()
        
        # Initialize with current status
        self._refresh_usb_status(status_text)
        
        ttk.Button(main_frame, text="Close", command=usb_window.destroy).pack(pady=(10, 0))
    
    def _scan_devices(self, text_widget):
        """Scan for Xbox devices and display results"""
        try:
            # Import USB manager
            sys.path.insert(0, str(Path(__file__).parent / "src"))
            from usb_passthrough_manager import USBPassthroughManager
            
            manager = USBPassthroughManager()
            devices = manager.scan_xbox_devices()
            
            text_widget.delete(1.0, tk.END)
            if devices:
                text_widget.insert(tk.END, f"Found {len(devices)} Xbox 360 devices:\n\n")
                for i, dev in enumerate(devices, 1):
                    text_widget.insert(tk.END, f"{i}. {dev['vendor_product']}\n")
                    text_widget.insert(tk.END, f"   {dev['description']}\n")
                    text_widget.insert(tk.END, f"   Bus {dev['bus']}, Device {dev['device']}\n\n")
            else:
                text_widget.insert(tk.END, "No Xbox 360 devices found.\n")
                text_widget.insert(tk.END, "Make sure devices are connected and drivers are installed.")
                
        except Exception as e:
            text_widget.delete(1.0, tk.END)
            text_widget.insert(tk.END, f"Error scanning devices: {e}")
    
    def _start_capture(self, duration):
        """Start USB capture"""
        try:
            messagebox.showinfo("USB Capture", 
                              f"Starting USB capture for {duration} seconds.\n\n"
                              "Connect/disconnect Xbox devices during this time.\n"
                              "Capture will be saved to Desktop/captures/")
            
            # This would integrate with the USB manager
            self._log_message(f"USB capture started for {duration} seconds", "INFO")
            
        except Exception as e:
            messagebox.showerror("Capture Error", f"Failed to start capture: {e}")
    
    def _setup_passthrough(self):
        """Setup USB passthrough"""
        result = messagebox.askyesno("USB Passthrough", 
                                   "USB passthrough allows the Pi to act as a USB proxy.\n\n"
                                   "This is an advanced feature that requires:\n"
                                   "• Xbox device connected to Pi\n"
                                   "• Raw gadget kernel support\n"
                                   "• Proper USB cable setup\n\n"
                                   "Continue with setup?")
        
        if result:
            try:
                self._log_message("Setting up USB passthrough...", "INFO")
                messagebox.showinfo("Passthrough Setup", 
                                  "Passthrough setup initiated.\nCheck logs for progress.")
            except Exception as e:
                messagebox.showerror("Setup Error", f"Failed to setup passthrough: {e}")
    
    def _refresh_usb_status(self, text_widget):
        """Refresh USB system status"""
        try:
            text_widget.delete(1.0, tk.END)
            
            # Check various USB system components
            status_items = [
                ("USB monitoring (usbmon)", os.path.exists("/sys/kernel/debug/usb/usbmon")),
                ("Raw gadget support", os.path.exists("/dev/raw-gadget")),
                ("DWC2 module", self._check_module_loaded("dwc2")),
                ("libcomposite module", self._check_module_loaded("libcomposite")),
                ("USB gadget configfs", os.path.exists("/sys/kernel/config/usb_gadget")),
            ]
            
            text_widget.insert(tk.END, "USB System Status:\n\n")
            for item, status in status_items:
                status_text = "✅ Available" if status else "❌ Not Available"
                text_widget.insert(tk.END, f"{item}: {status_text}\n")
            
            text_widget.insert(tk.END, f"\nCapture directory: {Path.home() / 'Desktop' / 'captures'}\n")
            
        except Exception as e:
            text_widget.delete(1.0, tk.END)
            text_widget.insert(tk.END, f"Error checking status: {e}")
    
    def _check_module_loaded(self, module_name):
        """Check if a kernel module is loaded"""
        try:
            result = subprocess.run(['lsmod'], capture_output=True, text=True, check=True)
            return module_name in result.stdout
        except:
            return False
    
    def _view_logs(self):
        """Open log file in system viewer"""
        try:
            if self.installer.log_file.exists():
                import subprocess
                subprocess.run(['xdg-open', str(self.installer.log_file)])
            else:
                messagebox.showinfo("No Log File", "No log file found yet.")
        except Exception as e:
            messagebox.showerror("Error", f"Could not open log file: {e}")
    
    def _exit_app(self):
        """Exit the application"""
        if self.installation_running:
            if not messagebox.askyesno("Exit During Installation", 
                                     "Installation is running. Are you sure you want to exit?"):
                return
        
        self.root.quit()
        self.root.destroy()

if __name__ == "__main__":
    main()