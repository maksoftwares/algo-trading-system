from __future__ import annotations

import csv
import json
import shutil
from pathlib import Path
from typing import Any

from .account_registry import MT5AccountSpec, load_mt5_account_registry
from .market_data_export import _sha256_file, _table, _utc_now, _write_json_atomic


DEFAULT_CONTRACT = Path("config") / "ml" / "a3_ml_ea_handoff_contract.json"
DEFAULT_STATUS_JSON = Path("outputs") / "reports" / "A3_ML_EA_HANDOFF_STATUS.json"
HANDOFF_SCHEMA_VERSION = "a3_ml_ea_handoff_v1"


def generate_ea_handoff_report(root: Path, contract_path: Path | None = None, *, publish: bool = False) -> Path:
    root = root.resolve()
    contract_path = (contract_path or root / DEFAULT_CONTRACT).resolve()
    contract = _read_json(contract_path)
    registry = load_mt5_account_registry(root / contract.get("registry_path", "config/ml/mt5_accounts.yaml"))
    bridge_status_path = (root / contract.get("shadow_bridge_status_json", "outputs/reports/A3_ML_SHADOW_BRIDGE_STATUS.json")).resolve()
    predictions_path = (root / contract.get("shadow_predictions_csv", "outputs/reports/A3_ML_SHADOW_PREDICTIONS.csv")).resolve()
    status_json = (root / contract.get("status_report_json", str(DEFAULT_STATUS_JSON))).resolve()
    staging_dir = (root / contract.get("staging_dir", "outputs/reports/ea_handoff")).resolve()
    terminal_file_name = str(contract.get("terminal_file_name", "A3_ML_EA_HANDOFF.csv"))
    pointer_path = root / "outputs" / "reports" / "C02_DATASET_POINTER.json"
    bridge_status = _read_json(bridge_status_path)
    predictions = _read_csv(predictions_path)
    pointer = _read_json(pointer_path)
    allowed_accounts = [str(value) for value in contract.get("allowed_accounts", [])]
    accounts = [account for account in registry.accounts if account.account_scope in allowed_accounts]
    validations = _validations(
        contract=contract,
        bridge_status=bridge_status,
        predictions=predictions,
        predictions_path=predictions_path,
        accounts=accounts,
        terminal_file_name=terminal_file_name,
    )
    ready = all(item["passed"] for item in validations)
    publish_attempted = bool(publish and ready)
    staged_files: list[dict[str, Any]] = []
    published_files: list[dict[str, Any]] = []
    if ready:
        staged_files = _write_staged_files(staging_dir, terminal_file_name, accounts, predictions)
    if publish_attempted:
        published_files = _publish_to_terminal_files(staged_files, accounts, terminal_file_name)
    status = "PUBLISHED_TO_MT5_FILES" if published_files else ("READY_DRY_RUN" if ready else "REFUSED_NOT_READY")
    payload = {
        "status": status,
        "stage": "C06-EA-HANDOFF",
        "created_at_utc": _utc_now(),
        "schema_version": HANDOFF_SCHEMA_VERSION,
        "dataset_version": bridge_status.get("dataset_version", pointer.get("dataset_version", "")),
        "authorization": {
            "python_demo_predictions_authorized": ready,
            "ea_consumption_authorized": ready,
            "mt5_file_publish_requested": bool(publish),
            "mt5_file_publish_attempted": publish_attempted,
            "broker_action_authorized": False,
        },
        "inputs": {
            "contract": str(contract_path),
            "shadow_bridge_status": str(bridge_status_path),
            "shadow_predictions_csv": str(predictions_path),
            "registry_path": str(root / contract.get("registry_path", "config/ml/mt5_accounts.yaml")),
        },
        "outputs": {
            "status_report_json": str(status_json),
            "status_report_md": str(status_json.with_suffix(".md")),
            "staging_dir": str(staging_dir),
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
            "Attach or configure an EA to read the terminal file in shadow mode only; broker action remains false."
            if ready
            else "Wait for C03 PASS, C05 TRAINED_SHADOW_ONLY, and C04 READY_SHADOW_ONLY, then rerun C06."
        ),
    }
    _write_status(status_json, payload)
    _update_pointer(pointer_path, pointer, payload)
    return status_json


def render_ea_handoff_status_md(payload: dict[str, Any]) -> str:
    rows = [
        {
            "Check": item["check"],
            "Passed": str(item["passed"]).lower(),
            "Detail": item["detail"],
        }
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
            "# A3 ML EA Handoff Status",
            "",
            f"Overall status: {payload['status']}",
            "",
            "## Authorization",
            "",
            f"- Python demo predictions authorized: {str(payload['authorization']['python_demo_predictions_authorized']).lower()}",
            f"- EA consumption authorized: {str(payload['authorization']['ea_consumption_authorized']).lower()}",
            f"- MT5 file publish requested: {str(payload['authorization']['mt5_file_publish_requested']).lower()}",
            f"- MT5 file publish attempted: {str(payload['authorization']['mt5_file_publish_attempted']).lower()}",
            f"- Broker action authorized: {str(payload['authorization']['broker_action_authorized']).lower()}",
            "",
            "## Accounts",
            "",
            _table(accounts, ["Account", "Login", "Files roots"]) if accounts else "No accounts configured.",
            "",
            "## Validations",
            "",
            _table(rows, ["Check", "Passed", "Detail"]) if rows else "No validations ran.",
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


def _validations(
    *,
    contract: dict[str, Any],
    bridge_status: dict[str, Any],
    predictions: list[dict[str, str]],
    predictions_path: Path,
    accounts: list[MT5AccountSpec],
    terminal_file_name: str,
) -> list[dict[str, Any]]:
    allowed_accounts = [str(value) for value in contract.get("allowed_accounts", [])]
    allowed_actions = set(str(value) for value in contract.get("allowed_actions", []))
    bridge_authorization = bridge_status.get("authorization", {})
    bridge_outputs = bridge_status.get("outputs", {})
    prediction_actions = {row.get("action", "") for row in predictions}
    prediction_accounts = {row.get("account_scope", "") for row in predictions}
    expected_sha = bridge_outputs.get("predictions_sha256", "")
    observed_sha = _sha256_file(predictions_path) if predictions_path.exists() else ""
    checks = [
        _check(
            "shadow_bridge_ready",
            bridge_status.get("status") == "READY_SHADOW_ONLY",
            f"observed={bridge_status.get('status', 'MISSING')} required=READY_SHADOW_ONLY",
        ),
        _check(
            "bridge_authorizes_ea_consumption",
            bridge_authorization.get("ea_consumption_authorized") is True,
            f"observed={bridge_authorization.get('ea_consumption_authorized', 'MISSING')} required=true",
        ),
        _check(
            "bridge_blocks_broker_action",
            bridge_authorization.get("broker_action_authorized") is False,
            f"observed={bridge_authorization.get('broker_action_authorized', 'MISSING')} required=false",
        ),
        _check("predictions_file_exists", predictions_path.exists(), str(predictions_path)),
        _check("predictions_hash_matches_bridge", bool(expected_sha) and observed_sha == expected_sha, f"observed={observed_sha} expected={expected_sha}"),
        _check("predictions_not_empty", bool(predictions), f"rows={len(predictions)}"),
        _check("prediction_actions_allowed", prediction_actions <= allowed_actions, f"observed={','.join(sorted(prediction_actions)) or 'none'}"),
        _check("prediction_accounts_allowed", prediction_accounts <= set(allowed_accounts), f"observed={','.join(sorted(prediction_accounts)) or 'none'}"),
        _check("all_allowed_accounts_configured", {account.account_scope for account in accounts} == set(allowed_accounts), f"configured={','.join(account.account_scope for account in accounts)}"),
        _check("all_accounts_have_files_roots", all(account.files_roots for account in accounts), _files_root_detail(accounts)),
        _check("terminal_file_name_safe", _terminal_file_name_safe(terminal_file_name), terminal_file_name),
    ]
    return checks


def _write_staged_files(
    staging_dir: Path,
    terminal_file_name: str,
    accounts: list[MT5AccountSpec],
    predictions: list[dict[str, str]],
) -> list[dict[str, Any]]:
    staging_dir.mkdir(parents=True, exist_ok=True)
    fields = _handoff_fields()
    output = []
    for account in accounts:
        rows = [_handoff_row(row) for row in predictions if row.get("account_scope") == account.account_scope]
        path = staging_dir / f"{account.account_label}_{terminal_file_name}"
        _write_csv(path, rows, fields)
        output.append(
            {
                "account_label": account.account_label,
                "account_scope": account.account_scope,
                "path": str(path),
                "rows": len(rows),
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


def _handoff_row(row: dict[str, str]) -> dict[str, str]:
    return {
        "schema_version": HANDOFF_SCHEMA_VERSION,
        "generated_at_utc": row.get("generated_at_utc", ""),
        "expires_at_utc": row.get("expires_at_utc", ""),
        "dataset_version": row.get("dataset_version", ""),
        "account_scope": row.get("account_scope", ""),
        "account_label": row.get("account_label", ""),
        "symbol": row.get("symbol", ""),
        "exact_signal_id": row.get("exact_signal_id", ""),
        "setup_group_id": row.get("setup_group_id", ""),
        "decision_time_utc": row.get("decision_time_utc", ""),
        "direction": row.get("direction", ""),
        "p_win_calibrated": row.get("p_win_calibrated", ""),
        "threshold": row.get("threshold", ""),
        "action": row.get("action", "ABSTAIN"),
        "reason": row.get("reason", ""),
        "model_id": row.get("model_id", ""),
        "model_hash": row.get("model_hash", ""),
        "feature_schema_hash": row.get("feature_schema_hash", ""),
        "drift_status": row.get("drift_status", ""),
        "broker_action_authorized": "false",
    }


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


def _write_status(status_json: Path, payload: dict[str, Any]) -> None:
    status_json.parent.mkdir(parents=True, exist_ok=True)
    status_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    status_json.with_suffix(".md").write_text(render_ea_handoff_status_md(payload), encoding="utf-8")


def _update_pointer(pointer_path: Path, pointer: dict[str, Any], payload: dict[str, Any]) -> None:
    if not pointer:
        return
    pointer["c06_ea_handoff_status_report"] = payload["outputs"]["status_report_json"]
    pointer["c06_ea_handoff_status"] = payload["status"]
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


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _write_csv(path: Path, rows: list[dict[str, str]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
