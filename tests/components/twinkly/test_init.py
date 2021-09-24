"""Tests of the initialization of the twinly integration."""

from homeassistant.helpers.entity_registry import EntityRegistry
from unittest.mock import patch
from uuid import uuid4

from homeassistant.components.twinkly.const import (
    CONF_ENTRY_HOST,
    CONF_ENTRY_ID,
    CONF_ENTRY_MODEL,
    CONF_ENTRY_NAME,
    DOMAIN as TWINKLY_DOMAIN,
)
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from tests.common import MockConfigEntry
from tests.components.twinkly import TEST_HOST, TEST_MODEL, TEST_NAME_ORIGINAL


async def test_setup_entry(hass: HomeAssistant):
    """Validate that setup entry also configure the client."""

    id = str(uuid4())
    config_entry = MockConfigEntry(
        domain=TWINKLY_DOMAIN,
        data={
            CONF_ENTRY_HOST: TEST_HOST,
            CONF_ENTRY_ID: id,
            CONF_ENTRY_NAME: TEST_NAME_ORIGINAL,
            CONF_ENTRY_MODEL: TEST_MODEL,
        },
        entry_id=id,
    )

    with patch(
        "homeassistant.config_entries.ConfigEntries.async_forward_entry_setup",
        return_value=True,
    ):
        await hass.config_entries.async_add(config_entry)
        assert await hass.config_entries.async_setup(config_entry.entry_id)

    assert er.async_get(hass).async_get(id) is not None


async def test_unload_entry(hass: HomeAssistant):
    """Validate that unload entry also clear the client."""

    id = str(uuid4())
    config_entry = MockConfigEntry(
        domain=TWINKLY_DOMAIN,
        data={
            CONF_ENTRY_HOST: TEST_HOST,
            CONF_ENTRY_ID: id,
            CONF_ENTRY_NAME: TEST_NAME_ORIGINAL,
            CONF_ENTRY_MODEL: TEST_MODEL,
        },
        entry_id=id,
    )

    with patch(
        "homeassistant.config_entries.ConfigEntries.async_forward_entry_setup",
        return_value=True,
    ):
        await hass.config_entries.async_add(config_entry)
        assert await hass.config_entries.async_setup(config_entry.entry_id)

        assert await hass.config_entries.async_unload(config_entry.entry_id)

    assert config_entry.state is ConfigEntryState.NOT_LOADED
