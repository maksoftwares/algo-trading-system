from __future__ import annotations

import json
import sys
import traceback
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from .account_registry import load_mt5_account_registry
from .account_verification import generate_account_verification_matrix
from .history_log_snapshot import generate_history_log_snapshot_report
from .market_data_export import _table, _utc_now, _write_json_atomic, generate_bar_tick_export_report, parse_utc
from .pipeline_orchestrator import run_offline_prediction_readiness_pipeline


DEFAULT_REPORT_JSON = Path("outputs") / "reports" / "A3_ML_LIVE_REFRESH_STATUS.json"
DEFAULT_REQUESTED_START_UTC = "2026-06-01T00:00:00Z"


def run_live_refresh_or_preflight(
    root: Path,
    report_json: Path | None = None,
    *,
    execute_live_readonly: bool = False,
    requested_start_utc: str | None = None,
    max_tick_days: int | None = None,
    publish: bool = False,
) -> Path:
    root = root.resolve()
    report_json = (report_json or root / DEFAULT_REPORT_JSON).resolve()
    registry_path = root / "config" / "ml" / "mt5_accounts.yaml"
    pointer_path = root / "outputs" / "reports" / "C02_DATASET_POINTER.json"
    requested_start_utc = requested_start_utc or _requested_start_from_pointer(pointer_path) or DEFAULT_REQUESTED_START_UTC
    records: list[dict[str, Any]] = []
    if execute_live_readonly:
        records = _run_live_steps(
            root,
            registry_path=registry_path,
            requested_start_utc=requested_start_utc,
            max_tick_days=max_tick_days,
            publish=publish,
        )
    else:
        records = _preflight_steps(root, registry_path=registry_path, requested_start_utc=requested_start_utc, publish=publish)
    summary = _summary(root)
    payload = {
        "status": _overall_status(records, summary, execute_live_readonly=execute_live_readonly),
        "stage": "C08-LIVE-REFRESH",
        "created_at_utc": _utc_now(),
        "schema_version": "a3_ml_live_refresh_status_v1",
        "mode": "EXECUTE_LIVE_READONLY" if execute_live_readonly else "PREFLIGHT_ONLY",
        "requested_start_utc": requested_start_utc,
        "max_tick_days": max_tick_days,
        "publish_requested": bool(publish),
        "steps": records,
        "summary": summary,
        "boundary": {
            "mt5_connection_attempted": bool(execute_live_readonly and _step_passed_or_attempted(records, "C02-01 account verification")),
            "data_export_attempted": bool(execute_live_readonly and _step_passed_or_attempted(records, "C02-02 bars/ticks export")),
            "terminal_runtime_change_authorized": False,
            "ea_file_drop_authorized": bool(summary.get("c06", {}).get("authorization", {}).get("mt5_file_publish_attempted", False)),
            "broker_action_authorized": False,
        },
        "next_allowed_stage": _next_allowed_stage(summary, execute_live_readonly=execute_live_readonly),
    }
    report_json.parent.mkdir(parents=True, exist_ok=True)
    report_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    report_json.with_suffix(".md").write_text(render_live_refresh_status_md(payload), encoding="utf-8")
    pointer = _read_json(pointer_path)
    if pointer:
        pointer["c08_live_refresh_status_report"] = str(report_json)
        pointer["c08_live_refresh_status"] = payload["status"]
        pointer["python_demo_predictions_authorized"] = bool(summary.get("c04", {}).get("authorization", {}).get("python_demo_predictions_authorized", False))
        pointer["ea_consumption_authorized"] = bool(summary.get("c06", {}).get("authorization", {}).get("ea_consumption_authorized", False))
        pointer["broker_action_authorized"] = False
        _write_json_atomic(pointer_path, pointer)
    return report_json


def render_live_refresh_status_md(payload: dict[str, Any]) -> str:
    rows = [
        {
            "Step": item.get("step", ""),
            "Status": item.get("status", ""),
            "Detail": item.get("detail", ""),
        }
        for item in payload.get("steps", [])
    ]
    summary = payload.get("summary", {})
    stage_rows = [
        {"Stage": "C02 account verification", "Status": summary.get("c02_account_verification", {}).get("status", "MISSING")},
        {"Stage": "C02 bars/ticks export", "Status": summary.get("c02_bar_tick_export", {}).get("status", "MISSING")},
        {"Stage": "C03 readiness", "Status": summary.get("c03", {}).get("status", "MISSING")},
        {"Stage": "C05 training", "Status": summary.get("c05", {}).get("status", "MISSING")},
        {"Stage": "C04 shadow bridge", "Status": summary.get("c04", {}).get("status", "MISSING")},
        {"Stage": "C06 EA handoff", "Status": summary.get("c06", {}).get("status", "MISSING")},
        {"Stage": "C07 pipeline", "Status": summary.get("c07", {}).get("status", "MISSING")},
    ]
    failed_gates = _failed_c03_gates(summary)
    failed_lines = "\n".join(f"- {gate}" for gate in failed_gates) if failed_gates else "- none"
    return "\n".join(
        [
            "# A3 ML Live Refresh Status",
            "",
            f"Overall status: {payload['status']}",
            f"Mode: {payload['mode']}",
            f"Requested start UTC: {payload['requested_start_utc']}",
            f"Publish requested: {str(payload.get('publish_requested', False)).lower()}",
            "",
            "## Stage Summary",
            "",
            _table(stage_rows, ["Stage", "Status"]),
            "",
            "## Steps",
            "",
            _table(rows, ["Step", "Status", "Detail"]) if rows else "No steps recorded.",
            "",
            "## Failed C03 Gates",
            "",
            failed_lines,
            "",
            "## Boundary",
            "",
            f"- MT5 connection attempted: {str(payload['boundary']['mt5_connection_attempted']).lower()}.",
            f"- Data export attempted: {str(payload['boundary']['data_export_attempted']).lower()}.",
            "- Terminal runtime change authorized: false.",
            f"- EA file drop authorized: {str(payload['boundary']['ea_file_drop_authorized']).lower()}.",
            "- Broker action authorized: false.",
            "",
            "## Next",
            "",
            payload["next_allowed_stage"],
            "",
        ]
    )


def _run_live_steps(
    root: Path,
    *,
    registry_path: Path,
    requested_start_utc: str,
    max_tick_days: int | None,
    publish: bool,
) -> list[dict[str, Any]]:
    requested_start = parse_utc(requested_start_utc)
    steps: list[tuple[str, Callable[[], Path]]] = [
        (
            "C02-01 account verification",
            lambda: generate_account_verification_matrix(
                root,
                registry_path=registry_path,
                python_executable=sys.executable,
                worker_script=root / "scripts" / "c02_verify_mt5_accounts.py",
            ),
        ),
        (
            "C02-02 bars/ticks export",
            lambda: generate_bar_tick_export_report(
                root,
                registry_path=registry_path,
                requested_start_utc=requested_start,
                max_tick_days=max_tick_days,
                python_executable=sys.executable,
                worker_script=root / "scripts" / "c02_export_mt5_market_data.py",
            ),
        ),
        (
            "C02-03 history/log snapshot",
            lambda: generate_history_log_snapshot_report(
                root,
                registry_path=registry_path,
                python_executable=sys.executable,
                worker_script=root / "scripts" / "c02_snapshot_history_logs.py",
            ),
        ),
        ("C07 offline readiness pipeline", lambda: run_offline_prediction_readiness_pipeline(root, publish=publish)),
    ]
    return _run_steps(steps)


def _preflight_steps(root: Path, *, registry_path: Path, requested_start_utc: str, publish: bool) -> list[dict[str, Any]]:
    records = []
    records.append(_preflight_record("registry_exists", registry_path.exists(), str(registry_path)))
    if registry_path.exists():
        try:
            registry = load_mt5_account_registry(registry_path)
            all_files_roots = all(account.files_roots for account in registry.accounts)
            records.append(_preflight_record("registry_parses", True, f"accounts={','.join(account.account_label for account in registry.accounts)}"))
            records.append(_preflight_record("all_accounts_have_files_roots", all_files_roots, _files_root_detail(registry.accounts)))
        except Exception as exc:
            records.append(_preflight_record("registry_parses", False, f"{type(exc).__name__}: {exc}"))
    for script_name in (
        "c02_verify_mt5_accounts.py",
        "c02_export_mt5_market_data.py",
        "c02_snapshot_history_logs.py",
        "c07_run_ml_readiness_pipeline.py",
    ):
        path = root / "scripts" / script_name
        records.append(_preflight_record(f"script_exists:{script_name}", path.exists(), str(path)))
    try:
        parse_utc(requested_start_utc)
        records.append(_preflight_record("requested_start_utc_valid", True, requested_start_utc))
    except Exception as exc:
        records.append(_preflight_record("requested_start_utc_valid", False, f"{type(exc).__name__}: {exc}"))
    records.append(_preflight_record("publish_flag_safe", not publish, "publish is ignored unless execute-live-readonly is set"))
    return records


def _run_steps(steps: list[tuple[str, Callable[[], Path]]]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    failed = False
    for step_name, runner in steps:
        if failed:
            records.append({"step": step_name, "status": "SKIPPED", "output": "", "detail": "previous step failed"})
            continue
        try:
            output = runner()
            status = _report_status(output)
            record_status = "PASS" if status in {"PASS", "NOT_READY", "READY_DRY_RUN", "PUBLISHED_TO_MT5_FILES"} else status
            records.append({"step": step_name, "status": record_status, "output": str(output), "detail": f"report_status={status}"})
            if record_status not in {"PASS"}:
                failed = True
        except Exception as exc:  # pragma: no cover - operator diagnostics
            failed = True
            records.append(
                {
                    "step": step_name,
                    "status": "FAIL_CLOSED",
                    "output": "",
                    "detail": f"{type(exc).__name__}: {exc}",
                    "traceback": traceback.format_exc(),
                }
            )
    return records


def _summary(root: Path) -> dict[str, Any]:
    reports = root / "outputs" / "reports"
    return {
        "c02_account_verification": _read_json(reports / "C02_ACCOUNT_VERIFICATION_MATRIX.json"),
        "c02_bar_tick_export": _read_json(reports / "C02_BAR_TICK_EXPORT_REPORT.json"),
        "c03": _read_json(reports / "C03_TRAINING_READINESS_REPORT.json"),
        "c05": _read_json(reports / "A3_ML_TRAINING_STATUS.json"),
        "c04": _read_json(reports / "A3_ML_SHADOW_BRIDGE_STATUS.json"),
        "c06": _read_json(reports / "A3_ML_EA_HANDOFF_STATUS.json"),
        "c07": _read_json(reports / "A3_ML_PIPELINE_RUN_STATUS.json"),
    }


def _overall_status(records: list[dict[str, Any]], summary: dict[str, Any], *, execute_live_readonly: bool) -> str:
    if any(record.get("status") in {"FAIL_CLOSED", "BLOCKED", "NO_GO"} for record in records):
        return "FAIL_CLOSED" if execute_live_readonly else "PREFLIGHT_BLOCKED"
    if not execute_live_readonly:
        return "PREFLIGHT_READY"
    c06_status = summary.get("c06", {}).get("status")
    if c06_status in {"READY_DRY_RUN", "PUBLISHED_TO_MT5_FILES"}:
        return c06_status
    return "NOT_READY"


def _next_allowed_stage(summary: dict[str, Any], *, execute_live_readonly: bool) -> str:
    if not execute_live_readonly:
        return "When markets have advanced, rerun C08 with --execute-live-readonly to refresh MT5 data and then C07."
    c07_status = summary.get("c07", {}).get("status")
    if c07_status in {"READY_DRY_RUN", "PUBLISHED_TO_MT5_FILES"}:
        return "Review C06 output, then configure EA passive consumption only; broker action remains false."
    return "Continue collecting A1/A2/A3 live data, then rerun C08."


def _requested_start_from_pointer(pointer_path: Path) -> str:
    pointer = _read_json(pointer_path)
    return str(pointer.get("requested_start_utc", ""))


def _failed_c03_gates(summary: dict[str, Any]) -> list[str]:
    return [
        f"{check.get('gate')} observed {check.get('observed')} required {check.get('required')}"
        for check in summary.get("c03", {}).get("checks", [])
        if not check.get("passed")
    ]


def _preflight_record(check: str, passed: bool, detail: str) -> dict[str, Any]:
    return {"step": check, "status": "PASS" if passed else "BLOCKED", "output": "", "detail": detail}


def _files_root_detail(accounts) -> str:
    return "; ".join(f"{account.account_label}={','.join(account.files_roots) or 'missing'}" for account in accounts)


def _step_passed_or_attempted(records: list[dict[str, Any]], step: str) -> bool:
    return any(record.get("step") == step for record in records)


def _report_status(path: Path) -> str:
    payload = _read_json(path)
    return str(payload.get("status", "MISSING"))


def _read_json(path_or_text: str | Path) -> dict[str, Any]:
    if not path_or_text:
        return {}
    path = Path(path_or_text)
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))
