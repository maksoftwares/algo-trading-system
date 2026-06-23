from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .market_data_export import _table, _utc_now, _write_json_atomic


DEFAULT_REPORT_JSON = Path("outputs") / "reports" / "A3_ML_GATE_CLOSURE_PLAN_STATUS.json"
SCHEMA_VERSION = "a3_ml_gate_closure_plan_status_v1"
STATUS_WAITING = "WAITING_FOR_REVIEWER_AND_MARKET_DATA"
STATUS_READY = "READY_FOR_DEMO_PYTHON_PREDICTIONS"


def generate_gate_closure_plan(root: Path, report_json: Path | None = None) -> Path:
    root = root.resolve()
    reports = root / "outputs" / "reports"
    report_json = (report_json or root / DEFAULT_REPORT_JSON).resolve()
    inputs = _inputs(reports)
    c03 = inputs["c03"]
    gate_actions = _gate_actions(inputs)
    status = STATUS_READY if c03.get("status") == "PASS" else STATUS_WAITING
    payload = {
        "status": status,
        "stage": "C47-GATE-CLOSURE-PLAN",
        "created_at_utc": _utc_now(),
        "schema_version": SCHEMA_VERSION,
        "dataset_version": inputs["pointer"].get("dataset_version", c03.get("dataset_version", "")),
        "readiness_status": {
            "c03": c03.get("status", "MISSING"),
            "c05": inputs["c05"].get("status", "MISSING"),
            "c23": inputs["c23"].get("status", "MISSING"),
            "c33": inputs["c33"].get("status", "MISSING"),
            "c45": inputs["c45"].get("status", "MISSING"),
            "c46": inputs["c46"].get("status", "MISSING"),
        },
        "gate_actions": gate_actions,
        "today_possible": _today_possible(inputs, gate_actions),
        "today_not_forceable": _today_not_forceable(gate_actions),
        "operator_sequence": _operator_sequence(inputs),
        "progress_signal": _progress_signal(inputs),
        "authorization": {
            "training_authorized": False,
            "python_demo_predictions_authorized": False,
            "ea_consumption_authorized": False,
            "broker_action_authorized": False,
        },
        "boundary": {
            "mt5_connection_attempted": False,
            "data_export_attempted": False,
            "config_write_attempted": False,
            "model_training_authorized": False,
            "python_demo_predictions_authorized": False,
            "ea_consumption_authorized": False,
            "broker_action_authorized": False,
        },
        "outputs": {
            "status_report_json": str(report_json),
            "status_report_md": str(report_json.with_suffix(".md")),
        },
        "next_allowed_stage": _next_allowed_stage(status),
    }
    _write_status(report_json, payload)
    _update_pointer(reports / "C02_DATASET_POINTER.json", payload)
    return report_json


def render_gate_closure_plan_md(payload: dict[str, Any]) -> str:
    gate_rows = [
        {
            "Gate": item.get("gate", ""),
            "Observed": item.get("observed", ""),
            "Required": item.get("required", ""),
            "Owner": item.get("primary_owner", ""),
            "Next": item.get("next_action", ""),
        }
        for item in payload.get("gate_actions", [])
    ]
    possible = "\n".join(f"- {item}" for item in payload.get("today_possible", [])) or "- none"
    not_forceable = "\n".join(f"- {item}" for item in payload.get("today_not_forceable", [])) or "- none"
    sequence = "\n".join(f"{index}. {item}" for index, item in enumerate(payload.get("operator_sequence", []), start=1))
    progress_rows = [{"Metric": key, "Value": value} for key, value in payload.get("progress_signal", {}).items()]
    return "\n".join(
        [
            "# A3 ML Gate Closure Plan",
            "",
            f"Overall status: {payload['status']}",
            f"Dataset version: {payload.get('dataset_version', '')}",
            "",
            "## Readiness Status",
            "",
            "\n".join(f"- {key}: {value}" for key, value in payload.get("readiness_status", {}).items()),
            "",
            "## Gate Actions",
            "",
            _table(gate_rows, ["Gate", "Observed", "Required", "Owner", "Next"]) if gate_rows else "No failed gates.",
            "",
            "## Possible Today",
            "",
            possible,
            "",
            "## Not Forceable Today",
            "",
            not_forceable,
            "",
            "## Operator Sequence",
            "",
            sequence or "1. none",
            "",
            "## Progress Signal",
            "",
            _table(progress_rows, ["Metric", "Value"]),
            "",
            "## Boundary",
            "",
            "- MT5 connection attempted: false.",
            "- Data export attempted: false.",
            "- Config write attempted: false.",
            "- Model training authorized: false.",
            "- Python demo predictions authorized: false.",
            "- EA consumption authorized: false.",
            "- Broker action authorized: false.",
            "",
            "## Next",
            "",
            payload["next_allowed_stage"],
            "",
        ]
    )


def _inputs(reports: Path) -> dict[str, dict[str, Any]]:
    return {
        "pointer": _read_json(reports / "C02_DATASET_POINTER.json"),
        "c03": _read_json(reports / "C03_TRAINING_READINESS_REPORT.json"),
        "c05": _read_json(reports / "A3_ML_TRAINING_STATUS.json"),
        "c23": _read_json(reports / "A3_ML_DEMO_PYTHON_LAUNCH_CONTROLLER_STATUS.json"),
        "c33": _read_json(reports / "A3_ML_DEMO_SHADOW_COLLECTION_HEALTH_STATUS.json"),
        "c40": _read_json(reports / "A3_ML_DEMO_READINESS_WORK_ORDER.json"),
        "c45": _read_json(reports / "A3_ML_REVIEWER_SUBMISSION_BUNDLE_STATUS.json"),
        "c46": _read_json(reports / "A3_ML_READINESS_PROGRESS_TRACKER_STATUS.json"),
    }


def _gate_actions(inputs: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    c46_delta = inputs["c46"].get("delta_from_previous", {})
    slippage_rows = inputs["c40"].get("per_account_slippage_deficits", [])
    actions = []
    for gate in inputs["c03"].get("checks", []):
        if gate.get("passed"):
            continue
        gate_name = gate.get("gate", "")
        actions.append(
            {
                "gate": gate_name,
                "observed": str(gate.get("observed", "")),
                "required": str(gate.get("required", "")),
                **_gate_action_detail(gate_name, c46_delta, slippage_rows),
            }
        )
    return actions


def _gate_action_detail(gate: str, delta: dict[str, Any], slippage_rows: list[dict[str, Any]]) -> dict[str, str]:
    if gate == "dataset_status":
        return {
            "primary_owner": "reviewer_then_pipeline",
            "can_move_today": "maybe",
            "next_action": "Get label-promotion decision, apply through C42/C43, then rerun C03/C05.",
        }
    if gate == "market_setup_groups":
        return {
            "primary_owner": "reviewer_or_market_data",
            "can_move_today": "maybe",
            "next_action": f"Need 77 more groups; latest dataset added {delta.get('market_setup_groups', 0)}. Reviewer contract expansion can help if approved.",
        }
    if gate == "active_weeks":
        return {
            "primary_owner": "market_time_or_external_history",
            "can_move_today": "no_without_external_history",
            "next_action": "Needs about 4.63 more active weeks unless older compatible decisions are provided and reviewed.",
        }
    if gate == "at_least_two_regimes":
        return {
            "primary_owner": "market_data",
            "can_move_today": "no_without_new_regime_data",
            "next_action": "Continue collecting until C01 sees at least two non-UNKNOWN regimes, or import reviewed compatible history.",
        }
    if gate == "feature_budget":
        return {
            "primary_owner": "reviewer_then_pipeline",
            "can_move_today": "maybe",
            "next_action": "Feature budget is 0 until reviewed label promotion creates trainable groups and C01/C03 are rebuilt.",
        }
    if gate == "slippage_readiness":
        weak = [
            f"{row.get('account_label')}: entry {row.get('entry_fills_deficit', 0)}, SL {row.get('sl_exits_deficit', 0)}, TP {row.get('tp_exits_deficit', 0)}, request {row.get('request_price_resolved_deficit', 0)}"
            for row in slippage_rows
            if row.get("slippage_status") != "ADEQUATE"
        ]
        return {
            "primary_owner": "live_fill_collection",
            "can_move_today": "only_if_A2_A3_generate_fills",
            "next_action": "Close A2/A3 deficits: " + "; ".join(weak),
        }
    return {
        "primary_owner": "pipeline",
        "can_move_today": "unknown",
        "next_action": "Review the C03 gate and rerun C43 after upstream state changes.",
    }


def _today_possible(inputs: dict[str, dict[str, Any]], gate_actions: list[dict[str, Any]]) -> list[str]:
    items = []
    if inputs["c45"].get("status") == "READY_TO_SEND_TO_REVIEWER":
        items.append("Send C45 reviewer submission bundle and request the filled C44 decision template.")
    if inputs["c33"].get("collection_health", {}).get("all_accounts_collecting", False):
        items.append("Keep A1/A2/A3 terminals running; collection health is currently green.")
    if any(item.get("primary_owner") == "reviewer_then_pipeline" for item in gate_actions):
        items.append("If reviewer returns a final template today, validate with C42 and apply with C43 fail-closed.")
    items.append("Run C43/C46 after new market data or reviewer response to measure actual gate movement.")
    return items


def _today_not_forceable(gate_actions: list[dict[str, Any]]) -> list[str]:
    items = []
    if any(item.get("gate") == "active_weeks" for item in gate_actions):
        items.append("The 8-week active-span gate cannot be forced by repeated refreshes; it needs time or reviewed older compatible decisions.")
    if any(item.get("gate") == "at_least_two_regimes" for item in gate_actions):
        items.append("The second-regime gate cannot be invented; it needs market data that C01 classifies as another non-UNKNOWN regime.")
    if any(item.get("gate") == "slippage_readiness" for item in gate_actions):
        items.append("A2/A3 slippage readiness cannot close without more account-specific fills/request-price evidence.")
    return items


def _operator_sequence(inputs: dict[str, dict[str, Any]]) -> list[str]:
    return [
        "Send C45 bundle to reviewer.",
        "Keep A1/A2/A3 terminals and broker-shadow taps running.",
        "When reviewer fills C44, run C42 validation.",
        "If C42 is valid and decision is final, run C43 with --decision-json and --apply-reviewer-configs.",
        "Run C43 with --refresh-live-readonly after market data advances.",
        "Use C46 deltas to confirm whether groups, labels, fills, and active span are actually improving.",
    ]


def _progress_signal(inputs: dict[str, dict[str, Any]]) -> dict[str, Any]:
    delta = inputs["c46"].get("delta_from_previous", {})
    latest = inputs["c46"].get("latest_dataset", {})
    return {
        "latest_dataset": latest.get("dataset_version", ""),
        "signal_instances_delta": delta.get("signal_instances", 0),
        "market_setup_groups_delta": delta.get("market_setup_groups", 0),
        "labels_delta": delta.get("labels", 0),
        "mature_labels_delta": delta.get("mature_labels", 0),
        "fill_rows_delta": delta.get("fill_rows", 0),
        "all_accounts_collecting": inputs["c33"].get("collection_health", {}).get("all_accounts_collecting", False),
    }


def _next_allowed_stage(status: str) -> str:
    if status == STATUS_READY:
        return "Continue to C05/C04/C06/C10/C23 passive demo prediction gates; broker action remains false."
    return "Execute the operator sequence: send C45, keep collection running, apply reviewer decision only through C42/C43, then rerun C43/C46."


def _write_status(status_json: Path, payload: dict[str, Any]) -> None:
    status_json.parent.mkdir(parents=True, exist_ok=True)
    status_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    status_json.with_suffix(".md").write_text(render_gate_closure_plan_md(payload), encoding="utf-8")


def _update_pointer(pointer_path: Path, payload: dict[str, Any]) -> None:
    if not pointer_path.exists():
        return
    pointer = _read_json(pointer_path)
    pointer["c47_gate_closure_plan_report"] = payload["outputs"]["status_report_json"]
    pointer["c47_gate_closure_plan_status"] = payload["status"]
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
