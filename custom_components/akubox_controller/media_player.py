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
from homeassistant.const import STATE_IDLE # Using IDLE as a base state

from .const import DOMAIN, DEFAULT_NAME, UPDATE_INTERVAL_VOLUME
from .api import AkuBoxApiClient, AkuBoxApiError

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
    host: str = akubox_data["host"]
# In media_player.py async_setup_entry
# ...
    volume_scan_interval = entry.options.get(
        "scan_interval_volume", UPDATE_INTERVAL_VOLUME # UPDATE_INTERVAL_VOLUME from const.py as default
    )
    # Create a data update coordinator for volume
    volume_coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name=f"{DEFAULT_NAME} Volume ({host})",
        update_method=client.get_volume,
        update_interval=timedelta(seconds=UPDATE_INTERVAL_VOLUME),
    )

    # Fetch initial data
    await volume_coordinator.async_config_entry_first_refresh()

    # Determine device name using hostname (fetched via system_coordinator if possible, or fallback)
    # This assumes system_coordinator might have been set up by sensor.py
    # A more robust way would be to fetch system_info here if not available
    # For simplicity, we'll try to get hostname from client if possible
    device_name_prefix = DEFAULT_NAME
    hostname = host # Fallback
    try:
        # Attempt to get system_info again to ensure hostname is available for device naming
        # This could be optimized by sharing the system_coordinator or its data
        system_info = await client.get_system_info()
        api_hostname = client.get_hostname_from_system_info(system_info)
        if api_hostname:
            hostname = api_hostname
            device_name_prefix = f"{DEFAULT_NAME} ({hostname})"
        else:
            device_name_prefix = f"{DEFAULT_NAME} ({host})"

    except AkuBoxApiError:
        _LOGGER.warning("Could not fetch system info for hostname for media_player on %s", host)
        device_name_prefix = f"{DEFAULT_NAME} ({host})"


    device_info = {
        "identifiers": {(DOMAIN, entry.unique_id or entry.entry_id)},
        "name": device_name_prefix,
        "manufacturer": "AkuBox Custom",
        "model": "AkuBox Controller (Media)",
    }

    async_add_entities([AkuBoxMediaPlayer(volume_coordinator, client, entry, device_info)])


class AkuBoxMediaPlayer(CoordinatorEntity, MediaPlayerEntity):
    """Representation of an AkuBox Media Player (for volume control)."""

    _attr_supported_features = SUPPORT_AKUBOX
    _attr_has_entity_name = True # Uses the entity name directly, not device name + entity name

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        client: AkuBoxApiClient,
        config_entry: ConfigEntry,
        device_info: dict,
    ):
        """Initialize the media player."""
        super().__init__(coordinator)
        self._client = client
        self._config_entry = config_entry
        self._attr_name = "Volume Control" # This will be entity name, e.g. "AkuBox (hostname) Volume Control"
        self._attr_unique_id = f"{config_entry.unique_id}_mediaplayer_volume"
        self._attr_device_info = device_info
        self._attr_volume_level = None # Will be 0.0 to 1.0
        self._attr_state = STATE_IDLE # Default state as it's mainly for volume

    @property
    def state(self) -> MediaPlayerState:
        """Return the state of the player."""
        # If you had playback status, you'd map it here.
        # For a simple volume controller, IDLE or STANDBY is fine.
        return self._attr_state

    @property
    def volume_level(self) -> float | None:
        """Volume level of the media player (0..1)."""
        if self.coordinator.data and "volume" in self.coordinator.data:
            api_volume = self.coordinator.data["volume"]
            if isinstance(api_volume, (int, float)):
                 self._attr_volume_level = api_volume / 100.0
                 return self._attr_volume_level
        return self._attr_volume_level # Return last known if update failed


    async def async_set_volume_level(self, volume: float) -> None:
        """Set volume level, range 0..1."""
        api_volume = int(volume * 100)
        _LOGGER.debug("Setting AkuBox volume to %s (API: %s)", volume, api_volume)
        try:
            await self._client.set_volume(api_volume)
            self._attr_volume_level = volume # Optimistically update
            await self.coordinator.async_request_refresh() # Request a refresh to confirm
        except AkuBoxApiError as e:
            _LOGGER.error("Error setting AkuBox volume: %s", e)
        except ValueError as e: # From client's set_volume if value out of range
            _LOGGER.error("Invalid volume value for AkuBox: %s", e)


    async def async_volume_up(self) -> None:
        """Volume up the media player."""
        if self.volume_level is not None:
            current_api_volume = int(self.volume_level * 100)
            await self.async_set_volume_level(min(1.0, (current_api_volume + 5) / 100.0)) # Step by 5%

    async def async_volume_down(self) -> None:
        """Volume down media player."""
        if self.volume_level is not None:
            current_api_volume = int(self.volume_level * 100)
            await self.async_set_volume_level(max(0.0, (current_api_volume - 5) / 100.0)) # Step by 5%

    # Override update to parse volume from coordinator data
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        if self.coordinator.data and "volume" in self.coordinator.data:
            api_volume = self.coordinator.data["volume"]
            if isinstance(api_volume, (int, float)):
                self._attr_volume_level = api_volume / 100.0
                self._attr_state = STATE_IDLE # Or determine based on other data if available
            else:
                _LOGGER.warning("Received invalid volume data: %s", self.coordinator.data)
        else:
            _LOGGER.debug("No volume data in coordinator update: %s", self.coordinator.data)
        super()._handle_coordinator_update()