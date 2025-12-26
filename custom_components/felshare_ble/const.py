"""Felshare Diffuser (Bluetooth) constants."""
from __future__ import annotations

DOMAIN = "felshare_ble"

# Nordic UART Service (NUS) UUIDs used by the diffuser
NUS_SERVICE_UUID = "6e400001-b5a3-f393-e0a9-e50e24dcca9e"
NUS_TX_CHAR_UUID = "6e400002-b5a3-f393-e0a9-e50e24dcca9e"  # Write
NUS_RX_CHAR_UUID = "6e400003-b5a3-f393-e0a9-e50e24dcca9e"  # Notify

CONF_ADDRESS = "address"
CONF_NAME = "name"

DEFAULT_POLL_INTERVAL_SECONDS = 300  # send status 0x05 every 5 min
CONNECT_TIMEOUT = 30

# Work schedule bitmask: 0=Sun, 1=Mon, ... 6=Sat
DAY_BITS = {"sun": 0, "mon": 1, "tue": 2, "wed": 3, "thu": 4, "fri": 5, "sat": 6}
UI_DAY_ORDER = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]
