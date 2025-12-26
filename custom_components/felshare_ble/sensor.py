from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
from homeassistant.const import PERCENTAGE
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .entity import FelshareEntity

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [
            FelshareAttrSensor(coordinator, "device_time", "Device time"),
            FelshareAttrSensor(coordinator, "oil_level_pct", "Oil level", native_unit_of_measurement=PERCENTAGE),
        ]
    )

class FelshareAttrSensor(FelshareEntity, SensorEntity):
    def __init__(self, coordinator, key, name, native_unit_of_measurement=None):
        super().__init__(coordinator, key, name)
        self._attr_native_unit_of_measurement = native_unit_of_measurement

    @property
    def native_value(self):
        return (self.coordinator.data or {}).get(self._key)
