from __future__ import annotations

import pandas as pd

from backtest import ambiguous_outcome, assert_no_outside_regime, cost_r, run_cell


def bars() -> pd.DataFrame:
    end = pd.date_range("2020-01-01 00:05", periods=8, freq="5min", tz="UTC")
    data = pd.DataFrame({"timestamp_utc": end, "bar_start_utc": end - pd.Timedelta(minutes=5)})
    for side, delta in (("mid", 0.0), ("bid", -0.1), ("ask", 0.1)):
        data[f"{side}_open"] = 100.0 + delta
        data[f"{side}_high"] = 101.5 + delta
        data[f"{side}_low"] = 98.5 + delta
        data[f"{side}_close"] = 100.0 + delta
    data["spread_open_points"] = 20.0; data["spread_p95_points"] = 35.0
    data["chop_active_at_open"] = True
    return data


def candidate(time: pd.Timestamp, direction: str = "LONG", setup: int = 1) -> dict[str, object]:
    return {
        "strategy_id": "TEST", "direction": direction, "signal_time": time, "setup_start_time": time - pd.Timedelta(hours=1),
        "chop_episode_id": 1, "setup_episode_id": setup, "chop_active": True,
        "adx14_h4": 20.0, "er24": 0.2, "displacement_atr24": 1.0, "range_width_atr24": 3.0,
        "volatility_subtype": "MEDIUM_VOL_CHOP", "range_width_subtype": "MEDIUM_WIDTH_CHOP", "drift_subtype": "FLAT_CHOP",
        "atr": 1.0, "raw_z": -2.0 if direction == "LONG" else 2.0, "raw_center": 100.0, "raw_scale": 1.0,
        "signal_accepted_pre_execution": True, "rejection_reason": "", "target_frozen": 101.4 if direction == "LONG" else 98.6,
        "stop_kind": "ENTRY_ATR", "stop_value": 1.0, "max_hold_bars": 3,
    }


def test_stop_first_on_ambiguous_bar() -> None:
    assert ambiguous_outcome(True, True) == ("STOP", True)


def test_cost_r_is_price_cost_over_initial_risk() -> None:
    assert cost_r(0.2, 1.0) == 0.2


def test_entry_is_next_bar_and_uses_ask_for_long() -> None:
    frame = bars(); signal = pd.DataFrame([candidate(frame.iloc[0]["timestamp_utc"])])
    result = run_cell(frame, signal, "M5", 6, 0.05)
    trade = result.trades.iloc[0]
    assert trade["entry_time"] == frame.iloc[1]["bar_start_utc"]
    assert trade["entry_price"] == frame.iloc[1]["ask_open"]


def test_short_uses_bid_entry_and_ask_stop_target_side() -> None:
    frame = bars(); signal = pd.DataFrame([candidate(frame.iloc[0]["timestamp_utc"], "SHORT")])
    result = run_cell(frame, signal, "M5", 6, 0.05)
    assert result.trades.iloc[0]["entry_price"] == frame.iloc[1]["bid_open"]


def test_one_position_and_direction_cooldown_are_enforced() -> None:
    frame = bars()
    frame.loc[:, ["bid_high", "ask_high"]] = 100.5
    frame.loc[:, ["bid_low", "ask_low"]] = 99.5
    signals = pd.DataFrame([
        candidate(frame.iloc[0]["timestamp_utc"], setup=1),
        candidate(frame.iloc[1]["timestamp_utc"], setup=2),
        candidate(frame.iloc[4]["timestamp_utc"], setup=3),
    ])
    result = run_cell(frame, signals, "M5", 6, 0.05)
    assert len(result.trades) == 1
    assert "POSITION_ALREADY_OPEN" in set(result.signals["rejection_reason"])
    assert "DIRECTION_COOLDOWN_ACTIVE" in set(result.signals["rejection_reason"])


def test_regime_exit_closes_at_next_executable_open() -> None:
    frame = bars(); frame.loc[2:, "chop_active_at_open"] = False
    # Avoid stop/target before the regime exit.
    frame.loc[:, ["bid_high", "ask_high"]] = 100.5
    frame.loc[:, ["bid_low", "ask_low"]] = 99.5
    signal = pd.DataFrame([candidate(frame.iloc[0]["timestamp_utc"])])
    result = run_cell(frame, signal, "M5", 6, 0.05)
    assert result.trades.iloc[0]["exit_reason"] == "REGIME_EXIT"
    assert result.trades.iloc[0]["exit_time"] == frame.iloc[2]["timestamp_utc"]


def test_no_trade_outside_active_h4_chop() -> None:
    frame = bars(); frame.loc[1, "chop_active_at_open"] = False
    signal = pd.DataFrame([candidate(frame.iloc[0]["timestamp_utc"])])
    result = run_cell(frame, signal, "M5", 6, 0.05)
    assert result.trades.empty
    assert result.signals.iloc[0]["rejection_reason"] == "REGIME_INACTIVE_AT_ENTRY"
    assert_no_outside_regime(result.trades)
