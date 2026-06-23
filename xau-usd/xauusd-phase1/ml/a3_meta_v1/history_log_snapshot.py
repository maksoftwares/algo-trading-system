from __future__ import annotations

import csv
import json
import os
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from .account_registry import load_mt5_account_registry
from .contract_scope import approved_log_catalog_entries
from .market_data_export import (
    DEFAULT_OUTPUT_ROOT,
    _field,
    _file_record,
    _git_short,
    _iso,
    _json_safe,
    _overall_status,
    _require_utc,
    _safe_call,
    _sha256_file,
    _table,
    _utc_now,
    _write_json_atomic,
    parse_utc,
)
from .mt5_readonly import MT5ConnectionSpec, ReadOnlyMT5Client
from .processes import list_running_processes
from .terminal_verification import (
    RunningProcess,
    verify_mt5_identity,
    verify_no_new_terminal_process,
    verify_terminal_already_running,
    verify_terminal_executable_exists,
)


DEFAULT_REPORT_JSON = Path("outputs") / "reports" / "C02_HISTORY_LOG_SNAPSHOT_REPORT.json"
ProcessProvider = Callable[[], list[RunningProcess]]
ClientFactory = Callable[[], Any]
TerminalExists = Callable[[str], bool]


def snapshot_account_history_logs_read_only(
    root: Path,
    registry_path: Path,
    account_label: str,
    requested_start_utc: datetime,
    snapshot_cutoff_utc: datetime,
    dataset_version: str,
    output_root: Path | None = None,
    process_provider: ProcessProvider | None = None,
    client_factory: ClientFactory | None = None,
    terminal_exists: TerminalExists | None = None,
) -> dict[str, Any]:
    root = root.resolve()
    output_root = (output_root or root / DEFAULT_OUTPUT_ROOT).resolve()
    registry = load_mt5_account_registry(registry_path)
    accounts = registry.by_label()
    if account_label not in accounts:
        return _unknown_record(account_label, dataset_version)
    account = accounts[account_label]
    requested_start_utc = _require_utc(requested_start_utc, "requested_start_utc")
    snapshot_cutoff_utc = _require_utc(snapshot_cutoff_utc, "snapshot_cutoff_utc")
    process_provider = process_provider or list_running_processes
    client_factory = client_factory or ReadOnlyMT5Client.from_installed_package
    terminal_exists = terminal_exists or (lambda value: Path(value).exists())
    account_root = output_root / dataset_version / "raw" / account.account_label
    checks: list[dict[str, Any]] = []
    files: list[dict[str, Any]] = []
    log_records: list[dict[str, Any]] = []
    history_counts: dict[str, int] = {}
    client: Any | None = None
    mt5_initialized = False
    mt5_initialize_attempted = False

    exists_result = verify_terminal_executable_exists(account, terminal_exists(account.terminal_exe))
    checks.append(_asdict(exists_result))
    if not exists_result.passed:
        return _record(account, dataset_version, exists_result.status, exists_result.code, exists_result.detail, checks=checks)
    try:
        before_processes = process_provider()
    except Exception as exc:
        return _record(account, dataset_version, "FAIL_CLOSED", "PROCESS_ENUMERATION_FAILED", str(exc), checks=checks)
    process_result = verify_terminal_already_running(account, before_processes)
    checks.append(_asdict(process_result))
    if not process_result.passed:
        return _record(account, dataset_version, process_result.status, process_result.code, process_result.detail, checks=checks)
    try:
        client = client_factory()
    except Exception as exc:
        return _record(account, dataset_version, "FAIL_CLOSED", "MT5_PACKAGE_UNAVAILABLE", str(exc), checks=checks)

    try:
        mt5_initialize_attempted = True
        mt5_initialized = bool(client.initialize(MT5ConnectionSpec(account.terminal_exe, account.portable)))
        if not mt5_initialized:
            return _record(account, dataset_version, "FAIL_CLOSED", "MT5_INITIALIZE_FAILED", str(_safe_call(client.last_error)), checks=checks)
        launch_result = verify_no_new_terminal_process(account, before_processes, process_provider())
        checks.append(_asdict(launch_result))
        if not launch_result.passed:
            return _record(account, dataset_version, launch_result.status, launch_result.code, launch_result.detail, checks=checks)
        identity_result = verify_mt5_identity(account, registry.common, client)
        checks.append(_asdict(identity_result))
        if not identity_result.passed:
            return _record(account, dataset_version, identity_result.status, identity_result.code, identity_result.detail, checks=checks)

        orders = _history_rows(client.history_orders_get(requested_start_utc, snapshot_cutoff_utc, group=f"*{account.symbol}*"), account, dataset_version)
        deals = _history_rows(client.history_deals_get(requested_start_utc, snapshot_cutoff_utc, group=f"*{account.symbol}*"), account, dataset_version)
        positions = _history_rows(client.positions_get(symbol=account.symbol), account, dataset_version)
        pending_orders = _history_rows(client.orders_get(symbol=account.symbol), account, dataset_version)
        files.append(_write_csv_dynamic(account_root / "history" / "orders.csv", orders))
        files.append(_write_csv_dynamic(account_root / "history" / "deals.csv", deals))
        files.append(_write_csv_dynamic(account_root / "history" / "positions_audit.csv", positions))
        files.append(_write_csv_dynamic(account_root / "history" / "pending_orders_audit.csv", pending_orders))
        history_counts = {
            "orders": len(orders),
            "deals": len(deals),
            "positions_audit": len(positions),
            "pending_orders_audit": len(pending_orders),
        }

        terminal_info = client.terminal_info()
        terminal_files = Path(str(_field(terminal_info, "data_path"))) / "MQL5" / "Files"
        files_root = Path(account.files_roots[0]) if account.files_roots else terminal_files
        for entry in _catalog_entries_for_account(root, account.account_label, root / account.log_catalog):
            record = _stable_copy_log(files_root, account_root / "logs", entry)
            log_records.append(record)
            if record.get("snapshot_path"):
                files.append(_file_record(Path(record["snapshot_path"]), record.get("row_count")))

        manifest = {
            "manifest_schema_version": "c02_history_log_snapshot_manifest_v1",
            "dataset_version": dataset_version,
            "created_at_utc": _utc_now(),
            "account_label": account.account_label,
            "account_scope": account.account_scope,
            "requested_start_utc": _iso(requested_start_utc),
            "snapshot_cutoff_utc": _iso(snapshot_cutoff_utc),
            "history_counts": history_counts,
            "log_records": log_records,
            "files": files,
            "training_authorized": False,
            "broker_action_authorized": False,
        }
        manifest_file = _write_json_atomic(account_root / "manifest" / "HISTORY_LOG_MANIFEST.json", manifest)
        files.append(manifest_file)
        return _record(
            account,
            dataset_version,
            "PASS",
            "HISTORY_LOG_SNAPSHOT_PASS",
            "history and configured runtime logs snapshotted read-only",
            checks=checks,
            files=files,
            history_counts=history_counts,
            log_records=log_records,
            mt5_initialize_attempted=mt5_initialize_attempted,
            mt5_initialized=mt5_initialized,
            output_root=account_root,
        )
    except Exception as exc:
        return _record(
            account,
            dataset_version,
            "FAIL_CLOSED",
            "HISTORY_LOG_SNAPSHOT_EXCEPTION",
            str(exc),
            checks=checks,
            files=files,
            history_counts=history_counts,
            log_records=log_records,
            mt5_initialize_attempted=mt5_initialize_attempted,
            mt5_initialized=mt5_initialized,
            output_root=account_root,
        )
    finally:
        if mt5_initialized and client is not None:
            client.shutdown()


def generate_history_log_snapshot_report(
    root: Path,
    registry_path: Path | None = None,
    requested_start_utc: datetime | None = None,
    snapshot_cutoff_utc: datetime | None = None,
    dataset_version: str | None = None,
    output_root: Path | None = None,
    report_json: Path | None = None,
    account_labels: tuple[str, ...] | list[str] | None = None,
    python_executable: str | None = None,
    worker_script: Path | None = None,
) -> Path:
    root = root.resolve()
    pointer = _load_pointer(root)
    registry_path = (registry_path or root / "config" / "ml" / "mt5_accounts.yaml").resolve()
    registry = load_mt5_account_registry(registry_path)
    requested_start_utc = requested_start_utc or parse_utc(pointer["requested_start_utc"])
    snapshot_cutoff_utc = snapshot_cutoff_utc or parse_utc(pointer["snapshot_cutoff_utc"])
    requested_start_utc = _require_utc(requested_start_utc, "requested_start_utc")
    snapshot_cutoff_utc = _require_utc(snapshot_cutoff_utc, "snapshot_cutoff_utc")
    dataset_version = dataset_version or pointer["dataset_version"]
    output_root = (output_root or root / DEFAULT_OUTPUT_ROOT).resolve()
    report_json = (report_json or root / DEFAULT_REPORT_JSON).resolve()
    report_md = report_json.with_suffix(".md")
    labels = tuple(account_labels or [account.account_label for account in registry.accounts])
    python_executable = python_executable or sys.executable
    worker_script = (worker_script or root / "scripts" / "c02_snapshot_history_logs.py").resolve()
    records = [
        _run_worker(
            python_executable,
            worker_script,
            root,
            registry_path,
            label,
            requested_start_utc,
            snapshot_cutoff_utc,
            dataset_version,
            output_root,
        )
        for label in labels
    ]
    status = _overall_status(records)
    payload: dict[str, Any] = {
        "status": status,
        "stage": "C02-03",
        "created_at_utc": _utc_now(),
        "dataset_version": dataset_version,
        "requested_start_utc": _iso(requested_start_utc),
        "snapshot_cutoff_utc": _iso(snapshot_cutoff_utc),
        "output_root": str(output_root / dataset_version),
        "boundary": {
            "data_exported": any(record.get("data_exported") for record in records),
            "model_training_authorized": False,
            "broker_action_authorized": False,
            "terminal_runtime_change_authorized": False,
            "worker_process_isolation": True,
            "exported_sources": ["orders", "deals", "positions_audit", "pending_orders_audit", "runtime_logs"],
        },
        "account_records": records,
        "next_allowed_stage": "C02-04 normalized source tables",
    }
    report_json.parent.mkdir(parents=True, exist_ok=True)
    report_json.write_text(json.dumps(_json_safe(payload), indent=2), encoding="utf-8")
    report_md.write_text(render_history_log_snapshot_report_md(payload), encoding="utf-8")
    pointer["history_log_snapshot_status"] = status
    pointer["history_log_snapshot_report"] = str(report_json)
    pointer["training_authorized"] = False
    _write_json_atomic(root / "outputs" / "reports" / "C02_DATASET_POINTER.json", pointer)
    return report_json


def render_history_log_snapshot_report_md(payload: dict[str, Any]) -> str:
    rows = [
        {
            "Account": record.get("account_label", ""),
            "Status": record.get("status", ""),
            "Code": record.get("code", ""),
            "Orders": str(record.get("history_counts", {}).get("orders", 0)),
            "Deals": str(record.get("history_counts", {}).get("deals", 0)),
            "Logs": str(len(record.get("log_records", []))),
        }
        for record in payload.get("account_records", [])
    ]
    return "\n".join(
        [
            "# C02 History/Log Snapshot Report",
            "",
            f"Overall status: {payload['status']}",
            "",
            "## Boundary",
            "",
            "- Stage: C02-03 history and runtime log snapshots.",
            f"- Data exported: {str(payload['boundary']['data_exported']).lower()}.",
            "- Model training authorized: false.",
            "- Broker action authorized: false.",
            "- Terminal runtime change authorized: false.",
            "- Worker process isolation: true.",
            "",
            "## Snapshot",
            "",
            f"- Dataset version: {payload['dataset_version']}",
            f"- Requested start UTC: {payload['requested_start_utc']}",
            f"- Snapshot cutoff UTC: {payload['snapshot_cutoff_utc']}",
            "",
            "## Accounts",
            "",
            _table(rows, ["Account", "Status", "Code", "Orders", "Deals", "Logs"]),
            "",
            "## Next",
            "",
            payload["next_allowed_stage"],
            "",
        ]
    )


def _run_worker(
    python_executable: str,
    worker_script: Path,
    root: Path,
    registry_path: Path,
    account_label: str,
    requested_start_utc: datetime,
    snapshot_cutoff_utc: datetime,
    dataset_version: str,
    output_root: Path,
) -> dict[str, Any]:
    command = [
        python_executable,
        str(worker_script),
        "--root",
        str(root),
        "--registry",
        str(registry_path),
        "--requested-start-utc",
        _iso(requested_start_utc),
        "--snapshot-cutoff-utc",
        _iso(snapshot_cutoff_utc),
        "--dataset-version",
        dataset_version,
        "--output-root",
        str(output_root),
        "--worker-account",
        account_label,
    ]
    completed = subprocess.run(command, capture_output=True, text=True, check=False)
    try:
        return json.loads(completed.stdout.strip())
    except json.JSONDecodeError:
        return {
            "account_label": account_label,
            "status": "FAIL_CLOSED",
            "code": "WORKER_OUTPUT_INVALID",
            "detail": (completed.stderr or completed.stdout or "worker emitted no JSON").strip(),
            "data_exported": False,
            "worker_returncode": completed.returncode,
        }


def _stable_copy_log(files_root: Path, output_logs_root: Path, entry: dict[str, Any]) -> dict[str, Any]:
    source = files_root / entry["filename"]
    target = output_logs_root / entry["logical_source_name"] / entry["filename"]
    record = {
        "logical_source_name": entry["logical_source_name"],
        "source_type": entry["source_type"],
        "family": entry.get("family", ""),
        "append_active": bool(entry.get("append_active", False)),
        "original_path": str(source),
        "snapshot_path": "",
        "copy_status": "",
        "sha256": "",
        "row_count": 0,
    }
    if not source.exists():
        record["copy_status"] = "SOURCE_MISSING"
        return record
    target.parent.mkdir(parents=True, exist_ok=True)
    for attempt in range(3):
        before = source.stat()
        tmp = target.with_name(target.name + ".tmp")
        shutil.copy2(source, tmp)
        after = source.stat()
        stable = before.st_size == after.st_size and before.st_mtime_ns == after.st_mtime_ns
        if stable or attempt == 2:
            os.replace(tmp, target)
            record.update(
                {
                    "snapshot_path": str(target),
                    "copy_status": "STABLE_COPY" if stable else "VOLATILE_SOURCE_SNAPSHOT",
                    "source_size_before": before.st_size,
                    "source_size_after": after.st_size,
                    "source_mtime_before_utc": _iso(datetime.fromtimestamp(before.st_mtime, timezone.utc)),
                    "source_mtime_after_utc": _iso(datetime.fromtimestamp(after.st_mtime, timezone.utc)),
                    "sha256": _sha256_file(target),
                    "row_count": _csv_row_count(target) if target.suffix.lower() == ".csv" else 0,
                }
            )
            return record
        tmp.unlink(missing_ok=True)
        time.sleep(0.2)
    return record


def _history_rows(records: Any, account: Any, dataset_version: str) -> list[dict[str, Any]]:
    rows = []
    if records is None:
        return rows
    for record in list(records):
        row = _object_to_row(record)
        row.update(
            {
                "dataset_version": dataset_version,
                "account_scope": account.account_scope,
                "account_label": account.account_label,
                "symbol_filter": account.symbol,
            }
        )
        rows.append(row)
    return rows


def _object_to_row(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if hasattr(value, "_asdict"):
        return {str(key): _json_safe(item) for key, item in value._asdict().items()}
    return {
        key: _json_safe(getattr(value, key))
        for key in dir(value)
        if not key.startswith("_") and not callable(getattr(value, key))
    }


def _write_csv_dynamic(path: Path, rows: list[dict[str, Any]]) -> dict[str, Any]:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = sorted({key for row in rows for key in row}) or ["dataset_version", "account_scope", "account_label", "symbol_filter"]
    tmp = path.with_name(path.name + ".tmp")
    with tmp.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(tmp, path)
    return _file_record(path, len(rows))


def _load_log_catalog(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("schema_version") != "c02_log_catalog_v1":
        raise ValueError(f"unsupported log catalog schema: {path}")
    entries = payload.get("entries")
    if not isinstance(entries, list):
        raise ValueError(f"log catalog entries must be a list: {path}")
    return payload


def _catalog_entries_for_account(root: Path, account_label: str, path: Path) -> list[dict[str, Any]]:
    catalog = _load_log_catalog(path)
    entries = [dict(entry) for entry in catalog["entries"]]
    seen = {(entry.get("logical_source_name", ""), entry.get("filename", "")) for entry in entries}
    for entry in approved_log_catalog_entries(root, account_label):
        key = (entry.get("logical_source_name", ""), entry.get("filename", ""))
        if key not in seen:
            entries.append(entry)
            seen.add(key)
    return entries


def _load_pointer(root: Path) -> dict[str, Any]:
    pointer = root / "outputs" / "reports" / "C02_DATASET_POINTER.json"
    return json.loads(pointer.read_text(encoding="utf-8"))


def _csv_row_count(path: Path) -> int:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return max(sum(1 for _ in csv.reader(handle)) - 1, 0)


def _record(
    account: Any,
    dataset_version: str,
    status: str,
    code: str,
    detail: str,
    *,
    checks: list[dict[str, Any]] | None = None,
    files: list[dict[str, Any]] | None = None,
    history_counts: dict[str, int] | None = None,
    log_records: list[dict[str, Any]] | None = None,
    mt5_initialize_attempted: bool = False,
    mt5_initialized: bool = False,
    output_root: Path | None = None,
) -> dict[str, Any]:
    return {
        "account_label": account.account_label,
        "account_scope": account.account_scope,
        "dataset_version": dataset_version,
        "status": status,
        "code": code,
        "detail": detail,
        "checks": checks or [],
        "files": files or [],
        "history_counts": history_counts or {},
        "log_records": log_records or [],
        "mt5_initialize_attempted": mt5_initialize_attempted,
        "mt5_initialized": mt5_initialized,
        "data_exported": status == "PASS",
        "model_training_authorized": False,
        "broker_action_authorized": False,
        "output_root": str(output_root) if output_root else "",
    }


def _unknown_record(account_label: str, dataset_version: str) -> dict[str, Any]:
    return {
        "account_label": account_label,
        "account_scope": "",
        "dataset_version": dataset_version,
        "status": "FAIL_CLOSED",
        "code": "UNKNOWN_ACCOUNT_LABEL",
        "detail": "account label not present in registry",
        "data_exported": False,
        "model_training_authorized": False,
        "broker_action_authorized": False,
    }


def _asdict(value: Any) -> dict[str, Any]:
    if hasattr(value, "__dataclass_fields__"):
        return {key: getattr(value, key) for key in value.__dataclass_fields__}
    return dict(value)
