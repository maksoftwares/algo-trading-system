from __future__ import annotations

import importlib.util
from pathlib import Path
import sys


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "run_xau_920101_breakout_retest_backtest_variants.py"
SPEC = importlib.util.spec_from_file_location("a2_backtest_runner", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def test_build_trades_from_deals_pairs_by_position_id_and_includes_costs() -> None:
    deals = [
        {
            "timestamp_broker": "2026.06.01 09:00:00",
            "deal_ticket": "10",
            "position_id": "100",
            "entry_code": "0",
            "direction": "LONG",
            "volume": "0.01",
            "price": "3300.00",
            "profit": "0.00",
            "commission": "-0.10",
            "swap": "0.00",
            "order_ticket": "20",
            "comment": "entry",
        },
        {
            "timestamp_broker": "2026.06.01 10:00:00",
            "deal_ticket": "11",
            "position_id": "100",
            "entry_code": "1",
            "direction": "SHORT",
            "volume": "0.01",
            "price": "3310.00",
            "profit": "10.00",
            "commission": "-0.10",
            "swap": "-0.05",
            "order_ticket": "21",
            "reason_code": "5",
            "comment": "take profit",
        },
        {
            "timestamp_broker": "2026.06.01 09:30:00",
            "deal_ticket": "12",
            "position_id": "200",
            "entry_code": "0",
            "direction": "SHORT",
            "volume": "0.01",
            "price": "3305.00",
            "profit": "0.00",
            "commission": "-0.10",
            "swap": "0.00",
            "order_ticket": "22",
        },
    ]

    trades = MODULE.build_trades_from_deals(deals)

    assert len(trades) == 1
    assert trades[0]["position_id"] == "100"
    assert trades[0]["direction"] == "LONG"
    assert trades[0]["profit_aed"] == 9.75
    assert trades[0]["entry_price"] == 3300.0
    assert trades[0]["exit_price"] == 3310.0
