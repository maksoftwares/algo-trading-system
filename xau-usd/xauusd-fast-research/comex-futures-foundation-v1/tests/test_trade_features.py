from __future__ import annotations

import pandas as pd
import pandas.testing as pdt
import pytest

from tbbo_features import (
    add_flow_features,
    aggregate_trade_seconds,
    generate_trade_candidates,
    load_trade_feature_config,
    normalize_trades,
)


def trades() -> pd.DataFrame:
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
        }
    )


def test_trade_schema_does_not_require_unavailable_book_fields() -> None:
    normalized = normalize_trades(trades())
    assert normalized["aggressor_sign"].tolist() == [1.0, -1.0, 1.0, 0.0]
    assert normalized["signed_volume"].tolist() == [5.0, -2.0, 3.0, 0.0]
    assert not any(column.startswith("bid_") or column.startswith("ask_") for column in normalized)


def test_identical_trade_rows_are_counted_as_distinct_fills() -> None:
    duplicated = pd.concat([trades().iloc[[0]], trades().iloc[[0]]], ignore_index=True)
    normalized = normalize_trades(duplicated)
    seconds = aggregate_trade_seconds(duplicated, tick_size=0.1)
    assert normalized["event_ordinal_in_message"].tolist() == [0, 1]
    assert seconds.iloc[0]["trade_count"] == 2
    assert seconds.iloc[0]["contract_volume"] == pytest.approx(10.0)


def test_trade_second_bar_uses_all_prints() -> None:
    seconds = aggregate_trade_seconds(trades(), tick_size=0.1)
    first = seconds.iloc[0]
    assert first["trade_count"] == 2
    assert first["contract_volume"] == pytest.approx(7.0)
    assert first["signed_volume"] == pytest.approx(3.0)
    assert first["trade_price_last"] == pytest.approx(100.0)
    assert first["mid_px"] == pytest.approx(100.0)


def test_trade_features_are_causal() -> None:
    config = load_trade_feature_config()
    early = add_flow_features(aggregate_trade_seconds(trades().iloc[:3], tick_size=0.1), config)
    full = add_flow_features(aggregate_trade_seconds(trades(), tick_size=0.1), config)
    comparable = full.loc[full["feature_time_utc"] <= early["feature_time_utc"].max(), early.columns]
    pdt.assert_frame_equal(early.reset_index(drop=True), comparable.reset_index(drop=True))


def feature_rows() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "feature_time_utc": pd.to_datetime(
                [
                    "2026-07-01T12:30:00Z",
                    "2026-07-01T12:31:00Z",
                    "2026-07-01T12:33:00Z",
                ]
            ),
            "instrument_id": [101, 101, 101],
            "instrument_age_seconds": [600, 660, 780],
            "contract_volume_5s": [30.0, 35.0, 40.0],
            "flow_imbalance_5s": [0.70, -0.72, -0.75],
            "flow_imbalance_30s": [0.40, -0.45, -0.20],
            "volume_share_5s_of_60s": [0.30, 0.35, 0.40],
            "price_impulse_ticks_5s": [3.0, -3.0, 0.5],
        }
    )


def test_trade_rules_emit_both_locked_mechanisms() -> None:
    result = generate_trade_candidates(feature_rows(), load_trade_feature_config())
    assert result[["family", "direction"]].to_dict("records") == [
        {"family": "flow_continuation", "direction": "LONG"},
        {"family": "flow_continuation", "direction": "SHORT"},
        {"family": "absorption_reversal", "direction": "LONG"},
    ]


def test_trade_contract_is_zero_payment_and_research_only() -> None:
    controls = load_trade_feature_config()["research_controls"]
    assert controls["zero_payment_lane"] is True
    assert controls["unavailable_bbo_fields_must_not_be_imputed"] is True
    assert controls["broker_action_authorized"] is False
