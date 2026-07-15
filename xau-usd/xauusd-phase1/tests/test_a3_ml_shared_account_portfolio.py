from __future__ import annotations

from datetime import UTC, datetime

import numpy as np

from ml.a3_meta_v1.shared_account_portfolio import (
    _max_drawdown,
    _overlap_metrics,
    _profit_factor,
    _six_month_blocks,
)


def test_overlap_counts_same_and_opposite_direction_entries() -> None:
    rows = [
        _trade("T1", "2024-01-01T10:00:00Z", "2024-01-01T12:00:00Z", "LONG"),
        _trade("T2", "2024-01-01T11:00:00Z", "2024-01-01T13:00:00Z", "LONG"),
        _trade("T3", "2024-01-01T11:30:00Z", "2024-01-01T12:30:00Z", "SHORT"),
    ]
    result = _overlap_metrics(rows)
    assert result["maximum_concurrent_trades"] == 3
    assert result["same_direction_overlap_entries"] == 1
    assert result["opposite_direction_overlap_entries"] == 1


def test_drawdown_and_profit_factor_use_losses_correctly() -> None:
    values = np.asarray([10.0, -4.0, -8.0, 6.0])
    assert _max_drawdown(values) == 12.0
    assert _profit_factor(values) == 16.0 / 12.0


def test_six_month_blocks_do_not_cross_scope() -> None:
    rows = [
        {**_trade("T1", "2024-02-01T00:00:00Z", "2024-02-02T00:00:00Z", "LONG"), "stress_profit_usd": 10.0},
        {**_trade("T2", "2024-08-01T00:00:00Z", "2024-08-02T00:00:00Z", "LONG"), "stress_profit_usd": -2.0},
    ]
    blocks = _six_month_blocks(
        rows,
        datetime(2024, 1, 1, tzinfo=UTC),
        datetime(2025, 1, 1, tzinfo=UTC),
    )
    assert [row["stress_net_usd"] for row in blocks] == [10.0, -2.0]


def _trade(trade_id: str, entry: str, exit_: str, direction: str) -> dict[str, object]:
    return {
        "trade_id": trade_id,
        "entry_dt": datetime.fromisoformat(entry.replace("Z", "+00:00")),
        "exit_dt": datetime.fromisoformat(exit_.replace("Z", "+00:00")),
        "direction": direction,
        "volume": 0.01,
        "source": "source",
    }
