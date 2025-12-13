# Protocol Analysis & Reverse Engineering

This directory contains all materials related to reverse engineering the BlockBlueLight BLE protocol.

## Contents

### Documentation
- **`BLE_PROTOCOL_ANALYSIS.md`** - Complete protocol documentation with packet structure, commands, and implementation details

### Captured Logs
- **`btsnoop_hci.log`** - Android Bluetooth HCI snoop log captured while using the original app

### Analysis Scripts

Python scripts for protocol analysis and device control (requires `bleak` library).

#### control_device.py
Main control script for turning the device ON/OFF.

**Usage:**
```bash
python3 control_device.py scan   # Scan for device
python3 control_device.py on     # Turn ON
python3 control_device.py off    # Turn OFF
python3 control_device.py status # Query status
```

#### scan_devices.py
Scan for all BLE devices in range and display details.

**Usage:**
```bash
python3 scan_devices.py
```

#### inspect_device.py
Connect to device and inspect all services and characteristics.

**Usage:**
```bash
python3 inspect_device.py
```

#### analyze_ble.py
Analyze the HCI log file to decode BLE protocol.

**Usage:**
```bash
python3 analyze_ble.py
```

Requires Wireshark/tshark to be installed.

## Setup

```bash
python3 -m venv ../.venv
source ../.venv/bin/activate  # On Windows: ..\.venv\Scripts\activate
pip install bleak
```

## How the Protocol Was Reverse Engineered

1. **Captured HCI log** - Enabled Bluetooth HCI snoop log on Android
2. **Used original app** - Performed ON/OFF operations
3. **Analyzed with Wireshark** - Used tshark to filter and decode BLE packets
4. **Identified patterns** - Found command structure and differences between ON/OFF
5. **Verified checksum** - Confirmed XOR checksum algorithm
6. **Tested implementation** - Created Python scripts to validate findings

See `BLE_PROTOCOL_ANALYSIS.md` for complete details.

## Device Information

- **MAC Address**: 3C:AB:72:5E:F5:22
- **Device Name**: BLOCK3CAB725EF522
- **Service UUID**: 0000fff0-0000-1000-8000-00805f9b34fb
- **Write Characteristic**: 0000fff2-0000-1000-8000-00805f9b34fb (FFF2)
- **Notify Characteristic**: 0000fff1-0000-1000-8000-00805f9b34fb (FFF1)

**Note**: Characteristic naming is opposite of typical convention - FFF2 is for writing, FFF1 is for notifications.
