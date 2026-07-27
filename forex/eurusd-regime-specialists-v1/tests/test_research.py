from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from eurusd_regime_specialists.research import (
    active_weekday_fx_days,
    generate_raw_signals,
    metric_block,
    verify_lock,
    wilder_average,
    walk_long_exit,
)
from eurusd_regime_specialists.ensemble import verify_ensemble_lock
from eurusd_regime_specialists.asymmetric import (
    payoff_metrics,
    verify_asymmetric_lock,
    walk_timed_long_exit,
)
from eurusd_regime_specialists.confirmed_reversal import verify_lock as verify_confirmation_lock
from eurusd_regime_specialists.crossasset_handoff import verify_lock as verify_handoff_lock
from eurusd_regime_specialists.retrospective_overfit import (
    density_bucket,
    perfect_foresight_oracle,
    resolve_portfolio,
    select_cells,
)


def test_lock():
    assert len(verify_lock()) == 2
    assert len(verify_ensemble_lock()) == 2
    assert len(verify_asymmetric_lock()) == 2
    assert len(verify_confirmation_lock()) == 2
    assert len(verify_handoff_lock()) == 2


def test_wilder_seed_and_recursion():
    values = pd.Series([float("nan"), 1.0, 2.0, 3.0, 4.0])
    actual = wilder_average(values, 3)
    assert actual.iloc[3] == 2.0
    assert actual.iloc[4] == (2.0 * 2.0 + 4.0) / 3.0


def test_same_bar_is_stop_first():
    index = pd.date_range("2026-01-01", periods=1, freq="5min", tz="UTC")
    frame = pd.DataFrame(
        {"bid_open": [1.0], "bid_low": [0.8], "bid_high": [1.2], "bid_close": [1.0]},
        index=index,
    )
    _, price, reason = walk_long_exit(frame, 0, 0.9, 1.1, 0.01)
    assert reason == "STOP"
    assert price == 0.89


def test_timed_exit_uses_last_bid_close():
    index = pd.date_range("2026-01-01", periods=3, freq="5min", tz="UTC")
    frame = pd.DataFrame(
        {
            "bid_open": [1.0, 1.01, 1.02],
            "bid_low": [0.99, 1.0, 1.01],
            "bid_high": [1.01, 1.02, 1.03],
            "bid_close": [1.005, 1.015, 1.025],
        },
        index=index,
    )
    _, price, reason = walk_timed_long_exit(
        frame, 0, index[-1], 0.8, 1.2, 0.001
    )
    assert reason == "TIME_12H"
    assert price == 1.024


def test_realized_payoff_ratio_is_average_win_over_average_loss():
    result = payoff_metrics(pd.DataFrame({"r": [1.5, 1.5, -1.0, -1.0]}))
    assert result["win_rate"] == 0.5
    assert result["realized_payoff_ratio"] == 1.5
    assert result["profit_factor"] == 1.5


def test_drawdown_includes_zero_origin():
    assert metric_block(pd.DataFrame({"r": [-1.0, 0.2]}))["max_drawdown_r"] == 1.0


def test_active_day_denominator_excludes_sunday_fragment():
    index = pd.to_datetime(
        ["2026-01-04T22:00:00Z", "2026-01-05T00:00:00Z", "2026-01-06T00:00:00Z"]
    )
    frame = pd.DataFrame({"x": [1, 1, 1]}, index=index)
    assert active_weekday_fx_days(
        frame, pd.Timestamp("2026-01-04T00:00:00Z"), pd.Timestamp("2026-01-06T23:59:59Z")
    ) == 2


def test_signal_uses_latest_completed_state_across_context_gap():
    idx = pd.date_range("2026-01-01", periods=50, freq="30min", tz="UTC")
    m5_idx = pd.date_range("2026-01-01", periods=300, freq="5min", tz="UTC")
    price = [1.1] * 294 + [1.08] * 6
    m5 = pd.DataFrame(
        {
            "timestamp_ms": m5_idx.astype("int64") // 1_000_000,
            "bid_open": price,
            "bid_high": price,
            "bid_low": price,
            "bid_close": price,
            "ask_open": [x + 0.0001 for x in price],
            "ask_high": [x + 0.0001 for x in price],
            "ask_low": [x + 0.0001 for x in price],
            "ask_close": [x + 0.0001 for x in price],
            "tick_count": 1,
        },
        index=m5_idx,
    )
    state = pd.DataFrame(
        {
            "direction": ["NEUTRAL"],
            "phase": ["UNRESOLVED"],
            "shock": [False],
            "DXY_compressed": [False],
            "EURUSD_compressed": [False],
        },
        index=pd.DatetimeIndex([idx[-10]], name="timestamp_utc"),
    )
    cfg = {
        "seed": {
            "bands_period": 20,
            "bands_deviation": 2.0,
            "rsi_period": 14,
            "rsi_oversold": 35.0,
            "atr_period": 14,
            "recent_low_bars": 6,
        }
    }
    signals = generate_raw_signals(m5, state, cfg)
    assert not signals.empty
    assert signals.iloc[-1]["owner"] == "S4_NEUTRAL_AUCTION"


def test_retrospective_selector_uses_realized_cell_outcomes():
    rows = []
    for hour, results in (
        (8, [1.5] * 8 + [-1.0] * 7),
        (9, [1.5] * 4 + [-1.0] * 11),
    ):
        for index, result in enumerate(results):
            rows.append(
                {
                    "owner": "S1",
                    "seed_id": "FAST",
                    "entry_hour_utc": hour,
                    "entry_time_utc": pd.Timestamp(
                        "2020-01-01T00:00:00Z"
                    )
                    + pd.Timedelta(days=index),
                    "r": result,
                }
            )
    selected, _ = select_cells(pd.DataFrame(rows))
    assert selected["entry_hour_utc"].tolist() == [8]


def test_retrospective_portfolio_keeps_one_position_at_a_time():
    frame = pd.DataFrame(
        {
            "entry_time_utc": pd.to_datetime(
                [
                    "2026-01-01T00:00:00Z",
                    "2026-01-01T00:05:00Z",
                    "2026-01-01T01:05:00Z",
                ]
            ),
            "exit_time_utc": pd.to_datetime(
                [
                    "2026-01-01T01:00:00Z",
                    "2026-01-01T00:30:00Z",
                    "2026-01-01T02:00:00Z",
                ]
            ),
            "owner_priority": [0, 0, 0],
            "seed_priority": [0, 0, 0],
        }
    )
    resolved = resolve_portfolio(frame, maximum_trades_per_utc_day=12)
    assert len(resolved) == 2


def test_density_oracle_keeps_only_exact_count_days():
    frame = pd.DataFrame(
        {
            "entry_time_utc": pd.to_datetime(
                [
                    "2026-01-01T00:00:00Z",
                    "2026-01-01T01:00:00Z",
                    "2026-01-02T00:00:00Z",
                    "2026-01-02T01:00:00Z",
                    "2026-01-02T02:00:00Z",
                ]
            ),
            "owner_priority": [0, 0, 0, 0, 0],
            "seed_priority": [0, 0, 0, 0, 0],
        }
    )
    selected = density_bucket(frame, trades_per_day=2)
    assert len(selected) == 2
    assert selected["entry_time_utc"].dt.day.unique().tolist() == [1]


def test_perfect_foresight_oracle_discards_every_loss():
    frame = pd.DataFrame(
        {
            "entry_time_utc": pd.to_datetime(
                [f"2026-01-01T0{hour}:00:00Z" for hour in range(6)]
            ),
            "owner_priority": [0] * 6,
            "seed_priority": [0] * 6,
            "exit_reason": ["TARGET"] * 5 + ["STOP"],
            "r": [1.5] * 5 + [-1.0],
        }
    )
    selected = perfect_foresight_oracle(frame, winners_per_active_day=4)
    assert len(selected) == 4
    assert (selected["r"] > 0).all()
