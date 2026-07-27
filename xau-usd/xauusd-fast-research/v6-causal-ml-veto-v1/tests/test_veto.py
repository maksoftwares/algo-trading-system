from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from src.veto import (
    annual_split,
    build_feature_matrix,
    day_equal_sample_weights,
    probability_cutoff,
    trade_metrics,
    validate_feature_contract,
    verify_sources,
)


def feature_config():
    return {
        "features": {
            "numeric": [
                "speed",
                "flow",
                "imb",
                "activity",
                "spr",
                "eff",
                "adv_pre",
                "align",
                "score",
                "pre2h",
                "slope",
                "log_stop",
            ],
            "derived": ["direction_long", "utc_time_sin", "utc_time_cos"],
            "regimes": [
                "R0_SHOCK",
                "R1_UPTREND",
                "R2_DOWNTREND",
                "R3_COMPRESSION",
                "R4_CHOP",
                "R5_TRANSITION",
            ],
        }
    }


def feature_rows():
    return pd.DataFrame(
        {
            "scan_time": pd.to_datetime(
                ["2025-01-01 06:30", "2025-01-01 18:30"], utc=True
            ),
            "long": [True, False],
            "stop": [10.0, 20.0],
            "regime": ["R1_UPTREND", "R2_DOWNTREND"],
            "speed": [1.0, 2.0],
            "flow": [1.0, -1.0],
            "imb": [0.2, -0.2],
            "activity": [10.0, 12.0],
            "spr": [0.01, 0.02],
            "eff": [0.5, 0.4],
            "adv_pre": [0.1, 0.2],
            "align": [1.0, -1.0],
            "score": [0.2, 0.3],
            "pre2h": [-1.0, 1.0],
            "slope": [2.0, -2.0],
        }
    )


def test_feature_contract_rejects_outcome_columns():
    config = feature_config()
    config["features"]["numeric"].append("future_pnl")
    with pytest.raises(ValueError, match="Outcome-derived"):
        validate_feature_contract(config)


def test_feature_matrix_contains_only_locked_finite_features():
    config = feature_config()
    matrix = build_feature_matrix(feature_rows(), config)
    assert matrix.columns.tolist() == validate_feature_contract(config)
    assert np.isfinite(matrix.to_numpy()).all()
    assert "fee_stress_pnl_usd" not in matrix


def test_annual_split_purges_training_exits_and_uses_previous_year():
    corpus = pd.DataFrame(
        {
            "entry_time": pd.to_datetime(
                [
                    "2020-01-01",
                    "2020-12-31",
                    "2021-01-01",
                    "2021-12-31",
                    "2022-01-01",
                ],
                utc=True,
            ),
            "exit_time": pd.to_datetime(
                [
                    "2020-01-02",
                    "2020-12-30",
                    "2021-01-02",
                    "2021-12-28",
                    "2022-01-02",
                ],
                utc=True,
            ),
        }
    )
    train, calibration = annual_split(corpus, 2022, 48)
    assert train["exit_time"].max() < pd.Timestamp("2020-12-30", tz="UTC")
    assert calibration["entry_time"].dt.year.unique().tolist() == [2021]
    assert calibration["exit_time"].max() < pd.Timestamp("2021-12-30", tz="UTC")


def test_probability_cutoff_retains_top_sixty_percent():
    probabilities = np.arange(10, dtype=float) / 10.0
    cutoff = probability_cutoff(probabilities, 0.60)
    assert cutoff == pytest.approx(np.quantile(probabilities, 0.40))
    assert int((probabilities >= cutoff).sum()) == 6


def test_day_equal_weights_give_each_day_same_total():
    frame = pd.DataFrame(
        {
            "scan_time": pd.to_datetime(
                ["2025-01-01"] * 2 + ["2025-01-02"] * 4, utc=True
            )
        }
    )
    weights = day_equal_sample_weights(frame)
    totals = pd.Series(weights).groupby(frame["scan_time"].dt.day).sum()
    assert totals.iloc[0] == pytest.approx(totals.iloc[1])
    assert weights.mean() == pytest.approx(1.0)


def test_trade_metrics_removes_largest_winners():
    frame = pd.DataFrame(
        {
            "exit_time": pd.to_datetime(
                ["2025-01-01", "2025-01-02", "2025-01-03"], utc=True
            ),
            "trade_id": ["a", "b", "c"],
            "fee_stress_pnl_usd": [10.0, 2.0, -3.0],
        }
    )
    metrics = trade_metrics(frame, 1)
    assert metrics["stress_net_usd"] == pytest.approx(9.0)
    assert metrics["winner_removed_stress_net_usd"] == pytest.approx(-1.0)


def test_verify_sources_fails_closed(tmp_path: Path):
    source = tmp_path / "source.txt"
    source.write_text("changed", encoding="utf-8")
    config = {
        "sources": {
            "source": {"path": str(source), "sha256": "0" * 64}
        }
    }
    with pytest.raises(ValueError, match="Locked source drift"):
        verify_sources(config)
