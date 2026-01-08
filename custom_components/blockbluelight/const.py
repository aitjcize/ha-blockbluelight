"""Constants for the BlockBlueLight integration."""

DOMAIN = "blockbluelight"

# Timer settings
DEFAULT_TIMER_DURATION = 15  # minutes
MIN_TIMER_DURATION = 1
MAX_TIMER_DURATION = 60
CONF_TIMER_DURATION = "timer_duration"

# BLE Service and Characteristic UUIDs
SERVICE_UUID = "0000fff0-0000-1000-8000-00805f9b34fb"
WRITE_CHAR_UUID = "0000fff2-0000-1000-8000-00805f9b34fb"  # FFF2 is write
NOTIFY_CHAR_UUID = "0000fff1-0000-1000-8000-00805f9b34fb"  # FFF1 is notify

# Commands
TURN_ON_CMD = bytes([0x3A, 0x01, 0x20, 0x00, 0x01, 0x01, 0x23, 0x0A])
TURN_OFF_CMD = bytes([0x3A, 0x01, 0x20, 0x00, 0x01, 0x00, 0x22, 0x0A])
STATUS_QUERY_CMD = bytes([0x3A, 0x01, 0x10, 0x00, 0x00, 0x11, 0x0A])

# Response codes
RESPONSE_START_BYTE = 0x2A
POWER_CMD_TYPE = 0x20
STATUS_CMD_TYPE = 0x10
TIMER_CMD_TYPE = 0x31


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
