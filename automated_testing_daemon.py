#!/usr/bin/env python3
"""
Automated Testing Daemon for Xbox 360 Emulation Project
Continuous self-testing, debugging, and automatic error recovery
Designed specifically for Raspberry Pi 4 hardware
"""

import asyncio
import json
import logging
import time
import subprocess
import sys
from pathlib import Path
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Any
import threading
import schedule

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

try:
    from xbox360_emulator import Xbox360Emulator
    from xbox360_gadget import Xbox360Gadget
    from network_bridge import NetworkBridge
except ImportError as e:
    print(f"Warning: Could not import core modules: {e}")


@dataclass
class TestResult:
    """Test result data structure"""
    test_name: str
    status: str  # 'pass', 'fail', 'error'
    duration: float
    error_message: Optional[str] = None
    timestamp: datetime = None
    auto_fixed: bool = False
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


class AutomatedTestingDaemon:
    """
    Automated Testing Daemon that continuously monitors and tests
    the Xbox 360 emulation system on Raspberry Pi 4
    """
    
    def __init__(self, config_file: str = "test_daemon_config.json"):
        self.config_file = Path(config_file)
        self.config = self._load_config()
        self.results_dir = Path(self.config['results_directory'])
        self.results_dir.mkdir(exist_ok=True)
        
        # Setup logging
        self._setup_logging()
        
        # Test tracking
        self.test_results: List[TestResult] = []
        self.last_full_test = None
        self.system_health = {"status": "unknown", "last_check": None}
        
        # Error recovery tracking
        self.error_patterns = self._load_error_patterns()
        self.fix_attempts = {}
        
        # System components
        self.emulator = None
        self.running = False
        
        self.logger.info("Automated Testing Daemon initialized")
    
    def _load_config(self) -> Dict[str, Any]:
        """Load daemon configuration"""
        default_config = {
            "test_interval_minutes": 15,
            "full_test_interval_hours": 4,
            "health_check_interval_minutes": 5,
            "max_fix_attempts": 3,
            "results_directory": "./test-results",
            "log_level": "INFO",
            "enable_auto_recovery": True,
            "enable_hardware_tests": True,
            "enable_network_tests": True,
            "enable_usb_tests": True,
            "notification_webhook": None,
            "test_types": {
                "quick_smoke": ["system_health", "basic_functionality"],
                "comprehensive": ["unit_tests", "integration_tests", "hardware_tests"],
                "critical_path": ["usb_gadget_activation", "network_bridge", "xbox_protocol"]
            }
        }
        
        if self.config_file.exists():
            try:
                with open(self.config_file) as f:
                    config = json.load(f)
                default_config.update(config)
            except Exception as e:
                print(f"Error loading config: {e}, using defaults")
        else:
            # Create default config file
            with open(self.config_file, 'w') as f:
                json.dump(default_config, f, indent=2)
            print(f"Created default config: {self.config_file}")
        
        return default_config
    
    def _setup_logging(self):
        """Setup logging for the daemon"""
        log_file = self.results_dir / "test_daemon.log"
        
        logging.basicConfig(
            level=getattr(logging, self.config['log_level']),
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def _load_error_patterns(self) -> Dict[str, Dict]:
        """Load error patterns and their automatic fixes"""
        return {
            "usb_gadget_activation_failed": {
                "pattern": "Failed to activate USB gadget",
                "fixes": [
                    "sudo modprobe -r dwc2",
                    "sudo modprobe dwc2",
                    "sudo modprobe -r libcomposite", 
                    "sudo modprobe libcomposite"
                ],
                "test_after_fix": "test_usb_gadget_basic"
            },
            "network_bridge_creation_failed": {
                "pattern": "Failed to create bridge",
                "fixes": [
                    "sudo ip link delete br0",
                    "sudo systemctl restart networking",
                    "sleep 5"
                ],
                "test_after_fix": "test_network_bridge_basic"
            },
            "kernel_module_load_failed": {
                "pattern": "Failed to load kernel modules",
                "fixes": [
                    "sudo modprobe -r dwc2 libcomposite",
                    "sudo modprobe libcomposite",
                    "sudo modprobe dwc2",
                    "echo 'dwc2' | sudo tee -a /etc/modules",
                    "echo 'libcomposite' | sudo tee -a /etc/modules"
                ],
                "test_after_fix": "test_kernel_modules"
            },
            "udc_not_found": {
                "pattern": "No USB Device Controller found",
                "fixes": [
                    "echo 'dtoverlay=dwc2' | sudo tee -a /boot/config.txt",
                    "sudo systemctl reboot"  # This will be handled specially
                ],
                "test_after_fix": "test_udc_availability"
            },
            "permission_denied": {
                "pattern": "PermissionError|Permission denied",
                "fixes": [
                    "sudo chown -R pi:pi /sys/kernel/config/usb_gadget/ || true",
                    "sudo chmod -R 755 /sys/kernel/config/usb_gadget/ || true"
                ],
                "test_after_fix": "test_permissions"
            }
        }
    
    async def start_daemon(self):
        """Start the automated testing daemon"""
        self.running = True
        self.logger.info("Starting Automated Testing Daemon")
        
        # Schedule different types of tests
        schedule.every(self.config['health_check_interval_minutes']).minutes.do(
            self._schedule_health_check
        )
        schedule.every(self.config['test_interval_minutes']).minutes.do(
            self._schedule_quick_test
        )
        schedule.every(self.config['full_test_interval_hours']).hours.do(
            self._schedule_comprehensive_test
        )
        
        # Run initial system check
        await self.run_system_health_check()
        
        # Main daemon loop
        try:
            while self.running:
                schedule.run_pending()
                await asyncio.sleep(30)  # Check every 30 seconds
                
                # Check for any pending error recovery
                await self._check_and_recover_errors()
                
        except KeyboardInterrupt:
            self.logger.info("Daemon shutdown requested")
        except Exception as e:
            self.logger.error(f"Daemon error: {e}")
        finally:
            await self.stop_daemon()
    
    def _schedule_health_check(self):
        """Schedule health check to run"""
        asyncio.create_task(self.run_system_health_check())
    
    def _schedule_quick_test(self):
        """Schedule quick test to run"""
        asyncio.create_task(self.run_quick_tests())
    
    def _schedule_comprehensive_test(self):
        """Schedule comprehensive test to run"""
        asyncio.create_task(self.run_comprehensive_tests())
    
    async def run_system_health_check(self):
        """Run system health check"""
        self.logger.info("Running system health check")
        start_time = time.time()
        
        health_tests = [
            self._check_raspberry_pi_hardware,
            self._check_kernel_modules,
            self._check_usb_device_controller,
            self._check_network_interfaces,
            self._check_system_resources,
            self._check_permissions
        ]
        
        health_results = {}
        overall_healthy = True
        
        for test_func in health_tests:
            try:
                test_name = test_func.__name__
                result = await test_func()
                health_results[test_name] = result
                if not result['healthy']:
                    overall_healthy = False
                    self.logger.warning(f"Health check failed: {test_name} - {result.get('error', 'Unknown error')}")
            except Exception as e:
                health_results[test_func.__name__] = {
                    'healthy': False,
                    'error': str(e)
                }
                overall_healthy = False
                self.logger.error(f"Health check error in {test_func.__name__}: {e}")
        
        duration = time.time() - start_time
        
        self.system_health = {
            "status": "healthy" if overall_healthy else "unhealthy",
            "last_check": datetime.now(),
            "details": health_results,
            "duration": duration
        }
        
        # Save health check results
        health_file = self.results_dir / f"health_check_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(health_file, 'w') as f:
            json.dump(self.system_health, f, indent=2, default=str)
        
        # Trigger automatic recovery if unhealthy
        if not overall_healthy:
            await self._attempt_automatic_recovery(health_results)
        
        self.logger.info(f"Health check completed in {duration:.2f}s - Status: {self.system_health['status']}")
    
    async def _check_raspberry_pi_hardware(self) -> Dict[str, Any]:
        """Check Raspberry Pi 4 hardware"""
        try:
            with open('/proc/cpuinfo', 'r') as f:
                cpu_info = f.read()
            
            if 'Raspberry Pi 4' not in cpu_info:
                return {'healthy': False, 'error': 'Not running on Raspberry Pi 4'}
            
            # Check temperature
            with open('/sys/class/thermal/thermal_zone0/temp', 'r') as f:
                temp = int(f.read().strip()) / 1000
            
            if temp > 80:
                return {'healthy': False, 'error': f'CPU temperature too high: {temp}°C'}
            
            return {'healthy': True, 'temperature': temp, 'model': 'Raspberry Pi 4'}
            
        except Exception as e:
            return {'healthy': False, 'error': str(e)}
    
    async def _check_kernel_modules(self) -> Dict[str, Any]:
        """Check required kernel modules"""
        try:
            result = subprocess.run(['lsmod'], capture_output=True, text=True, check=True)
            modules = result.stdout
            
            required_modules = ['libcomposite', 'dwc2']
            missing_modules = []
            
            for module in required_modules:
                if module not in modules:
                    missing_modules.append(module)
            
            if missing_modules:
                return {
                    'healthy': False,
                    'error': f'Missing kernel modules: {missing_modules}'
                }
            
            return {'healthy': True, 'modules_loaded': required_modules}
            
        except Exception as e:
            return {'healthy': False, 'error': str(e)}
    
    async def _check_usb_device_controller(self) -> Dict[str, Any]:
        """Check USB Device Controller availability"""
        try:
            import os
            udc_path = '/sys/class/udc'
            
            if not os.path.exists(udc_path):
                return {'healthy': False, 'error': 'UDC path does not exist'}
            
            udcs = os.listdir(udc_path)
            
            if not udcs:
                return {'healthy': False, 'error': 'No USB Device Controllers found'}
            
            return {'healthy': True, 'udcs': udcs}
            
        except Exception as e:
            return {'healthy': False, 'error': str(e)}
    
    async def _check_network_interfaces(self) -> Dict[str, Any]:
        """Check network interfaces"""
        try:
            result = subprocess.run(['ip', 'link', 'show'], capture_output=True, text=True, check=True)
            interfaces = []
            
            for line in result.stdout.split('\n'):
                if ':' in line and 'LOOPBACK' not in line:
                    interface = line.split(':')[1].strip().split('@')[0]
                    if interface and interface != 'lo':
                        interfaces.append(interface)
            
            if not interfaces:
                return {'healthy': False, 'error': 'No network interfaces found'}
            
            return {'healthy': True, 'interfaces': interfaces}
            
        except Exception as e:
            return {'healthy': False, 'error': str(e)}
    
    async def _check_system_resources(self) -> Dict[str, Any]:
        """Check system resources (memory, disk, CPU)"""
        try:
            # Check memory
            with open('/proc/meminfo', 'r') as f:
                mem_info = f.read()
            
            mem_total = int([line for line in mem_info.split('\n') if 'MemTotal' in line][0].split()[1])
            mem_available = int([line for line in mem_info.split('\n') if 'MemAvailable' in line][0].split()[1])
            
            mem_usage = (mem_total - mem_available) / mem_total * 100
            
            # Check disk space
            result = subprocess.run(['df', '/'], capture_output=True, text=True, check=True)
            disk_line = result.stdout.split('\n')[1]
            disk_usage = int(disk_line.split()[4].rstrip('%'))
            
            warnings = []
            if mem_usage > 90:
                warnings.append(f'High memory usage: {mem_usage:.1f}%')
            if disk_usage > 90:
                warnings.append(f'High disk usage: {disk_usage}%')
            
            return {
                'healthy': len(warnings) == 0,
                'warnings': warnings,
                'memory_usage_percent': mem_usage,
                'disk_usage_percent': disk_usage
            }
            
        except Exception as e:
            return {'healthy': False, 'error': str(e)}
    
    async def _check_permissions(self) -> Dict[str, Any]:
        """Check file system permissions for USB gadget"""
        try:
            import os
            
            # Check configfs permissions
            configfs_path = '/sys/kernel/config'
            if not os.access(configfs_path, os.W_OK):
                return {'healthy': False, 'error': 'No write access to configfs'}
            
            # Check if we can create USB gadget directory
            test_path = f'{configfs_path}/usb_gadget/test_access'
            try:
                os.makedirs(test_path, exist_ok=True)
                os.rmdir(test_path)
            except PermissionError:
                return {'healthy': False, 'error': 'Cannot create USB gadget directories'}
            
            return {'healthy': True, 'configfs_writable': True}
            
        except Exception as e:
            return {'healthy': False, 'error': str(e)}
    
    async def run_quick_tests(self):
        """Run quick smoke tests"""
        self.logger.info("Running quick smoke tests")
        start_time = time.time()
        
        quick_tests = [
            self._test_usb_gadget_creation,
            self._test_network_interface_discovery,
            self._test_basic_emulator_initialization
        ]
        
        test_results = []
        
        for test_func in quick_tests:
            result = await self._run_single_test(test_func)
            test_results.append(result)
            self.test_results.append(result)
            
            # If test failed, attempt automatic recovery
            if result.status == 'fail':
                await self._attempt_test_recovery(result)
        
        duration = time.time() - start_time
        self.logger.info(f"Quick tests completed in {duration:.2f}s")
        
        # Save results
        await self._save_test_results(test_results, "quick_test")
    
    async def run_comprehensive_tests(self):
        """Run comprehensive test suite"""
        self.logger.info("Starting comprehensive test suite")
        start_time = time.time()
        
        # Run pytest with our test suite
        try:
            result = subprocess.run([
                'python3', '-m', 'pytest', 'tests/',
                '--json-report', f'--json-report-file={self.results_dir}/comprehensive_test_results.json',
                '--html', f'{self.results_dir}/comprehensive_test_report.html',
                '--self-contained-html',
                '-v'
            ], capture_output=True, text=True, cwd=Path(__file__).parent)
            
            duration = time.time() - start_time
            
            test_result = TestResult(
                test_name="comprehensive_test_suite",
                status="pass" if result.returncode == 0 else "fail",
                duration=duration,
                error_message=result.stderr if result.returncode != 0 else None
            )
            
            self.test_results.append(test_result)
            self.last_full_test = datetime.now()
            
            self.logger.info(f"Comprehensive tests completed in {duration:.2f}s - Status: {test_result.status}")
            
            if test_result.status == "fail":
                await self._analyze_test_failures()
            
        except Exception as e:
            self.logger.error(f"Error running comprehensive tests: {e}")
    
    async def _run_single_test(self, test_func) -> TestResult:
        """Run a single test function"""
        start_time = time.time()
        test_name = test_func.__name__
        
        try:
            result = await test_func()
            duration = time.time() - start_time
            
            if result:
                return TestResult(
                    test_name=test_name,
                    status="pass",
                    duration=duration
                )
            else:
                return TestResult(
                    test_name=test_name,
                    status="fail",
                    duration=duration,
                    error_message="Test returned False"
                )
                
        except Exception as e:
            duration = time.time() - start_time
            return TestResult(
                test_name=test_name,
                status="error",
                duration=duration,
                error_message=str(e)
            )
    
    async def _test_usb_gadget_creation(self) -> bool:
        """Test USB gadget creation"""
        try:
            gadget = Xbox360Gadget()
            # Test creation without activation
            return gadget._validate_hardware()
        except Exception as e:
            self.logger.error(f"USB gadget test failed: {e}")
            return False
    
    async def _test_network_interface_discovery(self) -> bool:
        """Test network interface discovery"""
        try:
            bridge = NetworkBridge()
            interfaces = bridge._discover_interfaces()
            return len(interfaces) > 0
        except Exception as e:
            self.logger.error(f"Network interface test failed: {e}")
            return False
    
    async def _test_basic_emulator_initialization(self) -> bool:
        """Test basic emulator initialization"""
        try:
            emulator = Xbox360Emulator()
            return emulator is not None
        except Exception as e:
            self.logger.error(f"Emulator initialization test failed: {e}")
            return False
    
    async def _attempt_automatic_recovery(self, health_results: Dict):
        """Attempt automatic recovery based on health check results"""
        if not self.config['enable_auto_recovery']:
            return
        
        self.logger.info("Attempting automatic recovery")
        
        for test_name, result in health_results.items():
            if not result['healthy']:
                error_msg = result.get('error', '')
                
                # Find matching error pattern
                for pattern_name, pattern_info in self.error_patterns.items():
                    if any(keyword in error_msg.lower() for keyword in pattern_info['pattern'].lower().split('|')):
                        await self._apply_error_fix(pattern_name, pattern_info)
                        break
    
    async def _apply_error_fix(self, pattern_name: str, pattern_info: Dict):
        """Apply automatic fix for detected error pattern"""
        if pattern_name in self.fix_attempts:
            if self.fix_attempts[pattern_name] >= self.config['max_fix_attempts']:
                self.logger.warning(f"Max fix attempts reached for {pattern_name}")
                return
        else:
            self.fix_attempts[pattern_name] = 0
        
        self.fix_attempts[pattern_name] += 1
        
        self.logger.info(f"Applying fix for {pattern_name} (attempt {self.fix_attempts[pattern_name]})")
        
        try:
            for fix_command in pattern_info['fixes']:
                if fix_command == "sudo systemctl reboot":
                    self.logger.info("Reboot required - scheduling for 30 seconds")
                    # Schedule reboot and exit daemon gracefully
                    subprocess.Popen(['sudo', 'shutdown', '-r', '+1'])
                    await self.stop_daemon()
                    return
                
                self.logger.info(f"Executing fix: {fix_command}")
                result = subprocess.run(fix_command.split(), capture_output=True, text=True)
                
                if result.returncode != 0:
                    self.logger.warning(f"Fix command failed: {fix_command} - {result.stderr}")
                else:
                    self.logger.info(f"Fix command succeeded: {fix_command}")
                
                # Wait between commands
                await asyncio.sleep(2)
            
            # Test the fix
            if 'test_after_fix' in pattern_info:
                self.logger.info(f"Testing fix for {pattern_name}")
                # Run verification test here
                await asyncio.sleep(5)  # Give system time to settle
                
        except Exception as e:
            self.logger.error(f"Error applying fix for {pattern_name}: {e}")
    
    async def _save_test_results(self, results: List[TestResult], test_type: str):
        """Save test results to file"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        results_file = self.results_dir / f"{test_type}_{timestamp}.json"
        
        results_data = {
            'test_type': test_type,
            'timestamp': timestamp,
            'results': [asdict(result) for result in results],
            'summary': {
                'total': len(results),
                'passed': len([r for r in results if r.status == 'pass']),
                'failed': len([r for r in results if r.status == 'fail']),
                'errors': len([r for r in results if r.status == 'error'])
            }
        }
        
        with open(results_file, 'w') as f:
            json.dump(results_data, f, indent=2, default=str)
    
    async def stop_daemon(self):
        """Stop the daemon gracefully"""
        self.logger.info("Stopping Automated Testing Daemon")
        self.running = False
        
        if self.emulator:
            try:
                await self.emulator.stop_emulation()
            except Exception as e:
                self.logger.error(f"Error stopping emulator: {e}")


def main():
    """Main entry point for the daemon"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Xbox 360 Emulation Automated Testing Daemon')
    parser.add_argument('--config', default='test_daemon_config.json',
                      help='Configuration file path')
    parser.add_argument('--daemon', action='store_true',
                      help='Run as background daemon')
    args = parser.parse_args()
    
    daemon = AutomatedTestingDaemon(args.config)
    
    if args.daemon:
        # Run as background daemon
        import daemon as daemon_context
        with daemon_context.DaemonContext():
            asyncio.run(daemon.start_daemon())
    else:
        # Run in foreground
        asyncio.run(daemon.start_daemon())


if __name__ == "__main__":
    main()