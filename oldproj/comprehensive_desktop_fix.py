#!/usr/bin/env python3
"""
Comprehensive Desktop App Fix
Addresses all identified issues with desktop launchers
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path
from datetime import datetime

class DesktopFixer:
    def __init__(self):
        self.setup_logging()
        
    def setup_logging(self):
        """Setup centralized logging"""
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
        
        self.debug_log_dir = desktop_dir / "debuglogs"
        self.debug_log_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_file = self.debug_log_dir / f"desktop_fix_{timestamp}.log"
        self.log_buffer = []
        
        self.log("🔧 Comprehensive Desktop Fix Started", "INFO")
        self.log("=" * 50, "INFO")
        self.log(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", "INFO")
        self.log(f"Working Directory: {Path.cwd()}", "INFO")
        self.log(f"Log File: {self.log_file}", "INFO")
        self.log("=" * 50, "INFO")
    
    def log(self, message, level="INFO"):
        """Log message with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] [{level}] {message}"
        self.log_buffer.append(log_entry + "\n")
        print(log_entry)
        
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
    
    def run_command(self, cmd, description="", ignore_errors=False):
        """Run command and log results"""
        if description:
            self.log(f"🔧 {description}", "INFO")
        
        try:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            
            if result.returncode == 0:
                self.log(f"✅ Command succeeded", "SUCCESS")
                if result.stdout:
                    for line in result.stdout.strip().split('\n'):
                        if line.strip():
                            self.log(f"   {line}", "OUTPUT")
                return True
            else:
                if ignore_errors:
                    self.log(f"⚠️  Command failed but continuing (exit code: {result.returncode})", "WARNING")
                else:
                    self.log(f"❌ Command failed (exit code: {result.returncode})", "ERROR")
                
                if result.stderr:
                    for line in result.stderr.strip().split('\n'):
                        if line.strip():
                            self.log(f"   {line}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Command exception: {e}", "ERROR")
            return False
    
    def fix_path_spaces_issue(self):
        """Fix issues with spaces in directory path"""
        self.log("\n🛠️ Fixing Path Spaces Issues", "INFO")
        self.log("-" * 35, "INFO")
        
        current_path = Path.cwd()
        self.log(f"Current path: {current_path}", "INFO")
        
        if ' ' in str(current_path):
            self.log("⚠️  Path contains spaces - this can cause issues", "WARNING")
            self.log("💡 Solutions:", "INFO")
            self.log("   1. Move project to path without spaces", "INFO")
            self.log("   2. Use quoted paths in desktop files", "INFO")
            self.log("   3. Create symlink without spaces", "INFO")
            
            # Try to create a symlink without spaces
            try:
                home_dir = Path.home()
                symlink_path = home_dir / "Xbox360WifiEthernet"
                
                if not symlink_path.exists():
                    symlink_path.symlink_to(current_path)
                    self.log(f"✅ Created symlink: {symlink_path} -> {current_path}", "SUCCESS")
                    return str(symlink_path)
                else:
                    self.log(f"✅ Symlink already exists: {symlink_path}", "SUCCESS")
                    return str(symlink_path)
                    
            except Exception as e:
                self.log(f"❌ Could not create symlink: {e}", "ERROR")
        else:
            self.log("✅ Path has no spaces - good!", "SUCCESS")
        
        return str(current_path)
    
    def install_missing_dependencies(self):
        """Install missing system dependencies"""
        self.log("\n🔧 Installing Missing Dependencies", "INFO")
        self.log("-" * 38, "INFO")
        
        # Check what's missing
        missing_packages = []
        
        if not shutil.which('zenity'):
            missing_packages.append('zenity')
            self.log("❌ zenity not found", "ERROR")
        else:
            self.log("✅ zenity available", "SUCCESS")
        
        # Check python3-tk
        try:
            import tkinter
            self.log("✅ python3-tk available", "SUCCESS")
        except ImportError:
            missing_packages.append('python3-tk')
            self.log("❌ python3-tk not found", "ERROR")
        
        if missing_packages:
            self.log(f"\n📦 Installing missing packages: {', '.join(missing_packages)}", "INFO")
            
            # Try to install (might need sudo)
            install_cmd = f"apt update && apt install -y {' '.join(missing_packages)}"
            
            self.log("💡 Note: Package installation may require sudo privileges", "WARNING")
            
            # For WSL/testing, we'll just note what needs to be installed
            self.log(f"📋 To install manually, run:", "INFO")
            self.log(f"   sudo {install_cmd}", "INFO")
            
            return False
        else:
            self.log("✅ All dependencies available", "SUCCESS")
            return True
    
    def create_improved_desktop_files(self, safe_path=None):
        """Create improved desktop files with better error handling"""
        self.log("\n📄 Creating Improved Desktop Files", "INFO")
        self.log("-" * 40, "INFO")
        
        if safe_path is None:
            safe_path = Path.cwd()
        
        # Improved desktop file content
        desktop_content_gui = f"""[Desktop Entry]
Version=1.0
Type=Application
Name=Xbox 360 WiFi Emulator
Comment=Install and manage Xbox 360 WiFi Module Emulator (GUI)
Exec=bash -c 'cd "{safe_path}" && python3 installer.py || (echo "Failed to start installer"; echo "Trying alternative path..."; cd "$(dirname "$(readlink -f "%k")")" && python3 installer.py || (echo "Error: installer.py not found"; echo "Current directory: $(pwd)"; echo "Files: $(ls -la *.py 2>/dev/null || echo None)"; read -p "Press Enter to close..."))'
Icon=network-wireless
Terminal=false
Categories=System;Network;
StartupNotify=true
Path={safe_path}

[Desktop Action Terminal]
Name=Open in Terminal
Exec=bash -c 'cd "{safe_path}" && x-terminal-emulator -e bash || x-terminal-emulator -e bash -c "cd \\"{safe_path}\\" && bash"'

Actions=Terminal;
"""

        desktop_content_terminal = f"""[Desktop Entry]
Version=1.0
Type=Application
Name=Xbox 360 WiFi Emulator (Terminal)
Comment=Install and manage Xbox 360 WiFi Module Emulator (Terminal Mode)
Exec=bash -c 'cd "{safe_path}" && python3 installer.py; read -p "Press Enter to close..."'
Icon=network-wireless
Terminal=true
Categories=System;Network;
StartupNotify=true
Path={safe_path}
"""

        # Write improved desktop files
        desktop_files = [
            ("Xbox360-Emulator-Fixed.desktop", desktop_content_gui),
            ("Xbox360-Emulator-Terminal-Fixed.desktop", desktop_content_terminal)
        ]
        
        created_files = []
        
        for filename, content in desktop_files:
            try:
                desktop_file = Path(filename)
                with open(desktop_file, 'w') as f:
                    f.write(content)
                
                # Make executable
                os.chmod(desktop_file, 0o755)
                
                self.log(f"✅ Created: {filename}", "SUCCESS")
                created_files.append(desktop_file)
                
            except Exception as e:
                self.log(f"❌ Failed to create {filename}: {e}", "ERROR")
        
        return created_files
    
    def test_desktop_files(self, desktop_files):
        """Test the created desktop files"""
        self.log("\n🧪 Testing Desktop Files", "INFO")
        self.log("-" * 27, "INFO")
        
        for desktop_file in desktop_files:
            self.log(f"\n🎯 Testing: {desktop_file.name}", "INFO")
            
            # Test with gtk-launch
            if shutil.which('gtk-launch'):
                cmd = f"timeout 3 gtk-launch {desktop_file.name}"
                self.log(f"Testing with gtk-launch...", "INFO")
                result = self.run_command(cmd, ignore_errors=True)
                
                if result:
                    self.log("✅ gtk-launch test passed", "SUCCESS")
                else:
                    self.log("⚠️  gtk-launch test had issues", "WARNING")
            
            # Check file permissions
            if os.access(desktop_file, os.X_OK):
                self.log("✅ File is executable", "SUCCESS")
            else:
                self.log("❌ File is not executable", "ERROR")
    
    def provide_usage_instructions(self, desktop_files, safe_path):
        """Provide clear usage instructions"""
        self.log("\n📋 Usage Instructions", "INFO")
        self.log("-" * 22, "INFO")
        
        self.log("🎯 To use the fixed desktop launchers:", "INFO")
        self.log("", "INFO")
        
        self.log("1. 📂 Copy to desktop:", "INFO")
        for df in desktop_files:
            self.log(f"   cp {df.name} ~/Desktop/", "INFO")
        
        self.log("\n2. 🖱️  Double-click the desktop file to launch", "INFO")
        
        self.log("\n3. 🖥️  Alternative manual testing:", "INFO")
        for df in desktop_files:
            if shutil.which('gtk-launch'):
                self.log(f"   gtk-launch {df.name}", "INFO")
            else:
                self.log(f"   xdg-open {df.name}", "INFO")
        
        self.log("\n4. 🔧 Direct command line:", "INFO")
        self.log(f"   cd '{safe_path}'", "INFO")
        self.log("   python3 installer.py", "INFO")
        
        self.log("\n5. 📂 If installer.py is not found:", "INFO")
        self.log("   - Make sure you're in the correct directory", "INFO")
        self.log("   - Check that installer.py exists: ls -la installer.py", "INFO")
        self.log("   - Try the symlink path if created", "INFO")
    
    def run_comprehensive_fix(self):
        """Run complete desktop fix"""
        try:
            self.log("🚀 Starting comprehensive desktop fix...", "INFO")
            
            # Fix path issues
            safe_path = self.fix_path_spaces_issue()
            
            # Install dependencies
            self.install_missing_dependencies()
            
            # Create improved desktop files
            desktop_files = self.create_improved_desktop_files(safe_path)
            
            # Test desktop files
            if desktop_files:
                self.test_desktop_files(desktop_files)
                
                # Provide usage instructions
                self.provide_usage_instructions(desktop_files, safe_path)
            
            self.log("\n" + "=" * 50, "INFO")
            self.log("✅ Comprehensive Desktop Fix Complete!", "SUCCESS")
            self.log("=" * 50, "INFO")
            self.log(f"📂 Fix log saved to: {self.log_file}", "INFO")
            
            if desktop_files:
                self.log("🎉 New desktop files created:", "SUCCESS")
                for df in desktop_files:
                    self.log(f"   - {df.name}", "SUCCESS")
                self.log("\n💡 Copy these files to ~/Desktop/ and double-click to test!", "INFO")
            
        except Exception as e:
            self.log(f"❌ Comprehensive fix failed: {e}", "ERROR")
            import traceback
            self.log(traceback.format_exc(), "ERROR")
        finally:
            self.flush_log()

def main():
    """Main fix function"""
    print("🔧 Xbox 360 WiFi Emulator - Comprehensive Desktop Fix")
    print("=" * 55)
    print("🎯 Fixing all identified desktop app issues...")
    print("📝 All actions logged to ~/Desktop/debuglogs/")
    print()
    
    fixer = DesktopFixer()
    fixer.run_comprehensive_fix()
    
    print(f"\n📂 Complete fix log available at:")
    print(f"   {fixer.log_file}")
    print("\n🎉 Desktop fix complete! Try the new desktop files.")

if __name__ == "__main__":
    main()