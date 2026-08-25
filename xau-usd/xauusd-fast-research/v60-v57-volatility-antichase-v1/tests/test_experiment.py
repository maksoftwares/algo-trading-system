from __future__ import annotations

from pathlib import Path
import sys

import pandas as pd
import pytest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.experiment import (
    august_comparison,
    closed_metrics,
    crossfeed_comparison,
    policy_mask,
)


RULE = {
    "source_id": "V57_BREAK_SWING_H4ADX_HIGH",
    "direction": "LONG",
    "maximum_causal_rank_exclusive": 0.1,
    "minimum_atr_ratio_inclusive": 1.2,
    "maximum_distance_to_24h_high_atr_exclusive": 1.0,
}


def row(**changes):
    value = {
        "execution_source_id": "V57_BREAK_SWING_H4ADX_HIGH",
        "direction": "LONG",
        "rank": 0.09,
        "atr_ratio": 1.2,
        "dist_hi_24h": 0.99,
    }
    value.update(changes)
    return value


def test_policy_uses_strict_rank_and_extreme_boundaries() -> None:
    frame = pd.DataFrame(
        [
            row(),
            row(rank=0.1),
            row(atr_ratio=1.199999),
            row(dist_hi_24h=1.0),
            row(direction="SHORT"),
        ]
    )
    assert policy_mask(frame, RULE).tolist() == [True, False, False, False, False]


def test_missing_feature_retains_trade() -> None:
    frame = pd.DataFrame([row(rank=None), row(atr_ratio=float("nan"))])
    assert policy_mask(frame, RULE).tolist() == [False, False]


def test_closed_metrics_include_zero_start_drawdown() -> None:
    result = closed_metrics([10.0, -15.0, 4.0])
    assert result["net_pnl_usd"] == pytest.approx(-1.0)
    assert result["profit_factor"] == pytest.approx(14.0 / 15.0)
    assert result["closed_drawdown_usd"] == pytest.approx(15.0)


def test_august_adapter_uses_causal_rank() -> None:
    broker = pd.DataFrame(
        [
            {
                "candidate_id": "candidate",
                "entry_time_utc": "2026-08-10T00:00:00Z",
                "broker_exit_time_utc": "2026-08-10T01:00:00Z",
                "baseline_executed": True,
                "broker_outcome_resolved": True,
                "broker_pnl_usd": -12.0,
                "causal_rank": 0.09,
                "prior_source_executed_count": 50,
            }
        ]
    )
    features = pd.DataFrame([{"candidate_id": "candidate", **row()}])
    rule = {**RULE, "minimum_prior_source_closed_trades": 50}
    result, audit = august_comparison(broker, features, rule)
    assert result["vetoes"] == 1
    assert result["challenger"]["trades"] == 0
    assert result["challenger"]["net_pnl_usd"] == 0.0
    assert bool(audit.loc[0, "would_veto"])


def test_crossfeed_requires_selected_trade_coverage() -> None:
    frame = pd.DataFrame(
        [
            {
                "trade_id": "selected",
                "dukascopy_covered": True,
                "runtime_entry_time_utc": "2026-01-01T00:00:00Z",
                "runtime_exit_time_ms": 2,
                "dukascopy_spread_only_pnl_usd": -5.0,
            },
            {
                "trade_id": "retained",
                "dukascopy_covered": True,
                "runtime_entry_time_utc": "2026-01-01T00:00:00Z",
                "runtime_exit_time_ms": 3,
                "dukascopy_spread_only_pnl_usd": 2.0,
            },
        ]
    )
    result = crossfeed_comparison(frame, {"selected"})
    assert result["delta_net_pnl_usd"] == 5.0
    assert result["veto_cohort"]["profit_factor"] == 0.0
    with pytest.raises(ValueError, match="lacks selected trades"):
        crossfeed_comparison(frame, {"missing"})
