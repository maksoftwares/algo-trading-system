from __future__ import annotations

import copy
import json
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path
from types import SimpleNamespace

import pandas as pd
import pytest


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ml.a3_meta_v1.dukascopy_r1_r2_portability import (  # noqa: E402
    R1,
    R2,
    aggregate_h1_bidask_bars,
    apply_specialist_controls,
    indicator_frame,
    r1_signal,
    r2_signal,
    trend_stack,
    wilder_atr,
)


def _timestamp(value: datetime) -> int:
    return int(value.timestamp() * 1000)


def _h1(start: datetime, count: int, slope: float = 0.1) -> list[dict]:
    rows = []
    for index in range(count):
        close = 1500.0 + slope * index
        rows.append(
            {
                "timestamp_ms": _timestamp(start + timedelta(hours=index)),
                "bid_open": close - 0.05,
                "bid_high": close + 0.2,
                "bid_low": close - 0.2,
                "bid_close": close,
                "ask_open": close + 0.15,
                "ask_high": close + 0.4,
                "ask_low": close,
                "ask_close": close + 0.2,
                "tick_count": 10,
            }
        )
    return rows


def _contract() -> dict:
    return json.loads(
        (ROOT / "config" / "ml" / "a3_ml_r1_r2_dukascopy_portability_v1.json").read_text(
            encoding="utf-8"
        )
    )


def test_server_day_aggregation_starts_at_20_utc() -> None:
    rows = _h1(datetime(2020, 1, 1, 19, tzinfo=UTC), 4)
    d1 = aggregate_h1_bidask_bars(rows, width_hours=24, utc_offset_hours=4)
    assert [row["timestamp_ms"] for row in d1] == [
        _timestamp(datetime(2019, 12, 31, 20, tzinfo=UTC)),
        _timestamp(datetime(2020, 1, 1, 20, tzinfo=UTC)),
    ]
    assert d1[1]["tick_count"] == 30


def test_wilder_atr_uses_sma_seed_then_recursive_smoothing() -> None:
    frame = pd.DataFrame(_h1(datetime(2020, 1, 1, tzinfo=UTC), 20))
    atr = wilder_atr(frame, 14)
    assert pd.isna(atr.iloc[12])
    assert atr.iloc[13] == pytest.approx(0.4)
    assert atr.iloc[19] == pytest.approx(0.4)


def test_future_bar_cannot_change_prior_indicator_values() -> None:
    rows = _h1(datetime(2020, 1, 1, tzinfo=UTC), 100)
    before = indicator_frame(rows)
    changed = copy.deepcopy(rows)
    changed.append(
        {
            **rows[-1],
            "timestamp_ms": rows[-1]["timestamp_ms"] + 60 * 60_000,
            "bid_open": 9999.0,
            "bid_high": 10001.0,
            "bid_low": 9998.0,
            "bid_close": 10000.0,
        }
    )
    after = indicator_frame(changed)
    pd.testing.assert_series_equal(before["ema20"], after.iloc[:-1]["ema20"], check_names=False)
    pd.testing.assert_series_equal(before["atr14"], after.iloc[:-1]["atr14"], check_names=False)


def test_r1_signal_uses_completed_d1_box_and_h4_expansion() -> None:
    d1 = indicator_frame(_h1(datetime(2019, 1, 1, tzinfo=UTC), 300, slope=0.02))
    h4 = indicator_frame(_h1(datetime(2020, 1, 1, tzinfo=UTC), 40, slope=0.02))
    index = 30
    d1_index = 290
    box_high = float(d1.iloc[d1_index - 1 : d1_index + 1]["bid_high"].max())
    h4.loc[index, ["bid_open", "bid_low", "bid_high", "bid_close"]] = [
        box_high - 1.0,
        box_high - 1.2,
        box_high + 1.2,
        box_high + 1.0,
    ]
    h4.loc[index, "atr14"] = 1.0
    d1.loc[d1_index, "atr_pct_252"] = 50.0
    d1.loc[d1_index, "median_range20"] = 10.0
    signal = r1_signal(h4, index, d1, d1_index)
    assert signal is not None
    assert signal["stop_distance"] >= 3.5


def test_r2_signal_requires_bearish_rejection_touch() -> None:
    h1 = indicator_frame(_h1(datetime(2020, 1, 1, tzinfo=UTC), 100, slope=-0.1))
    index = 90
    fast = float(h1.loc[index, "ema20"])
    h1.loc[index, ["bid_open", "bid_high", "bid_low", "bid_close"]] = [
        fast - 0.1,
        fast + 0.1,
        fast - 1.1,
        fast - 1.0,
    ]
    h1.loc[index, "atr14"] = 0.8
    signal = r2_signal(h1, index)
    assert signal is not None
    assert signal["stop_distance"] >= 3.5


def test_specialist_controls_apply_spread_and_open_position_caps() -> None:
    contract = _contract()
    contract["specialist_controls"][R2]["maximum_open_positions"] = 1
    start = datetime(2020, 1, 1, tzinfo=UTC)
    labels = [
        SimpleNamespace(
            candidate_id="a",
            family_id=R2,
            status="RESOLVED",
            entry_time_utc=start.isoformat().replace("+00:00", "Z"),
            exit_time_utc=(start + timedelta(hours=2)).isoformat().replace("+00:00", "Z"),
            entry_spread=0.2,
        ),
        SimpleNamespace(
            candidate_id="b",
            family_id=R2,
            status="RESOLVED",
            entry_time_utc=(start + timedelta(hours=1)).isoformat().replace("+00:00", "Z"),
            exit_time_utc=(start + timedelta(hours=3)).isoformat().replace("+00:00", "Z"),
            entry_spread=0.2,
        ),
        SimpleNamespace(
            candidate_id="c",
            family_id=R1,
            status="RESOLVED",
            entry_time_utc=(start + timedelta(hours=1)).isoformat().replace("+00:00", "Z"),
            exit_time_utc=(start + timedelta(hours=3)).isoformat().replace("+00:00", "Z"),
            entry_spread=1.0,
        ),
    ]
    candidates = {
        key: SimpleNamespace(candidate_id=key, family_id=family, stop_distance=4.0)
        for key, family in (("a", R2), ("b", R2), ("c", R1))
    }
    selected, reasons = apply_specialist_controls(labels, candidates, contract)
    assert [row.candidate_id for row in selected] == ["a"]
    assert reasons["max_open_positions_reached"] == 1
    assert reasons["spread_too_high"] == 1


def test_trend_stack_is_directional() -> None:
    up = {"bid_close": 12, "ema20": 11, "ema50": 10, "ema20_lag5": 10, "ema50_lag5": 9}
    assert trend_stack(up, True)
    assert not trend_stack(up, False)
