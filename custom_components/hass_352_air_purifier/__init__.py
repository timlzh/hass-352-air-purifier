"""The 352 Air Purifier integration."""

from __future__ import annotations

import asyncio
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .air352.api import Air352API
from .const import CONF_PASSWORD, CONF_PHONE, DOMAIN
from .coordinator import AirPurifierCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["sensor", "fan", "light"]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> bool:
    """Set up 352 Air Purifier from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    api = hass.data[DOMAIN][entry.entry_id] = Air352API(
        entry.data[CONF_PHONE], entry.data[CONF_PASSWORD]
    )
    await api.login_by_pwd()
    _LOGGER.debug(f"Login successful, token {api.token}")

    hass.data[DOMAIN]["lock"] = async_lock = asyncio.Lock()
    devices = await api.get_device_list(async_lock)
    hass.data[DOMAIN]["devices"] = devices
    hass.data[DOMAIN]["coordinators"] = {}
    _LOGGER.debug(f"Devices: {devices}")
    for device in devices:
        _LOGGER.debug(f"Device: {device}")
        hass.data[DOMAIN]["coordinators"][device.macAddress] = AirPurifierCoordinator(
            hass,
            device,
        )

    # 设置平台
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
