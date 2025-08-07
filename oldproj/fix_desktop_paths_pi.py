#!/usr/bin/env python3
"""
Fix Desktop App Paths for Raspberry Pi
Creates proper desktop files with correct Pi paths and logs everything to debuglogs
"""

import os
import shutil
from pathlib import Path
from datetime import datetime

class DesktopPathFixer:
    def __init__(self):
        self.setup_logging()
        
    def setup_logging(self):
        """Setup centralized logging to debuglogs directory"""
        # Handle both Desktop and desktop (lowercase) variants for Pi
        possible_paths = [
            Path.home() / "Desktop" / "debuglogs",
            Path.home() / "desktop" / "debuglogs",
            Path("/home/pi/Desktop/debuglogs"),
            Path("/home/pi/desktop/debuglogs"),
            Path.home() / "debuglogs"
        ]
        
        self.debug_log_dir = None
        for path in possible_paths:
            if path.parent.exists():
                self.debug_log_dir = path
                break
        
        if not self.debug_log_dir:
            self.debug_log_dir = Path.home() / "Desktop" / "debuglogs"
        
        # Create directory
        self.debug_log_dir.mkdir(parents=True, exist_ok=True)
        
        # Create log file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_file = self.debug_log_dir / f"desktop_path_fix_{timestamp}.log"
        
        # Start logging
        self.log_buffer = []
        self.log("🖥️ Desktop Path Fix for Pi Started", "INFO")
        self.log("=" * 45, "INFO")
        self.log(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", "INFO")
        self.log(f"Working Directory: {Path.cwd()}", "INFO")
        self.log(f"User: {os.getenv('USER', 'unknown')}", "INFO")
        self.log(f"Home Directory: {Path.home()}", "INFO")
        self.log(f"Debug Log Directory: {self.debug_log_dir}", "INFO")
        self.log(f"Log File: {self.log_file}", "INFO")
        self.log("=" * 45, "INFO")
        
    def log(self, message, level="INFO"):
        """Log message with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] [{level}] {message}"
        self.log_buffer.append(log_entry + "\n")
        print(log_entry)
        
        if len(self.log_buffer) >= 3 or level in ['ERROR', 'SUCCESS']:
            self.flush_log()
    
    def flush_log(self):
        """Write log buffer to file"""
        try:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.writelines(self.log_buffer)
            self.log_buffer = []
        except Exception as e:
            print(f"Warning: Could not write to log file: {e}")
    
    def analyze_current_desktop_files(self):
        """Analyze existing desktop files and their path issues"""
        self.log("\n🔍 ANALYZING CURRENT DESKTOP FILES", "INFO")
        self.log("-" * 40, "INFO")
        
        current_dir = Path.cwd()
        desktop_files = list(current_dir.glob("*.desktop"))
        
        self.log(f"Current directory: {current_dir}", "INFO")
        self.log(f"Found {len(desktop_files)} desktop files", "INFO")
        
        issues_found = []
        
        for desktop_file in desktop_files:
            self.log(f"\n🔍 Analyzing: {desktop_file.name}", "INFO")
            
            try:
                with open(desktop_file, 'r') as f:
                    content = f.read()
                
                # Check for path issues
                if "/mnt/c/" in content:
                    self.log("❌ ISSUE: Contains Windows WSL path (/mnt/c/)", "ERROR")
                    issues_found.append(f"{desktop_file.name}: WSL path")
                    
                if 'SCRIPT_DIR="$(dirname "$(readlink -f "%k")")"' in content:
                    self.log("⚠️ ISSUE: Uses complex %k path resolution", "WARNING")  
                    issues_found.append(f"{desktop_file.name}: Complex path resolution")
                
                if "installer.py" in content:
                    # Check if installer.py exists in current directory
                    installer_path = current_dir / "installer.py"
                    if installer_path.exists():
                        self.log("✅ installer.py exists in current directory", "SUCCESS")
                    else:
                        self.log("❌ ISSUE: installer.py not found in current directory", "ERROR")
                        issues_found.append(f"installer.py missing")
                
                # Show first few lines for reference
                lines = content.split('\n')[:10]
                for i, line in enumerate(lines, 1):
                    if line.strip():
                        self.log(f"   {i:2d}: {line}", "DEBUG")
                        
            except Exception as e:
                self.log(f"❌ Error reading {desktop_file.name}: {e}", "ERROR")
                issues_found.append(f"{desktop_file.name}: Read error")
        
        self.log(f"\n📊 ANALYSIS SUMMARY:", "INFO")
        self.log(f"Issues found: {len(issues_found)}", "INFO")
        for issue in issues_found:
            self.log(f"   • {issue}", "ERROR")
        
        return issues_found
    
    def create_pi_desktop_files(self):
        """Create proper desktop files for Raspberry Pi"""
        self.log("\n🔧 CREATING PI DESKTOP FILES", "INFO")
        self.log("-" * 35, "INFO")
        
        # Use the actual path from log files
        pi_project_dir = "/home/chris/Desktop/Xbox360WifiEthernet"
        installer_path = Path(pi_project_dir) / "installer.py"
        
        # Also check current directory as fallback
        current_dir = Path.cwd()
        current_installer = current_dir / "installer.py"
        
        if Path(pi_project_dir).exists():
            project_dir = pi_project_dir
            self.log(f"✅ Using Pi project directory: {project_dir}", "SUCCESS")
        elif current_installer.exists():
            project_dir = str(current_dir)
            self.log(f"⚠️ Pi directory not found, using current: {project_dir}", "WARNING")
        else:
            self.log("❌ installer.py not found in Pi directory or current directory", "ERROR")
            self.log(f"Pi directory checked: {pi_project_dir}", "ERROR")
            self.log(f"Current directory: {current_dir}", "ERROR")
            return False
        
        self.log(f"✅ Project directory: {project_dir}", "SUCCESS")
        
        # Create GUI desktop file
        gui_desktop_content = f"""[Desktop Entry]
Version=1.0
Type=Application
Name=Xbox 360 WiFi Emulator
Comment=Install and manage Xbox 360 WiFi Module Emulator (GUI)
Exec=bash -c 'cd "{project_dir}" && python3 installer.py'
Icon=network-wireless
Terminal=false
Categories=System;Network;
StartupNotify=true
Path={project_dir}

[Desktop Action Terminal]
Name=Open in Terminal
Exec=bash -c 'cd "{project_dir}" && x-terminal-emulator -e bash -c "echo \\"Xbox 360 WiFi Emulator Directory\\"; echo \\"Current directory: $(pwd)\\"; echo \\"Files available:\\"; ls -la *.py; echo; echo \\"To run installer: python3 installer.py\\"; echo \\"Press Enter to continue...\\"; read"'

Actions=Terminal;
"""
        
        # Create terminal desktop file
        terminal_desktop_content = f"""[Desktop Entry]
Version=1.0
Type=Application
Name=Xbox 360 WiFi Emulator (Terminal)
Comment=Install and manage Xbox 360 WiFi Module Emulator (Terminal Mode)
Exec=bash -c 'cd "{project_dir}" && python3 installer.py; echo; echo "Press Enter to close..."; read'
Icon=network-wireless
Terminal=true
Categories=System;Network;
StartupNotify=true
Path={project_dir}
"""
        
        # Create comprehensive launcher desktop file  
        comprehensive_desktop_content = f"""[Desktop Entry]
Version=1.0
Type=Application
Name=Xbox 360 WiFi Emulator (Fixed)
Comment=Xbox 360 WiFi Module Emulator with comprehensive Pi fixes
Exec=bash -c 'cd "{project_dir}" && if [ -f launch_comprehensive.sh ]; then ./launch_comprehensive.sh; else python3 installer.py; fi'
Icon=network-wireless
Terminal=true
Categories=System;Network;
StartupNotify=true
Path={project_dir}
"""
        
        desktop_files_to_create = [
            ("Xbox360-Emulator-Pi.desktop", gui_desktop_content),
            ("Xbox360-Emulator-Pi-Terminal.desktop", terminal_desktop_content),
            ("Xbox360-Emulator-Pi-Fixed.desktop", comprehensive_desktop_content)
        ]
        
        created_files = []
        
        for filename, content in desktop_files_to_create:
            try:
                desktop_file = Path(filename)
                
                # Write content
                with open(desktop_file, 'w') as f:
                    f.write(content)
                
                # Make executable
                os.chmod(desktop_file, 0o755)
                
                self.log(f"✅ Created: {filename}", "SUCCESS")
                created_files.append(desktop_file)
                
            except Exception as e:
                self.log(f"❌ Failed to create {filename}: {e}", "ERROR")
        
        return created_files
    
    def copy_to_desktop(self, desktop_files):
        """Copy desktop files to user's desktop"""
        self.log("\n📂 COPYING TO DESKTOP", "INFO")
        self.log("-" * 25, "INFO")
        
        # Find user's desktop directory
        possible_desktop_dirs = [
            Path.home() / "Desktop",
            Path.home() / "desktop",
            Path("/home/pi/Desktop"),
            Path("/home/pi/desktop")
        ]
        
        desktop_dir = None
        for path in possible_desktop_dirs:
            if path.exists():
                desktop_dir = path
                self.log(f"✅ Found desktop directory: {path}", "SUCCESS")
                break
        
        if not desktop_dir:
            # Create Desktop directory
            desktop_dir = Path.home() / "Desktop"
            desktop_dir.mkdir(exist_ok=True)
            self.log(f"✅ Created desktop directory: {desktop_dir}", "SUCCESS")
        
        copied_files = []
        for desktop_file in desktop_files:
            try:
                dest_file = desktop_dir / desktop_file.name
                shutil.copy2(desktop_file, dest_file)
                
                # Make executable
                os.chmod(dest_file, 0o755)
                
                self.log(f"✅ Copied to desktop: {dest_file.name}", "SUCCESS")
                copied_files.append(dest_file)
                
            except Exception as e:
                self.log(f"❌ Failed to copy {desktop_file.name}: {e}", "ERROR")
        
        return copied_files, desktop_dir
    
    def test_desktop_files(self, desktop_files):
        """Test the created desktop files"""
        self.log("\n🧪 TESTING DESKTOP FILES", "INFO")  
        self.log("-" * 27, "INFO")
        
        for desktop_file in desktop_files:
            self.log(f"\n🎯 Testing: {desktop_file.name}", "INFO")
            
            # Check file permissions
            if os.access(desktop_file, os.X_OK):
                self.log("✅ File is executable", "SUCCESS")
            else:
                self.log("❌ File is not executable", "ERROR")
            
            # Check if it's a valid desktop file
            try:
                with open(desktop_file, 'r') as f:
                    content = f.read()
                
                if "[Desktop Entry]" in content:
                    self.log("✅ Valid desktop file format", "SUCCESS")
                else:
                    self.log("❌ Invalid desktop file format", "ERROR")
                
                if f"Path={Path.cwd()}" in content:
                    self.log("✅ Contains correct working directory path", "SUCCESS")
                else:
                    self.log("⚠️ Path directive may be missing or incorrect", "WARNING")
                
                if "/mnt/c/" in content:
                    self.log("❌ Still contains Windows WSL paths", "ERROR")
                else:
                    self.log("✅ No Windows WSL paths found", "SUCCESS")
                    
            except Exception as e:
                self.log(f"❌ Error testing {desktop_file.name}: {e}", "ERROR")
    
    def provide_usage_instructions(self, copied_files, desktop_dir):
        """Provide usage instructions"""
        self.log("\n📋 USAGE INSTRUCTIONS", "INFO")
        self.log("-" * 25, "INFO")
        
        self.log("🎯 TO USE THE FIXED DESKTOP FILES:", "SUCCESS")
        self.log("", "INFO")
        
        if copied_files:
            self.log(f"✅ Desktop files copied to: {desktop_dir}", "SUCCESS")
            self.log("Double-click any of these files:", "INFO")
            for f in copied_files:
                self.log(f"   • {f.name}", "INFO")
        
        self.log("", "INFO")
        self.log("🔧 MANUAL LAUNCH OPTIONS:", "INFO")
        self.log(f"   cd {Path.cwd()}", "INFO")
        self.log("   python3 installer.py", "INFO")
        
        self.log("", "INFO")
        self.log("📂 ALL LOGGING GOES TO:", "INFO")
        self.log(f"   {self.debug_log_dir}/", "INFO")
        
        self.log("", "INFO")
        self.log("💡 IF DESKTOP FILES DON'T WORK:", "INFO")
        self.log("   1. Right-click → Properties → Permissions → Allow executing", "INFO")
        self.log("   2. Or run: chmod +x ~/Desktop/Xbox360-Emulator-Pi*.desktop", "INFO")
        self.log("   3. Check log files in debuglogs/ for errors", "INFO")
    
    def run_desktop_path_fix(self):
        """Run complete desktop path fix"""
        try:
            self.log("🚀 Starting desktop path fix for Raspberry Pi...", "INFO")
            
            # Step 1: Analyze current desktop files
            issues = self.analyze_current_desktop_files()
            
            if not issues:
                self.log("\n🎉 No desktop file issues detected!", "SUCCESS")
                # Still create Pi-specific files for consistency
            
            # Step 2: Create proper Pi desktop files
            desktop_files = self.create_pi_desktop_files()
            
            if not desktop_files:
                self.log("❌ Failed to create desktop files", "ERROR")
                return False
            
            # Step 3: Test the created files
            self.test_desktop_files(desktop_files)
            
            # Step 4: Copy to desktop
            copied_files, desktop_dir = self.copy_to_desktop(desktop_files)
            
            # Step 5: Provide usage instructions
            self.provide_usage_instructions(copied_files, desktop_dir)
            
            self.log("\n" + "=" * 45, "INFO")
            self.log("✅ DESKTOP PATH FIX COMPLETE!", "SUCCESS")
            self.log("=" * 45, "INFO")
            self.log(f"📂 Complete fix log: {self.log_file}", "INFO")
            self.log(f"🖥️ Desktop files created: {len(desktop_files)}", "SUCCESS")
            self.log(f"📋 Files copied to desktop: {len(copied_files)}", "SUCCESS")
            
            return True
            
        except Exception as e:
            self.log(f"❌ Desktop path fix failed: {e}", "ERROR")
            import traceback
            self.log(traceback.format_exc(), "ERROR")
            return False
        finally:
            self.flush_log()

def main():
    """Main desktop path fix function"""
    print("🖥️ Xbox 360 WiFi Emulator - Desktop Path Fix for Pi")
    print("=" * 55)
    print("🎯 Fixing desktop app path issues for Raspberry Pi")
    print("📝 All actions logged to debuglogs directory")
    print()
    
    fixer = DesktopPathFixer()
    success = fixer.run_desktop_path_fix()
    
    print(f"\n📂 Complete desktop path fix log:")
    print(f"   {fixer.log_file}")
    
    if success:
        print("\n🎉 Desktop path fix complete!")
        print("💡 New Pi-specific desktop files created and copied to desktop")
        print("🖱️ Double-click any desktop file to launch the installer")
    else:
        print("\n❌ Desktop path fix encountered issues")
        print("💡 Check the log file for detailed information")

if __name__ == "__main__":
    main()