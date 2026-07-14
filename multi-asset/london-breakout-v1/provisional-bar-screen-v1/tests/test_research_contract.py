from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from src.research_contract import (
    breakout, classify, combined_gates, directional_bias, exit_deadline, final_completed_h1,
    first_signal, in_overnight, instrument_gates, london_time, nearest_rank_p95,
    next_exact_bar, reconstruct, require_same_day_exit, resolve_bar, spread_price,
)


UTC = timezone.utc


def dt(text: str) -> datetime:
    return datetime.fromisoformat(text).replace(tzinfo=UTC)


def bar(bid=(100.0, 101.0, 99.0, 100.0), ask=(100.2, 101.2, 99.2, 100.2)) -> dict:
    return {"bid": bid, "ask": ask}


def test_01_london_spring_dst_mapping() -> None:
    assert london_time(dt("2025-03-30T01:00:00")).hour == 2


def test_02_london_autumn_dst_mapping() -> None:
    assert london_time(dt("2025-10-26T00:30:00")).hour == london_time(dt("2025-10-26T01:30:00")).hour == 1


def test_03_overnight_excludes_0800() -> None:
    assert in_overnight(dt("2025-01-02T07:59:00")) and not in_overnight(dt("2025-01-02T08:00:00"))


def test_04_h1_bias_final_completed_before_0800() -> None:
    cutoff = dt("2025-01-02T08:00:00")
    bars = [{"end": cutoff - timedelta(hours=1), "id": 1}, {"end": cutoff, "id": 2}, {"end": cutoff + timedelta(hours=1), "id": 3}]
    assert final_completed_h1(bars, cutoff)["id"] == 2


def test_05_future_h1_mutation_cannot_change_selection() -> None:
    cutoff = dt("2025-01-02T08:00:00")
    base = [{"end": cutoff, "id": "frozen"}]
    assert final_completed_h1(base + [{"end": cutoff + timedelta(hours=1), "id": "future", "close": 999}], cutoff)["id"] == "frozen"


def test_06_bias_exact_mirror() -> None:
    assert directional_bias(102, 101, 100, 10) == "LONG"
    assert directional_bias(98, 99, 100, 10) == "SHORT"


def test_07_breakout_exact_mirror() -> None:
    assert breakout("LONG", 100, 102, 100, 102, 100.9, 10)
    assert breakout("SHORT", 100, 100, 98, 98, 99.1, 10)


def test_08_first_qualifying_signal_only() -> None:
    events = [{"time": dt("2025-01-02T09:00:00"), "qualifies": True}, {"time": dt("2025-01-02T08:30:00"), "qualifies": True}]
    assert first_signal(events)["time"].hour == 8


def test_09_one_trade_per_instrument_date() -> None:
    events = [{"time": dt("2025-01-02T08:30:00"), "qualifies": True}, {"time": dt("2025-01-02T09:00:00"), "qualifies": True}]
    assert sum(event is first_signal(events) for event in events) == 1


def test_10_bid_reconstruction() -> None:
    prices = reconstruct((1, 2, 0.5, 1.5), 0.1, "BID")
    assert prices["bid"][0] == 1 and prices["ask"][0] == 1.1


def test_11_mid_reconstruction() -> None:
    prices = reconstruct((1, 2, 0.5, 1.5), 0.2, "MID")
    assert prices["bid"][0] == 0.9 and prices["ask"][0] == 1.1


def test_12_unknown_quote_basis_fails_closed() -> None:
    with pytest.raises(ValueError, match="quote basis"):
        reconstruct((1, 2, 0.5, 1.5), 0.1, "UNKNOWN")


def test_13_spread_point_to_price_conversion() -> None:
    assert spread_price(13, 0.001, 3) == pytest.approx(0.013)


def test_14_negative_or_missing_spread_fails() -> None:
    for value in (-1, float("nan")):
        with pytest.raises(ValueError):
            spread_price(value, 0.01, 2)


def test_15_entry_next_exact_m5_open() -> None:
    expected = dt("2025-01-02T08:15:00")
    assert next_exact_bar([{"time": expected, "open": 1}], expected)["open"] == 1


def test_16_missing_next_m5_rejects() -> None:
    with pytest.raises(ValueError, match="MISSING_NEXT_M5"):
        next_exact_bar([], dt("2025-01-02T08:15:00"))


def test_17_long_stop_gap_uses_worse_bid_open() -> None:
    assert resolve_bar("LONG", bar(bid=(98, 101, 97, 99)), 99, 104, 100).price == 98


def test_18_short_stop_gap_uses_worse_ask_open() -> None:
    assert resolve_bar("SHORT", bar(ask=(102, 103, 99, 101)), 101, 96, 100).price == 102


def test_19_favorable_target_gap_fills_at_target() -> None:
    assert resolve_bar("LONG", bar(bid=(105, 106, 104, 105)), 98, 104, 100).price == 104


def test_20_same_m5_stop_target_is_stop_first() -> None:
    result = resolve_bar("LONG", bar(bid=(100, 105, 97, 102)), 98, 104, 100)
    assert result.reason == "AMBIGUOUS_M5_STOP_FIRST" and result.price == 98


def test_21_mfe_mae_end_at_selected_exit() -> None:
    result = resolve_bar("LONG", bar(bid=(100, 500, 97, 400)), 98, 104, 100)
    assert result.mfe == 0 and result.mae == -2


def test_22_eight_hour_hold_uses_elapsed_time() -> None:
    entry = dt("2025-01-02T05:00:00")
    assert exit_deadline(entry) == entry + timedelta(hours=8)


def test_23_forced_1600_london_exit() -> None:
    entry = dt("2025-07-02T10:00:00")  # 11:00 London
    assert london_time(exit_deadline(entry)).hour == 16


def test_24_missing_same_day_exit_invalidates() -> None:
    with pytest.raises(ValueError, match="MISSING_SAME_DAY"):
        require_same_day_exit(dt("2025-01-02T10:00:00"), None)


def test_25_no_overnight_carry() -> None:
    with pytest.raises(ValueError):
        require_same_day_exit(dt("2025-01-02T10:00:00"), dt("2025-01-03T10:00:00"))


def test_26_development_p95_immutable_after_exam_mutation() -> None:
    development = list(range(1, 101))
    frozen = nearest_rank_p95(development)
    exam = [999]
    exam[0] = 1_000_000
    assert nearest_rank_p95(development) == frozen == 95


def test_27_gbpusd_explicitly_unavailable() -> None:
    rows = (Path(__file__).parents[1] / "outputs" / "LONDON_PROVISIONAL_DATA_INVENTORY.csv").read_text()
    assert "GBPUSD,PRE_OUTCOME_DATA_UNAVAILABLE_NOT_SCORED" in rows


def test_28_all_three_scored_instruments_visible() -> None:
    rows = (Path(__file__).parents[1] / "outputs" / "LONDON_PROVISIONAL_INSTRUMENT_RESULTS.csv").read_text()
    assert all(symbol in rows for symbol in ("XAUUSD", "EURUSD", "USDJPY"))


def test_29_every_instrument_gate_threshold_boundary() -> None:
    metrics = dict(full_history_trades=200, locked_exam_trades=25, baseline_pf=1.10, baseline_expectancy=.04,
                   baseline_net=.001, stress_pf=1, stress_net=.001, worst_segment_pf=.85, drawdown=20, top_ten_winners=.40)
    assert all(instrument_gates(metrics).values())
    failing = dict(full_history_trades=199, locked_exam_trades=24, baseline_pf=1.099, baseline_expectancy=.039,
                   baseline_net=0, stress_pf=.999, stress_net=0, worst_segment_pf=.849, drawdown=20.001, top_ten_winners=.401)
    for name, value in failing.items():
        probe = {**metrics, name: value}
        assert instrument_gates(probe)[name] is False


def test_30_every_combined_gate_threshold_boundary() -> None:
    metrics = dict(full_history_trades=1200, average_trades_year=120, median_trades_month=8, locked_exam_trades=100,
                   latest_six_months=45, latest_three_months=20, locked_exam_months=9, baseline_pf=1.2,
                   baseline_expectancy=.07, baseline_net=.001, stress_pf=1.05, stress_expectancy=.001,
                   stress_net=.001, exam_pf=1.1, exam_net=.001, drawdown=25, top_ten_winners=.3,
                   top_three_days=.2, instrument_contribution=.6)
    assert all(combined_gates(metrics).values())
    failing = dict(full_history_trades=1199, average_trades_year=119.99, median_trades_month=7.99, locked_exam_trades=99,
                   latest_six_months=44, latest_three_months=19, locked_exam_months=8, baseline_pf=1.199,
                   baseline_expectancy=.069, baseline_net=0, stress_pf=1.049, stress_expectancy=0,
                   stress_net=0, exam_pf=1.099, exam_net=0, drawdown=25.001, top_ten_winners=.301,
                   top_three_days=.201, instrument_contribution=.601)
    for name, value in failing.items():
        probe = {**metrics, name: value}
        assert combined_gates(probe)[name] is False


def test_31_classification_precedence() -> None:
    assert classify(False, 3, True).endswith("DATA_INVALID")
    assert classify(True, 1, True).endswith("REJECTED_NO_TICK_ACQUISITION")
    assert classify(True, 2, True).endswith("POSITIVE_TICK_CONFIRMATION_REQUIRED")


def test_32_no_absolute_paths_in_outputs() -> None:
    output = Path(__file__).parents[1] / "outputs"
    text = "".join(path.read_text(encoding="utf-8") for path in output.iterdir())
    assert "C:\\" not in text and "/home/" not in text


def test_33_no_broker_action_or_order_code() -> None:
    root = Path(__file__).parents[1]
    paths = [root / "run_provisional_screen.py", *sorted((root / "src").glob("*.py"))]
    source = "\n".join(path.read_text(encoding="utf-8") for path in paths)
    forbidden = ["order_" + "send(", "TRADE_" + "ACTION_", "Meta" + "Trader5"]
    assert all(token not in source for token in forbidden)


def test_34_manifest_records_full_deterministic_replay() -> None:
    import json
    manifest = json.loads((Path(__file__).parents[1] / "outputs" / "LONDON_PROVISIONAL_RUN_MANIFEST.json").read_text())
    assert manifest["deterministic_replay_match"] is True
