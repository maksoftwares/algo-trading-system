from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PACKAGE_ROOT / "src"))

from eurusd_regime_specialists.neutral_occ_fxe_flow import (  # noqa: E402
    attach_occ_source,
    prepare_occ_source,
)


def source_frame(
    *,
    calls: list[int],
    puts: list[int],
    records: list[bool] | None = None,
) -> pd.DataFrame:
    dates = pd.bdate_range("2025-01-01", periods=len(calls))
    return pd.DataFrame(
        {
            "trade_date": dates,
            "call_volume": calls,
            "put_volume": puts,
            "total_customer_volume": [
                call + put for call, put in zip(calls, puts)
            ],
            "source_has_records": records or [True] * len(calls),
            "available_time_utc": (
                dates + pd.Timedelta(days=1)
            ).tz_localize("UTC"),
        }
    )


def config() -> dict:
    return {
        "candidate": {
            "baseline_sessions": 20,
            "maximum_source_age_hours": 96,
            "minimum_participation_ratio": 1.0,
        }
    }


def test_flow_baselines_exclude_current_session() -> None:
    calls = [100] * 20 + [400]
    puts = [100] * 21
    prepared = prepare_occ_source(
        source_frame(calls=calls, puts=puts),
        baseline_sessions=20,
    )
    row = prepared.iloc[-1]
    assert np.isclose(row["prior_imbalance_median"], 0.0)
    assert row["normalized_imbalance"] > 0
    assert np.isclose(
        row["prior_total_volume_median"], 200.0
    )
    assert np.isclose(row["participation_ratio"], 2.5)


def test_latest_report_is_available_only_next_midnight() -> None:
    frame = source_frame(
        calls=[100] * 20 + [400],
        puts=[100] * 21,
    )
    final_date = frame.iloc[-1]["trade_date"]
    candidates = pd.DataFrame(
        {
            "completion_time_utc": [
                pd.Timestamp(final_date, tz="UTC"),
                pd.Timestamp(final_date, tz="UTC")
                + pd.Timedelta(days=1),
            ]
        }
    )
    attached = attach_occ_source(candidates, frame, config())
    assert attached.iloc[0]["trade_date"] < final_date
    assert attached.iloc[1]["trade_date"] == final_date


def test_normalized_call_flow_selects_long() -> None:
    frame = source_frame(
        calls=[100] * 20 + [400],
        puts=[100] * 21,
    )
    decision = (
        pd.Timestamp(frame.iloc[-1]["trade_date"], tz="UTC")
        + pd.Timedelta(days=1)
    )
    attached = attach_occ_source(
        pd.DataFrame(
            {"completion_time_utc": [decision]}
        ),
        frame,
        config(),
    )
    assert attached.iloc[0]["trade_candidate"]
    assert attached.iloc[0]["side"] == "LONG"


def test_no_record_report_remains_cash() -> None:
    records = [True] * 20 + [False]
    frame = source_frame(
        calls=[100] * 20 + [400],
        puts=[100] * 21,
        records=records,
    )
    decision = (
        pd.Timestamp(frame.iloc[-1]["trade_date"], tz="UTC")
        + pd.Timedelta(days=1)
    )
    attached = attach_occ_source(
        pd.DataFrame(
            {"completion_time_utc": [decision]}
        ),
        frame,
        config(),
    )
    assert not attached.iloc[0]["trade_candidate"]
    assert attached.iloc[0]["side"] == "CASH"
