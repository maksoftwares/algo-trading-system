from __future__ import annotations

import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from pullback import (  # noqa: E402
    build_features,
    generate_candidates,
    load_config,
    policy_grid,
    resample_quotes,
    select_policy,
)


def test_registered_grid_has_exactly_240_policies() -> None:
    policies = policy_grid(load_config(ROOT))
    assert len(policies) == 240
    assert len({policy["policy_id"] for policy in policies}) == 240


def test_resampling_never_uses_a_future_quote() -> None:
    quotes = pd.DataFrame(
        {
            "tick_time_msc": [1_000, 4_900, 5_100, 9_900],
            "bid": [10.0, 11.0, 12.0, 13.0],
            "ask": [10.2, 11.2, 12.2, 13.2],
            "spread_price": [0.2] * 4,
        }
    )
    config = load_config(ROOT)
    bars = resample_quotes(quotes, config)
    assert bars["tick_time_msc"].tolist() == [5_000]
    assert bars["source_time_msc"].tolist() == [4_900]
    assert (bars["source_time_msc"] <= bars["tick_time_msc"]).all()


def test_feature_windows_end_before_or_at_decision() -> None:
    config = load_config(ROOT)
    config["feature"]["baseline_shift_samples"] = 3
    config["feature"]["baseline_samples"] = 4
    config["feature"]["baseline_minimum_samples"] = 2
    config["feature"]["impulse_start_lag_samples"] = 3
    config["feature"]["impulse_end_lag_samples"] = 2
    config["feature"]["pullback_end_lag_samples"] = 1
    bars = pd.DataFrame(
        {
            "tick_time_msc": np.arange(10, dtype=np.int64) * 5_000,
            "mid": np.arange(10, dtype=float),
            "bid": np.arange(10, dtype=float) - 0.1,
            "ask": np.arange(10, dtype=float) + 0.1,
            "spread_price": [0.2] * 10,
            "date_utc": ["2026-07-01"] * 10,
        }
    )
    features = build_features(bars, config)
    assert features.iloc[5]["impulse_dollars"] == 1.0
    assert features.iloc[5]["pullback_dollars"] == 1.0
    assert features.iloc[5]["resume_dollars"] == 1.0


def test_candidate_requires_impulse_pullback_and_resumption() -> None:
    config = load_config(ROOT)
    times = np.arange(400, dtype=np.int64) * 5_000 + 1_700_000_000_000
    mid = np.full(400, 2000.0)
    mid[:380] += np.tile([0.0, 0.02], 190)
    mid[395] = 2001.0
    mid[398] = 2000.5
    mid[399] = 2000.8
    bars = pd.DataFrame(
        {
            "tick_time_msc": times,
            "bid": mid - 0.15,
            "ask": mid + 0.15,
            "mid": mid,
            "spread_price": [0.30] * 400,
            "date_utc": ["2023-11-14"] * 400,
        }
    )
    features = build_features(bars, config)
    policy = {
        "impulse_scale_multiple": 4.0,
        "maximum_retracement_fraction": 0.75,
        "minimum_resume_scale_multiple": 0.5,
        "cooldown_minutes": 30,
    }
    candidates = generate_candidates(features, policy, config)
    assert not candidates.empty
    assert set(candidates.columns) >= {"candidate_side", "tick_time_msc"}
    assert (candidates["tick_time_msc"] <= times[-1]).all()


def test_selector_uses_density_facts_only() -> None:
    config = load_config(ROOT)
    rows = []
    for index, policy in enumerate(policy_grid(config)[:2]):
        rows.append(
            {
                **policy,
                "candidates_per_weekday": 1.0 + 0.1 * index,
                "active_day_share": 0.8,
                "minority_direction_share": 0.4,
                "first_half_candidates_per_weekday": 1.0,
                "second_half_candidates_per_weekday": 1.0,
            }
        )
    selected = select_policy(pd.DataFrame(rows), config)
    assert selected is not None
    assert selected["policy_id"] == rows[0]["policy_id"]


def test_empty_forward_source_produces_declared_candidate_schema() -> None:
    config = load_config(ROOT)
    candidates = generate_candidates(pd.DataFrame(), policy_grid(config)[0], config)
    assert candidates.empty
    assert "candidate_side" in candidates.columns


def test_contract_never_authorizes_execution_or_payment() -> None:
    controls = load_config(ROOT)["research_controls"]
    assert controls["outcome_blind_calibration"] is True
    for key in (
        "same_version_tuning_authorized",
        "model_training_authorized",
        "python_predictions_authorized",
        "ea_consumption_authorized",
        "demo_authorized",
        "live_authorized",
        "payment_authorized",
        "broker_action_authorized",
    ):
        assert controls[key] is False


def test_config_is_valid_json() -> None:
    path = ROOT / "config" / "capital_relative_spread_pullback_forward_v49.json"
    assert json.loads(path.read_text(encoding="utf-8"))["schema_version"].endswith(
        "v49"
    )
