from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
PARENT = ROOT.parent / "ppi-event-reaction-v1"


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


LOCK = _load("ppi_fade_regime_v2_lock_tests", ROOT / "lock_contract.py")


def _config() -> dict:
    return json.loads(
        (ROOT / "config" / "ppi_fade_regime_confirmation_v2.json").read_text(
            encoding="utf-8"
        )
    )


def test_policy_is_one_contiguous_attempt_with_symmetric_nontrend_states() -> None:
    config = _config()
    policy = config["policy"]
    assert policy["attempt_no"] == 11102
    assert config["research_controls"]["campaign_attempts_before_v2"] == 11101
    assert config["research_controls"]["registered_policy_count"] == 1
    assert config["research_controls"]["parameter_search_count"] == 0
    assert policy["allowed_regimes"] == ["CHOP", "COMPRESSION", "TRANSITION"]


def test_signal_and_execution_mechanics_transfer_exactly_from_parent_fade() -> None:
    config = _config()
    parent = json.loads(
        (PARENT / "config" / "ppi_event_reaction_v1.json").read_text(
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
    assert len(candidates) == 16
    assert set(candidates["policy_id"]) == {config["policy"]["policy_id"]}
    assert set(candidates["regime"]) <= set(config["policy"]["allowed_regimes"])
    assert not candidates["candidate_id"].duplicated().any()
    assert candidates["feature_time_utc"].ge(config["source"]["start_utc"]).all()
    assert candidates["feature_time_utc"].lt(
        config["source"]["end_exclusive_utc"]
    ).all()
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


def test_parent_historical_evidence_supports_only_hypothesis_generation() -> None:
    outcomes = pd.read_parquet(
        PARENT / "outputs" / "PPI_EVENT_HISTORICAL_DISCOVERY_OUTCOMES.parquet"
    )
    fade = outcomes.loc[outcomes["policy_id"].eq("EVENT_PPI_FADE_RR2")]
    nontrend = fade.loc[fade["regime"].isin(["CHOP", "COMPRESSION", "TRANSITION"])]
    downtrend = fade.loc[fade["regime"].eq("TREND_DOWN")]
    assert len(nontrend) == 26
    assert nontrend["stress_net_r"].sum() > 0.0
    assert len(downtrend) == 6
    assert downtrend["stress_net_r"].sum() < 0.0


def test_contract_uses_only_54_confirmation_tick_months() -> None:
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


def test_parent_confirmation_is_still_sealed() -> None:
    assert not (
        PARENT
        / "outputs"
        / "PPI_EVENT_RELATED_CONFIRMATION_OUTCOMES_OPENED.json"
    ).exists()


def test_posthoc_confirmation_gate_is_stricter_than_parent_where_changed() -> None:
    config = _config()
    parent = json.loads(
        (PARENT / "config" / "ppi_event_reaction_v1.json").read_text(
            encoding="utf-8"
        )
    )
    gate = config["gate"]
    parent_gate = parent["gates"]["related_confirmation"]
    assert gate["minimum_stress_pf"] >= parent_gate["minimum_stress_pf"]
    assert gate["minimum_average_stress_r"] >= parent_gate[
        "minimum_average_stress_r"
    ]
    assert gate["maximum_holm_qvalue"] <= parent_gate["maximum_holm_qvalue"]
    assert gate["maximum_closed_drawdown_r"] <= parent_gate[
        "maximum_closed_drawdown_r"
    ]
