from __future__ import annotations

import sys
from datetime import datetime, timedelta
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
import build_a1_xau_r6_distribution_break_failed_reclaim_census as R  # noqa: E402


def bar(time: datetime, open_: float, high: float, low: float, close: float) -> R.Bar:
    return R.Bar(time, open_, high, low, close)


def test_wilder_atr_uses_seed_then_rma() -> None:
    start = datetime(2020, 1, 1)
    bars = [bar(start + timedelta(hours=i), 100, 101, 100, 100.5) for i in range(17)]
    atr = R.wilder_atr(bars)
    assert atr[13] is None
    assert atr[14] == pytest.approx(1.0)
    assert atr[16] == pytest.approx(1.0)


def test_bar_validation_rejects_duplicate_and_invalid_ohlc() -> None:
    now = datetime(2020, 1, 1)
    with pytest.raises(ValueError, match="timestamps"):
        R.validate_bars([bar(now, 1, 2, 1, 1.5), bar(now, 1, 2, 1, 1.5)])
    with pytest.raises(ValueError, match="range"):
        R.validate_bars([bar(now, 1, 1.1, 1.05, 1.2)])


def test_router_unknown_on_unavailable_history() -> None:
    now = datetime(2020, 1, 1)
    bars = [bar(now + timedelta(hours=i), 100, 101, 100, 100.5) for i in range(20)]
    assert R.classify_router(h1=bars, h4=bars, d1=bars, decision=now + timedelta(days=3)) == "UNKNOWN"


def fixture_market() -> tuple[list[R.Bar], list[R.Bar], list[R.Bar], list[R.Tick]]:
    start = datetime(2022, 1, 1)
    h4 = [bar(start + timedelta(hours=4 * i), 100, 100.6, 99.6, 100.2) for i in range(16)]
    impulse = [
        bar(start + timedelta(hours=4 * (2 + i)), 100 + 0.5 * i, 100.7 + 0.5 * i, 99.9 + 0.5 * i, 100.6 + 0.5 * i)
        for i in range(6)
    ]
    distribution = [
        bar(start + timedelta(hours=4 * (8 + i)), 103.5, 104.5, 102.5, 103.5)
        for i in range(6)
    ]
    h4[2:8], h4[8:14] = impulse, distribution
    h4[14] = bar(start + timedelta(hours=56), 103.0, 103.2, 102.1, 102.2)
    h4[15] = bar(start + timedelta(hours=60), 102.2, 102.8, 102.0, 102.4)
    h1 = [bar(start + timedelta(hours=i), 101, 101.4, 100.6, 101) for i in range(80)]
    h1[60] = bar(start + timedelta(hours=60), 102.4, 102.45, 102.1, 102.2)
    h1[61] = bar(start + timedelta(hours=61), 102.2, 102.4, 102.0, 102.1)
    d1 = [bar(start + timedelta(days=i), 100, 101, 99, 100.5) for i in range(2)]
    ticks = [R.Tick(start + timedelta(hours=61), 1000, 102.10, 102.11)]
    return h4, h1, d1, ticks


def test_exact_shift_detector_emits_one_raw_row(monkeypatch: pytest.MonkeyPatch) -> None:
    h4, h1, d1, ticks = fixture_market()
    monkeypatch.setattr(R, "wilder_atr", lambda bars, period=14: [1.0] * len(bars))
    monkeypatch.setattr(R, "classify_router", lambda **_: "CHOP")
    result = R.detect(
        h4=h4, h1=h1, d1=d1, ticks=ticks,
        contract=R.Contract(0.01, 2, 0.01, 1.0, 0.01, 0.01, 100, 0, 0),
    )
    assert len(result.rows) == 1
    row = result.rows[0]
    assert row["impulse_start_h4_time"].endswith("08:00:00")
    assert row["box_start_h4_time"].endswith("08:00:00")  # day 2, shift 7
    assert row["breakdown_h4_time"].endswith("08:00:00")   # day 3, shift 1
    assert row["decision_time"].endswith("13:00:00")
    assert row["availability_status"] == "RAW_OPPORTUNITY_AVAILABLE"
    assert result.funnel["RAW_OPPORTUNITY_AVAILABLE"] == 1


def test_first_reclaim_attempt_consumes_episode(monkeypatch: pytest.MonkeyPatch) -> None:
    h4, h1, d1, ticks = fixture_market()
    first = h1[60]
    h1[60] = bar(first.time, 102.2, 102.45, 102.1, 102.4)  # touches, but does not reject
    h1[61] = bar(h1[61].time, 102.4, 102.45, 102.0, 102.1)  # later rejection is unavailable
    monkeypatch.setattr(R, "wilder_atr", lambda bars, period=14: [1.0] * len(bars))
    monkeypatch.setattr(R, "classify_router", lambda **_: "CHOP")
    result = R.detect(h4=h4, h1=h1, d1=d1, ticks=ticks, contract=R.Contract(0.01, 2, 0.01, 1, 0.01, 0.01, 100, 0, 0))
    assert not result.rows
    assert result.funnel["FIRST_RECLAIM_NOT_REJECTED"] == 1
