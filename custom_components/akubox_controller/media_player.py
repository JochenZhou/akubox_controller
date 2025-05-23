# /config/custom_components/akubox_controller/media_player.py
import logging
from datetime import timedelta

from homeassistant.components.media_player import (
    MediaPlayerEntity,
    MediaPlayerEntityFeature,
    MediaPlayerState,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed,
)
from homeassistant.const import STATE_IDLE, CONF_HOST

from .const import DOMAIN, UPDATE_INTERVAL_VOLUME # DEFAULT_NAME no longer needed here
from .api import AkuBoxApiClient, AkuBoxApiError, DEVICE_VOLUME_MAX

_LOGGER = logging.getLogger(__name__)

SUPPORT_AKUBOX = MediaPlayerEntityFeature.VOLUME_SET | MediaPlayerEntityFeature.VOLUME_STEP

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up AkuBox media_player from a config entry."""
    akubox_data = hass.data[DOMAIN][entry.entry_id]
    client: AkuBoxApiClient = akubox_data["client"]
    # host: str = entry.data[CONF_HOST] # entry.title is now the primary device name

    volume_scan_interval = entry.options.get(
        "scan_interval_volume", UPDATE_INTERVAL_VOLUME
    )

    coordinator_name = f"{entry.title} Volume" # Use entry.title for coordinator name
    volume_coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name=coordinator_name,
        update_method=client.get_volume,
        update_interval=timedelta(seconds=volume_scan_interval),
    )

    await volume_coordinator.async_config_entry_first_refresh()

    device_info = {
        "identifiers": {(DOMAIN, entry.unique_id or entry.entry_id)},
        "name": entry.title, # Use the ConfigEntry title as the device name
        "manufacturer": "AkuBox Custom",
        "model": "AkuBox Controller (Media)", # Specific model for media player part
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
        _LOGGER.warning("Could not fetch system_info for version details for %s media_player: %s", entry.title, err)


    async_add_entities([AkuBoxMediaPlayer(volume_coordinator, client, entry, device_info)])


class AkuBoxMediaPlayer(CoordinatorEntity, MediaPlayerEntity):
    """Representation of an AkuBox Media Player (for volume control)."""

    _attr_supported_features = SUPPORT_AKUBOX
    _attr_has_entity_name = True # Name will be "Volume Control"

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        client: AkuBoxApiClient,
        config_entry: ConfigEntry, # Keep for unique_id
        device_info: dict,
    ):
        """Initialize the media player."""
        super().__init__(coordinator)
        self._client = client
        self._attr_name = "Volume Control" # This is the entity specific name
        self._attr_unique_id = f"{config_entry.unique_id}_mediaplayer_volume"
        self._attr_device_info = device_info # This links to the device named by entry.title
        self._attr_volume_level: float | None = None
        self._attr_state = STATE_IDLE

    @property
    def state(self) -> MediaPlayerState:
        """Return the state of the player."""
        return self._attr_state

    @property
    def volume_level(self) -> float | None:
        """Volume level of the media player (0..1)."""
        if self.coordinator.data and "volume" in self.coordinator.data:
            api_volume = self.coordinator.data["volume"]
            if isinstance(api_volume, (int, float)) and DEVICE_VOLUME_MAX > 0:
                 self._attr_volume_level = max(0.0, min(1.0, api_volume / DEVICE_VOLUME_MAX))
                 return self._attr_volume_level
        return self._attr_volume_level


    async def async_set_volume_level(self, volume: float) -> None:
        """Set volume level, range 0..1."""
        if DEVICE_VOLUME_MAX <= 0:
            _LOGGER.error("DEVICE_VOLUME_MAX is not positive for %s, cannot set volume.", self.entity_id)
            return

        api_volume = round(volume * DEVICE_VOLUME_MAX)
        api_volume = max(0, min(int(DEVICE_VOLUME_MAX), api_volume))

        _LOGGER.debug("Setting AkuBox volume for %s to HA level %s (API: %s)", self.entity_id, volume, api_volume)
        try:
            await self._client.set_volume(api_volume)
            self._attr_volume_level = volume
            await self.coordinator.async_request_refresh()
        except AkuBoxApiError as e:
            _LOGGER.error("Error setting AkuBox volume for %s: %s", self.entity_id, e)
        except ValueError as e: # From client's set_volume if value out of range
            _LOGGER.error("Invalid volume value for AkuBox %s: %s", self.entity_id, e)


    async def async_volume_up(self) -> None:
        """Volume up the media player."""
        if self.volume_level is not None and DEVICE_VOLUME_MAX > 0:
            current_api_volume = round(self.volume_level * DEVICE_VOLUME_MAX)
            new_api_volume = min(int(DEVICE_VOLUME_MAX), current_api_volume + 3)
            new_ha_volume = new_api_volume / DEVICE_VOLUME_MAX
            await self.async_set_volume_level(new_ha_volume)

    async def async_volume_down(self) -> None:
        """Volume down media player."""
        if self.volume_level is not None and DEVICE_VOLUME_MAX > 0:
            current_api_volume = round(self.volume_level * DEVICE_VOLUME_MAX)
            new_api_volume = max(0, current_api_volume - 3)
            new_ha_volume = new_api_volume / DEVICE_VOLUME_MAX
            await self.async_set_volume_level(new_ha_volume)

    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        if self.coordinator.data and "volume" in self.coordinator.data:
            api_volume = self.coordinator.data["volume"]
            if isinstance(api_volume, (int, float)) and DEVICE_VOLUME_MAX > 0:
                self._attr_volume_level = max(0.0, min(1.0, api_volume / DEVICE_VOLUME_MAX))
                self._attr_state = STATE_IDLE
            else:
                _LOGGER.warning("Received invalid volume data for %s: %s or DEVICE_VOLUME_MAX is invalid", self.entity_id, self.coordinator.data)
        else:
            _LOGGER.debug("No volume data in coordinator update for %s: %s", self.entity_id, self.coordinator.data)
        super()._handle_coordinator_update()