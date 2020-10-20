"""The Twinkly API client"""

import logging
from typing import Any
from aiohttp import ClientSession, ClientResponseError
from .const import *

_LOGGER = logging.getLogger(__name__)


class TwinklyClient:
    """Client of the Twinkly API."""

    def __init__(self, host: str, session: ClientSession = None):
        """Initialize a TwinklyClient."""
        self._host = host
        self._base_url = "http://" + host + "/xled/v1/"
        self._token = None
        self._session = (
            session
            if session
            else ClientSession(raise_for_status=True, timeout=EP_TIMEOUT)
        )

        self._is_on = False
        self._brightness = 0
        self._is_available = False
        self._attributes = {ATTR_HOST: self._host}

    @property
    def host(self) -> str:
        """Gets the host used by this client"""
        return self._host

    async def get_device_info(self) -> Any:
        """Retreives the device informations."""
        return await self.__send_request(EP_DEVICE_INFO)

    async def get_is_on(self) -> bool:
        """Gets a boolean which indicates the current state of the device."""
        return (await self.__send_request(EP_MODE))["mode"] != "off"

    async def set_is_on(self, is_on: bool) -> None:
        """Turns the device on / off"""
        await self.__send_request(EP_MODE, {"mode": "movie" if is_on else "off"})

    async def get_brigthness(self) -> int:
        """Gets the current brightness of the device."""
        brightness = await self.__send_request(EP_BRIGHTNESS)
        return int(brightness["value"]) if brightness["mode"] == "enabled" else 100

    async def set_brightness(self, brightness: int) -> None:
        """Sets the brightness of the device."""
        await self.__send_request(EP_BRIGHTNESS, {"value": brightness, "type": "A"})

    async def __send_request(
        self, endpoint: str, data: Any = None, retry: int = 1
    ) -> Any:
        """Send an authenticated request with auto retry if not yet auth."""
        if self._token is None:
            await self.__auth()

        try:
            response = await self._session.request(
                method="GET" if data is None else "POST",
                url=self._base_url + endpoint,
                json=data,
                headers={"X-Auth-Token": self._token},
                raise_for_status=True,
                timeout=EP_TIMEOUT,
            )
            result = await response.json() if data is None else None
            return result
        except ClientResponseError as err:
            if err.code == 401 and retry > 0:
                self._token = None
                return await self.__send_request(endpoint, data, retry - 1)
            raise

    async def __auth(self) -> None:
        """Authenticates to the device."""
        _LOGGER.info("Authenticating to '%s'", self._host)

        # Login to the device using a hard-coded challenge
        login_response = await self._session.post(
            url=self._base_url + EP_LOGIN,
            json={"challenge": "Uswkc0TgJDmwl5jrsyaYSwY8fqeLJ1ihBLAwYcuADEo="},
            raise_for_status=True,
            timeout=EP_TIMEOUT,
        )
        login_result = await login_response.json()
        _LOGGER.debug("Sucessfully logged-in to '%s'", self._host)

        # Get the token, but do not store it until it gets verified
        token = login_result["authentication_token"]

        # Verify the token is valid
        await self._session.post(
            url=self._base_url + EP_VERIFY,
            headers={"X-Auth-Token": token},
            raise_for_status=True,
            timeout=EP_TIMEOUT,
        )
        _LOGGER.debug("Sucessfully verified token to '%s'", self._host)

        self._token = token
