from __future__ import annotations

from pathlib import Path
import sys

import pandas as pd
import pytest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from router_forward import (  # noqa: E402
    load_config,
    load_frozen,
    route_candidate,
    route_stats,
    validate_resolution_rows,
    verify_named_prefix,
)


def _historical() -> pd.DataFrame:
    return pd.DataFrame(columns=["attempt_no", "exit_time", "stress_net_r"])


def _resolution(
    index: int,
    *,
    stress: float = -0.6,
    status: str = "EXECUTED",
    knowledge: str | None = None,
) -> dict[str, object]:
    exit_time = pd.Timestamp("2026-07-10T00:00:00Z") + pd.Timedelta(days=index)
    knowledge_time = exit_time if knowledge is None else pd.Timestamp(knowledge)
    row: dict[str, object] = {
        "candidate_id": f"candidate-{index}",
        "origin_attempt": 23925,
        "resolution_status": status,
        "broker_action_authorized": False,
    }
    if status == "EXECUTED":
        row.update(
            {
                "entry_time_utc": (exit_time - pd.Timedelta(hours=1)).isoformat(),
                "exit_time_utc": exit_time.isoformat(),
                "knowledge_time_utc": knowledge_time.isoformat(),
                "stress_net_r": stress,
            }
        )
    return row


def _candidate() -> dict[str, object]:
    return {
        "candidate_id": "future-candidate",
        "candidate_fact_sha256": "a" * 64,
        "origin_attempt": 23925,
        "signal_time_utc": "2026-07-20T00:00:00Z",
        "scheduled_entry_time_utc": "2026-07-20T00:00:00Z",
        "signal_time": pd.Timestamp("2026-07-20T00:00:00Z"),
        "scheduled_entry_time": pd.Timestamp("2026-07-20T00:00:00Z"),
        "direction": "LONG",
        "direction_sign": 1,
    }


def test_cold_start_uses_frozen_half_weight() -> None:
    frozen = load_frozen(load_config())
    multiplier, reason, stats, _, prospective = route_stats(
        23925,
        pd.Timestamp("2026-07-20T00:00:00Z"),
        _historical(),
        [],
        frozen,
    )
    assert multiplier == pytest.approx(0.5)
    assert reason == "COLD_START"
    assert stats.count == 0
    assert prospective == 0


def test_five_causally_known_losses_trigger_frozen_weak_weight() -> None:
    config = load_config()
    frozen = load_frozen(config)
    rows = validate_resolution_rows([_resolution(index) for index in range(5)], config)
    multiplier, reason, stats, _, prospective = route_stats(
        23925,
        pd.Timestamp("2026-07-20T00:00:00Z"),
        _historical(),
        rows,
        frozen,
    )
    assert stats.count == 5
    assert stats.drawdown_r == pytest.approx(3.0)
    assert multiplier == pytest.approx(0.25)
    assert reason == "WEAK"
    assert prospective == 5


def test_future_or_equal_knowledge_time_is_strictly_excluded() -> None:
    config = load_config()
    frozen = load_frozen(config)
    rows = validate_resolution_rows(
        [
            _resolution(0, knowledge="2026-07-20T00:00:00Z"),
            _resolution(1, knowledge="2026-07-20T00:00:01Z"),
        ],
        config,
    )
    _, _, stats, _, prospective = route_stats(
        23925,
        pd.Timestamp("2026-07-20T00:00:00Z"),
        _historical(),
        rows,
        frozen,
    )
    assert stats.count == 0
    assert prospective == 0


def test_rejected_component_candidate_never_enters_history() -> None:
    config = load_config()
    frozen = load_frozen(config)
    rows = validate_resolution_rows([_resolution(0, status="REJECTED")], config)
    _, _, stats, _, prospective = route_stats(
        23925,
        pd.Timestamp("2026-07-20T00:00:00Z"),
        _historical(),
        rows,
        frozen,
    )
    assert stats.count == 0
    assert prospective == 0


def test_route_output_contains_no_candidate_outcome_or_authority() -> None:
    frozen = load_frozen(load_config())
    route = route_candidate(_candidate(), _historical(), [], frozen, "contract-sha")
    assert route["risk_weight"] == pytest.approx(0.5)
    assert route["candidate_outcome_attached"] is False
    assert route["aggregate_economics_opened"] is False
    assert route["broker_action_authorized"] is False
    assert "stress_net_r" not in route
    assert "gross_r" not in route


def test_resolution_knowledge_cannot_precede_exit() -> None:
    config = load_config()
    row = _resolution(0, knowledge="2026-07-01T00:00:00Z")
    with pytest.raises(ValueError, match="known before its exit"):
        validate_resolution_rows([row], config)


def test_append_only_prefix_rejects_mutation_and_truncation() -> None:
    payload = b'{"candidate_id":"one"}\n'
    state = {
        "route_prefix_bytes": len(payload),
        "route_prefix_sha256": __import__("hashlib").sha256(payload).hexdigest(),
    }
    verify_named_prefix(payload + b"next\n", state, "route")
    with pytest.raises(ValueError, match="truncated"):
        verify_named_prefix(payload[:-1], state, "route")
    with pytest.raises(ValueError, match="mutated"):
        verify_named_prefix(b"X" + payload[1:], state, "route")
