from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
RESEARCH_ROOT = ROOT.parent


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


LOCK = _load("corrected_event_v4_lock_tests", ROOT / "lock_contract.py")


def _config() -> dict:
    return json.loads(
        (ROOT / "config" / "event_reaction_corrected_v4.json").read_text(
            encoding="utf-8"
        )
    )


def test_eight_policies_have_contiguous_attempts_and_no_search() -> None:
    config = _config()
    policies = config["policies"]
    assert [policy["attempt_no"] for policy in policies] == list(
        range(11103, 11111)
    )
    assert len(policies) == 8
    assert {
        (policy["event_type"], policy["mode"]) for policy in policies
    } == {
        (event_type, mode)
        for event_type in ("NFP", "CPI", "FOMC", "PPI")
        for mode in ("IMPULSE", "FADE")
    }
    assert all(policy["target_r"] == 2.0 for policy in policies)
    assert all(policy["break_atr"] == 0.1 for policy in policies)
    assert all(policy["stop_buffer_atr"] == 0.1 for policy in policies)
    assert all(policy["minimum_body_fraction"] == 0.35 for policy in policies)
    assert config["research_controls"]["parameter_search_count"] == 0


def test_candidate_ledger_is_outcome_free_causal_and_complete() -> None:
    config = _config()
    candidates = pd.read_parquet(
        ROOT / "outputs" / config["outputs"]["candidates"]
    )
    assert len(candidates) == 533
    assert set(candidates["policy_id"]) == {
        policy["policy_id"] for policy in config["policies"]
    }
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


def test_calendar_contains_all_four_official_event_types() -> None:
    config = _config()
    calendar = pd.read_csv(
        ROOT / "outputs" / config["outputs"]["calendar"],
        parse_dates=["event_time_utc"],
    )
    assert len(calendar) == 436
    assert not calendar["event_id"].duplicated().any()
    assert calendar["event_type"].value_counts().to_dict() == {
        "NFP": 119,
        "CPI": 119,
        "PPI": 119,
        "FOMC": 79,
    }


def test_contract_uses_exact_official_and_tick_source_counts() -> None:
    config = _config()
    paths = LOCK.contract_paths(config)
    fomc = [name for name in paths if name.startswith("external/fomc/")]
    ticks = [
        name for name in paths if name.startswith("external/raw/XAUUSD/year=")
    ]
    assert len(fomc) == 79
    assert len(ticks) == 120
    assert all(
        201607
        <= int(name.split("year=")[1][:4]) * 100
        + int(name.split("month=")[1][:2])
        < 202607
        for name in ticks
    )


def test_corrected_engine_has_resolution_guard_and_no_defective_division() -> None:
    text = (
        RESEARCH_ROOT
        / "macro-event-reaction-replication-v2"
        / "src"
        / "event_reaction.py"
    ).read_text(encoding="utf-8")
    assert "_timestamp_series_ms" in text
    assert "Candidate decisions fall outside the M5 epoch-millisecond range" in text
    assert 'm5["bar_start_utc"].astype("int64") // 1_000_000' not in text


def test_confirmation_is_not_opened_before_historical_advancement() -> None:
    assert not (
        ROOT
        / "outputs"
        / "CORRECTED_EVENT_RELATED_CONFIRMATION_OUTCOMES_OPENED.json"
    ).exists()


def test_research_controls_deny_training_execution_and_paid_data() -> None:
    controls = _config()["research_controls"]
    assert controls["prior_event_results_invalidated"] is True
    assert controls["execution_timestamp_defect_only_strategy_change"] is True
    assert controls["research_only"] is True
    assert controls["paid_data_authorized"] is False
    assert controls["databento_use_authorized"] is False
    assert controls["model_training_authorized"] is False
    assert controls["ea_consumption_authorized"] is False
    assert controls["broker_action_authorized"] is False
