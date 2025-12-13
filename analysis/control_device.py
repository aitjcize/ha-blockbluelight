#!/usr/bin/env python3
"""
BLE Device Controller for BlockBlueLight devices
Simple script to turn the device ON/OFF via Bluetooth LE
"""

import asyncio
import sys
from bleak import BleakClient, BleakScanner

# Device will be auto-discovered by name pattern
DEVICE_NAME_PATTERN = "BLOCK"
SERVICE_UUID = "0000fff0-0000-1000-8000-00805f9b34fb"
# Note: FFF2 is WRITE, FFF1 is NOTIFY (opposite of typical naming!)
WRITE_CHAR_UUID = "0000fff2-0000-1000-8000-00805f9b34fb"
NOTIFY_CHAR_UUID = "0000fff1-0000-1000-8000-00805f9b34fb"

# Commands
TURN_ON_CMD = bytes([0x3A, 0x01, 0x20, 0x00, 0x01, 0x01, 0x23, 0x0A])
TURN_ON_CMD_2 = bytes([0x3A, 0x01, 0x20, 0x00, 0x01, 0x02, 0x24, 0x0A])  # Second command for timer mode
TURN_OFF_CMD = bytes([0x3A, 0x01, 0x20, 0x00, 0x01, 0x00, 0x22, 0x0A])
STATUS_QUERY_CMD = bytes([0x3A, 0x01, 0x10, 0x00, 0x00, 0x11, 0x0A])

def create_timer_command(minutes: int) -> bytes:
    """Create a command to set the timer duration.
    
    Args:
        minutes: Timer duration in minutes (1-60)
    
    Returns:
        Command bytes to set timer
    
    Note:
        The device timer value is in seconds (minutes * 60).
        The timer value is sent as a 2-byte big-endian integer.
        Checksum is the SUM of all bytes (excluding 0x3A start and 0x0A end).
    """
    # Timer value is in seconds
    seconds = minutes * 60
    
    # Timer value is 2 bytes, big-endian
    timer_high = (seconds >> 8) & 0xFF
    timer_low = seconds & 0xFF
    
    # Command structure: 3a 01 31 00 02 [timer_high] [timer_low] [checksum] 0a
    cmd = [0x3A, 0x01, 0x31, 0x00, 0x02, timer_high, timer_low]
    
    # Calculate checksum (SUM of all bytes except 0x3A start and 0x0A end)
    checksum = sum(cmd[1:]) & 0xFF
    
    cmd.append(checksum)
    cmd.append(0x0A)
    
    return bytes(cmd)

def notification_handler(sender, data):
    """Handle notifications from the device"""
    print(f"Received response: {data.hex(' ')}")
    
    # Parse response
    if len(data) > 5 and data[0] == 0x2A:  # Response starts with 0x2A
        cmd_type = data[2]
        if cmd_type == 0x10:  # Status response
            # Byte 5 is power state, bytes 8-9 are actual countdown timer
            if len(data) > 9:
                status_byte = data[5]
                # Bytes 6-7 appear to be initial timer setting
                initial_timer_high = data[6]
                initial_timer_low = data[7]
                initial_timer = (initial_timer_high << 8) | initial_timer_low
                
                # Bytes 8-9 are the actual countdown timer
                timer_high = data[8]
                timer_low = data[9]
                timer_seconds = (timer_high << 8) | timer_low
                
                # Display power status
                if status_byte == 0x01:
                    power_status = "ON"
                elif status_byte == 0x00:
                    power_status = "OFF"
                else:
                    power_status = f"UNKNOWN (0x{status_byte:02x})"
                
                # Display timer
                if timer_seconds > 0:
                    minutes = timer_seconds // 60
                    seconds = timer_seconds % 60
                    print(f"  → Device is {power_status}, Timer: {minutes}:{seconds:02d} ({timer_seconds}s remaining, initial: {initial_timer}s)")
                else:
                    print(f"  → Device is {power_status}, Timer: OFF")
        elif cmd_type == 0x20:  # Power command response
            print("  → Power command acknowledged")
        elif cmd_type == 0x31:  # Timer command response
            print("  → Timer command acknowledged")

async def find_device():
    """Scan for and return the BlockBlueLight device."""
    print(f"Scanning for devices with '{DEVICE_NAME_PATTERN}' in name...")
    devices = await BleakScanner.discover(timeout=5.0, return_adv=True)
    
    for address, (device, adv_data) in devices.items():
        if device.name and DEVICE_NAME_PATTERN in device.name.upper():
            print(f"Found device: {device.name} ({device.address})")
            print(f"  RSSI: {adv_data.rssi} dBm")
            if adv_data.service_uuids:
                print(f"  Services: {', '.join(adv_data.service_uuids)}")
            return device
    
    print(f"No device found with '{DEVICE_NAME_PATTERN}' in name!")
    return None

async def scan_for_device():
    """Scan for the device and display info."""
    device = await find_device()
    return device is not None

async def send_command(command_bytes, timer_minutes=None):
    """Send a command to the device.
    
    Args:
        command_bytes: The main command to send
        timer_minutes: Optional timer duration in minutes (1-60)
    
    Note:
        When setting a timer, send the timer command first, then turn on.
        The sequence is: Set Timer → Turn ON
    """
    device = await find_device()
    if not device:
        print("Device not found!")
        return
    
    print(f"Found device: {device.name} ({device.address})")
    
    async with BleakClient(device) as client:
        print(f"Connected: {client.is_connected}")

        # Enable notifications
        await client.start_notify(NOTIFY_CHAR_UUID, notification_handler)
        print("Notifications enabled")
        
        # If timer is specified with turn on command, set timer first
        if timer_minutes is not None and command_bytes == TURN_ON_CMD:
            timer_cmd = create_timer_command(timer_minutes)
            print(f"Setting timer to {timer_minutes} minutes...")
            print(f"Timer command bytes: {' '.join(f'{b:02x}' for b in timer_cmd)}")
            await client.write_gatt_char(WRITE_CHAR_UUID, timer_cmd, response=False)
            await asyncio.sleep(0.2)
            
            # Send turn-on command
            print("Sending turn ON command...")
            await client.write_gatt_char(WRITE_CHAR_UUID, TURN_ON_CMD, response=False)
            print("Command sent!")
        else:
            # Send main command normally
            await client.write_gatt_char(WRITE_CHAR_UUID, command_bytes, response=False)
            print("Command sent!")
        
        # Query status to see current state
        print("\nQuerying device status...")
        await client.write_gatt_char(WRITE_CHAR_UUID, STATUS_QUERY_CMD, response=False)
        
        # Wait for response
        await asyncio.sleep(1)
        
        print("Done!")

async def main():
    if len(sys.argv) < 2:
        print("Usage: python control_device.py <on|off|status|scan> [timer_minutes]")
        print("Examples:")
        print("  python control_device.py on          # Turn on without timer")
        print("  python control_device.py on 20       # Turn on with 20 minute timer")
        print("  python control_device.py off         # Turn off")
        print("  python control_device.py status      # Query status")
        print("  python control_device.py scan        # Scan for devices")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    timer_minutes = None
    
    # Parse timer argument if provided
    if len(sys.argv) >= 3 and command == "on":
        try:
            timer_minutes = int(sys.argv[2])
            if timer_minutes < 1 or timer_minutes > 60:
                print("Error: Timer must be between 1 and 60 minutes")
                sys.exit(1)
        except ValueError:
            print("Error: Timer must be a number")
            sys.exit(1)
    
    if command == "scan":
        await scan_for_device()
    elif command == "on":
        print("=" * 60)
        if timer_minutes:
            print(f"Sending TURN ON with {timer_minutes} minute timer...")
        else:
            print("Sending TURN ON...")
        print(f"Command bytes: {' '.join(f'{b:02x}' for b in TURN_ON_CMD)}")
        await send_command(TURN_ON_CMD, timer_minutes)
    elif command == "off":
        print("=" * 60)
        print("Sending TURN OFF...")
        print(f"Command bytes: {' '.join(f'{b:02x}' for b in TURN_OFF_CMD)}")
        await send_command(TURN_OFF_CMD)
    elif command == "status":
        print("=" * 60)
        print("Querying STATUS...")
        print(f"Command bytes: {' '.join(f'{b:02x}' for b in STATUS_QUERY_CMD)}")
        await send_command(STATUS_QUERY_CMD)
    else:
        print(f"Unknown command: {command}")
        print("Usage: python control_device.py <on|off|status|scan> [timer_minutes]")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
