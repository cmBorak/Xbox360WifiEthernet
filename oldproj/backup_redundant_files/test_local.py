#!/usr/bin/env python3
"""
Xbox 360 WiFi Module Emulator - Local Testing Script
Test the installer and components without Docker
"""

import os
import sys
import subprocess
import platform
import tempfile
from pathlib import Path

def print_header(text):
    print(f"\n{'='*50}")
    print(f"🎮 {text}")
    print(f"{'='*50}")

def print_success(text):
    print(f"✅ {text}")

def print_error(text):
    print(f"❌ {text}")

def print_warning(text):
    print(f"⚠️  {text}")

def print_info(text):
    print(f"ℹ️  {text}")

class Xbox360LocalTester:
    def __init__(self):
        self.script_dir = Path(__file__).parent.absolute()
        self.test_results = []
    
    def check_python_requirements(self):
        """Check if Python requirements are met"""
        print_header("Checking Python Requirements")
        
        # Check Python version
        python_version = sys.version_info
        if python_version >= (3, 6):
            print_success(f"Python {python_version.major}.{python_version.minor}.{python_version.micro}")
        else:
            print_error(f"Python {python_version.major}.{python_version.minor} - need 3.6+")
            return False
        
        # Check tkinter
        try:
            import tkinter
            print_success("tkinter available")
        except ImportError:
            print_error("tkinter not available - needed for GUI")
            if platform.system() == "Linux":
                print_info("Install with: sudo apt-get install python3-tk")
            return False
        
        # Check if we can import our modules
        try:
            sys.path.insert(0, str(self.script_dir))
            import installer_ui
            print_success("installer_ui.py imports successfully")
        except ImportError as e:
            print_error(f"Cannot import installer_ui: {e}")
            return False
        except Exception as e:
            print_warning(f"installer_ui import warning: {e}")
        
        return True
    
    def check_system_requirements(self):
        """Check system requirements"""
        print_header("Checking System Requirements")
        
        # Check OS
        system = platform.system()
        print_success(f"Operating System: {system}")
        
        if system == "Linux":
            # Check if we're in WSL
            try:
                with open('/proc/version', 'r') as f:
                    if 'microsoft' in f.read().lower():
                        print_info("Running in WSL")
            except:
                pass
        
        # Check available commands
        commands_to_check = ['bash', 'python3']
        for cmd in commands_to_check:
            if subprocess.run(['which', cmd], capture_output=True).returncode == 0:
                print_success(f"{cmd} command available")
            else:
                print_error(f"{cmd} command not found")
        
        return True
    
    def test_installer_scripts(self):
        """Test if installer scripts are present and syntactically correct"""
        print_header("Testing Installer Scripts")
        
        scripts_to_test = [
            'installer_ui.py',
            'install_fully_automated.sh',
            'launch_installer.sh',
            'system_status.sh',
            'quick_capture.sh'
        ]
        
        all_good = True
        
        for script in scripts_to_test:
            script_path = self.script_dir / script
            
            if not script_path.exists():
                print_error(f"{script} not found")
                all_good = False
                continue
            
            if script.endswith('.py'):
                # Test Python syntax
                try:
                    subprocess.run([sys.executable, '-m', 'py_compile', str(script_path)], 
                                 check=True, capture_output=True)
                    print_success(f"{script} - Python syntax OK")
                except subprocess.CalledProcessError:
                    print_error(f"{script} - Python syntax error")
                    all_good = False
            
            elif script.endswith('.sh'):
                # Test bash syntax
                try:
                    subprocess.run(['bash', '-n', str(script_path)], 
                                 check=True, capture_output=True)
                    print_success(f"{script} - Bash syntax OK")
                except subprocess.CalledProcessError:
                    print_error(f"{script} - Bash syntax error")
                    all_good = False
                except FileNotFoundError:
                    print_warning(f"{script} - Cannot test (bash not available)")
        
        return all_good
    
    def test_gui_launcher(self):
        """Test if GUI can be launched"""
        print_header("Testing GUI Launcher")
        
        try:
            # Try to import and create the GUI (but don't show it)
            sys.path.insert(0, str(self.script_dir))
            
            # Test if we can create the GUI components
            import tkinter as tk
            from installer_ui import Xbox360InstallerGUI
            
            # Create a test root window (but don't show it)
            root = tk.Tk()
            root.withdraw()  # Hide the window
            
            # Try to create the GUI object
            app = Xbox360InstallerGUI(root)
            print_success("GUI components can be created")
            
            # Destroy test window
            root.destroy()
            
            return True
            
        except Exception as e:
            print_error(f"GUI creation failed: {e}")
            return False
    
    def create_mock_environment(self):
        """Create mock files for testing"""
        print_header("Creating Mock Test Environment")
        
        # Create temporary mock files
        mock_files = {
            '/tmp/mock_lsusb_output': 'Bus 001 Device 003: ID 045e:02a8 Microsoft Corp. Xbox 360 Wireless Adapter\n',
            '/tmp/mock_cpuinfo': 'Hardware\t: BCM2711\nModel\t\t: Raspberry Pi 4 Model B Rev 1.1\n'
        }
        
        for file_path, content in mock_files.items():
            try:
                with open(file_path, 'w') as f:
                    f.write(content)
                print_success(f"Created mock file: {file_path}")
            except Exception as e:
                print_warning(f"Could not create {file_path}: {e}")
        
        print_info("Mock environment created for testing")
        return True
    
    def run_basic_tests(self):
        """Run basic functionality tests"""
        print_header("Running Basic Functionality Tests")
        
        test_passed = 0
        total_tests = 0
        
        # Test 1: Can we execute Python scripts?
        total_tests += 1
        try:
            result = subprocess.run([sys.executable, '-c', 'print("Python execution test")'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                print_success("Python script execution")
                test_passed += 1
            else:
                print_error("Python script execution failed")
        except Exception as e:
            print_error(f"Python execution test failed: {e}")
        
        # Test 2: Can we import our modules?
        total_tests += 1
        try:
            import installer_ui
            print_success("Module import test")
            test_passed += 1
        except Exception as e:
            print_error(f"Module import failed: {e}")
        
        # Test 3: Can we create temporary files?
        total_tests += 1
        try:
            with tempfile.NamedTemporaryFile(mode='w', delete=True) as f:
                f.write("test")
                f.flush()
                print_success("File system access")
                test_passed += 1
        except Exception as e:
            print_error(f"File system test failed: {e}")
        
        print_info(f"Basic tests: {test_passed}/{total_tests} passed")
        return test_passed == total_tests
    
    def show_recommendations(self):
        """Show recommendations based on test results"""
        print_header("Recommendations")
        
        system = platform.system()
        
        if system == "Windows":
            print_info("For Windows users:")
            print("  1. Use WSL for best compatibility")
            print("  2. Install Docker Desktop for containerized testing")
            print("  3. Use TEST_SIMPLE.bat for quick Docker testing")
        
        elif system == "Linux":
            print_info("For Linux users:")
            print("  1. Install missing dependencies with apt-get")
            print("  2. Use ./launch_installer.sh for GUI installation")
            print("  3. Use sudo for full installation functionality")
        
        elif system == "Darwin":
            print_info("For macOS users:")
            print("  1. Install dependencies with brew")
            print("  2. Use Docker for best emulation experience")
            print("  3. VNC access may be needed for GUI testing")
        
        print()
        print_info("Next steps:")
        print("  1. Fix any failed tests above")
        print("  2. Try: python3 installer_ui.py (for GUI)")
        print("  3. Try: ./test_simple.sh (for Docker testing)")
        print("  4. Check README.md for detailed instructions")
    
    def run_all_tests(self):
        """Run all tests"""
        print_header("Xbox 360 WiFi Module Emulator - Local Testing")
        
        tests = [
            ("Python Requirements", self.check_python_requirements),
            ("System Requirements", self.check_system_requirements),
            ("Installer Scripts", self.test_installer_scripts),
            ("GUI Components", self.test_gui_launcher),
            ("Mock Environment", self.create_mock_environment),
            ("Basic Functionality", self.run_basic_tests)
        ]
        
        results = []
        for test_name, test_func in tests:
            try:
                result = test_func()
                results.append((test_name, result))
            except Exception as e:
                print_error(f"{test_name} test crashed: {e}")
                results.append((test_name, False))
        
        # Show summary
        print_header("Test Summary")
        passed = 0
        for test_name, result in results:
            if result:
                print_success(f"{test_name}")
                passed += 1
            else:
                print_error(f"{test_name}")
        
        print(f"\nOverall: {passed}/{len(results)} tests passed")
        
        if passed == len(results):
            print_success("All tests passed! System is ready for Xbox 360 emulator installation.")
        else:
            print_warning("Some tests failed. Check the output above for details.")
        
        self.show_recommendations()

def main():
    """Main entry point"""
    tester = Xbox360LocalTester()
    tester.run_all_tests()

if __name__ == "__main__":
    main()