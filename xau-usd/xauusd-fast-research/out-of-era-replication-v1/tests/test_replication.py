from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from replication import (  # noqa: E402
    _official_nfp_calendar,
    holm_adjust,
    load_side_specific_m5,
    one_sided_daily_pvalue,
    run_nfp,
    simulate_gld_plan,
)


def _m5() -> pd.DataFrame:
    starts = pd.date_range("2010-01-04", periods=3, freq="5min", tz="UTC")
    return pd.DataFrame(
        {
            "bar_start_utc": starts,
            "bar_end_utc": starts + pd.Timedelta(minutes=5),
            "bid_open": [100.0, 100.0, 100.0],
            "bid_high": [106.0, 101.0, 101.0],
            "bid_low": [94.0, 99.0, 99.0],
            "bid_close": [100.0, 100.0, 100.0],
            "ask_open": [100.2, 100.2, 100.2],
            "ask_high": [106.2, 101.2, 101.2],
            "ask_low": [94.2, 99.2, 99.2],
            "ask_close": [100.2, 100.2, 100.2],
        }
    )


def test_gld_same_bar_collision_is_stop_first() -> None:
    execution = {
        "maximum_entry_gap_minutes": 10,
        "minimum_stop_distance_usd": 3.5,
        "maximum_entry_spread_usd": 0.75,
        "maximum_entry_spread_r": 0.15,
        "gld_maximum_hold_m5_bars": 3,
        "ounces_at_0_01_lot": 1.0,
        "ticket_cost_usd": 0.3,
        "holding_cost_per_24h_usd": 0.35,
        "stress_slippage_r": 0.05,
    }
    result = simulate_gld_plan(
        _m5(),
        pd.Timestamp("2010-01-04T00:00:00Z"),
        "LONG",
        95.0,
        105.0,
        execution,
    )
    assert result is not None
    assert result["exit_reason"] == "AMBIGUOUS_M5_STOP_FIRST"
    assert result["exit_price"] == 95.0


def test_holm_adjustment_is_monotone_in_rank() -> None:
    adjusted = holm_adjust({"a": 0.01, "b": 0.02, "c": 0.50})
    assert adjusted == {"a": 0.03, "b": 0.04, "c": 0.5}


def test_daily_pvalue_uses_daily_aggregation() -> None:
    trades = pd.DataFrame(
        {
            "entry_time": pd.to_datetime(
                ["2020-01-01", "2020-01-01 12:00", "2020-01-02"],
                format="mixed",
                utc=True,
            ),
            "stress_net_r": [1.0, -0.5, 1.0],
        }
    )
    assert np.isfinite(one_sided_daily_pvalue(trades))


def test_side_specific_loader_aligns_and_closes_m5_bars(tmp_path: Path) -> None:
    timestamps = pd.date_range("2010-01-04", periods=15, freq="5min", tz="UTC")
    for side, offset in (("bid", 0.0), ("ask", 0.2), ("mid", 0.1)):
        path = (
            tmp_path
            / "bars"
            / "XAUUSD"
            / side
            / "M5"
            / "year=2010"
            / "month=01"
            / "bars.parquet"
        )
        path.parent.mkdir(parents=True)
        pd.DataFrame(
            {
                "timestamp_utc": timestamps,
                "timestamp_ms": timestamps.astype("int64") // 1_000_000,
                "tick_count": 10,
                "open": 100.0 + offset,
                "high": 101.0 + offset,
                "low": 99.0 + offset,
                "close": 100.5 + offset,
            }
        ).to_parquet(path, index=False)
    frame = load_side_specific_m5(tmp_path, ["2010-01"])
    assert len(frame) == 15
    assert frame.loc[0, "timestamp_utc"] == timestamps[0] + pd.Timedelta(minutes=5)
    assert np.isclose(
        frame.loc[0, "ask_open"] - frame.loc[0, "bid_open"], 0.2
    )
    assert np.isfinite(frame.loc[13, "atr"])


def test_official_nfp_calendar_applies_new_york_dst(tmp_path: Path) -> None:
    path = tmp_path / "bls.json"
    path.write_text(
        '[{"date":"2010-01-08","primaryUrl":"https://bls.test/a"},'
        '{"date":"2010-06-04","primaryUrl":"https://bls.test/b"}]',
        encoding="utf-8",
    )
    calendar = _official_nfp_calendar(path)
    assert calendar.loc[0, "event_time_utc"].hour == 13
    assert calendar.loc[1, "event_time_utc"].hour == 12


def test_nfp_adapter_uses_sealed_tick_store_root(
    tmp_path: Path, monkeypatch
) -> None:
    calendar_path = tmp_path / "bls.json"
    calendar_path.write_text(
        '[{"date":"2010-01-08","primaryUrl":"https://bls.test/a"}]',
        encoding="utf-8",
    )
    captured: dict[str, Path] = {}

    def candidate(event, policy, m5):
        return {
            "candidate_id": "event-1",
            "policy_id": policy["policy_id"],
            "feature_time_utc": event.event_time_utc,
        }

    def label(frame, m5, tick_root, symbol, source, execution):
        captured["tick_root"] = tick_root
        return (
            pd.DataFrame(
                {
                    "candidate_id": ["event-1"],
                    "entry_time": [pd.Timestamp("2010-01-08T13:45:00Z")],
                    "exit_time": [pd.Timestamp("2010-01-08T14:00:00Z")],
                    "direction": ["SHORT"],
                    "stress_net_r": [0.5],
                }
            ),
            {"candidate_rows": 1},
        )

    import replication

    monkeypatch.setattr(replication.EVENT, "candidate_for_event_policy", candidate)
    monkeypatch.setattr(replication.EVENT, "label_candidates", label)
    sealed_root = tmp_path / "sealed-replay"
    outcomes, events, _ = run_nfp(
        pd.DataFrame(),
        sealed_root,
        calendar_path,
        {
            "policies": [{"policy_id": "EVENT_NFP_FADE_RR2"}],
            "source": {},
            "execution": {},
        },
    )
    assert events == 1
    assert captured["tick_root"] == sealed_root
    assert outcomes.loc[0, "candidate_id"] == "NFP_FADE_RR2_EXACT"
    assert outcomes.loc[0, "source_candidate_id"] == "event-1"
