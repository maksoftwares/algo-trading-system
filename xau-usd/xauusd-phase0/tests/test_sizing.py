from __future__ import annotations

import pytest

from phase0.config import load_project_config
from phase0.sizing import (
    SizingError,
    calculate_position_size,
    calculate_price_risk,
    calculate_risk_money,
    floor_to_lot_step,
    gross_pnl_usd,
    net_pnl_usd,
    r_multiple,
)


def test_risk_money_uses_current_equity():
    assert calculate_risk_money(12000.0, 0.005) == pytest.approx(60.0)


def test_price_risk_rejects_invalid_stop():
    assert calculate_price_risk("LONG", 100.0, 99.0) == pytest.approx(1.0)
    assert calculate_price_risk("SHORT", 100.0, 101.0) == pytest.approx(1.0)

    with pytest.raises(SizingError):
        calculate_price_risk("LONG", 100.0, 100.5)


def test_floor_to_lot_step_never_rounds_up():
    assert floor_to_lot_step(0.129, 0.01) == pytest.approx(0.12)
    assert floor_to_lot_step(1.234, 0.1) == pytest.approx(1.2)


def test_calculate_position_size(project_root):
    config = load_project_config(project_root)

    size = calculate_position_size(
        config,
        symbol="XAUUSD",
        direction="LONG",
        entry_price=100.0,
        stop_loss=99.0,
        current_equity=10000.0,
        risk_per_trade_pct=0.005,
    )

    assert size.risk_money == pytest.approx(50.0)
    assert size.raw_lots == pytest.approx(0.5)
    assert size.lots == pytest.approx(0.5)
    assert size.actual_risk_pct == pytest.approx(0.005)


def test_pnl_and_r_multiple():
    gross = gross_pnl_usd("LONG", 100.0, 101.5, lots=0.5, contract_size_per_lot=100.0)
    net = net_pnl_usd(gross, lots=0.5, commission_usd_per_round_turn_lot=4.0)

    assert gross == pytest.approx(75.0)
    assert net == pytest.approx(73.0)
    assert r_multiple(net, risk_money_at_entry=50.0) == pytest.approx(1.46)
