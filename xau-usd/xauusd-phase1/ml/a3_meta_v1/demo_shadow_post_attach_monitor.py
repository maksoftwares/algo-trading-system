from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from .market_data_export import _table, _utc_now, _write_json_atomic
from .post_attach_monitor import wait_for_post_attach_runtime_evidence
from .research_preview_runtime_verifier import verify_research_preview_runtime_read_path


DEFAULT_STATUS_JSON = Path("outputs") / "reports" / "A3_ML_DEMO_SHADOW_POST_ATTACH_MONITOR_STATUS.json"
SCHEMA_VERSION = "a3_ml_demo_shadow_post_attach_monitor_status_v1"


def wait_for_demo_shadow_post_attach(
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
    final_c22: dict[str, Any] = {}
    final_c27: dict[str, Any] = {}

    while True:
        c22_path = wait_for_post_attach_runtime_evidence(root, timeout_seconds=0, poll_seconds=poll_seconds)
        c27_path = verify_research_preview_runtime_read_path(root)
        final_c22 = _read_json(c22_path)
        final_c27 = _read_json(c27_path)
        elapsed_seconds = round(time.monotonic() - started_monotonic, 3)
        status = _status(final_c22, final_c27, timeout_seconds=timeout_seconds, timed_out=False)
        attempts.append(_attempt_payload(len(attempts) + 1, elapsed_seconds, final_c22, final_c27, status))
        if status in {"DEMO_SHADOW_RUNTIME_CONFIRMED_ALL_ACCOUNTS", "PREFLIGHT_BLOCKED"}:
            break
        if timeout_seconds == 0:
            break
        remaining = timeout_seconds - (time.monotonic() - started_monotonic)
        if remaining <= 0:
            break
        time.sleep(min(poll_seconds, max(0.0, remaining)))

    elapsed_seconds = round(time.monotonic() - started_monotonic, 3)
    timed_out = timeout_seconds > 0 and elapsed_seconds >= timeout_seconds
    status = _status(final_c22, final_c27, timeout_seconds=timeout_seconds, timed_out=timed_out)
    pointer = _read_json(root / "outputs" / "reports" / "C02_DATASET_POINTER.json")
    payload = {
        "status": status,
        "stage": "C28-DEMO-SHADOW-POST-ATTACH-MONITOR",
        "created_at_utc": _utc_now(),
        "started_at_utc": started_at_utc,
        "schema_version": SCHEMA_VERSION,
        "dataset_version": pointer.get("dataset_version", ""),
        "monitor": {
            "timeout_seconds": timeout_seconds,
            "poll_seconds": poll_seconds,
            "elapsed_seconds": elapsed_seconds,
            "attempt_count": len(attempts),
            "timed_out": bool(timed_out and status != "DEMO_SHADOW_RUNTIME_CONFIRMED_ALL_ACCOUNTS"),
        },
        "authorization": {
            "official_model_training_authorized": False,
            "python_demo_predictions_authorized": False,
            "ea_consumption_authorized": False,
            "broker_action_authorized": False,
        },
        "upstream_statuses": {
            "c22_post_attach_runtime_monitor": final_c22.get("status", "MISSING"),
            "c27_research_preview_runtime_verifier": final_c27.get("status", "MISSING"),
        },
        "runtime_evidence": {
            "post_attach_runtime_evidence_all_accounts": final_c22.get("status") == "RUNTIME_EVIDENCE_PRESENT_ALL_ACCOUNTS",
            "research_preview_read_path_confirmed_all_accounts": final_c27.get("status") == "RESEARCH_PREVIEW_READ_PATH_CONFIRMED_ALL_ACCOUNTS",
            "handoff_research_preview_ready_all_accounts": bool(
                final_c27.get("runtime_evidence", {}).get("handoff_research_preview_ready_all_accounts", False)
            ),
            "broker_shadow_tap_exists_all_accounts": bool(
                final_c27.get("runtime_evidence", {}).get("broker_shadow_tap_exists_all_accounts", False)
            ),
        },
        "attempts": attempts,
        "inputs": {
            "c22_post_attach_runtime_monitor": str(root / "outputs" / "reports" / "A3_ML_POST_ATTACH_RUNTIME_MONITOR_STATUS.json"),
            "c27_research_preview_runtime_verifier": str(root / "outputs" / "reports" / "A3_ML_RESEARCH_PREVIEW_RUNTIME_VERIFIER_STATUS.json"),
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


def render_demo_shadow_post_attach_monitor_md(payload: dict[str, Any]) -> str:
    attempt_rows = [
        {
            "Attempt": str(item.get("attempt", "")),
            "Elapsed": str(item.get("elapsed_seconds", "")),
            "C22": item.get("c22_status", ""),
            "C27": item.get("c27_status", ""),
            "Status": item.get("status", ""),
        }
        for item in payload.get("attempts", [])
    ]
    runtime = payload.get("runtime_evidence", {})
    return "\n".join(
        [
            "# A3 ML Demo Shadow Post-Attach Monitor Status",
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
            f"- C22 post-attach runtime monitor: {payload['upstream_statuses']['c22_post_attach_runtime_monitor']}",
            f"- C27 research preview runtime verifier: {payload['upstream_statuses']['c27_research_preview_runtime_verifier']}",
            "",
            "## Evidence Summary",
            "",
            f"- Post-attach runtime evidence all accounts: {str(runtime.get('post_attach_runtime_evidence_all_accounts', False)).lower()}.",
            f"- Research preview read path confirmed all accounts: {str(runtime.get('research_preview_read_path_confirmed_all_accounts', False)).lower()}.",
            f"- Handoff research preview ready all accounts: {str(runtime.get('handoff_research_preview_ready_all_accounts', False)).lower()}.",
            f"- Broker shadow tap exists all accounts: {str(runtime.get('broker_shadow_tap_exists_all_accounts', False)).lower()}.",
            "",
            "## Attempts",
            "",
            _table(attempt_rows, ["Attempt", "Elapsed", "C22", "C27", "Status"]) if attempt_rows else "No attempts ran.",
            "",
            "## Authorization",
            "",
            "- Official model training authorized: false.",
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
    c22: dict[str, Any],
    c27: dict[str, Any],
    status: str,
) -> dict[str, Any]:
    c27_runtime = c27.get("runtime_evidence", {})
    return {
        "attempt": attempt,
        "elapsed_seconds": elapsed_seconds,
        "c22_status": c22.get("status", "MISSING"),
        "c27_status": c27.get("status", "MISSING"),
        "status": status,
        "post_attach_runtime_evidence_all_accounts": c22.get("status") == "RUNTIME_EVIDENCE_PRESENT_ALL_ACCOUNTS",
        "research_preview_read_path_confirmed_all_accounts": c27.get("status") == "RESEARCH_PREVIEW_READ_PATH_CONFIRMED_ALL_ACCOUNTS",
        "handoff_research_preview_ready_all_accounts": bool(
            c27_runtime.get("handoff_research_preview_ready_all_accounts", False)
        ),
        "broker_shadow_tap_exists_all_accounts": bool(c27_runtime.get("broker_shadow_tap_exists_all_accounts", False)),
    }


def _status(c22: dict[str, Any], c27: dict[str, Any], *, timeout_seconds: int, timed_out: bool) -> str:
    c22_status = c22.get("status", "MISSING")
    c27_status = c27.get("status", "MISSING")
    if c22_status == "PREFLIGHT_BLOCKED" or c27_status == "PREFLIGHT_BLOCKED":
        return "PREFLIGHT_BLOCKED"
    c22_ready = c22_status == "RUNTIME_EVIDENCE_PRESENT_ALL_ACCOUNTS"
    c27_ready = c27_status == "RESEARCH_PREVIEW_READ_PATH_CONFIRMED_ALL_ACCOUNTS"
    if c22_ready and c27_ready:
        return "DEMO_SHADOW_RUNTIME_CONFIRMED_ALL_ACCOUNTS"
    if c22_ready:
        return "RUNTIME_PRESENT_WAITING_READ_PATH"
    if c27_ready:
        return "READ_PATH_CONFIRMED_WAITING_RUNTIME_EVIDENCE"
    if c22_status == "PARTIAL_RUNTIME_EVIDENCE_PRESENT" or c27_status == "PARTIAL_RESEARCH_PREVIEW_RUNTIME_EVIDENCE":
        return "PARTIAL_DEMO_SHADOW_RUNTIME_EVIDENCE"
    if timed_out and timeout_seconds > 0:
        return "TIMEOUT_WAITING_FOR_DEMO_SHADOW_RUNTIME"
    return "WAITING_FOR_MT5_RUNTIME_ATTACH"


def _next_allowed_stage(status: str) -> str:
    if status == "DEMO_SHADOW_RUNTIME_CONFIRMED_ALL_ACCOUNTS":
        return "Demo-shadow runtime is confirmed: MT5 is logging observers and broker-shadow EAs can read Python preview rows. Continue collecting/exporting data until official C03/C05/C04/C06 gates pass."
    if status == "RUNTIME_PRESENT_WAITING_READ_PATH":
        return "MT5 runtime evidence is present, but C27 has not confirmed the Python preview read path. Reload broker-shadow consumers and rerun C28."
    if status == "READ_PATH_CONFIRMED_WAITING_RUNTIME_EVIDENCE":
        return "Python preview read path is confirmed, but observer/runtime evidence is incomplete. Attach or reload missing observers and rerun C28."
    if status == "PARTIAL_DEMO_SHADOW_RUNTIME_EVIDENCE":
        return "Some post-attach evidence exists. Attach or reload the missing A1/A2/A3 observers and broker-shadow consumers, wait for a tick or M5 bar, then rerun C28."
    if status == "TIMEOUT_WAITING_FOR_DEMO_SHADOW_RUNTIME":
        return "No complete demo-shadow runtime proof appeared before timeout. Attach or reload observers and broker-shadow consumers on all accounts, then rerun C28."
    if status == "WAITING_FOR_MT5_RUNTIME_ATTACH":
        return "Attach or reload A3MlPredictionObserver and dry-run broker-shadow consumers on XAUUSD M5 for A1/A2/A3, then rerun C28 with a positive timeout."
    return "Fix C22/C27 preflight issues, then rerun C28."


def _write_status(status_json: Path, payload: dict[str, Any]) -> None:
    status_json.parent.mkdir(parents=True, exist_ok=True)
    status_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    status_json.with_suffix(".md").write_text(render_demo_shadow_post_attach_monitor_md(payload), encoding="utf-8")


def _update_pointer(pointer_path: Path, payload: dict[str, Any]) -> None:
    if not pointer_path.exists():
        return
    pointer = _read_json(pointer_path)
    pointer["c28_demo_shadow_post_attach_monitor_report"] = payload["outputs"]["status_report_json"]
    pointer["c28_demo_shadow_post_attach_monitor_status"] = payload["status"]
    pointer["c28_demo_shadow_runtime_confirmed_all_accounts"] = bool(
        payload["status"] == "DEMO_SHADOW_RUNTIME_CONFIRMED_ALL_ACCOUNTS"
    )
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
