# BlockBlueLight - Home Assistant Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/custom-components/hacs)
[![GitHub release](https://img.shields.io/github/release/aitjcize/ha-blockbluelight.svg)](https://github.com/aitjcize/ha-blockbluelight/releases)
[![License](https://img.shields.io/github/license/aitjcize/ha-blockbluelight.svg)](LICENSE)

A Home Assistant custom integration for controlling BlockBlueLight red light therapy devices via Bluetooth LE.

## Features

- 🔍 **Automatic Discovery** - Finds your device automatically via Bluetooth
- 🔌 **ESPHome Bluetooth Proxy Support** - Works with your existing proxies
- 💡 **Switch Control** - Simple ON/OFF control
- ⏱️ **Built-in Auto-off Timer** - Set duration (1-60 minutes) for therapy sessions
- 🔋 **Smart Connection** - Connects on-demand, auto-disconnects after 2 minutes
- 🎨 **Config Flow UI** - No YAML configuration needed

## Quick Start

### Requirements

- Home Assistant 2024.1.0 or newer
- Bluetooth support (built-in adapter or ESPHome Bluetooth Proxy)
- BlockBlueLight device in Bluetooth range

### Installation via HACS (Recommended)

1. Open HACS in Home Assistant
2. Go to **Integrations**
3. Click the **⋮** menu (top right) → **Custom repositories**
4. Add repository URL: `https://github.com/aitjcize/ha-blockbluelight`
5. Category: **Integration**
6. Click **Add**
7. Click **+ Explore & Download Repositories**
8. Search for "BlockBlueLight"
9. Click **Download**
10. Restart Home Assistant
11. Go to **Settings** → **Devices & Services** → **Add Integration**
12. Search for "BlockBlueLight" and configure

### Manual Installation

1. Copy the `custom_components/blockbluelight` folder to your Home Assistant `config/custom_components/` directory
2. Restart Home Assistant
3. Go to **Settings** → **Devices & Services** → **Add Integration**
4. Search for "BlockBlueLight" and configure

## Usage

After installation, you'll have two entities:

### Light Entity
- **Entity ID**: `light.block3cab725ef522` (based on device name)
- **Controls**: Turn the device ON/OFF
- **Type**: Red light therapy light

### Timer Duration Entity
- **Entity ID**: `number.block3cab725ef522_timer_duration`
- **Range**: 1-60 minutes (default: 15)
- **Purpose**: Set how long the device stays on before automatically turning off
- **Perfect for**: Red light therapy sessions (typically 10-20 minutes)

## Automation Examples

### Basic: Turn on at sunset (auto-off after timer)
```yaml
automation:
  - alias: "Red light therapy at sunset"
    trigger:
      - platform: sun
        event: sunset
    action:
      - service: light.turn_on
        target:
          entity_id: light.block3cab725ef522
```

### Set custom timer duration
```yaml
automation:
  - alias: "20-minute therapy session"
    trigger:
      - platform: time
        at: "20:00:00"
    action:
      - service: number.set_value
        target:
          entity_id: number.block3cab725ef522_timer_duration
        data:
          value: 20
      - service: light.turn_on
        target:
          entity_id: light.block3cab725ef522
```

### Morning and evening sessions
```yaml
automation:
  - alias: "Morning therapy - 10 minutes"
    trigger:
      - platform: time
        at: "07:00:00"
    action:
      - service: number.set_value
        target:
          entity_id: number.block3cab725ef522_timer_duration
        data:
          value: 10
      - service: light.turn_on
        target:
          entity_id: light.block3cab725ef522

  - alias: "Evening therapy - 15 minutes"
    trigger:
      - platform: time
        at: "21:00:00"
    action:
      - service: number.set_value
        target:
          entity_id: number.block3cab725ef522_timer_duration
        data:
          value: 15
      - service: light.turn_on
        target:
          entity_id: light.block3cab725ef522
```

## Lovelace Card Examples

### Simple entities card
```yaml
type: entities
title: Red Light Therapy
entities:
  - entity: light.block3cab725ef522
    name: Power
  - entity: number.block3cab725ef522_timer_duration
    name: Session Duration
```

### Button card with timer
```yaml
type: vertical-stack
cards:
  - type: light
    entity: light.block3cab725ef522
    name: Red Light Therapy
  - type: entities
    entities:
      - entity: number.block3cab725ef522_timer_duration
        name: Auto-off Timer
```

## Troubleshooting

### Device Not Discovered

1. **Check Bluetooth is enabled** in Home Assistant
2. **Verify ESPHome Bluetooth Proxy** is working:
   - Go to **Settings** → **Devices & Services** → **ESPHome**
   - Check your proxy device is online
3. **Check device is in range** of the Bluetooth proxy
4. **Restart Home Assistant** and wait a few minutes for discovery

### Connection Issues

1. **Check logs**: Go to **Settings** → **System** → **Logs**
2. Look for errors related to `blockbluelight`
3. Try removing and re-adding the integration
4. Make sure no other device is connected to the BlockBlueLight device

### Enable Debug Logging

Add to `configuration.yaml`:

```yaml
logger:
  default: info
  logs:
    custom_components.blockbluelight: debug
    homeassistant.components.bluetooth: debug
```

Then restart Home Assistant and check the logs.

## Device Details

### BLE Protocol Information

- **Device Name Pattern**: `BLOCK` followed by MAC address (e.g., `BLOCK3CAB725EF522`)
- **Service UUID**: 0000fff0-0000-1000-8000-00805f9b34fb
- **Write Characteristic**: 0000fff2-0000-1000-8000-00805f9b34fb (FFF2)
- **Notify Characteristic**: 0000fff1-0000-1000-8000-00805f9b34fb (FFF1)

**Note**: Characteristic naming is opposite of typical convention - FFF2 is for writing, FFF1 is for notifications.

### Commands

- **Turn ON**: `3A 01 20 00 01 01 23 0A`
- **Turn OFF**: `3A 01 20 00 01 00 22 0A`
- **Status Query**: `3A 01 10 00 00 11 0A`
- **Set Timer**: `3A 01 31 00 02 [timer_high] [timer_low] [checksum] 0A`

## Repository Structure

- **`custom_components/blockbluelight/`** - Home Assistant integration
- **`analysis/`** - Protocol reverse engineering materials
  - `BLE_PROTOCOL_ANALYSIS.md` - Complete protocol documentation
  - `btsnoop_hci.log` - Captured HCI log
  - Python scripts for testing and analysis

## For Developers

### Publishing to HACS

1. **Create GitHub repository** named `ha-blockbluelight`
2. **Push code**:
   ```bash
   git init
   git add .
   git commit -m "Initial release v1.0.0"
   git remote add origin https://github.com/YOUR_USERNAME/ha-blockbluelight.git
   git branch -M main
   git push -u origin main
   ```

3. **Create release** on GitHub:
   - Tag: `v1.0.0`
   - Title: `v1.0.0 - Initial Release`
   - Copy description from `CHANGELOG.md`

4. **Add to HACS** as custom repository:
   - HACS → Integrations → ⋮ → Custom repositories
   - Add: `https://github.com/YOUR_USERNAME/ha-blockbluelight`
   - Category: Integration

### Updating the Integration

1. Update version in `custom_components/blockbluelight/manifest.json`
2. Update `CHANGELOG.md`
3. Commit and push changes
4. Create new release on GitHub

HACS will automatically detect new releases and notify users.

### File Structure

```
custom_components/blockbluelight/
├── __init__.py           # Integration setup
├── config_flow.py        # Config flow for UI setup
├── const.py              # Constants (UUIDs, commands)
├── coordinator.py        # BLE communication coordinator
├── manifest.json         # Integration metadata
├── light.py              # Light entity implementation
├── number.py             # Timer duration entity
├── strings.json          # UI strings
└── translations/
    └── en.json          # English translations
```

### Key Components

- **Coordinator**: Manages BLE connection, sends commands, handles notifications
- **Light Entity**: Provides ON/OFF control in Home Assistant UI
- **Number Entity**: Timer duration configuration
- **Config Flow**: Handles device discovery and setup

## Known Limitations

- Only supports ON/OFF control (no brightness, color, etc.)
- Requires Bluetooth to be in range
- One device connection at a time

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT License - See [LICENSE](LICENSE) file for details

## Credits

Protocol reverse-engineered from Android HCI logs using Wireshark and Python. See `analysis/` directory for complete reverse engineering details.

## Disclaimer

This is an unofficial integration and is not affiliated with or endorsed by the device manufacturer. Use at your own risk.
