from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pandas as pd
import pytest

from ml.a3_meta_v1.intraday_macro_source import (
    EXPECTED_SYMBOLS,
    IntradayMacroSourceError,
    active_day_coverage,
    build_combined_m5,
    classify_source,
    contract_months,
    install_locked_instruments,
    validate_contract,
)


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "config/ml/a3_ml_intraday_macro_source_v1.json"


def _contract() -> dict:
    return json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))


def test_contract_is_source_only_and_locks_ninety_months() -> None:
    contract = _contract()
    validate_contract(contract)
    months = contract_months(contract)
    assert len(months) == 90
    assert months[0] == "2019-01"
    assert months[-1] == "2026-06"
    assert contract["research_controls"]["gold_outcome_join_authorized"] is False
    assert contract["authorization"]["broker_action_authorized"] is False


def test_contract_rejects_new_instrument_or_execution_authority() -> None:
    contract = _contract()
    contract["instruments"][0]["source_code"] = "OTHER"
    with pytest.raises(IntradayMacroSourceError, match="instrument lock"):
        validate_contract(contract)
    contract = _contract()
    contract["authorization"]["python_demo_predictions_authorized"] = True
    with pytest.raises(IntradayMacroSourceError, match="execution"):
        validate_contract(contract)


def test_locked_instruments_are_installed_without_extending_timeframes() -> None:
    foundation = SimpleNamespace()
    install_locked_instruments(foundation, _contract())
    assert tuple(foundation.INSTRUMENTS) == EXPECTED_SYMBOLS
    assert foundation.INSTRUMENTS["DOLLARIDXUSD"]["source_code"] == "DOLLAR.IDX-USD"
    assert foundation.TIMEFRAMES_MINUTES == {"M5": 5}
    assert foundation.PRICE_BASES == ("Bid", "Ask", "Mid")


def _write_bar(path: Path, timestamps: list[int], offset: float) -> None:
    frame = pd.DataFrame(
        {
            "timestamp_ms": timestamps,
            "open": [100.0 + offset + index for index in range(len(timestamps))],
            "high": [101.0 + offset + index for index in range(len(timestamps))],
            "low": [99.0 + offset + index for index in range(len(timestamps))],
            "close": [100.5 + offset + index for index in range(len(timestamps))],
            "volume": [10.0, 11.0],
            "tick_count": [2, 3],
        }
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_parquet(path, index=False)


def test_combined_m5_preserves_symbol_availability(tmp_path: Path) -> None:
    contract = _contract()
    contract["window"]["start_utc"] = "2019-01-01T00:00:00Z"
    contract["window"]["end_exclusive_utc"] = "2019-02-01T00:00:00Z"
    contract["window"]["expected_months_per_instrument"] = 1
    first = int(pd.Timestamp("2019-01-02T12:00:00Z").timestamp() * 1000)
    timestamps = [first, first + 300_000]
    for symbol_index, symbol in enumerate(EXPECTED_SYMBOLS):
        for basis_index, basis in enumerate(("Bid", "Ask", "Mid")):
            _write_bar(
                tmp_path
                / "bars"
                / symbol
                / basis.lower()
                / "M5"
                / "year=2019"
                / "month=01"
                / "bars.parquet",
                timestamps,
                symbol_index * 10.0 + basis_index,
            )
    output = tmp_path / "combined.parquet"
    result = build_combined_m5(tmp_path, contract, output)
    combined = pd.read_parquet(output)
    assert result["rows"] == 2
    assert combined["dollaridxusd_available"].all()
    assert combined["ustbondtrusd_available"].all()
    assert combined.loc[0, "dollaridxusd_bid_open"] == 100.0
    assert combined.loc[0, "ustbondtrusd_mid_open"] == 112.0


def test_active_day_coverage_uses_xau_days_as_denominator() -> None:
    day = pd.Timestamp("2024-01-02T00:00:00Z")
    source = pd.DataFrame(
        {
            "timestamp_utc": [day, day + pd.Timedelta(days=1)],
            "dollaridxusd_available": [True, True],
            "ustbondtrusd_available": [True, False],
        }
    )
    xau = pd.DataFrame(
        {
            "timestamp_ms": [
                int(day.timestamp() * 1000),
                int((day + pd.Timedelta(days=1)).timestamp() * 1000),
            ]
        }
    )
    rows = {row["symbol"]: row for row in active_day_coverage(source, xau)}
    assert rows["DOLLARIDXUSD"]["active_source_day_share_vs_xau"] == 1.0
    assert rows["USTBONDTRUSD"]["active_source_day_share_vs_xau"] == 0.5


@pytest.mark.parametrize(
    ("arguments", "expected"),
    [
        (
            dict(
                metadata_valid=True,
                complete=True,
                integrity_valid=True,
                coverage_valid=True,
                deterministic=True,
            ),
            "INTRADAY_MACRO_SOURCE_VALID",
        ),
        (
            dict(
                metadata_valid=True,
                complete=False,
                integrity_valid=True,
                coverage_valid=True,
                deterministic=True,
            ),
            "INTRADAY_MACRO_SOURCE_PARTIAL_NOT_READY",
        ),
        (
            dict(
                metadata_valid=True,
                complete=True,
                integrity_valid=True,
                coverage_valid=False,
                deterministic=True,
            ),
            "INTRADAY_MACRO_SOURCE_INVALID",
        ),
    ],
)
def test_source_classification(arguments: dict, expected: str) -> None:
    assert classify_source(**arguments) == expected
