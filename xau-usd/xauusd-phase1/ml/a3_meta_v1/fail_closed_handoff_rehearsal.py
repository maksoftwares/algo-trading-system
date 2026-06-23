from __future__ import annotations

import csv
import json
import shutil
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from .account_registry import MT5AccountSpec, load_mt5_account_registry
from .market_data_export import _sha256_file, _table, _utc_now, _write_json_atomic


DEFAULT_STATUS_JSON = Path("outputs") / "reports" / "A3_ML_FAIL_CLOSED_HANDOFF_REHEARSAL_STATUS.json"
DEFAULT_STAGING_DIR = Path("outputs") / "reports" / "ea_handoff_rehearsal"
DEFAULT_TERMINAL_FILE_NAME = "A3_ML_EA_HANDOFF.csv"
HANDOFF_SCHEMA_VERSION = "a3_ml_ea_handoff_v1"
SCHEMA_VERSION = "a3_ml_fail_closed_handoff_rehearsal_status_v1"
EXPECTED_ACCOUNTS = ("1025742", "1033030", "1033669")


def publish_fail_closed_handoff_rehearsal(
    root: Path,
    report_json: Path | None = None,
    *,
    publish: bool = False,
    terminal_file_name: str = DEFAULT_TERMINAL_FILE_NAME,
) -> Path:
    root = root.resolve()
    report_json = (report_json or root / DEFAULT_STATUS_JSON).resolve()
    registry = load_mt5_account_registry(root / "config" / "ml" / "mt5_accounts.yaml")
    pointer = _read_json(root / "outputs" / "reports" / "C02_DATASET_POINTER.json")
    readiness = _read_json(root / "outputs" / "reports" / "C03_TRAINING_READINESS_REPORT.json")
    accounts = list(registry.accounts)
    validations = _validations(accounts, terminal_file_name)
    ready = all(item["passed"] for item in validations)
    generated_at = datetime.now(timezone.utc).replace(microsecond=0)
    rows = _fail_closed_rows(
        accounts=accounts,
        dataset_version=pointer.get("dataset_version", ""),
        generated_at=generated_at,
        readiness_status=readiness.get("status", "UNKNOWN"),
    )
    staged_files: list[dict[str, Any]] = []
    published_files: list[dict[str, Any]] = []
    if ready:
        staged_files = _write_staged_files(root / DEFAULT_STAGING_DIR, terminal_file_name, accounts, rows)
    publish_attempted = bool(publish and ready)
    if publish_attempted:
        published_files = _publish_to_terminal_files(staged_files, accounts, terminal_file_name)
    status = "PUBLISHED_FAIL_CLOSED_REHEARSAL" if published_files else ("READY_DRY_RUN" if ready else "REFUSED_UNSAFE")
    payload = {
        "status": status,
        "stage": "C13-FAIL-CLOSED-HANDOFF-REHEARSAL",
        "created_at_utc": _utc_now(),
        "schema_version": SCHEMA_VERSION,
        "dataset_version": pointer.get("dataset_version", ""),
        "readiness_status": readiness.get("status", "UNKNOWN"),
        "authorization": {
            "training_authorized": False,
            "python_demo_predictions_authorized": False,
            "ea_consumption_authorized": False,
            "mt5_file_publish_requested": bool(publish),
            "mt5_file_publish_attempted": publish_attempted,
            "broker_action_authorized": False,
        },
        "inputs": {
            "registry_path": str(root / "config" / "ml" / "mt5_accounts.yaml"),
            "pointer": str(root / "outputs" / "reports" / "C02_DATASET_POINTER.json"),
            "readiness_report": str(root / "outputs" / "reports" / "C03_TRAINING_READINESS_REPORT.json"),
        },
        "outputs": {
            "status_report_json": str(report_json),
            "status_report_md": str(report_json.with_suffix(".md")),
            "staging_dir": str(root / DEFAULT_STAGING_DIR),
            "terminal_file_name": terminal_file_name,
            "staged_files": staged_files,
            "published_files": published_files,
        },
        "accounts": [_account_payload(account) for account in accounts],
        "validations": validations,
        "boundary": {
            "mt5_connection_attempted": False,
            "terminal_runtime_change_authorized": False,
            "ea_file_drop_authorized": publish_attempted,
            "broker_action_authorized": False,
        },
        "next_allowed_stage": (
            "The passive observer can read fail-closed ABSTAIN handoff rows from all three MT5 Files roots. "
            "Real Python prediction authorization still requires C03 PASS, C05 TRAINED_SHADOW_ONLY, C04 READY_SHADOW_ONLY, and C06 publish."
            if published_files
            else "Run C13 with --publish to place fail-closed ABSTAIN rehearsal files in all three MT5 Files roots."
            if ready
            else "Fix unsafe registry or terminal file validation, then rerun C13."
        ),
    }
    _write_status(report_json, payload)
    _update_pointer(root / "outputs" / "reports" / "C02_DATASET_POINTER.json", pointer, payload)
    return report_json


def render_fail_closed_handoff_rehearsal_md(payload: dict[str, Any]) -> str:
    validations = [
        {"Check": item["check"], "Passed": str(item["passed"]).lower(), "Detail": item["detail"]}
        for item in payload.get("validations", [])
    ]
    accounts = [
        {
            "Account": item["account_label"],
            "Login": item["account_scope"],
            "Files roots": ", ".join(item["files_roots"]) or "missing",
        }
        for item in payload.get("accounts", [])
    ]
    published = payload.get("outputs", {}).get("published_files", [])
    published_lines = "\n".join(f"- {item['target_path']}" for item in published) if published else "- none"
    return "\n".join(
        [
            "# A3 ML Fail-Closed Handoff Rehearsal Status",
            "",
            f"Overall status: {payload['status']}",
            f"Dataset version: {payload.get('dataset_version', '')}",
            f"Readiness status: {payload.get('readiness_status', '')}",
            "",
            "## Authorization",
            "",
            "- Training authorized: false",
            "- Python demo predictions authorized: false",
            "- EA consumption authorized: false",
            f"- MT5 file publish requested: {str(payload['authorization']['mt5_file_publish_requested']).lower()}",
            f"- MT5 file publish attempted: {str(payload['authorization']['mt5_file_publish_attempted']).lower()}",
            "- Broker action authorized: false",
            "",
            "## Accounts",
            "",
            _table(accounts, ["Account", "Login", "Files roots"]) if accounts else "No accounts configured.",
            "",
            "## Validations",
            "",
            _table(validations, ["Check", "Passed", "Detail"]) if validations else "No validations ran.",
            "",
            "## Published Files",
            "",
            published_lines,
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


def _validations(accounts: list[MT5AccountSpec], terminal_file_name: str) -> list[dict[str, Any]]:
    scopes = tuple(account.account_scope for account in accounts)
    return [
        _check("expected_accounts_configured", scopes == EXPECTED_ACCOUNTS, f"configured={','.join(scopes)}"),
        _check("all_accounts_have_files_roots", all(account.files_roots for account in accounts), _files_root_detail(accounts)),
        _check(
            "files_roots_are_mql5_files",
            all(_is_mql5_files_root(Path(root)) for account in accounts for root in account.files_roots),
            _files_root_detail(accounts),
        ),
        _check("terminal_file_name_safe", _terminal_file_name_safe(terminal_file_name), terminal_file_name),
    ]


def _fail_closed_rows(
    *,
    accounts: list[MT5AccountSpec],
    dataset_version: str,
    generated_at: datetime,
    readiness_status: str,
) -> list[dict[str, str]]:
    expires_at = generated_at + timedelta(days=7)
    rows = []
    for account in accounts:
        rows.append(
            {
                "schema_version": HANDOFF_SCHEMA_VERSION,
                "generated_at_utc": _fmt(generated_at),
                "expires_at_utc": _fmt(expires_at),
                "dataset_version": dataset_version,
                "account_scope": account.account_scope,
                "account_label": account.account_label,
                "symbol": account.symbol,
                "exact_signal_id": f"C13_FAIL_CLOSED_REHEARSAL_{account.account_label}",
                "setup_group_id": "C13_FAIL_CLOSED_REHEARSAL",
                "decision_time_utc": _fmt(generated_at),
                "direction": "",
                "p_win_calibrated": "",
                "threshold": "",
                "action": "ABSTAIN",
                "reason": f"C13_FAIL_CLOSED_REHEARSAL_C03_{readiness_status}",
                "model_id": "",
                "model_hash": "",
                "feature_schema_hash": "",
                "drift_status": "ML_HANDOFF_REHEARSAL_FAIL_CLOSED",
                "broker_action_authorized": "false",
            }
        )
    return rows


def _write_staged_files(
    staging_dir: Path,
    terminal_file_name: str,
    accounts: list[MT5AccountSpec],
    rows: list[dict[str, str]],
) -> list[dict[str, Any]]:
    staging_dir.mkdir(parents=True, exist_ok=True)
    output = []
    for account in accounts:
        account_rows = [row for row in rows if row["account_scope"] == account.account_scope]
        path = staging_dir / f"{account.account_label}_{terminal_file_name}"
        _write_csv(path, account_rows, _handoff_fields())
        output.append(
            {
                "account_label": account.account_label,
                "account_scope": account.account_scope,
                "path": str(path),
                "rows": len(account_rows),
                "sha256": _sha256_file(path),
            }
        )
    return output


def _publish_to_terminal_files(
    staged_files: list[dict[str, Any]],
    accounts: list[MT5AccountSpec],
    terminal_file_name: str,
) -> list[dict[str, Any]]:
    by_label = {item["account_label"]: item for item in staged_files}
    published = []
    for account in accounts:
        staged = by_label.get(account.account_label)
        if not staged:
            continue
        source = Path(staged["path"])
        for files_root_text in account.files_roots:
            files_root = Path(files_root_text)
            if not _is_mql5_files_root(files_root):
                raise ValueError(f"unsafe MT5 files root for {account.account_label}: {files_root}")
            files_root.mkdir(parents=True, exist_ok=True)
            target = files_root / terminal_file_name
            shutil.copy2(source, target)
            published.append(
                {
                    "account_label": account.account_label,
                    "account_scope": account.account_scope,
                    "target_path": str(target),
                    "rows": staged["rows"],
                    "sha256": _sha256_file(target),
                }
            )
    return published


def _handoff_fields() -> list[str]:
    return [
        "schema_version",
        "generated_at_utc",
        "expires_at_utc",
        "dataset_version",
        "account_scope",
        "account_label",
        "symbol",
        "exact_signal_id",
        "setup_group_id",
        "decision_time_utc",
        "direction",
        "p_win_calibrated",
        "threshold",
        "action",
        "reason",
        "model_id",
        "model_hash",
        "feature_schema_hash",
        "drift_status",
        "broker_action_authorized",
    ]


def _write_status(status_json: Path, payload: dict[str, Any]) -> None:
    status_json.parent.mkdir(parents=True, exist_ok=True)
    status_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    status_json.with_suffix(".md").write_text(render_fail_closed_handoff_rehearsal_md(payload), encoding="utf-8")


def _update_pointer(pointer_path: Path, pointer: dict[str, Any], payload: dict[str, Any]) -> None:
    if not pointer:
        return
    pointer["c13_fail_closed_handoff_rehearsal_status_report"] = payload["outputs"]["status_report_json"]
    pointer["c13_fail_closed_handoff_rehearsal_status"] = payload["status"]
    pointer["python_demo_predictions_authorized"] = False
    pointer["ea_consumption_authorized"] = False
    pointer["broker_action_authorized"] = False
    _write_json_atomic(pointer_path, pointer)


def _write_csv(path: Path, rows: list[dict[str, str]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def _account_payload(account: MT5AccountSpec) -> dict[str, Any]:
    return {
        "account_label": account.account_label,
        "account_scope": account.account_scope,
        "role": account.role,
        "files_roots": list(account.files_roots),
    }


def _check(check: str, passed: bool, detail: str) -> dict[str, Any]:
    return {"check": check, "passed": bool(passed), "detail": detail}


def _files_root_detail(accounts: list[MT5AccountSpec]) -> str:
    return "; ".join(f"{account.account_label}={','.join(account.files_roots) or 'missing'}" for account in accounts)


def _terminal_file_name_safe(value: str) -> bool:
    path = Path(value)
    return path.name == value and value.lower().endswith(".csv") and ".." not in value


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


def _fmt(value: datetime) -> str:
    return value.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
