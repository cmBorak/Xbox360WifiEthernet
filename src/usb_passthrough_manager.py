#!/usr/bin/env python3
"""
Xbox 360 USB Passthrough Manager
Manages USB passthrough, capture, and emulation functionality
"""

import os
import sys
import time
import logging
import subprocess
import threading
import queue
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime

# Import our modules
from xbox360_gadget import Xbox360Gadget
from xbox_capture_analyzer import Xbox360CaptureAnalyzer

logger = logging.getLogger(__name__)

class USBPassthroughManager:
    """Manages USB passthrough and capture for Xbox 360 WiFi adapter"""
    
    def __init__(self, capture_dir: Optional[Path] = None):
        self.capture_dir = capture_dir or Path.home() / "Desktop" / "captures"
        self.capture_dir.mkdir(parents=True, exist_ok=True)
        
        self.gadget = Xbox360Gadget()
        self.analyzer = Xbox360CaptureAnalyzer()
        self.usbmon_process = None
        self.capture_active = False
        self.capture_file = None
        self.passthrough_active = False
        
        # USB device tracking
        self.target_devices = []
        self.device_monitor_thread = None
        self.monitor_queue = queue.Queue()
        
        logger.info(f"USB Passthrough Manager initialized - capture dir: {self.capture_dir}")
    
    def scan_xbox_devices(self) -> List[Dict]:
        """Scan for Xbox 360 wireless adapters on the system"""
        logger.info("Scanning for Xbox 360 wireless adapters...")
        
        devices = []
        try:
            # Use lsusb to find Xbox devices
            result = subprocess.run(['lsusb'], capture_output=True, text=True, check=True)
            
            for line in result.stdout.split('\n'):
                if '045e:' in line:  # Microsoft vendor ID
                    # Look for various Xbox 360 device IDs
                    xbox_device_ids = ['02a8', '0292', '028e', '02d9', '02dd']
                    for device_id in xbox_device_ids:
                        if device_id in line:
                            # Parse lsusb output: Bus 001 Device 003: ID 045e:02a8 Microsoft Corp. Xbox 360 Wireless Networking Adapter
                            parts = line.split()
                            if len(parts) >= 6:
                                bus = parts[1]
                                device = parts[3].rstrip(':')
                                vendor_product = parts[5]
                                description = ' '.join(parts[6:])
                                
                                devices.append({
                                    'bus': bus,
                                    'device': device,
                                    'vendor_product': vendor_product,
                                    'description': description,
                                    'device_path': f"/dev/bus/usb/{bus.zfill(3)}/{device.zfill(3)}"
                                })
            
            logger.info(f"Found {len(devices)} Xbox 360 devices")
            for dev in devices:
                logger.info(f"  {dev['vendor_product']}: {dev['description']}")
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to scan USB devices: {e}")
        
        return devices
    
    def start_usbmon_capture(self, bus: str = "0") -> bool:
        """Start USB monitoring with usbmon"""
        if self.capture_active:
            logger.warning("USB capture already active")
            return False
        
        try:
            # Create capture filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.capture_file = self.capture_dir / f"xbox360_usb_capture_{timestamp}.log"
            
            # Load usbmon module if not loaded
            try:
                subprocess.run(['modprobe', 'usbmon'], check=True)
                logger.info("usbmon module loaded")
            except subprocess.CalledProcessError:
                logger.warning("Could not load usbmon module (may already be loaded)")
            
            # Check if usbmon is available
            usbmon_device = f"/sys/kernel/debug/usb/usbmon/{bus}u"
            if not os.path.exists(usbmon_device):
                logger.error(f"usbmon device not found: {usbmon_device}")
                logger.info("Try: sudo mount -t debugfs none /sys/kernel/debug")
                return False
            
            # Start usbmon capture
            cmd = ['cat', usbmon_device]
            logger.info(f"Starting USB capture: {' '.join(cmd)}")
            logger.info(f"Capture file: {self.capture_file}")
            
            with open(self.capture_file, 'w') as f:
                self.usbmon_process = subprocess.Popen(
                    cmd, stdout=f, stderr=subprocess.PIPE,
                    text=True, bufsize=1
                )
            
            self.capture_active = True
            logger.info("✅ USB capture started")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start USB capture: {e}")
            return False
    
    def stop_usbmon_capture(self) -> bool:
        """Stop USB monitoring"""
        if not self.capture_active:
            logger.warning("USB capture not active")
            return False
        
        try:
            if self.usbmon_process:
                self.usbmon_process.terminate()
                self.usbmon_process.wait(timeout=5)
                self.usbmon_process = None
            
            self.capture_active = False
            logger.info("✅ USB capture stopped")
            
            # Analyze the capture if it exists and has content
            if self.capture_file and self.capture_file.exists() and self.capture_file.stat().st_size > 0:
                logger.info(f"Capture file size: {self.capture_file.stat().st_size} bytes")
                return True
            else:
                logger.warning("Capture file is empty or missing")
                return False
            
        except Exception as e:
            logger.error(f"Failed to stop USB capture: {e}")
            return False
    
    def analyze_last_capture(self) -> Optional[Dict]:
        """Analyze the most recent capture file"""
        if not self.capture_file or not self.capture_file.exists():
            logger.warning("No capture file to analyze")
            return None
        
        try:
            logger.info(f"Analyzing capture: {self.capture_file}")
            
            # Reset analyzer
            self.analyzer = Xbox360CaptureAnalyzer()
            
            # Parse the capture
            self.analyzer.parse_usbmon_log(self.capture_file)
            self.analyzer.analyze_authentication_sequence()
            self.analyzer.extract_device_descriptors()
            constants = self.analyzer.extract_protocol_constants()
            
            # Generate analysis report
            report_file = self.capture_file.with_suffix('.analysis.md')
            self.analyzer.generate_analysis_report(report_file)
            
            results = {
                'capture_file': str(self.capture_file),
                'report_file': str(report_file),
                'control_transfers': len(self.analyzer.control_transfers),
                'bulk_transfers': len(self.analyzer.bulk_transfers),
                'auth_sequence': len(self.analyzer.authentication_sequence),
                'constants': constants
            }
            
            logger.info("✅ Capture analysis complete")
            logger.info(f"  Control transfers: {results['control_transfers']}")
            logger.info(f"  Bulk transfers: {results['bulk_transfers']}")
            logger.info(f"  Auth sequence: {results['auth_sequence']}")
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to analyze capture: {e}")
            return None
    
    def setup_usb_passthrough(self) -> bool:
        """Setup USB passthrough using raw-gadget"""
        logger.info("Setting up USB passthrough...")
        
        try:
            # Check if raw-gadget is available
            if not os.path.exists('/dev/raw-gadget'):
                logger.error("raw-gadget not available. Check kernel configuration.")
                return False
            
            # Setup gadget structure
            success = self.gadget.setup_complete_gadget()
            if not success:
                logger.error("Failed to setup USB gadget")
                return False
            
            # Build usb-sniffify if needed
            sniffify_dir = Path(__file__).parent.parent / "usb_sniffing_tools" / "usb-sniffify"
            if sniffify_dir.exists():
                build_dir = sniffify_dir / "build"
                if not (build_dir / "raw-gadget-passthrough").exists():
                    logger.info("Building usb-sniffify...")
                    if self._build_usb_sniffify(sniffify_dir):
                        logger.info("✅ usb-sniffify built successfully")
                    else:
                        logger.warning("Failed to build usb-sniffify")
                        return False
            
            logger.info("✅ USB passthrough setup complete")
            return True
            
        except Exception as e:
            logger.error(f"Failed to setup USB passthrough: {e}")
            return False
    
    def _build_usb_sniffify(self, source_dir: Path) -> bool:
        """Build the usb-sniffify tools"""
        try:
            build_dir = source_dir / "build"
            build_dir.mkdir(exist_ok=True)
            
            # Run cmake
            result = subprocess.run(
                ['cmake', '..'], 
                cwd=build_dir, 
                capture_output=True, 
                text=True,
                timeout=60
            )
            
            if result.returncode != 0:
                logger.error(f"CMake failed: {result.stderr}")
                return False
            
            # Run make
            result = subprocess.run(
                ['make', '-j4'], 
                cwd=build_dir, 
                capture_output=True, 
                text=True,
                timeout=300
            )
            
            if result.returncode != 0:
                logger.error(f"Make failed: {result.stderr}")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Build failed: {e}")
            return False
    
    def start_passthrough(self, source_device: str) -> bool:
        """Start USB passthrough from source device"""
        if self.passthrough_active:
            logger.warning("USB passthrough already active")
            return False
        
        try:
            logger.info(f"Starting USB passthrough from {source_device}")
            
            # Find the passthrough binary
            sniffify_dir = Path(__file__).parent.parent / "usb_sniffing_tools" / "usb-sniffify"
            passthrough_bin = sniffify_dir / "build" / "raw-gadget-passthrough"
            
            if not passthrough_bin.exists():
                logger.error(f"Passthrough binary not found: {passthrough_bin}")
                return False
            
            # Start passthrough process
            cmd = [str(passthrough_bin), source_device]
            logger.info(f"Running: {' '.join(cmd)}")
            
            self.passthrough_process = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                text=True, bufsize=1
            )
            
            # Give it a moment to start
            time.sleep(2)
            
            # Check if it's still running
            if self.passthrough_process.poll() is None:
                self.passthrough_active = True
                logger.info("✅ USB passthrough started")
                return True
            else:
                stdout, stderr = self.passthrough_process.communicate()
                logger.error(f"Passthrough failed to start: {stderr}")
                return False
            
        except Exception as e:
            logger.error(f"Failed to start USB passthrough: {e}")
            return False
    
    def stop_passthrough(self) -> bool:
        """Stop USB passthrough"""
        if not self.passthrough_active:
            logger.warning("USB passthrough not active")
            return False
        
        try:
            if hasattr(self, 'passthrough_process') and self.passthrough_process:
                self.passthrough_process.terminate()
                self.passthrough_process.wait(timeout=5)
                self.passthrough_process = None
            
            self.passthrough_active = False
            logger.info("✅ USB passthrough stopped")
            return True
            
        except Exception as e:
            logger.error(f"Failed to stop USB passthrough: {e}")
            return False
    
    def get_status(self) -> Dict:
        """Get comprehensive status of USB passthrough system"""
        status = {
            'capture_active': self.capture_active,
            'capture_file': str(self.capture_file) if self.capture_file else None,
            'passthrough_active': self.passthrough_active,
            'gadget_status': self.gadget.get_status(),
            'available_devices': self.scan_xbox_devices(),
            'capture_dir': str(self.capture_dir),
            'usbmon_available': os.path.exists('/sys/kernel/debug/usb/usbmon'),
            'raw_gadget_available': os.path.exists('/dev/raw-gadget')
        }
        
        return status
    
    def create_capture_session(self, description: str = "") -> Dict:
        """Create a new capture session with metadata"""
        session = {
            'id': datetime.now().strftime("%Y%m%d_%H%M%S"),
            'description': description,
            'start_time': datetime.now().isoformat(),
            'devices_before': self.scan_xbox_devices(),
            'capture_dir': self.capture_dir / f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        }
        
        # Create session directory
        session['capture_dir'].mkdir(parents=True, exist_ok=True)
        
        # Save session metadata
        session_file = session['capture_dir'] / "session_metadata.json"
        import json
        with open(session_file, 'w') as f:
            json.dump(session, f, indent=2, default=str)
        
        logger.info(f"Created capture session: {session['id']}")
        return session


def main():
    """Main function for standalone testing"""
    import argparse
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    parser = argparse.ArgumentParser(description='Xbox 360 USB Passthrough Manager')
    parser.add_argument('action', choices=[
        'scan', 'capture', 'analyze', 'passthrough', 'status', 'session'
    ], help='Action to perform')
    parser.add_argument('--device', help='Target device for passthrough')
    parser.add_argument('--duration', type=int, default=30, help='Capture duration in seconds')
    parser.add_argument('--output', help='Output directory for captures')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose logging')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Initialize manager
    output_dir = Path(args.output) if args.output else None
    manager = USBPassthroughManager(capture_dir=output_dir)
    
    try:
        if args.action == 'scan':
            devices = manager.scan_xbox_devices()
            if devices:
                print("Found Xbox 360 devices:")
                for i, dev in enumerate(devices, 1):
                    print(f"  {i}. {dev['vendor_product']}: {dev['description']}")
                    print(f"     Bus {dev['bus']}, Device {dev['device']}")
            else:
                print("No Xbox 360 devices found")
        
        elif args.action == 'capture':
            print(f"Starting USB capture for {args.duration} seconds...")
            if manager.start_usbmon_capture():
                print("Capture started. Connect/disconnect Xbox device now...")
                time.sleep(args.duration)
                manager.stop_usbmon_capture()
                
                results = manager.analyze_last_capture()
                if results:
                    print("Capture analysis complete:")
                    print(f"  Control transfers: {results['control_transfers']}")
                    print(f"  Bulk transfers: {results['bulk_transfers']}")
                    print(f"  Auth sequence: {results['auth_sequence']}")
                    print(f"  Report: {results['report_file']}")
            else:
                print("Failed to start capture")
        
        elif args.action == 'passthrough':
            if not args.device:
                devices = manager.scan_xbox_devices()
                if devices:
                    args.device = devices[0]['device_path']
                    print(f"Using device: {args.device}")
                else:
                    print("No devices found and none specified")
                    sys.exit(1)
            
            if manager.setup_usb_passthrough():
                if manager.start_passthrough(args.device):
                    print("USB passthrough active. Press Ctrl+C to stop...")
                    try:
                        while True:
                            time.sleep(1)
                    except KeyboardInterrupt:
                        manager.stop_passthrough()
                        print("Passthrough stopped")
            else:
                print("Failed to setup passthrough")
        
        elif args.action == 'status':
            status = manager.get_status()
            print("USB Passthrough Manager Status:")
            print(f"  Capture active: {status['capture_active']}")
            print(f"  Passthrough active: {status['passthrough_active']}")
            print(f"  Available devices: {len(status['available_devices'])}")
            print(f"  usbmon available: {status['usbmon_available']}")
            print(f"  raw-gadget available: {status['raw_gadget_available']}")
            
            gadget_status = status['gadget_status']
            print(f"  Gadget configured: {gadget_status['configured']}")
            print(f"  Gadget active: {gadget_status['active']}")
        
        elif args.action == 'session':
            session = manager.create_capture_session("Manual test session")
            print(f"Created capture session: {session['id']}")
            print(f"Session directory: {session['capture_dir']}")
            
    except KeyboardInterrupt:
        print("\nOperation cancelled")
    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()