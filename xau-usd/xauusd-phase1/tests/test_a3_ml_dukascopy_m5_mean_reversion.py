from __future__ import annotations

import copy
import json
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pandas as pd
import pytest


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ml.a3_meta_v1.dukascopy_m5_mean_reversion import (  # noqa: E402
    _fade_signal,
    _h1_range_allows,
    _m5_frame,
    _validate_contract,
)


def _contract() -> dict:
    return json.loads(
        (
            ROOT
            / "config"
            / "ml"
            / "a3_ml_dukascopy_m5_mean_reversion_train.json"
        ).read_text(encoding="utf-8")
    )


def _row(**overrides: float) -> dict:
    row = {
        "atr": 2.0,
        "zscore": 2.2,
        "rsi": 75.0,
        "prior_high": 101.0,
        "prior_low": 99.0,
        "three_bar_move": 3.2,
        "bid_open": 100.5,
        "bid_high": 101.5,
        "bid_low": 100.0,
        "bid_close": 101.4,
    }
    row.update(overrides)
    return row


def test_contract_freezes_matrix_and_rejects_validation_access() -> None:
    contract = _contract()
    _validate_contract(contract)
    changed = copy.deepcopy(contract)
    changed["authorization"]["validation_outcomes_authorized"] = True
    with pytest.raises(ValueError, match="requires validation_outcomes_authorized=false"):
        _validate_contract(changed)


def test_band_fade_uses_zscore_and_rsi_extremes() -> None:
    signal = _contract()["signal"]
    assert _fade_signal("BAND_FADE", _row(), signal)[0] == "SHORT"
    long_row = _row(zscore=-2.2, rsi=25.0, bid_open=99.5, bid_close=98.6)
    assert _fade_signal("BAND_FADE", long_row, signal)[0] == "LONG"
    assert _fade_signal("BAND_FADE", _row(rsi=60.0), signal)[0] is None


def test_impulse_fade_enters_against_three_bar_move() -> None:
    signal = _contract()["signal"]
    assert _fade_signal("IMPULSE_FADE", _row(), signal)[0] == "SHORT"
    long_row = _row(
        three_bar_move=-3.2,
        bid_open=99.5,
        bid_high=100.0,
        bid_low=98.5,
        bid_close=98.6,
    )
    assert _fade_signal("IMPULSE_FADE", long_row, signal)[0] == "LONG"


def test_sweep_fade_requires_close_back_inside_prior_extreme() -> None:
    signal = _contract()["signal"]
    short_row = _row(
        bid_open=101.2,
        bid_high=101.4,
        bid_low=100.0,
        bid_close=100.4,
    )
    assert _fade_signal("SWEEP_FADE", short_row, signal)[0] == "SHORT"
    assert _fade_signal(
        "SWEEP_FADE", _row(bid_high=101.4, bid_close=101.2), signal
    )[0] is None


def test_h1_range_gate_uses_normalized_separation_and_slope() -> None:
    signal = _contract()["signal"]
    row = {"atr": 10.0, "ema_fast": 100.0, "ema_slow": 97.0, "ema_fast_prior": 99.0}
    assert _h1_range_allows(row, signal)
    row["ema_slow"] = 90.0
    assert not _h1_range_allows(row, signal)


def _bars(count: int = 80) -> list[dict]:
    start = datetime(2020, 1, 1, tzinfo=UTC)
    rows = []
    for index in range(count):
        close = 1500.0 + 0.1 * index
        rows.append(
            {
                "timestamp_ms": int((start + timedelta(minutes=5 * index)).timestamp() * 1000),
                "bid_open": close - 0.1,
                "bid_high": close + 0.3,
                "bid_low": close - 0.3,
                "bid_close": close,
                "tick_count": 10,
            }
        )
    return rows


def test_future_bar_does_not_change_prior_indicators() -> None:
    contract = _contract()
    baseline = _m5_frame(_bars(), contract)
    changed = _bars()
    changed.append(
        {
            "timestamp_ms": changed[-1]["timestamp_ms"] + 300_000,
            "bid_open": 9990.0,
            "bid_high": 10010.0,
            "bid_low": 9980.0,
            "bid_close": 10000.0,
            "tick_count": 10,
        }
    )
    rerun = _m5_frame(changed, contract).iloc[: len(baseline)]
    for column in ("atr", "zscore", "rsi", "prior_high", "prior_low", "three_bar_move"):
        pd.testing.assert_series_equal(
            baseline[column].reset_index(drop=True),
            rerun[column].reset_index(drop=True),
            check_names=False,
        )


def test_wilder_rsi_handles_one_sided_price_changes() -> None:
    frame = _m5_frame(_bars(), _contract())
    assert frame["rsi"].dropna().iloc[-1] == pytest.approx(100.0)
