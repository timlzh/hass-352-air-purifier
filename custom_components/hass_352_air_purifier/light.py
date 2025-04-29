"""Support for 352 Air Purifier light."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.light import LightEntity
from homeassistant.components.light.const import ColorMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .air352.const import LightState
from .air352.device import AirPurifierDevice
from .const import DOMAIN
from .coordinator import AirPurifierCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the 352 Air Purifier light."""
    devices: list[AirPurifierDevice] = hass.data[DOMAIN]["devices"]

    async_add_entities(
        [
            AirPurifierLight(hass.data[DOMAIN]["coordinators"][device.macAddress])
            for device in devices
        ],
        True,
    )


class AirPurifierLight(CoordinatorEntity, LightEntity):
    """Representation of a 352 Air Purifier light."""

    _attr_has_entity_name = True
    _attr_name = "Light"
    _attr_supported_color_modes = {ColorMode.ONOFF}
    _attr_color_mode = ColorMode.ONOFF

    def __init__(self, coordinator: AirPurifierCoordinator) -> None:
        """Initialize the light."""
        super().__init__(coordinator)
        self._coordinator = coordinator
        self._attr_unique_id = f"{coordinator._device.macAddress}_light"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, coordinator._device.macAddress)},
            "name": coordinator._device.deviceName,
            "manufacturer": "352",
        }

    @property
    def is_on(self) -> bool:
        """Return true if light is on."""
        if not self._coordinator._device.state:
            return False
        return self._coordinator._device.state.light_state == LightState.ON

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on the light."""
        await self._coordinator._device.turn_light_on()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off the light."""
        await self._coordinator._device.turn_light_off()

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        if not self._coordinator._device.state:
            return
        self._attr_is_on = self._coordinator._device.state.light_state == LightState.ON
        self.async_write_ha_state()
