from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PACKAGE_ROOT))
sys.path.insert(0, str(PACKAGE_ROOT / "src"))

from build_neutral_dtcc_skew_source import match_session  # noqa: E402
from eurusd_regime_specialists.neutral_dtcc_skew import (  # noqa: E402
    attach_dtcc_skew,
    prepare_dtcc_skew,
)


def daily_source(skews: list[float]) -> pd.DataFrame:
    dates = pd.bdate_range("2025-01-01", periods=len(skews))
    return pd.DataFrame(
        {
            "report_date": dates,
            "available_time_utc": (
                dates + pd.Timedelta(days=1)
            ).tz_localize("UTC"),
            "matched_pairs": [5] * len(dates),
            "daily_log_premium_skew": skews,
            "median_pair_score": [0.2] * len(dates),
            "source_eligible": [True] * len(dates),
        }
    )


def config(maximum_age_hours: int = 96) -> dict:
    return {
        "candidate": {
            "baseline_sessions": 20,
            "maximum_source_age_hours": maximum_age_hours,
        }
    }


def test_skew_baseline_excludes_current_session() -> None:
    prepared = prepare_dtcc_skew(
        daily_source([0.0] * 20 + [0.5]),
        baseline_sessions=20,
    )
    row = prepared.iloc[-1]
    assert np.isclose(row["prior_skew_median"], 0.0)
    assert np.isclose(row["normalized_skew"], 0.5)


def test_positive_normalized_skew_selects_long() -> None:
    source = daily_source([0.0] * 20 + [0.5])
    decision = source.iloc[-1]["available_time_utc"]
    attached = attach_dtcc_skew(
        pd.DataFrame({"completion_time_utc": [decision]}),
        source,
        config(),
    )
    assert attached.iloc[0]["trade_candidate"]
    assert attached.iloc[0]["side"] == "LONG"


def test_stale_skew_session_remains_cash() -> None:
    source = daily_source([0.0] * 20 + [0.5])
    decision = (
        source.iloc[-1]["available_time_utc"]
        + pd.Timedelta(hours=97)
    )
    attached = attach_dtcc_skew(
        pd.DataFrame({"completion_time_utc": [decision]}),
        source,
        config(),
    )
    assert not attached.iloc[0]["trade_candidate"]
    assert attached.iloc[0]["side"] == "CASH"


def pairing_frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "report_date": [pd.Timestamp("2026-01-05")] * 4,
            "available_time_utc": [
                pd.Timestamp("2026-01-06", tz="UTC")
            ]
            * 4,
            "option_kind": ["CALL", "CALL", "PUT", "PUT"],
            "dissemination_identifier": ["c1", "c2", "p1", "p2"],
            "execution_timestamp": pd.to_datetime(
                [
                    "2026-01-05T12:00:00Z",
                    "2026-01-05T12:01:00Z",
                    "2026-01-05T12:02:00Z",
                    "2026-01-05T12:03:00Z",
                ],
                utc=True,
            ),
            "tenor_days": [30, 45, 31, 44],
            "absolute_log_moneyness": [
                0.0100,
                0.0200,
                0.0105,
                0.0195,
            ],
            "premium_rate": [0.020, 0.030, 0.010, 0.015],
        }
    )


def test_pairing_matches_without_reuse() -> None:
    pairs = match_session(pairing_frame())
    assert len(pairs) == 2
    assert len({row["call_id"] for row in pairs}) == 2
    assert len({row["put_id"] for row in pairs}) == 2
    assert all(row["pair_log_premium_skew"] > 0 for row in pairs)


def test_pairing_rejects_distant_moneyness() -> None:
    frame = pairing_frame()
    frame.loc[frame["option_kind"].eq("PUT"), "absolute_log_moneyness"] = (
        0.025
    )
    pairs = match_session(frame)
    assert len(pairs) == 0
