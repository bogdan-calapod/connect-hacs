"""Constants for the PDQ Connect integration."""

DOMAIN = "pdq_connect"

# API base
API_BASE_URL = "https://app.pdq.com"

# Endpoints
API_DEVICES = f"{API_BASE_URL}/v1/api/devices"
API_DEVICE = f"{API_BASE_URL}/v1/api/devices/{{device_id}}"
API_GROUPS = f"{API_BASE_URL}/v1/api/groups"
API_PACKAGES = f"{API_BASE_URL}/v1/api/packages"
API_PACKAGE = f"{API_BASE_URL}/v1/api/packages/{{package_id}}"
API_DEPLOYMENTS = f"{API_BASE_URL}/v1/api/deployments"

# Config keys
CONF_API_KEY = "api_key"
CONF_UPDATE_INTERVAL = "update_interval"

# Defaults
DEFAULT_UPDATE_INTERVAL = 300   # 5 minutes
MIN_UPDATE_INTERVAL = 60        # 1 minute
MAX_UPDATE_INTERVAL = 3600      # 1 hour

# Sensor types: used as unique_id suffixes and display labels
SENSOR_OS = "os"
SENSOR_OS_VERSION = "os_version"
SENSOR_OS_FULL_NAME = "os_full_name"
SENSOR_LAST_SEEN = "last_seen_at"
SENSOR_CURRENT_USER = "current_user"
SENSOR_LAST_USER = "last_user"
SENSOR_FREE_PERCENT = "free_percent"
SENSOR_MEMORY = "memory"
SENSOR_MANUFACTURER = "manufacturer"
SENSOR_MODEL = "model"
SENSOR_SERIAL = "serial_number"
SENSOR_ARCHITECTURE = "architecture"
SENSOR_REQUIRE_REBOOT = "require_reboot"

# Service names
SERVICE_DEPLOY_PACKAGE = "deploy_package"

# Service call attributes
ATTR_PACKAGE_ID = "package_id"
ATTR_TARGET_IDS = "target_ids"

# "Online" threshold: device considered online if last seen within this many seconds
ONLINE_THRESHOLD_SECONDS = 600  # 10 minutes

ATTRIBUTION = "Data provided by PDQ Connect"
