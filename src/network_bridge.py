#!/usr/bin/env python3
"""
Xbox 360 Network Bridge Manager
Handles intelligent bridging between USB gadget and ethernet with Xbox optimization
"""

import os
import sys
import time
import logging
import subprocess
import ipaddress
from pathlib import Path

logger = logging.getLogger(__name__)

class Xbox360NetworkBridge:
    """Advanced network bridge for Xbox 360 optimization"""
    
    def __init__(self, bridge_name="br0", eth_interface="eth0", usb_interface="usb0"):
        self.bridge_name = bridge_name
        self.eth_interface = eth_interface
        self.usb_interface = usb_interface
        self.is_configured = False
        
        # Xbox Live optimized settings
        self.xbox_optimizations = {
            'mtu': 1500,
            'txqueuelen': 1000,
            'tcp_congestion': 'bbr',  # Better congestion control
            'net_core_rmem_max': 134217728,  # 128MB receive buffer
            'net_core_wmem_max': 134217728,  # 128MB send buffer
        }
    
    def _run_command(self, cmd, check=True, capture_output=True):
        """Execute shell command with error handling"""
        try:
            logger.debug(f"Running: {cmd}")
            result = subprocess.run(cmd, shell=True, check=check, 
                                  capture_output=capture_output, text=True)
            if capture_output:
                return result.stdout.strip()
            return result.returncode == 0
        except subprocess.CalledProcessError as e:
            logger.error(f"Command failed: {cmd}")
            if capture_output and e.stderr:
                logger.error(f"Error: {e.stderr}")
            if check:
                raise
            return False
    
    def check_interfaces(self):
        """Check if required network interfaces exist"""
        logger.info("Checking network interfaces...")
        
        # Check ethernet interface
        if not os.path.exists(f'/sys/class/net/{self.eth_interface}'):
            raise RuntimeError(f"Ethernet interface {self.eth_interface} not found")
        
        logger.info(f"✅ Ethernet interface {self.eth_interface} found")
        
        # USB interface will be created by gadget, so just log status
        usb_exists = os.path.exists(f'/sys/class/net/{self.usb_interface}')
        if usb_exists:
            logger.info(f"✅ USB interface {self.usb_interface} found")
        else:
            logger.info(f"ℹ️  USB interface {self.usb_interface} not yet available")
        
        return usb_exists
    
    def install_bridge_utils(self):
        """Ensure bridge utilities are installed"""
        logger.info("Checking bridge utilities...")
        
        # Check if brctl is available
        result = self._run_command("which brctl", check=False)
        if not result:
            logger.info("Installing bridge-utils...")
            self._run_command("apt-get update -qq")
            self._run_command("apt-get install -y bridge-utils")
        
        logger.info("✅ Bridge utilities available")
    
    def optimize_network_stack(self):
        """Apply Xbox Live optimized network settings"""
        logger.info("Applying Xbox Live network optimizations...")
        
        # TCP congestion control
        self._run_command(f"echo {self.xbox_optimizations['tcp_congestion']} > /proc/sys/net/ipv4/tcp_congestion_control")
        
        # Increase network buffers for high bandwidth
        self._run_command(f"echo {self.xbox_optimizations['net_core_rmem_max']} > /proc/sys/net/core/rmem_max")
        self._run_command(f"echo {self.xbox_optimizations['net_core_wmem_max']} > /proc/sys/net/core/wmem_max")
        
        # Enable IP forwarding
        self._run_command("echo 1 > /proc/sys/net/ipv4/ip_forward")
        
        # Optimize for gaming (low latency)
        self._run_command("echo 1 > /proc/sys/net/ipv4/tcp_low_latency")
        
        # Increase connection tracking table
        self._run_command("echo 65536 > /proc/sys/net/netfilter/nf_conntrack_max")
        
        logger.info("✅ Network stack optimized for Xbox Live")
    
    def create_bridge(self):
        """Create and configure bridge interface"""
        logger.info(f"Creating bridge interface {self.bridge_name}...")
        
        # Check if bridge already exists
        if os.path.exists(f'/sys/class/net/{self.bridge_name}'):
            logger.info(f"Bridge {self.bridge_name} already exists, removing...")
            self._run_command(f"ip link set {self.bridge_name} down", check=False)
            self._run_command(f"brctl delbr {self.bridge_name}", check=False)
        
        # Create new bridge
        self._run_command(f"brctl addbr {self.bridge_name}")
        
        # Configure bridge settings for optimal performance
        self._run_command(f"brctl setfd {self.bridge_name} 0")      # Forward delay = 0
        self._run_command(f"brctl sethello {self.bridge_name} 1")   # Hello time = 1s
        self._run_command(f"brctl setmaxage {self.bridge_name} 10") # Max age = 10s
        
        # Disable spanning tree for performance (since we control topology)
        self._run_command(f"brctl stp {self.bridge_name} off")
        
        logger.info("✅ Bridge interface created")
    
    def add_ethernet_to_bridge(self):
        """Add ethernet interface to bridge"""
        logger.info(f"Adding {self.eth_interface} to bridge...")
        
        # Bring down ethernet interface
        self._run_command(f"ip link set {self.eth_interface} down")
        
        # Remove any IP addresses from ethernet
        self._run_command(f"ip addr flush dev {self.eth_interface}", check=False)
        
        # Add to bridge
        self._run_command(f"brctl addif {self.bridge_name} {self.eth_interface}")
        
        # Configure interface settings
        self._run_command(f"ip link set {self.eth_interface} mtu {self.xbox_optimizations['mtu']}")
        self._run_command(f"ip link set {self.eth_interface} txqueuelen {self.xbox_optimizations['txqueuelen']}")
        
        # Bring interface back up
        self._run_command(f"ip link set {self.eth_interface} up")
        
        logger.info(f"✅ {self.eth_interface} added to bridge")
    
    def add_usb_to_bridge(self, retry_count=10, retry_delay=2):
        """Add USB gadget interface to bridge (with retry logic)"""
        logger.info(f"Adding {self.usb_interface} to bridge...")
        
        # Wait for USB interface to become available
        for attempt in range(retry_count):
            if os.path.exists(f'/sys/class/net/{self.usb_interface}'):
                break
            logger.info(f"Waiting for {self.usb_interface}... (attempt {attempt + 1}/{retry_count})")
            time.sleep(retry_delay)
        else:
            logger.warning(f"USB interface {self.usb_interface} not available after {retry_count} attempts")
            return False
        
        try:
            # Configure USB interface
            self._run_command(f"ip link set {self.usb_interface} down")
            self._run_command(f"ip addr flush dev {self.usb_interface}", check=False)
            
            # Add to bridge
            self._run_command(f"brctl addif {self.bridge_name} {self.usb_interface}")
            
            # Configure interface settings
            self._run_command(f"ip link set {self.usb_interface} mtu {self.xbox_optimizations['mtu']}")
            self._run_command(f"ip link set {self.usb_interface} txqueuelen {self.xbox_optimizations['txqueuelen']}")
            
            # Bring interface up
            self._run_command(f"ip link set {self.usb_interface} up")
            
            logger.info(f"✅ {self.usb_interface} added to bridge")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add {self.usb_interface} to bridge: {e}")
            return False
    
    def configure_bridge_ip(self, use_dhcp=True, static_ip=None):
        """Configure bridge IP address"""
        logger.info("Configuring bridge IP address...")
        
        if use_dhcp:
            logger.info("Requesting IP via DHCP...")
            # Try DHCP first
            result = self._run_command(f"dhclient {self.bridge_name}", check=False)
            if result:
                logger.info("✅ DHCP configuration successful")
                return True
            else:
                logger.warning("DHCP failed, trying fallback configuration")
        
        # Fallback to static IP or auto-configuration
        if static_ip:
            logger.info(f"Configuring static IP: {static_ip}")
            self._run_command(f"ip addr add {static_ip} dev {self.bridge_name}")
        else:
            # Auto-configure with a sensible default
            fallback_ip = "192.168.137.1/24"
            logger.info(f"Configuring fallback IP: {fallback_ip}")
            self._run_command(f"ip addr add {fallback_ip} dev {self.bridge_name}")
        
        logger.info("✅ Bridge IP configured")
        return True
    
    def setup_nat_rules(self):
        """Setup NAT/masquerading for internet access"""
        logger.info("Setting up NAT rules for internet access...")
        
        # Clear existing rules
        self._run_command("iptables -t nat -F POSTROUTING", check=False)
        self._run_command("iptables -F FORWARD", check=False)
        
        # Enable masquerading for outbound traffic
        self._run_command(f"iptables -t nat -A POSTROUTING -o {self.eth_interface} -j MASQUERADE")
        
        # Allow forwarding from bridge to ethernet
        self._run_command(f"iptables -A FORWARD -i {self.bridge_name} -o {self.eth_interface} -j ACCEPT")
        self._run_command(f"iptables -A FORWARD -i {self.eth_interface} -o {self.bridge_name} -m state --state RELATED,ESTABLISHED -j ACCEPT")
        
        # Xbox Live specific optimizations
        # Allow Xbox Live traffic (port 88 UDP, 53 UDP/TCP, 3074 UDP/TCP)
        xbox_ports = [
            ("88", "udp"),    # Xbox Live
            ("53", "udp"),    # DNS
            ("53", "tcp"),    # DNS
            ("3074", "udp"),  # Xbox Live voice/data
            ("3074", "tcp"),  # Xbox Live voice/data
        ]
        
        for port, protocol in xbox_ports:
            self._run_command(f"iptables -A FORWARD -p {protocol} --dport {port} -j ACCEPT")
        
        # Save iptables rules
        self._run_command("iptables-save > /etc/iptables/rules.v4", check=False)
        
        logger.info("✅ NAT rules configured")
    
    def bring_up_bridge(self):
        """Bring bridge interface up"""
        logger.info(f"Bringing up bridge {self.bridge_name}...")
        
        self._run_command(f"ip link set {self.bridge_name} up")
        
        # Wait for interface to be fully up
        time.sleep(2)
        
        logger.info("✅ Bridge interface is up")
    
    def get_bridge_status(self):
        """Get detailed bridge status"""
        status = {
            'bridge_exists': os.path.exists(f'/sys/class/net/{self.bridge_name}'),
            'bridge_up': False,
            'eth_in_bridge': False,
            'usb_in_bridge': False,
            'ip_address': None,
            'interfaces': []
        }
        
        if status['bridge_exists']:
            # Check if bridge is up
            try:
                result = self._run_command(f"ip link show {self.bridge_name}")
                status['bridge_up'] = 'UP' in result
            except:
                pass
            
            # Check bridge interfaces
            try:
                result = self._run_command(f"brctl show {self.bridge_name}")
                lines = result.split('\n')[1:]  # Skip header
                for line in lines:
                    if line.strip():
                        parts = line.split()
                        if len(parts) >= 4:
                            interface = parts[3]
                            status['interfaces'].append(interface)
                            if interface == self.eth_interface:
                                status['eth_in_bridge'] = True
                            elif interface == self.usb_interface:
                                status['usb_in_bridge'] = True
            except:
                pass
            
            # Get IP address
            try:
                result = self._run_command(f"ip addr show {self.bridge_name}")
                for line in result.split('\n'):
                    if 'inet ' in line and 'scope global' in line:
                        status['ip_address'] = line.split()[1]
                        break
            except:
                pass
        
        return status
    
    def setup_complete_bridge(self, wait_for_usb=True):
        """Complete bridge setup process"""
        logger.info("🌐 Setting up Xbox 360 network bridge...")
        
        try:
            self.install_bridge_utils()
            self.check_interfaces()
            self.optimize_network_stack()
            self.create_bridge()
            self.add_ethernet_to_bridge()
            
            if wait_for_usb:
                # Try to add USB interface (may not be ready yet)
                usb_added = self.add_usb_to_bridge()
                if not usb_added:
                    logger.info("USB interface will be added when Xbox is connected")
            
            self.bring_up_bridge()
            self.configure_bridge_ip(use_dhcp=True)
            self.setup_nat_rules()
            
            self.is_configured = True
            logger.info("🌐 Xbox 360 network bridge setup complete!")
            return True
            
        except Exception as e:
            logger.error(f"Bridge setup failed: {e}")
            return False
    
    def monitor_xbox_connection(self):
        """Monitor for Xbox connection and add USB interface when available"""
        logger.info("Monitoring for Xbox 360 connection...")
        
        while True:
            # Check if USB interface exists and is not in bridge yet
            status = self.get_bridge_status()
            if (os.path.exists(f'/sys/class/net/{self.usb_interface}') and 
                not status['usb_in_bridge']):
                
                logger.info("Xbox 360 connected! Adding to bridge...")
                if self.add_usb_to_bridge(retry_count=3, retry_delay=1):
                    logger.info("✅ Xbox 360 successfully bridged")
                    break
                else:
                    logger.warning("Failed to add Xbox to bridge, will retry...")
            
            time.sleep(5)  # Check every 5 seconds


def main():
    """Main function for standalone execution"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Xbox 360 Network Bridge Manager')
    parser.add_argument('action', choices=['setup', 'status', 'monitor', 'add-usb'],
                       help='Action to perform')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Enable verbose logging')
    parser.add_argument('--bridge', default='br0',
                       help='Bridge interface name (default: br0)')
    parser.add_argument('--eth', default='eth0',
                       help='Ethernet interface name (default: eth0)')
    parser.add_argument('--usb', default='usb0',
                       help='USB interface name (default: usb0)')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    bridge = Xbox360NetworkBridge(args.bridge, args.eth, args.usb)
    
    try:
        if args.action == 'setup':
            success = bridge.setup_complete_bridge()
            sys.exit(0 if success else 1)
            
        elif args.action == 'status':
            status = bridge.get_bridge_status()
            print("Xbox 360 Bridge Status:")
            print(f"  Bridge exists: {status['bridge_exists']}")
            print(f"  Bridge up: {status['bridge_up']}")
            print(f"  Ethernet in bridge: {status['eth_in_bridge']}")
            print(f"  USB in bridge: {status['usb_in_bridge']}")
            print(f"  IP address: {status['ip_address']}")
            print(f"  Interfaces: {', '.join(status['interfaces'])}")
            
        elif args.action == 'monitor':
            bridge.monitor_xbox_connection()
            
        elif args.action == 'add-usb':
            success = bridge.add_usb_to_bridge()
            sys.exit(0 if success else 1)
            
    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()