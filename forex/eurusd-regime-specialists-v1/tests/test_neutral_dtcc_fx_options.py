from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PACKAGE_ROOT))
sys.path.insert(0, str(PACKAGE_ROOT / "src"))

from download_neutral_dtcc_fx_options import qualified_trade  # noqa: E402
from eurusd_regime_specialists.neutral_dtcc_fx_options import (  # noqa: E402
    attach_dtcc_source,
    prepare_dtcc_source,
)


def source_frame(
    *,
    call_notional: list[float],
    put_notional: list[float],
    call_premium: list[float] | None = None,
    put_premium: list[float] | None = None,
) -> pd.DataFrame:
    dates = pd.bdate_range("2025-01-01", periods=len(call_notional))
    calls = call_premium or call_notional
    puts = put_premium or put_notional
    return pd.DataFrame(
        {
            "trade_date": dates,
            "available_time_utc": (
                dates + pd.Timedelta(days=1)
            ).tz_localize("UTC"),
            "call_qualified_trades": [1] * len(dates),
            "put_qualified_trades": [1] * len(dates),
            "call_eur_notional": call_notional,
            "put_eur_notional": put_notional,
            "call_usd_premium": calls,
            "put_usd_premium": puts,
            "qualified_total_trades": [2] * len(dates),
        }
    )


def config(maximum_age_hours: int = 96) -> dict:
    return {
        "candidate": {
            "baseline_sessions": 20,
            "maximum_source_age_hours": maximum_age_hours,
        }
    }


def test_baselines_exclude_current_source_session() -> None:
    frame = source_frame(
        call_notional=[100.0] * 20 + [400.0],
        put_notional=[100.0] * 21,
        call_premium=[10.0] * 20 + [40.0],
        put_premium=[10.0] * 21,
    )
    prepared = prepare_dtcc_source(frame, baseline_sessions=20)
    row = prepared.iloc[-1]
    assert np.isclose(row["prior_notional_imbalance_median"], 0.0)
    assert np.isclose(row["prior_premium_imbalance_median"], 0.0)
    assert row["composite_imbalance"] > 0


def test_call_notional_and_premium_flow_select_long() -> None:
    frame = source_frame(
        call_notional=[100.0] * 20 + [400.0],
        put_notional=[100.0] * 21,
        call_premium=[10.0] * 20 + [40.0],
        put_premium=[10.0] * 21,
    )
    decision = frame.iloc[-1]["available_time_utc"]
    attached = attach_dtcc_source(
        pd.DataFrame({"completion_time_utc": [decision]}),
        frame,
        config(),
    )
    assert attached.iloc[0]["trade_candidate"]
    assert attached.iloc[0]["side"] == "LONG"


def test_source_older_than_frozen_tolerance_remains_cash() -> None:
    frame = source_frame(
        call_notional=[100.0] * 20 + [400.0],
        put_notional=[100.0] * 21,
    )
    decision = (
        frame.iloc[-1]["available_time_utc"]
        + pd.Timedelta(hours=97)
    )
    attached = attach_dtcc_source(
        pd.DataFrame({"completion_time_utc": [decision]}),
        frame,
        config(),
    )
    assert not attached.iloc[0]["trade_candidate"]
    assert attached.iloc[0]["side"] == "CASH"


def valid_raw_trade() -> dict:
    return {
        "actionType": "NEWT",
        "eventType": "TRAD",
        "packageIndicator": "FALSE",
        "uniqueProductIdentifierUnderlierName": "EUR USD",
        "uniqueProductIdentifierShortName": (
            "NA%2FO%20Van%20Call%20EUR%20USD"
        ),
        "disseminationIdentifier": "123",
        "disseminationTimestamp": "2026-07-24T12:01:00Z",
        "executionTimestamp": "2026-07-24T12:00:00Z",
        "expirationDate": "2026-08-24",
        "callCurrencyLeg1": "EUR",
        "callAmountLeg1": "1,000,000",
        "optionPremiumCurrency": "USD",
        "optionPremiumAmount": "12,500",
    }


def test_downloader_accepts_only_causal_standalone_new_trade() -> None:
    parsed = qualified_trade(
        valid_raw_trade(),
        "CALL",
        pd.Timestamp("2026-07-24"),
    )
    assert parsed is not None
    assert parsed["eur_notional"] == 1_000_000
    assert parsed["usd_premium"] == 12_500


def test_downloader_rejects_package_trade() -> None:
    row = valid_raw_trade()
    row["packageIndicator"] = "TRUE"
    assert (
        qualified_trade(
            row,
            "CALL",
            pd.Timestamp("2026-07-24"),
        )
        is None
    )
