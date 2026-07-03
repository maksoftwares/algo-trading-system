from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PHASE1_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_JSON = PHASE1_ROOT / "outputs" / "reports" / "A1_A2_920101_H1_ONLY_SMART_TREND_UPDATE_2026_06_29.json"

A1_TERMINAL_DATA = Path("C:/Users/ZHAO ZHU INFORMATION/AppData/Roaming/MetaQuotes/Terminal/D0E8209F77C8CF37AD8BF550E51FF075")
A1_TERMINAL_EXE = Path("C:/Program Files/MetaTrader 5/terminal64.exe")
A2_ROOT = Path("C:/MT5PortableTier1BestEA")
A2_TERMINAL_DATA = A2_ROOT
A2_TERMINAL_EXE = A2_ROOT / "terminal64.exe"
METAEDITOR_EXE = Path("C:/Program Files/MetaTrader 5/MetaEditor64.exe")

EXECUTOR_EA = "Phase2ExperimentalDemoExecutor"
GUARDIAN_EA = "Account1DailyProfitFloorGuardian"
EXECUTOR_AUTH_TOKEN = "EXPERIMENTAL_DEMO_AUTHORIZED_REVIEW_ONLY"
EXECUTOR_COST_ACK = "I_ACKNOWLEDGE_COST_SUSPENDED_NON_CANONICAL_EXPERIMENT"
EXECUTOR_STATUS = "EXPERIMENTAL_QUARANTINE_REVIEW_ONLY"
FAMILY_STATUS = "COST_SUSPENDED_CANONICAL"

A1_ACCOUNT = "1025742"
A2_ACCOUNT = "1033030"
SYMBOL = "XAUUSD"
CANDIDATE = "breakout_retest"
SESSION_START = "12"
SESSION_END = "15"
FIXED_LOT = "0.01"
MAX_OPEN = "1"
MAX_COST_R = "0.30"
MAX_SPREAD = "75.0"
DAILY_FLOOR_AED = "50.0"
NEXT_DAILY_FLOOR_AED = "100.0"
SMART_TREND_ENABLED = "true"
SMART_TREND_SHADOW_ONLY = "false"
SMART_TREND_D1_LAG = "5"
SMART_TREND_H1_LAG = "3"
SMART_TREND_REQUIRE_D1 = "false"
SMART_TREND_REQUIRE_H1 = "true"
SMART_TREND_MIN_D1 = "0.25"
SMART_TREND_MIN_H1 = "0.15"


@dataclass(frozen=True)
class ChartRow:
    lane: str
    chart: str
    path: str
    symbol: str
    expert: str
    inputs: dict[str, str]
    sha256: str


def main() -> int:
    parser = argparse.ArgumentParser(description="Apply owner-approved A1/A2 920101 runtime maintenance.")
    parser.add_argument("--apply", action="store_true", help="Actually stop terminals, write profiles, and relaunch.")
    parser.add_argument("--no-launch", action="store_true", help="Do not relaunch terminals after profile writes.")
    args = parser.parse_args()

    mode = "apply" if args.apply else "dry-run"
    payload = run(mode=mode, launch=not args.no_launch)
    OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_JSON.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    OUTPUT_JSON.with_suffix(".md").write_text(render_markdown(payload), encoding="utf-8")
    print(f"{payload['status']} -> {OUTPUT_JSON}")
    return 0 if payload["status"].startswith("PASS") or payload["status"].startswith("DRY_RUN") else 1


def run(*, mode: str, launch: bool) -> dict[str, Any]:
    started_at = now_utc()
    a1_profile = A1_TERMINAL_DATA / "MQL5" / "Profiles" / "Charts" / "Default"
    a2_profile = A2_TERMINAL_DATA / "MQL5" / "Profiles" / "Charts" / "Default"
    require_dir(a1_profile)
    require_dir(a2_profile)
    require_file(A1_TERMINAL_EXE)
    require_file(A2_TERMINAL_EXE)
    require_file(METAEDITOR_EXE)

    before_a1 = inventory("A1", a1_profile)
    before_a2 = inventory("A2", a2_profile)
    before_a3_hashes = profile_hashes(Path("C:/MT5PortableRepairLane/MQL5/Profiles/Charts/Default"))

    compile_reports: list[dict[str, Any]] = []
    terminal_actions: list[dict[str, Any]] = []
    backups: dict[str, str] = {}
    changed_files: list[dict[str, Any]] = []
    after_a1 = before_a1
    after_a2 = before_a2

    if mode == "apply":
        compile_reports.extend(deploy_and_compile(A1_TERMINAL_DATA))
        compile_reports.extend(deploy_and_compile(A2_TERMINAL_DATA))

        terminal_actions.append(stop_terminal("A1", A1_TERMINAL_EXE))
        terminal_actions.append(stop_terminal("A2", A2_TERMINAL_EXE))

        backups["A1"] = str(backup_profile(a1_profile, A1_TERMINAL_DATA, "a1_a2_920101_h1_only_smart_trend_a1"))
        backups["A2"] = str(backup_profile(a2_profile, A2_TERMINAL_DATA, "a1_a2_920101_h1_only_smart_trend_a2"))

        changed_files.extend(apply_a1_profile(a1_profile))
        changed_files.extend(apply_a2_profile(a2_profile))

        after_a1 = inventory("A1", a1_profile)
        after_a2 = inventory("A2", a2_profile)

        if launch:
            terminal_actions.append(launch_terminal("A1", A1_TERMINAL_EXE, portable=False))
            terminal_actions.append(launch_terminal("A2", A2_TERMINAL_EXE, portable=True))
            time.sleep(8)

    planned_a1 = apply_a1_profile_preview(a1_profile)
    planned_a2 = apply_a2_profile_preview(a2_profile)
    after_a3_hashes = profile_hashes(Path("C:/MT5PortableRepairLane/MQL5/Profiles/Charts/Default"))
    checks = build_checks(
        mode=mode,
        after_a1=after_a1,
        after_a2=after_a2,
        before_a3_hashes=before_a3_hashes,
        after_a3_hashes=after_a3_hashes,
        terminal_actions=terminal_actions,
        compile_reports=compile_reports,
        backups=backups,
    )
    status = "DRY_RUN_READY" if mode == "dry-run" else ("PASS_APPLIED" if all(check["status"] == "PASS" for check in checks) else "FAIL_APPLIED")
    return {
        "status": status,
        "mode": mode,
        "created_at_utc": now_utc(),
        "started_at_utc": started_at,
        "authority": "Owner approved replacing the strict D1+H1 smart trend gate with an H1-only broker-action trend gate for the A1/A2 920101 XAU evening forward test. D1 remains diagnostic/logged only. Demo accounts only; no canonical Phase 2/live-capital approval.",
        "scope": {
            "a1_account": A1_ACCOUNT,
            "a2_account": A2_ACCOUNT,
            "symbol": SYMBOL,
            "candidate": CANDIDATE,
            "session_server_hours": f"{SESSION_START}->{SESSION_END}",
            "lot": FIXED_LOT,
            "smart_trend_filter": {
                "enabled": SMART_TREND_ENABLED,
                "shadow_only": SMART_TREND_SHADOW_ONLY,
                "d1_required": SMART_TREND_REQUIRE_D1,
                "h1_required": SMART_TREND_REQUIRE_H1,
                "d1_trend_score_aligned_min": SMART_TREND_MIN_D1,
                "h1_ema20_slope_aligned_atr_min": SMART_TREND_MIN_H1,
            },
            "daily_floor_aed": DAILY_FLOOR_AED,
            "next_daily_floor_aed": NEXT_DAILY_FLOOR_AED,
            "a3_touched": False,
        },
        "before": {
            "A1": [row_to_dict(row) for row in before_a1],
            "A2": [row_to_dict(row) for row in before_a2],
        },
        "after": {
            "A1": [row_to_dict(row) for row in after_a1],
            "A2": [row_to_dict(row) for row in after_a2],
        },
        "planned_changes": {
            "A1": planned_a1,
            "A2": planned_a2,
        },
        "changed_files": changed_files,
        "profile_backups": backups,
        "compile_reports": compile_reports,
        "terminal_actions": terminal_actions,
        "checks": checks,
        "startup_log_tails": startup_tails(),
        "claude_verification_focus": [
            "Confirm A1 now has exactly one broker-action XAU Phase2ExperimentalDemoExecutor breakout_retest chart for account 1025742.",
            "Confirm A1 EURUSD/GBPUSD standard executor and A1 repair/WR50 lanes are disarmed.",
            "Confirm A2 XAU Phase2ExperimentalDemoExecutor remains broker-action enabled and aligned to A1.",
            "Confirm A1 and A2 both have active daily profit/loss guardians using their account-specific halt files.",
            "Confirm A3 profile hashes did not change and A3 remains paused.",
        ],
    }


def deploy_and_compile(terminal_data: Path) -> list[dict[str, Any]]:
    reports: list[dict[str, Any]] = []
    mql5 = terminal_data / "MQL5"
    (mql5 / "Experts").mkdir(parents=True, exist_ok=True)
    (mql5 / "Include" / "Phase1").mkdir(parents=True, exist_ok=True)

    for include in ("Phase1Types.mqh", "Phase1BreakoutRetest.mqh"):
        source = PHASE1_ROOT / "mt5" / "Include" / "Phase1" / include
        target = mql5 / "Include" / "Phase1" / include
        shutil.copy2(source, target)
    for include in ("DirectionStateShadow.mqh", "A3MlShadowTap.mqh", "A3MlEaHandoff.mqh"):
        source = PHASE1_ROOT / "mt5" / "Include" / include
        target = mql5 / "Include" / include
        shutil.copy2(source, target)

    for name in (EXECUTOR_EA, GUARDIAN_EA):
        source = PHASE1_ROOT / "mt5" / "Experts" / f"{name}.mq5"
        target = mql5 / "Experts" / f"{name}.mq5"
        shutil.copy2(source, target)
        reports.append(compile_one(name, terminal_data))
    return reports


def compile_one(name: str, terminal_data: Path) -> dict[str, Any]:
    scratch = Path("C:/MT5CompileScratch920101") / terminal_data.name / name
    scratch_mql5 = scratch / "MQL5"
    scratch_experts = scratch_mql5 / "Experts"
    scratch_include = scratch_mql5 / "Include" / "Phase1"
    if scratch.exists():
        shutil.rmtree(scratch)
    scratch_experts.mkdir(parents=True, exist_ok=True)
    scratch_include.mkdir(parents=True, exist_ok=True)
    shutil.copy2(terminal_data / "MQL5" / "Experts" / f"{name}.mq5", scratch_experts / f"{name}.mq5")
    for include in ("Phase1Types.mqh", "Phase1BreakoutRetest.mqh"):
        source = terminal_data / "MQL5" / "Include" / "Phase1" / include
        if source.exists():
            shutil.copy2(source, scratch_include / include)
    scratch_include_root = scratch_mql5 / "Include"
    for include in ("DirectionStateShadow.mqh", "A3MlShadowTap.mqh", "A3MlEaHandoff.mqh"):
        source = terminal_data / "MQL5" / "Include" / include
        if source.exists():
            shutil.copy2(source, scratch_include_root / include)
    log = scratch / f"compile_{name}.log"
    subprocess.run([str(METAEDITOR_EXE), f"/compile:{scratch_experts / (name + '.mq5')}", f"/log:{log}"], text=True, capture_output=True, timeout=120)
    ex5 = scratch_experts / f"{name}.ex5"
    target_ex5 = terminal_data / "MQL5" / "Experts" / f"{name}.ex5"
    target_log = terminal_data / "MQL5" / "Logs" / f"compile_{name}_a1_a2_920101_20260629.log"
    target_log.parent.mkdir(parents=True, exist_ok=True)
    if log.exists():
        shutil.copy2(log, target_log)
    ok = ex5.exists() and compile_log_ok(target_log)
    if ex5.exists():
        shutil.copy2(ex5, target_ex5)
    return {
        "terminal_data": str(terminal_data),
        "ea": name,
        "status": "PASS" if ok else "FAIL",
        "log": str(target_log),
        "ex5": str(target_ex5) if ex5.exists() else "",
        "log_tail": read_tail(target_log, 12),
    }


def compile_log_ok(path: Path) -> bool:
    text = read_text_any(path).lower()
    return "0 errors" in text and ("0 warnings" in text or "0 warning" in text)


def apply_a1_profile(profile: Path) -> list[dict[str, Any]]:
    changes: list[dict[str, Any]] = []
    changes.append(write_chart(profile / "chart03.chr", render_executor_chart("A1", A1_ACCOUNT, "experimental_demo_kill_switch.txt", "a1_920101_evening")))
    for chart in ("chart01.chr", "chart02.chr", "chart18.chr", "chart19.chr", "chart20.chr"):
        path = profile / chart
        if path.exists():
            before = sha256_file(path)
            text = read_text_any(path)
            text = update_inputs(text, {
                "InpDryRunOnly": "true",
                "InpBrokerActionAllowed": "false",
                "InpRunId": f"DISABLED_NON_SPEC_{chart}_20260621",
            })
            write_text_preserving_encoding(path, text)
            changes.append({"path": str(path), "before_sha256": before, "after_sha256": sha256_file(path), "action": "disabled_non_spec_broker_action"})
    changes.extend(disable_extra_phase2_executors(profile, keep_chart="chart03.chr"))
    wr50 = profile / "chart21.chr"
    if wr50.exists():
        before = sha256_file(wr50)
        text = update_inputs(read_text_any(wr50), {
            "InpAllowDemoTrading": "false",
            "InpRunId": "WR50_DISABLED_OUTSIDE_920101_FORWARD_20260621",
        })
        write_text_preserving_encoding(wr50, text)
        changes.append({"path": str(wr50), "before_sha256": before, "after_sha256": sha256_file(wr50), "action": "disabled_wr50_broker_action"})
    guardian = profile / "chart26.chr"
    if guardian.exists():
        before = sha256_file(guardian)
        text = update_inputs(read_text_any(guardian), guardian_inputs("A1", A1_ACCOUNT, "experimental_demo_kill_switch.txt", "919100"))
        write_text_preserving_encoding(guardian, text)
        changes.append({"path": str(guardian), "before_sha256": before, "after_sha256": sha256_file(guardian), "action": "updated_a1_guardian_daily_lock_loss"})
    else:
        changes.append(write_chart(guardian, render_guardian_chart("A1", A1_ACCOUNT, "experimental_demo_kill_switch.txt", "919100")))
    return changes


def apply_a2_profile(profile: Path) -> list[dict[str, Any]]:
    changes: list[dict[str, Any]] = []
    chart = profile / "chart02.chr"
    changes.append(write_chart(chart, render_executor_chart("A2", A2_ACCOUNT, "tier1_bestea_kill_switch.txt", "a2_920101_evening")))
    changes.extend(disable_extra_phase2_executors(profile, keep_chart="chart02.chr"))
    changes.append(write_chart(profile / "chart03.chr", render_guardian_chart("A2", A2_ACCOUNT, "tier1_bestea_kill_switch.txt", "919200")))
    return changes


def disable_extra_phase2_executors(profile: Path, *, keep_chart: str) -> list[dict[str, Any]]:
    changes: list[dict[str, Any]] = []
    for path in sorted(profile.glob("chart*.chr")):
        if path.name == keep_chart:
            continue
        text = read_text_any(path)
        if parse_expert(text) != EXECUTOR_EA:
            continue
        before = sha256_file(path)
        text = update_inputs(text, {
            "InpDryRunOnly": "true",
            "InpBrokerActionAllowed": "false",
            "InpRunId": f"DISABLED_EXTRA_PHASE2_EXECUTOR_{path.stem.upper()}_20260623",
        })
        write_text_preserving_encoding(path, text)
        changes.append({
            "path": str(path),
            "before_sha256": before,
            "after_sha256": sha256_file(path),
            "action": "disabled_extra_phase2_executor",
        })
    return changes


def apply_a1_profile_preview(profile: Path) -> list[str]:
    return [
        f"Restore/update A1 XAU 920101 broker-action chart at {profile / 'chart03.chr'} with H1-only smart trend gate",
        "Disable A1 EURUSD/GBPUSD standard breakout broker action",
        "Disable A1 repair broker action charts",
        "Disable A1 WR50 broker action",
        "Enable A1 guardian daily profit +50 / next +100 and daily loss -100 entry halt/close control",
    ]


def apply_a2_profile_preview(profile: Path) -> list[str]:
    return [
        f"Align/update A2 XAU 920101 chart at {profile / 'chart02.chr'} with H1-only smart trend gate",
        f"Attach/update A2 active daily profit/loss guardian at {profile / 'chart03.chr'}",
    ]


def executor_inputs(lane: str, account: str, kill_switch: str, log_slug: str) -> dict[str, str]:
    return {
        "InpRunId": f"{lane}_XAU_920101_EVENING_H1_ONLY_TREND_V2_20260629",
        "InpDryRunOnly": "false",
        "InpBrokerActionAllowed": "true",
        "InpCandidate": CANDIDATE,
        "InpCandidateStatus": EXECUTOR_STATUS,
        "InpFamilyLifecycleStatus": FAMILY_STATUS,
        "InpTargetSymbol": SYMBOL,
        "InpQualifiedSymbolsCsv": SYMBOL,
        "InpExpectedServerMarker": "Demo",
        "InpAllowedAccountLoginsCsv": account,
        "InpExperimentalAuthorizationToken": EXECUTOR_AUTH_TOKEN,
        "InpRequiredExperimentalAuthorizationToken": EXECUTOR_AUTH_TOKEN,
        "InpCostSuspensionAcknowledgementToken": EXECUTOR_COST_ACK,
        "InpRequiredCostSuspensionAcknowledgementToken": EXECUTOR_COST_ACK,
        "InpAuthorizedCandidatesCsv": CANDIDATE,
        "InpAttachmentLogFileName": f"{log_slug}_signal_log.csv",
        "InpStartupLogFileName": f"{log_slug}_startup_log.csv",
        "InpOrderLogFileName": f"{log_slug}_order_log.csv",
        "InpDirectionStateFileName": f"{log_slug}_direction_state.csv",
        "InpKillSwitchFileName": kill_switch,
        "InpFixedLot": FIXED_LOT,
        "InpEURUSDFixedLot": "0.01",
        "InpGBPUSDFixedLot": "0.01",
        "InpMaxOrdersPerDay": "0",
        "InpMaxAccountOrdersPerDay": "0",
        "InpMinSecondsBetweenOrders": "60",
        "InpMaxOpenPositionsPerInstance": MAX_OPEN,
        "InpDeviationPoints": "50",
        "InpMaxEstimatedCostR": MAX_COST_R,
        "InpMaxMeasuredSpreadPoints": MAX_SPREAD,
        "InpTradeSessionGateEnabled": "true",
        "InpTradeSessionStartHour": SESSION_START,
        "InpTradeSessionEndHour": SESSION_END,
        "InpSmartTrendFilterEnabled": SMART_TREND_ENABLED,
        "InpSmartTrendFilterShadowOnly": SMART_TREND_SHADOW_ONLY,
        "InpSmartTrendD1LagBars": SMART_TREND_D1_LAG,
        "InpSmartTrendH1LagBars": SMART_TREND_H1_LAG,
        "InpSmartTrendRequireD1": SMART_TREND_REQUIRE_D1,
        "InpSmartTrendRequireH1": SMART_TREND_REQUIRE_H1,
        "InpSmartTrendMinD1Aligned": SMART_TREND_MIN_D1,
        "InpSmartTrendMinH1Aligned": SMART_TREND_MIN_H1,
    }


def guardian_inputs(lane: str, account: str, halt_file: str, magic: str) -> dict[str, str]:
    token = f"{lane}_DAILY_PROFIT_LOSS_GUARDIAN_OWNER_AUTHORIZED_20260621"
    prefix = f"{lane}_DAILY_PROFIT_LOSS_GUARDIAN"
    return {
        "InpRunId": f"{prefix}_V1_ARMED_20260621",
        "InpDryRunOnly": "false",
        "InpCloseActionAllowed": "true",
        "InpAllowedAccountLogin": account,
        "InpExpectedServerMarker": "Demo",
        "InpOwnerAuthorizationToken": token,
        "InpRequiredOwnerAuthorizationToken": token,
        "InpDailyFloorAed": DAILY_FLOOR_AED,
        "InpNextDailyFloorEnabled": "true",
        "InpNextDailyFloorAed": NEXT_DAILY_FLOOR_AED,
        "InpHaltEntriesWhenArmed": "true",
        "InpDailyLossStopEnabled": "true",
        "InpDailyLossStopAed": "-100.0",
        "InpDubaiUtcOffsetMinutes": "240",
        "InpTimerSeconds": "2",
        "InpDeviationPoints": "100",
        "InpGuardianMagic": magic,
        "InpGuardianKillSwitchFileName": f"{prefix}_KILL.txt",
        "InpEntryHaltFileName": halt_file,
        "InpStateFileName": f"{prefix}_STATE.txt",
        "InpEventLogFileName": f"{prefix}_EVENTS.csv",
        "InpDailySummaryFileName": f"{prefix}_DAILY_SUMMARY.csv",
        "InpStartupLogFileName": f"{prefix}_STARTUP.csv",
    }


def render_executor_chart(lane: str, account: str, kill_switch: str, log_slug: str) -> str:
    return render_chart_base(
        expert=EXECUTOR_EA,
        expert_path=f"Experts\\{EXECUTOR_EA}.ex5",
        inputs=executor_inputs(lane, account, kill_switch, log_slug),
        window_top=20,
        window_bottom=740,
    )


def render_guardian_chart(lane: str, account: str, halt_file: str, magic: str) -> str:
    return render_chart_base(
        expert=GUARDIAN_EA,
        expert_path=f"Experts\\{GUARDIAN_EA}.ex5",
        inputs=guardian_inputs(lane, account, halt_file, magic),
        window_top=760,
        window_bottom=1320,
    )


def render_chart_base(*, expert: str, expert_path: str, inputs: dict[str, str], window_top: int, window_bottom: int) -> str:
    lines = [
        "<chart>",
        f"id={int(time.time())}",
        f"symbol={SYMBOL}",
        "description=Gold",
        "period_type=0",
        "period_size=5",
        "digits=2",
        "tick_size=0.010000",
        "scale_fix=0",
        "scale_fixed_min=0.000000",
        "scale_fixed_max=0.000000",
        "scale=3",
        "mode=1",
        "fore=0",
        "grid=0",
        "volume=0",
        "scroll=1",
        "shift=1",
        "ohlc=0",
        "one_click=0",
        "one_click_btn=0",
        "askline=1",
        "days=0",
        "window_left=104",
        f"window_top={window_top}",
        "window_right=1084",
        f"window_bottom={window_bottom}",
        "windows_total=1",
        "",
        "<expert>",
        f"name={expert}",
        f"path={expert_path}",
        "expertmode=1",
        "<inputs>",
    ]
    lines.extend(f"{key}={value}" for key, value in inputs.items())
    lines.extend(
        [
            "</inputs>",
            "</expert>",
            "",
            "<window>",
            "height=100.000000",
            "objects=0",
            "<indicator>",
            "name=Main",
            "path=",
            "apply=1",
            "</indicator>",
            "</window>",
            "</chart>",
            "",
        ]
    )
    return "\n".join(lines)


def inventory(lane: str, profile: Path) -> list[ChartRow]:
    rows = []
    for path in sorted(profile.glob("chart*.chr")):
        text = read_text_any(path)
        rows.append(ChartRow(lane, path.name, str(path), parse_value(text, "symbol"), parse_expert(text), parse_inputs(text), sha256_file(path)))
    return rows


def parse_expert(text: str) -> str:
    in_expert = False
    for raw in text.splitlines():
        stripped = raw.strip()
        if stripped == "<expert>":
            in_expert = True
            continue
        if stripped == "</expert>":
            in_expert = False
            continue
        if in_expert and stripped.startswith("name="):
            return stripped.split("=", 1)[1]
    return "NO_EA"


def parse_inputs(text: str) -> dict[str, str]:
    inputs: dict[str, str] = {}
    in_inputs = False
    for raw in text.splitlines():
        stripped = raw.strip()
        if stripped == "<inputs>":
            in_inputs = True
            continue
        if stripped == "</inputs>":
            in_inputs = False
            continue
        if in_inputs and "=" in stripped:
            key, value = stripped.split("=", 1)
            inputs[key] = value
    return inputs


def parse_value(text: str, key: str) -> str:
    prefix = f"{key}="
    for raw in text.splitlines():
        stripped = raw.strip()
        if stripped.startswith(prefix):
            return stripped.split("=", 1)[1]
    return ""


def update_inputs(text: str, replacements: dict[str, str]) -> str:
    lines: list[str] = []
    in_inputs = False
    seen: set[str] = set()
    for raw in text.splitlines():
        stripped = raw.strip()
        if stripped == "<inputs>":
            in_inputs = True
            lines.append(raw)
            continue
        if stripped == "</inputs>":
            for key, value in replacements.items():
                if key not in seen:
                    lines.append(f"{key}={value}")
            lines.append(raw)
            in_inputs = False
            continue
        if in_inputs and "=" in stripped:
            key = stripped.split("=", 1)[0]
            if key in replacements:
                raw = f"{key}={replacements[key]}"
                seen.add(key)
        lines.append(raw)
    return "\n".join(lines) + ("\n" if text.endswith("\n") else "")


def write_chart(path: Path, text: str) -> dict[str, Any]:
    before = sha256_file(path) if path.exists() else ""
    path.write_text(text, encoding="utf-8")
    return {"path": str(path), "before_sha256": before, "after_sha256": sha256_file(path), "action": "write_chart"}


def write_text_preserving_encoding(path: Path, text: str) -> None:
    encoding = detect_encoding(path)
    path.write_bytes(text.encode(encoding))


def detect_encoding(path: Path) -> str:
    data = path.read_bytes()[:4]
    if data.startswith(b"\xff\xfe") or data.startswith(b"\xfe\xff"):
        return "utf-16"
    return "utf-8"


def read_text_any(path: Path) -> str:
    for encoding in ("utf-8", "utf-16", "cp1252"):
        try:
            return path.read_text(encoding=encoding)
        except UnicodeError:
            continue
    return path.read_text(errors="replace")


def row_to_dict(row: ChartRow) -> dict[str, Any]:
    return {
        "lane": row.lane,
        "chart": row.chart,
        "path": row.path,
        "symbol": row.symbol,
        "expert": row.expert,
        "sha256": row.sha256,
        "InpCandidate": row.inputs.get("InpCandidate", ""),
        "InpTargetSymbol": row.inputs.get("InpTargetSymbol", ""),
        "InpAllowedAccountLoginsCsv": row.inputs.get("InpAllowedAccountLoginsCsv", ""),
        "InpDryRunOnly": row.inputs.get("InpDryRunOnly", ""),
        "InpBrokerActionAllowed": row.inputs.get("InpBrokerActionAllowed", ""),
        "InpTradeSessionGateEnabled": row.inputs.get("InpTradeSessionGateEnabled", ""),
        "InpTradeSessionStartHour": row.inputs.get("InpTradeSessionStartHour", ""),
        "InpTradeSessionEndHour": row.inputs.get("InpTradeSessionEndHour", ""),
        "InpMaxOpenPositionsPerInstance": row.inputs.get("InpMaxOpenPositionsPerInstance", ""),
        "InpMaxEstimatedCostR": row.inputs.get("InpMaxEstimatedCostR", ""),
        "InpMaxMeasuredSpreadPoints": row.inputs.get("InpMaxMeasuredSpreadPoints", ""),
        "InpSmartTrendFilterEnabled": row.inputs.get("InpSmartTrendFilterEnabled", ""),
        "InpSmartTrendFilterShadowOnly": row.inputs.get("InpSmartTrendFilterShadowOnly", ""),
        "InpSmartTrendRequireD1": row.inputs.get("InpSmartTrendRequireD1", ""),
        "InpSmartTrendRequireH1": row.inputs.get("InpSmartTrendRequireH1", ""),
        "InpSmartTrendMinD1Aligned": row.inputs.get("InpSmartTrendMinD1Aligned", ""),
        "InpSmartTrendMinH1Aligned": row.inputs.get("InpSmartTrendMinH1Aligned", ""),
        "InpAllowDemoTrading": row.inputs.get("InpAllowDemoTrading", ""),
        "InpCloseActionAllowed": row.inputs.get("InpCloseActionAllowed", ""),
        "InpDailyFloorAed": row.inputs.get("InpDailyFloorAed", ""),
        "InpNextDailyFloorEnabled": row.inputs.get("InpNextDailyFloorEnabled", ""),
        "InpNextDailyFloorAed": row.inputs.get("InpNextDailyFloorAed", ""),
        "InpDailyLossStopEnabled": row.inputs.get("InpDailyLossStopEnabled", ""),
        "InpDailyLossStopAed": row.inputs.get("InpDailyLossStopAed", ""),
        "InpEntryHaltFileName": row.inputs.get("InpEntryHaltFileName", ""),
    }


def build_checks(
    *,
    mode: str,
    after_a1: list[ChartRow],
    after_a2: list[ChartRow],
    before_a3_hashes: dict[str, str],
    after_a3_hashes: dict[str, str],
    terminal_actions: list[dict[str, Any]],
    compile_reports: list[dict[str, Any]],
    backups: dict[str, str],
) -> list[dict[str, str]]:
    checks: list[dict[str, str]] = []

    def check(name: str, passed: bool, detail: str) -> None:
        checks.append({"name": name, "status": "PASS" if passed else "FAIL", "detail": detail})

    a1_xau = [
        row for row in after_a1
        if row.expert == EXECUTOR_EA
        and row.inputs.get("InpTargetSymbol") == SYMBOL
        and row.inputs.get("InpAllowedAccountLoginsCsv") == A1_ACCOUNT
        and executor_row_is_active(row)
    ]
    a2_xau = [
        row for row in after_a2
        if row.expert == EXECUTOR_EA
        and row.inputs.get("InpTargetSymbol") == SYMBOL
        and row.inputs.get("InpAllowedAccountLoginsCsv") == A2_ACCOUNT
        and executor_row_is_active(row)
    ]
    check("a1_has_one_active_xau_920101_chart", len(a1_xau) == 1, ",".join(row.chart for row in a1_xau))
    check("a2_has_one_active_xau_920101_chart", len(a2_xau) == 1, ",".join(row.chart for row in a2_xau))
    check("a1_non_spec_executors_disarmed", all(non_spec_ok(row) for row in after_a1), "A1 non-spec broker action false/dry-run true")
    check("a1_wr50_disarmed", all(row.expert != "WR50_BreakoutWideStop_v0" or row.inputs.get("InpAllowDemoTrading") == "false" for row in after_a1), "WR50 demo trading disabled")
    check("a1_guardian_active_loss_stop", any(guardian_row_ok(row, A1_ACCOUNT, "experimental_demo_kill_switch.txt") for row in after_a1), "A1 guardian active with -100 loss stop")
    check("a2_guardian_active_loss_stop", any(guardian_row_ok(row, A2_ACCOUNT, "tier1_bestea_kill_switch.txt") for row in after_a2), "A2 guardian active with -100 loss stop")
    check("a3_profile_untouched", before_a3_hashes == after_a3_hashes, "A3 profile hash map unchanged")
    if mode == "apply":
        check("profile_backups_created", bool(backups.get("A1")) and bool(backups.get("A2")), json.dumps(backups, sort_keys=True))
        check("terminals_stopped_before_write", all(item.get("status") == "PASS" for item in terminal_actions if item.get("action") == "stop"), json.dumps(terminal_actions, sort_keys=True))
        check("compile_reports_pass", bool(compile_reports) and all(item.get("status") == "PASS" for item in compile_reports), json.dumps(compile_reports, sort_keys=True))
    return checks


def executor_row_is_active(row: ChartRow) -> bool:
    inputs = row.inputs
    return (
        row.symbol == SYMBOL
        and inputs.get("InpCandidate") == CANDIDATE
        and inputs.get("InpDryRunOnly") == "false"
        and inputs.get("InpBrokerActionAllowed") == "true"
        and inputs.get("InpTradeSessionGateEnabled") == "true"
        and inputs.get("InpTradeSessionStartHour") == SESSION_START
        and inputs.get("InpTradeSessionEndHour") == SESSION_END
        and inputs.get("InpMaxOpenPositionsPerInstance") == MAX_OPEN
        and inputs.get("InpMaxEstimatedCostR") == MAX_COST_R
        and inputs.get("InpMaxMeasuredSpreadPoints") == MAX_SPREAD
        and inputs.get("InpFixedLot") == FIXED_LOT
        and inputs.get("InpSmartTrendFilterEnabled") == SMART_TREND_ENABLED
        and inputs.get("InpSmartTrendFilterShadowOnly") == SMART_TREND_SHADOW_ONLY
        and inputs.get("InpSmartTrendRequireD1") == SMART_TREND_REQUIRE_D1
        and inputs.get("InpSmartTrendRequireH1") == SMART_TREND_REQUIRE_H1
        and inputs.get("InpSmartTrendMinD1Aligned") == SMART_TREND_MIN_D1
        and inputs.get("InpSmartTrendMinH1Aligned") == SMART_TREND_MIN_H1
    )


def non_spec_ok(row: ChartRow) -> bool:
    if row.expert == EXECUTOR_EA and row.inputs.get("InpTargetSymbol") != SYMBOL:
        return row.inputs.get("InpDryRunOnly") == "true" and row.inputs.get("InpBrokerActionAllowed") == "false"
    if row.expert == "Phase2ExperimentalDemoRepairExecutor":
        return row.inputs.get("InpDryRunOnly") == "true" and row.inputs.get("InpBrokerActionAllowed") == "false"
    return True


def guardian_row_ok(row: ChartRow, account: str, halt_file: str) -> bool:
    return (
        row.expert == GUARDIAN_EA
        and row.inputs.get("InpAllowedAccountLogin") == account
        and row.inputs.get("InpDryRunOnly") == "false"
        and row.inputs.get("InpCloseActionAllowed") == "true"
        and row.inputs.get("InpDailyFloorAed") == DAILY_FLOOR_AED
        and row.inputs.get("InpNextDailyFloorEnabled") == "true"
        and row.inputs.get("InpNextDailyFloorAed") == NEXT_DAILY_FLOOR_AED
        and row.inputs.get("InpDailyLossStopEnabled") == "true"
        and row.inputs.get("InpDailyLossStopAed") == "-100.0"
        and row.inputs.get("InpEntryHaltFileName") == halt_file
    )


def startup_tails() -> dict[str, list[str]]:
    return {
        "A1_920101": read_tail(A1_TERMINAL_DATA / "MQL5" / "Files" / "a1_920101_evening_startup_log.csv", 5),
        "A2_920101": read_tail(A2_TERMINAL_DATA / "MQL5" / "Files" / "a2_920101_evening_startup_log.csv", 5),
        "A1_guardian": read_tail(A1_TERMINAL_DATA / "MQL5" / "Files" / "A1_DAILY_PROFIT_LOSS_GUARDIAN_STARTUP.csv", 5),
        "A2_guardian": read_tail(A2_TERMINAL_DATA / "MQL5" / "Files" / "A2_DAILY_PROFIT_LOSS_GUARDIAN_STARTUP.csv", 5),
    }


def stop_terminal(lane: str, terminal_exe: Path) -> dict[str, Any]:
    before = process_snapshot(terminal_exe)
    ps = f"""
$target = (Resolve-Path -LiteralPath '{terminal_exe}' -ErrorAction SilentlyContinue).Path
if($target) {{
  $procs = Get-CimInstance Win32_Process | Where-Object {{ $_.ExecutablePath -eq $target }}
  foreach($proc in $procs) {{
    $p = Get-Process -Id $proc.ProcessId -ErrorAction SilentlyContinue
    if($p) {{ [void]$p.CloseMainWindow() }}
  }}
  Start-Sleep -Seconds 5
  foreach($proc in $procs) {{
    $p = Get-Process -Id $proc.ProcessId -ErrorAction SilentlyContinue
    if($p) {{ Stop-Process -Id $proc.ProcessId -Force }}
  }}
}}
"""
    subprocess.run(["powershell", "-NoProfile", "-Command", ps], text=True, capture_output=True, timeout=35)
    after = process_snapshot(terminal_exe)
    return {"lane": lane, "action": "stop", "before": before, "after": after, "status": "PASS" if not after["running"] else "FAIL"}


def launch_terminal(lane: str, terminal_exe: Path, *, portable: bool) -> dict[str, Any]:
    args = [str(terminal_exe)]
    if portable:
        args.append("/portable")
    subprocess.Popen(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return {"lane": lane, "action": "launch", "terminal": str(terminal_exe), "portable": str(portable), "status": "PASS"}


def process_snapshot(terminal_exe: Path) -> dict[str, Any]:
    ps = f"""
$target = (Resolve-Path -LiteralPath '{terminal_exe}' -ErrorAction SilentlyContinue).Path
if(-not $target) {{ ConvertTo-Json @{{running=$false;pids=@()}} -Compress; exit 0 }}
$procs = Get-CimInstance Win32_Process | Where-Object {{ $_.ExecutablePath -eq $target }}
ConvertTo-Json @{{running=[bool]$procs;pids=@($procs | ForEach-Object {{ $_.ProcessId }})}} -Compress
"""
    result = subprocess.run(["powershell", "-NoProfile", "-Command", ps], text=True, capture_output=True, timeout=15)
    try:
        return json.loads(result.stdout.strip() or "{}")
    except json.JSONDecodeError:
        return {"running": False, "pids": [], "raw": result.stdout}


def backup_profile(profile: Path, terminal_data: Path, prefix: str) -> Path:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    backup = terminal_data / "_codex_quarantine" / "profile_backups" / f"{prefix}_{stamp}"
    backup.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(profile, backup)
    return backup


def profile_hashes(profile: Path) -> dict[str, str]:
    if not profile.exists():
        return {}
    return {path.name: sha256_file(path) for path in sorted(profile.glob("chart*.chr"))}


def sha256_file(path: Path) -> str:
    if not path.exists():
        return ""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require_dir(path: Path) -> None:
    if not path.exists() or not path.is_dir():
        raise FileNotFoundError(path)


def require_file(path: Path) -> None:
    if not path.exists() or not path.is_file():
        raise FileNotFoundError(path)


def read_tail(path: Path, lines: int) -> list[str]:
    if not path.exists():
        return []
    return read_text_any(path).splitlines()[-lines:]


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# A1/A2 920101 H1-Only Smart Trend Update - 2026-06-29",
        "",
        f"Status: `{payload['status']}`",
        f"Mode: `{payload['mode']}`",
        "",
        payload["authority"],
        "",
        "## Scope",
        "",
        f"- A1 account: `{payload['scope']['a1_account']}`",
        f"- A2 account: `{payload['scope']['a2_account']}`",
        f"- Symbol/candidate: `{payload['scope']['symbol']} / {payload['scope']['candidate']}`",
        f"- Session server hours: `{payload['scope']['session_server_hours']}`",
        f"- Lot: `{payload['scope']['lot']}`",
        f"- Smart trend filter: `enabled={payload['scope']['smart_trend_filter']['enabled']} shadow_only={payload['scope']['smart_trend_filter']['shadow_only']} require_D1={payload['scope']['smart_trend_filter']['d1_required']} D1>={payload['scope']['smart_trend_filter']['d1_trend_score_aligned_min']} require_H1={payload['scope']['smart_trend_filter']['h1_required']} H1>={payload['scope']['smart_trend_filter']['h1_ema20_slope_aligned_atr_min']}`",
        f"- Daily floor / next floor: `{payload['scope']['daily_floor_aed']} / {payload['scope']['next_daily_floor_aed']}`",
        f"- A3 touched: `{payload['scope']['a3_touched']}`",
        "",
        "## Checks",
        "",
        "| Check | Status | Detail |",
        "| --- | --- | --- |",
    ]
    for check in payload["checks"]:
        lines.append(f"| {check['name']} | `{check['status']}` | {check['detail']} |")
    lines.extend(["", "## Profile Backups", ""])
    for lane, backup in payload["profile_backups"].items():
        lines.append(f"- {lane}: `{backup}`")
    lines.extend(["", "## Changed Files", "", "| Action | Path |", "| --- | --- |"])
    for item in payload["changed_files"]:
        lines.append(f"| {item.get('action', '')} | `{item.get('path', '')}` |")
    lines.extend(["", "## After Runtime-Relevant Charts", ""])
    for lane in ("A1", "A2"):
        lines.extend([f"### {lane}", "", "| Chart | Symbol | Expert | Candidate | Account | Dry-run | Broker | Session | Smart trend | Max open | Cost | Spread | Guardian floor | Guardian loss | Halt file |", "| --- | --- | --- | --- | --- | --- | --- | --- | --- | ---: | ---: | ---: | --- | --- | --- |"])
        for row in payload["after"][lane]:
            if row["expert"] == "NO_EA":
                continue
            lines.append(
                "| {chart} | {symbol} | `{expert}` | `{candidate}` | `{account}` | `{dry}` | `{broker}` | `{session}` | `{smart}` | `{max_open}` | `{cost}` | `{spread}` | `{floor}` | `{loss}` | `{halt}` |".format(
                    chart=row["chart"],
                    symbol=row["symbol"],
                    expert=row["expert"],
                    candidate=row["InpCandidate"],
                    account=row["InpAllowedAccountLoginsCsv"],
                    dry=row["InpDryRunOnly"],
                    broker=row["InpBrokerActionAllowed"],
                    session=f"{row['InpTradeSessionStartHour']}->{row['InpTradeSessionEndHour']}" if row["InpTradeSessionStartHour"] else "",
                    smart=f"{row['InpSmartTrendFilterEnabled']} shadow={row['InpSmartTrendFilterShadowOnly']} require_D1={row['InpSmartTrendRequireD1']} D1={row['InpSmartTrendMinD1Aligned']} require_H1={row['InpSmartTrendRequireH1']} H1={row['InpSmartTrendMinH1Aligned']}",
                    max_open=row["InpMaxOpenPositionsPerInstance"],
                    cost=row["InpMaxEstimatedCostR"],
                    spread=row["InpMaxMeasuredSpreadPoints"],
                    floor=f"{row['InpDailyFloorAed']} next={row['InpNextDailyFloorAed']}".strip(),
                    loss=f"{row['InpDailyLossStopEnabled']} {row['InpDailyLossStopAed']}".strip(),
                    halt=row["InpEntryHaltFileName"],
                )
            )
        lines.append("")
    lines.extend(["## Claude Verification Focus", ""])
    for item in payload["claude_verification_focus"]:
        lines.append(f"- {item}")
    lines.append("")
    return "\n".join(lines)


if __name__ == "__main__":
    raise SystemExit(main())
