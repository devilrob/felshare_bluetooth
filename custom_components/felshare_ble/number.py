from __future__ import annotations

from homeassistant.components.number import NumberEntity
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.const import UnitOfTime

from .const import DOMAIN
from .entity import FelshareEntity
from .protocol import parse_hhmm

def _current_work_fields(data: dict):
    sh, sm = parse_hhmm(data.get("work_start", "09:00"))
    eh, em = parse_hhmm(data.get("work_end", "21:00"))
    enabled = bool(data.get("work_enabled", True))
    daymask = int(data.get("work_days_mask", 0x7F))
    run_s = int(data.get("work_run_s", 30))
    stop_s = int(data.get("work_stop_s", 280))
    return sh, sm, eh, em, enabled, daymask, run_s, stop_s

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [
            FelshareOilCapacityNumber(coordinator),
            FelshareOilRemainNumber(coordinator),
            FelshareOilConsumptionNumber(coordinator),
            FelshareWorkRunNumber(coordinator),
            FelshareWorkStopNumber(coordinator),
        ]
    )

class FelshareOilCapacityNumber(FelshareEntity, NumberEntity):
    _attr_native_min_value = 0
    _attr_native_max_value = 65535
    _attr_native_step = 1
    _attr_native_unit_of_measurement = "mL"

    def __init__(self, coordinator):
        super().__init__(coordinator, "oil_capacity_ml", "Oil capacity")

    @property
    def native_value(self):
        return (self.coordinator.data or {}).get("oil_capacity_ml")

    async def async_set_native_value(self, value: float):
        await self.coordinator.async_set_oil_capacity(int(value))

class FelshareOilRemainNumber(FelshareEntity, NumberEntity):
    _attr_native_min_value = 0
    _attr_native_max_value = 65535
    _attr_native_step = 1
    _attr_native_unit_of_measurement = "mL"

    def __init__(self, coordinator):
        super().__init__(coordinator, "oil_remain_ml", "Oil remaining")

    @property
    def native_value(self):
        return (self.coordinator.data or {}).get("oil_remain_ml")

    async def async_set_native_value(self, value: float):
        await self.coordinator.async_set_oil_remain(int(value))

class FelshareOilConsumptionNumber(FelshareEntity, NumberEntity):
    _attr_native_min_value = 0
    _attr_native_max_value = 6553.5
    _attr_native_step = 0.1
    _attr_native_unit_of_measurement = "mL/h"

    def __init__(self, coordinator):
        super().__init__(coordinator, "oil_consumption_ml_h", "Oil consumption")

    @property
    def native_value(self):
        raw = (self.coordinator.data or {}).get("oil_consumption_raw")
        if raw is None:
            return None
        return round(float(raw) / 10.0, 1)

    async def async_set_native_value(self, value: float):
        await self.coordinator.async_set_oil_consumption(float(value))

class FelshareWorkRunNumber(FelshareEntity, NumberEntity):
    _attr_native_min_value = 0
    _attr_native_max_value = 2000
    _attr_native_step = 1
    _attr_native_unit_of_measurement = UnitOfTime.SECONDS

    def __init__(self, coordinator):
        super().__init__(coordinator, "work_run_s", "Work run")

    @property
    def native_value(self):
        return (self.coordinator.data or {}).get("work_run_s")

    async def async_set_native_value(self, value: float):
        data = self.coordinator.data or {}
        sh, sm, eh, em, enabled, daymask, _run_s, stop_s = _current_work_fields(data)
        await self.coordinator.async_set_workmode(sh, sm, eh, em, enabled, daymask, int(value), int(stop_s))

class FelshareWorkStopNumber(FelshareEntity, NumberEntity):
    _attr_native_min_value = 0
    _attr_native_max_value = 2000
    _attr_native_step = 1
    _attr_native_unit_of_measurement = UnitOfTime.SECONDS

    def __init__(self, coordinator):
        super().__init__(coordinator, "work_stop_s", "Work stop")

    @property
    def native_value(self):
        return (self.coordinator.data or {}).get("work_stop_s")

    async def async_set_native_value(self, value: float):
        data = self.coordinator.data or {}
        sh, sm, eh, em, enabled, daymask, run_s, _stop_s = _current_work_fields(data)
        await self.coordinator.async_set_workmode(sh, sm, eh, em, enabled, daymask, int(run_s), int(value))
