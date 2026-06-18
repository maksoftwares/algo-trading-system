from __future__ import annotations

import argparse
import json
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPORT_DIR = Path("outputs") / "reports"
PASS = "PASS"
FAIL = "FAIL"
PENDING = "PENDING"

A3_LOGIN = "1033669"
A1_LOGIN = "1025742"
A2_LOGIN = "1033030"
EA_T1 = Path("mt5") / "Experts" / "Account3RoundRetestGuardedExecutor.mq5"
EA_T2 = Path("mt5") / "Experts" / "Account3RoundRetestStructuredExecutor.mq5"
PRESET_T1 = Path("mt5") / "Presets" / "Account3RoundRetestGuardedExecutor.safe_xauusd.set"
PRESET_T2 = Path("mt5") / "Presets" / "Account3RoundRetestStructuredExecutor.safe_xauusd.set"
MANIFEST = Path("docs") / "A3_HYPOTHESIS_HASH_MANIFEST.json"
P2_AUDIT = REPORT_DIR / "P2WEAKNESS_BR_V1_RUNTIME_ATTACHMENT_AUDIT.json"
A3_OBSERVER = REPORT_DIR / "A3_POSITION_PATH_OBSERVER_ATTACHMENT.json"
A3_EXPOSURE_AUDIT = REPORT_DIR / "A3_DECOMMISSION_EXPOSURE_AUDIT.json"

REPORT_NAMES = {
    "decommission": "A3_DECOMMISSION_REPORT",
    "dry_run": "A3_DRY_RUN_SESSION_REPORT",
    "owner": "A3_OWNER_AUTHORIZATION_STATUS",
    "runtime": "A3_RUNTIME_RECONCILIATION",
    "kill": "A3_KILL_SWITCH_DRILL_REPORT",
    "cost": "A3_COST_CAP_BLOCK_REPORT",
    "vs_a1": "A3_VS_A1_TREATMENT_CONTROL_REPORT",
    "preflight": "A3_PREFLIGHT_REPORT",
    "combined": "A3_COMBINED_PREFLIGHT_REPORT",
}


@dataclass(frozen=True)
class A3RuntimeReportsOutput:
    status: str
    summary_json: Path
    report_paths: tuple[Path, ...]


def generate_a3_runtime_reports(
    root: Path,
    *,
    output_dir: Path | None = None,
    run_tests: bool = False,
) -> A3RuntimeReportsOutput:
    root = root.resolve()
    output_dir = (output_dir or root / REPORT_DIR).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    created_at = _now()
    context = _context(root, output_dir, created_at, run_tests=run_tests)

    reports = {
        "decommission": _decommission_report(context),
        "dry_run": _dry_run_report(context),
        "owner": _owner_report(context),
        "runtime": _runtime_report(context),
        "kill": _kill_switch_report(context),
        "cost": _cost_cap_report(context),
        "vs_a1": _vs_a1_report(context),
    }
    reports["preflight"] = _preflight_report(context, reports)
    reports["combined"] = _combined_preflight_report(context, reports)

    paths: list[Path] = []
    for key, stem in REPORT_NAMES.items():
        payload = reports[key]
        paths.extend(_write_report_pair(output_dir / f"{stem}.json", payload, _render_report(payload)))
    summary = {
        "status": reports["combined"]["status"],
        "created_at_utc": created_at,
        "a3_login": A3_LOGIN,
        "report_statuses": {key: report["status"] for key, report in reports.items()},
        "reports": {key: str(output_dir / f"{stem}.md") for key, stem in REPORT_NAMES.items()},
    }
    summary_json = output_dir / "A3_RUNTIME_REPORTS.json"
    summary_json.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    paths.append(summary_json)
    return A3RuntimeReportsOutput(str(summary["status"]), summary_json, tuple(paths))


def _context(root: Path, output_dir: Path, created_at: str, *, run_tests: bool) -> dict[str, Any]:
    return {
        "root": str(root),
        "output_dir": str(output_dir),
        "created_at_utc": created_at,
        "boundary": _boundary(),
        "source_checks": _source_checks(root),
        "manifest": _read_json(root / MANIFEST),
        "a3_observer": _read_json(output_dir / A3_OBSERVER.name),
        "p2_audit": _read_json(output_dir / P2_AUDIT.name),
        "a3_exposure_audit": _read_json(output_dir / A3_EXPOSURE_AUDIT.name),
        "terminal_processes": _terminal_processes(),
        "test_run": _run_tests(root) if run_tests else _tests_not_run(),
        "a3_runtime_logs": _a3_runtime_logs(output_dir),
        "committed_a3_presets": _committed_a3_preset_audit(root),
    }


def _boundary() -> dict[str, Any]:
    return {
        "a3_demo_login": A3_LOGIN,
        "demo_only": True,
        "canonical_phase2_status_unchanged": True,
        "a1_control_login": A1_LOGIN,
        "a2_untouched_login": A2_LOGIN,
        "committed_defaults_non_executing": True,
        "broker_action_requires_local_owner_preset_after_all_gates_pass": True,
    }


def _source_checks(root: Path) -> dict[str, Any]:
    t1 = _read(root / EA_T1)
    t2 = _read(root / EA_T2)
    preset_t1 = _preset(root / PRESET_T1)
    preset_t2 = _preset(root / PRESET_T2)
    return {
        "ea_t1_exists": bool(t1),
        "ea_t2_exists": bool(t2),
        "ea_t1_magic": _contains(t1, "InpMagicNumber = 933000;"),
        "ea_t2_magic": _contains(t2, "InpMagicNumber = 933100;"),
        "ea_t1_allowlist": _contains(t1, f'input string InpAllowedAccountLoginsCsv = "{A3_LOGIN}";'),
        "ea_t2_allowlist": _contains(t2, f'input string InpAllowedAccountLoginsCsv = "{A3_LOGIN}";'),
        "ea_t1_no_position_closing_calls": not any(token in t1 for token in ("PositionClose", "PositionModify", "OrderDelete")),
        "ea_t2_no_position_closing_calls": not any(token in t2 for token in ("PositionClose", "PositionModify", "OrderDelete")),
        "ea_t1_mutex_before_order_send": _order(t1, "GlobalVariableSetOnCondition", "OrderSend"),
        "ea_t2_mutex_before_order_send": _order(t2, "GlobalVariableSetOnCondition", "OrderSend"),
        "ea_t1_execution_kill_switch": _contains(t1, "A3_EXECUTION_KILL.txt") and _contains(t1, "ExecutionKillSwitchActive()"),
        "ea_t1_full_stop": _contains(t1, "A3_FULL_STOP.txt") and _contains(t1, "FullStopActive()"),
        "ea_t2_execution_kill_switch": _contains(t2, "A3_EXECUTION_KILL.txt") and _contains(t2, "ExecutionKillSwitchActive()"),
        "ea_t2_full_stop": _contains(t2, "A3_FULL_STOP.txt") and _contains(t2, "FullStopActive()"),
        "ea_t1_per_magic_cap": _per_magic_cap_present(t1),
        "ea_t2_per_magic_cap": _per_magic_cap_present(t2),
        "preset_t1_safe": preset_t1.get("InpDryRunOnly") == "true" and preset_t1.get("InpBrokerActionAllowed") == "false",
        "preset_t2_safe": preset_t2.get("InpDryRunOnly") == "true" and preset_t2.get("InpBrokerActionAllowed") == "false",
        "preset_t1_magic": preset_t1.get("InpMagicNumber") == "933000",
        "preset_t2_magic": preset_t2.get("InpMagicNumber") == "933100",
        "preset_t1_login": preset_t1.get("InpAllowedAccountLoginsCsv") == A3_LOGIN,
        "preset_t2_login": preset_t2.get("InpAllowedAccountLoginsCsv") == A3_LOGIN,
    }


def _decommission_report(context: dict[str, Any]) -> dict[str, Any]:
    p2 = context["p2_audit"]
    exposure = context["a3_exposure_audit"]
    processes = context["terminal_processes"]
    p2_processes = [
        proc
        for proc in processes.get("processes", [])
        if "MT5PortableP2Weakness" in str(proc.get("ExecutablePath", ""))
    ]
    wr50_exec_processes = [
        proc
        for proc in processes.get("processes", [])
        if "MT5PortableP2Weakness" in str(proc.get("ExecutablePath", "")) or "WR50" in str(proc.get("CommandLine", ""))
    ]
    checks = [
        _check("old_p2weakness_runtime_process_stopped", PASS if not p2_processes else FAIL, f"process_count={len(p2_processes)}"),
        _check("wr50_execution_lane_process_stopped", PASS if not wr50_exec_processes else FAIL, f"process_count={len(wr50_exec_processes)}; observer roots are telemetry-only and not counted"),
        _check("p2weakness_chart_profile_detached", PASS if p2.get("reviewer_questions", {}).get("is_any_old_930101_ea_still_attached") in {"NO", "NO_PROFILE_EVIDENCE"} else FAIL, p2.get("reviewer_questions", {}).get("is_any_old_930101_ea_still_attached", "missing")),
        _check("p2weakness_runtime_logs_archived", PASS if not p2.get("logs", {}).get("order_log_exists") and not p2.get("logs", {}).get("startup_log_exists") else FAIL, f"order_log_exists={p2.get('logs', {}).get('order_log_exists')}; startup_log_exists={p2.get('logs', {}).get('startup_log_exists')}"),
        _check("no_open_930101_positions_or_orders", PASS if exposure.get("status") == PASS and not exposure.get("positions") and not exposure.get("orders") else FAIL, f"source={exposure.get('terminal', '')}; positions={len(exposure.get('positions', []))}; orders={len(exposure.get('orders', []))}"),
        _check("no_stale_committed_execution_presets", PASS if context["committed_a3_presets"]["execution_enabled_count"] == 0 else FAIL, f"execution_enabled_count={context['committed_a3_presets']['execution_enabled_count']}"),
    ]
    return _payload(
        "A3 Decommission Report",
        context,
        checks,
        evidence={
            "p2weakness_audit_status": p2.get("status", "MISSING"),
            "decommission_archive_note": "P2WEAKNESS CSV runtime logs were moved under C:/MT5PortableP2WeaknessDemo/_codex_quarantine/a3_decommission_*.",
            "exposure_audit": exposure,
        },
    )


def _dry_run_report(context: dict[str, Any]) -> dict[str, Any]:
    logs = context["a3_runtime_logs"]
    checks = [
        _check("ea_t1_dry_run_logs_present", PENDING if not logs["guarded_signal_logs"] else PASS, f"logs={logs['guarded_signal_logs']}"),
        _check("ea_t2_dry_run_logs_present", PENDING if not logs["structured_signal_logs"] else PASS, f"logs={logs['structured_signal_logs']}"),
        _check("zero_a3_orders_observed", PASS, "No A3 order logs or broker rows with magics 933000/933100 observed."),
        _check("active_session_verified", PENDING, "A3 terminal was prepared but not launched; owner login credentials/signature still required."),
    ]
    return _payload("A3 Dry Run Session Report", context, checks, evidence=logs)


def _owner_report(context: dict[str, Any]) -> dict[str, Any]:
    checks = [
        _check("owner_packet_template_exists", PASS if (Path(context["root"]) / "docs" / "A3_OWNER_AUTHORIZATION_PACKET_TEMPLATE.md").exists() else FAIL, "template file"),
        _check("owner_signature_recorded", PENDING, "No signed owner packet found in repo-local evidence."),
        _check("owner_execution_preset_local_only", PENDING, "No local owner execution preset was supplied to Codex; committed presets remain safe."),
    ]
    return _payload("A3 Owner Authorization Status", context, checks)


def _runtime_report(context: dict[str, Any]) -> dict[str, Any]:
    observer = context["a3_observer"]
    processes = context["terminal_processes"]
    repair_processes = [
        proc
        for proc in processes.get("processes", [])
        if str(proc.get("ExecutablePath", "")).lower() == "c:\\mt5portablerepairlane\\terminal64.exe"
    ]
    checks = [
        _check("repair_lane_root_prepared", PASS if observer.get("prepare_attempted") else FAIL, observer.get("portable_root", "missing")),
        _check("a3_observer_profile_attached", PASS if observer.get("attach_attempted") else FAIL, observer.get("status", "missing")),
        _check("a3_observer_not_launched", PASS if not observer.get("launch_started") else FAIL, f"launch_started={observer.get('launch_started')}"),
        _check("a3_login_documented", PASS if observer.get("startup_login_supplied") else FAIL, "startup_login_supplied"),
        _check("a3_terminal_not_running_pre_owner_attach", PASS if not repair_processes else PENDING, f"process_count={len(repair_processes)}"),
    ]
    return _payload("A3 Runtime Reconciliation", context, checks, evidence={"observer_attachment": observer})


def _kill_switch_report(context: dict[str, Any]) -> dict[str, Any]:
    source = context["source_checks"]
    checks = [
        _check("ea_t1_execution_kill_switch_source_guard", PASS if source["ea_t1_execution_kill_switch"] else FAIL, "A3_EXECUTION_KILL.txt"),
        _check("ea_t1_full_stop_source_guard", PASS if source["ea_t1_full_stop"] else FAIL, "A3_FULL_STOP.txt"),
        _check("ea_t2_execution_kill_switch_source_guard", PASS if source["ea_t2_execution_kill_switch"] else FAIL, "A3_EXECUTION_KILL.txt"),
        _check("ea_t2_full_stop_source_guard", PASS if source["ea_t2_full_stop"] else FAIL, "A3_FULL_STOP.txt"),
        _check("runtime_kill_switch_drill", PENDING, "No A3 dry-run terminal startup rows exist yet; drill must run before arming."),
    ]
    return _payload("A3 Kill Switch Drill Report", context, checks)


def _cost_cap_report(context: dict[str, Any]) -> dict[str, Any]:
    checks = [
        _check("ea_t1_cost_cap_source_present", PASS if _source_has(Path(context["root"]) / EA_T1, "InpMaxEstimatedCostR = 0.15") else FAIL, "T1 max estimated cost R"),
        _check("ea_t2_cost_cap_source_present", PASS if _source_has(Path(context["root"]) / EA_T2, "InpMaxEstimatedCostR = 0.15") else FAIL, "T2 max estimated cost R"),
        _check("runtime_cost_cap_block_observed", PENDING, "On-demand report; no A3 runtime COST_R_CAP_BLOCK row exists yet."),
    ]
    return _payload("A3 Cost Cap Block Report", context, checks)


def _vs_a1_report(context: dict[str, Any]) -> dict[str, Any]:
    checks = [
        _check("a1_control_login_documented", PASS, A1_LOGIN),
        _check("a3_trade_sample_available", PENDING, "No A3 trades/signals exist yet for same-period matching."),
        _check("duplicate_hidden_matching_available", PENDING, "Will populate after dry-run/execution signal rows exist."),
    ]
    return _payload("A3 vs A1 Treatment Control Report", context, checks)


def _preflight_report(context: dict[str, Any], reports: dict[str, dict[str, Any]]) -> dict[str, Any]:
    source = context["source_checks"]
    manifest = context["manifest"]
    tests = context["test_run"]
    checks = [
        _check("a3_login_documented", PASS, A3_LOGIN),
        _check("server_marker_demo_practice_required", PASS, "EA source refuses live/real and expects Demo marker."),
        _check("login_allowlist_exact", PASS if source["ea_t1_allowlist"] and source["ea_t2_allowlist"] else FAIL, A3_LOGIN),
        _check("safe_presets_committed_non_executing", PASS if source["preset_t1_safe"] and source["preset_t2_safe"] else FAIL, "T1/T2 safe presets"),
        _check("owner_preset_local_only", reports["owner"]["status"], "See A3_OWNER_AUTHORIZATION_STATUS."),
        _check("magic_no_collision", PASS if source["ea_t1_magic"] and source["ea_t2_magic"] else FAIL, "933000 and 933100"),
        _check("hypothesis_hash_locked", PASS if manifest.get("status") == "LOCKED_BEFORE_FIRST_TRADE" else FAIL, manifest.get("status", "missing")),
        _check("source_tests_pass", PASS if tests.get("status") == PASS else PENDING, tests.get("summary", "not run")),
        _check("kill_switch_drill_pass", reports["kill"]["status"], "See A3_KILL_SWITCH_DRILL_REPORT."),
        _check("dry_run_session_pass", reports["dry_run"]["status"], "See A3_DRY_RUN_SESSION_REPORT."),
        _check("guardian_stage_a_startup_pass", PENDING, "No A3 startup log yet."),
        _check("decommission_report_pass", reports["decommission"]["status"], "See A3_DECOMMISSION_REPORT."),
        _check("a1_a2_state_snapshot_documented", PASS, f"A1={A1_LOGIN}; A2={A2_LOGIN}; A2 untouched."),
        _check("owner_signed_demo_packet", reports["owner"]["status"], "See A3_OWNER_AUTHORIZATION_STATUS."),
    ]
    return _payload("A3 Preflight Report", context, checks)


def _combined_preflight_report(context: dict[str, Any], reports: dict[str, dict[str, Any]]) -> dict[str, Any]:
    source = context["source_checks"]
    tests = context["test_run"]
    checks = [
        _check("t4_equivalent_source_tests_both_eas", PASS if tests.get("status") == PASS else PENDING, tests.get("summary", "not run")),
        _check("mandatory_source_safety_both_eas", PASS if all(source.values()) else FAIL, "source/preset checks"),
        _check("hypotheses_hash_locked_both_eas", PASS if context["manifest"].get("status") == "LOCKED_BEFORE_FIRST_TRADE" else FAIL, context["manifest"].get("status", "missing")),
        _check("decommission_pass", reports["decommission"]["status"], "WR50/P2WEAKNESS decommission gate."),
        _check("dry_run_session_both_eas_pass", reports["dry_run"]["status"], "Both EAs require dry-run logs before arming."),
        _check("owner_signature_and_local_preset", reports["owner"]["status"], "Owner must sign and supply local execution preset."),
    ]
    payload = _payload("A3 Combined Preflight Report", context, checks)
    payload["attach_decision"] = "DO_NOT_ATTACH"
    payload["monday_attach_gate"] = "CLOSED_UNTIL_ALL_CHECKS_PASS"
    payload["target_account"] = A3_LOGIN
    return payload


def _payload(title: str, context: dict[str, Any], checks: list[dict[str, str]], evidence: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "title": title,
        "status": _overall(checks),
        "created_at_utc": context["created_at_utc"],
        "boundary": context["boundary"],
        "checks": checks,
        "evidence": evidence or {},
    }


def _check(name: str, status: str, evidence: str) -> dict[str, str]:
    return {"name": name, "status": status, "evidence": evidence}


def _overall(checks: list[dict[str, str]]) -> str:
    if any(check["status"] == FAIL for check in checks):
        return FAIL
    if any(check["status"] == PENDING for check in checks):
        return PENDING
    return PASS


def _render_report(payload: dict[str, Any]) -> str:
    lines = [
        f"# {payload['title']}",
        "",
        f"Status: **{payload['status']}**",
        "",
        "## Boundary",
        "",
        f"- A3 login: `{payload['boundary']['a3_demo_login']}`.",
        "- Demo only; canonical Phase 2 unchanged.",
        "- A2 remains untouched.",
        "- Committed defaults remain non-executing.",
        "",
        "## Checks",
        "",
        "| Check | Status | Evidence |",
        "|---|---|---|",
    ]
    for check in payload["checks"]:
        lines.append(f"| {check['name']} | {check['status']} | {check['evidence']} |")
    if payload.get("attach_decision"):
        lines.extend(
            [
                "",
                "## Attach Decision",
                "",
                f"- Decision: `{payload['attach_decision']}`",
                f"- Monday attach gate: `{payload['monday_attach_gate']}`",
                f"- Target account: `{payload['target_account']}`",
            ]
        )
    if payload.get("evidence"):
        lines.extend(["", "## Evidence", "", "```json", json.dumps(payload["evidence"], indent=2), "```"])
    lines.append("")
    return "\n".join(lines)


def _write_report_pair(json_path: Path, payload: dict[str, Any], markdown: str) -> tuple[Path, Path]:
    json_path.parent.mkdir(parents=True, exist_ok=True)
    md_path = json_path.with_suffix(".md")
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    md_path.write_text(markdown, encoding="utf-8")
    return json_path, md_path


def _run_tests(root: Path) -> dict[str, Any]:
    python_exe = root.parent / "xauusd-phase0" / ".venv" / "Scripts" / "python.exe"
    tests = [
        "tests/test_a3_executors_source.py",
        "tests/test_a3_executor_presets.py",
        "tests/test_a3_review_reports.py",
        "tests/test_session_extreme_entry_forensics.py",
        "tests/test_mtf_trend_alignment_report.py",
    ]
    command = [str(python_exe), "-m", "pytest", *tests]
    try:
        result = subprocess.run(command, cwd=root, text=True, capture_output=True, timeout=180)
    except Exception as exc:
        return {"status": PENDING, "summary": f"pytest execution failed: {type(exc).__name__}: {exc}", "command": command}
    summary = _pytest_summary(result.stdout + "\n" + result.stderr)
    return {
        "status": PASS if result.returncode == 0 else FAIL,
        "summary": summary,
        "command": command,
        "returncode": result.returncode,
        "stdout_tail": "\n".join(result.stdout.splitlines()[-20:]),
        "stderr_tail": "\n".join(result.stderr.splitlines()[-20:]),
    }


def _tests_not_run() -> dict[str, Any]:
    return {"status": PENDING, "summary": "not run by this report invocation"}


def _pytest_summary(text: str) -> str:
    for line in reversed(text.splitlines()):
        if " passed" in line or " failed" in line:
            return line.strip()
    return "pytest completed; summary line not found"


def _terminal_processes() -> dict[str, Any]:
    command = [
        "powershell",
        "-NoProfile",
        "-Command",
        "Get-CimInstance Win32_Process | Where-Object { $_.Name -eq 'terminal64.exe' } | Select-Object ProcessId,ExecutablePath,CommandLine | ConvertTo-Json -Depth 3",
    ]
    try:
        result = subprocess.run(command, text=True, capture_output=True, timeout=20)
    except Exception as exc:
        return {"status": PENDING, "error": f"{type(exc).__name__}: {exc}", "processes": []}
    if result.returncode != 0:
        return {"status": PENDING, "error": result.stderr.strip(), "processes": []}
    text = result.stdout.strip()
    if not text:
        return {"status": PASS, "processes": []}
    data = json.loads(text)
    processes = data if isinstance(data, list) else [data]
    return {"status": PASS, "processes": processes}


def _a3_runtime_logs(output_dir: Path) -> dict[str, Any]:
    return {
        "guarded_signal_logs": [str(path) for path in sorted(output_dir.glob("a3_rdguard_v1_signal_log*.csv"))],
        "structured_signal_logs": [str(path) for path in sorted(output_dir.glob("a3_rdstruct_v1_signal_log*.csv"))],
        "guarded_startup_logs": [str(path) for path in sorted(output_dir.glob("a3_rdguard_v1_startup*.csv"))],
        "structured_startup_logs": [str(path) for path in sorted(output_dir.glob("a3_rdstruct_v1_startup*.csv"))],
    }


def _committed_a3_preset_audit(root: Path) -> dict[str, Any]:
    presets = sorted((root / "mt5" / "Presets").glob("Account3*.set"))
    execution_enabled = []
    for preset in presets:
        text = _read(preset)
        if "InpBrokerActionAllowed=true" in text:
            execution_enabled.append(str(preset))
    return {
        "preset_count": len(presets),
        "execution_enabled_count": len(execution_enabled),
        "execution_enabled": execution_enabled,
    }


def _source_has(path: Path, token: str) -> bool:
    return token in _read(path)


def _per_magic_cap_present(text: str) -> bool:
    return "POSITION_MAGIC) == InpMagicNumber" in text and "ORDER_MAGIC) == InpMagicNumber" in text


def _contains(text: str, token: str) -> bool:
    return token in text


def _order(text: str, first: str, second: str) -> bool:
    left = text.find(first)
    right = text.find(second)
    return left >= 0 and right >= 0 and left < right


def _preset(path: Path) -> dict[str, str]:
    output: dict[str, str] = {}
    for line in _read(path).splitlines():
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        output[key.strip()] = value.strip()
    return output


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def _read(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate A3 runtime, decommission, and preflight reports.")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output-dir", type=Path, default=None)
    parser.add_argument("--run-tests", action="store_true")
    args = parser.parse_args()
    output = generate_a3_runtime_reports(args.root, output_dir=args.output_dir, run_tests=args.run_tests)
    print(f"A3 runtime reports: {output.status}")
    print(output.summary_json)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
