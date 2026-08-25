from __future__ import annotations

from dataclasses import dataclass
import importlib.util
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("v18_scenario", ROOT / "src" / "scenario.py")
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
        self.events: list[str] = []

    def _market_pnl(self, position: Position, bid: float, ask: float) -> float:
        return position.pnl

    def _record(self, event: str, now_ms: int, **kwargs) -> None:
        self.events.append(event)

    def _close(
        self,
        trade_id: str,
        now_ms: int,
        pnl: float,
        reason: str,
        *,
        counted_by_v60: bool,
    ) -> None:
        del self.positions[trade_id]
        self.closed.append(trade_id)

    def simulate(self, quotes):
        return {}


class FakeV6:
    @staticmethod
    def combined_challenger_class(replay, evaluator, feature_map, anti_rule):
        return FakeBase


def challenger_type():
    return scenario.v7_exempt_challenger_class(
        replay=object(),
        evaluator=object(),
        v6_scenario=FakeV6(),
        feature_map={},
        anti_rule={},
        policy={
            "exempt_source_ids": ["V7_SWING_HEALTH"],
            "account_profit_protection_arm_r": 1.5,
            "account_profit_protection_retain_r": 0.5,
        },
    )


def test_protected_positions_excludes_only_v7() -> None:
    positions = {
        "v7": Position(Candidate("V7_SWING_HEALTH", 10.0), 30.0),
        "r1": Position(Candidate("R1_PULLBACK", 10.0), 20.0),
    }
    observed = scenario.protected_positions(positions, {"V7_SWING_HEALTH"})
    assert list(observed) == ["r1"]


def test_v7_only_position_never_arms_or_closes() -> None:
    instance = challenger_type()()
    instance.positions = {
        "v7": Position(Candidate("V7_SWING_HEALTH", 10.0), 100.0)
    }
    instance._evaluate_profit_protection(1, 0.0, 0.0)
    assert instance.positions.keys() == {"v7"}
    assert instance.profit_protection_arms == 0
    assert instance.v7_exempt_only_cycles == 1


def test_mixed_basket_arms_and_closes_only_non_exempt_position() -> None:
    instance = challenger_type()()
    instance.positions = {
        "v7": Position(Candidate("V7_SWING_HEALTH", 10.0), 100.0),
        "r1": Position(Candidate("R1_PULLBACK", 10.0), 20.0),
    }
    instance._evaluate_profit_protection(1, 0.0, 0.0)
    assert instance.profit_protection_armed
    assert instance.profit_protection_arms == 1

    instance.positions["r1"].pnl = 4.0
    instance._evaluate_profit_protection(2, 0.0, 0.0)
    assert instance.closed == ["r1"]
    assert set(instance.positions) == {"v7"}
    assert instance.profit_giveback_closes == 1
    assert not instance.profit_protection_armed
