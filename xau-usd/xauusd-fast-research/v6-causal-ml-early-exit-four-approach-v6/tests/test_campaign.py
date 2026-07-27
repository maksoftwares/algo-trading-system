import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from src.campaign import (
    LANE_ROOT,
    apply_action_policy,
    attach_path_sequence_features,
    competing_utility,
    fit_predict_regime_hurdle,
    sequence_feature_names,
    unanimous_trigger,
)


def test_sequence_uses_completed_bars_and_masks_pre_entry(config):
    times = pd.date_range(
        "2026-01-01 00:00:00Z", periods=7, freq="5min", tz="UTC"
    )
    context = {
        "cap_t": times.tz_localize(None).to_numpy(),
        "cap": pd.DataFrame(
            {
                "bid_close": [101, 102, 103, 104, 105, 106, 1000],
                "ask_close": [101.2, 102.2, 103.2, 104.2, 105.2, 106.2, 1000.2],
            }
        ),
    }
    snapshots = pd.DataFrame(
        {
            "entry_time": [times[0]],
            "decision_time": [times[6]],
            "checkpoint_minutes": [30],
            "entry_price": [100.0],
            "risk_usd": [10.0],
            "long": [True],
        }
    )
    result = attach_path_sequence_features(snapshots, context, config)
    active_names = [name for name in result if name.startswith("path_active_")]
    return_names = [name for name in result if name.startswith("path_return_")]
    assert result.loc[0, active_names].sum() == 6.0
    assert result.loc[0, return_names[-1]] == pytest.approx(0.1)
    assert result.loc[0, return_names].max() < 1.0


def test_sequence_feature_contract_is_fixed_48_by_2(config):
    names = sequence_feature_names(config)
    assert len(names) == 96
    assert names[0] == "path_return_step_01"
    assert names[47] == "path_return_step_48"
    assert names[-1] == "path_active_step_48"


def test_competing_utility_penalizes_recovery_sacrifice():
    score = competing_utility(
        np.array([0.8, 0.4]),
        np.array([1.0, 1.0]),
        np.array([2.0, 2.0]),
    )
    np.testing.assert_allclose(score, [0.4, -0.8])


def test_action_policy_keeps_frozen_adverse_guards(config):
    snapshots = pd.DataFrame(
        {
            "current_r": [-0.2, -0.05, -0.2, -0.2],
            "max_adverse_r": [0.3, 0.3, 0.2, 0.3],
            "recent_15m_r": [-0.1, -0.1, -0.1, 0.1],
        }
    )
    assert apply_action_policy(
        snapshots, np.array([0.1, 0.1, 0.1, 0.1]), config
    ).tolist() == [True, False, False, False]


def test_regime_model_fails_closed_when_group_is_too_small(config):
    train = pd.DataFrame({"entry_regime": ["R1_UPTREND"] * 2})
    target = pd.DataFrame({"entry_regime": ["R1_UPTREND"]})
    settings = dict(config["arms"]["B_REGIME_COMPETING"])
    settings["minimum_group_training_rows"] = 3
    with pytest.raises(ValueError, match="Insufficient R1_UPTREND"):
        fit_predict_regime_hurdle(
            train,
            target,
            pd.DataFrame({"x": [0.0, 1.0]}),
            np.array([-1.0, 1.0]),
            np.ones(2),
            pd.DataFrame({"x": [0.5]}),
            settings,
            config,
        )


def test_ensemble_requires_locked_unanimity():
    observed = unanimous_trigger(
        [
            np.array([True, True, False]),
            np.array([True, False, True]),
            np.array([True, True, True]),
        ],
        3,
    )
    assert observed.tolist() == [True, False, False]


def test_v5_policy_and_walk_forward_are_frozen(config):
    v5_config = json.loads(
        (
            LANE_ROOT.parent
            / "v6-causal-ml-early-exit-crossasset-v5"
            / "config"
            / "v6_causal_ml_early_exit_crossasset_v5.json"
        ).read_text(encoding="utf-8")
    )
    for section in ("action_policy", "walk_forward", "windows", "gates"):
        assert config[section] == v5_config[section]


def test_locked_v5_sources_exist_and_match(config):
    import hashlib

    for source in config["sources"].values():
        path = Path(source["path"])
        if not path.is_absolute():
            path = LANE_ROOT.parents[2] / path
        assert path.is_file()
        assert hashlib.sha256(path.read_bytes()).hexdigest() == source["sha256"]
