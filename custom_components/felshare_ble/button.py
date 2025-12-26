from __future__ import annotations

import asyncio

from homeassistant.components.button import ButtonEntity
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .entity import FelshareEntity

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [
            FelshareButton(coordinator, "request_status", "Refresh status (05)"),
            FelshareButton(coordinator, "request_bulk", "Read work schedule (0C)"),
            FelsharePowerOnSafeButton(coordinator),
        ]
    )

class FelshareButton(FelshareEntity, ButtonEntity):
    def __init__(self, coordinator, key, name):
        super().__init__(coordinator, key, name)

    async def async_press(self) -> None:
        if self._key == "request_status":
            await self.coordinator.async_request_status()
        elif self._key == "request_bulk":
            await self.coordinator.async_request_bulk()

class FelsharePowerOnSafeButton(FelshareEntity, ButtonEntity):
    def __init__(self, coordinator):
        super().__init__(coordinator, "power_on_safe", "Power ON (safe)")

    async def async_press(self) -> None:
        await self.coordinator.async_set_power(False)
        await asyncio.sleep(0.25)
        await self.coordinator.async_set_power(True)
