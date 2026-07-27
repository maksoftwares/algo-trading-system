from __future__ import annotations

import json
from pathlib import Path


PACKAGE = Path(__file__).resolve().parents[1]
OUTPUT = PACKAGE / "outputs"


def load(name: str) -> dict:
    return json.loads((OUTPUT / name).read_text(encoding="utf-8"))


def test_legacy_ready_label_is_superseded() -> None:
    audit = load("AUDIT.json")
    assert audit["verdict"] == "RESEARCH_WATCHLIST"
    assert audit["controlled_shadow_ready"] is False
    assert audit["controlled_demo_ready"] is False
    assert audit["live_ready"] is False


def test_headline_metrics_reproduce() -> None:
    metrics = load("AUDIT.json")["metrics"]["portfolio"]
    assert metrics["trades"] == 697
    assert abs(metrics["net_pnl_usd"] - 119.42) < 1e-9
    assert abs(metrics["profit_factor"] - 1.307490279887736) < 1e-12
    assert abs(metrics["maximum_closed_trade_drawdown_usd"] - 28.45) < 1e-9


def test_overlay_is_same_opportunity_sizing() -> None:
    audit = load("AUDIT.json")
    overlay = audit["metrics"]["overlay_decomposition"]
    assert overlay["overlay_trade_count"] == 120
    assert overlay["same_entry_incremental_overlay"]["trades"] == 120
    assert audit["source_safety"]["trend_overlay_implementation"] is True
    assert audit["source_safety"]["trend_overlay_is_independent_entry"] is False
    assert (
        audit["acceptance_gates"]["no_duplicate_or_same_opportunity_stacking"][
            "status"
        ]
        == "FAIL"
    )


def test_shared_account_and_control_safety_are_not_overclaimed() -> None:
    audit = load("AUDIT.json")
    safety = audit["source_safety"]
    assert safety["control_demo_rejected_during_init"] is False
    assert safety["control_time_exit_checks_demo_mode"] is False
    assert safety["control_position_lookup_iterates_magic_owned_positions"] is False
    assert safety["shared_account_floating_drawdown_guard"] is False
    assert (
        audit["acceptance_gates"]["exact_combined_mt5_strategy_tester_parity"][
            "status"
        ]
        == "FAIL"
    )


def test_data_gap_map_preserves_quarantine_and_empty_broker_h1() -> None:
    coverage = load("DATA_COVERAGE_MANIFEST.json")
    assert coverage["broker_h1"]["files"] == 0
    assert coverage["broker_h1"]["status"] == "EMPTY_NO_BROKER_H1_EVIDENCE"
    quarantine = coverage["october_2024_quarantine"]
    assert quarantine["missing_frozen_month"] == "2024-10"
    assert quarantine["repair_status"] == "UNREPAIRED_EXPLICIT_QUARANTINE"
    assert coverage["audusd_intraday_status"].startswith("NOT_PRESENT")
