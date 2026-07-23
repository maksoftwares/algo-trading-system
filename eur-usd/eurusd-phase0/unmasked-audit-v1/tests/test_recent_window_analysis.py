from __future__ import annotations

import importlib.util
import sys
from datetime import datetime
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "build_recent_window_analysis.py"
SPEC = importlib.util.spec_from_file_location("eurusd_recent_windows", SCRIPT)
assert SPEC and SPEC.loader
ANALYSIS = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = ANALYSIS
SPEC.loader.exec_module(ANALYSIS)


def test_recent_windows_reconcile_to_exact_ledger() -> None:
    trades = ANALYSIS.load_trades()
    result = ANALYSIS.measure_window("12_months", datetime(2025, 7, 2), trades)

    assert result["trades"] == 312
    assert result["wins"] == 172
    assert result["losses"] == 140
    assert result["net_usd"] == 2.98
    assert result["profit_factor"] == 1.0167


def test_primary_stress_uses_half_pip_and_negative_cost_multiplier() -> None:
    trade = ANALYSIS.Trade(
        entry_time=datetime(2026, 1, 1),
        exit_time=datetime(2026, 1, 1),
        price_profit=1.0,
        commission=-0.10,
        swap=-0.20,
        net=0.70,
    )

    assert ANALYSIS.stressed_value(trade, 0.5) == 0.575


def test_closed_trade_drawdown_rebases_window_to_zero() -> None:
    def trade(net: float, minute: int) -> object:
        timestamp = datetime(2026, 1, 1, 0, minute)
        return ANALYSIS.Trade(timestamp, timestamp, net, 0.0, 0.0, net)

    assert ANALYSIS.closed_trade_drawdown([trade(-2.0, 1), trade(5.0, 2), trade(-3.0, 3)]) == 3.0
