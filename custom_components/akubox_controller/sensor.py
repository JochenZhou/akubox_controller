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
    EntityCategory,
    CONF_HOST, # Import CONF_HOST
)

from .const import (
    DOMAIN,
    # DEFAULT_NAME, # No longer needed here for device_info name
    UPDATE_INTERVAL_SYSTEM,
    SENSOR_CPU_USAGE,
    SENSOR_MEMORY_USAGE_PERCENT,
    SENSOR_BATTERY_LEVEL,
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
    # host: str = entry.data[CONF_HOST] # entry.title is now the primary device name

    system_scan_interval = entry.options.get(
        "scan_interval_system", UPDATE_INTERVAL_SYSTEM
    )

    # Use entry.title for coordinator name for better logging/identification
    coordinator_name = f"{entry.title} System Info"
    system_coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name=coordinator_name,
        update_method=client.get_system_info,
        update_interval=timedelta(seconds=system_scan_interval),
    )

    await system_coordinator.async_config_entry_first_refresh()

    device_info = {
        "identifiers": {(DOMAIN, entry.unique_id or entry.entry_id)}, # unique_id is host IP
        "name": entry.title,  # Use the ConfigEntry title as the device name
        "manufacturer": "AkuBox Custom",
        "model": "AkuBox Controller",
    }

    # Try to populate sw_version and hw_version from coordinator data
    # This data might also be available directly from client.get_system_info() if needed
    # but coordinator is preferred if data is already fetched.
    if system_coordinator.data:
        if sw_version := system_coordinator.data.get("system", {}).get("go_version"):
            device_info["sw_version"] = sw_version
        if os_name := system_coordinator.data.get("system", {}).get("os"):
            arch = system_coordinator.data.get('system', {}).get('architecture', 'N/A')
            device_info["hw_version"] = f"{os_name}/{arch}"
    else: # Fallback if coordinator data is not yet available or first refresh failed
        try:
            _LOGGER.debug("Coordinator data not available for device info on %s, attempting direct fetch.", entry.title)
            direct_system_info = await client.get_system_info()
            if sw_version := direct_system_info.get("system", {}).get("go_version"):
                device_info["sw_version"] = sw_version
            if os_name := direct_system_info.get("system", {}).get("os"):
                arch = direct_system_info.get('system', {}).get('architecture', 'N/A')
                device_info["hw_version"] = f"{os_name}/{arch}"
        except AkuBoxApiError as err:
            _LOGGER.warning("Could not fetch system_info for version details for %s: %s", entry.title, err)


    entities = [
        AkuBoxSystemSensor(system_coordinator, entry, SENSOR_CPU_USAGE, "CPU 使用率", device_info, unit=PERCENTAGE, device_class=None, state_class=SensorStateClass.MEASUREMENT, entity_category=None, icon="mdi:chip"),
        AkuBoxSystemSensor(system_coordinator, entry, SENSOR_MEMORY_USAGE_PERCENT, "内存使用率", device_info, unit=PERCENTAGE, device_class=None, state_class=SensorStateClass.MEASUREMENT, entity_category=None, icon="mdi:memory"),
        AkuBoxSystemSensor(system_coordinator, entry, SENSOR_BATTERY_LEVEL, "电池电量", device_info, unit=PERCENTAGE, device_class=SensorDeviceClass.BATTERY, state_class=SensorStateClass.MEASUREMENT, entity_category=None),
        AkuBoxSystemSensor(system_coordinator, entry, SENSOR_BATTERY_STATUS, "电池状态", device_info, unit=None, device_class=None, state_class=None, entity_category=None, icon="mdi:battery-charging"),
        AkuBoxSystemSensor(system_coordinator, entry, SENSOR_UPTIME, "运行时间", device_info, unit=None, device_class=SensorDeviceClass.TIMESTAMP, state_class=None, entity_category=EntityCategory.DIAGNOSTIC),
        AkuBoxSystemSensor(system_coordinator, entry, SENSOR_HOSTNAME, "主机名", device_info, unit=None, device_class=None, state_class=None, entity_category=EntityCategory.DIAGNOSTIC, icon="mdi:card-account-details-outline"),
        AkuBoxSystemSensor(system_coordinator, entry, SENSOR_OS, "操作系统", device_info, unit=None, device_class=None, state_class=None, entity_category=EntityCategory.DIAGNOSTIC, icon="mdi:linux"),
        AkuBoxSystemSensor(system_coordinator, entry, SENSOR_ARCHITECTURE, "架构", device_info, unit=None, device_class=None, state_class=None, entity_category=EntityCategory.DIAGNOSTIC, icon="mdi:chip"),
        AkuBoxSystemSensor(system_coordinator, entry, SENSOR_GO_VERSION, "Go 版本", device_info, unit=None, device_class=None, state_class=None, entity_category=EntityCategory.DIAGNOSTIC, icon="mdi:language-go"),
        AkuBoxSystemSensor(system_coordinator, entry, SENSOR_NUM_GOROUTINE, "Go 协程数", device_info, unit=None, device_class=None, state_class=SensorStateClass.MEASUREMENT, entity_category=EntityCategory.DIAGNOSTIC, icon="mdi:cog-sync-outline"),
        AkuBoxSystemSensor(system_coordinator, entry, SENSOR_WORK_DIR, "工作目录", device_info, unit=None, device_class=None, state_class=None, entity_category=EntityCategory.DIAGNOSTIC, icon="mdi:folder-cog-outline"),
    ]
    async_add_entities(entities)


class AkuBoxSystemSensor(CoordinatorEntity, SensorEntity):
    """Representation of an AkuBox System Sensor."""
    _attr_has_entity_name = True # Use the name_suffix as the entity name part

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        config_entry: ConfigEntry, # Keep config_entry for unique_id generation
        sensor_type: str,
        name_suffix: str, # This will become the entity's specific name part
        device_info: dict,
        unit: str | None = None,
        device_class: SensorDeviceClass | None = None,
        state_class: SensorStateClass | None = None,
        entity_category: EntityCategory | None = None,
        icon: str | None = None,
    ):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._sensor_type = sensor_type

        # Unique ID uses entry.unique_id (which is host IP) and sensor_type
        self._attr_unique_id = f"{config_entry.unique_id}_{sensor_type}"
        # Device name is from device_info (entry.title)
        # Entity name will be "Device Name Name Suffix" if _attr_has_entity_name = False
        # If _attr_has_entity_name = True, self.name property or self._attr_name should be just the "Name Suffix"
        self.entity_id = f"sensor.{DOMAIN}_{config_entry.unique_id}_{sensor_type}".lower() # Optional: helps with predictable entity_id
        self._attr_name = name_suffix # Set entity name directly (e.g., "CPU 使用率")
        self._attr_device_info = device_info
        self._attr_native_unit_of_measurement = unit
        self._attr_device_class = device_class
        self._attr_state_class = state_class
        self._attr_entity_category = entity_category
        if icon is not None:
             self._attr_icon = icon

    @property
    def native_value(self) -> Any:
        """Return the state of the sensor."""
        if self.coordinator.data is None:
            return None
        data = self.coordinator.data

        try:
            if self._sensor_type == SENSOR_CPU_USAGE:
                val = data.get("cpu", {}).get("usage")
                return round(val, 2) if val is not None else None
            elif self._sensor_type == SENSOR_MEMORY_USAGE_PERCENT:
                mem = data.get("memory", {})
                total = mem.get("total")
                used = mem.get("used")
                if total is not None and used is not None and total > 0:
                    return round((used / total) * 100, 2)
                return None
            elif self._sensor_type == SENSOR_BATTERY_LEVEL:
                return data.get("battery", {}).get("capacity")
            elif self._sensor_type == SENSOR_BATTERY_STATUS:
                return data.get("battery", {}).get("status")
            elif self._sensor_type == SENSOR_UPTIME:
                start_time_str = data.get("system", {}).get("start_time")
                if start_time_str:
                    try:
                        return datetime.fromisoformat(start_time_str)
                    except ValueError:
                         _LOGGER.warning("Could not parse uptime string: %s for %s", start_time_str, self.entity_id)
                         try:
                             parts = start_time_str.split('.')
                             dt_part = parts[0]
                             if '+' in start_time_str:
                                 tz_part_str = '+' + start_time_str.split('+')[-1]
                             elif '-' in start_time_str.split('T')[-1]:
                                 # Check if it's a timezone offset or part of the date/time
                                 potential_tz_part = start_time_str.split('T')[-1]
                                 if '-' in potential_tz_part and len(potential_tz_part.split('-')) > 2 : # e.g. 15:30:00-07:00
                                    tz_part_str = '-' + potential_tz_part.split('-')[-2] + potential_tz_part.split('-')[-1]
                                 else: # No valid timezone offset found this way
                                    tz_part_str = ""
                             else:
                                 tz_part_str = ""

                             if tz_part_str:
                                 dt_obj = datetime.strptime(dt_part + tz_part_str.replace(':', ''), "%Y-%m-%dT%H:%M:%S%z")
                                 return dt_obj
                             else:
                                 dt_obj = datetime.strptime(dt_part, "%Y-%m-%dT%H:%M:%S")
                                 return dt_obj.replace(tzinfo=timezone.utc)

                         except Exception as e:
                             _LOGGER.error("Failed to parse uptime string '%s' with custom logic for %s: %s", start_time_str, self.entity_id, e)
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
            _LOGGER.debug("Could not retrieve sensor data for %s (%s): %s. Data: %s", self.name, self._sensor_type, e, data)
            return None
        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return additional state attributes."""
        if self.coordinator.data is None:
            return None
        data = self.coordinator.data
        attrs: dict[str, Any] = {}

        try:
            if self._sensor_type == SENSOR_CPU_USAGE:
                cpu_data = data.get("cpu", {})
                if ATTR_CPU_NUM in cpu_data: attrs[ATTR_CPU_NUM] = cpu_data[ATTR_CPU_NUM]
                if ATTR_GO_MAX_PROC in cpu_data: attrs[ATTR_GO_MAX_PROC] = cpu_data[ATTR_GO_MAX_PROC]
            elif self._sensor_type == SENSOR_MEMORY_USAGE_PERCENT:
                mem_data = data.get("memory", {})
                if "total" in mem_data and mem_data["total"] is not None:
                    attrs[ATTR_MEMORY_TOTAL_MB] = round(mem_data["total"] / (1024*1024), 2)
                if "used" in mem_data and mem_data["used"] is not None:
                    attrs[ATTR_MEMORY_USED_MB] = round(mem_data["used"] / (1024*1024), 2)
        except (KeyError, TypeError, AttributeError):
            pass
        return attrs if attrs else None