from __future__ import annotations

import json
from pathlib import Path
import sys

import pandas as pd
import pytest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from portability import BASE, HIGH_VOL, ROTATION, select_candidate  # noqa: E402


def config() -> dict:
    return json.loads(
        (ROOT / "config" / "portability_v2.json").read_text(encoding="utf-8")
    )


def test_fixed_candidate_identity_and_parameters() -> None:
    candidate = config()["candidate"]
    assert candidate == {
        "strategy_id": ROTATION,
        "timeframe": "M5",
        "volatility_subtype": HIGH_VOL,
        "source_trade_count": 111,
        "source_stress_net_r": 10.609385661322035,
    }
    assert config()["rotation"] == {
        "excursion_z": 1.5,
        "target_band_z": 1.25,
        "stop_atr": 1.25,
        "max_hold_hours": 12,
    }


def test_candidate_selector_has_no_subtype_fallback() -> None:
    frame = pd.DataFrame(
        {
            "strategy_id": [ROTATION, ROTATION, ROTATION],
            "volatility_subtype": [HIGH_VOL, "LOW_VOL_CHOP", "MEDIUM_VOL_CHOP"],
            "signal_time": pd.to_datetime(
                ["2024-01-01T00:00:00Z", "2024-01-01T00:05:00Z", "2024-01-01T00:10:00Z"]
            ),
            "direction": ["LONG", "SHORT", "LONG"],
        }
    )
    result = select_candidate(frame)
    assert len(result) == 1
    assert result["volatility_subtype"].tolist() == [HIGH_VOL]


def test_candidate_selector_rejects_other_strategy() -> None:
    frame = pd.DataFrame(
        {
            "strategy_id": ["OTHER"],
            "volatility_subtype": [HIGH_VOL],
            "signal_time": pd.to_datetime(["2024-01-01T00:00:00Z"]),
            "direction": ["LONG"],
        }
    )
    with pytest.raises(ValueError):
        select_candidate(frame)


def test_source_subtype_row_is_exactly_the_selected_evidence() -> None:
    rows = pd.read_csv(ROOT.parent / "chop-v1" / "outputs" / "CHOP_SUBTYPE_RESULTS.csv")
    match = rows.loc[
        rows["strategy_id"].eq(ROTATION)
        & rows["timeframe"].eq("M5")
        & rows["subtype_dimension"].eq("volatility_subtype")
        & rows["subtype"].eq(HIGH_VOL)
    ]
    assert len(match) == 1
    assert int(match["trades"].iat[0]) == 111
    assert float(match["stress_net_r"].iat[0]) == pytest.approx(10.609385661322035)


def test_stage_gate_requires_winner_removal_and_cost_metrics() -> None:
    gate = config()["gates"]["exam"]
    metrics = {
        "trades": 12,
        "trades_per_source_day": 0.03,
        "profit_factor": 1.3,
        "stress_profit_factor": 1.2,
        "average_stress_r": 0.04,
        "stress_drawdown_r": 5.0,
        "top_winners_removed_stress_net_r": 0.1,
        "positive_active_year_share": 1.0,
    }
    passed, checks = BASE.evaluate_gate(metrics, gate)
    assert passed and all(checks.values())
    metrics["top_winners_removed_stress_net_r"] = -0.1
    assert not BASE.evaluate_gate(metrics, gate)[0]
