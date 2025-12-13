"""Number platform for BlockBlueLight timer."""

from __future__ import annotations

import logging

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo, EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    DEFAULT_TIMER_DURATION,
    DOMAIN,
    MAX_TIMER_DURATION,
    MIN_TIMER_DURATION,
)
from .coordinator import BlockBlueLightCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up BlockBlueLight number based on a config entry."""
    coordinator: BlockBlueLightCoordinator = hass.data[DOMAIN][entry.entry_id]

    async_add_entities([BlockBlueLightTimer(coordinator, entry)])


class BlockBlueLightTimer(NumberEntity):
    """Representation of BlockBlueLight timer duration."""

    _attr_has_entity_name = True
    _attr_name = "Timer duration"
    _attr_icon = "mdi:timer"
    _attr_native_unit_of_measurement = UnitOfTime.MINUTES
    _attr_native_min_value = MIN_TIMER_DURATION
    _attr_native_max_value = MAX_TIMER_DURATION
    _attr_native_step = 1
    _attr_mode = NumberMode.BOX
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(
        self,
        coordinator: BlockBlueLightCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the number entity."""
        self._coordinator = coordinator
        self._attr_unique_id = f"{entry.unique_id}_timer"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.unique_id)},
        )

    @property
    def native_value(self) -> float:
        """Return the current timer duration."""
        return self._coordinator.timer_duration

    async def async_set_native_value(self, value: float) -> None:
        """Set the timer duration."""
        self._coordinator.set_timer_duration(int(value))
        self.async_write_ha_state()
