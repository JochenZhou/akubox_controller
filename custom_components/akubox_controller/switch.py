# /config/custom_components/akubox_controller/switch.py
import logging
import asyncio
from typing import Any

from homeassistant.components.switch import SwitchEntity, SwitchDeviceClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.const import CONF_HOST # Import CONF_HOST

from .const import (
    DOMAIN,
    # DEFAULT_NAME, # No longer needed here
    SWITCH_DLNA,
    SWITCH_LED_LOGO,
)
from .api import AkuBoxApiClient, AkuBoxApiError, AkuBoxApiConnectionError

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up AkuBox switches from a config entry."""
    akubox_data = hass.data[DOMAIN][entry.entry_id]
    client: AkuBoxApiClient = akubox_data["client"]
    # host: str = entry.data[CONF_HOST] # entry.title is now the primary device name

    device_info = {
        "identifiers": {(DOMAIN, entry.unique_id or entry.entry_id)},
        "name": entry.title, # Use the ConfigEntry title as the device name
        "manufacturer": "AkuBox Custom",
        "model": "AkuBox Controller", # Can be more specific if needed
    }
    # Try to populate sw_version and hw_version
    try:
        system_info_for_versions = await client.get_system_info()
        if sw_version := system_info_for_versions.get("system", {}).get("go_version"):
            device_info["sw_version"] = sw_version
        if os_name := system_info_for_versions.get("system", {}).get("os"):
            arch = system_info_for_versions.get('system', {}).get('architecture', 'N/A')
            device_info["hw_version"] = f"{os_name}/{arch}"
    except AkuBoxApiError as err:
        _LOGGER.warning("Could not fetch system_info for version details for %s switches: %s", entry.title, err)

    switches_to_add = [
        AkuBoxSwitch(client, entry, device_info, SWITCH_DLNA, "DLNA 服务", "mdi:dlna"),
        AkuBoxSwitch(client, entry, device_info, SWITCH_LED_LOGO, "LED Logo 灯", "mdi:led-on"),
    ]

    if switches_to_add:
        _LOGGER.info("Attempting initial update for %s switches for %s before adding to Home Assistant.", len(switches_to_add), entry.title)
        update_tasks = [switch_entity.async_update() for switch_entity in switches_to_add]
        try:
            await asyncio.gather(*update_tasks)
            _LOGGER.info("Initial update for switches for %s completed.", entry.title)
        except Exception as e:
            _LOGGER.error("Error during initial gather of switch updates for %s: %s", entry.title, e, exc_info=True)

    async_add_entities(switches_to_add)


class AkuBoxSwitch(SwitchEntity):
    """Representation of an AkuBox Switch."""

    _attr_should_poll = True
    _attr_has_entity_name = True # Name will be "DLNA 服务" or "LED Logo 灯"

    def __init__(
        self,
        client: AkuBoxApiClient,
        config_entry: ConfigEntry, # Keep for unique_id
        device_info: dict,
        switch_type: str,
        name_suffix: str, # This becomes the entity name
        default_icon: str,
    ):
        """Initialize the switch."""
        self._client = client
        self._switch_type = switch_type

        self._attr_unique_id = f"{config_entry.unique_id}_{switch_type}"
        self._attr_name = name_suffix # Set entity name directly
        self._attr_device_info = device_info # Links to device named by entry.title
        self._default_icon = default_icon
        self._attr_is_on: bool | None = None
        self._attr_available = True # Assume available until first update
        self.entity_id = f"switch.{DOMAIN}_{config_entry.unique_id}_{switch_type}".lower()


    @property
    def icon(self) -> str | None:
        """Return the icon to use in the frontend, if any."""
        if self._switch_type == SWITCH_LED_LOGO:
            return "mdi:led-on" if self.is_on else "mdi:led-off"
        return self._default_icon

    @property
    def device_class(self) -> SwitchDeviceClass | None:
        """Return the class of this entity."""
        return SwitchDeviceClass.SWITCH

    async def async_update(self) -> None:
        """Fetch new state data for the switch."""
        _LOGGER.debug("Attempting to update state for switch %s (%s)", self._attr_name, self.entity_id)
        try:
            if self._switch_type == SWITCH_DLNA:
                self._attr_is_on = await self._client.get_dlna_state()
            elif self._switch_type == SWITCH_LED_LOGO:
                self._attr_is_on = await self._client.get_led_logo_state()
            self._attr_available = True
            _LOGGER.debug("Successfully updated state for switch %s (%s): is_on=%s", self._attr_name, self.entity_id, self._attr_is_on)
        except AkuBoxApiConnectionError as err:
            _LOGGER.warning("Connection error fetching state for switch %s (%s): %s. Marking as unavailable.", self._attr_name, self.entity_id, err)
            self._attr_available = False
        except AkuBoxApiError as err:
            _LOGGER.error("API error fetching state for switch %s (%s): %s. Marking as unavailable.", self._attr_name, self.entity_id, err)
            self._attr_available = False
        except Exception as err: # pylint: disable=broad-except
            _LOGGER.exception("Unexpected error fetching state for switch %s (%s). Marking as unavailable.", self._attr_name, self.entity_id)
            self._attr_available = False

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the switch on."""
        try:
            if self._switch_type == SWITCH_DLNA:
                await self._client.set_dlna_state(True)
            elif self._switch_type == SWITCH_LED_LOGO:
                await self._client.set_led_logo_state(True)
            self._attr_is_on = True
            self._attr_available = True
        except AkuBoxApiError as e:
            _LOGGER.error("Error turning on %s (%s): %s", self._attr_name, self.entity_id, e)
            self._attr_available = False # Assume unavailable on error
        finally:
            self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the switch off."""
        try:
            if self._switch_type == SWITCH_DLNA:
                await self._client.set_dlna_state(False)
            elif self._switch_type == SWITCH_LED_LOGO:
                await self._client.set_led_logo_state(False)
            self._attr_is_on = False
            self._attr_available = True
        except AkuBoxApiError as e:
            _LOGGER.error("Error turning off %s (%s): %s", self._attr_name, self.entity_id, e)
            self._attr_available = False # Assume unavailable on error
        finally:
            self.async_write_ha_state()
