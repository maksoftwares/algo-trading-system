from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.scenario import should_veto_monthly, utc_month


POLICY = {
    "minimum_closed_trades_in_month": 8,
    "maximum_month_pnl_usd_exclusive": -20.0,
    "maximum_causal_rank_exclusive": 0.4,
}


def test_month_key_is_utc() -> None:
    stamp = int(datetime(2026, 8, 31, 23, 59, tzinfo=UTC).timestamp() * 1000)
    assert utc_month(stamp) == "2026-08"


@pytest.mark.parametrize(
    ("closed", "pnl", "rank", "expected"),
    [
        (7, -100.0, 0.0, False),
        (8, -20.0, 0.0, False),
        (8, -20.01, 0.40, False),
        (8, -20.01, 0.39, True),
        (8, -20.01, None, False),
        (8, -20.01, float("nan"), False),
    ],
)
def test_veto_boundaries(closed: int, pnl: float, rank: float | None, expected: bool) -> None:
    assert should_veto_monthly(
        closed_trades=closed,
        closed_pnl_usd=pnl,
        causal_rank=rank,
        policy=POLICY,
    ) is expected


def test_nonfinite_month_pnl_rejected() -> None:
    with pytest.raises(ValueError, match="finite"):
        should_veto_monthly(
            closed_trades=8,
            closed_pnl_usd=float("nan"),
            causal_rank=0.1,
            policy=POLICY,
        )
