"""Coordinator for Felshare BLE diffuser."""
from __future__ import annotations

import asyncio
import logging
from datetime import timedelta
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.exceptions import ConfigEntryNotReady

from .const import DEFAULT_POLL_INTERVAL_SECONDS
from .ble import FelshareBleConnection
from .protocol import (
    bytes_status_request,
    bytes_bulk_request,
    bytes_power,
    bytes_fan,
    bytes_workmode,
    bytes_oil_name,
    bytes_oil_capacity_ml,
    bytes_oil_remain_ml,
    bytes_oil_consumption,
)

_LOGGER = logging.getLogger(__name__)

class FelshareCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    def __init__(self, hass: HomeAssistant, address: str, name: str) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=f"Felshare BLE {name}",
            update_interval=None,  # push-based
        )
        self.address = address
        self.name = name
        self.data: dict[str, Any] = {}

        self._conn = FelshareBleConnection(hass, address, name, self._on_state)
        self._unsub_poll = None
        self._start_task: asyncio.Task | None = None
    def start_background(self) -> None:
        """Start coordinator tasks without blocking config-entry setup."""
        if getattr(self, "_start_task", None) is None:
            self._start_task = self.hass.async_create_task(self.async_start())

    async def async_start(self) -> None:
        """Start background tasks and attempt initial sync."""
        # keepalive poll (optional)
        if self._unsub_poll is None:
            self._unsub_poll = async_track_time_interval(
                self.hass,
                self._poll_status,
                timedelta(seconds=DEFAULT_POLL_INTERVAL_SECONDS),
            )

        # Kick off initial reads (status + schedule). These will auto-connect as needed.
        try:
            await self.async_request_status()
            await asyncio.sleep(0.2)
            await self.async_request_bulk()
        except asyncio.CancelledError:
            # Home Assistant is shutting down or unloading; honor cancellation.
            raise
        except Exception:
            _LOGGER.debug("Initial BLE requests failed (will retry on poll / user actions)", exc_info=True)


    async def async_stop(self) -> None:
        if self._start_task is not None and not self._start_task.done():
            self._start_task.cancel()
            try:
                await self._start_task
            except asyncio.CancelledError:
                pass
        self._start_task = None

        if self._unsub_poll is not None:
            self._unsub_poll()
            self._unsub_poll = None
        await self._conn.disconnect()

    def _on_state(self, partial: dict[str, Any]) -> None:
        self.data = {**(self.data or {}), **partial}
        self.async_set_updated_data(self.data)

    async def _poll_status(self, _now) -> None:
        try:
            await self._conn.write(bytes_status_request())
        except Exception:
            _LOGGER.debug("Poll status failed", exc_info=True)

    # ----- command helpers -----
    async def async_request_status(self) -> None:
        await self._conn.write(bytes_status_request())

    async def async_request_bulk(self) -> None:
        await self._conn.write(bytes_bulk_request())

    async def async_set_power(self, on: bool) -> None:
        await self._conn.write(bytes_power(on))

    async def async_set_fan(self, on: bool) -> None:
        await self._conn.write(bytes_fan(on))

    async def async_set_workmode(self, sh: int, sm: int, eh: int, em: int, enabled: bool, daymask: int, run_s: int, stop_s: int) -> None:
        await self._conn.write(bytes_workmode(sh, sm, eh, em, enabled, daymask, run_s, stop_s))

    async def async_set_oil_name(self, name: str) -> None:
        await self._conn.write(bytes_oil_name(name, null_term=True))

    async def async_set_oil_capacity(self, cap_ml: int) -> None:
        await self._conn.write(bytes_oil_capacity_ml(cap_ml))

    async def async_set_oil_remain(self, rem_ml: int) -> None:
        await self._conn.write(bytes_oil_remain_ml(rem_ml))

    async def async_set_oil_consumption(self, ml_per_hour: float) -> None:
        raw = int(round(float(ml_per_hour) * 10.0))
        await self._conn.write(bytes_oil_consumption(raw))