from __future__ import annotations

import argparse
import csv
import json
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
DEFAULT_OUTPUT_JSON = Path("outputs") / "reports" / "XAUUSD_ROUND_FAMILY_QUARANTINE_APPLIED_2026_06_17.json"
DEFAULT_OUTPUT_MD = Path("outputs") / "reports" / "XAUUSD_ROUND_FAMILY_QUARANTINE_APPLIED_2026_06_17.md"

TARGET_SYMBOL = "XAUUSD"
TARGET_CANDIDATES = {"symbol_normalized_round_retest_v0", "round_number_retest_v0"}
PROTECTED_CANDIDATES = {"breakout_retest", "swing_breakout_retest_v0"}
QUARANTINED_STATUS = "OWNER_APPROVED_ROUND_FAMILY_QUARANTINED"
OWNER_DECISION_DOC = "xau-usd/xauusd-phase1/docs/XAUUSD_ROUND_FAMILY_QUARANTINE_OWNER_DECISION_2026_06_17.md"
REVIEWER_SIGNOFF = "XAUUSD_REVIEWER_SIGNOFF_ROUND_QUARANTINE_2026_06_17.md"


@dataclass(frozen=True)
class ApplyOutput:
    status: str
    json_path: Path
    markdown_path: Path
    changed_charts: tuple[str, ...]


def apply_round_family_quarantine(
    phase1_root: Path,
    *,
    terminal_data_dir: Path = DEFAULT_TERMINAL_DATA_DIR,
    terminal_exe: Path = DEFAULT_TERMINAL_EXE,
    output_json: Path | None = None,
    owner_name: str = "Muhammad Ali Khan",
    apply: bool = False,
    launch: bool = True,
) -> ApplyOutput:
    phase1_root = phase1_root.resolve()
    terminal_data_dir = terminal_data_dir.resolve()
    terminal_exe = terminal_exe.resolve()
    output_json = (output_json or phase1_root / DEFAULT_OUTPUT_JSON).resolve()
    output_md = output_json.with_suffix(".md") if output_json.name != DEFAULT_OUTPUT_JSON.name else phase1_root / DEFAULT_OUTPUT_MD
    output_json.parent.mkdir(parents=True, exist_ok=True)

    profile = terminal_data_dir / "MQL5" / "Profiles" / "Charts" / "Default"
    files_dir = terminal_data_dir / "MQL5" / "Files"
    if not profile.exists():
        raise FileNotFoundError(f"Default profile not found: {profile}")

    pre_close_inventory = chart_inventory(profile)
    pre_close_target = target_charts(pre_close_inventory)
    order_counts_before = order_log_counts(files_dir, pre_close_target)
    terminal_closed = close_terminal(terminal_exe) if apply else False
    before_inventory = chart_inventory(profile)
    before_target = target_charts(before_inventory)
    before_protected = protected_charts(before_inventory)
    missing = sorted(TARGET_CANDIDATES - {row["candidate"] for row in before_target})
    if missing:
        raise RuntimeError(f"Missing target XAUUSD charts for: {', '.join(missing)}")

    backup_dir = ""
    changed_paths: list[Path] = []
    if apply:
        stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        backup = terminal_data_dir / "_codex_quarantine" / "profile_backups" / f"default_profile_before_round_family_quarantine_{stamp}"
        shutil.copytree(profile, backup)
        backup_dir = str(backup)
        for item in before_target:
            path = Path(item["path"])
            changed = quarantine_chart(path)
            if changed:
                changed_paths.append(path)
    after_inventory = chart_inventory(profile)
    after_target = target_charts(after_inventory)
    after_protected = protected_charts(after_inventory)
    changed_chart_names = tuple(path.name for path in changed_paths)

    relaunched = False
    if apply and launch:
        subprocess.Popen([str(terminal_exe)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        relaunched = True
        time.sleep(7.0)

    order_counts_after = order_log_counts(files_dir, after_target)
    startup_counts_after = startup_log_counts(files_dir, after_target)
    verification = verify_application(
        before_target=before_target,
        after_target=after_target,
        before_protected=before_protected,
        after_protected=after_protected,
        changed_chart_names=changed_chart_names,
        order_counts_before=order_counts_before,
        order_counts_after=order_counts_after,
    )
    status = "ROUND_FAMILY_QUARANTINE_APPLIED" if apply and verification["status"] == "PASS" else "DRY_RUN_READY"
    if apply and verification["status"] != "PASS":
        status = "ROUND_FAMILY_QUARANTINE_APPLIED_WITH_VERIFICATION_WARNINGS"

    payload: dict[str, Any] = {
        "status": status,
        "created_at_utc": utc_now(),
        "boundary": "Demo-only controlled maintenance window. No live/real-capital authorization and no canonical Phase 2 approval.",
        "owner": {
            "name": owner_name,
            "decision": "APPROVE_BOTH_ITEMS",
            "approved_candidates": sorted(TARGET_CANDIDATES),
            "decision_doc": OWNER_DECISION_DOC,
            "reviewer_signoff": REVIEWER_SIGNOFF,
        },
        "scope": {
            "symbol": TARGET_SYMBOL,
            "target_candidates": sorted(TARGET_CANDIDATES),
            "explicitly_out_of_scope": [
                "broad afternoon ban",
                "direction-only rule",
                "cost-threshold runtime rule",
                "breakout_retest changes",
                "swing_breakout_retest_v0 changes",
                "EURUSD/GBPUSD round-family changes",
                "repair-v1 lane changes",
                "live trading",
                "real capital",
            ],
        },
        "terminal": {
            "terminal_exe": str(terminal_exe),
            "terminal_data_dir": str(terminal_data_dir),
            "profile": str(profile),
            "terminal_closed_before_edit": terminal_closed,
            "terminal_relaunched": relaunched,
            "profile_backup_dir": backup_dir or "NOT_CREATED_DRY_RUN",
        },
        "pre_close_target_charts": pre_close_target,
        "before_target_charts": before_target,
        "after_target_charts": after_target,
        "before_protected_charts": before_protected,
        "after_protected_charts": after_protected,
        "changed_charts": list(changed_chart_names),
        "order_log_counts_before": order_counts_before,
        "order_log_counts_after": order_counts_after,
        "startup_log_counts_after": startup_counts_after,
        "verification": verification,
        "rollback": {
            "profile_backup_dir": backup_dir or "NOT_CREATED_DRY_RUN",
            "instruction": "Close the standard MT5 terminal, replace the Default profile with this backup, then relaunch.",
        },
    }
    output_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    output_md.write_text(render_markdown(payload), encoding="utf-8")
    return ApplyOutput(status=status, json_path=output_json, markdown_path=output_md, changed_charts=changed_chart_names)


def chart_inventory(profile: Path) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for chart in sorted(profile.glob("chart*.chr")):
        text = read_chart_text(chart)
        inputs = parse_inputs(text)
        rows.append(
            {
                "chart": chart.name,
                "path": str(chart),
                "symbol": parse_line(text, "symbol"),
                "expert": parse_line(text, "name"),
                "dry_run": inputs.get("InpDryRunOnly", ""),
                "broker_action_allowed": inputs.get("InpBrokerActionAllowed", ""),
                "candidate": inputs.get("InpCandidate", ""),
                "candidate_status": inputs.get("InpCandidateStatus", ""),
                "target_symbol": inputs.get("InpTargetSymbol", ""),
                "qualified_symbols": inputs.get("InpQualifiedSymbolsCsv", ""),
                "signal_log": inputs.get("InpAttachmentLogFileName", ""),
                "startup_log": inputs.get("InpStartupLogFileName", ""),
                "order_log": inputs.get("InpOrderLogFileName", ""),
            }
        )
    return rows


def target_charts(inventory: list[dict[str, str]]) -> list[dict[str, str]]:
    return [
        row
        for row in inventory
        if row["symbol"] == TARGET_SYMBOL
        and row["candidate"] in TARGET_CANDIDATES
        and row["expert"] == "Phase2ExperimentalDemoExecutor"
    ]


def protected_charts(inventory: list[dict[str, str]]) -> list[dict[str, str]]:
    return [
        row
        for row in inventory
        if row["symbol"] == TARGET_SYMBOL
        and row["candidate"] in PROTECTED_CANDIDATES
        and row["expert"] == "Phase2ExperimentalDemoExecutor"
    ]


def quarantine_chart(path: Path) -> bool:
    text = read_chart_text(path)
    original = text
    replacements = {
        "InpDryRunOnly": "true",
        "InpBrokerActionAllowed": "false",
        "InpCandidateStatus": QUARANTINED_STATUS,
    }
    lines = []
    for line in text.splitlines():
        if "=" in line:
            key, _value = line.split("=", 1)
            if key in replacements:
                line = f"{key}={replacements[key]}"
        lines.append(line)
    new_text = "\n".join(lines) + ("\n" if text.endswith("\n") else "")
    if new_text != original:
        path.write_text(new_text, encoding="utf-8")
        return True
    return False


def verify_application(
    *,
    before_target: list[dict[str, str]],
    after_target: list[dict[str, str]],
    before_protected: list[dict[str, str]],
    after_protected: list[dict[str, str]],
    changed_chart_names: tuple[str, ...],
    order_counts_before: dict[str, int],
    order_counts_after: dict[str, int],
) -> dict[str, Any]:
    checks: list[dict[str, str]] = []
    after_by_candidate = {row["candidate"]: row for row in after_target}
    for candidate in sorted(TARGET_CANDIDATES):
        row = after_by_candidate.get(candidate, {})
        passed = (
            row.get("symbol") == TARGET_SYMBOL
            and row.get("dry_run") == "true"
            and row.get("broker_action_allowed") == "false"
            and row.get("candidate_status") == QUARANTINED_STATUS
        )
        checks.append(
            {
                "check": f"{candidate}_quarantined",
                "status": "PASS" if passed else "FAIL",
                "detail": json.dumps(row, sort_keys=True),
            }
        )
    protected_before = comparable_chart_rows(before_protected)
    protected_after = comparable_chart_rows(after_protected)
    protected_unchanged = protected_before == protected_after
    checks.append(
        {
            "check": "protected_breakout_core_unchanged",
            "status": "PASS" if protected_unchanged else "FAIL",
            "detail": f"before={protected_before}; after={protected_after}",
        }
    )
    expected_changed = {row["chart"] for row in before_target}
    checks.append(
        {
            "check": "only_target_charts_changed_by_script",
            "status": "PASS" if set(changed_chart_names) == expected_changed else "FAIL",
            "detail": f"changed={list(changed_chart_names)} expected={sorted(expected_changed)}",
        }
    )
    order_counts_stable = order_counts_before == order_counts_after
    checks.append(
        {
            "check": "target_order_logs_no_new_rows_during_window",
            "status": "PASS" if order_counts_stable else "WARN",
            "detail": f"before={order_counts_before}; after={order_counts_after}",
        }
    )
    status = "PASS" if all(row["status"] == "PASS" for row in checks) else "WARN"
    if any(row["status"] == "FAIL" for row in checks):
        status = "FAIL"
    return {"status": status, "checks": checks}


def comparable_chart_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    keys = [
        "chart",
        "symbol",
        "expert",
        "dry_run",
        "broker_action_allowed",
        "candidate",
        "candidate_status",
        "target_symbol",
        "qualified_symbols",
    ]
    return [{key: row.get(key, "") for key in keys} for row in sorted(rows, key=lambda item: item["chart"])]


def order_log_counts(files_dir: Path, rows: list[dict[str, str]]) -> dict[str, int]:
    return {
        row["order_log"]: csv_row_count(files_dir / row["order_log"])
        for row in rows
        if row.get("order_log")
    }


def startup_log_counts(files_dir: Path, rows: list[dict[str, str]]) -> dict[str, int]:
    return {
        row["startup_log"]: csv_row_count(files_dir / row["startup_log"])
        for row in rows
        if row.get("startup_log")
    }


def csv_row_count(path: Path) -> int:
    if not path.exists():
        return 0
    try:
        with path.open("r", encoding="utf-8-sig", errors="replace", newline="") as handle:
            return sum(1 for _row in csv.reader(handle))
    except OSError:
        return 0


def parse_inputs(text: str) -> dict[str, str]:
    inputs: dict[str, str] = {}
    in_inputs = False
    for raw in text.splitlines():
        line = raw.strip()
        if line == "<inputs>":
            in_inputs = True
            continue
        if line == "</inputs>":
            in_inputs = False
            continue
        if in_inputs and "=" in line:
            key, value = line.split("=", 1)
            inputs[key] = value
    return inputs


def parse_line(text: str, key: str) -> str:
    prefix = f"{key}="
    for raw in text.splitlines():
        line = raw.strip()
        if line.startswith(prefix):
            return line.split("=", 1)[1]
    return ""


def close_terminal(terminal_exe: Path) -> bool:
    ps = f"""
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
    result = subprocess.run(["powershell", "-NoProfile", "-Command", ps], text=True, capture_output=True, timeout=30)
    return result.returncode == 0


def read_chart_text(path: Path) -> str:
    data = path.read_bytes()
    for encoding in ("utf-8", "utf-16", "utf-16-le", "cp1252"):
        try:
            return data.decode(encoding)
        except UnicodeError:
            continue
    return data.decode(errors="replace")


def render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# XAUUSD Round-Family Quarantine Applied - 2026-06-17",
        "",
        f"Overall status: `{payload['status']}`",
        "",
        str(payload["boundary"]),
        "",
        "## Owner Decision",
        "",
        f"- Owner: `{payload['owner']['name']}`",
        f"- Decision: `{payload['owner']['decision']}`",
        f"- Approved candidates: `{', '.join(payload['owner']['approved_candidates'])}`",
        f"- Owner packet: `{payload['owner']['decision_doc']}`",
        f"- Reviewer sign-off: `{payload['owner']['reviewer_signoff']}`",
        "",
        "## Scope",
        "",
        f"- Symbol: `{payload['scope']['symbol']}`",
        f"- Targets: `{', '.join(payload['scope']['target_candidates'])}`",
        "- Out of scope: `" + ", ".join(payload["scope"]["explicitly_out_of_scope"]) + "`",
        "",
        "## Maintenance Window",
        "",
        f"- Terminal: `{payload['terminal']['terminal_exe']}`",
        f"- Data folder: `{payload['terminal']['terminal_data_dir']}`",
        f"- Profile: `{payload['terminal']['profile']}`",
        f"- Terminal closed before edit: `{str(payload['terminal']['terminal_closed_before_edit']).lower()}`",
        f"- Terminal relaunched: `{str(payload['terminal']['terminal_relaunched']).lower()}`",
        f"- Profile backup: `{payload['terminal']['profile_backup_dir']}`",
        "",
        "## Target Charts",
        "",
        table(payload["after_target_charts"], ["chart", "symbol", "candidate", "dry_run", "broker_action_allowed", "candidate_status", "signal_log", "order_log"]),
        "",
        "## Protected Breakout Charts",
        "",
        table(payload["after_protected_charts"], ["chart", "symbol", "candidate", "dry_run", "broker_action_allowed", "candidate_status", "signal_log", "order_log"]),
        "",
        "## Verification",
        "",
        table(payload["verification"]["checks"], ["check", "status", "detail"]),
        "",
        "## Order Log Row Counts",
        "",
        table(
            [
                {
                    "order_log": key,
                    "before_rows": str(payload["order_log_counts_before"].get(key, "")),
                    "after_rows": str(payload["order_log_counts_after"].get(key, "")),
                }
                for key in sorted(set(payload["order_log_counts_before"]) | set(payload["order_log_counts_after"]))
            ],
            ["order_log", "before_rows", "after_rows"],
        ),
        "",
        "## Startup Log Row Counts After Relaunch",
        "",
        table(
            [{"startup_log": key, "rows": str(value)} for key, value in payload["startup_log_counts_after"].items()],
            ["startup_log", "rows"],
        ),
        "",
        "Note: `Phase2ExperimentalDemoExecutor` intentionally refuses to initialize when `InpDryRunOnly=true` or `InpBrokerActionAllowed=false`. For this reversible quarantine, the profile input values are the broker-action proof; existing historical logs are preserved.",
        "",
        "## Rollback",
        "",
        f"- Backup: `{payload['rollback']['profile_backup_dir']}`",
        f"- Instruction: {payload['rollback']['instruction']}",
        "",
    ]
    return "\n".join(lines)


def table(rows: list[dict[str, Any]], columns: list[str]) -> str:
    if not rows:
        return "_No rows._"
    output = [
        "| " + " | ".join(columns) + " |",
        "| " + " | ".join("---" for _ in columns) + " |",
    ]
    for row in rows:
        output.append("| " + " | ".join(str(row.get(column, "")) for column in columns) + " |")
    return "\n".join(output)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Apply owner-approved XAUUSD round-family quarantine to the standard demo MT5 profile.")
    parser.add_argument("--phase1-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--terminal-data-dir", type=Path, default=DEFAULT_TERMINAL_DATA_DIR)
    parser.add_argument("--terminal-exe", type=Path, default=DEFAULT_TERMINAL_EXE)
    parser.add_argument("--output-json", type=Path, default=None)
    parser.add_argument("--owner-name", default="Muhammad Ali Khan")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--no-launch", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    output = apply_round_family_quarantine(
        args.phase1_root,
        terminal_data_dir=args.terminal_data_dir,
        terminal_exe=args.terminal_exe,
        output_json=args.output_json,
        owner_name=args.owner_name,
        apply=args.apply,
        launch=not args.no_launch,
    )
    print(f"{output.status}: changed charts={', '.join(output.changed_charts) or 'none'}")
    print(output.json_path)
    print(output.markdown_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
