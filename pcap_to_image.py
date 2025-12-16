#!/usr/bin/env python3
"""
PCAP to Image Converter - Convert PCAP files to grayscale images
Usage: python pcap_to_image.py --input <input_dir> --mode [header|full] --size 28x28
"""

import argparse
import os
import numpy as np
from PIL import Image
from scapy.all import rdpcap, raw, Ether, IP, TCP, UDP

def get_header_bytes(packet):
    """Extract only header bytes from packet"""
    header_bytes = bytearray()
    
    # Ethernet header (if present)
    if Ether in packet:
        eth_header = bytes(packet[Ether])[:14]  # Ethernet header is 14 bytes
        header_bytes.extend(eth_header)
    
    # IP header
    if IP in packet:
        ip_header_len = packet[IP].ihl * 4  # IHL is in 32-bit words
        ip_start = len(header_bytes)
        ip_bytes = bytes(packet[IP])[:ip_header_len]
        header_bytes.extend(ip_bytes)
    
    # TCP header
    if TCP in packet:
        tcp_header_len = packet[TCP].dataofs * 4  # dataofs is in 32-bit words
        tcp_bytes = bytes(packet[TCP])[:tcp_header_len]
        header_bytes.extend(tcp_bytes)
    # UDP header
    elif UDP in packet:
        udp_bytes = bytes(packet[UDP])[:8]  # UDP header is always 8 bytes
        header_bytes.extend(udp_bytes)
    
    return bytes(header_bytes)

def packet_to_bytes(packet, mode='full'):
    """Extract bytes from packet based on mode"""
    if mode == 'header':
        return get_header_bytes(packet)
    else:  # full
        return raw(packet)

def pcap_to_image(pcap_file, output_path, mode='full', size=(28, 28)):
    """Convert PCAP file to grayscale image with specific size"""
    
    print(f"[*] Processing: {os.path.basename(pcap_file)}")
    
    try:
        packets = rdpcap(pcap_file)
    except Exception as e:
        print(f"[!] Error reading {pcap_file}: {e}")
        return False
    
    # Collect all bytes from packets
    all_bytes = bytearray()
    for packet in packets:
        packet_bytes = packet_to_bytes(packet, mode)
        all_bytes.extend(packet_bytes)
    
    if len(all_bytes) == 0:
        print(f"[!] No data extracted from {pcap_file}")
        return False
    
    width, height = size
    target_size = width * height
    
    # Trim or pad to exact target size
    if len(all_bytes) > target_size:
        # Trim to target size
        all_bytes = all_bytes[:target_size]
        print(f"    Trimmed from {len(all_bytes)} to {target_size} bytes")
    elif len(all_bytes) < target_size:
        # Pad with zeros
        padding_needed = target_size - len(all_bytes)
        all_bytes.extend([0] * padding_needed)
        print(f"    Padded with {padding_needed} zeros to reach {target_size} bytes")
    
    # Convert to numpy array and reshape
    img_array = np.array(list(all_bytes), dtype=np.uint8).reshape(height, width)
    
    # Create grayscale image
    img = Image.fromarray(img_array, mode='L')
    
    # Save image
    img.save(output_path)
    print(f"[+] Saved image: {os.path.basename(output_path)} ({width}x{height})")
    
    return True

def process_directory_tree(input_base_dir, output_base_dir, mode='full', size=(28, 28)):
    """Process all PCAP files recursively, preserving directory structure"""
    
    total_files = 0
    successful = 0
    
    print(f"[*] Mode: {mode}")
    print(f"[*] Image size: {size[0]}x{size[1]} ({size[0]*size[1]} bytes)")
    print(f"[*] Scanning directory tree...\n")
    
    for root, dirs, files in os.walk(input_base_dir):
        # Calculate relative path to preserve structure
        rel_path = os.path.relpath(root, input_base_dir)
        
        # Create corresponding output directory
        if rel_path == '.':
            output_dir = output_base_dir
        else:
            output_dir = os.path.join(output_base_dir, rel_path)
        
        # Get all PCAP files in current directory
        pcap_files = [f for f in files if f.endswith('.pcap')]
        
        if pcap_files:
            os.makedirs(output_dir, exist_ok=True)
            print(f"Directory: {rel_path if rel_path != '.' else '(root)'}")
            print(f"Found {len(pcap_files)} PCAP files")
            
            for pcap_file in pcap_files:
                total_files += 1
                input_path = os.path.join(root, pcap_file)
                
                # Create output filename (replace .pcap with .png)
                output_filename = os.path.splitext(pcap_file)[0] + '.png'
                output_path = os.path.join(output_dir, output_filename)
                
                if pcap_to_image(input_path, output_path, mode, size):
                    successful += 1
            
            print()  # Empty line between directories
    
    print(f"{'='*60}")
    print(f"[*] Conversion complete: {successful}/{total_files} files converted")

def parse_size(size_str):
    """Parse size string like '28x28' into tuple (28, 28)"""
    try:
        parts = size_str.lower().split('x')
        if len(parts) != 2:
            raise ValueError
        width = int(parts[0])
        height = int(parts[1])
        if width <= 0 or height <= 0:
            raise ValueError
        return (width, height)
    except:
        raise argparse.ArgumentTypeError(
            f"Size must be in format WIDTHxHEIGHT (e.g., 28x28), got: {size_str}"
        )

def main():
    parser = argparse.ArgumentParser(description='Convert PCAP files to grayscale images')
    parser.add_argument('--input', default='1_splitted_pcap',
                        help='Input directory containing PCAP files (default: 1_splitted_pcap)')
    parser.add_argument('--output', default='2_Images',
                        help='Output directory for images (default: 2_Images)')
    parser.add_argument('--mode', choices=['header', 'full'], default='full',
                        help='Conversion mode: header (headers only) or full (entire packet)')
    parser.add_argument('--size', type=parse_size, default='28x28',
                        help='Image size as WIDTHxHEIGHT (default: 28x28)')
    
    args = parser.parse_args()
    
    # Create output directory if it doesn't exist
    os.makedirs(args.output, exist_ok=True)
    
    # Check input directory exists
    if not os.path.exists(args.input):
        print(f"[!] Error: Input directory '{args.input}' not found")
        return
    
    process_directory_tree(args.input, args.output, args.mode, args.size)

if __name__ == '__main__':
    main()