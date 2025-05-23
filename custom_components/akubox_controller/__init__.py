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
        if not await client.test_connection():
            raise ConfigEntryNotReady(f"Cannot connect to AkuBox at {host}")
        _LOGGER.info("Successfully connected to AkuBox at %s", host)
    except AkuBoxApiConnectionError as err:
        _LOGGER.error("Failed to connect to AkuBox at %s: %s", host, err)
        raise ConfigEntryNotReady(f"Connection error for AkuBox at {host}: {err}") from err
    except AkuBoxApiAuthError as err:
        _LOGGER.error("Authentication error for AkuBox at %s: %s", host, err)
        raise ConfigEntryNotReady(f"Authentication error for AkuBox at {host}: {err}") from err


    hass.data[DOMAIN][entry.entry_id] = {
        "client": client,
        "host": host
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    entry.async_on_unload(entry.add_update_listener(update_listener))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
        _LOGGER.info("Successfully unloaded AkuBox Controller for %s", entry.data[CONF_HOST])

    return unload_ok

async def update_listener(hass: HomeAssistant, entry: ConfigEntry):
   """Handle options update."""
   _LOGGER.info("Configuration options updated for %s, reloading integration to apply changes.", entry.title)
   await hass.config_entries.async_reload(entry.entry_id)