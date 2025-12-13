#!/usr/bin/env python3
import subprocess
import sys
from collections import defaultdict

def hex_to_ascii(hex_str):
    """Convert hex string to ASCII if printable"""
    try:
        bytes_data = bytes.fromhex(hex_str.replace(':', ''))
        ascii_str = bytes_data.decode('ascii', errors='ignore')
        return ascii_str if ascii_str.isprintable() else None
    except:
        return None

def analyze_commands():
    # Extract all write commands to handle 0x0010 (FFF1 characteristic)
    cmd = [
        'tshark', '-r', 'btsnoop_hci.log',
        '-Y', 'btatt.opcode == 0x52 && btatt.handle == 0x0010',
        '-T', 'fields',
        '-e', 'frame.number',
        '-e', 'frame.time_relative',
        '-e', 'btatt.value'
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    commands = []
    for line in result.stdout.strip().split('\n'):
        if not line:
            continue
        parts = line.split('\t')
        if len(parts) >= 3:
            frame_num = parts[0]
            timestamp = float(parts[1])
            value = parts[2]
            commands.append((frame_num, timestamp, value))
    
    print("=" * 80)
    print("ALL WRITE COMMANDS TO HANDLE 0x0010 (FFF1 Characteristic)")
    print("=" * 80)
    
    # Group similar commands
    command_groups = defaultdict(list)
    
    for frame_num, timestamp, value in commands:
        # Parse the hex value
        hex_bytes = value.replace(':', '')
        
        # Try to decode
        ascii_repr = hex_to_ascii(hex_bytes)
        
        print(f"\nFrame {frame_num:4s} @ {timestamp:8.2f}s")
        print(f"  Raw Hex: {value}")
        print(f"  Bytes:   {' '.join([hex_bytes[i:i+2] for i in range(0, len(hex_bytes), 2)])}")
        
        if ascii_repr:
            print(f"  ASCII:   {repr(ascii_repr)}")
        
        # Categorize command
        if hex_bytes.startswith('3a0120'):
            command_groups['POWER'].append((frame_num, timestamp, value))
            if '000100' in hex_bytes:
                print(f"  >>> LIKELY: TURN OFF COMMAND")
            elif '000101' in hex_bytes:
                print(f"  >>> LIKELY: TURN ON COMMAND")
        elif hex_bytes.startswith('3a0110'):
            command_groups['STATUS_QUERY'].append((frame_num, timestamp, value))
            print(f"  >>> STATUS QUERY")
        elif hex_bytes.startswith('3a0140'):
            command_groups['QUERY_40'].append((frame_num, timestamp, value))
            print(f"  >>> QUERY TYPE 0x40")
        elif hex_bytes.startswith('3a0174'):
            command_groups['CUSTOM_NAME'].append((frame_num, timestamp, value))
            print(f"  >>> CUSTOM NAME SETTING")
        elif hex_bytes.startswith('3a0152'):
            command_groups['COMMAND_52'].append((frame_num, timestamp, value))
        elif hex_bytes.startswith('3a0142'):
            command_groups['COMMAND_42'].append((frame_num, timestamp, value))
        elif hex_bytes.startswith('3a0175'):
            command_groups['COMMAND_75'].append((frame_num, timestamp, value))
    
    print("\n" + "=" * 80)
    print("COMMAND SUMMARY")
    print("=" * 80)
    
    for cmd_type, cmd_list in sorted(command_groups.items()):
        print(f"\n{cmd_type}: {len(cmd_list)} occurrences")
        if cmd_type == 'POWER':
            print("  Commands:")
            for frame, ts, val in cmd_list[:10]:  # Show first 10
                print(f"    Frame {frame}: {val}")

if __name__ == '__main__':
    analyze_commands()
