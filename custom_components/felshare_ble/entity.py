"""Shared entity base for Felshare BLE."""
from __future__ import annotations

from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .coordinator import FelshareCoordinator
from .const import DOMAIN

class FelshareEntity(CoordinatorEntity[FelshareCoordinator]):
    _attr_has_entity_name = True

    def __init__(self, coordinator: FelshareCoordinator, key: str, name: str) -> None:
        super().__init__(coordinator)
        self._key = key
        self._attr_name = name
        self._attr_unique_id = f"{coordinator.address}-{key}"

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self.coordinator.address)},
            "name": self.coordinator.name,
            "manufacturer": "Felshare",
            "model": "Diffuser (BLE)",
        }
