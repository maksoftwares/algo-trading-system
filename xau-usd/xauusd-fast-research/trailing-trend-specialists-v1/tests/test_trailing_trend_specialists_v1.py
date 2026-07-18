from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "src" / "trend.py"
SPEC = importlib.util.spec_from_file_location(
    "trailing_trend_specialists_v1_tests", MODULE_PATH
)
if SPEC is None or SPEC.loader is None:
    raise ImportError(MODULE_PATH)
TREND = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = TREND
SPEC.loader.exec_module(TREND)


def _policy(direction_mechanic: str = "DONCHIAN", cooldown: int = 0) -> dict:
    return {
        "attempt_no": 11094,
        "policy_id": "TEST_POLICY",
        "timeframe": "H4",
        "mechanic": direction_mechanic,
        "initial_stop_atr": 2.0,
        "trail_stop_atr": 1.5,
        "cooldown_decisions": cooldown,
    }


def _execution() -> dict:
    return {
        "maximum_entry_gap_minutes": 10,
        "maximum_spread_price": 1.0,
        "maximum_spread_r": 0.5,
        "minimum_stop_distance_price": 1.0,
        "ounces_at_lot_size": 1.0,
        "extra_execution_cost_usd": 0.0,
        "holding_cost_per_24h_usd": 0.0,
        "stress_slippage_r": 0.0,
        "current_account_risk_usd": 100.0,
    }


def _m5(rows: list[dict[str, float]]) -> pd.DataFrame:
    starts = pd.date_range("2024-01-01T00:00:00Z", periods=len(rows), freq="5min")
    output = []
    for start, raw in zip(starts, rows, strict=True):
        bid_open = float(raw.get("bid_open", 100.0))
        ask_open = float(raw.get("ask_open", bid_open + 0.2))
        bid_high = float(raw.get("bid_high", bid_open + 0.5))
        bid_low = float(raw.get("bid_low", bid_open - 0.5))
        bid_close = float(raw.get("bid_close", bid_open))
        ask_high = float(raw.get("ask_high", bid_high + 0.2))
        ask_low = float(raw.get("ask_low", bid_low + 0.2))
        ask_close = float(raw.get("ask_close", bid_close + 0.2))
        output.append(
            {
                "bar_start_utc": start,
                "bar_end_utc": start + pd.Timedelta(minutes=5),
                "bid_open": bid_open,
                "bid_high": bid_high,
                "bid_low": bid_low,
                "bid_close": bid_close,
                "ask_open": ask_open,
                "ask_high": ask_high,
                "ask_low": ask_low,
                "ask_close": ask_close,
                "mid_open": (bid_open + ask_open) / 2.0,
                "mid_high": (bid_high + ask_high) / 2.0,
                "mid_low": (bid_low + ask_low) / 2.0,
                "mid_close": (bid_close + ask_close) / 2.0,
            }
        )
    return pd.DataFrame(output)


def _decisions(
    m5: pd.DataFrame,
    indexes: list[int],
    directions: list[int],
    atrs: list[float] | None = None,
    exit_long: list[bool] | None = None,
    exit_short: list[bool] | None = None,
) -> pd.DataFrame:
    count = len(indexes)
    return pd.DataFrame(
        {
            "bar_end_utc": [m5.loc[index, "bar_start_utc"] for index in indexes],
            "atr": atrs or [1.0] * count,
            "desired_direction": directions,
            "exit_long": exit_long or [False] * count,
            "exit_short": exit_short or [False] * count,
        }
    )


def _simulate(
    m5: pd.DataFrame, decisions: pd.DataFrame, policy: dict | None = None
) -> pd.DataFrame:
    return TREND.simulate_policy(
        m5,
        decisions,
        policy or _policy(),
        _execution(),
        pd.Timestamp("2024-01-01T00:00:00Z"),
        pd.Timestamp(m5["bar_end_utc"].iloc[-1]),
    )


def test_donchian_channels_exclude_current_bar_and_future_prices() -> None:
    starts = pd.date_range("2024-01-01T00:00:00Z", periods=7, freq="4h")
    highs = np.array([10.0, 11.0, 12.0, 99.0, 14.0, 15.0, 16.0])
    lows = np.array([8.0, 9.0, 10.0, 11.0, 12.0, 13.0, 14.0])
    closes = np.array([9.0, 10.0, 11.0, 12.5, 13.0, 14.0, 15.0])
    bars = pd.DataFrame(
        {
            "bar_start_utc": starts,
            "bar_end_utc": starts + pd.Timedelta(hours=4),
            "mid_open": closes - 0.1,
            "mid_high": highs,
            "mid_low": lows,
            "mid_close": closes,
        }
    )
    policy = {
        "mechanic": "DONCHIAN",
        "entry_lookback": 3,
        "exit_lookback": 2,
        "atr_period": 2,
    }
    changed = bars.copy()
    changed.loc[changed.index > 3, ["mid_open", "mid_high", "mid_low", "mid_close"]] += 500.0

    first = TREND.prepare_policy_bars(bars, policy)
    second = TREND.prepare_policy_bars(changed, policy)

    assert first.loc[3, "entry_high"] == 12.0
    assert first.loc[3, "desired_direction"] == 1
    pd.testing.assert_series_equal(
        first.loc[3, ["atr", "entry_high", "entry_low", "desired_direction"]],
        second.loc[3, ["atr", "entry_high", "entry_low", "desired_direction"]],
    )


def test_long_enters_ask_and_stops_on_bid() -> None:
    m5 = _m5(
        [
            {"bid_open": 100.0, "bid_low": 99.5},
            {"bid_open": 100.0, "bid_low": 98.0},
            {"bid_open": 99.0},
        ]
    )
    trades = _simulate(m5, _decisions(m5, [0], [1]))

    assert len(trades) == 1
    assert trades.loc[0, "entry_price"] == 100.2
    assert trades.loc[0, "initial_stop"] == 98.2
    assert trades.loc[0, "exit_price"] == 98.2
    assert trades.loc[0, "exit_reason"] == "STOP"


def test_short_enters_bid_and_stops_on_ask() -> None:
    m5 = _m5(
        [
            {"bid_open": 100.0, "ask_high": 100.7},
            {"bid_open": 100.0, "ask_high": 102.2},
            {"bid_open": 101.0},
        ]
    )
    trades = _simulate(m5, _decisions(m5, [0], [-1]))

    assert len(trades) == 1
    assert trades.loc[0, "entry_price"] == 100.0
    assert trades.loc[0, "initial_stop"] == 102.0
    assert trades.loc[0, "exit_price"] == 102.0
    assert trades.loc[0, "exit_reason"] == "STOP"


def test_gap_through_stop_uses_worse_executable_open() -> None:
    m5 = _m5(
        [
            {"bid_open": 100.0, "bid_low": 99.5},
            {"bid_open": 97.5, "ask_open": 97.7, "bid_low": 97.0},
            {"bid_open": 98.0},
        ]
    )
    trades = _simulate(m5, _decisions(m5, [0], [1]))

    assert len(trades) == 1
    assert trades.loc[0, "exit_price"] == 97.5
    assert trades.loc[0, "exit_reason"] == "GAP_THROUGH_STOP"


def test_completed_decision_trail_only_tightens() -> None:
    m5 = _m5(
        [
            {"bid_open": 100.0, "bid_high": 101.0, "bid_low": 99.5},
            {"bid_open": 101.0, "bid_high": 105.0, "bid_low": 100.5},
            {"bid_open": 104.0, "bid_high": 104.5, "bid_low": 103.4},
            {"bid_open": 103.0},
        ]
    )
    trades = _simulate(m5, _decisions(m5, [0, 2], [1, 0]))

    assert len(trades) == 1
    assert trades.loc[0, "initial_stop"] == 98.2
    assert trades.loc[0, "final_stop"] == 103.5
    assert trades.loc[0, "final_stop"] > trades.loc[0, "initial_stop"]
    assert trades.loc[0, "exit_price"] == 103.5


def test_exit_blocks_same_decision_and_exact_future_cooldown() -> None:
    m5 = _m5(
        [
            {"bid_open": 100.0, "bid_low": 99.5},
            {"bid_open": 97.5, "ask_open": 97.7, "bid_low": 97.0},
            {"bid_open": 100.0, "bid_low": 99.5},
            {"bid_open": 100.0, "bid_low": 99.5},
            {"bid_open": 100.0, "bid_low": 99.5},
            {"bid_open": 101.0, "bid_low": 100.5},
        ]
    )
    decisions = _decisions(m5, [0, 1, 2, 3, 4], [1, 1, 1, 1, 1])
    trades = _simulate(m5, decisions, _policy(cooldown=2))

    assert len(trades) == 2
    assert trades.loc[1, "entry_time"] == m5.loc[4, "bar_start_utc"]


def test_closed_drawdown_includes_initial_zero() -> None:
    assert TREND.closed_drawdown(pd.Series([-2.0, 1.0])) == 2.0


def test_holm_adjustment_is_monotone_in_rank_order() -> None:
    adjusted = TREND.holm_adjust({"a": 0.01, "b": 0.04, "c": 0.03})
    assert adjusted == {"a": 0.03, "c": 0.06, "b": 0.06}


def test_six_registered_attempts_are_exact_and_unique() -> None:
    config = json.loads(
        (ROOT / "config" / "trailing_trend_specialists_v1.json").read_text(
            encoding="utf-8"
        )
    )
    policies = config["policies"]
    assert len(policies) == 6
    assert [policy["attempt_no"] for policy in policies] == list(
        range(11094, 11100)
    )
    assert len({policy["policy_id"] for policy in policies}) == 6
    assert config["research_controls"]["parameter_search_count"] == 0
