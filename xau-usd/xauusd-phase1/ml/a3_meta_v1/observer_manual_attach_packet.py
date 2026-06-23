from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .account_registry import MT5AccountSpec, load_mt5_account_registry
from .market_data_export import _table, _utc_now, _write_json_atomic


DEFAULT_STATUS_JSON = Path("outputs") / "reports" / "A3_ML_OBSERVER_MANUAL_ATTACH_PACKET.json"
SCHEMA_VERSION = "a3_ml_observer_manual_attach_packet_v1"
EXPERT_NAME = "A3MlPredictionObserver"
PRESET_NAME = "A3MlPredictionObserver.passive_xauusd.set"
HANDOFF_FILE_NAME = "A3_ML_EA_HANDOFF.csv"
STARTUP_LOG_NAME = "a3_ml_prediction_observer_startup.csv"
PREDICTION_LOG_NAME = "a3_ml_prediction_observer_log.csv"


def generate_observer_manual_attach_packet(root: Path, report_json: Path | None = None) -> Path:
    root = root.resolve()
    report_json = (report_json or root / DEFAULT_STATUS_JSON).resolve()
    registry = load_mt5_account_registry(root / "config" / "ml" / "mt5_accounts.yaml")
    pointer = _read_json(root / "outputs" / "reports" / "C02_DATASET_POINTER.json")
    c09 = _read_json(root / "outputs" / "reports" / "A3_ML_OBSERVER_DEPLOY_STATUS.json")
    c13 = _read_json(root / "outputs" / "reports" / "A3_ML_FAIL_CLOSED_HANDOFF_REHEARSAL_STATUS.json")
    c14 = _read_json(root / "outputs" / "reports" / "A3_ML_OBSERVER_RUNTIME_ATTACH_STATUS.json")
    accounts = [_account_attach_payload(account) for account in registry.accounts]
    validations = _validations(accounts, c09, c13)
    all_preflight_ready = all(item["passed"] for item in validations)
    all_runtime_logging = all(item["startup_log_exists"] and item["prediction_log_exists"] for item in accounts)
    any_runtime_logging = any(item["startup_log_exists"] or item["prediction_log_exists"] for item in accounts)
    if not all_preflight_ready:
        status = "PREFLIGHT_BLOCKED"
    elif all_runtime_logging:
        status = "RUNTIME_LOGS_PRESENT_ALL_ACCOUNTS"
    elif any_runtime_logging:
        status = "PARTIAL_RUNTIME_LOGS_PRESENT"
    else:
        status = "MANUAL_ATTACH_REQUIRED"
    payload = {
        "status": status,
        "stage": "C15-ML-OBSERVER-MANUAL-ATTACH-PACKET",
        "created_at_utc": _utc_now(),
        "schema_version": SCHEMA_VERSION,
        "dataset_version": pointer.get("dataset_version", ""),
        "authorization": {
            "python_demo_predictions_authorized": False,
            "ea_consumption_authorized": False,
            "broker_action_authorized": False,
            "manual_attach_required": status in {"MANUAL_ATTACH_REQUIRED", "PARTIAL_RUNTIME_LOGS_PRESENT"},
        },
        "inputs": {
            "registry_path": str(root / "config" / "ml" / "mt5_accounts.yaml"),
            "c09_observer_deploy": str(root / "outputs" / "reports" / "A3_ML_OBSERVER_DEPLOY_STATUS.json"),
            "c13_fail_closed_handoff": str(root / "outputs" / "reports" / "A3_ML_FAIL_CLOSED_HANDOFF_REHEARSAL_STATUS.json"),
            "c14_runtime_attach": str(root / "outputs" / "reports" / "A3_ML_OBSERVER_RUNTIME_ATTACH_STATUS.json"),
        },
        "upstream_statuses": {
            "c09_observer_deploy": c09.get("status", "MISSING"),
            "c13_fail_closed_handoff": c13.get("status", "MISSING"),
            "c14_runtime_attach": c14.get("status", "MISSING"),
        },
        "outputs": {
            "status_report_json": str(report_json),
            "status_report_md": str(report_json.with_suffix(".md")),
        },
        "accounts": accounts,
        "manual_attach_steps": _manual_steps(),
        "validations": validations,
        "boundary": {
            "mt5_connection_attempted": False,
            "terminal_runtime_launch_attempted": False,
            "terminal_shutdown_attempted": False,
            "profile_or_chart_file_write_attempted": False,
            "broker_action_authorized": False,
        },
        "next_allowed_stage": _next_allowed_stage(status),
    }
    _write_status(report_json, payload)
    _update_pointer(root / "outputs" / "reports" / "C02_DATASET_POINTER.json", pointer, payload)
    return report_json


def render_observer_manual_attach_packet_md(payload: dict[str, Any]) -> str:
    accounts = [
        {
            "Account": item["account_label"],
            "Login": item["account_scope"],
            "Terminal": item["terminal_exe"],
            "Startup log": str(item["startup_log_exists"]).lower(),
            "Prediction log": str(item["prediction_log_exists"]).lower(),
        }
        for item in payload.get("accounts", [])
    ]
    validations = [
        {"Check": item["check"], "Passed": str(item["passed"]).lower(), "Detail": item["detail"]}
        for item in payload.get("validations", [])
    ]
    steps = "\n".join(f"{index}. {step}" for index, step in enumerate(payload.get("manual_attach_steps", []), start=1))
    account_details = []
    for item in payload.get("accounts", []):
        account_details.extend(
            [
                f"### {item['account_label']} {item['account_scope']}",
                "",
                f"- Terminal: {item['terminal_exe']}",
                f"- Files root: {item['files_root']}",
                f"- Expert: {item['expert_path']}",
                f"- Preset: {item['preset_path']}",
                f"- Handoff file: {item['handoff_path']}",
                f"- Startup log: {item['startup_log_path']}",
                f"- Prediction log: {item['prediction_log_path']}",
                "",
            ]
        )
    return "\n".join(
        [
            "# A3 ML Observer Manual Attach Packet",
            "",
            f"Overall status: {payload['status']}",
            f"Dataset version: {payload.get('dataset_version', '')}",
            "",
            "## Authorization",
            "",
            "- Python demo predictions authorized: false",
            "- EA consumption authorized: false",
            "- Broker action authorized: false",
            "",
            "## Upstream Statuses",
            "",
            f"- C09 observer deploy: {payload.get('upstream_statuses', {}).get('c09_observer_deploy', '')}",
            f"- C13 fail-closed handoff: {payload.get('upstream_statuses', {}).get('c13_fail_closed_handoff', '')}",
            f"- C14 runtime attach: {payload.get('upstream_statuses', {}).get('c14_runtime_attach', '')}",
            "",
            "## Account Runtime State",
            "",
            _table(accounts, ["Account", "Login", "Terminal", "Startup log", "Prediction log"]) if accounts else "No accounts configured.",
            "",
            "## Manual Attach Steps",
            "",
            steps,
            "",
            "## Account Details",
            "",
            *account_details,
            "## Validations",
            "",
            _table(validations, ["Check", "Passed", "Detail"]) if validations else "No validations ran.",
            "",
            "## Boundary",
            "",
            "- MT5 connection attempted: false.",
            "- Terminal runtime launch attempted: false.",
            "- Terminal shutdown attempted: false.",
            "- Profile or chart file write attempted: false.",
            "- Broker action authorized: false.",
            "",
            "## Next",
            "",
            payload["next_allowed_stage"],
            "",
        ]
    )


def _account_attach_payload(account: MT5AccountSpec) -> dict[str, Any]:
    data_root = Path(account.expected_data_path or "")
    files_root = Path(account.files_roots[0]) if account.files_roots else data_root / "MQL5" / "Files"
    return {
        "account_label": account.account_label,
        "account_scope": account.account_scope,
        "role": account.role,
        "terminal_exe": account.terminal_exe,
        "data_root": str(data_root),
        "files_root": str(files_root),
        "expert_path": str(data_root / "MQL5" / "Experts" / f"{EXPERT_NAME}.ex5"),
        "expert_exists": (data_root / "MQL5" / "Experts" / f"{EXPERT_NAME}.ex5").exists(),
        "preset_path": str(data_root / "MQL5" / "Presets" / PRESET_NAME),
        "preset_exists": (data_root / "MQL5" / "Presets" / PRESET_NAME).exists(),
        "handoff_path": str(files_root / HANDOFF_FILE_NAME),
        "handoff_exists": (files_root / HANDOFF_FILE_NAME).exists(),
        "startup_log_path": str(files_root / STARTUP_LOG_NAME),
        "startup_log_exists": (files_root / STARTUP_LOG_NAME).exists(),
        "prediction_log_path": str(files_root / PREDICTION_LOG_NAME),
        "prediction_log_exists": (files_root / PREDICTION_LOG_NAME).exists(),
    }


def _validations(accounts: list[dict[str, Any]], c09: dict[str, Any], c13: dict[str, Any]) -> list[dict[str, Any]]:
    checks = [
        _check("c09_observer_deployed", c09.get("status") == "DEPLOYED_PASSIVE_OBSERVER", c09.get("status", "MISSING")),
        _check(
            "c13_fail_closed_handoff_published",
            c13.get("status") == "PUBLISHED_FAIL_CLOSED_REHEARSAL",
            c13.get("status", "MISSING"),
        ),
    ]
    for account in accounts:
        prefix = account["account_label"]
        checks.extend(
            [
                _check(f"{prefix}_expert_exists", bool(account["expert_exists"]), account["expert_path"]),
                _check(f"{prefix}_preset_exists", bool(account["preset_exists"]), account["preset_path"]),
                _check(f"{prefix}_handoff_exists", bool(account["handoff_exists"]), account["handoff_path"]),
            ]
        )
    return checks


def _manual_steps() -> list[str]:
    return [
        "Open each MT5 terminal for A1, A2, and A3.",
        "Open or select an XAUUSD M5 chart.",
        "Attach the Expert Advisor named A3MlPredictionObserver.",
        "Load preset A3MlPredictionObserver.passive_xauusd.set.",
        "Confirm InpDryRunOnly=true, InpTargetSymbol=XAUUSD, and InpHandoffFileName=A3_ML_EA_HANDOFF.csv.",
        "Click OK only with those passive settings.",
        "Wait for a tick or new M5 bar, then run C28 to wait for observer logs and demo-shadow read-path evidence.",
    ]


def _next_allowed_stage(status: str) -> str:
    if status == "RUNTIME_LOGS_PRESENT_ALL_ACCOUNTS":
        return "Passive ML observer runtime is logging on all accounts. Continue data collection and rerun C10 after new market data."
    if status == "PARTIAL_RUNTIME_LOGS_PRESENT":
        return "Attach the passive observer on the remaining accounts, then run C28 to wait for demo-shadow runtime evidence."
    if status == "MANUAL_ATTACH_REQUIRED":
        return "Attach A3MlPredictionObserver manually on XAUUSD M5 for A1, A2, and A3, then run C28 to wait for demo-shadow runtime evidence."
    return "Fix missing observer, preset, or handoff files, then rerun C09/C13/C15."


def _write_status(status_json: Path, payload: dict[str, Any]) -> None:
    status_json.parent.mkdir(parents=True, exist_ok=True)
    status_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    status_json.with_suffix(".md").write_text(render_observer_manual_attach_packet_md(payload), encoding="utf-8")


def _update_pointer(pointer_path: Path, pointer: dict[str, Any], payload: dict[str, Any]) -> None:
    if not pointer:
        return
    pointer["c15_observer_manual_attach_packet_report"] = payload["outputs"]["status_report_json"]
    pointer["c15_observer_manual_attach_packet_status"] = payload["status"]
    pointer["python_demo_predictions_authorized"] = False
    pointer["ea_consumption_authorized"] = False
    pointer["broker_action_authorized"] = False
    _write_json_atomic(pointer_path, pointer)


def _check(check: str, passed: bool, detail: str) -> dict[str, Any]:
    return {"check": check, "passed": bool(passed), "detail": detail}


def _read_json(path_or_text: str | Path) -> dict[str, Any]:
    if not path_or_text:
        return {}
    path = Path(path_or_text)
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))
