from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime

from src.forward_residual_live_outcome_adjudicator import (
    CONFIG_PATH,
    build_summary,
    process,
    resolve_receipt,
    selection_parity,
    write_outputs,
)

ROOT = CONFIG_PATH.parents[1]
LOCK = (
    ROOT
    / "EURUSD_FORWARD_RESIDUAL_LIVE_OUTCOME_ADJUDICATOR_LOCK_2026_07_30.sha256.json"
)


def _config() -> dict:
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def _signal(
    day: str = "2026-09-01",
    side: str = "LONG",
) -> dict:
    return {
        "decision_id": f"EURUSD_FORWARD_RESIDUAL_LIVE_SIGNAL_V1|{day}",
        "campaign_id": "EURUSD_FORWARD_RESIDUAL_LIVE_SIGNAL_V1",
        "decision_date": day,
        "decision_time_utc": f"{day}T20:00:00Z",
        "published_at_utc": f"{day}T20:03:00Z",
        "status": "PUBLISHED_SIGNAL",
        "eligible_side": side,
        "eligibility_reason": "REGIME_SIDE_ADMITTED",
        "regime": "BROAD_EUR_UP",
        "training_days_before": 20,
        "context": {"strength_240": 0.8},
        "side_statistics_before": {
            "LONG": {"observations": 20},
            "SHORT": {"observations": 20},
        },
        "demo_order_authorized": False,
    }


def _receipt(
    day: str = "2026-09-01",
    side: str = "LONG",
) -> dict:
    entry = 1.14520 if side == "LONG" else 1.14513
    return {
        "receipt_id": (
            "EURUSD_FORWARD_RESIDUAL_MT5_SHADOW_BRIDGE_V1|"
            f"EURUSD_FORWARD_RESIDUAL_LIVE_SIGNAL_V1|{day}"
        ),
        "campaign_id": "EURUSD_FORWARD_RESIDUAL_MT5_SHADOW_BRIDGE_V1",
        "decision_id": f"EURUSD_FORWARD_RESIDUAL_LIVE_SIGNAL_V1|{day}",
        "decision_date": day,
        "publisher_status": "PUBLISHED_SIGNAL",
        "published_at_utc": f"{day}T20:03:00Z",
        "received_at_utc": f"{day}T20:04:00Z",
        "tick_time_utc": f"{day}T20:04:00Z",
        "status": "SHADOW_ENTRY_CAPTURED",
        "eligible_side": side,
        "regime": "BROAD_EUR_UP",
        "bid": 1.14513,
        "ask": 1.14520,
        "entry": entry,
        "stop": entry - 0.0008 if side == "LONG" else entry + 0.0008,
        "target": entry + 0.0012 if side == "LONG" else entry - 0.0012,
        "demo_order_authorized": False,
        "order_api_called": False,
        "position_mutation_attempted": False,
    }


def _tick(
    milliseconds: int,
    bid: float,
    ask: float,
) -> dict:
    return {
        "time_msc": milliseconds,
        "bid": bid,
        "ask": ask,
        "last": 0.0,
        "flags": 6,
    }


def test_long_target_resolves_from_unique_captured_tick() -> None:
    start = int(
        datetime(2026, 9, 1, 20, 4, tzinfo=UTC).timestamp() * 1000
    )
    ticks = [
        _tick(start + 123, 1.14513, 1.14520),
        _tick(start + 60_000, 1.14580, 1.14587),
        _tick(start + 120_000, 1.14640, 1.14647),
    ]
    outcome = resolve_receipt(_receipt(), ticks, _config())
    assert outcome["status"] == "RESOLVED"
    assert outcome["exit_reason"] == "TARGET"
    assert round(outcome["result_pips"], 10) == 12.0
    assert round(outcome["result_r"], 10) == 1.5
    assert round(outcome["pnl_usd"], 10) == 1.2
    assert outcome["entry_tick_match_count"] == 1


def test_short_stop_uses_first_executable_gap_ask() -> None:
    start = int(
        datetime(2026, 9, 1, 20, 4, tzinfo=UTC).timestamp() * 1000
    )
    ticks = [
        _tick(start + 123, 1.14513, 1.14520),
        _tick(start + 60_000, 1.14593, 1.14600),
    ]
    outcome = resolve_receipt(
        _receipt(side="SHORT"),
        ticks,
        _config(),
    )
    assert outcome["exit_reason"] == "STOP"
    assert round(outcome["result_pips"], 10) == -8.7
    assert round(outcome["pnl_usd"], 10) == -0.87


def test_ambiguous_entry_tick_is_invalid_not_imputed() -> None:
    start = int(
        datetime(2026, 9, 1, 20, 4, tzinfo=UTC).timestamp() * 1000
    )
    ticks = [
        _tick(start + 100, 1.14513, 1.14520),
        _tick(start + 200, 1.14513, 1.14520),
    ]
    outcome = resolve_receipt(_receipt(), ticks, _config())
    assert outcome["status"] == "INVALID_ENTRY_TICK_MATCH"
    assert outcome["result_r"] is None
    assert outcome["raw_tick_count"] == 2


def test_friday_receipt_is_cash_without_tick_query() -> None:
    signal = _signal(day="2026-09-04")
    receipt = _receipt(day="2026-09-04")

    def forbidden_provider(_start, _end):
        raise AssertionError("Friday market-closure receipt queried ticks")

    outcomes, _, summary, artifacts = process(
        [signal],
        [receipt],
        [],
        [],
        [],
        datetime(2026, 9, 5, 2, 20, tzinfo=UTC),
        forbidden_provider,
        _config(),
    )
    assert outcomes[0]["status"] == "CASH_MARKET_CLOSURE"
    assert artifacts == {}
    assert summary["resolved_live_outcomes"] == 0


def test_friday_publisher_cash_gets_terminal_parity_without_research_record() -> None:
    signal = _signal(day="2026-09-04", side="CASH")
    signal.update(
        {
            "status": "CASH_MARKET_CLOSURE",
            "eligible_side": "CASH",
            "eligibility_reason": "IMMUTABLE_CASH_MARKET_CLOSURE",
            "regime": None,
            "training_days_before": None,
        }
    )

    def forbidden_provider(_start, _end):
        raise AssertionError("Friday publisher cash queried ticks")

    outcomes, parity, summary, artifacts = process(
        [signal],
        [],
        [],
        [],
        [],
        datetime(2026, 9, 5, 2, 20, tzinfo=UTC),
        forbidden_provider,
        _config(),
    )
    assert outcomes == []
    assert len(parity) == 1
    assert parity[0]["parity_pass"] is True
    assert parity[0]["terminal_status"] is None
    assert parity[0]["comparisons"] == {
        "operational_cash_not_comparable": True
    }
    assert summary["selection_parity_rows"] == 1
    assert summary["pending_selection_parity"] == 0
    assert artifacts == {}


def test_selection_parity_compares_pre_outcome_and_terminal_state() -> None:
    signal = _signal()
    terminal = {
        "decision_date": "2026-09-01",
        "decision_time_utc": "2026.09.01 20:00:00",
        "status": "RESOLVED",
        "regime": "BROAD_EUR_UP",
        "eligible_side": "LONG",
        "eligibility_reason": "REGIME_SIDE_ADMITTED",
        "training_days_before": 20,
        "context": {"strength_240": 0.8},
        "side_statistics_before": {
            "LONG": {"observations": 20},
            "SHORT": {"observations": 20},
        },
    }
    parity = selection_parity(signal, terminal, _config())
    assert parity["parity_pass"] is True
    terminal["eligible_side"] = "SHORT"
    mismatch = selection_parity(signal, terminal, _config())
    assert mismatch["parity_pass"] is False
    assert mismatch["comparisons"]["eligible_side"] is False


def test_live_economic_gates_wait_only_for_mt5_parity_and_soak() -> None:
    outcomes = []
    parity_rows = []
    for index in range(50):
        pnl = 2.0 if index % 2 == 0 else -1.0
        outcomes.append(
            {
                "status": "RESOLVED",
                "pnl_usd": pnl,
                "stressed_pnl_usd": pnl - 0.1,
            }
        )
        parity_rows.append({"parity_pass": True})
    summary = build_summary(
        [{}] * 50,
        [{}] * 50,
        outcomes,
        parity_rows,
        _config(),
    )
    assert summary["win_rate"] == 0.5
    assert summary["payoff_ratio"] == 2.0
    assert summary["profit_factor"] == 2.0
    assert summary["selection_mismatches"] == 0
    assert summary["status"] == "WAITING_MT5_PARITY_AND_SOAK"
    assert summary["demo_order_authorized"] is False


def test_outcome_and_raw_tick_artifacts_are_append_only(tmp_path) -> None:
    outcomes = [
        {
            "campaign_id": "EURUSD_FORWARD_RESIDUAL_LIVE_OUTCOME_V1",
            "decision_id": "signal-1",
            "status": "RESOLVED",
            "demo_order_authorized": False,
        }
    ]
    parity = [
        {
            "campaign_id": "EURUSD_FORWARD_RESIDUAL_LIVE_OUTCOME_V1",
            "decision_id": "signal-1",
            "parity_pass": True,
        }
    ]
    summary = {"status": "WAITING", "resolved_live_outcomes": 1,
               "invalid_outcomes": 0, "selection_mismatches": 0,
               "profit_factor": 1.2, "stressed_profit_factor": 1.1,
               "net_pnl_usd": 1.0}
    raw = {"abc.json": b"[]\n"}
    write_outputs(outcomes, parity, summary, raw, tmp_path)
    mutated = json.loads(json.dumps(outcomes))
    mutated[0]["status"] = "STOP"
    try:
        write_outputs(mutated, parity, summary, raw, tmp_path)
    except ValueError as error:
        assert "mutation refused" in str(error)
    else:
        raise AssertionError("live outcome was mutated")


def test_contract_rejects_research_pnl_and_order_paths() -> None:
    config = _config()
    assert config["demo_order_authorized"] is False
    assert "NO_RESEARCH_ENTRY_PNL_SUBSTITUTION" in config["prohibitions"]
    assert "NO_FRIDAY_20UTC_ENTRY" in config["prohibitions"]
    assert "NO_ORDER_SEND" in config["prohibitions"]


def test_live_outcome_lock_matches_every_frozen_file() -> None:
    lock = json.loads(LOCK.read_text(encoding="utf-8"))
    assert lock["locked_before_forward_floor"] is True
    assert lock["locked_with_zero_live_signals"] is True
    assert lock["locked_with_zero_mt5_receipts"] is True
    assert lock["locked_with_zero_live_outcomes"] is True
    assert lock["historical_backfill_allowed"] is False
    assert lock["demo_order_authorized"] is False
    for relative, expected in lock["files"].items():
        actual = hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()
        assert actual == expected, relative
