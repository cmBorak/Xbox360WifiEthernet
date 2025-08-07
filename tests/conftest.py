"""
Test configuration and fixtures for Xbox 360 Emulation Project
Provides hardware abstraction for testing without Pi hardware
"""
import pytest
import sys
from unittest.mock import Mock, MagicMock, patch
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

@pytest.fixture
def mock_raspberry_pi():
    """Mock Raspberry Pi hardware environment"""
    with patch('builtins.open', create=True) as mock_open:
        # Mock /proc/cpuinfo for Pi detection
        mock_open.return_value.__enter__.return_value.read.return_value = """
processor       : 0
model name      : ARMv7 Processor rev 3 (v7l)
BogoMIPS        : 108.00
Features        : half thumb fastmult vfp edsp neon vfpv3 tls vfpv4 idiva idivt vfpd32 lpae evtstrm crc32
CPU implementer : 0x41
CPU architecture: 7
CPU variant     : 0x0
CPU part        : 0xd08
CPU revision    : 3

Hardware        : BCM2835
Revision        : c03111
Serial          : 10000000fa7ec986
Model           : Raspberry Pi 4 Model B Rev 1.1
"""
        yield mock_open

@pytest.fixture
def mock_kernel_modules():
    """Mock kernel module operations"""
    with patch('subprocess.run') as mock_run:
        # Mock successful module loading
        mock_run.return_value.returncode = 0
        yield mock_run

@pytest.fixture
def mock_usb_gadget():
    """Mock USB gadget file system"""
    mock_data = {}
    
    def mock_file_operations(path, mode='r'):
        mock_file = Mock()
        if 'w' in mode:
            # Mock write operations
            mock_file.__enter__.return_value.write = lambda data: mock_data.update({path: data})
        else:
            # Mock read operations
            mock_file.__enter__.return_value.read = lambda: mock_data.get(path, "")
        return mock_file
    
    with patch('builtins.open', mock_file_operations):
        yield mock_data

@pytest.fixture
def mock_network_interfaces():
    """Mock network interface operations"""
    with patch('subprocess.run') as mock_run:
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "eth0\nwlan0\nusb0\n"
        yield mock_run

@pytest.fixture
def mock_system_checks():
    """Mock all system-level checks"""
    with patch('os.path.exists') as mock_exists, \
         patch('os.access') as mock_access, \
         patch('pwd.getpwnam') as mock_getpwnam:
        
        mock_exists.return_value = True
        mock_access.return_value = True
        mock_getpwnam.return_value = Mock(pw_uid=1000, pw_gid=1000)
        
        yield {
            'exists': mock_exists,
            'access': mock_access,
            'getpwnam': mock_getpwnam
        }