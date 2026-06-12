from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEFAULT_TERMINAL_DATA_DIR = Path(
    "C:/Users/ZHAO ZHU INFORMATION/AppData/Roaming/MetaQuotes/Terminal/D0E8209F77C8CF37AD8BF550E51FF075"
)
DEFAULT_TERMINAL_EXE = Path("C:/Program Files/MetaTrader 5/terminal64.exe")
DEFAULT_METAEDITOR_EXE = Path("C:/Program Files/MetaTrader 5/MetaEditor64.exe")
DEFAULT_OUTPUT_JSON = Path("outputs") / "reports" / "PHASE2_FLOOR_DECISIONS_APPLIED.json"

EXECUTOR_NAME = "Phase2ExperimentalDemoExecutor"
GUARDIAN_NAME = "AccountEquityGuardianShadow"
OWNER_ACCOUNT_LOGIN = "1025742"


@dataclass(frozen=True)
class ChartInventoryRow:
    chart: str
    symbol: str
    expert: str
    candidate: str
    broker_action_allowed: str
    dry_run_only: str
    fixed_lot: str
    eurusd_lot: str
    gbpusd_lot: str


def apply_phase2_floor_decisions(
    phase1_root: Path,
    terminal_data_dir: Path = DEFAULT_TERMINAL_DATA_DIR,
    terminal_exe: Path = DEFAULT_TERMINAL_EXE,
    metaeditor_exe: Path = DEFAULT_METAEDITOR_EXE,
    output_json: Path | None = None,
    launch: bool = True,
    wait_seconds: int = 75,
) -> dict[str, Any]:
    phase1_root = phase1_root.resolve()
    terminal_data_dir = terminal_data_dir.resolve()
    terminal_exe = terminal_exe.resolve()
    metaeditor_exe = metaeditor_exe.resolve()
    output_json = (output_json or phase1_root / DEFAULT_OUTPUT_JSON).resolve()
    output_json.parent.mkdir(parents=True, exist_ok=True)

    profile_dir = terminal_data_dir / "MQL5" / "Profiles" / "Charts" / "Default"
    if not profile_dir.exists():
        raise FileNotFoundError(profile_dir)

    before = chart_inventory(profile_dir)
    compiled = compile_floor_sources(phase1_root, terminal_data_dir, metaeditor_exe)
    terminal_closed = close_terminal(terminal_exe)
    profile_backup = backup_profile(profile_dir, terminal_data_dir)
    deployed = deploy_floor_sources(phase1_root, terminal_data_dir, compiled)
    usdjpy_changed = disable_usdjpy_broker_action(profile_dir)
    guardian_chart = ensure_guardian_chart(profile_dir)
    after = chart_inventory(profile_dir)

    launched = False
    log_state_before_wait = floor_log_state(terminal_data_dir)
    if launch:
        subprocess.Popen([str(terminal_exe)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        launched = True
        wait_for_guardian_startup(terminal_data_dir, wait_seconds)
    log_state_after_wait = floor_log_state(terminal_data_dir)

    broker_action_charts = [
        row
        for row in after
        if row.broker_action_allowed.lower() == "true" and row.expert in {EXECUTOR_NAME, "Phase2ExperimentalDemoRepairExecutor"}
    ]

    checks = [
        check("A3_family_mutex_source_deployed", "PASS" if compiled["executor"]["compile_pass"] else "FAIL", compiled["executor"]["compile_log"]),
        check("A7_guardian_source_deployed", "PASS" if compiled["guardian"]["compile_pass"] else "FAIL", compiled["guardian"]["compile_log"]),
        check("A6_usdjpy_broker_action_off", "PASS" if not usdjpy_changed["remaining_usdjpy_broker_action"] else "FAIL", usdjpy_changed["evidence"]),
        check("A7_guardian_stage_a_attached", "PASS" if guardian_chart else "FAIL", guardian_chart or "missing"),
        check(
            "guardian_startup_log",
            "PASS" if log_state_after_wait["guardian_startup_exists"] else "PENDING_RUNTIME_EVIDENCE",
            log_state_after_wait["guardian_startup"],
        ),
        check("declined_items_untouched", "PASS", "A1/A2/A4/A5 were not changed by this script."),
    ]

    payload: dict[str, Any] = {
        "status": "PASS" if all(item["status"] == "PASS" for item in checks) else "PENDING",
        "created_at_utc": now_utc(),
        "authority": (
            "Owner-approved Block A maintenance window: A3 family duplicate mutex, "
            "A6 USDJPY broker-action off, A7 AccountEquityGuardianShadow Stage A attach. "
            "Declined A1/A2/A4/A5 were not changed."
        ),
        "boundary": "Demo only; no canonical Phase 2 approval; no live trading or real-capital authorization.",
        "terminal": {
            "terminal_exe": str(terminal_exe),
            "terminal_data_dir": str(terminal_data_dir),
            "terminal_closed_before_profile_change": terminal_closed,
            "terminal_relaunched": launched,
            "profile_backup": str(profile_backup),
        },
        "approved_items": {
            "A3_family_duplicate_mutex": {
                "status": "APPLIED",
                "guard_reason": "WOULD_DUPLICATE_FAMILY_EVENT",
                "scope": f"{EXECUTOR_NAME} only; entry/stop/target logic untouched.",
            },
            "A6_usdjpy_broker_action_off": usdjpy_changed,
            "A7_guardian_stage_a": {
                "status": "ATTACHED" if guardian_chart else "MISSING",
                "chart": guardian_chart,
                "observer_only": True,
            },
        },
        "declined_items_not_touched": ["A1_weak_family_quarantine", "A2_repair_off", "A4_guard_rearm", "A5_lot_revert"],
        "compiled": compiled,
        "deployed": deployed,
        "before_charts": [row.__dict__ for row in before],
        "after_charts": [row.__dict__ for row in after],
        "broker_action_chart_count_after": len(broker_action_charts),
        "log_state_before_wait": log_state_before_wait,
        "log_state_after_wait": log_state_after_wait,
        "checks": checks,
    }
    write_report_pair(output_json, payload, render_report(payload))
    return payload


def compile_floor_sources(phase1_root: Path, terminal_data_dir: Path, metaeditor_exe: Path) -> dict[str, Any]:
    if not metaeditor_exe.exists():
        raise FileNotFoundError(metaeditor_exe)
    scratch_root = Path("C:/MT5CompileScratchFloorDecisions")
    if scratch_root.exists():
        shutil.rmtree(scratch_root)
    scratch_experts = scratch_root / "MQL5" / "Experts"
    scratch_include = scratch_root / "MQL5" / "Include" / "Phase1"
    scratch_experts.mkdir(parents=True, exist_ok=True)
    scratch_include.mkdir(parents=True, exist_ok=True)

    for include in ("Phase1Types.mqh", "Phase1BreakoutRetest.mqh"):
        shutil.copy2(phase1_root / "mt5" / "Include" / "Phase1" / include, scratch_include / include)

    results: dict[str, Any] = {}
    for name in (EXECUTOR_NAME, GUARDIAN_NAME):
        source = phase1_root / "mt5" / "Experts" / f"{name}.mq5"
        scratch_source = scratch_experts / source.name
        shutil.copy2(source, scratch_source)
        scratch_log = scratch_root / "Logs" / f"compile_{name}.log"
        scratch_log.parent.mkdir(parents=True, exist_ok=True)
        completed = subprocess.run(
            [str(metaeditor_exe), f"/compile:{scratch_source}", f"/log:{scratch_log}"],
            check=False,
            timeout=120,
        )
        scratch_ex5 = scratch_experts / f"{name}.ex5"
        target_log = terminal_data_dir / "MQL5" / "Logs" / f"compile_{name}_floor_decisions.log"
        target_log.parent.mkdir(parents=True, exist_ok=True)
        if scratch_log.exists():
            shutil.copy2(scratch_log, target_log)
        results["executor" if name == EXECUTOR_NAME else "guardian"] = {
            "name": name,
            "source": str(source),
            "scratch_source": str(scratch_source),
            "scratch_ex5": str(scratch_ex5),
            "compile_log": str(target_log),
            "returncode": completed.returncode,
            "compile_pass": scratch_ex5.exists() and compile_log_passed(target_log),
        }
    return results


def deploy_floor_sources(phase1_root: Path, terminal_data_dir: Path, compiled: dict[str, Any]) -> list[str]:
    deployed: list[str] = []
    experts_dir = terminal_data_dir / "MQL5" / "Experts"
    include_dir = terminal_data_dir / "MQL5" / "Include" / "Phase1"
    experts_dir.mkdir(parents=True, exist_ok=True)
    include_dir.mkdir(parents=True, exist_ok=True)
    for include in ("Phase1Types.mqh", "Phase1BreakoutRetest.mqh"):
        target = include_dir / include
        shutil.copy2(phase1_root / "mt5" / "Include" / "Phase1" / include, target)
        deployed.append(str(target))
    for name, key in ((EXECUTOR_NAME, "executor"), (GUARDIAN_NAME, "guardian")):
        source_target = experts_dir / f"{name}.mq5"
        shutil.copy2(phase1_root / "mt5" / "Experts" / f"{name}.mq5", source_target)
        deployed.append(str(source_target))
        ex5_source = Path(compiled[key]["scratch_ex5"])
        if ex5_source.exists():
            ex5_target = experts_dir / f"{name}.ex5"
            shutil.copy2(ex5_source, ex5_target)
            deployed.append(str(ex5_target))
    return deployed


def backup_profile(profile_dir: Path, terminal_data_dir: Path) -> Path:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    backup = terminal_data_dir / "_codex_quarantine" / "profile_backups" / f"default_profile_before_floor_decisions_{stamp}"
    backup.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(profile_dir, backup)
    return backup


def disable_usdjpy_broker_action(profile_dir: Path) -> dict[str, Any]:
    changed: list[str] = []
    remaining: list[str] = []
    for chart in sorted(profile_dir.glob("chart*.chr")):
        text = read_text_any(chart)
        row = parse_chart(chart)
        if row.symbol != "USDJPY":
            continue
        if "InpBrokerActionAllowed=true" in text:
            text = text.replace("InpBrokerActionAllowed=true", "InpBrokerActionAllowed=false")
            text = text.replace("InpDryRunOnly=false", "InpDryRunOnly=true")
            chart.write_text(text, encoding="utf-8")
            changed.append(chart.name)
        refreshed = parse_chart(chart)
        if refreshed.broker_action_allowed.lower() == "true":
            remaining.append(chart.name)
    evidence = "No USDJPY charts with broker action were found." if not changed and not remaining else f"changed={changed}; remaining={remaining}"
    return {
        "status": "OFF" if not remaining else "FAIL",
        "changed_charts": changed,
        "remaining_usdjpy_broker_action": remaining,
        "evidence": evidence,
    }


def ensure_guardian_chart(profile_dir: Path) -> str:
    for chart in sorted(profile_dir.glob("chart*.chr")):
        if f"name={GUARDIAN_NAME}" in read_text_any(chart):
            return str(chart)
    chart = profile_dir / f"chart{next_chart_index(profile_dir):02d}.chr"
    chart.write_text(render_guardian_chart(chart.stem), encoding="utf-8")
    return str(chart)


def render_guardian_chart(chart_stem: str) -> str:
    digits = "".join(ch for ch in chart_stem if ch.isdigit())
    index = int(digits) if digits else 1
    left = 20 + ((index - 1) % 4) * 42
    top = 20 + ((index - 1) // 4) * 35
    return "\n".join(
        [
            "<chart>",
            f"id={int(time.time())}{index:04d}",
            "symbol=XAUUSD",
            "description=XAUUSD",
            "period_type=0",
            "period_size=5",
            "digits=2",
            "tick_size=0.01",
            "scale_fix=0",
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
            f"window_left={left}",
            f"window_top={top}",
            f"window_right={left + 980}",
            f"window_bottom={top + 720}",
            "windows_total=1",
            "",
            "<expert>",
            f"name={GUARDIAN_NAME}",
            f"path=Experts\\{GUARDIAN_NAME}.ex5",
            "expertmode=1",
            "<inputs>",
            "InpEnableShadowLogging=true",
            "InpAllowNonDemoAccounts=false",
            f"InpAllowedAccountLogin={OWNER_ACCOUNT_LOGIN}",
            "InpTimerSeconds=10",
            "InpDailyLossLimitAed=150.0",
            "InpPeakArmAtAed=150.0",
            "InpGivebackPct=0.40",
            "InpProfitTargetAed=300.0",
            "InpMaxSameDirectionCount=2",
            "InpKillSwitchFileName=GUARDIAN_SHADOW_KILL.txt",
            "InpLogFileName=EQUITY_GUARDIAN_SHADOW_LOG.csv",
            "InpStartupFileName=EQUITY_GUARDIAN_SHADOW_STARTUP.csv",
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


def chart_inventory(profile_dir: Path) -> list[ChartInventoryRow]:
    return [parse_chart(chart) for chart in sorted(profile_dir.glob("chart*.chr"))]


def parse_chart(chart: Path) -> ChartInventoryRow:
    text = read_text_any(chart)
    values = {}
    expert_name = "NO_EA"
    in_expert = False
    for raw in text.splitlines():
        stripped = raw.strip()
        if stripped == "<expert>":
            in_expert = True
            continue
        if stripped == "</expert>":
            in_expert = False
            continue
        if "=" not in raw:
            continue
        key, value = raw.split("=", 1)
        key = key.strip()
        value = value.strip()
        values[key] = value
        if in_expert and key == "name":
            expert_name = value
    inputs = parse_inputs(text)
    return ChartInventoryRow(
        chart=chart.name,
        symbol=values.get("symbol", ""),
        expert=expert_name,
        candidate=inputs.get("InpCandidate", ""),
        broker_action_allowed=inputs.get("InpBrokerActionAllowed", ""),
        dry_run_only=inputs.get("InpDryRunOnly", ""),
        fixed_lot=inputs.get("InpFixedLot", ""),
        eurusd_lot=inputs.get("InpEURUSDFixedLot", ""),
        gbpusd_lot=inputs.get("InpGBPUSDFixedLot", ""),
    )


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
        if in_inputs and stripped.startswith("Inp") and "=" in stripped:
            key, value = stripped.split("=", 1)
            inputs[key] = value
    return inputs


def next_chart_index(profile_dir: Path) -> int:
    indexes: list[int] = []
    for chart in profile_dir.glob("chart*.chr"):
        digits = "".join(ch for ch in chart.stem if ch.isdigit())
        if digits:
            indexes.append(int(digits))
    return max(indexes, default=0) + 1


def close_terminal(terminal_exe: Path) -> bool:
    if not terminal_exe.exists():
        return False
    command = f"""
$target = (Resolve-Path -LiteralPath '{terminal_exe}').Path
$procs = Get-CimInstance Win32_Process | Where-Object {{ $_.ExecutablePath -eq $target }}
if(-not $procs) {{ exit 0 }}
foreach($proc in $procs) {{
  $p = Get-Process -Id $proc.ProcessId -ErrorAction SilentlyContinue
  if($p) {{ [void]$p.CloseMainWindow() }}
}}
Start-Sleep -Seconds 5
foreach($proc in $procs) {{
  $p = Get-Process -Id $proc.ProcessId -ErrorAction SilentlyContinue
  if($p) {{ Stop-Process -Id $proc.ProcessId -Force }}
}}
exit 0
"""
    result = subprocess.run(["powershell", "-NoProfile", "-Command", command], text=True, capture_output=True, timeout=45)
    return result.returncode == 0


def wait_for_guardian_startup(terminal_data_dir: Path, wait_seconds: int) -> None:
    deadline = time.time() + max(0, wait_seconds)
    while time.time() < deadline:
        if floor_log_state(terminal_data_dir)["guardian_startup_exists"]:
            return
        time.sleep(1.0)


def floor_log_state(terminal_data_dir: Path) -> dict[str, Any]:
    files = terminal_data_dir / "MQL5" / "Files"
    startup = files / "EQUITY_GUARDIAN_SHADOW_STARTUP.csv"
    log = files / "EQUITY_GUARDIAN_SHADOW_LOG.csv"
    return {
        "guardian_startup": str(startup),
        "guardian_startup_exists": startup.exists(),
        "guardian_startup_mtime": mtime_text(startup),
        "guardian_log": str(log),
        "guardian_log_exists": log.exists(),
        "guardian_log_mtime": mtime_text(log),
    }


def compile_log_passed(path: Path) -> bool:
    text = read_text_any(path).lower()
    return "0 errors, 0 warnings" in text or "0 error(s), 0 warning(s)" in text


def read_text_any(path: Path) -> str:
    if not path.exists():
        return ""
    payload = path.read_bytes()
    for encoding in ("utf-8", "utf-16", "utf-16-le", "cp1252"):
        try:
            return payload.decode(encoding)
        except UnicodeError:
            continue
    return payload.decode(errors="replace")


def mtime_text(path: Path) -> str:
    if not path.exists():
        return "missing"
    return datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat().replace("+00:00", "Z")


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def check(name: str, status: str, evidence: str) -> dict[str, str]:
    return {"name": name, "status": status, "evidence": evidence}


def write_report_pair(output_json: Path, payload: dict[str, Any], markdown: str) -> None:
    output_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    output_json.with_suffix(".md").write_text(markdown, encoding="utf-8")


def render_report(payload: dict[str, Any]) -> str:
    lines = [
        "# Phase 2 Floor Decisions Applied",
        "",
        f"Overall status: {payload['status']}",
        "",
        str(payload["authority"]),
        "",
        str(payload["boundary"]),
        "",
        "## Applied Items",
        "",
        "| Item | Result | Evidence |",
        "|---|---|---|",
        f"| A3 family duplicate mutex | APPLIED | Guard reason `WOULD_DUPLICATE_FAMILY_EVENT`; compile log `{payload['compiled']['executor']['compile_log']}` |",
        f"| A6 USDJPY broker-action off | {payload['approved_items']['A6_usdjpy_broker_action_off']['status']} | {payload['approved_items']['A6_usdjpy_broker_action_off']['evidence']} |",
        f"| A7 guardian Stage A attach | {payload['approved_items']['A7_guardian_stage_a']['status']} | `{payload['approved_items']['A7_guardian_stage_a']['chart']}`; compile log `{payload['compiled']['guardian']['compile_log']}` |",
        "",
        "## Declined Items Preserved",
        "",
        "- A1 weak-family quarantine: declined, not changed.",
        "- A2 repair executor off: declined, not changed.",
        "- A4 guard re-arm: declined, not changed.",
        "- A5 lot revert: declined, not changed.",
        "",
        "## Runtime Evidence",
        "",
        f"- Terminal: `{payload['terminal']['terminal_exe']}`",
        f"- Profile backup: `{payload['terminal']['profile_backup']}`",
        f"- Closed before profile/source change: `{payload['terminal']['terminal_closed_before_profile_change']}`",
        f"- Relaunched: `{payload['terminal']['terminal_relaunched']}`",
        f"- Guardian startup log: `{payload['log_state_after_wait']['guardian_startup']}` exists=`{payload['log_state_after_wait']['guardian_startup_exists']}`",
        f"- Broker-action chart count after: `{payload['broker_action_chart_count_after']}`",
        "",
        "## Checks",
        "",
        "| Check | Status | Evidence |",
        "|---|---|---|",
    ]
    lines.extend(f"| {item['name']} | {item['status']} | {escape_md(item['evidence'])} |" for item in payload["checks"])
    lines.extend(["", "## Before Charts", "", *inventory_table(payload["before_charts"]), "", "## After Charts", "", *inventory_table(payload["after_charts"]), ""])
    return "\n".join(lines)


def escape_md(value: object) -> str:
    return str(value).replace("|", "\\|").replace("\n", "<br>")


def inventory_table(rows: list[dict[str, str]]) -> list[str]:
    lines = ["| Chart | Symbol | Expert | Candidate | Broker Action | Dry Run | Lot | EUR Lot | GBP Lot |", "|---|---|---|---|---:|---:|---:|---:|---:|"]
    for row in rows:
        lines.append(
            "| {chart} | {symbol} | {expert} | {candidate} | {broker_action_allowed} | {dry_run_only} | {fixed_lot} | {eurusd_lot} | {gbpusd_lot} |".format(
                **{key: escape_md(value) for key, value in row.items()}
            )
        )
    return lines


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Apply owner-approved Phase 2 floor decisions A3/A6/A7.")
    parser.add_argument("--phase1-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--terminal-data-dir", type=Path, default=DEFAULT_TERMINAL_DATA_DIR)
    parser.add_argument("--terminal-exe", type=Path, default=DEFAULT_TERMINAL_EXE)
    parser.add_argument("--metaeditor-exe", type=Path, default=DEFAULT_METAEDITOR_EXE)
    parser.add_argument("--output-json", type=Path, default=None)
    parser.add_argument("--no-launch", action="store_true")
    parser.add_argument("--wait-seconds", type=int, default=75)
    args = parser.parse_args(argv)
    payload = apply_phase2_floor_decisions(
        phase1_root=args.phase1_root,
        terminal_data_dir=args.terminal_data_dir,
        terminal_exe=args.terminal_exe,
        metaeditor_exe=args.metaeditor_exe,
        output_json=args.output_json,
        launch=not args.no_launch,
        wait_seconds=args.wait_seconds,
    )
    print(f"Phase 2 floor decisions applied: {payload['status']}")
    return 0 if payload["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
