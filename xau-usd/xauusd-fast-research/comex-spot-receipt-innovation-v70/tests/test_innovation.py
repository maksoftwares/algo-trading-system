from __future__ import annotations

from pathlib import Path
import sys

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from innovation import (  # noqa: E402
    build_innovation_features,
    bucket_received_trades,
    canonical_hash,
    generate_candidates,
    normalize_received_trades,
    policy_grid,
    publisher_clock_lead_rows,
)


def trade_frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "ts_recv": pd.to_datetime(
                [
                    "2025-01-02T12:00:00.050Z",
                    "2025-01-02T12:00:00.250Z",
                    "2025-01-02T12:00:00.450Z",
                ],
                utc=True,
            ),
            "ts_event": pd.to_datetime(
                [
                    "2025-01-02T12:00:00.040Z",
                    "2025-01-02T12:00:00.240Z",
                    "2025-01-02T12:00:00.440Z",
                ],
                utc=True,
            ),
            "instrument_id": [1, 1, 1],
            "side": ["B", "B", "B"],
            "price": [2000.0, 2000.5, 2001.0],
            "size": [3, 4, 5],
        }
    )


def test_received_trade_normalization_uses_receipt_clock_as_primary() -> None:
    frame = trade_frame()
    frame.loc[0, "ts_recv"] = pd.Timestamp("2025-01-02T12:00:00.030Z")
    normalized = normalize_received_trades(frame)
    assert normalized["ts_recv"].is_monotonic_increasing
    assert publisher_clock_lead_rows(frame) == 1


def test_receipt_bucket_ends_strictly_after_source_messages() -> None:
    buckets = bucket_received_trades(trade_frame(), bucket_ms=100)
    assert (buckets["last_source_recv_utc"] < buckets["feature_time_utc"]).all()
    assert buckets["received_volume"].sum() == 12


def test_innovation_uses_only_strictly_prior_spot_quotes() -> None:
    buckets = bucket_received_trades(trade_frame(), bucket_ms=100)
    quotes = pd.DataFrame(
        {
            "timestamp_ms": [
                1735819199999,
                1735819200099,
                1735819200299,
                1735819200499,
            ],
            "bid": [1999.8, 1999.8, 2000.0, 2000.1],
            "ask": [2000.0, 2000.0, 2000.2, 2000.3],
            "mid": [1999.9, 1999.9, 2000.1, 2000.2],
        }
    )
    features = build_innovation_features(
        buckets,
        quotes,
        horizon_ms=200,
        maximum_spot_quote_staleness_ms=1000,
        maximum_comex_baseline_staleness_ms=100,
    )
    assert not features.empty
    assert (
        features["current_spot_quote_timestamp_ms"] < features["decision_timestamp_ms"]
    ).all()
    assert (features["directional_innovation_usd"] > 0).all()


def test_grid_registers_exactly_one_thousand_policies() -> None:
    calibration = {
        "horizon_ms_grid": [250, 500, 1000, 2000, 5000],
        "minimum_absolute_comex_move_usd_grid": [0.4, 0.6, 0.8, 1.0, 1.2],
        "minimum_directional_innovation_usd_grid": [0.2, 0.3, 0.4, 0.5, 0.6],
        "minimum_absolute_flow_imbalance_grid": [0.0, 0.15, 0.3, 0.45],
        "minimum_received_volume_grid": [5, 10],
    }
    assert len(policy_grid(calibration)) == 1000


def test_candidate_router_keeps_only_first_event_per_date() -> None:
    features = pd.DataFrame(
        {
            "feature_time_utc": pd.to_datetime(
                ["2025-01-02T12:00:00Z", "2025-01-02T12:01:00Z"], utc=True
            ),
            "instrument_id": [1, 1],
            "horizon_ms": [500, 500],
            "comex_move_usd": [1.0, 1.2],
            "directional_innovation_usd": [0.8, 0.9],
            "flow_imbalance": [0.6, 0.7],
            "horizon_received_volume": [20, 30],
            "decision_timestamp_ms": [1735819200000, 1735819260000],
            "direction": ["LONG", "LONG"],
        }
    )
    policy = {
        "horizon_ms": 500,
        "minimum_absolute_comex_move_usd": 0.4,
        "minimum_directional_innovation_usd": 0.2,
        "minimum_absolute_flow_imbalance": 0.0,
        "minimum_received_volume": 5,
    }
    selected = generate_candidates(features, policy=policy, family="TEST")
    assert len(selected) == 1
    assert selected["decision_timestamp_ms"].iloc[0] == 1735819200000


def test_contract_hash_excludes_only_hash_field() -> None:
    payload = {"value": 1}
    payload["contract_sha256"] = canonical_hash(payload, "contract_sha256")
    assert payload["contract_sha256"] == canonical_hash(payload, "contract_sha256")
    payload["value"] = 2
    assert payload["contract_sha256"] != canonical_hash(payload, "contract_sha256")
