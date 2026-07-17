from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

import pandas as pd
import pytest


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "src" / "cftc_gold_options_positioning" / "foundation.py"
SPEC = importlib.util.spec_from_file_location("cftc_options_foundation_tests", MODULE_PATH)
if SPEC is None or SPEC.loader is None:
    raise ImportError(MODULE_PATH)
FOUNDATION = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = FOUNDATION
SPEC.loader.exec_module(FOUNDATION)


def _source(kind: str, missing_second: bool = False) -> pd.DataFrame:
    dates = ["2024-01-02", "2024-01-09"]
    if missing_second:
        dates = dates[:1]
    rows = []
    offset = 100.0 if kind == "combined" else 0.0
    for index, report_date in enumerate(dates):
        row = {
            "id": f"{kind}-{index}",
            "market_and_exchange_names": "GOLD - COMMODITY EXCHANGE INC.",
            "report_date_as_yyyy_mm_dd": report_date,
            "cftc_contract_market_code": FOUNDATION.CONTRACT_CODE,
            "open_interest_all": 1000.0 + offset + index,
        }
        for columns in FOUNDATION.POSITION_COLUMNS.values():
            for column in columns:
                if column is not None:
                    row[column] = 200.0 + offset + index
        rows.append(row)
    return pd.DataFrame(rows)


def test_build_pairs_reports_and_uses_following_monday() -> None:
    result = FOUNDATION.build_curated_frame(_source("combined"), _source("futures"))
    assert len(result) == 2
    assert result.loc[0, "available_utc"] == pd.Timestamp("2024-01-08T00:00:00Z")
    assert result.loc[0, "options_open_interest_delta_equivalent"] == 100.0
    assert result.loc[0, "managed_money_options_long"] == 100.0
    assert result.loc[0, "managed_money_options_net"] == 0.0
    assert result.loc[0, "managed_money_combined_net"] == 0.0
    assert result.loc[0, "managed_money_futures_net"] == 0.0


def test_unpaired_report_dates_fail_closed() -> None:
    with pytest.raises(ValueError, match="Unpaired CFTC report dates"):
        FOUNDATION.build_curated_frame(
            _source("combined"), _source("futures", missing_second=True)
        )


def test_duplicate_report_dates_fail_closed() -> None:
    duplicate = pd.concat([_source("combined"), _source("combined").iloc[[0]]])
    with pytest.raises(ValueError, match="Duplicate combined"):
        FOUNDATION.build_curated_frame(duplicate, _source("futures"))
