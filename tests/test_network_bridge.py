"""
Unit tests for Network Bridge functionality
Tests network interface management without requiring actual network hardware
"""
import pytest
from unittest.mock import Mock, patch, call
import subprocess
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from network_bridge import NetworkBridge


class TestNetworkBridge:
    """Test Network Bridge functionality"""
    
    def test_bridge_initialization(self):
        """Test bridge initialization with default parameters"""
        bridge = NetworkBridge()
        assert bridge.bridge_name == "br0"
        assert bridge.interfaces == []
        assert bridge.is_active is False
    
    def test_interface_discovery(self, mock_network_interfaces):
        """Test network interface discovery"""
        bridge = NetworkBridge()
        interfaces = bridge._discover_interfaces()
        
        expected_interfaces = ['eth0', 'wlan0', 'usb0']
        assert all(iface in interfaces for iface in expected_interfaces)
    
    def test_interface_validation_success(self, mock_network_interfaces):
        """Test successful interface validation"""
        with patch.object(NetworkBridge, '_discover_interfaces', return_value=['eth0', 'wlan0', 'usb0']):
            bridge = NetworkBridge()
            result = bridge._validate_interfaces(['eth0', 'wlan0'])
            assert result is True
    
    def test_interface_validation_failure(self, mock_network_interfaces):
        """Test interface validation failure for non-existent interface"""
        with patch.object(NetworkBridge, '_discover_interfaces', return_value=['eth0', 'wlan0']):
            bridge = NetworkBridge()
            with pytest.raises(ValueError, match="Interface 'nonexistent0' not found"):
                bridge._validate_interfaces(['eth0', 'nonexistent0'])
    
    def test_bridge_creation(self, mock_network_interfaces):
        """Test bridge creation sequence"""
        bridge = NetworkBridge()
        bridge._create_bridge()
        
        # Verify bridge creation commands
        expected_calls = [
            call(['ip', 'link', 'add', 'name', 'br0', 'type', 'bridge'], check=True),
            call(['ip', 'link', 'set', 'br0', 'up'], check=True)
        ]
        mock_network_interfaces.assert_has_calls(expected_calls, any_order=False)
    
    def test_bridge_creation_failure(self, mock_network_interfaces):
        """Test bridge creation failure handling"""
        mock_network_interfaces.side_effect = subprocess.CalledProcessError(1, 'ip')
        
        bridge = NetworkBridge()
        with pytest.raises(RuntimeError, match="Failed to create bridge"):
            bridge._create_bridge()
    
    def test_interface_addition(self, mock_network_interfaces):
        """Test adding interfaces to bridge"""
        bridge = NetworkBridge()
        bridge._add_interface_to_bridge('eth0')
        
        expected_calls = [
            call(['ip', 'link', 'set', 'eth0', 'master', 'br0'], check=True),
            call(['ip', 'link', 'set', 'eth0', 'up'], check=True)
        ]
        mock_network_interfaces.assert_has_calls(expected_calls)
    
    def test_interface_addition_failure(self, mock_network_interfaces):
        """Test interface addition failure handling"""
        mock_network_interfaces.side_effect = subprocess.CalledProcessError(1, 'ip')
        
        bridge = NetworkBridge()
        with pytest.raises(RuntimeError, match="Failed to add interface eth0 to bridge"):
            bridge._add_interface_to_bridge('eth0')
    
    def test_bridge_configuration(self, mock_network_interfaces):
        """Test bridge configuration with STP and forwarding delay"""
        bridge = NetworkBridge()
        bridge._configure_bridge()
        
        expected_calls = [
            call(['ip', 'link', 'set', 'br0', 'type', 'bridge', 'stp_state', '1'], check=True),
            call(['ip', 'link', 'set', 'br0', 'type', 'bridge', 'forward_delay', '2'], check=True),
            call(['ip', 'link', 'set', 'br0', 'type', 'bridge', 'hello_time', '1'], check=True)
        ]
        mock_network_interfaces.assert_has_calls(expected_calls)
    
    def test_dhcp_configuration(self, mock_network_interfaces):
        """Test DHCP client configuration on bridge"""
        bridge = NetworkBridge()
        bridge._configure_dhcp()
        
        mock_network_interfaces.assert_called_with(['dhclient', 'br0'], check=True)
    
    def test_full_bridge_activation(self, mock_network_interfaces):
        """Test complete bridge activation sequence"""
        with patch.object(NetworkBridge, '_discover_interfaces', return_value=['eth0', 'wlan0', 'usb0']):
            bridge = NetworkBridge()
            result = bridge.activate(['eth0', 'usb0'])
            
            assert result is True
            assert bridge.is_active is True
            assert 'eth0' in bridge.interfaces
            assert 'usb0' in bridge.interfaces
    
    def test_bridge_deactivation(self, mock_network_interfaces):
        """Test bridge deactivation and cleanup"""
        bridge = NetworkBridge()
        bridge.is_active = True
        bridge.interfaces = ['eth0', 'usb0']
        
        bridge.deactivate()
        
        expected_calls = [
            call(['ip', 'link', 'set', 'br0', 'down'], check=True),
            call(['ip', 'link', 'delete', 'br0'], check=True)
        ]
        mock_network_interfaces.assert_has_calls(expected_calls)
        assert bridge.is_active is False
    
    def test_bridge_status_monitoring(self, mock_network_interfaces):
        """Test bridge status monitoring"""
        mock_network_interfaces.return_value.stdout = """
br0: flags=4163<UP,BROADCAST,RUNNING,MULTICAST>  mtu 1500
        inet 192.168.1.100  netmask 255.255.255.0  broadcast 192.168.1.255
        ether 02:42:ac:11:00:02  txqueuelen 1000  (Ethernet)
        RX packets 0  bytes 0 (0.0 B)
        TX packets 0  bytes 0 (0.0 B)
"""
        
        bridge = NetworkBridge()
        bridge.is_active = True
        status = bridge.get_status()
        
        assert 'active' in status
        assert status['active'] is True
        assert 'bridge_name' in status
    
    def test_network_performance_optimization(self, mock_network_interfaces):
        """Test network performance optimization settings"""
        bridge = NetworkBridge()
        bridge._optimize_performance()
        
        # Verify performance optimization commands
        expected_calls = [
            call(['sysctl', '-w', 'net.bridge.bridge-nf-call-iptables=0'], check=True),
            call(['sysctl', '-w', 'net.bridge.bridge-nf-call-ip6tables=0'], check=True),
            call(['sysctl', '-w', 'net.bridge.bridge-nf-call-arptables=0'], check=True)
        ]
        mock_network_interfaces.assert_has_calls(expected_calls)
    
    def test_error_injection_network_down(self, mock_network_interfaces):
        """Test error injection - network interface down scenario"""
        mock_network_interfaces.side_effect = [
            Mock(returncode=0),  # Bridge creation succeeds
            subprocess.CalledProcessError(1, 'ip')  # Interface addition fails
        ]
        
        bridge = NetworkBridge()
        with pytest.raises(RuntimeError):
            bridge.activate(['eth0'])
    
    def test_error_injection_permission_denied(self, mock_network_interfaces):
        """Test error injection - permission denied scenario"""
        mock_network_interfaces.side_effect = subprocess.CalledProcessError(1, 'ip', 'Operation not permitted')
        
        bridge = NetworkBridge()
        with pytest.raises(RuntimeError, match="Failed to create bridge"):
            bridge._create_bridge()
    
    def test_concurrent_bridge_operations(self, mock_network_interfaces):
        """Test concurrent bridge operations handling"""
        import threading
        
        bridge = NetworkBridge()
        results = []
        
        def activate_bridge():
            try:
                result = bridge.activate(['eth0'])
                results.append(result)
            except Exception as e:
                results.append(str(e))
        
        # Start multiple concurrent operations
        threads = [threading.Thread(target=activate_bridge) for _ in range(3)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        
        # Only one should succeed, others should handle gracefully
        assert len(results) == 3
    
    def test_bridge_recovery_after_failure(self, mock_network_interfaces):
        """Test bridge recovery after partial failure"""
        # First attempt fails at interface addition
        mock_network_interfaces.side_effect = [
            Mock(returncode=0),  # Bridge creation succeeds
            subprocess.CalledProcessError(1, 'ip'),  # Interface addition fails
            Mock(returncode=0),  # Cleanup succeeds
            Mock(returncode=0),  # Second attempt bridge creation
            Mock(returncode=0),  # Second attempt interface addition
            Mock(returncode=0),  # Configuration
            Mock(returncode=0)   # DHCP
        ]
        
        bridge = NetworkBridge()
        
        # First attempt should fail and cleanup
        with pytest.raises(RuntimeError):
            bridge.activate(['eth0'])
        
        # Second attempt should succeed
        mock_network_interfaces.side_effect = None
        mock_network_interfaces.return_value.returncode = 0
        
        result = bridge.activate(['eth0'])
        assert result is True