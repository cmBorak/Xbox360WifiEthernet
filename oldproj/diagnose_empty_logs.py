#!/usr/bin/env python3
"""
Diagnose Empty Logs Issue
Specifically diagnoses why GUI operations are failing immediately on Pi
"""

import os
import sys
import traceback
from datetime import datetime
from pathlib import Path

def log_to_debuglogs(message, level="INFO"):
    """Log directly to debuglogs with error handling"""
    try:
        # Setup debuglogs directory
        desktop_dir = Path.home() / "Desktop"
        if not desktop_dir.exists():
            desktop_dir = Path("/home/pi/Desktop")
        if not desktop_dir.exists():
            desktop_dir = Path.home()
        
        debug_log_dir = desktop_dir / "debuglogs"
        debug_log_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = debug_log_dir / f"empty_logs_diagnosis_{timestamp}.log"
        
        log_entry = f"[{datetime.now().strftime('%H:%M:%S')}] [{level}] {message}\n"
        
        # Always write to file
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(log_entry)
        
        # Also print to console
        print(f"[{level}] {message}")
        
        return str(log_file)
        
    except Exception as e:
        print(f"[ERROR] Logging failed: {e}")
        print(f"[{level}] {message}")
        return None

def diagnose_import_issues():
    """Diagnose Python import issues"""
    log_to_debuglogs("🔍 Diagnosing Python Import Issues", "INFO")
    
    # Test critical imports
    imports_to_test = [
        ("tkinter", "GUI framework"),
        ("pathlib", "Path handling"),
        ("subprocess", "System commands"),
        ("threading", "Threading support"),
        ("queue", "Queue operations"),
        ("platform", "Platform info"),
        ("datetime", "Date/time functions"),
        ("os", "Operating system interface"),
        ("sys", "System interface")
    ]
    
    failed_imports = []
    
    for module_name, description in imports_to_test:
        try:
            __import__(module_name)
            log_to_debuglogs(f"✅ {module_name}: OK ({description})", "SUCCESS")
        except ImportError as e:
            log_to_debuglogs(f"❌ {module_name}: FAILED - {e}", "ERROR")
            failed_imports.append((module_name, str(e)))
        except Exception as e:
            log_to_debuglogs(f"❌ {module_name}: ERROR - {e}", "ERROR")
            failed_imports.append((module_name, str(e)))
    
    return failed_imports

def test_installer_import():
    """Test importing the installer module"""
    log_to_debuglogs("🔍 Testing Installer Module Import", "INFO")
    
    try:
        # Change to correct directory
        script_dir = Path(__file__).parent
        log_to_debuglogs(f"Script directory: {script_dir}", "INFO")
        
        if not (script_dir / "installer.py").exists():
            log_to_debuglogs("❌ installer.py not found in current directory", "ERROR")
            log_to_debuglogs(f"Current directory: {Path.cwd()}", "INFO")
            log_to_debuglogs(f"Files in directory: {list(Path.cwd().glob('*.py'))}", "INFO")
            return False
        
        # Test import
        sys.path.insert(0, str(script_dir))
        from installer import XboxInstaller
        log_to_debuglogs("✅ XboxInstaller import successful", "SUCCESS")
        
        # Test GUI import
        from installer import XboxInstallerGUI, GUI_AVAILABLE
        log_to_debuglogs(f"✅ XboxInstallerGUI import successful", "SUCCESS")
        log_to_debuglogs(f"GUI Available: {GUI_AVAILABLE}", "INFO")
        
        return True
        
    except ImportError as e:
        log_to_debuglogs(f"❌ Installer import failed: {e}", "ERROR")
        log_to_debuglogs(f"Import traceback: {traceback.format_exc()}", "ERROR")
        return False
    except Exception as e:
        log_to_debuglogs(f"❌ Installer test failed: {e}", "ERROR")
        log_to_debuglogs(f"Full traceback: {traceback.format_exc()}", "ERROR")
        return False

def test_gui_initialization():
    """Test GUI initialization"""
    log_to_debuglogs("🔍 Testing GUI Initialization", "INFO")
    
    try:
        # Test basic tkinter
        import tkinter as tk
        root = tk.Tk()
        root.withdraw()  # Hide window
        log_to_debuglogs("✅ Basic Tkinter initialization successful", "SUCCESS")
        root.destroy()
        
        # Test installer GUI
        script_dir = Path(__file__).parent
        sys.path.insert(0, str(script_dir))
        
        from installer import XboxInstallerGUI
        log_to_debuglogs("Attempting to create XboxInstallerGUI instance...", "INFO")
        
        gui = XboxInstallerGUI()
        log_to_debuglogs("✅ XboxInstallerGUI created successfully", "SUCCESS")
        
        # Test debug log directory setup
        if hasattr(gui, 'debug_log_dir'):
            log_to_debuglogs(f"Debug log directory: {gui.debug_log_dir}", "INFO")
            if gui.debug_log_dir.exists():
                log_to_debuglogs("✅ Debug log directory exists", "SUCCESS")
            else:
                log_to_debuglogs("❌ Debug log directory does not exist", "ERROR")
        
        # Test session logging
        if hasattr(gui, '_start_log_session'):
            log_to_debuglogs("Testing session logging...", "INFO")
            gui._start_log_session("diagnosis_test")
            log_to_debuglogs("✅ Session logging started successfully", "SUCCESS")
            gui._end_log_session()
            log_to_debuglogs("✅ Session logging ended successfully", "SUCCESS")
        
        # Clean up
        if hasattr(gui, 'root'):
            gui.root.destroy()
        
        return True
        
    except Exception as e:
        log_to_debuglogs(f"❌ GUI initialization failed: {e}", "ERROR")
        log_to_debuglogs(f"Full traceback: {traceback.format_exc()}", "ERROR")
        return False

def test_logging_mechanism():
    """Test the logging mechanism specifically"""
    log_to_debuglogs("🔍 Testing Logging Mechanism", "INFO")
    
    try:
        script_dir = Path(__file__).parent
        sys.path.insert(0, str(script_dir))
        
        from installer import XboxInstallerGUI
        gui = XboxInstallerGUI()
        
        # Test manual logging operations
        log_to_debuglogs("Testing _start_log_session...", "INFO")
        result = gui._start_log_session("manual_test")
        log_to_debuglogs(f"_start_log_session result: {result}", "INFO")
        
        if hasattr(gui, 'current_log_session') and gui.current_log_session:
            log_to_debuglogs(f"Current log session: {gui.current_log_session}", "SUCCESS")
            
            # Test writing to log
            log_to_debuglogs("Testing _log_to_file...", "INFO")
            gui._log_to_file("Test log entry from diagnosis", "info")
            log_to_debuglogs("✅ _log_to_file executed", "SUCCESS")
            
            # Test ending session
            log_to_debuglogs("Testing _end_log_session...", "INFO")
            gui._end_log_session()
            log_to_debuglogs("✅ _end_log_session executed", "SUCCESS")
            
            # Check if log file was created
            if gui.current_log_session and Path(gui.current_log_session).exists():
                log_to_debuglogs(f"✅ Log file created: {gui.current_log_session}", "SUCCESS")
                # Read log file content
                with open(gui.current_log_session, 'r') as f:
                    content = f.read()
                    log_to_debuglogs(f"Log file content length: {len(content)} characters", "INFO")
            else:
                log_to_debuglogs("❌ Log file was not created", "ERROR")
        else:
            log_to_debuglogs("❌ current_log_session not set", "ERROR")
        
        return True
        
    except Exception as e:
        log_to_debuglogs(f"❌ Logging mechanism test failed: {e}", "ERROR")
        log_to_debuglogs(f"Full traceback: {traceback.format_exc()}", "ERROR")
        return False

def check_system_environment():
    """Check system environment factors"""
    log_to_debuglogs("🔍 Checking System Environment", "INFO")
    
    # Check display
    display = os.getenv('DISPLAY')
    log_to_debuglogs(f"DISPLAY: {display or 'Not set'}", "INFO")
    
    # Check if running in SSH
    ssh_client = os.getenv('SSH_CLIENT')
    ssh_tty = os.getenv('SSH_TTY')
    if ssh_client or ssh_tty:
        log_to_debuglogs("⚠️ Running in SSH session", "WARNING")
        log_to_debuglogs("GUI may require X11 forwarding or local display", "WARNING")
    
    # Check desktop environment
    desktop_session = os.getenv('DESKTOP_SESSION', 'unknown')
    xdg_current_desktop = os.getenv('XDG_CURRENT_DESKTOP', 'unknown')
    log_to_debuglogs(f"Desktop Session: {desktop_session}", "INFO")
    log_to_debuglogs(f"XDG Current Desktop: {xdg_current_desktop}", "INFO")
    
    # Check Python version
    log_to_debuglogs(f"Python Version: {sys.version}", "INFO")
    log_to_debuglogs(f"Python Executable: {sys.executable}", "INFO")

def main():
    """Main diagnosis function"""
    print("🔍 Xbox 360 WiFi Emulator - Empty Logs Diagnosis")
    print("=" * 55)
    print("🎯 Diagnosing why GUI operations fail immediately...")
    print("📝 All findings logged to ~/Desktop/debuglogs/")
    print()
    
    log_file = log_to_debuglogs("🚀 Empty Logs Diagnosis Started", "INFO")
    log_to_debuglogs("=" * 50, "INFO")
    
    try:
        # Step 1: Check system environment
        check_system_environment()
        
        # Step 2: Test imports
        log_to_debuglogs("\n" + "=" * 30, "INFO")
        failed_imports = diagnose_import_issues()
        
        # Step 3: Test installer import
        log_to_debuglogs("\n" + "=" * 30, "INFO")
        installer_ok = test_installer_import()
        
        # Step 4: Test GUI initialization
        if installer_ok:
            log_to_debuglogs("\n" + "=" * 30, "INFO")
            gui_ok = test_gui_initialization()
            
            # Step 5: Test logging mechanism
            if gui_ok:
                log_to_debuglogs("\n" + "=" * 30, "INFO")
                logging_ok = test_logging_mechanism()
        
        # Summary
        log_to_debuglogs("\n" + "=" * 50, "INFO")
        log_to_debuglogs("📊 Diagnosis Summary", "INFO")
        log_to_debuglogs("=" * 20, "INFO")
        
        if failed_imports:
            log_to_debuglogs(f"❌ Failed imports: {len(failed_imports)}", "ERROR")
            for module, error in failed_imports:
                log_to_debuglogs(f"   - {module}: {error}", "ERROR")
        else:
            log_to_debuglogs("✅ All imports successful", "SUCCESS")
        
        log_to_debuglogs(f"Installer import: {'✅ OK' if installer_ok else '❌ FAILED'}", "SUCCESS" if installer_ok else "ERROR")
        
        if 'gui_ok' in locals():
            log_to_debuglogs(f"GUI initialization: {'✅ OK' if gui_ok else '❌ FAILED'}", "SUCCESS" if gui_ok else "ERROR")
        
        if 'logging_ok' in locals():
            log_to_debuglogs(f"Logging mechanism: {'✅ OK' if logging_ok else '❌ FAILED'}", "SUCCESS" if logging_ok else "ERROR")
        
        log_to_debuglogs("=" * 50, "INFO")
        log_to_debuglogs("✅ Diagnosis Complete", "SUCCESS")
        
        if log_file:
            log_to_debuglogs(f"📂 Full diagnosis log: {log_file}", "INFO")
            print(f"\n📂 Complete diagnosis available at: {log_file}")
        
    except Exception as e:
        log_to_debuglogs(f"❌ Diagnosis failed: {e}", "ERROR")
        log_to_debuglogs(f"Full traceback: {traceback.format_exc()}", "ERROR")

if __name__ == "__main__":
    main()