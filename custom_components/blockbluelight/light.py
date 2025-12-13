"""Light platform for BlockBlueLight."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.light import ColorMode, LightEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import BlockBlueLightCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up BlockBlueLight light based on a config entry."""
    coordinator: BlockBlueLightCoordinator = hass.data[DOMAIN][entry.entry_id]

    async_add_entities([BlockBlueLightLight(coordinator, entry)])


class BlockBlueLightLight(
    CoordinatorEntity[BlockBlueLightCoordinator], LightEntity
):
    """Representation of a BlockBlueLight light."""

    _attr_has_entity_name = True
    _attr_name = None
    _attr_supported_color_modes = {ColorMode.ONOFF}
    _attr_color_mode = ColorMode.ONOFF

    def __init__(
        self,
        coordinator: BlockBlueLightCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the light."""
        super().__init__(coordinator)

        self._attr_unique_id = entry.unique_id
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.unique_id)},
            name=entry.title,
            manufacturer="BlockBlueLight",
            model="Red Light Therapy Device",
        )

    @property
    def is_on(self) -> bool:
        """Return true if the light is on."""
        return self.coordinator.is_on

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return True

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the state attributes."""
        attrs = {}
        if self.coordinator.timer_remaining > 0:
            attrs["timer_remaining_seconds"] = self.coordinator.timer_remaining
            attrs["timer_remaining_minutes"] = round(
                self.coordinator.timer_remaining / 60, 1
            )
        return attrs

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the light on."""
        await self.coordinator.async_turn_on()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the light off."""
        await self.coordinator.async_turn_off()

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self.async_write_ha_state()
