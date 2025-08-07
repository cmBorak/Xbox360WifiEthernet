"""
Xbox 360 Protocol Validation Tests
Tests Xbox 360 protocol compliance and authentication flows
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
from pathlib import Path
import struct
import binascii

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


class TestXbox360ProtocolCompliance:
    """Test Xbox 360 protocol compliance and validation"""
    
    def test_usb_descriptor_validation(self):
        """Test USB descriptor compliance with Xbox 360 specifications"""
        from xbox360_gadget import Xbox360Gadget
        
        gadget = Xbox360Gadget()
        
        # Xbox 360 Controller USB Specifications
        expected_specs = {
            'vendor_id': '0x045e',      # Microsoft
            'product_id': '0x028e',     # Xbox 360 Controller
            'device_class': '0x00',     # Device class
            'device_subclass': '0x00',  # Device subclass
            'device_protocol': '0x00',  # Device protocol
            'max_packet_size': '0x40',  # 64 bytes max packet size
            'manufacturer': 'Microsoft Corp.',
            'product': 'Controller (XBOX 360 For Windows)'
        }
        
        specs = gadget.get_usb_specifications()
        
        for key, expected_value in expected_specs.items():
            assert specs[key] == expected_value, f"USB spec mismatch: {key}"
    
    def test_xbox_controller_endpoints(self):
        """Test Xbox 360 controller endpoint configuration"""
        from xbox360_gadget import Xbox360Gadget
        
        gadget = Xbox360Gadget()
        endpoints = gadget.get_endpoint_configuration()
        
        # Xbox 360 Controller has 2 endpoints: IN and OUT
        assert len(endpoints) == 2
        
        # Endpoint 1: Interrupt IN (controller to host)
        in_endpoint = endpoints['ep1in']
        assert in_endpoint['type'] == 'interrupt'
        assert in_endpoint['direction'] == 'in'
        assert in_endpoint['max_packet_size'] == 32
        assert in_endpoint['interval'] == 4  # 4ms polling interval
        
        # Endpoint 2: Interrupt OUT (host to controller)
        out_endpoint = endpoints['ep1out']
        assert out_endpoint['type'] == 'interrupt'
        assert out_endpoint['direction'] == 'out'
        assert out_endpoint['max_packet_size'] == 32
        assert out_endpoint['interval'] == 8  # 8ms polling interval
    
    def test_xbox_input_report_format(self):
        """Test Xbox 360 controller input report packet format"""
        from xbox_auth import XboxAuthenticator
        
        auth = XboxAuthenticator()
        
        # Create a mock controller state
        controller_state = {
            'buttons': 0x0000,      # No buttons pressed
            'left_trigger': 0x00,   # Left trigger not pressed
            'right_trigger': 0x00,  # Right trigger not pressed
            'left_stick_x': 0x0000, # Left stick centered
            'left_stick_y': 0x0000, # Left stick centered
            'right_stick_x': 0x0000,# Right stick centered
            'right_stick_y': 0x0000 # Right stick centered
        }
        
        # Generate input report packet
        input_packet = auth.create_input_report(controller_state)
        
        # Validate packet structure (20 bytes total)
        assert len(input_packet) == 20
        
        # Packet header validation
        assert input_packet[0] == 0x00  # Message type
        assert input_packet[1] == 0x14  # Packet size (20 bytes)
        
        # Button data validation (bytes 2-3)
        button_data = struct.unpack('<H', input_packet[2:4])[0]
        assert button_data == controller_state['buttons']
        
        # Trigger data validation (bytes 4-5)
        assert input_packet[4] == controller_state['left_trigger']
        assert input_packet[5] == controller_state['right_trigger']
        
        # Stick data validation (bytes 6-13)
        left_x = struct.unpack('<h', input_packet[6:8])[0]
        left_y = struct.unpack('<h', input_packet[8:10])[0]
        right_x = struct.unpack('<h', input_packet[10:12])[0]
        right_y = struct.unpack('<h', input_packet[12:14])[0]
        
        assert left_x == controller_state['left_stick_x']
        assert left_y == controller_state['left_stick_y']
        assert right_x == controller_state['right_stick_x']
        assert right_y == controller_state['right_stick_y']
    
    def test_xbox_live_authentication_handshake(self):
        """Test Xbox Live authentication handshake sequence"""
        from xbox_auth import XboxAuthenticator
        
        auth = XboxAuthenticator()
        
        # Mock authentication challenge from Xbox
        challenge_packet = bytes([
            0x01, 0x03,  # Auth challenge message
            0x00, 0x08,  # Length: 8 bytes
            0x42, 0x00, 0x00, 0x00,  # Challenge data
            0x1A, 0x2B, 0x3C, 0x4D   # More challenge data
        ])
        
        # Process authentication challenge
        response = auth.process_auth_challenge(challenge_packet)
        
        # Validate response format
        assert len(response) >= 8
        assert response[0] == 0x01  # Auth response message type
        assert response[1] == 0x04  # Auth response subtype
        
        # Response should contain proper authentication data
        assert len(response) == struct.unpack('<H', response[2:4])[0] + 4
    
    def test_xbox_controller_button_mapping(self):
        """Test Xbox 360 controller button mapping"""
        from xbox_auth import XboxAuthenticator
        
        auth = XboxAuthenticator()
        
        # Test individual button mappings
        button_mappings = {
            'dpad_up': 0x0001,
            'dpad_down': 0x0002,
            'dpad_left': 0x0004,
            'dpad_right': 0x0008,
            'start': 0x0010,
            'back': 0x0020,
            'left_thumb': 0x0040,
            'right_thumb': 0x0080,
            'left_shoulder': 0x0100,
            'right_shoulder': 0x0200,
            'guide': 0x0400,
            'a': 0x1000,
            'b': 0x2000,
            'x': 0x4000,
            'y': 0x8000
        }
        
        for button_name, expected_value in button_mappings.items():
            button_state = {button_name: True}
            button_mask = auth.create_button_mask(button_state)
            assert button_mask & expected_value == expected_value
    
    def test_xbox_controller_stick_calibration(self):
        """Test Xbox 360 controller analog stick calibration"""
        from xbox_auth import XboxAuthenticator
        
        auth = XboxAuthenticator()
        
        # Test stick range validation (-32768 to 32767)
        test_values = [
            (-32768, True),   # Minimum value (valid)
            (-32769, False),  # Below minimum (invalid)
            (32767, True),    # Maximum value (valid)
            (32768, False),   # Above maximum (invalid)
            (0, True),        # Center position (valid)
            (-16384, True),   # Quarter left (valid)
            (16384, True)     # Quarter right (valid)
        ]
        
        for value, should_be_valid in test_values:
            is_valid = auth.validate_stick_value(value)
            assert is_valid == should_be_valid, f"Stick value {value} validation failed"
    
    def test_xbox_controller_trigger_range(self):
        """Test Xbox 360 controller trigger range validation"""
        from xbox_auth import XboxAuthenticator
        
        auth = XboxAuthenticator()
        
        # Test trigger range validation (0 to 255)
        test_values = [
            (0, True),     # Not pressed (valid)
            (127, True),   # Half pressed (valid)
            (255, True),   # Fully pressed (valid)
            (-1, False),   # Below minimum (invalid)
            (256, False)   # Above maximum (invalid)
        ]
        
        for value, should_be_valid in test_values.items():
            is_valid = auth.validate_trigger_value(value)
            assert is_valid == should_be_valid, f"Trigger value {value} validation failed"
    
    def test_xbox_rumble_command_processing(self):
        """Test Xbox 360 controller rumble command processing"""
        from xbox_auth import XboxAuthenticator
        
        auth = XboxAuthenticator()
        
        # Mock rumble command from Xbox
        rumble_packet = bytes([
            0x00, 0x08,  # Message type and length
            0x00, 0x00,  # Padding
            0x80, 0x40,  # Left motor (high), Right motor (low)
            0x00, 0x00   # Padding
        ])
        
        # Process rumble command
        rumble_data = auth.process_rumble_command(rumble_packet)
        
        # Validate rumble data extraction
        assert rumble_data['left_motor'] == 0x80   # High intensity
        assert rumble_data['right_motor'] == 0x40  # Medium intensity
        
        # Validate rumble response
        response = auth.create_rumble_response(rumble_data)
        assert len(response) == 8  # Standard response length
        assert response[0] == 0x00  # Acknowledgment message type
    
    def test_xbox_controller_connection_sequence(self):
        """Test Xbox 360 controller connection and enumeration sequence"""
        from xbox360_emulator import Xbox360Emulator
        
        emulator = Xbox360Emulator()
        
        # Mock USB enumeration sequence
        enumeration_steps = [
            'device_descriptor_request',
            'configuration_descriptor_request', 
            'string_descriptor_requests',
            'set_configuration',
            'set_interface',
            'xbox_initialization_sequence'
        ]
        
        for step in enumeration_steps:
            result = emulator.handle_enumeration_step(step)
            assert result is True, f"Enumeration step '{step}' failed"
    
    def test_xbox_protocol_timing_requirements(self):
        """Test Xbox 360 protocol timing requirements"""
        import time
        from xbox_auth import XboxAuthenticator
        
        auth = XboxAuthenticator()
        
        # Test input report timing (should be <= 8ms interval)
        start_time = time.time()
        for _ in range(10):
            auth.send_input_report({'buttons': 0})
            time.sleep(0.004)  # 4ms interval
        end_time = time.time()
        
        # Should complete within acceptable timing window
        total_time = end_time - start_time
        assert total_time <= 0.1  # 100ms maximum for 10 reports
    
    def test_xbox_controller_disconnection_handling(self):
        """Test Xbox 360 controller graceful disconnection"""
        from xbox360_emulator import Xbox360Emulator
        
        emulator = Xbox360Emulator()
        emulator.start_emulation()
        
        # Test graceful disconnection
        result = emulator.disconnect_controller()
        assert result is True
        
        # Verify clean state after disconnection
        status = emulator.get_connection_status()
        assert status['connected'] is False
        assert status['enumerated'] is False
    
    @pytest.mark.critical
    def test_xbox_protocol_compliance_comprehensive(self):
        """Comprehensive Xbox 360 protocol compliance test"""
        from xbox360_emulator import Xbox360Emulator
        from xbox_auth import XboxAuthenticator
        
        emulator = Xbox360Emulator()
        auth = XboxAuthenticator()
        
        # Test full protocol compliance
        compliance_tests = [
            ('usb_descriptors', self._test_usb_descriptors),
            ('endpoint_config', self._test_endpoint_configuration),
            ('input_reports', self._test_input_report_format),
            ('authentication', self._test_authentication_flow),
            ('button_mapping', self._test_button_mapping),
            ('analog_inputs', self._test_analog_input_validation),
            ('timing_compliance', self._test_timing_compliance)
        ]
        
        results = {}
        for test_name, test_func in compliance_tests:
            try:
                test_func(emulator, auth)
                results[test_name] = 'PASS'
            except Exception as e:
                results[test_name] = f'FAIL: {str(e)}'
        
        # All critical tests must pass
        failed_tests = [name for name, result in results.items() if result.startswith('FAIL')]
        assert len(failed_tests) == 0, f"Protocol compliance failures: {failed_tests}"
    
    def _test_usb_descriptors(self, emulator, auth):
        """Helper method for USB descriptor testing"""
        specs = emulator.gadget.get_usb_specifications()
        assert specs['vendor_id'] == '0x045e'
        assert specs['product_id'] == '0x028e'
    
    def _test_endpoint_configuration(self, emulator, auth):
        """Helper method for endpoint configuration testing"""
        endpoints = emulator.gadget.get_endpoint_configuration()
        assert len(endpoints) == 2
        assert 'ep1in' in endpoints
        assert 'ep1out' in endpoints
    
    def _test_input_report_format(self, emulator, auth):
        """Helper method for input report format testing"""
        state = {'buttons': 0, 'left_trigger': 0, 'right_trigger': 0}
        packet = auth.create_input_report(state)
        assert len(packet) == 20
    
    def _test_authentication_flow(self, emulator, auth):
        """Helper method for authentication flow testing"""
        challenge = bytes([0x01, 0x03, 0x00, 0x08, 0x42, 0x00, 0x00, 0x00])
        response = auth.process_auth_challenge(challenge)
        assert len(response) >= 8
    
    def _test_button_mapping(self, emulator, auth):
        """Helper method for button mapping testing"""
        button_mask = auth.create_button_mask({'a': True})
        assert button_mask & 0x1000 == 0x1000
    
    def _test_analog_input_validation(self, emulator, auth):
        """Helper method for analog input validation"""
        assert auth.validate_stick_value(0) is True
        assert auth.validate_trigger_value(255) is True
    
    def _test_timing_compliance(self, emulator, auth):
        """Helper method for timing compliance testing"""
        # Basic timing test - should complete within reasonable time
        start = time.time()
        auth.send_input_report({'buttons': 0})
        end = time.time()
        assert (end - start) < 0.01  # Less than 10ms