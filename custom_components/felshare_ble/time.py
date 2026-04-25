from __future__ import annotations

from datetime import time as dtime

from homeassistant.components.time import TimeEntity
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .entity import FelshareEntity, current_work_fields
from .protocol import parse_hhmm

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([FelshareWorkStartTime(coordinator), FelshareWorkEndTime(coordinator)])

class FelshareWorkStartTime(FelshareEntity, TimeEntity):
    def __init__(self, coordinator):
        super().__init__(coordinator, "work_start", "Work start")

    @property
    def native_value(self):
        s = (self.coordinator.data or {}).get("work_start")
        if not s:
            return None
        hh, mm = parse_hhmm(s)
        return dtime(hour=hh, minute=mm)

    async def async_set_value(self, value: dtime) -> None:
        data = self.coordinator.data or {}
        _sh, _sm, eh, em, enabled, daymask, run_s, stop_s = current_work_fields(data)
        await self.coordinator.async_set_workmode(value.hour, value.minute, eh, em, enabled, daymask, run_s, stop_s)

class FelshareWorkEndTime(FelshareEntity, TimeEntity):
    def __init__(self, coordinator):
        super().__init__(coordinator, "work_end", "Work end")

    @property
    def native_value(self):
        s = (self.coordinator.data or {}).get("work_end")
        if not s:
            return None
        hh, mm = parse_hhmm(s)
        return dtime(hour=hh, minute=mm)

    async def async_set_value(self, value: dtime) -> None:
        data = self.coordinator.data or {}
        sh, sm, _eh, _em, enabled, daymask, run_s, stop_s = current_work_fields(data)
        await self.coordinator.async_set_workmode(sh, sm, value.hour, value.minute, enabled, daymask, run_s, stop_s)
