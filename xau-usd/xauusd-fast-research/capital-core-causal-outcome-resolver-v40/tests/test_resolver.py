from __future__ import annotations

import json
from pathlib import Path
import sys

import pandas as pd
import pytest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from resolver import (  # noqa: E402
    FrameTickStore,
    _source_candidate_id,
    _v28_candidate_id,
    _v29_candidate_id,
    load_config,
    parse_candidate_snapshot,
    process_v28,
    process_v29,
    process_v34,
    resolve_candidate_causally,
    sha256_bytes,
    utc_text,
    validate_candidate,
    verify_prefix,
)


def _v28_raw(
    timestamp: str = "2026-07-20T00:00:00Z", *, attempt: int = 11142
) -> dict[str, object]:
    config = load_config()
    signal = pd.Timestamp(timestamp)
    source_id = _source_candidate_id(attempt, signal)
    dependency = config["frozen_identity"]["v28"]["rule_dependency_sha256"]
    return {
        "candidate_id": _v28_candidate_id(source_id, dependency),
        "source_candidate_id": source_id,
        "specialist_id": "R2_DOWNTREND",
        "composite_id": "R2_DOWNTREND_FAILED_RALLY_DUAL_MODE_V1",
        "origin_attempt": attempt,
        "origin_variant_id": "TEST",
        "regime_owner": "DOWNTREND",
        "mechanic": "TEST",
        "signal_time_utc": timestamp,
        "scheduled_entry_time_utc": timestamp,
        "direction": "LONG",
        "direction_sign": 1,
        "signal_atr": 2.0,
        "stop_atr": 1.0,
        "hold_hours": 1.0,
        "parameters_json": "{}",
        "rule_dependency_sha256": dependency,
        "trade_permission": False,
        "broker_action_allowed": False,
        "python_execution_authorized": False,
    }


def _v29_raw(timestamp: str = "2026-07-20T00:00:00Z") -> dict[str, object]:
    config = load_config()
    signal = pd.Timestamp(timestamp)
    dependency = config["frozen_identity"]["v29"]["rule_dependency_sha256"]
    return {
        "candidate_id": _v29_candidate_id(signal, dependency),
        "specialist_id": "R1_PULLBACK_LONG_V2_M15_SESSION_09_15",
        "decision_time_utc": timestamp,
        "confirmation_bar_time_utc": utc_text(signal - pd.Timedelta(minutes=15)),
        "direction": "LONG",
        "signal_reason": "R1_H1_EMA_PULLBACK_LONG_M15",
        "regime": "UPTREND",
        "stop_points": 1000.0,
        "break_distance_atr": 0.2,
        "estimated_cost_r": 0.02,
        "spread_points": 20.0,
        "rule_dependency_sha256": dependency,
        "trade_permission": False,
        "broker_action_allowed": False,
        "python_execution_authorized": False,
    }


def _v34_raw(
    timestamp: str = "2026-07-20T00:00:00Z", *, attempt: int = 39888
) -> dict[str, object]:
    config = load_config()
    signal = pd.Timestamp(timestamp)
    dependency = config["frozen_identity"]["v34"]["rule_dependency_sha256"]
    return {
        "candidate_id": _source_candidate_id(attempt, signal),
        "component_priority": 1,
        "origin_attempt": attempt,
        "origin_variant_id": "TEST",
        "regime_owner": "CHOP",
        "mechanic": "TEST",
        "geometry_id": "EXTENDED",
        "signal_time_utc": timestamp,
        "scheduled_entry_time_utc": timestamp,
        "direction_sign": 1,
        "direction": "LONG",
        "signal_atr": 2.0,
        "stop_atr": 1.0,
        "target_r": 2.0,
        "hold_hours": 1.0,
        "source_feed": "CAPITAL_QUOTE_M5_V34",
        "economic_outcome_opened": False,
        "rule_dependency_sha256": dependency,
    }


def _ticks(rows: list[tuple[str, float, float]]) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "tick_time_msc": [
                int(pd.Timestamp(timestamp).value // 1_000_000)
                for timestamp, _, _ in rows
            ],
            "bid": [bid for _, bid, _ in rows],
            "ask": [ask for _, _, ask in rows],
        }
    )


def _records() -> list[dict[str, object]]:
    return [{"path": "test.csv", "prefix_bytes": 1, "prefix_sha256": "x"}]


def test_all_source_schemas_and_identities_are_fail_closed() -> None:
    config = load_config()
    for stream, raw in (("v28", _v28_raw()), ("v29", _v29_raw()), ("v34", _v34_raw())):
        normalized = validate_candidate(stream, raw, config)
        assert normalized["stream"] == stream
        changed = dict(raw)
        changed["gross_r"] = 1.0
        with pytest.raises(ValueError, match="schema changed"):
            validate_candidate(stream, changed, config)
    authority = _v29_raw()
    authority["broker_action_allowed"] = True
    with pytest.raises(ValueError, match="enables broker_action_allowed"):
        validate_candidate("v29", authority, config)


def test_candidate_snapshot_rejects_duplicate_ids() -> None:
    raw = _v28_raw()
    snapshot = ((json.dumps(raw) + "\n") * 2).encode("ascii")
    with pytest.raises(ValueError, match="duplicate IDs"):
        parse_candidate_snapshot("v28", snapshot, load_config())


def test_consumed_prefix_rejects_truncation_and_mutation() -> None:
    previous = b'{"candidate_id":"one"}\n'
    state = {
        "source_prefix_bytes": len(previous),
        "source_prefix_sha256": sha256_bytes(previous),
    }
    verify_prefix(
        previous + b"next\n",
        state,
        "source_prefix_bytes",
        "source_prefix_sha256",
        "source",
    )
    with pytest.raises(ValueError, match="truncated"):
        verify_prefix(
            previous[:-1],
            state,
            "source_prefix_bytes",
            "source_prefix_sha256",
            "source",
        )
    with pytest.raises(ValueError, match="mutated"):
        verify_prefix(
            b"X" + previous[1:],
            state,
            "source_prefix_bytes",
            "source_prefix_sha256",
            "source",
        )


def test_v28_uses_executable_stop_or_fixed_horizon() -> None:
    candidate = validate_candidate("v28", _v28_raw(), load_config())
    horizon = _ticks(
        [
            ("2026-07-20T00:00:00Z", 100.0, 100.2),
            ("2026-07-20T01:00:00Z", 100.5, 100.7),
        ]
    )
    probe = resolve_candidate_causally(
        candidate,
        FrameTickStore(horizon),
        load_config(),
        int(horizon["tick_time_msc"].max()),
    )
    assert probe.outcome is not None
    assert probe.outcome["exit_reason"] == "FIXED_HORIZON"
    assert probe.outcome["exit_price"] == pytest.approx(100.5)

    stopped = _ticks(
        [
            ("2026-07-20T00:00:00Z", 100.0, 100.2),
            ("2026-07-20T00:30:00Z", 98.0, 98.2),
        ]
    )
    probe = resolve_candidate_causally(
        candidate,
        FrameTickStore(stopped),
        load_config(),
        int(stopped["tick_time_msc"].max()),
    )
    assert probe.outcome is not None
    assert probe.outcome["exit_reason"] == "STOP_SLIPPAGE"
    assert probe.outcome["exit_price"] == pytest.approx(98.0)


def test_v34_target_is_locked_and_horizon_tick_is_not_preempted() -> None:
    candidate = validate_candidate("v34", _v34_raw(), load_config())
    ticks = _ticks(
        [
            ("2026-07-20T00:00:00Z", 100.0, 100.2),
            ("2026-07-20T00:10:00Z", 104.4, 104.6),
            ("2026-07-20T01:00:00Z", 103.0, 103.2),
        ]
    )
    probe = resolve_candidate_causally(
        candidate,
        FrameTickStore(ticks),
        load_config(),
        int(ticks["tick_time_msc"].max()),
    )
    assert probe.outcome is not None
    assert probe.outcome["exit_reason"] == "TARGET"
    assert probe.outcome["exit_price"] == pytest.approx(104.2)


def test_v29_has_no_invented_horizon_and_resolves_only_on_target() -> None:
    candidate = validate_candidate("v29", _v29_raw(), load_config())
    open_ticks = _ticks(
        [
            ("2026-07-20T00:00:00Z", 100.0, 100.2),
            ("2026-07-21T00:00:00Z", 101.0, 101.2),
        ]
    )
    probe = resolve_candidate_causally(
        candidate,
        FrameTickStore(open_ticks),
        load_config(),
        int(open_ticks["tick_time_msc"].max()),
    )
    assert probe.outcome is None
    assert probe.waiting == "OPEN_POSITION"

    closed_ticks = _ticks(
        [
            ("2026-07-20T00:00:00Z", 100.0, 100.2),
            ("2026-07-21T00:00:00Z", 120.5, 120.7),
        ]
    )
    probe = resolve_candidate_causally(
        candidate,
        FrameTickStore(closed_ticks),
        load_config(),
        int(closed_ticks["tick_time_msc"].max()),
    )
    assert probe.outcome is not None
    assert probe.outcome["exit_reason"] == "TARGET"
    assert probe.outcome["exit_price"] == pytest.approx(120.2)


def test_v28_component_overlap_is_terminal_and_idempotent() -> None:
    config = load_config()
    candidates = [
        validate_candidate("v28", _v28_raw("2026-07-20T00:00:00Z"), config),
        validate_candidate("v28", _v28_raw("2026-07-20T00:30:00Z"), config),
    ]
    ticks = _ticks(
        [
            ("2026-07-20T00:00:00Z", 100.0, 100.2),
            ("2026-07-20T00:30:00Z", 100.0, 100.2),
            ("2026-07-20T01:00:00Z", 100.0, 100.2),
            ("2026-07-20T01:30:00Z", 100.0, 100.2),
        ]
    )
    rows, pending = process_v28(
        candidates,
        [],
        ticks,
        _records(),
        int(ticks["tick_time_msc"].max()),
        config,
        pd.Timestamp("2026-07-20T02:00:00Z"),
    )
    assert pending == {}
    assert [row["resolution_status"] for row in rows] == ["EXECUTED", "REJECTED"]
    assert rows[1]["rejection_reason"] == "COMPONENT_POSITION_OVERLAP"
    replay, _ = process_v28(
        candidates,
        rows,
        ticks,
        _records(),
        int(ticks["tick_time_msc"].max()),
        config,
        pd.Timestamp("2026-07-20T02:05:00Z"),
    )
    assert replay == []


def test_v34_shared_position_policy_rejects_overlap() -> None:
    config = load_config()
    candidates = [
        validate_candidate("v34", _v34_raw("2026-07-20T00:00:00Z"), config),
        validate_candidate(
            "v34", _v34_raw("2026-07-20T00:05:00Z", attempt=40193), config
        ),
    ]
    ticks = _ticks(
        [
            ("2026-07-20T00:00:00Z", 100.0, 100.2),
            ("2026-07-20T00:05:00Z", 100.0, 100.2),
            ("2026-07-20T01:00:00Z", 100.0, 100.2),
            ("2026-07-20T01:05:00Z", 100.0, 100.2),
        ]
    )
    rows, pending = process_v34(
        candidates,
        [],
        ticks,
        _records(),
        int(ticks["tick_time_msc"].max()),
        config,
        pd.Timestamp("2026-07-20T02:00:00Z"),
    )
    assert pending == {}
    assert rows[0]["resolution_status"] == "EXECUTED"
    assert rows[1]["rejection_reason"] == "POSITION_OVERLAP"


def test_v29_reserves_eight_open_slots_before_rejecting_ninth() -> None:
    config = load_config()
    candidates = [
        validate_candidate("v29", _v29_raw(f"2026-07-20T00:{minute:02d}:00Z"), config)
        for minute in range(9)
    ]
    ticks = _ticks(
        [(f"2026-07-20T00:{minute:02d}:00Z", 100.0, 100.2) for minute in range(9)]
    )
    rows, pending = process_v29(
        candidates,
        [],
        ticks,
        _records(),
        int(ticks["tick_time_msc"].max()),
        config,
        pd.Timestamp("2026-07-20T00:10:00Z"),
    )
    assert pending == {"OPEN_POSITION": 8}
    assert len(rows) == 1
    assert rows[0]["resolution_status"] == "REJECTED"
    assert rows[0]["rejection_reason"] == "MAX_OPEN_POSITIONS"


def test_runtime_has_no_broker_execution_surface() -> None:
    text = (ROOT / "run_resolver.py").read_text(encoding="utf-8") + (
        ROOT / "src" / "resolver.py"
    ).read_text(encoding="utf-8")
    for token in (
        "MetaTrader5",
        "order_send",
        "order_check",
        "TRADE_ACTION_",
        "CTrade",
    ):
        assert token not in text
