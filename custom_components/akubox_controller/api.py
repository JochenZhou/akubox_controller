# /config/custom_components/akubox_controller/api.py
import asyncio
import aiohttp
import logging
from datetime import datetime, timezone

from .const import (
    API_SYSTEM_INFO,
    API_VOLUME_GET,
    API_VOLUME_SET,
)

_LOGGER = logging.getLogger(__name__)
REQUEST_TIMEOUT = 10 # seconds

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

    async def _request(self, method: str, endpoint: str, data: dict = None) -> dict:
        """Make an API request."""
        url = f"{self._base_url}{endpoint}"
        _LOGGER.debug("Requesting %s %s (data: %s)", method, url, data)
        try:
            async with asyncio.timeout(REQUEST_TIMEOUT):
                if method == "GET":
                    response = await self._session.get(url)
                elif method == "POST":
                    response = await self._session.post(url, json=data)
                else:
                    raise ValueError(f"Unsupported HTTP method: {method}")

                if response.status == 200:
                    try:
                        json_data = await response.json()
                        _LOGGER.debug("Response from %s: %s", url, json_data)
                        return json_data
                    except aiohttp.ContentTypeError:
                        _LOGGER.error("Invalid JSON response from %s: %s", url, await response.text())
                        raise AkuBoxApiError(f"Invalid JSON response from {url}")
                elif response.status == 401 or response.status == 403: # Example for auth errors
                    _LOGGER.error("Authentication error for %s: %s", url, response.status)
                    raise AkuBoxApiAuthError(f"Authentication error at {url}")
                else:
                    _LOGGER.error(
                        "API request to %s failed with status %s: %s",
                        url,
                        response.status,
                        await response.text()
                    )
                    raise AkuBoxApiError(
                        f"API request to {url} failed with status {response.status}"
                    )
        except asyncio.TimeoutError:
            _LOGGER.error("Timeout during request to %s", url)
            raise AkuBoxApiConnectionError(f"Timeout connecting to {url}")
        except aiohttp.ClientError as err:
            _LOGGER.error("Client error during request to %s: %s", url, err)
            raise AkuBoxApiConnectionError(f"Error connecting to {url}: {err}")
        except ValueError as err: # For unsupported method
             _LOGGER.error(str(err))
             raise AkuBoxApiError(str(err))


    async def get_system_info(self) -> dict:
        """Get system information."""
        return await self._request("GET", API_SYSTEM_INFO)

    async def get_volume(self) -> dict:
        """Get current volume."""
        return await self._request("GET", API_VOLUME_GET)

    async def set_volume(self, volume_level: int) -> dict:
        """Set volume level (0-100)."""
        if not 0 <= volume_level <= 100:
            raise ValueError("Volume level must be between 0 and 100")
        return await self._request("POST", API_VOLUME_SET, data={"volume": volume_level})

    async def test_connection(self) -> bool:
        """Test if the connection to the AkuBox is working."""
        try:
            await self.get_system_info() # Try fetching system info as a connection test
            return True
        except AkuBoxApiError:
            return False

    def get_hostname_from_system_info(self, system_info: dict) -> str | None:
        """Extract hostname from system info, returns None if not found."""
        try:
            return system_info.get("system", {}).get("hostname")
        except AttributeError: # if system_info is not a dict or system key is missing
            return None