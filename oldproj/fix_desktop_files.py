#!/usr/bin/env python3
"""
Quick Desktop File Fix Script
Makes desktop files executable and tests basic functionality
"""

import os
import subprocess
from pathlib import Path
from datetime import datetime

def log_to_debuglogs(message):
    """Log message to debuglogs directory"""
    try:
        # Setup debuglogs directory
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
        
        debug_log_dir = desktop_dir / "debuglogs"
        debug_log_dir.mkdir(exist_ok=True)
        
        # Create/append to fix log
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = debug_log_dir / f"desktop_fix_{timestamp}.log"
        
        log_entry = f"[{datetime.now().strftime('%H:%M:%S')}] {message}\n"
        
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(log_entry)
        
        print(message)
        return str(log_file)
        
    except Exception as e:
        print(f"{message} (logging failed: {e})")
        return None

def fix_desktop_files():
    """Fix desktop file permissions and basic issues"""
    log_file = log_to_debuglogs("🔧 Desktop File Fix Started")
    
    script_dir = Path.cwd()
    desktop_files = list(script_dir.glob("*.desktop"))
    
    if not desktop_files:
        log_to_debuglogs("❌ No desktop files found in current directory")
        log_to_debuglogs(f"   Current directory: {script_dir}")
        return False
    
    log_to_debuglogs(f"📂 Found {len(desktop_files)} desktop files:")
    for df in desktop_files:
        log_to_debuglogs(f"   - {df.name}")
    
    success_count = 0
    
    for desktop_file in desktop_files:
        log_to_debuglogs(f"\n🔧 Processing: {desktop_file.name}")
        
        try:
            # Make executable
            os.chmod(desktop_file, 0o755)
            log_to_debuglogs("✅ Made executable (chmod +x)")
            
            # Check if installer.py exists
            if 'installer.py' in desktop_file.read_text():
                installer_path = script_dir / "installer.py"
                if installer_path.exists():
                    log_to_debuglogs("✅ installer.py found")
                    
                    # Test Python syntax
                    result = subprocess.run(['python3', '-m', 'py_compile', str(installer_path)], 
                                          capture_output=True, text=True)
                    if result.returncode == 0:
                        log_to_debuglogs("✅ installer.py syntax is valid")
                    else:
                        log_to_debuglogs(f"❌ installer.py syntax error: {result.stderr}")
                else:
                    log_to_debuglogs("❌ installer.py not found")
            
            success_count += 1
            
        except Exception as e:
            log_to_debuglogs(f"❌ Error processing {desktop_file.name}: {e}")
    
    log_to_debuglogs(f"\n✅ Successfully processed {success_count}/{len(desktop_files)} desktop files")
    
    # Provide usage instructions
    log_to_debuglogs("\n📋 Next Steps:")
    log_to_debuglogs("1. Copy desktop file to desktop: cp *.desktop ~/Desktop/")
    log_to_debuglogs("2. Double-click desktop file to test")
    log_to_debuglogs("3. Or test manually: python3 installer.py")
    log_to_debuglogs("4. Check logs in ~/Desktop/debuglogs/ for any issues")
    
    if log_file:
        log_to_debuglogs(f"\n📝 Fix log saved to: {log_file}")
    
    return success_count > 0

def main():
    print("🔧 Xbox 360 WiFi Emulator - Desktop File Fix")
    print("=" * 45)
    print("🎯 Making desktop files executable and checking basic functionality")
    print("📝 Logging all actions to ~/Desktop/debuglogs/")
    print()
    
    if fix_desktop_files():
        print("\n🎉 Desktop files fixed successfully!")
        print("💡 Now try double-clicking a desktop file or run the debug script")
    else:
        print("\n❌ Desktop file fix encountered issues")
        print("💡 Run debug_desktop_app.py for detailed analysis")

if __name__ == "__main__":
    main()