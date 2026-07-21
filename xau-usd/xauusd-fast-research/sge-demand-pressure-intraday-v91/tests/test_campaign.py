from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

import numpy as np
import pandas as pd
import pytest


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "sge_v91_test_campaign", ROOT / "src" / "campaign.py"
)
assert SPEC is not None and SPEC.loader is not None
CAMPAIGN = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = CAMPAIGN
SPEC.loader.exec_module(CAMPAIGN)


def _config() -> dict:
    return {
        "features": {
            "h1_atr_period": 3,
            "return_horizons": [1, 2, 3],
            "state_z_lookbacks": [2],
            "maximum_sge_staleness_days": 7,
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


def _write_sge(path: Path, dates: pd.DatetimeIndex) -> None:
    rows = []
    contracts = ("Au99.99", "Au(T+D)", "mAu(T+D)", "Ag(T+D)")
    for date_index, date in enumerate(dates):
        for contract_index, contract in enumerate(contracts):
            rows.append(
                {
                    "date": date,
                    "contract": contract,
                    "close": 400.0 + date_index + contract_index * 0.1,
                    "volume_kg": 1000.0 + date_index * 10 + contract_index,
                    "open_interest_lot": 10000.0 + date_index * 20,
                    "direction": (
                        "short_to_long" if date_index % 2 else "long_to_short"
                    ),
                    "delivery_volume_lot": 100.0 + date_index,
                }
            )
    pd.DataFrame(rows).to_parquet(path, index=False)


def test_sge_state_is_not_usable_on_its_own_date(tmp_path: Path) -> None:
    path = tmp_path / "sge.parquet"
    _write_sge(path, pd.date_range("2024-01-01", periods=2, freq="D"))
    sge = CAMPAIGN.load_sge(path, 1)
    assert sge.loc[0, "available_utc"] == pd.Timestamp("2024-01-02T00:00:00Z")
    with pytest.raises(ValueError, match="Same-day"):
        CAMPAIGN.load_sge(path, 0)


def test_prepare_features_uses_strictly_older_sge_dates(tmp_path: Path) -> None:
    path = tmp_path / "sge.parquet"
    _write_sge(path, pd.date_range("2023-12-20", periods=20, freq="D"))
    sge = CAMPAIGN.load_sge(path, 1)
    frame = CAMPAIGN.prepare_features(_h1(), sge, _config())
    observed = frame.loc[frame["date"].notna()]
    assert not observed.empty
    assert (observed["date"].dt.date < observed["bar_end_utc"].dt.date).all()


def test_cash_breakout_direction_must_agree_with_lagged_return() -> None:
    frame = pd.DataFrame(
        {
            "cash_return_1d_bps": [15.0, -15.0, 15.0],
            "mid_close": [101.0, 98.0, 98.0],
            "prior_high_3": [100.0, 100.0, 100.0],
            "prior_low_3": [99.0, 99.0, 99.0],
            "atr14": [1.0, 1.0, 1.0],
            "session_slot": ["LONDON", "NY", "LONDON"],
        }
    )
    params = {
        "return_horizon": 1,
        "minimum_return_bps": 10.0,
        "session": "BOTH",
        "channel_bars": 3,
        "breakout_buffer_atr": 0.0,
    }
    mask, direction = CAMPAIGN.signal_mask_direction(
        frame, "CASH_MOMENTUM_BREAKOUT", params
    )
    assert mask.tolist() == [True, True, False]
    assert direction.tolist() == [1, -1, 1]


def test_basis_reversion_points_against_dislocation() -> None:
    frame = pd.DataFrame(
        {
            "basis_z_20": [2.0, -2.0],
            "impulse_6_atr": [1.0, -1.0],
            "body_atr": [-0.25, 0.25],
            "session_slot": ["LONDON", "NY"],
        }
    )
    params = {
        "basis_z_lookback": 20,
        "minimum_basis_z": 1.0,
        "impulse_hours": 6,
        "dislocation_min_atr": 0.5,
        "confirmation_min_atr": 0.1,
        "session": "BOTH",
    }
    mask, direction = CAMPAIGN.signal_mask_direction(
        frame, "DEFERRED_BASIS_REVERSION", params
    )
    assert mask.tolist() == [True, True]
    assert direction.tolist() == [-1, 1]


def test_delivery_direction_mapping_is_fixed(tmp_path: Path) -> None:
    path = tmp_path / "sge.parquet"
    _write_sge(path, pd.date_range("2024-01-01", periods=3, freq="D"))
    sge = CAMPAIGN.load_sge(path, 1)
    frame = CAMPAIGN.prepare_features(_h1(), sge, _config())
    signs = frame.loc[frame["delivery_direction_sign"].notna(), "delivery_direction_sign"]
    assert set(signs.astype(int)) == {-1, 1}


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
