from __future__ import annotations

from dataclasses import dataclass
import importlib.util
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("v20_scenario", ROOT / "src" / "scenario.py")
assert spec is not None and spec.loader is not None
scenario = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = scenario
spec.loader.exec_module(scenario)


@dataclass
class Candidate:
    source_id: str
    risk_usd: float


@dataclass
class Position:
    candidate: Candidate
    pnl: float


class FakeBase:
    def __init__(self) -> None:
        self.config = {
            "portfolio_protection": {
                "enabled": True,
                "open_profit_arm_r": 1.5,
                "open_profit_retain_r": 0.5,
            }
        }
        self.positions: dict[str, Position] = {}
        self.profit_protection_armed = False
        self.profit_protection_peak_open_pnl = 0.0
        self.profit_protection_tickets: set[str] = set()
        self.profit_protection_arms = 0
        self.profit_giveback_closes = 0
        self.closed: list[str] = []
        self.baseline_calls = 0

    def _evaluate_profit_protection(self, now_ms: int, bid: float, ask: float) -> None:
        self.baseline_calls += 1
        if not self.positions:
            self.profit_protection_armed = False
            self.profit_protection_peak_open_pnl = 0.0
            self.profit_protection_tickets = set()
            return
        risk = sum(position.candidate.risk_usd for position in self.positions.values())
        pnl = sum(position.pnl for position in self.positions.values())
        self.profit_protection_tickets = set(self.positions)
        self.profit_protection_peak_open_pnl = max(
            self.profit_protection_peak_open_pnl, pnl
        )
        if not self.profit_protection_armed and pnl >= 1.5 * risk:
            self.profit_protection_armed = True
            self.profit_protection_arms += 1
        elif self.profit_protection_armed and pnl <= 0.5 * risk:
            self.closed.extend(sorted(self.positions))
            self.profit_giveback_closes += len(self.positions)
            self.positions.clear()
            self.profit_protection_armed = False
            self.profit_protection_peak_open_pnl = 0.0
            self.profit_protection_tickets = set()

    def simulate(self, quotes):
        return {}


class FakeV6:
    @staticmethod
    def combined_challenger_class(replay, evaluator, feature_map, anti_rule):
        return FakeBase


def challenger_type():
    return scenario.v7_solo_bypass_challenger_class(
        replay=object(),
        evaluator=object(),
        v6_scenario=FakeV6(),
        feature_map={},
        anti_rule={},
        policy={
            "solo_source_id": "V7_SWING_HEALTH",
            "account_profit_protection_arm_r": 1.5,
            "account_profit_protection_retain_r": 0.5,
        },
    )


def test_v7_only_basket_bypasses_and_resets_protection() -> None:
    instance = challenger_type()()
    instance.profit_protection_armed = True
    instance.profit_protection_peak_open_pnl = 50.0
    instance.profit_protection_tickets = {"old"}
    instance.positions = {
        "v7": Position(Candidate("V7_SWING_HEALTH", 10.0), 100.0)
    }

    instance._evaluate_profit_protection(1, 0.0, 0.0)

    assert set(instance.positions) == {"v7"}
    assert instance.baseline_calls == 0
    assert instance.v7_solo_bypass_cycles == 1
    assert instance.v7_solo_bypass_trade_ids == {"v7"}
    assert not instance.profit_protection_armed
    assert not instance.profit_protection_tickets


def test_mixed_basket_delegates_unchanged_and_closes_v7_too() -> None:
    instance = challenger_type()()
    instance.positions = {
        "v7": Position(Candidate("V7_SWING_HEALTH", 10.0), 20.0),
        "r1": Position(Candidate("R1_PULLBACK", 10.0), 20.0),
    }

    instance._evaluate_profit_protection(1, 0.0, 0.0)
    assert instance.baseline_calls == 1
    assert instance.profit_protection_armed

    instance.positions["v7"].pnl = 2.0
    instance.positions["r1"].pnl = 2.0
    instance._evaluate_profit_protection(2, 0.0, 0.0)

    assert instance.baseline_calls == 2
    assert instance.closed == ["r1", "v7"]
    assert not instance.positions
    assert instance.v7_mixed_basket_cycles == 2


def test_non_v7_basket_always_delegates() -> None:
    instance = challenger_type()()
    instance.positions = {
        "r1": Position(Candidate("R1_PULLBACK", 10.0), 20.0)
    }

    instance._evaluate_profit_protection(1, 0.0, 0.0)

    assert instance.baseline_calls == 1
    assert instance.standard_protection_cycles == 1
    assert instance.v7_present_cycles == 0
    assert instance.v7_solo_bypass_cycles == 0


def test_changed_threshold_is_rejected() -> None:
    scenario_type = scenario.v7_solo_bypass_challenger_class(
        replay=object(),
        evaluator=object(),
        v6_scenario=FakeV6(),
        feature_map={},
        anti_rule={},
        policy={
            "solo_source_id": "V7_SWING_HEALTH",
            "account_profit_protection_arm_r": 1.4,
            "account_profit_protection_retain_r": 0.5,
        },
    )

    try:
        scenario_type()
    except ValueError as error:
        assert "thresholds changed" in str(error)
    else:
        raise AssertionError("V20 accepted a changed protection threshold")
