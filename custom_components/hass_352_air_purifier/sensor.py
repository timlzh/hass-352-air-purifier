"""Support for 352 Air Purifier PM2.5 sensor."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONCENTRATION_MICROGRAMS_PER_CUBIC_METER
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .air352.device import AirPurifierDevice
from .const import DOMAIN
from .coordinator import AirPurifierCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the 352 Air Purifier PM2.5 sensor."""
    devices: list[AirPurifierDevice] = hass.data[DOMAIN]["devices"]

    async_add_entities(
        [
            AirPurifierPM25Sensor(hass.data[DOMAIN]["coordinators"][device.macAddress])
            for device in devices
        ],
        True,
    )


class AirPurifierPM25Sensor(CoordinatorEntity, SensorEntity):
    """Representation of a 352 Air Purifier PM2.5 sensor."""

    _attr_has_entity_name = True
    _attr_name = "PM2.5"
    _attr_native_unit_of_measurement = CONCENTRATION_MICROGRAMS_PER_CUBIC_METER
    _attr_device_class = SensorDeviceClass.PM25
    _attr_suggested_display_precision = 0

    def __init__(self, coordinator: AirPurifierCoordinator) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._coordinator = coordinator
        self._attr_unique_id = f"{coordinator._device.macAddress}_pm25"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, coordinator._device.macAddress)},
            "name": coordinator._device.deviceName,
            "manufacturer": "352",
        }

    @property
    def native_value(self) -> int | None:
        """Return the state of the sensor."""
        if not self._coordinator._device.state:
            return None
        return self._coordinator._device.state.pm

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the state attributes."""
        if not self._coordinator._device.state:
            return {}
        return {
            "air_quality": self._coordinator._device.state.air_quality.name.lower(),
        }

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        if not self._coordinator._device.state:
            return
        self._attr_native_value = self._coordinator._device.state.pm
        self.async_write_ha_state()
