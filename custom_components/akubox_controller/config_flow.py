# /config/custom_components/akubox_controller/config_flow.py
import voluptuous as vol
import logging
from typing import Any

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.const import CONF_HOST

from .const import (
    DOMAIN,
    DEFAULT_NAME,
    UPDATE_INTERVAL_SYSTEM,
    UPDATE_INTERVAL_VOLUME,
    CONF_CUSTOM_NAME,      # 新增
    GENERIC_HOSTNAMES,     # 新增
)
from .api import AkuBoxApiClient, AkuBoxApiConnectionError, AkuBoxApiAuthError

_LOGGER = logging.getLogger(__name__)

DATA_SCHEMA = vol.Schema({
    vol.Required(CONF_HOST): str,
    vol.Optional(CONF_CUSTOM_NAME, default=""): str, # 新增自定义名称字段
})

class AkuBoxConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for AkuBox Controller."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_POLL

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        """Handle the initial step."""
        errors = {}
        if user_input is not None:
            host = user_input[CONF_HOST]
            custom_name = user_input.get(CONF_CUSTOM_NAME, "").strip()

            await self.async_set_unique_id(host) # Unique ID is still the host IP
            self._abort_if_unique_id_configured()

            session = async_get_clientsession(self.hass)
            client = AkuBoxApiClient(host, session)
            entry_title: str

            try:
                system_info = await client.get_system_info()
                api_hostname = client.get_hostname_from_system_info(system_info)

                if custom_name:
                    entry_title = custom_name
                elif api_hostname and api_hostname.lower() not in GENERIC_HOSTNAMES:
                    entry_title = f"{DEFAULT_NAME} ({api_hostname})"
                else:
                    entry_title = f"{DEFAULT_NAME} ({host})"

                # Store the host and potentially the custom_name if needed elsewhere from entry.data
                # For this purpose, only host is strictly needed in data for client re-creation.
                # The title handles the display name.
                config_data_to_store = {
                    CONF_HOST: host,
                    # CONF_CUSTOM_NAME: custom_name # Storing it if needed for other purposes
                }
                if custom_name: # Optionally store custom_name if provided
                    config_data_to_store[CONF_CUSTOM_NAME] = custom_name


                return self.async_create_entry(
                    title=entry_title,
                    data=config_data_to_store
                )
            except AkuBoxApiConnectionError:
                errors["base"] = "cannot_connect"
                _LOGGER.error("Failed to connect to AkuBox at %s", host)
            except AkuBoxApiAuthError:
                errors["base"] = "invalid_auth"
                _LOGGER.error("Authentication failed for AkuBox at %s", host)
            except Exception as e:
                _LOGGER.exception("Unexpected exception during AkuBox setup at %s: %s", host, e)
                errors["base"] = "unknown"

        # Prepare schema with defaults (especially if coming back from an error)
        current_host = ""
        current_custom_name = ""
        if user_input: # Repopulate form if there was an error
            current_host = user_input.get(CONF_HOST, "")
            current_custom_name = user_input.get(CONF_CUSTOM_NAME, "")

        form_schema = vol.Schema({
            vol.Required(CONF_HOST, default=current_host): str,
            vol.Optional(CONF_CUSTOM_NAME, default=current_custom_name): str,
        })

        return self.async_show_form(
            step_id="user", data_schema=form_schema, errors=errors
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: config_entries.ConfigEntry) -> config_entries.OptionsFlow:
        """Get the options flow for this handler."""
        return AkuBoxOptionsFlowHandler(config_entry)


class AkuBoxOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle an options flow for AkuBox Controller."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> dict[str, Any]:
        """Manage the options."""
        errors = {} # Not currently used for options validation but good practice
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        scan_interval_system = self.config_entry.options.get(
            "scan_interval_system", UPDATE_INTERVAL_SYSTEM
        )
        scan_interval_volume = self.config_entry.options.get(
            "scan_interval_volume", UPDATE_INTERVAL_VOLUME
        )

        options_schema = vol.Schema({
            vol.Optional(
                "scan_interval_system",
                default=scan_interval_system,
            ): vol.All(vol.Coerce(int), vol.Range(min=5)),
            vol.Optional(
                "scan_interval_volume",
                default=scan_interval_volume,
            ): vol.All(vol.Coerce(int), vol.Range(min=5)),
        })

        return self.async_show_form(
            step_id="init", data_schema=options_schema, errors=errors
        )