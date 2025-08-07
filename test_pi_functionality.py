#!/usr/bin/env python3
"""
Comprehensive Pi Test Script for Xbox 360 WiFi Module Emulator
Run this on Raspberry Pi 4 to test all functionality and generate detailed logs
"""

import os
import sys
import time
import json
import logging
import subprocess
import traceback
from datetime import datetime
from pathlib import Path

# Test script version
SCRIPT_VERSION = "1.0.0"
TEST_LOG_FILE = f"pi_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

def setup_logging():
    """Setup comprehensive logging"""
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(levelname)s - [%(name)s] - %(message)s',
        handlers=[
            logging.FileHandler(TEST_LOG_FILE),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)

def run_command(cmd, description="", timeout=30):
    """Run command and return results with detailed logging"""
    logger = logging.getLogger(__name__)
    
    logger.info(f"🔧 {description}")
    logger.info(f"Command: {cmd}")
    
    try:
        start_time = time.time()
        result = subprocess.run(
            cmd, 
            shell=True, 
            capture_output=True, 
            text=True, 
            timeout=timeout
        )
        end_time = time.time()
        
        success = result.returncode == 0
        duration = end_time - start_time
        
        logger.info(f"Duration: {duration:.2f}s")
        logger.info(f"Exit code: {result.returncode}")
        
        if result.stdout.strip():
            logger.info(f"STDOUT:\n{result.stdout}")
        
        if result.stderr.strip():
            logger.warning(f"STDERR:\n{result.stderr}")
        
        if success:
            logger.info("✅ Command succeeded")
        else:
            logger.error("❌ Command failed")
        
        return {
            'success': success,
            'stdout': result.stdout,
            'stderr': result.stderr,
            'returncode': result.returncode,
            'duration': duration
        }
        
    except subprocess.TimeoutExpired:
        logger.error(f"⏰ Command timed out after {timeout}s")
        return {
            'success': False,
            'stdout': '',
            'stderr': f'Command timeout after {timeout}s',
            'returncode': -1,
            'duration': timeout
        }
    except Exception as e:
        logger.error(f"💥 Command exception: {e}")
        return {
            'success': False,
            'stdout': '',
            'stderr': str(e),
            'returncode': -2,
            'duration': 0
        }

def test_system_info():
    """Test 1: Gather system information"""
    logger = logging.getLogger(__name__)
    logger.info("=" * 60)
    logger.info("TEST 1: SYSTEM INFORMATION")
    logger.info("=" * 60)
    
    tests = [
        ("uname -a", "Get kernel information"),
        ("cat /proc/cpuinfo | grep 'Raspberry Pi'", "Check Pi hardware"),
        ("cat /etc/os-release", "Get OS information"),
        ("python3 --version", "Check Python version"),
        ("lsusb", "List USB devices"),
        ("lsmod | grep -E '(dwc2|libcomposite|configfs|g_ether)'", "Check USB modules"),
        ("mount | grep -E '(configfs|debugfs)'", "Check filesystem mounts"),
        ("ls -la /sys/class/udc/", "Check USB Device Controllers"),
        ("ls -la /dev/raw-gadget", "Check raw-gadget device"),
        ("ip link show", "Show network interfaces")
    ]
    
    results = {}
    for cmd, desc in tests:
        results[desc] = run_command(cmd, desc)
    
    return results

def test_usb_diagnostic():
    """Test 2: Run USB system diagnostic"""
    logger = logging.getLogger(__name__)
    logger.info("=" * 60)
    logger.info("TEST 2: USB SYSTEM DIAGNOSTIC")
    logger.info("=" * 60)
    
    if not Path("diagnose_usb.py").exists():
        logger.error("❌ diagnose_usb.py not found")
        return {'success': False, 'error': 'diagnose_usb.py missing'}
    
    result = run_command("python3 diagnose_usb.py", "Run USB system diagnostic", timeout=60)
    return result

def test_xbox_gadget():
    """Test 3: Test Xbox 360 gadget functionality"""
    logger = logging.getLogger(__name__)
    logger.info("=" * 60)
    logger.info("TEST 3: XBOX 360 GADGET FUNCTIONALITY")
    logger.info("=" * 60)
    
    # Add src to path and test Xbox gadget
    sys.path.insert(0, str(Path.cwd() / "src"))
    
    try:
        from xbox360_gadget import Xbox360Gadget
        
        logger.info("🎮 Testing Xbox 360 gadget creation...")
        gadget = Xbox360Gadget("test-xbox360")
        
        # Test gadget setup
        logger.info("🔧 Testing complete gadget setup...")
        success = gadget.setup_complete_gadget(create_network=True, create_functionfs=False)
        
        if success:
            logger.info("✅ Xbox 360 gadget setup successful")
            
            # Check if usb0 interface was created
            time.sleep(3)  # Wait for interface creation
            usb0_check = run_command("ip link show usb0", "Check usb0 interface creation")
            
            # Get gadget status
            status = gadget.get_status()
            logger.info(f"Gadget status: {json.dumps(status, indent=2)}")
            
            # Deactivate gadget
            logger.info("🔧 Deactivating gadget...")
            gadget.deactivate_gadget()
            
            return {
                'success': True,
                'gadget_setup': success,
                'usb0_created': usb0_check['success'],
                'status': status
            }
        else:
            logger.error("❌ Xbox 360 gadget setup failed")
            return {'success': False, 'error': 'Gadget setup failed'}
            
    except Exception as e:
        logger.error(f"💥 Xbox gadget test failed: {e}")
        logger.error(traceback.format_exc())
        return {'success': False, 'error': str(e), 'traceback': traceback.format_exc()}

def test_usb_passthrough():
    """Test 4: Test USB passthrough functionality"""
    logger = logging.getLogger(__name__)
    logger.info("=" * 60)
    logger.info("TEST 4: USB PASSTHROUGH FUNCTIONALITY")
    logger.info("=" * 60)
    
    try:
        from usb_passthrough_manager import USBPassthroughManager
        
        logger.info("🔌 Testing USB passthrough manager...")
        manager = USBPassthroughManager()
        
        # Test Xbox device scanning
        logger.info("🔍 Scanning for Xbox devices...")
        devices = manager.scan_xbox_devices()
        logger.info(f"Found {len(devices)} Xbox devices: {json.dumps(devices, indent=2)}")
        
        # Test USB capture setup (without actually starting capture)
        logger.info("📊 Testing capture configuration...")
        capture_config = {
            'duration': 10,
            'output_format': 'pcap',
            'filter_xbox_only': True
        }
        
        # Test session management
        session_id = manager.create_capture_session(capture_config)
        logger.info(f"Created capture session: {session_id}")
        
        return {
            'success': True,
            'devices_found': len(devices),
            'devices': devices,
            'session_created': session_id is not None
        }
        
    except Exception as e:
        logger.error(f"💥 USB passthrough test failed: {e}")
        logger.error(traceback.format_exc())
        return {'success': False, 'error': str(e), 'traceback': traceback.format_exc()}

def test_usb_capture():
    """Test 5: Test USB capture functionality"""
    logger = logging.getLogger(__name__)
    logger.info("=" * 60)
    logger.info("TEST 5: USB CAPTURE FUNCTIONALITY")
    logger.info("=" * 60)
    
    try:
        from xbox360_capture_analyzer import Xbox360CaptureAnalyzer
        
        logger.info("📊 Testing USB capture analyzer...")
        analyzer = Xbox360CaptureAnalyzer()
        
        # Test capture setup
        logger.info("🔧 Testing capture configuration...")
        config = analyzer.get_default_config()
        logger.info(f"Default config: {json.dumps(config, indent=2)}")
        
        # Test usbmon availability
        usbmon_check = run_command("ls -la /sys/kernel/debug/usb/usbmon/", "Check usbmon availability")
        
        return {
            'success': True,
            'analyzer_created': True,
            'usbmon_available': usbmon_check['success'],
            'default_config': config
        }
        
    except Exception as e:
        logger.error(f"💥 USB capture test failed: {e}")
        logger.error(traceback.format_exc())
        return {'success': False, 'error': str(e), 'traceback': traceback.format_exc()}

def test_build_tools():
    """Test 6: Test USB-Sniffify build"""
    logger = logging.getLogger(__name__)
    logger.info("=" * 60)
    logger.info("TEST 6: USB-SNIFFIFY BUILD TEST")
    logger.info("=" * 60)
    
    build_dir = Path("usb_sniffing_tools/usb-sniffify/build")
    
    if not Path("usb_sniffing_tools/usb-sniffify").exists():
        logger.error("❌ USB-Sniffify directory not found")
        return {'success': False, 'error': 'USB-Sniffify directory missing'}
    
    # Ensure build directory exists
    build_dir.mkdir(parents=True, exist_ok=True)
    
    # Test CMake configuration
    cmake_result = run_command(
        "cd usb_sniffing_tools/usb-sniffify/build && cmake ..",
        "Configure build with CMake",
        timeout=60
    )
    
    if not cmake_result['success']:
        return {'success': False, 'cmake_failed': True, 'cmake_result': cmake_result}
    
    # Test build
    make_result = run_command(
        "cd usb_sniffing_tools/usb-sniffify/build && make -j$(nproc)",
        "Build USB-Sniffify tools",
        timeout=120
    )
    
    # Check built executables
    executables = []
    for exe in ['passthrough', 'passthrough-c', 'raw-gadget-passthrough', 'libusbhax', 'hid']:
        exe_path = build_dir / exe
        if exe_path.exists():
            executables.append(exe)
            logger.info(f"✅ Built executable: {exe}")
        else:
            logger.warning(f"❌ Missing executable: {exe}")
    
    return {
        'success': make_result['success'],
        'cmake_result': cmake_result,
        'make_result': make_result,
        'executables_built': executables,
        'total_executables': len(executables)
    }

def test_gui_functionality():
    """Test 7: Test GUI functionality (basic import test)"""
    logger = logging.getLogger(__name__)
    logger.info("=" * 60)
    logger.info("TEST 7: GUI FUNCTIONALITY TEST")
    logger.info("=" * 60)
    
    try:
        # Test if we can import tkinter
        import tkinter as tk
        logger.info("✅ tkinter import successful")
        
        # Test basic GUI creation (non-interactive)
        logger.info("🖥️ Testing basic GUI creation...")
        root = tk.Tk()
        root.withdraw()  # Hide the window
        
        # Test if we can import the installer GUI
        if Path("installer.py").exists():
            # Import test only - don't actually run GUI
            logger.info("📋 Testing installer GUI import...")
            
            # This is tricky - we need to test without actually running the GUI
            # Let's just check if the file can be parsed
            with open("installer.py", "r") as f:
                content = f.read()
                if "XboxInstallerGUI" in content:
                    logger.info("✅ XboxInstallerGUI class found in installer.py")
                    gui_found = True
                else:
                    logger.warning("❌ XboxInstallerGUI class not found")
                    gui_found = False
        else:
            logger.error("❌ installer.py not found")
            gui_found = False
        
        root.destroy()
        
        return {
            'success': True,
            'tkinter_available': True,
            'gui_class_found': gui_found
        }
        
    except Exception as e:
        logger.error(f"💥 GUI test failed: {e}")
        logger.error(traceback.format_exc())
        return {'success': False, 'error': str(e), 'traceback': traceback.format_exc()}

def generate_summary_report(test_results):
    """Generate comprehensive summary report"""
    logger = logging.getLogger(__name__)
    logger.info("=" * 80)
    logger.info("COMPREHENSIVE TEST SUMMARY REPORT")
    logger.info("=" * 80)
    
    total_tests = len(test_results)
    passed_tests = sum(1 for result in test_results.values() if result and result.get('success', False))
    
    logger.info(f"📊 Test Results: {passed_tests}/{total_tests} tests passed")
    logger.info(f"📅 Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"📝 Script Version: {SCRIPT_VERSION}")
    logger.info(f"📄 Log File: {TEST_LOG_FILE}")
    
    # Individual test results
    for test_name, result in test_results.items():
        if result and result.get('success', False):
            logger.info(f"✅ {test_name}: PASSED")
        else:
            logger.error(f"❌ {test_name}: FAILED")
            if result and 'error' in result:
                logger.error(f"   Error: {result['error']}")
    
    logger.info("=" * 80)
    
    # Overall status
    if passed_tests == total_tests:
        logger.info("🎉 ALL TESTS PASSED - System is fully functional!")
    elif passed_tests >= total_tests * 0.7:
        logger.warning(f"⚠️ MOSTLY WORKING - {passed_tests}/{total_tests} tests passed")
    else:
        logger.error(f"❌ CRITICAL ISSUES - Only {passed_tests}/{total_tests} tests passed")
    
    logger.info("=" * 80)
    
    return {
        'total_tests': total_tests,
        'passed_tests': passed_tests,
        'success_rate': passed_tests / total_tests,
        'overall_status': 'PASS' if passed_tests == total_tests else 'FAIL'
    }

def main():
    """Main test execution"""
    logger = setup_logging()
    
    logger.info("🚀 Starting comprehensive Pi functionality test...")
    logger.info(f"📝 Logging to: {TEST_LOG_FILE}")
    logger.info(f"📅 Test started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"📍 Working directory: {os.getcwd()}")
    
    # Check if we're running on Pi
    try:
        with open('/proc/cpuinfo', 'r') as f:
            if 'Raspberry Pi' not in f.read():
                logger.warning("⚠️ Not running on Raspberry Pi - some tests may fail")
    except:
        logger.warning("⚠️ Cannot detect hardware - assuming Pi environment")
    
    # Run all tests
    test_results = {}
    
    try:
        test_results['System Information'] = test_system_info()
        test_results['USB Diagnostic'] = test_usb_diagnostic()
        test_results['Xbox Gadget'] = test_xbox_gadget()
        test_results['USB Passthrough'] = test_usb_passthrough()
        test_results['USB Capture'] = test_usb_capture()
        test_results['Build Tools'] = test_build_tools()
        test_results['GUI Functionality'] = test_gui_functionality()
        
    except KeyboardInterrupt:
        logger.warning("⚠️ Test interrupted by user")
    except Exception as e:
        logger.error(f"💥 Test execution failed: {e}")
        logger.error(traceback.format_exc())
    
    # Generate summary report
    summary = generate_summary_report(test_results)
    
    logger.info(f"✅ Test completed. Results saved to: {TEST_LOG_FILE}")
    
    # Save results to JSON for easy parsing
    json_file = TEST_LOG_FILE.replace('.log', '.json')
    try:
        with open(json_file, 'w') as f:
            json.dump({
                'summary': summary,
                'test_results': test_results,
                'timestamp': datetime.now().isoformat(),
                'script_version': SCRIPT_VERSION
            }, f, indent=2, default=str)
        logger.info(f"📊 JSON results saved to: {json_file}")
    except Exception as e:
        logger.error(f"Failed to save JSON results: {e}")
    
    return summary['overall_status'] == 'PASS'

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"CRITICAL ERROR: {e}")
        traceback.print_exc()
        sys.exit(2)