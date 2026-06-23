from __future__ import annotations

import importlib.util
import json
import sys
import traceback
from pathlib import Path
from typing import Any, Callable

from .diagnostic_labels import generate_diagnostic_labels
from .ea_handoff import generate_ea_handoff_report
from .grouping_verdict import generate_c02_final_verdict, generate_c02_grouping_audit
from .market_data_export import _table, _utc_now, _write_json_atomic
from .model_training import train_or_refuse_model
from .readiness_gate import generate_c03_training_readiness_report
from .shadow_bridge import generate_shadow_bridge_outputs
from .source_normalization import normalize_c02_snapshot


DEFAULT_REPORT_JSON = Path("outputs") / "reports" / "A3_ML_PIPELINE_RUN_STATUS.json"


def run_offline_prediction_readiness_pipeline(root: Path, report_json: Path | None = None, *, publish: bool = False) -> Path:
    root = root.resolve()
    report_json = (report_json or root / DEFAULT_REPORT_JSON).resolve()
    pointer_path = root / "outputs" / "reports" / "C02_DATASET_POINTER.json"
    pointer_before = _read_json(pointer_path)
    steps = _offline_steps(root, publish=publish)
    records: list[dict[str, Any]] = []
    failed = False
    for step_name, runner in steps:
        if failed:
            records.append({"step": step_name, "status": "SKIPPED", "output": "", "detail": "previous step failed"})
            continue
        try:
            output = runner()
            records.append({"step": step_name, "status": "PASS", "output": str(output), "detail": ""})
        except Exception as exc:  # pragma: no cover - retained for operator diagnostics
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
    summary = _collect_current_status(root)
    payload = {
        "status": _overall_status(records, summary),
        "stage": "C07-PIPELINE-ORCHESTRATOR",
        "created_at_utc": _utc_now(),
        "schema_version": "a3_ml_pipeline_run_status_v1",
        "dataset_version": summary.get("dataset_version") or pointer_before.get("dataset_version", ""),
        "publish_requested": bool(publish),
        "steps": records,
        "summary": summary,
        "next_blocker": _next_blocker(summary),
        "boundary": {
            "mt5_connection_attempted": False,
            "terminal_runtime_change_authorized": False,
            "ea_file_drop_authorized": bool(summary.get("c06", {}).get("authorization", {}).get("mt5_file_publish_attempted", False)),
            "broker_action_authorized": False,
        },
        "next_allowed_stage": _next_allowed_stage(summary),
    }
    report_json.parent.mkdir(parents=True, exist_ok=True)
    report_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    report_json.with_suffix(".md").write_text(render_pipeline_run_status_md(payload), encoding="utf-8")
    pointer = _read_json(pointer_path)
    if pointer:
        pointer["c07_pipeline_run_status_report"] = str(report_json)
        pointer["c07_pipeline_run_status"] = payload["status"]
        pointer["python_demo_predictions_authorized"] = bool(summary.get("c04", {}).get("authorization", {}).get("python_demo_predictions_authorized", False))
        pointer["ea_consumption_authorized"] = bool(summary.get("c06", {}).get("authorization", {}).get("ea_consumption_authorized", False))
        pointer["broker_action_authorized"] = False
        _write_json_atomic(pointer_path, pointer)
    return report_json


def render_pipeline_run_status_md(payload: dict[str, Any]) -> str:
    steps = [
        {
            "Step": item["step"],
            "Status": item["status"],
            "Output": item.get("output", ""),
        }
        for item in payload.get("steps", [])
    ]
    summary = payload.get("summary", {})
    rows = [
        {"Stage": "C01 data audit", "Status": summary.get("c01", {}).get("status", "MISSING")},
        {"Stage": "C03 readiness", "Status": summary.get("c03", {}).get("status", "MISSING")},
        {"Stage": "C05 training", "Status": summary.get("c05", {}).get("status", "MISSING")},
        {"Stage": "C04 shadow bridge", "Status": summary.get("c04", {}).get("status", "MISSING")},
        {"Stage": "C06 EA handoff", "Status": summary.get("c06", {}).get("status", "MISSING")},
    ]
    failed_gates = _failed_c03_gates(summary)
    failed_lines = "\n".join(f"- {item}" for item in failed_gates) if failed_gates else "- none"
    return "\n".join(
        [
            "# A3 ML Pipeline Run Status",
            "",
            f"Overall status: {payload['status']}",
            f"Dataset version: {payload.get('dataset_version', '')}",
            f"Publish requested: {str(payload.get('publish_requested', False)).lower()}",
            "",
            "## Stage Summary",
            "",
            _table(rows, ["Stage", "Status"]),
            "",
            "## Pipeline Steps",
            "",
            _table(steps, ["Step", "Status", "Output"]) if steps else "No steps ran.",
            "",
            "## Current Blocker",
            "",
            payload.get("next_blocker", ""),
            "",
            "## Failed C03 Gates",
            "",
            failed_lines,
            "",
            "## Boundary",
            "",
            "- MT5 connection attempted: false.",
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


def _offline_steps(root: Path, *, publish: bool) -> list[tuple[str, Callable[[], Path]]]:
    return [
        ("C02-04 normalize snapshots", lambda: normalize_c02_snapshot(root)),
        ("C02-05 grouping audit", lambda: generate_c02_grouping_audit(root)),
        ("C02-05 final verdict", lambda: generate_c02_final_verdict(root)),
        ("C02-06 diagnostic labels", lambda: generate_diagnostic_labels(root)),
        ("C01 feature/data audit", lambda: _run_c01(root)),
        ("C03 readiness", lambda: generate_c03_training_readiness_report(root)),
        ("C05 train or refuse", lambda: train_or_refuse_model(root)),
        ("C04 shadow bridge", lambda: generate_shadow_bridge_outputs(root)),
        ("C06 EA handoff", lambda: generate_ea_handoff_report(root, publish=publish)),
    ]


def _run_c01(root: Path) -> Path:
    pointer = _read_json(root / "outputs" / "reports" / "C02_DATASET_POINTER.json")
    c01 = _load_c01_module(root)
    output = c01.generate_a3_ml_c01_pipeline(
        root,
        decisions_csv=Path(pointer["c02_labeled_decisions_csv"]),
        trades_csv=Path(pointer["c02_trades_csv"]),
        bars_dir=Path(pointer["c02_bars_dir"]),
        data_audit_json=root / "outputs" / "reports" / "C02_C01_DATA_AUDIT.json",
    )
    return output.data_audit_json


def _collect_current_status(root: Path) -> dict[str, Any]:
    reports = root / "outputs" / "reports"
    pointer = _read_json(reports / "C02_DATASET_POINTER.json")
    return {
        "dataset_version": pointer.get("dataset_version", ""),
        "c01": _read_json(reports / "C02_C01_DATA_AUDIT.json"),
        "c03": _read_json(reports / "C03_TRAINING_READINESS_REPORT.json"),
        "c05": _read_json(reports / "A3_ML_TRAINING_STATUS.json"),
        "c04": _read_json(reports / "A3_ML_SHADOW_BRIDGE_STATUS.json"),
        "c06": _read_json(reports / "A3_ML_EA_HANDOFF_STATUS.json"),
    }


def _overall_status(records: list[dict[str, Any]], summary: dict[str, Any]) -> str:
    if any(record["status"] == "FAIL_CLOSED" for record in records):
        return "FAIL_CLOSED"
    c06_status = summary.get("c06", {}).get("status")
    if c06_status in {"READY_DRY_RUN", "PUBLISHED_TO_MT5_FILES"}:
        return c06_status
    return "NOT_READY"


def _next_blocker(summary: dict[str, Any]) -> str:
    c03 = summary.get("c03", {})
    if c03.get("status") != "PASS":
        failures = _failed_c03_gates(summary)
        return "C03 readiness is not PASS: " + ("; ".join(failures) if failures else c03.get("status", "MISSING"))
    c05 = summary.get("c05", {})
    if c05.get("status") != "TRAINED_SHADOW_ONLY":
        return f"C05 training is {c05.get('status', 'MISSING')}, required TRAINED_SHADOW_ONLY"
    c04 = summary.get("c04", {})
    if c04.get("status") != "READY_SHADOW_ONLY":
        return f"C04 shadow bridge is {c04.get('status', 'MISSING')}, required READY_SHADOW_ONLY"
    c06 = summary.get("c06", {})
    if c06.get("status") not in {"READY_DRY_RUN", "PUBLISHED_TO_MT5_FILES"}:
        return f"C06 EA handoff is {c06.get('status', 'MISSING')}, required READY_DRY_RUN or PUBLISHED_TO_MT5_FILES"
    return "No blocker detected."


def _next_allowed_stage(summary: dict[str, Any]) -> str:
    c06_status = summary.get("c06", {}).get("status")
    if c06_status == "PUBLISHED_TO_MT5_FILES":
        return "EA may read the generated handoff file in shadow mode only; broker action remains false."
    if c06_status == "READY_DRY_RUN":
        return "Run C06 with --publish only after confirming the target EA is configured for passive shadow consumption."
    return "Collect more live data on A1/A2/A3, rerun C02 live export when market data advances, then rerun C07."


def _failed_c03_gates(summary: dict[str, Any]) -> list[str]:
    output = []
    for check in summary.get("c03", {}).get("checks", []):
        if not check.get("passed"):
            output.append(f"{check.get('gate')} observed {check.get('observed')} required {check.get('required')}")
    return output


def _load_c01_module(root: Path):
    path = root / "scripts" / "generate_a3_ml_c01_pipeline.py"
    spec = importlib.util.spec_from_file_location("generate_a3_ml_c01_pipeline", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not load C01 script: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules["generate_a3_ml_c01_pipeline"] = module
    spec.loader.exec_module(module)
    return module


def _read_json(path_or_text: str | Path) -> dict[str, Any]:
    if not path_or_text:
        return {}
    path = Path(path_or_text)
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))
