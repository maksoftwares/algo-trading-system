from __future__ import annotations

import importlib.util
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "deployed_specialist_monitor",
    ROOT / "deployed_specialist_monitor.py",
)
assert SPEC is not None and SPEC.loader is not None
MONITOR = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MONITOR
SPEC.loader.exec_module(MONITOR)


def test_every_deployed_source_has_an_operational_feed_mapping() -> None:
    config = MONITOR.read_json(MONITOR.CONFIG_PATH)
    source_ids = {str(row["source_id"]) for row in config["sources"]}

    assert len(source_ids) == 9
    assert set(MONITOR.FEED_BY_SOURCE) == source_ids


def test_monitor_is_read_only() -> None:
    text = (ROOT / "deployed_specialist_monitor.py").read_text(encoding="utf-8")

    assert "MetaTrader5" not in text
    assert "order_send" not in text
    assert "broker_action_added" in text


def test_tick_monitor_skips_newer_header_only_market_closed_file(
    tmp_path: Path,
) -> None:
    header = "timestamp_utc,bid,ask\n"
    active = tmp_path / "xau_ticks_20260731.csv"
    active.write_text(
        header + "2026.07.31 20:59:59.000Z,3300.0,3300.2\n",
        encoding="utf-8",
    )
    closed = tmp_path / "xau_ticks_20260801.csv"
    closed.write_text(header, encoding="utf-8")
    config = {
        "feeds": {
            "terminal_files_directory": str(tmp_path),
            "tick_filename_glob": "xau_ticks_*.csv",
        }
    }

    status = MONITOR.latest_tick_transport(config)

    assert status["errors"] == []
    assert status["latest_path"] == str(active)
    assert status["newest_path"] == str(closed)
    assert status["market_state"] == "MARKET_CLOSED_OR_IDLE"
    assert status["filename_day_matches_row"] is True


def test_last_complete_csv_row_ignores_incomplete_tail(tmp_path: Path) -> None:
    path = tmp_path / "ticks.csv"
    path.write_bytes(
        b"timestamp_utc,bid,ask\n"
        b"2026.07.31 20:59:59.000Z,3300.0,3300.2\n"
        b"2026.07.31 21:00:00.000Z,3300.1"
    )

    row = MONITOR.last_complete_csv_row(path)

    assert row is not None
    assert row["timestamp_utc"] == "2026.07.31 20:59:59.000Z"
