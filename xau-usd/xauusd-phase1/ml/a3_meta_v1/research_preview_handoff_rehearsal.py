from __future__ import annotations

import csv
import json
import shutil
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from .account_registry import MT5AccountSpec, load_mt5_account_registry
from .market_data_export import _sha256_file, _table, _utc_now, _write_json_atomic


DEFAULT_STATUS_JSON = Path("outputs") / "reports" / "A3_ML_RESEARCH_PREVIEW_HANDOFF_REHEARSAL_STATUS.json"
DEFAULT_STAGING_DIR = Path("outputs") / "reports" / "ea_handoff_research_preview"
DEFAULT_PREVIEW_CSV = Path("outputs") / "reports" / "A3_ML_EXPLORATORY_SHADOW_PREVIEW.csv"
DEFAULT_ARTIFACT_JSON = Path("outputs") / "reports" / "A3_ML_EXPLORATORY_MODEL_REHEARSAL_ARTIFACT.json"
DEFAULT_TERMINAL_FILE_NAME = "A3_ML_EA_HANDOFF.csv"
HANDOFF_SCHEMA_VERSION = "a3_ml_ea_handoff_v1"
SCHEMA_VERSION = "a3_ml_research_preview_handoff_rehearsal_status_v1"
EXPECTED_ACCOUNTS = ("1025742", "1033030", "1033669")


def publish_research_preview_handoff_rehearsal(
    root: Path,
    report_json: Path | None = None,
    *,
    publish: bool = False,
    terminal_file_name: str = DEFAULT_TERMINAL_FILE_NAME,
) -> Path:
    root = root.resolve()
    report_json = (report_json or root / DEFAULT_STATUS_JSON).resolve()
    reports = root / "outputs" / "reports"
    registry = load_mt5_account_registry(root / "config" / "ml" / "mt5_accounts.yaml")
    pointer = _read_json(reports / "C02_DATASET_POINTER.json")
    c18 = _read_json(reports / "A3_ML_EXPLORATORY_TRAINING_REHEARSAL_STATUS.json")
    artifact_path = reports / DEFAULT_ARTIFACT_JSON.name
    preview_path = reports / DEFAULT_PREVIEW_CSV.name
    artifact = _read_json(artifact_path)
    preview_rows = _read_csv(preview_path)
    accounts = list(registry.accounts)
    validations = _validations(
        accounts=accounts,
        terminal_file_name=terminal_file_name,
        c18=c18,
        artifact=artifact,
        artifact_path=artifact_path,
        preview_path=preview_path,
        preview_rows=preview_rows,
    )
    ready = all(item["passed"] for item in validations)
    generated_at = datetime.now(timezone.utc).replace(microsecond=0)
    handoff_rows = (
        _handoff_rows(
            accounts=accounts,
            preview_rows=preview_rows,
            artifact=artifact,
            artifact_sha256=_sha256_file(artifact_path) if artifact_path.exists() else "",
            pointer=pointer,
            generated_at=generated_at,
        )
        if ready
        else []
    )
    staged_files: list[dict[str, Any]] = []
    published_files: list[dict[str, Any]] = []
    if ready:
        staged_files = _write_staged_files(root / DEFAULT_STAGING_DIR, terminal_file_name, accounts, handoff_rows)
    publish_attempted = bool(publish and ready)
    if publish_attempted:
        published_files = _publish_to_terminal_files(staged_files, accounts, terminal_file_name)
    status = (
        "PUBLISHED_RESEARCH_PREVIEW_FAIL_CLOSED"
        if published_files
        else ("READY_DRY_RUN" if ready else "REFUSED_NOT_READY")
    )
    payload = {
        "status": status,
        "stage": "C26-RESEARCH-PREVIEW-HANDOFF-REHEARSAL",
        "created_at_utc": _utc_now(),
        "schema_version": SCHEMA_VERSION,
        "dataset_version": pointer.get("dataset_version", artifact.get("dataset_version", "")),
        "authorization": {
            "official_model_training_authorized": False,
            "python_demo_predictions_authorized": False,
            "ea_consumption_authorized": False,
            "mt5_file_publish_requested": bool(publish),
            "mt5_file_publish_attempted": publish_attempted,
            "broker_action_authorized": False,
        },
        "quarantine": {
            "official_model_artifact": False,
            "eligible_for_c04_shadow_bridge": False,
            "eligible_for_c06_ea_handoff": False,
            "handoff_rows_force_abstain": True,
            "reason": "C26 only lets MT5 prove it can read Python-produced research preview rows while official C03/C05/C04/C06 gates remain closed.",
        },
        "inputs": {
            "registry_path": str(root / "config" / "ml" / "mt5_accounts.yaml"),
            "c18_exploratory_training_rehearsal": str(reports / "A3_ML_EXPLORATORY_TRAINING_REHEARSAL_STATUS.json"),
            "preview_csv": str(preview_path),
            "artifact_json": str(artifact_path),
        },
        "outputs": {
            "status_report_json": str(report_json),
            "status_report_md": str(report_json.with_suffix(".md")),
            "staging_dir": str(root / DEFAULT_STAGING_DIR),
            "terminal_file_name": terminal_file_name,
            "handoff_rows": len(handoff_rows),
            "staged_files": staged_files,
            "published_files": published_files,
        },
        "accounts": [_account_payload(account) for account in accounts],
        "validations": validations,
        "boundary": {
            "mt5_connection_attempted": False,
            "terminal_runtime_change_authorized": False,
            "profile_or_chart_file_write_attempted": False,
            "ea_file_drop_authorized": publish_attempted,
            "broker_action_authorized": False,
        },
        "next_allowed_stage": _next_allowed_stage(status),
    }
    _write_status(report_json, payload)
    _update_pointer(root / "outputs" / "reports" / "C02_DATASET_POINTER.json", pointer, payload)
    return report_json


def render_research_preview_handoff_rehearsal_md(payload: dict[str, Any]) -> str:
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
            "# A3 ML Research Preview Handoff Rehearsal Status",
            "",
            f"Overall status: {payload['status']}",
            f"Dataset version: {payload.get('dataset_version', '')}",
            "",
            "## Meaning",
            "",
            "This publishes only research-preview ABSTAIN rows. It is not the official model handoff and it does not authorize Python demo predictions, EA consumption, or broker action.",
            "",
            "## Authorization",
            "",
            "- Official model training authorized: false.",
            "- Python demo predictions authorized: false.",
            "- EA consumption authorized: false.",
            f"- MT5 file publish requested: {str(payload['authorization']['mt5_file_publish_requested']).lower()}.",
            f"- MT5 file publish attempted: {str(payload['authorization']['mt5_file_publish_attempted']).lower()}.",
            "- Broker action authorized: false.",
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
            "- Profile or chart file write attempted: false.",
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
    accounts: list[MT5AccountSpec],
    terminal_file_name: str,
    c18: dict[str, Any],
    artifact: dict[str, Any],
    artifact_path: Path,
    preview_path: Path,
    preview_rows: list[dict[str, str]],
) -> list[dict[str, Any]]:
    scopes = tuple(account.account_scope for account in accounts)
    preview_accounts = {row.get("account_scope", "") for row in preview_rows}
    account_scopes = {account.account_scope for account in accounts}
    return [
        _check("c18_rehearsed_research_only", c18.get("status") == "REHEARSED_RESEARCH_ONLY", c18.get("status", "MISSING")),
        _check(
            "c18_keeps_demo_authorization_false",
            c18.get("authorization", {}).get("python_demo_predictions_authorized") is False
            and c18.get("authorization", {}).get("ea_consumption_authorized") is False
            and c18.get("authorization", {}).get("broker_action_authorized") is False,
            "C18 authorization must remain false",
        ),
        _check("artifact_exists", artifact_path.exists(), str(artifact_path)),
        _check(
            "artifact_is_research_only",
            artifact.get("schema_version") == "a3_ml_exploratory_model_rehearsal_artifact_v1"
            and artifact.get("status") == "REHEARSED_RESEARCH_ONLY"
            and artifact.get("official_model_artifact") is False,
            artifact.get("status", "MISSING"),
        ),
        _check("preview_csv_exists", preview_path.exists(), str(preview_path)),
        _check("preview_rows_not_empty", bool(preview_rows), f"rows={len(preview_rows)}"),
        _check(
            "preview_rows_force_abstain",
            bool(preview_rows) and all(row.get("preview_action") == "ABSTAIN" for row in preview_rows),
            _preview_action_detail(preview_rows),
        ),
        _check(
            "preview_broker_action_false",
            bool(preview_rows) and all(str(row.get("broker_action_authorized", "")).lower() == "false" for row in preview_rows),
            _preview_broker_action_detail(preview_rows),
        ),
        _check("expected_accounts_configured", scopes == EXPECTED_ACCOUNTS, f"configured={','.join(scopes)}"),
        _check(
            "preview_accounts_allowed",
            preview_accounts <= account_scopes,
            f"observed={','.join(sorted(preview_accounts)) or 'none'} allowed={','.join(sorted(account_scopes))}",
        ),
        _check(
            "preview_covers_all_accounts",
            account_scopes <= preview_accounts,
            f"observed={','.join(sorted(preview_accounts)) or 'none'} required={','.join(sorted(account_scopes))}",
        ),
        _check("all_accounts_have_files_roots", all(account.files_roots for account in accounts), _files_root_detail(accounts)),
        _check(
            "files_roots_are_mql5_files",
            all(_is_mql5_files_root(Path(root)) for account in accounts for root in account.files_roots),
            _files_root_detail(accounts),
        ),
        _check("terminal_file_name_safe", _terminal_file_name_safe(terminal_file_name), terminal_file_name),
    ]


def _handoff_rows(
    *,
    accounts: list[MT5AccountSpec],
    preview_rows: list[dict[str, str]],
    artifact: dict[str, Any],
    artifact_sha256: str,
    pointer: dict[str, Any],
    generated_at: datetime,
) -> list[dict[str, str]]:
    expires_at = generated_at + timedelta(days=7)
    account_by_scope = {account.account_scope: account for account in accounts}
    rows: list[dict[str, str]] = []
    for row in preview_rows:
        account = account_by_scope.get(row.get("account_scope", ""))
        if account is None:
            continue
        rows.append(
            {
                "schema_version": HANDOFF_SCHEMA_VERSION,
                "generated_at_utc": _fmt(generated_at),
                "expires_at_utc": _fmt(expires_at),
                "dataset_version": row.get("dataset_version") or artifact.get("dataset_version") or pointer.get("dataset_version", ""),
                "account_scope": account.account_scope,
                "account_label": account.account_label,
                "symbol": row.get("symbol") or account.symbol,
                "exact_signal_id": row.get("source_signal_id", ""),
                "setup_group_id": row.get("setup_group_id", ""),
                "decision_time_utc": row.get("decision_time_utc", ""),
                "direction": row.get("direction", ""),
                "p_win_calibrated": row.get("p_win_rehearsal", ""),
                "threshold": "",
                "action": "ABSTAIN",
                "reason": "C26_RESEARCH_PREVIEW_NOT_AUTHORIZED_FOR_DEMO",
                "model_id": artifact.get("model_id", ""),
                "model_hash": artifact_sha256,
                "feature_schema_hash": artifact.get("feature_schema_hash", ""),
                "drift_status": "ML_RESEARCH_PREVIEW_FAIL_CLOSED",
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


def _next_allowed_stage(status: str) -> str:
    if status == "PUBLISHED_RESEARCH_PREVIEW_FAIL_CLOSED":
        return "Attach or reload the dry-run broker shadow consumers on XAUUSD M5. They should log ml_available=true with ABSTAIN research-preview rows; official Python demo prediction authority remains closed."
    if status == "READY_DRY_RUN":
        return "Run C26 with --publish only if you want MT5 to read research-preview ABSTAIN rows for a safe EA read-path rehearsal."
    return "Run C18 successfully first, then rerun C26. Do not use C26 rows as official model predictions."


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
    status_json.with_suffix(".md").write_text(render_research_preview_handoff_rehearsal_md(payload), encoding="utf-8")


def _update_pointer(pointer_path: Path, pointer: dict[str, Any], payload: dict[str, Any]) -> None:
    if not pointer:
        return
    pointer["c26_research_preview_handoff_rehearsal_report"] = payload["outputs"]["status_report_json"]
    pointer["c26_research_preview_handoff_rehearsal_status"] = payload["status"]
    pointer["c26_research_preview_handoff_rows"] = payload["outputs"]["handoff_rows"]
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


def _preview_action_detail(rows: list[dict[str, str]]) -> str:
    actions = sorted({row.get("preview_action", "") for row in rows})
    return f"observed={','.join(actions) or 'none'} required=ABSTAIN"


def _preview_broker_action_detail(rows: list[dict[str, str]]) -> str:
    values = sorted({str(row.get("broker_action_authorized", "")).lower() for row in rows})
    return f"observed={','.join(values) or 'none'} required=false"


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


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _fmt(value: datetime) -> str:
    return value.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
