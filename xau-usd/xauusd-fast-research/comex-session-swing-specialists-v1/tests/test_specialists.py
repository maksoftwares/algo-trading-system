from __future__ import annotations

import json
from pathlib import Path
import sys

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from specialists import FAMILIES, completed_h1_atr  # noqa: E402


def test_h1_atr_excludes_incomplete_hour() -> None:
    complete_rows = 15 * 12
    periods = complete_rows + 11
    starts = pd.date_range("2024-01-02T00:00:00Z", periods=periods, freq="5min")
    base = pd.Series(range(periods), dtype=float) / 100.0 + 2000.0
    spot = pd.DataFrame(
        {
            "bar_start_utc": starts,
            "mid_open": base,
            "mid_high": base + 1.0,
            "mid_low": base - 1.0,
            "mid_close": base + 0.25,
        }
    )

    result = completed_h1_atr(spot, period=14)

    assert len(result) == 15
    assert result.iloc[-1]["timestamp_h1"] == pd.Timestamp("2024-01-02T15:00:00Z")
    assert pd.notna(result.iloc[-1]["h1_atr"])


def test_all_preregistered_families_have_frozen_risk_settings() -> None:
    config = json.loads(
        (ROOT / "config" / "comex_session_swing_specialists_v1.json").read_text(
            encoding="utf-8"
        )
    )

    assert set(FAMILIES) == set(config["families"])
    for settings in config["families"].values():
        assert settings["stop_atr"] > 0
        assert settings["target_r"] > 0
        assert settings["maximum_hold_hours"] in {36.0, 48.0}
