"""
Unit tests for Xbox 360 USB Gadget functionality
Tests the core USB device emulation without requiring Pi hardware
"""
import pytest
from unittest.mock import Mock, patch, call
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from xbox360_gadget import Xbox360Gadget


class TestXbox360Gadget:
    """Test Xbox 360 USB Gadget functionality"""
    
    def test_gadget_initialization(self, mock_raspberry_pi, mock_system_checks):
        """Test gadget initialization with proper hardware detection"""
        gadget = Xbox360Gadget()
        assert gadget.gadget_name == "xbox360_controller"
        assert gadget.udc_device is None
    
    def test_hardware_validation_success(self, mock_raspberry_pi):
        """Test successful Raspberry Pi 4 detection"""
        gadget = Xbox360Gadget()
        # Should not raise exception with mocked Pi 4
        result = gadget._validate_hardware()
        assert result is True
    
    def test_hardware_validation_failure(self):
        """Test hardware validation failure on non-Pi hardware"""
        with patch('builtins.open') as mock_open:
            mock_open.return_value.__enter__.return_value.read.return_value = "Generic x86 CPU"
            
            gadget = Xbox360Gadget()
            with pytest.raises(RuntimeError, match="This requires Raspberry Pi 4"):
                gadget._validate_hardware()
    
    def test_kernel_modules_loading(self, mock_kernel_modules):
        """Test kernel module loading sequence"""
        gadget = Xbox360Gadget()
        gadget._load_kernel_modules()
        
        # Verify correct modules are loaded in order
        expected_calls = [
            call(['modprobe', 'libcomposite'], check=True),
            call(['modprobe', 'dwc2'], check=True)
        ]
        mock_kernel_modules.assert_has_calls(expected_calls)
    
    def test_kernel_modules_loading_failure(self, mock_kernel_modules):
        """Test kernel module loading failure handling"""
        import subprocess
        mock_kernel_modules.side_effect = subprocess.CalledProcessError(1, 'modprobe')
        
        gadget = Xbox360Gadget()
        with pytest.raises(RuntimeError, match="Failed to load kernel modules"):
            gadget._load_kernel_modules()
    
    def test_usb_descriptor_creation(self, mock_usb_gadget):
        """Test USB descriptor file creation"""
        gadget = Xbox360Gadget()
        gadget._create_usb_descriptors()
        
        # Verify critical descriptor files are written
        assert '/sys/kernel/config/usb_gadget/xbox360_controller/idVendor' in mock_usb_gadget
        assert '/sys/kernel/config/usb_gadget/xbox360_controller/idProduct' in mock_usb_gadget
        
        # Verify Xbox 360 controller IDs
        assert mock_usb_gadget['/sys/kernel/config/usb_gadget/xbox360_controller/idVendor'] == '0x045e'
        assert mock_usb_gadget['/sys/kernel/config/usb_gadget/xbox360_controller/idProduct'] == '0x028e'
    
    def test_udc_activation(self, mock_usb_gadget):
        """Test USB Device Controller activation"""
        with patch('os.listdir') as mock_listdir:
            mock_listdir.return_value = ['20980000.usb']
            
            gadget = Xbox360Gadget()
            gadget._activate_udc()
            
            # Verify UDC is written to the correct file
            assert '/sys/kernel/config/usb_gadget/xbox360_controller/UDC' in mock_usb_gadget
            assert mock_usb_gadget['/sys/kernel/config/usb_gadget/xbox360_controller/UDC'] == '20980000.usb'
    
    def test_udc_activation_no_controller(self):
        """Test UDC activation failure when no controller available"""
        with patch('os.listdir', return_value=[]):
            gadget = Xbox360Gadget()
            with pytest.raises(RuntimeError, match="No USB Device Controller found"):
                gadget._activate_udc()
    
    def test_gadget_cleanup(self, mock_usb_gadget):
        """Test proper gadget cleanup"""
        with patch('os.path.exists', return_value=True), \
             patch('os.rmdir') as mock_rmdir:
            
            gadget = Xbox360Gadget()
            gadget._cleanup_gadget()
            
            # Verify cleanup sequence
            assert '/sys/kernel/config/usb_gadget/xbox360_controller/UDC' in mock_usb_gadget
            assert mock_usb_gadget['/sys/kernel/config/usb_gadget/xbox360_controller/UDC'] == ''
    
    def test_full_activation_sequence(self, mock_raspberry_pi, mock_kernel_modules, mock_usb_gadget):
        """Test complete gadget activation sequence"""
        with patch('os.listdir', return_value=['20980000.usb']):
            gadget = Xbox360Gadget()
            result = gadget.activate()
            
            assert result is True
            assert gadget.is_active is True
            
            # Verify activation sequence completed
            assert '/sys/kernel/config/usb_gadget/xbox360_controller/UDC' in mock_usb_gadget
    
    def test_activation_failure_recovery(self, mock_raspberry_pi, mock_kernel_modules):
        """Test activation failure and cleanup"""
        with patch('os.listdir', return_value=[]), \
             patch.object(Xbox360Gadget, '_cleanup_gadget') as mock_cleanup:
            
            gadget = Xbox360Gadget()
            result = gadget.activate()
            
            assert result is False
            assert gadget.is_active is False
            mock_cleanup.assert_called_once()  # Ensure cleanup on failure
    
    def test_status_monitoring(self, mock_raspberry_pi):
        """Test gadget status monitoring"""
        with patch('builtins.open', create=True) as mock_open:
            mock_open.return_value.__enter__.return_value.read.return_value = '20980000.usb'
            
            gadget = Xbox360Gadget()
            status = gadget.get_status()
            
            assert 'active' in status
            assert 'udc_device' in status
    
    def test_error_injection_hardware_failure(self):
        """Test error injection - hardware failure scenario"""
        with patch('builtins.open') as mock_open:
            mock_open.side_effect = FileNotFoundError("Hardware not available")
            
            gadget = Xbox360Gadget()
            with pytest.raises(RuntimeError):
                gadget._validate_hardware()
    
    def test_error_injection_permission_failure(self, mock_raspberry_pi):
        """Test error injection - permission failure scenario"""
        with patch('builtins.open') as mock_open:
            mock_open.side_effect = PermissionError("Access denied")
            
            gadget = Xbox360Gadget()
            with pytest.raises(PermissionError):
                gadget._create_usb_descriptors()