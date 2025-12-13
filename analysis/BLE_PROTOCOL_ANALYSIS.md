# BLE Protocol Analysis - Device 3C:AB:72:5E:F5:22

## Device Information
- **MAC Address**: 3C:AB:72:5E:F5:22
- **Device Name**: BLOCK3CAB725EF522
- **Pairing**: Not required
- **Encryption**: None

## GATT Services & Characteristics

### Service: FFF0 (Unknown/Custom Service)
This is the main service for device control.

#### Characteristics:
**IMPORTANT**: The characteristic naming is opposite of typical convention!

1. **FFF2** (Write Characteristic)
   - **Properties**: Write, Write Without Response
   - **Purpose**: Command channel (send commands to device)
   - **Handle in log**: 0x0010
   
2. **FFF1** (Notify Characteristic)
   - **Properties**: Notify
   - **Purpose**: Response/notification channel (receive data from device)
   - **Handle in log**: 0x0012
   - **CCCD**: Handle 0x0013 (must enable notifications)

### Standard Services:
- **1800**: Generic Access (Device Name, Appearance)
- **1801**: Generic Attribute

## Protocol Format

All commands follow this structure:
```
[START] [LENGTH] [COMMAND] [DATA...] [CHECKSUM] [END]
```

- **START**: `0x3A` (`:`)
- **LENGTH**: `0x01` (1 byte for most commands)
- **COMMAND**: Command type byte
- **DATA**: Variable length data
- **CHECKSUM**: **SUM** of all bytes from LENGTH to end of DATA (masked to 8 bits)
- **END**: `0x0A` (newline `\n`)

**Important**: The checksum is calculated as the **sum** (not XOR) of bytes, excluding the start byte (0x3A) and end byte (0x0A).

## Protocol Specification

### Command Types (Write to FFF2)

| Command | Hex  | Purpose | Data Format |
|---------|------|---------|-------------|
| Power Control | `0x20` | Turn device ON/OFF | `3A 01 20 00 01 [STATE] [CHECKSUM] 0A`<br>STATE: `0x01`=ON, `0x00`=OFF |
| Status Query | `0x10` | Query device status | `3A 01 10 00 00 11 0A` |
| Timer Set | `0x31` | Set countdown timer | `3A 01 31 00 02 [HIGH] [LOW] [CHECKSUM] 0A`<br>Timer in seconds (2-byte big-endian) |
| Query 0x40 | `0x40` | Query device parameters | `3A 01 40 00 00 41 0A` |
| Custom Name | `0x74` | Set custom preset names | `3A 01 74 00 [LEN] [ASCII...] [CHECKSUM] 0A` |

### Notification Types (Receive from FFF1)

All notifications start with `0x2A` instead of `0x3A`.

| Response | Hex  | Format | Contains |
|----------|------|--------|----------|
| Power Ack | `0x20` | `2A 01 20 00 00 21 0A` | Acknowledgment of power command |
| Status | `0x10` | `2A 01 10 00 05 [STATE] [TIMER_H] [TIMER_L] [CHK] 0A` | Power state + Timer remaining |
| Timer Ack | `0x31` | `2A 01 31 00 00 32 0A` | Acknowledgment of timer command |
| Query 0x40 | `0x40` | `2A 01 40 00 07 [DATA...] [CHK] 0A` | Device parameters |

### Status Notification Details (0x10)

The status notification is sent periodically and contains real-time device state:

**Format**: `2A 01 10 00 05 [STATE] [INITIAL_HIGH] [INITIAL_LOW] [TIMER_HIGH] [TIMER_LOW] [CHECKSUM] 0A`

**Byte Positions**:
- Byte 0: `0x2A` - Notification start
- Byte 1: `0x01` - Length
- Byte 2: `0x10` - Status response type
- Byte 3-4: `0x00 0x05` - Fixed parameters
- **Byte 5**: Power state
  - `0x01` = Device ON
  - `0x00` = Device OFF
- **Byte 6-7**: Initial timer setting (2-byte big-endian, in seconds)
  - The timer value that was originally set
  - Remains constant during countdown
- **Byte 8-9**: Current timer countdown (2-byte big-endian, in seconds)
  - `0x0000` = No timer / timer expired
  - `0x0384` = 900 seconds (15 minutes) remaining
  - `0x04B0` = 1200 seconds (20 minutes) remaining
  - **This is the actual countdown value that decrements**
- Byte 10: Checksum (sum of bytes 1-9, masked to 8 bits)
- Byte 11: `0x0A` - End byte

**Examples**:
- `2A 01 10 00 05 01 04 B0 04 B0 7F 0A` - Device ON, 20 min initial, 20 min remaining (just started)
- `2A 01 10 00 05 01 00 3C 00 1B 6E 0A` - Device ON, 1 min initial, 27 seconds remaining
- `2A 01 10 00 05 00 00 00 00 00 16 0A` - Device OFF, no timer

### Checksum Calculation

The checksum is the **sum** (not XOR) of all bytes between START and END, masked to 8 bits:

```
checksum = (byte1 + byte2 + ... + byteN) & 0xFF
```

**Example for TURN ON command** (`3A 01 20 00 01 01 23 0A`):
```
checksum = (0x01 + 0x20 + 0x00 + 0x01 + 0x01) & 0xFF
         = 0x23
```

**Example for 15-minute timer** (`3A 01 31 00 02 03 84 BB 0A`):
```
checksum = (0x01 + 0x31 + 0x00 + 0x02 + 0x03 + 0x84) & 0xFF
         = 0xBB
```

## Key Commands

### 1. TURN ON Command
**Hex**: `3A 01 20 00 01 01 23 0A`

Breakdown:
- `3A` - Start byte
- `01` - Length
- `20` - Command type (Power control)
- `00 01` - Parameter (power state)
- `01` - Additional parameter
- `23` - Checksum (0x01 + 0x20 + 0x00 + 0x01 + 0x01 = 0x23)
- `0A` - End byte

**ASCII representation**: `:` + `\x01 \x01\x01#\n`

### 2. TURN OFF Command
**Hex**: `3A 01 20 00 01 00 22 0A`

Breakdown:
- `3A` - Start byte
- `01` - Length
- `20` - Command type (Power control)
- `00 01` - Parameter (power state)
- `00` - Power OFF (0x00 = OFF, 0x01 = ON)
- `22` - Checksum (0x01 + 0x20 + 0x00 + 0x01 + 0x00 = 0x22)
- `0A` - End byte

**ASCII representation**: `:` + `\x01 \x00\x00"\n`

### 3. Status Query Command
**Hex**: `3A 01 10 00 00 11 0A`

Breakdown:
- `3A` - Start byte
- `01` - Length
- `10` - Command type (Status query)
- `00 00` - Parameters
- `11` - Checksum
- `0A` - End byte

**Response format** (from handle 0x0012):
```
2A 01 10 00 05 01 04 B0 04 AE 7C 0A
```
Contains device status including power state and other parameters.

### 4. Query 0x40 Command
**Hex**: `3A 01 40 00 00 41 0A`

Breakdown:
- `3A` - Start byte
- `01` - Length
- `40` - Command type (Query type 0x40)
- `00 00` - Parameters
- `41` - Checksum
- `0A` - End byte

**Response format**:
```
2A 01 40 00 07 64 64 64 64 64 00 00 3C 0A
```
Contains additional device parameters.

## Communication Pattern

### Typical Session Flow:
1. **Connect** to device via BLE
2. **Discover services** and characteristics
3. **Enable notifications** on FFF2 (write 0x0100 to CCCD at handle 0x0013)
4. **Send commands** to FFF1 (handle 0x0010)
5. **Receive responses** via notifications from FFF2 (handle 0x0012)

### Polling Pattern:
The app continuously polls the device:
- Status query (0x10) every ~500ms
- Query 0x40 every ~500ms (alternating with status query)

## Response Format

Responses start with `0x2A` (`*`) instead of `0x3A` (`:`), but follow similar structure:
```
[START=0x2A] [LENGTH] [COMMAND] [DATA...] [CHECKSUM] [END=0x0A]
```

### Example Status Response:
```
2A 01 10 00 05 01 04 B0 04 AE 7C 0A
```
- `2A` - Response start byte
- `01` - Length
- `10` - Response to command 0x10
- `00 05 01 04 B0 04 AE` - Status data (includes power state in byte 5)
- `7C` - Checksum
- `0A` - End byte

The 5th byte after command (0x01 or 0x04) appears to indicate power state:
- `0x04` = Device ON
- `0x00` = Device OFF

## Implementation Notes

### To control the device:
1. Connect to device (MAC: `3C:AB:72:5E:F5:22` on Android, UUID on macOS/iOS)
2. Find service UUID: `FFF0`
3. Find characteristic UUID: `FFF2` (for writing commands)
4. Enable notifications on UUID: `FFF1` (for responses)
5. Write command bytes to FFF2

**Note**: On macOS/iOS, BLE devices use UUID addresses instead of MAC addresses. Use scanning to find the device by name "BLOCK3CAB725EF522".

**Implementation Reference**: See `analysis/control_device.py` for a complete working Python implementation using the bleak library.

## Additional Commands Found

### Custom Name Setting (Command 0x74):
Used to set custom preset names like "Custom 1", "Custom 2", etc.
```
3A 01 74 00 09 00 43 75 73 74 6F 6D 20 31 4A 0A
```
ASCII data: "Custom 1"

### Command 0x52:
```
3A 01 52 00 01 00 54 0A
```
Purpose unclear - possibly related to preset selection.

### Command 0x75:
```
3A 01 75 00 00 76 0A
```
Purpose unclear - possibly related to settings.

## Timer Protocol

### Set Timer Command (0x31)
**Format**: `3A 01 31 00 02 [TIMER_HIGH] [TIMER_LOW] [CHECKSUM] 0A`

The device supports a built-in countdown timer. The timer value is specified in **seconds** as a 2-byte big-endian integer.

**Examples**:
- **20 minutes**: `3A 01 31 00 02 04 B0 E8 0A`
  - Timer value: `0x04B0` = 1200 seconds = 20 minutes
  - Checksum: `0x01 + 0x31 + 0x00 + 0x02 + 0x04 + 0xB0` = 0xE8

- **17 minutes**: `3A 01 31 00 02 03 FC 33 0A`
  - Timer value: `0x03FC` = 1020 seconds = 17 minutes
  - Checksum: `0x01 + 0x31 + 0x00 + 0x02 + 0x03 + 0xFC` = 0x33

- **15 minutes**: `3A 01 31 00 02 03 84 BB 0A`
  - Timer value: `0x0384` = 900 seconds = 15 minutes
  - Checksum: `0x01 + 0x31 + 0x00 + 0x02 + 0x03 + 0x84` = 0xBB

- **10 minutes**: `3A 01 31 00 02 02 58 8E 0A`
  - Timer value: `0x0258` = 600 seconds = 10 minutes
  - Checksum: `0x01 + 0x31 + 0x00 + 0x02 + 0x02 + 0x58` = 0x8E

### Timer Usage Sequence

To turn on the device with a timer:
1. **Set Timer**: Send timer command (0x31) with desired duration
2. **Turn ON**: Send turn on command (0x20)

**Note**: The device does NOT need to be turned off first. Simply send the timer command followed by the turn on command.

### Timer Response (0x31)
When the timer command is acknowledged, the device responds with:
```
2A 01 31 00 00 32 0A
```

### Timer Countdown Notifications

The device sends periodic status notifications (command type 0x10) that include the **remaining timer value**:

**Notification Format**:
```
2A 01 10 00 05 [STATUS] [TIMER_HIGH] [TIMER_LOW] [CHECKSUM] 0A
```

**Example countdown notifications**:
- `2A 01 10 00 05 01 04 B0 04 B0 7F 0A` - 20 minutes remaining (1200 seconds)
- `2A 01 10 00 05 01 03 84 03 84 25 0A` - 15 minutes remaining (900 seconds)
- `2A 01 10 00 05 01 03 84 03 83 24 0A` - 15 minutes remaining (899 seconds)
- `2A 01 10 00 05 01 02 58 02 58 CB 0A` - 10 minutes remaining (600 seconds)

**Parsing**:
- Bytes 6-7: Timer remaining (2-byte big-endian, in seconds)
- Byte 5: Power state (0x04 = ON, 0x00 = OFF)

The device continuously sends these notifications, allowing clients to track the countdown in real-time.

### Creating Timer Commands

To create a timer command for any duration:

1. Convert minutes to seconds: `seconds = minutes × 60`
2. Split into 2 bytes (big-endian):
   - `timer_high = (seconds >> 8) & 0xFF`
   - `timer_low = seconds & 0xFF`
3. Build command: `3A 01 31 00 02 [timer_high] [timer_low] [checksum] 0A`
4. Calculate checksum: `(0x01 + 0x31 + 0x00 + 0x02 + timer_high + timer_low) & 0xFF`

**Example - 25 minute timer**:
- Seconds: 25 × 60 = 1500 = `0x05DC`
- Command: `3A 01 31 00 02 05 DC 15 0A`
- Checksum: `(0x01 + 0x31 + 0x00 + 0x02 + 0x05 + 0xDC) & 0xFF = 0x15`

## Summary

**TURN ON**: `3A 01 20 00 01 01 23 0A`  
**TURN OFF**: `3A 01 20 00 01 00 22 0A`  
**SET TIMER**: `3A 01 31 00 02 [HIGH] [LOW] [CHECKSUM] 0A`

The key difference in power commands is byte 5:
- `0x01` = ON
- `0x00` = OFF

Timer value is in seconds (2-byte big-endian), and the device sends countdown notifications automatically.
