#!/usr/bin/env python3
"""
Xbox 360 USB Capture Analyzer
Parses USB captures to extract Xbox authentication protocol details
"""

import sys
import re
import struct
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class Xbox360CaptureAnalyzer:
    """Analyzes USB captures from Xbox 360 wireless adapter"""
    
    def __init__(self):
        self.control_transfers = []
        self.bulk_transfers = []
        self.authentication_sequence = []
        self.device_info = {}
    
    def parse_usbmon_log(self, log_file):
        """Parse Linux usbmon log format"""
        logger.info(f"Parsing usbmon log: {log_file}")
        
        with open(log_file, 'r') as f:
            for line_num, line in enumerate(f, 1):
                try:
                    self._parse_usbmon_line(line.strip(), line_num)
                except Exception as e:
                    logger.warning(f"Error parsing line {line_num}: {e}")
        
        logger.info(f"Parsed {len(self.control_transfers)} control transfers")
        logger.info(f"Parsed {len(self.bulk_transfers)} bulk transfers")
    
    def _parse_usbmon_line(self, line, line_num):
        """Parse individual usbmon log line"""
        if not line or line.startswith('#'):
            return
        
        # usbmon format: timestamp tag type dev:ep dir status length data
        parts = line.split()
        if len(parts) < 7:
            return
        
        timestamp = parts[0]
        tag = parts[1]
        transfer_type = parts[2]
        dev_ep = parts[3]
        direction = parts[4]
        status = parts[5]
        length = parts[6]
        data = ' '.join(parts[7:]) if len(parts) > 7 else ''
        
        # Parse device and endpoint
        if ':' in dev_ep:
            device, endpoint = dev_ep.split(':')
        else:
            return
        
        transfer = {
            'timestamp': timestamp,
            'tag': tag,
            'type': transfer_type,
            'device': device,
            'endpoint': endpoint,
            'direction': direction,
            'status': status,
            'length': int(length) if length.isdigit() else 0,
            'data': data,
            'line_num': line_num
        }
        
        # Categorize transfer type
        if transfer_type == 'S' and endpoint == '00':  # Setup on control endpoint
            self.control_transfers.append(transfer)
            self._analyze_control_transfer(transfer)
        elif endpoint in ['01', '02', '81', '82']:  # Bulk endpoints
            self.bulk_transfers.append(transfer)
    
    def _analyze_control_transfer(self, transfer):
        """Analyze control transfer for Xbox authentication"""
        data = transfer['data']
        if not data:
            return
        
        # Parse setup packet (8 bytes)
        data_bytes = []
        for hex_pair in data.split():
            if len(hex_pair) == 2 and all(c in '0123456789abcdefABCDEF' for c in hex_pair):
                data_bytes.append(int(hex_pair, 16))
        
        if len(data_bytes) >= 8:
            bmRequestType = data_bytes[0]
            bRequest = data_bytes[1]
            wValue = (data_bytes[3] << 8) | data_bytes[2]
            wIndex = (data_bytes[5] << 8) | data_bytes[4]
            wLength = (data_bytes[7] << 8) | data_bytes[6]
            
            # Check for Xbox vendor requests
            if (bmRequestType & 0x60) == 0x40:  # Vendor request
                auth_request = {
                    'timestamp': transfer['timestamp'],
                    'request_type': bmRequestType,
                    'request': bRequest,
                    'value': wValue,
                    'index': wIndex,
                    'length': wLength,
                    'direction': 'IN' if (bmRequestType & 0x80) else 'OUT',
                    'raw_data': data_bytes
                }
                
                self.authentication_sequence.append(auth_request)
                logger.info(f"Xbox Auth Request: type={bmRequestType:02x}, req={bRequest:02x}, "
                           f"val={wValue:04x}, idx={wIndex:04x}, len={wLength}")
    
    def analyze_authentication_sequence(self):
        """Analyze the complete authentication sequence"""
        logger.info("Analyzing Xbox 360 authentication sequence...")
        
        if not self.authentication_sequence:
            logger.warning("No authentication requests found in capture")
            return
        
        # Group by request type
        identification_requests = [r for r in self.authentication_sequence if r['request'] == 0x01]
        challenge_requests = [r for r in self.authentication_sequence if r['request'] == 0x02]
        verification_requests = [r for r in self.authentication_sequence if r['request'] == 0x04]
        
        logger.info(f"Found {len(identification_requests)} identification requests")
        logger.info(f"Found {len(challenge_requests)} challenge requests")
        logger.info(f"Found {len(verification_requests)} verification requests")
        
        # Analyze timing
        if len(self.authentication_sequence) > 1:
            first_time = float(self.authentication_sequence[0]['timestamp'])
            last_time = float(self.authentication_sequence[-1]['timestamp'])
            total_time = last_time - first_time
            logger.info(f"Authentication sequence duration: {total_time:.3f} seconds")
    
    def extract_device_descriptors(self):
        """Extract device descriptors from capture"""
        logger.info("Extracting device descriptors...")
        
        # Look for GET_DESCRIPTOR requests
        descriptor_requests = []
        for transfer in self.control_transfers:
            data_bytes = self._parse_hex_data(transfer['data'])
            if len(data_bytes) >= 8:
                bmRequestType = data_bytes[0]
                bRequest = data_bytes[1]
                if bRequest == 0x06:  # GET_DESCRIPTOR
                    descriptor_requests.append(transfer)
        
        logger.info(f"Found {len(descriptor_requests)} descriptor requests")
        
        for req in descriptor_requests:
            data_bytes = self._parse_hex_data(req['data'])
            if len(data_bytes) >= 8:
                wValue = (data_bytes[3] << 8) | data_bytes[2]
                descriptor_type = (wValue >> 8) & 0xFF
                descriptor_index = wValue & 0xFF
                
                desc_name = {
                    1: "DEVICE",
                    2: "CONFIGURATION", 
                    3: "STRING",
                    4: "INTERFACE",
                    5: "ENDPOINT"
                }.get(descriptor_type, f"UNKNOWN({descriptor_type})")
                
                logger.info(f"Descriptor request: {desc_name} index {descriptor_index}")
    
    def _parse_hex_data(self, data_str):
        """Parse hex data string into byte array"""
        data_bytes = []
        if data_str:
            for hex_pair in data_str.split():
                if len(hex_pair) == 2 and all(c in '0123456789abcdefABCDEF' for c in hex_pair):
                    data_bytes.append(int(hex_pair, 16))
        return data_bytes
    
    def generate_analysis_report(self, output_file):
        """Generate comprehensive analysis report"""
        logger.info(f"Generating analysis report: {output_file}")
        
        with open(output_file, 'w') as f:
            f.write("# Xbox 360 Wireless Adapter USB Capture Analysis\n\n")
            
            f.write("## Summary\n")
            f.write(f"- Control Transfers: {len(self.control_transfers)}\n")
            f.write(f"- Bulk Transfers: {len(self.bulk_transfers)}\n")
            f.write(f"- Authentication Requests: {len(self.authentication_sequence)}\n\n")
            
            f.write("## Authentication Sequence\n")
            for i, auth in enumerate(self.authentication_sequence, 1):
                f.write(f"### Request {i}\n")
                f.write(f"- Timestamp: {auth['timestamp']}\n")
                f.write(f"- Request Type: 0x{auth['request_type']:02x}\n")
                f.write(f"- Request: 0x{auth['request']:02x}\n")
                f.write(f"- Value: 0x{auth['value']:04x}\n")
                f.write(f"- Index: 0x{auth['index']:04x}\n")
                f.write(f"- Length: {auth['length']}\n")
                f.write(f"- Direction: {auth['direction']}\n")
                f.write(f"- Raw Data: {' '.join(f'{b:02x}' for b in auth['raw_data'][:16])}\n\n")
            
            f.write("## Implementation Notes\n")
            f.write("Based on this capture analysis, update the Xbox authentication handler with:\n")
            f.write("1. Exact request/response timing\n")
            f.write("2. Precise data formats and checksums\n")
            f.write("3. Error handling patterns\n")
            f.write("4. Device descriptor accuracy\n")
    
    def extract_protocol_constants(self):
        """Extract protocol constants for implementation"""
        constants = {
            'vendor_requests': set(),
            'request_values': set(),
            'data_patterns': []
        }
        
        for auth in self.authentication_sequence:
            constants['vendor_requests'].add(auth['request'])
            constants['request_values'].add(auth['value'])
            
            # Look for data patterns
            if auth['raw_data']:
                pattern = ' '.join(f'{b:02x}' for b in auth['raw_data'][:8])
                constants['data_patterns'].append(pattern)
        
        logger.info("Protocol Constants:")
        logger.info(f"  Vendor Requests: {sorted(constants['vendor_requests'])}")
        logger.info(f"  Request Values: {sorted(constants['request_values'])}")
        
        return constants


def main():
    """Main function for USB capture analysis"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Xbox 360 USB Capture Analyzer')
    parser.add_argument('capture_file', help='USB capture file to analyze')
    parser.add_argument('--format', choices=['usbmon', 'wireshark'], default='usbmon',
                       help='Capture file format')
    parser.add_argument('--output', '-o', help='Output analysis report file')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Enable verbose logging')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    analyzer = Xbox360CaptureAnalyzer()
    
    try:
        if args.format == 'usbmon':
            analyzer.parse_usbmon_log(args.capture_file)
        else:
            logger.error(f"Format {args.format} not implemented yet")
            sys.exit(1)
        
        analyzer.analyze_authentication_sequence()
        analyzer.extract_device_descriptors()
        analyzer.extract_protocol_constants()
        
        if args.output:
            analyzer.generate_analysis_report(args.output)
        
        logger.info("Analysis complete!")
        
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()