from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from eurusd_regime_specialists.neutral_cme_options_surface import (
    REQUIRED_COLUMNS,
    black76_price,
    build_daily_risk_reversal,
    conservative_availability_utc,
    infer_forward_discount,
    prepare_euu_eod,
    verify_lock,
)


def _synthetic_euu_rows(skew_slope: float = 0.20) -> pd.DataFrame:
    trade_date = pd.Timestamp("2025-01-02T00:00:00Z")
    expiry_date = pd.Timestamp("2025-02-01T00:00:00Z")
    years = (expiry_date - trade_date).days / 365.0
    forward = 1.10
    discount = 0.997
    rows: list[dict[str, str]] = []
    for strike in np.arange(1.03, 1.181, 0.005):
        volatility = 0.09 + skew_slope * (strike - forward)
        for put_call in ("C", "P"):
            row = {column: "" for column in REQUIRED_COLUMNS}
            row.update(
                {
                    "Trade Date": "20250102",
                    "Exchange Code": "XCME",
                    "Asset Class": "FX",
                    "Product Code": "EUU",
                    "Product Type": "OPT",
                    "Put/Call": put_call,
                    "Strike Price": str(round(strike * 10_000)),
                    "Contract Year": "2025",
                    "Contract Month": "02",
                    "Settlement": f"{black76_price(forward, strike, years, volatility, discount, put_call):.10f}",
                    "Open Interest": "100",
                    "Total Volume": "10",
                    "Delta": "",
                    "Implied Volatility": "",
                    "Last Trade Date": "20250201",
                }
            )
            rows.append(row)
    return pd.DataFrame(rows)


def _surface_config() -> dict[str, object]:
    return {
        "surface": {
            "minimum_dte": 20,
            "maximum_dte": 45,
            "target_dte": 30,
            "target_abs_delta": 0.25,
            "maximum_abs_delta_distance": 0.08,
            "minimum_call_put_pairs": 7,
        }
    }


def test_surface_contract_is_hash_locked():
    assert len(verify_lock()) == 3


def test_euu_parser_requires_official_schema():
    with pytest.raises(ValueError, match="missing required columns"):
        prepare_euu_eod(pd.DataFrame({"Trade Date": ["20250102"]}))


def test_put_call_parity_recovers_forward_and_discount():
    prepared = prepare_euu_eod(_synthetic_euu_rows())
    forward, discount = infer_forward_discount(prepared)
    assert forward == pytest.approx(1.10, abs=1e-7)
    assert discount == pytest.approx(0.997, abs=1e-7)


def test_positive_25d_risk_reversal_fixes_long_without_outcomes():
    prepared = prepare_euu_eod(_synthetic_euu_rows())
    result = build_daily_risk_reversal(
        prepared, _surface_config()
    )
    assert len(result) == 1
    actual = result.iloc[0]
    assert actual["side"] == "LONG"
    assert actual["rr25_vol_points"] > 0
    assert actual["call25_abs_delta"] == pytest.approx(
        0.25, abs=0.08
    )
    assert actual["put25_abs_delta"] == pytest.approx(
        0.25, abs=0.08
    )
    assert actual["forward"] == pytest.approx(1.10, abs=1e-7)
    assert actual["availability_utc"] == pd.Timestamp(
        "2025-01-04T00:00:00Z"
    )


def test_final_release_lag_crosses_weekend_before_decision():
    friday = pd.Timestamp("2025-01-03T00:00:00Z")
    assert conservative_availability_utc(friday) == pd.Timestamp(
        "2025-01-07T00:00:00Z"
    )
