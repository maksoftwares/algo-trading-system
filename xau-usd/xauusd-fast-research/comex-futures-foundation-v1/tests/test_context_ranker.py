from __future__ import annotations

import pandas as pd

from context_ranker import join_context, prepare_spot_context, select_trades


def m5_rows() -> pd.DataFrame:
    times = pd.date_range("2022-12-31T00:00:00Z", periods=60, freq="5min")
    values = pd.Series(range(60), dtype=float) + 100.0
    return pd.DataFrame(
        {
            "timestamp_ms": times.astype("int64") // 1_000_000,
            "mid_high": values + 0.5,
            "mid_low": values - 0.5,
            "mid_close": values,
            "atr": 2.0,
            "atr_ratio": 1.0,
            "quote_intensity_ratio": 1.0,
            "tick_imbalance_5m": 0.2,
            "tick_imbalance_15m": 0.1,
            "tick_microprice_edge_last": 0.02,
            "price_efficiency_5m": 0.5,
            "tick_spread_last": 0.1,
            "body_fraction": 0.5,
        }
    )


def test_spot_context_is_available_only_after_bar_completion() -> None:
    context = prepare_spot_context(m5_rows())
    assert context.iloc[0]["available_time_utc"] == pd.Timestamp("2022-12-31T00:05:00Z")


def test_join_uses_completed_bar_and_direction_adjustment() -> None:
    candidate = pd.DataFrame(
        {
            "candidate_id": ["a"],
            "feature_time_utc": pd.to_datetime(["2022-12-31T04:55:00Z"]),
            "instrument_id": [1],
            "family": ["flow_continuation"],
            "direction": ["SHORT"],
            "contract_volume_5s": [20.0],
            "flow_imbalance_5s": [-0.7],
            "flow_imbalance_30s": [-0.4],
            "volume_share_5s_of_60s": [0.3],
            "price_impulse_ticks_5s": [-3.0],
        }
    )
    label = pd.DataFrame(
        {
            "candidate_id": ["a"],
            "family": ["flow_continuation"],
            "direction": ["SHORT"],
            "status": ["RESOLVED"],
            "entry_time_utc": pd.to_datetime(["2022-12-31T04:55:01Z"]),
            "exit_time_utc": pd.to_datetime(["2022-12-31T05:00:00Z"]),
            "stress_net_pnl_usd": [1.0],
            "stress_net_r": [0.5],
        }
    )
    joined = join_context(candidate, label, m5_rows())
    assert joined.iloc[0]["available_time_utc"] == pd.Timestamp("2022-12-31T04:55:00Z")
    assert joined.iloc[0]["dir_flow_imbalance_5s"] == 0.7
    assert joined.iloc[0]["dir_price_impulse_ticks_5s"] == 3.0


def test_selection_enforces_one_open_trade_and_daily_cap() -> None:
    rows = pd.DataFrame(
        {
            "entry_time_utc": pd.to_datetime(["2023-01-02T10:00:00Z", "2023-01-02T10:05:00Z", "2023-01-02T11:00:00Z"]),
            "exit_time_utc": pd.to_datetime(["2023-01-02T10:30:00Z", "2023-01-02T10:10:00Z", "2023-01-02T11:10:00Z"]),
            "model_score": [0.5, 0.9, 0.8],
        }
    )
    selected = select_trades(
        rows,
        0.1,
        {"maximum_trades_per_family_day": 2, "cooldown_minutes": 15},
    )
    assert selected["model_score"].tolist() == [0.5, 0.8]
