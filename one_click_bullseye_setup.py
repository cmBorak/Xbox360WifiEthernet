#!/usr/bin/env python3
"""
One-Click Xbox 360 WiFi Emulator Setup for Pi OS Bullseye ARM64
Automates the complete workflow: validate → fix → install → reboot prompt
"""

import os
import sys
import subprocess
import time
from pathlib import Path
from datetime import datetime

# GUI support for confirmation dialogs
try:
    import tkinter as tk
    from tkinter import messagebox
    GUI_AVAILABLE = True
except ImportError:
    GUI_AVAILABLE = False

class OneClickBullseyeSetup:
    """One-click automation for complete Bullseye setup"""
    
    def __init__(self):
        self.setup_logging()
        self.workflow_steps = [
            ("System Validation", "python3 validate_bullseye_system.py"),
            ("Apply Bullseye Fixes", "python3 comprehensive_bullseye_fix.py"), 
            ("Desktop Integration", "python3 fix_desktop_paths_bullseye.py"),
            ("Install Xbox Emulator", "python3 installer.py"),
            ("Reboot Prompt", "reboot_prompt")
        ]
        self.current_step = 0
        self.total_steps = len(self.workflow_steps)
        
    def setup_logging(self):
        """Setup one-click setup logging"""
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
        
        # Create one-click log
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_file = self.debug_log_dir / f"one_click_setup_{timestamp}.log"
        self.log_buffer = []
        
        self.log("🚀 Xbox 360 WiFi Emulator - One-Click Bullseye Setup", "INFO")
        self.log("=" * 60, "INFO")
        self.log(f"Setup started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", "INFO")
        self.log(f"Working directory: {Path.cwd()}", "INFO")
        self.log(f"Log file: {self.log_file}", "INFO")
        self.log("=" * 60, "INFO")
    
    def log(self, message: str, level: str = "INFO"):
        """Enhanced logging with colors and progress"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] [{level}] {message}"
        self.log_buffer.append(log_entry + "\n")
        
        # Console colors with step progress
        colors = {
            "INFO": "\033[0;36m",      # Cyan
            "SUCCESS": "\033[0;32m",   # Green
            "WARNING": "\033[1;33m",   # Yellow
            "ERROR": "\033[0;31m",     # Red
            "CRITICAL": "\033[1;35m",  # Magenta
            "STEP": "\033[1;34m"       # Bold Blue
        }
        
        color = colors.get(level, "\033[0m")
        
        # Add step progress for important messages
        if level == "STEP":
            progress = f"[{self.current_step}/{self.total_steps}]"
            print(f"{color}{progress} {message}\033[0m")
        else:
            print(f"{color}[{timestamp}] {message}\033[0m")
        
        # Flush important messages
        if len(self.log_buffer) >= 3 or level in ['ERROR', 'SUCCESS', 'CRITICAL', 'STEP']:
            self.flush_log()
    
    def flush_log(self):
        """Write log buffer to file"""
        try:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.writelines(self.log_buffer)
            self.log_buffer = []
        except Exception as e:
            print(f"Warning: Could not write to log file: {e}")
    
    def show_welcome_message(self):
        """Show welcome message and get user confirmation"""
        welcome_text = """
🎮 Xbox 360 WiFi Module Emulator - One-Click Setup
═══════════════════════════════════════════════════

This script will automatically:
  1. ✅ Validate your Pi OS Bullseye ARM64 system
  2. 🔧 Apply comprehensive Bullseye fixes
  3. 🖥️ Setup desktop integration
  4. 📦 Install Xbox 360 emulator
  5. 🔄 Prompt for required reboot

⚠️  IMPORTANT NOTES:
  • This process may take 10-15 minutes
  • Your Pi will need to reboot at the end
  • All operations are logged to debuglogs/
  • You can monitor progress in the terminal

🎯 REQUIREMENTS:
  • Pi OS Bullseye ARM64 (64-bit)
  • Raspberry Pi 4+ recommended
  • Internet connection for packages
  • sudo privileges for system changes
"""
        
        print(welcome_text)
        
        # GUI confirmation if available
        if GUI_AVAILABLE:
            try:
                root = tk.Tk()
                root.withdraw()  # Hide main window
                
                response = messagebox.askyesno(
                    "Xbox 360 WiFi Emulator - One-Click Setup",
                    "Start the automated setup process?\n\n"
                    "This will:\n"
                    "• Validate your system\n" 
                    "• Apply Bullseye fixes\n"
                    "• Install the emulator\n"
                    "• Require a reboot\n\n"
                    "Continue?",
                    icon='question'
                )
                
                root.destroy()
                return response
            except:
                pass
        
        # Fallback to console confirmation
        while True:
            response = input("\n🚀 Ready to start? [Y/n]: ").strip().lower()
            if response in ['', 'y', 'yes']:
                return True
            elif response in ['n', 'no']:
                return False
            else:
                print("Please enter 'y' for yes or 'n' for no")
    
    def check_prerequisites(self):
        """Check basic prerequisites before starting"""
        self.log("\n🔍 CHECKING PREREQUISITES", "STEP")
        self.log("-" * 30, "INFO")
        
        prerequisites_ok = True
        
        # Check if we're in the right directory
        required_files = [
            "validate_bullseye_system.py",
            "comprehensive_bullseye_fix.py", 
            "fix_desktop_paths_bullseye.py",
            "installer.py"
        ]
        
        for filename in required_files:
            if Path(filename).exists():
                self.log(f"✅ Found: {filename}", "SUCCESS")
            else:
                self.log(f"❌ Missing: {filename}", "ERROR")
                prerequisites_ok = False
        
        # Check Python version
        python_version = f"{sys.version_info.major}.{sys.version_info.minor}"
        if sys.version_info >= (3, 9):
            self.log(f"✅ Python {python_version} is compatible", "SUCCESS")
        else:
            self.log(f"❌ Python {python_version} may be too old", "ERROR")
            prerequisites_ok = False
        
        # Check sudo access
        try:
            result = subprocess.run(['sudo', '-n', 'true'], capture_output=True)
            if result.returncode == 0:
                self.log("✅ Sudo access confirmed", "SUCCESS")
            else:
                self.log("⚠️ Sudo access required for installation", "WARNING")
                # Not a blocker, will prompt when needed
        except:
            self.log("⚠️ Could not verify sudo access", "WARNING")
        
        if not prerequisites_ok:
            self.log("\n❌ Prerequisites check failed!", "ERROR")
            self.log("Make sure you're in the Xbox360WifiEthernet directory", "ERROR")
            return False
        
        self.log("\n✅ Prerequisites check passed!", "SUCCESS")
        return True
    
    def run_workflow_step(self, step_name: str, command: str):
        """Run a single workflow step"""
        self.current_step += 1
        
        self.log(f"\n{step_name}", "STEP")
        self.log("=" * len(step_name), "INFO")
        
        if command == "reboot_prompt":
            return self.handle_reboot_prompt()
        
        try:
            # Show what we're about to run
            self.log(f"Executing: {command}", "INFO")
            
            # Run the command with real-time output
            process = subprocess.Popen(
                command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1
            )
            
            # Stream output in real-time
            while True:
                output = process.stdout.readline()
                if output == '' and process.poll() is not None:
                    break
                if output:
                    # Clean up the output and log it
                    clean_output = output.strip()
                    if clean_output:
                        # Preserve color codes from the child process
                        print(f"  {clean_output}")
                        # Also log to file (without color codes)
                        import re
                        clean_for_log = re.sub(r'\033\[[0-9;]*m', '', clean_output)
                        self.log_buffer.append(f"  {clean_for_log}\n")
            
            # Get final return code
            return_code = process.poll()
            
            if return_code == 0:
                self.log(f"✅ {step_name} completed successfully", "SUCCESS")
                return True
            else:
                self.log(f"❌ {step_name} failed (exit code: {return_code})", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ {step_name} failed with exception: {e}", "ERROR")
            return False
    
    def handle_reboot_prompt(self):
        """Handle the reboot prompt step"""
        self.log("🔄 Installation complete! Reboot is required for USB gadget functionality.", "INFO")
        
        # GUI reboot prompt if available
        if GUI_AVAILABLE:
            try:
                root = tk.Tk()
                root.withdraw()
                
                response = messagebox.askyesnocancel(
                    "Reboot Required",
                    "Installation complete!\n\n"
                    "A reboot is required for USB gadget functionality to work.\n\n"
                    "Reboot now?\n\n"
                    "• Yes: Reboot immediately\n"
                    "• No: Reboot later manually\n"
                    "• Cancel: Show instructions",
                    icon='question'
                )
                
                root.destroy()
                
                if response is True:  # Yes - reboot now
                    self.log("🔄 Rebooting system now...", "INFO")
                    subprocess.run(['sudo', 'reboot'])
                    return True
                elif response is False:  # No - reboot later
                    self.log("⏸️ Reboot postponed - remember to reboot manually", "WARNING")
                    self.show_completion_instructions(manual_reboot=True)
                    return True
                else:  # Cancel - show instructions
                    self.show_completion_instructions(manual_reboot=True)
                    return True
            except:
                pass
        
        # Fallback to console prompt
        print("\n🔄 REBOOT REQUIRED")
        print("=" * 20)
        print("Installation is complete, but a reboot is required for")
        print("USB gadget functionality to work properly.")
        print()
        
        while True:
            choice = input("Reboot now? [Y/n/i]: ").strip().lower()
            if choice in ['', 'y', 'yes']:
                self.log("🔄 Rebooting system now...", "INFO")
                subprocess.run(['sudo', 'reboot'])
                return True
            elif choice in ['n', 'no']:
                self.log("⏸️ Reboot postponed - remember to reboot manually", "WARNING")
                self.show_completion_instructions(manual_reboot=True)
                return True
            elif choice in ['i', 'info']:
                self.show_completion_instructions(manual_reboot=True)
                return True
            else:
                print("Please enter 'y' to reboot now, 'n' to reboot later, or 'i' for info")
    
    def show_completion_instructions(self, manual_reboot=False):
        """Show completion instructions"""
        instructions = f"""
🎉 Xbox 360 WiFi Emulator Setup Complete!
═══════════════════════════════════════════

📦 WHAT WAS INSTALLED:
  ✅ System validated for Bullseye ARM64
  ✅ Comprehensive Bullseye fixes applied  
  ✅ Desktop integration created
  ✅ Xbox 360 emulator installed

📂 LOGGING:
  📄 Complete setup log: {self.log_file}
  📁 All logs saved to: {self.debug_log_dir}/

🚀 NEXT STEPS:
"""
        
        if manual_reboot:
            instructions += """  1. 🔄 Reboot your Pi: sudo reboot
  2. 🎮 After reboot, launch emulator:
     • Double-click desktop files, or
     • Run: ./launch_bullseye_comprehensive.sh"""
        else:
            instructions += """  🎮 After reboot, launcher options:
     • Double-click desktop files, or  
     • Run: ./launch_bullseye_comprehensive.sh"""
        
        instructions += f"""

🖥️ DESKTOP FILES CREATED:
  • Xbox360-Emulator-Bullseye.desktop (GUI)
  • Xbox360-Emulator-Bullseye-Terminal.desktop (Terminal)
  • Xbox360-Emulator-Bullseye-Comprehensive.desktop (Full launcher)
  • Xbox360-Emulator-Bullseye-Fix.desktop (Fix issues)

🔧 TROUBLESHOOTING:
  • Check status: python3 installer.py --status
  • Validate system: python3 validate_bullseye_system.py
  • Apply fixes: python3 comprehensive_bullseye_fix.py

💡 SUPPORT:
  All operations are logged to debuglogs/ for troubleshooting.
  Check the README_BULLSEYE.md for detailed documentation.
"""
        
        print(instructions)
        self.log("Setup completion instructions displayed", "INFO")
    
    def handle_step_failure(self, step_name: str, step_num: int):
        """Handle when a workflow step fails"""
        self.log(f"\n❌ Step {step_num} failed: {step_name}", "ERROR")
        
        # GUI error dialog if available
        if GUI_AVAILABLE:
            try:
                root = tk.Tk()
                root.withdraw()
                
                response = messagebox.askyesnocancel(
                    f"Step Failed: {step_name}",
                    f"Step {step_num} failed: {step_name}\n\n"
                    f"Check the log file for details:\n{self.log_file}\n\n"
                    "Continue with remaining steps?",
                    icon='error'
                )
                
                root.destroy()
                
                if response is True:  # Continue
                    return True
                elif response is False:  # Stop
                    return False
                else:  # Cancel - show log
                    self.log(f"User requested log viewing for failed step: {step_name}", "INFO")
                    return False
            except:
                pass
        
        # Console fallback
        print(f"\n❌ STEP FAILED: {step_name}")
        print("=" * 30)
        print(f"Check the log file for details: {self.log_file}")
        print()
        
        while True:
            choice = input("Continue with remaining steps? [y/N]: ").strip().lower()
            if choice in ['y', 'yes']:
                return True
            elif choice in ['', 'n', 'no']:
                return False
            else:
                print("Please enter 'y' to continue or 'n' to stop")
    
    def run_one_click_setup(self):
        """Run the complete one-click setup workflow"""
        try:
            # Show welcome and get confirmation
            if not self.show_welcome_message():
                self.log("Setup cancelled by user", "INFO")
                print("\n👋 Setup cancelled. Run again when ready!")
                return False
            
            self.log("🚀 Starting one-click Bullseye setup...", "INFO")
            
            # Check prerequisites
            if not self.check_prerequisites():
                return False
            
            # Run each workflow step
            for step_name, command in self.workflow_steps:
                success = self.run_workflow_step(step_name, command)
                
                if not success:
                    # Handle step failure
                    if not self.handle_step_failure(step_name, self.current_step):
                        self.log("Setup stopped due to step failure", "ERROR")
                        return False
                    else:
                        self.log(f"Continuing despite {step_name} failure", "WARNING")
                
                # Small delay between steps for readability
                time.sleep(1)
            
            self.log("\n" + "=" * 60, "INFO") 
            self.log("🎉 ONE-CLICK BULLSEYE SETUP COMPLETE!", "SUCCESS")
            self.log("=" * 60, "INFO")
            
            return True
            
        except KeyboardInterrupt:
            self.log("\n⏹️ Setup interrupted by user (Ctrl+C)", "WARNING")
            print("\n⏹️ Setup interrupted. Partial installation may need cleanup.")
            return False
        except Exception as e:
            self.log(f"❌ One-click setup failed: {e}", "ERROR")
            import traceback
            self.log(traceback.format_exc(), "ERROR")
            return False
        finally:
            self.flush_log()

def main():
    """Main one-click setup function"""
    print("🚀 Xbox 360 WiFi Emulator - One-Click Pi OS Bullseye ARM64 Setup")
    print("=" * 70)
    print()
    
    # Check if we're likely on the right system
    try:
        with open('/etc/os-release', 'r') as f:
            os_content = f.read()
        if 'bullseye' not in os_content.lower():
            print("⚠️  WARNING: This script is optimized for Pi OS Bullseye")
            print("   Current OS may not be fully supported")
            input("   Press Enter to continue anyway or Ctrl+C to exit...")
    except:
        print("⚠️  Could not detect OS version")
        input("   Press Enter to continue or Ctrl+C to exit...")
    
    setup = OneClickBullseyeSetup()
    success = setup.run_one_click_setup()
    
    print(f"\n📂 Complete setup log: {setup.log_file}")
    
    if success:
        print("\n🎉 One-click setup completed successfully!")
        print("🔄 Follow the reboot instructions to finish the installation")
    else:
        print("\n❌ One-click setup encountered issues")
        print("💡 Check the log file for detailed information")
        print("🔧 You can run individual scripts manually if needed")

if __name__ == "__main__":
    main()