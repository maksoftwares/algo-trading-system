from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .market_data_export import _table, _utc_now, _write_json_atomic


DEFAULT_REPORT_JSON = Path("outputs") / "reports" / "A3_ML_DEMO_READINESS_WORK_ORDER.json"
SCHEMA_VERSION = "a3_ml_demo_readiness_work_order_v1"


def generate_demo_readiness_work_order(root: Path, report_json: Path | None = None) -> Path:
    root = root.resolve()
    reports = root / "outputs" / "reports"
    report_json = (report_json or root / DEFAULT_REPORT_JSON).resolve()
    inputs = _inputs(reports)
    authorization = _authorization(inputs)
    status = _status(inputs, authorization)
    payload = {
        "status": status,
        "stage": "C40-DEMO-READINESS-WORK-ORDER",
        "created_at_utc": _utc_now(),
        "schema_version": SCHEMA_VERSION,
        "dataset_version": inputs["pointer"].get("dataset_version", ""),
        "go_no_go": {
            "can_start_official_python_demo_predictions": bool(authorization["python_demo_predictions_authorized"]),
            "can_start_ea_consumption": bool(authorization["ea_consumption_authorized"]),
            "broker_action_authorized": False,
            "reason": _go_no_go_reason(inputs, authorization),
        },
        "summary": _summary(inputs),
        "blocking_gates": _blocking_gates(inputs),
        "per_account_slippage_deficits": _slippage_deficits(inputs),
        "critical_path": _critical_path(inputs, status),
        "operator_commands": _operator_commands(root),
        "authorization": authorization,
        "boundary": {
            "mt5_connection_attempted": False,
            "data_export_attempted": False,
            "terminal_runtime_change_authorized": False,
            "profile_or_chart_file_write_attempted": False,
            "model_training_authorized": False,
            "python_demo_predictions_authorized": bool(authorization["python_demo_predictions_authorized"]),
            "ea_consumption_authorized": bool(authorization["ea_consumption_authorized"]),
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


def render_demo_readiness_work_order_md(payload: dict[str, Any]) -> str:
    summary = payload.get("summary", {})
    gate_rows = [
        {
            "Gate": item.get("gate", ""),
            "Observed": item.get("observed", ""),
            "Required": item.get("required", ""),
            "Gap": item.get("gap_text", ""),
        }
        for item in payload.get("blocking_gates", [])
    ]
    slippage_rows = [
        {
            "Account": item.get("account_label", ""),
            "Status": item.get("slippage_status", ""),
            "Entry Deficit": item.get("entry_fills_deficit", 0),
            "SL Deficit": item.get("sl_exits_deficit", 0),
            "TP Deficit": item.get("tp_exits_deficit", 0),
            "Request Deficit": item.get("request_price_resolved_deficit", 0),
        }
        for item in payload.get("per_account_slippage_deficits", [])
    ]
    path_lines = "\n".join(f"- {item}" for item in payload.get("critical_path", [])) or "- none"
    command_rows = [
        {"Command": key, "Value": value}
        for key, value in payload.get("operator_commands", {}).items()
    ]
    return "\n".join(
        [
            "# A3 ML Demo Readiness Work Order",
            "",
            f"Overall status: {payload['status']}",
            f"Dataset version: {payload.get('dataset_version', '')}",
            "",
            "## Go/No-Go",
            "",
            f"- Official Python demo predictions: {str(payload['go_no_go']['can_start_official_python_demo_predictions']).lower()}",
            f"- EA consumption: {str(payload['go_no_go']['can_start_ea_consumption']).lower()}",
            "- Broker action: false",
            f"- Reason: {payload['go_no_go']['reason']}",
            "",
            "## Summary",
            "",
            f"- C03 readiness: {summary.get('c03_status', '')}",
            f"- C05 training: {summary.get('c05_status', '')}",
            f"- C23 launch controller: {summary.get('c23_status', '')}",
            f"- C33 collection health: {summary.get('c33_status', '')}",
            f"- C39 historical coverage: {summary.get('c39_status', '')}",
            f"- All accounts collecting: {str(summary.get('all_accounts_collecting', False)).lower()}",
            "",
            "## Blocking Gates",
            "",
            _table(gate_rows, ["Gate", "Observed", "Required", "Gap"]) if gate_rows else "No blocking gates.",
            "",
            "## Slippage Deficits",
            "",
            _table(slippage_rows, ["Account", "Status", "Entry Deficit", "SL Deficit", "TP Deficit", "Request Deficit"]) if slippage_rows else "No slippage deficits.",
            "",
            "## Critical Path",
            "",
            path_lines,
            "",
            "## Commands",
            "",
            _table(command_rows, ["Command", "Value"]),
            "",
            "## Boundary",
            "",
            "- MT5 connection attempted: false.",
            "- Data export attempted: false.",
            "- Terminal runtime change authorized: false.",
            "- Model training authorized: false.",
            f"- Python demo predictions authorized: {str(payload['authorization']['python_demo_predictions_authorized']).lower()}.",
            f"- EA consumption authorized: {str(payload['authorization']['ea_consumption_authorized']).lower()}.",
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
        "c11": _read_json(reports / "A3_ML_READINESS_GAP_REPORT.json"),
        "c23": _read_json(reports / "A3_ML_DEMO_PYTHON_LAUNCH_CONTROLLER_STATUS.json"),
        "c33": _read_json(reports / "A3_ML_DEMO_SHADOW_COLLECTION_HEALTH_STATUS.json"),
        "c38": _read_json(reports / "A3_ML_LABEL_TRAINABILITY_BLOCKER_STATUS.json"),
        "c39": _read_json(reports / "A3_ML_HISTORICAL_DECISION_COVERAGE_STATUS.json"),
    }


def _authorization(inputs: dict[str, dict[str, Any]]) -> dict[str, bool]:
    c23_auth = inputs["c23"].get("authorization", {})
    pointer = inputs["pointer"]
    python_ready = bool(pointer.get("python_demo_predictions_authorized", False)) and bool(c23_auth.get("python_demo_predictions_authorized", False))
    ea_ready = bool(pointer.get("ea_consumption_authorized", False)) and bool(c23_auth.get("ea_consumption_authorized", False))
    return {
        "python_demo_predictions_authorized": python_ready,
        "ea_consumption_authorized": ea_ready,
        "broker_action_authorized": False,
    }


def _status(inputs: dict[str, dict[str, Any]], authorization: dict[str, bool]) -> str:
    if authorization["python_demo_predictions_authorized"] and authorization["ea_consumption_authorized"]:
        return "READY_FOR_DEMO_PYTHON_PREDICTIONS"
    c33_health = inputs["c33"].get("collection_health", {})
    if not c33_health.get("all_accounts_collecting", False):
        return "RESTORE_COLLECTION_HEALTH"
    if inputs["c39"].get("status") == "OLDER_COMPATIBLE_DECISIONS_FOUND":
        return "REVIEW_OLDER_COMPATIBLE_BACKFILL"
    if inputs["c38"].get("status") == "LABEL_PROMOTION_REVIEW_REQUIRED_SLIPPAGE_BLOCKED":
        return "WAITING_FOR_DATA_AND_REVIEW"
    return "WAITING_FOR_DATA"


def _summary(inputs: dict[str, dict[str, Any]]) -> dict[str, Any]:
    c33_health = inputs["c33"].get("collection_health", {})
    c11_decisions = inputs["c11"].get("decision_coverage", {})
    return {
        "c03_status": inputs["c03"].get("status", "MISSING"),
        "c05_status": inputs["c05"].get("status", "MISSING"),
        "c23_status": inputs["c23"].get("status", "MISSING"),
        "c33_status": inputs["c33"].get("status", "MISSING"),
        "c38_status": inputs["c38"].get("status", "MISSING"),
        "c39_status": inputs["c39"].get("status", "MISSING"),
        "all_accounts_collecting": bool(c33_health.get("all_accounts_collecting", False)),
        "handoff_dataset_current_all_accounts": bool(c33_health.get("handoff_dataset_current_all_accounts", False)),
        "observer_prediction_fresh_all_accounts": bool(c33_health.get("observer_prediction_fresh_all_accounts", False)),
        "broker_shadow_tap_present_all_accounts": bool(c33_health.get("broker_shadow_tap_present_all_accounts", False)),
        "active_span_weeks": c11_decisions.get("active_span_weeks", 0),
        "estimated_active_weeks_pass_date_utc": inputs["c11"].get("backfill_assessment", {}).get("estimated_active_weeks_pass_date_utc", ""),
        "older_compatible_current_scope_rows": inputs["c39"].get("summary", {}).get("older_compatible_current_scope_would_signal_rows", 0),
    }


def _blocking_gates(inputs: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "gate": item.get("gate", ""),
            "observed": item.get("observed", ""),
            "required": item.get("required", ""),
            "gap_text": item.get("gap_text", ""),
        }
        for item in inputs["c11"].get("gate_gaps", inputs["c03"].get("checks", []))
        if not item.get("passed", False)
    ]


def _slippage_deficits(inputs: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for account in inputs["c11"].get("slippage_gap", {}).get("accounts", []):
        deficits = account.get("deficits_if_per_account", {})
        rows.append(
            {
                "account_label": account.get("account_label", ""),
                "slippage_status": account.get("slippage_status", ""),
                "entry_fills": account.get("entry_fills", 0),
                "sl_exits": account.get("sl_exits", 0),
                "tp_exits": account.get("tp_exits", 0),
                "request_price_resolved": account.get("request_price_resolved", 0),
                "entry_fills_deficit": deficits.get("entry_fills", 0),
                "sl_exits_deficit": deficits.get("sl_exits", 0),
                "tp_exits_deficit": deficits.get("tp_exits", 0),
                "request_price_resolved_deficit": deficits.get("request_price_resolved", 0),
            }
        )
    return rows


def _critical_path(inputs: dict[str, dict[str, Any]], status: str) -> list[str]:
    items = []
    c33_health = inputs["c33"].get("collection_health", {})
    if not c33_health.get("all_accounts_collecting", False):
        items.append("Restore all-account collection health before waiting on model gates.")
    if inputs["c39"].get("status") == "OLDER_COMPATIBLE_DECISIONS_FOUND":
        items.append("Review older compatible current-scope decisions before importing any backfill.")
    if inputs["c39"].get("status") == "NO_OLDER_COMPATIBLE_DECISIONS_FOUND":
        items.append("No older compatible MT5 Files decisions were found; active-weeks gap must close via live collection or external reviewed history.")
    for gate in _blocking_gates(inputs):
        items.append(f"{gate['gate']}: observed {gate['observed']}, required {gate['required']}, gap {gate['gap_text']}.")
    for row in _slippage_deficits(inputs):
        if row["slippage_status"] != "ADEQUATE":
            items.append(
                f"{row['account_label']} slippage deficit: entry {row['entry_fills_deficit']}, "
                f"SL {row['sl_exits_deficit']}, TP {row['tp_exits_deficit']}, request-price {row['request_price_resolved_deficit']}."
            )
    if status.startswith("WAITING"):
        items.append("Keep A1/A2/A3 collecting and rerun live read-only refresh after market data advances.")
    return items


def _operator_commands(root: Path) -> dict[str, str]:
    root_arg = _quote(str(root))
    return {
        "refresh_live_readonly": f"python scripts/c08_live_refresh_pipeline.py --root {root_arg} --execute-live-readonly",
        "demo_launch_controller_after_refresh": f"python scripts/c23_run_demo_python_launch_controller.py --root {root_arg} --refresh-live-readonly",
        "action_packet": f"python scripts/c24_generate_demo_prediction_action_packet.py --root {root_arg}",
        "collection_health": f"python scripts/c33_check_demo_shadow_collection_health.py --root {root_arg}",
        "historical_coverage_probe": f"python scripts/c39_probe_historical_decision_coverage.py --root {root_arg}",
    }


def _go_no_go_reason(inputs: dict[str, dict[str, Any]], authorization: dict[str, bool]) -> str:
    if authorization["python_demo_predictions_authorized"] and authorization["ea_consumption_authorized"]:
        return "C03/C05/C04/C06/C10/C23 are ready for passive demo Python predictions."
    c03_status = inputs["c03"].get("status", "MISSING")
    c05_status = inputs["c05"].get("status", "MISSING")
    c23_status = inputs["c23"].get("status", "MISSING")
    return f"Not ready: C03={c03_status}, C05={c05_status}, C23={c23_status}."


def _next_allowed_stage(status: str) -> str:
    if status == "READY_FOR_DEMO_PYTHON_PREDICTIONS":
        return "EA may consume Python predictions in passive demo mode only; broker action remains false."
    if status == "RESTORE_COLLECTION_HEALTH":
        return "Fix stale/missing observer or broker-shadow runtime evidence, then rerun C33/C23."
    if status == "REVIEW_OLDER_COMPATIBLE_BACKFILL":
        return "Review and import only approved older compatible current-scope rows, then rerun C08/C03."
    if status == "WAITING_FOR_DATA_AND_REVIEW":
        return "Keep collecting data, obtain reviewer decision for label promotion/contract expansion, then rerun C08/C23."
    return "Keep collecting data on A1/A2/A3, then rerun C08/C23 after market data advances."


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _quote(value: str) -> str:
    return f'"{value}"' if " " in value else value


def _write_status(status_json: Path, payload: dict[str, Any]) -> None:
    status_json.parent.mkdir(parents=True, exist_ok=True)
    status_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    status_json.with_suffix(".md").write_text(render_demo_readiness_work_order_md(payload), encoding="utf-8")


def _update_pointer(pointer_path: Path, payload: dict[str, Any]) -> None:
    if not pointer_path.exists():
        return
    pointer = _read_json(pointer_path)
    pointer["c40_demo_readiness_work_order_report"] = payload["outputs"]["status_report_json"]
    pointer["c40_demo_readiness_work_order_status"] = payload["status"]
    pointer["python_demo_predictions_authorized"] = bool(payload["authorization"]["python_demo_predictions_authorized"])
    pointer["ea_consumption_authorized"] = bool(payload["authorization"]["ea_consumption_authorized"])
    pointer["broker_action_authorized"] = False
    _write_json_atomic(pointer_path, pointer)
