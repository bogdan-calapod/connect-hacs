"""PDQ Connect Home Assistant integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.typing import ConfigType

from .api import PDQConnectAPI, PDQConnectAPIError, PDQConnectAuthError
from .const import (
    ATTR_PACKAGE_ID,
    ATTR_TARGET_IDS,
    CONF_API_KEY,
    DOMAIN,
    SERVICE_DEPLOY_PACKAGE,
)
from .coordinator import PDQConnectCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.BINARY_SENSOR]

# Service call schema
DEPLOY_PACKAGE_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_PACKAGE_ID): cv.string,
        vol.Required(ATTR_TARGET_IDS): vol.All(
            cv.ensure_list, [cv.string]
        ),
    }
)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up PDQ Connect from configuration.yaml (not used – config flow only)."""
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up a PDQ Connect config entry."""
    _LOGGER.debug("Setting up PDQ Connect entry %s", entry.entry_id)

    api = PDQConnectAPI(entry.data[CONF_API_KEY])
    coordinator = PDQConnectCoordinator(hass, entry, api)

    # Initial data fetch – will raise ConfigEntryNotReady on failure
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    # Forward setup to all platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # ------------------------------------------------------------------ #
    # Service: pdq_connect.deploy_package                                  #
    # ------------------------------------------------------------------ #

    async def handle_deploy_package(call: ServiceCall) -> None:
        """Deploy a package to one or more devices/groups."""
        package_id: str = call.data[ATTR_PACKAGE_ID]
        target_ids: list[str] = call.data[ATTR_TARGET_IDS]

        _LOGGER.info(
            "Deploying package %s to targets %s", package_id, target_ids
        )

        try:
            await hass.async_add_executor_job(
                api.deploy_package, package_id, target_ids
            )
            _LOGGER.info("Deployment triggered successfully")
        except PDQConnectAuthError as err:
            _LOGGER.error("Auth error during deployment: %s", err)
        except PDQConnectAPIError as err:
            _LOGGER.error("API error during deployment: %s", err)
        except Exception as err:  # noqa: BLE001
            _LOGGER.exception("Unexpected error during deployment: %s", err)

    # Register the service only once, keyed to the first entry that sets up.
    # If multiple entries exist, they all share the same service (the service
    # chooses the API of the first registered entry; for a single-org setup
    # this is fine; a more sophisticated implementation could accept an
    # entry_id parameter).
    if not hass.services.has_service(DOMAIN, SERVICE_DEPLOY_PACKAGE):
        hass.services.async_register(
            DOMAIN,
            SERVICE_DEPLOY_PACKAGE,
            handle_deploy_package,
            schema=DEPLOY_PACKAGE_SCHEMA,
        )

    _LOGGER.debug("PDQ Connect entry %s setup complete", entry.entry_id)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a PDQ Connect config entry."""
    _LOGGER.debug("Unloading PDQ Connect entry %s", entry.entry_id)

    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        coordinator: PDQConnectCoordinator = hass.data[DOMAIN].pop(entry.entry_id)
        await hass.async_add_executor_job(coordinator.api.close)

    # Remove service if no entries remain
    if not hass.data.get(DOMAIN):
        hass.services.async_remove(DOMAIN, SERVICE_DEPLOY_PACKAGE)

    return unload_ok
