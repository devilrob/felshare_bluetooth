from __future__ import annotations

from homeassistant.components.switch import SwitchEntity
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN, DAY_BITS, UI_DAY_ORDER
from .entity import FelshareEntity
from .protocol import parse_hhmm

def _current_work_fields(data: dict) -> tuple[int,int,int,int,bool,int,int,int]:
    sh, sm = parse_hhmm(data.get("work_start", "09:00"))
    eh, em = parse_hhmm(data.get("work_end", "21:00"))
    enabled = bool(data.get("work_enabled", True))
    daymask = int(data.get("work_days_mask", 0x7F))
    run_s = int(data.get("work_run_s", 30))
    stop_s = int(data.get("work_stop_s", 280))
    return sh, sm, eh, em, enabled, daymask, run_s, stop_s

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    coordinator = hass.data[DOMAIN][entry.entry_id]

    entities = [
        FelsharePowerSwitch(coordinator, "power_on", "Power"),
        FelshareFanSwitch(coordinator, "fan_on", "Fan"),
        FelshareWorkEnabledSwitch(coordinator, "work_enabled", "Work schedule enabled"),
    ]
    for d in UI_DAY_ORDER:
        entities.append(FelshareWorkDaySwitch(coordinator, f"work_day_{d}", f"Work day {d.title()}", d))
    async_add_entities(entities)

class FelsharePowerSwitch(FelshareEntity, SwitchEntity):
    @property
    def is_on(self):
        return bool((self.coordinator.data or {}).get("power_on", False))

    async def async_turn_on(self, **kwargs):
        await self.coordinator.async_set_power(True)

    async def async_turn_off(self, **kwargs):
        await self.coordinator.async_set_power(False)

class FelshareFanSwitch(FelshareEntity, SwitchEntity):
    @property
    def is_on(self):
        return bool((self.coordinator.data or {}).get("fan_on", False))

    async def async_turn_on(self, **kwargs):
        await self.coordinator.async_set_fan(True)

    async def async_turn_off(self, **kwargs):
        await self.coordinator.async_set_fan(False)

class FelshareWorkEnabledSwitch(FelshareEntity, SwitchEntity):
    @property
    def is_on(self):
        return bool((self.coordinator.data or {}).get("work_enabled", False))

    async def async_turn_on(self, **kwargs):
        data = self.coordinator.data or {}
        sh, sm, eh, em, _enabled, daymask, run_s, stop_s = _current_work_fields(data)
        await self.coordinator.async_set_workmode(sh, sm, eh, em, True, daymask, run_s, stop_s)

    async def async_turn_off(self, **kwargs):
        data = self.coordinator.data or {}
        sh, sm, eh, em, _enabled, daymask, run_s, stop_s = _current_work_fields(data)
        await self.coordinator.async_set_workmode(sh, sm, eh, em, False, daymask, run_s, stop_s)

class FelshareWorkDaySwitch(FelshareEntity, SwitchEntity):
    def __init__(self, coordinator, key, name, day_key: str):
        super().__init__(coordinator, key, name)
        self._day_key = day_key

    @property
    def is_on(self):
        mask = int((self.coordinator.data or {}).get("work_days_mask", 0))
        bit = DAY_BITS[self._day_key]
        return bool(mask & (1 << bit))

    async def _set_day(self, on: bool):
        data = self.coordinator.data or {}
        sh, sm, eh, em, enabled, daymask, run_s, stop_s = _current_work_fields(data)
        bit = DAY_BITS[self._day_key]
        if on:
            daymask |= (1 << bit)
        else:
            daymask &= ~(1 << bit)
        await self.coordinator.async_set_workmode(sh, sm, eh, em, enabled, daymask, run_s, stop_s)

    async def async_turn_on(self, **kwargs):
        await self._set_day(True)

    async def async_turn_off(self, **kwargs):
        await self._set_day(False)
