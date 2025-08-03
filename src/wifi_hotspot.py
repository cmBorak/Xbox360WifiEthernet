#!/usr/bin/env python3
"""
Xbox 360 WiFi Hotspot Manager
Creates a WiFi access point named "PI-Net" that Xbox 360 can scan and connect to
"""

import os
import sys
import time
import logging
import subprocess
import tempfile
from pathlib import Path

logger = logging.getLogger(__name__)

class Xbox360WiFiHotspot:
    """WiFi Access Point for Xbox 360 with PI-Net SSID"""
    
    def __init__(self, ssid="PI-Net", password="xbox360pi", interface="wlan0"):
        self.ssid = ssid
        self.password = password
        self.interface = interface
        self.ap_interface = f"{interface}_ap"
        self.hostapd_conf = "/etc/hostapd/xbox360_hostapd.conf"
        self.dnsmasq_conf = "/etc/dnsmasq.d/xbox360_ap.conf"
        self.is_running = False
        
        # Network configuration for Xbox 360 compatibility
        self.network_config = {
            'ip_range': '192.168.4.0/24',
            'gateway': '192.168.4.1',
            'dhcp_start': '192.168.4.10',
            'dhcp_end': '192.168.4.50',
            'dns_primary': '8.8.8.8',
            'dns_secondary': '8.8.4.4'
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
    
    def check_prerequisites(self):
        """Check if WiFi hotspot can be created"""
        logger.info("Checking WiFi hotspot prerequisites...")
        
        # Check if running as root
        if os.geteuid() != 0:
            raise RuntimeError("WiFi hotspot requires root privileges")
        
        # Check if wireless interface exists
        if not os.path.exists(f'/sys/class/net/{self.interface}'):
            raise RuntimeError(f"Wireless interface {self.interface} not found")
        
        # Check if hostapd is installed
        result = self._run_command("which hostapd", check=False)
        if not result:
            logger.info("Installing hostapd...")
            self._run_command("apt-get update -qq")
            self._run_command("apt-get install -y hostapd")
        
        # Check if dnsmasq is installed
        result = self._run_command("which dnsmasq", check=False)
        if not result:
            logger.info("Installing dnsmasq...")
            self._run_command("apt-get install -y dnsmasq")
        
        # Check wireless capabilities
        try:
            result = self._run_command(f"iwconfig {self.interface}")
            if "no wireless extensions" in result.lower():
                raise RuntimeError(f"Interface {self.interface} does not support WiFi")
        except:
            raise RuntimeError(f"Cannot determine wireless capabilities of {self.interface}")
        
        logger.info("✅ WiFi hotspot prerequisites met")
    
    def create_hostapd_config(self):
        """Create hostapd configuration for Xbox 360 compatible AP"""
        logger.info("Creating hostapd configuration...")
        
        # Xbox 360 works best with specific WiFi settings
        hostapd_config = f"""# Xbox 360 Compatible WiFi Access Point Configuration
# Generated for PI-Net hotspot

# Interface configuration
interface={self.interface}
driver=nl80211

# Network configuration
ssid={self.ssid}
hw_mode=g
channel=6
ieee80211n=1
wmm_enabled=1

# Security configuration (WPA2 for Xbox 360 compatibility)
auth_algs=1
ignore_broadcast_ssid=0
wpa=2
wpa_passphrase={self.password}
wpa_key_mgmt=WPA-PSK
wpa_pairwise=TKIP
rsn_pairwise=CCMP

# Xbox 360 specific optimizations
beacon_int=100
dtim_period=2
max_num_sta=10
rts_threshold=2347
fragm_threshold=2346

# Country code (adjust as needed)
country_code=US

# Logging
logger_syslog=-1
logger_syslog_level=2
"""
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(self.hostapd_conf), exist_ok=True)
        
        with open(self.hostapd_conf, 'w') as f:
            f.write(hostapd_config)
        
        logger.info(f"✅ hostapd configuration created: {self.hostapd_conf}")
    
    def create_dnsmasq_config(self):
        """Create dnsmasq configuration for DHCP and DNS"""
        logger.info("Creating dnsmasq configuration...")
        
        dnsmasq_config = f"""# Xbox 360 Compatible DHCP/DNS Configuration
# Generated for PI-Net hotspot

# Interface to use
interface={self.interface}
bind-interfaces

# DHCP configuration
dhcp-range={self.network_config['dhcp_start']},{self.network_config['dhcp_end']},255.255.255.0,24h

# DNS configuration
server={self.network_config['dns_primary']}
server={self.network_config['dns_secondary']}

# Xbox Live DNS optimizations
address=/xbox.com/{self.network_config['gateway']}
address=/xboxlive.com/{self.network_config['gateway']}
address=/live.com/{self.network_config['gateway']}

# Gateway advertisement
dhcp-option=3,{self.network_config['gateway']}
dhcp-option=6,{self.network_config['dns_primary']},{self.network_config['dns_secondary']}

# Xbox 360 specific DHCP options
dhcp-option=15,xbox360-network
dhcp-option=252,http://{self.network_config['gateway']}/wpad.dat

# Logging
log-dhcp
log-queries
"""
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(self.dnsmasq_conf), exist_ok=True)
        
        with open(self.dnsmasq_conf, 'w') as f:
            f.write(dnsmasq_config)
        
        logger.info(f"✅ dnsmasq configuration created: {self.dnsmasq_conf}")
    
    def configure_interface(self):
        """Configure wireless interface for access point mode"""
        logger.info(f"Configuring interface {self.interface}...")
        
        # Stop any existing network manager control
        self._run_command(f"nmcli device set {self.interface} managed no", check=False)
        
        # Bring interface down
        self._run_command(f"ip link set {self.interface} down")
        
        # Configure IP address
        self._run_command(f"ip addr flush dev {self.interface}")
        self._run_command(f"ip addr add {self.network_config['gateway']}/24 dev {self.interface}")
        
        # Bring interface up
        self._run_command(f"ip link set {self.interface} up")
        
        logger.info(f"✅ Interface {self.interface} configured with IP {self.network_config['gateway']}")
    
    def setup_forwarding(self, eth_interface="eth0"):
        """Setup IP forwarding and NAT for internet access"""
        logger.info("Setting up IP forwarding and NAT...")
        
        # Enable IP forwarding
        self._run_command("echo 1 > /proc/sys/net/ipv4/ip_forward")
        
        # Clear existing iptables rules
        self._run_command("iptables -F FORWARD", check=False)
        self._run_command("iptables -t nat -F POSTROUTING", check=False)
        
        # Setup NAT rules
        self._run_command(f"iptables -t nat -A POSTROUTING -o {eth_interface} -j MASQUERADE")
        self._run_command(f"iptables -A FORWARD -i {self.interface} -o {eth_interface} -j ACCEPT")
        self._run_command(f"iptables -A FORWARD -i {eth_interface} -o {self.interface} -m state --state RELATED,ESTABLISHED -j ACCEPT")
        
        # Xbox Live specific rules
        xbox_ports = [
            ("88", "udp"),    # Xbox Live
            ("53", "udp"),    # DNS
            ("53", "tcp"),    # DNS
            ("3074", "udp"),  # Xbox Live voice/data
            ("3074", "tcp"),  # Xbox Live voice/data
            ("80", "tcp"),    # HTTP
            ("443", "tcp"),   # HTTPS
        ]
        
        for port, protocol in xbox_ports:
            self._run_command(f"iptables -A FORWARD -p {protocol} --dport {port} -j ACCEPT")
        
        # Save iptables rules
        self._run_command("iptables-save > /etc/iptables/rules.v4", check=False)
        
        logger.info("✅ IP forwarding and NAT configured")
    
    def start_services(self):
        """Start hostapd and dnsmasq services"""
        logger.info("Starting WiFi hotspot services...")
        
        # Stop existing services
        self._run_command("systemctl stop hostapd", check=False)
        self._run_command("systemctl stop dnsmasq", check=False)
        
        # Start dnsmasq first
        self._run_command("systemctl start dnsmasq")
        
        # Start hostapd
        self._run_command(f"hostapd {self.hostapd_conf} -B")
        
        # Wait for services to stabilize
        time.sleep(3)
        
        # Verify services are running
        if self.is_hotspot_running():
            self.is_running = True
            logger.info("✅ WiFi hotspot 'PI-Net' is running")
        else:
            raise RuntimeError("Failed to start WiFi hotspot services")
    
    def stop_services(self):
        """Stop WiFi hotspot services"""
        logger.info("Stopping WiFi hotspot services...")
        
        # Stop services
        self._run_command("pkill hostapd", check=False)
        self._run_command("systemctl stop dnsmasq", check=False)
        
        # Reset interface
        self._run_command(f"ip addr flush dev {self.interface}", check=False)
        self._run_command(f"ip link set {self.interface} down", check=False)
        
        # Re-enable network manager
        self._run_command(f"nmcli device set {self.interface} managed yes", check=False)
        
        self.is_running = False
        logger.info("✅ WiFi hotspot stopped")
    
    def is_hotspot_running(self):
        """Check if hotspot is currently running"""
        try:
            # Check if hostapd is running
            result = self._run_command("pgrep hostapd", check=False)
            if not result:
                return False
            
            # Check if interface has correct IP
            result = self._run_command(f"ip addr show {self.interface}")
            if self.network_config['gateway'] not in result:
                return False
            
            # Check if dnsmasq is running
            result = self._run_command("systemctl is-active dnsmasq", check=False)
            if "active" not in result:
                return False
            
            return True
        except:
            return False
    
    def get_status(self):
        """Get detailed hotspot status"""
        status = {
            'running': self.is_hotspot_running(),
            'ssid': self.ssid,
            'interface': self.interface,
            'ip_address': self.network_config['gateway'],
            'connected_clients': []
        }
        
        if status['running']:
            # Get connected clients from dnsmasq lease file
            try:
                with open('/var/lib/dhcp/dhcpd.leases', 'r') as f:
                    # Parse DHCP leases (simplified)
                    status['connected_clients'] = []
                    # Add parsing logic here if needed
            except:
                pass
        
        return status
    
    def setup_complete_hotspot(self, eth_interface="eth0"):
        """Complete WiFi hotspot setup process"""
        logger.info("🌐 Setting up Xbox 360 WiFi hotspot 'PI-Net'...")
        
        try:
            self.check_prerequisites()
            self.create_hostapd_config()
            self.create_dnsmasq_config()
            self.configure_interface()
            self.setup_forwarding(eth_interface)
            self.start_services()
            
            logger.info("🌐 Xbox 360 WiFi hotspot 'PI-Net' is ready!")
            logger.info(f"   SSID: {self.ssid}")
            logger.info(f"   Password: {self.password}")
            logger.info(f"   Gateway: {self.network_config['gateway']}")
            return True
            
        except Exception as e:
            logger.error(f"WiFi hotspot setup failed: {e}")
            return False


def main():
    """Main function for standalone execution"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Xbox 360 WiFi Hotspot Manager')
    parser.add_argument('action', choices=['start', 'stop', 'status', 'setup'],
                       help='Action to perform')
    parser.add_argument('--ssid', default='PI-Net',
                       help='WiFi network name (default: PI-Net)')
    parser.add_argument('--password', default='xbox360pi',
                       help='WiFi password (default: xbox360pi)')
    parser.add_argument('--interface', default='wlan0',
                       help='Wireless interface (default: wlan0)')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Enable verbose logging')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    hotspot = Xbox360WiFiHotspot(args.ssid, args.password, args.interface)
    
    try:
        if args.action == 'setup':
            success = hotspot.setup_complete_hotspot()
            sys.exit(0 if success else 1)
            
        elif args.action == 'start':
            hotspot.start_services()
            
        elif args.action == 'stop':
            hotspot.stop_services()
            
        elif args.action == 'status':
            status = hotspot.get_status()
            print("Xbox 360 WiFi Hotspot Status:")
            print(f"  Running: {status['running']}")
            print(f"  SSID: {status['ssid']}")
            print(f"  Interface: {status['interface']}")
            print(f"  IP Address: {status['ip_address']}")
            print(f"  Connected Clients: {len(status['connected_clients'])}")
            
    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()