from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

import ml.a3_meta_v1.intraday_crossasset_event_census as census
from ml.a3_meta_v1.intraday_crossasset_event_census import (
    build_m15_features,
    generate_events,
    label_event,
    validate_contract,
)


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "config/ml/a3_ml_intraday_crossasset_event_census_v1.json"


def _contract() -> dict:
    return json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))


def test_contract_locks_hypotheses_causality_and_no_execution() -> None:
    contract = _contract()
    validate_contract(contract)
    assert len(contract["event_families"]) == 4
    assert contract["selection"]["maximum_hypotheses"] == 8
    assert contract["causal_features"]["source_volatility_scale_is_lagged_one_bar"]
    assert contract["authorization"]["broker_action_authorized"] is False

    contract["event_families"].pop()
    with pytest.raises(ValueError, match="family set"):
        validate_contract(contract)

    contract = _contract()
    contract["authorization"]["python_demo_predictions_authorized"] = True
    with pytest.raises(ValueError, match="forbidden"):
        validate_contract(contract)


def _synthetic_sources(m15_bars: int = 140) -> tuple[pd.DataFrame, pd.DataFrame]:
    count = m15_bars * 3
    timestamps = pd.date_range("2019-01-02T00:00:00Z", periods=count, freq="5min")
    timestamp_ms = np.array(
        [int(timestamp.timestamp() * 1000) for timestamp in timestamps], dtype=np.int64
    )
    xau_mid = 1300.0 + np.linspace(0.0, 20.0, count)
    xau = pd.DataFrame(
        {
            "timestamp_ms": timestamp_ms,
            "bid_open": xau_mid - 0.25,
            "bid_high": xau_mid + 0.75,
            "bid_low": xau_mid - 0.75,
            "bid_close": xau_mid + 0.1,
            "ask_open": xau_mid + 0.25,
            "ask_high": xau_mid + 1.25,
            "ask_low": xau_mid - 0.25,
            "ask_close": xau_mid + 0.6,
            "mid_open": xau_mid,
            "mid_high": xau_mid + 1.0,
            "mid_low": xau_mid - 0.5,
            "mid_close": xau_mid + 0.35,
            "atr": np.full(count, 4.0),
        }
    )
    dollar = 100.0 + np.sin(np.arange(count) / 11.0) * 0.5 + np.arange(count) * 0.001
    bond = 110.0 + np.cos(np.arange(count) / 13.0) * 0.4 - np.arange(count) * 0.0005
    macro = pd.DataFrame(
        {
            "timestamp_ms": timestamp_ms,
            "dollaridxusd_mid_open": dollar,
            "dollaridxusd_mid_high": dollar + 0.02,
            "dollaridxusd_mid_low": dollar - 0.02,
            "dollaridxusd_mid_close": dollar + 0.005,
            "ustbondtrusd_mid_open": bond,
            "ustbondtrusd_mid_high": bond + 0.02,
            "ustbondtrusd_mid_low": bond - 0.02,
            "ustbondtrusd_mid_close": bond + 0.005,
            "dollaridxusd_available": np.ones(count, dtype=bool),
            "ustbondtrusd_available": np.ones(count, dtype=bool),
        }
    )
    return xau, macro


def test_m15_features_are_contiguous_and_future_changes_do_not_change_prefix() -> None:
    xau, macro = _synthetic_sources()
    first = build_m15_features(xau, macro, _contract())
    changed = macro.copy()
    changed.loc[360:, "dollaridxusd_mid_close"] *= 1.5
    changed.loc[360:, "dollaridxusd_mid_open"] *= 1.5
    changed.loc[360:, "dollaridxusd_mid_high"] *= 1.5
    changed.loc[360:, "dollaridxusd_mid_low"] *= 1.5
    second = build_m15_features(xau, changed, _contract())

    assert len(first) == 140
    assert first.loc[100, "dollar_z_4"] == pytest.approx(second.loc[100, "dollar_z_4"])
    assert first.loc[100, "bond_z_12"] == pytest.approx(second.loc[100, "bond_z_12"])
    assert (
        first.loc[100, "decision_timestamp_ms"]
        == first.loc[100, "timestamp_ms"] + 900_000
    )


def test_event_generation_preserves_family_and_direction_hypotheses() -> None:
    start = pd.Timestamp("2020-01-02T12:00:00Z")
    rows = []
    for index, sign in enumerate((1.0, -1.0)):
        timestamp = start + pd.Timedelta(minutes=15 * index)
        rows.append(
            {
                "timestamp_ms": int(timestamp.timestamp() * 1000),
                "decision_timestamp_ms": int(
                    (timestamp + pd.Timedelta(minutes=15)).timestamp() * 1000
                ),
                "decision_date_utc": timestamp.strftime("%Y-%m-%d"),
                "inside_decision_session": True,
                "source_last_index": index * 3 + 2,
                "atr": 5.0,
                "mid_open": 1500.0,
                "mid_high": 1502.0,
                "mid_low": 1498.0,
                "mid_close": 1501.0 if sign > 0 else 1499.0,
                "body_fraction": 0.5,
                "dollar_z_4": -2.0 * sign,
                "bond_z_4": 2.0 * sign,
                "dollar_z_12": -2.0 * sign,
                "bond_z_12": 2.0 * sign,
                "xau_return_1_atr": 0.2 * sign,
                "xau_return_4_atr": 0.0,
            }
        )
    events = generate_events(pd.DataFrame(rows), _contract())
    agreement = [
        row
        for row in events
        if row["family_id"] == "crossasset_agreement_continuation_v1"
    ]
    assert {row["direction"] for row in agreement} == {"LONG", "SHORT"}
    assert len({row["event_id"] for row in events}) == len(events)


def test_label_event_resolves_same_bar_collision_stop_first() -> None:
    decision = pd.Timestamp("2020-01-02T12:00:00Z")
    timestamps = pd.date_range(
        decision - pd.Timedelta(minutes=5), periods=146, freq="5min"
    )
    frame = pd.DataFrame(
        {
            "timestamp_ms": np.array(
                [int(timestamp.timestamp() * 1000) for timestamp in timestamps],
                dtype=np.int64,
            ),
            "bid_open": np.full(146, 100.0),
            "bid_high": np.full(146, 101.0),
            "bid_low": np.full(146, 99.0),
            "bid_close": np.full(146, 100.0),
            "ask_open": np.full(146, 100.5),
            "ask_high": np.full(146, 101.5),
            "ask_low": np.full(146, 99.5),
            "ask_close": np.full(146, 100.5),
        }
    )
    frame.loc[1, "bid_high"] = 112.0
    frame.loc[1, "bid_low"] = 92.0
    event = {
        "event_id": "event",
        "family_id": "crossasset_agreement_continuation_v1",
        "direction": "LONG",
        "split": "train",
        "decision_time_utc": decision.isoformat().replace("+00:00", "Z"),
        "decision_timestamp_ms": int(decision.timestamp() * 1000),
        "source_last_index": 0,
        "atr": 4.0,
        "signal_low": 95.0,
        "signal_high": 105.0,
    }
    label = label_event(frame, event, _contract())
    assert label["status"] == "RESOLVED"
    assert label["exit_reason"] == "STOP"
    assert label["exit_price"] == pytest.approx(93.5)


def test_chronological_firewall_does_not_label_later_segments_after_train_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    contract = _contract()
    for gate in contract["selection"].values():
        if isinstance(gate, dict) and "minimum_events" in gate:
            gate["minimum_events"] = 1
    family = "crossasset_agreement_continuation_v1"
    event_times = {
        "train": "2020-06-01T12:00:00Z",
        "validation": "2022-06-01T12:00:00Z",
        "internal_test": "2023-06-01T12:00:00Z",
        "exam": "2024-06-01T12:00:00Z",
    }
    events = []
    for split, raw in event_times.items():
        timestamp = pd.Timestamp(raw)
        events.append(
            {
                "event_id": split,
                "family_id": family,
                "direction": "LONG",
                "split": split,
                "decision_time_utc": raw,
                "decision_timestamp_ms": int(timestamp.timestamp() * 1000),
            }
        )

    def losing_label(_xau: pd.DataFrame, event: dict, _contract: dict) -> dict:
        return {
            **census._label_identity({**event, "atr": 5.0}),
            "status": "RESOLVED",
            "exit_time_utc": event["decision_time_utc"],
            "stress_net_r": -1.0,
            "stress_net_pnl_usd": -5.0,
        }

    monkeypatch.setattr(census, "label_event", losing_label)
    decision_ms = [
        int(pd.Timestamp(raw).timestamp() * 1000) for raw in event_times.values()
    ]
    m15 = pd.DataFrame(
        {
            "decision_timestamp_ms": decision_ms,
            "decision_date_utc": [raw[:10] for raw in event_times.values()],
            "base_feature_available": [True] * 4,
            "inside_decision_session": [True] * 4,
            "joined_source_available": [True] * 4,
        }
    )
    xau = pd.DataFrame({"timestamp_ms": decision_ms})
    report, labels, _ = census.evaluate_chronologically(
        xau=xau,
        m15=m15,
        events=events,
        contract=contract,
        contract_file=CONTRACT_PATH,
        macro_report={"classification": "INTRADAY_MACRO_SOURCE_VALID"},
        broker_report={"classification": "BROKER_COST_CALIBRATION_VALID"},
    )
    assert {row["split"] for row in labels} == {"train"}
    assert (
        report["hypotheses"][f"{family}:LONG"]["validation"]["opened_for_decision"]
        is False
    )
