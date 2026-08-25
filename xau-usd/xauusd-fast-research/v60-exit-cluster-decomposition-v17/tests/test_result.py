from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RESULT = ROOT / "outputs" / "RESULT.json"


def load_result() -> dict:
    return json.loads(
        RESULT.read_text(encoding="utf-8"),
        parse_constant=lambda value: (_ for _ in ()).throw(
            ValueError(f"Non-standard JSON constant: {value}")
        ),
    )


def test_result_is_read_only_and_replay_identity_is_exact() -> None:
    result = load_result()
    assert result["decision"] == "DIAGNOSTIC_SUPPORTS_TARGETED_PROTECTION_RESEARCH"
    assert result["deployment_authorized"] is False
    assert result["broker_action_authorized"] is False
    assert all(result["input_identity"].values())


def test_global_protection_tradeoff_is_recorded() -> None:
    result = load_result()
    endpoint = result["portfolio_attribution"]["endpoint"]
    protected = result["portfolio_attribution"]["protected"]
    assert endpoint["trades"] == protected["trades"] == 1390
    assert result["portfolio_attribution"]["protection_action_trades"] == 161
    assert protected["net_pnl_usd"] < endpoint["net_pnl_usd"]
    assert protected["profit_factor"] > endpoint["profit_factor"]
    assert protected["closed_drawdown_usd"] < endpoint["closed_drawdown_usd"]
    assert protected["net_to_closed_drawdown"] > endpoint["net_to_closed_drawdown"]
    assert result["monthly_downside"]["protected"]["negative_month_pnl_usd"] > result[
        "monthly_downside"
    ]["endpoint"]["negative_month_pnl_usd"]


def test_only_v7_supports_targeted_protection_research() -> None:
    result = load_result()
    eligible = [
        row["source_id"] for row in result["protection_eligibility"] if row["eligible"]
    ]
    assert eligible == ["V7_SWING_HEALTH"]
    v7 = next(
        row
        for row in result["protection_eligibility"]
        if row["source_id"] == "V7_SWING_HEALTH"
    )
    assert v7["protection_action_trades"] == 40
    assert v7["protection_delta_usd"] < 0.0
    assert v7["negative_historical_folds"] == 2


def test_cluster_control_is_rejected_by_long_history() -> None:
    result = load_result()
    assert not any(row["eligible"] for row in result["cluster_eligibility"])
    later = next(
        row for row in result["cluster_eligibility"] if row["cohort"] == "CLUSTER_LATER"
    )
    assert later["trades"] == 355
    assert later["net_pnl_usd"] > 1000.0
    assert later["profit_factor"] > 1.8
    assert later["negative_historical_folds"] == 0


def test_recent_and_feed_diagnostics_are_not_authorization_evidence() -> None:
    result = load_result()
    counts = result["july"]["feed_integrity"]["reconstructed_candidate_counts"]
    assert counts == {
        "R1_BOX": 0,
        "R1_PULLBACK": 0,
        "R2_DOWNTREND": 0,
        "R3_COMPRESSION": 0,
    }
    assert result["july"]["protected"]["net_pnl_usd"] < 0.0
    assert result["august_through_25"]["broker"]["net_pnl_usd"] < 0.0
    assert result["july"]["evidence_status"].startswith("EXPOSED")
    assert result["august_through_25"]["evidence_status"].startswith("EXPOSED")
