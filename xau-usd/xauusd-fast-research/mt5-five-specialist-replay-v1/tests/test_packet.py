from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "mt5_replay_packet", ROOT / "build_packet.py"
)
if SPEC is None or SPEC.loader is None:
    raise ImportError(ROOT / "build_packet.py")
PACKET = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = PACKET
SPEC.loader.exec_module(PACKET)

COLLECT_SPEC = importlib.util.spec_from_file_location(
    "mt5_replay_collector", ROOT / "collect_reports.py"
)
if COLLECT_SPEC is None or COLLECT_SPEC.loader is None:
    raise ImportError(ROOT / "collect_reports.py")
COLLECTOR = importlib.util.module_from_spec(COLLECT_SPEC)
sys.modules[COLLECT_SPEC.name] = COLLECTOR
COLLECT_SPEC.loader.exec_module(COLLECTOR)


def test_frozen_three_month_schedules() -> None:
    config = PACKET.load_config()
    frames = PACKET.load_source_frames(config)
    schedules = {
        row["specialist_id"]: PACKET.build_schedule(row, frames, config)
        for row in config["replay_specialists"]
    }
    assert {key: len(value) for key, value in schedules.items()} == {
        "R2_DOWNTREND": 2,
        "R3_COMPRESSION": 2,
        "R4_CHOP": 0,
        "R5_TRANSITION": 2,
    }
    assert schedules["R2_DOWNTREND"]["server_entry_time"].tolist() == [
        "2026.06.09 19:00:00",
        "2026.06.11 12:00:00",
    ]
    assert schedules["R5_TRANSITION"]["target_r"].eq(2.75).all()
    assert schedules["R3_COMPRESSION"]["target_r"].eq(0.0).all()
    assert all(
        list(schedule.columns) == PACKET.SCHEDULE_COLUMNS
        for schedule in schedules.values()
    )


def test_replay_config_is_real_tick_and_tester_only() -> None:
    config = PACKET.load_config()
    definition = config["replay_specialists"][0]
    parser = PACKET.replay_config(definition, "schedule.csv", config)
    assert parser["Tester"]["Model"] == "4"
    assert parser["Tester"]["FromDate"] == "2026.04.01"
    assert parser["Tester"]["ToDate"] == "2026.06.30"
    assert parser["TesterInputs"]["InpExpectedServerMarker"] == "Demo"
    assert float(parser["TesterInputs"]["InpFixedLots"]) == 0.01


def test_window_has_no_r4_schedule() -> None:
    config = PACKET.load_config()
    frames = PACKET.load_source_frames(config)
    definition = next(
        row for row in config["replay_specialists"] if row["specialist_id"] == "R4_CHOP"
    )
    schedule = PACKET.build_schedule(definition, frames, config)
    assert schedule.empty
    assert isinstance(schedule, pd.DataFrame)


def test_combined_schedule_contains_all_six_replay_signals() -> None:
    config = PACKET.load_config()
    frames = PACKET.load_source_frames(config)
    schedules = {
        row["specialist_id"]: PACKET.build_schedule(row, frames, config)
        for row in config["replay_specialists"]
    }
    combined = PACKET.build_combined_schedule(schedules, config["combined_replay"])
    assert len(combined) == 6
    assert combined["specialist_id"].eq("ALL_SPECIALISTS").all()
    assert combined["server_entry_time"].is_monotonic_increasing
    assert combined["signal_id"].str.match(r"R[235]_.*__").all()


def test_mt5_report_reader_accepts_utf8_and_utf16(tmp_path: Path) -> None:
    payload = "<td>History Quality:</td><td>100% real ticks</td>"
    utf8 = tmp_path / "utf8.htm"
    utf16 = tmp_path / "utf16.htm"
    utf8.write_text(payload, encoding="utf-8")
    utf16.write_text(payload, encoding="utf-16")
    assert COLLECTOR.read_mt5_html(utf8) == payload
    assert COLLECTOR.read_mt5_html(utf16) == payload
    assert COLLECTOR.drawdown("114.08 (8.81%)") == (114.08, 8.81)
    assert COLLECTOR.weekday_count("2026-04-01T00:00:00Z", "2026-07-01T00:00:00Z") == 65
