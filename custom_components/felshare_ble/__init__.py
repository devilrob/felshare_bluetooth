"""Felshare Diffuser (Bluetooth) integration."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.const import Platform
from homeassistant.components import bluetooth
from homeassistant.exceptions import ConfigEntryNotReady

from .const import DOMAIN, CONF_ADDRESS, CONF_NAME
from .coordinator import FelshareCoordinator

PLATFORMS: list[Platform] = [
    Platform.SENSOR,
    Platform.SWITCH,
    Platform.NUMBER,
    Platform.TEXT,
    Platform.TIME,
    Platform.BUTTON,
]

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Felshare BLE from a config entry.

    IMPORTANT: BLE connects can take longer than Home Assistant's config-entry setup
    timeout (especially when waiting for an advertisement). We therefore start the
    coordinator in the background and let entities become available once connected.
    """
    # If Home Assistant has no connectable Bluetooth scanners/adapters, we cannot use BLE.
    if bluetooth.async_scanner_count(hass, connectable=True) == 0:
        raise ConfigEntryNotReady(
            "No connectable Bluetooth scanners are available. "
            "Make sure a USB Bluetooth adapter is present or an ESPHome Bluetooth Proxy is configured."
        )

    address = entry.data[CONF_ADDRESS]
    name = entry.data.get(CONF_NAME, address)

    coordinator = FelshareCoordinator(hass, address, name)
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Start BLE connection / initial reads in the background (non-blocking).
    coordinator.start_background()

    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    coordinator: FelshareCoordinator = hass.data[DOMAIN].pop(entry.entry_id)
    ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    await coordinator.async_stop()
    return ok
