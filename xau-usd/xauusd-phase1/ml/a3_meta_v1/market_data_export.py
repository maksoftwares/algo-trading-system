from __future__ import annotations

import csv
import hashlib
import json
import os
import subprocess
import sys
from dataclasses import asdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable, Iterable

from .account_registry import load_mt5_account_registry
from .mt5_readonly import MT5ConnectionSpec, ReadOnlyMT5Client
from .processes import list_running_processes
from .terminal_verification import (
    RunningProcess,
    VerificationResult,
    verify_mt5_identity,
    verify_no_new_terminal_process,
    verify_terminal_already_running,
    verify_terminal_executable_exists,
)


DEFAULT_OUTPUT_ROOT = Path("data") / "ml" / "a3_meta_v1" / "c02"
DEFAULT_REPORT_JSON = Path("outputs") / "reports" / "C02_BAR_TICK_EXPORT_REPORT.json"
TIMEFRAMES = ("M5", "M15", "H1", "H4", "D1")
ProcessProvider = Callable[[], list[RunningProcess]]
ClientFactory = Callable[[], Any]
TerminalExists = Callable[[str], bool]


def export_account_bars_ticks_read_only(
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
    max_tick_days: int | None = None,
) -> dict[str, Any]:
    root = root.resolve()
    output_root = (output_root or root / DEFAULT_OUTPUT_ROOT).resolve()
    registry = load_mt5_account_registry(registry_path)
    accounts = registry.by_label()
    if account_label not in accounts:
        return _unknown_account_record(account_label, dataset_version)
    account = accounts[account_label]
    requested_start_utc = _require_utc(requested_start_utc, "requested_start_utc")
    snapshot_cutoff_utc = _require_utc(snapshot_cutoff_utc, "snapshot_cutoff_utc")
    if requested_start_utc >= snapshot_cutoff_utc:
        return _record(account, dataset_version, "FAIL_CLOSED", "INVALID_EXPORT_WINDOW", "requested start must be before cutoff")

    process_provider = process_provider or list_running_processes
    client_factory = client_factory or ReadOnlyMT5Client.from_installed_package
    terminal_exists = terminal_exists or (lambda value: Path(value).exists())
    checks: list[dict[str, Any]] = []
    files: list[dict[str, Any]] = []
    coverage: dict[str, Any] = {"bars": {}, "ticks": {"chunks": []}}
    account_root = output_root / dataset_version / "raw" / account.account_label
    mt5_initialize_attempted = False
    mt5_initialized = False
    client: Any | None = None

    exists_result = verify_terminal_executable_exists(account, terminal_exists(account.terminal_exe))
    checks.append(asdict(exists_result))
    if not exists_result.passed:
        return _record(account, dataset_version, exists_result.status, exists_result.code, exists_result.detail, checks=checks)
    try:
        before_processes = process_provider()
    except Exception as exc:
        return _record(account, dataset_version, "FAIL_CLOSED", "PROCESS_ENUMERATION_FAILED", str(exc), checks=checks)
    process_result = verify_terminal_already_running(account, before_processes)
    checks.append(asdict(process_result))
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
            return _record(
                account,
                dataset_version,
                "FAIL_CLOSED",
                "MT5_INITIALIZE_FAILED",
                json.dumps(_json_safe(_safe_call(client.last_error)), sort_keys=True),
                checks=checks,
                mt5_initialize_attempted=mt5_initialize_attempted,
                mt5_initialized=mt5_initialized,
            )
        after_initialize = process_provider()
        launch_result = verify_no_new_terminal_process(account, before_processes, after_initialize)
        checks.append(asdict(launch_result))
        if not launch_result.passed:
            return _record(
                account,
                dataset_version,
                launch_result.status,
                launch_result.code,
                launch_result.detail,
                checks=checks,
                mt5_initialize_attempted=mt5_initialize_attempted,
                mt5_initialized=mt5_initialized,
            )
        identity_result = verify_mt5_identity(account, registry.common, client)
        checks.append(asdict(identity_result))
        if not identity_result.passed:
            return _record(
                account,
                dataset_version,
                identity_result.status,
                identity_result.code,
                identity_result.detail,
                checks=checks,
                mt5_initialize_attempted=mt5_initialize_attempted,
                mt5_initialized=mt5_initialized,
            )

        metadata_path = account_root / "metadata" / "mt5_metadata.json"
        metadata = _metadata_summary(client, account.symbol)
        files.append(_write_json_atomic(metadata_path, metadata))

        for timeframe in TIMEFRAMES:
            timeframe_value = client.timeframe_value(timeframe)
            rates = client.copy_rates_range(account.symbol, timeframe_value, requested_start_utc, snapshot_cutoff_utc)
            rows = _bar_rows(rates, account, timeframe, dataset_version, snapshot_cutoff_utc)
            path = account_root / "bars" / f"{account.symbol}_{timeframe}.csv"
            files.append(_write_csv_atomic(path, rows, _bar_fields()))
            coverage["bars"][timeframe] = _coverage_summary(rows, "time_utc")

        tick_start = requested_start_utc
        if max_tick_days is not None:
            tick_start = max(tick_start, snapshot_cutoff_utc - timedelta(days=max_tick_days))
        tick_flags = client.copy_ticks_all_flags()
        for start, end in _daily_windows(tick_start, snapshot_cutoff_utc):
            ticks = client.copy_ticks_range(account.symbol, start, end, tick_flags)
            rows = _tick_rows(ticks, account, dataset_version)
            day = start.strftime("%Y%m%d")
            path = account_root / "ticks" / f"{account.symbol}_ticks_{day}.csv"
            files.append(_write_csv_atomic(path, rows, _tick_fields()))
            chunk = _coverage_summary(rows, "time_utc")
            chunk["chunk_start_utc"] = _iso(start)
            chunk["chunk_end_utc"] = _iso(end)
            chunk["file"] = str(path)
            coverage["ticks"]["chunks"].append(chunk)

        manifest = {
            "manifest_schema_version": "c02_bar_tick_export_manifest_v1",
            "dataset_version": dataset_version,
            "created_at_utc": _utc_now(),
            "account_label": account.account_label,
            "account_scope": account.account_scope,
            "symbol": account.symbol,
            "requested_start_utc": _iso(requested_start_utc),
            "snapshot_cutoff_utc": _iso(snapshot_cutoff_utc),
            "files": files,
            "coverage": coverage,
            "training_authorized": False,
            "broker_action_authorized": False,
        }
        manifest_file = _write_json_atomic(account_root / "manifest" / "BAR_TICK_MANIFEST.json", manifest)
        files.append(manifest_file)
        return _record(
            account,
            dataset_version,
            "PASS",
            "BAR_TICK_EXPORT_PASS",
            "bars and tick chunks exported read-only",
            checks=checks,
            files=files,
            coverage=coverage,
            mt5_initialize_attempted=mt5_initialize_attempted,
            mt5_initialized=mt5_initialized,
            output_root=account_root,
        )
    except Exception as exc:
        return _record(
            account,
            dataset_version,
            "FAIL_CLOSED",
            "BAR_TICK_EXPORT_EXCEPTION",
            str(exc),
            checks=checks,
            files=files,
            coverage=coverage,
            mt5_initialize_attempted=mt5_initialize_attempted,
            mt5_initialized=mt5_initialized,
            output_root=account_root,
        )
    finally:
        if mt5_initialized and client is not None:
            client.shutdown()


def generate_bar_tick_export_report(
    root: Path,
    registry_path: Path | None = None,
    requested_start_utc: datetime | None = None,
    output_root: Path | None = None,
    report_json: Path | None = None,
    account_labels: tuple[str, ...] | list[str] | None = None,
    max_tick_days: int | None = None,
    python_executable: str | None = None,
    worker_script: Path | None = None,
) -> Path:
    root = root.resolve()
    registry_path = (registry_path or root / "config" / "ml" / "mt5_accounts.yaml").resolve()
    registry = load_mt5_account_registry(registry_path)
    requested_start_utc = _require_utc(requested_start_utc or _default_requested_start(), "requested_start_utc")
    snapshot_cutoff_utc = _floor_to_minute(
        datetime.now(timezone.utc) - timedelta(minutes=registry.common.snapshot_safety_lag_minutes)
    )
    dataset_version = _dataset_version(root, registry_path, requested_start_utc, snapshot_cutoff_utc)
    output_root = (output_root or root / DEFAULT_OUTPUT_ROOT).resolve()
    report_json = (report_json or root / DEFAULT_REPORT_JSON).resolve()
    report_md = report_json.with_suffix(".md")
    labels = tuple(account_labels or [account.account_label for account in registry.accounts])
    python_executable = python_executable or sys.executable
    worker_script = (worker_script or root / "scripts" / "c02_export_mt5_market_data.py").resolve()
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
            max_tick_days,
        )
        for label in labels
    ]
    status = _overall_status(records)
    root_manifest_path = output_root / dataset_version / "ROOT_BAR_TICK_EXPORT_MANIFEST.json"
    root_manifest = {
        "manifest_schema_version": "c02_root_bar_tick_export_manifest_v1",
        "dataset_version": dataset_version,
        "created_at_utc": _utc_now(),
        "status": status,
        "requested_start_utc": _iso(requested_start_utc),
        "snapshot_cutoff_utc": _iso(snapshot_cutoff_utc),
        "accounts_requested": list(labels),
        "account_records": records,
        "training_authorized": False,
        "broker_action_authorized": False,
    }
    root_manifest_file = _write_json_atomic(root_manifest_path, root_manifest)
    payload: dict[str, Any] = {
        "status": status,
        "stage": "C02-02",
        "created_at_utc": _utc_now(),
        "dataset_version": dataset_version,
        "requested_start_utc": _iso(requested_start_utc),
        "snapshot_cutoff_utc": _iso(snapshot_cutoff_utc),
        "output_root": str(output_root / dataset_version),
        "root_manifest": root_manifest_file,
        "boundary": {
            "data_exported": any(record.get("data_exported") for record in records),
            "model_training_authorized": False,
            "broker_action_authorized": False,
            "terminal_runtime_change_authorized": False,
            "worker_process_isolation": True,
            "exported_sources": ["bars", "ticks", "mt5_metadata"],
        },
        "account_records": records,
        "next_allowed_stage": "C02-03 history/log snapshots after bars/ticks review",
    }
    report_json.parent.mkdir(parents=True, exist_ok=True)
    report_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    report_md.write_text(render_bar_tick_export_report_md(payload), encoding="utf-8")
    _write_json_atomic(root / "outputs" / "reports" / "C02_DATASET_POINTER.json", _dataset_pointer(payload))
    return report_json


def render_bar_tick_export_report_md(payload: dict[str, Any]) -> str:
    rows = [
        {
            "Account": record.get("account_label", ""),
            "Scope": record.get("account_scope", ""),
            "Status": record.get("status", ""),
            "Code": record.get("code", ""),
            "Bars": _bar_count_text(record),
            "Tick Chunks": str(len(record.get("coverage", {}).get("ticks", {}).get("chunks", []))),
        }
        for record in payload.get("account_records", [])
    ]
    return "\n".join(
        [
            "# C02 Bars/Ticks Export Report",
            "",
            f"Overall status: {payload['status']}",
            "",
            "## Boundary",
            "",
            "- Stage: C02-02 bars/ticks export.",
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
            f"- Output root: {payload['output_root']}",
            "",
            "## Accounts",
            "",
            _table(rows, ["Account", "Scope", "Status", "Code", "Bars", "Tick Chunks"]),
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
    max_tick_days: int | None,
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
    if max_tick_days is not None:
        command.extend(["--max-tick-days", str(max_tick_days)])
    completed = subprocess.run(command, capture_output=True, text=True, check=False)
    try:
        return json.loads(completed.stdout.strip())
    except json.JSONDecodeError:
        return {
            "account_label": account_label,
            "account_scope": "",
            "status": "FAIL_CLOSED",
            "code": "WORKER_OUTPUT_INVALID",
            "detail": (completed.stderr or completed.stdout or "worker emitted no JSON").strip(),
            "data_exported": False,
            "worker_returncode": completed.returncode,
        }


def _bar_rows(records: Any, account: Any, timeframe: str, dataset_version: str, cutoff: datetime) -> list[dict[str, Any]]:
    rows = []
    for item in _iter_records(records):
        timestamp = _record_value(item, "time")
        time_utc = datetime.fromtimestamp(int(timestamp), timezone.utc)
        rows.append(
            {
                "dataset_version": dataset_version,
                "account_scope": account.account_scope,
                "account_label": account.account_label,
                "symbol": account.symbol,
                "timeframe": timeframe,
                "time_utc": _iso(time_utc),
                "open": _record_value(item, "open"),
                "high": _record_value(item, "high"),
                "low": _record_value(item, "low"),
                "close": _record_value(item, "close"),
                "tick_volume": _record_value(item, "tick_volume"),
                "spread": _record_value(item, "spread"),
                "real_volume": _record_value(item, "real_volume"),
                "export_cutoff_utc": _iso(cutoff),
            }
        )
    return rows


def _tick_rows(records: Any, account: Any, dataset_version: str) -> list[dict[str, Any]]:
    rows = []
    point = 0.01
    for item in _iter_records(records):
        time_msc = _record_value(item, "time_msc")
        timestamp = float(time_msc) / 1000.0 if time_msc not in (None, "") else float(_record_value(item, "time"))
        bid = _float_or_none(_record_value(item, "bid"))
        ask = _float_or_none(_record_value(item, "ask"))
        spread_price = ask - bid if ask is not None and bid is not None else None
        rows.append(
            {
                "dataset_version": dataset_version,
                "account_scope": account.account_scope,
                "account_label": account.account_label,
                "symbol": account.symbol,
                "time_utc": _iso(datetime.fromtimestamp(timestamp, timezone.utc)),
                "time_msc": time_msc,
                "bid": bid,
                "ask": ask,
                "last": _record_value(item, "last"),
                "volume": _record_value(item, "volume"),
                "volume_real": _record_value(item, "volume_real"),
                "flags": _record_value(item, "flags"),
                "spread_price": spread_price,
                "spread_points": spread_price / point if spread_price is not None else None,
            }
        )
    return rows


def _iter_records(records: Any) -> Iterable[Any]:
    if records is None:
        return []
    return list(records)


def _record_value(record: Any, name: str) -> Any:
    if isinstance(record, dict):
        return _scalar(record.get(name))
    try:
        return _scalar(record[name])
    except (KeyError, IndexError, TypeError, ValueError):
        return _scalar(getattr(record, name, None))


def _scalar(value: Any) -> Any:
    if hasattr(value, "item"):
        return value.item()
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return value


def _metadata_summary(client: Any, symbol: str) -> dict[str, Any]:
    account_info = _safe_call(client.account_info)
    terminal_info = _safe_call(client.terminal_info)
    symbol_info = _safe_call(lambda: client.symbol_info(symbol))
    return {
        "account": {
            "login": _field(account_info, "login"),
            "server": _field(account_info, "server"),
            "trade_mode": _field(account_info, "trade_mode"),
            "currency": _field(account_info, "currency"),
            "leverage": _field(account_info, "leverage"),
            "margin_mode": _field(account_info, "margin_mode"),
            "company": _field(account_info, "company"),
        },
        "terminal": {
            "path": _field(terminal_info, "path"),
            "data_path": _field(terminal_info, "data_path"),
            "commondata_path": _field(terminal_info, "commondata_path"),
            "connected": _field(terminal_info, "connected"),
            "build": _field(terminal_info, "build"),
            "maxbars": _field(terminal_info, "maxbars"),
        },
        "symbol": {
            "name": symbol,
            "visible": _field(symbol_info, "visible"),
            "point": _field(symbol_info, "point"),
            "digits": _field(symbol_info, "digits"),
            "trade_tick_size": _field(symbol_info, "trade_tick_size"),
            "trade_tick_value": _field(symbol_info, "trade_tick_value"),
            "trade_contract_size": _field(symbol_info, "trade_contract_size"),
        },
    }


def _coverage_summary(rows: list[dict[str, Any]], time_field: str) -> dict[str, Any]:
    times = [str(row.get(time_field, "")) for row in rows if row.get(time_field)]
    return {
        "row_count": len(rows),
        "min_time_utc": min(times) if times else "",
        "max_time_utc": max(times) if times else "",
        "coverage_status": "HAS_ROWS" if rows else "NO_ROWS",
    }


def _write_csv_atomic(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> dict[str, Any]:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    with tmp.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(tmp, path)
    return _file_record(path, len(rows))


def _write_json_atomic(path: Path, payload: dict[str, Any]) -> dict[str, Any]:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f"{path.name}.{os.getpid()}.tmp")
    with tmp.open("w", encoding="utf-8") as handle:
        handle.write(json.dumps(_json_safe(payload), indent=2))
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(tmp, path)
    return _file_record(path, None)


def _file_record(path: Path, row_count: int | None) -> dict[str, Any]:
    return {
        "path": str(path),
        "relative_path": path.name,
        "bytes": path.stat().st_size,
        "sha256": _sha256_file(path),
        "row_count": row_count,
    }


def _record(
    account: Any,
    dataset_version: str,
    status: str,
    code: str,
    detail: str,
    *,
    checks: list[dict[str, Any]] | None = None,
    files: list[dict[str, Any]] | None = None,
    coverage: dict[str, Any] | None = None,
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
        "coverage": coverage or {},
        "mt5_initialize_attempted": mt5_initialize_attempted,
        "mt5_initialized": mt5_initialized,
        "data_exported": status == "PASS",
        "model_training_authorized": False,
        "broker_action_authorized": False,
        "output_root": str(output_root) if output_root else "",
    }


def _unknown_account_record(account_label: str, dataset_version: str) -> dict[str, Any]:
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


def _overall_status(records: list[dict[str, Any]]) -> str:
    if records and all(record.get("status") == "PASS" for record in records):
        return "PASS"
    if any(record.get("status") == "FAIL_CLOSED" for record in records):
        return "FAIL_CLOSED"
    return "PARTIAL_EXPORT"


def _dataset_pointer(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "dataset_version": payload["dataset_version"],
        "status": payload["status"],
        "private_storage_root_alias": "xau-usd/xauusd-phase1/data/ml/a3_meta_v1/c02",
        "output_root": payload["output_root"],
        "root_manifest_sha256": payload["root_manifest"]["sha256"],
        "requested_start_utc": payload["requested_start_utc"],
        "snapshot_cutoff_utc": payload["snapshot_cutoff_utc"],
        "training_authorized": False,
    }


def _dataset_version(root: Path, registry_path: Path, start: datetime, cutoff: datetime) -> str:
    digest = hashlib.sha256()
    digest.update(registry_path.read_bytes())
    git = _git_short(root)
    return f"xauusd_c02_multiacct_{cutoff.strftime('%Y%m%d%H%M')}_g{git}_c{digest.hexdigest()[:8]}"


def _git_short(root: Path) -> str:
    completed = subprocess.run(["git", "rev-parse", "--short=8", "HEAD"], cwd=root.parent.parent, capture_output=True, text=True)
    if completed.returncode == 0:
        return completed.stdout.strip()
    return "nogit000"


def _daily_windows(start: datetime, end: datetime) -> list[tuple[datetime, datetime]]:
    windows = []
    cursor = start
    while cursor < end:
        next_midnight = datetime(cursor.year, cursor.month, cursor.day, tzinfo=timezone.utc) + timedelta(days=1)
        chunk_end = min(next_midnight, end)
        windows.append((cursor, chunk_end))
        cursor = chunk_end
    return windows


def _require_utc(value: datetime, name: str) -> datetime:
    if value.tzinfo is None or value.utcoffset() != timedelta(0):
        raise ValueError(f"{name} must be timezone-aware UTC")
    return value


def parse_utc(value: str) -> datetime:
    text = value.strip().replace("Z", "+00:00")
    parsed = datetime.fromisoformat(text)
    return _require_utc(parsed, "datetime")


def _floor_to_minute(value: datetime) -> datetime:
    return value.replace(second=0, microsecond=0)


def _default_requested_start() -> datetime:
    return datetime(2026, 6, 1, tzinfo=timezone.utc)


def _bar_fields() -> list[str]:
    return [
        "dataset_version",
        "account_scope",
        "account_label",
        "symbol",
        "timeframe",
        "time_utc",
        "open",
        "high",
        "low",
        "close",
        "tick_volume",
        "spread",
        "real_volume",
        "export_cutoff_utc",
    ]


def _tick_fields() -> list[str]:
    return [
        "dataset_version",
        "account_scope",
        "account_label",
        "symbol",
        "time_utc",
        "time_msc",
        "bid",
        "ask",
        "last",
        "volume",
        "volume_real",
        "flags",
        "spread_price",
        "spread_points",
    ]


def _bar_count_text(record: dict[str, Any]) -> str:
    bars = record.get("coverage", {}).get("bars", {})
    if not bars:
        return ""
    return ", ".join(f"{tf}:{bars.get(tf, {}).get('row_count', 0)}" for tf in TIMEFRAMES)


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _field(value: Any, name: str) -> Any:
    if value is None:
        return None
    if isinstance(value, dict):
        return value.get(name)
    return getattr(value, name, None)


def _float_or_none(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _safe_call(callback: Callable[[], Any]) -> Any:
    try:
        return callback()
    except Exception:
        return None


def _json_safe(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if hasattr(value, "_asdict"):
        return _json_safe(value._asdict())
    if hasattr(value, "item"):
        return _json_safe(value.item())
    return str(value)


def _iso(value: datetime) -> str:
    return value.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _utc_now() -> str:
    return _iso(datetime.now(timezone.utc))


def _table(rows: list[dict[str, str]], columns: list[str]) -> str:
    if not rows:
        return "No rows."
    header = "| " + " | ".join(columns) + " |"
    separator = "| " + " | ".join("---" for _ in columns) + " |"
    body = ["| " + " | ".join(str(row.get(column, "")).replace("|", "\\|") for column in columns) + " |" for row in rows]
    return "\n".join([header, separator, *body])
