from __future__ import annotations

import csv
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .account_registry import MT5AccountSpec, load_mt5_account_registry
from .market_data_export import _table, _utc_now, _write_json_atomic


DEFAULT_REPORT_JSON = Path("outputs") / "reports" / "A3_ML_DECISION_BACKFILL_AUDIT_STATUS.json"
SCHEMA_VERSION = "a3_ml_decision_backfill_audit_status_v1"
SYMBOL = "XAUUSD"
CURRENT_FAMILY = "breakout_retest"
SIGNAL_FIELD_HINTS = {"timestamp_utc", "timestamp_broker", "symbol", "qualified_symbol", "would_signal", "direction"}


def generate_decision_backfill_audit(root: Path, report_json: Path | None = None) -> Path:
    root = root.resolve()
    report_json = (report_json or root / DEFAULT_REPORT_JSON).resolve()
    reports = root / "outputs" / "reports"
    registry = load_mt5_account_registry(root / "config" / "ml" / "mt5_accounts.yaml")
    pointer = _read_json(reports / "C02_DATASET_POINTER.json")
    cataloged = _cataloged_files(root, registry.accounts)
    records = []
    for account in registry.accounts:
        files_root = Path(account.files_roots[0]) if account.files_roots else None
        if files_root is None or not files_root.exists():
            continue
        for path in sorted(files_root.glob("*.csv")):
            record = _inspect_signalish_csv(account, path, cataloged.get(account.account_label, {}))
            if record is not None:
                records.append(record)
    current_scope = [item for item in records if item["current_scope_would_signal_rows"] > 0]
    uncataloged_current = [item for item in current_scope if not item["cataloged"]]
    out_of_scope = [item for item in records if item["out_of_scope_would_signal_rows"] > 0]
    family_rows = _family_rows(out_of_scope)
    status = _status(uncataloged_current, out_of_scope)
    payload = {
        "status": status,
        "stage": "C34-DECISION-BACKFILL-AUDIT",
        "created_at_utc": _utc_now(),
        "schema_version": SCHEMA_VERSION,
        "dataset_version": pointer.get("dataset_version", ""),
        "current_contract": {
            "symbol": SYMBOL,
            "family": CURRENT_FAMILY,
            "may_import_without_contract_change": False,
        },
        "summary": {
            "signalish_csv_files_scanned": len(records),
            "current_scope_files_with_would_signals": len(current_scope),
            "uncataloged_current_scope_files": len(uncataloged_current),
            "current_scope_would_signal_rows": sum(item["current_scope_would_signal_rows"] for item in current_scope),
            "out_of_scope_files_with_would_signals": len(out_of_scope),
            "out_of_scope_would_signal_rows": sum(item["out_of_scope_would_signal_rows"] for item in out_of_scope),
            "out_of_scope_estimated_groups": len({group for item in out_of_scope for group in item["out_of_scope_group_keys"]}),
        },
        "family_summary": family_rows,
        "uncataloged_current_scope_candidates": [
            _candidate_row(item, "current_scope") for item in uncataloged_current
        ],
        "out_of_scope_candidates": [_candidate_row(item, "out_of_scope") for item in out_of_scope],
        "records": records,
        "authorization": {
            "contract_expansion_authorized": False,
            "training_authorized": False,
            "python_demo_predictions_authorized": False,
            "ea_consumption_authorized": False,
            "broker_action_authorized": False,
        },
        "boundary": {
            "mt5_connection_attempted": False,
            "data_export_attempted": False,
            "terminal_runtime_change_authorized": False,
            "profile_or_chart_file_write_attempted": False,
            "model_training_authorized": False,
            "python_demo_predictions_authorized": False,
            "broker_action_authorized": False,
        },
        "outputs": {
            "status_report_json": str(report_json),
            "status_report_md": str(report_json.with_suffix(".md")),
        },
        "next_allowed_stage": _next_allowed_stage(status),
    }
    _write_status(report_json, payload)
    _update_pointer(reports / "C02_DATASET_POINTER.json", payload)
    return report_json


def render_decision_backfill_audit_md(payload: dict[str, Any]) -> str:
    summary = payload.get("summary", {})
    family_rows = [
        {
            "Family": item.get("family", ""),
            "Rows": str(item.get("would_signal_rows", 0)),
            "Groups": str(item.get("estimated_groups", 0)),
            "Files": str(item.get("files", 0)),
            "Min": item.get("min_signal_utc", ""),
            "Max": item.get("max_signal_utc", ""),
        }
        for item in payload.get("family_summary", [])
    ]
    current_rows = [
        {
            "Account": item.get("account_label", ""),
            "File": item.get("filename", ""),
            "Rows": str(item.get("would_signal_rows", 0)),
            "Min": item.get("min_signal_utc", ""),
            "Max": item.get("max_signal_utc", ""),
        }
        for item in payload.get("uncataloged_current_scope_candidates", [])
    ]
    out_rows = [
        {
            "Account": item.get("account_label", ""),
            "File": item.get("filename", ""),
            "Family": item.get("family", ""),
            "Rows": str(item.get("would_signal_rows", 0)),
            "Min": item.get("min_signal_utc", ""),
            "Max": item.get("max_signal_utc", ""),
        }
        for item in payload.get("out_of_scope_candidates", [])
    ]
    return "\n".join(
        [
            "# A3 ML Decision Backfill Audit",
            "",
            f"Overall status: {payload['status']}",
            f"Dataset version: {payload.get('dataset_version', '')}",
            "",
            "## Summary",
            "",
            f"- Signal-like CSV files scanned: {summary.get('signalish_csv_files_scanned', 0)}",
            f"- Current-scope would-signal rows: {summary.get('current_scope_would_signal_rows', 0)}",
            f"- Uncataloged current-scope files: {summary.get('uncataloged_current_scope_files', 0)}",
            f"- Out-of-scope would-signal rows: {summary.get('out_of_scope_would_signal_rows', 0)}",
            f"- Out-of-scope estimated groups: {summary.get('out_of_scope_estimated_groups', 0)}",
            "",
            "## Family Summary",
            "",
            _table(family_rows, ["Family", "Rows", "Groups", "Files", "Min", "Max"]) if family_rows else "No out-of-scope family rows.",
            "",
            "## Uncataloged Current Scope",
            "",
            _table(current_rows, ["Account", "File", "Rows", "Min", "Max"]) if current_rows else "No uncataloged current-scope files found.",
            "",
            "## Out-Of-Scope Candidates",
            "",
            _table(out_rows, ["Account", "File", "Family", "Rows", "Min", "Max"]) if out_rows else "No out-of-scope candidates found.",
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


def _inspect_signalish_csv(account: MT5AccountSpec, path: Path, cataloged_files: dict[str, str]) -> dict[str, Any] | None:
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            fieldnames = list(reader.fieldnames or [])
            if not _signalish(fieldnames, path.name):
                return None
            rows = list(reader)
    except (OSError, UnicodeDecodeError, csv.Error):
        return {
            "account_label": account.account_label,
            "account_scope": account.account_scope,
            "filename": path.name,
            "path": str(path),
            "cataloged": path.name in cataloged_files,
            "catalog_family": cataloged_files.get(path.name, ""),
            "status": "READ_FAILED",
            "row_count": 0,
            "xau_rows": 0,
            "current_scope_would_signal_rows": 0,
            "out_of_scope_would_signal_rows": 0,
            "out_of_scope_group_keys": [],
            "families": [],
            "min_signal_utc": "",
            "max_signal_utc": "",
            "fieldnames": [],
        }
    current_count = 0
    out_count = 0
    group_keys: set[str] = set()
    families: Counter[str] = Counter()
    times: list[datetime] = []
    xau_rows = 0
    for row in rows:
        if not _is_xau(row):
            continue
        xau_rows += 1
        if not _truthy(row.get("would_signal")):
            continue
        family = _family(path.name, row, cataloged_files.get(path.name, ""))
        timestamp = _parse_time(row.get("timestamp_utc") or row.get("timestamp_broker") or "")
        if timestamp is not None:
            times.append(timestamp)
        if family == CURRENT_FAMILY:
            current_count += 1
        else:
            out_count += 1
            families[family] += 1
            group_keys.add(_group_key(family, row, timestamp))
    return {
        "account_label": account.account_label,
        "account_scope": account.account_scope,
        "filename": path.name,
        "path": str(path),
        "cataloged": path.name in cataloged_files,
        "catalog_family": cataloged_files.get(path.name, ""),
        "status": "PASS",
        "row_count": len(rows),
        "xau_rows": xau_rows,
        "current_scope_would_signal_rows": current_count,
        "out_of_scope_would_signal_rows": out_count,
        "out_of_scope_group_keys": sorted(group_keys),
        "families": [{"family": key, "would_signal_rows": value} for key, value in sorted(families.items())],
        "min_signal_utc": _iso(min(times)) if times else "",
        "max_signal_utc": _iso(max(times)) if times else "",
        "fieldnames": fieldnames,
    }


def _family_rows(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_family: dict[str, dict[str, Any]] = {}
    for record in records:
        for item in record.get("families", []):
            family = item["family"]
            bucket = by_family.setdefault(
                family,
                {
                    "family": family,
                    "would_signal_rows": 0,
                    "files": 0,
                    "group_keys": set(),
                    "times": [],
                },
            )
            bucket["would_signal_rows"] += int(item.get("would_signal_rows", 0))
            bucket["files"] += 1
            bucket["group_keys"].update(record.get("out_of_scope_group_keys", []))
            for key in ("min_signal_utc", "max_signal_utc"):
                parsed = _parse_time(record.get(key, ""))
                if parsed is not None:
                    bucket["times"].append(parsed)
    rows = []
    for family, bucket in sorted(by_family.items()):
        times = bucket["times"]
        rows.append(
            {
                "family": family,
                "would_signal_rows": bucket["would_signal_rows"],
                "estimated_groups": len(bucket["group_keys"]),
                "files": bucket["files"],
                "min_signal_utc": _iso(min(times)) if times else "",
                "max_signal_utc": _iso(max(times)) if times else "",
            }
        )
    return rows


def _candidate_row(record: dict[str, Any], mode: str) -> dict[str, Any]:
    families = record.get("families", [])
    family = ",".join(item.get("family", "") for item in families) if mode == "out_of_scope" else CURRENT_FAMILY
    row_count = (
        record.get("out_of_scope_would_signal_rows", 0)
        if mode == "out_of_scope"
        else record.get("current_scope_would_signal_rows", 0)
    )
    return {
        "account_label": record.get("account_label", ""),
        "account_scope": record.get("account_scope", ""),
        "filename": record.get("filename", ""),
        "family": family,
        "would_signal_rows": row_count,
        "min_signal_utc": record.get("min_signal_utc", ""),
        "max_signal_utc": record.get("max_signal_utc", ""),
        "reason": "requires contract expansion and reviewer approval" if mode == "out_of_scope" else "current-scope file is not cataloged",
    }


def _status(uncataloged_current: list[dict[str, Any]], out_of_scope: list[dict[str, Any]]) -> str:
    if uncataloged_current:
        return "CURRENT_SCOPE_UNCATALOGED_BACKFILL_FOUND"
    if out_of_scope:
        return "CURRENT_SCOPE_EXHAUSTED_OUT_OF_SCOPE_BACKFILL_FOUND"
    return "NO_BACKFILL_CANDIDATES_FOUND"


def _next_allowed_stage(status: str) -> str:
    if status == "CURRENT_SCOPE_UNCATALOGED_BACKFILL_FOUND":
        return "Review uncataloged current-scope files, add only contract-compatible logs to the C02 catalogs, then rerun C08/C03."
    if status == "CURRENT_SCOPE_EXHAUSTED_OUT_OF_SCOPE_BACKFILL_FOUND":
        return "Do not import out-of-scope rows into the locked model. Ask reviewer to approve or reject a multi-family C02/C03 contract expansion."
    return "No disk backfill was found. Continue live data collection and rerun C08/C23 after market data advances."


def _cataloged_files(root: Path, accounts: tuple[MT5AccountSpec, ...]) -> dict[str, dict[str, str]]:
    result: dict[str, dict[str, str]] = {}
    for account in accounts:
        path = root / account.log_catalog
        payload = _read_json(path)
        result[account.account_label] = {
            str(entry.get("filename", "")): str(entry.get("family", "")) for entry in payload.get("entries", [])
        }
    return result


def _signalish(fieldnames: list[str], filename: str) -> bool:
    lower = filename.lower()
    if "signal" in lower or "attachment" in lower:
        return True
    return len(SIGNAL_FIELD_HINTS & {field.casefold() for field in fieldnames}) >= 4


def _is_xau(row: dict[str, str]) -> bool:
    return (row.get("symbol") or row.get("qualified_symbol") or "").strip().upper() == SYMBOL


def _family(filename: str, row: dict[str, str], catalog_family: str) -> str:
    text = " ".join([row.get("candidate", ""), row.get("comment", ""), filename, catalog_family]).lower()
    if "breakout_retest" in text:
        return CURRENT_FAMILY
    if "round_number" in text or "symbol_normalized_round" in text or "round_retest" in text:
        return "round_number_retest"
    if "session_extreme" in text:
        return "session_extreme_retest"
    if "soft_retest" in text:
        return "soft_retest"
    if "rdguard" in text:
        return "rdguard"
    if "rdstruct" in text:
        return "rdstruct"
    return "unknown"


def _group_key(family: str, row: dict[str, str], timestamp: datetime | None) -> str:
    direction = str(row.get("direction", "")).upper()
    level = row.get("level_price") or row.get("entry_price") or ""
    time_bucket = _iso(timestamp).rsplit(":", 1)[0] if timestamp else ""
    return "|".join([family, direction, time_bucket, str(level)])


def _truthy(value: Any) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def _parse_time(value: str | None) -> datetime | None:
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


def _iso(value: datetime) -> str:
    return value.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _read_json(path_or_text: str | Path) -> dict[str, Any]:
    if not path_or_text:
        return {}
    path = Path(path_or_text)
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _write_status(status_json: Path, payload: dict[str, Any]) -> None:
    status_json.parent.mkdir(parents=True, exist_ok=True)
    status_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    status_json.with_suffix(".md").write_text(render_decision_backfill_audit_md(payload), encoding="utf-8")


def _update_pointer(pointer_path: Path, payload: dict[str, Any]) -> None:
    if not pointer_path.exists():
        return
    pointer = _read_json(pointer_path)
    pointer["c34_decision_backfill_audit_report"] = payload["outputs"]["status_report_json"]
    pointer["c34_decision_backfill_audit_status"] = payload["status"]
    pointer["c34_uncataloged_current_scope_files"] = payload["summary"]["uncataloged_current_scope_files"]
    pointer["c34_out_of_scope_would_signal_rows"] = payload["summary"]["out_of_scope_would_signal_rows"]
    pointer["python_demo_predictions_authorized"] = False
    pointer["ea_consumption_authorized"] = False
    pointer["broker_action_authorized"] = False
    _write_json_atomic(pointer_path, pointer)
