"""Unit tests for Felshare BLE protocol helpers.

Covers the bugs fixed in the audit:
- BUG-3: parse_hhmm error handling
- BUG-4: oil_level_pct clamping
- Frame encoding / decoding roundtrips
- Workmode bitmask manipulation
"""
import sys
import os
import importlib.util

# Import protocol.py directly to avoid the HA-dependent package __init__.py
_protocol_path = os.path.join(
    os.path.dirname(__file__), "..", "custom_components", "felshare_ble", "protocol.py"
)
_spec = importlib.util.spec_from_file_location("felshare_ble_protocol", _protocol_path)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)

parse_hhmm = _mod.parse_hhmm
decode_frame = _mod.decode_frame
bytes_workmode = _mod.bytes_workmode
bytes_power = _mod.bytes_power
bytes_fan = _mod.bytes_fan
bytes_oil_name = _mod.bytes_oil_name
bytes_oil_capacity_ml = _mod.bytes_oil_capacity_ml
bytes_oil_remain_ml = _mod.bytes_oil_remain_ml
bytes_oil_consumption = _mod.bytes_oil_consumption
bytes_status_request = _mod.bytes_status_request
bytes_bulk_request = _mod.bytes_bulk_request
find_workmode_inside_bytes = _mod.find_workmode_inside_bytes
clamp_int = _mod.clamp_int
sanitize_ascii_label = _mod.sanitize_ascii_label


# ---------------------------------------------------------------------------
# parse_hhmm — BUG-3 regression tests
# ---------------------------------------------------------------------------

class TestParseHhmm:
    def test_valid_normal(self):
        assert parse_hhmm("09:00") == (9, 0)

    def test_valid_midnight(self):
        assert parse_hhmm("00:00") == (0, 0)

    def test_valid_end_of_day(self):
        assert parse_hhmm("23:59") == (23, 59)

    def test_valid_padded(self):
        assert parse_hhmm("  21:30  ") == (21, 30)

    # --- error cases that previously crashed (BUG-3 fix) ---

    def test_empty_string(self):
        # Must not raise; returns safe default (0, 0)
        assert parse_hhmm("") == (0, 0)

    def test_none_input(self):
        assert parse_hhmm(None) == (0, 0)

    def test_no_colon(self):
        assert parse_hhmm("0900") == (0, 0)

    def test_multiple_colons(self):
        assert parse_hhmm("09:00:00") == (0, 0)

    def test_non_numeric(self):
        assert parse_hhmm("aa:bb") == (0, 0)

    def test_whitespace_only(self):
        assert parse_hhmm("   ") == (0, 0)


# ---------------------------------------------------------------------------
# decode_frame — oil_level_pct clamping (BUG-4 regression)
# ---------------------------------------------------------------------------

def _build_status_frame(remain_ml: int, capacity_ml: int) -> bytes:
    """Build a minimal valid 0x05 status frame with given oil values.

    Protocol byte map (from decode_frame):
      [0]     = 0x05 cmd
      [1:3]   = year (u16be)
      [3]     = month  [4]=day  [5]=hour  [6]=minute  [7]=second
      [8]     = padding (unused by decoder)
      [9]     = power  [10]=fan
      [11:13] = consumption_raw (u16be)
      [13:15] = oil_capacity_ml (u16be)
      [15:20] = padding
      [20:22] = oil_remain_ml (u16be)
      [22:24] = padding
      [24+]   = oil name bytes
    """
    year_bytes = (2024).to_bytes(2, "big")
    capacity_bytes = capacity_ml.to_bytes(2, "big")
    remain_bytes = remain_ml.to_bytes(2, "big")
    frame = (
        bytes([0x05])              # [0]
        + year_bytes               # [1:3]
        + bytes([6, 15, 10, 30, 0])  # [3:8]  month, day, hour, min, sec
        + bytes([0x00])            # [8]    padding
        + bytes([0x01, 0x01])      # [9:11] power=on, fan=on
        + bytes([0x00, 0x0A])      # [11:13] consumption_raw=10
        + capacity_bytes           # [13:15]
        + bytes([0, 0, 0, 0, 0])   # [15:20] padding
        + remain_bytes             # [20:22]
        + bytes([0, 0])            # [22:24] padding
        + b"Rose\x00"              # [24+]
    )
    return frame


class TestOilLevelPct:
    def test_normal_half(self):
        frame = _build_status_frame(remain_ml=500, capacity_ml=1000)
        st = decode_frame(frame)
        assert st["oil_level_pct"] == 50

    def test_full(self):
        frame = _build_status_frame(remain_ml=1000, capacity_ml=1000)
        st = decode_frame(frame)
        assert st["oil_level_pct"] == 100

    def test_empty(self):
        frame = _build_status_frame(remain_ml=0, capacity_ml=1000)
        st = decode_frame(frame)
        assert st["oil_level_pct"] == 0

    def test_over_capacity_clamped_to_100(self):
        # BUG-4: remain > capacity must clamp to 100, not return >100
        frame = _build_status_frame(remain_ml=1500, capacity_ml=1000)
        st = decode_frame(frame)
        assert st["oil_level_pct"] == 100, (
            f"Expected 100 but got {st['oil_level_pct']} — BUG-4 not fixed"
        )

    def test_zero_capacity_no_key(self):
        # capacity=0 must not produce oil_level_pct (division by zero guard)
        frame = _build_status_frame(remain_ml=0, capacity_ml=0)
        st = decode_frame(frame)
        assert "oil_level_pct" not in st


# ---------------------------------------------------------------------------
# Frame encoding helpers
# ---------------------------------------------------------------------------

class TestBytesHelpers:
    def test_power_on(self):
        assert bytes_power(True) == bytes([0x03, 0x01])

    def test_power_off(self):
        assert bytes_power(False) == bytes([0x03, 0x00])

    def test_fan_on(self):
        assert bytes_fan(True) == bytes([0x04, 0x01])

    def test_fan_off(self):
        assert bytes_fan(False) == bytes([0x04, 0x00])

    def test_status_request(self):
        assert bytes_status_request() == bytes([0x05])

    def test_bulk_request(self):
        assert bytes_bulk_request() == bytes([0x0C])

    def test_oil_capacity_normal(self):
        b = bytes_oil_capacity_ml(1000)
        assert b[0] == 0x0F
        assert int.from_bytes(b[1:], "big") == 1000

    def test_oil_capacity_max_clamp(self):
        b = bytes_oil_capacity_ml(99999)
        assert int.from_bytes(b[1:], "big") == 65535

    def test_oil_capacity_negative_clamp(self):
        b = bytes_oil_capacity_ml(-1)
        assert int.from_bytes(b[1:], "big") == 0

    def test_oil_remain(self):
        b = bytes_oil_remain_ml(500)
        assert b[0] == 0x10
        assert int.from_bytes(b[1:], "big") == 500

    def test_oil_consumption(self):
        b = bytes_oil_consumption(100)
        assert b[0] == 0x0E
        assert int.from_bytes(b[1:], "big") == 100

    def test_oil_name_with_null(self):
        b = bytes_oil_name("Rose")
        assert b[0] == 0x08
        assert b[1:] == b"Rose\x00"

    def test_oil_name_no_null(self):
        b = bytes_oil_name("Rose", null_term=False)
        assert b[1:] == b"Rose"

    def test_oil_name_non_ascii_stripped(self):
        # Non-ASCII chars should be silently ignored
        b = bytes_oil_name("Róse")
        assert b"\xc3" not in b  # UTF-8 byte for ó should be stripped

    def test_oil_name_empty(self):
        b = bytes_oil_name("")
        assert b[0] == 0x08
        assert b[1:] == b"\x00"


# ---------------------------------------------------------------------------
# Workmode frame encoding + decoding roundtrip
# ---------------------------------------------------------------------------

class TestWorkmode:
    def test_roundtrip_basic(self):
        frame = bytes_workmode(9, 0, 21, 30, True, 0x7F, 30, 280)
        assert frame[0] == 0x32
        assert frame[1] == 0x01
        assert len(frame) == 11

        st = decode_frame(frame)
        assert st["work_start"] == "09:00"
        assert st["work_end"] == "21:30"
        assert st["work_enabled"] is True
        assert st["work_days_mask"] == 0x7F
        assert st["work_run_s"] == 30
        assert st["work_stop_s"] == 280

    def test_disabled_schedule(self):
        frame = bytes_workmode(0, 0, 0, 0, False, 0, 0, 0)
        st = decode_frame(frame)
        assert st["work_enabled"] is False
        assert st["work_days_mask"] == 0

    def test_individual_day_bits(self):
        # Only Monday (bit 1)
        frame = bytes_workmode(9, 0, 17, 0, True, 0b0000010, 60, 120)
        st = decode_frame(frame)
        assert st["work_days_mask"] == 0b0000010

    def test_enabled_flag_masked_from_daymask(self):
        # enabled bit (0x80) must not leak into daymask
        frame = bytes_workmode(9, 0, 17, 0, True, 0x7F, 30, 280)
        st = decode_frame(frame)
        assert st["work_enabled"] is True
        assert st["work_days_mask"] == 0x7F  # all 7 day bits, no overflow

    def test_find_workmode_inside_bulk(self):
        wm_frame = bytes_workmode(8, 0, 22, 0, True, 0x3F, 45, 300)
        # Embed inside a fake 0x0C bulk frame with header bytes
        bulk = bytes([0x0C, 0xAB, 0xCD]) + wm_frame + bytes([0xFF, 0xFF])
        result = find_workmode_inside_bytes(bulk)
        assert result is not None
        sh, sm, eh, em, flag, run_s, stop_s, offset = result
        assert sh == 8 and sm == 0
        assert eh == 22 and em == 0
        assert run_s == 45 and stop_s == 300

    def test_find_workmode_too_short(self):
        assert find_workmode_inside_bytes(bytes([0x32, 0x01])) is None


# ---------------------------------------------------------------------------
# Simple property frame decoding
# ---------------------------------------------------------------------------

class TestSimpleFrames:
    def test_power_frame_on(self):
        st = decode_frame(bytes([0x03, 0x01]))
        assert st["power_on"] is True

    def test_power_frame_off(self):
        st = decode_frame(bytes([0x03, 0x00]))
        assert st["power_on"] is False

    def test_fan_frame_on(self):
        st = decode_frame(bytes([0x04, 0x01]))
        assert st["fan_on"] is True

    def test_oil_name_frame(self):
        st = decode_frame(bytes([0x08]) + b"Lavender\x00")
        assert st["oil_name"] == "Lavender"

    def test_oil_capacity_frame(self):
        st = decode_frame(bytes([0x0F, 0x03, 0xE8]))  # 1000 mL
        assert st["oil_capacity_ml"] == 1000

    def test_oil_remain_frame(self):
        st = decode_frame(bytes([0x10, 0x01, 0xF4]))  # 500 mL
        assert st["oil_remain_ml"] == 500

    def test_consumption_frame(self):
        st = decode_frame(bytes([0x0E, 0x00, 0x64]))  # raw=100 → 10.0 mL/h
        assert st["oil_consumption_raw"] == 100

    def test_empty_frame(self):
        assert decode_frame(b"") == {}

    def test_unknown_frame(self):
        # Unknown command byte should return empty dict, not crash
        st = decode_frame(bytes([0xFF, 0x01, 0x02, 0x03]))
        assert st == {}


# ---------------------------------------------------------------------------
# sanitize_ascii_label
# ---------------------------------------------------------------------------

class TestSanitizeAscii:
    def test_plain_string(self):
        assert sanitize_ascii_label(b"Lavender") == "Lavender"

    def test_null_terminated(self):
        assert sanitize_ascii_label(b"Rose\x00garbage") == "Rose"

    def test_strips_non_printable(self):
        result = sanitize_ascii_label(bytes([0x08, 0x41, 0x08]))  # BS A BS
        assert result == "A"

    def test_empty(self):
        assert sanitize_ascii_label(b"") == ""

    def test_all_nulls(self):
        assert sanitize_ascii_label(b"\x00\x00") == ""


# ---------------------------------------------------------------------------
# clamp_int
# ---------------------------------------------------------------------------

class TestClampInt:
    def test_within_range(self):
        assert clamp_int(50, 0, 100) == 50

    def test_below_min(self):
        assert clamp_int(-5, 0, 100) == 0

    def test_above_max(self):
        assert clamp_int(200, 0, 100) == 100

    def test_at_boundaries(self):
        assert clamp_int(0, 0, 100) == 0
        assert clamp_int(100, 0, 100) == 100
