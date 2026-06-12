from __future__ import annotations

import csv
import importlib.util
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_outcome_resolution_matches_broker_trade_with_one_minute_tolerance(tmp_path: Path):
    module = _load_module()
    shadow_dir = tmp_path / "shadow"
    shadow_dir.mkdir()
    _write_shadow_rows(
        shadow_dir / "shadow_fix_observer_signal_log_xauusd.csv",
        [
            _shadow_row(
                candidate="breakout_retest",
                m5_bar_time="2026.06.12 06:15:00",
                time_bucket="Morning 06:00-11:59",
                direction="LONG",
            )
        ],
    )
    actual_csv = tmp_path / "actual.csv"
    _write_actual_rows(
        actual_csv,
        [
            {
                "entry_time": "2026-06-12 06:16:12",
                "exit_time": "2026-06-12 06:25:00",
                "candidate": "breakout_retest",
                "symbol": "XAUUSD",
                "direction": "BUY",
                "state": "CLOSED",
                "profit_aed": "25.00",
                "position_ticket": "123",
                "exit_price": "102.00",
            }
        ],
    )

    output = module.generate_observer_outcome_resolution(
        tmp_path,
        shadow_files_dir=shadow_dir,
        actual_trades_csv=actual_csv,
        output_json=tmp_path / "out.json",
    )
    payload = json.loads(output.read_text(encoding="utf-8"))
    rows = _read_rows(tmp_path / "out.csv")

    assert payload["status"] == "PASS_ALL_SIGNALS_RESOLVED"
    assert payload["resolved_count"] == 1
    assert rows[0]["resolution_status"] == "BROKER_CLOSED_WIN"
    assert rows[0]["resolution_source"] == "broker_trade_join"
    assert rows[0]["direction"] == "LONG"
    assert rows[0]["normalized_direction"] == "BUY"
    assert rows[0]["matched_position_ticket"] == "123"
    assert rows[0]["actual_profit_aed"] == "25.00"
    scoreboard = json.loads(
        (tmp_path / "outputs" / "reports" / "OBSERVER_SHADOW_POLICY_SCOREBOARD.json").read_text(encoding="utf-8")
    )
    assert scoreboard["broker_join_resolved_count"] == 1
    assert scoreboard["replay_resolved_count"] == 0
    assert scoreboard["rows"][0]["aggregation_level"] == "candidate"
    assert scoreboard["rows"][0]["family"] == "breakout"


def test_outcome_resolution_marks_round_retest_clone_family_as_proposed_block(tmp_path: Path):
    module = _load_module()
    shadow_dir = tmp_path / "shadow"
    shadow_dir.mkdir()
    _write_shadow_rows(
        shadow_dir / "shadow_fix_observer_signal_log_xauusd.csv",
        [
            _shadow_row(
                candidate="round_number_retest_v0",
                m5_bar_time="2026.06.12 18:05:00",
                time_bucket="Evening 16:00-20:59",
                direction="SELL",
            )
        ],
    )
    actual_csv = tmp_path / "actual.csv"
    _write_actual_rows(actual_csv, [])

    output = module.generate_observer_outcome_resolution(
        tmp_path,
        shadow_files_dir=shadow_dir,
        actual_trades_csv=actual_csv,
        output_json=tmp_path / "out.json",
    )
    payload = json.loads(output.read_text(encoding="utf-8"))
    rows = _read_rows(tmp_path / "out.csv")

    assert payload["status"] == "PARTIAL_REVIEW_NEEDS_FRESH_M5_BARS"
    assert rows[0]["proposed_v2_shadow_action"] == "BLOCK"
    assert rows[0]["proposed_v2_shadow_reason"] == "BLOCK_WEAK_EA_ROUND_RETEST_CLONE_FAMILY"
    assert rows[0]["resolution_status"] == "UNRESOLVED_NO_BROKER_MATCH_NO_REPLAY_BARS"


def test_outcome_resolution_replays_m5_bars_when_supplied(tmp_path: Path):
    module = _load_module()
    shadow_dir = tmp_path / "shadow"
    shadow_dir.mkdir()
    _write_shadow_rows(
        shadow_dir / "shadow_fix_observer_signal_log_xauusd.csv",
        [
            _shadow_row(
                candidate="breakout_retest",
                m5_bar_time="2026.06.12 18:05:00",
                time_bucket="Evening 16:00-20:59",
                direction="LONG",
                entry_price="100.00",
                stop_loss="95.00",
                take_profit="110.00",
            )
        ],
    )
    actual_csv = tmp_path / "actual.csv"
    _write_actual_rows(actual_csv, [])
    bars_dir = tmp_path / "bars"
    bars_dir.mkdir()
    _write_m5_bars(
        bars_dir / "XAUUSD_test_M5.csv",
        [
            {
                "bar_start_utc": "2026-06-12 18:05:00",
                "bar_end_utc": "2026-06-12 18:10:00",
                "open": "100.00",
                "high": "100.50",
                "low": "99.50",
            },
            {
                "bar_start_utc": "2026-06-12 18:10:00",
                "bar_end_utc": "2026-06-12 18:15:00",
                "open": "100.00",
                "high": "109.00",
                "low": "99.00",
            }
        ],
    )

    output = module.generate_observer_outcome_resolution(
        tmp_path,
        shadow_files_dir=shadow_dir,
        actual_trades_csv=actual_csv,
        bars_dir=bars_dir,
        output_json=tmp_path / "out.json",
    )
    payload = json.loads(output.read_text(encoding="utf-8"))
    rows = _read_rows(tmp_path / "out.csv")

    assert payload["status"] == "PASS_ALL_SIGNALS_RESOLVED"
    assert rows[0]["resolution_status"] == "REPLAY_TP"
    assert rows[0]["resolution_source"] == "m5_bar_replay_executor_v2_adverse_first"
    assert rows[0]["replay_model"] == "executor_v2"
    assert rows[0]["normalized_direction"] == "BUY"
    assert rows[0]["replay_entry_price"] == "100.250000"
    assert rows[0]["replay_exit_price"] == "108.125000"
    assert payload["replay_resolved_count"] == 1
    assert payload["bar_quality"][0]["symbol"] == "XAUUSD"
    assert payload["bar_quality"][0]["rows"] == 2


def test_outcome_resolution_uses_adverse_first_when_bar_hits_stop_and_target(tmp_path: Path):
    module = _load_module()
    shadow_dir = tmp_path / "shadow"
    shadow_dir.mkdir()
    _write_shadow_rows(
        shadow_dir / "shadow_fix_observer_signal_log_xauusd.csv",
        [
            _shadow_row(
                candidate="breakout_retest",
                m5_bar_time="2026.06.12 18:05:00",
                time_bucket="Evening 16:00-20:59",
                direction="BUY",
                entry_price="100.00",
                stop_loss="95.00",
                take_profit="110.00",
            )
        ],
    )
    actual_csv = tmp_path / "actual.csv"
    _write_actual_rows(actual_csv, [])
    bars_dir = tmp_path / "bars"
    bars_dir.mkdir()
    _write_m5_bars(
        bars_dir / "XAUUSD_test_M5.csv",
        [
            {
                "bar_start_utc": "2026-06-12 18:05:00",
                "bar_end_utc": "2026-06-12 18:10:00",
                "open": "100.00",
                "high": "100.50",
                "low": "99.50",
            },
            {
                "bar_start_utc": "2026-06-12 18:10:00",
                "bar_end_utc": "2026-06-12 18:15:00",
                "open": "100.00",
                "high": "109.00",
                "low": "94.00",
            }
        ],
    )

    output = module.generate_observer_outcome_resolution(
        tmp_path,
        shadow_files_dir=shadow_dir,
        actual_trades_csv=actual_csv,
        bars_dir=bars_dir,
        output_json=tmp_path / "out.json",
    )
    rows = _read_rows(tmp_path / "out.csv")

    assert rows[0]["resolution_status"] == "REPLAY_SL"
    assert rows[0]["replay_exit_price"] == "95.000000"


def test_outcome_resolution_replays_short_as_sell(tmp_path: Path):
    module = _load_module()
    shadow_dir = tmp_path / "shadow"
    shadow_dir.mkdir()
    _write_shadow_rows(
        shadow_dir / "shadow_fix_observer_signal_log_xauusd.csv",
        [
            _shadow_row(
                candidate="breakout_retest",
                m5_bar_time="2026.06.12 18:05:00",
                time_bucket="Evening 16:00-20:59",
                direction="SHORT",
                entry_price="100.00",
                stop_loss="105.00",
                take_profit="90.00",
            )
        ],
    )
    actual_csv = tmp_path / "actual.csv"
    _write_actual_rows(actual_csv, [])
    bars_dir = tmp_path / "bars"
    bars_dir.mkdir()
    _write_m5_bars(
        bars_dir / "XAUUSD_test_M5.csv",
        [
            {
                "bar_start_utc": "2026-06-12 18:05:00",
                "bar_end_utc": "2026-06-12 18:10:00",
                "open": "100.00",
                "high": "101.00",
                "low": "99.00",
            },
            {
                "bar_start_utc": "2026-06-12 18:10:00",
                "bar_end_utc": "2026-06-12 18:15:00",
                "open": "100.00",
                "high": "101.00",
                "low": "91.50",
            }
        ],
    )

    output = module.generate_observer_outcome_resolution(
        tmp_path,
        shadow_files_dir=shadow_dir,
        actual_trades_csv=actual_csv,
        bars_dir=bars_dir,
        output_json=tmp_path / "out.json",
    )
    rows = _read_rows(tmp_path / "out.csv")
    payload = json.loads(output.read_text(encoding="utf-8"))

    assert rows[0]["direction"] == "SHORT"
    assert rows[0]["normalized_direction"] == "SELL"
    assert rows[0]["resolution_status"] == "REPLAY_TP"
    assert rows[0]["replay_entry_price"] == "99.750000"
    assert rows[0]["replay_exit_price"] == "91.875000"
    assert payload["replay_resolved_count"] == 1


def test_outcome_resolution_marks_unknown_direction_without_guessing(tmp_path: Path):
    module = _load_module()
    shadow_dir = tmp_path / "shadow"
    shadow_dir.mkdir()
    _write_shadow_rows(
        shadow_dir / "shadow_fix_observer_signal_log_xauusd.csv",
        [
            _shadow_row(
                candidate="breakout_retest",
                m5_bar_time="2026.06.12 18:05:00",
                time_bucket="Evening 16:00-20:59",
                direction="SIDEWAYS",
            )
        ],
    )
    actual_csv = tmp_path / "actual.csv"
    _write_actual_rows(
        actual_csv,
        [
            {
                "entry_time": "2026-06-12 18:05:30",
                "exit_time": "2026-06-12 18:20:00",
                "candidate": "breakout_retest",
                "symbol": "XAUUSD",
                "direction": "BUY",
                "state": "CLOSED",
                "profit_aed": "10.00",
                "position_ticket": "777",
                "exit_price": "101.00",
            }
        ],
    )

    output = module.generate_observer_outcome_resolution(
        tmp_path,
        shadow_files_dir=shadow_dir,
        actual_trades_csv=actual_csv,
        output_json=tmp_path / "out.json",
    )
    payload = json.loads(output.read_text(encoding="utf-8"))
    rows = _read_rows(tmp_path / "out.csv")

    assert payload["status"] == "PARTIAL_REVIEW_NEEDS_FRESH_M5_BARS"
    assert payload["resolved_count"] == 0
    assert rows[0]["normalized_direction"] == ""
    assert rows[0]["resolution_status"] == "UNRESOLVED_UNKNOWN_DIRECTION"


def test_outcome_resolution_report_states_no_runtime_touch(tmp_path: Path):
    module = _load_module()
    shadow_dir = tmp_path / "shadow"
    shadow_dir.mkdir()
    _write_shadow_rows(
        shadow_dir / "shadow_fix_observer_signal_log_xauusd.csv",
        [
            _shadow_row(
                candidate="breakout_retest",
                m5_bar_time="2026.06.12 18:05:00",
                time_bucket="Evening 16:00-20:59",
                direction="BUY",
            )
        ],
    )
    actual_csv = tmp_path / "actual.csv"
    _write_actual_rows(actual_csv, [])

    module.generate_observer_outcome_resolution(
        tmp_path,
        shadow_files_dir=shadow_dir,
        actual_trades_csv=actual_csv,
        output_json=tmp_path / "out.json",
    )
    report = (tmp_path / "out.md").read_text(encoding="utf-8")

    assert "does not touch MT5 runtime" in report
    assert "analysis-only" in report


def _shadow_row(
    *,
    candidate: str,
    m5_bar_time: str,
    time_bucket: str,
    direction: str,
    entry_price: str = "100.00",
    stop_loss: str = "99.00",
    take_profit: str = "102.00",
) -> dict[str, str]:
    return {
        "timestamp_broker": m5_bar_time,
        "m5_bar_time": m5_bar_time,
        "time_bucket": time_bucket,
        "candidate": candidate,
        "symbol": "XAUUSD",
        "direction": direction,
        "would_signal": "true",
        "shadow_action": "KEEP",
        "shadow_reason": "KEEP",
        "entry_price": entry_price,
        "stop_loss": stop_loss,
        "take_profit": take_profit,
        "spread_points": "50",
    }


def _write_shadow_rows(path: Path, rows: list[dict[str, str]]) -> None:
    _write_rows(
        path,
        [
            "timestamp_broker",
            "m5_bar_time",
            "time_bucket",
            "candidate",
            "symbol",
            "direction",
            "would_signal",
            "shadow_action",
            "shadow_reason",
            "entry_price",
            "stop_loss",
            "take_profit",
            "spread_points",
        ],
        rows,
    )


def _write_actual_rows(path: Path, rows: list[dict[str, str]]) -> None:
    _write_rows(
        path,
        [
            "entry_time",
            "exit_time",
            "candidate",
            "symbol",
            "direction",
            "state",
            "profit_aed",
            "position_ticket",
            "exit_price",
        ],
        rows,
    )


def _write_m5_bars(path: Path, rows: list[dict[str, str]]) -> None:
    _write_rows(path, ["bar_start_utc", "bar_end_utc", "open", "high", "low"], rows)


def _write_rows(path: Path, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _read_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _load_module():
    path = ROOT / "scripts" / "generate_observer_outcome_resolution.py"
    spec = importlib.util.spec_from_file_location("generate_observer_outcome_resolution", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules["generate_observer_outcome_resolution"] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module
