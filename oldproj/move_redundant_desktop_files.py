#!/usr/bin/env python3
"""
Move Redundant Desktop Files
Moves the specified redundant desktop files to a separate directory
and logs everything to debuglogs
"""

import os
import shutil
from pathlib import Path
from datetime import datetime

class RedundantDesktopFileMover:
    def __init__(self):
        self.setup_logging()
        
    def setup_logging(self):
        """Setup centralized logging to debuglogs directory"""
        # Handle both Desktop and desktop (lowercase) variants
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
        self.log_file = self.debug_log_dir / f"move_redundant_desktop_{timestamp}.log"
        
        # Start logging
        self.log_buffer = []
        self.log("📁 Move Redundant Desktop Files Started", "INFO")
        self.log("=" * 45, "INFO")
        self.log(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", "INFO")
        self.log(f"Working Directory: {Path.cwd()}", "INFO")
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
    
    def identify_redundant_files(self):
        """Identify the specific redundant desktop files"""
        self.log("\n🔍 IDENTIFYING REDUNDANT DESKTOP FILES", "INFO")
        self.log("-" * 42, "INFO")
        
        # Files specifically mentioned by user
        redundant_files = [
            "Xbox360-Emulator-Fixed.desktop",
            "Xbox360-Emulator-Simple.desktop", 
            "Xbox360-Emulator-Terminal-Fixed.desktop"
        ]
        
        current_dir = Path.cwd()
        existing_files = []
        missing_files = []
        
        for filename in redundant_files:
            file_path = current_dir / filename
            if file_path.exists():
                existing_files.append(file_path)
                self.log(f"✅ Found: {filename}", "SUCCESS")
                
                # Show file size
                size = file_path.stat().st_size
                self.log(f"   Size: {size} bytes", "INFO")
                
            else:
                missing_files.append(filename)
                self.log(f"❌ Not found: {filename}", "WARNING")
        
        if missing_files:
            self.log(f"\n⚠️ Missing files: {len(missing_files)}", "WARNING")
            for filename in missing_files:
                self.log(f"   • {filename}", "WARNING")
        
        self.log(f"\n📊 Summary:", "INFO")
        self.log(f"   Files to move: {len(existing_files)}", "INFO")
        self.log(f"   Missing files: {len(missing_files)}", "INFO")
        
        return existing_files
    
    def create_redundant_directory(self):
        """Create directory for redundant desktop files"""
        self.log("\n📁 CREATING REDUNDANT FILES DIRECTORY", "INFO")
        self.log("-" * 40, "INFO")
        
        current_dir = Path.cwd()
        redundant_dir = current_dir / "redundant_desktop_files"
        
        try:
            redundant_dir.mkdir(exist_ok=True)
            self.log(f"✅ Created directory: {redundant_dir}", "SUCCESS")
            
            # Create README file explaining what these files are
            readme_content = f"""# Redundant Desktop Files

This directory contains desktop launcher files that are no longer needed.

## Files moved here:
- Xbox360-Emulator-Fixed.desktop
- Xbox360-Emulator-Simple.desktop  
- Xbox360-Emulator-Terminal-Fixed.desktop

## Reason for moving:
These files were replaced with improved Pi-specific desktop files:
- Xbox360-Emulator-Pi.desktop (GUI version)
- Xbox360-Emulator-Pi-Terminal.desktop (Terminal version)
- Xbox360-Emulator-Pi-Fixed.desktop (Comprehensive launcher)

## Current active desktop files:
The new Pi-specific desktop files are located in the main directory and
have been copied to ~/Desktop/ for easy access.

## Safe to delete:
These redundant files can be safely deleted if no longer needed.

Moved on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
            
            readme_file = redundant_dir / "README.md"
            with open(readme_file, 'w') as f:
                f.write(readme_content)
            
            self.log("✅ Created README.md explaining the moved files", "SUCCESS")
            
            return redundant_dir
            
        except Exception as e:
            self.log(f"❌ Failed to create directory: {e}", "ERROR")
            return None
    
    def move_files(self, files_to_move, destination_dir):
        """Move the redundant files to the destination directory"""
        self.log("\n📦 MOVING REDUNDANT FILES", "INFO")
        self.log("-" * 27, "INFO")
        
        moved_files = []
        failed_moves = []
        
        for file_path in files_to_move:
            try:
                destination_path = destination_dir / file_path.name
                
                # Check if destination already exists
                if destination_path.exists():
                    self.log(f"⚠️ Destination exists: {file_path.name}", "WARNING")
                    # Create backup name
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    backup_name = f"{file_path.stem}_backup_{timestamp}{file_path.suffix}"
                    destination_path = destination_dir / backup_name
                    self.log(f"   Using backup name: {backup_name}", "INFO")
                
                # Move the file
                shutil.move(file_path, destination_path)
                
                self.log(f"✅ Moved: {file_path.name} → {destination_path.name}", "SUCCESS")
                moved_files.append((file_path.name, destination_path))
                
            except Exception as e:
                self.log(f"❌ Failed to move {file_path.name}: {e}", "ERROR")
                failed_moves.append(file_path.name)
        
        # Summary
        self.log(f"\n📊 Move Summary:", "INFO")
        self.log(f"   Successfully moved: {len(moved_files)}", "SUCCESS")
        self.log(f"   Failed moves: {len(failed_moves)}", "ERROR" if failed_moves else "INFO")
        
        if moved_files:
            self.log("✅ Moved files:", "SUCCESS")
            for original, destination in moved_files:
                self.log(f"   {original} → {destination.name}", "SUCCESS")
        
        if failed_moves:
            self.log("❌ Failed moves:", "ERROR")
            for filename in failed_moves:
                self.log(f"   {filename}", "ERROR")
        
        return moved_files, failed_moves
    
    def verify_cleanup(self):
        """Verify the cleanup was successful"""
        self.log("\n🔍 VERIFYING CLEANUP", "INFO")
        self.log("-" * 22, "INFO")
        
        current_dir = Path.cwd()
        redundant_dir = current_dir / "redundant_desktop_files"
        
        # Check what desktop files remain in main directory
        remaining_desktop_files = list(current_dir.glob("*.desktop"))
        self.log(f"Desktop files remaining in main directory: {len(remaining_desktop_files)}", "INFO")
        
        for desktop_file in remaining_desktop_files:
            self.log(f"   ✅ {desktop_file.name}", "SUCCESS")
        
        # Check what's in the redundant directory
        if redundant_dir.exists():
            moved_files = list(redundant_dir.glob("*.desktop"))
            self.log(f"Desktop files in redundant directory: {len(moved_files)}", "INFO")
            
            for moved_file in moved_files:
                self.log(f"   📁 {moved_file.name}", "INFO")
        
        # Recommend which files are now the active ones
        self.log("\n💡 ACTIVE DESKTOP FILES:", "INFO")
        active_patterns = ["*Pi*.desktop", "*comprehensive*.desktop"]
        active_files = []
        
        for pattern in active_patterns:
            active_files.extend(current_dir.glob(pattern))
        
        if active_files:
            self.log("These are your current active desktop files:", "SUCCESS")
            for active_file in active_files:
                self.log(f"   🎯 {active_file.name}", "SUCCESS")
        else:
            self.log("⚠️ No Pi-specific desktop files found", "WARNING")
            self.log("💡 You may want to run: python3 fix_desktop_paths_pi.py", "INFO")
    
    def provide_final_instructions(self, redundant_dir, moved_files):
        """Provide final instructions"""
        self.log("\n📋 FINAL INSTRUCTIONS", "INFO")
        self.log("-" * 22, "INFO")
        
        if moved_files:
            self.log("✅ CLEANUP COMPLETE:", "SUCCESS")
            self.log(f"   Redundant files moved to: {redundant_dir}", "SUCCESS")
            self.log(f"   Files moved: {len(moved_files)}", "SUCCESS")
            
            self.log("\n🗑️ SAFE TO DELETE:", "INFO")
            self.log(f"   The entire {redundant_dir.name}/ directory can be safely deleted", "INFO")
            self.log("   if you're sure you don't need the old desktop files.", "INFO")
            
            self.log("\n🎯 ACTIVE DESKTOP FILES:", "INFO")
            self.log("   Use the Pi-specific desktop files that remain in the main directory", "INFO")
            self.log("   These have been optimized for Raspberry Pi with correct paths", "INFO")
            
        else:
            self.log("⚠️ NO FILES WERE MOVED:", "WARNING")
            self.log("   The specified redundant files were not found", "WARNING")
        
        self.log(f"\n📂 FULL LOG AVAILABLE:", "INFO")
        self.log(f"   {self.log_file}", "INFO")
    
    def run_redundant_file_cleanup(self):
        """Run complete redundant desktop file cleanup"""
        try:
            self.log("🚀 Starting redundant desktop file cleanup...", "INFO")
            
            # Step 1: Identify redundant files
            files_to_move = self.identify_redundant_files()
            
            if not files_to_move:
                self.log("\n🎉 No redundant files found to move!", "SUCCESS")
                self.log("The specified files may have already been moved or don't exist.", "INFO")
                return True
            
            # Step 2: Create redundant directory
            redundant_dir = self.create_redundant_directory()
            
            if not redundant_dir:
                self.log("❌ Failed to create redundant files directory", "ERROR")
                return False
            
            # Step 3: Move the files
            moved_files, failed_moves = self.move_files(files_to_move, redundant_dir)
            
            # Step 4: Verify cleanup
            self.verify_cleanup()
            
            # Step 5: Provide final instructions
            self.provide_final_instructions(redundant_dir, moved_files)
            
            self.log("\n" + "=" * 45, "INFO")
            self.log("✅ REDUNDANT FILE CLEANUP COMPLETE!", "SUCCESS")
            self.log("=" * 45, "INFO")
            self.log(f"📂 Complete cleanup log: {self.log_file}", "INFO")
            
            return len(moved_files) > 0
            
        except Exception as e:
            self.log(f"❌ Redundant file cleanup failed: {e}", "ERROR")
            import traceback
            self.log(traceback.format_exc(), "ERROR")
            return False
        finally:
            self.flush_log()

def main():
    """Main cleanup function"""
    print("📁 Xbox 360 WiFi Emulator - Move Redundant Desktop Files")
    print("=" * 60)
    print("🎯 Moving specific redundant desktop files:")
    print("   • Xbox360-Emulator-Fixed.desktop")
    print("   • Xbox360-Emulator-Simple.desktop")
    print("   • Xbox360-Emulator-Terminal-Fixed.desktop")
    print("📝 All actions logged to debuglogs directory")
    print()
    
    mover = RedundantDesktopFileMover()
    success = mover.run_redundant_file_cleanup()
    
    print(f"\n📂 Complete cleanup log:")
    print(f"   {mover.log_file}")
    
    if success:
        print("\n🎉 Redundant desktop files moved successfully!")
        print("💡 Check the redundant_desktop_files/ directory")
        print("🗑️  The redundant_desktop_files/ directory can be safely deleted if not needed")
    else:
        print("\n❌ Some files may not have been found or moved")
        print("💡 Check the log file for detailed information")

if __name__ == "__main__":
    main()