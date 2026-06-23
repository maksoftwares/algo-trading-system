from __future__ import annotations

import csv
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .account_registry import MT5AccountSpec, load_mt5_account_registry
from .market_data_export import _table, _utc_now, _write_json_atomic


DEFAULT_REPORT_JSON = Path("outputs") / "reports" / "A3_ML_HISTORICAL_DECISION_COVERAGE_STATUS.json"
SCHEMA_VERSION = "a3_ml_historical_decision_coverage_status_v1"
SYMBOL = "XAUUSD"
CURRENT_FAMILY = "breakout_retest"
TIME_KEYS = (
    "timestamp_utc",
    "time_utc",
    "timestamp",
    "m5_bar_time",
    "bar_start_utc",
    "decision_time",
    "decision_time_utc",
)
SCAN_NAME_HINTS = ("signal", "observer", "handoff", "prediction")


def generate_historical_decision_coverage_report(root: Path, report_json: Path | None = None) -> Path:
    root = root.resolve()
    reports = root / "outputs" / "reports"
    report_json = (report_json or root / DEFAULT_REPORT_JSON).resolve()
    registry = load_mt5_account_registry(root / "config" / "ml" / "mt5_accounts.yaml")
    pointer = _read_json(reports / "C02_DATASET_POINTER.json")
    first_decision = _first_decision_time(root, pointer)
    records = []
    for account in registry.accounts:
        for files_root in account.files_roots:
            root_path = Path(files_root)
            if not root_path.exists():
                records.append(_missing_root_record(account, root_path))
                continue
            for path in sorted(root_path.glob("*.csv")):
                record = _inspect_csv(account, path, first_decision)
                if record is not None:
                    records.append(record)
    summary = _summary(records, first_decision)
    status = _status(summary)
    payload = {
        "status": status,
        "stage": "C39-HISTORICAL-DECISION-COVERAGE",
        "created_at_utc": _utc_now(),
        "schema_version": SCHEMA_VERSION,
        "dataset_version": pointer.get("dataset_version", ""),
        "current_first_decision_utc": _iso(first_decision) if first_decision else "",
        "summary": summary,
        "family_summary": _family_summary(records),
        "older_compatible_records": [
            _candidate_record(record, "older_compatible_current_scope_would_signal_rows")
            for record in records
            if record.get("older_compatible_current_scope_would_signal_rows", 0) > 0
        ],
        "older_out_of_scope_records": [
            _candidate_record(record, "older_out_of_scope_would_signal_rows")
            for record in records
            if record.get("older_out_of_scope_would_signal_rows", 0) > 0
        ],
        "records": records,
        "authorization": {
            "older_decision_import_authorized": False,
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


def render_historical_decision_coverage_md(payload: dict[str, Any]) -> str:
    summary = payload.get("summary", {})
    family_rows = [
        {
            "Family": item.get("family", ""),
            "Would": item.get("would_signal_rows", 0),
            "Older": item.get("older_than_current_first_decision_rows", 0),
            "Min": item.get("min_utc", ""),
            "Max": item.get("max_utc", ""),
        }
        for item in payload.get("family_summary", [])
    ]
    compatible_rows = [
        {
            "Account": item.get("account_label", ""),
            "File": item.get("filename", ""),
            "Rows": item.get("rows", 0),
            "Min": item.get("min_utc", ""),
            "Max": item.get("max_utc", ""),
        }
        for item in payload.get("older_compatible_records", [])
    ]
    out_rows = [
        {
            "Account": item.get("account_label", ""),
            "File": item.get("filename", ""),
            "Rows": item.get("rows", 0),
            "Families": item.get("families", ""),
            "Min": item.get("min_utc", ""),
            "Max": item.get("max_utc", ""),
        }
        for item in payload.get("older_out_of_scope_records", [])
    ]
    return "\n".join(
        [
            "# A3 ML Historical Decision Coverage",
            "",
            f"Overall status: {payload['status']}",
            f"Dataset version: {payload.get('dataset_version', '')}",
            f"Current first decision UTC: {payload.get('current_first_decision_utc', '')}",
            "",
            "## Summary",
            "",
            f"- CSV files scanned: {summary.get('csv_files_scanned', 0)}",
            f"- Files with decision-like rows: {summary.get('files_with_decision_like_rows', 0)}",
            f"- Older compatible current-scope rows: {summary.get('older_compatible_current_scope_would_signal_rows', 0)}",
            f"- Older out-of-scope rows: {summary.get('older_out_of_scope_would_signal_rows', 0)}",
            f"- Earliest row UTC: {summary.get('earliest_row_utc', '')}",
            f"- Latest row UTC: {summary.get('latest_row_utc', '')}",
            "",
            "## Family Summary",
            "",
            _table(family_rows, ["Family", "Would", "Older", "Min", "Max"]) if family_rows else "No family rows found.",
            "",
            "## Older Compatible Current Scope",
            "",
            _table(compatible_rows, ["Account", "File", "Rows", "Min", "Max"]) if compatible_rows else "No older compatible current-scope decision rows found.",
            "",
            "## Older Out-Of-Scope Rows",
            "",
            _table(out_rows, ["Account", "File", "Rows", "Families", "Min", "Max"]) if out_rows else "No older out-of-scope decision rows found.",
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


def _inspect_csv(account: MT5AccountSpec, path: Path, first_decision: datetime | None) -> dict[str, Any] | None:
    if not any(hint in path.name.lower() for hint in SCAN_NAME_HINTS):
        return None
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            fieldnames = list(reader.fieldnames or [])
            keys = [key for key in TIME_KEYS if key in fieldnames]
            if not keys:
                return None
            rows = list(reader)
    except (OSError, UnicodeDecodeError, csv.Error):
        return _read_failed_record(account, path)
    family_counts: Counter[str] = Counter()
    older_family_counts: Counter[str] = Counter()
    times: list[datetime] = []
    xau_rows = 0
    would_signal_rows = 0
    current_scope_would = 0
    out_of_scope_would = 0
    older_compatible = 0
    older_out_of_scope = 0
    for row in rows:
        if not _is_xau(row):
            continue
        timestamp = _row_time(row, keys)
        if timestamp is None:
            continue
        xau_rows += 1
        times.append(timestamp)
        if not _truthy(row.get("would_signal")):
            continue
        family = _family(path.name, row)
        family_counts[family] += 1
        would_signal_rows += 1
        older = bool(first_decision and timestamp < first_decision)
        if family == CURRENT_FAMILY:
            current_scope_would += 1
            if older:
                older_compatible += 1
                older_family_counts[family] += 1
        else:
            out_of_scope_would += 1
            if older:
                older_out_of_scope += 1
                older_family_counts[family] += 1
    if not times and not would_signal_rows:
        return None
    return {
        "account_label": account.account_label,
        "account_scope": account.account_scope,
        "filename": path.name,
        "path": str(path),
        "status": "PASS",
        "row_count": len(rows),
        "xau_time_rows": xau_rows,
        "would_signal_rows": would_signal_rows,
        "current_scope_would_signal_rows": current_scope_would,
        "out_of_scope_would_signal_rows": out_of_scope_would,
        "older_compatible_current_scope_would_signal_rows": older_compatible,
        "older_out_of_scope_would_signal_rows": older_out_of_scope,
        "families": [{"family": key, "would_signal_rows": value} for key, value in sorted(family_counts.items())],
        "older_families": [{"family": key, "rows": value} for key, value in sorted(older_family_counts.items())],
        "min_utc": _iso(min(times)) if times else "",
        "max_utc": _iso(max(times)) if times else "",
    }


def _summary(records: list[dict[str, Any]], first_decision: datetime | None) -> dict[str, Any]:
    pass_records = [record for record in records if record.get("status") == "PASS"]
    times = []
    for record in pass_records:
        for key in ("min_utc", "max_utc"):
            parsed = _parse_time(record.get(key, ""))
            if parsed is not None:
                times.append(parsed)
    return {
        "csv_files_scanned": len(records),
        "files_with_decision_like_rows": len(pass_records),
        "current_first_decision_utc": _iso(first_decision) if first_decision else "",
        "earliest_row_utc": _iso(min(times)) if times else "",
        "latest_row_utc": _iso(max(times)) if times else "",
        "older_compatible_current_scope_would_signal_rows": sum(
            int(record.get("older_compatible_current_scope_would_signal_rows", 0)) for record in pass_records
        ),
        "older_out_of_scope_would_signal_rows": sum(
            int(record.get("older_out_of_scope_would_signal_rows", 0)) for record in pass_records
        ),
        "would_signal_rows": sum(int(record.get("would_signal_rows", 0)) for record in pass_records),
    }


def _family_summary(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    buckets: dict[str, dict[str, Any]] = {}
    for record in records:
        if record.get("status") != "PASS":
            continue
        record_times = []
        for key in ("min_utc", "max_utc"):
            parsed = _parse_time(record.get(key, ""))
            if parsed is not None:
                record_times.append(parsed)
        for item in record.get("families", []):
            family = item.get("family", "")
            bucket = buckets.setdefault(family, {"family": family, "would_signal_rows": 0, "older_than_current_first_decision_rows": 0, "times": []})
            bucket["would_signal_rows"] += int(item.get("would_signal_rows", 0))
            bucket["times"].extend(record_times)
        for item in record.get("older_families", []):
            family = item.get("family", "")
            bucket = buckets.setdefault(family, {"family": family, "would_signal_rows": 0, "older_than_current_first_decision_rows": 0, "times": []})
            bucket["older_than_current_first_decision_rows"] += int(item.get("rows", 0))
    rows = []
    for family, bucket in sorted(buckets.items()):
        times = bucket.pop("times", [])
        rows.append(
            {
                **bucket,
                "min_utc": _iso(min(times)) if times else "",
                "max_utc": _iso(max(times)) if times else "",
            }
        )
    return rows


def _status(summary: dict[str, Any]) -> str:
    if summary.get("older_compatible_current_scope_would_signal_rows", 0) > 0:
        return "OLDER_COMPATIBLE_DECISIONS_FOUND"
    if summary.get("older_out_of_scope_would_signal_rows", 0) > 0:
        return "OLDER_ONLY_OUT_OF_SCOPE_DECISIONS_FOUND"
    return "NO_OLDER_COMPATIBLE_DECISIONS_FOUND"


def _next_allowed_stage(status: str) -> str:
    if status == "OLDER_COMPATIBLE_DECISIONS_FOUND":
        return "Review older compatible current-scope rows, catalog/import only approved files, then rerun C08/C03."
    if status == "OLDER_ONLY_OUT_OF_SCOPE_DECISIONS_FOUND":
        return "Do not import out-of-scope rows without reviewer-approved contract expansion."
    return "No older compatible decision rows were found in configured MT5 Files roots; continue live collection or obtain external reviewed history."


def _candidate_record(record: dict[str, Any], count_key: str) -> dict[str, Any]:
    return {
        "account_label": record.get("account_label", ""),
        "account_scope": record.get("account_scope", ""),
        "filename": record.get("filename", ""),
        "path": record.get("path", ""),
        "rows": record.get(count_key, 0),
        "families": ",".join(item.get("family", "") for item in record.get("older_families", [])),
        "min_utc": record.get("min_utc", ""),
        "max_utc": record.get("max_utc", ""),
    }


def _first_decision_time(root: Path, pointer: dict[str, Any]) -> datetime | None:
    reports = root / "outputs" / "reports"
    c11 = _read_json(reports / "A3_ML_READINESS_GAP_REPORT.json")
    from_c11 = _parse_time(c11.get("decision_coverage", {}).get("min_decision_utc", ""))
    if from_c11 is not None:
        return from_c11
    path = Path(pointer.get("c02_labeled_decisions_csv", reports / "C02_LABELED_DECISIONS.csv"))
    times = []
    for row in _read_csv(path):
        parsed = _parse_time(row.get("decision_time") or row.get("decision_time_utc"))
        if parsed is not None:
            times.append(parsed)
    return min(times) if times else None


def _row_time(row: dict[str, str], keys: list[str]) -> datetime | None:
    for key in keys:
        parsed = _parse_time(row.get(key))
        if parsed is not None:
            return parsed
    return None


def _is_xau(row: dict[str, str]) -> bool:
    symbol = (row.get("symbol") or row.get("qualified_symbol") or "").strip().upper()
    return not symbol or SYMBOL in symbol


def _family(filename: str, row: dict[str, str]) -> str:
    text = " ".join([row.get("candidate", ""), row.get("comment", ""), filename]).lower()
    if "breakout_retest" in text or "soft_retest" in text or "tier1" in text:
        return CURRENT_FAMILY
    if "round_number" in text or "symbol_normalized_round" in text or "round_retest" in text:
        return "round_number_retest"
    if "session_extreme" in text:
        return "session_extreme_retest"
    if "rdguard" in text:
        return "rdguard"
    if "rdstruct" in text:
        return "rdstruct"
    if "handoff" in filename.lower() or "prediction" in filename.lower() or "observer" in filename.lower():
        return CURRENT_FAMILY
    return "unknown"


def _truthy(value: Any) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def _parse_time(value: str | None) -> datetime | None:
    text = str(value or "").strip()
    if not text:
        return None
    text = text.replace("Z", "+00:00").replace("T", " ")
    for fmt in ("%Y.%m.%d %H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"):
        try:
            return datetime.strptime(text.replace("+00:00", "")[:19], fmt).replace(tzinfo=timezone.utc)
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


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def _read_json(path_or_text: str | Path) -> dict[str, Any]:
    if not path_or_text:
        return {}
    path = Path(path_or_text)
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _missing_root_record(account: MT5AccountSpec, path: Path) -> dict[str, Any]:
    return {
        "account_label": account.account_label,
        "account_scope": account.account_scope,
        "filename": "<missing files root>",
        "path": str(path),
        "status": "MISSING_FILES_ROOT",
    }


def _read_failed_record(account: MT5AccountSpec, path: Path) -> dict[str, Any]:
    return {
        "account_label": account.account_label,
        "account_scope": account.account_scope,
        "filename": path.name,
        "path": str(path),
        "status": "READ_FAILED",
    }


def _write_status(status_json: Path, payload: dict[str, Any]) -> None:
    status_json.parent.mkdir(parents=True, exist_ok=True)
    status_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    status_json.with_suffix(".md").write_text(render_historical_decision_coverage_md(payload), encoding="utf-8")


def _update_pointer(pointer_path: Path, payload: dict[str, Any]) -> None:
    if not pointer_path.exists():
        return
    pointer = _read_json(pointer_path)
    pointer["c39_historical_decision_coverage_report"] = payload["outputs"]["status_report_json"]
    pointer["c39_historical_decision_coverage_status"] = payload["status"]
    pointer["c39_older_compatible_current_scope_rows"] = payload["summary"]["older_compatible_current_scope_would_signal_rows"]
    pointer["c39_older_out_of_scope_rows"] = payload["summary"]["older_out_of_scope_would_signal_rows"]
    pointer["python_demo_predictions_authorized"] = False
    pointer["ea_consumption_authorized"] = False
    pointer["broker_action_authorized"] = False
    _write_json_atomic(pointer_path, pointer)
