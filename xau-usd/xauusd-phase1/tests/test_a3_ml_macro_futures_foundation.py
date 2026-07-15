from __future__ import annotations

import io
import json
import zipfile
from pathlib import Path

import pandas as pd
import pytest

from ml.a3_meta_v1.macro_futures_foundation import (
    MacroFuturesFoundationError,
    _asof_join_market,
    _build_daily_features,
    _read_cftc,
    _read_fred,
    _validate_daily_features,
    _validate_enriched,
)


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "config/ml/a3_ml_macro_futures_foundation_v1.json"


def test_contract_freezes_conservative_source_lags() -> None:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    lags = {row["series_id"]: row["availability_lag_days"] for row in contract["fred_series"]}
    assert lags == {"DFII5": 1, "DFII10": 1, "DGS2": 1, "DGS10": 1, "DTWEXBGS": 7}
    assert contract["cftc"]["contract_market_code"] == "088691"
    assert contract["cftc"]["conservative_release_hour_utc"] == 21


def test_fred_reader_applies_availability_lag(tmp_path: Path) -> None:
    path = tmp_path / "fred.csv"
    path.write_text("observation_date,DFII10\n2024-01-02,1.75\n", encoding="utf-8")
    frame = _read_fred(
        path,
        {"series_id": "DFII10", "column": "real_yield_10y", "availability_lag_days": 1},
    )
    assert frame.iloc[0]["available_at_utc"] == pd.Timestamp("2024-01-03T00:00:00Z")
    assert frame.iloc[0]["real_yield_10y"] == 1.75


def test_cftc_reader_filters_comex_gold_and_delays_until_friday(tmp_path: Path) -> None:
    rows = pd.DataFrame(
        [
            _cot_row("088691", "2024-01-02", 1000),
            _cot_row("088695", "2024-01-02", 2000),
        ]
    )
    path = tmp_path / "cot.zip"
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("f_year.txt", rows.to_csv(index=False))
    frame = _read_cftc(
        path,
        {"contract_market_code": "088691", "release_delay_days": 3, "conservative_release_hour_utc": 21},
    )
    assert len(frame) == 1
    assert frame.iloc[0]["available_at_utc"] == pd.Timestamp("2024-01-05T21:00:00Z")
    assert frame.iloc[0]["cot_open_interest"] == 1000


def test_asof_join_never_uses_future_macro_or_cot() -> None:
    market = pd.DataFrame(
        {
            "timestamp_ms": [
                int(pd.Timestamp("2024-01-05T20:55:00Z").timestamp() * 1000),
                int(pd.Timestamp("2024-01-05T21:00:00Z").timestamp() * 1000),
            ]
        }
    )
    daily = pd.DataFrame(
        {
            "available_at_utc": pd.to_datetime(
                ["2024-01-03T00:00:00Z", "2024-01-05T21:00:00Z"]
            ),
            "macro_available_at_utc": pd.to_datetime(["2024-01-03T00:00:00Z", "2024-01-03T00:00:00Z"]),
            "cot_available_at_utc": pd.to_datetime(
                ["2023-12-29T21:00:00Z", "2024-01-05T21:00:00Z"], utc=True
            ),
            "real_yield_10y": [1.5, 1.5],
            "cot_open_interest": [900.0, 1000.0],
        }
    )
    joined = _asof_join_market(market, daily)
    assert joined.iloc[0]["cot_open_interest"] == 900.0
    assert joined.iloc[1]["cot_open_interest"] == 1000.0
    assert joined.iloc[0]["macro_available_at_ms"] == int(
        pd.Timestamp("2024-01-03T00:00:00Z").timestamp() * 1000
    )
    assert joined.iloc[1]["cot_available_at_ms"] == int(
        pd.Timestamp("2024-01-05T21:00:00Z").timestamp() * 1000
    )
    _validate_enriched(joined)


def test_daily_validator_rejects_duplicate_availability() -> None:
    frame = pd.DataFrame(
        {"available_at_utc": pd.to_datetime(["2024-01-01T00:00:00Z", "2024-01-01T00:00:00Z"])}
    )
    with pytest.raises(MacroFuturesFoundationError, match="unique and sorted"):
        _validate_daily_features(
            frame,
            pd.Timestamp("2024-01-01T00:00:00Z"),
            pd.Timestamp("2024-01-10T00:00:00Z"),
        )


def test_daily_features_are_backward_looking() -> None:
    dates = pd.date_range("2024-01-01", periods=25, tz="UTC")
    fred = pd.DataFrame(
        {
            "available_at_utc": dates,
            "real_yield_5y": range(25),
            "real_yield_10y": range(1, 26),
            "nominal_yield_2y": range(2, 27),
            "nominal_yield_10y": range(4, 29),
            "broad_usd_index": range(100, 125),
        }
    )
    cot = pd.DataFrame([_cot_feature_row("2024-01-05T21:00:00Z"), _cot_feature_row("2024-01-12T21:00:00Z")])
    result = _build_daily_features(fred, cot)
    row = result[result["available_at_utc"] == pd.Timestamp("2024-01-21T00:00:00Z")].iloc[0]
    assert row["real_yield_10y_change_20"] == 20
    assert row["cot_open_interest"] == 1000


def _cot_row(code: str, date: str, open_interest: int) -> dict[str, object]:
    return {
        "CFTC_Contract_Market_Code": code,
        "Report_Date_as_YYYY-MM-DD": date,
        "Open_Interest_All": open_interest,
        "M_Money_Positions_Long_All": 400,
        "M_Money_Positions_Short_All": 300,
        "Prod_Merc_Positions_Long_All": 200,
        "Prod_Merc_Positions_Short_All": 500,
        "Swap_Positions_Long_All": 250,
        "Swap__Positions_Short_All": 150,
    }


def _cot_feature_row(date: str) -> dict[str, object]:
    return {
        "available_at_utc": pd.Timestamp(date),
        "cot_open_interest": 1000,
        "cot_managed_money_long": 400,
        "cot_managed_money_short": 300,
        "cot_producer_long": 200,
        "cot_producer_short": 500,
        "cot_swap_long": 250,
        "cot_swap_short": 150,
    }
