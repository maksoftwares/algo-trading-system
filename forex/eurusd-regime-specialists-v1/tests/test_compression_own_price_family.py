from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from eurusd_regime_specialists import compression_own_price_family as module


def _config() -> dict:
    return json.loads(module.CONFIG_PATH.read_text(encoding="utf-8"))


def _bars() -> pd.DataFrame:
    index = pd.date_range(
        "2025-01-02T19:00:00Z",
        periods=12,
        freq="5min",
    )
    return pd.DataFrame(
        {
            "mid_open": [1.1 + index * 0.0001 for index in range(12)],
            "mid_close": [
                1.10005 + index * 0.0001 for index in range(12)
            ],
        },
        index=index,
    )


def _record(day: str = "2025-01-02") -> dict:
    return {
        "decision_date": day,
        "decision_time_utc": f"{day.replace('-', '.')} 20:00:00",
        "status": "RESOLVED",
        "regime": "CROSSPAIR_COMPRESSION",
        "long_outcome": {
            "outcome": "TARGET",
            "result_r": 1.4875,
            "exit_time": f"{day.replace('-', '.')} 21:00:00",
        },
        "short_outcome": {
            "outcome": "STOP",
            "result_r": -1.0125,
            "exit_time": f"{day.replace('-', '.')} 21:00:00",
        },
    }


def test_completed_return_uses_only_bars_before_decision() -> None:
    result = module.completed_return(
        _bars(),
        pd.Timestamp("2025-01-02T20:00:00Z"),
        60,
    )
    assert result is not None
    assert result > 0.0


def test_completed_return_fails_when_exact_bar_is_missing() -> None:
    bars = _bars().drop(pd.Timestamp("2025-01-02T19:30:00Z"))
    assert (
        module.completed_return(
            bars,
            pd.Timestamp("2025-01-02T20:00:00Z"),
            60,
        )
        is None
    )


def test_fade_and_momentum_are_exact_opposites() -> None:
    record = {
        **_record(),
        "own_price_features": {
            "own_return_15": 0.01,
            "own_return_60": 0.01,
            "own_return_240": 0.01,
        },
    }
    rules = {
        rule["id"]: rule for rule in _config()["candidate_rules_in_fixed_order"]
    }
    assert module.rule_side(rules["OWN_RETURN_60_FADE"], record) == "SHORT"
    assert module.rule_side(rules["OWN_RETURN_60_MOMENTUM"], record) == "LONG"


def test_validation_outcome_cannot_change_development_table() -> None:
    config = _config()
    record = {
        **_record("2019-01-02"),
        "own_price_features": {
            "own_return_15": 0.01,
            "own_return_60": 0.01,
            "own_return_240": 0.01,
        },
    }
    records = [copy.deepcopy(record) for _ in range(300)]
    before = module.development_table(records, config)
    future = copy.deepcopy(record)
    future["decision_date"] = "2025-01-02"
    future["long_outcome"]["result_r"] = -1000.0
    future["short_outcome"]["result_r"] = 1000.0
    after = module.development_table([*records, future], config)
    pd.testing.assert_frame_equal(before, after)


def test_config_is_research_only_and_never_authorizes_orders() -> None:
    config = module.load_config()
    assert config["owned_regime"] == "CROSSPAIR_COMPRESSION"
    assert config["result_can_count_as_forward_evidence"] is False
    assert config["demo_order_authorized"] is False
    assert "NO_VALIDATION_BASED_RULE_SELECTION" in config["prohibitions"]
    assert "NO_ORDER_AUTHORIZATION" in config["prohibitions"]


def test_no_selected_rule_returns_datetime_typed_empty_frame() -> None:
    frame = module.trade_frame([], None, _config())
    assert frame.empty
    assert isinstance(frame["entry_time"].dtype, pd.DatetimeTZDtype)
    assert isinstance(frame["exit_time"].dtype, pd.DatetimeTZDtype)


def test_empty_specialist_combines_as_protected_only() -> None:
    empty = module.trade_frame([], None, _config())
    m15 = pd.DataFrame(
        {
            "entry_time": pd.to_datetime(["2025-01-02T08:00:00Z"]),
            "exit_time": pd.to_datetime(["2025-01-02T09:00:00Z"]),
            "decision_date": ["2025-01-02"],
            "component": ["M15_REGIME"],
            "side": ["SHORT"],
            "pnl_usd": [2.0],
            "stressed_pnl_usd": [1.9],
        }
    )
    combined, result = module.combined_portfolio(
        empty,
        m15,
        "2025-01-01",
        "2026-01-01",
        261,
    )
    assert len(combined) == 1
    assert result["trades"] == 1
    assert result["m15_residual_owned_date_overlaps"] == 0
