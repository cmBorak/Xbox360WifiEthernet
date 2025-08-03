#!/usr/bin/env python3
"""
Xbox 360 WiFi Module Emulator - Main Orchestrator
Coordinates USB gadget, network bridge, and Xbox 360 protocol handling
"""

import os
import sys
import time
import json
import logging
import threading
from pathlib import Path
from datetime import datetime

# Import our custom modules
from xbox360_gadget import Xbox360Gadget
from network_bridge import Xbox360NetworkBridge

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('/var/log/xbox360-emulator.log')
    ]
)
logger = logging.getLogger(__name__)

class Xbox360EmulatorManager:
    """Main Xbox 360 WiFi Module Emulator Manager"""
    
    def __init__(self, config_file="/etc/xbox360-emulator.conf"):
        self.config_file = config_file
        self.config = self.load_config()
        
        # Initialize components
        self.gadget = Xbox360Gadget(self.config['gadget']['name'])
        self.bridge = Xbox360NetworkBridge(
            bridge_name=self.config['bridge']['name'],
            eth_interface=self.config['bridge']['eth_interface'],
            usb_interface=self.config['bridge']['usb_interface']
        )
        
        # State tracking
        self.running = False
        self.xbox_connected = False
        self.last_status_check = 0
        self.connection_monitor_thread = None
        
        # Statistics
        self.stats = {
            'start_time': None,
            'xbox_connections': 0,
            'total_uptime': 0,
            'bytes_transferred': 0,
            'last_xbox_connect': None
        }
    
    def load_config(self):
        """Load configuration with sensible defaults"""
        default_config = {
            'gadget': {
                'name': 'xbox360',
                'auto_start': True
            },
            'bridge': {
                'name': 'br0',
                'eth_interface': 'eth0',
                'usb_interface': 'usb0',
                'use_dhcp': True,
                'static_ip': None
            },
            'monitoring': {
                'status_check_interval': 30,
                'connection_monitor': True,
                'auto_recovery': True
            },
            'logging': {
                'level': 'INFO',
                'file': '/var/log/xbox360-emulator.log'
            }
        }
        
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    user_config = json.load(f)
                # Merge user config with defaults
                self._merge_config(default_config, user_config)
            except Exception as e:
                logger.warning(f"Failed to load config file: {e}")
        
        return default_config
    
    def _merge_config(self, default, user):
        """Recursively merge user config into default config"""
        for key, value in user.items():
            if key in default:
                if isinstance(default[key], dict) and isinstance(value, dict):
                    self._merge_config(default[key], value)
                else:
                    default[key] = value
    
    def save_config(self):
        """Save current configuration"""
        try:
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
            logger.info(f"Configuration saved to {self.config_file}")
        except Exception as e:
            logger.error(f"Failed to save config: {e}")
    
    def check_system_requirements(self):
        """Comprehensive system requirements check"""
        logger.info("Checking system requirements...")
        
        requirements = {
            'raspberry_pi_4': False,
            'usb_gadget_support': False,
            'bridge_utils': False,
            'root_privileges': False,
            'kernel_modules': False
        }
        
        # Check if Raspberry Pi 4
        try:
            with open('/proc/cpuinfo', 'r') as f:
                if 'Raspberry Pi 4' in f.read():
                    requirements['raspberry_pi_4'] = True
        except:
            pass
        
        # Check root privileges
        requirements['root_privileges'] = os.geteuid() == 0
        
        # Check USB gadget support
        requirements['usb_gadget_support'] = os.path.exists('/sys/kernel/config')
        
        # Check bridge utilities
        requirements['bridge_utils'] = os.system('which brctl >/dev/null 2>&1') == 0
        
        # Check kernel modules
        try:
            result = os.system('lsmod | grep -q libcomposite')
            if result != 0:
                os.system('modprobe libcomposite >/dev/null 2>&1')
                result = os.system('lsmod | grep -q libcomposite')
            requirements['kernel_modules'] = result == 0
        except:
            pass
        
        # Report results
        for req, status in requirements.items():
            status_icon = "✅" if status else "❌"
            logger.info(f"{status_icon} {req.replace('_', ' ').title()}: {status}")
        
        missing = [req for req, status in requirements.items() if not status]
        if missing:
            logger.error(f"Missing requirements: {', '.join(missing)}")
            return False
        
        logger.info("✅ All system requirements met")
        return True
    
    def initialize_system(self):
        """Initialize the complete Xbox 360 emulation system"""
        logger.info("🎮 Initializing Xbox 360 WiFi Module Emulator...")
        
        try:
            # Check system requirements
            if not self.check_system_requirements():
                raise RuntimeError("System requirements not met")
            
            # Setup USB gadget
            logger.info("Setting up USB gadget...")
            if not self.gadget.setup_complete_gadget():
                raise RuntimeError("Failed to setup USB gadget")
            
            # Setup network bridge
            logger.info("Setting up network bridge...")
            if not self.bridge.setup_complete_bridge(wait_for_usb=False):
                raise RuntimeError("Failed to setup network bridge")
            
            # Start monitoring
            if self.config['monitoring']['connection_monitor']:
                self.start_connection_monitor()
            
            self.running = True
            self.stats['start_time'] = datetime.now()
            
            logger.info("🎮 Xbox 360 WiFi Module Emulator initialized successfully!")
            return True
            
        except Exception as e:
            logger.error(f"Initialization failed: {e}")
            return False
    
    def start_connection_monitor(self):
        """Start Xbox connection monitoring in background thread"""
        if self.connection_monitor_thread and self.connection_monitor_thread.is_alive():
            return
        
        self.connection_monitor_thread = threading.Thread(
            target=self._connection_monitor_loop,
            daemon=True
        )
        self.connection_monitor_thread.start()
        logger.info("📡 Connection monitor started")
    
    def _connection_monitor_loop(self):
        """Background loop to monitor Xbox connections"""
        while self.running:
            try:
                # Check if Xbox is connected (USB interface exists)
                usb_connected = os.path.exists(f'/sys/class/net/{self.bridge.usb_interface}')
                
                if usb_connected and not self.xbox_connected:
                    # Xbox just connected
                    logger.info("🎮 Xbox 360 connected!")
                    self.xbox_connected = True
                    self.stats['xbox_connections'] += 1
                    self.stats['last_xbox_connect'] = datetime.now()
                    
                    # Add USB interface to bridge if not already added
                    bridge_status = self.bridge.get_bridge_status()
                    if not bridge_status['usb_in_bridge']:
                        logger.info("Adding Xbox to network bridge...")
                        self.bridge.add_usb_to_bridge(retry_count=3, retry_delay=1)
                
                elif not usb_connected and self.xbox_connected:
                    # Xbox disconnected
                    logger.info("🎮 Xbox 360 disconnected")
                    self.xbox_connected = False
                
                # Periodic status check
                current_time = time.time()
                if (current_time - self.last_status_check >= 
                    self.config['monitoring']['status_check_interval']):
                    self._periodic_status_check()
                    self.last_status_check = current_time
                
            except Exception as e:
                logger.error(f"Connection monitor error: {e}")
                if self.config['monitoring']['auto_recovery']:
                    logger.info("Attempting auto-recovery...")
                    self._attempt_recovery()
            
            time.sleep(5)  # Check every 5 seconds
    
    def _periodic_status_check(self):
        """Perform periodic system health check"""
        logger.debug("Performing periodic status check...")
        
        # Check gadget status
        gadget_status = self.gadget.get_status()
        if not gadget_status['active']:
            logger.warning("USB gadget not active, attempting restart...")
            try:
                self.gadget.activate_gadget()
            except Exception as e:
                logger.error(f"Failed to restart gadget: {e}")
        
        # Check bridge status
        bridge_status = self.bridge.get_bridge_status()
        if not bridge_status['bridge_up']:
            logger.warning("Bridge not up, attempting restart...")
            try:
                self.bridge.bring_up_bridge()
            except Exception as e:
                logger.error(f"Failed to restart bridge: {e}")
    
    def _attempt_recovery(self):
        """Attempt automatic system recovery"""
        logger.info("Attempting system recovery...")
        
        try:
            # Restart gadget
            if self.gadget.is_active():
                self.gadget.deactivate_gadget()
            time.sleep(2)
            self.gadget.activate_gadget()
            
            # Reconfigure bridge
            bridge_status = self.bridge.get_bridge_status()
            if not bridge_status['bridge_up']:
                self.bridge.bring_up_bridge()
            
            logger.info("✅ System recovery completed")
            
        except Exception as e:
            logger.error(f"Recovery failed: {e}")
    
    def get_comprehensive_status(self):
        """Get comprehensive system status"""
        gadget_status = self.gadget.get_status()
        bridge_status = self.bridge.get_bridge_status()
        
        # Calculate uptime
        uptime_seconds = 0
        if self.stats['start_time']:
            uptime_seconds = (datetime.now() - self.stats['start_time']).total_seconds()
        
        status = {
            'system': {
                'running': self.running,
                'xbox_connected': self.xbox_connected,
                'uptime_seconds': uptime_seconds,
                'uptime_formatted': self._format_uptime(uptime_seconds)
            },
            'gadget': gadget_status,
            'bridge': bridge_status,
            'statistics': self.stats.copy(),
            'config': self.config
        }
        
        # Convert datetime objects to strings for JSON serialization
        for key, value in status['statistics'].items():
            if isinstance(value, datetime):
                status['statistics'][key] = value.isoformat()
        
        return status
    
    def _format_uptime(self, seconds):
        """Format uptime in human readable format"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        seconds = int(seconds % 60)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    
    def stop(self):
        """Stop the emulator system"""
        logger.info("🛑 Stopping Xbox 360 WiFi Module Emulator...")
        
        self.running = False
        
        # Stop connection monitor
        if self.connection_monitor_thread and self.connection_monitor_thread.is_alive():
            self.connection_monitor_thread.join(timeout=5)
        
        # Deactivate gadget
        try:
            self.gadget.deactivate_gadget()
        except Exception as e:
            logger.warning(f"Error deactivating gadget: {e}")
        
        logger.info("🛑 Xbox 360 WiFi Module Emulator stopped")
    
    def run_interactive_mode(self):
        """Run in interactive mode with status display"""
        logger.info("🎮 Xbox 360 WiFi Module Emulator - Interactive Mode")
        logger.info("=" * 50)
        
        try:
            while self.running:
                # Display status
                status = self.get_comprehensive_status()
                
                print("\n" + "=" * 50)
                print("📊 XBOX 360 WIFI EMULATOR STATUS")
                print("=" * 50)
                print(f"🎮 Xbox Connected: {'Yes' if status['system']['xbox_connected'] else 'No'}")
                print(f"⏱️  Uptime: {status['system']['uptime_formatted']}")
                print(f"🔌 USB Gadget: {'Active' if status['gadget']['active'] else 'Inactive'}")
                print(f"🌐 Bridge: {'Up' if status['bridge']['bridge_up'] else 'Down'}")
                print(f"📡 Connections: {status['statistics']['xbox_connections']}")
                
                if status['bridge']['ip_address']:
                    print(f"🔗 IP Address: {status['bridge']['ip_address']}")
                
                print("\nPress Ctrl+C to stop...")
                time.sleep(10)
                
        except KeyboardInterrupt:
            logger.info("Received interrupt signal")
        finally:
            self.stop()


def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Xbox 360 WiFi Module Emulator')
    parser.add_argument('action', choices=['start', 'stop', 'status', 'interactive', 'init'],
                       help='Action to perform')
    parser.add_argument('--config', default='/etc/xbox360-emulator.conf',
                       help='Configuration file path')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Enable verbose logging')
    parser.add_argument('--daemon', '-d', action='store_true',
                       help='Run as daemon (background process)')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Check if running as root
    if os.geteuid() != 0:
        logger.error("This program must be run as root (use sudo)")
        sys.exit(1)
    
    emulator = Xbox360EmulatorManager(args.config)
    
    try:
        if args.action == 'init':
            success = emulator.initialize_system()
            sys.exit(0 if success else 1)
            
        elif args.action == 'start':
            if emulator.initialize_system():
                if args.daemon:
                    logger.info("Running in daemon mode...")
                    # Keep running until signal
                    try:
                        while emulator.running:
                            time.sleep(60)
                    except KeyboardInterrupt:
                        pass
                else:
                    emulator.run_interactive_mode()
            else:
                sys.exit(1)
                
        elif args.action == 'stop':
            emulator.stop()
            
        elif args.action == 'status':
            status = emulator.get_comprehensive_status()
            print(json.dumps(status, indent=2))
            
        elif args.action == 'interactive':
            if emulator.initialize_system():
                emulator.run_interactive_mode()
            else:
                sys.exit(1)
                
    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()