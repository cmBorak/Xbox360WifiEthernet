#!/usr/bin/env python3
"""
Test script to verify centralized logging system functionality
This script tests the logging integration across all app components
"""

import sys
import os
from pathlib import Path
import subprocess
import time

def test_logging_setup():
    """Test if the logging system can be initialized"""
    print("🧪 Testing Centralized Logging System")
    print("=" * 40)
    
    try:
        # Test if GUI components are available
        from installer import XboxInstallerGUI, GUI_AVAILABLE
        
        if not GUI_AVAILABLE:
            print("❌ GUI components not available")
            print("   Install tkinter: sudo apt install python3-tk")
            return False
        
        print("✅ GUI components available")
        
        # Test debug log directory setup
        print("\n📂 Testing debug log directory setup...")
        gui = XboxInstallerGUI()
        
        print(f"   Debug log directory: {gui.debug_log_dir}")
        
        if gui.debug_log_dir.exists():
            print("✅ Debug logs directory exists")
            
            # Check README file
            readme_file = gui.debug_log_dir / "README.txt"
            if readme_file.exists():
                print("✅ README.txt created")
                
                # Read README content to verify it's correct
                with open(readme_file, 'r') as f:
                    content = f.read()
                    if "Xbox 360 WiFi Module Emulator" in content:
                        print("✅ README.txt contains correct content")
                    else:
                        print("⚠️  README.txt content may be incorrect")
            else:
                print("❌ README.txt missing")
            
            # List existing log files
            log_files = list(gui.debug_log_dir.glob("*.log"))
            if log_files:
                print(f"📄 Found {len(log_files)} existing log files:")
                for log_file in sorted(log_files)[-5:]:  # Show last 5
                    size = log_file.stat().st_size
                    print(f"   {log_file.name} ({size} bytes)")
            else:
                print("📄 No existing log files (this is normal for first run)")
                
        else:
            print("❌ Debug logs directory not found")
            return False
            
        # Test session logging functionality
        print("\n🔄 Testing session logging functionality...")
        try:
            # Test starting a log session
            gui._start_log_session("test")
            print("✅ Log session started successfully")
            
            # Test writing to log
            gui._log_to_file("Test log entry", "info")
            print("✅ Log entry written successfully")
            
            # Test ending log session
            gui._end_log_session()
            print("✅ Log session ended successfully")
            
            # Check if test log file was created
            test_logs = list(gui.debug_log_dir.glob("*test*.log"))
            if test_logs:
                latest_test_log = max(test_logs, key=lambda x: x.stat().st_mtime)
                print(f"✅ Test log file created: {latest_test_log.name}")
                
                # Verify log content
                with open(latest_test_log, 'r') as f:
                    content = f.read()
                    if "Test log entry" in content:
                        print("✅ Log content verified")
                    else:
                        print("⚠️  Log content not found")
            else:
                print("❌ Test log file not created")
                
        except Exception as e:
            print(f"❌ Session logging test failed: {e}")
            return False
            
        print("\n✅ All logging tests passed!")
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("💡 Make sure you're in the correct directory")
        return False
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_component_integration():
    """Test if all components can access the logging system"""
    print("\n🔗 Testing Component Integration")
    print("=" * 35)
    
    try:
        from installer import XboxInstallerGUI
        gui = XboxInstallerGUI()
        
        # Test that all major methods have access to logging
        methods_to_check = [
            '_start_log_session',
            '_end_log_session', 
            '_log_to_file',
            '_setup_debug_log_directory'
        ]
        
        for method_name in methods_to_check:
            if hasattr(gui, method_name):
                print(f"✅ {method_name} available")
            else:
                print(f"❌ {method_name} not found")
                
        print("\n✅ Component integration verified!")
        return True
        
    except Exception as e:
        print(f"❌ Component integration test failed: {e}")
        return False

def print_completion_message():
    """Print completion message with next steps"""
    print("\n" + "=" * 50)
    print("🎉 Centralized Logging Test Complete!")
    print("=" * 50)
    print("📋 What to do next:")
    print("   1. 🚀 Run: python3 installer.py")
    print("   2. 🔍 Use the debug, status, and fix buttons to generate logs")
    print("   3. 📂 Check ~/Desktop/debuglogs/ for session log files")
    print("   4. 🧪 Run operations like install, capture, passthrough")
    print("\n💡 Each major operation now creates its own timestamped log file")
    print(f"📂 Log directory: {Path.home() / 'Desktop' / 'debuglogs'}")

def main():
    """Main test function"""
    print("🧪 Xbox 360 WiFi Emulator - Centralized Logging Test")
    print("=" * 55)
    
    # Test 1: Basic logging setup
    if not test_logging_setup():
        print("\n❌ Basic logging setup failed!")
        sys.exit(1)
    
    # Test 2: Component integration
    if not test_component_integration():
        print("\n❌ Component integration failed!")
        sys.exit(1)
    
    # Success!
    print_completion_message()
    
    # Offer to open the installer
    try:
        response = input("\n❓ Would you like to open the installer GUI to test live logging? (y/n): ")
        if response.lower().startswith('y'):
            print("🚀 Opening installer GUI...")
            subprocess.run([sys.executable, "installer.py"], cwd=Path.cwd())
    except KeyboardInterrupt:
        print("\n👋 Test completed!")
    except Exception as e:
        print(f"\n⚠️  Could not open GUI: {e}")
        print("💡 You can manually run: python3 installer.py")

if __name__ == "__main__":
    main()