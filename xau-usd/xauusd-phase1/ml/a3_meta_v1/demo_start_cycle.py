from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .demo_activation import run_demo_prediction_activation
from .ea_handoff import generate_ea_handoff_report
from .exploratory_training_rehearsal import run_exploratory_training_rehearsal
from .market_data_export import _table, _utc_now, _write_json_atomic
from .post_attach_monitor import wait_for_post_attach_runtime_evidence
from .runtime_evidence import audit_runtime_evidence
from .runtime_launch_diagnostic import diagnose_runtime_launch


DEFAULT_STATUS_JSON = Path("outputs") / "reports" / "A3_ML_DEMO_START_CYCLE_STATUS.json"
SCHEMA_VERSION = "a3_ml_demo_start_cycle_status_v1"


def run_demo_start_cycle(
    root: Path,
    report_json: Path | None = None,
    *,
    run_pipeline: bool = True,
    refresh_live_readonly: bool = False,
    requested_start_utc: str | None = None,
    max_tick_days: int | None = None,
    auto_publish: bool = False,
    run_rehearsal: bool = True,
    run_runtime_audit: bool = True,
    run_runtime_diagnostic: bool = True,
    run_post_attach_monitor: bool = True,
    post_attach_timeout_seconds: int = 0,
    post_attach_poll_seconds: int = 5,
) -> Path:
    root = root.resolve()
    report_json = (report_json or root / DEFAULT_STATUS_JSON).resolve()
    actions = []
    actions.append(
        _run_action(
            "C10 activation gate",
            lambda: run_demo_prediction_activation(
                root,
                run_pipeline=run_pipeline,
                refresh_live_readonly=refresh_live_readonly,
                requested_start_utc=requested_start_utc,
                max_tick_days=max_tick_days,
                publish=False,
            ),
        )
    )
    if run_rehearsal:
        actions.append(_run_action("C18 exploratory training rehearsal", lambda: run_exploratory_training_rehearsal(root)))
    if run_runtime_audit:
        actions.append(_run_action("C20 runtime evidence audit", lambda: audit_runtime_evidence(root)))
    if run_runtime_diagnostic:
        actions.append(_run_action("C21 runtime launch diagnostic", lambda: diagnose_runtime_launch(root)))
    if run_post_attach_monitor:
        actions.append(
            _run_action(
                "C22 post-attach runtime monitor",
                lambda: wait_for_post_attach_runtime_evidence(
                    root,
                    timeout_seconds=post_attach_timeout_seconds,
                    poll_seconds=post_attach_poll_seconds,
                ),
            )
        )
    if auto_publish:
        c10_after_gate = _read_json(root / "outputs" / "reports" / "A3_ML_DEMO_PREDICTION_ACTIVATION_STATUS.json")
        if c10_after_gate.get("status") == "READY_TO_PUBLISH_HANDOFF":
            actions.append(_run_action("C06 publish EA handoff", lambda: generate_ea_handoff_report(root, publish=True)))
        else:
            actions.append(
                {
                    "action": "C06 publish EA handoff",
                    "status": "SKIPPED_NOT_READY",
                    "output": "",
                    "detail": f"c10_status={c10_after_gate.get('status', 'MISSING')} required=READY_TO_PUBLISH_HANDOFF",
                }
            )
    actions.append(_run_action("C10 final activation summary", lambda: run_demo_prediction_activation(root, run_pipeline=False)))

    summary = _summary(root)
    status = _cycle_status(summary)
    payload = {
        "status": status,
        "stage": "C19-DEMO-START-CYCLE",
        "created_at_utc": _utc_now(),
        "schema_version": SCHEMA_VERSION,
        "dataset_version": summary.get("pointer", {}).get("dataset_version", ""),
        "requested_actions": {
            "run_pipeline": bool(run_pipeline),
            "refresh_live_readonly": bool(refresh_live_readonly),
            "auto_publish": bool(auto_publish),
            "run_rehearsal": bool(run_rehearsal),
            "run_runtime_audit": bool(run_runtime_audit),
            "run_runtime_diagnostic": bool(run_runtime_diagnostic),
            "run_post_attach_monitor": bool(run_post_attach_monitor),
            "post_attach_timeout_seconds": int(post_attach_timeout_seconds),
            "post_attach_poll_seconds": int(post_attach_poll_seconds),
            "requested_start_utc": requested_start_utc or "",
            "max_tick_days": max_tick_days,
        },
        "actions": actions,
        "summary": _summary_head(summary),
        "authorization": {
            "python_demo_predictions_authorized": bool(summary.get("c10", {}).get("authorization", {}).get("python_demo_predictions_authorized", False)),
            "ea_consumption_authorized": bool(summary.get("c10", {}).get("authorization", {}).get("ea_consumption_authorized", False)),
            "mt5_file_publish_requested": bool(auto_publish),
            "mt5_file_publish_attempted": bool(summary.get("c06", {}).get("authorization", {}).get("mt5_file_publish_attempted", False)),
            "broker_action_authorized": False,
        },
        "boundary": {
            "mt5_connection_attempted": bool(refresh_live_readonly),
            "data_export_attempted": bool(refresh_live_readonly),
            "terminal_runtime_change_authorized": False,
            "profile_or_chart_change_authorized": False,
            "ea_file_drop_authorized": bool(summary.get("c06", {}).get("authorization", {}).get("mt5_file_publish_attempted", False)),
            "official_model_artifact_written": Path(root / "outputs" / "reports" / "A3_ML_MODEL_ARTIFACT.json").exists(),
            "broker_action_authorized": False,
        },
        "outputs": {
            "status_report_json": str(report_json),
            "status_report_md": str(report_json.with_suffix(".md")),
        },
        "next_allowed_stage": _next_allowed_stage(status, summary, auto_publish=auto_publish),
    }
    _write_status(report_json, payload)
    _update_pointer(root / "outputs" / "reports" / "C02_DATASET_POINTER.json", payload)
    return report_json


def render_demo_start_cycle_status_md(payload: dict[str, Any]) -> str:
    action_rows = [
        {"Action": item.get("action", ""), "Status": item.get("status", ""), "Detail": item.get("detail", "")}
        for item in payload.get("actions", [])
    ]
    summary_rows = [{"Stage": key, "Status": value} for key, value in payload.get("summary", {}).get("stage_statuses", {}).items()]
    return "\n".join(
        [
            "# A3 ML Demo Start Cycle Status",
            "",
            f"Overall status: {payload['status']}",
            f"Dataset version: {payload.get('dataset_version', '')}",
            "",
            "## Stage Summary",
            "",
            _table(summary_rows, ["Stage", "Status"]) if summary_rows else "No stage statuses.",
            "",
            "## Actions",
            "",
            _table(action_rows, ["Action", "Status", "Detail"]) if action_rows else "No actions ran.",
            "",
            "## Authorization",
            "",
            f"- Python demo predictions authorized: {str(payload['authorization']['python_demo_predictions_authorized']).lower()}.",
            f"- EA consumption authorized: {str(payload['authorization']['ea_consumption_authorized']).lower()}.",
            f"- MT5 file publish requested: {str(payload['authorization']['mt5_file_publish_requested']).lower()}.",
            f"- MT5 file publish attempted: {str(payload['authorization']['mt5_file_publish_attempted']).lower()}.",
            "- Broker action authorized: false.",
            "",
            "## Boundary",
            "",
            f"- MT5 connection attempted: {str(payload['boundary']['mt5_connection_attempted']).lower()}.",
            f"- Data export attempted: {str(payload['boundary']['data_export_attempted']).lower()}.",
            "- Terminal runtime change authorized: false.",
            "- Profile or chart change authorized: false.",
            f"- EA file drop authorized: {str(payload['boundary']['ea_file_drop_authorized']).lower()}.",
            f"- Official model artifact written: {str(payload['boundary']['official_model_artifact_written']).lower()}.",
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
        "c18": _read_json(reports / "A3_ML_EXPLORATORY_TRAINING_REHEARSAL_STATUS.json"),
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
            "C18 rehearsal": summary.get("c18", {}).get("status", "MISSING"),
            "C20 runtime evidence": summary.get("c20", {}).get("status", "MISSING"),
            "C21 runtime launch diagnostic": summary.get("c21", {}).get("status", "MISSING"),
            "C22 post-attach runtime monitor": summary.get("c22", {}).get("status", "MISSING"),
        },
        "dataset_version": summary.get("pointer", {}).get("dataset_version", ""),
    }


def _cycle_status(summary: dict[str, Any]) -> str:
    c10_status = summary.get("c10", {}).get("status", "MISSING")
    if c10_status == "READY_FOR_PASSIVE_EA_CONSUMPTION":
        return "READY_FOR_DEMO_EA_SHADOW_PREDICTIONS"
    if c10_status == "READY_TO_PUBLISH_HANDOFF":
        return "READY_TO_PUBLISH_HANDOFF"
    if c10_status == "WAITING_FOR_DATA":
        return "WAITING_FOR_DATA"
    if any(stage.get("status") == "FAIL_CLOSED" for stage in summary.values() if isinstance(stage, dict)):
        return "FAIL_CLOSED"
    return c10_status


def _next_allowed_stage(status: str, summary: dict[str, Any], *, auto_publish: bool) -> str:
    if status == "READY_FOR_DEMO_EA_SHADOW_PREDICTIONS":
        return "EA handoff files are published for passive shadow reading. Attach/reload EAs only in shadow mode; broker action remains false."
    if status == "READY_TO_PUBLISH_HANDOFF":
        return "Rerun C19 with --auto-publish to copy the already validated handoff files to all configured MT5 Files roots."
    if status == "WAITING_FOR_DATA":
        c21_status = summary.get("c21", {}).get("status", "MISSING")
        if c21_status == "LAUNCH_SENT_NO_OBSERVER_JOURNAL_EVIDENCE":
            return "Attach A3MlPredictionObserver manually on XAUUSD M5 for A1/A2/A3, run C22 to wait for runtime evidence, then rerun C19. Keep A1/A2/A3 collecting data after market data advances."
        if c21_status == "PREFLIGHT_BLOCKED":
            return "Fix the C21 startup-config preflight issue, then rerun C19 before using demo Python predictions."
        return "Keep A1/A2/A3 collecting data, then rerun C19 with --refresh-live-readonly after market data advances."
    if auto_publish and summary.get("c10", {}).get("status") != "READY_TO_PUBLISH_HANDOFF":
        return "Auto-publish was skipped because the official activation gate is not ready."
    return "Review the C10 activation report and fix the first failing gate."


def _run_action(name: str, runner) -> dict[str, Any]:
    try:
        output = runner()
        payload = _read_json(output)
        return {
            "action": name,
            "status": payload.get("status", "MISSING"),
            "output": str(output),
            "detail": "",
        }
    except Exception as exc:  # pragma: no cover - operator diagnostics
        return {
            "action": name,
            "status": "FAIL_CLOSED",
            "output": "",
            "detail": f"{type(exc).__name__}: {exc}",
        }


def _write_status(status_json: Path, payload: dict[str, Any]) -> None:
    status_json.parent.mkdir(parents=True, exist_ok=True)
    status_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    status_json.with_suffix(".md").write_text(render_demo_start_cycle_status_md(payload), encoding="utf-8")


def _update_pointer(pointer_path: Path, payload: dict[str, Any]) -> None:
    if not pointer_path.exists():
        return
    pointer = _read_json(pointer_path)
    pointer["c19_demo_start_cycle_status_report"] = payload["outputs"]["status_report_json"]
    pointer["c19_demo_start_cycle_status"] = payload["status"]
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
