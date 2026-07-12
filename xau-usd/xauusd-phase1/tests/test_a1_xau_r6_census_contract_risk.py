from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import build_a1_xau_r6_distribution_break_failed_reclaim_census as R  # noqa: E402


def contract(**overrides: object) -> R.Contract:
    values = dict(point=0.01, digits=2, tick_size=0.05, tick_value_loss=5.0, volume_min=0.01, volume_step=0.01, contract_size=100.0, stops_level=0, freeze_level=0)
    values.update(overrides)
    return R.Contract(**values)


def test_normalize_up_uses_tick_size_and_digits() -> None:
    assert R.normalize_up(100.001, contract()) == 100.05
    assert R.normalize_up(100.05, contract()) == 100.05


def test_risk_equivalent_uses_tick_steps_and_loss_value() -> None:
    # 1.00 price move / 0.05 tick = 20 ticks; 20 * $5 * 0.01 = $1.
    assert R.minimum_contract_risk(100.0, 101.0, contract()) == pytest.approx(1.0)


def test_invalid_contract_metadata_fails_closed() -> None:
    with pytest.raises(ValueError, match="metadata"):
        R.normalize_up(100, contract(point=0.0))
    with pytest.raises(ValueError, match="prices"):
        R.minimum_contract_risk(101, 100, contract())


@pytest.mark.parametrize("risk,reference,deployment", [(2.5, True, True), (25.0, True, False), (25.01, False, False)])
def test_locked_risk_boundaries(risk: float, reference: bool, deployment: bool) -> None:
    assert (risk <= 25.0) is reference
    assert (risk <= 2.5) is deployment
