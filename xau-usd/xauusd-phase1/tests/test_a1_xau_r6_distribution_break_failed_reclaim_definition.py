from __future__ import annotations

import sys
import json
from datetime import datetime, timedelta
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
import build_a1_xau_r6_distribution_break_failed_reclaim_census as R  # noqa: E402
import validate_a1_xau_r6_outcome_blind_census as V  # noqa: E402


def bar(time: datetime, open_: float, high: float, low: float, close: float) -> R.Bar:
    return R.Bar(time, open_, high, low, close)


def contract(**overrides: object) -> R.Contract:
    values = dict(
        account_currency="USD", account_leverage=50, margin_mode=2,
        server="Capital.ComMena-Demo", symbol="XAUUSD", point=0.01, digits=2,
        tick_size=0.01, tick_value=1.0, tick_value_loss=1.0,
        volume_min=0.01, volume_step=0.01, volume_max=1000.0,
        contract_size=100.0, stops_level=0, freeze_level=0,
    )
    values.update(overrides)
    return R.Contract(**values)


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


def native_bars(decision: datetime, count: int, spacing: timedelta) -> list[R.Bar]:
    start = decision - spacing * (count - 1)
    return [bar(start + spacing * i, 100, 102, 100, 101) for i in range(count)]


def router_market() -> tuple[datetime, list[R.Bar], list[R.Bar], list[R.Bar]]:
    decision = datetime(2024, 1, 1)
    return (
        decision,
        native_bars(decision, 30, timedelta(hours=1)),
        native_bars(decision, 70, timedelta(hours=4)),
        native_bars(decision, 277, timedelta(days=1)),
    )


def test_router_exact_availability_boundary_and_all_states(monkeypatch: pytest.MonkeyPatch) -> None:
    decision, h1, h4, d1 = router_market()
    monkeypatch.setattr(R, "wilder_atr", lambda bars, period=14: [1.0] * len(bars))
    monkeypatch.setattr(R, "percentile_rank", lambda values, current: 50.0)
    monkeypatch.setattr(R, "_trend_stack", lambda bars, index, up: False)
    assert R.classify_router(h1=h1, h4=h4, d1=d1[:-1], decision=decision) == "UNKNOWN"
    assert R.classify_router(h1=h1, h4=h4, d1=d1, decision=decision) == "CHOP"
    h1[-2] = bar(h1[-2].time, 100, 104, 100, 101)
    assert R.classify_router(h1=h1, h4=h4, d1=d1, decision=decision) == "SHOCK"
    h1[-2] = bar(h1[-2].time, 100, 102, 100, 101)
    monkeypatch.setattr(R, "_trend_stack", lambda bars, index, up: up)
    assert R.classify_router(h1=h1, h4=h4, d1=d1, decision=decision) == "UPTREND"
    monkeypatch.setattr(R, "_trend_stack", lambda bars, index, up: not up)
    assert R.classify_router(h1=h1, h4=h4, d1=d1, decision=decision) == "DOWNTREND"


def test_router_compression_uses_five_day_box_width_not_mean_daily_range(monkeypatch: pytest.MonkeyPatch) -> None:
    decision, h1, h4, d1 = router_market()
    monkeypatch.setattr(R, "wilder_atr", lambda bars, period=14: [1.0] * len(bars))
    monkeypatch.setattr(R, "percentile_rank", lambda values, current: 0.0)
    monkeypatch.setattr(R, "_trend_stack", lambda bars, index, up: False)
    for offset, index in enumerate(range(len(d1) - 6, len(d1) - 1)):
        low = 100 + 25 * offset
        d1[index] = bar(d1[index].time, low, low + 2, low, low + 1)
    assert R.classify_router(h1=h1, h4=h4, d1=d1, decision=decision) == "CHOP"
    for index in range(len(d1) - 6, len(d1) - 1):
        d1[index] = bar(d1[index].time, 100, 102, 100, 101)
    assert R.classify_router(h1=h1, h4=h4, d1=d1, decision=decision) == "COMPRESSION"


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
    ticks = [R.Tick(start + timedelta(hours=61), 1000, 102.10, 102.11, source_h1_bar_time=start + timedelta(hours=61))]
    return h4, h1, d1, ticks


def test_exact_shift_detector_emits_one_raw_row(monkeypatch: pytest.MonkeyPatch) -> None:
    h4, h1, d1, ticks = fixture_market()
    monkeypatch.setattr(R, "wilder_atr", lambda bars, period=14: [1.0] * len(bars))
    monkeypatch.setattr(R, "classify_router", lambda **_: "CHOP")
    result = R.detect(
        h4=h4, h1=h1, d1=d1, ticks=ticks,
        contract=contract(),
    )
    assert len(result.rows) == 1
    row = result.rows[0]
    assert row["impulse_start_h4_time"].endswith("08:00:00")
    assert row["box_start_h4_time"].endswith("08:00:00")  # day 2, shift 7
    assert row["breakdown_h4_time"].endswith("08:00:00")   # day 3, shift 1
    assert row["decision_time"].endswith("13:00:00")
    assert row["availability_status"] == "RAW_OPPORTUNITY_AVAILABLE"
    assert result.funnel["RAW_OPPORTUNITY_AVAILABLE"] == 1
    context = R.RowContext(
        tuple(h4[2:8]), tuple(h4[8:14]), h4[14], h1[60], h1[61].time,
        ticks[0], contract(), 1.0, 1.0, 1.0,
    )
    schema = json.loads((SCRIPTS.parent / "docs" / "A1_XAU_R6_OUTCOME_BLIND_CENSUS_SCHEMA_V1.json").read_text())
    V.validate_row(dict(row), schema, context)
    V.validate_funnel(result.funnel, result.rows, result.anchors, result.incidence)
    bad = dict(row)
    bad["breakdown_distance_atr"] = float(bad["breakdown_distance_atr"]) + 0.01
    with pytest.raises(ValueError, match="formula"):
        V.validate_row(bad, schema, context)
    bad = dict(row)
    bad["candidate_id"] = "not-a-hash"
    with pytest.raises(Exception, match="pattern"):
        V.validate_row(bad, schema, context)


def test_first_reclaim_attempt_consumes_episode(monkeypatch: pytest.MonkeyPatch) -> None:
    h4, h1, d1, ticks = fixture_market()
    first = h1[60]
    h1[60] = bar(first.time, 102.2, 102.45, 102.1, 102.4)  # touches, but does not reject
    h1[61] = bar(h1[61].time, 102.4, 102.45, 102.0, 102.1)  # later rejection is unavailable
    monkeypatch.setattr(R, "wilder_atr", lambda bars, period=14: [1.0] * len(bars))
    monkeypatch.setattr(R, "classify_router", lambda **_: "CHOP")
    result = R.detect(h4=h4, h1=h1, d1=d1, ticks=ticks, contract=contract())
    assert not result.rows
    assert result.funnel["FIRST_RECLAIM_NOT_REJECTED"] == 1


def test_incomplete_horizon_and_unavailable_reclaim_atr_fail_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    h4, h1, d1, ticks = fixture_market()
    monkeypatch.setattr(R, "classify_router", lambda **_: "CHOP")
    monkeypatch.setattr(R, "wilder_atr", lambda bars, period=14: [1.0] * len(bars))
    incomplete = R.detect(h4=h4, h1=h1[:64], d1=d1, ticks=ticks, contract=contract())
    assert incomplete.funnel["DATA_UNAVAILABLE"] == 1
    assert incomplete.funnel["NO_RECLAIM_WITHIN_SIX_H1"] == 0

    def atr_with_missing(bars: list[R.Bar], period: int = 14) -> list[float | None]:
        values: list[float | None] = [1.0] * len(bars)
        if bars is h1:
            values[60] = None
        return values

    monkeypatch.setattr(R, "wilder_atr", atr_with_missing)
    missing = R.detect(h4=h4, h1=h1, d1=d1, ticks=ticks, contract=contract())
    assert missing.funnel["DATA_UNAVAILABLE"] == 1
    assert not missing.rows


def test_same_second_tick_ownership_and_monotonic_source_are_enforced(monkeypatch: pytest.MonkeyPatch) -> None:
    h4, h1, d1, ticks = fixture_market()
    monkeypatch.setattr(R, "wilder_atr", lambda bars, period=14: [1.0] * len(bars))
    monkeypatch.setattr(R, "classify_router", lambda **_: "CHOP")
    decision = h1[61].time
    ambiguous = [R.Tick(decision, 1000, 102.10, 102.11)]
    result = R.detect(h4=h4, h1=h1, d1=d1, ticks=ambiguous, contract=contract())
    assert result.funnel["DATA_UNAVAILABLE"] == 1
    owned = [
        R.Tick(decision, 1000, 102.10, 102.11, source_h1_bar_time=h1[60].time),
        R.Tick(decision, 1001, 102.10, 102.11, source_h1_bar_time=decision),
    ]
    assert len(R.detect(h4=h4, h1=h1, d1=d1, ticks=owned, contract=contract()).rows) == 1
    closed_first = [
        R.Tick(decision, 1000, 102.10, 102.11, session_open=False, source_h1_bar_time=decision),
        R.Tick(decision, 1001, 102.10, 102.11, source_h1_bar_time=decision),
    ]
    assert R.detect(h4=h4, h1=h1, d1=d1, ticks=closed_first, contract=contract()).funnel["ENTRY_TICK_UNAVAILABLE"] == 1
    with pytest.raises(ValueError, match="monotonic"):
        R.detect(h4=h4, h1=h1, d1=d1, ticks=list(reversed(owned)), contract=contract())


def test_native_weekend_gap_and_fifteen_minute_entry_expiry(monkeypatch: pytest.MonkeyPatch) -> None:
    h4, h1, d1, _ = fixture_market()
    for index in range(61, len(h1)):
        source = h1[index]
        h1[index] = bar(source.time + timedelta(days=2), source.open, source.high, source.low, source.close)
    decision = h1[61].time
    monkeypatch.setattr(R, "wilder_atr", lambda bars, period=14: [1.0] * len(bars))
    monkeypatch.setattr(R, "classify_router", lambda **_: "CHOP")
    at_expiry = [R.Tick(decision + timedelta(minutes=15), 1000, 102.10, 102.11, source_h1_bar_time=decision)]
    result = R.detect(h4=h4, h1=h1, d1=d1, ticks=at_expiry, contract=contract())
    assert result.rows[0]["decision_time"] == R.broker_time(decision)
    too_late = [R.Tick(decision + timedelta(minutes=15, seconds=1), 1000, 102.10, 102.11, source_h1_bar_time=decision)]
    assert R.detect(h4=h4, h1=h1, d1=d1, ticks=too_late, contract=contract()).funnel["ENTRY_TICK_UNAVAILABLE"] == 1


def test_suppression_releases_on_twelfth_completed_h4_and_reuses_release_bar(monkeypatch: pytest.MonkeyPatch) -> None:
    h4, h1, d1, ticks = fixture_market()
    for index in range(16, 28):
        h4.append(bar(h4[-1].time + timedelta(hours=4), 101, 101.5, 100.5, 101))
    monkeypatch.setattr(R, "wilder_atr", lambda bars, period=14: [1.0] * len(bars))
    monkeypatch.setattr(R, "classify_router", lambda **_: "CHOP")
    result = R.detect(h4=h4, h1=h1, d1=d1, ticks=ticks, contract=contract())
    assert result.funnel["SUPPRESSION_ACTIVE"] == 11
    assert next(anchor for anchor in result.anchors if anchor.anchor_time == h4[26].time).status != "SUPPRESSION_ACTIVE"


def test_suppression_releases_on_box_mid_and_reuses_release_bar(monkeypatch: pytest.MonkeyPatch) -> None:
    h4, h1, d1, ticks = fixture_market()
    h4[15] = bar(h4[15].time, 103.4, 104.0, 103.3, 103.6)
    h4.append(bar(h4[-1].time + timedelta(hours=4), 103.6, 103.8, 103.2, 103.5))
    monkeypatch.setattr(R, "wilder_atr", lambda bars, period=14: [1.0] * len(bars))
    monkeypatch.setattr(R, "classify_router", lambda **_: "CHOP")
    result = R.detect(h4=h4, h1=h1, d1=d1, ticks=ticks, contract=contract())
    assert result.funnel["SUPPRESSION_ACTIVE"] == 0
    assert next(anchor for anchor in result.anchors if anchor.anchor_time == h4[15].time).status != "SUPPRESSION_ACTIVE"


def test_actual_detector_and_terminal_funnel_are_prefix_invariant(monkeypatch: pytest.MonkeyPatch) -> None:
    h4, h1, d1, ticks = fixture_market()
    extended_h4 = list(h4)
    extended_h1 = list(h1)
    for _ in range(6):
        extended_h4.append(bar(extended_h4[-1].time + timedelta(hours=4), 101, 101.5, 100.5, 101))
    for _ in range(12):
        extended_h1.append(bar(extended_h1[-1].time + timedelta(hours=1), 101, 101.4, 100.6, 101))
    monkeypatch.setattr(R, "wilder_atr", lambda bars, period=14: [1.0] * len(bars))
    monkeypatch.setattr(R, "classify_router", lambda **_: "CHOP")
    base = dict(h4=h4, h1=h1, d1=d1, ticks=ticks, contract=contract())
    extended = dict(h4=extended_h4, h1=extended_h1, d1=d1, ticks=ticks, contract=contract())
    V.validate_detector_prefix_invariance(R.detect, base, extended, prefix_end=ticks[0].time)
