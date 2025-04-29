"""Support for 352 Air Purifier fan."""

from __future__ import annotations

import asyncio
import logging
import math
from typing import Any

from homeassistant.components.fan import FanEntity, FanEntityFeature
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util.percentage import (
    percentage_to_ranged_value,
    ranged_value_to_percentage,
)

from .air352.const import SwitchState, WindSpeed
from .air352.device import AirPurifierDevice
from .const import (
    ATTR_AIR_QUALITY,
    ATTR_MODE,
    ATTR_PM25,
    ATTR_WIND_SPEED,
    DOMAIN,
)
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
            AirPurifierFan(hass.data[DOMAIN]["coordinators"][device.macAddress])
            for device in devices
        ],
        True,
    )


class AirPurifierFan(CoordinatorEntity, FanEntity):
    """Representation of a 352 Air Purifier fan."""

    _attr_has_entity_name = True
    _attr_name = None
    _attr_supported_features = (
        FanEntityFeature.SET_SPEED
        # | FanEntityFeature.PRESET_MODE
        | FanEntityFeature.TURN_ON
        | FanEntityFeature.TURN_OFF
    )

    def __init__(self, coordinator: AirPurifierCoordinator) -> None:
        """Initialize the fan."""
        super().__init__(coordinator)
        self._coordinator = coordinator
        self._attr_unique_id = self._device.macAddress
        self._attr_device_info = {
            "identifiers": {(DOMAIN, self._device.macAddress)},
            "name": self._device.deviceName,
            "manufacturer": "352",
        }

    @property
    def _device(self) -> AirPurifierDevice:
        return self._coordinator._device

    @property
    def is_on(self) -> bool:
        """Return true if device is on."""
        return (
            self._device.state is not None
            and self._device.state.switch_state == SwitchState.ON
        )

    @property
    def percentage(self) -> int:
        """Return the current speed percentage."""
        if not self._device.state:
            return 0
        return ranged_value_to_percentage((1, 6), self._device.state.wind_speed.value)

    @property
    def speed_count(self) -> int:
        """Return the number of speeds the fan supports."""
        return len(WindSpeed._member_names_)

    # @property
    # def preset_modes(self) -> list[str]:
    #     """Return the list of available preset modes."""
    #     return ["auto", "sleep", "fast", "custom"]

    # @property
    # def preset_mode(self) -> str | None:
    #     """Return the current preset mode."""
    #     if not self._device.state:
    #         return None
    #     return self._device.state.ac_mode.name.lower()

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the state attributes."""
        if not self._device.state:
            return {}
        return {
            ATTR_PM25: self._device.state.pm,
            ATTR_AIR_QUALITY: self._device.state.air_quality.name.lower(),
            ATTR_WIND_SPEED: self._device.state.wind_speed.value,
            ATTR_MODE: self._device.state.ac_mode.name.lower(),
        }

    async def async_turn_on(
        self,
        percentage: int | None = None,
        preset_mode: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Turn on the fan."""
        await self._device.turn_on()
        await self.coordinator.async_request_refresh()
        await asyncio.sleep(1)
        if percentage is not None:
            await self.async_set_percentage(percentage)
        if preset_mode is not None:
            await self.async_set_preset_mode(preset_mode)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off the fan."""
        await self._device.turn_off()
        await self.coordinator.async_request_refresh()

    async def async_set_percentage(self, percentage: int) -> None:
        """Set the speed of the fan."""
        await self._device.set_wind_speed(
            WindSpeed(math.ceil(percentage_to_ranged_value((1, 6), percentage)))
        )
        await self.coordinator.async_request_refresh()

    # async def async_set_preset_mode(self, preset_mode: str) -> None:
    #     """Set the preset mode of the fan."""
    #     await self._device.set_ac_mode(acMode=AcMode[preset_mode.upper()])
    #     self.__attr_preset_mode = preset_mode
    #     await self.coordinator.async_request_refresh()

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self._attr_percentage = (
            ranged_value_to_percentage((1, 6), self._device.state.wind_speed.value)
            if self._device.state
            else None
        )
        self._attr_preset_mode = (
            self._device.state.ac_mode.name.lower() if self._device.state else None
        )
        self._attr_extra_state_attributes = (
            {
                ATTR_PM25: self._device.state.pm,
                ATTR_AIR_QUALITY: self._device.state.air_quality.name.lower(),
                ATTR_WIND_SPEED: self._device.state.wind_speed.value,
                ATTR_MODE: self._device.state.ac_mode.name.lower(),
            }
            if self._device.state
            else {}
        )
        self._attr_is_on = (
            self._device.state.switch_state == SwitchState.ON
            if self._device.state
            else False
        )
        self._attr_available = self._device.state is not None
        self.async_write_ha_state()
