"""The Twinkly light component."""
from __future__ import annotations

import asyncio
import logging

from aiohttp import ClientError
from twinkly_client.client import TwinklyClient

from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    SUPPORT_BRIGHTNESS,
    LightEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo

from .const import (
    ATTR_HOST,
    CONF_ENTRY_HOST,
    CONF_ENTRY_ID,
    CONF_ENTRY_MODEL,
    CONF_ENTRY_NAME,
    DEV_MODEL,
    DEV_NAME,
    DEV_ATTRIBUTES,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, config_entry: ConfigEntry, async_add_entities
) -> None:
    """Setups an entity from a config entry (UI config flow)."""

    id = config_entry.data[CONF_ENTRY_ID]
    client = hass.data.get(DOMAIN, {}).get(id)

    entity = TwinklyLight(id, config_entry, client)

    async_add_entities([entity], update_before_add=True)


class TwinklyLight(LightEntity):
    """Implementation of the light for the Twinkly service."""

    def __init__(self, id, conf: ConfigEntry, client: TwinklyClient) -> None:
        """Initialize a TwinklyLight entity."""
        self._id = id
        self._conf = conf
        self._client = client

        # Those are saved in the config entry in order to have meaningful values even
        # if the device is currently offline.
        # They are expected to be updated using the device_info.
        self._name = conf.data[CONF_ENTRY_NAME]
        self._model = conf.data[CONF_ENTRY_MODEL]

        # Set default state before any update
        self._is_on = False
        self._brightness = 0
        self._is_available = False
        self._attributes = {
            ATTR_HOST: self._client.host
        }  # TODO Is host interesting as a state attribute?

    @property
    def supported_features(self):
        """Get the features supported by this entity."""
        return SUPPORT_BRIGHTNESS

    @property
    def available(self) -> bool:
        """Get a boolean which indicates if this entity is currently available."""
        return self._is_available

    @property
    def unique_id(self) -> str | None:
        """Id of the device."""
        return self._id

    @property
    def name(self) -> str:
        """Name of the device."""
        return self._name if self._name else "Twinkly light"

    @property
    def model(self) -> str:
        """Name of the device."""
        return self._model

    @property
    def icon(self) -> str:
        """Icon of the device."""
        return "mdi:string-lights"

    @property
    def device_info(self) -> DeviceInfo | None:
        """Get device specific attributes."""
        return {
            "identifiers": {(DOMAIN, self._id)},
            "name": self.name,
            "manufacturer": "LEDWORKS",
            "model": self.model,
        }

    @property
    def is_on(self) -> bool:
        """Return true if light is on."""
        return self._is_on

    @property
    def brightness(self) -> int | None:
        """Return the brightness of the light."""
        return self._brightness

    @property
    def extra_state_attributes(self) -> dict:
        """Return device specific state attributes."""

        attributes = self._attributes

        # Make sure to update any normalized property
        attributes[ATTR_HOST] = self._client.host

        return attributes

    async def async_turn_on(self, **kwargs) -> None:
        """Turn device on."""
        if ATTR_BRIGHTNESS in kwargs:
            brightness = int(kwargs[ATTR_BRIGHTNESS] / 2.55)

            # If brightness is 0, the twinkly will only "disable" the brightness,
            # which means that it will be 100%.
            if brightness == 0:
                await self._client.set_is_on(False)
                return

            await self._client.set_brightness(brightness)

        await self._client.set_is_on(True)
        # self.is_on = True

    async def async_turn_off(self, **kwargs) -> None:
        """Turn device off."""
        await self._client.set_is_on(False)
        # self.is_on = False

    async def async_update(self) -> None:
        """Asynchronously updates the device properties."""
        _LOGGER.debug("Updating '%s'", self._client.host)

        try:
            self._is_on = await self._client.get_is_on()

            self._brightness = (
                int(round((await self._client.get_brightness()) * 2.55))
                if self._is_on
                else 0
            )

            device_info = await self._client.get_device_info()

            if (
                DEV_NAME in device_info
                and DEV_MODEL in device_info
                and (
                    device_info[DEV_NAME] != self._name
                    or device_info[DEV_MODEL] != self._model
                )
            ):
                self._name = device_info[DEV_NAME]
                self._model = device_info[DEV_MODEL]

                # If the name has changed, persist it in conf entry,
                # so we will be able to restore this new name if hass is started while the LED string is offline.
                self.hass.config_entries.async_update_entry(
                    self._conf,
                    data={
                        CONF_ENTRY_HOST: self._client.host,  # this cannot change
                        CONF_ENTRY_ID: self._id,  # this cannot change
                        CONF_ENTRY_NAME: self._name,
                        CONF_ENTRY_MODEL: self._model,
                    },
                )

            for key, value in device_info.items():
                if key in DEV_ATTRIBUTES:
                    try:
                        self._attributes[key] = DEV_ATTRIBUTES[key](value)
                    except (ValueError, TypeError):
                        _LOGGER.debug("Unexpected type of %s", key)

            if not self._is_available:
                _LOGGER.info("Twinkly '%s' is now available", self._client.host)

            # We don't use the echo API to track the availability since we already have to pull
            # the device to get its state.
            self._is_available = True
        except (asyncio.TimeoutError, ClientError):
            # We log this as "info" as it's pretty common that the christmas light are not reachable in july
            if self._is_available:
                _LOGGER.info(
                    "Twinkly '%s' is not reachable (client error)", self._client.host
                )
            self._is_available = False
