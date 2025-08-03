#!/usr/bin/env python3
"""
Xbox 360 FunctionFS Implementation
Custom USB function using FunctionFS to handle Xbox authentication and networking
"""

import os
import sys
import time
import struct
import select
import logging
import threading
from pathlib import Path
from xbox_auth import Xbox360AuthHandler

logger = logging.getLogger(__name__)

class Xbox360FunctionFS:
    """Xbox 360 USB Function using FunctionFS"""
    
    def __init__(self, mount_point="/dev/xbox360_ffs"):
        self.mount_point = Path(mount_point)
        self.auth_handler = Xbox360AuthHandler()
        self.is_running = False
        self.ep0_fd = None
        self.ep_in_fd = None
        self.ep_out_fd = None
        self.control_thread = None
        
        # USB Descriptors for Xbox 360 Wireless Network Adapter
        self.descriptors = self._create_usb_descriptors()
        self.strings = self._create_usb_strings()
    
    def _create_usb_descriptors(self):
        """Create USB descriptors for Xbox 360 wireless adapter"""
        
        # USB 2.0 Device Descriptor
        device_desc = struct.pack('<BBHBBBBHHHBBBB',
            18,     # bLength
            1,      # bDescriptorType (Device)
            0x0200, # bcdUSB (USB 2.0)
            0xFF,   # bDeviceClass (Vendor Specific)
            0x00,   # bDeviceSubClass
            0x00,   # bDeviceProtocol
            64,     # bMaxPacketSize0
            0x045E, # idVendor (Microsoft)
            0x02A8, # idProduct (Xbox 360 Wireless Network Adapter)
            0x0202, # bcdDevice (2.02)
            1,      # iManufacturer
            2,      # iProduct
            3,      # iSerialNumber
            1       # bNumConfigurations
        )
        
        # Configuration Descriptor
        config_desc = struct.pack('<BBHBBBBB',
            9,      # bLength
            2,      # bDescriptorType (Configuration)
            32,     # wTotalLength (9 + 9 + 7 + 7)
            1,      # bNumInterfaces
            1,      # bConfigurationValue
            0,      # iConfiguration
            0x80,   # bmAttributes (Bus powered)
            250     # bMaxPower (500mA)
        )
        
        # Interface Descriptor
        interface_desc = struct.pack('<BBBBBBBBB',
            9,      # bLength
            4,      # bDescriptorType (Interface)
            0,      # bInterfaceNumber
            0,      # bAlternateSetting
            2,      # bNumEndpoints
            0xFF,   # bInterfaceClass (Vendor Specific)
            0x00,   # bInterfaceSubClass
            0x00,   # bInterfaceProtocol
            0       # iInterface
        )
        
        # Endpoint Descriptor (IN)
        ep_in_desc = struct.pack('<BBBBBHB',
            7,      # bLength
            5,      # bDescriptorType (Endpoint)
            0x81,   # bEndpointAddress (IN)
            0x02,   # bmAttributes (Bulk)
            64,     # wMaxPacketSize
            0       # bInterval
        )
        
        # Endpoint Descriptor (OUT)
        ep_out_desc = struct.pack('<BBBBBHB',
            7,      # bLength
            5,      # bDescriptorType (Endpoint)
            0x02,   # bEndpointAddress (OUT)
            0x02,   # bmAttributes (Bulk)
            64,     # wMaxPacketSize
            0       # bInterval
        )
        
        # Combine all descriptors
        descriptors = (
            device_desc +
            config_desc + 
            interface_desc +
            ep_in_desc +
            ep_out_desc
        )
        
        return descriptors
    
    def _create_usb_strings(self):
        """Create USB string descriptors"""
        strings = [
            "Microsoft Corp.",                    # Manufacturer
            "Wireless Network Adapter Boot",     # Product
            f"{self.auth_handler.device_serial:016x}"  # Serial Number
        ]
        
        # Encode strings in FunctionFS format
        encoded_strings = b''
        for string in strings:
            encoded = string.encode('utf-8')
            encoded_strings += struct.pack('<H', len(encoded)) + encoded
        
        return encoded_strings
    
    def setup_functionfs_mount(self):
        """Setup FunctionFS mount point"""
        logger.info("Setting up FunctionFS mount...")
        
        # Create mount point
        self.mount_point.mkdir(parents=True, exist_ok=True)
        
        # Check if already mounted
        with open('/proc/mounts', 'r') as f:
            if str(self.mount_point) in f.read():
                logger.info("FunctionFS already mounted")
                return True
        
        # Mount FunctionFS
        mount_cmd = f"mount -t functionfs xbox360_ffs {self.mount_point}"
        result = os.system(mount_cmd)
        if result != 0:
            raise RuntimeError(f"Failed to mount FunctionFS: {result}")
        
        logger.info(f"✅ FunctionFS mounted at {self.mount_point}")
        return True
    
    def initialize_functionfs(self):
        """Initialize FunctionFS endpoints and descriptors"""
        logger.info("Initializing FunctionFS...")
        
        # Open ep0 for control transfers
        ep0_path = self.mount_point / "ep0"
        if not ep0_path.exists():
            raise RuntimeError(f"FunctionFS ep0 not found at {ep0_path}")
        
        self.ep0_fd = os.open(ep0_path, os.O_RDWR)
        
        # Write descriptors to ep0
        logger.info("Writing USB descriptors...")
        os.write(self.ep0_fd, self.descriptors)
        
        # Write strings to ep0
        logger.info("Writing USB strings...")
        os.write(self.ep0_fd, self.strings)
        
        # Open bulk endpoints
        ep1_path = self.mount_point / "ep1"  # IN endpoint
        ep2_path = self.mount_point / "ep2"  # OUT endpoint
        
        # Wait for endpoints to become available
        for i in range(10):
            if ep1_path.exists() and ep2_path.exists():
                break
            time.sleep(0.5)
        else:
            raise RuntimeError("FunctionFS endpoints not available")
        
        self.ep_in_fd = os.open(ep1_path, os.O_RDWR)
        self.ep_out_fd = os.open(ep2_path, os.O_RDWR)
        
        logger.info("✅ FunctionFS initialized")
        return True
    
    def handle_control_transfers(self):
        """Handle USB control transfers on ep0"""
        logger.info("Starting control transfer handler...")
        
        while self.is_running:
            try:
                # Use select to check for control requests
                ready, _, _ = select.select([self.ep0_fd], [], [], 1.0)
                
                if ready:
                    # Read control request
                    try:
                        data = os.read(self.ep0_fd, 8)  # Standard setup packet size
                        if len(data) >= 8:
                            self._process_control_request(data)
                    except OSError as e:
                        if e.errno != 11:  # EAGAIN is normal
                            logger.error(f"Control read error: {e}")
                
            except Exception as e:
                logger.error(f"Control transfer error: {e}")
                if self.is_running:
                    time.sleep(1)
    
    def _process_control_request(self, setup_data):
        """Process USB control setup request"""
        if len(setup_data) < 8:
            return
        
        # Parse setup packet
        bmRequestType, bRequest, wValue, wIndex, wLength = struct.unpack('<BBHHH', setup_data)
        
        logger.debug(f"Control Request: type={bmRequestType:02x}, req={bRequest:02x}, "
                    f"val={wValue:04x}, idx={wIndex:04x}, len={wLength}")
        
        # Handle Xbox authentication requests
        response = self.auth_handler.handle_usb_control_transfer(
            bmRequestType, bRequest, wValue, wIndex
        )
        
        if response:
            try:
                # Send response back through ep0
                os.write(self.ep0_fd, response[:wLength] if len(response) > wLength else response)
                logger.debug(f"Sent control response: {len(response)} bytes")
            except OSError as e:
                logger.error(f"Failed to send control response: {e}")
        else:
            # Send zero-length packet for unsupported requests
            try:
                os.write(self.ep0_fd, b'')
            except OSError:
                pass
    
    def handle_bulk_transfers(self):
        """Handle bulk data transfers"""
        logger.info("Starting bulk transfer handler...")
        
        while self.is_running:
            try:
                # Check for outgoing data from Xbox
                ready, _, _ = select.select([self.ep_out_fd], [], [], 1.0)
                
                if ready:
                    try:
                        data = os.read(self.ep_out_fd, 1024)
                        if data:
                            logger.debug(f"Received bulk data: {len(data)} bytes")
                            # Process network data here
                            self._process_network_data(data)
                    except OSError as e:
                        if e.errno != 11:  # EAGAIN is normal
                            logger.error(f"Bulk read error: {e}")
                
            except Exception as e:
                logger.error(f"Bulk transfer error: {e}")
                if self.is_running:
                    time.sleep(1)
    
    def _process_network_data(self, data):
        """Process network data from Xbox"""
        # This is where we would handle network packets
        # For now, just log the data
        logger.debug(f"Processing network data: {data.hex()}")
        
        # Echo data back (for testing)
        try:
            os.write(self.ep_in_fd, data)
        except OSError as e:
            logger.error(f"Failed to send network data: {e}")
    
    def start(self):
        """Start the FunctionFS Xbox 360 emulator"""
        logger.info("🎮 Starting Xbox 360 FunctionFS Emulator...")
        
        try:
            self.setup_functionfs_mount()
            self.initialize_functionfs()
            
            self.is_running = True
            
            # Start control transfer handler in separate thread
            self.control_thread = threading.Thread(
                target=self.handle_control_transfers,
                daemon=True
            )
            self.control_thread.start()
            
            # Start bulk transfer handler in separate thread
            self.bulk_thread = threading.Thread(
                target=self.handle_bulk_transfers,
                daemon=True
            )
            self.bulk_thread.start()
            
            logger.info("✅ Xbox 360 FunctionFS Emulator started")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start FunctionFS emulator: {e}")
            return False
    
    def stop(self):
        """Stop the FunctionFS Xbox 360 emulator"""
        logger.info("🛑 Stopping Xbox 360 FunctionFS Emulator...")
        
        self.is_running = False
        
        # Wait for threads to finish
        if self.control_thread and self.control_thread.is_alive():
            self.control_thread.join(timeout=5)
        
        # Close file descriptors
        for fd in [self.ep0_fd, self.ep_in_fd, self.ep_out_fd]:
            if fd is not None:
                try:
                    os.close(fd)
                except OSError:
                    pass
        
        # Unmount FunctionFS
        try:
            os.system(f"umount {self.mount_point}")
        except:
            pass
        
        logger.info("🛑 Xbox 360 FunctionFS Emulator stopped")
    
    def get_status(self):
        """Get FunctionFS status"""
        return {
            'running': self.is_running,
            'mount_point': str(self.mount_point),
            'auth_status': self.auth_handler.get_auth_status(),
            'endpoints_open': all([
                self.ep0_fd is not None,
                self.ep_in_fd is not None,
                self.ep_out_fd is not None
            ])
        }


def main():
    """Main function for testing FunctionFS implementation"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Xbox 360 FunctionFS Implementation')
    parser.add_argument('action', choices=['start', 'stop', 'status', 'test'],
                       help='Action to perform')
    parser.add_argument('--mount-point', default='/dev/xbox360_ffs',
                       help='FunctionFS mount point')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Enable verbose logging')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    functionfs = Xbox360FunctionFS(args.mount_point)
    
    try:
        if args.action == 'start':
            if functionfs.start():
                try:
                    # Keep running until interrupted
                    while functionfs.is_running:
                        time.sleep(1)
                except KeyboardInterrupt:
                    logger.info("Received interrupt signal")
                finally:
                    functionfs.stop()
            else:
                sys.exit(1)
                
        elif args.action == 'stop':
            functionfs.stop()
            
        elif args.action == 'status':
            status = functionfs.get_status()
            print("Xbox 360 FunctionFS Status:")
            for key, value in status.items():
                print(f"  {key}: {value}")
                
        elif args.action == 'test':
            print("Testing Xbox 360 FunctionFS...")
            success = functionfs.start()
            if success:
                print("✅ FunctionFS started successfully")
                time.sleep(2)
                functionfs.stop()
                print("✅ FunctionFS stopped successfully")
            else:
                print("❌ FunctionFS failed to start")
                sys.exit(1)
                
    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()