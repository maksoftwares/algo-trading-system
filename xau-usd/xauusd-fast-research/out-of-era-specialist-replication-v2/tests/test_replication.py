from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "src" / "replication.py"
SPEC = importlib.util.spec_from_file_location("out_of_era_v2_replication_tests", MODULE_PATH)
if SPEC is None or SPEC.loader is None:
    raise ImportError(MODULE_PATH)
REPLICATION = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = REPLICATION
SPEC.loader.exec_module(REPLICATION)


def _trades(times: list[str], values: list[float]) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "entry_time": pd.to_datetime(times, utc=True),
            "direction": ["LONG"] * len(times),
            "stress_net_r": values,
        }
    )


def test_closed_drawdown_includes_initial_equity_peak() -> None:
    assert REPLICATION.closed_drawdown(pd.Series([-2.0, 3.0])) == 2.0


def test_holm_adjustment_uses_all_five_candidates() -> None:
    adjusted = REPLICATION.holm_adjust(
        {"a": 0.01, "b": 0.03, "c": 0.20, "d": 0.50, "e": 0.90}
    )
    assert np.isclose(adjusted["a"], 0.05)
    assert np.isclose(adjusted["b"], 0.12)
    assert np.isclose(adjusted["c"], 0.60)
    assert adjusted["d"] == 1.0
    assert adjusted["e"] == 1.0


def test_daily_significance_includes_zero_trade_days() -> None:
    days = pd.date_range("2020-01-01T00:00:00Z", periods=10, freq="1D")
    trades = _trades(["2020-01-01T10:00:00Z"], [1.0])
    values = REPLICATION.daily_values(trades, days)
    assert len(values) == 10
    assert np.isclose(values.sum(), 1.0)
    assert 0.0 < REPLICATION.one_sided_daily_pvalue(trades, days) < 0.5


def test_distinct_selection_rejects_correlated_compression_variant() -> None:
    economic = ["R1", "FOMC", "R1B", "COMPRESSION"]
    pairwise = []
    for first_index, first in enumerate(economic):
        for second in economic[first_index + 1 :]:
            pairwise.append(
                {
                    "first_candidate_id": first,
                    "second_candidate_id": second,
                    "independence_pass": not (first == "R1B" and second == "COMPRESSION"),
                }
            )
    selected = REPLICATION.select_distinct_survivors(
        economic,
        pairwise,
        ["R1", "FOMC", "R1B", "COMPRESSION"],
        {
            "R1": "UPTREND",
            "FOMC": "EVENT",
            "R1B": "COMPRESSION",
            "COMPRESSION": "COMPRESSION",
        },
    )
    assert selected == ["R1", "FOMC", "R1B"]


def test_normalized_tick_store_preserves_order_and_boundaries(tmp_path: Path) -> None:
    base = int(pd.Timestamp("2020-01-01T00:00:00Z").value // 1_000_000)
    path = (
        tmp_path
        / "normalized"
        / "XAUUSD"
        / "year=2020"
        / "month=01"
        / "ticks.parquet"
    )
    path.parent.mkdir(parents=True)
    pd.DataFrame(
        {
            "timestamp_ms": [base, base + 500, base + 1000],
            "bid": [100.0, 101.0, 102.0],
            "ask": [100.2, 101.2, 102.2],
        }
    ).to_parquet(path, index=False)
    store = REPLICATION.VerifiedNormalizedTickStore(tmp_path, "XAUUSD")
    ticks = list(store.ticks_between(base, base + 500))
    assert [tick.timestamp_ms for tick in ticks] == [base, base + 500]


def test_event_label_orders_stop_before_target_on_same_tick() -> None:
    ticks = [REPLICATION.Tick(1000, 100.0, 100.2)]
    hit = REPLICATION.EVENT.first_threshold_hit(
        ticks,
        "LONG",
        stop=100.0,
        target=100.0,
        minimum_timestamp_ms=1000,
        maximum_timestamp_ms=1000,
    )
    assert hit is not None
    assert hit[2] == "STOP"


def test_event_label_end_to_end_reaches_stop_with_millisecond_bars() -> None:
    start = pd.Timestamp("2020-01-02T00:00:00Z")
    m5 = pd.DataFrame(
        {
            "bar_start_utc": pd.Series([start]).dt.as_unit("ms"),
            "bar_end_utc": pd.Series([start + pd.Timedelta(minutes=5)]).dt.as_unit("ms"),
            "bid_open": [100.0],
            "bid_high": [103.0],
            "bid_low": [98.0],
            "bid_close": [100.0],
            "ask_open": [100.2],
            "ask_high": [103.2],
            "ask_low": [98.2],
            "ask_close": [100.2],
        }
    )
    decision_ms = int(start.value // 1_000_000)
    candidates = pd.DataFrame(
        {
            "candidate_id": ["candidate"],
            "policy_id": ["policy"],
            "event_id": ["event"],
            "event_type": ["FOMC"],
            "mode": ["IMPULSE"],
            "regime": ["CHOP"],
            "direction": ["LONG"],
            "feature_time_utc": [start],
            "raw_stop_distance": [1.0],
            "target_r": [2.0],
        }
    )

    class Store:
        values = [
            REPLICATION.Tick(decision_ms + 1, 100.0, 100.2),
            REPLICATION.Tick(decision_ms + 2, 99.0, 99.2),
        ]

        def ticks_between(self, lower: int, upper: int):
            return (
                tick for tick in self.values if lower <= tick.timestamp_ms <= upper
            )

    outcomes, audit = REPLICATION.label_event_candidates(
        candidates,
        m5,
        Store(),
        {"maximum_entry_delay_ms": 10000, "exit_tick_grace_ms": 10000},
        {
            "minimum_stop_distance_usd": 1.0,
            "maximum_stop_distance_usd": 10.0,
            "maximum_entry_spread_usd": 1.0,
            "maximum_entry_spread_r": 0.5,
            "maximum_hold_hours": 1,
            "ounces": 1.0,
            "ticket_cost_usd": 0.0,
            "holding_cost_per_24h_usd": 0.0,
            "stress_slippage_r": 0.0,
        },
    )
    assert len(outcomes) == 1
    assert outcomes.loc[0, "exit_reason"] == "STOP"
    assert audit["stop_outcomes"] == 1
    assert audit["max_hold_outcomes"] == 0


def test_regime_h4_uses_complete_buckets_and_sums_tick_count() -> None:
    starts = pd.date_range("2020-01-02T00:00:00Z", periods=49, freq="5min")
    m5 = pd.DataFrame(
        {
            "bar_start_utc": starts,
            "tick_count": [10] * len(starts),
        }
    )
    for side in ("bid", "ask", "mid"):
        for field in ("open", "high", "low", "close"):
            m5[f"{side}_{field}"] = 100.0
    h4 = REPLICATION.build_regime_h4(m5)
    assert len(h4) == 1
    assert h4.loc[0, "tick_count"] == 480
    assert h4.attrs["incomplete_buckets_dropped"] == 1
