from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

import numpy as np
import pandas as pd
import pytest


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("cboe_gvz_v89_test_campaign", ROOT / "src" / "campaign.py")
assert SPEC is not None and SPEC.loader is not None
CAMPAIGN = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = CAMPAIGN
SPEC.loader.exec_module(CAMPAIGN)


def _config() -> dict:
    return {
        "features": {
            "h1_atr_period": 3,
            "gvz_lookbacks": [2],
            "maximum_gvz_staleness_days": 7,
            "realized_volatility_hours": 4,
            "realized_volatility_minimum_hours": 3,
            "intraday_baseline_hours": 4,
            "intraday_baseline_minimum_hours": 3,
        }
    }


def _h1() -> pd.DataFrame:
    starts = pd.date_range("2024-01-01", periods=120, freq="h", tz="UTC")
    close = 2000.0 + np.arange(len(starts), dtype=float) * 0.2
    return pd.DataFrame(
        {
            "bar_start_utc": starts,
            "bar_end_utc": starts + pd.Timedelta(hours=1),
            "mid_open": close - 0.05,
            "mid_high": close + 0.2,
            "mid_low": close - 0.2,
            "mid_close": close,
        }
    )


def test_gvz_is_not_usable_on_its_own_date(tmp_path: Path) -> None:
    path = tmp_path / "gvz.csv"
    path.write_text("DATE,GVZ\n01/01/2024,20.0\n01/02/2024,22.0\n", encoding="ascii")
    gvz = CAMPAIGN.load_gvz(path, 1)
    assert gvz.loc[0, "available_utc"] == pd.Timestamp("2024-01-02T00:00:00Z")
    with pytest.raises(ValueError, match="Same-day"):
        CAMPAIGN.load_gvz(path, 0)


def test_prepare_features_uses_strictly_older_gvz_dates(tmp_path: Path) -> None:
    path = tmp_path / "gvz.csv"
    dates = pd.date_range("2023-12-20", periods=20, freq="D")
    rows = ["DATE,GVZ", *[f"{day:%m/%d/%Y},{20 + index / 10:.2f}" for index, day in enumerate(dates)]]
    path.write_text("\n".join(rows) + "\n", encoding="ascii")
    gvz = CAMPAIGN.load_gvz(path, 1)
    frame = CAMPAIGN.prepare_features(_h1(), gvz, _config())
    observed = frame.loc[frame["gvz_date"].notna()]
    assert not observed.empty
    assert (
        observed["gvz_date"].dt.date < observed["bar_end_utc"].dt.date
    ).all()


def test_breakout_direction_comes_from_completed_xau_structure() -> None:
    frame = pd.DataFrame(
        {
            "gvz_level_z_20": [2.0, 2.0],
            "mid_close": [101.0, 98.0],
            "prior_high_3": [100.0, 100.0],
            "prior_low_3": [99.0, 99.0],
            "atr14": [1.0, 1.0],
            "atr_ratio_causal": [1.0, 1.0],
            "session_slot": ["LONDON", "NY"],
        }
    )
    params = {
        "lookback": 20,
        "state_threshold_z": 1.0,
        "session": "BOTH",
        "channel_bars": 3,
        "breakout_buffer_atr": 0.0,
        "compression_max": 1.25,
    }
    mask, direction = CAMPAIGN.signal_mask_direction(
        frame, "GVZ_HIGH_BREAKOUT", params
    )
    assert mask.tolist() == [True, True]
    assert direction.tolist() == [1, -1]


def test_benjamini_hochberg_is_monotone_in_rank() -> None:
    pvalues = pd.Series([0.01, 0.04, 0.03, 0.20])
    adjusted = CAMPAIGN.benjamini_hochberg(pvalues)
    ranked = adjusted.iloc[np.argsort(pvalues.to_numpy())].to_numpy()
    assert np.all(np.diff(ranked) >= -1e-12)
    assert ((adjusted >= pvalues) & (adjusted <= 1.0)).all()


def test_calendar_weekday_denominator_excludes_weekends() -> None:
    start = pd.Timestamp("2024-01-01T00:00:00Z")
    end = pd.Timestamp("2024-01-08T00:00:00Z")
    assert CAMPAIGN._calendar_weekdays(start, end) == 5
