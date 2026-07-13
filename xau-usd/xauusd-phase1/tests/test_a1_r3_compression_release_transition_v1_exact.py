from __future__ import annotations

import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import run_a1_r3_compression_release_transition_v1_exact as r3  # noqa: E402


def test_frozen_candidate_is_strict_symmetric_compression_release() -> None:
    variants = r3.build_variants()
    assert len(variants) == 1
    assert variants[0].name == r3.SOURCE_ID
    inputs = r3.R3_INPUTS
    assert inputs["InpSignalMode"] == "7"
    assert inputs["InpDirectionMode"] == "0"
    assert inputs["InpRegimeRouterMode"] == "5"
    assert inputs["InpD1CompressionAtrPercentileMax"] == "30.00"
    assert inputs["InpD1CompressionBoxDays"] == "5"
    assert inputs["InpD1CompressionRangeMedianMax"] == "1.00"
    assert inputs["InpD1CompressionH4MinBodyFraction"] == "0.50"
    assert inputs["InpRiskReward"] == "2.00"


def test_candidate_has_no_calendar_or_performance_masks() -> None:
    inputs = r3.R3_INPUTS
    assert inputs["InpBlockedEntryHoursCsv"] == ""
    assert inputs["InpBlockedEntryDayHoursCsv"] == ""
    assert inputs["InpBlockedLongEntryHoursCsv"] == ""
    assert inputs["InpBlockedShortEntryHoursCsv"] == ""
    assert inputs["InpUseDirectionalSessionFilter"] == "false"
    assert inputs["InpPortfolioDailyGuardEnabled"] == "false"
    assert inputs["InpH4D1WeeklyLossGovernorEnabled"] == "false"
    assert inputs["InpH4D1PrevMonthHealthGateEnabled"] == "false"
    assert inputs["InpH4D1NegativeStackGuardEnabled"] == "false"
    assert inputs["InpH4D1ThirdEntryQualityGateEnabled"] == "false"


def test_candidate_uses_fail_closed_one_percent_stop_risk_and_no_stacking() -> None:
    inputs = r3.R3_INPUTS
    assert inputs["InpUseRiskNormalizedLots"] == "true"
    assert inputs["InpRiskAmountUsd"] == "100.00"
    assert inputs["InpRejectRiskOvershootEnabled"] == "true"
    assert inputs["InpMaxRiskOvershootPct"] == "0.00"
    assert inputs["InpOnePositionPerMagic"] == "true"
    assert inputs["InpMaxOpenPositionsPerMagic"] == "1"


def test_existing_signal_uses_only_completed_d1_and_h4_bars_and_is_symmetric() -> None:
    source = r3.EA_SOURCE.read_text(encoding="utf-8")
    start = source.index("bool TryD1CompressionH4ExpansionSignal")
    end = source.index("bool TryD1CompressionH1ExpansionSignal", start)
    block = source[start:end]
    assert "TimeframeHigh(PERIOD_D1, 1, box_days)" in block
    assert "TimeframeLow(PERIOD_D1, 1, box_days)" in block
    assert "IndicatorAtrPercentile(PERIOD_D1, 14, 252, 1)" in block
    assert "iClose(InpTargetSymbol, PERIOD_H4, 1)" in block
    assert "h4_close > box_high && h4_close > h4_open" in block
    assert "h4_close < box_low && h4_close < h4_open" in block
    assert 'reason = "D1_COMPRESSION_H4_EXPANSION_LONG"' in block
    assert 'reason = "D1_COMPRESSION_H4_EXPANSION_SHORT"' in block


def test_readiness_check_is_explicit_while_router_mode_is_pending() -> None:
    source = r3.EA_SOURCE.read_text(encoding="utf-8")
    token = "REGIME_ROUTER_R3_COMPRESSION_RELEASE_SHOCK_BLOCK = 5"
    if token in source:
        r3.require_ready()
    else:
        with pytest.raises(RuntimeError, match="R3 exact infrastructure is not ready"):
            r3.require_ready()


def test_mt5_equity_drawdown_parser() -> None:
    assert r3.parse_money_percent("1 733.37 (24.59%)") == (1733.37, 24.59)
    assert r3.parse_money_percent("0.00 (0.00%)") == (0.0, 0.0)
    assert r3.parse_money_percent(None) == (None, None)


def test_admission_fails_when_one_direction_or_equity_dd_is_weak() -> None:
    book = {
        "signals": 120,
        "wr": 55.0,
        "wl": 2.1,
        "pf": 2.2,
        "stress_030_pf": 2.0,
        "stress_030_net": 100.0,
        "positive_year_buckets": 3,
        "top10_removed_net": 10.0,
        "top3_days_removed_net": 10.0,
        "best_month_share_pct": 25.0,
    }
    long_shape = {"signals": 80, "stress_030_net": 75.0}
    short_shape = {"signals": 10, "stress_030_net": -5.0}
    orders = {"actions": {"ORDER_SEND_OK": 120}, "guard_reasons": {}}
    signals = {"unexpected_reasons": []}

    checks = r3.standalone_checks(
        book,
        long_shape,
        short_shape,
        12.0,
        orders,
        signals,
    )

    assert checks["short_trades_ge_20"] is False
    assert checks["short_stress_net_gt_0"] is False
    assert checks["max_equity_dd_lte_10pct"] is False
    assert not all(checks.values())
