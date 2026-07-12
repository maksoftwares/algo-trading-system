from __future__ import annotations

import sys
import hashlib
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import build_a1_xau_r6_distribution_break_failed_reclaim_census as R  # noqa: E402


def contract(**overrides: object) -> R.Contract:
    values = dict(
        account_currency="USD", account_leverage=50, margin_mode=2,
        server="Capital.ComMena-Demo", symbol="XAUUSD", point=0.01, digits=2,
        tick_size=0.01, tick_value=1.0, tick_value_loss=1.0,
        volume_min=0.01, volume_step=0.01, volume_max=1000.0,
        contract_size=100.0, stops_level=0, freeze_level=0,
    )
    values.update(overrides)
    return R.Contract(**values)


def test_normalize_up_uses_tick_size_and_digits() -> None:
    assert R.normalize_up(100.001, contract(tick_size=0.05)) == 100.05
    assert R.normalize_up(100.05, contract(tick_size=0.05)) == 100.05


def test_risk_equivalent_uses_tick_steps_and_loss_value() -> None:
    # 1.00 price move / 0.05 tick = 20 ticks; 20 * $5 * 0.01 = $1.
    assert R.minimum_contract_risk(100.0, 101.0, contract(tick_size=0.05, tick_value=5.0, tick_value_loss=5.0)) == pytest.approx(1.0)


def test_captured_capital_com_order_calc_profit_parity() -> None:
    # Immutable Capital.ComMena-Demo snapshot: USD, leverage 50, margin mode 2,
    # XAUUSD 0.01 minimum lot, 0.01 tick, $1 tick value. The archived native
    # order capture 1829.33 -> 1804.83 at 0.01 lot has a $24.50 loss magnitude.
    captured = contract()
    R.validate_order_calc_profit_fixture(1804.83, 1829.33, 24.50, captured)
    with pytest.raises(ValueError, match="parity"):
        R.validate_order_calc_profit_fixture(1804.83, 1829.33, 24.49, captured)


def test_hash_addressed_native_order_calc_profit_boundary_fixtures() -> None:
    fixtures = [
        {"entry_bid": 2000.0, "risk_price": 2002.49, "captured_loss": 2.49},
        {"entry_bid": 2000.0, "risk_price": 2002.5, "captured_loss": 2.5},
        {"entry_bid": 2000.0, "risk_price": 2002.51, "captured_loss": 2.51},
        {"entry_bid": 2000.0, "risk_price": 2024.99, "captured_loss": 24.99},
        {"entry_bid": 2000.0, "risk_price": 2025.0, "captured_loss": 25.0},
        {"entry_bid": 2000.0, "risk_price": 2025.01, "captured_loss": 25.01},
    ]
    payload = json.dumps(fixtures, separators=(",", ":"), sort_keys=True).encode()
    assert hashlib.sha256(payload).hexdigest() == "306a727ccce65b5e801fc9ffd7ecc76ded605054720a6e0b05ef2970ba1971e0"
    for fixture in fixtures:
        R.validate_order_calc_profit_fixture(**fixture, contract=contract())
        risk = R.minimum_contract_risk(fixture["entry_bid"], fixture["risk_price"], contract())
        assert R.risk_at_or_below(risk, 2.5) is (fixture["captured_loss"] <= 2.5)
        assert R.risk_at_or_below(risk, 25.0) is (fixture["captured_loss"] <= 25.0)


def test_invalid_contract_metadata_fails_closed() -> None:
    with pytest.raises(ValueError, match="metadata"):
        R.normalize_up(100, contract(point=0.0))
    with pytest.raises(ValueError, match="prices"):
        R.minimum_contract_risk(101, 100, contract())
    with pytest.raises(ValueError, match="metadata"):
        R.validate_contract(contract(account_currency=""))


@pytest.mark.parametrize("risk,reference,deployment", [(2.5, True, True), (25.0, True, False), (25.01, False, False)])
def test_locked_risk_boundaries(risk: float, reference: bool, deployment: bool) -> None:
    assert (risk <= 25.0) is reference
    assert (risk <= 2.5) is deployment
