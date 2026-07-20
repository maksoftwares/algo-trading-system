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
    deterministic_id,
    load_config,
    parse_candidate_snapshot,
    process_candidates,
    resolve_candidate_causally,
    sha256_bytes,
    validate_candidate,
    verify_prefix,
)


def candidate_record(timestamp: str = "2026-07-20T00:00:00Z") -> dict[str, object]:
    config = load_config()
    source = config["source"]
    identity = config["frozen_identity"]
    execution = config["execution"]
    signal = pd.Timestamp(timestamp)
    contract = str(identity["source_contract_sha256"])
    specialist = str(source["specialist_id"])
    return {
        "schema_version": source["candidate_schema_version"],
        "record_type": "CANDIDATE",
        "candidate_id": deterministic_id("candidate", specialist, signal, contract),
        "state_id": deterministic_id("state", specialist, signal, contract),
        "specialist_id": specialist,
        "signal_time_utc": timestamp,
        "direction": "LONG",
        "stop_distance": 10.0,
        "target_r": execution["target_r"],
        "contract_hash": contract,
        "maximum_entry_gap_minutes": execution["maximum_entry_gap_minutes"],
        "maximum_spread_price": execution["maximum_spread_price"],
        "maximum_spread_r": execution["maximum_spread_r"],
        "ticket_cost_usd": execution["ticket_cost_usd"],
        "holding_cost_per_24h_usd": execution["holding_cost_per_24h_usd"],
        "stress_slippage_r": execution["stress_slippage_r"],
        "trade_permission": False,
        "broker_action_allowed": False,
        "python_execution_authorized": False,
    }


def normalized(timestamp: str = "2026-07-20T00:00:00Z") -> dict[str, object]:
    return validate_candidate(candidate_record(timestamp), load_config())


def ticks(rows: list[tuple[str, float, float]]) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "tick_time_msc": [
                int(pd.Timestamp(time).value // 1_000_000) for time, _, _ in rows
            ],
            "bid": [bid for _, bid, _ in rows],
            "ask": [ask for _, _, ask in rows],
        }
    )


def test_candidate_schema_identity_and_authority_are_exact() -> None:
    config = load_config()
    record = candidate_record()
    parsed = parse_candidate_snapshot(
        (json.dumps(record, sort_keys=True) + "\n").encode("ascii"), config
    )
    assert len(parsed) == 1
    changed = dict(record)
    changed["candidate_id"] = "wrong"
    with pytest.raises(ValueError, match="candidate ID"):
        validate_candidate(changed, config)
    changed = dict(record)
    changed["trade_permission"] = True
    with pytest.raises(ValueError, match="enables trade_permission"):
        validate_candidate(changed, config)
    changed = dict(record)
    changed["gross_r"] = 1.0
    with pytest.raises(ValueError, match="schema changed"):
        validate_candidate(changed, config)


def test_candidate_prefix_detects_truncation_and_mutation() -> None:
    previous = b'{"candidate_id":"one"}\n'
    state = {
        "source_prefix_bytes": len(previous),
        "source_prefix_sha256": sha256_bytes(previous),
    }
    verify_prefix(
        previous + b'{"candidate_id":"two"}\n',
        state,
        "source_prefix_bytes",
        "source_prefix_sha256",
        "candidate source",
    )
    with pytest.raises(ValueError, match="truncated"):
        verify_prefix(
            previous[:-1],
            state,
            "source_prefix_bytes",
            "source_prefix_sha256",
            "candidate source",
        )
    with pytest.raises(ValueError, match="mutated"):
        verify_prefix(
            b"X" + previous[1:],
            state,
            "source_prefix_bytes",
            "source_prefix_sha256",
            "candidate source",
        )


def test_target_and_stop_use_frozen_executable_prices() -> None:
    config = load_config()
    candidate = normalized()
    target_frame = ticks(
        [
            ("2026-07-20T00:00:00Z", 100.0, 100.2),
            ("2026-07-20T01:00:00Z", 120.5, 120.7),
        ]
    )
    probe = resolve_candidate_causally(
        candidate,
        FrameTickStore(target_frame),
        config,
        int(target_frame["tick_time_msc"].max()),
    )
    assert probe.outcome is not None
    assert probe.outcome["exit_reason"] == "TARGET"
    assert probe.outcome["exit_price"] == pytest.approx(120.2)

    stop_frame = ticks(
        [
            ("2026-07-20T00:00:00Z", 100.0, 100.2),
            ("2026-07-20T01:00:00Z", 89.0, 89.2),
        ]
    )
    probe = resolve_candidate_causally(
        candidate,
        FrameTickStore(stop_frame),
        config,
        int(stop_frame["tick_time_msc"].max()),
    )
    assert probe.outcome is not None
    assert probe.outcome["exit_reason"] == "STOP_SLIPPAGE"
    assert probe.outcome["exit_price"] == pytest.approx(89.0)


def test_no_hit_remains_open_without_an_invented_horizon() -> None:
    config = load_config()
    candidate = normalized()
    frame = ticks(
        [
            ("2026-07-20T00:00:00Z", 100.0, 100.2),
            ("2026-08-20T00:00:00Z", 105.0, 105.2),
        ]
    )
    probe = resolve_candidate_causally(
        candidate,
        FrameTickStore(frame),
        config,
        int(frame["tick_time_msc"].max()),
    )
    assert probe.outcome is None
    assert probe.rejection is None
    assert probe.waiting == "OPEN_POSITION"


def test_primary_policy_enforces_two_open_positions() -> None:
    config = load_config()
    candidates = [
        normalized("2026-07-20T00:00:00Z"),
        normalized("2026-07-21T00:00:00Z"),
        normalized("2026-07-22T00:00:00Z"),
    ]
    frame = ticks(
        [
            ("2026-07-20T00:00:00Z", 100.0, 100.2),
            ("2026-07-21T00:00:00Z", 100.0, 100.2),
            ("2026-07-22T00:00:00Z", 100.0, 100.2),
        ]
    )
    rows, pending = process_candidates(
        candidates,
        [],
        frame,
        [],
        int(frame["tick_time_msc"].max()),
        config,
        pd.Timestamp("2026-07-22T01:00:00Z"),
    )
    assert pending == {"OPEN_POSITION": 2}
    assert len(rows) == 1
    assert rows[0]["resolution_status"] == "REJECTED"
    assert rows[0]["rejection_reason"] == "MAX_CONCURRENT_POSITIONS"
    assert rows[0]["knowledge_time_utc"] == "2026-07-22T00:00:00Z"


def test_primary_policy_enforces_one_entry_per_utc_day() -> None:
    config = load_config()
    candidates = [
        normalized("2026-07-20T00:00:00Z"),
        normalized("2026-07-20T04:00:00Z"),
    ]
    frame = ticks(
        [
            ("2026-07-20T00:00:00Z", 100.0, 100.2),
            ("2026-07-20T04:00:00Z", 100.0, 100.2),
            ("2026-07-20T05:00:00Z", 120.5, 120.7),
        ]
    )
    rows, pending = process_candidates(
        candidates,
        [],
        frame,
        [],
        int(frame["tick_time_msc"].max()),
        config,
        pd.Timestamp("2026-07-20T05:00:00Z"),
    )
    assert pending == {}
    assert len(rows) == 2
    assert rows[0]["resolution_status"] == "EXECUTED"
    assert rows[1]["rejection_reason"] == "DAILY_ENTRY_CAP"
    assert rows[1]["knowledge_time_utc"] == "2026-07-20T04:00:00Z"


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
