"""Binary sensor platform for PDQ Connect – device online/offline."""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import ATTRIBUTION, DOMAIN, ONLINE_THRESHOLD_SECONDS
from .coordinator import PDQConnectCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up PDQ Connect binary sensor entities."""
    coordinator: PDQConnectCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities = [
        PDQDeviceOnlineSensor(coordinator, entry, device["id"])
        for device in coordinator.data.devices
        if "id" in device
    ]

    async_add_entities(entities)
    _LOGGER.info(
        "Created %d PDQ Connect binary sensor entities", len(entities)
    )


class PDQDeviceOnlineSensor(
    CoordinatorEntity[PDQConnectCoordinator], BinarySensorEntity
):
    """Binary sensor that is ON when a device was seen recently."""

    _attr_attribution = ATTRIBUTION
    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
    _attr_has_entity_name = True
    _attr_name = "Online"

    def __init__(
        self,
        coordinator: PDQConnectCoordinator,
        entry: ConfigEntry,
        device_id: str,
    ) -> None:
        super().__init__(coordinator)
        self._device_id = device_id
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_{device_id}_online"

    @property
    def _device_data(self) -> dict[str, Any]:
        return self.coordinator.data.devices_by_id.get(self._device_id, {})

    @property
    def device_info(self) -> DeviceInfo:
        device = self._device_data
        return DeviceInfo(
            identifiers={(DOMAIN, self._device_id)},
            name=device.get("name") or device.get("hostname") or self._device_id,
            manufacturer=device.get("manufacturer"),
            model=device.get("model"),
            sw_version=device.get("osFullName") or device.get("os"),
            serial_number=device.get("serialNumber"),
            configuration_url="https://app.pdq.com",
        )

    @property
    def is_on(self) -> bool | None:
        """Return True when the device was seen within the online threshold."""
        device = self._device_data
        last_seen_raw = device.get("lastSeenAt")
        if not last_seen_raw:
            return None

        try:
            last_seen = datetime.fromisoformat(
                last_seen_raw.replace("Z", "+00:00")
            )
            if last_seen.tzinfo is None:
                last_seen = last_seen.replace(tzinfo=timezone.utc)
        except ValueError:
            _LOGGER.debug("Could not parse lastSeenAt: %s", last_seen_raw)
            return None

        threshold = datetime.now(tz=timezone.utc) - timedelta(
            seconds=ONLINE_THRESHOLD_SECONDS
        )
        return last_seen >= threshold

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        device = self._device_data
        return {
            "device_id": device.get("id"),
            "last_seen_at": device.get("lastSeenAt"),
            "hostname": device.get("hostname"),
            "current_user": device.get("currentUser"),
            "require_reboot": device.get("requireReboot"),
        }
