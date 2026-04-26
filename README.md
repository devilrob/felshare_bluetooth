# Felshare Diffuser (BLE) — Home Assistant Integration

Control a **Felshare waterless diffuser** from Home Assistant via **Bluetooth Low Energy (BLE)**.
The integration uses the device's Nordic UART Service (NUS) to send commands and receive state updates in real time — no cloud, no polling every few seconds.

> **Prerequisite:** Home Assistant must have a working **Bluetooth adapter** (USB dongle) or an **ESPHome Bluetooth Proxy** positioned close to the diffuser.

---

## Features

| Entity | Platform | Description |
|--------|----------|-------------|
| Power | `switch` | Turn the diffuser on/off |
| Fan | `switch` | Toggle the fan independently |
| Work schedule enabled | `switch` | Enable/disable the timed work schedule |
| Work day Mon–Sun | `switch` × 7 | Enable individual days in the schedule |
| Work start | `time` | Schedule start time (HH:MM) |
| Work end | `time` | Schedule end time (HH:MM) |
| Work run | `number` | Diffuser-on duration per cycle (seconds, 0–2000) |
| Work stop | `number` | Diffuser-off duration per cycle (seconds, 0–2000) |
| Oil capacity | `number` | Total tank capacity in mL (0–65535) |
| Oil remaining | `number` | Current oil level in mL (0–65535) |
| Oil consumption | `number` | Consumption rate in mL/h (0–6553.5, step 0.1) |
| Oil name | `text` | Label for the current oil (printable ASCII, max 64 chars) |
| Oil level | `sensor` | Remaining oil as a percentage (0–100%) |
| Device time | `sensor` | Timestamp reported by the device |
| Refresh status | `button` | Request a fresh status frame (0x05) from the device |
| Read work schedule | `button` | Request the full work-schedule frame (0x0C) |
| Power ON (safe) | `button` | Power OFF → 250 ms pause → Power ON (clean restart) |

---

## Installation

### Via HACS (recommended)

1. **HACS** → **Integrations** → ⋮ → **Custom repositories**
2. Enter `https://github.com/devilrob/felshare_bluetooth` → Category: **Integration**
3. Install **Felshare Diffuser (Bluetooth)** and restart Home Assistant
4. **Settings → Devices & Services → Add Integration → Felshare Diffuser (Bluetooth)**

### Manual

1. Copy `custom_components/felshare_ble/` into your HA `config/custom_components/` folder
2. Restart Home Assistant
3. **Settings → Devices & Services → Add Integration → Felshare Diffuser (Bluetooth)**

---

## Setup

When you add the integration you can:

- **Auto-discover**: If the diffuser is nearby and advertising, it will appear in the list automatically — just select it and confirm.
- **Manual entry**: Paste the device's BLE MAC address (format `AA:BB:CC:DD:EE:FF`) and give it a name.

The integration connects in the background after setup — entities become available once the first successful BLE handshake completes (usually within a few seconds).

---

## How it works

Communication uses the [Nordic UART Service (NUS)](https://developer.nordicsemi.com/nRF_Connect_SDK/doc/latest/nrf/libraries/bluetooth_services/services/nus.html):

- **TX characteristic** (`6e400002-…`) — commands sent *to* the device
- **RX characteristic** (`6e400003-…`) — notifications received *from* the device

The integration operates in **push mode**: state updates arrive as BLE notifications and are merged into the coordinator immediately. A lightweight keepalive poll (status request `0x05`) runs every 5 minutes to detect connection drops and refresh the device clock.

All user commands include **automatic retry**: if a write fails due to a transient BLE error, the integration disconnects, waits 300 ms, and tries once more before surfacing the error.

---

## Bluetooth requirements & troubleshooting

### Common errors

| Error | Cause | Fix |
|-------|-------|-----|
| `No connectable Bluetooth scanners` | No adapter/proxy visible to HA | Add a USB Bluetooth dongle or an ESPHome Bluetooth Proxy |
| `TimeoutError` / `Failed to connect` | Device out of range or busy | Move the adapter closer; close the Felshare phone app |
| `BleakNotFoundError: not found / not reachable` | Device not advertising | Power-cycle the diffuser; wait ~10 s for it to appear |
| Entities stuck on "unavailable" | BLE connection dropped | HA will reconnect automatically on the next poll or command |

### Step-by-step checklist

1. Place the diffuser **within 2–3 m** of the Bluetooth adapter or proxy.
2. **Close the Felshare phone app** — most BLE devices only allow one active connection at a time.
3. Power-cycle the diffuser (switch off → wait 5 s → switch on).
4. In HA: **Settings → Devices & Services → Bluetooth** — verify the adapter is listed and the diffuser MAC address appears in the discovered devices list.
5. If using an ESPHome Bluetooth Proxy, make sure it is online and its RSSI for the diffuser is above −80 dBm.

### Multiple BLE integrations

Each Bluetooth adapter has a limited number of simultaneous connections. If you have many BLE devices (locks, sensors, etc.) and experience frequent disconnects, try:
- Dedicating a second USB Bluetooth dongle to this diffuser
- Using an ESPHome Bluetooth Proxy (extends range and adds connection capacity)

---

## Known limitations

- **One diffuser per config entry.** Each physical device requires its own integration entry.
- **Auto-discovery may trigger for other Nordic UART devices.** The NUS service UUID (`6e400001-…`) is a generic Nordic standard used by many BLE devices. If unwanted entries appear during discovery, simply dismiss them.
- **No command queue.** If you send several commands in quick succession, each is sent individually. The retry mechanism handles transient failures but does not re-order or batch commands.
- **Stale state after long disconnection.** If the device goes offline for an extended period, sensor values remain at the last known reading until the connection is restored and a fresh status is received.

---

## Reporting issues

Please include the following in your bug report:

- Home Assistant version
- Bluetooth setup (USB adapter model or ESPHome Bluetooth Proxy firmware version)
- Full log output for the `felshare_ble` component (enable debug logging with the snippet below)
- Steps to reproduce

### Enabling debug logging

Add to `configuration.yaml`:

```yaml
logger:
  default: warning
  logs:
    custom_components.felshare_ble: debug
```

Then restart Home Assistant and reproduce the issue. Copy the relevant log lines from **Settings → System → Logs**.

---

## Changelog

See [CHANGELOG.md](CHANGELOG.md).
