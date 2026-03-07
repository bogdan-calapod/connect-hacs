"""Sensor platform for PDQ Connect."""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    PERCENTAGE,
    UnitOfInformation,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import ATTRIBUTION, DOMAIN
from .coordinator import PDQConnectCoordinator

_LOGGER = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Sensor descriptors
# ---------------------------------------------------------------------------

DEVICE_SENSOR_DESCRIPTIONS: tuple[SensorEntityDescription, ...] = (
    SensorEntityDescription(
        key="last_seen_at",
        name="Last Seen",
        device_class=SensorDeviceClass.TIMESTAMP,
        icon="mdi:clock-outline",
    ),
    SensorEntityDescription(
        key="os",
        name="OS",
        icon="mdi:microsoft-windows",
    ),
    SensorEntityDescription(
        key="osVersion",
        name="OS Version",
        icon="mdi:tag-outline",
    ),
    SensorEntityDescription(
        key="osFullName",
        name="OS Full Name",
        icon="mdi:information-outline",
    ),
    SensorEntityDescription(
        key="currentUser",
        name="Current User",
        icon="mdi:account",
    ),
    SensorEntityDescription(
        key="lastUser",
        name="Last User",
        icon="mdi:account-clock",
    ),
    SensorEntityDescription(
        key="freePercent",
        name="Free Disk",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:harddisk",
    ),
    SensorEntityDescription(
        key="memory",
        name="Memory",
        native_unit_of_measurement=UnitOfInformation.BYTES,
        device_class=SensorDeviceClass.DATA_SIZE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:memory",
    ),
    SensorEntityDescription(
        key="architecture",
        name="Architecture",
        icon="mdi:cpu-64-bit",
    ),
    SensorEntityDescription(
        key="manufacturer",
        name="Manufacturer",
        icon="mdi:factory",
    ),
    SensorEntityDescription(
        key="model",
        name="Model",
        icon="mdi:laptop",
    ),
    SensorEntityDescription(
        key="serialNumber",
        name="Serial Number",
        icon="mdi:barcode",
    ),
    SensorEntityDescription(
        key="publicIpAddress",
        name="Public IP",
        icon="mdi:ip-network",
    ),
    SensorEntityDescription(
        key="hostname",
        name="Hostname",
        icon="mdi:server-network",
    ),
)

# Sensors backed by the packages catalogue
PACKAGE_SENSOR_DESCRIPTIONS: tuple[SensorEntityDescription, ...] = (
    SensorEntityDescription(
        key="package_count",
        name="Package Count",
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:package-variant-closed",
    ),
)


# ---------------------------------------------------------------------------
# Platform setup
# ---------------------------------------------------------------------------


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up PDQ Connect sensor entities."""
    coordinator: PDQConnectCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities: list[SensorEntity] = []

    # One set of sensors per device
    for device in coordinator.data.devices:
        device_id = device.get("id")
        if not device_id:
            continue
        for desc in DEVICE_SENSOR_DESCRIPTIONS:
            entities.append(PDQDeviceSensor(coordinator, entry, device_id, desc))

    # Global package count sensor
    entities.append(PDQPackageCountSensor(coordinator, entry))

    async_add_entities(entities)
    _LOGGER.info("Created %d PDQ Connect sensor entities", len(entities))


# ---------------------------------------------------------------------------
# Device sensor
# ---------------------------------------------------------------------------


class PDQDeviceSensor(CoordinatorEntity[PDQConnectCoordinator], SensorEntity):
    """A sensor that tracks one attribute of a PDQ Connect device."""

    _attr_attribution = ATTRIBUTION
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: PDQConnectCoordinator,
        entry: ConfigEntry,
        device_id: str,
        description: SensorEntityDescription,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._device_id = device_id
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_{device_id}_{description.key}"

    # ------------------------------------------------------------------
    # Device info (groups all sensors for this device together in HA UI)
    # ------------------------------------------------------------------

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

    # ------------------------------------------------------------------
    # State
    # ------------------------------------------------------------------

    @property
    def _device_data(self) -> dict[str, Any]:
        return self.coordinator.data.devices_by_id.get(self._device_id, {})

    @property
    def native_value(self) -> Any:
        device = self._device_data
        key = self.entity_description.key
        value = device.get(key)

        if value is None:
            return None

        # Parse ISO-8601 timestamps into aware datetime objects
        if self.entity_description.device_class == SensorDeviceClass.TIMESTAMP:
            if isinstance(value, str):
                try:
                    dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
                    if dt.tzinfo is None:
                        dt = dt.replace(tzinfo=timezone.utc)
                    return dt
                except ValueError:
                    _LOGGER.debug("Could not parse timestamp: %s", value)
                    return None
            return value

        return value

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Expose the raw device payload as attributes on the last_seen sensor."""
        if self.entity_description.key != "last_seen_at":
            return {}
        device = self._device_data
        return {
            "device_id": device.get("id"),
            "os": device.get("os"),
            "os_version": device.get("osVersion"),
            "require_reboot": device.get("requireReboot"),
            "architecture": device.get("architecture"),
            "public_ip": device.get("publicIpAddress"),
        }


# ---------------------------------------------------------------------------
# Global package count sensor
# ---------------------------------------------------------------------------


class PDQPackageCountSensor(CoordinatorEntity[PDQConnectCoordinator], SensorEntity):
    """Reports the total number of packages in the PDQ Connect catalogue."""

    _attr_attribution = ATTRIBUTION
    _attr_has_entity_name = True
    _attr_icon = "mdi:package-variant-closed"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(
        self,
        coordinator: PDQConnectCoordinator,
        entry: ConfigEntry,
    ) -> None:
        super().__init__(coordinator)
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_package_count"
        self._attr_name = "PDQ Connect Package Count"

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, f"{self._entry.entry_id}_service")},
            name="PDQ Connect",
            manufacturer="PDQ",
            entry_type="service",
            configuration_url="https://app.pdq.com",
        )

    @property
    def native_value(self) -> int:
        return len(self.coordinator.data.packages)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {
            "packages": [
                {"id": p.get("id"), "name": p.get("name"), "publisher": p.get("publisher")}
                for p in self.coordinator.data.packages
            ]
        }
