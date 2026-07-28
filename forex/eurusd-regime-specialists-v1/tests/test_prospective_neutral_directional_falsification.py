from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from eurusd_regime_specialists.prospective_neutral_directional_falsification import (
    evaluate_directional_falsification,
    execute_opposite_side_counterfactual,
    load_config,
    paired_randomization_p_value,
)

PATH_HASH = "e" * 64


def _path(entry: pd.Timestamp, primary_side: str) -> dict:
    index = pd.date_range(entry, periods=144, freq="5min")
    if primary_side == "LONG":
        bid_high = 1.0020
        bid_low = 0.9995
    else:
        bid_high = 1.0005
        bid_low = 0.9980
    frame = pd.DataFrame(
        {
            "timestamp_utc": index,
            "bid_open": 1.00000,
            "bid_high": bid_high,
            "bid_low": bid_low,
            "bid_close": 1.00000,
            "ask_open": 1.00007,
            "ask_high": bid_high + 0.00007,
            "ask_low": bid_low + 0.00007,
            "ask_close": 1.00007,
        }
    )
    return {
        "frame": frame,
        "entry_time_utc": entry,
        "deadline_utc": entry + pd.Timedelta(hours=12),
        "path_evidence_sha256": PATH_HASH,
    }


def _trade(
    number: int,
    entry: pd.Timestamp,
    *,
    side: str,
    outcome_r: float,
) -> dict:
    return {
        "signal_id": f"{number:064x}",
        "status": "CLOSED",
        "entry_time_utc": entry,
        "exit_time_utc": entry,
        "side": side,
        "risk_pips": 10.0,
        "r": outcome_r,
        "extra_half_pip_stress_r": outcome_r - 0.05,
        "path_evidence_sha256": PATH_HASH,
    }


def _sample() -> tuple[pd.DataFrame, dict[str, dict]]:
    records: list[dict] = []
    paths: dict[str, dict] = {}
    outcomes = [1.5, -1.0] * 15
    for index, outcome in enumerate(outcomes, start=1):
        entry = (
            pd.Timestamp("2026-08-01T12:00:00Z")
            + pd.DateOffset(days=index * 12)
        )
        side = "LONG" if index % 2 else "SHORT"
        trade = _trade(index, entry, side=side, outcome_r=outcome)
        records.append(trade)
        paths[trade["signal_id"]] = _path(entry, side)
    return pd.DataFrame(records), paths


def test_counterfactual_uses_exact_same_time_risk_and_opposite_side() -> None:
    entry = pd.Timestamp("2026-08-07T12:50:00Z")
    primary = _trade(1, entry, side="LONG", outcome_r=1.5)
    result = execute_opposite_side_counterfactual(
        primary,
        _path(entry, "LONG"),
    )
    assert result["primary_side"] == "LONG"
    assert result["counterfactual_side"] == "SHORT"
    assert result["entry_time_utc"] == entry
    assert result["risk_pips"] == 10.0
    assert result["exit_reason"] == "STOP"
    assert result["r"] == pytest.approx(-1.01)
    assert result["broker_action_allowed"] is False


def test_stop_first_policy_applies_when_opposite_path_touches_both() -> None:
    entry = pd.Timestamp("2026-08-07T12:50:00Z")
    primary = _trade(1, entry, side="SHORT", outcome_r=1.5)
    path = _path(entry, "SHORT")
    path["frame"].loc[0, "bid_high"] = 1.0030
    path["frame"].loc[0, "ask_high"] = 1.00307
    path["frame"].loc[0, "bid_low"] = 0.9970
    path["frame"].loc[0, "ask_low"] = 0.99707
    result = execute_opposite_side_counterfactual(primary, path)
    assert result["counterfactual_side"] == "LONG"
    assert result["exit_reason"] == "STOP"
    assert result["r"] < 0


def test_paired_randomization_exact_and_monte_carlo_are_one_sided() -> None:
    exact = paired_randomization_p_value(
        np.asarray([1.0, 1.0]),
        exact_maximum_pairs=20,
        monte_carlo_sign_vectors=1000,
        seed=1,
    )
    assert exact["method"] == "EXACT_SIGN_ENUMERATION"
    assert exact["one_sided_p_value"] == pytest.approx(0.25)
    neutral = paired_randomization_p_value(
        np.zeros(4),
        exact_maximum_pairs=20,
        monte_carlo_sign_vectors=1000,
        seed=1,
    )
    assert neutral["one_sided_p_value"] == 1.0
    monte_carlo = paired_randomization_p_value(
        np.ones(30),
        exact_maximum_pairs=20,
        monte_carlo_sign_vectors=10000,
        seed=20260728,
    )
    assert monte_carlo["method"] == (
        "FIXED_SEED_MONTE_CARLO_SIGN_RANDOMIZATION"
    )
    assert monte_carlo["one_sided_p_value"] < 0.01


def test_frequency_is_not_a_directional_falsification_gate() -> None:
    cfg = load_config()
    assert cfg["frequency_policy"]["minimum_trades_per_day"] is None
    assert cfg["frequency_policy"][
        "frequency_is_reported_but_not_an_admission_gate"
    ]
    result = evaluate_directional_falsification(
        pd.DataFrame(columns=["status"]),
        {},
        evaluated_at_utc="2026-08-01T00:00:00Z",
    )
    assert result["frequency"]["admission_gate"] is False
    assert all("frequency" not in key for key in result["gate_results"])


def test_profitable_sparse_primary_survives_opposite_side_falsification() -> None:
    routed, paths = _sample()
    result = evaluate_directional_falsification(
        routed,
        paths,
        evaluated_at_utc="2027-07-29T12:00:00Z",
    )
    assert result["primary"]["trades"] == 30
    assert result["primary"]["profit_factor"] == pytest.approx(1.5)
    assert result["frequency"]["trades_per_elapsed_weekday"] < 1.0
    assert result["opposite_side_counterfactual"]["profit_factor"] == 0.0
    assert result["primary_minus_counterfactual"]["expectancy_r"] > 0
    assert result["paired_randomization"]["one_sided_p_value"] < 0.1
    assert all(result["gate_results"].values())
    assert result["directional_hypothesis_survived"] is True
    assert result["status"] == (
        "DIRECTIONAL_HYPOTHESIS_SURVIVES_FALSIFICATION_REVIEW"
    )
    assert result["research_review_allowed"] is True
    assert result["broker_action_allowed"] is False


def test_missing_path_rejects_mature_sample_without_retuning() -> None:
    routed, paths = _sample()
    paths.pop(str(routed.iloc[0]["signal_id"]))
    result = evaluate_directional_falsification(
        routed,
        paths,
        evaluated_at_utc="2027-07-29T12:00:00Z",
    )
    assert result["gate_results"]["all_closed_primary_paths"] is False
    assert result["directional_hypothesis_survived"] is False
    assert result["status"] == "DIRECTIONAL_HYPOTHESIS_REJECTED_NO_RETUNING"


def test_prestart_closed_trade_is_rejected() -> None:
    entry = pd.Timestamp("2026-07-28T12:00:00Z")
    trade = _trade(1, entry, side="LONG", outcome_r=1.5)
    with pytest.raises(ValueError, match="Pre-start"):
        evaluate_directional_falsification(
            pd.DataFrame([trade]),
            {trade["signal_id"]: _path(entry, "LONG")},
            evaluated_at_utc="2026-07-28T13:00:00Z",
        )
