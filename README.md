# Felshare Diffuser (BLE) — Home Assistant Integration

This custom integration controls a **Felshare waterless diffuser** via **Bluetooth Low Energy (BLE)** using the device's Nordic UART Service (NUS).

> **Important:** Home Assistant must have a **working Bluetooth adapter** (USB) **or** an **ESPHome Bluetooth Proxy** close to the diffuser.

## Features (current)
- Power / Fan on/off
- Status refresh (Status `0x05`)
- Bulk refresh (Workmode + schedule)
- Edit:
  - Oil Name
  - Oil Capacity (mL)
  - Oil Remaining (mL)
  - Consumption (mL/h)
  - Work schedule (start/end + run/stop + days)
- Entities: `switch`, `sensor`, `number`, `text`, `time`

## Installation (HACS)
1. HACS → **Integrations** → ⋮ → **Custom repositories**
2. Add your repo URL and choose **Integration**
3. Install **Felshare Diffuser (BLE)**
4. Restart Home Assistant
5. Settings → Devices & Services → **Add Integration** → **Felshare Diffuser (Bluetooth)**

## Bluetooth requirements / troubleshooting
If you see errors like:
- `Failed to connect after ... attempt(s): TimeoutError`
- `BleakNotFoundError ... not found / not reachable`

Do this first:
1. Put the diffuser **very close** to the HA Bluetooth adapter / proxy.
2. **Close the Felshare phone app** (many BLE devices allow only one active connection).
3. Power-cycle the diffuser.
4. Settings → Devices & Services → **Bluetooth**:
   - Verify there is at least **one** adapter/proxy listed.
   - Verify the diffuser is **discovered** (you should see its MAC and RSSI).

Tip: Too many BLE integrations can exhaust connection slots. Temporarily disable other BLE-heavy integrations to test.

## Reporting issues
Please include:
- Home Assistant version
- How Bluetooth is provided (USB adapter model, or ESPHome Bluetooth Proxy)
- The full log for `felshare_ble`
