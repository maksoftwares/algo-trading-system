from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EXPERTS = ROOT / "mt5" / "Experts"
PRESETS = ROOT / "mt5" / "Presets"
DOCS = ROOT / "docs"

EA_T1 = EXPERTS / "Account3RoundRetestGuardedExecutor.mq5"
EA_T2 = EXPERTS / "Account3RoundRetestStructuredExecutor.mq5"


def _text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_a3_committed_defaults_are_non_executing():
    for path in (EA_T1, EA_T2):
        text = _text(path)
        assert "input bool InpDryRunOnly = true;" in text
        assert "input bool InpBrokerActionAllowed = false;" in text


def test_a3_magic_bands_and_reserved_band_are_source_locked():
    t1 = _text(EA_T1)
    t2 = _text(EA_T2)
    manifest = _text(DOCS / "A3_HYPOTHESIS_HASH_MANIFEST.json")

    assert "input int InpMagicNumber = 933000;" in t1
    assert "InpMagicNumber < 933000 || InpMagicNumber > 933099" in t1
    assert "input int InpMagicNumber = 933100;" in t2
    assert "InpMagicNumber < 933100 || InpMagicNumber > 933199" in t2
    assert "933200-933299" in manifest


def test_no_committed_a3_execution_enabled_preset_anywhere():
    offenders = []
    for path in PRESETS.glob("Account3RoundRetest*Executor*.set"):
        if "InpBrokerActionAllowed=true" in _text(path):
            offenders.append(path.name)
    assert offenders == []


def test_a3_login_allowlist_demo_server_live_real_refusal_and_two_tier_kill_switch():
    for path in (EA_T1, EA_T2):
        text = _text(path)
        assert 'input string InpAllowedAccountLoginsCsv = "1033669";' in text
        assert "AccountLoginWhitelisted()" in text
        assert "InpExpectedServerMarker" in text
        assert 'ContainsText(server, "live")' in text
        assert 'ContainsText(server, "real")' in text
        assert 'input string InpExecutionKillSwitchFileName = "A3_EXECUTION_KILL.txt";' in text
        assert 'input string InpFullStopFileName = "A3_FULL_STOP.txt";' in text
        assert "FullStopActive()" in text
        assert "ExecutionKillSwitchActive()" in text
        assert "EXECUTION_KILL_SWITCH_BLOCK" in text
        assert 'guard_reason = "SCOPE_LOCK_BLOCK";' in text


def test_a3_t1_impulse_formula_and_logging_are_present():
    text = _text(EA_T1)

    assert "double Ret12Atr()" in text
    assert "double close_1 = iClose(_Symbol, PERIOD_M5, 1);" in text
    assert "double close_13 = iClose(_Symbol, PERIOD_M5, 13);" in text
    assert "return (close_1 - close_13) / atr14;" in text
    assert '"ret12_atr"' in text
    assert '"impulse_alignment"' in text
    assert "DoubleToString(ret12_atr, 6)" in text
    assert "DoubleToString(impulse_alignment, 6)" in text


def test_a3_t2_has_structure_filter_and_no_impulse_veto():
    text = _text(EA_T2)

    assert "STRUCT_FILTER_BLOCK" in text
    assert "A3StructureState" in text
    assert "ConfirmedM15SwingLevel" in text
    assert "StructuralConfirmation" in text
    assert '"structure_swing_bar_index"' in text
    assert '"structure_distance_from_level_points"' in text
    forbidden = ("VETO_IMPULSE", "InpImpulseVetoThreshold", "ret12_atr", "impulse_alignment")
    for token in forbidden:
        assert token not in text


def test_a3_required_reason_codes_present():
    t1 = _text(EA_T1)
    t2 = _text(EA_T2)

    for token in (
        "VETO_IMPULSE",
        "MUTEX_CLAIMED_ELSEWHERE",
        "STREAK_PAUSE",
        "DAILY_STOP_PAUSE",
        "SPREAD_CAP_BLOCK",
        "COST_R_CAP_BLOCK",
        "COST_WARN",
        "SCOPE_LOCK_BLOCK",
    ):
        assert token in t1

    for token in (
        "STRUCT_FILTER_BLOCK",
        "MUTEX_CLAIMED_ELSEWHERE",
        "STREAK_PAUSE",
        "DAILY_STOP_PAUSE",
        "SPREAD_CAP_BLOCK",
        "COST_R_CAP_BLOCK",
        "COST_WARN",
        "SCOPE_LOCK_BLOCK",
    ):
        assert token in t2


def test_a3_signal_rows_include_confluence_fields():
    for path in (EA_T1, EA_T2):
        text = _text(path)
        assert '"confluence_families"' in text
        assert '"confluence_count"' in text
        assert "ConfluenceFamiliesForSignal" in text
        assert "ConfluenceCountForSignal" in text


def test_a3_gv_mutex_claim_occurs_before_order_send():
    for path in (EA_T1, EA_T2):
        text = _text(path)
        claim = text.index("if(!ClaimMutexBeforeOrder(observation, mutex_name))")
        order_send = text.index("bool sent = OrderSend(request, result);")
        assert claim < order_send
        assert "GlobalVariableSetOnCondition" in text


def test_a3_executors_write_startup_gv_mutex_self_test_rows():
    cases = (
        (EA_T1, "FAMMUX_SELFTEST_RD_", "ATTACHED_A3_RDGUARD_V1"),
        (EA_T2, "FAMMUX_SELFTEST_RDSTRUCT_", "ATTACHED_A3_RDSTRUCT_V1"),
    )
    for path, prefix, attached_status in cases:
        text = _text(path)
        self_test_call = text.index("RunFamilyMutexNamespaceSelfTest(gv_mutex_self_test_status)")
        attached_row = text.index(f'WriteStartupRow("{attached_status}")')

        assert self_test_call < attached_row
        assert "RunFamilyMutexNamespaceSelfTest" in text
        assert prefix in text
        assert "GV_MUTEX_NAMESPACE_SELF_TEST_PASS" in text
        assert "GV_MUTEX_NAMESPACE_SELF_TEST_FAIL" in text
        assert "WriteStartupRow(gv_mutex_self_test_status);" in text
        assert "GlobalVariableSetOnCondition(test_name, (double)InpMagicNumber, 0.0)" in text


def test_a3_eas_have_no_position_management_or_order_deletion_calls():
    for path in (EA_T1, EA_T2):
        text = _text(path)
        for forbidden in ("PositionClose", "PositionModify", "OrderDelete"):
            assert forbidden not in text


def test_a3_eas_are_xauusd_only():
    for path in (EA_T1, EA_T2):
        text = _text(path)
        assert 'input string InpTargetSymbol = "XAUUSD";' in text
        assert '_Symbol != "XAUUSD" || InpTargetSymbol != "XAUUSD"' in text
        for forbidden_symbol in ("EURUSD", "GBPUSD", "USDJPY"):
            assert forbidden_symbol not in text


def test_a3_streak_daily_and_g5_constants_match_locked_parameters():
    for path in (EA_T1, EA_T2):
        text = _text(path)
        assert "input int InpStreakLossCount = 3;" in text
        assert "input int InpStreakWindowMinutes = 120;" in text
        assert "input double InpDailyLossStopAed = -150.0;" in text
        assert "input int InpMaxOpenPositionsPerMagic = 1;" in text
        assert "input double InpMaxEstimatedCostR = 0.15;" in text
        assert "input double InpCostWarnR = 0.20;" in text
        assert "input double InpAbsoluteRejectCostR = 0.30;" in text
        assert "input double InpMaxMeasuredSpreadPoints = 75.0;" in text
        assert "input int InpMinSecondsBetweenOrders = 60;" in text
        assert "input double InpFixedLot = 0.01;" in text


def test_a3_hypothesis_manifest_hashes_match_files():
    manifest = json.loads(_text(DOCS / "A3_HYPOTHESIS_HASH_MANIFEST.json"))

    assert manifest["locked_before_first_trade"] is True
    for row in manifest["hypotheses"]:
        path = ROOT.parents[1] / row["file"]
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        assert digest == row["sha256"]
