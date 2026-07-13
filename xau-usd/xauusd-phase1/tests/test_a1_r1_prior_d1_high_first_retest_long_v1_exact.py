from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import run_a1_r1_prior_d1_high_first_retest_long_v1_exact as r1  # noqa: E402
import run_a1_r2_prior_d1_low_first_retest_short_v1_exact as r2  # noqa: E402


def test_r1_pdh_runner_is_one_frozen_authorized_structural_cell() -> None:
    variants = r1.build_variants()
    checks = r1.static_checks(variants)
    assert len(variants) == 1
    assert variants[0].name == r1.VARIANT_NAME
    assert variants[0].tester_inputs == r1.FROZEN_INPUTS
    assert all(checks.values()), checks
    assert r1.HISTORICAL_RUN_AUTHORIZED is True
    assert r1.PREREG.exists()


def test_r1_pdh_is_the_directional_parameter_mirror_of_frozen_r2_pdl() -> None:
    left = r1.FROZEN_INPUTS
    right = r2.FROZEN_INPUTS
    mirrored = {
        "InpR1PdhAtrPeriod": "InpR2PdlAtrPeriod",
        "InpR1PdhH1AtrPercentileLookback": "InpR2PdlH1AtrPercentileLookback",
        "InpR1PdhH1AtrPercentileMin": "InpR2PdlH1AtrPercentileMin",
        "InpR1PdhH1AtrPercentileMax": "InpR2PdlH1AtrPercentileMax",
        "InpR1PdhBreakMarginH1Atr": "InpR2PdlBreakMarginH1Atr",
        "InpR1PdhBreakMinRangeH1Atr": "InpR2PdlBreakMinRangeH1Atr",
        "InpR1PdhBreakMinBodyFraction": "InpR2PdlBreakMinBodyFraction",
        "InpR1PdhRetestWindowM15Bars": "InpR2PdlRetestWindowM15Bars",
        "InpR1PdhRetestTouchM15Atr": "InpR2PdlRetestTouchM15Atr",
        "InpR1PdhReclaimDistanceM15Atr": "InpR2PdlRejectDistanceM15Atr",
        "InpR1PdhReclaimMinBodyFraction": "InpR2PdlRejectMinBodyFraction",
        "InpR1PdhStopBufferM15Atr": "InpR2PdlStopBufferM15Atr",
        "InpR1PdhMaxStopH1Atr": "InpR2PdlMaxStopH1Atr",
    }
    for r1_key, r2_key in mirrored.items():
        assert left[r1_key] == right[r2_key], (r1_key, r2_key)
    assert left["InpR1PdhBreakCloseLocationMin"] == "0.75"
    assert right["InpR2PdlBreakCloseLocationMax"] == "0.25"
    assert left["InpR1PdhReclaimCloseLocationMin"] == "0.75"
    assert right["InpR2PdlRejectCloseLocationMax"] == "0.25"
    assert left["InpRegimeRouterMode"] == "1"
    assert right["InpRegimeRouterMode"] == "2"
    assert left["InpDirectionMode"] == "1"
    assert right["InpDirectionMode"] == "2"


def test_r1_pdh_uses_global_10k_50usd_risk_and_no_masks_or_stacking() -> None:
    inputs = r1.FROZEN_INPUTS
    assert inputs["InpUseRiskNormalizedLots"] == "true"
    assert inputs["InpRiskAmountUsd"] == "50.00"
    assert inputs["InpMaxRiskLots"] == "0.10"
    assert inputs["InpRejectRiskOvershootEnabled"] == "true"
    assert inputs["InpMaxRiskOvershootPct"] == "10.00"
    assert inputs["InpOnePositionPerMagic"] == "true"
    assert inputs["InpMaxOpenPositionsPerMagic"] == "1"
    assert inputs["InpMaxTradesPerDay"] == "0"
    assert inputs["InpCooldownMinutes"] == "0"
    assert inputs["InpBlockedEntryHoursCsv"] == ""
    assert inputs["InpBlockedEntryDayHoursCsv"] == ""
    assert inputs["InpBlockedLongEntryHoursCsv"] == ""
    assert inputs["InpBlockedShortEntryHoursCsv"] == ""
    assert inputs["InpPortfolioDailyGuardEnabled"] == "false"
    assert inputs["InpH4D1PrevMonthHealthGateEnabled"] == "false"
    assert inputs["InpH4D1WeeklyLossGovernorEnabled"] == "false"


def test_r1_pdh_is_statically_independent_from_box_and_r3_compression() -> None:
    inputs = r1.FROZEN_INPUTS
    assert inputs["InpSignalMode"] == "23"
    assert inputs["InpSignalMode"] != "7"
    assert not any(key.startswith("InpD1Compression") for key in inputs)
    prereg = r1.PREREG.read_text(encoding="utf-8")
    assert "does not use D1 compression ATR percentile" in prereg
    assert "first M15 retest touch" in prereg
    assert "There is no retry" in prereg


def test_implementation_readiness_is_fail_closed_until_ea_patch_exists() -> None:
    readiness = r1.implementation_readiness()
    source = r1.EA_SOURCE.read_text(encoding="utf-8")
    for token, present in readiness.items():
        assert present is (token in source)
    if all(readiness.values()):
        assert "SIGNAL_R1_PRIOR_D1_HIGH_FIRST_RETEST_LONG = 23" in source
        assert "g_r1_pdh_consumed_break_time = g_r1_pdh_break_time;" in source
        assert "r1_pdh_first_retest_rejected" in source
        assert "CurrentXauRegime() != XAU_REGIME_UPTREND" in source
    else:
        assert not r1.HISTORICAL_RUN_AUTHORIZED


def test_first_touch_is_consumed_before_reclaim_qualification_and_cannot_retry() -> None:
    source = r1.EA_SOURCE.read_text(encoding="utf-8")
    start = source.index("bool TryR1PriorD1HighFirstRetestLongSignal(")
    end = source.index("\nbool TryWeeklyLevel(", start)
    block = source[start:end]

    touch = block.index("const bool touched_level =")
    no_touch = block.index("if(!touched_level)", touch)
    first_touch_consumption = block.index(
        "// Consumption is deliberately before candle qualification", no_touch
    )
    consume = block.index(
        "g_r1_pdh_consumed_break_time = g_r1_pdh_break_time;", first_touch_consumption
    )
    qualify = block.index("const bool reclaimed_level =", touch)
    reject = block.index('g_r1_pdh_last_outcome_reason = "r1_pdh_first_retest_rejected";', qualify)
    assert touch < no_touch < first_touch_consumption < consume < qualify < reject
    no_touch_block = block[no_touch:first_touch_consumption]
    assert "if(final_retest_bar)" in no_touch_block
    assert 'g_r1_pdh_last_outcome_reason = "r1_pdh_expired";' in no_touch_block
    assert "if(!reclaimed_level)" in block

    accepted_tail = block[block.index('direction = "LONG";') :]
    assert "ResetR1PriorD1HighBreakState" not in accepted_tail
    assert "return true;" in accepted_tail


def test_mode23_has_causal_initialization_entry_ownership_and_exact_audit_mapping() -> None:
    source = r1.EA_SOURCE.read_text(encoding="utf-8")
    refresh_start = source.index("void RefreshR1PriorD1HighBreakState()")
    refresh_end = source.index("\ndouble R1PriorD1HighRetestLow", refresh_start)
    refresh = source[refresh_start:refresh_end]
    assert "g_r1_pdh_last_scanned_h1_bar == 0" in refresh
    assert "ArmR1PriorD1HighBreakAtH1Shift(1);" in refresh
    assert "oldest_shift" not in refresh

    arm_start = source.index("bool ArmR1PriorD1HighBreakAtH1Shift(")
    arm_end = source.index("\nvoid RefreshR1PriorD1HighBreakState", arm_start)
    arm = source[arm_start:arm_end]
    assert "CurrentXauRegime() != XAU_REGIME_UPTREND" in arm
    assert "containing_d1_shift + 1" in source

    assert "log_recent_high = g_r1_pdh_break_close;" in source
    assert "log_recent_low = g_r1_pdh_level;" in source
    assert "log_three_bar_move_atr = g_r1_pdh_h1_atr_percentile / 100.0;" in source
    assert '"r1_pdh_stop_h1_atr_exceeded"' in source
    assert (
        'reason = "R1_PRIOR_D1_HIGH_FIRST_RETEST_LONG_STATE_" + '
        "RegimeStateName(CurrentXauRegime());"
    ) in source


def test_native_r1_purity_matches_only_exact_uptrend_reason(tmp_path: Path) -> None:
    signal_csv = tmp_path / "signals.csv"
    signal_csv.write_text(
        "timestamp_broker\tstage\tdirection\treason\n"
        "2026.01.02 10:00:00\tWOULD_SIGNAL\tLONG\tR1_PRIOR_D1_HIGH_FIRST_RETEST_LONG_STATE_uptrend\n"
        "2026.01.03 10:00:00\tWOULD_SIGNAL\tLONG\tR1_PRIOR_D1_HIGH_FIRST_RETEST_LONG_STATE_chop\n",
        encoding="utf-8",
    )
    rows = [
        {"entry_time": datetime(2026, 1, 2, 10, 4), "direction": "LONG"},
        {"entry_time": datetime(2026, 1, 3, 10, 4), "direction": "LONG"},
    ]
    result = r1.native_r1_purity(rows, signal_csv)
    assert result["matched_signal_reasons"] == 2
    assert result["uptrend_reasons"] == 1
    assert result["purity_pct"] == 50.0


def test_global_drawdown_failure_is_alpha_only_not_fully_qualified() -> None:
    all_pass = {
        "alpha_checks": {"alpha": True},
        "robustness_checks": {"robust": True},
        "regime_independence_checks": {"regime": True},
        "execution_checks": {"execution": True},
        "drawdown_checks": {"drawdown": True},
    }
    windows = [
        {group: dict(values) for group, values in all_pass.items()},
        {group: dict(values) for group, values in all_pass.items()},
    ]
    windows[1]["drawdown_checks"]["drawdown"] = False
    status, _ = r1.decide({"static": True}, windows)
    assert status == "R1_PDH_FIRST_RETEST_ALPHA_ONLY_RISK_REPAIR_REQUIRED"
    windows[0]["alpha_checks"]["alpha"] = False
    status, _ = r1.decide({"static": True}, windows)
    assert status == "R1_PDH_FIRST_RETEST_REJECT"
