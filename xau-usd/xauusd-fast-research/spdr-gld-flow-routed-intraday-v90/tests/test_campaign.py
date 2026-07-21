from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

import numpy as np
import pandas as pd
import pytest


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "spdr_gld_v90_test_campaign", ROOT / "src" / "campaign.py"
)
assert SPEC is not None and SPEC.loader is not None
CAMPAIGN = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = CAMPAIGN
SPEC.loader.exec_module(CAMPAIGN)


def _config() -> dict:
    return {
        "features": {
            "h1_atr_period": 3,
            "flow_horizons": [1, 3, 5],
            "flow_z_lookbacks": [2],
            "maximum_gld_staleness_days": 7,
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


def _write_gld(path: Path, dates: pd.DatetimeIndex) -> None:
    frame = pd.DataFrame(
        {
            "Date": dates.strftime("%d-%b-%Y"),
            "Closing Price": 180.0 + np.arange(len(dates), dtype=float),
            "Total Ounces of Gold in the Trust": 10_000_000.0
            + np.arange(len(dates), dtype=float) * 10_000.0,
            "Tonnes of Gold": 311.0 + np.arange(len(dates), dtype=float),
        }
    )
    frame.to_excel(path, sheet_name="US GLD Historical Archive", index=False)


def test_gld_holdings_are_not_usable_on_their_own_date(tmp_path: Path) -> None:
    path = tmp_path / "gld.xlsx"
    _write_gld(path, pd.date_range("2024-01-01", periods=2, freq="D"))
    gld = CAMPAIGN.load_gld(path, "US GLD Historical Archive", 1)
    assert gld.loc[0, "available_utc"] == pd.Timestamp("2024-01-02T00:00:00Z")
    with pytest.raises(ValueError, match="Same-day"):
        CAMPAIGN.load_gld(path, "US GLD Historical Archive", 0)


def test_prepare_features_uses_strictly_older_gld_dates(tmp_path: Path) -> None:
    path = tmp_path / "gld.xlsx"
    _write_gld(path, pd.date_range("2023-12-20", periods=20, freq="D"))
    gld = CAMPAIGN.load_gld(path, "US GLD Historical Archive", 1)
    frame = CAMPAIGN.prepare_features(_h1(), gld, _config())
    observed = frame.loc[frame["gld_date"].notna()]
    assert not observed.empty
    assert (
        observed["gld_date"].dt.date < observed["bar_end_utc"].dt.date
    ).all()


def test_breakout_direction_must_agree_with_lagged_holdings_flow() -> None:
    frame = pd.DataFrame(
        {
            "flow_1d_bps": [15.0, -15.0, 15.0],
            "mid_close": [101.0, 98.0, 98.0],
            "prior_high_3": [100.0, 100.0, 100.0],
            "prior_low_3": [99.0, 99.0, 99.0],
            "atr14": [1.0, 1.0, 1.0],
            "session_slot": ["LONDON", "NY", "LONDON"],
        }
    )
    params = {
        "flow_horizon": 1,
        "minimum_flow_bps": 10.0,
        "session": "BOTH",
        "channel_bars": 3,
        "breakout_buffer_atr": 0.0,
    }
    mask, direction = CAMPAIGN.signal_mask_direction(
        frame, "FLOW_ALIGNED_BREAKOUT", params
    )
    assert mask.tolist() == [True, True, False]
    assert direction.tolist() == [1, -1, 1]


def test_divergence_reversal_requires_price_turn_toward_flow() -> None:
    frame = pd.DataFrame(
        {
            "flow_3d_bps": [20.0, -20.0],
            "impulse_6_atr": [-1.0, 1.0],
            "body_atr": [0.25, -0.25],
            "session_slot": ["LONDON", "NY"],
        }
    )
    params = {
        "flow_horizon": 3,
        "minimum_flow_bps": 10.0,
        "impulse_hours": 6,
        "divergence_min_atr": 0.6,
        "confirmation_min_atr": 0.1,
        "session": "BOTH",
    }
    mask, direction = CAMPAIGN.signal_mask_direction(
        frame, "FLOW_DIVERGENCE_REVERSAL", params
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
