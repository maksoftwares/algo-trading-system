from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from .account_registry import MT5AccountSpec, load_mt5_account_registry
from .market_data_export import _table, _utc_now, _write_json_atomic


DEFAULT_STATUS_JSON = Path("outputs") / "reports" / "A3_ML_RUNTIME_LAUNCH_DIAGNOSTIC_STATUS.json"
SCHEMA_VERSION = "a3_ml_runtime_launch_diagnostic_status_v1"
STARTUP_CONFIG_NAME = "a3_ml_prediction_observer_startup.ini"
OBSERVER_NAME = "A3MlPredictionObserver"
OBSERVER_PRESET = "A3MlPredictionObserver.passive_xauusd.set"
LOG_PATTERNS = re.compile(
    r"A3MlPredictionObserver|a3_ml_prediction|A3_ML_EA_HANDOFF|a3_ml_broker_shadow_tap|startup\.ini|"
    r"cannot|failed|error",
    re.IGNORECASE,
)


def diagnose_runtime_launch(root: Path, report_json: Path | None = None) -> Path:
    root = root.resolve()
    report_json = (report_json or root / DEFAULT_STATUS_JSON).resolve()
    registry = load_mt5_account_registry(root / "config" / "ml" / "mt5_accounts.yaml")
    pointer = _read_json(root / "outputs" / "reports" / "C02_DATASET_POINTER.json")
    c14 = _read_json(root / "outputs" / "reports" / "A3_ML_OBSERVER_RUNTIME_ATTACH_STATUS.json")
    c20 = _read_json(root / "outputs" / "reports" / "A3_ML_RUNTIME_EVIDENCE_STATUS.json")
    accounts = [_account_diagnostic(account) for account in registry.accounts]
    validations = _validations(accounts)
    status = _status(c14, c20, accounts, validations)
    payload = {
        "status": status,
        "stage": "C21-ML-RUNTIME-LAUNCH-DIAGNOSTIC",
        "created_at_utc": _utc_now(),
        "schema_version": SCHEMA_VERSION,
        "dataset_version": pointer.get("dataset_version", ""),
        "authorization": {
            "python_demo_predictions_authorized": False,
            "ea_consumption_authorized": False,
            "broker_action_authorized": False,
        },
        "upstream_statuses": {
            "c14_observer_runtime_attach": c14.get("status", "MISSING"),
            "c20_runtime_evidence": c20.get("status", "MISSING"),
        },
        "diagnostic_summary": {
            "startup_configs_safe_all_accounts": all(item["startup_config"]["safe_passive_config"] for item in accounts),
            "observer_log_mentions_all_accounts": all(item["log_scan"]["observer_mentions"] > 0 for item in accounts),
            "observer_log_mentions_any_account": any(item["log_scan"]["observer_mentions"] > 0 for item in accounts),
            "error_mentions_any_account": any(item["log_scan"]["error_mentions"] > 0 for item in accounts),
        },
        "inputs": {
            "registry_path": str(root / "config" / "ml" / "mt5_accounts.yaml"),
            "c14_runtime_attach": str(root / "outputs" / "reports" / "A3_ML_OBSERVER_RUNTIME_ATTACH_STATUS.json"),
            "c20_runtime_evidence": str(root / "outputs" / "reports" / "A3_ML_RUNTIME_EVIDENCE_STATUS.json"),
        },
        "outputs": {
            "status_report_json": str(report_json),
            "status_report_md": str(report_json.with_suffix(".md")),
        },
        "accounts": accounts,
        "validations": validations,
        "boundary": {
            "mt5_connection_attempted": False,
            "data_export_attempted": False,
            "terminal_runtime_launch_attempted": False,
            "terminal_shutdown_attempted": False,
            "profile_or_chart_file_write_attempted": False,
            "ea_file_drop_authorized": False,
            "broker_action_authorized": False,
        },
        "next_allowed_stage": _next_allowed_stage(status),
    }
    _write_status(report_json, payload)
    _update_pointer(root / "outputs" / "reports" / "C02_DATASET_POINTER.json", pointer, payload)
    return report_json


def render_runtime_launch_diagnostic_md(payload: dict[str, Any]) -> str:
    accounts = [
        {
            "Account": item["account_label"],
            "Config safe": str(item["startup_config"]["safe_passive_config"]).lower(),
            "Observer mentions": str(item["log_scan"]["observer_mentions"]),
            "Error mentions": str(item["log_scan"]["error_mentions"]),
            "Files checked": str(item["log_scan"]["files_checked"]),
        }
        for item in payload.get("accounts", [])
    ]
    validations = [
        {"Check": item["check"], "Passed": str(item["passed"]).lower(), "Detail": item["detail"]}
        for item in payload.get("validations", [])
    ]
    return "\n".join(
        [
            "# A3 ML Runtime Launch Diagnostic Status",
            "",
            f"Overall status: {payload['status']}",
            f"Dataset version: {payload.get('dataset_version', '')}",
            "",
            "## Upstream Statuses",
            "",
            f"- C14 observer runtime attach: {payload['upstream_statuses']['c14_observer_runtime_attach']}",
            f"- C20 runtime evidence: {payload['upstream_statuses']['c20_runtime_evidence']}",
            "",
            "## Diagnostic Summary",
            "",
            f"- Startup configs safe all accounts: {str(payload['diagnostic_summary']['startup_configs_safe_all_accounts']).lower()}.",
            f"- Observer log mentions all accounts: {str(payload['diagnostic_summary']['observer_log_mentions_all_accounts']).lower()}.",
            f"- Observer log mentions any account: {str(payload['diagnostic_summary']['observer_log_mentions_any_account']).lower()}.",
            f"- Error mentions any account: {str(payload['diagnostic_summary']['error_mentions_any_account']).lower()}.",
            "",
            "## Account Diagnostics",
            "",
            _table(accounts, ["Account", "Config safe", "Observer mentions", "Error mentions", "Files checked"])
            if accounts
            else "No accounts configured.",
            "",
            "## Validations",
            "",
            _table(validations, ["Check", "Passed", "Detail"]) if validations else "No validations ran.",
            "",
            "## Authorization",
            "",
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


def _account_diagnostic(account: MT5AccountSpec) -> dict[str, Any]:
    data_root = Path(account.expected_data_path or "")
    config_path = _config_dir(data_root) / STARTUP_CONFIG_NAME
    logs_dir = data_root / "Logs"
    mql5_logs_dir = data_root / "MQL5" / "Logs"
    return {
        "account_label": account.account_label,
        "account_scope": account.account_scope,
        "role": account.role,
        "data_root": str(data_root),
        "startup_config": _startup_config_payload(config_path),
        "log_scan": _scan_logs([logs_dir, mql5_logs_dir]),
    }


def _startup_config_payload(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""
    required = {
        "allow_live_trading_disabled": "AllowLiveTrading=0" in text,
        "observer_expert_set": f"Expert={OBSERVER_NAME}" in text,
        "passive_preset_set": f"ExpertParameters={OBSERVER_PRESET}" in text,
        "symbol_xauusd": "Symbol=XAUUSD" in text,
        "period_m5": "Period=M5" in text,
    }
    return {
        "path": str(path),
        "exists": path.exists(),
        "bytes": path.stat().st_size if path.exists() else 0,
        "safe_passive_config": all(required.values()),
        "checks": required,
    }


def _scan_logs(directories: list[Path]) -> dict[str, Any]:
    files = []
    for directory in directories:
        if directory.exists():
            files.extend(sorted(directory.glob("*.log"), key=lambda path: path.stat().st_mtime, reverse=True)[:5])
    matches = []
    error_mentions = 0
    observer_mentions = 0
    for file_path in files:
        for line in _safe_tail_lines(file_path, limit=600):
            if not LOG_PATTERNS.search(line):
                continue
            clean_line = line.strip()
            matches.append({"file": str(file_path), "line": clean_line})
            if re.search(r"A3MlPredictionObserver|a3_ml_prediction", clean_line, re.IGNORECASE):
                observer_mentions += 1
            if re.search(r"cannot|failed|error", clean_line, re.IGNORECASE):
                error_mentions += 1
    return {
        "files_checked": len(files),
        "observer_mentions": observer_mentions,
        "error_mentions": error_mentions,
        "matched_lines": matches[-40:],
    }


def _safe_tail_lines(path: Path, *, limit: int) -> list[str]:
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return []
    return lines[-limit:]


def _validations(accounts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    checks = []
    for account in accounts:
        prefix = account["account_label"]
        config = account["startup_config"]
        checks.append(_check(f"{prefix}_startup_config_exists", bool(config["exists"]), config["path"]))
        checks.append(_check(f"{prefix}_startup_config_safe_passive", bool(config["safe_passive_config"]), json.dumps(config["checks"], sort_keys=True)))
    return checks


def _status(
    c14: dict[str, Any],
    c20: dict[str, Any],
    accounts: list[dict[str, Any]],
    validations: list[dict[str, Any]],
) -> str:
    if any(not item["passed"] for item in validations):
        return "PREFLIGHT_BLOCKED"
    if c20.get("status") == "RUNTIME_EVIDENCE_PRESENT_ALL_ACCOUNTS":
        return "RUNTIME_EVIDENCE_PRESENT_ALL_ACCOUNTS"
    if c14.get("authorization", {}).get("runtime_launch_attempted") is True:
        if any(item["log_scan"]["observer_mentions"] > 0 for item in accounts):
            return "LAUNCH_SENT_WITH_PARTIAL_JOURNAL_EVIDENCE"
        return "LAUNCH_SENT_NO_OBSERVER_JOURNAL_EVIDENCE"
    return "READY_FOR_MANUAL_ATTACH_OR_LAUNCH_RETRY"


def _next_allowed_stage(status: str) -> str:
    if status == "RUNTIME_EVIDENCE_PRESENT_ALL_ACCOUNTS":
        return "Runtime evidence is present. Continue data collection and rerun C19 after market data advances."
    if status == "LAUNCH_SENT_WITH_PARTIAL_JOURNAL_EVIDENCE":
        return "Inspect the matched journal lines, attach missing accounts manually, then run C22 to wait for C20/C21 runtime evidence."
    if status == "LAUNCH_SENT_NO_OBSERVER_JOURNAL_EVIDENCE":
        return "The startup config is safe, but MT5 did not show observer startup evidence. Attach A3MlPredictionObserver manually on XAUUSD M5 for A1/A2/A3, then run C22 to wait for C20/C21 runtime evidence."
    if status == "READY_FOR_MANUAL_ATTACH_OR_LAUNCH_RETRY":
        return "Run C14 with --launch or manually attach the passive observer, then run C22 to wait for C20/C21 runtime evidence."
    return "Fix missing or unsafe startup configs, then rerun C14/C21."


def _config_dir(data_root: Path) -> Path:
    if (data_root / "Config").exists():
        return data_root / "Config"
    if (data_root / "config").exists():
        return data_root / "config"
    return data_root / "Config"


def _write_status(status_json: Path, payload: dict[str, Any]) -> None:
    status_json.parent.mkdir(parents=True, exist_ok=True)
    status_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    status_json.with_suffix(".md").write_text(render_runtime_launch_diagnostic_md(payload), encoding="utf-8")


def _update_pointer(pointer_path: Path, pointer: dict[str, Any], payload: dict[str, Any]) -> None:
    if not pointer:
        return
    pointer["c21_runtime_launch_diagnostic_report"] = payload["outputs"]["status_report_json"]
    pointer["c21_runtime_launch_diagnostic_status"] = payload["status"]
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
