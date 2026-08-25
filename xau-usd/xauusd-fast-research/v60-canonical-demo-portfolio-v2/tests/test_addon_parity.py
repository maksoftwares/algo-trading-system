from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys

import pandas as pd

from addons import (
    REPO_ROOT,
    _candidate_health_observability,
    _health_snapshot,
    _source_entry_weekday_allowed,
    historical_rule_frames,
)


ROOT = Path(__file__).resolve().parents[1]
CONFIG = json.loads(
    (ROOT / "config" / "v60_canonical_demo_portfolio_v2.json").read_text(
        encoding="utf-8"
    )
)


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def test_health_sleeve_historical_candidate_parity() -> None:
    frames = historical_rule_frames(CONFIG)
    research = REPO_ROOT / "xau-usd" / "xauusd-fast-research"
    v53 = load_module(
        "v60_v2_test_v53_portfolio",
        research / "one-trade-per-day-health-portfolio-v53" / "src" / "portfolio.py",
    )
    frozen_v7 = pd.read_parquet(
        research / "pullback-swing-replication-v7" / "outputs" / "PULLBACK_SWING_REPLICATION_V7_TRADES.parquet"
    )
    assert frames["V7_SWING_HEALTH"]["event_id"].astype(str).tolist() == frozen_v7[
        "event_id"
    ].astype(str).tolist()

    unified = pd.read_parquet(
        research
        / "one-trade-per-day-unified-portfolio-v57"
        / "outputs"
        / "ONE_TRADE_PER_DAY_UNIFIED_PORTFOLIO_V57_CANDIDATES.parquet"
    )
    accepted_events: dict[str, set[str]] = {}
    limits = {
        "V7_SWING_HEALTH": 30.0,
        "V8_RETEST_HEALTH": 20.0,
        "V57_BREAK_SWING_H4ADX_HIGH": 30.0,
    }
    for sleeve_id, frame in frames.items():
        prepared = frame.copy()
        prepared["trade_id"] = sleeve_id + "_" + prepared["event_id"].astype(str)
        prepared["pnl_usd"] = prepared["stress_net_r"] * prepared["risk_usd"]
        gated = v53.causal_shadow_health_gate(prepared, 100, 1.0)
        gated = gated.loc[gated["risk_usd"].le(limits[sleeve_id])]
        accepted_events[sleeve_id] = set(gated["event_id"].astype(str))

    accepted_events["V57_BREAK_SWING_H4ADX_HIGH"] -= (
        accepted_events["V7_SWING_HEALTH"] | accepted_events["V8_RETEST_HEALTH"]
    )
    for sleeve_id, expected in accepted_events.items():
        rows = unified.loc[unified["sleeve_id"].eq(sleeve_id), "trade_id"].astype(str)
        prefixes = {
            "V7_SWING_HEALTH": "V7_",
            "V8_RETEST_HEALTH": "V8_",
            "V57_BREAK_SWING_H4ADX_HIGH": "V9_BREAK_",
        }
        observed = {value.removeprefix(prefixes[sleeve_id]) for value in rows}
        assert observed == expected


def test_v25_frozen_candidate_identity_and_origin() -> None:
    research = REPO_ROOT / "xau-usd" / "xauusd-fast-research"
    candidates = pd.read_parquet(
        research
        / "chop-failed-reversion-rawtick-v25"
        / "outputs"
        / "CHOP_FAILED_REVERSION_RAWTICK_V25_CANDIDATES.parquet"
    )
    manifest = json.loads(
        (
            research
            / "chop-failed-reversion-rawtick-v25"
            / "outputs"
            / "CHOP_FAILED_REVERSION_RAWTICK_V25_CANDIDATE_MANIFEST.json"
        ).read_text(encoding="utf-8")
    )
    assert len(candidates) == int(manifest["rows"]) == 1006
    assert int(manifest["origin_raw_signals"]) == 1986
    assert set(candidates["origin_attempt"].astype(int)) == {39583}
    assert not candidates["candidate_id"].duplicated().any()
    assert set(candidates["stop_atr"].astype(float)) == {1.0}
    assert set(candidates["target_r"].astype(float)) == {2.0}
    assert set(candidates["hold_hours"].astype(float)) == {12.0}


def test_health_snapshot_exposes_recent_degradation_without_policy_action() -> None:
    values = [2.0] * 80 + [1.0] * 5 + [-2.0] * 15
    snapshot = _health_snapshot(
        {
            "history": [
                {
                    "event_id": str(index),
                    "exit_time_utc": f"2026-01-{index + 1:02d}T00:00:00Z",
                    "pnl_usd": value,
                }
                for index, value in enumerate(values)
            ]
        }
    )

    assert snapshot["windows"]["20"]["completed_count"] == 20
    assert snapshot["windows"]["20"]["net_pnl_usd"] == -25.0
    assert snapshot["recent_20_degraded"] is True
    assert snapshot["policy_effect"] == "OBSERVABILITY_ONLY"

    candidate_fields = _candidate_health_observability(
        {"history": [{"pnl_usd": value} for value in values]}
    )
    assert candidate_fields == {
        "health_recent_20_completed_count": 20,
        "health_recent_20_profit_factor": 1.0 / 6.0,
        "health_recent_20_net_usd": -25.0,
    }


def test_v57_source_generation_rejects_weekend_without_global_block() -> None:
    sunday = pd.Timestamp("2026-08-23T23:35:00Z")
    monday = pd.Timestamp("2026-08-24T00:05:00Z")

    assert not _source_entry_weekday_allowed(
        CONFIG, "V57_BREAK_SWING_H4ADX_HIGH", sunday
    )
    assert _source_entry_weekday_allowed(
        CONFIG, "V57_BREAK_SWING_H4ADX_HIGH", monday
    )
    assert _source_entry_weekday_allowed(CONFIG, "R4_CHOP", sunday)
