# /config/custom_components/akubox_controller/sensor.py
import logging
from datetime import timedelta, datetime, timezone
from typing import Any

from homeassistant.components.sensor import (
    SensorEntity,
    SensorDeviceClass,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed,
)
from homeassistant.const import (
    PERCENTAGE,
    UnitOfInformation,
    EntityCategory,
)

from .const import (
    DOMAIN,
    DEFAULT_NAME,
    UPDATE_INTERVAL_SYSTEM,
    SENSOR_CPU_USAGE,
    SENSOR_MEMORY_USAGE_PERCENT,
    SENSOR_BATTERY_CAPACITY,
    SENSOR_BATTERY_STATUS,
    SENSOR_UPTIME,
    SENSOR_HOSTNAME,
    SENSOR_OS,
    SENSOR_ARCHITECTURE,
    SENSOR_GO_VERSION,
    SENSOR_NUM_GOROUTINE,
    SENSOR_WORK_DIR,
    ATTR_CPU_NUM,
    ATTR_GO_MAX_PROC,
    ATTR_MEMORY_TOTAL_MB,
    ATTR_MEMORY_USED_MB,
)
from .api import AkuBoxApiClient, AkuBoxApiError

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up AkuBox sensors from a config entry."""
    akubox_data = hass.data[DOMAIN][entry.entry_id]
    client: AkuBoxApiClient = akubox_data["client"]
    host: str = akubox_data["host"] # Or derive from entry unique_id if preferred
    # In sensor.py async_setup_entry
    # ...
    # Get scan interval from options, fallback to const if not set
    system_scan_interval = entry.options.get(
        "scan_interval_system", UPDATE_INTERVAL_SYSTEM # UPDATE_INTERVAL_SYSTEM from const.py as default
    )
    
    system_coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name=f"{DEFAULT_NAME} System ({host})",
        update_method=client.get_system_info,
        update_interval=timedelta(seconds=system_scan_interval), # Use the interval from options
    )

    # Fetch initial data so we have it when entities are added
    await system_coordinator.async_config_entry_first_refresh()

    # Use hostname from API for device naming, fallback to host IP
    device_name_prefix = DEFAULT_NAME
    try:
        hostname = system_coordinator.data.get("system", {}).get("hostname", host)
        device_name_prefix = f"{DEFAULT_NAME} ({hostname})"
    except Exception: # pylint: disable=broad-except
        hostname = host # Fallback
        _LOGGER.warning("Could not determine hostname for %s, using IP.", host)


    device_info = {
        "identifiers": {(DOMAIN, entry.unique_id or entry.entry_id)}, # Use entry.unique_id (which we set to host)
        "name": device_name_prefix,
        "manufacturer": "AkuBox Custom", # Or your manufacturer name
        "model": "AkuBox Controller", # Can be enhanced if API provides model
        # "sw_version": system_coordinator.data.get("system", {}).get("go_version"), # Example
    }
    if sw_version := system_coordinator.data.get("system", {}).get("go_version"):
        device_info["sw_version"] = sw_version
    if os_name := system_coordinator.data.get("system", {}).get("os"):
        device_info["hw_version"] = f"{os_name}/{system_coordinator.data.get('system', {}).get('architecture', 'N/A')}"


    entities = [
        AkuBoxSystemSensor(system_coordinator, entry, SENSOR_CPU_USAGE, "CPU 使用率", device_info, unit=PERCENTAGE, device_class=None, state_class=SensorStateClass.MEASUREMENT, entity_category=None),
        AkuBoxSystemSensor(system_coordinator, entry, SENSOR_MEMORY_USAGE_PERCENT, "内存使用率", device_info, unit=PERCENTAGE, device_class=None, state_class=SensorStateClass.MEASUREMENT, entity_category=None),
        AkuBoxSystemSensor(system_coordinator, entry, SENSOR_BATTERY_CAPACITY, "电池容量", device_info, unit=PERCENTAGE, device_class=SensorDeviceClass.BATTERY, state_class=SensorStateClass.MEASUREMENT, entity_category=None),
        AkuBoxSystemSensor(system_coordinator, entry, SENSOR_BATTERY_STATUS, "电池状态", device_info, unit=None, device_class=None, state_class=None, entity_category=None), # No specific device_class for charging status string
        AkuBoxSystemSensor(system_coordinator, entry, SENSOR_UPTIME, "运行时间", device_info, unit=None, device_class=SensorDeviceClass.TIMESTAMP, state_class=None, entity_category=EntityCategory.DIAGNOSTIC),
        AkuBoxSystemSensor(system_coordinator, entry, SENSOR_HOSTNAME, "主机名", device_info, unit=None, device_class=None, state_class=None, entity_category=EntityCategory.DIAGNOSTIC),
        AkuBoxSystemSensor(system_coordinator, entry, SENSOR_OS, "操作系统", device_info, unit=None, device_class=None, state_class=None, entity_category=EntityCategory.DIAGNOSTIC),
        AkuBoxSystemSensor(system_coordinator, entry, SENSOR_ARCHITECTURE, "架构", device_info, unit=None, device_class=None, state_class=None, entity_category=EntityCategory.DIAGNOSTIC),
        AkuBoxSystemSensor(system_coordinator, entry, SENSOR_GO_VERSION, "Go 版本", device_info, unit=None, device_class=None, state_class=None, entity_category=EntityCategory.DIAGNOSTIC),
        AkuBoxSystemSensor(system_coordinator, entry, SENSOR_NUM_GOROUTINE, "Go 协程数", device_info, unit=None, device_class=None, state_class=SensorStateClass.MEASUREMENT, entity_category=EntityCategory.DIAGNOSTIC),
        AkuBoxSystemSensor(system_coordinator, entry, SENSOR_WORK_DIR, "工作目录", device_info, unit=None, device_class=None, state_class=None, entity_category=EntityCategory.DIAGNOSTIC),
    ]
    async_add_entities(entities)


class AkuBoxSystemSensor(CoordinatorEntity, SensorEntity):
    """Representation of an AkuBox System Sensor."""

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        config_entry: ConfigEntry,
        sensor_type: str,
        name_suffix: str,
        device_info: dict,
        unit: str | None = None,
        device_class: SensorDeviceClass | None = None,
        state_class: SensorStateClass | None = None,
        entity_category: EntityCategory | None = None,
    ):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._config_entry = config_entry
        self._sensor_type = sensor_type
        self._host = config_entry.data.get("host", "unknown_host") # Fallback for unique ID part

        # Determine unique ID using host and sensor type
        # For config_entry.unique_id to be available and stable, it must be set in config_flow
        # We set unique_id to host in config_flow
        self._attr_unique_id = f"{config_entry.unique_id}_{sensor_type}"
        self._attr_name = f"{device_info['name']} {name_suffix}" # Use the potentially hostname-enriched name
        self._attr_device_info = device_info
        self._attr_native_unit_of_measurement = unit
        self._attr_device_class = device_class
        self._attr_state_class = state_class
        self._attr_entity_category = entity_category
        self._attr_extra_state_attributes = {}


    @property
    def native_value(self) -> Any:
        """Return the state of the sensor."""
        data = self.coordinator.data
        if not data:
            return None

        try:
            if self._sensor_type == SENSOR_CPU_USAGE:
                val = data.get("cpu", {}).get("usage")
                return round(val, 2) if val is not None else None
            elif self._sensor_type == SENSOR_MEMORY_USAGE_PERCENT:
                mem = data.get("memory", {})
                total = mem.get("total")
                used = mem.get("used")
                if total and used is not None and total > 0:
                    return round((used / total) * 100, 2)
                return None
            elif self._sensor_type == SENSOR_BATTERY_CAPACITY:
                return data.get("battery", {}).get("capacity")
            elif self._sensor_type == SENSOR_BATTERY_STATUS:
                return data.get("battery", {}).get("status")
            elif self._sensor_type == SENSOR_UPTIME:
                start_time_str = data.get("system", {}).get("start_time")
                if start_time_str:
                    # Format example: "2025-05-21T15:31:24.414714711+08:00"
                    # Python's datetime.fromisoformat handles this well
                    try:
                        return datetime.fromisoformat(start_time_str)
                    except ValueError:
                         _LOGGER.warning("Could not parse uptime string: %s", start_time_str)
                         # Try to parse without nanoseconds if previous fails
                         try:
                             dt_obj = datetime.strptime(start_time_str.split('.')[0] + start_time_str.split('+')[1].split(':')[0], "%Y-%m-%dT%H:%M:%S%z")
                             return dt_obj.astimezone(timezone.utc) # Ensure UTC for HA
                         except Exception as e:
                             _LOGGER.error("Failed to parse uptime %s: %s", start_time_str, e)
                             return None
                return None
            elif self._sensor_type == SENSOR_HOSTNAME:
                return data.get("system", {}).get("hostname")
            elif self._sensor_type == SENSOR_OS:
                return data.get("system", {}).get("os")
            elif self._sensor_type == SENSOR_ARCHITECTURE:
                return data.get("system", {}).get("architecture")
            elif self._sensor_type == SENSOR_GO_VERSION:
                return data.get("system", {}).get("go_version")
            elif self._sensor_type == SENSOR_NUM_GOROUTINE:
                return data.get("system", {}).get("num_goroutine")
            elif self._sensor_type == SENSOR_WORK_DIR:
                return data.get("system", {}).get("work_dir")

        except (KeyError, TypeError, AttributeError) as e:
            _LOGGER.debug("Could not retrieve sensor data for %s: %s. Data: %s", self._sensor_type, e, data)
            return None
        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional state attributes."""
        attrs = {}
        data = self.coordinator.data
        if not data:
            return attrs

        try:
            if self._sensor_type == SENSOR_CPU_USAGE:
                cpu_data = data.get("cpu", {})
                if ATTR_CPU_NUM in cpu_data: attrs[ATTR_CPU_NUM] = cpu_data[ATTR_CPU_NUM]
                if ATTR_GO_MAX_PROC in cpu_data: attrs[ATTR_GO_MAX_PROC] = cpu_data[ATTR_GO_MAX_PROC]
            elif self._sensor_type == SENSOR_MEMORY_USAGE_PERCENT:
                mem_data = data.get("memory", {})
                if "total" in mem_data: attrs[ATTR_MEMORY_TOTAL_MB] = round(mem_data["total"] / (1024*1024), 2)
                if "used" in mem_data: attrs[ATTR_MEMORY_USED_MB] = round(mem_data["used"] / (1024*1024), 2)
        except (KeyError, TypeError, AttributeError):
            pass # Silently ignore if attributes are not found
        return attrs
