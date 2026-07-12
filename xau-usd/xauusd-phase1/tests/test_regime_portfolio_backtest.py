from __future__ import annotations

from datetime import datetime, timezone

import pytest

from ml.a3_meta_v1.regime_portfolio_backtest import _max_drawdown, _stats, _validate_rows


def _row(source: str, direction: str, exit_time: str, profit: float) -> dict[str, object]:
    entry = datetime.fromisoformat("2026-01-01T00:00:00+00:00")
    exit_dt = datetime.fromisoformat(exit_time.replace("Z", "+00:00")).astimezone(timezone.utc)
    return {
        "source": source,
        "assigned_regime": "R1" if direction == "LONG" else "R2",
        "entry_time": "2026.01.01 00:00:00",
        "entry_time_dt": entry,
        "exit_time": exit_dt.strftime("%Y.%m.%d %H:%M:%S"),
        "exit_time_dt": exit_dt,
        "direction": direction,
        "volume": 0.01,
        "entry_price": 2000.0,
        "exit_price": 2010.0,
        "profit_usd": profit,
        "stress_profit_usd": profit - 0.30,
        "exit_comment": "",
    }


def test_stats_include_stress_and_drawdown() -> None:
    rows = [
        _row("r1_box_clean_strict_uptrend", "LONG", "2026-01-02T00:00:00Z", 10.0),
        _row("r2_pullback_short_h1_confirm", "SHORT", "2026-01-03T00:00:00Z", -4.0),
        _row("r1_box_clean_strict_uptrend", "LONG", "2026-01-04T00:00:00Z", 6.0),
    ]
    rows[2]["entry_time"] = "2026.01.02 00:00:00"
    _validate_rows(rows)
    stats = _stats(rows)
    assert stats["net_usd"] == 12.0
    assert stats["stress_net_usd"] == 11.1
    assert stats["profit_factor"] == 4.0
    assert stats["max_closed_drawdown_usd"] == 4.3


def test_rejects_wrong_direction() -> None:
    rows = [_row("r1_box_clean_strict_uptrend", "SHORT", "2026-01-02T00:00:00Z", 10.0)]
    with pytest.raises(ValueError, match="source direction mismatch"):
        _validate_rows(rows)


def test_max_drawdown_uses_chronological_profit_path() -> None:
    assert _max_drawdown([5.0, -2.0, -7.0, 3.0]) == 9.0
