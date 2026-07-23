from __future__ import annotations

import importlib.util
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "run_unmasked_audit.py"
SPEC = importlib.util.spec_from_file_location("eurusd_unmasked_audit", SCRIPT)
assert SPEC and SPEC.loader
AUDIT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(AUDIT)


def test_metrics_uses_net_trade_signs() -> None:
    result = AUDIT.metrics([{"net": 2.0}, {"net": 1.0}, {"net": -1.0}])
    assert result["trades"] == 3
    assert result["wins"] == 2
    assert result["losses"] == 1
    assert result["net_usd"] == 2.0
    assert result["profit_factor"] == 3.0


def test_primary_stress_applies_half_pip_and_negative_cost_multiplier() -> None:
    row = {"price_profit": 1.0, "commission": -0.10, "swap": -0.20}
    assert AUDIT.stress_trade(row, 0.5) == 0.575


def test_order_reason_extracts_structured_suffix() -> None:
    row = {"deal_and_reason": "12|result_price=1.10000|reason=entered"}
    assert AUDIT.order_reason(row) == "entered"
