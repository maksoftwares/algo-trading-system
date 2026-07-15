from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from ml.a3_meta_v1.external_specialist_campaign import (
    _cftc_direction,
    _economic_gates,
    _macro_direction,
)


ROOT = Path(__file__).resolve().parents[1]
MACRO = ROOT / "config/ml/a3_ml_macro_repricing_specialists_v1.json"
CFTC = ROOT / "config/ml/a3_ml_cftc_positioning_specialists_v1.json"


def test_macro_directions_follow_frozen_economic_signs() -> None:
    contract = json.loads(MACRO.read_text(encoding="utf-8"))
    row = pd.Series(
        {
            "macro_staleness_days": 1.0,
            "real_yield_10y_change_1": 0.10,
            "real_yield_10y_change_5": 0.20,
            "nominal_yield_10y_change_5": 0.35,
            "broad_usd_index_change_5": 0.60,
        }
    )
    assert _macro_direction(row, "REAL_YIELD_SHOCK", contract["signal"]) == "SHORT"
    assert _macro_direction(row, "YIELD_USD_AGREEMENT", contract["signal"]) == "SHORT"
    row["broad_usd_index_change_5"] = -0.20
    assert _macro_direction(row, "INFLATION_REPRICING", contract["signal"]) == "LONG"


def test_stale_macro_is_rejected() -> None:
    contract = json.loads(MACRO.read_text(encoding="utf-8"))
    row = pd.Series(
        {
            "macro_staleness_days": 5.0,
            "real_yield_10y_change_1": -0.20,
            "real_yield_10y_change_5": -0.20,
            "nominal_yield_10y_change_5": 0.0,
            "broad_usd_index_change_5": -1.0,
        }
    )
    assert _macro_direction(row, "REAL_YIELD_SHOCK", contract["signal"]) is None


def test_cftc_trend_and_crowding_have_distinct_directions() -> None:
    contract = json.loads(CFTC.read_text(encoding="utf-8"))
    row = pd.Series(
        {
            "cot_staleness_days": 2.0,
            "atr": 2.0,
            "xau_return_60m_price": 0.60,
            "cot_managed_money_net_share_change_1": 0.02,
            "cot_managed_money_net_share_z52": -1.8,
            "cot_producer_net_share_change_1": 0.02,
        }
    )
    assert _cftc_direction(row, "COT_TREND_CONFIRM", contract["signal"]) == "LONG"
    assert _cftc_direction(row, "COT_CROWDED_REVERSAL", contract["signal"]) == "LONG"
    assert _cftc_direction(row, "COT_PRODUCER_CONFIRM", contract["signal"]) == "LONG"


def test_segment_gate_requires_robust_economics() -> None:
    gate = json.loads(MACRO.read_text(encoding="utf-8"))["validation_gates"]
    metrics = {
        "trades": 100,
        "trades_per_source_day": 0.5,
        "stress_profit_factor": 1.14,
        "average_stress_r": 0.05,
        "positive_month_share": 0.60,
        "maximum_closed_drawdown_r": 10.0,
        "top10_winners_removed_net_r": 1.0,
    }
    checks = _economic_gates(metrics, gate)
    assert not checks["stress_profit_factor"]
    metrics["stress_profit_factor"] = 1.20
    assert all(_economic_gates(metrics, gate).values())


def test_contracts_keep_later_windows_firewalled() -> None:
    for path in (MACRO, CFTC):
        contract = json.loads(path.read_text(encoding="utf-8"))
        authorization = contract["authorization"]
        assert authorization["validation_requires_train_family_pass"]
        assert authorization["internal_test_requires_validation_pass"]
        assert authorization["exam_requires_internal_test_pass"]
        assert not authorization["python_demo_predictions_authorized"]
