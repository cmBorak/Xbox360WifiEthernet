#!/usr/bin/env python3
"""
Xbox 360 WiFi Module Emulator - Cleanup Redundant Files
Safely removes redundant files after refactoring while preserving important ones
"""

import os
import sys
import shutil
from pathlib import Path
from typing import List, Dict

class RedundantFileCleanup:
    def __init__(self):
        self.script_dir = Path(__file__).parent.absolute()
        self.backup_dir = self.script_dir / "backup_redundant_files"
        
        # Files to remove (redundant after refactoring)
        self.files_to_remove = [
            # Redundant installation scripts
            "install_complete.sh",
            "install_fixed.sh", 
            "install_fully_automated.sh",
            "launch_installer.sh",
            "run_installer_ui.sh",
            "setup.sh",
            "debug_install.sh",
            "installer_ui.py",  # Replaced by installer.py
            
            # Redundant testing scripts
            "test_in_docker.sh",
            "test_simple.sh",
            "test_local.py",
            
            # Redundant USB sniffing scripts
            "setup_usb_sniffing.sh",
            "setup_usbmon_only.sh", 
            "build_usb_sniffify.sh",
            
            # Redundant batch files
            "INSTALL_XBOX360.bat",
            "TEST_SIMPLE.bat", 
            "TEST_XBOX360.bat",
            
            # Redundant documentation
            "START_HERE.md",
            "TROUBLESHOOTING.md",
            "CHANGELOG.md",
            
            # Desktop file (will be recreated by installer)
            "Xbox360_Installer.desktop",
        ]
        
        # Directories to remove
        self.dirs_to_remove = [
            "docker",  # Simplified approach doesn't need complex Docker setup
            "tests",   # Basic tests, replaced by test.py
        ]
        
        # Files to keep (important)
        self.files_to_keep = [
            "installer.py",    # New unified installer
            "install.sh",      # New universal launcher
            "xbox360.bat",     # New universal Windows launcher  
            "test.py",         # New universal tester
            "README.md",       # Main documentation
            "REFACTOR_PLAN.md", # Refactoring documentation
            "src/",            # Source code directory
            "usb_sniffing_tools/", # USB sniffing tools
            "config/",         # Configuration files
            "docs/",           # Keep existing docs for now
        ]
    
    def print_status(self, message: str, level: str = "info"):
        """Print colored status message"""
        colors = {
            'info': '\033[0;34mℹ️ ',
            'success': '\033[0;32m✅',
            'warning': '\033[1;33m⚠️ ',
            'error': '\033[0;31m❌',
            'header': '\033[0;35m🧹'
        }
        reset = '\033[0m'
        print(f"{colors.get(level, 'ℹ️ ')}{message}{reset}")
    
    def analyze_files(self) -> Dict:
        """Analyze current files and what will be affected"""
        analysis = {
            'files_to_remove': [],
            'dirs_to_remove': [],
            'files_missing': [],
            'dirs_missing': [],
            'total_size_to_remove': 0
        }
        
        # Check files to remove
        for file_name in self.files_to_remove:
            file_path = self.script_dir / file_name
            if file_path.exists():
                analysis['files_to_remove'].append(file_path)
                if file_path.is_file():
                    analysis['total_size_to_remove'] += file_path.stat().st_size
            else:
                analysis['files_missing'].append(file_name)
        
        # Check directories to remove
        for dir_name in self.dirs_to_remove:
            dir_path = self.script_dir / dir_name
            if dir_path.exists() and dir_path.is_dir():
                analysis['dirs_to_remove'].append(dir_path)
                # Calculate directory size
                for file_path in dir_path.rglob('*'):
                    if file_path.is_file():
                        analysis['total_size_to_remove'] += file_path.stat().st_size
            else:
                analysis['dirs_missing'].append(dir_name)
        
        return analysis
    
    def backup_files(self, analysis: Dict) -> bool:
        """Backup files before removal"""
        self.print_status("Creating backup of files to be removed...", "info")
        
        try:
            # Create backup directory
            self.backup_dir.mkdir(exist_ok=True)
            
            # Backup files
            for file_path in analysis['files_to_remove']:
                backup_path = self.backup_dir / file_path.name
                shutil.copy2(file_path, backup_path)
                self.print_status(f"Backed up: {file_path.name}", "success")
            
            # Backup directories
            for dir_path in analysis['dirs_to_remove']:
                backup_path = self.backup_dir / dir_path.name
                if backup_path.exists():
                    shutil.rmtree(backup_path)
                shutil.copytree(dir_path, backup_path)
                self.print_status(f"Backed up directory: {dir_path.name}", "success")
            
            self.print_status(f"Backup created in: {self.backup_dir}", "success")
            return True
            
        except Exception as e:
            self.print_status(f"Backup failed: {e}", "error")
            return False
    
    def remove_files(self, analysis: Dict) -> bool:
        """Remove redundant files"""
        self.print_status("Removing redundant files...", "info")
        
        try:
            # Remove files
            for file_path in analysis['files_to_remove']:
                file_path.unlink()
                self.print_status(f"Removed file: {file_path.name}", "success")
            
            # Remove directories
            for dir_path in analysis['dirs_to_remove']:
                shutil.rmtree(dir_path)
                self.print_status(f"Removed directory: {dir_path.name}", "success")
            
            return True
            
        except Exception as e:
            self.print_status(f"File removal failed: {e}", "error")
            return False
    
    def show_analysis(self, analysis: Dict):
        """Show analysis of what will be removed"""
        self.print_status("CLEANUP ANALYSIS", "header")
        print("=" * 50)
        
        print(f"\n📁 Files to remove ({len(analysis['files_to_remove'])}):")
        for file_path in analysis['files_to_remove']:
            size_kb = file_path.stat().st_size / 1024
            print(f"  • {file_path.name} ({size_kb:.1f} KB)")
        
        print(f"\n📂 Directories to remove ({len(analysis['dirs_to_remove'])}):")
        for dir_path in analysis['dirs_to_remove']:
            file_count = len(list(dir_path.rglob('*')))
            print(f"  • {dir_path.name}/ ({file_count} items)")
        
        if analysis['files_missing']:
            print(f"\n❓ Files already missing ({len(analysis['files_missing'])}):")
            for file_name in analysis['files_missing']:
                print(f"  • {file_name}")
        
        total_mb = analysis['total_size_to_remove'] / (1024 * 1024)
        print(f"\n💾 Total space to be freed: {total_mb:.2f} MB")
        
        print(f"\n✅ Files that will be KEPT:")
        for keep_item in self.files_to_keep:
            keep_path = self.script_dir / keep_item
            if keep_path.exists():
                print(f"  • {keep_item}")
    
    def run_cleanup(self, create_backup: bool = True):
        """Run the complete cleanup process"""
        self.print_status("Xbox 360 WiFi Module Emulator - File Cleanup", "header")
        
        # Analyze files
        analysis = self.analyze_files()
        self.show_analysis(analysis)
        
        if not analysis['files_to_remove'] and not analysis['dirs_to_remove']:
            self.print_status("No redundant files found to remove", "info")
            return True
        
        # Confirm with user
        print("\n" + "="*50)
        response = input("Continue with cleanup? (y/N): ").strip().lower()
        if response not in ['y', 'yes']:
            self.print_status("Cleanup cancelled", "info")
            return False
        
        # Create backup if requested
        if create_backup:
            if not self.backup_files(analysis):
                self.print_status("Cannot proceed without backup", "error")
                return False
        
        # Remove files
        if not self.remove_files(analysis):
            self.print_status("File removal failed", "error")
            return False
        
        # Show completion message
        print("\n" + "="*50)
        self.print_status("CLEANUP COMPLETED SUCCESSFULLY", "header")
        print("="*50)
        
        files_removed = len(analysis['files_to_remove'])
        dirs_removed = len(analysis['dirs_to_remove'])
        space_freed_mb = analysis['total_size_to_remove'] / (1024 * 1024)
        
        self.print_status(f"Removed {files_removed} files and {dirs_removed} directories", "success")
        self.print_status(f"Freed {space_freed_mb:.2f} MB of disk space", "success")
        
        if create_backup:
            self.print_status(f"Backup available at: {self.backup_dir}", "info")
        
        print(f"\n🎯 Your streamlined Xbox 360 emulator now has only essential files:")
        print("  • installer.py - Universal installer (GUI + CLI)")
        print("  • install.sh - Universal Linux/Mac launcher") 
        print("  • xbox360.bat - Universal Windows launcher")
        print("  • test.py - Universal testing script")
        print("  • src/ - Source code directory")
        print("  • usb_sniffing_tools/ - USB tools")
        
        return True

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Xbox 360 WiFi Module Emulator - Cleanup Redundant Files")
    parser.add_argument('--analyze', action='store_true', help='Analyze files without removing')
    parser.add_argument('--no-backup', action='store_true', help='Skip creating backup (not recommended)')
    parser.add_argument('--force', action='store_true', help='Skip confirmation prompt')
    
    args = parser.parse_args()
    
    cleanup = RedundantFileCleanup()
    
    if args.analyze:
        # Just show analysis
        analysis = cleanup.analyze_files()
        cleanup.show_analysis(analysis)
        return 0
    
    # Override confirmation if force flag is used
    if args.force:
        import builtins
        original_input = builtins.input
        builtins.input = lambda x: 'y'
    
    try:
        success = cleanup.run_cleanup(create_backup=not args.no_backup)
        return 0 if success else 1
    finally:
        if args.force:
            builtins.input = original_input

if __name__ == "__main__":
    sys.exit(main())