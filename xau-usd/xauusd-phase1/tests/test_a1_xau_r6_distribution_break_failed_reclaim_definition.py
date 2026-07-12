from __future__ import annotations

import sys
import json
import hashlib
import dataclasses
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


MT5_ROUTER_FIXTURES = {
    "UPTREND": ("62a7b6f528c41beb4e56260b0967fa8da18950e2be45857b2903c4af92fe6aa5", 2.3327889183408757, 2.441938199210026, 80.0, 81.74603174603175, 597.575000000001, 592.3250850147854),
    "DOWNTREND": ("94e5055dde6ae69d6d8c2ac83f83aebc118595082c35b41e9a7c2281a34388c7", 2.3327889183408757, 2.441938199210026, 80.0, 81.74603174603175, 402.42499999999893, 407.67491498521537),
    "COMPRESSION": ("a06d6b92e7db4af7f0f95b4d069362b7d3cc7439b05acabade3279fa35ac380e", 1.1977067532874262, 1.2432328799007755, 1.6666666666666667, 0.3968253968253968, 499.98499999999996, 499.99399708520787),
    "CHOP": ("ef38a8e2032a3b860e864d09a760aa4d4c1701eea91485540783edc7d6439ef1", 1.1977067532874262, 2.1101371087934915, 45.0, 10.714285714285714, 503.472753853296, 501.513218700092),
}


def mt5_router_fixture(decision: datetime, count: int, spacing: timedelta, state: str, timeframe: str) -> list[R.Bar]:
    start = decision - spacing * (count - 1)
    sign = 1 if state == "UPTREND" else -1 if state == "DOWNTREND" else 0
    output = []
    for index in range(count):
        center = 500 + sign * 0.35 * index
        if sign == 0:
            center = 500 + (0.3 if index % 2 else -0.3)
        width = 6.0 if index % 11 == 0 else 2.0
        if state in {"COMPRESSION", "CHOP"} and index >= count - 30:
            width = 1.0
        if state == "CHOP" and timeframe == "d1" and count - 6 <= index <= count - 2:
            center = 500 + 4 * (index - (count - 6))
        open_ = center - 0.1 * sign
        close = center + 0.1 * sign if sign else center
        output.append(bar(start + spacing * index, open_, center + width / 2, center - width / 2, close))
    return output


@pytest.mark.parametrize("state", sorted(MT5_ROUTER_FIXTURES))
def test_hash_addressed_mt5_router_numerical_parity_without_monkeypatch(state: str) -> None:
    decision = datetime(2024, 1, 1)
    h1 = mt5_router_fixture(decision, 40, timedelta(hours=1), state, "h1")
    h4 = mt5_router_fixture(decision, 80, timedelta(hours=4), state, "h4")
    d1 = mt5_router_fixture(decision, 290, timedelta(days=1), state, "d1")
    payload = {
        timeframe: [(value.time.isoformat(), value.open, value.high, value.low, value.close) for value in bars]
        for timeframe, bars in (("h1", h1), ("h4", h4), ("d1", d1))
    }
    expected_hash, h1_atr, d1_atr, pct60, pct252, ema20, ema50 = MT5_ROUTER_FIXTURES[state]
    assert hashlib.sha256(json.dumps(payload, separators=(",", ":"), sort_keys=True).encode()).hexdigest() == expected_hash
    h1_index, d1_index = R._last_completed_index(h1, decision), R._last_completed_index(d1, decision)
    h1_values, d1_values = R.wilder_atr(h1), R.wilder_atr(d1)
    assert h1_values[h1_index] == pytest.approx(h1_atr)
    assert d1_values[d1_index] == pytest.approx(d1_atr)
    assert R.percentile_rank([value for value in d1_values[d1_index - 59 : d1_index + 1] if value], d1_values[d1_index]) == pytest.approx(pct60)
    assert R.percentile_rank([value for value in d1_values[d1_index - 251 : d1_index + 1] if value], d1_values[d1_index]) == pytest.approx(pct252)
    closes = [value.close for value in d1]
    assert R.ema(closes, 20)[d1_index] == pytest.approx(ema20)
    assert R.ema(closes, 50)[d1_index] == pytest.approx(ema50)
    assert R.classify_router(h1=h1, h4=h4, d1=d1, decision=decision) == state


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
    context = result.contexts[str(row["candidate_id"])]
    schema = json.loads((SCRIPTS.parent / "docs" / "A1_XAU_R6_OUTCOME_BLIND_CENSUS_SCHEMA_V1.json").read_text())
    monkeypatch.setattr(V, "classify_router", lambda **_: "CHOP")
    V.validate_row(dict(row), schema, context)
    V.validate_detection(result, schema)
    V.validate_funnel(result.funnel, result.rows, result.anchors, result.incidence)
    bad = dict(row)
    bad["breakdown_distance_atr"] = float(bad["breakdown_distance_atr"]) + 0.01
    with pytest.raises(ValueError, match="formula"):
        V.validate_row(bad, schema, context)
    bad = dict(row)
    bad["candidate_id"] = "not-a-hash"
    with pytest.raises(Exception, match="pattern"):
        V.validate_row(bad, schema, context)
    closed_entry = dataclasses.replace(context.entry_tick, session_open=False)
    closed_context = dataclasses.replace(context, entry_tick=closed_entry, causal_ticks=(closed_entry,))
    with pytest.raises(ValueError, match="predicate|eligible"):
        V.validate_row(dict(row), schema, closed_context)
    monkeypatch.setattr(V, "classify_router", lambda **_: "DOWNTREND")
    with pytest.raises(ValueError, match="router"):
        V.validate_row(dict(row), schema, context)


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


def test_complete_six_h1_decision_horizon_must_remain_inside_locked_interval(monkeypatch: pytest.MonkeyPatch) -> None:
    h4, h1, d1, ticks = fixture_market()
    delta = datetime(2026, 6, 30, 16) - h4[14].time
    h4 = [dataclasses.replace(value, time=value.time + delta) for value in h4]
    h1 = [dataclasses.replace(value, time=value.time + delta) for value in h1]
    d1 = [dataclasses.replace(value, time=value.time + delta) for value in d1]
    ticks = [
        dataclasses.replace(
            value, time=value.time + delta,
            source_h1_bar_time=value.source_h1_bar_time + delta if value.source_h1_bar_time else None,
        )
        for value in ticks
    ]
    monkeypatch.setattr(R, "wilder_atr", lambda bars, period=14: [1.0] * len(bars))
    monkeypatch.setattr(R, "classify_router", lambda **_: "CHOP")
    result = R.detect(h4=h4, h1=h1, d1=d1, ticks=ticks, contract=contract())
    assert not result.rows
    assert result.funnel["DATA_UNAVAILABLE"] == 1


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
    prefix = R.detect(h4=h4, h1=h1, d1=d1, ticks=owned, contract=contract())
    assert len(prefix.rows) == 1
    for late_tick in (
        R.Tick(decision, 1002, 102.10, 102.11),
        R.Tick(decision, 1002, 102.10, 102.11, source_h1_bar_time=h1[60].time),
    ):
        extended = R.detect(h4=h4, h1=h1, d1=d1, ticks=owned + [late_tick], contract=contract())
        assert extended.rows == prefix.rows
        assert extended.anchors == prefix.anchors
    closed_first = [
        R.Tick(decision, 1000, 102.10, 102.11, session_open=False, source_h1_bar_time=decision),
        R.Tick(decision, 1001, 102.10, 102.11, source_h1_bar_time=decision),
    ]
    assert R.detect(h4=h4, h1=h1, d1=d1, ticks=closed_first, contract=contract()).funnel["ENTRY_TICK_UNAVAILABLE"] == 1
    # Nothing after the consumed entry may retroactively affect the signal.
    assert len(R.detect(h4=h4, h1=h1, d1=d1, ticks=list(reversed(owned)), contract=contract()).rows) == 1
    invalid_before_entry = [
        R.Tick(decision - timedelta(seconds=2), 1001, 102.10, 102.11, source_h1_bar_time=h1[60].time),
        R.Tick(decision - timedelta(seconds=1), 1000, 102.10, 102.11, source_h1_bar_time=h1[60].time),
        owned[1],
    ]
    with pytest.raises(ValueError, match="monotonic"):
        R.detect(h4=h4, h1=h1, d1=d1, ticks=invalid_before_entry, contract=contract())


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
