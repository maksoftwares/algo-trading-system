from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
from types import SimpleNamespace

import pandas as pd
import pytest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from resolver import (  # noqa: E402
    FrameTickStore,
    Quote,
    candidate_fact_sha256,
    load_config,
    load_frozen_execution,
    load_tick_snapshots,
    parse_candidate_snapshot,
    process_candidates,
    resolve_candidate_causally,
    sha256_bytes,
    validate_candidate,
    verify_resolution_prefix,
    verify_source_prefix,
)


def _execution() -> dict[str, float | int | str]:
    return {
        "maximum_entry_gap_minutes": 20,
        "maximum_horizon_gap_hours": 72,
        "maximum_entry_spread_r": 0.15,
        "maximum_research_risk_usd": 50.0,
        "ounces_at_lot_size": 1.0,
        "ticket_cost_usd": 0.30,
        "holding_cost_per_24h_usd": 0.35,
        "stress_slippage_r": 0.05,
        "maximum_trades_per_component_utc_day": 4,
        "maximum_trades_per_portfolio_utc_day": 4,
        "stop_fill_policy": "OBSERVED_EXECUTABLE_TICK_ON_CROSS",
        "target_fill_policy": "LOCKED_TARGET_PRICE_ON_FIRST_CROSS",
        "horizon_fill_policy": "FIRST_EXECUTABLE_TICK_AT_OR_AFTER_DEADLINE",
    }


def _candidate_id(attempt: int, timestamp: pd.Timestamp) -> str:
    payload = f"{attempt}|{timestamp.isoformat()}".encode("ascii")
    return hashlib.sha256(payload).hexdigest()[:24]


def _candidate_record(
    timestamp: str = "2026-07-20T00:00:00Z",
    *,
    attempt: int = 23925,
    direction: int = 1,
    signal_atr: float = 2.0,
    stop_atr: float = 1.0,
    target_r: float = 2.0,
    hold_hours: float = 1.0,
) -> dict[str, object]:
    config = load_config()
    signal = pd.Timestamp(timestamp)
    return {
        "candidate_id": _candidate_id(attempt, signal),
        "origin_attempt": attempt,
        "origin_variant_id": "TEST",
        "regime_owner": "transition",
        "mechanic": "TEST_MECHANIC",
        "geometry_id": "TEST_GEOMETRY",
        "direction_sign": direction,
        "direction": "LONG" if direction > 0 else "SHORT",
        "signal_atr": signal_atr,
        "stop_atr": stop_atr,
        "target_r": target_r,
        "hold_hours": hold_hours,
        "parameters_json": "{}",
        "signal_time_utc": timestamp,
        "scheduled_entry_time_utc": timestamp,
        "rule_dependency_sha256": config["frozen_identity"][
            "v35_rule_dependency_sha256"
        ],
    }


def _normalized(**kwargs: object) -> dict[str, object]:
    return validate_candidate(_candidate_record(**kwargs), load_config())


def _namespace(row: dict[str, object]) -> SimpleNamespace:
    return SimpleNamespace(
        candidate_id=row["candidate_id"],
        origin_attempt=row["origin_attempt"],
        origin_variant_id=row["origin_variant_id"],
        regime_owner=row["regime_owner"],
        mechanic=row["mechanic"],
        geometry_id=row["geometry_id"],
        signal_time=row["signal_time"],
        scheduled_entry_time=row["scheduled_entry_time"],
        direction_sign=row["direction_sign"],
        direction=row["direction"],
        signal_atr=row["signal_atr"],
        stop_atr=row["stop_atr"],
        target_r=row["target_r"],
        hold_hours=row["hold_hours"],
    )


def _ticks(rows: list[tuple[str, float, float]]) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "tick_time_msc": [
                int(pd.Timestamp(time).value // 1_000_000) for time, _, _ in rows
            ],
            "bid": [bid for _, bid, _ in rows],
            "ask": [ask for _, _, ask in rows],
        }
    )


def _historical() -> pd.DataFrame:
    return pd.DataFrame(columns=["attempt_no", "entry_time", "exit_time"])


def test_candidate_identity_and_timing_are_fail_closed() -> None:
    config = load_config()
    record = _candidate_record()
    normalized = validate_candidate(record, config)
    assert normalized["signal_time"] == normalized["scheduled_entry_time"]
    changed = dict(record)
    changed["scheduled_entry_time_utc"] = "2026-07-20T00:15:00Z"
    with pytest.raises(ValueError, match="signal/entry time parity"):
        validate_candidate(changed, config)
    changed = dict(record)
    changed["gross_r"] = 1.0
    with pytest.raises(ValueError, match="candidate schema changed"):
        validate_candidate(changed, config)


def test_candidate_source_prefix_detects_truncation_and_mutation() -> None:
    previous = b'{"candidate_id":"one"}\n'
    state = {
        "source_prefix_bytes": len(previous),
        "source_prefix_sha256": sha256_bytes(previous),
    }
    verify_source_prefix(previous + b'{"candidate_id":"two"}\n', state)
    with pytest.raises(ValueError, match="truncated"):
        verify_source_prefix(previous[:-1], state)
    with pytest.raises(ValueError, match="mutated"):
        verify_source_prefix(b"X" + previous[1:], state)


def test_resolution_prefix_detects_truncation_and_mutation() -> None:
    previous = b'{"resolution_status":"EXECUTED"}\n'
    state = {
        "resolution_prefix_bytes": len(previous),
        "resolution_prefix_sha256": sha256_bytes(previous),
    }
    verify_resolution_prefix(previous + b'{"resolution_status":"REJECTED"}\n', state)
    with pytest.raises(ValueError, match="truncated"):
        verify_resolution_prefix(previous[:-1], state)
    with pytest.raises(ValueError, match="mutated"):
        verify_resolution_prefix(b"X" + previous[1:], state)


def test_complete_target_matches_frozen_v9_execution() -> None:
    execution_module = load_frozen_execution(load_config())
    candidate = _normalized()
    frame = _ticks(
        [
            ("2026-07-20T00:00:00Z", 100.0, 100.2),
            ("2026-07-20T00:10:00Z", 104.3, 104.5),
            ("2026-07-20T01:00:00Z", 103.0, 103.2),
        ]
    )
    store = FrameTickStore(frame)
    observed_through = int(frame["tick_time_msc"].max())
    actual, rejection, waiting, _ = resolve_candidate_causally(
        _namespace(candidate), store, execution_module, _execution(), observed_through
    )
    frozen, frozen_rejection = execution_module.execute_candidate(
        _namespace(candidate), store, Quote, _execution()
    )
    assert rejection is None
    assert waiting is None
    assert frozen_rejection is None
    assert actual == frozen
    assert actual["exit_reason"] == "TARGET"
    assert actual["exit_price"] == pytest.approx(104.2)


def test_stop_uses_observed_executable_slippage_price() -> None:
    execution_module = load_frozen_execution(load_config())
    candidate = _normalized()
    frame = _ticks(
        [
            ("2026-07-20T00:00:00Z", 100.0, 100.2),
            ("2026-07-20T00:10:00Z", 98.0, 98.2),
        ]
    )
    actual, rejection, waiting, _ = resolve_candidate_causally(
        _namespace(candidate),
        FrameTickStore(frame),
        execution_module,
        _execution(),
        int(frame["tick_time_msc"].max()),
    )
    assert rejection is None
    assert waiting is None
    assert actual["exit_reason"] == "STOP_SLIPPAGE"
    assert actual["exit_price"] == pytest.approx(98.0)


def test_no_hit_waits_then_uses_side_correct_horizon_quote() -> None:
    execution_module = load_frozen_execution(load_config())
    candidate = _normalized(direction=-1)
    early = _ticks(
        [
            ("2026-07-20T00:00:00Z", 100.0, 100.2),
            ("2026-07-20T00:30:00Z", 99.8, 100.0),
        ]
    )
    outcome, rejection, waiting, _ = resolve_candidate_causally(
        _namespace(candidate),
        FrameTickStore(early),
        execution_module,
        _execution(),
        int(early["tick_time_msc"].max()),
    )
    assert outcome is None
    assert rejection is None
    assert waiting == "AWAITING_HORIZON_WINDOW"

    complete = _ticks(
        [
            ("2026-07-20T00:00:00Z", 100.0, 100.2),
            ("2026-07-20T00:30:00Z", 99.8, 100.0),
            ("2026-07-20T01:00:05Z", 99.5, 99.7),
        ]
    )
    outcome, rejection, waiting, _ = resolve_candidate_causally(
        _namespace(candidate),
        FrameTickStore(complete),
        execution_module,
        _execution(),
        int(complete["tick_time_msc"].max()),
    )
    assert rejection is None
    assert waiting is None
    assert outcome["exit_reason"] == "FIXED_HORIZON"
    assert outcome["entry_price"] == pytest.approx(100.0)
    assert outcome["exit_price"] == pytest.approx(99.7)
    assert outcome["horizon_delay_minutes"] == pytest.approx(5 / 60)


def test_missing_entry_and_horizon_are_not_rejected_before_their_cutoffs() -> None:
    execution_module = load_frozen_execution(load_config())
    candidate = _normalized()
    empty = FrameTickStore(pd.DataFrame(columns=["tick_time_msc", "bid", "ask"]))
    scheduled_ms = int(pd.Timestamp("2026-07-20T00:00:00Z").value // 1_000_000)
    _, rejection, waiting, _ = resolve_candidate_causally(
        _namespace(candidate), empty, execution_module, _execution(), scheduled_ms
    )
    assert rejection is None
    assert waiting == "AWAITING_ENTRY_WINDOW"
    _, rejection, waiting, _ = resolve_candidate_causally(
        _namespace(candidate),
        empty,
        execution_module,
        _execution(),
        scheduled_ms + 20 * 60_000,
    )
    assert rejection == "NO_TIMELY_ENTRY_QUOTE"
    assert waiting is None

    entry_only = _ticks([("2026-07-20T00:00:00Z", 100.0, 100.2)])
    horizon_cutoff = int(pd.Timestamp("2026-07-23T01:00:00Z").value // 1_000_000)
    _, rejection, waiting, _ = resolve_candidate_causally(
        _namespace(candidate),
        FrameTickStore(entry_only),
        execution_module,
        _execution(),
        horizon_cutoff - 1,
    )
    assert rejection is None
    assert waiting == "AWAITING_HORIZON_WINDOW"
    _, rejection, waiting, _ = resolve_candidate_causally(
        _namespace(candidate),
        FrameTickStore(entry_only),
        execution_module,
        _execution(),
        horizon_cutoff,
    )
    assert rejection == "NO_HORIZON_QUOTE"
    assert waiting is None


def test_process_candidates_applies_overlap_and_is_idempotent() -> None:
    execution_module = load_frozen_execution(load_config())
    first = _normalized(timestamp="2026-07-20T00:00:00Z", signal_atr=10.0)
    second = _normalized(timestamp="2026-07-20T00:30:00Z", signal_atr=10.0)
    frame = _ticks(
        [
            ("2026-07-20T00:00:00Z", 100.0, 100.2),
            ("2026-07-20T00:30:00Z", 100.1, 100.3),
            ("2026-07-20T01:00:00Z", 100.2, 100.4),
            ("2026-07-20T01:30:00Z", 100.3, 100.5),
        ]
    )
    rows, pending = process_candidates(
        [first, second],
        [],
        _historical(),
        frame,
        [],
        int(frame["tick_time_msc"].max()),
        execution_module,
        _execution(),
        pd.Timestamp("2026-07-20T02:00:00Z"),
    )
    assert pending == {}
    assert [row["resolution_status"] for row in rows] == ["EXECUTED", "REJECTED"]
    assert rows[1]["rejection_reason"] == "COMPONENT_POSITION_OVERLAP"

    replay, replay_pending = process_candidates(
        [first, second],
        rows,
        _historical(),
        frame,
        [],
        int(frame["tick_time_msc"].max()),
        execution_module,
        _execution(),
        pd.Timestamp("2026-07-20T02:05:00Z"),
    )
    assert replay == []
    assert replay_pending == {}


def test_process_candidates_applies_four_trade_component_daily_cap() -> None:
    execution_module = load_frozen_execution(load_config())
    candidates = [
        _normalized(
            timestamp=f"2026-07-20T{hour:02d}:00:00Z",
            signal_atr=10.0,
            hold_hours=0.1,
        )
        for hour in range(5)
    ]
    quote_rows: list[tuple[str, float, float]] = []
    for hour in range(5):
        quote_rows.append((f"2026-07-20T{hour:02d}:00:00Z", 100.0, 100.2))
        quote_rows.append((f"2026-07-20T{hour:02d}:06:00Z", 100.0, 100.2))
    frame = _ticks(quote_rows)
    rows, pending = process_candidates(
        candidates,
        [],
        _historical(),
        frame,
        [],
        int(frame["tick_time_msc"].max()),
        execution_module,
        _execution(),
        pd.Timestamp("2026-07-20T05:00:00Z"),
    )
    assert pending == {}
    assert sum(row["resolution_status"] == "EXECUTED" for row in rows) == 4
    assert rows[-1]["resolution_status"] == "REJECTED"
    assert rows[-1]["rejection_reason"] == "COMPONENT_DAILY_CAP"


def test_tick_snapshot_rejects_any_authority(tmp_path: Path) -> None:
    config = load_config()
    path = (
        tmp_path
        / "xau_prospective_1033669_Capital_ComMena_Demo_XAUUSD_ticks_20260720.csv"
    )
    fields = [
        "schema_version",
        "timestamp_utc",
        "tick_time_msc",
        "account_login",
        "account_server",
        "symbol",
        "bid",
        "ask",
        "spread_price",
        "dry_run",
        "trade_permission",
        "broker_action_allowed",
        "python_execution_authorized",
    ]
    values = [
        "xau_prospective_tick_v1",
        "2026.07.20 00:00:00.000Z",
        "1784505600000",
        "1033669",
        "Capital.ComMena-Demo",
        "XAUUSD",
        "100.0",
        "100.2",
        "0.2",
        "true",
        "true",
        "false",
        "false",
    ]
    path.write_text(",".join(fields) + "\n" + ",".join(values) + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match="authority enabled"):
        load_tick_snapshots([path], config)


def test_candidate_jsonl_requires_exact_v35_schema() -> None:
    record = _candidate_record()
    snapshot = (json.dumps(record, sort_keys=True) + "\n").encode("ascii")
    parsed = parse_candidate_snapshot(snapshot, load_config())
    assert len(parsed) == 1
    assert parsed[0]["candidate_fact_sha256"] == candidate_fact_sha256(record)
