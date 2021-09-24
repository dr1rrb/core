"""Tests for the integration of a twinly device."""
from __future__ import annotations

from unittest.mock import patch

from homeassistant.components.twinkly.const import (
    CONF_ENTRY_HOST,
    CONF_ENTRY_ID,
    CONF_ENTRY_MODEL,
    CONF_ENTRY_NAME,
    DOMAIN as TWINKLY_DOMAIN,
)
from homeassistant.components.twinkly.light import TwinklyLight
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr, entity_registry as er
from homeassistant.helpers.device_registry import DeviceEntry
from homeassistant.helpers.entity_registry import RegistryEntry

from tests.common import MockConfigEntry
from tests.components.twinkly import (
    TEST_HOST,
    TEST_ID,
    TEST_MODEL,
    TEST_NAME_ORIGINAL,
    ClientMock,
)


async def test_initial_state(hass: HomeAssistant):
    """Validate that entity and device states are updated on startup."""
    entity_entry, device_entry, _ = await _create_entries(hass)

    state = hass.states.get(entity_entry.entity_id)

    # Basic state properties
    assert state.name == entity_entry.unique_id
    assert state.state == "on"
    assert state.attributes["host"] == TEST_HOST
    assert state.attributes["brightness"] == 26
    assert state.attributes["friendly_name"] == entity_entry.unique_id
    assert state.attributes["icon"] == "mdi:string-lights"

    # Validates that custom properties of the API device_info are propagated through attributes
    assert state.attributes["uuid"] == entity_entry.unique_id

    assert entity_entry.original_name == entity_entry.unique_id
    assert entity_entry.original_icon == "mdi:string-lights"

    assert device_entry.name == entity_entry.unique_id
    assert device_entry.model == TEST_MODEL
    assert device_entry.manufacturer == "LEDWORKS"


async def test_initial_state_offline(hass: HomeAssistant):
    """Validate that entity and device are restored from config is offline on startup."""
    client = ClientMock()
    client.is_offline = True
    entity_entry, device_entry, _ = await _create_entries(hass, client)

    state = hass.states.get(entity_entry.entity_id)

    assert state.name == TEST_NAME_ORIGINAL
    assert state.state == "unavailable"
    assert state.attributes["friendly_name"] == TEST_NAME_ORIGINAL
    assert state.attributes["icon"] == "mdi:string-lights"

    assert entity_entry.original_name == TEST_NAME_ORIGINAL
    assert entity_entry.original_icon == "mdi:string-lights"

    assert device_entry.name == TEST_NAME_ORIGINAL
    assert device_entry.model == TEST_MODEL
    assert device_entry.manufacturer == "LEDWORKS"


async def test_turn_on(hass: HomeAssistant):
    """Test support of the light.turn_on service."""
    client = ClientMock()
    client.is_on = False
    client.brightness = 20
    entity_entry, _, _ = await _create_entries(hass, client)

    assert hass.states.get(entity_entry.entity_id).state == "off"

    await hass.services.async_call(
        "light", "turn_on", service_data={"entity_id": entity_entry.entity_id}
    )
    await hass.async_block_till_done()

    state = hass.states.get(entity_entry.entity_id)

    assert state.state == "on"
    assert state.attributes["brightness"] == 51


async def test_turn_on_with_brightness(hass: HomeAssistant):
    """Test support of the light.turn_on service with a brightness parameter."""
    client = ClientMock()
    client.is_on = False
    client.brightness = 20
    entity_entry, _, _ = await _create_entries(hass, client)

    assert hass.states.get(entity_entry.entity_id).state == "off"

    await hass.services.async_call(
        "light",
        "turn_on",
        service_data={"entity_id": entity_entry.entity_id, "brightness": 255},
    )
    await hass.async_block_till_done()

    state = hass.states.get(entity_entry.entity_id)

    assert state.state == "on"
    assert state.attributes["brightness"] == 255


async def test_turn_off(hass: HomeAssistant):
    """Test support of the light.turn_off service."""
    entity_entry, _, _ = await _create_entries(hass)

    assert hass.states.get(entity_entry.entity_id).state == "on"

    await hass.services.async_call(
        "light", "turn_off", service_data={"entity_id": entity_entry.entity_id}
    )
    await hass.async_block_till_done()

    state = hass.states.get(entity_entry.entity_id)

    assert state.state == "off"
    assert state.attributes["brightness"] == 0


async def test_update_name(hass: HomeAssistant):
    """
    Validate device's name update behavior.

    Validate that if device name is changed from the Twinkly app,
    then the name of the entity is updated and it's also persisted,
    so it can be restored when starting HA while Twinkly is offline.
    """
    entity_entry, _, client = await _create_entries(hass)

    client.change_name("new_device_name")
    await hass.services.async_call(
        "light", "turn_off", service_data={"entity_id": entity_entry.entity_id}
    )  # We call turn_off which will automatically cause an async_update
    await hass.async_block_till_done()

    assert hass.config_entries.async_get_entry(entity_entry.entity_id) is not None
    assert (
        hass.config_entries.async_get_entry(entity_entry.entity_id).data[
            CONF_ENTRY_NAME
        ]
        == "new_device_name"
    )
    assert (
        hass.states.get(entity_entry.entity_id).attributes["friendly_name"]
        == "new_device_name"
    )


async def test_unload(hass: HomeAssistant):
    """Validate that entities can be unloaded from the UI."""

    _, _, client = await _create_entries(hass)
    entry_id = client.id

    assert await hass.config_entries.async_unload(entry_id)


async def _create_entries(
    hass: HomeAssistant, client=None
) -> tuple[RegistryEntry, DeviceEntry, ClientMock]:
    client = ClientMock() if client is None else client

    def get_client_mock(client, _):
        return client

    with patch("twinkly_client.TwinklyClient", side_effect=get_client_mock):
        config_entry = MockConfigEntry(
            domain=TWINKLY_DOMAIN,
            data={
                CONF_ENTRY_HOST: client,
                CONF_ENTRY_ID: client.id,
                CONF_ENTRY_NAME: TEST_NAME_ORIGINAL,
                CONF_ENTRY_MODEL: TEST_MODEL,
            },
            entry_id=client.id,
        )
        config_entry.add_to_hass(hass)
        assert await hass.config_entries.async_setup(client.id)
        await hass.async_block_till_done()

    device_registry = dr.async_get(hass)
    entity_registry = er.async_get(hass)

    entity_id = entity_registry.async_get_entity_id("light", TWINKLY_DOMAIN, client.id)
    entity_entry = entity_registry.async_get(entity_id)
    device_entry = device_registry.async_get_device({(TWINKLY_DOMAIN, client.id)})

    assert entity_entry is not None
    assert device_entry is not None

    return entity_entry, device_entry, client
