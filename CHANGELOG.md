# Changelog

## 0.1.2
- Increase BLE connection timeout to 30s to reduce BlueZ service discovery timeouts.
- Add Bluetooth matcher in `manifest.json` (NUS service UUID) to improve discovery.
- Add setup-time check for a **connectable** Bluetooth scanner/adapter and fail with a clearer message when missing.
- Prefer the latest `BluetoothServiceInfoBleak` via `bluetooth.async_last_service_info()` to avoid stale BLEDevice cache.

## 0.1.1
- Handle `asyncio.CancelledError` safely during startup/unload to avoid hard failures.

## 0.1.0
- Initial HACS-ready release.
