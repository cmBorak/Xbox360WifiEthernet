#!/usr/bin/env python3
"""
Desktop App Debug Script
Diagnoses desktop launcher issues and logs everything to debuglogs directory
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path
from datetime import datetime
import platform

class DesktopAppDebugger:
    def __init__(self):
        self.setup_logging()
        
    def setup_logging(self):
        """Setup centralized logging to debuglogs directory"""
        # Find desktop directory
        desktop_paths = [
            Path.home() / "Desktop",
            Path("/home/pi/Desktop"),
            Path("/home") / os.getenv('USER', 'pi') / "Desktop",
            Path.home() / "desktop"
        ]
        
        desktop_dir = None
        for path in desktop_paths:
            if path.exists():
                desktop_dir = path
                break
        
        if not desktop_dir:
            desktop_dir = Path.home() / "Desktop"
            desktop_dir.mkdir(exist_ok=True)
        
        # Create debuglogs directory
        self.debug_log_dir = desktop_dir / "debuglogs"
        self.debug_log_dir.mkdir(exist_ok=True)
        
        # Create log file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_file = self.debug_log_dir / f"desktop_debug_{timestamp}.log"
        
        # Start logging
        self.log_buffer = []
        self.log("🖥️ Desktop App Debug Session Started", "INFO")
        self.log("=" * 60, "INFO")
        self.log(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", "INFO")
        self.log(f"System: {platform.platform()}", "INFO")
        self.log(f"User: {os.getenv('USER', 'unknown')}", "INFO")
        self.log(f"Working Directory: {Path.cwd()}", "INFO")
        self.log(f"Script Directory: {Path(__file__).parent}", "INFO")
        self.log(f"Log File: {self.log_file}", "INFO")
        self.log("=" * 60, "INFO")
        
    def log(self, message, level="INFO"):
        """Add message to log buffer and print to console"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] [{level}] {message}"
        self.log_buffer.append(log_entry + "\n")
        print(log_entry)
        
        # Flush buffer every few entries or on errors
        if len(self.log_buffer) >= 5 or level in ['ERROR', 'CRITICAL']:
            self.flush_log()
    
    def flush_log(self):
        """Write log buffer to file"""
        try:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.writelines(self.log_buffer)
            self.log_buffer = []
        except Exception as e:
            print(f"Warning: Could not write to log file: {e}")
    
    def run_command(self, cmd, description="", timeout=10):
        """Run command and log results"""
        self.log(f"🔧 {description}", "INFO")
        self.log(f"Command: {cmd}", "DEBUG")
        
        try:
            result = subprocess.run(cmd, shell=True, capture_output=True, 
                                  text=True, timeout=timeout)
            
            if result.returncode == 0:
                self.log(f"✅ Success (exit code: {result.returncode})", "SUCCESS")
                if result.stdout:
                    for line in result.stdout.strip().split('\n'):
                        if line.strip():
                            self.log(f"   {line}", "OUTPUT")
            else:
                self.log(f"❌ Failed (exit code: {result.returncode})", "ERROR")
                if result.stderr:
                    for line in result.stderr.strip().split('\n'):
                        if line.strip():
                            self.log(f"   {line}", "ERROR")
                if result.stdout:
                    for line in result.stdout.strip().split('\n'):
                        if line.strip():
                            self.log(f"   {line}", "OUTPUT")
            
            return result
            
        except subprocess.TimeoutExpired:
            self.log(f"⏰ Command timed out after {timeout}s", "ERROR")
            return None
        except Exception as e:
            self.log(f"❌ Command failed: {e}", "ERROR")
            return None
    
    def check_file_permissions(self, filepath):
        """Check file permissions and log details"""
        try:
            path = Path(filepath)
            if path.exists():
                stat = path.stat()
                perms = oct(stat.st_mode)[-3:]
                
                self.log(f"📂 {filepath}", "INFO")
                self.log(f"   Exists: ✅ Yes", "SUCCESS")
                self.log(f"   Permissions: {perms}", "INFO")
                self.log(f"   Size: {stat.st_size} bytes", "INFO")
                self.log(f"   Owner: {stat.st_uid}", "INFO")
                
                # Check if executable
                if os.access(filepath, os.X_OK):
                    self.log(f"   Executable: ✅ Yes", "SUCCESS")
                else:
                    self.log(f"   Executable: ❌ No", "ERROR")
                
                return True
            else:
                self.log(f"📂 {filepath}", "INFO")
                self.log(f"   Exists: ❌ No", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Error checking {filepath}: {e}", "ERROR")
            return False
    
    def debug_desktop_environment(self):
        """Debug desktop environment"""
        self.log("\n🖥️ Desktop Environment Analysis", "INFO")
        self.log("-" * 40, "INFO")
        
        # Check desktop session
        desktop_session = os.getenv('DESKTOP_SESSION', 'unknown')
        self.log(f"Desktop Session: {desktop_session}", "INFO")
        
        # Check XDG environment
        xdg_vars = ['XDG_CURRENT_DESKTOP', 'XDG_SESSION_TYPE', 'XDG_DATA_DIRS']
        for var in xdg_vars:
            value = os.getenv(var, 'not set')
            self.log(f"{var}: {value}", "INFO")
        
        # Check display
        display = os.getenv('DISPLAY', 'not set')
        self.log(f"DISPLAY: {display}", "INFO")
        
        # Check if running in X11 or Wayland
        if os.getenv('WAYLAND_DISPLAY'):
            self.log("Session Type: Wayland", "INFO")
        elif os.getenv('DISPLAY'):
            self.log("Session Type: X11", "INFO")
        else:
            self.log("Session Type: Console/Unknown", "WARNING")
    
    def debug_desktop_files(self):
        """Debug desktop files"""
        self.log("\n📄 Desktop Files Analysis", "INFO")
        self.log("-" * 30, "INFO")
        
        script_dir = Path.cwd()
        desktop_files = list(script_dir.glob("*.desktop"))
        
        if not desktop_files:
            self.log("❌ No desktop files found in current directory", "ERROR")
            return
        
        for desktop_file in desktop_files:
            self.log(f"\n🔍 Analyzing: {desktop_file.name}", "INFO")
            
            # Check file permissions
            self.check_file_permissions(desktop_file)
            
            # Read and analyze content
            try:
                with open(desktop_file, 'r') as f:
                    content = f.read()
                
                self.log("📝 Desktop file content:", "INFO")
                for i, line in enumerate(content.split('\n'), 1):
                    if line.strip():
                        self.log(f"   {i:2d}: {line}", "DEBUG")
                
                # Check for common issues
                if 'Exec=' in content:
                    exec_line = [line for line in content.split('\n') if line.startswith('Exec=')][0]
                    self.log(f"🚀 Exec command: {exec_line}", "INFO")
                    
                    # Check if paths exist
                    if '%k' in exec_line:
                        self.log("✅ Uses %k parameter for relative paths", "SUCCESS")
                    elif 'SCRIPT_DIR' in exec_line:
                        self.log("✅ Uses SCRIPT_DIR for dynamic paths", "SUCCESS")
                    elif '/mnt/c/' in exec_line or '/home/' in exec_line:
                        self.log("⚠️ Contains hardcoded paths", "WARNING")
                
            except Exception as e:
                self.log(f"❌ Error reading desktop file: {e}", "ERROR")
    
    def debug_python_environment(self):
        """Debug Python environment"""
        self.log("\n🐍 Python Environment Analysis", "INFO")
        self.log("-" * 35, "INFO")
        
        # Python version
        self.log(f"Python Version: {sys.version}", "INFO")
        self.log(f"Python Executable: {sys.executable}", "INFO")
        
        # Check installer.py
        installer_path = Path.cwd() / "installer.py"
        if installer_path.exists():
            self.log("✅ installer.py found", "SUCCESS")
            
            # Test syntax
            result = self.run_command(f"python3 -m py_compile {installer_path}", 
                                    "Testing installer.py syntax")
            
            # Check imports
            self.log("🔍 Testing critical imports:", "INFO")
            critical_imports = ['tkinter', 'pathlib', 'subprocess', 'threading']
            for module in critical_imports:
                try:
                    __import__(module)
                    self.log(f"   ✅ {module}", "SUCCESS")
                except ImportError as e:
                    self.log(f"   ❌ {module}: {e}", "ERROR")
        else:
            self.log("❌ installer.py not found", "ERROR")
    
    def test_desktop_file_execution(self):
        """Test desktop file execution"""
        self.log("\n🧪 Desktop File Execution Test", "INFO")
        self.log("-" * 37, "INFO")
        
        desktop_files = list(Path.cwd().glob("*.desktop"))
        
        for desktop_file in desktop_files:
            self.log(f"\n🎯 Testing: {desktop_file.name}", "INFO")
            
            try:
                with open(desktop_file, 'r') as f:
                    content = f.read()
                
                # Extract Exec command
                exec_lines = [line for line in content.split('\n') if line.startswith('Exec=')]
                if not exec_lines:
                    self.log("❌ No Exec line found", "ERROR")
                    continue
                
                exec_command = exec_lines[0].replace('Exec=', '')
                self.log(f"Exec command: {exec_command}", "INFO")
                
                # Test the command (but don't actually run the GUI)
                if 'python3 installer.py' in exec_command:
                    # Extract the directory resolution part
                    if 'SCRIPT_DIR=' in exec_command:
                        test_cmd = 'SCRIPT_DIR="$(dirname "$(readlink -f "%k")")"; echo "Script dir would be: $SCRIPT_DIR"'
                        self.run_command(test_cmd, "Testing directory resolution")
                
            except Exception as e:
                self.log(f"❌ Error testing {desktop_file.name}: {e}", "ERROR")
    
    def check_desktop_integration(self):
        """Check desktop integration"""
        self.log("\n🔧 Desktop Integration Check", "INFO")
        self.log("-" * 32, "INFO")
        
        # Check for desktop file handlers
        commands_to_check = [
            ('gtk-launch', 'GTK desktop file launcher'),
            ('xdg-open', 'XDG desktop file opener'),
            ('gio', 'GNOME desktop integration'),
            ('zenity', 'Dialog boxes (used in desktop files)')
        ]
        
        for cmd, description in commands_to_check:
            if shutil.which(cmd):
                self.log(f"✅ {cmd}: Available ({description})", "SUCCESS")
            else:
                self.log(f"❌ {cmd}: Not found ({description})", "ERROR")
    
    def provide_solutions(self):
        """Provide solutions based on findings"""
        self.log("\n🛠️ Recommended Solutions", "INFO")
        self.log("-" * 25, "INFO")
        
        self.log("1. 📋 Make desktop files executable:", "INFO")
        self.log("   chmod +x *.desktop", "INFO")
        
        self.log("\n2. 🖥️ Test desktop file manually:", "INFO")
        self.log("   gtk-launch Xbox360-Emulator.desktop", "INFO")
        self.log("   # or", "INFO")
        self.log("   xdg-open Xbox360-Emulator.desktop", "INFO")
        
        self.log("\n3. 🔧 Install missing dependencies:", "INFO")
        self.log("   sudo apt update", "INFO")
        self.log("   sudo apt install python3-tk zenity", "INFO")
        
        self.log("\n4. 📂 Copy to desktop for testing:", "INFO")
        self.log("   cp *.desktop ~/Desktop/", "INFO")
        self.log("   # Then double-click from desktop", "INFO")
        
        self.log("\n5. 🐛 Manual testing:", "INFO")
        self.log("   cd ~/Desktop/Xbox360WifiEthernet", "INFO")
        self.log("   python3 installer.py", "INFO")
    
    def run_comprehensive_debug(self):
        """Run complete debug analysis"""
        try:
            self.log("🚀 Starting comprehensive desktop app debug...", "INFO")
            
            # System info
            self.debug_desktop_environment()
            
            # Desktop files
            self.debug_desktop_files()
            
            # Python environment
            self.debug_python_environment()
            
            # Desktop integration
            self.check_desktop_integration()
            
            # Test execution
            self.test_desktop_file_execution()
            
            # Solutions
            self.provide_solutions()
            
            self.log("\n" + "=" * 60, "INFO")
            self.log("✅ Desktop App Debug Analysis Complete!", "SUCCESS")
            self.log("=" * 60, "INFO")
            self.log(f"📂 Full debug log saved to: {self.log_file}", "INFO")
            self.log("💡 Check the solutions section above for next steps", "INFO")
            
        except Exception as e:
            self.log(f"❌ Debug analysis failed: {e}", "ERROR")
            import traceback
            self.log(traceback.format_exc(), "ERROR")
        finally:
            self.flush_log()

def main():
    """Main debug function"""
    print("🖥️ Xbox 360 WiFi Emulator - Desktop App Debugger")
    print("=" * 55)
    print("🔍 Debugging desktop app issues...")
    print("📝 All findings will be logged to ~/Desktop/debuglogs/")
    print()
    
    debugger = DesktopAppDebugger()
    debugger.run_comprehensive_debug()
    
    print(f"\n📂 Complete debug log available at:")
    print(f"   {debugger.log_file}")
    print("\n💡 You can now share this debug log for troubleshooting!")

if __name__ == "__main__":
    main()