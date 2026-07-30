from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from eurusd_regime_specialists import dense_residual_family as module


def _config() -> dict:
    return json.loads(module.CONFIG_PATH.read_text(encoding="utf-8"))


def _context(
    strength_15: float,
    strength_60: float,
    strength_240: float,
    agreement_60: float = 0.0,
    agreement_240: float = 0.0,
) -> dict[str, float]:
    return {
        "strength_15": strength_15,
        "strength_60": strength_60,
        "strength_240": strength_240,
        "agreement_15": 0.0,
        "agreement_60": agreement_60,
        "agreement_240": agreement_240,
        "signed_activity_60": 0.0,
        "cost_pressure": 0.0,
    }


def _record(day: str, context: dict[str, float]) -> dict:
    return {
        "decision_date": day,
        "decision_time_utc": f"{day.replace('-', '.')} 20:00:00",
        "status": "RESOLVED",
        "regime": "MIXED_TRANSITION",
        "context": context,
        "long_outcome": {
            "side": "LONG",
            "outcome": "TARGET",
            "result_r": 1.4875,
            "exit_time": f"{day.replace('-', '.')} 21:00:00",
        },
        "short_outcome": {
            "side": "SHORT",
            "outcome": "STOP",
            "result_r": -1.0125,
            "exit_time": f"{day.replace('-', '.')} 21:00:00",
        },
    }


def test_rule_side_uses_fixed_orientation_and_zero_tie_break() -> None:
    config = _config()
    rules = {
        rule["id"]: rule for rule in config["candidate_rules_in_fixed_order"]
    }
    context = _context(-1.0, 0.5, 1.0, agreement_60=0.0)
    assert module.rule_side(rules["STRENGTH_15_MOMENTUM"], context) == "SHORT"
    assert module.rule_side(rules["STRENGTH_15_FADE"], context) == "LONG"
    assert module.rule_side(rules["AGREEMENT_60_MOMENTUM"], context) == "LONG"


def test_majority_strength_is_not_magnitude_weighted() -> None:
    config = _config()
    rule = next(
        rule
        for rule in config["candidate_rules_in_fixed_order"]
        if rule["id"] == "MAJORITY_STRENGTH_MOMENTUM"
    )
    context = _context(-3.0, 0.1, 0.1)
    assert module.rule_side(rule, context) == "LONG"


def test_selection_uses_only_passing_development_rows() -> None:
    config = _config()
    config["regimes_in_fixed_order"] = ["MIXED_TRANSITION"]
    table = pd.DataFrame(
        [
            {
                "regime": "MIXED_TRANSITION",
                "rule_id": "A",
                "rule_index": 0,
                "trades": 60,
                "net": 10.0,
                "stressed_profit_factor": 1.2,
                "best_5pct_removed_profit_factor": 1.1,
                "trade_sequence_half_profit_factors": [1.1, 1.1],
            },
            {
                "regime": "MIXED_TRANSITION",
                "rule_id": "B",
                "rule_index": 1,
                "trades": 60,
                "net": 20.0,
                "stressed_profit_factor": 1.3,
                "best_5pct_removed_profit_factor": 1.2,
                "trade_sequence_half_profit_factors": [1.2, 1.2],
            },
        ]
    )
    assert module.select_rules(table, config) == {
        "MIXED_TRANSITION": "B"
    }


def test_validation_outcomes_cannot_change_development_selection() -> None:
    config = _config()
    records = [
        _record("2017-01-02", _context(1.0, 1.0, 1.0))
        for _ in range(60)
    ]
    table_before = module.development_candidate_table(records, config)
    selections_before = module.select_rules(table_before, config)
    changed = copy.deepcopy(records)
    future = _record("2025-01-02", _context(-1.0, -1.0, -1.0))
    future["long_outcome"]["result_r"] = -1000.0
    future["short_outcome"]["result_r"] = 1000.0
    changed.append(future)
    table_after = module.development_candidate_table(changed, config)
    selections_after = module.select_rules(table_after, config)
    assert selections_after == selections_before


def test_selected_rule_produces_one_trade_per_resolved_day() -> None:
    config = _config()
    records = [
        _record("2025-01-02", _context(1.0, 1.0, 1.0)),
        _record("2025-01-03", _context(-1.0, -1.0, -1.0)),
    ]
    selections = {
        regime: None for regime in config["regimes_in_fixed_order"]
    }
    selections["MIXED_TRANSITION"] = "STRENGTH_60_MOMENTUM"
    trades = module.selected_trades(
        records,
        selections,
        config,
        "2025-01-01",
        "2026-01-01",
    )
    assert len(trades) == 2
    assert trades["side"].tolist() == ["LONG", "SHORT"]


def test_config_is_research_only_and_never_authorizes_orders() -> None:
    config = module.load_config()
    assert config["result_can_count_as_forward_evidence"] is False
    assert config["demo_order_authorized"] is False
    assert "NO_VALIDATION_BASED_RULE_SELECTION" in config["prohibitions"]
    assert "NO_ORDER_AUTHORIZATION" in config["prohibitions"]
