#!/usr/bin/env python3
"""
PCAP Splitter - Split PCAP files by session or flow
Usage: python split_pcap.py <input_path> --mode [session|flow] --max-bits 800
"""

import argparse
import os
from datetime import datetime
from scapy.all import rdpcap, wrpcap, IP, TCP, UDP, Raw
from collections import defaultdict

def get_session_key(packet):
    """Extract session key (5-tuple) from packet"""
    if IP not in packet:
        return None
    
    src_ip = packet[IP].src
    dst_ip = packet[IP].dst
    proto = packet[IP].proto
    
    src_port = dst_port = 0
    if TCP in packet:
        src_port = packet[TCP].sport
        dst_port = packet[TCP].dport
    elif UDP in packet:
        src_port = packet[UDP].sport
        dst_port = packet[UDP].dport
    
    # Normalize: smaller IP first for bidirectional sessions
    if src_ip < dst_ip:
        return (src_ip, src_port, dst_ip, dst_port, proto)
    else:
        return (dst_ip, dst_port, src_ip, src_port, proto)

def get_flow_key(packet):
    """Extract flow key (unidirectional 5-tuple) from packet"""
    if IP not in packet:
        return None
    
    src_ip = packet[IP].src
    dst_ip = packet[IP].dst
    proto = packet[IP].proto
    
    src_port = dst_port = 0
    if TCP in packet:
        src_port = packet[TCP].sport
        dst_port = packet[TCP].dport
    elif UDP in packet:
        src_port = packet[UDP].sport
        dst_port = packet[UDP].dport
    
    return (src_ip, src_port, dst_ip, dst_port, proto)

def trim_packets_to_bits(packets, max_bits):
    """Trim or pad packets to exactly max_bits"""
    from scapy.all import Ether, Raw, Packet
    
    max_bytes = max_bits // 8
    trimmed = []
    current_bytes = 0
    
    for packet in packets:
        packet_bytes = len(bytes(packet))
        
        if current_bytes + packet_bytes <= max_bytes:
            # Add full packet
            trimmed.append(packet)
            current_bytes += packet_bytes
        else:
            # Add partial packet to reach exactly max_bytes
            remaining = max_bytes - current_bytes
            if remaining > 0:
                packet_data = bytes(packet)[:remaining]
                # Create a minimal packet with the trimmed data
                trimmed_packet = Ether() / Raw(load=packet_data)
                trimmed.append(trimmed_packet)
            break
    
    # Pad with zero bytes if needed
    if current_bytes < max_bytes:
        padding_bytes = max_bytes - current_bytes
        padding_packet = Ether() / Raw(load=b'\x00' * padding_bytes)
        trimmed.append(padding_packet)
    
    return trimmed

def split_pcap(input_file, output_base_dir, mode='session', max_bits=800):
    """Split PCAP file by session or flow with bit limit"""
    
    print(f"[*] Reading PCAP file: {input_file}")
    try:
        packets = rdpcap(input_file)
    except Exception as e:
        print(f"[!] Error reading {input_file}: {e}")
        return
    
    # Group packets by session/flow
    grouped = defaultdict(list)
    
    for packet in packets:
        if mode == 'session':
            key = get_session_key(packet)
        else:  # flow
            key = get_flow_key(packet)
        
        if key:
            grouped[key].append(packet)
    
    # Get base filename without extension
    base_name = os.path.splitext(os.path.basename(input_file))[0]
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Save each session/flow
    print(f"[*] Found {len(grouped)} {mode}s")
    print(f"[*] Max bits per file: {max_bits} ({max_bits//8} bytes)")
    
    for idx, (key, pkts) in enumerate(grouped.items(), 1):
        # Trim/pad packets to exact bit size
        trimmed_pkts = trim_packets_to_bits(pkts, max_bits)
        
        output_filename = f"{base_name}_{timestamp}_{mode}_{idx:04d}.pcap"
        output_path = os.path.join(output_base_dir, output_filename)
        
        wrpcap(output_path, trimmed_pkts)
        print(f"[+] Saved {mode} {idx}: {output_filename} ({len(trimmed_pkts)} packets)")
    
    print(f"[*] Split complete: {len(grouped)} files created")

def process_directory_tree(input_path, output_base_dir, mode='session', max_bits=800):
    """Process PCAP files recursively, preserving directory structure"""
    
    if os.path.isfile(input_path):
        # Single file
        if input_path.endswith('.pcap'):
            output_dir = output_base_dir
            os.makedirs(output_dir, exist_ok=True)
            split_pcap(input_path, output_dir, mode, max_bits)
        else:
            print(f"[!] Not a PCAP file: {input_path}")
        return
    
    # Directory processing
    for root, dirs, files in os.walk(input_path):
        # Calculate relative path from input to preserve structure
        rel_path = os.path.relpath(root, input_path)
        
        # Create corresponding output directory
        if rel_path == '.':
            output_dir = output_base_dir
        else:
            output_dir = os.path.join(output_base_dir, rel_path)
        
        os.makedirs(output_dir, exist_ok=True)
        
        # Process all PCAP files in current directory
        pcap_files = [f for f in files if f.endswith('.pcap')]
        
        for pcap_file in pcap_files:
            input_file = os.path.join(root, pcap_file)
            print(f"\n{'='*60}")
            split_pcap(input_file, output_dir, mode, max_bits)

def main():
    parser = argparse.ArgumentParser(description='Split PCAP files by session or flow')
    parser.add_argument('input', help='Input PCAP file or directory path')
    parser.add_argument('--mode', choices=['session', 'flow'], default='session',
                        help='Split mode: session (bidirectional) or flow (unidirectional)')
    parser.add_argument('--output', default='1_splitted_pcap',
                        help='Output base directory (default: 1_splitted_pcap)')
    parser.add_argument('--max-bits', type=int, default=800,
                        help='Maximum bits per split file (default: 800)')
    
    args = parser.parse_args()
    
    # Create output directory if it doesn't exist
    os.makedirs(args.output, exist_ok=True)
    
    # Check input exists
    if not os.path.exists(args.input):
        print(f"[!] Error: Input path '{args.input}' not found")
        return
    
    process_directory_tree(args.input, args.output, args.mode, args.max_bits)

if __name__ == '__main__':
    main()