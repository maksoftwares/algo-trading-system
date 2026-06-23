from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .demo_start_cycle import run_demo_start_cycle
from .market_data_export import _table, _utc_now, _write_json_atomic


DEFAULT_STATUS_JSON = Path("outputs") / "reports" / "A3_ML_DEMO_PYTHON_LAUNCH_CONTROLLER_STATUS.json"
SCHEMA_VERSION = "a3_ml_demo_python_launch_controller_status_v1"


def run_demo_python_launch_controller(
    root: Path,
    report_json: Path | None = None,
    *,
    run_pipeline: bool = False,
    refresh_live_readonly: bool = False,
    requested_start_utc: str | None = None,
    max_tick_days: int | None = None,
    auto_publish: bool = False,
    post_attach_timeout_seconds: int = 0,
    post_attach_poll_seconds: int = 5,
) -> Path:
    root = root.resolve()
    report_json = (report_json or root / DEFAULT_STATUS_JSON).resolve()
    c19_path = run_demo_start_cycle(
        root,
        run_pipeline=run_pipeline,
        refresh_live_readonly=refresh_live_readonly,
        requested_start_utc=requested_start_utc,
        max_tick_days=max_tick_days,
        auto_publish=auto_publish,
        run_post_attach_monitor=True,
        post_attach_timeout_seconds=post_attach_timeout_seconds,
        post_attach_poll_seconds=post_attach_poll_seconds,
    )
    summary = _summary(root)
    status = _status(summary)
    payload = {
        "status": status,
        "stage": "C23-ML-DEMO-PYTHON-LAUNCH-CONTROLLER",
        "created_at_utc": _utc_now(),
        "schema_version": SCHEMA_VERSION,
        "dataset_version": summary.get("pointer", {}).get("dataset_version", ""),
        "requested_actions": {
            "run_pipeline": bool(run_pipeline),
            "refresh_live_readonly": bool(refresh_live_readonly),
            "auto_publish": bool(auto_publish),
            "post_attach_timeout_seconds": int(post_attach_timeout_seconds),
            "post_attach_poll_seconds": int(post_attach_poll_seconds),
            "requested_start_utc": requested_start_utc or "",
            "max_tick_days": max_tick_days,
        },
        "summary": _summary_head(summary),
        "readiness": _readiness(summary),
        "authorization": {
            "python_demo_predictions_authorized": bool(
                status == "READY_FOR_DEMO_PYTHON_PREDICTIONS"
                and summary.get("c10", {}).get("authorization", {}).get("python_demo_predictions_authorized", False)
            ),
            "ea_consumption_authorized": bool(
                status == "READY_FOR_DEMO_PYTHON_PREDICTIONS"
                and summary.get("c10", {}).get("authorization", {}).get("ea_consumption_authorized", False)
            ),
            "broker_action_authorized": False,
        },
        "inputs": {
            "c19_demo_start_cycle": str(c19_path),
            "c10_activation": str(root / "outputs" / "reports" / "A3_ML_DEMO_PREDICTION_ACTIVATION_STATUS.json"),
            "c22_post_attach_runtime_monitor": str(root / "outputs" / "reports" / "A3_ML_POST_ATTACH_RUNTIME_MONITOR_STATUS.json"),
        },
        "outputs": {
            "status_report_json": str(report_json),
            "status_report_md": str(report_json.with_suffix(".md")),
        },
        "boundary": {
            "mt5_connection_attempted": bool(refresh_live_readonly),
            "data_export_attempted": bool(refresh_live_readonly),
            "terminal_runtime_launch_attempted": False,
            "terminal_shutdown_attempted": False,
            "profile_or_chart_file_write_attempted": False,
            "ea_file_drop_authorized": bool(summary.get("c19", {}).get("authorization", {}).get("mt5_file_publish_attempted", False)),
            "broker_action_authorized": False,
        },
        "next_allowed_stage": _next_allowed_stage(status),
    }
    _write_status(report_json, payload)
    _update_pointer(root / "outputs" / "reports" / "C02_DATASET_POINTER.json", payload)
    return report_json


def render_demo_python_launch_controller_md(payload: dict[str, Any]) -> str:
    summary_rows = [
        {"Stage": key, "Status": value}
        for key, value in payload.get("summary", {}).get("stage_statuses", {}).items()
    ]
    readiness_rows = [
        {"Check": key, "Ready": str(value).lower()}
        for key, value in payload.get("readiness", {}).items()
        if isinstance(value, bool)
    ]
    return "\n".join(
        [
            "# A3 ML Demo Python Launch Controller Status",
            "",
            f"Overall status: {payload['status']}",
            f"Dataset version: {payload.get('dataset_version', '')}",
            "",
            "## Stage Summary",
            "",
            _table(summary_rows, ["Stage", "Status"]) if summary_rows else "No stage statuses.",
            "",
            "## Readiness",
            "",
            _table(readiness_rows, ["Check", "Ready"]) if readiness_rows else "No readiness checks.",
            "",
            "## Authorization",
            "",
            f"- Python demo predictions authorized: {str(payload['authorization']['python_demo_predictions_authorized']).lower()}.",
            f"- EA consumption authorized: {str(payload['authorization']['ea_consumption_authorized']).lower()}.",
            "- Broker action authorized: false.",
            "",
            "## Boundary",
            "",
            f"- MT5 connection attempted: {str(payload['boundary']['mt5_connection_attempted']).lower()}.",
            f"- Data export attempted: {str(payload['boundary']['data_export_attempted']).lower()}.",
            "- Terminal runtime launch attempted: false.",
            "- Terminal shutdown attempted: false.",
            "- Profile or chart file write attempted: false.",
            f"- EA file drop authorized: {str(payload['boundary']['ea_file_drop_authorized']).lower()}.",
            "- Broker action authorized: false.",
            "",
            "## Next",
            "",
            payload["next_allowed_stage"],
            "",
        ]
    )


def _summary(root: Path) -> dict[str, Any]:
    reports = root / "outputs" / "reports"
    return {
        "pointer": _read_json(reports / "C02_DATASET_POINTER.json"),
        "c03": _read_json(reports / "C03_TRAINING_READINESS_REPORT.json"),
        "c05": _read_json(reports / "A3_ML_TRAINING_STATUS.json"),
        "c04": _read_json(reports / "A3_ML_SHADOW_BRIDGE_STATUS.json"),
        "c06": _read_json(reports / "A3_ML_EA_HANDOFF_STATUS.json"),
        "c10": _read_json(reports / "A3_ML_DEMO_PREDICTION_ACTIVATION_STATUS.json"),
        "c19": _read_json(reports / "A3_ML_DEMO_START_CYCLE_STATUS.json"),
        "c20": _read_json(reports / "A3_ML_RUNTIME_EVIDENCE_STATUS.json"),
        "c21": _read_json(reports / "A3_ML_RUNTIME_LAUNCH_DIAGNOSTIC_STATUS.json"),
        "c22": _read_json(reports / "A3_ML_POST_ATTACH_RUNTIME_MONITOR_STATUS.json"),
    }


def _summary_head(summary: dict[str, Any]) -> dict[str, Any]:
    return {
        "stage_statuses": {
            "C03 readiness": summary.get("c03", {}).get("status", "MISSING"),
            "C05 official training": summary.get("c05", {}).get("status", "MISSING"),
            "C04 shadow bridge": summary.get("c04", {}).get("status", "MISSING"),
            "C06 EA handoff": summary.get("c06", {}).get("status", "MISSING"),
            "C10 activation": summary.get("c10", {}).get("status", "MISSING"),
            "C19 demo start cycle": summary.get("c19", {}).get("status", "MISSING"),
            "C20 runtime evidence": summary.get("c20", {}).get("status", "MISSING"),
            "C21 runtime launch diagnostic": summary.get("c21", {}).get("status", "MISSING"),
            "C22 post-attach runtime monitor": summary.get("c22", {}).get("status", "MISSING"),
        },
        "dataset_version": summary.get("pointer", {}).get("dataset_version", ""),
    }


def _readiness(summary: dict[str, Any]) -> dict[str, Any]:
    return {
        "data_ready": summary.get("c03", {}).get("status") == "PASS",
        "official_model_trained": summary.get("c05", {}).get("status") == "TRAINED_SHADOW_ONLY",
        "python_shadow_bridge_ready": summary.get("c04", {}).get("status") == "READY_SHADOW_ONLY",
        "ea_handoff_ready_or_published": summary.get("c06", {}).get("status") in {"READY_DRY_RUN", "PUBLISHED_TO_MT5_FILES"},
        "runtime_evidence_all_accounts": summary.get("c20", {}).get("status") == "RUNTIME_EVIDENCE_PRESENT_ALL_ACCOUNTS",
        "runtime_launch_diagnostic_all_accounts": summary.get("c21", {}).get("status") == "RUNTIME_EVIDENCE_PRESENT_ALL_ACCOUNTS",
        "post_attach_monitor_ready": summary.get("c22", {}).get("status") == "RUNTIME_EVIDENCE_PRESENT_ALL_ACCOUNTS",
        "activation_authorizes_python": bool(summary.get("c10", {}).get("authorization", {}).get("python_demo_predictions_authorized", False)),
        "activation_authorizes_ea_consumption": bool(summary.get("c10", {}).get("authorization", {}).get("ea_consumption_authorized", False)),
    }


def _status(summary: dict[str, Any]) -> str:
    statuses = [
        stage.get("status", "")
        for stage in summary.values()
        if isinstance(stage, dict)
    ]
    c10_status = summary.get("c10", {}).get("status", "MISSING")
    c19_status = summary.get("c19", {}).get("status", "MISSING")
    c22_status = summary.get("c22", {}).get("status", "MISSING")
    c03_status = summary.get("c03", {}).get("status", "MISSING")
    if "FAIL_CLOSED" in statuses:
        return "FAIL_CLOSED"
    if c10_status == "READY_FOR_PASSIVE_EA_CONSUMPTION" and c19_status == "READY_FOR_DEMO_EA_SHADOW_PREDICTIONS":
        return "READY_FOR_DEMO_PYTHON_PREDICTIONS"
    waiting_for_data = c03_status in {"NO_GO", "MISSING", ""} or c10_status == "WAITING_FOR_DATA"
    waiting_for_attach = c22_status == "WAITING_FOR_MANUAL_ATTACH"
    if waiting_for_attach and waiting_for_data:
        return "WAITING_FOR_MANUAL_ATTACH_AND_DATA"
    if waiting_for_attach:
        return "WAITING_FOR_MANUAL_ATTACH"
    if c22_status in {"TIMEOUT_WAITING_FOR_RUNTIME_EVIDENCE", "PARTIAL_RUNTIME_EVIDENCE_PRESENT"} and waiting_for_data:
        return "WAITING_FOR_RUNTIME_EVIDENCE_AND_DATA"
    if c22_status == "TIMEOUT_WAITING_FOR_RUNTIME_EVIDENCE":
        return "WAITING_FOR_RUNTIME_EVIDENCE"
    if c22_status == "PARTIAL_RUNTIME_EVIDENCE_PRESENT":
        return "PARTIAL_RUNTIME_EVIDENCE_PRESENT"
    if c10_status == "READY_TO_PUBLISH_HANDOFF":
        return "READY_TO_PUBLISH_HANDOFF"
    if waiting_for_data:
        return "WAITING_FOR_DATA"
    return c10_status


def _next_allowed_stage(status: str) -> str:
    if status == "READY_FOR_DEMO_PYTHON_PREDICTIONS":
        return "Python demo predictions are authorized for passive EA consumption. Broker action remains false."
    if status == "WAITING_FOR_MANUAL_ATTACH_AND_DATA":
        return "Attach A3MlPredictionObserver on XAUUSD M5 for A1/A2/A3, run C23 with a positive post-attach timeout, and keep collecting/exporting data until C03 passes."
    if status == "WAITING_FOR_MANUAL_ATTACH":
        return "Attach A3MlPredictionObserver on XAUUSD M5 for A1/A2/A3, then rerun C23 with a positive post-attach timeout."
    if status == "WAITING_FOR_RUNTIME_EVIDENCE_AND_DATA":
        return "Runtime evidence is incomplete and data is still below readiness. Reload missing observers, rerun C23, and continue data collection."
    if status == "WAITING_FOR_RUNTIME_EVIDENCE":
        return "Runtime evidence is incomplete. Reload missing observers, then rerun C23 with a positive post-attach timeout."
    if status == "PARTIAL_RUNTIME_EVIDENCE_PRESENT":
        return "Some accounts are logging. Attach or reload the missing accounts, then rerun C23."
    if status == "READY_TO_PUBLISH_HANDOFF":
        return "Rerun C19 or C23 with --auto-publish after confirming the handoff should be copied to all MT5 Files roots."
    if status == "WAITING_FOR_DATA":
        return "Keep A1/A2/A3 collecting data, then rerun C23 with --refresh-live-readonly after market data advances."
    return "Review C10/C19/C22 reports and fix the first failing gate."


def _write_status(status_json: Path, payload: dict[str, Any]) -> None:
    status_json.parent.mkdir(parents=True, exist_ok=True)
    status_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    status_json.with_suffix(".md").write_text(render_demo_python_launch_controller_md(payload), encoding="utf-8")


def _update_pointer(pointer_path: Path, payload: dict[str, Any]) -> None:
    if not pointer_path.exists():
        return
    pointer = _read_json(pointer_path)
    pointer["c23_demo_python_launch_controller_report"] = payload["outputs"]["status_report_json"]
    pointer["c23_demo_python_launch_controller_status"] = payload["status"]
    pointer["python_demo_predictions_authorized"] = bool(payload["authorization"]["python_demo_predictions_authorized"])
    pointer["ea_consumption_authorized"] = bool(payload["authorization"]["ea_consumption_authorized"])
    pointer["broker_action_authorized"] = False
    _write_json_atomic(pointer_path, pointer)


def _read_json(path_or_text: str | Path) -> dict[str, Any]:
    if not path_or_text:
        return {}
    path = Path(path_or_text)
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))
