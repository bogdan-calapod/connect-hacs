"""Data Update Coordinator for PDQ Connect."""
from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import PDQConnectAPI, PDQConnectAPIError, PDQConnectAuthError
from .const import CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL, DOMAIN

_LOGGER = logging.getLogger(__name__)


class PDQConnectData:
    """Container for a single coordinator refresh result."""

    def __init__(
        self,
        devices: list[dict[str, Any]],
        packages: list[dict[str, Any]],
    ) -> None:
        self.devices = devices
        self.packages = packages
        # Index devices by ID for O(1) lookup in entities
        self.devices_by_id: dict[str, dict[str, Any]] = {
            d["id"]: d for d in devices if "id" in d
        }
        self.packages_by_id: dict[str, dict[str, Any]] = {
            p["id"]: p for p in packages if "id" in p
        }


class PDQConnectCoordinator(DataUpdateCoordinator[PDQConnectData]):
    """Coordinator that polls PDQ Connect for device and package data."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, api: PDQConnectAPI) -> None:
        self.api = api
        update_interval = entry.options.get(
            CONF_UPDATE_INTERVAL,
            entry.data.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL),
        )
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=update_interval),
        )

    async def _async_update_data(self) -> PDQConnectData:
        """Fetch all data from PDQ Connect (runs in executor)."""
        try:
            return await self.hass.async_add_executor_job(self._fetch_data)
        except PDQConnectAuthError as err:
            raise UpdateFailed(f"Authentication error: {err}") from err
        except PDQConnectAPIError as err:
            raise UpdateFailed(f"PDQ Connect API error: {err}") from err
        except Exception as err:
            _LOGGER.exception("Unexpected error fetching PDQ Connect data")
            raise UpdateFailed(f"Unexpected error: {err}") from err

    def _fetch_data(self) -> PDQConnectData:
        _LOGGER.debug("Fetching PDQ Connect data")
        devices = self.api.list_all_devices()
        packages = self.api.list_all_packages()
        _LOGGER.debug(
            "Fetched %d devices and %d packages", len(devices), len(packages)
        )
        return PDQConnectData(devices=devices, packages=packages)
