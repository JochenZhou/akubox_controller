# /config/custom_components/akubox_controller/api.py
import asyncio
import aiohttp
import logging

from .const import (
    API_SYSTEM_INFO,
    API_VOLUME_GET,
    API_VOLUME_SET,
    API_DLNA_STATE,     # 使用修改后的常量名
    API_LED_LOGO_STATE, # 使用修改后的常量名
    API_PORT_SWITCHES,
)

_LOGGER = logging.getLogger(__name__)
REQUEST_TIMEOUT = 10 # seconds
DEVICE_VOLUME_MAX = 63

class AkuBoxApiError(Exception):
    """Base exception for API errors."""
    pass

class AkuBoxApiConnectionError(AkuBoxApiError):
    """Exception for connection errors."""
    pass

class AkuBoxApiAuthError(AkuBoxApiError):
    """Exception for authentication errors (if any in future)."""
    pass


class AkuBoxApiClient:
    """Client to interact with the AkuBox API."""

    def __init__(self, host: str, session: aiohttp.ClientSession):
        """Initialize the API client."""
        self._host = host
        self._session = session
        self._base_url = f"http://{self._host}"
        self._switch_base_url = f"http://{self._host}:{API_PORT_SWITCHES}"

    async def _request_json(self, method: str, endpoint: str, data: dict = None, base_url: str = None) -> dict:
        """Make an API request expecting JSON response and potentially sending JSON data."""
        url_to_use = base_url or self._base_url
        url = f"{url_to_use}{endpoint}"
        _LOGGER.debug("Requesting JSON %s %s (data: %s)", method, url, data)
        try:
            async with asyncio.timeout(REQUEST_TIMEOUT):
                if method == "GET":
                    response = await self._session.get(url)
                elif method == "POST":
                    response = await self._session.post(url, json=data if data is not None else {})
                else:
                    raise ValueError(f"Unsupported HTTP method for JSON request: {method}")

                if response.status == 200:
                    try:
                        json_data = await response.json()
                        _LOGGER.debug("Response from %s: %s", url, json_data)
                        return json_data
                    except aiohttp.ContentTypeError:
                        _LOGGER.error("Invalid JSON response from %s: %s", url, await response.text())
                        raise AkuBoxApiError(f"Invalid JSON response from {url}")
                elif response.status == 401 or response.status == 403:
                    _LOGGER.error("Authentication error for %s: %s", url, response.status)
                    raise AkuBoxApiAuthError(f"Authentication error at {url}")
                else:
                    _LOGGER.error(
                        "API JSON request to %s failed with status %s: %s",
                        url,
                        response.status,
                        await response.text()
                    )
                    raise AkuBoxApiError(
                        f"API JSON request to {url} failed with status {response.status}"
                    )
        except asyncio.TimeoutError:
            _LOGGER.error("Timeout during JSON request to %s", url)
            raise AkuBoxApiConnectionError(f"Timeout connecting to {url}")
        except aiohttp.ClientError as err:
            _LOGGER.error("Client error during JSON request to %s: %s", url, err)
            raise AkuBoxApiConnectionError(f"Error connecting to {url}: {err}")
        except ValueError as err:
             _LOGGER.error(str(err))
             raise AkuBoxApiError(str(err))

    async def _post_plain_text(self, endpoint: str, text_payload: str, base_url: str = None) -> dict:
        """Make a POST API request sending plain text data."""
        url_to_use = base_url or self._base_url
        url = f"{url_to_use}{endpoint}"
        _LOGGER.debug("Requesting POST plain text %s (payload: %s)", url, text_payload)
        headers = {'Content-Type': 'text/plain; charset=utf-8'}
        try:
            async with asyncio.timeout(REQUEST_TIMEOUT):
                response = await self._session.post(url, data=text_payload.encode('utf-8'), headers=headers)

                response_text_content = await response.text()
                if response.status in (200, 204):
                    _LOGGER.debug("Plain text POST to %s successful with status %s. Response text: %s", url, response.status, response_text_content)
                    return {"status": "success", "status_code": response.status, "response_text": response_text_content}
                elif response.status == 401 or response.status == 403:
                    _LOGGER.error("Authentication error for plain text POST %s: %s", url, response.status)
                    raise AkuBoxApiAuthError(f"Authentication error at {url}")
                else:
                    _LOGGER.error(
                        "API plain text POST to %s failed with status %s: %s",
                        url,
                        response.status,
                        response_text_content
                    )
                    raise AkuBoxApiError(
                        f"API plain text POST to {url} failed with status {response.status}"
                    )
        except asyncio.TimeoutError:
            _LOGGER.error("Timeout during plain text POST to %s", url)
            raise AkuBoxApiConnectionError(f"Timeout connecting to {url}")
        except aiohttp.ClientError as err:
            _LOGGER.error("Client error during plain text POST to %s: %s", url, err)
            raise AkuBoxApiConnectionError(f"Error connecting to {url}: {err}")

    async def _get_plain_text(self, endpoint: str, base_url: str = None) -> str:
        """Make a GET API request expecting plain text response."""
        url_to_use = base_url or self._base_url
        url = f"{url_to_use}{endpoint}"
        _LOGGER.debug("Requesting GET plain text %s", url)
        try:
            async with asyncio.timeout(REQUEST_TIMEOUT):
                response = await self._session.get(url)
                response_text = await response.text()

                if response.status == 200:
                    _LOGGER.debug("Plain text GET from %s successful. Response: %s", url, response_text)
                    return response_text.strip().lower()
                elif response.status == 401 or response.status == 403:
                    _LOGGER.error("Authentication error for plain text GET %s: %s", url, response.status)
                    raise AkuBoxApiAuthError(f"Authentication error at {url}")
                else:
                    _LOGGER.error(
                        "API plain text GET from %s failed with status %s: %s",
                        url,
                        response.status,
                        response_text
                    )
                    raise AkuBoxApiError(
                        f"API plain text GET from {url} failed with status {response.status}"
                    )
        except asyncio.TimeoutError:
            _LOGGER.error("Timeout during plain text GET to %s", url)
            raise AkuBoxApiConnectionError(f"Timeout connecting to {url}")
        except aiohttp.ClientError as err:
            _LOGGER.error("Client error during plain text GET to %s: %s", url, err)
            raise AkuBoxApiConnectionError(f"Error connecting to {url}: {err}")


    async def get_system_info(self) -> dict:
        """Get system information."""
        return await self._request_json("GET", API_SYSTEM_INFO)

    async def get_volume(self) -> dict:
        """Get current volume."""
        return await self._request_json("GET", API_VOLUME_GET)

    async def set_volume(self, volume_level: int) -> dict:
        """Set volume level (0-63)."""
        if not 0 <= volume_level <= DEVICE_VOLUME_MAX:
            raise ValueError(f"Volume level must be between 0 and {DEVICE_VOLUME_MAX}")
        return await self._request_json("POST", API_VOLUME_SET, data={"volume": volume_level})

    async def test_connection(self) -> bool:
        """Test if the connection to the AkuBox is working."""
        try:
            await self.get_system_info() # Test main API port
            # Optionally, test switch API port if a simple GET endpoint exists
            # await self._get_plain_text(API_DLNA_STATE, base_url=self._switch_base_url)
            return True
        except AkuBoxApiError:
            return False

    def get_hostname_from_system_info(self, system_info: dict) -> str | None:
        """Extract hostname from system info, returns None if not found."""
        try:
            return system_info.get("system", {}).get("hostname")
        except AttributeError:
            return None

    # --- DLNA Control ---
    async def set_dlna_state(self, state: bool) -> dict:
        """Set DLNA state (on/off) using plain text request body."""
        payload_str = "on" if state else "off"
        _LOGGER.debug(f"Setting DLNA state to plain text: {payload_str}")
        return await self._post_plain_text(API_DLNA_STATE, payload_str, base_url=self._switch_base_url)

    async def get_dlna_state(self) -> bool:
        """Get current DLNA state. Returns True if 'on', False otherwise."""
        state_str = await self._get_plain_text(API_DLNA_STATE, base_url=self._switch_base_url)
        return state_str == "on"

    # --- LED Logo Control ---
    async def set_led_logo_state(self, state: bool) -> dict:
        """Set LED Logo state (on/off) using plain text request body."""
        payload_str = "on" if state else "off"
        _LOGGER.debug(f"Setting LED Logo state to plain text: {payload_str}")
        return await self._post_plain_text(API_LED_LOGO_STATE, payload_str, base_url=self._switch_base_url)

    async def get_led_logo_state(self) -> bool:
        """Get current LED Logo state. Returns True if 'on', False otherwise."""
        state_str = await self._get_plain_text(API_LED_LOGO_STATE, base_url=self._switch_base_url)
        return state_str == "on"