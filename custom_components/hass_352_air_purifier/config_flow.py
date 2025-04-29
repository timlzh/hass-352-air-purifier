"""Config flow for 352 Air Purifier integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.selector import (
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
)

from .air352.api import Air352API
from .const import CONF_PASSWORD, CONF_PHONE, DOMAIN

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_PHONE): TextSelector(
            TextSelectorConfig(type=TextSelectorType.TEL, autocomplete="username")
        ),
        vol.Required(CONF_PASSWORD): TextSelector(
            TextSelectorConfig(
                type=TextSelectorType.PASSWORD, autocomplete="current-password"
            )
        ),
    }
)


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> None:
    """Validate the user input allows us to connect."""
    try:
        api = Air352API(data[CONF_PHONE], data[CONF_PASSWORD])
        # 尝试登录以验证凭据
        await api.login_by_pwd()
    except Exception as ex:
        raise InvalidAuth from ex


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for 352 Air Purifier."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                await validate_input(self.hass, user_input)
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                return self.async_create_entry(
                    title=f"352 Air Purifier ({user_input[CONF_PHONE]})",
                    data=user_input,
                )

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )


class InvalidAuth(HomeAssistantError):
    """Error to indicate there is invalid auth."""
