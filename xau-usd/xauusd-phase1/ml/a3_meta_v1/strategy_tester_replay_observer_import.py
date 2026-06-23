from __future__ import annotations

import csv
import hashlib
import io
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .market_data_export import _table, _utc_now, _write_json_atomic, parse_utc


DEFAULT_REPORT_JSON = Path("outputs") / "reports" / "A3_ML_REPLAY_IMPORT_STATUS.json"
DEFAULT_C53_JSON = Path("outputs") / "reports" / "A3_ML_ISOLATED_STRATEGY_TESTER_TERMINAL_ROOT_STATUS.json"
DEFAULT_C54_JSON = Path("outputs") / "reports" / "A3_ML_STRATEGY_TESTER_REPLAY_LAUNCH_STATUS.json"
DEFAULT_C55_JSON = Path("outputs") / "reports" / "A3_ML_STRATEGY_TESTER_ACCOUNT_CONTEXT_DECISION_STATUS.json"
SCHEMA_VERSION = "a3_ml_strategy_tester_replay_observer_import_status_v1"
STATUS_IMPORTED = "REPLAY_OBSERVER_IMPORT_QUARANTINED"
STATUS_BLOCKED = "REPLAY_OBSERVER_IMPORT_BLOCKED"
SOURCE_TYPE = "strategy_tester_replay"
LABEL_STATUS = "REPLAY_OBSERVER_ONLY"
SIGNAL_LOG_NAME = "a3_breakout_tier1_compat_signal_log.csv"
SHADOW_TAP_NAME = "a3_ml_broker_shadow_tap.csv"
ORDER_LOG_NAME = "a3_breakout_tier1_compat_order_log.csv"
MANAGEMENT_LOG_NAME = "a3_breakout_tier1_compat_management_log.csv"
STARTUP_LOG_NAME = "a3_breakout_tier1_compat_startup.csv"
REQUIRED_SIGNAL_COLUMNS = {
    "timestamp_utc",
    "account_server",
    "account_login",
    "symbol",
    "run_id",
    "would_signal",
    "dry_run",
    "broker_action_allowed",
    "m5_bar_time",
}


def import_strategy_tester_replay_observer_evidence(
    root: Path,
    report_json: Path | None = None,
    *,
    c53_json: Path | None = None,
    c54_json: Path | None = None,
    c55_json: Path | None = None,
) -> Path:
    root = root.resolve()
    reports = root / "outputs" / "reports"
    report_json = (report_json or root / DEFAULT_REPORT_JSON).resolve()
    c53_json = (c53_json or root / DEFAULT_C53_JSON).resolve()
    c54_json = (c54_json or root / DEFAULT_C54_JSON).resolve()
    c55_json = (c55_json or root / DEFAULT_C55_JSON).resolve()
    pointer_path = reports / "C02_DATASET_POINTER.json"
    pointer = _read_json(pointer_path)
    c53 = _read_json(c53_json)
    c54 = _read_json(c54_json)
    c55 = _read_json(c55_json)
    context = _context(pointer, c53, c54)
    source_files = _source_files(c54, context["terminal_root"])
    validation = _validate(context, c54, c55, source_files)
    copied_files: list[dict[str, Any]] = []
    normalized_output = ""
    imported_rows = 0
    would_signal_rows = 0
    if validation["passed"]:
        copied_files = _copy_source_files(source_files, context["raw_replay_root"], context["terminal_root"])
        signal_source = _source_by_name(source_files, SIGNAL_LOG_NAME)
        signal_rows = _read_csv(signal_source["source_path"])
        imported_rows = len(signal_rows)
        would_signal_rows = sum(1 for row in signal_rows if _bool(row.get("would_signal")))
        normalized_output = str(_write_quarantined_observer_rows(signal_rows, context, signal_source))
    status = STATUS_IMPORTED if validation["passed"] else STATUS_BLOCKED
    payload = {
        "status": status,
        "stage": "C56-STRATEGY-TESTER-REPLAY-OBSERVER-IMPORT",
        "created_at_utc": _utc_now(),
        "schema_version": SCHEMA_VERSION,
        "dataset_version": context["dataset_version"],
        "selected_lane_id": context["selected_lane_id"],
        "account_label": context["account_label"],
        "account_scope": context["account_scope"],
        "source_type": SOURCE_TYPE,
        "label_status": LABEL_STATUS,
        "import_mode": "quarantined_observer_audit_only",
        "validation": validation,
        "row_counts": {
            "signal_rows_imported": imported_rows,
            "signal_would_signal_rows": would_signal_rows,
            "order_rows": validation.get("order_rows", 0),
            "management_rows": validation.get("management_rows", 0),
        },
        "source_manifest": _manifest_rows(source_files),
        "copied_files": copied_files,
        "outputs": {
            "status_report_json": str(report_json),
            "status_report_md": str(report_json.with_suffix(".md")),
            "raw_replay_root": str(context["raw_replay_root"]) if validation["passed"] else "",
            "quarantined_observer_csv": normalized_output,
        },
        "authorization": {
            "training_authorized": False,
            "python_demo_predictions_authorized": False,
            "ea_consumption_authorized": False,
            "broker_action_authorized": False,
        },
        "boundary": {
            "mt5_connection_attempted_by_c56": False,
            "terminal_launch_attempted_by_c56": False,
            "strategy_tester_launch_attempted_by_c56": False,
            "active_terminal_root_write_attempted": False,
            "model_training_attempted": False,
            "c03_rebuild_attempted": False,
            "python_demo_predictions_authorized": False,
            "ea_consumption_authorized": False,
            "broker_action_authorized": False,
        },
        "commands": _commands(root),
        "next_allowed_stage": _next_allowed_stage(status),
    }
    _write_status(report_json, payload)
    _update_pointer(pointer_path, payload)
    return report_json


def render_strategy_tester_replay_observer_import_md(payload: dict[str, Any]) -> str:
    checks = [
        {
            "Check": item.get("check", ""),
            "Pass": str(item.get("passed", False)).lower(),
            "Detail": item.get("detail", ""),
        }
        for item in payload.get("validation", {}).get("checks", [])
    ]
    sources = [
        {
            "Path": item.get("relative_path", item.get("name", "")),
            "Role": item.get("role", ""),
            "Rows": item.get("rows", ""),
            "SHA256": item.get("sha256", ""),
        }
        for item in payload.get("source_manifest", [])
    ]
    command_lines = "\n".join(f"- {key}: `{value}`" for key, value in payload.get("commands", {}).items())
    return "\n".join(
        [
            "# A3 ML Replay Import Status",
            "",
            f"Overall status: {payload['status']}",
            f"Dataset version: {payload.get('dataset_version', '')}",
            f"Selected lane: {payload.get('selected_lane_id', '')}",
            f"Account: {payload.get('account_label', '')} / {payload.get('account_scope', '')}",
            f"Source type: {payload.get('source_type', '')}",
            f"Label status: {payload.get('label_status', '')}",
            "",
            "## Row Counts",
            "",
            f"- Signal rows imported: {payload.get('row_counts', {}).get('signal_rows_imported', 0)}.",
            f"- Would-signal rows: {payload.get('row_counts', {}).get('signal_would_signal_rows', 0)}.",
            f"- Order rows: {payload.get('row_counts', {}).get('order_rows', 0)}.",
            f"- Management rows: {payload.get('row_counts', {}).get('management_rows', 0)}.",
            "",
            "## Validation",
            "",
            _table(checks, ["Check", "Pass", "Detail"]) if checks else "No checks.",
            "",
            "## Source Manifest",
            "",
            _table(sources, ["Path", "Role", "Rows", "SHA256"]) if sources else "No source files.",
            "",
            "## Outputs",
            "",
            f"- Raw replay root: {payload.get('outputs', {}).get('raw_replay_root', '')}.",
            f"- Quarantined observer CSV: {payload.get('outputs', {}).get('quarantined_observer_csv', '')}.",
            "",
            "## Commands",
            "",
            command_lines,
            "",
            "## Boundary",
            "",
            "- MT5 connection attempted by C56: false.",
            "- Terminal launch attempted by C56: false.",
            "- Strategy Tester launch attempted by C56: false.",
            "- C03 rebuild attempted: false.",
            "- Model training attempted: false.",
            "- Training authorized: false.",
            "- Python demo predictions authorized: false.",
            "- EA consumption authorized: false.",
            "- Broker action authorized: false.",
            "",
            "## Next",
            "",
            payload["next_allowed_stage"],
            "",
        ]
    )


def _context(pointer: dict[str, Any], c53: dict[str, Any], c54: dict[str, Any]) -> dict[str, Any]:
    dataset_version = str(pointer.get("dataset_version") or c54.get("dataset_version") or "UNKNOWN_DATASET")
    selected_lane_id = str(c54.get("selected_lane_id") or c53.get("selected_lane_id") or "UNKNOWN_LANE")
    selected = c53.get("selected_lane", {}) if isinstance(c53.get("selected_lane"), dict) else {}
    account_label = str(selected.get("account_label") or selected_lane_id.split("_", 1)[0] or "UNKNOWN")
    account_scope = str(selected.get("account_scope") or "")
    terminal_root = Path(str(selected.get("terminal_root", "")))
    output_root = Path(str(pointer.get("output_root") or ""))
    raw_replay_root = output_root / "raw" / account_label / "strategy_tester_replay" / _safe_name(selected_lane_id)
    normalized_csv = output_root / "normalized" / "replay_observer" / f"{_safe_name(selected_lane_id)}.csv"
    return {
        "dataset_version": dataset_version,
        "selected_lane_id": selected_lane_id,
        "account_label": account_label,
        "account_scope": account_scope,
        "snapshot_cutoff_utc": str(pointer.get("snapshot_cutoff_utc", "")),
        "terminal_root": terminal_root,
        "output_root": output_root,
        "raw_replay_root": raw_replay_root,
        "normalized_csv": normalized_csv,
    }


def _source_files(c54: dict[str, Any], terminal_root: Path) -> dict[str, dict[str, Any]]:
    files: dict[str, dict[str, Any]] = {}
    for item in c54.get("replay_outputs", []):
        if not isinstance(item, dict):
            continue
        source_path = Path(str(item.get("path", "")))
        name = source_path.name
        role = _role_for_name(name, source_path)
        relative_path = _relative_source_path(source_path, terminal_root)
        files[str(relative_path).replace("\\", "/")] = {
            "name": name,
            "role": role,
            "source_path": source_path,
            "expected_sha256": str(item.get("sha256", "")),
            "size_bytes": item.get("size_bytes", 0),
            "relative_path": relative_path,
        }
    return files


def _validate(context: dict[str, Any], c54: dict[str, Any], c55: dict[str, Any], source_files: dict[str, dict[str, Any]]) -> dict[str, Any]:
    checks = [
        _check("c54_completed_outputs_found", c54.get("status") == "STRATEGY_TESTER_REPLAY_LAUNCH_COMPLETED_OUTPUTS_FOUND", str(c54.get("status", "MISSING"))),
        _check("c55_no_account_context_blocker", c55.get("status", "MISSING") != "STRATEGY_TESTER_ACCOUNT_CONTEXT_DECISION_REQUIRED", str(c55.get("status", "MISSING"))),
        _check("dataset_output_root_exists", context["output_root"].exists(), str(context["output_root"])),
    ]
    for name in (SIGNAL_LOG_NAME, SHADOW_TAP_NAME, ORDER_LOG_NAME, MANAGEMENT_LOG_NAME, STARTUP_LOG_NAME):
        source = _source_by_name(source_files, name)
        checks.append(_check(f"{name}_present", bool(source) and source["source_path"].exists(), str(source.get("source_path", ""))))
    hash_checks = _hash_checks(source_files)
    checks.extend(hash_checks)
    signal_summary = _validate_signal_log(context, _source_by_name(source_files, SIGNAL_LOG_NAME))
    shadow_summary = _validate_shadow_tap(_source_by_name(source_files, SHADOW_TAP_NAME))
    order_rows = _row_count(_source_by_name(source_files, ORDER_LOG_NAME).get("source_path"))
    management_rows = _row_count(_source_by_name(source_files, MANAGEMENT_LOG_NAME).get("source_path"))
    checks.extend(signal_summary["checks"])
    checks.extend(shadow_summary["checks"])
    checks.append(_check("order_log_audit_only_zero_rows", order_rows == 0, str(order_rows)))
    checks.append(_check("management_log_audit_only_zero_rows", management_rows == 0, str(management_rows)))
    return {
        "passed": all(check["passed"] for check in checks),
        "checks": checks,
        "signal_rows": signal_summary["rows"],
        "shadow_rows": shadow_summary["rows"],
        "order_rows": order_rows,
        "management_rows": management_rows,
    }


def _validate_signal_log(context: dict[str, Any], source: dict[str, Any]) -> dict[str, Any]:
    path = source.get("source_path")
    rows = _read_csv(path)
    fieldnames = set(rows[0].keys()) if rows else set(_read_csv_fieldnames(path))
    expected_login = context.get("account_scope", "")
    snapshot_cutoff = _parse_time(context.get("snapshot_cutoff_utc", ""))
    checks = [
        _check("signal_log_has_rows", len(rows) > 0, str(len(rows))),
        _check("signal_log_required_columns", REQUIRED_SIGNAL_COLUMNS <= fieldnames, ",".join(sorted(REQUIRED_SIGNAL_COLUMNS - fieldnames)) or "all present"),
    ]
    bad_dry_run = [index for index, row in enumerate(rows, start=2) if not _bool(row.get("dry_run"))]
    bad_broker = [index for index, row in enumerate(rows, start=2) if _bool(row.get("broker_action_allowed"))]
    bad_login = [index for index, row in enumerate(rows, start=2) if expected_login and str(row.get("account_login", "")).strip() != expected_login]
    bad_time = []
    bad_feature_time = []
    for index, row in enumerate(rows, start=2):
        timestamp = _parse_time(row.get("timestamp_utc", ""))
        m5_time = _parse_time(row.get("m5_bar_time", ""))
        if timestamp is None or (snapshot_cutoff is not None and timestamp > snapshot_cutoff):
            bad_time.append(index)
        if timestamp is not None and m5_time is not None and m5_time > timestamp:
            bad_feature_time.append(index)
    checks.extend(
        [
            _check("signal_log_all_dry_run_true", not bad_dry_run, _bad_rows_detail(bad_dry_run)),
            _check("signal_log_all_broker_action_false", not bad_broker, _bad_rows_detail(bad_broker)),
            _check("signal_log_account_matches_lane", not bad_login, _bad_rows_detail(bad_login) if bad_login else expected_login),
            _check("signal_log_historical_utc_not_future_cutoff", not bad_time, _bad_rows_detail(bad_time)),
            _check("signal_log_m5_bar_time_not_after_decision_time", not bad_feature_time, _bad_rows_detail(bad_feature_time)),
        ]
    )
    return {"rows": len(rows), "checks": checks}


def _validate_shadow_tap(source: dict[str, Any]) -> dict[str, Any]:
    rows = _read_csv(source.get("source_path"))
    bad_dry_run = [index for index, row in enumerate(rows, start=2) if not _bool(row.get("ea_dry_run"))]
    bad_broker = [index for index, row in enumerate(rows, start=2) if _bool(row.get("ea_broker_action_allowed"))]
    bad_ml_auth = [index for index, row in enumerate(rows, start=2) if _bool(row.get("ml_broker_action_authorized"))]
    return {
        "rows": len(rows),
        "checks": [
            _check("shadow_tap_has_rows", len(rows) > 0, str(len(rows))),
            _check("shadow_tap_all_ea_dry_run_true", not bad_dry_run, _bad_rows_detail(bad_dry_run)),
            _check("shadow_tap_all_ea_broker_action_false", not bad_broker, _bad_rows_detail(bad_broker)),
            _check("shadow_tap_all_ml_broker_action_authorized_false", not bad_ml_auth, _bad_rows_detail(bad_ml_auth)),
        ],
    }


def _copy_source_files(source_files: dict[str, dict[str, Any]], raw_replay_root: Path, terminal_root: Path) -> list[dict[str, Any]]:
    copied: list[dict[str, Any]] = []
    for item in source_files.values():
        source_path = Path(item["source_path"])
        relative = item["relative_path"]
        destination = raw_replay_root / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_path, destination)
        copied.append(
            {
                "name": item["name"],
                "role": item["role"],
                "source_path": str(source_path),
                "copied_path": str(destination),
                "sha256": _sha256(destination),
                "relative_path": str(relative),
            }
        )
    return copied


def _write_quarantined_observer_rows(rows: list[dict[str, str]], context: dict[str, Any], signal_source: dict[str, Any]) -> Path:
    output = context["normalized_csv"]
    output.parent.mkdir(parents=True, exist_ok=True)
    extras = [
        "source_type",
        "label_status",
        "candidate_trainable",
        "training_authorized",
        "python_demo_predictions_authorized",
        "ea_consumption_authorized",
        "broker_action_authorized",
        "replay_lane_id",
        "replay_imported_at_utc",
        "source_signal_log_sha256",
    ]
    fieldnames = list(rows[0].keys()) + [item for item in extras if item not in rows[0]]
    imported_at = _utc_now()
    source_sha = signal_source.get("actual_sha256") or _sha256(Path(signal_source["source_path"]))
    with output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            out = dict(row)
            out.update(
                {
                    "source_type": SOURCE_TYPE,
                    "label_status": LABEL_STATUS,
                    "candidate_trainable": "false",
                    "training_authorized": "false",
                    "python_demo_predictions_authorized": "false",
                    "ea_consumption_authorized": "false",
                    "broker_action_authorized": "false",
                    "replay_lane_id": context["selected_lane_id"],
                    "replay_imported_at_utc": imported_at,
                    "source_signal_log_sha256": source_sha,
                }
            )
            writer.writerow(out)
    return output


def _hash_checks(source_files: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    checks: list[dict[str, Any]] = []
    for item in source_files.values():
        path = Path(item["source_path"])
        actual = _sha256(path) if path.exists() else ""
        item["actual_sha256"] = actual
        expected = str(item.get("expected_sha256", ""))
        check_name = f"{_safe_name(str(item.get('relative_path', item['name'])))}_hash_matches_c54"
        checks.append(_check(check_name, bool(expected) and expected == actual, actual or "missing"))
    return checks


def _manifest_rows(source_files: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for item in sorted(source_files.values(), key=lambda value: (value["role"], value["name"])):
        path = Path(item["source_path"])
        rows.append(
            {
                "name": item["name"],
                "role": item["role"],
                "relative_path": str(item.get("relative_path", item["name"])),
                "path": str(path),
                "exists": path.exists(),
                "rows": _row_count(path) if path.suffix.lower() == ".csv" else "",
                "size_bytes": path.stat().st_size if path.exists() else 0,
                "sha256": item.get("actual_sha256") or (_sha256(path) if path.exists() else ""),
                "expected_sha256": item.get("expected_sha256", ""),
            }
        )
    return rows


def _role_for_name(name: str, path: Path) -> str:
    if name == SIGNAL_LOG_NAME:
        return "import_quarantined_observer_rows"
    if name == SHADOW_TAP_NAME:
        return "audit_only_shadow_safety"
    if name in {ORDER_LOG_NAME, MANAGEMENT_LOG_NAME, STARTUP_LOG_NAME}:
        return "audit_only_dry_run_provenance"
    if path.suffix.lower() == ".log":
        return "audit_only_terminal_log"
    return "audit_only_replay_output"


def _relative_source_path(source_path: Path, terminal_root: Path) -> Path:
    try:
        return source_path.resolve().relative_to(terminal_root.resolve())
    except (ValueError, OSError):
        return Path(_safe_name(source_path.name))


def _source_by_name(source_files: dict[str, dict[str, Any]], name: str) -> dict[str, Any]:
    for item in source_files.values():
        if item.get("name") == name:
            return item
    return {}


def _row_count(path: Any) -> int:
    if not path:
        return 0
    return len(_read_csv(Path(path)))


def _read_csv(path: Any) -> list[dict[str, str]]:
    if not path:
        return []
    path = Path(path)
    if not path.exists():
        return []
    text = _read_text(path)
    reader = csv.DictReader(io.StringIO(text))
    return [dict(row) for row in reader]


def _read_csv_fieldnames(path: Any) -> list[str]:
    if not path:
        return []
    path = Path(path)
    if not path.exists():
        return []
    text = _read_text(path)
    reader = csv.DictReader(io.StringIO(text))
    return list(reader.fieldnames or [])


def _read_text(path: Path) -> str:
    data = path.read_bytes()
    if data.startswith((b"\xff\xfe", b"\xfe\xff")):
        return data.decode("utf-16", errors="replace")
    if data.count(b"\x00") > max(8, len(data) // 10):
        return data.decode("utf-16-le", errors="replace")
    return data.decode("utf-8-sig", errors="replace")


def _parse_time(value: Any) -> datetime | None:
    text = str(value or "").strip()
    if not text:
        return None
    try:
        if "." in text.split(" ", 1)[0]:
            return datetime.strptime(text, "%Y.%m.%d %H:%M:%S").replace(tzinfo=timezone.utc)
        return parse_utc(text)
    except (ValueError, TypeError):
        return None


def _bad_rows_detail(rows: list[int]) -> str:
    if not rows:
        return "0"
    sample = ",".join(str(item) for item in rows[:10])
    suffix = "" if len(rows) <= 10 else f" (+{len(rows) - 10} more)"
    return f"{len(rows)} bad rows: {sample}{suffix}"


def _commands(root: Path) -> dict[str, str]:
    python = _quote(sys.executable)
    script = _quote(str(root / "scripts" / "c56_import_strategy_tester_replay_observer.py"))
    root_arg = _quote(str(root))
    return {"regenerate_c56_import": f"{python} {script} --root {root_arg}"}


def _next_allowed_stage(status: str) -> str:
    if status == STATUS_IMPORTED:
        return (
            "Replay evidence is imported as quarantined observer-only data. "
            "Do not use it for C03 gates, training, Python demo predictions, EA consumption, or broker action without a separate promotion review."
        )
    return "Fix replay import validation failures before copying or using replay evidence."


def _write_status(status_json: Path, payload: dict[str, Any]) -> None:
    status_json.parent.mkdir(parents=True, exist_ok=True)
    status_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    status_json.with_suffix(".md").write_text(render_strategy_tester_replay_observer_import_md(payload), encoding="utf-8")


def _update_pointer(pointer_path: Path, payload: dict[str, Any]) -> None:
    if not pointer_path.exists():
        return
    pointer = _read_json(pointer_path)
    pointer["c56_replay_import_report"] = payload["outputs"]["status_report_json"]
    pointer["c56_replay_import_status"] = payload["status"]
    pointer["c56_replay_import_source_type"] = SOURCE_TYPE
    pointer["c56_replay_import_label_status"] = LABEL_STATUS
    pointer["c56_replay_quarantined_observer_csv"] = payload["outputs"]["quarantined_observer_csv"]
    pointer["training_authorized"] = False
    pointer["python_demo_predictions_authorized"] = False
    pointer["ea_consumption_authorized"] = False
    pointer["broker_action_authorized"] = False
    _write_json_atomic(pointer_path, pointer)


def _check(name: str, passed: bool, detail: str) -> dict[str, Any]:
    return {"check": name, "passed": bool(passed), "detail": str(detail)}


def _bool(value: Any) -> bool:
    return str(value or "").strip().casefold() == "true"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _read_json(path_or_text: str | Path) -> dict[str, Any]:
    if not path_or_text:
        return {}
    path = Path(path_or_text)
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _safe_name(value: str) -> str:
    return "".join(ch if ch.isalnum() or ch in "._-" else "_" for ch in value).strip("_") or "unnamed"


def _quote(value: str) -> str:
    return f'"{value}"' if " " in value else value
