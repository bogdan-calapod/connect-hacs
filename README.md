# PDQ Connect – Home Assistant Integration

A custom Home Assistant integration for [PDQ Connect](https://www.pdq.com/pdq-connect/),
the cloud-based endpoint management platform.

## Features

- **Device sensors** – per-device sensors for: Last Seen, OS, OS Version, OS Full Name,
  Current User, Last User, Free Disk %, Memory, Architecture, Manufacturer, Model,
  Serial Number, Public IP, Hostname
- **Device online binary sensor** – ON when a device was last seen within the
  configurable threshold (default 10 minutes)
- **Package count sensor** – total number of packages in your PDQ Connect catalogue,
  with a full package list in its attributes
- **Deploy package service** – `pdq_connect.deploy_package` to trigger deployments
  from HA automations

## Requirements

- Home Assistant 2024.1.0 or later
- A PDQ Connect account with an API key

## Installation

### HACS (recommended)

1. Add this repository as a custom HACS repository (category: Integration)
2. Install **PDQ Connect** from HACS
3. Restart Home Assistant

### Manual

1. Copy `custom_components/pdq_connect/` into your HA `config/custom_components/` directory
2. Restart Home Assistant

## Configuration

1. Go to **Settings → Devices & Services → Add Integration**
2. Search for **PDQ Connect**
3. Enter your API key (generate one in PDQ Connect under **Settings → API Keys**)
4. Optionally set the polling interval (default: 300 s)

## Service: `pdq_connect.deploy_package`

Trigger a package deployment from an automation or the Developer Tools:

```yaml
action: pdq_connect.deploy_package
data:
  package_id: "pkg_1bced782734040a581d"      # or a pkgver_... ID
  target_ids:
    - "grp_1bced782734040a581d"               # group ID
    - "dvc_1bced782734040a581d"               # device ID
```

`package_id` and `target_ids` values can be found in the sensor attributes or
directly in the PDQ Connect web app.

## Entities created

For each enrolled device PDQ Connect knows about:

| Entity | Type | Description |
|---|---|---|
| `sensor.<name>_last_seen` | Sensor (timestamp) | Last time the device checked in |
| `binary_sensor.<name>_online` | Binary Sensor | ON if seen within 10 min |
| `sensor.<name>_os` | Sensor | OS type (windows / mac / linux) |
| `sensor.<name>_os_version` | Sensor | OS version string |
| `sensor.<name>_os_full_name` | Sensor | Full OS name |
| `sensor.<name>_current_user` | Sensor | Currently logged-in user |
| `sensor.<name>_last_user` | Sensor | Last logged-in user |
| `sensor.<name>_free_disk` | Sensor (%) | Free disk percentage |
| `sensor.<name>_memory` | Sensor (B) | Total RAM in bytes |
| `sensor.<name>_architecture` | Sensor | CPU architecture |
| `sensor.<name>_manufacturer` | Sensor | Device manufacturer |
| `sensor.<name>_model` | Sensor | Device model |
| `sensor.<name>_serial_number` | Sensor | Serial number |
| `sensor.<name>_public_ip` | Sensor | Public IP address |
| `sensor.<name>_hostname` | Sensor | Hostname |

Plus one global entity:

| Entity | Type | Description |
|---|---|---|
| `sensor.pdq_connect_package_count` | Sensor | Total packages in catalogue |

## License

MIT – see [LICENSE](LICENSE)
