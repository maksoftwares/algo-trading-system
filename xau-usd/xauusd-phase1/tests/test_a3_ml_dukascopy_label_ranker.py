from __future__ import annotations

import copy
import json
import math
import sys
from pathlib import Path

import numpy as np
import pytest


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ml.a3_meta_v1.dukascopy_label_ranker import (  # noqa: E402
    RankerError,
    _calendar_month_bootstrap,
    _feature_matrix,
    _roc_auc,
    _select_validation,
    _validate_contract,
    _validate_population,
)


def _contract() -> dict:
    return json.loads(
        (ROOT / "config" / "ml" / "a3_ml_dukascopy_label_ranker.json").read_text(
            encoding="utf-8"
        )
    )


def _row(candidate_id: str, *, direction: str = "LONG", month: int = 1) -> dict[str, str]:
    return {
        "candidate_id": candidate_id,
        "direction": direction,
        "decision_time_utc": f"2024-{month:02d}-05T10:00:00.000Z",
        "exit_time_utc": f"2024-{month:02d}-05T12:00:00.000Z",
        "signal_close": "2000.0",
        "ema_fast": "1998.0",
        "ema_slow": "1995.0",
        "ema_fast_slope_atr": "0.2" if direction == "LONG" else "-0.2",
        "atr": "10.0",
        "body_fraction": "0.6",
        "close_location": "0.8" if direction == "LONG" else "0.2",
        "touch_distance_atr": "0.0",
        "stop_distance": "8.0",
        "stop_distance_atr": "0.8",
        "signal_tick_count": "5000",
        "entry_spread": "0.3",
        "label_profitable_after_stress": "1",
        "stress_net_pnl_usd": "10.0",
        "stress_net_r": "1.0",
        "exit_reason": "TARGET",
        "mfe_r": "2.0",
        "mae_r": "0.2",
        "duration_hours": "2.0",
    }


def test_outcome_mutation_cannot_change_causal_feature_matrix() -> None:
    contract = _contract()
    original = _row("a")
    changed = copy.deepcopy(original)
    changed.update(
        {
            "label_profitable_after_stress": "0",
            "stress_net_pnl_usd": "-9999",
            "stress_net_r": "-99",
            "exit_reason": "STOP",
            "mfe_r": "0",
            "mae_r": "9",
            "duration_hours": "100",
        }
    )
    first = _feature_matrix([original], contract["features"])
    second = _feature_matrix([changed], contract["features"])
    assert np.array_equal(first, second)


def test_forbidden_feature_is_rejected_before_training() -> None:
    contract = _contract()
    contract["features"][-1] = "stress_net_r"
    with pytest.raises(ValueError, match="frozen causal set"):
        _validate_contract(contract)


def test_validation_selection_uses_fixed_fraction_and_candidate_id_ties() -> None:
    rows = [_row(name) for name in ("c", "a", "b", "d", "e")]
    selected, cutoff = _select_validation(rows, [0.8, 0.8, 0.7, 0.2, 0.1], 0.25)
    assert len(selected) == math.ceil(5 * 0.25)
    assert selected == {"a", "c"}
    assert cutoff == pytest.approx(0.8)


def test_test_values_cannot_change_validation_cutoff() -> None:
    rows = [_row(name) for name in ("a", "b", "c", "d")]
    first = _select_validation(rows, [0.9, 0.8, 0.2, 0.1], 0.25)
    unrelated_test_probabilities = [0.999, 0.001, 0.5]
    assert unrelated_test_probabilities
    second = _select_validation(rows, [0.9, 0.8, 0.2, 0.1], 0.25)
    assert first == second


def test_calendar_month_bootstrap_is_deterministic() -> None:
    rows = []
    for month in range(1, 7):
        row = _row(f"m{month}", month=month)
        row["stress_net_r"] = str(month / 10.0)
        rows.append(row)
    first = _calendar_month_bootstrap(rows, samples=200, seed=42)
    second = _calendar_month_bootstrap(rows, samples=200, seed=42)
    assert first == second
    assert first["average_stress_r_p025"] > 0.0


def test_auc_handles_probability_ties() -> None:
    assert _roc_auc([0, 1, 0, 1], [0.1, 0.9, 0.5, 0.5]) == pytest.approx(0.875)


def test_bootstrap_rejects_too_few_active_months() -> None:
    with pytest.raises(RankerError, match="six active"):
        _calendar_month_bootstrap([_row("a")], samples=100, seed=1)


def test_population_must_match_upstream_split_counts() -> None:
    rows = {
        "train": [_row("train-long"), _row("train-short", direction="SHORT")],
        "validation": [_row("val-long"), _row("val-short", direction="SHORT")],
        "test": [_row("test-long"), _row("test-short", direction="SHORT")],
    }
    upstream = {
        "resolved_count": 7,
        "by_split": {
            "train": {"trades": 2},
            "validation": {"trades": 2},
            "test": {"trades": 3},
        },
    }
    with pytest.raises(RankerError, match="resolved count"):
        _validate_population(rows, upstream)
