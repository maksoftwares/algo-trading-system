from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
EA = ROOT / "mt5" / "Experts" / "A1XauM5MomentumContinuationExecutor.mq5"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import analyze_a1_r2_prior_d1_low_first_retest_episode_audit as audit  # noqa: E402
import run_a1_r2_prior_d1_low_first_retest_short_v1_exact as runner  # noqa: E402


def _ea_text() -> str:
    return EA.read_text(encoding="utf-8")


def test_r2_pdl_runner_is_one_authorized_frozen_structural_cell() -> None:
    variants = runner.build_variants()
    checks = runner.static_checks(variants)
    assert len(variants) == 1
    assert all(checks.values()), checks
    assert runner.HISTORICAL_RUN_AUTHORIZED is True
    assert variants[0].name == "r2_pdl_first_retest_structural_v1"
    inputs = variants[0].tester_inputs
    assert inputs == runner.FROZEN_INPUTS
    assert inputs["InpSignalMode"] == "22"
    assert inputs["InpRegimeRouterMode"] == "2"
    assert inputs["InpDirectionMode"] == "2"
    assert inputs["InpRiskReward"] == "2.00"
    assert inputs["InpMinAtrAbsoluteForEntry"] == "0.00"
    assert inputs["InpUseRiskNormalizedLots"] == "true"
    assert inputs["InpRiskAmountUsd"] == "50.00"
    assert inputs["InpMaxRiskLots"] == "0.10"
    assert inputs["InpRejectRiskOvershootEnabled"] == "true"
    assert inputs["InpMaxRiskOvershootPct"] == "10.00"
    assert runner.r2_common.stable_hash(inputs) == "334f77be0aa48a81f9c8b8bd7e27a687b318e3dea8a48689b89a231b221d909b"
    assert runner.PREREG.exists()
    assert runner.OUTPUT_STEM == audit.OUTPUT_STEM
    assert runner.VARIANT_NAME == audit.VARIANT_NAME


def test_r2_pdl_runner_has_no_calendar_or_trade_management_overlay() -> None:
    inputs = runner.FROZEN_INPUTS
    assert inputs["InpBlockedEntryHoursCsv"] == ""
    assert inputs["InpBlockedEntryDayHoursCsv"] == ""
    assert inputs["InpBlockedLongEntryHoursCsv"] == ""
    assert inputs["InpBlockedShortEntryHoursCsv"] == ""
    assert inputs["InpUseDirectionalSessionFilter"] == "false"
    assert inputs["InpMaxTradesPerDay"] == "0"
    assert inputs["InpCooldownMinutes"] == "0"
    assert inputs["InpPortfolioDailyGuardEnabled"] == "false"
    assert inputs["InpProfitProtectionEnabled"] == "false"
    assert inputs["InpPartialCloseEnabled"] == "false"
    assert inputs["InpSplitEntryEnabled"] == "false"


def test_r2_pdl_ea_defaults_preserve_existing_runtime_and_append_mode_22() -> None:
    text = _ea_text()
    assert "SIGNAL_R2_H1_PULLBACK_REJECTION_SHORT = 21," in text
    assert "SIGNAL_R2_PRIOR_D1_LOW_FIRST_RETEST_SHORT = 22" in text
    assert "input bool   InpRejectRiskOvershootEnabled    = false;" in text
    assert "input double InpMaxRiskOvershootPct           = 10.00;" in text
    assert "input int    InpR2PdlAtrPeriod                = 14;" in text
    assert "input int    InpR2PdlH1AtrPercentileLookback = 480;" in text
    assert "input double InpR2PdlH1AtrPercentileMin      = 40.00;" in text
    assert "input double InpR2PdlH1AtrPercentileMax      = 90.00;" in text
    assert "input int    InpR2PdlRetestWindowM15Bars     = 8;" in text
    assert "input double InpR2PdlMaxStopH1Atr            = 1.00;" in text


def test_r2_pdl_ea_uses_completed_causal_bars_and_consumes_first_rejection() -> None:
    text = _ea_text()
    assert "iLow(InpTargetSymbol, PERIOD_D1, containing_d1_shift + 1)" in text
    assert "const datetime h1_bar_time = iTime(InpTargetSymbol, PERIOD_H1, shift);" in text
    assert "const datetime break_time = h1_bar_time + PeriodSeconds(PERIOD_H1);" in text
    assert "IndicatorAtrPercentile(PERIOD_H1, atr_period, percentile_lookback, shift)" in text
    assert "atr_percentile >= InpR2PdlH1AtrPercentileMin" in text
    assert "atr_percentile <= InpR2PdlH1AtrPercentileMax" in text
    assert "m15_bar_time = iTime(InpTargetSymbol, PERIOD_M15, 1);" in text
    assert "m15_close_time = m15_bar_time + PeriodSeconds(PERIOD_M15);" in text
    assert "g_r2_pdl_retest_m15_bars_observed" in text
    assert "R2PdlTakeDistinctCompletedM15Bar" in text
    assert "const bool final_retest_bar" in text
    assert "g_r2_pdl_break_expiry" not in text
    assert "close > g_r2_pdl_level + MathMax(0.0, InpR2PdlInvalidReclaimH1Atr) * g_r2_pdl_h1_atr" in text
    assert "const double retest_high = R2PriorD1LowRetestHigh(g_r2_pdl_break_time);" in text
    assert 'reason = "R2_PRIOR_D1_LOW_FIRST_RETEST_SHORT_STATE_" + RegimeStateName(CurrentXauRegime());' in text
    assert "g_r2_pdl_consumed_break_time = g_r2_pdl_break_time;" in text
    assert "TryR2PriorD1LowFirstRetestShortSignal(direction, reason, htf_stop_distance, break_distance_atr);" in text


def test_r2_pdl_ea_logs_audit_fields_and_guards_stop_and_normalized_risk() -> None:
    text = _ea_text()
    assert "log_recent_high = g_r2_pdl_level;" in text
    assert "log_recent_low = g_r2_pdl_break_close;" in text
    assert "log_three_bar_move_atr = g_r2_pdl_h1_atr_percentile / 100.0;" in text
    assert '"r2_pdl_stop_h1_atr_exceeded"' in text
    assert '"risk_amount_overshoot"' in text
    lots_index = text.index("const double order_lots = LotsForStopDistance(stop_distance);")
    risk_index = text.index(": RiskOvershootAllowed(stop_distance, order_lots, actual_risk_usd);")
    send_index = text.index("if(direction == \"LONG\")", risk_index)
    assert lots_index < risk_index < send_index


def test_episode_audit_parses_equity_dd_and_fails_closed_when_missing(tmp_path: Path) -> None:
    assert audit.parse_money_prefix("1 720.10 (15.27%)") == 1720.10
    assert audit.parse_money_prefix("") is None
    report = tmp_path / "mt5.json"
    report.write_text(
        json.dumps({"variants": [{"mt5_report_metrics": {"Equity Drawdown Maximal": "1 720.10 (15.27%)"}}]}),
        encoding="utf-8",
    )
    assert audit.max_equity_dd_from_mt5(report) == 1720.10
    report.write_text(json.dumps({"variants": [{"mt5_report_metrics": {}}]}), encoding="utf-8")
    assert audit.max_equity_dd_from_mt5(report) is None


def test_episode_audit_matches_same_direction_signal_with_fill_tolerance() -> None:
    signal_time = datetime(2026, 3, 2, 10, 0, 0)
    rows = [
        {"entry_time": signal_time + timedelta(minutes=4), "direction": "SHORT"},
        {"entry_time": signal_time + timedelta(minutes=4), "direction": "LONG"},
    ]
    signals = [
        {
            "timestamp": signal_time,
            "direction": "SHORT",
            "reason": "R2_PRIOR_D1_LOW_FIRST_RETEST_SHORT_STATE_downtrend",
        }
    ]
    result = audit.native_regime_purity(rows, signals)
    assert result["matched_signal_reasons"] == 1
    assert result["downtrend_reasons"] == 1
    assert result["purity_pct"] == 50.0
    assert len(result["missing_entry_times"]) == 1


def test_episode_audit_overlap_is_directional_and_inclusive_at_15_minutes() -> None:
    base = datetime(2026, 4, 1, 8, 0, 0)
    candidate = [
        {"entry_time": base, "direction": "SHORT"},
        {"entry_time": base + timedelta(hours=1), "direction": "SHORT"},
        {"entry_time": base + timedelta(hours=2), "direction": "LONG"},
    ]
    control = [
        {"entry_time": base + timedelta(minutes=15), "direction": "SHORT"},
        {"entry_time": base + timedelta(hours=1, minutes=16), "direction": "SHORT"},
        {"entry_time": base + timedelta(hours=2), "direction": "SHORT"},
    ]
    result = audit.overlap_with_control(candidate, control, "control")
    assert result["overlap_trades"] == 1
    assert result["overlap_pct"] == 33.33


def test_episode_audit_losing_streak_and_concentration_are_deterministic() -> None:
    base = datetime(2026, 1, 1)
    rows = [
        {"entry_time": base, "exit_time": base + timedelta(hours=3), "pnl_usd": -50.0},
        {"entry_time": base, "exit_time": base + timedelta(hours=1), "pnl_usd": -50.0},
        {"entry_time": base, "exit_time": base + timedelta(hours=2), "pnl_usd": -50.0},
        {"entry_time": base, "exit_time": base + timedelta(hours=4), "pnl_usd": 100.0},
    ]
    assert audit.longest_losing_streak(rows) == 3
    assert audit.episode_concentration([{"net_usd": 60.0}, {"net_usd": 40.0}, {"net_usd": -10.0}]) == 60.0
