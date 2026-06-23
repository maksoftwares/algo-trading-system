from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .account_registry import MT5AccountSpec, load_mt5_account_registry
from .market_data_export import _table, _utc_now, _write_json_atomic


DEFAULT_REPORT_JSON = Path("outputs") / "reports" / "A3_ML_DECISION_LOG_DISCOVERY_REPORT.json"
SCHEMA_VERSION = "a3_ml_decision_log_discovery_report_v1"


def generate_decision_log_discovery_report(root: Path, report_json: Path | None = None) -> Path:
    root = root.resolve()
    report_json = (report_json or root / DEFAULT_REPORT_JSON).resolve()
    registry = load_mt5_account_registry(root / "config" / "ml" / "mt5_accounts.yaml")
    cataloged = _cataloged_files(root, registry.accounts)
    records = []
    for account in registry.accounts:
        files_root = Path(account.files_roots[0]) if account.files_roots else None
        if files_root is None:
            continue
        for path in sorted(files_root.glob("*.csv")):
            if not _looks_like_signal_file(path.name):
                continue
            records.append(_inspect_csv(account, path, cataloged.get(account.account_label, set())))
    candidates = [record for record in records if record["compatible_signal_rows"] > 0]
    older_candidates = [record for record in candidates if record.get("min_signal_utc", "") and record["min_signal_utc"] < "2026-06-09T00:00:00Z"]
    uncataloged_compatible = [record for record in candidates if not record["cataloged"]]
    payload = {
        "status": _status(uncataloged_compatible, older_candidates),
        "stage": "C12-DECISION-LOG-DISCOVERY",
        "created_at_utc": _utc_now(),
        "schema_version": SCHEMA_VERSION,
        "summary": {
            "csv_signal_like_files_scanned": len(records),
            "compatible_signal_logs": len(candidates),
            "older_compatible_signal_logs": len(older_candidates),
            "uncataloged_compatible_signal_logs": len(uncataloged_compatible),
        },
        "records": records,
        "recommended_catalog_additions": [
            {
                "account_label": record["account_label"],
                "filename": record["filename"],
                "compatible_signal_rows": record["compatible_signal_rows"],
                "min_signal_utc": record["min_signal_utc"],
                "max_signal_utc": record["max_signal_utc"],
                "reason": "compatible XAUUSD breakout_retest signal rows are present and this file is not cataloged",
            }
            for record in uncataloged_compatible
        ],
        "boundary": {
            "mt5_connection_attempted": False,
            "data_export_attempted": False,
            "terminal_runtime_change_authorized": False,
            "model_training_authorized": False,
            "python_demo_predictions_authorized": False,
            "broker_action_authorized": False,
        },
        "outputs": {
            "status_report_json": str(report_json),
            "status_report_md": str(report_json.with_suffix(".md")),
        },
        "next_allowed_stage": _next_allowed_stage(uncataloged_compatible),
    }
    _write_status(report_json, payload)
    _update_pointer(root / "outputs" / "reports" / "C02_DATASET_POINTER.json", payload)
    return report_json


def render_decision_log_discovery_report_md(payload: dict[str, Any]) -> str:
    rows = [
        {
            "Account": item["account_label"],
            "File": item["filename"],
            "Cataloged": str(item["cataloged"]).lower(),
            "Rows": item["compatible_signal_rows"],
            "Min": item["min_signal_utc"],
            "Max": item["max_signal_utc"],
        }
        for item in payload.get("records", [])
        if item.get("compatible_signal_rows", 0) > 0
    ]
    additions = payload.get("recommended_catalog_additions", [])
    addition_lines = "\n".join(f"- {item['account_label']} {item['filename']} rows={item['compatible_signal_rows']}" for item in additions) if additions else "- none"
    return "\n".join(
        [
            "# A3 ML Decision Log Discovery Report",
            "",
            f"Overall status: {payload['status']}",
            "",
            "## Summary",
            "",
            f"- CSV signal-like files scanned: {payload['summary']['csv_signal_like_files_scanned']}",
            f"- Compatible signal logs: {payload['summary']['compatible_signal_logs']}",
            f"- Older compatible signal logs: {payload['summary']['older_compatible_signal_logs']}",
            f"- Uncataloged compatible signal logs: {payload['summary']['uncataloged_compatible_signal_logs']}",
            "",
            "## Compatible Logs",
            "",
            _table(rows, ["Account", "File", "Cataloged", "Rows", "Min", "Max"]) if rows else "No compatible logs found.",
            "",
            "## Recommended Catalog Additions",
            "",
            addition_lines,
            "",
            "## Boundary",
            "",
            "- MT5 connection attempted: false.",
            "- Data export attempted: false.",
            "- Terminal runtime change authorized: false.",
            "- Model training authorized: false.",
            "- Python demo predictions authorized: false.",
            "- Broker action authorized: false.",
            "",
            "## Next",
            "",
            payload["next_allowed_stage"],
            "",
        ]
    )


def _cataloged_files(root: Path, accounts: tuple[MT5AccountSpec, ...]) -> dict[str, set[str]]:
    result: dict[str, set[str]] = {}
    for account in accounts:
        path = root / account.log_catalog
        payload = json.loads(path.read_text(encoding="utf-8"))
        result[account.account_label] = {entry.get("filename", "") for entry in payload.get("entries", [])}
    return result


def _inspect_csv(account: MT5AccountSpec, path: Path, cataloged_files: set[str]) -> dict[str, Any]:
    compatible = 0
    total = 0
    min_time: datetime | None = None
    max_time: datetime | None = None
    fieldnames: list[str] = []
    try:
        with path.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            fieldnames = list(reader.fieldnames or [])
            for row in reader:
                total += 1
                if not _compatible_signal_row(row, path.name):
                    continue
                compatible += 1
                timestamp = _parse_time(row.get("timestamp_utc", "") or row.get("timestamp_broker", ""))
                if timestamp is not None:
                    min_time = timestamp if min_time is None else min(min_time, timestamp)
                    max_time = timestamp if max_time is None else max(max_time, timestamp)
    except UnicodeDecodeError:
        return _record(account, path, cataloged_files, total, 0, "", "", fieldnames, "DECODE_FAILED")
    return _record(account, path, cataloged_files, total, compatible, _iso(min_time), _iso(max_time), fieldnames, "PASS")


def _record(
    account: MT5AccountSpec,
    path: Path,
    cataloged_files: set[str],
    row_count: int,
    compatible: int,
    min_time: str,
    max_time: str,
    fieldnames: list[str],
    status: str,
) -> dict[str, Any]:
    return {
        "account_label": account.account_label,
        "account_scope": account.account_scope,
        "filename": path.name,
        "path": str(path),
        "cataloged": path.name in cataloged_files,
        "status": status,
        "row_count": row_count,
        "compatible_signal_rows": compatible,
        "min_signal_utc": min_time,
        "max_signal_utc": max_time,
        "fieldnames": fieldnames,
    }


def _compatible_signal_row(row: dict[str, str], filename: str) -> bool:
    symbol = (row.get("symbol") or row.get("qualified_symbol") or "").upper()
    candidate = (row.get("candidate") or filename).lower()
    return (
        symbol == "XAUUSD"
        and "breakout_retest" in candidate
        and str(row.get("would_signal", "")).strip().lower() == "true"
        and (row.get("timestamp_utc") or row.get("timestamp_broker"))
    )


def _looks_like_signal_file(name: str) -> bool:
    lower = name.lower()
    return "signal" in lower or "attachment_log" in lower


def _status(uncataloged_compatible: list[dict[str, Any]], older_candidates: list[dict[str, Any]]) -> str:
    if uncataloged_compatible:
        return "UNCATALOGED_COMPATIBLE_LOGS_FOUND"
    if older_candidates:
        return "OLDER_COMPATIBLE_LOGS_CATALOGED"
    return "NO_UNCATALOGED_COMPATIBLE_LOGS"


def _next_allowed_stage(uncataloged_compatible: list[dict[str, Any]]) -> str:
    if uncataloged_compatible:
        return "Review recommended catalog additions, add only compatible source-contract logs, then rerun C02 history snapshot and C07."
    return "No additional compatible uncataloged decision logs were found in configured MT5 Files roots."


def _write_status(status_json: Path, payload: dict[str, Any]) -> None:
    status_json.parent.mkdir(parents=True, exist_ok=True)
    status_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    status_json.with_suffix(".md").write_text(render_decision_log_discovery_report_md(payload), encoding="utf-8")


def _update_pointer(pointer_path: Path, payload: dict[str, Any]) -> None:
    if not pointer_path.exists():
        return
    pointer = json.loads(pointer_path.read_text(encoding="utf-8"))
    pointer["c12_decision_log_discovery_report"] = payload["outputs"]["status_report_json"]
    pointer["c12_decision_log_discovery_status"] = payload["status"]
    pointer["python_demo_predictions_authorized"] = False
    pointer["broker_action_authorized"] = False
    _write_json_atomic(pointer_path, pointer)


def _parse_time(value: str) -> datetime | None:
    text = str(value or "").strip()
    if not text:
        return None
    text = text.replace("Z", "+00:00")
    for fmt in ("%Y.%m.%d %H:%M:%S", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(text.replace("+00:00", ""), fmt).replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _iso(value: datetime | None) -> str:
    if value is None:
        return ""
    return value.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
