from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .market_data_export import _table, _utc_now, _write_json_atomic
from .pipeline_orchestrator import run_offline_prediction_readiness_pipeline
from .readiness_progress_tracker import generate_readiness_progress_tracker


DEFAULT_STATUS_JSON = Path("outputs") / "reports" / "A3_ML_LATEST_DATASET_REPAIR_STATUS.json"
SCHEMA_VERSION = "a3_ml_latest_dataset_repair_status_v1"
STATUS_COMPLETE = "DATASET_COMPLETE_NO_REPAIR_NEEDED"
STATUS_REPAIRED = "REPAIRED_BY_OFFLINE_PIPELINE"
STATUS_REPAIR_REQUIRED = "REPAIR_REQUIRED_NOT_RUN"
STATUS_REPAIR_FAILED = "REPAIR_FAILED_INCOMPLETE"
INCOMPLETE_STATUS = "DATASET_ARTIFACTS_INCOMPLETE"


def repair_latest_dataset_if_needed(root: Path, report_json: Path | None = None, *, auto_repair: bool = True) -> Path:
    root = root.resolve()
    report_json = (report_json or root / DEFAULT_STATUS_JSON).resolve()
    pointer_before = _read_json(root / "outputs" / "reports" / "C02_DATASET_POINTER.json")
    before_path = generate_readiness_progress_tracker(root)
    before = _read_json(before_path)
    repair_attempted = False
    pipeline_path: Path | None = None
    pipeline = {}
    after_path = before_path
    after = before

    if before.get("status") == INCOMPLETE_STATUS and auto_repair:
        repair_attempted = True
        pipeline_path = run_offline_prediction_readiness_pipeline(root, publish=False)
        pipeline = _read_json(pipeline_path)
        after_path = generate_readiness_progress_tracker(root)
        after = _read_json(after_path)

    pointer_after = _read_json(root / "outputs" / "reports" / "C02_DATASET_POINTER.json")
    status = _status(before, after, repair_attempted=repair_attempted, auto_repair=auto_repair)
    payload = {
        "status": status,
        "stage": "C48-LATEST-DATASET-REPAIR",
        "created_at_utc": _utc_now(),
        "schema_version": SCHEMA_VERSION,
        "dataset_version_before": pointer_before.get("dataset_version", ""),
        "dataset_version_after": pointer_after.get("dataset_version", pointer_before.get("dataset_version", "")),
        "auto_repair_requested": bool(auto_repair),
        "repair_attempted": repair_attempted,
        "before": _tracker_summary(before, before_path),
        "after": _tracker_summary(after, after_path),
        "pipeline": {
            "status": pipeline.get("status", ""),
            "report": str(pipeline_path) if pipeline_path is not None else "",
            "publish_requested": bool(pipeline.get("publish_requested", False)),
        },
        "authorization": {
            "training_authorized": bool(pointer_after.get("training_authorized", False)),
            "python_demo_predictions_authorized": bool(pointer_after.get("python_demo_predictions_authorized", False)),
            "ea_consumption_authorized": bool(pointer_after.get("ea_consumption_authorized", False)),
            "broker_action_authorized": False,
        },
        "boundary": {
            "mt5_connection_attempted": False,
            "data_export_attempted": False,
            "terminal_runtime_change_authorized": False,
            "ea_file_drop_authorized": False,
            "offline_pipeline_attempted": repair_attempted,
            "model_training_delegated_to_c05_gate": repair_attempted,
            "broker_action_authorized": False,
        },
        "outputs": {
            "status_report_json": str(report_json),
            "status_report_md": str(report_json.with_suffix(".md")),
        },
        "next_allowed_stage": _next_allowed_stage(status),
    }
    _write_status(report_json, payload)
    _update_pointer(root / "outputs" / "reports" / "C02_DATASET_POINTER.json", payload)
    return report_json


def render_latest_dataset_repair_md(payload: dict[str, Any]) -> str:
    rows = [
        {
            "Phase": "before",
            "C46 status": payload.get("before", {}).get("status", ""),
            "Completeness": str(payload.get("before", {}).get("complete", False)).lower(),
            "Warnings": _short_list(payload.get("before", {}).get("warnings", [])),
        },
        {
            "Phase": "after",
            "C46 status": payload.get("after", {}).get("status", ""),
            "Completeness": str(payload.get("after", {}).get("complete", False)).lower(),
            "Warnings": _short_list(payload.get("after", {}).get("warnings", [])),
        },
    ]
    return "\n".join(
        [
            "# A3 ML Latest Dataset Repair Status",
            "",
            f"Overall status: {payload['status']}",
            f"Dataset before: {payload.get('dataset_version_before', '')}",
            f"Dataset after: {payload.get('dataset_version_after', '')}",
            "",
            "## Summary",
            "",
            f"- Auto repair requested: {str(payload.get('auto_repair_requested', False)).lower()}.",
            f"- Repair attempted: {str(payload.get('repair_attempted', False)).lower()}.",
            f"- Pipeline status: {payload.get('pipeline', {}).get('status', '') or 'not run'}.",
            "- Broker action authorized: false.",
            "",
            "## Tracker",
            "",
            _table(rows, ["Phase", "C46 status", "Completeness", "Warnings"]),
            "",
            "## Boundary",
            "",
            "- MT5 connection attempted: false.",
            "- Data export attempted: false.",
            "- Terminal runtime change authorized: false.",
            "- EA file drop authorized: false.",
            f"- Offline pipeline attempted: {str(payload['boundary']['offline_pipeline_attempted']).lower()}.",
            f"- Model training delegated to C05 gate: {str(payload['boundary']['model_training_delegated_to_c05_gate']).lower()}.",
            "- Broker action authorized: false.",
            "",
            "## Next",
            "",
            payload["next_allowed_stage"],
            "",
        ]
    )


def _status(before: dict[str, Any], after: dict[str, Any], *, repair_attempted: bool, auto_repair: bool) -> str:
    if before.get("status") != INCOMPLETE_STATUS:
        return STATUS_COMPLETE
    if not auto_repair:
        return STATUS_REPAIR_REQUIRED
    if repair_attempted and after.get("status") != INCOMPLETE_STATUS:
        return STATUS_REPAIRED
    return STATUS_REPAIR_FAILED


def _tracker_summary(payload: dict[str, Any], path: Path) -> dict[str, Any]:
    completeness = payload.get("latest_dataset_completeness", {})
    warnings = list(payload.get("completeness_warnings", []))
    return {
        "status": payload.get("status", "MISSING"),
        "report": str(path),
        "dataset_version": payload.get("dataset_version", ""),
        "complete": bool(completeness.get("complete", False)),
        "missing_artifacts": list(completeness.get("missing_artifacts", [])),
        "warnings": warnings,
    }


def _next_allowed_stage(status: str) -> str:
    if status in {STATUS_COMPLETE, STATUS_REPAIRED}:
        return "Continue C43/C46/C47 readiness checks; broker action remains false."
    if status == STATUS_REPAIR_REQUIRED:
        return "Run C48 with auto repair or run C07 offline pipeline before trusting the latest dataset."
    return "Latest dataset is still incomplete after repair; inspect C07 and C46 reports before continuing."


def _short_list(values: list[str], limit: int = 2) -> str:
    if not values:
        return "-"
    if len(values) <= limit:
        return "; ".join(values)
    return "; ".join(values[:limit]) + f"; +{len(values) - limit} more"


def _write_status(status_json: Path, payload: dict[str, Any]) -> None:
    status_json.parent.mkdir(parents=True, exist_ok=True)
    status_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    status_json.with_suffix(".md").write_text(render_latest_dataset_repair_md(payload), encoding="utf-8")


def _update_pointer(pointer_path: Path, payload: dict[str, Any]) -> None:
    if not pointer_path.exists():
        return
    pointer = _read_json(pointer_path)
    pointer["c48_latest_dataset_repair_report"] = payload["outputs"]["status_report_json"]
    pointer["c48_latest_dataset_repair_status"] = payload["status"]
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
