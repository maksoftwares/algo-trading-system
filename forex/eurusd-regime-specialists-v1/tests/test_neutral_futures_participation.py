from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PACKAGE_ROOT / "src"))

from eurusd_regime_specialists.neutral_futures_participation import (  # noqa: E402
    attach_exchange_sources,
    prepare_exchange_source,
)


def source_frame(
    start: str,
    periods: int,
    *,
    returns: list[float] | None = None,
    volumes: list[float] | None = None,
) -> pd.DataFrame:
    dates = pd.bdate_range(start, periods=periods)
    returns = returns or [0.01] * periods
    volumes = volumes or list(range(1, periods + 1))
    return pd.DataFrame(
        {
            "trade_date": dates.strftime("%Y-%m-%d"),
            "open": [100.0] * periods,
            "high": [102.0] * periods,
            "low": [98.0] * periods,
            "close": [100.0 * (1.0 + value) for value in returns],
            "volume": volumes,
            "source_row_valid": [True] * periods,
        }
    )


def config() -> dict:
    return {
        "candidate": {
            "volume_baseline_sessions": 20,
            "maximum_source_age_hours": 96,
            "minimum_participation_score": 1.0,
        }
    }


def test_volume_baseline_excludes_current_session() -> None:
    volumes = list(range(1, 21)) + [1000.0]
    prepared = prepare_exchange_source(
        source_frame(
            "2024-01-01", 21, volumes=volumes
        ),
        baseline_sessions=20,
        prefix="euro",
    )
    last = prepared.iloc[-1]
    assert last["euro_volume_ratio"] == 1000.0 / 10.5


def test_source_is_not_available_until_following_midnight() -> None:
    euro = source_frame("2024-01-01", 21)
    dollar = source_frame(
        "2024-01-01",
        21,
        returns=[-0.01] * 21,
    )
    final_trade_date = pd.Timestamp(
        euro.iloc[-1]["trade_date"], tz="UTC"
    )
    candidates = pd.DataFrame(
        {
            "completion_time_utc": [
                final_trade_date,
                final_trade_date + pd.Timedelta(days=1),
            ]
        }
    )
    attached = attach_exchange_sources(
        candidates, euro, dollar, config()
    )
    assert (
        attached.iloc[0]["euro_trade_date"]
        < final_trade_date.tz_localize(None)
    )
    assert (
        attached.iloc[1]["euro_trade_date"]
        == final_trade_date.tz_localize(None)
    )


def test_agreement_and_joint_participation_select_side() -> None:
    euro = source_frame(
        "2024-01-01",
        21,
        returns=[0.01] * 21,
        volumes=[100.0] * 20 + [121.0],
    )
    dollar = source_frame(
        "2024-01-01",
        21,
        returns=[-0.01] * 21,
        volumes=[100.0] * 20 + [100.0],
    )
    decision = (
        pd.Timestamp(euro.iloc[-1]["trade_date"], tz="UTC")
        + pd.Timedelta(days=1)
    )
    candidates = pd.DataFrame(
        {"completion_time_utc": [decision]}
    )
    attached = attach_exchange_sources(
        candidates, euro, dollar, config()
    )
    row = attached.iloc[0]
    assert row["direction_agreement"]
    assert np.isclose(row["participation_score"], 1.1)
    assert row["trade_candidate"]
    assert row["side"] == "LONG"


def test_disagreement_remains_cash() -> None:
    euro = source_frame(
        "2024-01-01",
        21,
        returns=[0.01] * 21,
        volumes=[100.0] * 21,
    )
    dollar = source_frame(
        "2024-01-01",
        21,
        returns=[0.01] * 21,
        volumes=[100.0] * 21,
    )
    decision = (
        pd.Timestamp(euro.iloc[-1]["trade_date"], tz="UTC")
        + pd.Timedelta(days=1)
    )
    attached = attach_exchange_sources(
        pd.DataFrame(
            {"completion_time_utc": [decision]}
        ),
        euro,
        dollar,
        config(),
    )
    assert not attached.iloc[0]["direction_agreement"]
    assert not attached.iloc[0]["trade_candidate"]
    assert attached.iloc[0]["side"] == "CASH"
