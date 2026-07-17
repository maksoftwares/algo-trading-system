from __future__ import annotations

from pathlib import Path

import pandas as pd

from m15_comex_ranker import align_comex_context, normalize_m15_time_columns, source_date
from tbbo_features import load_trade_feature_config


def test_source_date_is_strict() -> None:
    assert source_date(Path("glbx-mdp3-20220701.trades.dbn.zst")) == "20220701"


def test_alignment_uses_completed_second_and_direction() -> None:
    times = pd.date_range("2023-01-03T13:15:00Z", periods=305, freq="s")
    events = pd.DataFrame({"ts_event": times, "publisher_id": 1, "instrument_id": 10, "sequence": range(305), "side": "B", "price": 100.0 + pd.Series(range(305)) * 0.1, "size": 10})
    candidate = pd.DataFrame({"signal_time": pd.to_datetime(["2023-01-03T13:20:05Z"]), "direction_sign": [-1], "stress_net_r": [0.5], **{name: [0.1] for name in ["dir_return_15m_atr", "dir_return_1h_atr", "dir_return_4h_atr", "dir_return_24h_atr", "range_atr", "atr_ratio", "body_fraction", "dir_close_location", "efficiency_ratio_16", "dir_ema32_distance_atr", "quote_intensity_ratio_m15", "dir_tick_imbalance_5m", "dir_tick_imbalance_15m", "m5_quote_intensity_ratio", "spread_atr", "hour_sin", "hour_cos", "weekday_sin", "weekday_cos"]}})
    result = align_comex_context(events, candidate, load_trade_feature_config())
    assert len(result) == 1
    assert result.iloc[0]["feature_time_utc"] <= result.iloc[0]["signal_time"]
    assert result.iloc[0]["comex_dir_flow_5s"] == -1.0
    assert result.iloc[0]["comex_dir_impulse_5s"] < 0


def test_ranker_adapter_accepts_original_m15_time_columns() -> None:
    dataset = pd.DataFrame(
        {
            "signal_time": pd.to_datetime(["2022-08-01T12:00:00Z"]),
            "entry_time": pd.to_datetime(["2022-08-01T12:05:00Z"]),
            "exit_time": pd.to_datetime(["2022-08-01T12:10:00Z"]),
        }
    )
    normalized = normalize_m15_time_columns(dataset)
    assert "entry_time_utc" in normalized
    assert "exit_time_utc" in normalized
