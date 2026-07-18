from __future__ import annotations

import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd
import pytest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from campaign import (  # noqa: E402
    MECHANICS,
    bh_adjust,
    generate_manifest,
    simulate_h1_outcome,
)


def selection() -> dict[str, int]:
    return {
        "attempt_first": 11118,
        "attempt_last": 15117,
        "variants_per_mechanic": 200,
        "total_attempts": 4000,
    }


def execution() -> dict[str, float | int]:
    return {
        "maximum_entry_gap_minutes": 10,
        "maximum_entry_spread_r": 0.15,
        "maximum_research_risk_usd": 50.0,
        "ounces_at_lot_size": 1.0,
        "ticket_cost_usd": 0.3,
        "holding_cost_per_24h_usd": 0.35,
        "stress_slippage_r": 0.05,
    }


def synthetic_frame() -> pd.DataFrame:
    starts = pd.date_range("2026-01-01T00:00:00Z", periods=5, freq="1h")
    frame = pd.DataFrame(
        {
            "bar_start_utc": starts,
            "bar_end_utc": starts + pd.Timedelta(hours=1),
            "timestamp_utc": starts + pd.Timedelta(hours=1),
            "atr14": [10.0] * 5,
            "bid_open": [99.8, 100.0, 101.0, 102.0, 103.0],
            "ask_open": [100.0, 100.2, 101.2, 102.2, 103.2],
            "bid_high": [101.0, 101.0, 102.0, 103.0, 104.0],
            "bid_low": [99.0, 99.5, 100.5, 101.5, 102.5],
            "bid_close": [100.0, 100.8, 101.8, 102.8, 103.8],
            "ask_high": [101.2, 101.2, 102.2, 103.2, 104.2],
            "ask_low": [99.2, 99.7, 100.7, 101.7, 102.7],
            "ask_close": [100.2, 101.0, 102.0, 103.0, 104.0],
        }
    )
    return frame


def test_manifest_has_locked_attempt_boundary_and_mechanics() -> None:
    manifest = generate_manifest(selection())
    assert len(manifest) == 4000
    assert manifest["attempt_no"].tolist() == list(range(11118, 15118))
    assert not manifest["variant_id"].duplicated().any()
    assert manifest.groupby("regime_owner").size().to_dict() == {
        "CHOP": 1000,
        "COMPRESSION": 1000,
        "DOWNTREND": 1000,
        "TRANSITION": 1000,
    }
    assert set(manifest["mechanic"]) == {
        mechanic for mechanics in MECHANICS.values() for mechanic in mechanics
    }
    assert all(
        isinstance(json.loads(value), dict)
        for value in manifest["parameters_json"]
    )


def test_long_enters_next_bar_at_ask_and_exits_at_bid() -> None:
    outcome = simulate_h1_outcome(
        synthetic_frame(), 0, 1, 1.0, 2.0, execution()
    )
    assert outcome is not None
    assert outcome["entry_time"] == pd.Timestamp("2026-01-01T01:00:00Z")
    assert outcome["entry_price"] == pytest.approx(100.2)
    assert outcome["exit_time"] == pd.Timestamp("2026-01-01T03:00:00Z")
    assert outcome["exit_price"] == pytest.approx(102.0)
    assert outcome["exit_reason"] == "FIXED_HORIZON"


def test_short_stop_uses_ask_high() -> None:
    frame = synthetic_frame()
    frame.loc[1, "ask_high"] = 111.0
    outcome = simulate_h1_outcome(frame, 0, -1, 1.0, 2.0, execution())
    assert outcome is not None
    assert outcome["entry_price"] == pytest.approx(100.0)
    assert outcome["stop"] == pytest.approx(110.0)
    assert outcome["exit_price"] == pytest.approx(110.0)
    assert outcome["exit_reason"] == "STOP"


def test_gap_through_stop_pays_observed_open() -> None:
    frame = synthetic_frame()
    frame.loc[2, ["bid_open", "ask_open"]] = [111.0, 111.2]
    outcome = simulate_h1_outcome(frame, 0, -1, 1.0, 2.0, execution())
    assert outcome is not None
    assert outcome["exit_price"] == pytest.approx(111.2)
    assert outcome["exit_reason"] == "GAP_THROUGH_STOP"
    assert outcome["gross_r"] < -1.0


def test_entry_gap_rejects_missing_next_hour() -> None:
    frame = synthetic_frame()
    frame.loc[1:, "bar_start_utc"] += pd.Timedelta(hours=2)
    assert simulate_h1_outcome(frame, 0, 1, 1.0, 2.0, execution()) is None


def test_bh_adjust_is_monotone_in_ranked_pvalues() -> None:
    values = pd.Series([0.04, 0.001, 0.02, 0.5])
    adjusted = bh_adjust(values)
    ordered = pd.DataFrame({"p": values, "q": adjusted}).sort_values("p")
    assert np.all(np.diff(ordered["q"].to_numpy()) >= -1e-12)
    assert adjusted.between(0.0, 1.0).all()
    assert adjusted.iloc[1] == pytest.approx(0.004)
