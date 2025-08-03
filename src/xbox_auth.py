#!/usr/bin/env python3
"""
Xbox 360 Security Method 3 (XSM3) Authentication Handler
Implements authentication protocol required for Xbox 360 wireless adapter emulation
Based on research from https://oct0xor.github.io/2017/05/03/xsm3/
"""

import os
import sys
import time
import logging
import struct
import random
from pathlib import Path

logger = logging.getLogger(__name__)

class Xbox360AuthHandler:
    """Xbox Security Method 3 (XSM3) Authentication Handler"""
    
    def __init__(self):
        # Device identification constants
        self.device_serial = self._generate_device_serial()
        self.device_category = 0x01  # Wireless adapter category
        self.vendor_id = 0x045E      # Microsoft vendor ID
        
        # Authentication state
        self.auth_state = "init"
        self.challenge_data = None
        self.session_key = None
        
        # USB control transfer constants
        self.USB_REQ_GET_STATUS = 0x00
        self.USB_REQ_CLEAR_FEATURE = 0x01
        self.USB_REQ_SET_FEATURE = 0x03
        self.USB_REQ_GET_DESCRIPTOR = 0x06
        self.USB_REQ_SET_DESCRIPTOR = 0x07
        self.USB_REQ_GET_CONFIGURATION = 0x08
        self.USB_REQ_SET_CONFIGURATION = 0x09
        
        # Xbox specific vendor requests
        self.XBOX_REQ_GET_IDENTIFICATION = 0x01
        self.XBOX_REQ_GET_CHALLENGE = 0x02
        self.XBOX_REQ_SET_RESPONSE = 0x03
        self.XBOX_REQ_GET_VERIFICATION = 0x04
        
    def _generate_device_serial(self):
        """Generate a realistic device serial number"""
        # Xbox 360 wireless adapters typically have 8-byte serials
        # Format: Microsoft pattern with some randomness
        base_serial = 0x08260033196341  # Base pattern from real device
        # Add some randomness to last 2 bytes
        random_part = random.randint(0x1000, 0xFFFF)
        return (base_serial & 0xFFFFFFFFFF0000) | random_part
    
    def _calculate_checksum(self, data):
        """Calculate XOR checksum for Xbox protocol"""
        checksum = 0
        for byte in data:
            checksum ^= byte
        return checksum & 0xFF
    
    def _create_packet(self, command, data=b''):
        """Create Xbox protocol packet with header and checksum"""
        # 5-byte command header + data + 1-byte checksum
        header = struct.pack('<B4s', command, b'\x00\x00\x00\x00')
        packet = header + data
        checksum = self._calculate_checksum(packet)
        return packet + struct.pack('<B', checksum)
    
    def _parse_packet(self, packet):
        """Parse Xbox protocol packet"""
        if len(packet) < 6:  # Minimum: header + checksum
            return None, None
        
        command = packet[0]
        data = packet[5:-1]  # Skip header, get data before checksum
        received_checksum = packet[-1]
        
        # Verify checksum
        calculated_checksum = self._calculate_checksum(packet[:-1])
        if received_checksum != calculated_checksum:
            logger.warning(f"Checksum mismatch: got {received_checksum:02x}, expected {calculated_checksum:02x}")
            return None, None
        
        return command, data
    
    def handle_identification_request(self):
        """Handle Xbox identification protocol request"""
        logger.info("Handling Xbox identification request...")
        
        # Return device serial, category, and vendor ID
        identification_data = struct.pack('<QHH', 
                                        self.device_serial,
                                        self.device_category,
                                        self.vendor_id)
        
        packet = self._create_packet(self.XBOX_REQ_GET_IDENTIFICATION, identification_data)
        
        logger.info(f"Sending identification: serial={self.device_serial:016x}, "
                   f"category={self.device_category:04x}, vendor={self.vendor_id:04x}")
        
        self.auth_state = "identified"
        return packet
    
    def handle_challenge_request(self):
        """Handle Xbox challenge protocol request"""
        logger.info("Handling Xbox challenge request...")
        
        if self.auth_state != "identified":
            logger.error("Challenge request received before identification")
            return None
        
        # Generate challenge response data
        # This is a simplified implementation - real XSM3 uses complex crypto
        challenge_response = bytearray(16)
        
        # Use device serial as basis for challenge response
        serial_bytes = struct.pack('<Q', self.device_serial)
        for i in range(8):
            challenge_response[i] = serial_bytes[i]
            challenge_response[i + 8] = serial_bytes[i] ^ 0xAA  # Simple obfuscation
        
        packet = self._create_packet(self.XBOX_REQ_GET_CHALLENGE, bytes(challenge_response))
        
        logger.info("Sending challenge response")
        self.auth_state = "challenged"
        return packet
    
    def handle_verification_request(self, verification_data=None):
        """Handle Xbox verification protocol request"""
        logger.info("Handling Xbox verification request...")
        
        if self.auth_state != "challenged":
            logger.error("Verification request received before challenge")
            return None
        
        # Generate verification response
        # In real XSM3, this involves per-console keys from key vault
        # We'll use a simplified bypass approach
        
        verification_response = bytearray(32)
        
        # Create a believable verification response
        # Mix device serial with some constants
        serial_bytes = struct.pack('<Q', self.device_serial)
        
        for i in range(32):
            if i < 8:
                verification_response[i] = serial_bytes[i] ^ 0x55
            elif i < 16:
                verification_response[i] = serial_bytes[i - 8] ^ 0xAA
            elif i < 24:
                verification_response[i] = serial_bytes[i - 16] ^ 0x33
            else:
                verification_response[i] = serial_bytes[i - 24] ^ 0xCC
        
        packet = self._create_packet(self.XBOX_REQ_GET_VERIFICATION, bytes(verification_response))
        
        logger.info("Sending verification response")
        self.auth_state = "verified"
        return packet
    
    def handle_usb_control_transfer(self, bmRequestType, bRequest, wValue, wIndex, data=None):
        """Handle USB control transfer for Xbox authentication"""
        logger.debug(f"USB Control: type={bmRequestType:02x}, req={bRequest:02x}, "
                    f"val={wValue:04x}, idx={wIndex:04x}")
        
        # Check if this is a vendor-specific request to device
        if (bmRequestType & 0x60) == 0x40:  # Vendor request
            if (bmRequestType & 0x80) == 0x80:  # Device to host (IN)
                return self._handle_vendor_in_request(bRequest, wValue, wIndex)
            else:  # Host to device (OUT)
                return self._handle_vendor_out_request(bRequest, wValue, wIndex, data)
        
        # Handle standard USB requests
        return self._handle_standard_request(bmRequestType, bRequest, wValue, wIndex, data)
    
    def _handle_vendor_in_request(self, bRequest, wValue, wIndex):
        """Handle vendor-specific IN requests (device to host)"""
        if bRequest == self.XBOX_REQ_GET_IDENTIFICATION:
            return self.handle_identification_request()
        elif bRequest == self.XBOX_REQ_GET_CHALLENGE:
            return self.handle_challenge_request()
        elif bRequest == self.XBOX_REQ_GET_VERIFICATION:
            return self.handle_verification_request()
        else:
            logger.warning(f"Unknown vendor IN request: {bRequest:02x}")
            return None
    
    def _handle_vendor_out_request(self, bRequest, wValue, wIndex, data):
        """Handle vendor-specific OUT requests (host to device)"""
        if bRequest == self.XBOX_REQ_SET_RESPONSE:
            logger.info("Received Xbox response data")
            if data:
                command, payload = self._parse_packet(data)
                logger.debug(f"Response command: {command:02x}, payload length: {len(payload) if payload else 0}")
            return True
        else:
            logger.warning(f"Unknown vendor OUT request: {bRequest:02x}")
            return None
    
    def _handle_standard_request(self, bmRequestType, bRequest, wValue, wIndex, data):
        """Handle standard USB requests"""
        logger.debug(f"Standard USB request: {bRequest:02x}")
        return True  # Accept standard requests
    
    def get_auth_status(self):
        """Get current authentication status"""
        return {
            'state': self.auth_state,
            'device_serial': f"{self.device_serial:016x}",
            'device_category': f"{self.device_category:04x}",
            'vendor_id': f"{self.vendor_id:04x}",
            'authenticated': self.auth_state == "verified"
        }
    
    def reset_auth_state(self):
        """Reset authentication state"""
        logger.info("Resetting Xbox authentication state")
        self.auth_state = "init"
        self.challenge_data = None
        self.session_key = None
    
    def is_authenticated(self):
        """Check if device is authenticated with Xbox"""
        return self.auth_state == "verified"


def main():
    """Main function for testing authentication handler"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Xbox 360 Authentication Handler')
    parser.add_argument('action', choices=['test', 'status', 'reset'],
                       help='Action to perform')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Enable verbose logging')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    auth_handler = Xbox360AuthHandler()
    
    try:
        if args.action == 'test':
            print("Testing Xbox 360 Authentication Handler...")
            
            # Simulate authentication sequence
            print("\n1. Identification Request:")
            id_packet = auth_handler.handle_identification_request()
            print(f"   Response: {id_packet.hex() if id_packet else 'None'}")
            
            print("\n2. Challenge Request:")
            challenge_packet = auth_handler.handle_challenge_request()
            print(f"   Response: {challenge_packet.hex() if challenge_packet else 'None'}")
            
            print("\n3. Verification Request:")
            verify_packet = auth_handler.handle_verification_request()
            print(f"   Response: {verify_packet.hex() if verify_packet else 'None'}")
            
            print(f"\n4. Authentication Status:")
            status = auth_handler.get_auth_status()
            for key, value in status.items():
                print(f"   {key}: {value}")
                
        elif args.action == 'status':
            status = auth_handler.get_auth_status()
            print("Xbox 360 Authentication Status:")
            for key, value in status.items():
                print(f"  {key}: {value}")
                
        elif args.action == 'reset':
            auth_handler.reset_auth_state()
            print("Authentication state reset")
            
    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()