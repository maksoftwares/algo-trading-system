from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .account_registry import MT5AccountSpec, load_mt5_account_registry
from .market_data_export import _table, _utc_now, _write_json_atomic


DEFAULT_STATUS_JSON = Path("outputs") / "reports" / "A3_ML_RUNTIME_EVIDENCE_STATUS.json"
SCHEMA_VERSION = "a3_ml_runtime_evidence_status_v1"
HANDOFF_FILE_NAME = "A3_ML_EA_HANDOFF.csv"
OBSERVER_STARTUP_LOG = "a3_ml_prediction_observer_startup.csv"
OBSERVER_PREDICTION_LOG = "a3_ml_prediction_observer_log.csv"
BROKER_SHADOW_TAP_LOG = "a3_ml_broker_shadow_tap.csv"


def audit_runtime_evidence(root: Path, report_json: Path | None = None) -> Path:
    root = root.resolve()
    report_json = (report_json or root / DEFAULT_STATUS_JSON).resolve()
    registry = load_mt5_account_registry(root / "config" / "ml" / "mt5_accounts.yaml")
    pointer = _read_json(root / "outputs" / "reports" / "C02_DATASET_POINTER.json")
    accounts = [_account_runtime_evidence(account) for account in registry.accounts]
    validations = _validations(accounts)
    status = _status(accounts, validations)
    payload = {
        "status": status,
        "stage": "C20-ML-RUNTIME-EVIDENCE",
        "created_at_utc": _utc_now(),
        "schema_version": SCHEMA_VERSION,
        "dataset_version": pointer.get("dataset_version", ""),
        "authorization": {
            "python_demo_predictions_authorized": False,
            "ea_consumption_authorized": False,
            "broker_action_authorized": False,
        },
        "runtime_evidence": {
            "handoff_files_all_accounts": all(item["handoff"]["exists"] for item in accounts),
            "passive_observer_runtime_all_accounts": all(_observer_runtime_present(item) for item in accounts),
            "broker_shadow_tap_runtime_all_accounts": all(item["broker_shadow_tap"]["exists"] for item in accounts),
            "any_runtime_evidence": any(_any_runtime_evidence(item) for item in accounts),
        },
        "inputs": {
            "registry_path": str(root / "config" / "ml" / "mt5_accounts.yaml"),
            "c10_activation_status": str(root / "outputs" / "reports" / "A3_ML_DEMO_PREDICTION_ACTIVATION_STATUS.json"),
            "c19_demo_start_cycle_status": str(root / "outputs" / "reports" / "A3_ML_DEMO_START_CYCLE_STATUS.json"),
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


def render_runtime_evidence_md(payload: dict[str, Any]) -> str:
    account_rows = []
    for item in payload.get("accounts", []):
        account_rows.append(
            {
                "Account": item.get("account_label", ""),
                "Handoff": _yes_no(item.get("handoff", {}).get("exists", False)),
                "Observer startup": _yes_no(item.get("observer_startup", {}).get("exists", False)),
                "Observer log": _yes_no(item.get("observer_prediction", {}).get("exists", False)),
                "Broker tap": _yes_no(item.get("broker_shadow_tap", {}).get("exists", False)),
            }
        )
    validation_rows = [
        {"Check": item["check"], "Passed": str(item["passed"]).lower(), "Detail": item["detail"]}
        for item in payload.get("validations", [])
    ]
    return "\n".join(
        [
            "# A3 ML Runtime Evidence Status",
            "",
            f"Overall status: {payload['status']}",
            f"Dataset version: {payload.get('dataset_version', '')}",
            "",
            "## Account Evidence",
            "",
            _table(account_rows, ["Account", "Handoff", "Observer startup", "Observer log", "Broker tap"])
            if account_rows
            else "No accounts configured.",
            "",
            "## Runtime Evidence",
            "",
            f"- Handoff files all accounts: {str(payload['runtime_evidence']['handoff_files_all_accounts']).lower()}.",
            f"- Passive observer runtime all accounts: {str(payload['runtime_evidence']['passive_observer_runtime_all_accounts']).lower()}.",
            f"- Broker shadow tap runtime all accounts: {str(payload['runtime_evidence']['broker_shadow_tap_runtime_all_accounts']).lower()}.",
            f"- Any runtime evidence: {str(payload['runtime_evidence']['any_runtime_evidence']).lower()}.",
            "",
            "## Validations",
            "",
            _table(validation_rows, ["Check", "Passed", "Detail"]) if validation_rows else "No validations ran.",
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


def _account_runtime_evidence(account: MT5AccountSpec) -> dict[str, Any]:
    files_root = Path(account.files_roots[0]) if account.files_roots else Path(account.expected_data_path or "") / "MQL5" / "Files"
    return {
        "account_label": account.account_label,
        "account_scope": account.account_scope,
        "role": account.role,
        "files_root": str(files_root),
        "files_root_exists": files_root.exists(),
        "files_root_safe": _is_mql5_files_root(files_root),
        "handoff": _file_evidence(files_root / HANDOFF_FILE_NAME),
        "observer_startup": _file_evidence(files_root / OBSERVER_STARTUP_LOG),
        "observer_prediction": _file_evidence(files_root / OBSERVER_PREDICTION_LOG),
        "broker_shadow_tap": _file_evidence(files_root / BROKER_SHADOW_TAP_LOG),
    }


def _file_evidence(path: Path) -> dict[str, Any]:
    rows, header, tail = _csv_summary(path)
    return {
        "path": str(path),
        "exists": path.exists(),
        "size": path.stat().st_size if path.exists() else 0,
        "last_write_utc": _mtime_utc(path),
        "csv_header": header,
        "csv_rows": rows,
        "tail": tail,
    }


def _csv_summary(path: Path) -> tuple[int, list[str], dict[str, str]]:
    if not path.exists():
        return 0, [], {}
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            rows = list(reader)
            return len(rows), list(reader.fieldnames or []), rows[-1] if rows else {}
    except (OSError, UnicodeDecodeError, csv.Error):
        return 0, [], {}


def _validations(accounts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    checks: list[dict[str, Any]] = []
    for account in accounts:
        prefix = account["account_label"]
        checks.extend(
            [
                _check(f"{prefix}_files_root_exists", bool(account["files_root_exists"]), account["files_root"]),
                _check(f"{prefix}_files_root_safe", bool(account["files_root_safe"]), account["files_root"]),
                _check(f"{prefix}_handoff_file_exists", bool(account["handoff"]["exists"]), account["handoff"]["path"]),
            ]
        )
    return checks


def _status(accounts: list[dict[str, Any]], validations: list[dict[str, Any]]) -> str:
    if any(not item["passed"] for item in validations):
        return "PREFLIGHT_BLOCKED"
    observer_all = all(_observer_runtime_present(account) for account in accounts)
    broker_all = all(account["broker_shadow_tap"]["exists"] for account in accounts)
    if observer_all and broker_all:
        return "RUNTIME_EVIDENCE_PRESENT_ALL_ACCOUNTS"
    if any(_any_runtime_evidence(account) for account in accounts):
        return "PARTIAL_RUNTIME_EVIDENCE_PRESENT"
    return "WAITING_FOR_MT5_RUNTIME_LOGS"


def _observer_runtime_present(account: dict[str, Any]) -> bool:
    return bool(account["observer_startup"]["exists"] and account["observer_prediction"]["exists"])


def _any_runtime_evidence(account: dict[str, Any]) -> bool:
    return bool(
        account["observer_startup"]["exists"]
        or account["observer_prediction"]["exists"]
        or account["broker_shadow_tap"]["exists"]
    )


def _next_allowed_stage(status: str) -> str:
    if status == "RUNTIME_EVIDENCE_PRESENT_ALL_ACCOUNTS":
        return "All three accounts show passive observer and broker shadow-tap runtime evidence. Continue data collection and run C19 when market data advances."
    if status == "PARTIAL_RUNTIME_EVIDENCE_PRESENT":
        return "Some accounts are logging. Attach/reload the passive observer and deployed broker EAs on the missing accounts, wait for a new M5 bar, then rerun C20."
    if status == "WAITING_FOR_MT5_RUNTIME_LOGS":
        return "Attach/reload the passive observer and deployed broker EAs on A1/A2/A3, wait for logs, then rerun C20."
    return "Fix missing MT5 Files roots or handoff files, then rerun C13/C15/C20."


def _write_status(status_json: Path, payload: dict[str, Any]) -> None:
    status_json.parent.mkdir(parents=True, exist_ok=True)
    status_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    status_json.with_suffix(".md").write_text(render_runtime_evidence_md(payload), encoding="utf-8")


def _update_pointer(pointer_path: Path, pointer: dict[str, Any], payload: dict[str, Any]) -> None:
    if not pointer:
        return
    pointer["c20_runtime_evidence_status_report"] = payload["outputs"]["status_report_json"]
    pointer["c20_runtime_evidence_status"] = payload["status"]
    pointer["passive_observer_runtime_evidence_all_accounts"] = bool(
        payload["runtime_evidence"]["passive_observer_runtime_all_accounts"]
    )
    pointer["broker_shadow_tap_runtime_evidence_all_accounts"] = bool(
        payload["runtime_evidence"]["broker_shadow_tap_runtime_all_accounts"]
    )
    pointer["python_demo_predictions_authorized"] = False
    pointer["ea_consumption_authorized"] = False
    pointer["broker_action_authorized"] = False
    _write_json_atomic(pointer_path, pointer)


def _mtime_utc(path: Path) -> str:
    if not path.exists():
        return ""
    return datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _is_mql5_files_root(path: Path) -> bool:
    parts = [part.casefold() for part in path.parts]
    return len(parts) >= 2 and parts[-2:] == ["mql5", "files"]


def _yes_no(value: bool) -> str:
    return "yes" if value else "no"


def _check(check: str, passed: bool, detail: str) -> dict[str, Any]:
    return {"check": check, "passed": bool(passed), "detail": detail}


def _read_json(path_or_text: str | Path) -> dict[str, Any]:
    if not path_or_text:
        return {}
    path = Path(path_or_text)
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))
