from __future__ import annotations

import pandas as pd

from hour_ranker import label_both_directions, regular_signals


def m5_fixture() -> pd.DataFrame:
    times = pd.date_range("2023-01-03T12:00:00Z", periods=80, freq="5min")
    price = pd.Series(range(80), dtype=float) * 0.1 + 1800.0
    return pd.DataFrame({"timestamp_ms": times.astype("int64") // 1_000_000, "mid_high": price + 0.2, "mid_low": price - 0.2, "mid_close": price, "atr": 2.0, "atr_ratio": 1.0, "quote_intensity_ratio": 1.0, "tick_imbalance_5m": 0.1, "tick_imbalance_15m": 0.1, "tick_microprice_edge_last": 0.01, "price_efficiency_5m": 0.5, "tick_spread_last": 0.1, "body_fraction": 0.5, "ask_open": price + 0.05, "bid_open": price - 0.05, "ask_high": price + 0.25, "bid_low": price - 0.25, "ask_close": price + 0.05, "bid_close": price - 0.05})


def test_regular_signals_use_completed_m15_boundaries() -> None:
    signals = regular_signals(m5_fixture(), "2023-01-03T00:00:00Z", "2023-01-04T00:00:00Z")
    assert not signals.empty
    assert signals["signal_time"].dt.minute.mod(15).eq(0).all()
    assert (signals["available_time_utc"] <= signals["signal_time"]).all()


def test_side_correct_labels_charge_costs() -> None:
    m5 = m5_fixture()
    signals = regular_signals(m5, "2023-01-03T00:00:00Z", "2023-01-04T00:00:00Z").iloc[[0]]
    labeled = label_both_directions(signals, m5, {"horizon_m5_bars": 12, "stop_atr": 1.5, "ticket_cost_usd": 0.3, "stress_slippage_r": 0.05})
    assert labeled.iloc[0]["long_stress_net_r"] < 1.0
    assert labeled.iloc[0]["short_stress_net_r"] < 0.0
