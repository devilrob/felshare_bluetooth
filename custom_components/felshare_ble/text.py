from __future__ import annotations

from homeassistant.components.text import TextEntity
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .entity import FelshareEntity

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([FelshareOilNameText(coordinator)])

class FelshareOilNameText(FelshareEntity, TextEntity):
    _attr_native_min = 0
    _attr_native_max = 64
    _attr_pattern = r"^[\x20-\x7E]*$"  # printable ASCII only

    def __init__(self, coordinator):
        super().__init__(coordinator, "oil_name", "Oil name")

    @property
    def native_value(self):
        return (self.coordinator.data or {}).get("oil_name") or ""

    async def async_set_value(self, value: str) -> None:
        await self.coordinator.async_set_oil_name(value)
