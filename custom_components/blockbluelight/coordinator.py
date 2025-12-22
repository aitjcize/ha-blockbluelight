"""Coordinator for BlockBlueLight device."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from bleak.backends.device import BLEDevice
from bleak.exc import BleakError
from bleak_retry_connector import (
    BleakClientWithServiceCache,
    establish_connection,
)
from homeassistant.components import bluetooth
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)

from .const import (
    DEFAULT_TIMER_DURATION,
    DOMAIN,
    NOTIFY_CHAR_UUID,
    POWER_CMD_TYPE,
    RESPONSE_START_BYTE,
    STATUS_CMD_TYPE,
    STATUS_QUERY_CMD,
    TIMER_CMD_TYPE,
    TURN_OFF_CMD,
    TURN_ON_CMD,
    WRITE_CHAR_UUID,
    create_timer_command,
)

_LOGGER = logging.getLogger(__name__)

DISCONNECT_DELAY = 120  # Seconds to wait before disconnecting
COUNTDOWN_INTERVAL = 1  # Seconds between countdown updates


class BlockBlueLightCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Class to manage fetching BlockBlueLight data."""

    def __init__(
        self,
        hass: HomeAssistant,
        ble_device: BLEDevice,
    ) -> None:
        """Initialize."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
        )
        self._ble_device = ble_device
        self._client: BleakClientWithServiceCache | None = None
        self._disconnect_timer: asyncio.TimerHandle | None = None
        self._is_on: bool = False
        self._expected_disconnect = False
        self._auto_off_timer: asyncio.TimerHandle | None = None
        self._timer_duration: int = DEFAULT_TIMER_DURATION  # minutes
        self._timer_remaining: int = 0  # seconds remaining on device timer
        self._countdown_timer: asyncio.TimerHandle | None = None
        self._countdown_start_time: float | None = None

    @property
    def is_on(self) -> bool:
        """Return if device is on."""
        return self._is_on

    @property
    def timer_duration(self) -> int:
        """Return timer duration in minutes."""
        return self._timer_duration

    def set_timer_duration(self, duration: int) -> None:
        """Set timer duration in minutes."""
        self._timer_duration = duration
        _LOGGER.debug("Timer duration set to %d minutes", duration)

    @property
    def timer_remaining(self) -> int:
        """Return remaining timer in seconds."""
        return self._timer_remaining

    async def async_connect(self) -> None:
        """Connect to the device."""
        if self._client and self._client.is_connected:
            return

        _LOGGER.debug("Connecting to %s", self._ble_device.address)

        try:
            self._client = await establish_connection(
                BleakClientWithServiceCache,
                self._ble_device,
                self._ble_device.address,
                self._disconnected,
                use_services_cache=True,
                ble_device_callback=lambda: bluetooth.async_ble_device_from_address(
                    self.hass, self._ble_device.address, connectable=True
                ),
            )

            # Enable notifications
            await self._client.start_notify(
                NOTIFY_CHAR_UUID, self._notification_handler
            )
            _LOGGER.debug("Connected and notifications enabled")

            # Query initial status to get current device state and timer
            # This is important for resuming countdown after HA restart
            # Add a small delay to ensure device is ready to respond
            await asyncio.sleep(1)
            _LOGGER.info("Querying device status to sync state")

            # Retry status query a few times if needed (helps after HA restart)
            for attempt in range(5):
                try:
                    await self._query_status()
                    break
                except Exception as err:
                    if attempt < 2:
                        _LOGGER.warning(
                            "Status query attempt %d failed, retrying: %s",
                            attempt + 1,
                            err,
                        )
                        await asyncio.sleep(1)
                    else:
                        _LOGGER.error(
                            "Failed to query status after 3 attempts: %s", err
                        )

        except (BleakError, TimeoutError) as err:
            _LOGGER.error("Error connecting to device: %s", err)
            raise

    async def async_disconnect(self) -> None:
        """Disconnect from device."""
        # Don't disconnect if countdown is active
        if self._countdown_timer:
            _LOGGER.debug("Skipping disconnect - countdown timer is active")
            return

        self._expected_disconnect = True
        if self._disconnect_timer:
            self._disconnect_timer.cancel()
            self._disconnect_timer = None

        if self._auto_off_timer:
            self._auto_off_timer.cancel()

        if self._client and self._client.is_connected:
            _LOGGER.debug("Disconnecting from %s", self._ble_device.address)
            await self._client.disconnect()

    def _disconnected(self, client: BleakClientWithServiceCache) -> None:
        """Handle disconnection."""
        if self._expected_disconnect:
            _LOGGER.debug(
                "Expected disconnect from %s", self._ble_device.address
            )
            self._expected_disconnect = False
        else:
            _LOGGER.warning(
                "Unexpected disconnect from %s", self._ble_device.address
            )

        self._client = None

    @callback
    def _notification_handler(self, sender: int, data: bytearray) -> None:
        """Handle notifications from the device."""
        _LOGGER.debug("Received notification: %s", data.hex())

        if len(data) < 3 or data[0] != RESPONSE_START_BYTE:
            return

        cmd_type = data[2]

        if cmd_type == STATUS_CMD_TYPE:
            # Status response with timer information
            if len(data) > 9:
                status_byte = data[5]
                # Bytes 6-7 are initial timer setting
                # Bytes 8-9 are actual countdown timer
                timer_high = data[8]
                timer_low = data[9]
                timer_seconds = (timer_high << 8) | timer_low

                _LOGGER.debug(
                    "Status notification received: status_byte=0x%02x, timer=%d seconds",
                    status_byte,
                    timer_seconds,
                )

                new_state = status_byte == 0x01
                state_changed = new_state != self._is_on
                timer_changed = timer_seconds != self._timer_remaining

                if state_changed or timer_changed:
                    self._is_on = new_state
                    self._timer_remaining = timer_seconds
                    _LOGGER.info(
                        "Device state updated: %s (status_byte=0x%02x), Timer remaining: %d seconds (%.1f min)",
                        "ON" if new_state else "OFF",
                        status_byte,
                        timer_seconds,
                        timer_seconds / 60,
                    )
                    self.async_set_updated_data(
                        {
                            "is_on": self._is_on,
                            "timer_remaining": self._timer_remaining,
                        }
                    )

                    # Start/stop countdown based on timer state
                    if timer_seconds > 0 and not self._countdown_timer:
                        self._start_countdown()
                    elif timer_seconds == 0 and self._countdown_timer:
                        self._stop_countdown()

        elif cmd_type == POWER_CMD_TYPE:
            # Power command acknowledgment
            if len(data) > 5:
                status_byte = data[5]
                new_state = status_byte == 0x01
                if new_state != self._is_on:
                    self._is_on = new_state
                    _LOGGER.debug(
                        "Device state updated: %s", "ON" if new_state else "OFF"
                    )
                    self.async_set_updated_data({"is_on": self._is_on})

        elif cmd_type == TIMER_CMD_TYPE:
            # Timer command acknowledgment
            _LOGGER.debug("Timer command acknowledged")

    async def _send_command(self, command: bytes) -> None:
        """Send command to device."""
        if not self._client or not self._client.is_connected:
            await self.async_connect()

        if self._disconnect_timer:
            self._disconnect_timer.cancel()

        try:
            await self._client.write_gatt_char(
                WRITE_CHAR_UUID, command, response=False
            )
            _LOGGER.debug("Sent command: %s", command.hex())

            # Wait a bit for response
            await asyncio.sleep(0.5)

        except BleakError as err:
            _LOGGER.error("Error sending command: %s", err)
            raise UpdateFailed(f"Failed to send command: {err}") from err

        # Schedule disconnect after delay (unless countdown is active)
        if not self._countdown_timer:
            self._disconnect_timer = self.hass.loop.call_later(
                DISCONNECT_DELAY,
                lambda: asyncio.create_task(self.async_disconnect()),
            )
        else:
            _LOGGER.debug("Skipping disconnect timer - countdown is active")

    async def _query_status(self) -> None:
        """Query device status."""
        await self._send_command(STATUS_QUERY_CMD)

    def _start_countdown(self) -> None:
        """Start client-side countdown timer."""
        if self._countdown_timer:
            self._countdown_timer.cancel()

        import time

        self._countdown_start_time = time.time()
        _LOGGER.debug(
            "Starting countdown timer (interval: %d second)", COUNTDOWN_INTERVAL
        )
        self._countdown_timer = self.hass.loop.call_later(
            COUNTDOWN_INTERVAL, lambda: self._update_countdown()
        )

    def _stop_countdown(self) -> None:
        """Stop countdown timer."""
        if self._countdown_timer:
            _LOGGER.debug("Stopping countdown timer")
            self._countdown_timer.cancel()
            self._countdown_timer = None
            self._countdown_start_time = None

    def _update_countdown(self) -> None:
        """Update countdown timer and schedule next update."""
        if self._timer_remaining > 0:
            self._timer_remaining -= 1
            _LOGGER.debug(
                "Countdown: %d seconds remaining", self._timer_remaining
            )
            self.async_set_updated_data(
                {"is_on": self._is_on, "timer_remaining": self._timer_remaining}
            )

            # Schedule next countdown update
            if self._timer_remaining > 0:
                self._countdown_timer = self.hass.loop.call_later(
                    COUNTDOWN_INTERVAL, lambda: self._update_countdown()
                )
            else:
                # Timer expired, query device to confirm state and update light
                _LOGGER.info("Countdown complete, querying device status")
                self._countdown_timer = None

                async def query_and_disconnect():
                    try:
                        await self._query_status()
                        # Wait for status response
                        await asyncio.sleep(1)
                        # Now safe to disconnect
                        await self.async_disconnect()
                    except Exception as err:
                        _LOGGER.error(
                            "Error querying status after countdown: %s", err
                        )

                asyncio.create_task(query_and_disconnect())
        else:
            self._countdown_timer = None

    async def async_turn_on(self) -> None:
        """Turn the device on with timer if configured.

        Note:
            When setting a timer, send the timer command first, then turn on.
            The sequence is: Set Timer → Turn ON
        """
        # If timer is configured, set it before turning on
        if self._timer_duration > 0:
            _LOGGER.info(
                "Turning on device with %d minute timer", self._timer_duration
            )

            # Step 1: Set timer
            timer_cmd = create_timer_command(self._timer_duration)
            _LOGGER.debug("Setting timer command: %s", timer_cmd.hex())
            await self._send_command(timer_cmd)
            await asyncio.sleep(0.2)

            # Step 2: Turn ON
            await self._send_command(TURN_ON_CMD)
        else:
            # No timer, just turn on
            await self._send_command(TURN_ON_CMD)

        # Wait a bit for device to fully turn on before updating state
        await asyncio.sleep(0.5)

        self._is_on = True
        self.async_set_updated_data({"is_on": True})

        # Query status immediately and start countdown if timer is configured
        if self._timer_duration > 0:
            _LOGGER.debug(
                "Querying initial status and starting countdown timer"
            )
            await self._query_status()
            # Countdown will be started by notification handler when it receives timer value

        # Cancel any existing auto-off timer (device handles timer now)
        if self._auto_off_timer:
            self._auto_off_timer.cancel()
            self._auto_off_timer = None

    async def async_turn_off(self) -> None:
        """Turn the device off."""
        # Cancel auto-off timer if running
        if self._auto_off_timer:
            self._auto_off_timer.cancel()
            self._auto_off_timer = None

        await self._send_command(TURN_OFF_CMD)
        self._is_on = False
        self.async_set_updated_data({"is_on": False})

    async def _auto_turn_off(self) -> None:
        """Automatically turn off device after timer expires."""
        _LOGGER.info("Auto-off timer expired, turning off device")
        self._auto_off_timer = None
        await self.async_turn_off()
