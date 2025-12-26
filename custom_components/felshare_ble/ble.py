"""BLE connection layer for Felshare diffuser."""
from __future__ import annotations

import asyncio
import logging
from typing import Callable, Any

from bleak import BleakError
from bleak.backends.device import BLEDevice

from homeassistant.core import HomeAssistant
from homeassistant.components import bluetooth

from bleak_retry_connector import (
    BleakClientWithServiceCache,
    BleakNotFoundError,
    establish_connection,
)

from .const import NUS_RX_CHAR_UUID, NUS_TX_CHAR_UUID, CONNECT_TIMEOUT
from .protocol import decode_frame

_LOGGER = logging.getLogger(__name__)

class FelshareBleConnection:
    def __init__(self, hass: HomeAssistant, address: str, name: str, on_state: Callable[[dict[str, Any]], None]) -> None:
        self.hass = hass
        self.address = address
        self.name = name
        self._on_state = on_state

        self._client: BleakClientWithServiceCache | None = None
        self._cached_services = None
        self._lock = asyncio.Lock()
        self._connected_event = asyncio.Event()
        self._disconnecting = False

    @property
    def is_connected(self) -> bool:
        return self._client is not None and getattr(self._client, "is_connected", False)

    async def _get_ble_device(self) -> BLEDevice | None:
        """Return the best known BLEDevice for the configured address.

        Prefer the latest BluetoothServiceInfo (best RSSI) to avoid stale cache.
        """
        try:
            service_info = bluetooth.async_last_service_info(self.hass, self.address, connectable=True)
            if service_info is not None:
                dev = getattr(service_info, "device", None) or getattr(service_info, "ble_device", None)
                if dev is not None:
                    return dev
        except Exception:
            pass
        return bluetooth.async_ble_device_from_address(self.hass, self.address, connectable=True)

    def _disconnected(self, _client) -> None:
        _LOGGER.debug("%s disconnected", self.address)
        self._connected_event.clear()

    async def connect(self) -> None:
        async with self._lock:
            if self.is_connected:
                return

            # Ensure there is at least one connectable Bluetooth scanner/adapter.
            if bluetooth.async_scanner_count(self.hass, connectable=True) == 0:
                raise BleakError(
                    "No connectable Bluetooth scanners are available. "
                    "Check Settings → Devices & Services → Bluetooth (USB adapter or Bluetooth Proxy)."
                )

            device = await self._get_ble_device()
            if device is None:
                raise BleakNotFoundError(f"{self.address} not found / not reachable")

            _LOGGER.debug("Connecting to %s (%s)", self.name, self.address)
            self._disconnecting = False

            client = await establish_connection(
                BleakClientWithServiceCache,
                device,
                self.name,
                disconnected_callback=self._disconnected,
                cached_services=self._cached_services,
                ble_device_callback=self._get_ble_device,
                timeout=CONNECT_TIMEOUT,
            )
            self._client = client
            try:
                if client.services is not None:
                    self._cached_services = client.services
            except Exception:
                pass

            await client.start_notify(NUS_RX_CHAR_UUID, self._handle_notify)
            self._connected_event.set()

    async def disconnect(self) -> None:
        async with self._lock:
            self._disconnecting = True
            self._connected_event.clear()
            if self._client is None:
                return
            client = self._client
            self._client = None
            try:
                await client.stop_notify(NUS_RX_CHAR_UUID)
            except Exception:
                pass
            try:
                await client.disconnect()
            except Exception:
                pass

    async def ensure_connected(self) -> None:
        if self.is_connected:
            return
        await self.connect()

    def _handle_notify(self, _sender: int, data: bytearray) -> None:
        frame = bytes(data)
        if not frame:
            return
        st = decode_frame(frame)
        if st:
            self._on_state(st)

    async def write(self, payload: bytes, response: bool = False) -> None:
        await self.ensure_connected()
        assert self._client is not None
        async with self._lock:
            await self._client.write_gatt_char(NUS_TX_CHAR_UUID, payload, response=response)
