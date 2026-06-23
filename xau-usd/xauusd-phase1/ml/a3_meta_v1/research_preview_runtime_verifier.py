from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from .account_registry import MT5AccountSpec, load_mt5_account_registry
from .market_data_export import _table, _utc_now, _write_json_atomic
from .runtime_evidence import audit_runtime_evidence


DEFAULT_STATUS_JSON = Path("outputs") / "reports" / "A3_ML_RESEARCH_PREVIEW_RUNTIME_VERIFIER_STATUS.json"
HANDOFF_FILE_NAME = "A3_ML_EA_HANDOFF.csv"
BROKER_SHADOW_TAP_LOG = "a3_ml_broker_shadow_tap.csv"
SCHEMA_VERSION = "a3_ml_research_preview_runtime_verifier_status_v1"


def verify_research_preview_runtime_read_path(root: Path, report_json: Path | None = None) -> Path:
    root = root.resolve()
    report_json = (report_json or root / DEFAULT_STATUS_JSON).resolve()
    reports = root / "outputs" / "reports"
    c20_path = audit_runtime_evidence(root)
    registry = load_mt5_account_registry(root / "config" / "ml" / "mt5_accounts.yaml")
    pointer = _read_json(reports / "C02_DATASET_POINTER.json")
    c20 = _read_json(c20_path)
    c25 = _read_json(reports / "A3_ML_BROKER_SHADOW_MANUAL_ATTACH_PACKET.json")
    c26 = _read_json(reports / "A3_ML_RESEARCH_PREVIEW_HANDOFF_REHEARSAL_STATUS.json")
    accounts = [_account_payload(account) for account in registry.accounts]
    validations = _validations(accounts, c26)
    status = _status(accounts, validations)
    payload = {
        "status": status,
        "stage": "C27-RESEARCH-PREVIEW-RUNTIME-READ-PATH-VERIFIER",
        "created_at_utc": _utc_now(),
        "schema_version": SCHEMA_VERSION,
        "dataset_version": pointer.get("dataset_version", c26.get("dataset_version", "")),
        "authorization": {
            "official_model_training_authorized": False,
            "python_demo_predictions_authorized": False,
            "ea_consumption_authorized": False,
            "broker_action_authorized": False,
        },
        "upstream_statuses": {
            "c20_runtime_evidence": c20.get("status", "MISSING"),
            "c25_broker_shadow_manual_attach_packet": c25.get("status", "MISSING"),
            "c26_research_preview_handoff_rehearsal": c26.get("status", "MISSING"),
        },
        "runtime_evidence": {
            "handoff_research_preview_ready_all_accounts": all(item["handoff_research_preview_ready"] for item in accounts),
            "broker_shadow_tap_exists_all_accounts": all(item["broker_shadow_tap_exists"] for item in accounts),
            "research_preview_read_path_confirmed_all_accounts": all(item["research_preview_read_path_confirmed"] for item in accounts),
            "research_preview_read_path_confirmed_any_account": any(item["research_preview_read_path_confirmed"] for item in accounts),
        },
        "accounts": accounts,
        "validations": validations,
        "inputs": {
            "registry_path": str(root / "config" / "ml" / "mt5_accounts.yaml"),
            "c20_runtime_evidence": str(c20_path),
            "c25_broker_shadow_manual_attach_packet": str(reports / "A3_ML_BROKER_SHADOW_MANUAL_ATTACH_PACKET.json"),
            "c26_research_preview_handoff_rehearsal": str(reports / "A3_ML_RESEARCH_PREVIEW_HANDOFF_REHEARSAL_STATUS.json"),
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
        "next_allowed_stage": _next_allowed_stage(status),
    }
    _write_status(report_json, payload)
    _update_pointer(root / "outputs" / "reports" / "C02_DATASET_POINTER.json", pointer, payload)
    return report_json


def render_research_preview_runtime_verifier_md(payload: dict[str, Any]) -> str:
    accounts = [
        {
            "Account": item.get("account_label", ""),
            "Handoff": str(item.get("handoff_research_preview_ready", False)).lower(),
            "Tap log": str(item.get("broker_shadow_tap_exists", False)).lower(),
            "Read path": str(item.get("research_preview_read_path_confirmed", False)).lower(),
            "Rows": str(item.get("research_preview_tap_rows", 0)),
        }
        for item in payload.get("accounts", [])
    ]
    validations = [
        {"Check": item["check"], "Passed": str(item["passed"]).lower(), "Detail": item["detail"]}
        for item in payload.get("validations", [])
    ]
    return "\n".join(
        [
            "# A3 ML Research Preview Runtime Verifier Status",
            "",
            f"Overall status: {payload['status']}",
            f"Dataset version: {payload.get('dataset_version', '')}",
            "",
            "## Meaning",
            "",
            "This verifies the EA runtime read path for Python-produced research-preview rows. It still does not authorize official Python demo predictions, EA consumption, or broker action.",
            "",
            "## Upstream Statuses",
            "",
            f"- C20 runtime evidence: {payload.get('upstream_statuses', {}).get('c20_runtime_evidence', '')}",
            f"- C25 broker shadow manual attach packet: {payload.get('upstream_statuses', {}).get('c25_broker_shadow_manual_attach_packet', '')}",
            f"- C26 research preview handoff rehearsal: {payload.get('upstream_statuses', {}).get('c26_research_preview_handoff_rehearsal', '')}",
            "",
            "## Runtime Evidence",
            "",
            f"- Handoff research preview ready all accounts: {str(payload['runtime_evidence']['handoff_research_preview_ready_all_accounts']).lower()}.",
            f"- Broker shadow tap exists all accounts: {str(payload['runtime_evidence']['broker_shadow_tap_exists_all_accounts']).lower()}.",
            f"- Research preview read path confirmed all accounts: {str(payload['runtime_evidence']['research_preview_read_path_confirmed_all_accounts']).lower()}.",
            "",
            "## Account State",
            "",
            _table(accounts, ["Account", "Handoff", "Tap log", "Read path", "Rows"]) if accounts else "No accounts configured.",
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


def _account_payload(account: MT5AccountSpec) -> dict[str, Any]:
    files_root = Path(account.files_roots[0]) if account.files_roots else Path(account.expected_data_path or "") / "MQL5" / "Files"
    handoff_path = files_root / HANDOFF_FILE_NAME
    tap_path = files_root / BROKER_SHADOW_TAP_LOG
    handoff_rows = _read_csv(handoff_path)
    tap_rows = _read_csv(tap_path)
    matching_handoff = [
        row
        for row in handoff_rows
        if row.get("account_scope") == account.account_scope and row.get("symbol", account.symbol) == account.symbol
    ]
    matching_tap = [
        row
        for row in tap_rows
        if (not row.get("account_login") or row.get("account_login") == account.account_scope)
        and row.get("symbol", account.symbol) == account.symbol
    ]
    research_tap = [_research_preview_tap_row(row) for row in matching_tap]
    handoff_ready = bool(matching_handoff) and all(_research_preview_handoff_row(row) for row in matching_handoff)
    read_path_confirmed = bool(research_tap)
    return {
        "account_label": account.account_label,
        "account_scope": account.account_scope,
        "role": account.role,
        "files_root": str(files_root),
        "files_root_exists": files_root.exists(),
        "files_root_safe": _is_mql5_files_root(files_root),
        "handoff_path": str(handoff_path),
        "handoff_exists": handoff_path.exists(),
        "handoff_rows": len(handoff_rows),
        "matching_handoff_rows": len(matching_handoff),
        "handoff_actions": sorted({row.get("action", "") for row in matching_handoff}),
        "handoff_broker_action_authorized_values": sorted({str(row.get("broker_action_authorized", "")).lower() for row in matching_handoff}),
        "handoff_drift_values": sorted({row.get("drift_status", "") for row in matching_handoff}),
        "handoff_research_preview_ready": handoff_ready,
        "broker_shadow_tap_path": str(tap_path),
        "broker_shadow_tap_exists": tap_path.exists(),
        "broker_shadow_tap_rows": len(tap_rows),
        "matching_broker_shadow_tap_rows": len(matching_tap),
        "research_preview_tap_rows": len(research_tap),
        "latest_matching_broker_shadow_tap": matching_tap[-1] if matching_tap else {},
        "research_preview_read_path_confirmed": read_path_confirmed,
    }


def _validations(accounts: list[dict[str, Any]], c26: dict[str, Any]) -> list[dict[str, Any]]:
    checks = [
        _check(
            "c26_research_preview_published",
            c26.get("status") == "PUBLISHED_RESEARCH_PREVIEW_FAIL_CLOSED",
            c26.get("status", "MISSING"),
        ),
        _check(
            "c26_keeps_authorization_false",
            c26.get("authorization", {}).get("python_demo_predictions_authorized") is False
            and c26.get("authorization", {}).get("ea_consumption_authorized") is False
            and c26.get("authorization", {}).get("broker_action_authorized") is False,
            "C26 authorization must remain false",
        ),
    ]
    for account in accounts:
        prefix = account["account_label"]
        checks.extend(
            [
                _check(f"{prefix}_files_root_exists", bool(account["files_root_exists"]), account["files_root"]),
                _check(f"{prefix}_files_root_safe", bool(account["files_root_safe"]), account["files_root"]),
                _check(f"{prefix}_handoff_exists", bool(account["handoff_exists"]), account["handoff_path"]),
                _check(
                    f"{prefix}_handoff_research_preview_ready",
                    bool(account["handoff_research_preview_ready"]),
                    _handoff_detail(account),
                ),
            ]
        )
    return checks


def _status(accounts: list[dict[str, Any]], validations: list[dict[str, Any]]) -> str:
    if any(not item["passed"] for item in validations):
        return "PREFLIGHT_BLOCKED"
    if all(item["research_preview_read_path_confirmed"] for item in accounts):
        return "RESEARCH_PREVIEW_READ_PATH_CONFIRMED_ALL_ACCOUNTS"
    if any(item["research_preview_read_path_confirmed"] for item in accounts) or any(item["broker_shadow_tap_exists"] for item in accounts):
        return "PARTIAL_RESEARCH_PREVIEW_RUNTIME_EVIDENCE"
    return "WAITING_FOR_MT5_RUNTIME_ATTACH"


def _research_preview_handoff_row(row: dict[str, str]) -> bool:
    return (
        row.get("action") == "ABSTAIN"
        and str(row.get("broker_action_authorized", "")).lower() == "false"
        and row.get("drift_status") == "ML_RESEARCH_PREVIEW_FAIL_CLOSED"
        and bool(row.get("model_id"))
        and bool(row.get("p_win_calibrated"))
    )


def _research_preview_tap_row(row: dict[str, str]) -> bool:
    return (
        str(row.get("ml_available", "")).lower() == "true"
        and row.get("ml_action") == "ABSTAIN"
        and str(row.get("ml_broker_action_authorized", "")).lower() == "false"
        and row.get("ml_drift_status") == "ML_RESEARCH_PREVIEW_FAIL_CLOSED"
        and bool(row.get("ml_model_id"))
    )


def _handoff_detail(account: dict[str, Any]) -> str:
    return (
        f"matching_rows={account['matching_handoff_rows']} "
        f"actions={','.join(account['handoff_actions']) or 'none'} "
        f"broker_auth={','.join(account['handoff_broker_action_authorized_values']) or 'none'} "
        f"drift={','.join(account['handoff_drift_values']) or 'none'}"
    )


def _next_allowed_stage(status: str) -> str:
    if status == "RESEARCH_PREVIEW_READ_PATH_CONFIRMED_ALL_ACCOUNTS":
        return "The EA read path is confirmed for Python-produced research-preview rows on all accounts. Continue collecting/exporting data until C03/C05/C04/C06 can authorize official demo-shadow predictions."
    if status == "PARTIAL_RESEARCH_PREVIEW_RUNTIME_EVIDENCE":
        return "Some broker-shadow runtime evidence exists. Attach or reload the missing account broker-shadow consumers, wait for a new tick or M5 bar, then rerun C27."
    if status == "WAITING_FOR_MT5_RUNTIME_ATTACH":
        return "Attach or reload dry-run broker-shadow consumers on XAUUSD M5 for A1/A2/A3, wait for a tick or M5 bar, then rerun C27."
    return "Fix C26 or handoff preflight issues, then rerun C27."


def _write_status(status_json: Path, payload: dict[str, Any]) -> None:
    status_json.parent.mkdir(parents=True, exist_ok=True)
    status_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    status_json.with_suffix(".md").write_text(render_research_preview_runtime_verifier_md(payload), encoding="utf-8")


def _update_pointer(pointer_path: Path, pointer: dict[str, Any], payload: dict[str, Any]) -> None:
    if not pointer:
        return
    pointer["c27_research_preview_runtime_verifier_report"] = payload["outputs"]["status_report_json"]
    pointer["c27_research_preview_runtime_verifier_status"] = payload["status"]
    pointer["c27_research_preview_read_path_confirmed_all_accounts"] = bool(
        payload["runtime_evidence"]["research_preview_read_path_confirmed_all_accounts"]
    )
    pointer["python_demo_predictions_authorized"] = False
    pointer["ea_consumption_authorized"] = False
    pointer["broker_action_authorized"] = False
    _write_json_atomic(pointer_path, pointer)


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            return list(csv.DictReader(handle))
    except (OSError, UnicodeDecodeError, csv.Error):
        return []


def _read_json(path_or_text: str | Path) -> dict[str, Any]:
    if not path_or_text:
        return {}
    path = Path(path_or_text)
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _is_mql5_files_root(path: Path) -> bool:
    parts = [part.casefold() for part in path.parts]
    return len(parts) >= 2 and parts[-2:] == ["mql5", "files"]


def _check(check: str, passed: bool, detail: str) -> dict[str, Any]:
    return {"check": check, "passed": bool(passed), "detail": detail}
