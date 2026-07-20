from __future__ import annotations

import json

import pandas as pd

from catchup import (
    build_event_features,
    canonical_hash,
    decode_payload,
    generate_candidates,
    policy_grid,
)


def quote_frame(times: list[int], mids: list[float], spread: float) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "timestamp_ms": times,
            "bid": [value - spread / 2 for value in mids],
            "ask": [value + spread / 2 for value in mids],
            "mid": mids,
        }
    )


def test_decoder_preserves_cumulative_time_and_price() -> None:
    hour = 1_700_000_000_000 - 1_700_000_000_000 % 3_600_000
    payload = {
        "timestamp": hour,
        "multiplier": 0.001,
        "bid": 20.0,
        "ask": 20.02,
        "times": [10, 20],
        "bids": [1, -2],
        "asks": [2, -1],
        "bidVolumes": [1, 2],
        "askVolumes": [3, 4],
    }
    ticks = decode_payload(json.dumps(payload).encode(), scale=3, hour_ms=hour)
    assert [tick.timestamp_ms for tick in ticks] == [hour + 10, hour + 30]
    assert [tick.bid for tick in ticks] == [20.001, 19.999]
    assert [tick.ask for tick in ticks] == [20.022, 20.021]


def test_decoder_accepts_official_empty_hour_shape() -> None:
    payload = {
        "timestamp": None,
        "multiplier": None,
        "bid": None,
        "ask": None,
        "times": [],
        "bids": [],
        "asks": [],
        "bidVolumes": [],
        "askVolumes": [],
    }
    assert decode_payload(json.dumps(payload).encode(), scale=3, hour_ms=0) == ()


def test_features_use_strictly_prior_current_xau_quote() -> None:
    date = pd.Timestamp("2025-01-02T00:00:00Z")
    base = int(pd.Timestamp("2025-01-02T07:00:00Z").timestamp() * 1000)
    xag = quote_frame(
        [base - 1000, base - 100, base, base + 1000],
        [20.0, 20.0, 20.01, 20.02],
        0.02,
    )
    xau = quote_frame(
        [base - 1000, base - 1, base, base + 500],
        [2000.0, 2000.0, 2100.0, 2200.0],
        0.4,
    )
    rule = {
        "session_start_utc": "07:00",
        "session_end_utc": "18:00",
        "maximum_baseline_staleness_ms": 1000,
        "maximum_current_xau_staleness_ms": 1000,
    }
    prefilter = {
        "minimum_absolute_xag_move_bps": 1.0,
        "minimum_directional_innovation_bps": 0.5,
        "maximum_signed_xau_response_ratio": 0.75,
        "minimum_xag_quote_count": 2,
    }
    features = build_event_features(
        date, xag, xau, horizons_ms=[1000], rule=rule, prefilter=prefilter
    )
    assert not features.empty
    assert (features["xau_current_timestamp_ms"] < features["decision_timestamp_ms"]).all()
    assert features.iloc[0]["xau_move_bps"] == 0.0


def test_grid_has_exactly_one_thousand_policies() -> None:
    calibration = {
        "horizon_ms_grid": [1000, 2000, 5000, 10000, 20000],
        "minimum_absolute_xag_move_bps_grid": [1, 2, 3, 4, 5],
        "minimum_directional_innovation_bps_grid": [0.5, 1, 1.5, 2, 2.5],
        "maximum_signed_xau_response_ratio_grid": [0, 0.25, 0.5, 0.75],
        "minimum_xag_quote_count_grid": [2, 5],
    }
    assert len(policy_grid(calibration)) == 1000


def test_router_keeps_first_candidate_per_date() -> None:
    features = pd.DataFrame(
        {
            "feature_time_utc": pd.to_datetime(
                ["2025-01-02T07:01:00Z", "2025-01-02T07:02:00Z"], utc=True
            ),
            "decision_timestamp_ms": [1735801260000, 1735801320000],
            "horizon_ms": [1000, 1000],
            "xag_move_bps": [4.0, -5.0],
            "directional_innovation_bps": [3.0, 4.0],
            "signed_xau_response_ratio": [0.1, 0.0],
            "xag_quote_count": [5, 6],
            "direction": ["LONG", "SHORT"],
        }
    )
    policy = {
        "horizon_ms": 1000,
        "minimum_absolute_xag_move_bps": 1.0,
        "minimum_directional_innovation_bps": 0.5,
        "maximum_signed_xau_response_ratio": 0.75,
        "minimum_xag_quote_count": 2,
    }
    selected = generate_candidates(features, policy=policy, family="TEST")
    assert len(selected) == 1
    assert selected.iloc[0]["direction"] == "LONG"


def test_contract_hash_excludes_only_hash_field() -> None:
    payload = {"value": 1}
    payload["contract_sha256"] = canonical_hash(payload, "contract_sha256")
    assert payload["contract_sha256"] == canonical_hash(payload, "contract_sha256")
    payload["value"] = 2
    assert payload["contract_sha256"] != canonical_hash(payload, "contract_sha256")
