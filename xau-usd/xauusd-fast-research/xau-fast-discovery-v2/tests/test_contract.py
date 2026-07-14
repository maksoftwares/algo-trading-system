from __future__ import annotations

import json
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd
import pytest

from xau_fast_discovery.core import (
    BASE_COMMIT, BASE_TREE, BRANCH, DEVELOPMENT_END, DEVELOPMENT_START, EXAM_END, EXAM_START,
    STRATEGY_IDS, VALIDATION_END, VALIDATION_START, account_feasibility, add_indicators,
    causal_asof, classification, commercial_portfolio_gate, development_gate, execute_candidates,
    final_family_gate, segment_for_ms, weighted_percentile,
)

LANE = Path(__file__).resolve().parents[1]
REPO = LANE.parents[2]


def ms(value: str) -> int:
    return int(datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp() * 1000)


def test_exact_base_identity():
    assert subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO, text=True).strip() == BASE_COMMIT
    assert subprocess.check_output(["git", "rev-parse", "HEAD^{tree}"], cwd=REPO, text=True).strip() == BASE_TREE
    assert subprocess.check_output(["git", "branch", "--show-current"], cwd=REPO, text=True).strip() == BRANCH


@pytest.mark.parametrize("stamp,expected", [
    ("2021-06-30T23:59:59.999Z", "OUTSIDE"), ("2021-07-01T00:00:00Z", "DEVELOPMENT"),
    ("2024-06-30T23:59:59.999Z", "DEVELOPMENT"), ("2024-07-01T00:00:00Z", "VALIDATION"),
    ("2025-06-30T23:59:59.999Z", "VALIDATION"), ("2025-07-01T00:00:00Z", "LOCKED_EXAM"),
    ("2026-06-30T23:59:59.999Z", "LOCKED_EXAM"), ("2026-07-01T00:00:00Z", "OUTSIDE"),
])
def test_chronological_boundaries(stamp, expected):
    assert segment_for_ms(ms(stamp)) == expected


def bars(count=320, timeframe="H4"):
    width = {"M15": 900_000, "H1": 3_600_000, "H4": 14_400_000}[timeframe]
    close = np.linspace(100, 140, count) + np.sin(np.arange(count) / 5)
    return pd.DataFrame({"timestamp_ms": np.arange(count, dtype=np.int64) * width,
                         "open": close - .2, "high": close + 1, "low": close - 1,
                         "close": close, "volume": 1.0, "tick_count": 1})


def test_future_h4_mutation_cannot_change_prior_indicators():
    original = add_indicators(bars(), "H4")
    changed = bars()
    changed.loc[300:, ["open", "high", "low", "close"]] *= 10
    mutated = add_indicators(changed, "H4")
    pd.testing.assert_frame_equal(original.iloc[:300], mutated.iloc[:300])


def test_prior_only_atr_percentile_ignores_current_in_history():
    result = add_indicators(bars(), "H4")
    index = 300
    prior = result.ATR14.iloc[index - 252:index]
    expected = 100 * np.mean(prior.to_numpy() <= result.ATR14.iloc[index])
    assert result.ATR_PERCENTILE252_PRIOR.iloc[index] == pytest.approx(expected)


def test_h4_donchian_excludes_current_bar():
    frame = bars(40)
    frame.loc[30, "high"] = 999
    result = add_indicators(frame, "H4")
    assert result.DONCHIAN_HIGH20.iloc[30] < 999
    assert result.DONCHIAN_HIGH20.iloc[31] == 999


def test_completed_bar_asof_ownership():
    left = pd.DataFrame({"complete_ms": [100, 199, 200]})
    right = pd.DataFrame({"complete_ms": [100, 200], "value": [1, 2]})
    result = causal_asof(left, right, ["value"], "h_")
    assert result.h_value.tolist() == [1, 1, 2]
    assert result.h_complete_ms.tolist() == [100, 100, 200]


def test_impulse_rule_uses_true_range_not_high_low_range():
    frame = pd.DataFrame({"timestamp_ms":[0,900_000], "open":[100,111], "high":[101,112],
                          "low":[99,110], "close":[100,111], "volume":[1,1], "tick_count":[1,1]})
    result = add_indicators(pd.concat([bars(20, "M15"), frame.assign(timestamp_ms=[18_000_000,18_900_000])], ignore_index=True), "M15")
    last = result.iloc[-1]
    assert last.true_range >= last.range


@pytest.mark.parametrize("zone_stamp,local_hour", [("2024-03-31T06:30:00Z", 7), ("2024-10-27T07:30:00Z", 7)])
def test_london_historical_dst(zone_stamp, local_hour):
    local = datetime.fromisoformat(zone_stamp.replace("Z", "+00:00")).astimezone(ZoneInfo("Europe/London"))
    assert local.hour == local_hour


def test_pre_london_range_excludes_0700_bar_by_completion_label():
    completions = pd.Series([6 * 60 + 45, 7 * 60, 7 * 60 + 15])
    included = completions[(completions > 0) & (completions <= 7 * 60)]
    assert included.tolist() == [405, 420]


def candidate(strategy=STRATEGY_IDS[0], direction="LONG", signal="2023-01-03T10:00:00Z", stop=98.0, rr=2.0, hold=10):
    value = ms(signal)
    return {"strategy_id": strategy, "setup_episode_id": f"episode-{strategy}", "UTC_date": signal[:10],
            "direction": direction, "chronological_segment": "DEVELOPMENT", "higher_timeframe_regime_time": signal,
            "higher_timeframe_values": "{}", "setup_start_time": signal, "signal_time": signal,
            "signal_ms": value, "signal_bar_OHLC": "{}", "ATR_values": "{}", "frozen_levels": "{}",
            "raw_trigger_values": "{}", "signal_accepted_pre_execution": True, "signal_accepted": False,
            "rejection_reason": "PENDING_EXECUTION", "entry_time": "", "entry_bid": "", "entry_ask": "",
            "entry_price": "", "stop": stop, "target": "", "initial_risk_price": "", "rr": rr,
            "target_level": None, "max_hold_hours": hold, "stop_min_atr": None, "stop_max_atr": None, "m15_atr": 2.0}


def tick_frame(rows):
    return pd.DataFrame([{"timestamp_msc": ms(stamp), "bid": bid, "ask": ask, "spread": ask-bid, "source_sequence": f"s:{index:010d}"}
                         for index, (stamp, bid, ask) in enumerate(rows)])


def execute_one(c=None, rows=None, p95=1.0):
    c = c or candidate()
    rows = rows or [("2023-01-03T10:00:00Z", 100, 101), ("2023-01-03T10:01:00Z", 107, 108)]
    return execute_candidates([c], {"2023-01-03": tick_frame(rows)}, p95)


def test_next_tick_and_long_ask_entry_long_bid_exit_frozen_target():
    signals, trades = execute_one()
    assert trades[0]["entry_price"] == 101
    assert trades[0]["exit_price"] == 107
    assert trades[0]["target"] == 107
    assert signals[0]["signal_accepted"]


def test_short_bid_entry_and_short_ask_exit():
    c = candidate(direction="SHORT", stop=103)
    _, trades = execute_one(c, [("2023-01-03T10:00:00Z", 100, 101), ("2023-01-03T10:01:00Z", 93, 94)])
    assert trades[0]["entry_price"] == 100
    assert trades[0]["exit_price"] == 94


def test_stop_gap_uses_actual_worse_quote():
    _, trades = execute_one(rows=[("2023-01-03T10:00:00Z", 100, 101), ("2023-01-03T10:01:00Z", 97, 98)])
    assert trades[0]["exit_price"] == 97 and trades[0]["stop_gap"]


def test_mfe_mae_end_at_exit():
    _, trades = execute_one(rows=[("2023-01-03T10:00:00Z", 100, 101), ("2023-01-03T10:01:00Z", 107, 108), ("2023-01-03T10:02:00Z", 50, 51)])
    assert trades[0]["MFE_R"] == pytest.approx(2) and trades[0]["MAE_R"] == 0


def test_elapsed_maximum_hold():
    c = candidate(hold=1)
    _, trades = execute_one(c, [("2023-01-03T10:00:00Z", 100, 101), ("2023-01-03T11:00:00Z", 100, 101)])
    assert trades[0]["exit_reason"] == "MAXIMUM_ELAPSED_HOLD"


def test_same_day_20utc_force_exit():
    c = candidate(hold=12)
    _, trades = execute_one(c, [("2023-01-03T10:00:00Z", 100, 101), ("2023-01-03T20:00:00Z", 100, 101)])
    assert trades[0]["exit_reason"] == "SAME_DAY_20_UTC_FORCE_CLOSE"


def test_missing_same_day_exit_path_rejected():
    signals, trades = execute_one(rows=[("2023-01-03T10:00:00Z", 100, 101)])
    assert not trades and signals[0]["rejection_reason"] == "MISSING_SAME_DAY_EXIT_PATH"


def test_global_one_position_and_alphabetical_priority():
    a = candidate(STRATEGY_IDS[0])
    b = candidate(STRATEGY_IDS[1])
    signals, trades = execute_candidates([b, a], {"2023-01-03": tick_frame([("2023-01-03T10:00:00Z",100,101), ("2023-01-03T11:00:00Z",107,108)])}, 1)
    assert trades[0]["strategy_id"] == min(a["strategy_id"], b["strategy_id"])
    assert any(row["rejection_reason"] == "GLOBAL_XAU_POSITION_ALREADY_OPEN" for row in signals)


def test_one_family_trade_per_utc_date():
    first = candidate(signal="2023-01-03T10:00:00Z")
    second = candidate(signal="2023-01-03T12:00:00Z")
    second["setup_episode_id"] = "later"
    rows = tick_frame([("2023-01-03T10:00:00Z",100,101), ("2023-01-03T10:01:00Z",107,108), ("2023-01-03T12:00:00Z",100,101), ("2023-01-03T12:01:00Z",107,108)])
    signals, trades = execute_candidates([first, second], {"2023-01-03": rows}, 1)
    assert len(trades) == 1 and any(row["rejection_reason"] == "FAMILY_DAILY_TRADE_ALREADY_USED" for row in signals)


def test_identical_timestamp_unordered_conflict_is_stop_first():
    frame = tick_frame([("2023-01-03T10:00:00Z",100,101), ("2023-01-03T10:01:00Z",107,108), ("2023-01-03T10:01:00Z",97,98)])
    frame.loc[2, "source_sequence"] = frame.loc[1, "source_sequence"]
    _, trades = execute_candidates([candidate()], {"2023-01-03": frame}, 1)
    assert trades[0]["exit_reason"] == "IDENTICAL_TIMESTAMP_STOP_FIRST" and trades[0]["exit_price"] == 97


def test_baseline_spread_not_double_counted_and_stress_incremental():
    _, trades = execute_one(p95=2)
    trade = trades[0]
    assert trade["baseline_net_R"] == trade["gross_R"] == 2
    assert trade["stress_incremental_entry_spread_R"] == pytest.approx(1/3)
    assert trade["stress_incremental_exit_spread_R"] == pytest.approx(1/3)
    assert trade["stress_slippage_R"] == .05


def test_development_p95_weighted_freeze():
    assert weighted_percentile({1.0: 95, 2.0: 5}, .95) == 1.0


def passing_development():
    return {"trades":60,"profit_factor":1.05,"expectancy_R":.02,"net_R":1,"maximum_closed_drawdown_R":20,"top_ten_winner_share":.5}


@pytest.mark.parametrize("field,bad", [("trades",59),("profit_factor",1.049),("expectancy_R",.019),("net_R",0),("maximum_closed_drawdown_R",20.01),("top_ten_winner_share",.501)])
def test_every_baseline_development_gate_boundary(field,bad):
    baseline = passing_development(); stress = {**passing_development(), "profit_factor":1.0, "net_R":.01}
    baseline[field] = bad
    assert not development_gate(baseline, stress)[0]


@pytest.mark.parametrize("field,bad", [("profit_factor",.999),("net_R",0)])
def test_every_stress_development_gate_boundary(field,bad):
    stress = {**passing_development(), "profit_factor":1.0, "net_R":.01}; stress[field] = bad
    assert not development_gate(passing_development(), stress)[0]


def passing_final():
    return {"full_period_trades":150,"validation_trades":25,"locked_exam_trades":25,"baseline_PF":1.12,
            "baseline_expectancy_R":.05,"baseline_net_R":1,"stress_PF":1.03,"stress_expectancy_R":.01,
            "stress_net_R":1,"validation_net_R":1,"locked_exam_PF":1.05,"locked_exam_expectancy_R":.01,
            "locked_exam_net_R":1,"maximum_closed_drawdown_R":15,"top_ten_winner_share":.35,
            "top_three_winning_day_share":.25,"minimum_segment_PF":.90}


@pytest.mark.parametrize("field,bad", [("full_period_trades",149),("validation_trades",24),("locked_exam_trades",24),("baseline_PF",1.119),("baseline_expectancy_R",.049),("baseline_net_R",0),("stress_PF",1.029),("stress_expectancy_R",0),("stress_net_R",0),("validation_net_R",0),("locked_exam_PF",1.049),("locked_exam_expectancy_R",0),("locked_exam_net_R",0),("maximum_closed_drawdown_R",15.01),("top_ten_winner_share",.351),("top_three_winning_day_share",.251),("minimum_segment_PF",.899)])
def test_every_final_family_gate_boundary(field,bad):
    report = passing_final(); report[field] = bad
    assert not final_family_gate(report)[0]


def passing_portfolio():
    return {"full_period_trades":600,"annualized_trades":120,"median_monthly_trades":8,"locked_exam_trades":100,
            "latest_six_months_trades":45,"latest_three_months_trades":20,"locked_exam_active_months":9,
            "baseline_PF":1.25,"baseline_expectancy_R":.08,"baseline_net_R":1,"stress_PF":1.10,
            "stress_expectancy_R":.03,"stress_net_R":1,"locked_exam_PF":1.15,"locked_exam_expectancy_R":.05,
            "locked_exam_net_R":1,"baseline_floating_drawdown_R":20,"stress_floating_drawdown_R":25,
            "top_ten_winner_share":.30,"top_three_winning_day_share":.20,"maximum_family_positive_net_share":.60,
            "positive_rolling_12m_share":.70}


@pytest.mark.parametrize("field,bad", [("full_period_trades",599),("annualized_trades",119.9),("median_monthly_trades",7.9),("locked_exam_trades",99),("latest_six_months_trades",44),("latest_three_months_trades",19),("locked_exam_active_months",8),("baseline_PF",1.249),("baseline_expectancy_R",.079),("baseline_net_R",0),("stress_PF",1.099),("stress_expectancy_R",.029),("stress_net_R",0),("locked_exam_PF",1.149),("locked_exam_expectancy_R",.049),("locked_exam_net_R",0),("baseline_floating_drawdown_R",20.01),("stress_floating_drawdown_R",25.01),("top_ten_winner_share",.301),("top_three_winning_day_share",.201),("maximum_family_positive_net_share",.601),("positive_rolling_12m_share",.699)])
def test_every_portfolio_gate_boundary(field,bad):
    report = passing_portfolio(); report[field] = bad
    assert not commercial_portfolio_gate(report)[0]


@pytest.mark.parametrize("loss,margin,expected", [(5,200,True),(5.01,200,False),(5,200.01,False)])
def test_capital_minimum_volume_and_margin_feasibility(loss,margin,expected):
    passed, report = account_feasibility([loss],[margin])
    assert (not report["opportunity_rejection_reasons"]) is expected


def test_sizing_rejection_rate_gate():
    passed, report = account_feasibility([5]*9+[6], [100]*10)
    assert passed and report["rejection_rate"] == pytest.approx(.1)
    assert not account_feasibility([5]*8+[6]*2, [100]*10)[0]


@pytest.mark.parametrize("args,expected", [
    ((False,False,0),"XAU_FAST_DISCOVERY_V2_EVIDENCE_INVALID"),
    ((True,False,0),"XAU_FAST_DISCOVERY_V2_DATA_INCOMPLETE"),
    ((True,True,0),"XAU_FAST_DISCOVERY_V2_NO_DEVELOPMENT_SURVIVOR"),
    ((True,True,1),"XAU_FAST_DISCOVERY_V2_NO_PORTFOLIO_CANDIDATE"),
])
def test_classification_precedence(args,expected):
    assert classification(*args) == expected


def test_config_is_frozen_zero_search_and_hashable():
    config = json.loads((LANE / "config" / "frozen_config.json").read_text())
    assert config["parameter_search_count"] == 0 and len(config["strategy_ids"]) == 6


def test_no_mt5_tester_broker_action_absolute_paths_or_credentials_in_source():
    text = "\n".join(path.read_text(encoding="utf-8") for path in sorted((LANE / "src").rglob("*.py")))
    forbidden = ["import MetaTrader5", "OrderSend(", "C:\\Users\\", "password=", "token="]
    assert not any(value.lower() in text.lower() for value in forbidden)


def test_locked_exam_constants_do_not_enter_development_cost_or_strategy_functions():
    source = (LANE / "src" / "xau_fast_discovery" / "core.py").read_text()
    strategy_region = source[source.index("def generate_family_a"):source.index("def weighted_percentile")]
    assert "EXAM_START" not in strategy_region and "EXAM_END" not in strategy_region


def test_stage_a_and_conditional_stage_b_replay_contract_present():
    source = (LANE / "src" / "xau_fast_discovery" / "pipeline.py").read_text()
    assert "shutil.rmtree(run_one)" in source and "principal_identical" in source
    assert "stage_b_acquired" in source
