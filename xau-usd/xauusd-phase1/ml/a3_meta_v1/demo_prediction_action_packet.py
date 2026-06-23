from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from .broker_shadow_manual_attach_packet import generate_broker_shadow_manual_attach_packet
from .demo_python_launch_controller import run_demo_python_launch_controller
from .demo_shadow_operator_runbook import generate_demo_shadow_operator_runbook
from .market_data_export import _table, _utc_now, _write_json_atomic
from .readiness_gap import generate_readiness_gap_report


DEFAULT_STATUS_JSON = Path("outputs") / "reports" / "A3_ML_DEMO_PREDICTION_ACTION_PACKET.json"
SCHEMA_VERSION = "a3_ml_demo_prediction_action_packet_v1"


def generate_demo_prediction_action_packet(
    root: Path,
    report_json: Path | None = None,
    *,
    refresh_live_readonly: bool = False,
    requested_start_utc: str | None = None,
    max_tick_days: int | None = None,
    post_attach_timeout_seconds: int = 0,
    post_attach_poll_seconds: int = 5,
) -> Path:
    root = root.resolve()
    report_json = (report_json or root / DEFAULT_STATUS_JSON).resolve()
    c23_path = run_demo_python_launch_controller(
        root,
        refresh_live_readonly=refresh_live_readonly,
        requested_start_utc=requested_start_utc,
        max_tick_days=max_tick_days,
        post_attach_timeout_seconds=post_attach_timeout_seconds,
        post_attach_poll_seconds=post_attach_poll_seconds,
    )
    c11_path = generate_readiness_gap_report(root)
    c25_path = generate_broker_shadow_manual_attach_packet(root)
    c29_path = generate_demo_shadow_operator_runbook(root)
    reports = root / "outputs" / "reports"
    c23 = _read_json(c23_path)
    c11 = _read_json(c11_path)
    c15 = _read_json(reports / "A3_ML_OBSERVER_MANUAL_ATTACH_PACKET.json")
    c18 = _read_json(reports / "A3_ML_EXPLORATORY_TRAINING_REHEARSAL_STATUS.json")
    c20 = _read_json(reports / "A3_ML_RUNTIME_EVIDENCE_STATUS.json")
    c22 = _read_json(reports / "A3_ML_POST_ATTACH_RUNTIME_MONITOR_STATUS.json")
    c25 = _read_json(c25_path)
    c26 = _read_json(reports / "A3_ML_RESEARCH_PREVIEW_HANDOFF_REHEARSAL_STATUS.json")
    c27 = _read_json(reports / "A3_ML_RESEARCH_PREVIEW_RUNTIME_VERIFIER_STATUS.json")
    c28 = _read_json(reports / "A3_ML_DEMO_SHADOW_POST_ATTACH_MONITOR_STATUS.json")
    c29 = _read_json(c29_path)
    c30 = _read_json(reports / "A3_ML_BROKER_SHADOW_PRESET_DEPLOY_STATUS.json")
    c31 = _read_json(reports / "A3_ML_DEMO_ATTACH_WATCH_STATUS.json")
    c32 = _read_json(reports / "A3_ML_DEMO_OPERATOR_LAUNCH_KIT_STATUS.json")
    pointer = _read_json(reports / "C02_DATASET_POINTER.json")
    status = _status(c23)
    payload = {
        "status": status,
        "stage": "C24-ML-DEMO-PREDICTION-ACTION-PACKET",
        "created_at_utc": _utc_now(),
        "schema_version": SCHEMA_VERSION,
        "dataset_version": pointer.get("dataset_version", c23.get("dataset_version", "")),
        "requested_actions": {
            "refresh_live_readonly": bool(refresh_live_readonly),
            "requested_start_utc": requested_start_utc or "",
            "max_tick_days": max_tick_days,
            "post_attach_timeout_seconds": int(post_attach_timeout_seconds),
            "post_attach_poll_seconds": int(post_attach_poll_seconds),
        },
        "summary": {
            "c23_status": c23.get("status", "MISSING"),
            "c11_status": c11.get("status", "MISSING"),
            "c15_status": c15.get("status", "MISSING"),
            "c18_status": c18.get("status", "MISSING"),
            "c20_status": c20.get("status", "MISSING"),
            "c22_status": c22.get("status", "MISSING"),
            "c25_status": c25.get("status", "MISSING"),
            "c26_status": c26.get("status", "MISSING"),
            "c27_status": c27.get("status", "MISSING"),
            "c28_status": c28.get("status", "MISSING"),
            "c29_status": c29.get("status", "MISSING"),
            "c30_status": c30.get("status", "MISSING"),
            "c31_status": c31.get("status", "MISSING"),
            "c32_status": c32.get("status", "MISSING"),
        },
        "readiness": c23.get("readiness", {}),
        "data_gaps": _data_gaps(c11),
        "manual_attach": _manual_attach(c15),
        "broker_shadow_attach": _broker_shadow_attach(c25),
        "runtime_evidence": c20.get("runtime_evidence", {}),
        "operator_actions": _operator_actions(status, c23, c11, c15, c18, c20, c22, c25, c26, c27, c28, c30, c31, c32),
        "commands": _commands(root),
        "authorization": {
            "python_demo_predictions_authorized": bool(c23.get("authorization", {}).get("python_demo_predictions_authorized", False)),
            "ea_consumption_authorized": bool(c23.get("authorization", {}).get("ea_consumption_authorized", False)),
            "broker_action_authorized": False,
        },
        "inputs": {
            "c23_demo_python_launch_controller": str(c23_path),
            "c11_readiness_gap": str(c11_path),
            "c15_manual_attach_packet": str(reports / "A3_ML_OBSERVER_MANUAL_ATTACH_PACKET.json"),
            "c18_exploratory_training_rehearsal": str(reports / "A3_ML_EXPLORATORY_TRAINING_REHEARSAL_STATUS.json"),
            "c20_runtime_evidence": str(reports / "A3_ML_RUNTIME_EVIDENCE_STATUS.json"),
            "c22_post_attach_runtime_monitor": str(reports / "A3_ML_POST_ATTACH_RUNTIME_MONITOR_STATUS.json"),
            "c25_broker_shadow_manual_attach_packet": str(c25_path),
            "c26_research_preview_handoff_rehearsal": str(reports / "A3_ML_RESEARCH_PREVIEW_HANDOFF_REHEARSAL_STATUS.json"),
            "c27_research_preview_runtime_verifier": str(reports / "A3_ML_RESEARCH_PREVIEW_RUNTIME_VERIFIER_STATUS.json"),
            "c28_demo_shadow_post_attach_monitor": str(reports / "A3_ML_DEMO_SHADOW_POST_ATTACH_MONITOR_STATUS.json"),
            "c29_demo_shadow_operator_runbook": str(c29_path),
            "c30_broker_shadow_preset_deploy": str(reports / "A3_ML_BROKER_SHADOW_PRESET_DEPLOY_STATUS.json"),
            "c31_demo_attach_watch": str(reports / "A3_ML_DEMO_ATTACH_WATCH_STATUS.json"),
            "c32_demo_operator_launch_kit": str(reports / "A3_ML_DEMO_OPERATOR_LAUNCH_KIT_STATUS.json"),
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
            "model_training_authorized": False,
            "broker_action_authorized": False,
        },
        "next_allowed_stage": _next_allowed_stage(status),
    }
    _write_status(report_json, payload)
    _update_pointer(root / "outputs" / "reports" / "C02_DATASET_POINTER.json", payload)
    return report_json


def render_demo_prediction_action_packet_md(payload: dict[str, Any]) -> str:
    summary_rows = [{"Item": key, "Status": str(value)} for key, value in payload.get("summary", {}).items()]
    gap_rows = [
        {"Gate": item.get("gate", ""), "Observed": item.get("observed", ""), "Required": item.get("required", ""), "Gap": item.get("gap_text", "")}
        for item in payload.get("data_gaps", {}).get("failed_gates", [])
    ]
    account_rows = [
        {
            "Account": item.get("account_label", ""),
            "Expert": str(item.get("expert_exists", False)).lower(),
            "Preset": str(item.get("preset_exists", False)).lower(),
            "Startup log": str(item.get("startup_log_exists", False)).lower(),
            "Prediction log": str(item.get("prediction_log_exists", False)).lower(),
        }
        for item in payload.get("manual_attach", {}).get("accounts", [])
    ]
    broker_rows = [
        {
            "Account": item.get("account_label", ""),
            "Active ready": str(item.get("active_broker_executors_ml_ready", False)).lower(),
            "Expected EX5": str(item.get("expected_compiled_ex5_all_exist", False)).lower(),
            "Broker tap": str(item.get("broker_shadow_tap_exists", False)).lower(),
        }
        for item in payload.get("broker_shadow_attach", {}).get("accounts", [])
    ]
    actions = "\n".join(f"{index}. {item}" for index, item in enumerate(payload.get("operator_actions", []), start=1)) or "1. none"
    command_lines = "\n".join(f"- {key}: `{value}`" for key, value in payload.get("commands", {}).items())
    return "\n".join(
        [
            "# A3 ML Demo Prediction Action Packet",
            "",
            f"Overall status: {payload['status']}",
            f"Dataset version: {payload.get('dataset_version', '')}",
            "",
            "## Summary",
            "",
            _table(summary_rows, ["Item", "Status"]) if summary_rows else "No summary.",
            "",
            "## Data Gaps",
            "",
            _table(gap_rows, ["Gate", "Observed", "Required", "Gap"]) if gap_rows else "No failed data gates.",
            "",
            "## Manual Attach State",
            "",
            _table(account_rows, ["Account", "Expert", "Preset", "Startup log", "Prediction log"]) if account_rows else "No account details.",
            "",
            "## Broker Shadow State",
            "",
            _table(broker_rows, ["Account", "Active ready", "Expected EX5", "Broker tap"]) if broker_rows else "No broker shadow details.",
            "",
            "## Operator Actions",
            "",
            actions,
            "",
            "## Commands",
            "",
            command_lines,
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
            "- Model training authorized: false.",
            "- Broker action authorized: false.",
            "",
            "## Next",
            "",
            payload["next_allowed_stage"],
            "",
        ]
    )


def _status(c23: dict[str, Any]) -> str:
    c23_status = c23.get("status", "MISSING")
    mapping = {
        "READY_FOR_DEMO_PYTHON_PREDICTIONS": "READY_FOR_DEMO_PYTHON_PREDICTIONS",
        "WAITING_FOR_MANUAL_ATTACH_AND_DATA": "ACTION_REQUIRED_MANUAL_ATTACH_AND_DATA",
        "WAITING_FOR_MANUAL_ATTACH": "ACTION_REQUIRED_MANUAL_ATTACH",
        "WAITING_FOR_RUNTIME_EVIDENCE_AND_DATA": "ACTION_REQUIRED_RUNTIME_EVIDENCE_AND_DATA",
        "WAITING_FOR_RUNTIME_EVIDENCE": "ACTION_REQUIRED_RUNTIME_EVIDENCE",
        "PARTIAL_RUNTIME_EVIDENCE_PRESENT": "ACTION_REQUIRED_PARTIAL_RUNTIME_EVIDENCE",
        "READY_TO_PUBLISH_HANDOFF": "READY_TO_PUBLISH_HANDOFF",
        "WAITING_FOR_DATA": "WAITING_FOR_DATA",
        "FAIL_CLOSED": "FAIL_CLOSED",
    }
    return mapping.get(c23_status, c23_status)


def _data_gaps(c11: dict[str, Any]) -> dict[str, Any]:
    failed = [item for item in c11.get("gate_gaps", []) if not item.get("passed")]
    active_gap = next((item for item in failed if item.get("gate") == "active_weeks"), {})
    setup_gap = next((item for item in failed if item.get("gate") == "market_setup_groups"), {})
    return {
        "status": c11.get("status", "MISSING"),
        "failed_gates": failed,
        "remaining_active_weeks": c11.get("backfill_assessment", {}).get("remaining_active_weeks", 0),
        "estimated_active_weeks_pass_date_utc": c11.get("backfill_assessment", {}).get("estimated_active_weeks_pass_date_utc", ""),
        "market_setup_groups_gap": setup_gap.get("gap_value", 0),
        "active_weeks_gap": active_gap.get("gap_value", 0),
    }


def _manual_attach(c15: dict[str, Any]) -> dict[str, Any]:
    return {
        "status": c15.get("status", "MISSING"),
        "manual_attach_required": bool(c15.get("authorization", {}).get("manual_attach_required", False)),
        "accounts": c15.get("accounts", []),
        "steps": c15.get("manual_attach_steps", []),
    }


def _broker_shadow_attach(c25: dict[str, Any]) -> dict[str, Any]:
    return {
        "status": c25.get("status", "MISSING"),
        "manual_attach_required": bool(c25.get("authorization", {}).get("manual_attach_required", False)),
        "runtime_all_accounts": bool(
            c25.get("runtime_evidence", {}).get("broker_shadow_tap_runtime_all_accounts", False)
        ),
        "accounts": c25.get("accounts", []),
        "steps": c25.get("manual_attach_steps", []),
    }


def _operator_actions(
    status: str,
    c23: dict[str, Any],
    c11: dict[str, Any],
    c15: dict[str, Any],
    c18: dict[str, Any],
    c20: dict[str, Any],
    c22: dict[str, Any],
    c25: dict[str, Any],
    c26: dict[str, Any],
    c27: dict[str, Any],
    c28: dict[str, Any],
    c30: dict[str, Any],
    c31: dict[str, Any],
    c32: dict[str, Any],
) -> list[str]:
    actions: list[str] = []
    if status == "READY_FOR_DEMO_PYTHON_PREDICTIONS":
        return ["Run passive demo Python predictions only; broker action remains false."]
    if c30.get("status") != "DEPLOYED_SAFE_PASSIVE_PRESETS":
        actions.append("Run C30 with --deploy to write safe passive broker-shadow presets for A1, A2, and A3 before broker-shadow attach.")
    if c32.get("status", "MISSING") == "MISSING":
        actions.append("Run C32 to generate the local operator launch kit for MT5 attach/watch.")
    if c15.get("authorization", {}).get("manual_attach_required") or c22.get("status") == "WAITING_FOR_MANUAL_ATTACH":
        actions.append("Attach A3MlPredictionObserver on XAUUSD M5 for A1, A2, and A3 using the passive preset.")
    if c31.get("status") not in {"ATTACH_RUNTIME_FILES_PRESENT_ALL_ACCOUNTS", "MISSING"}:
        actions.append("Use C31 to watch exact attach files and identify any missing account before running C28.")
    elif c31.get("status", "MISSING") == "MISSING":
        actions.append("Run C31 while attaching MT5 EAs to watch exact observer and broker-shadow files appear.")
        actions.append("After attach, run the C23 wait command with --post-attach-timeout-seconds 300.")
    broker_shadow_ready = bool(c20.get("runtime_evidence", {}).get("broker_shadow_tap_runtime_all_accounts", False)) or bool(
        c25.get("runtime_evidence", {}).get("broker_shadow_tap_runtime_all_accounts", False)
    )
    if not broker_shadow_ready:
        c25_status = c25.get("status", "MISSING")
        if c25_status in {"MANUAL_ATTACH_REQUIRED", "PARTIAL_BROKER_SHADOW_RUNTIME_PRESENT"}:
            actions.append(
                "Use C25 to attach or reload dry-run broker shadow consumers on XAUUSD M5 for A1, A2, and A3."
            )
        elif c25_status == "PREFLIGHT_BLOCKED":
            actions.append("Fix the C25 broker-shadow preflight before expecting broker shadow tap logs.")
        else:
            actions.append("Generate/review C25 so broker shadow consumer attach steps are account-specific.")
    c26_status = c26.get("status", "MISSING")
    if c18.get("status") == "REHEARSED_RESEARCH_ONLY" and c26_status != "PUBLISHED_RESEARCH_PREVIEW_FAIL_CLOSED":
        actions.append("Optional today: run C26 with --publish to let MT5 read research-preview ABSTAIN rows from Python output.")
    elif c26_status == "PUBLISHED_RESEARCH_PREVIEW_FAIL_CLOSED":
        actions.append("C26 research-preview ABSTAIN handoff is published; after attach, broker-shadow taps should log ml_available=true.")
        if c28.get("status") != "DEMO_SHADOW_RUNTIME_CONFIRMED_ALL_ACCOUNTS":
            actions.append("After attach/reload, run C28 to wait for observer logs and prove the broker-shadow EAs read the Python preview handoff.")
    if c11.get("status") != "C03_PASS":
        actions.extend(c11.get("next_actions", []))
    if not actions:
        actions.append(c23.get("next_allowed_stage", "Review C23 and rerun after upstream state changes."))
    return actions


def _commands(root: Path) -> dict[str, str]:
    python = _quote(sys.executable)
    c23 = _quote(str(root / "scripts" / "c23_run_demo_python_launch_controller.py"))
    c24 = _quote(str(root / "scripts" / "c24_generate_demo_prediction_action_packet.py"))
    c25 = _quote(str(root / "scripts" / "c25_generate_broker_shadow_manual_attach_packet.py"))
    c26 = _quote(str(root / "scripts" / "c26_publish_research_preview_handoff_rehearsal.py"))
    c27 = _quote(str(root / "scripts" / "c27_verify_research_preview_runtime_read_path.py"))
    c28 = _quote(str(root / "scripts" / "c28_wait_for_demo_shadow_post_attach.py"))
    c29 = _quote(str(root / "scripts" / "c29_generate_demo_shadow_operator_runbook.py"))
    c30 = _quote(str(root / "scripts" / "c30_deploy_broker_shadow_presets.py"))
    c31 = _quote(str(root / "scripts" / "c31_watch_demo_attach.py"))
    c32 = _quote(str(root / "scripts" / "c32_generate_demo_operator_launch_kit.py"))
    kit = _quote(str(root / "outputs" / "reports" / "A3_ML_DEMO_OPERATOR_LAUNCH_KIT.ps1"))
    root_arg = _quote(str(root))
    return {
        "check_now": f"{python} {c24} --root {root_arg}",
        "operator_runbook": f"{python} {c29} --root {root_arg}",
        "generate_operator_launch_kit": f"{python} {c32} --root {root_arg}",
        "run_operator_launch_kit": f"powershell -ExecutionPolicy Bypass -File {kit}",
        "broker_shadow_preset_deploy": f"{python} {c30} --root {root_arg} --deploy",
        "broker_shadow_attach_packet": f"{python} {c25} --root {root_arg}",
        "demo_attach_watch": f"{python} {c31} --root {root_arg} --timeout-seconds 300 --poll-seconds 5",
        "research_preview_handoff_publish": f"{python} {c26} --root {root_arg} --publish",
        "research_preview_runtime_verify": f"{python} {c27} --root {root_arg}",
        "demo_shadow_post_attach_wait": f"{python} {c28} --root {root_arg} --timeout-seconds 300 --poll-seconds 5",
        "post_attach_wait": f"{python} {c23} --root {root_arg} --post-attach-timeout-seconds 300 --post-attach-poll-seconds 5",
        "refresh_after_market_data": f"{python} {c23} --root {root_arg} --refresh-live-readonly --post-attach-timeout-seconds 300 --post-attach-poll-seconds 5",
    }


def _next_allowed_stage(status: str) -> str:
    if status == "READY_FOR_DEMO_PYTHON_PREDICTIONS":
        return "Python demo predictions may run in passive mode; broker action remains false."
    if status == "ACTION_REQUIRED_MANUAL_ATTACH_AND_DATA":
        return "Attach the passive observer on all accounts, run C23 with a positive timeout, and continue collecting/exporting data until C03 passes."
    if status == "ACTION_REQUIRED_MANUAL_ATTACH":
        return "Attach the passive observer on all accounts, then run C23 with a positive timeout."
    if status == "ACTION_REQUIRED_RUNTIME_EVIDENCE_AND_DATA":
        return "Fix missing runtime evidence and continue collecting/exporting data until C03 passes."
    if status == "ACTION_REQUIRED_RUNTIME_EVIDENCE":
        return "Fix missing runtime evidence, then rerun C23."
    if status == "WAITING_FOR_DATA":
        return "Continue collecting/exporting A1/A2/A3 data and rerun C24 after new market sessions."
    if status == "READY_TO_PUBLISH_HANDOFF":
        return "Review C10/C19, then run with auto-publish if the handoff should be copied to MT5 Files roots."
    return "Review the action list above and rerun C24 after the first item changes."


def _quote(value: str) -> str:
    return f"'{value}'"


def _write_status(status_json: Path, payload: dict[str, Any]) -> None:
    status_json.parent.mkdir(parents=True, exist_ok=True)
    status_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    status_json.with_suffix(".md").write_text(render_demo_prediction_action_packet_md(payload), encoding="utf-8")


def _update_pointer(pointer_path: Path, payload: dict[str, Any]) -> None:
    if not pointer_path.exists():
        return
    pointer = _read_json(pointer_path)
    pointer["c24_demo_prediction_action_packet_report"] = payload["outputs"]["status_report_json"]
    pointer["c24_demo_prediction_action_packet_status"] = payload["status"]
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
