from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Callable

from .contract_expansion_config_proposal import generate_contract_expansion_config_proposal
from .contract_expansion_impact_estimate import generate_contract_expansion_impact_estimate
from .contract_expansion_packet import generate_contract_expansion_packet
from .decision_backfill_audit import generate_decision_backfill_audit
from .demo_prediction_action_packet import generate_demo_prediction_action_packet
from .demo_activation import run_demo_prediction_activation
from .demo_python_launch_controller import run_demo_python_launch_controller
from .demo_shadow_collection_health import check_demo_shadow_collection_health
from .ea_consumer_readiness import audit_ea_ml_consumers
from .ea_handoff import generate_ea_handoff_report
from .gate_closure_plan import generate_gate_closure_plan
from .historical_decision_coverage import generate_historical_decision_coverage_report
from .historical_backfill_replay_plan import generate_historical_backfill_replay_plan
from .isolated_strategy_tester_terminal_root import prepare_isolated_strategy_tester_terminal_root
from .isolated_strategy_tester_workspace import prepare_isolated_strategy_tester_workspace
from .label_trainability_blocker_audit import generate_label_trainability_blocker_audit
from .latest_dataset_repair import repair_latest_dataset_if_needed
from .market_data_export import _table, _utc_now, _write_json_atomic
from .readiness_gap import generate_readiness_gap_report
from .readiness_progress_tracker import generate_readiness_progress_tracker
from .readiness_work_order import generate_demo_readiness_work_order
from .research_preview_handoff_rehearsal import publish_research_preview_handoff_rehearsal
from .research_preview_runtime_verifier import verify_research_preview_runtime_read_path
from .reviewer_decision_intake import process_reviewer_decision
from .reviewer_decision_packet import generate_reviewer_decision_packet
from .reviewer_decision_template import generate_reviewer_decision_template
from .reviewer_handoff_package import package_reviewer_handoff
from .reviewer_submission_bundle import generate_reviewer_submission_bundle
from .strategy_tester_replay_packet import generate_strategy_tester_replay_packet
from .strategy_tester_account_context_decision import generate_strategy_tester_account_context_decision


DEFAULT_REPORT_JSON = Path("outputs") / "reports" / "A3_ML_DEMO_READINESS_CYCLE_STATUS.json"
SCHEMA_VERSION = "a3_ml_demo_readiness_cycle_status_v1"


def run_demo_readiness_cycle(
    root: Path,
    report_json: Path | None = None,
    *,
    refresh_live_readonly: bool = False,
    publish_research_preview: bool = True,
    decision_json: Path | None = None,
    apply_reviewer_configs: bool = False,
    post_attach_timeout_seconds: int = 0,
    post_attach_poll_seconds: int = 5,
) -> Path:
    root = root.resolve()
    report_json = (report_json or root / DEFAULT_REPORT_JSON).resolve()
    steps: list[dict[str, Any]] = []

    steps.append(
        _step(
            "C23 demo Python launch controller",
            lambda: run_demo_python_launch_controller(
                root,
                run_pipeline=bool(refresh_live_readonly),
                refresh_live_readonly=bool(refresh_live_readonly),
                post_attach_timeout_seconds=post_attach_timeout_seconds,
                post_attach_poll_seconds=post_attach_poll_seconds,
            ),
        )
    )
    steps.append(_step("C16 EA consumer readiness audit", lambda: audit_ea_ml_consumers(root)))
    steps.append(_step("C06 EA handoff dry-run", lambda: generate_ea_handoff_report(root, publish=False)))
    steps.append(
        _step(
            "C10 activation summary after EA checks",
            lambda: run_demo_prediction_activation(root, run_pipeline=False),
        )
    )
    for name, func in (
        ("C11 readiness gap", generate_readiness_gap_report),
        ("C34 decision backfill audit", generate_decision_backfill_audit),
        ("C35 contract expansion packet", generate_contract_expansion_packet),
        ("C36 contract expansion config proposal", generate_contract_expansion_config_proposal),
        ("C37 contract expansion impact estimate", generate_contract_expansion_impact_estimate),
        ("C38 label trainability blocker", generate_label_trainability_blocker_audit),
        ("C39 historical decision coverage", generate_historical_decision_coverage_report),
    ):
        steps.append(_step(name, lambda func=func: func(root)))
    if publish_research_preview:
        steps.append(
            _step(
                "C26 research preview handoff publish",
                lambda: publish_research_preview_handoff_rehearsal(root, publish=True),
            )
        )
        steps.append(
            _step(
                "C27 research preview runtime verifier",
                lambda: verify_research_preview_runtime_read_path(root),
            )
        )
    for name, func in (
        ("C33 demo shadow collection health", check_demo_shadow_collection_health),
        ("C48 latest dataset repair guard", repair_latest_dataset_if_needed),
        ("C40 demo readiness work order", generate_demo_readiness_work_order),
        ("C41 reviewer decision packet", generate_reviewer_decision_packet),
        ("C44 reviewer decision template", generate_reviewer_decision_template),
        ("C45 reviewer submission bundle", generate_reviewer_submission_bundle),
        ("C49 reviewer handoff package", package_reviewer_handoff),
        ("C46 readiness progress tracker", generate_readiness_progress_tracker),
        ("C47 gate closure plan", generate_gate_closure_plan),
        ("C50 historical backfill/replay plan", generate_historical_backfill_replay_plan),
        ("C51 Strategy Tester replay packet", generate_strategy_tester_replay_packet),
        ("C52 isolated Strategy Tester workspace", prepare_isolated_strategy_tester_workspace),
        ("C53 isolated Strategy Tester terminal root", prepare_isolated_strategy_tester_terminal_root),
        ("C55 Strategy Tester account context decision", generate_strategy_tester_account_context_decision),
    ):
        steps.append(_step(name, lambda func=func: func(root)))
    steps.append(
        _step(
            "C42 reviewer decision intake",
            lambda: process_reviewer_decision(
                root,
                decision_json=decision_json,
                apply_configs=apply_reviewer_configs,
            ),
        )
    )
    steps.append(_step("C24 demo prediction action packet", lambda: generate_demo_prediction_action_packet(root)))

    summary = _summary(root)
    status = _status(summary)
    payload = {
        "status": status,
        "stage": "C43-DEMO-READINESS-CYCLE",
        "created_at_utc": _utc_now(),
        "schema_version": SCHEMA_VERSION,
        "dataset_version": summary.get("pointer", {}).get("dataset_version", ""),
        "requested_actions": {
            "refresh_live_readonly": bool(refresh_live_readonly),
            "publish_research_preview": bool(publish_research_preview),
            "decision_json": str(decision_json.resolve()) if decision_json else "",
            "apply_reviewer_configs": bool(apply_reviewer_configs),
            "post_attach_timeout_seconds": int(post_attach_timeout_seconds),
            "post_attach_poll_seconds": int(post_attach_poll_seconds),
        },
        "summary": _summary_head(summary),
        "steps": steps,
        "authorization": {
            "python_demo_predictions_authorized": bool(
                summary.get("pointer", {}).get("python_demo_predictions_authorized", False)
            ),
            "ea_consumption_authorized": bool(summary.get("pointer", {}).get("ea_consumption_authorized", False)),
            "broker_action_authorized": False,
        },
        "commands": _commands(root),
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
            "python_demo_predictions_authorized": bool(
                summary.get("pointer", {}).get("python_demo_predictions_authorized", False)
            ),
            "ea_consumption_authorized": bool(summary.get("pointer", {}).get("ea_consumption_authorized", False)),
            "broker_action_authorized": False,
        },
        "next_allowed_stage": _next_allowed_stage(status),
    }
    _write_status(report_json, payload)
    _update_pointer(root / "outputs" / "reports" / "C02_DATASET_POINTER.json", payload)
    return report_json


def render_demo_readiness_cycle_md(payload: dict[str, Any]) -> str:
    summary = payload.get("summary", {})
    step_rows = [
        {
            "Step": item.get("step", ""),
            "Status": item.get("status", ""),
            "Report": item.get("report", ""),
        }
        for item in payload.get("steps", [])
    ]
    command_lines = "\n".join(f"- {key}: `{value}`" for key, value in payload.get("commands", {}).items())
    return "\n".join(
        [
            "# A3 ML Demo Readiness Cycle Status",
            "",
            f"Overall status: {payload['status']}",
            f"Dataset version: {payload.get('dataset_version', '')}",
            "",
            "## Summary",
            "",
            f"- C03 readiness: {summary.get('c03_status', '')}.",
            f"- C05 training: {summary.get('c05_status', '')}.",
            f"- C04 shadow bridge: {summary.get('c04_status', '')}.",
            f"- C06 EA handoff: {summary.get('c06_status', '')}.",
            f"- C10 activation: {summary.get('c10_status', '')}.",
            f"- C16 EA consumer readiness: {summary.get('c16_status', '')}.",
            f"- C23 launch controller: {summary.get('c23_status', '')}.",
            f"- C24 action packet: {summary.get('c24_status', '')}.",
            f"- C33 collection health: {summary.get('c33_status', '')}.",
            f"- C48 latest dataset repair: {summary.get('c48_status', '')}.",
            f"- C40 work order: {summary.get('c40_status', '')}.",
            f"- C41 reviewer packet: {summary.get('c41_status', '')}.",
            f"- C44 reviewer template: {summary.get('c44_status', '')}.",
            f"- C45 reviewer bundle: {summary.get('c45_status', '')}.",
            f"- C49 reviewer handoff package: {summary.get('c49_status', '')}.",
            f"- C46 progress tracker: {summary.get('c46_status', '')}.",
            f"- C47 gate closure plan: {summary.get('c47_status', '')}.",
            f"- C50 historical backfill/replay plan: {summary.get('c50_status', '')}.",
            f"- C51 Strategy Tester replay packet: {summary.get('c51_status', '')}.",
            f"- C52 isolated Strategy Tester workspace: {summary.get('c52_status', '')}.",
            f"- C53 isolated Strategy Tester terminal root: {summary.get('c53_status', '')}.",
            f"- C55 Strategy Tester account context decision: {summary.get('c55_status', '')}.",
            f"- C42 reviewer intake: {summary.get('c42_status', '')}.",
            f"- Python demo predictions authorized: {str(payload['authorization']['python_demo_predictions_authorized']).lower()}.",
            f"- EA consumption authorized: {str(payload['authorization']['ea_consumption_authorized']).lower()}.",
            "- Broker action authorized: false.",
            "",
            "## Steps",
            "",
            _table(step_rows, ["Step", "Status", "Report"]) if step_rows else "No steps.",
            "",
            "## Commands",
            "",
            command_lines,
            "",
            "## Boundary",
            "",
            f"- MT5 connection attempted: {str(payload['boundary']['mt5_connection_attempted']).lower()}.",
            f"- Data export attempted: {str(payload['boundary']['data_export_attempted']).lower()}.",
            "- Terminal runtime launch attempted: false.",
            "- Terminal shutdown attempted: false.",
            "- Profile or chart file write attempted: false.",
            "- Model training authorized: false.",
            f"- Python demo predictions authorized: {str(payload['boundary']['python_demo_predictions_authorized']).lower()}.",
            f"- EA consumption authorized: {str(payload['boundary']['ea_consumption_authorized']).lower()}.",
            "- Broker action authorized: false.",
            "",
            "## Next",
            "",
            payload["next_allowed_stage"],
            "",
        ]
    )


def _step(name: str, func: Callable[[], Path]) -> dict[str, Any]:
    path = func()
    payload = _read_json(path)
    return {
        "step": name,
        "status": payload.get("status", "MISSING"),
        "report": str(path),
    }


def _summary(root: Path) -> dict[str, dict[str, Any]]:
    reports = root / "outputs" / "reports"
    return {
        "pointer": _read_json(reports / "C02_DATASET_POINTER.json"),
        "c03": _read_json(reports / "C03_TRAINING_READINESS_REPORT.json"),
        "c05": _read_json(reports / "A3_ML_TRAINING_STATUS.json"),
        "c04": _read_json(reports / "A3_ML_SHADOW_BRIDGE_STATUS.json"),
        "c06": _read_json(reports / "A3_ML_EA_HANDOFF_STATUS.json"),
        "c10": _read_json(reports / "A3_ML_DEMO_PREDICTION_ACTIVATION_STATUS.json"),
        "c16": _read_json(reports / "A3_ML_EA_CONSUMER_READINESS_STATUS.json"),
        "c23": _read_json(reports / "A3_ML_DEMO_PYTHON_LAUNCH_CONTROLLER_STATUS.json"),
        "c24": _read_json(reports / "A3_ML_DEMO_PREDICTION_ACTION_PACKET.json"),
        "c33": _read_json(reports / "A3_ML_DEMO_SHADOW_COLLECTION_HEALTH_STATUS.json"),
        "c48": _read_json(reports / "A3_ML_LATEST_DATASET_REPAIR_STATUS.json"),
        "c40": _read_json(reports / "A3_ML_DEMO_READINESS_WORK_ORDER.json"),
        "c41": _read_json(reports / "A3_ML_REVIEWER_DECISION_PACKET_STATUS.json"),
        "c42": _read_json(reports / "A3_ML_REVIEWER_DECISION_INTAKE_STATUS.json"),
        "c44": _read_json(reports / "A3_ML_REVIEWER_DECISION_TEMPLATE_STATUS.json"),
        "c45": _read_json(reports / "A3_ML_REVIEWER_SUBMISSION_BUNDLE_STATUS.json"),
        "c49": _read_json(reports / "A3_ML_REVIEWER_HANDOFF_PACKAGE_STATUS.json"),
        "c46": _read_json(reports / "A3_ML_READINESS_PROGRESS_TRACKER_STATUS.json"),
        "c47": _read_json(reports / "A3_ML_GATE_CLOSURE_PLAN_STATUS.json"),
        "c50": _read_json(reports / "A3_ML_HISTORICAL_BACKFILL_REPLAY_PLAN_STATUS.json"),
        "c51": _read_json(reports / "A3_ML_STRATEGY_TESTER_REPLAY_PACKET_STATUS.json"),
        "c52": _read_json(reports / "A3_ML_ISOLATED_STRATEGY_TESTER_WORKSPACE_STATUS.json"),
        "c53": _read_json(reports / "A3_ML_ISOLATED_STRATEGY_TESTER_TERMINAL_ROOT_STATUS.json"),
        "c55": _read_json(reports / "A3_ML_STRATEGY_TESTER_ACCOUNT_CONTEXT_DECISION_STATUS.json"),
    }


def _summary_head(summary: dict[str, dict[str, Any]]) -> dict[str, Any]:
    return {
        "c03_status": summary.get("c03", {}).get("status", "MISSING"),
        "c05_status": summary.get("c05", {}).get("status", "MISSING"),
        "c04_status": summary.get("c04", {}).get("status", "MISSING"),
        "c06_status": summary.get("c06", {}).get("status", "MISSING"),
        "c10_status": summary.get("c10", {}).get("status", "MISSING"),
        "c16_status": summary.get("c16", {}).get("status", "MISSING"),
        "c23_status": summary.get("c23", {}).get("status", "MISSING"),
        "c24_status": summary.get("c24", {}).get("status", "MISSING"),
        "c33_status": summary.get("c33", {}).get("status", "MISSING"),
        "c48_status": summary.get("c48", {}).get("status", "MISSING"),
        "c40_status": summary.get("c40", {}).get("status", "MISSING"),
        "c41_status": summary.get("c41", {}).get("status", "MISSING"),
        "c42_status": summary.get("c42", {}).get("status", "MISSING"),
        "c44_status": summary.get("c44", {}).get("status", "MISSING"),
        "c45_status": summary.get("c45", {}).get("status", "MISSING"),
        "c49_status": summary.get("c49", {}).get("status", "MISSING"),
        "c46_status": summary.get("c46", {}).get("status", "MISSING"),
        "c47_status": summary.get("c47", {}).get("status", "MISSING"),
        "c50_status": summary.get("c50", {}).get("status", "MISSING"),
        "c51_status": summary.get("c51", {}).get("status", "MISSING"),
        "c52_status": summary.get("c52", {}).get("status", "MISSING"),
        "c53_status": summary.get("c53", {}).get("status", "MISSING"),
        "c55_status": summary.get("c55", {}).get("status", "MISSING"),
    }


def _status(summary: dict[str, dict[str, Any]]) -> str:
    pointer = summary.get("pointer", {})
    if pointer.get("python_demo_predictions_authorized") is True and pointer.get("ea_consumption_authorized") is True:
        return "READY_FOR_DEMO_PYTHON_PREDICTIONS"
    if summary.get("c33", {}).get("status") == "STALE_OR_PARTIAL_COLLECTION":
        return "RESTORE_COLLECTION_HEALTH"
    if summary.get("c42", {}).get("status") == "WAITING_FOR_REVIEWER_DECISION":
        return "WAITING_FOR_REVIEWER_DECISION_AND_DATA"
    if summary.get("c42", {}).get("status") == "APPLIED_REVIEWER_CONFIGS_FAIL_CLOSED":
        return "REVIEWER_CONFIGS_APPLIED_WAITING_FOR_GATES"
    if summary.get("c40", {}).get("status"):
        return str(summary["c40"]["status"])
    return "WAITING_FOR_DATA"


def _next_allowed_stage(status: str) -> str:
    if status == "READY_FOR_DEMO_PYTHON_PREDICTIONS":
        return "Official passive demo Python predictions may run; broker action remains false."
    if status == "RESTORE_COLLECTION_HEALTH":
        return "Republish C26 research-preview handoff and rerun C27/C33/C40/C41/C42/C24."
    if status == "WAITING_FOR_REVIEWER_DECISION_AND_DATA":
        return "Send C41 to the reviewer, keep A1/A2/A3 collecting, then rerun C43 after reviewer decision or new market data."
    if status == "REVIEWER_CONFIGS_APPLIED_WAITING_FOR_GATES":
        return "Rerun C43 with --refresh-live-readonly after config application; C03/C05/C04/C06/C10/C23 must pass before Python demo predictions."
    return "Keep collecting A1/A2/A3 data and rerun C43 after market data advances."


def _commands(root: Path) -> dict[str, str]:
    python = _quote(sys.executable)
    script = _quote(str(root / "scripts" / "c43_run_demo_readiness_cycle.py"))
    root_arg = _quote(str(root))
    return {
        "refresh_cycle": f"{python} {script} --root {root_arg} --refresh-live-readonly",
        "status_cycle_no_refresh": f"{python} {script} --root {root_arg}",
        "apply_reviewer_decision": f"{python} {script} --root {root_arg} --decision-json <reviewer_decision.json> --apply-reviewer-configs",
    }


def _quote(value: str) -> str:
    return f'"{value}"' if " " in value else value


def _write_status(status_json: Path, payload: dict[str, Any]) -> None:
    status_json.parent.mkdir(parents=True, exist_ok=True)
    status_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    status_json.with_suffix(".md").write_text(render_demo_readiness_cycle_md(payload), encoding="utf-8")


def _update_pointer(pointer_path: Path, payload: dict[str, Any]) -> None:
    if not pointer_path.exists():
        return
    pointer = _read_json(pointer_path)
    pointer["c43_demo_readiness_cycle_report"] = payload["outputs"]["status_report_json"]
    pointer["c43_demo_readiness_cycle_status"] = payload["status"]
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
