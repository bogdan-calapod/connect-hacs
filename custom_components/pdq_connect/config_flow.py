"""Config flow for the PDQ Connect integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
import homeassistant.helpers.config_validation as cv

from .api import PDQConnectAPI, PDQConnectAuthError, PDQConnectAPIError
from .const import (
    CONF_API_KEY,
    CONF_UPDATE_INTERVAL,
    DEFAULT_UPDATE_INTERVAL,
    DOMAIN,
    MAX_UPDATE_INTERVAL,
    MIN_UPDATE_INTERVAL,
)

_LOGGER = logging.getLogger(__name__)


async def _validate_api_key(hass: HomeAssistant, api_key: str) -> str | None:
    """
    Try to authenticate with the provided API key.

    Returns None on success, or an error key string on failure.
    """
    api = PDQConnectAPI(api_key)
    try:
        await hass.async_add_executor_job(api.validate)
    except PDQConnectAuthError:
        return "invalid_auth"
    except PDQConnectAPIError:
        return "cannot_connect"
    except Exception:
        _LOGGER.exception("Unexpected error during PDQ Connect validation")
        return "unknown"
    finally:
        await hass.async_add_executor_job(api.close)
    return None


class PDQConnectConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle the initial setup config flow."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Show the setup form and validate on submission."""
        errors: dict[str, str] = {}

        if user_input is not None:
            api_key = user_input[CONF_API_KEY].strip()
            error = await _validate_api_key(self.hass, api_key)
            if error:
                errors["base"] = error
            else:
                # Use a stable unique ID derived from a fingerprint of the key
                # (we don't want to store the key verbatim as the unique_id)
                await self.async_set_unique_id(api_key[:16])
                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title="PDQ Connect",
                    data={
                        CONF_API_KEY: api_key,
                        CONF_UPDATE_INTERVAL: user_input.get(
                            CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL
                        ),
                    },
                )

        data_schema = vol.Schema(
            {
                vol.Required(CONF_API_KEY): str,
                vol.Optional(
                    CONF_UPDATE_INTERVAL, default=DEFAULT_UPDATE_INTERVAL
                ): vol.All(
                    vol.Coerce(int),
                    vol.Range(min=MIN_UPDATE_INTERVAL, max=MAX_UPDATE_INTERVAL),
                ),
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> PDQConnectOptionsFlow:
        """Return the options flow handler."""
        return PDQConnectOptionsFlow(config_entry)


class PDQConnectOptionsFlow(config_entries.OptionsFlow):
    """Handle option updates (e.g. polling interval)."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Show options form."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        current_interval = self.config_entry.options.get(
            CONF_UPDATE_INTERVAL,
            self.config_entry.data.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL),
        )

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_UPDATE_INTERVAL, default=current_interval
                    ): vol.All(
                        vol.Coerce(int),
                        vol.Range(min=MIN_UPDATE_INTERVAL, max=MAX_UPDATE_INTERVAL),
                    ),
                }
            ),
        )
