from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from .market_data_export import _table, _utc_now, _write_json_atomic
from .runtime_evidence import audit_runtime_evidence
from .runtime_launch_diagnostic import diagnose_runtime_launch


DEFAULT_STATUS_JSON = Path("outputs") / "reports" / "A3_ML_POST_ATTACH_RUNTIME_MONITOR_STATUS.json"
SCHEMA_VERSION = "a3_ml_post_attach_runtime_monitor_status_v1"


def wait_for_post_attach_runtime_evidence(
    root: Path,
    report_json: Path | None = None,
    *,
    timeout_seconds: int = 300,
    poll_seconds: int = 5,
) -> Path:
    root = root.resolve()
    report_json = (report_json or root / DEFAULT_STATUS_JSON).resolve()
    timeout_seconds = max(0, int(timeout_seconds))
    poll_seconds = max(1, int(poll_seconds))
    started_monotonic = time.monotonic()
    started_at_utc = _utc_now()
    attempts: list[dict[str, Any]] = []
    final_c20: dict[str, Any] = {}
    final_c21: dict[str, Any] = {}

    while True:
        c20_path = audit_runtime_evidence(root)
        c21_path = diagnose_runtime_launch(root)
        final_c20 = _read_json(c20_path)
        final_c21 = _read_json(c21_path)
        elapsed_seconds = round(time.monotonic() - started_monotonic, 3)
        status = _status(final_c20, final_c21, timeout_seconds=timeout_seconds, timed_out=False)
        attempts.append(_attempt_payload(len(attempts) + 1, elapsed_seconds, final_c20, final_c21, status))
        if status in {"RUNTIME_EVIDENCE_PRESENT_ALL_ACCOUNTS", "PREFLIGHT_BLOCKED"}:
            break
        if timeout_seconds == 0:
            break
        remaining = timeout_seconds - (time.monotonic() - started_monotonic)
        if remaining <= 0:
            break
        time.sleep(min(poll_seconds, max(0.0, remaining)))

    elapsed_seconds = round(time.monotonic() - started_monotonic, 3)
    timed_out = timeout_seconds > 0 and elapsed_seconds >= timeout_seconds
    status = _status(final_c20, final_c21, timeout_seconds=timeout_seconds, timed_out=timed_out)
    payload = {
        "status": status,
        "stage": "C22-ML-POST-ATTACH-RUNTIME-MONITOR",
        "created_at_utc": _utc_now(),
        "started_at_utc": started_at_utc,
        "schema_version": SCHEMA_VERSION,
        "dataset_version": _read_json(root / "outputs" / "reports" / "C02_DATASET_POINTER.json").get("dataset_version", ""),
        "monitor": {
            "timeout_seconds": timeout_seconds,
            "poll_seconds": poll_seconds,
            "elapsed_seconds": elapsed_seconds,
            "attempt_count": len(attempts),
            "timed_out": bool(timed_out and status != "RUNTIME_EVIDENCE_PRESENT_ALL_ACCOUNTS"),
        },
        "authorization": {
            "python_demo_predictions_authorized": False,
            "ea_consumption_authorized": False,
            "broker_action_authorized": False,
        },
        "upstream_statuses": {
            "c20_runtime_evidence": final_c20.get("status", "MISSING"),
            "c21_runtime_launch_diagnostic": final_c21.get("status", "MISSING"),
        },
        "runtime_evidence": final_c20.get("runtime_evidence", {}),
        "diagnostic_summary": final_c21.get("diagnostic_summary", {}),
        "attempts": attempts,
        "inputs": {
            "registry_path": str(root / "config" / "ml" / "mt5_accounts.yaml"),
            "c20_runtime_evidence": str(root / "outputs" / "reports" / "A3_ML_RUNTIME_EVIDENCE_STATUS.json"),
            "c21_runtime_launch_diagnostic": str(root / "outputs" / "reports" / "A3_ML_RUNTIME_LAUNCH_DIAGNOSTIC_STATUS.json"),
        },
        "outputs": {
            "status_report_json": str(report_json),
            "status_report_md": str(report_json.with_suffix(".md")),
        },
        "boundary": {
            "mt5_connection_attempted": False,
            "data_export_attempted": False,
            "terminal_runtime_launch_attempted": False,
            "terminal_shutdown_attempted": False,
            "profile_or_chart_file_write_attempted": False,
            "ea_file_drop_authorized": False,
            "broker_action_authorized": False,
        },
        "next_allowed_stage": _next_allowed_stage(status),
    }
    _write_status(report_json, payload)
    _update_pointer(root / "outputs" / "reports" / "C02_DATASET_POINTER.json", payload)
    return report_json


def render_post_attach_monitor_md(payload: dict[str, Any]) -> str:
    attempt_rows = [
        {
            "Attempt": str(item.get("attempt", "")),
            "Elapsed": str(item.get("elapsed_seconds", "")),
            "C20": item.get("c20_status", ""),
            "C21": item.get("c21_status", ""),
            "Status": item.get("status", ""),
        }
        for item in payload.get("attempts", [])
    ]
    runtime = payload.get("runtime_evidence", {})
    diagnostic = payload.get("diagnostic_summary", {})
    return "\n".join(
        [
            "# A3 ML Post-Attach Runtime Monitor Status",
            "",
            f"Overall status: {payload['status']}",
            f"Dataset version: {payload.get('dataset_version', '')}",
            "",
            "## Monitor",
            "",
            f"- Timeout seconds: {payload['monitor']['timeout_seconds']}.",
            f"- Poll seconds: {payload['monitor']['poll_seconds']}.",
            f"- Elapsed seconds: {payload['monitor']['elapsed_seconds']}.",
            f"- Attempt count: {payload['monitor']['attempt_count']}.",
            f"- Timed out: {str(payload['monitor']['timed_out']).lower()}.",
            "",
            "## Upstream Statuses",
            "",
            f"- C20 runtime evidence: {payload['upstream_statuses']['c20_runtime_evidence']}",
            f"- C21 runtime launch diagnostic: {payload['upstream_statuses']['c21_runtime_launch_diagnostic']}",
            "",
            "## Evidence Summary",
            "",
            f"- Handoff files all accounts: {str(runtime.get('handoff_files_all_accounts', False)).lower()}.",
            f"- Passive observer runtime all accounts: {str(runtime.get('passive_observer_runtime_all_accounts', False)).lower()}.",
            f"- Broker shadow tap runtime all accounts: {str(runtime.get('broker_shadow_tap_runtime_all_accounts', False)).lower()}.",
            f"- Startup configs safe all accounts: {str(diagnostic.get('startup_configs_safe_all_accounts', False)).lower()}.",
            f"- Observer journal mentions all accounts: {str(diagnostic.get('observer_log_mentions_all_accounts', False)).lower()}.",
            "",
            "## Attempts",
            "",
            _table(attempt_rows, ["Attempt", "Elapsed", "C20", "C21", "Status"]) if attempt_rows else "No attempts ran.",
            "",
            "## Authorization",
            "",
            "- Python demo predictions authorized: false.",
            "- EA consumption authorized: false.",
            "- Broker action authorized: false.",
            "",
            "## Boundary",
            "",
            "- MT5 connection attempted: false.",
            "- Data export attempted: false.",
            "- Terminal runtime launch attempted: false.",
            "- Terminal shutdown attempted: false.",
            "- Profile or chart file write attempted: false.",
            "- EA file drop authorized: false.",
            "- Broker action authorized: false.",
            "",
            "## Next",
            "",
            payload["next_allowed_stage"],
            "",
        ]
    )


def _attempt_payload(
    attempt: int,
    elapsed_seconds: float,
    c20: dict[str, Any],
    c21: dict[str, Any],
    status: str,
) -> dict[str, Any]:
    runtime = c20.get("runtime_evidence", {})
    diagnostic = c21.get("diagnostic_summary", {})
    return {
        "attempt": attempt,
        "elapsed_seconds": elapsed_seconds,
        "c20_status": c20.get("status", "MISSING"),
        "c21_status": c21.get("status", "MISSING"),
        "status": status,
        "handoff_files_all_accounts": bool(runtime.get("handoff_files_all_accounts", False)),
        "passive_observer_runtime_all_accounts": bool(runtime.get("passive_observer_runtime_all_accounts", False)),
        "broker_shadow_tap_runtime_all_accounts": bool(runtime.get("broker_shadow_tap_runtime_all_accounts", False)),
        "startup_configs_safe_all_accounts": bool(diagnostic.get("startup_configs_safe_all_accounts", False)),
        "observer_log_mentions_all_accounts": bool(diagnostic.get("observer_log_mentions_all_accounts", False)),
    }


def _status(c20: dict[str, Any], c21: dict[str, Any], *, timeout_seconds: int, timed_out: bool) -> str:
    c20_status = c20.get("status", "MISSING")
    c21_status = c21.get("status", "MISSING")
    if c20_status == "PREFLIGHT_BLOCKED" or c21_status == "PREFLIGHT_BLOCKED":
        return "PREFLIGHT_BLOCKED"
    if c20_status == "RUNTIME_EVIDENCE_PRESENT_ALL_ACCOUNTS" and c21_status == "RUNTIME_EVIDENCE_PRESENT_ALL_ACCOUNTS":
        return "RUNTIME_EVIDENCE_PRESENT_ALL_ACCOUNTS"
    if c20_status == "PARTIAL_RUNTIME_EVIDENCE_PRESENT" or c21_status == "LAUNCH_SENT_WITH_PARTIAL_JOURNAL_EVIDENCE":
        return "PARTIAL_RUNTIME_EVIDENCE_PRESENT"
    if timed_out and timeout_seconds > 0:
        return "TIMEOUT_WAITING_FOR_RUNTIME_EVIDENCE"
    return "WAITING_FOR_MANUAL_ATTACH"


def _next_allowed_stage(status: str) -> str:
    if status == "RUNTIME_EVIDENCE_PRESENT_ALL_ACCOUNTS":
        return "Runtime evidence is present on all accounts. Rerun C19 with --no-run-pipeline, then continue collecting data until C03 passes."
    if status == "PARTIAL_RUNTIME_EVIDENCE_PRESENT":
        return "Some runtime evidence is present. Attach or reload the missing A1/A2/A3 observers and broker shadow consumers, then rerun C22."
    if status == "TIMEOUT_WAITING_FOR_RUNTIME_EVIDENCE":
        return "No complete runtime evidence appeared before timeout. Attach A3MlPredictionObserver and broker shadow consumers on XAUUSD M5 for A1/A2/A3, then rerun C22."
    if status == "WAITING_FOR_MANUAL_ATTACH":
        return "Attach A3MlPredictionObserver and broker shadow consumers on XAUUSD M5 for A1/A2/A3, then rerun C22 with a positive timeout."
    return "Fix C20/C21 preflight issues, then rerun C22."


def _write_status(status_json: Path, payload: dict[str, Any]) -> None:
    status_json.parent.mkdir(parents=True, exist_ok=True)
    status_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    status_json.with_suffix(".md").write_text(render_post_attach_monitor_md(payload), encoding="utf-8")


def _update_pointer(pointer_path: Path, payload: dict[str, Any]) -> None:
    if not pointer_path.exists():
        return
    pointer = _read_json(pointer_path)
    pointer["c22_post_attach_runtime_monitor_report"] = payload["outputs"]["status_report_json"]
    pointer["c22_post_attach_runtime_monitor_status"] = payload["status"]
    pointer["python_demo_predictions_authorized"] = False
    pointer["ea_consumption_authorized"] = False
    pointer["broker_action_authorized"] = False
    _write_json_atomic(pointer_path, pointer)


def _read_json(path_or_text: str | Path) -> dict[str, Any]:
    if not path_or_text:
        return {}
    path = Path(path_or_text)
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))
