from __future__ import annotations

import json
from pathlib import Path
import sys

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from adaptive import FAMILIES, FEATURE_COLUMNS, generate_candidates  # noqa: E402


def test_candidate_features_are_causal_and_complete() -> None:
    config = json.loads(
        (ROOT / "config" / "adaptive_h4_specialists_v1.json").read_text(
            encoding="utf-8"
        )
    )
    periods = 220
    starts = pd.date_range("2020-01-01T00:00:00Z", periods=periods, freq="4h")
    base = pd.Series(range(periods), dtype=float) * 0.5 + 1400.0
    frame = pd.DataFrame(
        {
            "bar_start_utc": starts,
            "timestamp_utc": starts + pd.Timedelta(hours=4),
            "mid_open": base,
            "mid_high": base + 2.0,
            "mid_low": base - 1.0,
            "mid_close": base + 1.5,
            "bid_close": base + 1.4,
            "ask_close": base + 1.6,
            "tick_count": [1000.0] * periods,
        }
    )

    candidates = generate_candidates(frame, config)

    assert not candidates.empty
    assert set(candidates["family_id"]).issubset(set(FAMILIES))
    assert candidates[list(FEATURE_COLUMNS)].notna().all().all()
    assert (candidates["signal_time"] <= frame["timestamp_utc"].max()).all()


def test_frozen_families_match_contract() -> None:
    config = json.loads(
        (ROOT / "config" / "adaptive_h4_specialists_v1.json").read_text(
            encoding="utf-8"
        )
    )

    assert set(FAMILIES) == set(config["families"])
    assert config["model"]["evaluation_block_months"] == 6
    assert config["research_controls"]["same_version_post_outcome_tuning_authorized"] is False
