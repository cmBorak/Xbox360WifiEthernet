#!/usr/bin/env python3
"""
Fix Desktop Paths for Pi OS Bullseye ARM64
Creates proper desktop files optimized for Bullseye environment
"""

import os
import shutil
from pathlib import Path
from datetime import datetime

class BullseyeDesktopFixer:
    """Desktop path fixer optimized for Pi OS Bullseye ARM64"""
    
    def __init__(self):
        self.setup_logging()
        
    def setup_logging(self):
        """Setup logging for Bullseye desktop fix"""
        # Bullseye typically uses lowercase desktop
        possible_paths = [
            Path.home() / "desktop" / "debuglogs",
            Path.home() / "Desktop" / "debuglogs",
            Path("/home/pi/desktop/debuglogs"),
            Path("/home/pi/Desktop/debuglogs"),
            Path.home() / "debuglogs"
        ]
        
        self.debug_log_dir = None
        for path in possible_paths:
            if path.parent.exists():
                self.debug_log_dir = path
                break
        
        if not self.debug_log_dir:
            self.debug_log_dir = Path.home() / "desktop" / "debuglogs"
        
        # Create directory
        self.debug_log_dir.mkdir(parents=True, exist_ok=True)
        
        # Create log file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_file = self.debug_log_dir / f"bullseye_desktop_fix_{timestamp}.log"
        
        # Start logging
        self.log_buffer = []
        self.log("🖥️ Desktop Path Fix for Pi OS Bullseye ARM64", "INFO")
        self.log("=" * 50, "INFO")
        self.log(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", "INFO")
        self.log(f"Working Directory: {Path.cwd()}", "INFO")
        self.log(f"User: {os.getenv('USER', 'unknown')}", "INFO")
        self.log(f"Home Directory: {Path.home()}", "INFO")
        self.log(f"Debug Log Directory: {self.debug_log_dir}", "INFO")
        self.log(f"Log File: {self.log_file}", "INFO")
        self.log("=" * 50, "INFO")
        
    def log(self, message, level="INFO"):
        """Log message with timestamp and colors"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] [{level}] {message}"
        self.log_buffer.append(log_entry + "\n")
        
        # Console colors
        colors = {
            "INFO": "\033[0;36m",
            "SUCCESS": "\033[0;32m", 
            "WARNING": "\033[1;33m",
            "ERROR": "\033[0;31m",
            "DEBUG": "\033[0;37m"
        }
        
        color = colors.get(level, "\033[0m")
        print(f"{color}[{timestamp}] {message}\033[0m")
        
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
    
    def detect_bullseye_paths(self):
        """Detect Bullseye-specific paths"""
        self.log("\n🔍 DETECTING BULLSEYE PATHS", "INFO")
        self.log("-" * 30, "INFO")
        
        # Detect project directory for Bullseye
        possible_project_dirs = [
            "/home/chris/desktop/Xbox360WifiEthernet",
            "/home/chris/Desktop/Xbox360WifiEthernet", 
            "/home/pi/desktop/Xbox360WifiEthernet",
            "/home/pi/Desktop/Xbox360WifiEthernet",
            str(Path.cwd())
        ]
        
        project_dir = None
        for path in possible_project_dirs:
            if Path(path).exists() and (Path(path) / "installer.py").exists():
                project_dir = path
                self.log(f"✅ Found project directory: {project_dir}", "SUCCESS")
                break
        
        if not project_dir:
            project_dir = str(Path.cwd())
            self.log(f"⚠️ Using current directory: {project_dir}", "WARNING")
        
        # Detect desktop directory for Bullseye
        possible_desktop_dirs = [
            Path.home() / "desktop",
            Path.home() / "Desktop",
            Path("/home/pi/desktop"),
            Path("/home/pi/Desktop")
        ]
        
        desktop_dir = None
        for path in possible_desktop_dirs:
            if path.exists():
                desktop_dir = path
                self.log(f"✅ Found desktop directory: {desktop_dir}", "SUCCESS")
                break
        
        if not desktop_dir:
            desktop_dir = Path.home() / "desktop"
            desktop_dir.mkdir(exist_ok=True)
            self.log(f"✅ Created desktop directory: {desktop_dir}", "SUCCESS")
        
        return project_dir, desktop_dir
    
    def analyze_current_desktop_files(self):
        """Analyze existing desktop files for Bullseye compatibility"""
        self.log("\n🔍 ANALYZING DESKTOP FILES FOR BULLSEYE", "INFO")
        self.log("-" * 40, "INFO")
        
        current_dir = Path.cwd()
        desktop_files = list(current_dir.glob("*.desktop"))
        
        self.log(f"Current directory: {current_dir}", "INFO")
        self.log(f"Found {len(desktop_files)} desktop files", "INFO")
        
        bullseye_issues = []
        
        for desktop_file in desktop_files:
            self.log(f"\n🔍 Analyzing: {desktop_file.name}", "INFO")
            
            try:
                with open(desktop_file, 'r') as f:
                    content = f.read()
                
                # Check for Bullseye-specific issues
                if "/boot/firmware/" in content:
                    self.log("❌ ISSUE: Contains Bookworm paths (/boot/firmware/)", "ERROR")
                    bullseye_issues.append(f"{desktop_file.name}: Bookworm paths")
                
                if "/mnt/c/" in content:
                    self.log("❌ ISSUE: Contains Windows WSL paths", "ERROR")
                    bullseye_issues.append(f"{desktop_file.name}: WSL paths")
                
                if not any(bullseye_path in content for bullseye_path in ["/home/chris/desktop", "/home/pi/desktop"]):
                    self.log("⚠️ ISSUE: May not use Bullseye-optimized paths", "WARNING")
                    bullseye_issues.append(f"{desktop_file.name}: Non-Bullseye paths")
                
            except Exception as e:
                self.log(f"❌ Error reading {desktop_file.name}: {e}", "ERROR")
                bullseye_issues.append(f"{desktop_file.name}: Read error")
        
        self.log(f"\n📊 BULLSEYE ANALYSIS SUMMARY:", "INFO")
        self.log(f"Issues found: {len(bullseye_issues)}", "INFO") 
        for issue in bullseye_issues:
            self.log(f"   • {issue}", "ERROR")
        
        return bullseye_issues
    
    def create_bullseye_desktop_files(self, project_dir):
        """Create desktop files optimized for Bullseye"""
        self.log("\n🔧 CREATING BULLSEYE DESKTOP FILES", "INFO")
        self.log("-" * 35, "INFO")
        
        installer_path = Path(project_dir) / "installer.py"
        
        if not installer_path.exists():
            self.log(f"❌ installer.py not found at: {installer_path}", "ERROR")
            return []
        
        self.log(f"✅ installer.py found at: {installer_path}", "SUCCESS")
        
        # GUI desktop file for Bullseye
        gui_desktop_content = f"""[Desktop Entry]
Version=1.0
Type=Application
Name=Xbox 360 WiFi Emulator (Bullseye)
Comment=Xbox 360 WiFi Module Emulator optimized for Pi OS Bullseye ARM64
Exec=bash -c 'cd "{project_dir}" && python3 installer.py'
Icon=network-wireless
Terminal=false
Categories=System;Network;Game;
StartupNotify=true
Path={project_dir}

[Desktop Action Terminal]
Name=Open in Terminal
Exec=bash -c 'cd "{project_dir}" && x-terminal-emulator -e bash -c "echo \\"Xbox 360 WiFi Emulator - Bullseye ARM64\\"; echo \\"Directory: $(pwd)\\"; echo \\"Files available:\\"; ls -la *.py; echo; echo \\"To run: python3 installer.py\\"; echo \\"Press Enter to continue...\\"; read"'

[Desktop Action Status]
Name=Check Status
Exec=bash -c 'cd "{project_dir}" && python3 installer.py --status'

Actions=Terminal;Status;
"""
        
        # Terminal desktop file for Bullseye
        terminal_desktop_content = f"""[Desktop Entry]
Version=1.0
Type=Application
Name=Xbox 360 WiFi Emulator (Bullseye Terminal)
Comment=Xbox 360 WiFi Module Emulator for Bullseye ARM64 (Terminal Mode)
Exec=bash -c 'cd "{project_dir}" && python3 installer.py; echo; echo "Press Enter to close..."; read'
Icon=network-wireless
Terminal=true
Categories=System;Network;Game;
StartupNotify=true
Path={project_dir}
"""
        
        # Comprehensive launcher for Bullseye  
        comprehensive_desktop_content = f"""[Desktop Entry]
Version=1.0
Type=Application
Name=Xbox 360 WiFi Emulator (Bullseye Comprehensive)
Comment=Xbox 360 WiFi Module Emulator with comprehensive Bullseye fixes
Exec=bash -c 'cd "{project_dir}" && if [ -f launch_bullseye_comprehensive.sh ]; then ./launch_bullseye_comprehensive.sh; else python3 installer.py; fi'
Icon=network-wireless
Terminal=true
Categories=System;Network;Game;
StartupNotify=true
Path={project_dir}
"""

        # Fix script launcher for Bullseye
        fix_desktop_content = f"""[Desktop Entry]
Version=1.0
Type=Application  
Name=Xbox 360 WiFi Emulator (Bullseye Fix)
Comment=Run comprehensive Bullseye fixes for Xbox 360 WiFi Module Emulator
Exec=bash -c 'cd "{project_dir}" && python3 comprehensive_bullseye_fix.py; echo; echo "Press Enter to close..."; read'
Icon=applications-system
Terminal=true
Categories=System;Settings;
StartupNotify=true
Path={project_dir}
"""
        
        desktop_files_to_create = [
            ("Xbox360-Emulator-Bullseye.desktop", gui_desktop_content),
            ("Xbox360-Emulator-Bullseye-Terminal.desktop", terminal_desktop_content),
            ("Xbox360-Emulator-Bullseye-Comprehensive.desktop", comprehensive_desktop_content),
            ("Xbox360-Emulator-Bullseye-Fix.desktop", fix_desktop_content)
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
                
                self.log(f"✅ Created Bullseye desktop file: {filename}", "SUCCESS")
                created_files.append(desktop_file)
                
            except Exception as e:
                self.log(f"❌ Failed to create {filename}: {e}", "ERROR")
        
        return created_files
    
    def copy_to_bullseye_desktop(self, desktop_files, desktop_dir):
        """Copy desktop files to Bullseye desktop directory"""
        self.log(f"\n📂 COPYING TO BULLSEYE DESKTOP: {desktop_dir}", "INFO")
        self.log("-" * 40, "INFO")
        
        copied_files = []
        for desktop_file in desktop_files:
            try:
                dest_file = desktop_dir / desktop_file.name
                shutil.copy2(desktop_file, dest_file)
                
                # Make executable
                os.chmod(dest_file, 0o755)
                
                self.log(f"✅ Copied to Bullseye desktop: {dest_file.name}", "SUCCESS")
                copied_files.append(dest_file)
                
            except Exception as e:
                self.log(f"❌ Failed to copy {desktop_file.name}: {e}", "ERROR")
        
        return copied_files
    
    def test_bullseye_desktop_files(self, desktop_files):
        """Test Bullseye desktop files"""
        self.log("\n🧪 TESTING BULLSEYE DESKTOP FILES", "INFO")
        self.log("-" * 35, "INFO")
        
        for desktop_file in desktop_files:
            self.log(f"\n🎯 Testing: {desktop_file.name}", "INFO")
            
            # Check file permissions
            if os.access(desktop_file, os.X_OK):
                self.log("✅ File is executable", "SUCCESS")
            else:
                self.log("❌ File is not executable", "ERROR")
            
            # Check content for Bullseye optimization
            try:
                with open(desktop_file, 'r') as f:
                    content = f.read()
                
                if "[Desktop Entry]" in content:
                    self.log("✅ Valid desktop file format", "SUCCESS")
                else:
                    self.log("❌ Invalid desktop file format", "ERROR")
                
                if "Bullseye" in content:
                    self.log("✅ Contains Bullseye branding", "SUCCESS")
                else:
                    self.log("⚠️ Missing Bullseye branding", "WARNING")
                
                if "/boot/firmware/" in content:
                    self.log("❌ Still contains Bookworm paths", "ERROR")
                else:
                    self.log("✅ No Bookworm paths found", "SUCCESS")
                
                if "/mnt/c/" in content:
                    self.log("❌ Still contains Windows WSL paths", "ERROR")
                else:
                    self.log("✅ No Windows WSL paths found", "SUCCESS")
                    
            except Exception as e:
                self.log(f"❌ Error testing {desktop_file.name}: {e}", "ERROR")
    
    def provide_bullseye_usage_instructions(self, copied_files, desktop_dir, project_dir):
        """Provide usage instructions for Bullseye"""
        self.log("\n📋 BULLSEYE USAGE INSTRUCTIONS", "INFO")
        self.log("-" * 35, "INFO")
        
        self.log("🎯 TO USE THE BULLSEYE DESKTOP FILES:", "SUCCESS")
        self.log("", "INFO")
        
        if copied_files:
            self.log(f"✅ Bullseye desktop files copied to: {desktop_dir}", "SUCCESS")
            self.log("Double-click any of these optimized files:", "INFO")
            for f in copied_files:
                if "Fix" in f.name:
                    self.log(f"   🔧 {f.name} - Run Bullseye fixes", "INFO")
                elif "Comprehensive" in f.name:
                    self.log(f"   🚀 {f.name} - Full launcher", "INFO")
                elif "Terminal" in f.name:
                    self.log(f"   💻 {f.name} - Terminal mode", "INFO")
                else:
                    self.log(f"   🎮 {f.name} - GUI mode", "INFO")
        
        self.log("", "INFO")
        self.log("🔧 BULLSEYE MANUAL LAUNCH OPTIONS:", "INFO")
        self.log(f"   cd {project_dir}", "INFO")
        self.log("   python3 installer.py                    # Main installer", "INFO")
        self.log("   python3 comprehensive_bullseye_fix.py   # Run fixes", "INFO")
        self.log("   ./launch_bullseye_comprehensive.sh      # Full launcher", "INFO")
        
        self.log("", "INFO")
        self.log("📂 ALL BULLSEYE LOGGING GOES TO:", "INFO")
        self.log(f"   {self.debug_log_dir}/", "INFO")
        
        self.log("", "INFO")
        self.log("💡 IF BULLSEYE DESKTOP FILES DON'T WORK:", "INFO")
        self.log("   1. Right-click → Properties → Permissions → Allow executing", "INFO")
        self.log("   2. Or run: chmod +x ~/desktop/Xbox360-Emulator-Bullseye*.desktop", "INFO")
        self.log("   3. Check Bullseye logs in debuglogs/ for errors", "INFO")
        self.log("   4. Verify Bullseye: grep bullseye /etc/os-release", "INFO")
    
    def run_bullseye_desktop_fix(self):
        """Run complete Bullseye desktop fix"""
        try:
            self.log("🚀 Starting Bullseye desktop fix...", "INFO")
            
            # Step 1: Detect Bullseye paths
            project_dir, desktop_dir = self.detect_bullseye_paths()
            
            # Step 2: Analyze current desktop files
            issues = self.analyze_current_desktop_files()
            
            if not issues:
                self.log("\n🎉 No desktop file issues detected for Bullseye!", "SUCCESS")
            
            # Step 3: Create Bullseye desktop files
            desktop_files = self.create_bullseye_desktop_files(project_dir)
            
            if not desktop_files:
                self.log("❌ Failed to create Bullseye desktop files", "ERROR")
                return False
            
            # Step 4: Test the created files
            self.test_bullseye_desktop_files(desktop_files)
            
            # Step 5: Copy to desktop
            copied_files = self.copy_to_bullseye_desktop(desktop_files, desktop_dir)
            
            # Step 6: Provide usage instructions
            self.provide_bullseye_usage_instructions(copied_files, desktop_dir, project_dir)
            
            self.log("\n" + "=" * 50, "INFO")
            self.log("✅ BULLSEYE DESKTOP FIX COMPLETE!", "SUCCESS")
            self.log("=" * 50, "INFO")
            self.log(f"📂 Complete fix log: {self.log_file}", "INFO")
            self.log(f"🖥️ Bullseye desktop files created: {len(desktop_files)}", "SUCCESS")
            self.log(f"📋 Files copied to desktop: {len(copied_files)}", "SUCCESS")
            
            return True
            
        except Exception as e:
            self.log(f"❌ Bullseye desktop fix failed: {e}", "ERROR")
            import traceback
            self.log(traceback.format_exc(), "ERROR")
            return False
        finally:
            self.flush_log()

def main():
    """Main Bullseye desktop fix function"""
    print("🖥️ Xbox 360 WiFi Emulator - Desktop Fix for Pi OS Bullseye ARM64")
    print("=" * 65)
    print("🎯 Creating desktop integration optimized for Bullseye")
    print("📝 All actions logged to debuglogs directory")
    print()
    
    fixer = BullseyeDesktopFixer()
    success = fixer.run_bullseye_desktop_fix()
    
    print(f"\n📂 Complete Bullseye desktop fix log:")
    print(f"   {fixer.log_file}")
    
    if success:
        print("\n🎉 Bullseye desktop fix complete!")
        print("💡 New Bullseye-optimized desktop files created")
        print("🖱️ Double-click any desktop file to launch")
    else:
        print("\n❌ Bullseye desktop fix encountered issues")
        print("💡 Check the log file for detailed information")

if __name__ == "__main__":
    main()