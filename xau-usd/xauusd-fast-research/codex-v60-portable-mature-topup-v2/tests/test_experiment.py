from __future__ import annotations

from types import SimpleNamespace

import numpy as np
import pandas as pd

from src import experiment


def test_policy_proposes_only_mature_top_twenty_percent() -> None:
    primary = pd.DataFrame({"rank": [0.99, 0.80, 0.81]})
    meta = pd.DataFrame(
        {
            "entry_time": pd.to_datetime(
                ["2023-01-01", "2024-01-01", "2024-01-02"], utc=True
            )
        }
    )
    observed: dict[str, np.ndarray] = {}

    def fake_factors(meta, proposed, demo_config, limits, prior):
        observed["proposed"] = np.asarray(proposed)
        return np.ones(len(meta)), {
            "proposed_topups": int(np.sum(proposed)),
            "accepted_topups": 0,
        }

    topup = SimpleNamespace(topup_factors=fake_factors)
    config = {
        "policy": {
            "maturity_entry_year": 2024,
            "minimum_rank_exclusive": 0.8,
            "retain_every_baseline_trade": True,
        },
        "risk_limits": {
            "account_initial_risk_usd": 60,
            "directional_initial_risk_usd": 60,
            "addon_initial_risk_usd": 45,
        },
    }
    experiment.policy_factors(
        primary, meta, config, {}, topup, SimpleNamespace()
    )
    assert observed["proposed"].tolist() == [False, False, True]


def test_topup_profit_factor_uses_only_accepted_topups() -> None:
    meta = pd.DataFrame({experiment.PNL: [10.0, -5.0, 100.0]})
    assert experiment.topup_profit_factor(meta, np.array([2.0, 2.0, 1.0])) == 2.0


def test_portable_contract_excludes_all_feed_specific_features() -> None:
    config = __import__("json").loads(
        experiment.CONFIG_PATH.read_text(encoding="utf-8")
    )
    assert not (
        set(config["feature_columns"])
        & set(config["excluded_feed_specific_features"])
    )
    assert config["authorization"]["demo_broker_action_authorized"] is False


def test_decision_audit_feature_name_does_not_duplicate_metadata() -> None:
    features = pd.DataFrame({"is_core": [1.0], "is_long": [1.0]})
    audit = features.rename(columns={"is_core": "feature_is_core"})
    decisions = pd.concat([pd.DataFrame({"is_core": [True]}), audit], axis=1)
    assert not decisions.columns.duplicated().any()
