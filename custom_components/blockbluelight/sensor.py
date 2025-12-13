"""Sensor platform for BlockBlueLight integration."""

from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import BlockBlueLightCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up BlockBlueLight sensor based on a config entry."""
    coordinator: BlockBlueLightCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([BlockBlueLightTimerSensor(coordinator, entry)])


class BlockBlueLightTimerSensor(SensorEntity):
    """Representation of a BlockBlueLight timer sensor."""

    _attr_has_entity_name = True
    _attr_name = "Timer Remaining"
    _attr_icon = "mdi:timer-outline"

    def __init__(
        self,
        coordinator: BlockBlueLightCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        self.coordinator = coordinator
        self._attr_unique_id = f"{entry.unique_id}_timer_remaining"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.unique_id)},
        }

    @property
    def native_value(self) -> str:
        """Return the timer remaining in m:s format."""
        seconds = self.coordinator.timer_remaining
        if seconds == 0:
            return "0:00"
        minutes = seconds // 60
        remaining_seconds = seconds % 60
        return f"{minutes}:{remaining_seconds:02d}"

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return True

    async def async_added_to_hass(self) -> None:
        """When entity is added to hass."""
        self.async_on_remove(
            self.coordinator.async_add_listener(self._handle_coordinator_update)
        )

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self.async_write_ha_state()
