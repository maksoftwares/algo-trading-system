from __future__ import annotations

import pandas as pd
import pandas.testing as pdt
import pytest

from tbbo_features import (
    add_flow_features,
    aggregate_tbbo_seconds,
    generate_candidates,
    load_feature_config,
    normalize_tbbo,
)


def events() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "ts_event": pd.to_datetime(
                [
                    "2026-01-05T13:20:00.100Z",
                    "2026-01-05T13:20:00.800Z",
                    "2026-01-05T13:20:01.100Z",
                    "2026-01-05T13:20:06.100Z",
                ]
            ),
            "publisher_id": [1, 1, 1, 1],
            "instrument_id": [101, 101, 101, 101],
            "sequence": [1, 2, 3, 4],
            "side": ["B", "A", "B", "N"],
            "price": [100.1, 100.0, 100.2, 100.3],
            "size": [5, 2, 3, 7],
            "bid_px_00": [100.0, 100.0, 100.1, 100.2],
            "ask_px_00": [100.1, 100.1, 100.2, 100.3],
            "bid_sz_00": [12, 10, 15, 9],
            "ask_sz_00": [8, 10, 5, 11],
        }
    )


def test_side_mapping_and_completed_second_timestamp() -> None:
    normalized = normalize_tbbo(events())
    assert normalized["aggressor_sign"].tolist() == [1.0, -1.0, 1.0, 0.0]
    assert normalized["signed_volume"].tolist() == [5.0, -2.0, 3.0, 0.0]
    assert normalized.iloc[0]["feature_time_utc"] == pd.Timestamp("2026-01-05T13:20:01Z")


def test_second_bar_uses_last_pretrade_bbo_and_all_trade_volume() -> None:
    seconds = aggregate_tbbo_seconds(events(), tick_size=0.1)
    first = seconds.iloc[0]
    assert first["trade_count"] == 2
    assert first["contract_volume"] == pytest.approx(7.0)
    assert first["signed_volume"] == pytest.approx(3.0)
    assert first["bid_size"] == pytest.approx(10.0)
    assert first["ask_size"] == pytest.approx(10.0)
    assert first["spread_ticks"] == pytest.approx(1.0)


def test_future_events_cannot_change_earlier_features() -> None:
    config = load_feature_config()
    early_events = events().iloc[:3].copy()
    early = add_flow_features(aggregate_tbbo_seconds(early_events, tick_size=0.1), config)
    full = add_flow_features(aggregate_tbbo_seconds(events(), tick_size=0.1), config)
    comparable = full.loc[full["feature_time_utc"] <= early["feature_time_utc"].max(), early.columns]
    pdt.assert_frame_equal(early.reset_index(drop=True), comparable.reset_index(drop=True))


def test_roll_instrument_features_do_not_cross_contracts() -> None:
    config = load_feature_config()
    second_contract = events().iloc[[3]].copy()
    second_contract["instrument_id"] = 202
    second_contract["sequence"] = 1
    combined = pd.concat([events().iloc[:3], second_contract], ignore_index=True)
    features = add_flow_features(aggregate_tbbo_seconds(combined, tick_size=0.1), config)
    first_new_contract = features.loc[features["instrument_id"] == 202].iloc[0]
    assert first_new_contract["instrument_age_seconds"] == 0
    assert first_new_contract["contract_volume_60s"] == pytest.approx(7.0)
    assert pd.isna(first_new_contract["price_impulse_ticks_5s"])


def test_duplicate_trade_event_is_rejected() -> None:
    duplicated = pd.concat([events(), events().iloc[[0]]], ignore_index=True)
    with pytest.raises(ValueError, match="duplicate"):
        normalize_tbbo(duplicated)


def feature_rows() -> pd.DataFrame:
    timestamps = pd.to_datetime(
        [
            "2026-07-01T12:30:00Z",
            "2026-07-01T12:31:00Z",
            "2026-07-01T12:33:00Z",
        ]
    )
    return pd.DataFrame(
        {
            "feature_time_utc": timestamps,
            "instrument_id": [101, 101, 101],
            "instrument_age_seconds": [600, 660, 780],
            "contract_volume_5s": [30.0, 35.0, 40.0],
            "flow_imbalance_5s": [0.70, -0.72, -0.75],
            "flow_imbalance_30s": [0.40, -0.45, -0.20],
            "volume_share_5s_of_60s": [0.30, 0.35, 0.40],
            "price_impulse_ticks_5s": [3.0, -3.0, 0.5],
            "quote_imbalance": [0.20, -0.25, 0.30],
            "spread_ticks": [1.0, 1.0, 1.0],
        }
    )


def test_locked_rules_emit_continuation_and_absorption_candidates() -> None:
    result = generate_candidates(feature_rows(), load_feature_config())
    assert result[["family", "direction"]].to_dict("records") == [
        {"family": "flow_continuation", "direction": "LONG"},
        {"family": "flow_continuation", "direction": "SHORT"},
        {"family": "absorption_reversal", "direction": "LONG"},
    ]


def test_session_is_dst_aware_and_excludes_premarket() -> None:
    frame = feature_rows().iloc[[0]].copy()
    frame["feature_time_utc"] = pd.to_datetime(["2026-01-05T12:30:00Z"])
    result = generate_candidates(frame, load_feature_config())
    assert result.empty


def test_contract_is_research_only_and_causal() -> None:
    controls = load_feature_config()["research_controls"]
    assert controls["features_use_completed_windows_only"] is True
    assert controls["cross_instrument_roll_features_prohibited"] is True
    assert controls["random_split_prohibited"] is True
    assert controls["broker_action_authorized"] is False
