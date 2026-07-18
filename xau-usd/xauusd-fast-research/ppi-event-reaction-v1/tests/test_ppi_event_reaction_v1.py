from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


ACQUIRE = _load("ppi_event_acquisition_tests", ROOT / "acquire_calendar.py")
LOCK = _load("ppi_event_lock_tests", ROOT / "lock_contract.py")


def test_official_archive_parser_filters_dates_and_applies_dst() -> None:
    text = "\n".join(
        [
            "[June 2016 Producer Price Index](https://www.bls.gov/news.release/archives/ppi_07142016.htm)",
            "[December 2016 Producer Price Index](https://www.bls.gov/news.release/archives/ppi_01132017.htm)",
            "[June 2026 Producer Price Index](https://www.bls.gov/news.release/archives/ppi_07152026.htm)",
        ]
    )
    frame = ACQUIRE.parse_archive(
        text,
        pd.Timestamp("2016-07-01T00:00:00Z"),
        pd.Timestamp("2026-07-01T00:00:00Z"),
    )
    assert frame["event_id"].tolist() == ["PPI_2016-07-14", "PPI_2017-01-13"]
    assert frame.loc[0, "event_time_utc"] == pd.Timestamp(
        "2016-07-14T12:30:00Z"
    )
    assert frame.loc[1, "event_time_utc"] == pd.Timestamp(
        "2017-01-13T13:30:00Z"
    )


def test_parser_rejects_non_bls_only_input() -> None:
    text = "[June 2016 Producer Price Index](https://example.com/ppi_07142016.htm)"
    try:
        ACQUIRE.parse_archive(
            text,
            pd.Timestamp("2016-07-01T00:00:00Z"),
            pd.Timestamp("2026-07-01T00:00:00Z"),
        )
    except ValueError as error:
        assert "No official PPI" in str(error)
    else:
        raise AssertionError("Non-BLS input unexpectedly produced an event")


def test_registered_policies_are_exact_transfer_attempts() -> None:
    config = json.loads(
        (ROOT / "config" / "ppi_event_reaction_v1.json").read_text(
            encoding="utf-8"
        )
    )
    policies = config["policies"]
    assert [policy["attempt_no"] for policy in policies] == [11100, 11101]
    assert [policy["mode"] for policy in policies] == ["IMPULSE", "FADE"]
    assert all(policy["event_type"] == "PPI" for policy in policies)
    assert all(policy["target_r"] == 2.0 for policy in policies)
    assert config["research_controls"]["parameter_search_count"] == 0


def test_frozen_calendar_has_expected_coverage_and_unique_sources() -> None:
    calendar = pd.read_csv(
        ROOT / "outputs" / "PPI_EVENT_CALENDAR.csv",
        parse_dates=["event_time_utc"],
    )
    assert len(calendar) == 119
    assert not calendar["event_id"].duplicated().any()
    assert not calendar["source_url"].duplicated().any()
    assert int(calendar["event_time_utc"].lt("2022-01-01T00:00:00Z").sum()) == 66
    assert int(calendar["event_time_utc"].ge("2022-01-01T00:00:00Z").sum()) == 53


def test_candidate_ledger_contains_no_outcomes_or_future_regime_features() -> None:
    candidates = pd.read_parquet(ROOT / "outputs" / "PPI_EVENT_CANDIDATES.parquet")
    prohibited = [
        column
        for column in candidates.columns
        if any(
            token in column.lower()
            for token in ("pnl", "profit", "exit_", "stress_", "winner")
        )
    ]
    assert prohibited == []
    assert not candidates["candidate_id"].duplicated().any()
    assert not (
        candidates["regime_feature_time_utc"].notna()
        & candidates["regime_feature_time_utc"].gt(candidates["feature_time_utc"])
    ).any()


def test_contract_uses_only_the_120_required_tick_months() -> None:
    config = json.loads(
        (ROOT / "config" / "ppi_event_reaction_v1.json").read_text(
            encoding="utf-8"
        )
    )
    paths = LOCK.contract_paths(config)
    tick_manifests = [
        name
        for name in paths
        if name.startswith("external/raw/XAUUSD/year=")
    ]
    assert len(tick_manifests) == 120
    assert all("year=2010" not in name for name in tick_manifests)
