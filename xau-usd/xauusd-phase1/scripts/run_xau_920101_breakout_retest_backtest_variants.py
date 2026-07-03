from __future__ import annotations

import argparse
import csv
import html
import json
import re
import shutil
import subprocess
import time
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PHASE1_ROOT = Path(__file__).resolve().parents[1]
EA_NAME = "Phase2ExperimentalDemoExecutor"
EA_SOURCE = PHASE1_ROOT / "mt5" / "Experts" / f"{EA_NAME}.mq5"
INCLUDE_SOURCE = PHASE1_ROOT / "mt5" / "Include"
DEFAULT_BACKTEST_ROOT = Path("C:/MT5A1M5MomentumBacktest")
DEFAULT_METAEDITOR = Path("C:/Program Files/MetaTrader 5/MetaEditor64.exe")
DEFAULT_OUTPUT_DIR = PHASE1_ROOT / "outputs" / "reports" / "mt5_backtests"
DEFAULT_FROM_DATE = "2026.04.01"
DEFAULT_TO_DATE = "2026.06.30"
DEFAULT_TAG = "Q2_2026"


AUTH_TOKEN = "EXPERIMENTAL_DEMO_AUTHORIZED_REVIEW_ONLY"
COST_ACK = "I_ACKNOWLEDGE_COST_SUSPENDED_NON_CANONICAL_EXPERIMENT"


@dataclass(frozen=True)
class Variant:
    name: str
    label: str
    note: str
    tester_inputs: dict[str, str]


VARIANTS = [
    Variant(
        name="baseline_24h_no_smart",
        label="Raw 24h breakout-retest, no smart trend filter",
        note="Shows the unfiltered executor behavior before session/trend guards.",
        tester_inputs={
            "InpTradeSessionGateEnabled": "false",
            "InpSmartTrendFilterEnabled": "false",
            "InpMaxEstimatedCostR": "0.30",
        },
    ),
    Variant(
        name="current_24h_h1_smart",
        label="Current 24h H1 smart-trend guard",
        note="Matches the current A1/A2 24h experiment shape: H1 guard on, D1 not required, no session gate.",
        tester_inputs={
            "InpTradeSessionGateEnabled": "false",
            "InpSmartTrendFilterEnabled": "true",
            "InpSmartTrendFilterShadowOnly": "false",
            "InpSmartTrendRequireD1": "false",
            "InpSmartTrendRequireH1": "true",
            "InpSmartTrendMinH1Aligned": "0.15",
            "InpMaxEstimatedCostR": "0.30",
        },
    ),
    Variant(
        name="old_12_15_h1_smart",
        label="Prior 12->15 server-hour H1 guard",
        note="Represents the pre-24h locked forward-test lane.",
        tester_inputs={
            "InpTradeSessionGateEnabled": "true",
            "InpTradeSessionStartHour": "12",
            "InpTradeSessionEndHour": "15",
            "InpSmartTrendFilterEnabled": "true",
            "InpSmartTrendFilterShadowOnly": "false",
            "InpSmartTrendRequireD1": "false",
            "InpSmartTrendRequireH1": "true",
            "InpSmartTrendMinH1Aligned": "0.15",
            "InpMaxEstimatedCostR": "0.30",
        },
    ),
    Variant(
        name="server_06_11_h1_smart",
        label="Server 06->11 H1 guard",
        note="Session slice; server hours are used because the EA gate uses broker server time.",
        tester_inputs={
            "InpTradeSessionGateEnabled": "true",
            "InpTradeSessionStartHour": "6",
            "InpTradeSessionEndHour": "11",
            "InpSmartTrendFilterEnabled": "true",
            "InpSmartTrendFilterShadowOnly": "false",
            "InpSmartTrendRequireD1": "false",
            "InpSmartTrendRequireH1": "true",
            "InpSmartTrendMinH1Aligned": "0.15",
            "InpMaxEstimatedCostR": "0.30",
        },
    ),
    Variant(
        name="server_12_15_h1_smart",
        label="Server 12->15 H1 guard",
        note="Same hours as the old forward-test lane, retained as a named session slice.",
        tester_inputs={
            "InpTradeSessionGateEnabled": "true",
            "InpTradeSessionStartHour": "12",
            "InpTradeSessionEndHour": "15",
            "InpSmartTrendFilterEnabled": "true",
            "InpSmartTrendFilterShadowOnly": "false",
            "InpSmartTrendRequireD1": "false",
            "InpSmartTrendRequireH1": "true",
            "InpSmartTrendMinH1Aligned": "0.15",
            "InpMaxEstimatedCostR": "0.30",
        },
    ),
    Variant(
        name="server_16_19_h1_smart",
        label="Server 16->19 H1 guard",
        note="Session slice; tests whether later server evening is cleaner than the old 12->15 lane.",
        tester_inputs={
            "InpTradeSessionGateEnabled": "true",
            "InpTradeSessionStartHour": "16",
            "InpTradeSessionEndHour": "19",
            "InpSmartTrendFilterEnabled": "true",
            "InpSmartTrendFilterShadowOnly": "false",
            "InpSmartTrendRequireD1": "false",
            "InpSmartTrendRequireH1": "true",
            "InpSmartTrendMinH1Aligned": "0.15",
            "InpMaxEstimatedCostR": "0.30",
        },
    ),
    Variant(
        name="server_20_05_h1_smart",
        label="Server 20->05 H1 guard",
        note="Overnight server-hour wraparound slice.",
        tester_inputs={
            "InpTradeSessionGateEnabled": "true",
            "InpTradeSessionStartHour": "20",
            "InpTradeSessionEndHour": "5",
            "InpSmartTrendFilterEnabled": "true",
            "InpSmartTrendFilterShadowOnly": "false",
            "InpSmartTrendRequireD1": "false",
            "InpSmartTrendRequireH1": "true",
            "InpSmartTrendMinH1Aligned": "0.15",
            "InpMaxEstimatedCostR": "0.30",
        },
    ),
    Variant(
        name="h1_d1_24h_smart",
        label="24h D1+H1 smart-trend guard",
        note="Stricter trend agreement test; historically D1 was too strict, but this reruns it on MT5 tester data.",
        tester_inputs={
            "InpTradeSessionGateEnabled": "false",
            "InpSmartTrendFilterEnabled": "true",
            "InpSmartTrendFilterShadowOnly": "false",
            "InpSmartTrendRequireD1": "true",
            "InpSmartTrendRequireH1": "true",
            "InpSmartTrendMinD1Aligned": "0.25",
            "InpSmartTrendMinH1Aligned": "0.15",
            "InpMaxEstimatedCostR": "0.30",
        },
    ),
    Variant(
        name="current_24h_h1_cost015",
        label="24h H1 guard with stricter cost_R <= 0.15",
        note="Cost-discipline variant; checks whether tight/high-cost trades are the damage source.",
        tester_inputs={
            "InpTradeSessionGateEnabled": "false",
            "InpSmartTrendFilterEnabled": "true",
            "InpSmartTrendFilterShadowOnly": "false",
            "InpSmartTrendRequireD1": "false",
            "InpSmartTrendRequireH1": "true",
            "InpSmartTrendMinH1Aligned": "0.15",
            "InpMaxEstimatedCostR": "0.15",
        },
    ),
    Variant(
        name="current_24h_h1_cost010",
        label="24h H1 guard with strict cost_R <= 0.10",
        note="Very strict cost filter; useful as diagnosis, not an automatic promotion candidate.",
        tester_inputs={
            "InpTradeSessionGateEnabled": "false",
            "InpSmartTrendFilterEnabled": "true",
            "InpSmartTrendFilterShadowOnly": "false",
            "InpSmartTrendRequireD1": "false",
            "InpSmartTrendRequireH1": "true",
            "InpSmartTrendMinH1Aligned": "0.15",
            "InpMaxEstimatedCostR": "0.10",
        },
    ),
    Variant(
        name="repair_24h_h1_faststop_min800",
        label="24h H1 guard + fast-stopout repair",
        note="Blocks tight/weak-confirmation entries: stop >=800pt, confirmation body/range >=0.35, directional close location >=0.60.",
        tester_inputs={
            "InpTradeSessionGateEnabled": "false",
            "InpSmartTrendFilterEnabled": "true",
            "InpSmartTrendFilterShadowOnly": "false",
            "InpSmartTrendRequireD1": "false",
            "InpSmartTrendRequireH1": "true",
            "InpSmartTrendMinH1Aligned": "0.15",
            "InpMaxEstimatedCostR": "0.30",
            "InpFastStopoutFilterEnabled": "true",
            "InpFastStopoutFilterShadowOnly": "false",
            "InpFastStopoutMinStopPoints": "800.0",
            "InpFastStopoutMinConfirmationBodyRange": "0.35",
            "InpFastStopoutMinCloseLocation": "0.60",
        },
    ),
    Variant(
        name="repair_24h_h1_faststop_min1200",
        label="24h H1 guard + strict fast-stopout repair",
        note="Same repair, but requires stop >=1200pt because the Q2 bucket below 1200pt was weak.",
        tester_inputs={
            "InpTradeSessionGateEnabled": "false",
            "InpSmartTrendFilterEnabled": "true",
            "InpSmartTrendFilterShadowOnly": "false",
            "InpSmartTrendRequireD1": "false",
            "InpSmartTrendRequireH1": "true",
            "InpSmartTrendMinH1Aligned": "0.15",
            "InpMaxEstimatedCostR": "0.30",
            "InpFastStopoutFilterEnabled": "true",
            "InpFastStopoutFilterShadowOnly": "false",
            "InpFastStopoutMinStopPoints": "1200.0",
            "InpFastStopoutMinConfirmationBodyRange": "0.35",
            "InpFastStopoutMinCloseLocation": "0.60",
        },
    ),
    Variant(
        name="repair_16_19_h1_faststop_min800",
        label="Server 16->19 H1 guard + fast-stopout repair",
        note="Applies the same repair only inside the previously strongest server-hour slice.",
        tester_inputs={
            "InpTradeSessionGateEnabled": "true",
            "InpTradeSessionStartHour": "16",
            "InpTradeSessionEndHour": "19",
            "InpSmartTrendFilterEnabled": "true",
            "InpSmartTrendFilterShadowOnly": "false",
            "InpSmartTrendRequireD1": "false",
            "InpSmartTrendRequireH1": "true",
            "InpSmartTrendMinH1Aligned": "0.15",
            "InpMaxEstimatedCostR": "0.30",
            "InpFastStopoutFilterEnabled": "true",
            "InpFastStopoutFilterShadowOnly": "false",
            "InpFastStopoutMinStopPoints": "800.0",
            "InpFastStopoutMinConfirmationBodyRange": "0.35",
            "InpFastStopoutMinCloseLocation": "0.60",
        },
    ),
    Variant(
        name="protect_current_24h_h1_lock125_080",
        label="Current 24h H1 guard + profit lock",
        note="No entry repair. Moves SL to +0.80R after +1.25R to measure pure giveback control.",
        tester_inputs={
            "InpTradeSessionGateEnabled": "false",
            "InpSmartTrendFilterEnabled": "true",
            "InpSmartTrendFilterShadowOnly": "false",
            "InpSmartTrendRequireD1": "false",
            "InpSmartTrendRequireH1": "true",
            "InpSmartTrendMinH1Aligned": "0.15",
            "InpMaxEstimatedCostR": "0.30",
            "InpProfitProtectionEnabled": "true",
            "InpProfitProtectionShadowOnly": "false",
            "InpProfitProtectionTriggerR": "1.25",
            "InpProfitProtectionLockR": "0.80",
        },
    ),
    Variant(
        name="repair_24h_h1_faststop_min800_lock125_080",
        label="Fast-stopout repair + late profit lock",
        note="Best entry repair plus conservative profit lock: arm at +1.25R, move SL to +0.80R.",
        tester_inputs={
            "InpTradeSessionGateEnabled": "false",
            "InpSmartTrendFilterEnabled": "true",
            "InpSmartTrendFilterShadowOnly": "false",
            "InpSmartTrendRequireD1": "false",
            "InpSmartTrendRequireH1": "true",
            "InpSmartTrendMinH1Aligned": "0.15",
            "InpMaxEstimatedCostR": "0.30",
            "InpFastStopoutFilterEnabled": "true",
            "InpFastStopoutFilterShadowOnly": "false",
            "InpFastStopoutMinStopPoints": "800.0",
            "InpFastStopoutMinConfirmationBodyRange": "0.35",
            "InpFastStopoutMinCloseLocation": "0.60",
            "InpProfitProtectionEnabled": "true",
            "InpProfitProtectionShadowOnly": "false",
            "InpProfitProtectionTriggerR": "1.25",
            "InpProfitProtectionLockR": "0.80",
        },
    ),
    Variant(
        name="repair_24h_h1_faststop_min800_lock100_050",
        label="Fast-stopout repair + earlier profit lock",
        note="Best entry repair plus earlier lock: arm at +1.00R, move SL to +0.50R.",
        tester_inputs={
            "InpTradeSessionGateEnabled": "false",
            "InpSmartTrendFilterEnabled": "true",
            "InpSmartTrendFilterShadowOnly": "false",
            "InpSmartTrendRequireD1": "false",
            "InpSmartTrendRequireH1": "true",
            "InpSmartTrendMinH1Aligned": "0.15",
            "InpMaxEstimatedCostR": "0.30",
            "InpFastStopoutFilterEnabled": "true",
            "InpFastStopoutFilterShadowOnly": "false",
            "InpFastStopoutMinStopPoints": "800.0",
            "InpFastStopoutMinConfirmationBodyRange": "0.35",
            "InpFastStopoutMinCloseLocation": "0.60",
            "InpProfitProtectionEnabled": "true",
            "InpProfitProtectionShadowOnly": "false",
            "InpProfitProtectionTriggerR": "1.00",
            "InpProfitProtectionLockR": "0.50",
        },
    ),
    Variant(
        name="revise_short_24h_h1_faststop_min800_lock100_050",
        label="Revised short-only 24h fast-stopout + profit lock",
        note="Claude revise candidate: drops weak long side while keeping the same H1, fast-stopout, and profit-protection rules.",
        tester_inputs={
            "InpTradeSessionGateEnabled": "false",
            "InpDirectionMode": "SHORT_ONLY",
            "InpSmartTrendFilterEnabled": "true",
            "InpSmartTrendFilterShadowOnly": "false",
            "InpSmartTrendRequireD1": "false",
            "InpSmartTrendRequireH1": "true",
            "InpSmartTrendMinH1Aligned": "0.15",
            "InpMaxEstimatedCostR": "0.30",
            "InpFastStopoutFilterEnabled": "true",
            "InpFastStopoutFilterShadowOnly": "false",
            "InpFastStopoutMinStopPoints": "800.0",
            "InpFastStopoutMinConfirmationBodyRange": "0.35",
            "InpFastStopoutMinCloseLocation": "0.60",
            "InpProfitProtectionEnabled": "true",
            "InpProfitProtectionShadowOnly": "false",
            "InpProfitProtectionTriggerR": "1.00",
            "InpProfitProtectionLockR": "0.50",
        },
    ),
    Variant(
        name="revise_short_20_11_h1_faststop_min800_lock100_050",
        label="Revised short-only night+morning fast-stopout + profit lock",
        note="Drops the breakeven afternoon and tiny evening sample; tests only server 20->11 short signals.",
        tester_inputs={
            "InpTradeSessionGateEnabled": "true",
            "InpTradeSessionStartHour": "20",
            "InpTradeSessionEndHour": "11",
            "InpDirectionMode": "SHORT_ONLY",
            "InpSmartTrendFilterEnabled": "true",
            "InpSmartTrendFilterShadowOnly": "false",
            "InpSmartTrendRequireD1": "false",
            "InpSmartTrendRequireH1": "true",
            "InpSmartTrendMinH1Aligned": "0.15",
            "InpMaxEstimatedCostR": "0.30",
            "InpFastStopoutFilterEnabled": "true",
            "InpFastStopoutFilterShadowOnly": "false",
            "InpFastStopoutMinStopPoints": "800.0",
            "InpFastStopoutMinConfirmationBodyRange": "0.35",
            "InpFastStopoutMinCloseLocation": "0.60",
            "InpProfitProtectionEnabled": "true",
            "InpProfitProtectionShadowOnly": "false",
            "InpProfitProtectionTriggerR": "1.00",
            "InpProfitProtectionLockR": "0.50",
        },
    ),
    Variant(
        name="revise_short_06_11_h1_faststop_min800_lock100_050",
        label="Revised short-only morning fast-stopout + profit lock",
        note="Tests the clean morning pocket alone; expected to be lower frequency.",
        tester_inputs={
            "InpTradeSessionGateEnabled": "true",
            "InpTradeSessionStartHour": "6",
            "InpTradeSessionEndHour": "11",
            "InpDirectionMode": "SHORT_ONLY",
            "InpSmartTrendFilterEnabled": "true",
            "InpSmartTrendFilterShadowOnly": "false",
            "InpSmartTrendRequireD1": "false",
            "InpSmartTrendRequireH1": "true",
            "InpSmartTrendMinH1Aligned": "0.15",
            "InpMaxEstimatedCostR": "0.30",
            "InpFastStopoutFilterEnabled": "true",
            "InpFastStopoutFilterShadowOnly": "false",
            "InpFastStopoutMinStopPoints": "800.0",
            "InpFastStopoutMinConfirmationBodyRange": "0.35",
            "InpFastStopoutMinCloseLocation": "0.60",
            "InpProfitProtectionEnabled": "true",
            "InpProfitProtectionShadowOnly": "false",
            "InpProfitProtectionTriggerR": "1.00",
            "InpProfitProtectionLockR": "0.50",
        },
    ),
    Variant(
        name="revise_short_20_05_h1_faststop_min800_lock100_050",
        label="Revised short-only night fast-stopout + profit lock",
        note="Tests whether the night carry survives as a standalone short-only pocket.",
        tester_inputs={
            "InpTradeSessionGateEnabled": "true",
            "InpTradeSessionStartHour": "20",
            "InpTradeSessionEndHour": "5",
            "InpDirectionMode": "SHORT_ONLY",
            "InpSmartTrendFilterEnabled": "true",
            "InpSmartTrendFilterShadowOnly": "false",
            "InpSmartTrendRequireD1": "false",
            "InpSmartTrendRequireH1": "true",
            "InpSmartTrendMinH1Aligned": "0.15",
            "InpMaxEstimatedCostR": "0.30",
            "InpFastStopoutFilterEnabled": "true",
            "InpFastStopoutFilterShadowOnly": "false",
            "InpFastStopoutMinStopPoints": "800.0",
            "InpFastStopoutMinConfirmationBodyRange": "0.35",
            "InpFastStopoutMinCloseLocation": "0.60",
            "InpProfitProtectionEnabled": "true",
            "InpProfitProtectionShadowOnly": "false",
            "InpProfitProtectionTriggerR": "1.00",
            "InpProfitProtectionLockR": "0.50",
        },
    ),
    Variant(
        name="repair_24h_h1_faststop_min800_be075",
        label="Fast-stopout repair + early break-even",
        note="Best entry repair plus early break-even: arm at +0.75R, move SL to entry.",
        tester_inputs={
            "InpTradeSessionGateEnabled": "false",
            "InpSmartTrendFilterEnabled": "true",
            "InpSmartTrendFilterShadowOnly": "false",
            "InpSmartTrendRequireD1": "false",
            "InpSmartTrendRequireH1": "true",
            "InpSmartTrendMinH1Aligned": "0.15",
            "InpMaxEstimatedCostR": "0.30",
            "InpFastStopoutFilterEnabled": "true",
            "InpFastStopoutFilterShadowOnly": "false",
            "InpFastStopoutMinStopPoints": "800.0",
            "InpFastStopoutMinConfirmationBodyRange": "0.35",
            "InpFastStopoutMinCloseLocation": "0.60",
            "InpProfitProtectionEnabled": "true",
            "InpProfitProtectionShadowOnly": "false",
            "InpProfitProtectionTriggerR": "0.75",
            "InpProfitProtectionLockR": "0.00",
        },
    ),
]


COMMON_TESTER_INPUTS = {
    "InpRunId": "BT_XAU_920101_BR_Q2_2026",
    "InpDryRunOnly": "false",
    "InpBrokerActionAllowed": "true",
    "InpCandidate": "breakout_retest",
    "InpCandidateStatus": "EXPERIMENTAL_QUARANTINE_REVIEW_ONLY",
    "InpFamilyLifecycleStatus": "COST_SUSPENDED_CANONICAL",
    "InpTargetSymbol": "XAUUSD",
    "InpQualifiedSymbolsCsv": "XAUUSD",
    "InpExpectedServerMarker": "Demo",
    "InpAllowedAccountLoginsCsv": "1025742",
    "InpExperimentalAuthorizationToken": AUTH_TOKEN,
    "InpRequiredExperimentalAuthorizationToken": AUTH_TOKEN,
    "InpCostSuspensionAcknowledgementToken": COST_ACK,
    "InpRequiredCostSuspensionAcknowledgementToken": COST_ACK,
    "InpAuthorizedCandidatesCsv": "breakout_retest",
    "InpDirectionStateFileName": "bt_xau_920101_direction_state.csv",
    "InpKillSwitchFileName": "nonexistent_bt_xau_920101_kill_switch.txt",
    "InpFixedLot": "0.01",
    "InpEURUSDFixedLot": "0.01",
    "InpGBPUSDFixedLot": "0.01",
    "InpMaxOrdersPerDay": "0",
    "InpMaxAccountOrdersPerDay": "0",
    "InpMinSecondsBetweenOrders": "60",
    "InpMaxOpenPositionsPerInstance": "1",
    "InpMaxOpenPositionsPerMagic": "1",
    "InpDeviationPoints": "50",
    "InpMaxEstimatedCostR": "0.30",
    "InpMaxMeasuredSpreadPoints": "75.0",
    "InpTradeSessionGateEnabled": "false",
    "InpTradeSessionStartHour": "0",
    "InpTradeSessionEndHour": "23",
    "InpSmartTrendFilterEnabled": "false",
    "InpSmartTrendFilterShadowOnly": "false",
    "InpSmartTrendD1LagBars": "5",
    "InpSmartTrendH1LagBars": "3",
    "InpSmartTrendRequireD1": "false",
    "InpSmartTrendRequireH1": "true",
    "InpSmartTrendMinD1Aligned": "0.25",
    "InpSmartTrendMinH1Aligned": "0.15",
    "InpFastStopoutFilterEnabled": "false",
    "InpFastStopoutFilterShadowOnly": "true",
    "InpFastStopoutMinStopPoints": "0.0",
    "InpFastStopoutMinConfirmationBodyRange": "0.0",
    "InpFastStopoutMinCloseLocation": "0.0",
    "InpProfitProtectionEnabled": "false",
    "InpProfitProtectionShadowOnly": "true",
    "InpProfitProtectionTriggerR": "1.25",
    "InpProfitProtectionLockR": "0.80",
    "InpDirectionMode": "BOTH",
}


def run_variants(
    backtest_root: Path = DEFAULT_BACKTEST_ROOT,
    metaeditor: Path = DEFAULT_METAEDITOR,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    from_date: str = DEFAULT_FROM_DATE,
    to_date: str = DEFAULT_TO_DATE,
    tag: str = DEFAULT_TAG,
    report_md: Path | None = None,
    report_json: Path | None = None,
    variant_names: set[str] | None = None,
    variant_timeout_seconds: int = 180,
    deposit: str = "1808.13",
    currency: str = "AED",
) -> dict[str, Any]:
    backtest_root = backtest_root.resolve()
    output_dir = output_dir.resolve()
    terminal = backtest_root / "terminal64.exe"
    require_file(EA_SOURCE)
    require_file(INCLUDE_SOURCE)
    require_file(terminal)
    require_file(metaeditor)

    compile_log = compile_ea(backtest_root, metaeditor)
    safe_tag = safe_name(tag)
    run_stamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    variant_dir = output_dir / f"xau_920101_breakout_retest_{safe_tag.lower()}_{run_stamp}"
    variant_dir.mkdir(parents=True, exist_ok=True)

    selected_variants = [variant for variant in VARIANTS if variant_names is None or variant.name in variant_names]
    if not selected_variants:
        available = ", ".join(variant.name for variant in VARIANTS)
        raise ValueError(f"No variants selected. Available variants: {available}")

    results = []
    for variant in selected_variants:
        results.append(
            run_variant(
                backtest_root,
                terminal,
                variant,
                variant_dir,
                from_date,
                to_date,
                safe_tag,
                variant_timeout_seconds,
                deposit,
                currency,
            )
        )

    report_md = report_md or PHASE1_ROOT / "outputs" / "reports" / f"XAU_920101_BREAKOUT_RETEST_VARIANT_BACKTEST_{safe_tag}.md"
    report_json = report_json or report_md.with_suffix(".json")
    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "scope": {
            "ea": EA_NAME,
            "symbol": "XAUUSD",
            "candidate": "breakout_retest",
            "timeframe": "M5",
            "period": f"{from_date} -> {to_date}",
            "account_context": "1025742 / Capital.ComMena-Demo",
            "tester_deposit": deposit,
            "tester_currency": currency,
            "terminal_sandbox": str(backtest_root),
            "model": "MT5 Strategy Tester / every tick / history quality from report",
            "no_live_runtime_change": True,
            "variant_count": len(selected_variants),
            "selected_variants": [variant.name for variant in selected_variants],
            "variant_timeout_seconds": variant_timeout_seconds,
            "anti_overfit_boundary": "Fixed session/smart-trend/cost variants only; no parameter optimizer or threshold sweep.",
        },
        "compile_log": str(compile_log),
        "variants": results,
        "winner": choose_winner(results),
    }
    report_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    report_md.write_text(render_markdown(payload), encoding="utf-8")
    return payload


def compile_ea(backtest_root: Path, metaeditor: Path) -> Path:
    mql5_root = backtest_root / "MQL5"
    experts = mql5_root / "Experts"
    include_target = mql5_root / "Include"
    experts.mkdir(parents=True, exist_ok=True)
    include_target.mkdir(parents=True, exist_ok=True)
    shutil.copy2(EA_SOURCE, experts / f"{EA_NAME}.mq5")
    copy_include_tree(INCLUDE_SOURCE, include_target)
    log = backtest_root / "Logs" / f"compile_{EA_NAME}_xau_920101_backtest_20260701.log"
    log.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [str(metaeditor), f"/compile:{experts / f'{EA_NAME}.mq5'}", f"/log:{log}"],
        text=True,
        capture_output=True,
        timeout=120,
        check=False,
    )
    ex5 = experts / f"{EA_NAME}.ex5"
    if not ex5.exists():
        raise RuntimeError(f"MetaEditor did not produce EX5. Log:\n{read_text(log)}")
    log_text = read_text(log).lower()
    if "error(s)" in log_text and "0 error(s)" not in log_text:
        raise RuntimeError(f"MetaEditor compile reported errors:\n{read_text(log)}")
    return log


def copy_include_tree(source: Path, target: Path) -> None:
    for path in source.rglob("*"):
        if not path.is_file():
            continue
        relative = path.relative_to(source)
        destination = target / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, destination)


def run_variant(
    backtest_root: Path,
    terminal: Path,
    variant: Variant,
    variant_dir: Path,
    from_date: str,
    to_date: str,
    tag: str,
    timeout_seconds: int = 180,
    deposit: str = "1808.13",
    currency: str = "AED",
) -> dict[str, Any]:
    report_base = f"XAU920101BreakoutRetest_{tag}_M5_{variant.name}"
    startup_log = f"xau_920101_bt_{variant.name}_startup.csv"
    signal_log = f"xau_920101_bt_{variant.name}_signal.csv"
    order_log = f"xau_920101_bt_{variant.name}_order.csv"
    management_log = f"xau_920101_bt_{variant.name}_management.csv"
    config = write_config(
        backtest_root,
        variant,
        report_base,
        startup_log,
        signal_log,
        order_log,
        management_log,
        from_date,
        to_date,
        tag,
        deposit,
        currency,
    )
    remove_old_variant_files(backtest_root, report_base, startup_log, signal_log, order_log, management_log)
    stop_backtest_terminal(terminal)
    proc = subprocess.Popen(
        [str(terminal), "/portable", f"/config:{config}"],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    html_report = backtest_root / "Reports" / f"{report_base}.htm"
    wait_for_file(html_report, timeout_seconds=timeout_seconds)
    time.sleep(2)
    stop_backtest_terminal(terminal)
    stdout_tail = ""
    stderr_tail = ""
    returncode = None
    try:
        stdout, stderr = proc.communicate(timeout=5)
        stdout_tail = stdout[-1000:] if stdout else ""
        stderr_tail = stderr[-1000:] if stderr else ""
        returncode = proc.returncode
    except subprocess.TimeoutExpired:
        proc.kill()
        stdout, stderr = proc.communicate(timeout=5)
        stdout_tail = stdout[-1000:] if stdout else ""
        stderr_tail = stderr[-1000:] if stderr else ""
        returncode = proc.returncode
    trades, metrics = parse_mt5_report(html_report)
    orders = read_order_rows(backtest_root, order_log)
    management = read_log_rows(backtest_root, management_log)
    summary = summarize_trades(trades)
    order_summary = summarize_orders(orders)
    management_summary = summarize_management(management)

    trade_csv = variant_dir / f"{report_base}_trades.csv"
    order_csv = variant_dir / f"{report_base}_orders.csv"
    management_csv = variant_dir / f"{report_base}_management.csv"
    summary_json = variant_dir / f"{report_base}_summary.json"
    write_dict_rows(trade_csv, trades)
    write_dict_rows(order_csv, orders)
    write_dict_rows(management_csv, management)
    result = {
        "name": variant.name,
        "label": variant.label,
        "note": variant.note,
        "tester_inputs": {**COMMON_TESTER_INPUTS, **variant.tester_inputs},
        "config": str(config),
        "html_report": str(html_report),
        "trade_csv": str(trade_csv),
        "order_csv": str(order_csv),
        "management_csv": str(management_csv),
        "summary_json": str(summary_json),
        "mt5_report_metrics": metrics,
        "summary": summary,
        "order_activity": order_summary,
        "management_activity": management_summary,
        "terminal_returncode": returncode,
        "terminal_stdout_tail": stdout_tail,
        "terminal_stderr_tail": stderr_tail,
    }
    summary_json.write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result


def stop_backtest_terminal(terminal: Path) -> None:
    terminal_text = str(terminal).replace("'", "''")
    command = (
        "Get-Process terminal64 -ErrorAction SilentlyContinue | "
        f"Where-Object {{$_.Path -eq '{terminal_text}'}} | "
        "Stop-Process -Force"
    )
    subprocess.run(
        ["powershell", "-NoProfile", "-Command", command],
        text=True,
        capture_output=True,
        timeout=20,
        check=False,
    )


def write_config(
    backtest_root: Path,
    variant: Variant,
    report_base: str,
    startup_log: str,
    signal_log: str,
    order_log: str,
    management_log: str,
    from_date: str,
    to_date: str,
    tag: str,
    deposit: str = "1808.13",
    currency: str = "AED",
) -> Path:
    inputs = {
        **COMMON_TESTER_INPUTS,
        **variant.tester_inputs,
        "InpRunId": f"BT_XAU_920101_BR_{safe_name(tag)}_{variant.name.upper()}",
        "InpAttachmentLogFileName": signal_log,
        "InpStartupLogFileName": startup_log,
        "InpOrderLogFileName": order_log,
        "InpManagementLogFileName": management_log,
    }
    lines = [
        "[Common]",
        "Login=1025742",
        "Server=Capital.ComMena-Demo",
        "KeepPrivate=1",
        "NewsEnable=0",
        "",
        "[Tester]",
        f"Expert={EA_NAME}.ex5",
        "Symbol=XAUUSD",
        "Period=M5",
        "Optimization=0",
        "Model=0",
        "Dates=2",
        f"FromDate={from_date}",
        f"ToDate={to_date}",
        "ForwardMode=0",
        f"Deposit={deposit}",
        f"Currency={currency}",
        "ProfitInPips=0",
        "Leverage=200",
        "ExecutionMode=0",
        "OptimizationCriterion=0",
        "Visual=0",
        f"Report=Reports\\{report_base}",
        "ReplaceReport=1",
        "ShutdownTerminal=1",
        "UseLocal=1",
        "UseRemote=0",
        "UseCloud=0",
        "",
        "[TesterInputs]",
    ]
    lines.extend(f"{key}={value}" for key, value in inputs.items())
    config = backtest_root / "Config" / f"{report_base}.ini"
    config.parent.mkdir(parents=True, exist_ok=True)
    config.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return config


def remove_old_variant_files(backtest_root: Path, report_base: str, *log_names: str) -> None:
    for suffix in [".htm", ".png", "-holding.png", "-mfemae.png", "-hst.png"]:
        path = backtest_root / "Reports" / f"{report_base}{suffix}"
        if path.exists():
            path.unlink()
    files_root = backtest_root / "Tester" / "Agent-127.0.0.1-3000" / "MQL5" / "Files"
    for name in log_names:
        path = files_root / name
        if path.exists():
            path.unlink()


def parse_mt5_report(path: Path) -> tuple[list[dict[str, Any]], dict[str, str]]:
    text = read_text(path)
    rows = []
    for match in re.finditer(r"<tr[^>]*>(.*?)</tr>", text, flags=re.I | re.S):
        cells = re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", match.group(1), flags=re.I | re.S)
        cleaned = [html.unescape(re.sub(r"<[^>]+>", "", cell)).strip().replace("\xa0", " ") for cell in cells]
        if cleaned:
            rows.append(cleaned)

    metrics = parse_metrics(rows)
    trades = []
    open_trade: dict[str, Any] | None = None
    for cells in rows:
        if len(cells) < 13 or cells[2] != "XAUUSD" or cells[4] not in {"in", "out"}:
            continue
        try:
            deal_time = datetime.strptime(cells[0], "%Y.%m.%d %H:%M:%S")
            profit = float(cells[10].replace(" ", ""))
            balance = float(cells[11].replace(" ", ""))
        except ValueError:
            continue
        deal_type = cells[3].lower()
        if cells[4] == "in":
            open_trade = {
                "entry_time": cells[0],
                "entry_date": deal_time.date().isoformat(),
                "entry_hour": deal_time.hour,
                "entry_session": server_session(deal_time.hour),
                "direction": "LONG" if deal_type == "buy" else "SHORT",
                "entry_deal": cells[1],
                "volume": cells[5],
                "entry_price": cells[6],
                "entry_comment": cells[12],
            }
            continue
        if open_trade is None:
            continue
        trade = {
            **open_trade,
            "exit_time": cells[0],
            "exit_date": deal_time.date().isoformat(),
            "exit_hour": deal_time.hour,
            "exit_session": server_session(deal_time.hour),
            "date": open_trade["entry_date"],
            "hour": open_trade["entry_hour"],
            "session": open_trade["entry_session"],
            "exit_deal": cells[1],
            "exit_price": cells[6],
            "profit_aed": profit,
            "balance": balance,
            "exit_comment": cells[12],
        }
        trades.append(trade)
        open_trade = None
    return trades, metrics


def parse_metrics(rows: list[list[str]]) -> dict[str, str]:
    flat = [cell for row in rows for cell in row]
    labels = [
        "History Quality:",
        "Bars:",
        "Ticks:",
        "Total Net Profit:",
        "Gross Profit:",
        "Gross Loss:",
        "Profit Factor:",
        "Expected Payoff:",
        "Recovery Factor:",
        "Sharpe Ratio:",
        "Total Trades:",
        "Short Trades (won %):",
        "Long Trades (won %):",
        "Profit Trades (% of total):",
        "Loss Trades (% of total):",
        "Total Deals:",
        "Balance Drawdown Maximal:",
        "Equity Drawdown Maximal:",
        "Balance Drawdown Relative:",
        "Equity Drawdown Relative:",
    ]
    metrics = {}
    for idx, cell in enumerate(flat):
        if cell in labels and idx + 1 < len(flat):
            metrics[cell.rstrip(":")] = flat[idx + 1]
    return metrics


def read_log_rows(backtest_root: Path, log_name: str) -> list[dict[str, str]]:
    path = backtest_root / "Tester" / "Agent-127.0.0.1-3000" / "MQL5" / "Files" / log_name
    if not path.exists():
        return []
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def read_order_rows(backtest_root: Path, order_log: str) -> list[dict[str, str]]:
    return read_log_rows(backtest_root, order_log)


def summarize_orders(rows: list[dict[str, str]]) -> dict[str, Any]:
    action_counts = Counter(row.get("action", "") for row in rows)
    guard_counts = Counter(row.get("guard_reason", "") for row in rows if row.get("action") == "GUARD_BLOCK")
    signal_reason_counts = Counter(row.get("signal_reason", "") for row in rows)
    return {
        "rows": len(rows),
        "actions": dict(action_counts.most_common()),
        "top_guard_reasons": dict(guard_counts.most_common(12)),
        "top_signal_reasons": dict(signal_reason_counts.most_common(12)),
    }


def summarize_management(rows: list[dict[str, str]]) -> dict[str, Any]:
    action_counts = Counter(row.get("action", "") for row in rows)
    sent_rows = [
        row
        for row in rows
        if row.get("action") in {"PROFIT_PROTECTION_SLTP_SENT", "PROFIT_PROTECTION_SHADOW_WOULD_MOVE_SL"}
    ]
    return {
        "rows": len(rows),
        "actions": dict(action_counts.most_common()),
        "profit_protection_moves": len(sent_rows),
    }


def write_dict_rows(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fieldnames: list[str] = []
    for row in rows:
        for key in row:
            if key not in fieldnames:
                fieldnames.append(key)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def summarize_trades(trades: list[dict[str, Any]]) -> dict[str, Any]:
    summary = {"overall": aggregate(trades)}
    for key in ["direction", "session", "date", "hour"]:
        grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for trade in trades:
            grouped[str(trade[key])].append(trade)
        summary[key] = {name: aggregate(items) for name, items in sorted(grouped.items())}
    summary["robustness"] = robustness(trades)
    return summary


def aggregate(trades: list[dict[str, Any]]) -> dict[str, Any]:
    count = len(trades)
    wins = sum(1 for trade in trades if trade["profit_aed"] > 0)
    losses = sum(1 for trade in trades if trade["profit_aed"] < 0)
    gross_profit = sum(trade["profit_aed"] for trade in trades if trade["profit_aed"] > 0)
    gross_loss = -sum(trade["profit_aed"] for trade in trades if trade["profit_aed"] < 0)
    pnl = gross_profit - gross_loss
    return {
        "trades": count,
        "wins": wins,
        "losses": losses,
        "win_rate_pct": round((wins / count) * 100, 2) if count else 0.0,
        "pnl_aed": round(pnl, 2),
        "gross_profit": round(gross_profit, 2),
        "gross_loss": round(gross_loss, 2),
        "profit_factor": round(gross_profit / gross_loss, 2) if gross_loss else None,
        "avg_pnl_aed": round(pnl / count, 2) if count else 0.0,
    }


def robustness(trades: list[dict[str, Any]]) -> dict[str, Any]:
    if not trades:
        return {"top3_removed_pnl_aed": 0.0, "worst_day_pnl_aed": 0.0, "max_trade_contribution_pct": 0.0}
    pnl = sum(float(trade["profit_aed"]) for trade in trades)
    winners = sorted((float(trade["profit_aed"]) for trade in trades if float(trade["profit_aed"]) > 0), reverse=True)
    top3_removed = pnl - sum(winners[:3])
    by_day: dict[str, float] = defaultdict(float)
    for trade in trades:
        by_day[str(trade["date"])] += float(trade["profit_aed"])
    worst_day = min(by_day.values()) if by_day else 0.0
    max_win = winners[0] if winners else 0.0
    contribution = (max_win / pnl * 100.0) if pnl > 0 else 0.0
    return {
        "top3_removed_pnl_aed": round(top3_removed, 2),
        "worst_day_pnl_aed": round(worst_day, 2),
        "max_trade_contribution_pct": round(contribution, 2),
    }


def choose_winner(results: list[dict[str, Any]]) -> dict[str, Any]:
    viable = []
    for result in results:
        overall = result["summary"]["overall"]
        robustness_data = result["summary"]["robustness"]
        if (
            overall["trades"] >= 30
            and overall["pnl_aed"] > 0
            and (overall["profit_factor"] or 0) >= 1.25
            and overall["win_rate_pct"] >= 50.0
            and robustness_data["top3_removed_pnl_aed"] > 0
        ):
            viable.append(result)
    if not viable:
        best = max(results, key=lambda item: item["summary"]["overall"]["pnl_aed"])
        return {
            "status": "NO_VARIANT_CLEARS_DIAGNOSTIC_BAR",
            "best_by_pnl": best["name"],
            "note": "No variant cleared the fixed diagnostic bar. Treat the best row as a clue, not an approval.",
        }
    best = max(viable, key=lambda item: ((item["summary"]["overall"]["profit_factor"] or 0), item["summary"]["overall"]["pnl_aed"]))
    return {
        "status": "DIAGNOSTIC_WINNER_NOT_PROMOTED",
        "best_by_pf": best["name"],
        "note": "Positive MT5 tester result only. Requires fresh forward confirmation before runtime promotion.",
    }


def render_markdown(payload: dict[str, Any]) -> str:
    currency = payload.get("scope", {}).get("tester_currency", "AED")
    lines = [
        "# XAU 920101 Breakout-Retest MT5 Variant Backtests",
        "",
        f"Generated: `{payload['generated_at_utc']}`",
        f"Period: `{payload['scope']['period']}`",
        f"Tester currency: `{currency}`",
        "",
        "## Boundary",
        "",
        "- MT5 Strategy Tester only.",
        "- No chart, preset, order, position, or live/demo runtime change was made.",
        "- The tested EA is `Phase2ExperimentalDemoExecutor.mq5`, using the actual breakout-retest observer and executor order path.",
        "- Variants are fixed session/smart-trend/cost variants. This is not an optimizer run.",
        "- Positive rows are diagnostic only until forward-tested.",
        f"- Profit/loss table values are in tester currency `{currency}`.",
        "",
        "## Variant Summary",
        "",
        f"| Variant | Trades | WR | Net {currency} | PF | Avg {currency} | Max Equity DD | Top3 Removed | Worst Day | Long {currency} / WR | Short {currency} / WR | Decision |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|",
    ]
    for result in payload["variants"]:
        overall = result["summary"]["overall"]
        direction = result["summary"].get("direction", {})
        long = direction.get("LONG", {})
        short = direction.get("SHORT", {})
        robust = result["summary"]["robustness"]
        decision = "diagnostic_only"
        if overall["pnl_aed"] <= 0:
            decision = "fail"
        elif overall["trades"] < 30:
            decision = "too_few_trades"
        elif robust["top3_removed_pnl_aed"] <= 0:
            decision = "outlier_sensitive"
        equity_dd = result.get("mt5_report_metrics", {}).get("Equity Drawdown Maximal", "n/a")
        lines.append(
            f"| `{result['name']}` | `{overall['trades']}` | `{overall['win_rate_pct']}%` | "
            f"`{overall['pnl_aed']}` | `{overall['profit_factor']}` | `{overall['avg_pnl_aed']}` | "
            f"`{equity_dd}` | `{robust['top3_removed_pnl_aed']}` | `{robust['worst_day_pnl_aed']}` | "
            f"`{long.get('pnl_aed', 0)} / {long.get('win_rate_pct', 0)}%` | "
            f"`{short.get('pnl_aed', 0)} / {short.get('win_rate_pct', 0)}%` | `{decision}` |"
        )
    lines.extend(
        [
            "",
            "## Winner Status",
            "",
            f"- Status: `{payload['winner']['status']}`",
            f"- Note: {payload['winner']['note']}",
            "",
            "## Session Splits By Variant",
            "",
        ]
    )
    for result in payload["variants"]:
        lines.extend(
            [
                f"### `{result['name']}`",
                "",
                f"{result['label']}",
                "",
                f"| Session | Trades | WR | Net {currency} | PF | Avg {currency} |",
                "|---|---:|---:|---:|---:|---:|",
            ]
        )
        for session, summary in result["summary"].get("session", {}).items():
            lines.append(
                f"| `{session}` | `{summary['trades']}` | `{summary['win_rate_pct']}%` | "
                f"`{summary['pnl_aed']}` | `{summary['profit_factor']}` | `{summary['avg_pnl_aed']}` |"
            )
        lines.extend(
            [
                "",
                "Order activity:",
                "",
                f"- Actions: `{json.dumps(result['order_activity']['actions'])}`",
                f"- Top guard reasons: `{json.dumps(result['order_activity']['top_guard_reasons'])}`",
                f"- Profit protection actions: `{json.dumps(result.get('management_activity', {}).get('actions', {}))}`",
                "",
            ]
        )
    lines.extend(
        [
            "## Artifact Paths",
            "",
        ]
    )
    for result in payload["variants"]:
        lines.extend(
            [
                f"### `{result['name']}`",
                "",
                f"- MT5 report: `{result['html_report']}`",
                f"- Trade CSV: `{result['trade_csv']}`",
                f"- Order CSV: `{result['order_csv']}`",
                f"- Management CSV: `{result.get('management_csv', '')}`",
                f"- Summary JSON: `{result['summary_json']}`",
                "",
            ]
        )
    lines.extend(
        [
            "## Initial Interpretation",
            "",
            "Use this report to compare the live-style 920101 guard choices against raw 24h behavior. "
            "The key questions are whether H1 filtering improves the raw book, whether a session slice is carrying the result, "
            "whether cost_R filtering removes damage, and whether any apparent winner survives top-winner removal.",
            "",
        ]
    )
    return "\n".join(lines)


def server_session(hour: int) -> str:
    if 6 <= hour < 12:
        return "server_06_11"
    if 12 <= hour < 16:
        return "server_12_15"
    if 16 <= hour < 20:
        return "server_16_19"
    return "server_20_05"


def wait_for_file(path: Path, timeout_seconds: int = 30) -> None:
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        if path.exists() and path.stat().st_size > 0:
            return
        time.sleep(1)
    raise TimeoutError(f"Timed out waiting for {path}")


def read_text(path: Path) -> str:
    data = path.read_bytes()
    for encoding in ("utf-16", "utf-8-sig", "utf-8"):
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", errors="replace")


def require_file(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(path)


def safe_name(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9_]+", "_", value.strip().upper())
    return cleaned.strip("_") or "BACKTEST"


def main() -> int:
    parser = argparse.ArgumentParser(description="Run MT5 Strategy Tester variants for XAU 920101 breakout-retest.")
    parser.add_argument("--from-date", default=DEFAULT_FROM_DATE, help="MT5 date, e.g. 2026.04.01")
    parser.add_argument("--to-date", default=DEFAULT_TO_DATE, help="MT5 date, e.g. 2026.06.30")
    parser.add_argument("--tag", default=DEFAULT_TAG, help="Report tag, e.g. Q2_2026")
    parser.add_argument("--backtest-root", type=Path, default=DEFAULT_BACKTEST_ROOT)
    parser.add_argument("--metaeditor", type=Path, default=DEFAULT_METAEDITOR)
    parser.add_argument(
        "--variants",
        default="",
        help="Optional comma-separated variant names to run. Defaults to all fixed variants.",
    )
    parser.add_argument(
        "--variant-timeout-seconds",
        type=int,
        default=180,
        help="Seconds to wait for each MT5 tester HTML report. Use a larger value for multi-year tests.",
    )
    parser.add_argument("--deposit", default="1808.13", help="Tester deposit amount.")
    parser.add_argument("--currency", default="AED", help="Tester deposit currency.")
    args = parser.parse_args()
    variant_names = {item.strip() for item in args.variants.split(",") if item.strip()} or None
    safe_tag = safe_name(args.tag)
    report_md = PHASE1_ROOT / "outputs" / "reports" / f"XAU_920101_BREAKOUT_RETEST_VARIANT_BACKTEST_{safe_tag}.md"
    report_json = report_md.with_suffix(".json")
    payload = run_variants(
        backtest_root=args.backtest_root,
        metaeditor=args.metaeditor,
        from_date=args.from_date,
        to_date=args.to_date,
        tag=safe_tag,
        report_md=report_md,
        report_json=report_json,
        variant_names=variant_names,
        variant_timeout_seconds=args.variant_timeout_seconds,
        deposit=args.deposit,
        currency=args.currency,
    )
    print(
        json.dumps(
            {
                "winner": payload["winner"],
                "variants": [
                    {
                        "name": variant["name"],
                        "overall": variant["summary"]["overall"],
                        "robustness": variant["summary"]["robustness"],
                    }
                    for variant in payload["variants"]
                ],
                "report": str(report_md),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
