# /config/custom_components/akubox_controller/__init__.py
import logging
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.exceptions import ConfigEntryNotReady

from .const import DOMAIN, PLATFORMS, CONF_HOST
from .api import AkuBoxApiClient, AkuBoxApiConnectionError, AkuBoxApiAuthError

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up AkuBox Controller from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    host = entry.data[CONF_HOST]

    session = async_get_clientsession(hass)
    client = AkuBoxApiClient(host, session)

    try:
        # Test connection during setup
        if not await client.test_connection():
            raise ConfigEntryNotReady(f"Cannot connect to AkuBox at {host}")
        _LOGGER.info("Successfully connected to AkuBox at %s", host)
    except AkuBoxApiConnectionError as err:
        _LOGGER.error("Failed to connect to AkuBox at %s: %s", host, err)
        raise ConfigEntryNotReady(f"Connection error for AkuBox at {host}: {err}") from err
    except AkuBoxApiAuthError as err: # Future-proofing
        _LOGGER.error("Authentication error for AkuBox at %s: %s", host, err)
        raise ConfigEntryNotReady(f"Authentication error for AkuBox at {host}: {err}") from err


    hass.data[DOMAIN][entry.entry_id] = {
        "client": client,
        "host": host
        # If you need to access coordinators to update their interval directly,
        # they would need to be created here and stored in hass.data
        # For example:
        # "system_coordinator": system_coordinator,
        # "volume_coordinator": volume_coordinator,
    }

    # Forward the setup to platforms (sensor, media_player)
    # The options will be available to platforms via entry.options
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Register update listener for options
    entry.async_on_unload(entry.add_update_listener(update_listener))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    # The listener is automatically removed on unload by async_on_unload
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
        _LOGGER.info("Successfully unloaded AkuBox Controller for %s", entry.data[CONF_HOST])

    return unload_ok

async def update_listener(hass: HomeAssistant, entry: ConfigEntry):
   """Handle options update."""
   _LOGGER.info("Configuration options updated for %s, reloading integration to apply changes.", entry.title)
   # This will reload the integration, causing async_setup_entry to be called again.
   # Platforms (sensor.py, media_player.py) will then need to read the updated
   # scan intervals from entry.options when creating their DataUpdateCoordinators.
   await hass.config_entries.async_reload(entry.entry_id)