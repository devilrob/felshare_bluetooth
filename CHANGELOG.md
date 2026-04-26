# Changelog

## 0.1.4
- Add automatic retry: user commands now retry once after a 300 ms pause when a transient BLE error occurs, instead of surfacing the error immediately.
- README rewritten with full entity table, setup guide, troubleshooting table, debug-logging snippet, and known limitations.

## 0.1.3
- **Fix (HIGH):** `TextEntity` max-length constraint for the oil name was silently ignored because the wrong attribute names (`_attr_native_min`/`_attr_native_max`) were used instead of `_attr_min`/`_attr_max`. The intended 64-character limit is now enforced by the HA UI.
- **Fix (HIGH):** Auto-discovery via Bluetooth was completely broken — the `"bluetooth"` section was missing from `manifest.json` so `async_step_bluetooth` was never triggered. Added NUS service UUID matcher. Also corrected the dependency from `bluetooth_adapters` to `bluetooth`.
- **Fix (MEDIUM):** `parse_hhmm()` crashed with an unhandled `ValueError` on any malformed time value from the device (e.g., missing colon, extra colon, non-numeric). Now returns `(0, 0)` as a safe fallback.
- **Fix (MEDIUM):** `oil_level_pct` sensor could display values above 100% when the reported remaining oil exceeded the reported capacity. Now clamped to the range 0–100.
- **Fix (MEDIUM):** `assert self._client is not None` in `ble.py` was checked outside the asyncio lock, creating a race condition — a concurrent `disconnect()` call could null the client between the assertion and the actual write. Replaced with an explicit `BleakError` raised *inside* the lock.
- Refactor: `_current_work_fields()` was duplicated identically in `switch.py`, `number.py`, and `time.py`. Extracted to `entity.py` as `current_work_fields()` with a typed return annotation.
- Tests: Added `tests/test_protocol.py` with 54 unit tests covering all fixed bugs, frame encoding/decoding, workmode bitmask logic, and edge cases.

## 0.1.2
- Increase BLE connection timeout to 30 s to reduce BlueZ service discovery timeouts.
- Add setup-time check for a connectable Bluetooth scanner/adapter and fail with a clearer message when missing.
- Prefer the latest `BluetoothServiceInfoBleak` via `bluetooth.async_last_service_info()` to avoid stale BLEDevice cache.

## 0.1.1
- Handle `asyncio.CancelledError` safely during startup/unload to avoid hard failures.

## 0.1.0
- Initial HACS-ready release.
