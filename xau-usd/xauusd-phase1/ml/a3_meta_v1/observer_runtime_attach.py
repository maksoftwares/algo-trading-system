from __future__ import annotations

import json
import subprocess
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .account_registry import MT5AccountSpec, load_mt5_account_registry
from .market_data_export import _table, _utc_now, _write_json_atomic


DEFAULT_STATUS_JSON = Path("outputs") / "reports" / "A3_ML_OBSERVER_RUNTIME_ATTACH_STATUS.json"
SCHEMA_VERSION = "a3_ml_observer_runtime_attach_status_v1"
EXPERT_NAME = "A3MlPredictionObserver"
PRESET_NAME = "A3MlPredictionObserver.passive_xauusd.set"
STARTUP_CONFIG_NAME = "a3_ml_prediction_observer_startup.ini"
HANDOFF_FILE_NAME = "A3_ML_EA_HANDOFF.csv"
STARTUP_LOG_NAME = "a3_ml_prediction_observer_startup.csv"
PREDICTION_LOG_NAME = "a3_ml_prediction_observer_log.csv"


@dataclass(frozen=True)
class RuntimeTarget:
    account: MT5AccountSpec
    data_root: Path
    terminal_exe: Path
    config_path: Path
    preset_path: Path
    ex5_path: Path
    handoff_path: Path
    startup_log_path: Path
    prediction_log_path: Path


def launch_prediction_observer_runtime(
    root: Path,
    report_json: Path | None = None,
    *,
    launch: bool = False,
    wait_seconds: int = 45,
) -> Path:
    root = root.resolve()
    report_json = (report_json or root / DEFAULT_STATUS_JSON).resolve()
    registry = load_mt5_account_registry(root / "config" / "ml" / "mt5_accounts.yaml")
    pointer = _read_json(root / "outputs" / "reports" / "C02_DATASET_POINTER.json")
    targets = [_runtime_target(account) for account in registry.accounts]
    validations = _validations(targets)
    ready = all(item["passed"] for item in validations)
    configs_written: list[dict[str, Any]] = []
    launch_records: list[dict[str, Any]] = []
    launched_at: datetime | None = None

    if ready:
        configs_written = [_write_startup_config(target) for target in targets]

    if launch and ready:
        launched_at = datetime.now(timezone.utc).replace(microsecond=0)
        launch_records = [_launch_terminal(target) for target in targets]
        _wait_for_logs(targets, launched_at, wait_seconds)

    logs = [_log_payload(target, launched_at) for target in targets]
    startup_all = all(item["startup_log_fresh_after_launch"] for item in logs) if launched_at else all(item["startup_log_exists"] for item in logs)
    prediction_all = (
        all(item["prediction_log_fresh_after_launch"] for item in logs)
        if launched_at
        else all(item["prediction_log_exists"] for item in logs)
    )

    if not ready:
        status = "PREFLIGHT_BLOCKED"
    elif launch and startup_all and prediction_all:
        status = "RUNTIME_LOGS_DETECTED_ALL_ACCOUNTS"
    elif launch and startup_all:
        status = "STARTUP_LOGS_DETECTED_ALL_ACCOUNTS"
    elif launch:
        status = "LAUNCH_SENT_WAITING_FOR_LOGS"
    else:
        status = "PREFLIGHT_READY"

    payload = {
        "status": status,
        "stage": "C14-ML-OBSERVER-RUNTIME-ATTACH",
        "created_at_utc": _utc_now(),
        "schema_version": SCHEMA_VERSION,
        "dataset_version": pointer.get("dataset_version", ""),
        "authorization": {
            "runtime_launch_requested": bool(launch),
            "runtime_launch_attempted": bool(launch and ready),
            "python_demo_predictions_authorized": False,
            "ea_consumption_authorized": False,
            "broker_action_authorized": False,
        },
        "inputs": {
            "registry_path": str(root / "config" / "ml" / "mt5_accounts.yaml"),
            "observer_deploy_status": str(root / "outputs" / "reports" / "A3_ML_OBSERVER_DEPLOY_STATUS.json"),
            "fail_closed_handoff_rehearsal": str(root / "outputs" / "reports" / "A3_ML_FAIL_CLOSED_HANDOFF_REHEARSAL_STATUS.json"),
        },
        "outputs": {
            "status_report_json": str(report_json),
            "status_report_md": str(report_json.with_suffix(".md")),
            "configs_written": configs_written,
            "launch_records": launch_records,
            "logs": logs,
        },
        "accounts": [_account_payload(target) for target in targets],
        "validations": validations,
        "boundary": {
            "mt5_connection_attempted": False,
            "terminal_runtime_launch_attempted": bool(launch and ready),
            "terminal_shutdown_attempted": False,
            "profile_or_chart_file_write_attempted": False,
            "startup_config_write_attempted": bool(ready),
            "allow_live_trading_in_startup_config": False,
            "broker_action_authorized": False,
        },
        "next_allowed_stage": _next_allowed_stage(status),
    }
    _write_status(report_json, payload)
    _update_pointer(root / "outputs" / "reports" / "C02_DATASET_POINTER.json", pointer, payload)
    return report_json


def render_observer_runtime_attach_md(payload: dict[str, Any]) -> str:
    validations = [
        {"Check": item["check"], "Passed": str(item["passed"]).lower(), "Detail": item["detail"]}
        for item in payload.get("validations", [])
    ]
    accounts = [
        {
            "Account": item["account_label"],
            "Login": item["account_scope"],
            "Config": item["startup_config"],
            "Files": item["files_root"],
        }
        for item in payload.get("accounts", [])
    ]
    logs = [
        {
            "Account": item["account_label"],
            "Startup": str(item["startup_log_exists"]).lower(),
            "Prediction": str(item["prediction_log_exists"]).lower(),
            "Fresh startup": str(item["startup_log_fresh_after_launch"]).lower(),
            "Fresh prediction": str(item["prediction_log_fresh_after_launch"]).lower(),
        }
        for item in payload.get("outputs", {}).get("logs", [])
    ]
    return "\n".join(
        [
            "# A3 ML Observer Runtime Attach Status",
            "",
            f"Overall status: {payload['status']}",
            f"Dataset version: {payload.get('dataset_version', '')}",
            "",
            "## Authorization",
            "",
            f"- Runtime launch requested: {str(payload['authorization']['runtime_launch_requested']).lower()}",
            f"- Runtime launch attempted: {str(payload['authorization']['runtime_launch_attempted']).lower()}",
            "- Python demo predictions authorized: false",
            "- EA consumption authorized: false",
            "- Broker action authorized: false",
            "",
            "## Accounts",
            "",
            _table(accounts, ["Account", "Login", "Config", "Files"]) if accounts else "No accounts configured.",
            "",
            "## Validations",
            "",
            _table(validations, ["Check", "Passed", "Detail"]) if validations else "No validations ran.",
            "",
            "## Runtime Logs",
            "",
            _table(logs, ["Account", "Startup", "Prediction", "Fresh startup", "Fresh prediction"]) if logs else "No logs checked.",
            "",
            "## Boundary",
            "",
            "- MT5 connection attempted: false.",
            f"- Terminal runtime launch attempted: {str(payload['boundary']['terminal_runtime_launch_attempted']).lower()}.",
            "- Terminal shutdown attempted: false.",
            "- Profile or chart file write attempted: false.",
            f"- Startup config write attempted: {str(payload['boundary']['startup_config_write_attempted']).lower()}.",
            "- Startup config allows live trading: false.",
            "- Broker action authorized: false.",
            "",
            "## Next",
            "",
            payload["next_allowed_stage"],
            "",
        ]
    )


def _runtime_target(account: MT5AccountSpec) -> RuntimeTarget:
    if not account.expected_data_path:
        data_root = Path("")
    else:
        data_root = Path(account.expected_data_path)
    files_root = Path(account.files_roots[0]) if account.files_roots else data_root / "MQL5" / "Files"
    return RuntimeTarget(
        account=account,
        data_root=data_root,
        terminal_exe=Path(account.terminal_exe),
        config_path=_config_dir(data_root) / STARTUP_CONFIG_NAME,
        preset_path=data_root / "MQL5" / "Presets" / PRESET_NAME,
        ex5_path=data_root / "MQL5" / "Experts" / f"{EXPERT_NAME}.ex5",
        handoff_path=files_root / HANDOFF_FILE_NAME,
        startup_log_path=files_root / STARTUP_LOG_NAME,
        prediction_log_path=files_root / PREDICTION_LOG_NAME,
    )


def _config_dir(data_root: Path) -> Path:
    if (data_root / "Config").exists():
        return data_root / "Config"
    if (data_root / "config").exists():
        return data_root / "config"
    return data_root / "Config"


def _validations(targets: list[RuntimeTarget]) -> list[dict[str, Any]]:
    checks: list[dict[str, Any]] = []
    for target in targets:
        prefix = target.account.account_label
        checks.extend(
            [
                _check(f"{prefix}_terminal_exe_exists", target.terminal_exe.exists(), str(target.terminal_exe)),
                _check(f"{prefix}_data_root_exists", target.data_root.exists(), str(target.data_root)),
                _check(f"{prefix}_observer_ex5_exists", target.ex5_path.exists(), str(target.ex5_path)),
                _check(f"{prefix}_passive_preset_exists", target.preset_path.exists(), str(target.preset_path)),
                _check(f"{prefix}_handoff_file_exists", target.handoff_path.exists(), str(target.handoff_path)),
                _check(f"{prefix}_files_root_safe", _is_mql5_files_root(target.handoff_path.parent), str(target.handoff_path.parent)),
            ]
        )
    return checks


def _write_startup_config(target: RuntimeTarget) -> dict[str, Any]:
    target.config_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "[Common]",
        f"Login={target.account.expected_login}",
        "Server=Capital.ComMena-Demo",
        "ProxyEnable=0",
        "NewsEnable=0",
        "",
        "[Charts]",
        "MaxBars=999999999",
        "",
        "[Experts]",
        "AllowLiveTrading=0",
        "AllowDllImport=0",
        "Enabled=1",
        "Account=0",
        "Profile=0",
        "",
        "[StartUp]",
        f"Expert={EXPERT_NAME}",
        f"ExpertParameters={PRESET_NAME}",
        "Symbol=XAUUSD",
        "Period=M5",
        "ShutdownTerminal=0",
        "",
    ]
    target.config_path.write_text("\n".join(lines), encoding="utf-8")
    return {
        "account_label": target.account.account_label,
        "account_scope": target.account.account_scope,
        "path": str(target.config_path),
        "bytes": target.config_path.stat().st_size,
        "allow_live_trading": False,
        "expert": EXPERT_NAME,
        "preset": PRESET_NAME,
    }


def _launch_terminal(target: RuntimeTarget) -> dict[str, Any]:
    command = [str(target.terminal_exe)]
    if target.account.portable:
        command.append("/portable")
    command.append(f"/config:{target.config_path}")
    try:
        process = subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception as exc:
        return {
            "account_label": target.account.account_label,
            "account_scope": target.account.account_scope,
            "status": "LAUNCH_FAILED",
            "command": command,
            "detail": f"{type(exc).__name__}: {exc}",
        }
    return {
        "account_label": target.account.account_label,
        "account_scope": target.account.account_scope,
        "status": "LAUNCH_SENT",
        "pid": process.pid,
        "command": command,
        "detail": "",
    }


def _wait_for_logs(targets: list[RuntimeTarget], launched_at: datetime, wait_seconds: int) -> None:
    deadline = time.time() + max(wait_seconds, 0)
    while time.time() < deadline:
        states = [_log_payload(target, launched_at) for target in targets]
        if all(state["startup_log_fresh_after_launch"] and state["prediction_log_fresh_after_launch"] for state in states):
            return
        time.sleep(1)


def _log_payload(target: RuntimeTarget, launched_at: datetime | None) -> dict[str, Any]:
    return {
        "account_label": target.account.account_label,
        "account_scope": target.account.account_scope,
        "startup_log_path": str(target.startup_log_path),
        "startup_log_exists": target.startup_log_path.exists(),
        "startup_log_size": target.startup_log_path.stat().st_size if target.startup_log_path.exists() else 0,
        "startup_log_last_write_utc": _mtime_utc(target.startup_log_path),
        "startup_log_fresh_after_launch": _fresh_after(target.startup_log_path, launched_at),
        "prediction_log_path": str(target.prediction_log_path),
        "prediction_log_exists": target.prediction_log_path.exists(),
        "prediction_log_size": target.prediction_log_path.stat().st_size if target.prediction_log_path.exists() else 0,
        "prediction_log_last_write_utc": _mtime_utc(target.prediction_log_path),
        "prediction_log_fresh_after_launch": _fresh_after(target.prediction_log_path, launched_at),
    }


def _mtime_utc(path: Path) -> str:
    if not path.exists():
        return ""
    return datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _fresh_after(path: Path, launched_at: datetime | None) -> bool:
    if launched_at is None or not path.exists():
        return False
    modified = datetime.fromtimestamp(path.stat().st_mtime, timezone.utc)
    return modified >= launched_at.replace(microsecond=0)


def _write_status(status_json: Path, payload: dict[str, Any]) -> None:
    status_json.parent.mkdir(parents=True, exist_ok=True)
    status_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    status_json.with_suffix(".md").write_text(render_observer_runtime_attach_md(payload), encoding="utf-8")


def _update_pointer(pointer_path: Path, pointer: dict[str, Any], payload: dict[str, Any]) -> None:
    if not pointer:
        return
    pointer["c14_observer_runtime_attach_status_report"] = payload["outputs"]["status_report_json"]
    pointer["c14_observer_runtime_attach_status"] = payload["status"]
    pointer["python_demo_predictions_authorized"] = False
    pointer["ea_consumption_authorized"] = False
    pointer["broker_action_authorized"] = False
    _write_json_atomic(pointer_path, pointer)


def _account_payload(target: RuntimeTarget) -> dict[str, Any]:
    return {
        "account_label": target.account.account_label,
        "account_scope": target.account.account_scope,
        "terminal_exe": str(target.terminal_exe),
        "data_root": str(target.data_root),
        "startup_config": str(target.config_path),
        "files_root": str(target.handoff_path.parent),
    }


def _next_allowed_stage(status: str) -> str:
    if status == "RUNTIME_LOGS_DETECTED_ALL_ACCOUNTS":
        return "Passive observer runtime is logging on all three accounts. Keep collecting data; real Python predictions still require C03 PASS and C05/C04/C06 readiness."
    if status == "STARTUP_LOGS_DETECTED_ALL_ACCOUNTS":
        return "Observer startup is visible on all accounts. Wait for timer prediction logs, then rerun C14 without launch or with a short launch retry."
    if status == "LAUNCH_SENT_WAITING_FOR_LOGS":
        return "Launch was sent, but logs were not fresh on all accounts. Confirm the terminal accepted the startup config or attach the passive preset manually."
    if status == "PREFLIGHT_READY":
        return "Run C14 with --launch to ask each terminal to open XAUUSD M5 with the passive ML observer."
    return "Fix blocked preflight checks, rerun C09/C13 if needed, then rerun C14."


def _check(check: str, passed: bool, detail: str) -> dict[str, Any]:
    return {"check": check, "passed": bool(passed), "detail": detail}


def _is_mql5_files_root(path: Path) -> bool:
    parts = [part.casefold() for part in path.parts]
    return len(parts) >= 2 and parts[-2:] == ["mql5", "files"]


def _read_json(path_or_text: str | Path) -> dict[str, Any]:
    if not path_or_text:
        return {}
    path = Path(path_or_text)
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))
