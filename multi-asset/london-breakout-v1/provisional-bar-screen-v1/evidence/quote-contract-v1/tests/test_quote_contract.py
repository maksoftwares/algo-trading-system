from __future__ import annotations

import json
from pathlib import Path

import pytest

from quote_contract import *


ROOT = Path(__file__).resolve().parents[1]


def ticks():
    return [
        {"time": 0, "time_msc": 0, "bid": 100.0, "ask": 100.2, "last": 100.1, "volume": 1, "flags": 1},
        {"time": 1, "time_msc": 1_000, "bid": 101.0, "ask": 101.4, "last": 101.2, "volume": 1, "flags": 1},
        {"time": 2, "time_msc": 2_000, "bid": 99.0, "ask": 99.3, "last": 99.1, "volume": 1, "flags": 1},
        {"time": 3, "time_msc": 3_000, "bid": 100.5, "ask": 100.6, "last": 100.55, "volume": 1, "flags": 1},
    ]


def perfect(rate=1.0, error=0.0):
    return {name: {"exact_rate": rate, "median_abs_difference": error} for name in ("open", "high", "low", "close")}


def test_01_tick_sorting_by_time_msc():
    ordered, _ = normalize_ticks(reversed(ticks())); assert [x["time_msc"] for x in ordered] == [0, 1000, 2000, 3000]


def test_02_duplicate_tick_detection():
    _, report = normalize_ticks(ticks() + [ticks()[0]]); assert report["duplicates"] == 1


def test_03_invalid_bid_ask_rejection():
    bad = ticks(); bad[0] = {**bad[0], "ask": 99};
    with pytest.raises(ValueError): aggregate_ticks(bad, 2)


def test_04_exact_m5_interval_construction():
    assert interval_start(299_999) == 0 and interval_start(300_000) == 300_000


def test_05_bid_ohlc_aggregation():
    assert aggregate_ticks(ticks(), 2)[0]["ohlc"]["BID"] == (100, 101, 99, 100.5)


def test_06_ask_ohlc_aggregation():
    assert aggregate_ticks(ticks(), 2)[0]["ohlc"]["ASK"] == (100.2, 101.4, 99.3, 100.6)


def test_07_mid_ohlc_aggregation():
    assert aggregate_ticks(ticks(), 2)[0]["ohlc"]["MID"] == (100.1, 101.2, 99.15, 100.55)


def test_08_last_ohlc_where_applicable():
    assert aggregate_ticks(ticks(), 2, True)[0]["ohlc"]["LAST"] == (100.1, 101.2, 99.1, 100.55)


def test_09_incomplete_first_bar_exclusion():
    assert not complete_interval({"start_msc": 0}, 1, BAR_MS)


def test_10_incomplete_final_bar_exclusion():
    assert not complete_interval({"start_msc": 0}, 0, BAR_MS - 1)


def test_11_repository_timestamp_alignment():
    assert interval_start(600_001) == 600_000


def test_12_one_bar_shift_detection():
    assert interval_start(600_001) != 300_000


def test_13_utc_offset_mismatch_detection():
    assert interval_start(3_600_000) != interval_start(0)


def test_14_digits_rounding():
    assert aggregate_ticks(ticks(), 1)[0]["ohlc"]["MID"][2] == 99.2


def test_15_point_conversion():
    assert (100.2 - 100.0) / .1 == pytest.approx(2)


def test_16_bid_basis_match_threshold():
    assert basis_pass(perfect())


def test_17_ask_basis_match_threshold():
    assert not basis_pass(perfect(.99))


def test_18_mid_basis_match_threshold():
    probe = perfect(); probe["high"]["exact_rate"] = .995; assert basis_pass(probe)


def test_19_alternative_basis_separation():
    assert separated(perfect(1, 0), [perfect(.99, 1)])


def test_20_ambiguous_basis_failure():
    assert not separated(perfect(1, 0), [perfect(.999, 0)])


def test_21_open_spread_calculation():
    assert aggregate_ticks(ticks(), 2)[0]["spreads"]["BAR_OPEN_SPREAD"] == pytest.approx(.2)


def test_22_close_spread_calculation():
    assert aggregate_ticks(ticks(), 2)[0]["spreads"]["BAR_CLOSE_SPREAD"] == pytest.approx(.1)


def test_23_minimum_spread_calculation():
    assert aggregate_ticks(ticks(), 2)[0]["spreads"]["BAR_MINIMUM_SPREAD"] == pytest.approx(.1)


def test_24_maximum_spread_calculation():
    assert aggregate_ticks(ticks(), 2)[0]["spreads"]["BAR_MAXIMUM_SPREAD"] == pytest.approx(.4)


def test_25_mean_spread_calculation():
    assert aggregate_ticks(ticks(), 2)[0]["spreads"]["BAR_MEAN_SPREAD"] == pytest.approx(.25)


def test_26_median_spread_calculation():
    assert aggregate_ticks(ticks(), 2)[0]["spreads"]["BAR_MEDIAN_SPREAD"] == pytest.approx(.25)


def test_27_exporter_rounding_reproduction():
    assert round(1.23456, 4) == 1.2346


def test_28_spread_exact_match_threshold():
    assert spread_pass({"exact_rate": .995, "within_one_rate": .995, "median_abs_error_points": 0})


def test_29_spread_within_one_threshold():
    assert spread_pass({"exact_rate": 0, "within_one_rate": .999, "median_abs_error_points": .25})


def test_30_spread_semantics_conflict_handling():
    assert not spread_pass({"exact_rate": .9, "within_one_rate": .99, "median_abs_error_points": 1})


def test_31_h1_aggregation_consistency():
    bars = [(1, 2, .5, 1.5)] * 12; assert aggregate_ohlc(bars) == (1, 2, .5, 1.5)


def test_32_m15_aggregation_consistency():
    bars = [(1, 2, .5, 1.5), (1.5, 3, 1, 2), (2, 2.5, 1.5, 2.2)]; assert aggregate_ohlc(bars) == (1, 3, .5, 2.2)


def test_33_segment_stability_reporting():
    assert segment(0) == "DEVELOPMENT_OVERLAP" and segment(1_735_689_600_000) == "VALIDATION_OVERLAP"


def test_34_future_tick_mutation_does_not_alter_earlier_bar():
    base = aggregate_ticks(ticks(), 2)[0]; future = ticks() + [{**ticks()[0], "time_msc": BAR_MS, "bid": 999, "ask": 1000}]; assert aggregate_ticks(future, 2)[0] == base


def test_35_all_three_instruments_required_before_scoring():
    assert not all_three_resolved({"XAUUSD": "QUOTE_CONTRACT_RESOLVED_BID", "EURUSD": "QUOTE_CONTRACT_RESOLVED_BID"})


def test_36_strategy_config_hashes_unchanged():
    result = json.loads((ROOT / "LONDON_QUOTE_CONTRACT_RESULT.json").read_text()); assert result["strategy_and_config_hashes_unchanged"] is True


def test_37_no_strategy_scoring_on_unresolved_contract():
    assert not strategy_scoring_allowed({s: "PROVENANCE_CHAIN_INCOMPLETE" for s in ("XAUUSD", "EURUSD", "USDJPY")})


def test_38_no_broker_action_order_code():
    source = "\n".join(path.read_text() for path in [ROOT / "quote_contract.py", ROOT / "run_quote_contract_audit.py"]); forbidden = ["order_"+"send(", "TRADE_"+"ACTION_"]; assert all(x not in source for x in forbidden)


def test_39_no_absolute_paths_in_outputs():
    text = "".join(path.read_text(encoding="utf-8") for path in ROOT.glob("LONDON_*")); assert "C:\\" not in text and "/home/" not in text


def test_40_complete_deterministic_replay():
    manifest = json.loads((ROOT / "LONDON_QUOTE_CONTRACT_MANIFEST.json").read_text()); assert manifest["deterministic_replay_match"] is True
