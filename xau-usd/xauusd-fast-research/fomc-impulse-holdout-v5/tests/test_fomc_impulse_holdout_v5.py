from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
PARENT = ROOT.parent / "event-reaction-corrected-v4"


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


LOCK = _load("fomc_impulse_v5_lock_tests", ROOT / "lock_contract.py")


def _config() -> dict:
    return json.loads(
        (ROOT / "config" / "fomc_impulse_holdout_v5.json").read_text(
            encoding="utf-8"
        )
    )


def test_policy_is_one_contiguous_exact_holdout_attempt() -> None:
    config = _config()
    policy = config["policy"]
    assert policy["attempt_no"] == 11111
    assert config["research_controls"]["campaign_attempts_before_v5"] == 11110
    assert config["research_controls"]["registered_policy_count"] == 1
    assert config["research_controls"]["parameter_search_count"] == 0
    assert policy["source_policy_id"] == "EVENT_FOMC_IMPULSE_RR2"


def test_policy_and_execution_transfer_exactly_from_corrected_parent() -> None:
    config = _config()
    parent = json.loads(
        (PARENT / "config" / "event_reaction_corrected_v4.json").read_text(
            encoding="utf-8"
        )
    )
    source_policy = next(
        policy
        for policy in parent["policies"]
        if policy["policy_id"] == config["policy"]["source_policy_id"]
    )
    fields = [
        "event_type",
        "mode",
        "impulse_minutes",
        "start_minutes",
        "end_minutes",
        "break_atr",
        "stop_buffer_atr",
        "minimum_body_fraction",
        "target_r",
    ]
    assert {key: config["policy"][key] for key in fields} == {
        key: source_policy[key] for key in fields
    }
    assert config["execution"] == parent["execution"]


def test_candidate_ledger_is_outcome_free_causal_and_fixed() -> None:
    config = _config()
    candidates = pd.read_parquet(
        ROOT / "outputs" / config["outputs"]["candidates"]
    )
    assert len(candidates) == 35
    assert candidates["direction"].value_counts().to_dict() == {
        "SHORT": 19,
        "LONG": 16,
    }
    assert set(candidates["policy_id"]) == {config["policy"]["policy_id"]}
    assert not candidates["candidate_id"].duplicated().any()
    prohibited = [
        column
        for column in candidates.columns
        if any(
            token in column.lower()
            for token in ("pnl", "profit", "exit_", "stress_", "winner")
        )
    ]
    assert prohibited == []
    assert not (
        candidates["regime_feature_time_utc"].notna()
        & candidates["regime_feature_time_utc"].gt(candidates["feature_time_utc"])
    ).any()


def test_contract_uses_only_54_holdout_tick_months() -> None:
    paths = LOCK.contract_paths(_config())
    manifests = [
        name for name in paths if name.startswith("external/raw/XAUUSD/year=")
    ]
    assert len(manifests) == 54
    assert all(
        202201
        <= int(name.split("year=")[1][:4]) * 100
        + int(name.split("month=")[1][:2])
        < 202607
        for name in manifests
    )


def test_parent_confirmation_remains_sealed() -> None:
    assert not (
        PARENT
        / "outputs"
        / "CORRECTED_EVENT_RELATED_CONFIRMATION_OUTCOMES_OPENED.json"
    ).exists()


def test_economic_and_deployment_feasibility_are_explicitly_separate() -> None:
    config = _config()
    assert config["economic_gate"]["minimum_current_account_feasible_share"] == 0.0
    assert config["deployment_gate"]["minimum_current_account_feasible_share"] == 0.8
    assert config["economic_gate"]["minimum_stress_pf"] == 1.25
    assert config["economic_gate"]["minimum_average_stress_r"] == 0.1
    assert config["economic_gate"]["maximum_pvalue"] == 0.1
    assert config["research_controls"]["economic_and_deployment_gates_separated"] is True


def test_research_controls_deny_training_execution_and_paid_data() -> None:
    controls = _config()["research_controls"]
    assert controls["research_only"] is True
    assert controls["paid_data_authorized"] is False
    assert controls["databento_use_authorized"] is False
    assert controls["model_training_authorized"] is False
    assert controls["ea_consumption_authorized"] is False
    assert controls["broker_action_authorized"] is False
