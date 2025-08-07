"""
Integration tests for Xbox 360 Emulation System
Tests complete system workflows and component interactions
"""
import pytest
import asyncio
import time
from unittest.mock import Mock, patch, MagicMock
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


class TestSystemIntegration:
    """Test complete system integration workflows"""
    
    @pytest.mark.asyncio
    async def test_complete_system_activation(self, mock_raspberry_pi, mock_kernel_modules, 
                                             mock_usb_gadget, mock_network_interfaces):
        """Test complete system activation sequence"""
        from xbox360_emulator import Xbox360Emulator
        
        with patch('os.listdir', return_value=['20980000.usb']), \
             patch.object(Xbox360Emulator, '_discover_interfaces', return_value=['eth0', 'wlan0', 'usb0']):
            
            emulator = Xbox360Emulator()
            result = await emulator.start_emulation()
            
            assert result is True
            assert emulator.is_running is True
            assert emulator.gadget.is_active is True
            assert emulator.network_bridge.is_active is True
    
    def test_system_initialization_sequence(self, mock_raspberry_pi, mock_system_checks):
        """Test proper system initialization order"""
        from xbox360_emulator import Xbox360Emulator
        
        with patch.object(Xbox360Emulator, '_validate_system_requirements') as mock_validate:
            emulator = Xbox360Emulator()
            mock_validate.assert_called_once()
    
    def test_component_dependency_validation(self, mock_raspberry_pi):
        """Test that components validate their dependencies"""
        from xbox360_gadget import Xbox360Gadget
        from network_bridge import NetworkBridge
        
        # Test USB gadget requires kernel modules
        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = subprocess.CalledProcessError(1, 'modprobe')
            
            gadget = Xbox360Gadget()
            with pytest.raises(RuntimeError, match="Failed to load kernel modules"):
                gadget.activate()
    
    def test_error_propagation_through_system(self, mock_raspberry_pi, mock_kernel_modules):
        """Test that errors properly propagate through system layers"""
        from xbox360_emulator import Xbox360Emulator
        
        # Mock USB gadget activation failure
        with patch('os.listdir', return_value=[]):  # No UDC available
            emulator = Xbox360Emulator()
            
            with pytest.raises(RuntimeError):
                emulator.start_emulation()
    
    def test_graceful_degradation_network_failure(self, mock_raspberry_pi, mock_kernel_modules, mock_usb_gadget):
        """Test graceful degradation when network bridge fails"""
        from xbox360_emulator import Xbox360Emulator
        
        with patch('os.listdir', return_value=['20980000.usb']), \
             patch('subprocess.run') as mock_run:
            
            # USB gadget succeeds, network bridge fails
            mock_run.side_effect = [
                Mock(returncode=0),  # Kernel modules load
                subprocess.CalledProcessError(1, 'ip')  # Network bridge fails
            ]
            
            emulator = Xbox360Emulator(allow_partial_activation=True)
            result = emulator.start_emulation()
            
            # Should succeed with USB gadget only
            assert result is True
            assert emulator.gadget.is_active is True
            assert emulator.network_bridge.is_active is False
    
    def test_system_state_consistency(self, mock_raspberry_pi, mock_kernel_modules, 
                                    mock_usb_gadget, mock_network_interfaces):
        """Test system maintains consistent state across operations"""
        from xbox360_emulator import Xbox360Emulator
        
        with patch('os.listdir', return_value=['20980000.usb']):
            emulator = Xbox360Emulator()
            
            # Initial state
            assert emulator.is_running is False
            
            # After successful start
            emulator.start_emulation()
            assert emulator.is_running is True
            assert emulator.gadget.is_active is True
            
            # After stop
            emulator.stop_emulation()
            assert emulator.is_running is False
            assert emulator.gadget.is_active is False
    
    def test_resource_cleanup_on_failure(self, mock_raspberry_pi, mock_kernel_modules):
        """Test proper resource cleanup when activation fails"""
        from xbox360_emulator import Xbox360Emulator
        
        with patch('os.listdir', return_value=['20980000.usb']), \
             patch('subprocess.run') as mock_run:
            
            # Setup partial failure scenario
            mock_run.side_effect = [
                Mock(returncode=0),  # Kernel modules succeed
                Mock(returncode=0),  # USB gadget creation succeeds  
                subprocess.CalledProcessError(1, 'ip')  # Network fails
            ]
            
            emulator = Xbox360Emulator()
            
            with pytest.raises(RuntimeError):
                emulator.start_emulation()
            
            # Verify cleanup was called
            assert emulator.is_running is False
    
    @pytest.mark.asyncio
    async def test_monitoring_system_integration(self, mock_raspberry_pi, mock_kernel_modules,
                                               mock_usb_gadget, mock_network_interfaces):
        """Test integration with monitoring and health check systems"""
        from xbox360_emulator import Xbox360Emulator
        
        with patch('os.listdir', return_value=['20980000.usb']):
            emulator = Xbox360Emulator()
            await emulator.start_emulation()
            
            # Test health monitoring
            health_status = emulator.get_health_status()
            assert health_status['overall_status'] == 'healthy'
            assert health_status['usb_gadget']['status'] == 'active'
            assert health_status['network_bridge']['status'] == 'active'
    
    def test_configuration_validation_integration(self, mock_raspberry_pi):
        """Test configuration validation across all components"""
        from xbox360_emulator import Xbox360Emulator
        
        # Test invalid configuration
        invalid_config = {
            'usb_gadget': {
                'vendor_id': '0xINVALID',  # Invalid format
                'product_id': '0x028e'
            },
            'network': {
                'interfaces': ['nonexistent0']  # Non-existent interface
            }
        }
        
        with pytest.raises(ValueError, match="Invalid configuration"):
            emulator = Xbox360Emulator(config=invalid_config)
    
    def test_concurrent_operation_handling(self, mock_raspberry_pi, mock_kernel_modules,
                                          mock_usb_gadget, mock_network_interfaces):
        """Test handling of concurrent operations"""
        from xbox360_emulator import Xbox360Emulator
        import threading
        
        with patch('os.listdir', return_value=['20980000.usb']):
            emulator = Xbox360Emulator()
            
            results = []
            
            def start_emulation():
                try:
                    result = emulator.start_emulation()
                    results.append(('start', result))
                except Exception as e:
                    results.append(('start', str(e)))
            
            def stop_emulation():
                try:
                    result = emulator.stop_emulation()
                    results.append(('stop', result))
                except Exception as e:
                    results.append(('stop', str(e)))
            
            # Test concurrent start operations
            threads = [threading.Thread(target=start_emulation) for _ in range(3)]
            for thread in threads:
                thread.start()
            for thread in threads:
                thread.join()
            
            # Only one start should succeed
            start_results = [r for r in results if r[0] == 'start']
            successful_starts = [r for r in start_results if r[1] is True]
            assert len(successful_starts) <= 1
    
    def test_system_recovery_after_crash(self, mock_raspberry_pi, mock_kernel_modules,
                                        mock_usb_gadget, mock_network_interfaces):
        """Test system recovery after simulated crash"""
        from xbox360_emulator import Xbox360Emulator
        
        with patch('os.listdir', return_value=['20980000.usb']):
            emulator = Xbox360Emulator()
            
            # Start system
            emulator.start_emulation()
            assert emulator.is_running is True
            
            # Simulate crash by setting invalid state
            emulator._simulate_crash()
            
            # Test recovery
            result = emulator.recover_from_crash()
            assert result is True
            assert emulator.is_running is True
    
    def test_performance_under_load(self, mock_raspberry_pi, mock_kernel_modules,
                                   mock_usb_gadget, mock_network_interfaces):
        """Test system performance under simulated load"""
        from xbox360_emulator import Xbox360Emulator
        
        with patch('os.listdir', return_value=['20980000.usb']):
            emulator = Xbox360Emulator()
            emulator.start_emulation()
            
            # Simulate high-frequency operations
            start_time = time.time()
            for _ in range(100):
                status = emulator.get_status()
                assert status['is_running'] is True
            
            end_time = time.time()
            
            # Should complete within reasonable time
            assert (end_time - start_time) < 5.0  # 5 seconds max
    
    def test_memory_leak_prevention(self, mock_raspberry_pi, mock_kernel_modules,
                                   mock_usb_gadget, mock_network_interfaces):
        """Test for memory leaks in repeated operations"""
        from xbox360_emulator import Xbox360Emulator
        import gc
        
        with patch('os.listdir', return_value=['20980000.usb']):
            initial_objects = len(gc.get_objects())
            
            for _ in range(10):
                emulator = Xbox360Emulator()
                emulator.start_emulation()
                emulator.stop_emulation()
                del emulator
                gc.collect()
            
            final_objects = len(gc.get_objects())
            
            # Should not have significant memory growth
            object_growth = final_objects - initial_objects
            assert object_growth < 100  # Allow some growth but not excessive