from __future__ import annotations

import csv
import json
from pathlib import Path

import pandas as pd
import pytest

from ml.a3_meta_v1.broker_cost_calibration import (
    _boundary_quote,
    _tick_date,
    describe,
    grouped_spread_metrics,
    minimum_stop_distance,
    validate_contract,
)


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "config/ml/a3_ml_broker_cost_calibration_v1.json"


def _contract() -> dict:
    return json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))


def test_contract_is_research_only_and_accounts_are_not_independent() -> None:
    contract = _contract()
    validate_contract(contract)
    assert contract["research_controls"]["same_server_accounts_are_independent_samples"] is False
    assert contract["research_controls"]["strategy_parameter_selection_authorized"] is False
    assert contract["research_controls"]["model_training_authorized"] is False
    assert contract["authorization"]["broker_action_authorized"] is False


def test_contract_rejects_demo_authorization() -> None:
    contract = _contract()
    contract["authorization"]["python_demo_predictions_authorized"] = True
    with pytest.raises(ValueError, match="forbidden broker calibration authorization"):
        validate_contract(contract)


def test_boundary_quotes_ignore_account_identity_columns(tmp_path: Path) -> None:
    path = tmp_path / "ticks.csv"
    fields = [
        "dataset_version",
        "account_scope",
        "account_label",
        "time_msc",
        "bid",
        "ask",
        "spread_price",
        "spread_points",
    ]
    rows = [
        {
            "dataset_version": "v1",
            "account_scope": "1033669",
            "account_label": "A3",
            "time_msc": "1000",
            "bid": "100.0",
            "ask": "100.5",
            "spread_price": "0.5",
            "spread_points": "50.0",
        },
        {
            "dataset_version": "v1",
            "account_scope": "1033669",
            "account_label": "A3",
            "time_msc": "2000",
            "bid": "101.0",
            "ask": "101.7",
            "spread_price": "0.7",
            "spread_points": "70.0",
        },
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    assert _boundary_quote(path, first=True) == (
        "1000",
        "100.0",
        "100.5",
        "0.5",
        "50.0",
    )
    assert _boundary_quote(path, first=False) == (
        "2000",
        "101.0",
        "101.7",
        "0.7",
        "70.0",
    )


def test_grouped_spread_metrics_preserve_last_quote() -> None:
    ticks = pd.DataFrame(
        {
            "spread_price": [0.2, 0.4, 0.6, 1.0],
        }
    )
    groups = pd.Series([0, 0, 0, 1])
    result = grouped_spread_metrics(ticks, groups, "bucket", include_last=True)
    first = result.iloc[0]
    assert first["ticks"] == 3
    assert first["spread_median"] == pytest.approx(0.4)
    assert first["spread_last"] == pytest.approx(0.6)


def test_describe_uses_locked_quantile_names() -> None:
    result = describe(pd.Series([0.2, 0.4, 0.6, 0.8]), [0.0, 0.5, 0.9, 1.0])
    assert result["count"] == 4
    assert result["q0.5"] == pytest.approx(0.5)
    assert result["q0.9"] == pytest.approx(0.74)


def test_minimum_stop_distance_enforces_total_cost_fraction() -> None:
    assert minimum_stop_distance(0.5, 0.3, 0.15) == pytest.approx(5.3333333333)
    with pytest.raises(ValueError, match="invalid cost geometry"):
        minimum_stop_distance(0.5, 0.3, 0.0)


def test_tick_date_is_strict() -> None:
    assert _tick_date("XAUUSD_ticks_20260625.csv") == "2026-06-25"
    with pytest.raises(Exception, match="invalid C02 tick filename"):
        _tick_date("ticks.csv")
