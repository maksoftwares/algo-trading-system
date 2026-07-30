from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from eurusd_regime_specialists import dense_residual_family as dense
from eurusd_regime_specialists import online_dense_residual_router as module


def _config() -> dict:
    return json.loads(module.CONFIG_PATH.read_text(encoding="utf-8"))


def _dense_config() -> dict:
    return json.loads(dense.CONFIG_PATH.read_text(encoding="utf-8"))


def _context(strength_60: float) -> dict[str, float]:
    return {
        "strength_15": strength_60,
        "strength_60": strength_60,
        "strength_240": strength_60,
        "agreement_15": 1.0 if strength_60 >= 0.0 else -1.0,
        "agreement_60": 1.0 if strength_60 >= 0.0 else -1.0,
        "agreement_240": 1.0 if strength_60 >= 0.0 else -1.0,
        "signed_activity_60": 0.0,
        "cost_pressure": 0.0,
    }


def _record(day: int, long_r: float, short_r: float) -> dict:
    date_text = f"2025-01-{day:02d}"
    return {
        "decision_date": date_text,
        "decision_time_utc": f"2025.01.{day:02d} 20:00:00",
        "status": "RESOLVED",
        "regime": "MIXED_TRANSITION",
        "context": _context(1.0),
        "long_outcome": {
            "side": "LONG",
            "outcome": "TARGET" if long_r > 0.0 else "STOP",
            "result_r": long_r,
            "exit_time": f"2025.01.{day:02d} 21:00:00",
        },
        "short_outcome": {
            "side": "SHORT",
            "outcome": "TARGET" if short_r > 0.0 else "STOP",
            "result_r": short_r,
            "exit_time": f"2025.01.{day:02d} 21:00:00",
        },
    }


def test_router_uses_fixed_rule_during_warmup() -> None:
    config = _config()
    dense_config = _dense_config()
    rules = dense_config["candidate_rules_in_fixed_order"]
    histories = {str(rule["id"]): [] for rule in rules}
    chosen, _, reason = module.select_rule(
        histories,
        rules,
        config,
        0.0625,
    )
    assert chosen["id"] == "STRENGTH_60_MOMENTUM"
    assert reason == "FIXED_WARMUP_RULE"


def test_router_ranks_only_completed_prior_outcomes() -> None:
    config = _config()
    config["online_router"][
        "minimum_prior_regime_observations_before_routing"
    ] = 2
    dense_config = _dense_config()
    records = [
        _record(1, 1.5, -1.0),
        _record(2, 1.5, -1.0),
        _record(3, -1000.0, 1000.0),
    ]
    trades = module.online_trades(records, config, dense_config)
    third = trades.iloc[2]
    assert third["side"] == "LONG"
    assert third["prior_regime_observations"] == 2


def test_current_outcome_can_affect_only_the_next_trade() -> None:
    config = _config()
    config["online_router"][
        "minimum_prior_regime_observations_before_routing"
    ] = 1
    dense_config = _dense_config()
    first = _record(1, 1.5, -1.0)
    second = _record(2, -1000.0, 1000.0)
    before = module.online_trades([first, second], config, dense_config)
    changed = copy.deepcopy(second)
    changed["long_outcome"]["result_r"] = 1000.0
    changed["short_outcome"]["result_r"] = -1000.0
    after = module.online_trades([first, changed], config, dense_config)
    assert before.iloc[1]["rule_id"] == after.iloc[1]["rule_id"]
    assert before.iloc[1]["side"] == after.iloc[1]["side"]


def test_router_emits_one_trade_for_every_resolved_record() -> None:
    records = [
        _record(1, 1.5, -1.0),
        _record(2, -1.0, 1.5),
        {
            **_record(3, 1.5, -1.0),
            "status": "CASH_MARKET_CLOSURE",
        },
    ]
    trades = module.online_trades(records, _config(), _dense_config())
    assert len(trades) == 2


def test_config_is_research_only_and_never_authorizes_orders() -> None:
    config = module.load_config()
    assert config["result_can_count_as_forward_evidence"] is False
    assert config["demo_order_authorized"] is False
    assert "NO_CURRENT_OUTCOME_LEAKAGE" in config["prohibitions"]
    assert "NO_ORDER_AUTHORIZATION" in config["prohibitions"]
