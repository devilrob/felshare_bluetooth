"""Shared entity base for Felshare BLE."""
from __future__ import annotations

from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .coordinator import FelshareCoordinator
from .const import DOMAIN
from .protocol import parse_hhmm


def current_work_fields(data: dict) -> tuple[int, int, int, int, bool, int, int, int]:
    """Extract current work-schedule fields from coordinator data with safe defaults."""
    sh, sm = parse_hhmm(data.get("work_start", "09:00"))
    eh, em = parse_hhmm(data.get("work_end", "21:00"))
    enabled = bool(data.get("work_enabled", True))
    daymask = int(data.get("work_days_mask", 0x7F))
    run_s = int(data.get("work_run_s", 30))
    stop_s = int(data.get("work_stop_s", 280))
    return sh, sm, eh, em, enabled, daymask, run_s, stop_s


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
