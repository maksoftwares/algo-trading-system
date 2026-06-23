from __future__ import annotations

import json
import traceback
from pathlib import Path
from typing import Any

from .live_refresh_orchestrator import run_live_refresh_or_preflight
from .market_data_export import _table, _utc_now, _write_json_atomic
from .observer_deploy import prepare_observer_deploy
from .pipeline_orchestrator import run_offline_prediction_readiness_pipeline


DEFAULT_STATUS_JSON = Path("outputs") / "reports" / "A3_ML_DEMO_PREDICTION_ACTIVATION_STATUS.json"
SCHEMA_VERSION = "a3_ml_demo_prediction_activation_status_v1"
EXPECTED_ACCOUNTS = ("A1", "A2", "A3")
REQUIRED_OBSERVER_ARTIFACTS = ("observer_source", "handoff_include", "passive_preset", "compiled_ex5")


def run_demo_prediction_activation(
    root: Path,
    report_json: Path | None = None,
    *,
    run_pipeline: bool = True,
    refresh_live_readonly: bool = False,
    requested_start_utc: str | None = None,
    max_tick_days: int | None = None,
    publish: bool = False,
    deploy_observer: bool = False,
    compile_observer: bool = True,
) -> Path:
    root = root.resolve()
    report_json = (report_json or root / DEFAULT_STATUS_JSON).resolve()
    actions: list[dict[str, Any]] = []
    if run_pipeline:
        actions.extend(
            _run_requested_actions(
                root,
                refresh_live_readonly=refresh_live_readonly,
                requested_start_utc=requested_start_utc,
                max_tick_days=max_tick_days,
                publish=publish,
            )
        )
    if deploy_observer:
        actions.append(_run_action("C09 observer deploy", lambda: prepare_observer_deploy(root, deploy=True, compile_scratch=compile_observer)))
    summary = _summary(root)
    validations = _validations(summary)
    status = _activation_status(summary, validations, publish_requested=publish)
    payload = {
        "status": status,
        "stage": "C10-DEMO-PREDICTION-ACTIVATION",
        "created_at_utc": _utc_now(),
        "schema_version": SCHEMA_VERSION,
        "dataset_version": summary.get("pointer", {}).get("dataset_version", ""),
        "requested_actions": {
            "run_pipeline": bool(run_pipeline),
            "refresh_live_readonly": bool(refresh_live_readonly),
            "publish": bool(publish),
            "deploy_observer": bool(deploy_observer),
        },
        "actions": actions,
        "summary": _summary_head(summary),
        "validations": validations,
        "blockers": _blockers(validations),
        "authorization": {
            "python_demo_predictions_authorized": status in {"READY_TO_PUBLISH_HANDOFF", "READY_FOR_PASSIVE_EA_CONSUMPTION"},
            "ea_consumption_authorized": status == "READY_FOR_PASSIVE_EA_CONSUMPTION",
            "handoff_publish_requested": bool(publish),
            "broker_action_authorized": False,
        },
        "boundary": {
            "mt5_connection_attempted": bool(refresh_live_readonly),
            "data_export_attempted": bool(refresh_live_readonly),
            "terminal_runtime_change_authorized": False,
            "profile_or_chart_change_authorized": False,
            "ea_file_drop_authorized": bool(summary.get("c06", {}).get("authorization", {}).get("mt5_file_publish_attempted", False)),
            "broker_action_authorized": False,
        },
        "outputs": {
            "status_report_json": str(report_json),
            "status_report_md": str(report_json.with_suffix(".md")),
        },
        "next_allowed_stage": _next_allowed_stage(status, validations, summary),
    }
    _write_status(report_json, payload)
    _update_pointer(root / "outputs" / "reports" / "C02_DATASET_POINTER.json", payload)
    return report_json


def render_demo_prediction_activation_status_md(payload: dict[str, Any]) -> str:
    summary_rows = [{"Stage": key, "Status": value} for key, value in payload.get("summary", {}).get("stage_statuses", {}).items()]
    validation_rows = [
        {"Check": item.get("check", ""), "Passed": str(item.get("passed", False)).lower(), "Detail": item.get("detail", "")}
        for item in payload.get("validations", [])
    ]
    action_rows = [
        {"Action": item.get("action", ""), "Status": item.get("status", ""), "Detail": item.get("detail", "")}
        for item in payload.get("actions", [])
    ]
    blockers = payload.get("blockers", [])
    blocker_lines = "\n".join(f"- {item}" for item in blockers) if blockers else "- none"
    return "\n".join(
        [
            "# A3 ML Demo Prediction Activation Status",
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
            "## Validations",
            "",
            _table(validation_rows, ["Check", "Passed", "Detail"]) if validation_rows else "No validations ran.",
            "",
            "## Blockers",
            "",
            blocker_lines,
            "",
            "## Authorization",
            "",
            f"- Python demo predictions authorized: {str(payload['authorization']['python_demo_predictions_authorized']).lower()}.",
            f"- EA consumption authorized: {str(payload['authorization']['ea_consumption_authorized']).lower()}.",
            f"- Handoff publish requested: {str(payload['authorization']['handoff_publish_requested']).lower()}.",
            "- Broker action authorized: false.",
            "",
            "## Boundary",
            "",
            f"- MT5 connection attempted: {str(payload['boundary']['mt5_connection_attempted']).lower()}.",
            f"- Data export attempted: {str(payload['boundary']['data_export_attempted']).lower()}.",
            "- Terminal runtime change authorized: false.",
            "- Profile or chart change authorized: false.",
            f"- EA file drop authorized: {str(payload['boundary']['ea_file_drop_authorized']).lower()}.",
            "- Broker action authorized: false.",
            "",
            "## Next",
            "",
            payload["next_allowed_stage"],
            "",
        ]
    )


def _run_requested_actions(
    root: Path,
    *,
    refresh_live_readonly: bool,
    requested_start_utc: str | None,
    max_tick_days: int | None,
    publish: bool,
) -> list[dict[str, Any]]:
    if refresh_live_readonly:
        return [
            _run_action(
                "C08 live read-only refresh",
                lambda: run_live_refresh_or_preflight(
                    root,
                    execute_live_readonly=True,
                    requested_start_utc=requested_start_utc,
                    max_tick_days=max_tick_days,
                    publish=publish,
                ),
            )
        ]
    return [_run_action("C07 offline prediction readiness pipeline", lambda: run_offline_prediction_readiness_pipeline(root, publish=publish))]


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
            "traceback": traceback.format_exc(),
        }


def _summary(root: Path) -> dict[str, Any]:
    reports = root / "outputs" / "reports"
    return {
        "pointer": _read_json(reports / "C02_DATASET_POINTER.json"),
        "c03": _read_json(reports / "C03_TRAINING_READINESS_REPORT.json"),
        "c05": _read_json(reports / "A3_ML_TRAINING_STATUS.json"),
        "c04": _read_json(reports / "A3_ML_SHADOW_BRIDGE_STATUS.json"),
        "c06": _read_json(reports / "A3_ML_EA_HANDOFF_STATUS.json"),
        "c13": _read_json(reports / "A3_ML_FAIL_CLOSED_HANDOFF_REHEARSAL_STATUS.json"),
        "c07": _read_json(reports / "A3_ML_PIPELINE_RUN_STATUS.json"),
        "c08": _read_json(reports / "A3_ML_LIVE_REFRESH_STATUS.json"),
        "c09": _read_json(reports / "A3_ML_OBSERVER_DEPLOY_STATUS.json"),
        "c14": _read_json(reports / "A3_ML_OBSERVER_RUNTIME_ATTACH_STATUS.json"),
        "c15": _read_json(reports / "A3_ML_OBSERVER_MANUAL_ATTACH_PACKET.json"),
        "c16": _read_json(reports / "A3_ML_EA_CONSUMER_READINESS_STATUS.json"),
        "c17": _read_json(reports / "A3_ML_BROKER_SHADOW_CONSUMER_DEPLOY_STATUS.json"),
        "c18": _read_json(reports / "A3_ML_EXPLORATORY_TRAINING_REHEARSAL_STATUS.json"),
        "c20": _read_json(reports / "A3_ML_RUNTIME_EVIDENCE_STATUS.json"),
        "c21": _read_json(reports / "A3_ML_RUNTIME_LAUNCH_DIAGNOSTIC_STATUS.json"),
        "c22": _read_json(reports / "A3_ML_POST_ATTACH_RUNTIME_MONITOR_STATUS.json"),
    }


def _summary_head(summary: dict[str, Any]) -> dict[str, Any]:
    return {
        "stage_statuses": {
            "C03 readiness": summary.get("c03", {}).get("status", "MISSING"),
            "C05 training": summary.get("c05", {}).get("status", "MISSING"),
            "C04 shadow bridge": summary.get("c04", {}).get("status", "MISSING"),
            "C06 EA handoff": summary.get("c06", {}).get("status", "MISSING"),
            "C09 observer deploy": summary.get("c09", {}).get("status", "MISSING"),
            "C13 fail-closed rehearsal": summary.get("c13", {}).get("status", "MISSING"),
            "C14 observer runtime": summary.get("c14", {}).get("status", "MISSING"),
            "C15 manual attach packet": summary.get("c15", {}).get("status", "MISSING"),
            "C16 EA consumer readiness": summary.get("c16", {}).get("status", "MISSING"),
            "C17 broker shadow consumer deploy": summary.get("c17", {}).get("status", "MISSING"),
            "C18 exploratory training rehearsal": summary.get("c18", {}).get("status", "MISSING"),
            "C20 runtime evidence": summary.get("c20", {}).get("status", "MISSING"),
            "C21 runtime launch diagnostic": summary.get("c21", {}).get("status", "MISSING"),
            "C22 post-attach runtime monitor": summary.get("c22", {}).get("status", "MISSING"),
        },
        "dataset_version": summary.get("pointer", {}).get("dataset_version", ""),
    }


def _validations(summary: dict[str, Any]) -> list[dict[str, Any]]:
    c03 = summary.get("c03", {})
    c05 = summary.get("c05", {})
    c04 = summary.get("c04", {})
    c06 = summary.get("c06", {})
    c09 = summary.get("c09", {})
    c16 = summary.get("c16", {})
    c20 = summary.get("c20", {})
    c21 = summary.get("c21", {})
    c03_failures = _failed_c03_gates(c03)
    observer_files = _observer_files_status(c09)
    handoff_files = _handoff_files_status(c06)
    passive_consumer = _passive_ea_consumer_status(c16)
    broker_executor_consumer = _broker_executor_consumer_status(c16)
    broker_clear = _broker_action_clear(summary)
    return [
        _check("c03_readiness_pass", c03.get("status") == "PASS", "; ".join(c03_failures) if c03_failures else f"observed={c03.get('status', 'MISSING')}"),
        _check("c05_model_trained", c05.get("status") == "TRAINED_SHADOW_ONLY", f"observed={c05.get('status', 'MISSING')} required=TRAINED_SHADOW_ONLY"),
        _check("c04_shadow_bridge_ready", c04.get("status") == "READY_SHADOW_ONLY", f"observed={c04.get('status', 'MISSING')} required=READY_SHADOW_ONLY"),
        _check(
            "c04_python_predictions_authorized",
            c04.get("authorization", {}).get("python_demo_predictions_authorized") is True,
            f"observed={c04.get('authorization', {}).get('python_demo_predictions_authorized', 'MISSING')} required=true",
        ),
        _check(
            "c06_ea_handoff_ready_or_published",
            c06.get("status") in {"READY_DRY_RUN", "PUBLISHED_TO_MT5_FILES"},
            f"observed={c06.get('status', 'MISSING')} required=READY_DRY_RUN or PUBLISHED_TO_MT5_FILES",
        ),
        _check("c09_observer_deployed", c09.get("status") == "DEPLOYED_PASSIVE_OBSERVER", f"observed={c09.get('status', 'MISSING')} required=DEPLOYED_PASSIVE_OBSERVER"),
        _check("observer_files_exist_all_accounts", observer_files["passed"], observer_files["detail"]),
        _check("c16_passive_ea_consumer_ready", passive_consumer["passed"], passive_consumer["detail"]),
        _check("c16_active_broker_executor_consumers_ready", broker_executor_consumer["passed"], broker_executor_consumer["detail"]),
        _check("handoff_files_published_all_accounts", handoff_files["passed"], handoff_files["detail"]),
        _check(
            "c20_runtime_evidence_all_accounts",
            c20.get("status") == "RUNTIME_EVIDENCE_PRESENT_ALL_ACCOUNTS",
            f"observed={c20.get('status', 'MISSING')} required=RUNTIME_EVIDENCE_PRESENT_ALL_ACCOUNTS",
        ),
        _check(
            "c21_runtime_launch_diagnostic_all_accounts",
            c21.get("status") == "RUNTIME_EVIDENCE_PRESENT_ALL_ACCOUNTS",
            f"observed={c21.get('status', 'MISSING')} required=RUNTIME_EVIDENCE_PRESENT_ALL_ACCOUNTS",
        ),
        _check("broker_action_false_everywhere", broker_clear["passed"], broker_clear["detail"]),
    ]


def _activation_status(summary: dict[str, Any], validations: list[dict[str, Any]], *, publish_requested: bool) -> str:
    c03_status = summary.get("c03", {}).get("status")
    c06_status = summary.get("c06", {}).get("status")
    if all(item["passed"] for item in validations):
        return "READY_FOR_PASSIVE_EA_CONSUMPTION"
    required_before_publish = {
        "c03_readiness_pass",
        "c05_model_trained",
        "c04_shadow_bridge_ready",
        "c04_python_predictions_authorized",
        "c06_ea_handoff_ready_or_published",
        "c09_observer_deployed",
        "observer_files_exist_all_accounts",
        "c16_passive_ea_consumer_ready",
        "broker_action_false_everywhere",
    }
    validation_map = {item["check"]: item["passed"] for item in validations}
    if c06_status == "READY_DRY_RUN" and all(validation_map.get(check) for check in required_before_publish):
        return "READY_TO_PUBLISH_HANDOFF" if not publish_requested else "HANDOFF_PUBLISH_FAILED"
    if c03_status in {"NO_GO", "MISSING", ""}:
        return "WAITING_FOR_DATA"
    return "REFUSED_NOT_READY"


def _observer_files_status(c09: dict[str, Any]) -> dict[str, Any]:
    files = c09.get("outputs", {}).get("deployed_files", [])
    if c09.get("status") != "DEPLOYED_PASSIVE_OBSERVER":
        return {"passed": False, "detail": f"c09_status={c09.get('status', 'MISSING')}"}
    seen = {(item.get("account_label", ""), item.get("artifact", "")) for item in files if Path(item.get("target_path", "")).exists()}
    missing = [f"{account}:{artifact}" for account in EXPECTED_ACCOUNTS for artifact in REQUIRED_OBSERVER_ARTIFACTS if (account, artifact) not in seen]
    return {"passed": not missing, "detail": "all observer artifacts exist" if not missing else "missing " + ",".join(missing)}


def _handoff_files_status(c06: dict[str, Any]) -> dict[str, Any]:
    if c06.get("status") != "PUBLISHED_TO_MT5_FILES":
        return {"passed": False, "detail": f"c06_status={c06.get('status', 'MISSING')} not published"}
    files = c06.get("outputs", {}).get("published_files", [])
    seen = {item.get("account_label", "") for item in files if Path(item.get("target_path", "")).exists()}
    missing = [account for account in EXPECTED_ACCOUNTS if account not in seen]
    return {"passed": not missing, "detail": "all handoff files exist" if not missing else "missing accounts " + ",".join(missing)}


def _broker_action_clear(summary: dict[str, Any]) -> dict[str, Any]:
    failures = []
    for key in ("c03", "c05", "c04", "c06", "c09", "c16", "c17", "c18", "c20", "c21", "c22"):
        stage = summary.get(key, {})
        authorization = stage.get("authorization", {})
        boundary = stage.get("boundary", {})
        if authorization.get("broker_action_authorized") is True:
            failures.append(f"{key}.authorization")
        if boundary.get("broker_action_authorized") is True:
            failures.append(f"{key}.boundary")
    return {"passed": not failures, "detail": "broker action false in all checked reports" if not failures else ",".join(failures)}


def _passive_ea_consumer_status(c16: dict[str, Any]) -> dict[str, Any]:
    if not c16:
        return {"passed": False, "detail": "observed=MISSING required=C16 EA consumer readiness report"}
    observed = c16.get("authorization", {}).get("passive_observer_ml_consumer_ready", "MISSING")
    return {
        "passed": observed is True,
        "detail": f"observed={observed} c16_status={c16.get('status', 'MISSING')} required=true",
    }


def _broker_executor_consumer_status(c16: dict[str, Any]) -> dict[str, Any]:
    if not c16:
        return {"passed": False, "detail": "observed=MISSING required=C16 EA consumer readiness report"}
    observed = c16.get("authorization", {}).get("broker_executor_ml_consumer_ready", "MISSING")
    return {
        "passed": observed is True,
        "detail": f"observed={observed} c16_status={c16.get('status', 'MISSING')} required=true",
    }


def _failed_c03_gates(c03: dict[str, Any]) -> list[str]:
    return [
        f"{check.get('gate')} observed {check.get('observed')} required {check.get('required')}"
        for check in c03.get("checks", [])
        if not check.get("passed")
    ]


def _blockers(validations: list[dict[str, Any]]) -> list[str]:
    return [f"{item['check']}: {item['detail']}" for item in validations if not item.get("passed")]


def _next_allowed_stage(status: str, validations: list[dict[str, Any]], summary: dict[str, Any]) -> str:
    if status == "READY_FOR_PASSIVE_EA_CONSUMPTION":
        return "EA handoff files are published and the passive observer is deployed. Attach only passive chart observers; broker action remains false."
    if status == "READY_TO_PUBLISH_HANDOFF":
        return "Rerun C10 with --publish to copy A3_ML_EA_HANDOFF.csv to all three MT5 Files roots."
    if status == "WAITING_FOR_DATA":
        c21_status = summary.get("c21", {}).get("status", "MISSING")
        if c21_status == "LAUNCH_SENT_NO_OBSERVER_JOURNAL_EVIDENCE":
            return "Attach A3MlPredictionObserver manually on XAUUSD M5 for A1/A2/A3, run C22 to wait for runtime evidence, then rerun C19 with --no-run-pipeline. Keep collecting/exporting A1/A2/A3 data until C03 passes."
        if c21_status == "PREFLIGHT_BLOCKED":
            return "Fix the C21 runtime-launch preflight issue, then rerun C19. Continue collecting/exporting A1/A2/A3 data until C03 passes."
        return "Collect/export more A1/A2/A3 data, rerun C18 for research-only Python training rehearsal as needed, then rerun C10 with --refresh-live-readonly when MT5 terminals and market data are available."
    first = next((item for item in validations if not item.get("passed")), None)
    return f"Fix {first['check']} then rerun C10." if first else "Rerun C10 after reviewing upstream reports."


def _check(check: str, passed: bool, detail: str) -> dict[str, Any]:
    return {"check": check, "passed": bool(passed), "detail": detail}


def _write_status(status_json: Path, payload: dict[str, Any]) -> None:
    status_json.parent.mkdir(parents=True, exist_ok=True)
    status_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    status_json.with_suffix(".md").write_text(render_demo_prediction_activation_status_md(payload), encoding="utf-8")


def _update_pointer(pointer_path: Path, payload: dict[str, Any]) -> None:
    if not pointer_path.exists():
        return
    pointer = _read_json(pointer_path)
    pointer["c10_demo_prediction_activation_status_report"] = payload["outputs"]["status_report_json"]
    pointer["c10_demo_prediction_activation_status"] = payload["status"]
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
