from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from .account_registry import MT5AccountSpec, load_mt5_account_registry
from .broker_shadow_manual_attach_packet import HANDOFF_FILE_NAME, SHADOW_TAP_LOG_NAME
from .market_data_export import _table, _utc_now, _write_json_atomic
from .observer_runtime_attach import EXPERT_NAME as OBSERVER_EXPERT_NAME
from .observer_runtime_attach import PREDICTION_LOG_NAME, PRESET_NAME as OBSERVER_PRESET_NAME, STARTUP_LOG_NAME


DEFAULT_STATUS_JSON = Path("outputs") / "reports" / "A3_ML_DEMO_ATTACH_WATCH_STATUS.json"
SCHEMA_VERSION = "a3_ml_demo_attach_watch_status_v1"


def watch_demo_attach(
    root: Path,
    report_json: Path | None = None,
    *,
    timeout_seconds: int = 0,
    poll_seconds: int = 5,
) -> Path:
    root = root.resolve()
    report_json = (report_json or root / DEFAULT_STATUS_JSON).resolve()
    timeout_seconds = max(0, int(timeout_seconds))
    poll_seconds = max(1, int(poll_seconds))
    registry = load_mt5_account_registry(root / "config" / "ml" / "mt5_accounts.yaml")
    pointer = _read_json(root / "outputs" / "reports" / "C02_DATASET_POINTER.json")
    reports = root / "outputs" / "reports"
    c15 = _read_json(reports / "A3_ML_OBSERVER_MANUAL_ATTACH_PACKET.json")
    c25 = _read_json(reports / "A3_ML_BROKER_SHADOW_MANUAL_ATTACH_PACKET.json")
    c30 = _read_json(reports / "A3_ML_BROKER_SHADOW_PRESET_DEPLOY_STATUS.json")
    started_monotonic = time.monotonic()
    started_at_utc = _utc_now()
    attempts: list[dict[str, Any]] = []
    final_accounts: list[dict[str, Any]] = []
    final_validations: list[dict[str, Any]] = []
    final_status = "WAITING_FOR_MANUAL_ATTACH"

    while True:
        final_accounts = [_account_payload(account, c15, c25, c30) for account in registry.accounts]
        final_validations = _validations(final_accounts, c30)
        final_status = _status(final_accounts, final_validations, timeout_seconds=timeout_seconds, timed_out=False)
        elapsed_seconds = round(time.monotonic() - started_monotonic, 3)
        attempts.append(_attempt_payload(len(attempts) + 1, elapsed_seconds, final_accounts, final_status))
        if final_status in {"ATTACH_RUNTIME_FILES_PRESENT_ALL_ACCOUNTS", "PREFLIGHT_BLOCKED"}:
            break
        if timeout_seconds == 0:
            break
        remaining = timeout_seconds - (time.monotonic() - started_monotonic)
        if remaining <= 0:
            break
        time.sleep(min(poll_seconds, max(0.0, remaining)))

    elapsed_seconds = round(time.monotonic() - started_monotonic, 3)
    timed_out = timeout_seconds > 0 and elapsed_seconds >= timeout_seconds
    final_status = _status(final_accounts, final_validations, timeout_seconds=timeout_seconds, timed_out=timed_out)
    payload = {
        "status": final_status,
        "stage": "C31-DEMO-ATTACH-WATCH",
        "created_at_utc": _utc_now(),
        "started_at_utc": started_at_utc,
        "schema_version": SCHEMA_VERSION,
        "dataset_version": pointer.get("dataset_version", ""),
        "monitor": {
            "timeout_seconds": timeout_seconds,
            "poll_seconds": poll_seconds,
            "elapsed_seconds": elapsed_seconds,
            "attempt_count": len(attempts),
            "timed_out": bool(timed_out and final_status != "ATTACH_RUNTIME_FILES_PRESENT_ALL_ACCOUNTS"),
        },
        "authorization": {
            "official_model_training_authorized": False,
            "python_demo_predictions_authorized": False,
            "ea_consumption_authorized": False,
            "broker_action_authorized": False,
        },
        "upstream_statuses": {
            "c15_observer_manual_attach": c15.get("status", "MISSING"),
            "c25_broker_shadow_manual_attach": c25.get("status", "MISSING"),
            "c30_broker_shadow_preset_deploy": c30.get("status", "MISSING"),
        },
        "runtime_evidence": {
            "observer_runtime_files_all_accounts": all(item["observer_runtime_files_present"] for item in final_accounts),
            "broker_shadow_tap_all_accounts": all(item["broker_shadow_tap_exists"] for item in final_accounts),
            "handoff_files_all_accounts": all(item["handoff_exists"] for item in final_accounts),
            "safe_presets_all_accounts": all(item["safe_presets_ready"] for item in final_accounts),
        },
        "accounts": final_accounts,
        "attempts": attempts,
        "validations": final_validations,
        "inputs": {
            "registry_path": str(root / "config" / "ml" / "mt5_accounts.yaml"),
            "c15_observer_manual_attach": str(reports / "A3_ML_OBSERVER_MANUAL_ATTACH_PACKET.json"),
            "c25_broker_shadow_manual_attach": str(reports / "A3_ML_BROKER_SHADOW_MANUAL_ATTACH_PACKET.json"),
            "c30_broker_shadow_preset_deploy": str(reports / "A3_ML_BROKER_SHADOW_PRESET_DEPLOY_STATUS.json"),
        },
        "outputs": {
            "status_report_json": str(report_json),
            "status_report_md": str(report_json.with_suffix(".md")),
        },
        "boundary": {
            "mt5_connection_attempted": False,
            "data_export_attempted": False,
            "terminal_runtime_launch_attempted": False,
            "terminal_shutdown_attempted": False,
            "profile_or_chart_file_write_attempted": False,
            "ea_file_drop_authorized": False,
            "broker_action_authorized": False,
        },
        "next_allowed_stage": _next_allowed_stage(final_status),
    }
    _write_status(report_json, payload)
    _update_pointer(root / "outputs" / "reports" / "C02_DATASET_POINTER.json", pointer, payload)
    return report_json


def render_demo_attach_watch_md(payload: dict[str, Any]) -> str:
    accounts = [
        {
            "Account": item["account_label"],
            "Observer": str(item["observer_runtime_files_present"]).lower(),
            "Broker tap": str(item["broker_shadow_tap_exists"]).lower(),
            "Handoff": str(item["handoff_exists"]).lower(),
            "Missing": ", ".join(item["missing_runtime_artifacts"]) or "-",
        }
        for item in payload.get("accounts", [])
    ]
    attempts = [
        {
            "Attempt": str(item["attempt"]),
            "Elapsed": str(item["elapsed_seconds"]),
            "Ready accounts": str(item["ready_account_count"]),
            "Missing": item["missing_summary"],
            "Status": item["status"],
        }
        for item in payload.get("attempts", [])
    ]
    validations = [
        {"Check": item["check"], "Passed": str(item["passed"]).lower(), "Detail": item["detail"]}
        for item in payload.get("validations", [])
    ]
    details = _account_detail_lines(payload.get("accounts", []))
    return "\n".join(
        [
            "# A3 ML Demo Attach Watch Status",
            "",
            f"Overall status: {payload['status']}",
            f"Dataset version: {payload.get('dataset_version', '')}",
            "",
            "## Monitor",
            "",
            f"- Timeout seconds: {payload['monitor']['timeout_seconds']}.",
            f"- Poll seconds: {payload['monitor']['poll_seconds']}.",
            f"- Elapsed seconds: {payload['monitor']['elapsed_seconds']}.",
            f"- Attempt count: {payload['monitor']['attempt_count']}.",
            f"- Timed out: {str(payload['monitor']['timed_out']).lower()}.",
            "",
            "## Account Evidence",
            "",
            _table(accounts, ["Account", "Observer", "Broker tap", "Handoff", "Missing"]) if accounts else "No accounts configured.",
            "",
            "## Exact Missing Paths",
            "",
            details,
            "",
            "## Attempts",
            "",
            _table(attempts, ["Attempt", "Elapsed", "Ready accounts", "Missing", "Status"]) if attempts else "No attempts ran.",
            "",
            "## Validations",
            "",
            _table(validations, ["Check", "Passed", "Detail"]) if validations else "No validations ran.",
            "",
            "## Authorization",
            "",
            "- Official model training authorized: false.",
            "- Python demo predictions authorized: false.",
            "- EA consumption authorized: false.",
            "- Broker action authorized: false.",
            "",
            "## Boundary",
            "",
            "- MT5 connection attempted: false.",
            "- Data export attempted: false.",
            "- Terminal runtime launch attempted: false.",
            "- Terminal shutdown attempted: false.",
            "- Profile or chart file write attempted: false.",
            "- EA file drop authorized: false.",
            "- Broker action authorized: false.",
            "",
            "## Next",
            "",
            payload["next_allowed_stage"],
            "",
        ]
    )


def _account_payload(account: MT5AccountSpec, c15: dict[str, Any], c25: dict[str, Any], c30: dict[str, Any]) -> dict[str, Any]:
    data_root = Path(account.expected_data_path or "")
    files_root = Path(account.files_roots[0]) if account.files_roots else data_root / "MQL5" / "Files"
    observer = _by_label(c15, account.account_label)
    broker = _by_label(c25, account.account_label)
    c30_target = _target_by_label(c30, account.account_label)
    startup_log = files_root / STARTUP_LOG_NAME
    prediction_log = files_root / PREDICTION_LOG_NAME
    broker_tap = files_root / SHADOW_TAP_LOG_NAME
    handoff = files_root / HANDOFF_FILE_NAME
    observer_preset = Path(observer.get("preset_path") or (data_root / "MQL5" / "Presets" / OBSERVER_PRESET_NAME))
    safe_preset_paths = broker.get("safe_preset_paths") or [item.get("target_path", "") for item in c30_target.get("presets", [])]
    safe_preset_names = broker.get("safe_preset_names") or [Path(path).name for path in safe_preset_paths]
    recommended_experts = broker.get("recommended_experts", [])
    safe_presets_ready = bool(safe_preset_paths) and all(Path(path).exists() for path in safe_preset_paths)
    missing = []
    if not startup_log.exists():
        missing.append("observer_startup_log")
    if not prediction_log.exists():
        missing.append("observer_prediction_log")
    if not broker_tap.exists():
        missing.append("broker_shadow_tap")
    if not handoff.exists():
        missing.append("handoff_file")
    return {
        "account_label": account.account_label,
        "account_scope": account.account_scope,
        "role": account.role,
        "terminal_exe": account.terminal_exe,
        "files_root": str(files_root),
        "observer_expert_name": OBSERVER_EXPERT_NAME,
        "observer_preset_path": str(observer_preset),
        "observer_preset_exists": observer_preset.exists(),
        "observer_startup_log_path": str(startup_log),
        "observer_startup_log_exists": startup_log.exists(),
        "observer_prediction_log_path": str(prediction_log),
        "observer_prediction_log_exists": prediction_log.exists(),
        "observer_runtime_files_present": startup_log.exists() and prediction_log.exists(),
        "handoff_path": str(handoff),
        "handoff_exists": handoff.exists(),
        "broker_shadow_tap_path": str(broker_tap),
        "broker_shadow_tap_exists": broker_tap.exists(),
        "recommended_broker_shadow_experts": recommended_experts,
        "safe_broker_shadow_preset_names": safe_preset_names,
        "safe_broker_shadow_preset_paths": safe_preset_paths,
        "safe_presets_ready": safe_presets_ready,
        "missing_runtime_artifacts": missing,
        "ready_for_c28": not missing and safe_presets_ready,
    }


def _validations(accounts: list[dict[str, Any]], c30: dict[str, Any]) -> list[dict[str, Any]]:
    checks = [
        _check(
            "c30_safe_passive_presets_deployed",
            c30.get("status") == "DEPLOYED_SAFE_PASSIVE_PRESETS",
            c30.get("status", "MISSING"),
        )
    ]
    for account in accounts:
        prefix = account["account_label"]
        checks.extend(
            [
                _check(f"{prefix}_observer_preset_exists", account["observer_preset_exists"], account["observer_preset_path"]),
                _check(f"{prefix}_safe_broker_shadow_presets_exist", account["safe_presets_ready"], _preset_detail(account)),
                _check(f"{prefix}_handoff_exists", account["handoff_exists"], account["handoff_path"]),
            ]
        )
    return checks


def _status(
    accounts: list[dict[str, Any]],
    validations: list[dict[str, Any]],
    *,
    timeout_seconds: int,
    timed_out: bool,
) -> str:
    if any(not item["passed"] for item in validations):
        return "PREFLIGHT_BLOCKED"
    if accounts and all(item["ready_for_c28"] for item in accounts):
        return "ATTACH_RUNTIME_FILES_PRESENT_ALL_ACCOUNTS"
    if any(not item["missing_runtime_artifacts"] for item in accounts):
        return "PARTIAL_ATTACH_RUNTIME_FILES_PRESENT"
    if timed_out and timeout_seconds > 0:
        return "TIMEOUT_WAITING_FOR_MANUAL_ATTACH"
    return "WAITING_FOR_MANUAL_ATTACH"


def _attempt_payload(attempt: int, elapsed_seconds: float, accounts: list[dict[str, Any]], status: str) -> dict[str, Any]:
    missing_parts = []
    for account in accounts:
        missing = ",".join(account["missing_runtime_artifacts"]) or "none"
        missing_parts.append(f"{account['account_label']}:{missing}")
    return {
        "attempt": attempt,
        "elapsed_seconds": elapsed_seconds,
        "ready_account_count": sum(1 for account in accounts if account["ready_for_c28"]),
        "missing_summary": "; ".join(missing_parts),
        "status": status,
    }


def _account_detail_lines(accounts: list[dict[str, Any]]) -> str:
    if not accounts:
        return "No accounts configured."
    lines: list[str] = []
    for account in accounts:
        lines.extend(
            [
                f"### {account['account_label']} {account['account_scope']}",
                "",
                f"- Terminal: {account['terminal_exe']}",
                f"- Observer preset: {account['observer_preset_path']}",
                f"- Missing observer startup log: {account['observer_startup_log_path'] if not account['observer_startup_log_exists'] else '-'}",
                f"- Missing observer prediction log: {account['observer_prediction_log_path'] if not account['observer_prediction_log_exists'] else '-'}",
                f"- Missing broker-shadow tap: {account['broker_shadow_tap_path'] if not account['broker_shadow_tap_exists'] else '-'}",
                f"- Broker-shadow presets: {', '.join(account['safe_broker_shadow_preset_paths']) or '-'}",
                "",
            ]
        )
    return "\n".join(lines).rstrip()


def _preset_detail(account: dict[str, Any]) -> str:
    paths = account.get("safe_broker_shadow_preset_paths", [])
    if not paths:
        return "no safe preset paths"
    missing = [path for path in paths if not Path(path).exists()]
    if missing:
        return "missing: " + ",".join(missing)
    return "safe presets exist"


def _next_allowed_stage(status: str) -> str:
    if status == "ATTACH_RUNTIME_FILES_PRESENT_ALL_ACCOUNTS":
        return "Attach files are present on all accounts. Run C28 to confirm the full Python preview read path."
    if status == "PARTIAL_ATTACH_RUNTIME_FILES_PRESENT":
        return "Some accounts have runtime files. Attach or reload the missing accounts from the Exact Missing Paths section, then rerun C31 or C28."
    if status == "TIMEOUT_WAITING_FOR_MANUAL_ATTACH":
        return "No complete attach evidence appeared before timeout. Keep MT5 open, attach/reload the listed EAs, then rerun C31 or C28."
    if status == "WAITING_FOR_MANUAL_ATTACH":
        return "Attach/reload A3MlPredictionObserver and the listed broker-shadow EAs on XAUUSD M5 for A1/A2/A3, then rerun C31 with a positive timeout or run C28."
    return "Fix C31 preflight checks before expecting MT5 runtime attach evidence."


def _by_label(payload: dict[str, Any], label: str) -> dict[str, Any]:
    for item in payload.get("accounts", []):
        if item.get("account_label") == label:
            return item
    return {}


def _target_by_label(payload: dict[str, Any], label: str) -> dict[str, Any]:
    for item in payload.get("targets", []):
        if item.get("account_label") == label:
            return item
    return {}


def _write_status(status_json: Path, payload: dict[str, Any]) -> None:
    status_json.parent.mkdir(parents=True, exist_ok=True)
    status_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    status_json.with_suffix(".md").write_text(render_demo_attach_watch_md(payload), encoding="utf-8")


def _update_pointer(pointer_path: Path, pointer: dict[str, Any], payload: dict[str, Any]) -> None:
    if not pointer:
        return
    pointer["c31_demo_attach_watch_report"] = payload["outputs"]["status_report_json"]
    pointer["c31_demo_attach_watch_status"] = payload["status"]
    pointer["c31_attach_runtime_files_present_all_accounts"] = payload["status"] == "ATTACH_RUNTIME_FILES_PRESENT_ALL_ACCOUNTS"
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
