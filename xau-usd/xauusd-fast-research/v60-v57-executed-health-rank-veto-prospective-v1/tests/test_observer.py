from __future__ import annotations

from datetime import UTC, datetime
import json
from pathlib import Path

from src.observer import broker_outcomes, build_snapshot


def deal(position_id, entry, time_msc, profit=0.0, magic=57):
    return {
        "magic": magic,
        "position_id": position_id,
        "entry": entry,
        "volume": 0.01,
        "time_msc": time_msc,
        "profit": profit,
        "commission": 0.0,
        "swap": 0.0,
        "fee": 0.0,
    }


def test_broker_outcome_requires_a_complete_position() -> None:
    state = {
        "positions": {
            "closed": {"source_id": "V57", "ticket": 1},
            "open": {"source_id": "V57", "ticket": 2},
        }
    }
    observed = broker_outcomes(
        state,
        [deal(1, 0, 1_000), deal(1, 1, 2_000, -3.6725), deal(2, 0, 1_000)],
        source_id="V57",
        magic=57,
        account_currency_per_usd=3.6725,
    )
    assert set(observed) == {"closed"}
    assert observed["closed"]["pnl_usd"] == -1.0


def test_broker_outcome_includes_exit_with_broker_magic() -> None:
    state = {"positions": {"closed": {"source_id": "V57", "ticket": 1}}}
    observed = broker_outcomes(
        state,
        [deal(1, 0, 1_000), deal(1, 1, 2_000, -3.6725, magic=0)],
        source_id="V57",
        magic=57,
        account_currency_per_usd=3.6725,
    )
    assert observed["closed"]["pnl_usd"] == -1.0


def test_wildcard_outcomes_use_each_source_magic() -> None:
    state = {
        "positions": {
            "a": {"source_id": "A", "ticket": 1},
            "b": {"source_id": "B", "ticket": 2},
        }
    }
    observed = broker_outcomes(
        state,
        [
            deal(1, 0, 1_000, magic=11),
            deal(1, 1, 2_000, -3.6725, magic=0),
            deal(2, 0, 1_000, magic=22),
            deal(2, 1, 2_000, 3.6725, magic=0),
        ],
        source_id="*",
        magic={"A": 11, "B": 22},
        account_currency_per_usd=3.6725,
    )
    assert observed["a"]["source_id"] == "A"
    assert observed["a"]["pnl_usd"] == -1.0
    assert observed["b"]["source_id"] == "B"
    assert observed["b"]["pnl_usd"] == 1.0


def test_snapshot_excludes_hypothetical_vetoes_from_future_health(tmp_path: Path) -> None:
    candidates = tmp_path / "candidates.jsonl"
    state_path = tmp_path / "state.json"
    rows = []
    positions = {}
    decisions = {}
    deals = []
    start_ms = 1_767_225_600_000
    for index in range(22):
        candidate_id = f"candidate-{index}"
        entry_ms = start_ms + index * 3_600_000
        rows.append(
            {
                "candidate_id": candidate_id,
                "event_id": f"event-{index}",
                "specialist_id": "V57",
                "scheduled_entry_time_utc": datetime.fromtimestamp(entry_ms / 1000, UTC).isoformat(),
            }
        )
        positions[candidate_id] = {"source_id": "V57", "ticket": index + 1}
        decisions[candidate_id] = {"reason": "SCORE_COMPLETE", "rank": 0.05}
        deals.extend(
            [
                deal(index + 1, 0, entry_ms + 1_000),
                deal(index + 1, 1, entry_ms + 2_000, -3.6725),
            ]
        )
    candidates.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")
    state_path.write_text(
        json.dumps({"positions": positions, "ml_topup": {"decisions": decisions}}),
        encoding="utf-8",
    )
    config = {
        "schema_version": "test",
        "lock": {
            "evidence_start_inclusive_utc": rows[20]["scheduled_entry_time_utc"],
            "policy": {
                "source_id": "V57",
                "lookback_closed_trades": 20,
                "maximum_prior_profit_factor_exclusive": 1.0,
                "maximum_causal_rank_exclusive": 0.1,
            },
        },
        "account": {"magic": 57, "account_currency_per_usd": 3.6725},
        "read_only_inputs": {
            "candidate_ledger": str(candidates),
            "portfolio_state": str(state_path),
        },
        "acceptance": {
            "minimum_elapsed_days": 0,
            "minimum_scored_executed_candidates": 2,
            "minimum_resolved_vetoes": 1,
            "maximum_veto_broker_profit_factor_exclusive": 0.8,
            "minimum_avoided_broker_pnl_usd_exclusive": 0.0,
        },
    }
    status, observed = build_snapshot(
        config, deals, now=datetime(2026, 2, 1, tzinfo=UTC)
    )
    assert observed[0]["would_veto"] is True
    assert observed[1]["prior_source_executed_count"] == 20
    assert observed[1]["prior_health_window_count"] == 20
    assert observed[1]["would_veto"] is True
    assert status["counts"]["resolved_vetoes"] == 2
    assert status["deployment_authorized"] is False
