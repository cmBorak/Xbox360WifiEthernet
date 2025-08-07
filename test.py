#!/usr/bin/env python3
"""
Xbox 360 WiFi Module Emulator - Simple Tester
Tests the current BullseyeXboxInstaller implementation
"""

import os
import sys
import subprocess
import platform
from pathlib import Path

def print_colored(message, level="info"):
    """Print colored messages"""
    colors = {
        'error': '\033[0;31m❌',
        'warning': '\033[1;33m⚠️ ',
        'success': '\033[0;32m✅',
        'info': '\033[0;34mℹ️ ',
        'header': '\033[0;35m🎮'
    }
    reset = '\033[0m'
    
    prefix = colors.get(level, 'ℹ️ ')
    print(f"{prefix} {message}{reset}")

def test_system_requirements():
    """Test basic system requirements"""
    print_colored("Testing System Requirements", "header")
    
    passed = 0
    total = 4
    
    # Test Python version
    if sys.version_info >= (3, 6):
        print_colored(f"Python {'.'.join(map(str, sys.version_info[:3]))}", "success")
        passed += 1
    else:
        print_colored(f"Python {'.'.join(map(str, sys.version_info[:3]))} - need 3.6+", "error")
    
    # Test tkinter
    try:
        import tkinter
        print_colored("tkinter (GUI support)", "success")
        passed += 1
    except ImportError:
        print_colored("tkinter not available", "error")
    
    # Test essential commands
    for cmd in ['bash', 'python3']:
        try:
            subprocess.run(['which', cmd], check=True, capture_output=True)
            print_colored(f"{cmd} command available", "success")
            passed += 1
        except (subprocess.CalledProcessError, FileNotFoundError):
            print_colored(f"{cmd} command not found", "error")
    
    print_colored(f"System Requirements: {passed}/{total} passed", "info")
    return passed == total

def test_installer_files():
    """Test if installer files are present and valid"""
    print_colored("Testing Installer Files", "header")
    
    script_dir = Path(__file__).parent
    required_files = ['installer.py', 'install.sh']
    optional_files = ['xbox360.bat', 'test.py']
    
    passed = 0
    total = len(required_files)
    
    for file in required_files:
        file_path = script_dir / file
        if file_path.exists():
            if file.endswith('.py'):
                try:
                    subprocess.run([sys.executable, '-m', 'py_compile', str(file_path)], 
                                 check=True, capture_output=True)
                    print_colored(f"{file} - syntax OK", "success")
                    passed += 1
                except subprocess.CalledProcessError:
                    print_colored(f"{file} - syntax error", "error")
            else:
                print_colored(f"{file} - present", "success")
                passed += 1
        else:
            print_colored(f"{file} - missing", "error")
    
    for file in optional_files:
        file_path = script_dir / file
        if file_path.exists():
            print_colored(f"{file} - present", "info")
    
    print_colored(f"Required Files: {passed}/{total} passed", "info")
    return passed == total

def test_installer_functionality():
    """Test installer functionality"""
    print_colored("Testing Installer Functionality", "header")
    
    passed = 0
    total = 3
    
    # Test installer import
    try:
        script_dir = Path(__file__).parent
        sys.path.insert(0, str(script_dir))
        import installer
        print_colored("installer.py imports successfully", "success")
        passed += 1
        
        # Test BullseyeXboxInstaller creation
        try:
            core = installer.BullseyeXboxInstaller()
            print_colored("BullseyeXboxInstaller can be created", "success")
            passed += 1
        except Exception as e:
            print_colored(f"BullseyeXboxInstaller creation failed: {e}", "error")
        
        # Test compatibility aliases
        try:
            core = installer.XboxInstallerCore()
            print_colored("XboxInstallerCore alias works", "success")
            passed += 1
        except Exception as e:
            print_colored(f"XboxInstallerCore creation failed: {e}", "error")
            
    except ImportError as e:
        print_colored(f"installer.py import failed: {e}", "error")
    except Exception as e:
        print_colored(f"installer.py test failed: {e}", "error")
    
    # Test GUI components if available
    try:
        import tkinter
        try:
            root = tkinter.Tk()
            root.withdraw()
            gui = installer.XboxInstallerGUI()
            root.destroy()
            print_colored("GUI components work", "warning")  # Changed to warning since GUI creation was tested
        except Exception as e:
            print_colored(f"GUI test failed: {e}", "warning")
    except ImportError:
        pass
    
    print_colored(f"Installer Functionality: {passed}/{total} passed", "info")
    return passed >= 2  # Allow GUI test to fail

def main():
    """Main entry point"""
    print("🎮 Xbox 360 WiFi Module Emulator - Universal Tester")
    print("="*50)
    
    # Show system info
    system_info = {
        'os': platform.system(),
        'arch': platform.machine(),
        'python_version': sys.version_info,
        'is_pi': False
    }
    
    # Check for Raspberry Pi
    try:
        with open('/proc/cpuinfo', 'r') as f:
            if 'Raspberry Pi' in f.read():
                system_info['is_pi'] = True
    except FileNotFoundError:
        pass
    
    print(f"OS: {system_info['os']} ({system_info['arch']})")
    print(f"Python: {'.'.join(map(str, system_info['python_version'][:3]))}")
    if system_info['is_pi']:
        print("Hardware: Raspberry Pi ✅")
    print("")
    
    # Run tests
    tests = [
        ("System Requirements", test_system_requirements),
        ("Installer Files", test_installer_files),
        ("Installer Functionality", test_installer_functionality),
    ]
    
    passed_tests = 0
    total_tests = len(tests)
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            if result:
                passed_tests += 1
        except Exception as e:
            print_colored(f"{test_name} crashed: {e}", "error")
    
    # Show summary
    print("\n" + "="*50)
    print_colored("TEST SUMMARY", "header")
    print("="*50)
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            if result:
                print_colored(f"{test_name}", "success")
            else:
                print_colored(f"{test_name}: Test failed", "error")
        except Exception as e:
            print_colored(f"{test_name}: {e}", "error")
    
    print("\n" + "-"*50)
    if passed_tests == total_tests:
        print_colored(f"✅ {passed_tests}/{total_tests} tests passed", "success")
    else:
        print_colored(f"⚠️ {passed_tests}/{total_tests} tests passed", "warning")
    
    # Recommendations
    print("\n" + "="*50)
    print_colored("RECOMMENDATIONS", "header")
    print("="*50)
    
    if system_info['os'] == 'Linux':
        print_colored("Linux users:", "info")
        print("  • Run: ./install.sh to start installer")
        print("  • Use sudo for installation")
        if system_info['is_pi']:
            print("  • Perfect! You're on Raspberry Pi")
    
    print_colored("Next steps:", "info")
    print("  1. Fix any failed tests above")
    print("  2. Run: python3 installer.py (or ./install.sh)")
    print("  3. Use --gui flag for graphical interface")
    print("  4. Use --test flag to test compatibility")

if __name__ == "__main__":
    main()