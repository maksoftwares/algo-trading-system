from __future__ import annotations

import sys
import hashlib
import json
import csv
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import build_a1_xau_r6_distribution_break_failed_reclaim_census as R  # noqa: E402

CONTRACT_FIXTURE = json.loads(
    (ROOT / "tests" / "fixtures" / "A1_XAU_R6_ORDERCALCPROFIT_PARITY_V1.json").read_text()
)


def contract(**overrides: object) -> R.Contract:
    values = dict(CONTRACT_FIXTURE["contract"])
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
    fixtures = CONTRACT_FIXTURE["boundary_replay_cases"]
    for fixture in fixtures:
        assert fixture["evidence_class"] == "DERIVED_FROM_NATIVE_LINEAR_CONTRACT"
        values = {key: fixture[key] for key in ("entry_bid", "risk_price", "captured_loss")}
        R.validate_order_calc_profit_fixture(**values, contract=contract())
        risk = R.minimum_contract_risk(fixture["entry_bid"], fixture["risk_price"], contract())
        assert R.risk_at_or_below(risk, 2.5) is (fixture["captured_loss"] <= 2.5)
        assert R.risk_at_or_below(risk, 25.0) is (fixture["captured_loss"] <= 25.0)


def test_native_contract_and_order_anchor_are_parsed_from_pinned_evidence() -> None:
    startup_path = ROOT / CONTRACT_FIXTURE["native_contract_source"]["path"]
    order_path = ROOT / CONTRACT_FIXTURE["native_order_source"]["path"]
    assert hashlib.sha256(startup_path.read_bytes()).hexdigest() == CONTRACT_FIXTURE["native_contract_source"]["sha256"]
    assert hashlib.sha256(order_path.read_bytes()).hexdigest() == CONTRACT_FIXTURE["native_order_source"]["sha256"]
    with startup_path.open(encoding="utf-8", newline="") as handle:
        startup = next(csv.DictReader(handle, delimiter="\t"))
    assert startup["server"] == contract().server
    assert startup["symbol"] == contract().symbol
    assert float(startup["tick_value_loss"]) == contract().tick_value_loss
    anchor = CONTRACT_FIXTURE["native_order_anchor"]
    with order_path.open(encoding="utf-8", newline="") as handle:
        orders = list(csv.DictReader(handle, delimiter="\t"))
    native = next(row for row in orders if row["timestamp_broker"] == anchor["timestamp_broker"] and row["action"] == "ORDER_SEND_OK")
    assert float(native["entry_reference"]) == anchor["entry"]
    assert float(native["sl"]) == anchor["stop"]
    assert float(native["lots"]) == anchor["volume"]
    assert abs(anchor["entry"] - anchor["stop"]) * contract().contract_size * anchor["volume"] == pytest.approx(anchor["loss_magnitude"])


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
