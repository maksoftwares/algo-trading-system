from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PACKAGE_ROOT / "src"))

from eurusd_regime_specialists.neutral_coinbase_stablecoin_flow import (  # noqa: E402
    build_decisions,
    build_product_signals,
)


def config() -> dict:
    return {
        "flow_rule": {"completed_m5_bars_per_product": 3},
        "windows": {
            "test": [
                "2025-01-01T00:00:00Z",
                "2025-12-31T23:59:59Z",
            ]
        },
        "outcome_blind_census": {},
    }


def source(*, gap: bool = False) -> pd.DataFrame:
    rows = []
    times = pd.date_range(
        "2025-01-01T23:45:00Z",
        periods=6,
        freq="5min",
    )
    if gap:
        times = times.delete(1)
    for product, moves in (
        ("USDC-EUR", [-1, -1, -1, 1, 1, 1]),
        ("USDT-EUR", [-1, -1, -1, -1, -1, -1]),
    ):
        for index, stamp in enumerate(times):
            move = moves[index]
            open_price = 0.96
            close = open_price + move * 0.0001
            rows.append(
                {
                    "product": product,
                    "eligible_date": "2025-01-02",
                    "open_time_utc": stamp,
                    "close_time_utc": stamp
                    + pd.Timedelta(minutes=5),
                    "open": open_price,
                    "high": max(open_price, close),
                    "low": min(open_price, close),
                    "close": close,
                    "base_volume": 100.0,
                }
            )
    return pd.DataFrame(rows)


def parent() -> pd.DataFrame:
    entries = pd.to_datetime(
        [
            "2025-01-02T00:00:00Z",
            "2025-01-02T00:15:00Z",
        ],
        utc=True,
    )
    return pd.DataFrame(
        {
            "entry_time_utc": entries,
            "eligible_date": ["2025-01-02"] * 2,
            "decision_id": ["A", "B"],
            "clock_minute": [0, 15],
        }
    )


def test_signed_volume_is_inverted_into_euro_terms() -> None:
    signals = build_product_signals(source(), config())
    first = signals[
        signals["entry_time_utc"].eq(
            pd.Timestamp("2025-01-02T00:00:00Z")
        )
    ]
    assert len(first) == 2
    assert np.allclose(
        first["euro_signed_volume_pressure_15m"], [1.0, 1.0]
    )


def test_agreement_trades_and_disagreement_is_cash() -> None:
    signals = build_product_signals(source(), config())
    decisions, census = build_decisions(
        parent(),
        signals,
        config(),
        enforce_frozen_census=False,
    )
    assert decisions["flow_side"].tolist() == ["LONG"]
    assert census["both_products_valid_points"] == 2
    assert census["agreement_candidates"] == 1
    assert census["valid_product_sign_disagreements"] == 1


def test_gap_invalidates_only_affected_decision() -> None:
    signals = build_product_signals(source(gap=True), config())
    decisions, census = build_decisions(
        parent(),
        signals,
        config(),
        enforce_frozen_census=False,
    )
    assert decisions.empty
    assert census["missing_or_invalid_product_points"] >= 1
