"""Felshare BLE protocol helpers.

The diffuser uses Nordic UART Service (NUS). Commands are written to TX characteristic
and responses/updates are received via RX notifications.

Frame formats (observed):
  - Status (0x05): variable length, contains time + power/fan + oil info
  - Bulk (0x0C): long frame that contains embedded WorkMode (0x32 0x01 ...)
  - WorkMode (0x32 0x01): exactly 11 bytes
  - Simple property frames: 0x03,0x04,0x08,0x0E,0x0F,0x10
"""
from __future__ import annotations

from typing import Any

def u16be(b: bytes) -> int:
    return int.from_bytes(b[:2], "big", signed=False)

def sanitize_ascii_label(raw: bytes) -> str:
    """Trim at NUL and keep printable ASCII."""
    if b"\x00" in raw:
        raw = raw.split(b"\x00", 1)[0]
    out = []
    for c in raw:
        if 32 <= c <= 126:
            out.append(chr(c))
    return "".join(out).strip()

def clamp_int(v: int, lo: int, hi: int) -> int:
    if v < lo:
        return lo
    if v > hi:
        return hi
    return v

def parse_hhmm(s: str) -> tuple[int, int]:
    s = (s or "").strip()
    hh, mm = s.split(":")
    return int(hh), int(mm)

def bytes_workmode(sh: int, sm: int, eh: int, em: int, enabled: bool, daymask: int, run_s: int, stop_s: int) -> bytes:
    flag = (0x80 if enabled else 0x00) | (daymask & 0x7F)
    return bytes([0x32, 0x01, sh & 0xFF, sm & 0xFF, eh & 0xFF, em & 0xFF, flag & 0xFF]) + int(run_s).to_bytes(2, "big") + int(stop_s).to_bytes(2, "big")

def bytes_power(on: bool) -> bytes:
    return bytes([0x03, 0x01 if on else 0x00])

def bytes_fan(on: bool) -> bytes:
    return bytes([0x04, 0x01 if on else 0x00])

def bytes_status_request() -> bytes:
    return bytes([0x05])

def bytes_bulk_request() -> bytes:
    return bytes([0x0C])

def bytes_oil_name(name: str, null_term: bool = True) -> bytes:
    name = (name or "").strip()
    b = name.encode("ascii", errors="ignore")
    if null_term:
        b += b"\x00"
    return bytes([0x08]) + b

def bytes_oil_capacity_ml(cap: int) -> bytes:
    cap = clamp_int(int(cap), 0, 65535)
    return bytes([0x0F]) + cap.to_bytes(2, "big")

def bytes_oil_remain_ml(rem: int) -> bytes:
    rem = clamp_int(int(rem), 0, 65535)
    return bytes([0x10]) + rem.to_bytes(2, "big")

def bytes_oil_consumption(raw_tenths: int) -> bytes:
    raw_tenths = clamp_int(int(raw_tenths), 0, 65535)
    return bytes([0x0E]) + raw_tenths.to_bytes(2, "big")

def find_workmode_inside_bytes(payload: bytes) -> tuple[int,int,int,int,int,int,int,int] | None:
    sig = bytes([0x32, 0x01])
    if len(payload) < 11:
        return None
    for i in range(0, len(payload) - 11 + 1):
        if payload[i:i+2] != sig:
            continue
        sh, sm, eh, em = payload[i+2], payload[i+3], payload[i+4], payload[i+5]
        flag = payload[i+6]
        run_s = u16be(payload[i+7:i+9])
        stop_s = u16be(payload[i+9:i+11])
        return (sh, sm, eh, em, flag, run_s, stop_s, i)
    return None

def decode_frame(frame: bytes) -> dict[str, Any]:
    """Decode a notification frame into a partial state dict."""
    st: dict[str, Any] = {}
    if not frame:
        return st

    cmd = frame[0]

    # Status 05
    if cmd == 0x05 and len(frame) >= 24:
        year = u16be(frame[1:3])
        month = frame[3]
        day = frame[4]
        hour = frame[5]
        minute = frame[6]
        second = frame[7]
        st["device_time"] = f"{year:04d}-{month:02d}-{day:02d} {hour:02d}:{minute:02d}:{second:02d}"

        pwr = frame[9]
        fan = frame[10]
        st["power_on"] = True if pwr == 1 else False if pwr == 0 else None
        st["fan_on"] = True if fan == 1 else False if fan == 0 else None

        st["oil_consumption_raw"] = u16be(frame[11:13])
        st["oil_capacity_ml"] = u16be(frame[13:15])
        st["oil_remain_ml"] = u16be(frame[20:22])

        cap = st.get("oil_capacity_ml")
        rem = st.get("oil_remain_ml")
        if isinstance(cap, int) and cap > 0 and isinstance(rem, int):
            st["oil_level_pct"] = int((rem * 100) / cap)

        raw_name = frame[24:] if len(frame) > 24 else b""
        name = sanitize_ascii_label(raw_name)
        if name:
            st["oil_name"] = name
        return st

    # Bulk 0C (contains embedded 32 01 ...)
    if cmd == 0x0C and len(frame) >= 20:
        wm = find_workmode_inside_bytes(frame)
        if wm:
            sh, sm, eh, em, flag, run_s, stop_s, _off = wm
            st["work_start"] = f"{sh:02d}:{sm:02d}"
            st["work_end"] = f"{eh:02d}:{em:02d}"
            st["work_enabled"] = bool(flag & 0x80)
            st["work_days_mask"] = int(flag & 0x7F)
            st["work_run_s"] = int(run_s)
            st["work_stop_s"] = int(stop_s)
        return st

    # WorkMode 32
    if cmd == 0x32 and len(frame) == 11 and frame[1] == 0x01:
        sh, sm, eh, em = frame[2], frame[3], frame[4], frame[5]
        flag = frame[6]
        st["work_start"] = f"{sh:02d}:{sm:02d}"
        st["work_end"] = f"{eh:02d}:{em:02d}"
        st["work_enabled"] = bool(flag & 0x80)
        st["work_days_mask"] = int(flag & 0x7F)
        st["work_run_s"] = u16be(frame[7:9])
        st["work_stop_s"] = u16be(frame[9:11])
        return st

    # Simple property frames
    if cmd == 0x03 and len(frame) >= 2:
        st["power_on"] = True if frame[1] == 1 else False if frame[1] == 0 else None
        return st
    if cmd == 0x04 and len(frame) >= 2:
        st["fan_on"] = True if frame[1] == 1 else False if frame[1] == 0 else None
        return st
    if cmd == 0x08 and len(frame) >= 2:
        name = sanitize_ascii_label(frame[1:])
        if name:
            st["oil_name"] = name
        return st
    if cmd == 0x0E and len(frame) >= 3:
        st["oil_consumption_raw"] = u16be(frame[1:3])
        return st
    if cmd == 0x0F and len(frame) >= 3:
        st["oil_capacity_ml"] = u16be(frame[1:3])
        return st
    if cmd == 0x10 and len(frame) >= 3:
        st["oil_remain_ml"] = u16be(frame[1:3])
        return st

    return st
