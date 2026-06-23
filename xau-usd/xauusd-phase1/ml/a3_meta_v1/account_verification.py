from __future__ import annotations

import json
import re
import subprocess
import sys
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from .account_registry import MT5AccountRegistry, load_mt5_account_registry
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


DEFAULT_OUTPUT_JSON = Path("outputs") / "reports" / "C02_ACCOUNT_VERIFICATION_MATRIX.json"
ProcessProvider = Callable[[], list[RunningProcess]]
ClientFactory = Callable[[], Any]
TerminalExists = Callable[[str], bool]


def verify_account_read_only(
    root: Path,
    registry_path: Path,
    account_label: str,
    process_provider: ProcessProvider | None = None,
    client_factory: ClientFactory | None = None,
    terminal_exists: TerminalExists | None = None,
) -> dict[str, Any]:
    root = root.resolve()
    registry = load_mt5_account_registry(registry_path)
    accounts = registry.by_label()
    if account_label not in accounts:
        return _unknown_account_record(account_label)
    account = accounts[account_label]
    process_provider = process_provider or list_running_processes
    client_factory = client_factory or ReadOnlyMT5Client.from_installed_package
    terminal_exists = terminal_exists or (lambda value: Path(value).exists())

    checks: list[dict[str, Any]] = []
    warnings: list[dict[str, str]] = []
    runtime_audit: dict[str, Any] = {}
    metadata: dict[str, Any] = {}
    before_processes: list[RunningProcess] = []
    after_initialize_processes: list[RunningProcess] = []
    after_shutdown_processes: list[RunningProcess] = []
    mt5_initialize_attempted = False
    mt5_initialized = False
    client: Any | None = None

    exists_result = verify_terminal_executable_exists(account, terminal_exists(account.terminal_exe))
    checks.append(asdict(exists_result))
    if not exists_result.passed:
        return _record(
            account=account,
            stage_status=exists_result,
            checks=checks,
            warnings=warnings,
            before_processes=before_processes,
            after_initialize_processes=after_initialize_processes,
            after_shutdown_processes=after_shutdown_processes,
            mt5_initialize_attempted=mt5_initialize_attempted,
            mt5_initialized=mt5_initialized,
            runtime_audit=runtime_audit,
            metadata=metadata,
        )

    try:
        before_processes = process_provider()
    except Exception as exc:
        return _record(
            account=account,
            stage_status=_fail(account, "PROCESS_ENUMERATION_FAILED", str(exc)),
            checks=checks,
            warnings=warnings,
            before_processes=before_processes,
            after_initialize_processes=after_initialize_processes,
            after_shutdown_processes=after_shutdown_processes,
            mt5_initialize_attempted=mt5_initialize_attempted,
            mt5_initialized=mt5_initialized,
            runtime_audit=runtime_audit,
            metadata=metadata,
        )
    process_result = verify_terminal_already_running(account, before_processes)
    checks.append(asdict(process_result))
    if not process_result.passed:
        return _record(
            account=account,
            stage_status=process_result,
            checks=checks,
            warnings=warnings,
            before_processes=before_processes,
            after_initialize_processes=after_initialize_processes,
            after_shutdown_processes=after_shutdown_processes,
            mt5_initialize_attempted=mt5_initialize_attempted,
            mt5_initialized=mt5_initialized,
            runtime_audit=runtime_audit,
            metadata=metadata,
        )

    try:
        client = client_factory()
    except Exception as exc:
        return _record(
            account=account,
            stage_status=_fail(account, "MT5_PACKAGE_UNAVAILABLE", str(exc)),
            checks=checks,
            warnings=warnings,
            before_processes=before_processes,
            after_initialize_processes=after_initialize_processes,
            after_shutdown_processes=after_shutdown_processes,
            mt5_initialize_attempted=mt5_initialize_attempted,
            mt5_initialized=mt5_initialized,
            runtime_audit=runtime_audit,
            metadata=metadata,
        )

    try:
        mt5_initialize_attempted = True
        mt5_initialized = bool(client.initialize(MT5ConnectionSpec(account.terminal_exe, account.portable)))
        if not mt5_initialized:
            detail = _safe_last_error(client)
            return _record(
                account=account,
                stage_status=_fail(account, "MT5_INITIALIZE_FAILED", detail),
                checks=checks,
                warnings=warnings,
                before_processes=before_processes,
                after_initialize_processes=after_initialize_processes,
                after_shutdown_processes=after_shutdown_processes,
                mt5_initialize_attempted=mt5_initialize_attempted,
                mt5_initialized=mt5_initialized,
                runtime_audit=runtime_audit,
                metadata=metadata,
            )
        after_initialize_processes = process_provider()
        launch_result = verify_no_new_terminal_process(account, before_processes, after_initialize_processes)
        checks.append(asdict(launch_result))
        if not launch_result.passed:
            return _record(
                account=account,
                stage_status=launch_result,
                checks=checks,
                warnings=warnings,
                before_processes=before_processes,
                after_initialize_processes=after_initialize_processes,
                after_shutdown_processes=after_shutdown_processes,
                mt5_initialize_attempted=mt5_initialize_attempted,
                mt5_initialized=mt5_initialized,
                runtime_audit=runtime_audit,
                metadata=metadata,
            )

        runtime_before = _runtime_ticket_snapshot(client, account.symbol)
        identity_result = verify_mt5_identity(account, registry.common, client)
        checks.append(asdict(identity_result))
        metadata = _safe_metadata_summary(client, account.symbol)
        runtime_after = _runtime_ticket_snapshot(client, account.symbol)
        runtime_audit = {
            "before_identity": runtime_before,
            "after_identity": runtime_after,
        }
        drift = _runtime_drift(runtime_before, runtime_after)
        if drift:
            runtime_audit["drift"] = drift
            if account.account_label == "A3":
                return _record(
                    account=account,
                    stage_status=_fail(account, "A3_RUNTIME_ACTIVITY_DURING_VERIFICATION", ",".join(drift)),
                    checks=checks,
                    warnings=warnings,
                    before_processes=before_processes,
                    after_initialize_processes=after_initialize_processes,
                    after_shutdown_processes=after_shutdown_processes,
                    mt5_initialize_attempted=mt5_initialize_attempted,
                    mt5_initialized=mt5_initialized,
                    runtime_audit=runtime_audit,
                    metadata=metadata,
                )
            warnings.append({"code": "EXTERNAL_RUNTIME_ACTIVITY_OBSERVED", "detail": ",".join(drift)})
        if not identity_result.passed:
            return _record(
                account=account,
                stage_status=identity_result,
                checks=checks,
                warnings=warnings,
                before_processes=before_processes,
                after_initialize_processes=after_initialize_processes,
                after_shutdown_processes=after_shutdown_processes,
                mt5_initialize_attempted=mt5_initialize_attempted,
                mt5_initialized=mt5_initialized,
                runtime_audit=runtime_audit,
                metadata=metadata,
            )
        return _record(
            account=account,
            stage_status=_pass(account, "ACCOUNT_VERIFICATION_PASS", "account, terminal, symbol, and runtime audit verified"),
            checks=checks,
            warnings=warnings,
            before_processes=before_processes,
            after_initialize_processes=after_initialize_processes,
            after_shutdown_processes=after_shutdown_processes,
            mt5_initialize_attempted=mt5_initialize_attempted,
            mt5_initialized=mt5_initialized,
            runtime_audit=runtime_audit,
            metadata=metadata,
        )
    except Exception as exc:
        return _record(
            account=account,
            stage_status=_fail(account, "ACCOUNT_VERIFICATION_EXCEPTION", str(exc)),
            checks=checks,
            warnings=warnings,
            before_processes=before_processes,
            after_initialize_processes=after_initialize_processes,
            after_shutdown_processes=after_shutdown_processes,
            mt5_initialize_attempted=mt5_initialize_attempted,
            mt5_initialized=mt5_initialized,
            runtime_audit=runtime_audit,
            metadata=metadata,
        )
    finally:
        if mt5_initialized and client is not None:
            try:
                client.shutdown()
            finally:
                try:
                    after_shutdown_processes = process_provider()
                except Exception as exc:
                    warnings.append({"code": "PROCESS_ENUMERATION_AFTER_SHUTDOWN_FAILED", "detail": str(exc)})


def generate_account_verification_matrix(
    root: Path,
    registry_path: Path | None = None,
    output_json: Path | None = None,
    account_labels: tuple[str, ...] | list[str] | None = None,
    python_executable: str | None = None,
    worker_script: Path | None = None,
) -> Path:
    root = root.resolve()
    registry_path = (registry_path or root / "config" / "ml" / "mt5_accounts.yaml").resolve()
    output_json = (output_json or root / DEFAULT_OUTPUT_JSON).resolve()
    output_md = output_json.with_suffix(".md")
    registry = load_mt5_account_registry(registry_path)
    labels = tuple(account_labels or [account.account_label for account in registry.accounts])
    python_executable = python_executable or sys.executable
    worker_script = (worker_script or root / "scripts" / "c02_verify_mt5_accounts.py").resolve()
    records = [
        _run_worker(python_executable, worker_script, root, registry_path, label)
        for label in labels
    ]
    status = "PASS" if records and all(record.get("status") == "PASS" for record in records) else "FAIL_CLOSED"
    payload: dict[str, Any] = {
        "status": status,
        "stage": "C02-01",
        "created_at_utc": _utc_now(),
        "registry_path": str(registry_path),
        "boundary": {
            "mt5_connection_attempted": any(record.get("mt5_initialize_attempted") for record in records),
            "data_exported": False,
            "model_training_authorized": False,
            "broker_action_authorized": False,
            "terminal_runtime_change_authorized": False,
            "worker_process_isolation": True,
        },
        "accounts_requested": list(labels),
        "account_records": records,
        "next_allowed_stage": "C02-02 bars/ticks export only if every account record is PASS",
    }
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    output_md.write_text(render_account_verification_matrix_md(payload), encoding="utf-8")
    return output_json


def render_account_verification_matrix_md(payload: dict[str, Any]) -> str:
    rows = [
        {
            "Account": record.get("account_label", ""),
            "Scope": record.get("account_scope", ""),
            "Status": record.get("status", ""),
            "Code": record.get("code", ""),
            "Detail": record.get("detail", ""),
        }
        for record in payload.get("account_records", [])
    ]
    return "\n".join(
        [
            "# C02 Account Verification Matrix",
            "",
            f"Overall status: {payload['status']}",
            "",
            "## Boundary",
            "",
            "- Stage: C02-01 account verification only.",
            f"- MT5 connection attempted: {str(payload['boundary']['mt5_connection_attempted']).lower()}.",
            "- Data exported: false.",
            "- Model training authorized: false.",
            "- Broker action authorized: false.",
            "- Terminal runtime change authorized: false.",
            "- Worker process isolation: true.",
            "",
            "## Accounts",
            "",
            _table(rows, ["Account", "Scope", "Status", "Code", "Detail"]),
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
) -> dict[str, Any]:
    command = [
        python_executable,
        str(worker_script),
        "--root",
        str(root),
        "--registry",
        str(registry_path),
        "--worker-account",
        account_label,
    ]
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
            "worker_returncode": completed.returncode,
        }


def _record(
    *,
    account: Any,
    stage_status: VerificationResult,
    checks: list[dict[str, Any]],
    warnings: list[dict[str, str]],
    before_processes: list[RunningProcess],
    after_initialize_processes: list[RunningProcess],
    after_shutdown_processes: list[RunningProcess],
    mt5_initialize_attempted: bool,
    mt5_initialized: bool,
    runtime_audit: dict[str, Any],
    metadata: dict[str, Any],
) -> dict[str, Any]:
    return {
        "account_label": account.account_label,
        "account_scope": account.account_scope,
        "expected_login": account.expected_login,
        "terminal_exe": account.terminal_exe,
        "portable": account.portable,
        "role": account.role,
        "symbol": account.symbol,
        "status": stage_status.status,
        "code": stage_status.code,
        "detail": stage_status.detail,
        "checks": checks,
        "warnings": warnings,
        "terminal_process_pids_before": _matching_pids(account.terminal_exe, before_processes),
        "terminal_process_pids_after_initialize": _matching_pids(account.terminal_exe, after_initialize_processes),
        "terminal_process_pids_after_shutdown": _matching_pids(account.terminal_exe, after_shutdown_processes),
        "mt5_initialize_attempted": mt5_initialize_attempted,
        "mt5_initialized": mt5_initialized,
        "data_exported": False,
        "broker_action_authorized": False,
        "model_training_authorized": False,
        "runtime_audit": runtime_audit,
        "metadata": metadata,
    }


def _unknown_account_record(account_label: str) -> dict[str, Any]:
    return {
        "account_label": account_label,
        "account_scope": "",
        "status": "FAIL_CLOSED",
        "code": "UNKNOWN_ACCOUNT_LABEL",
        "detail": "account label not present in registry",
        "mt5_initialize_attempted": False,
        "mt5_initialized": False,
        "data_exported": False,
        "broker_action_authorized": False,
        "model_training_authorized": False,
    }


def _runtime_ticket_snapshot(client: Any, symbol: str) -> dict[str, Any]:
    return {
        "position_tickets": _ticket_set(_safe_call(lambda: client.positions_get(symbol=symbol))),
        "pending_order_tickets": _ticket_set(_safe_call(lambda: client.orders_get(symbol=symbol))),
    }


def _runtime_drift(before: dict[str, Any], after: dict[str, Any]) -> list[str]:
    drift = []
    for key in ("position_tickets", "pending_order_tickets"):
        if before.get(key, {}).get("tickets") != after.get(key, {}).get("tickets"):
            drift.append(key)
    return drift


def _safe_metadata_summary(client: Any, symbol: str) -> dict[str, Any]:
    account_info = _safe_call(client.account_info)
    terminal_info = _safe_call(client.terminal_info)
    symbol_info = _safe_call(lambda: client.symbol_info(symbol))
    version = _safe_call(client.version)
    return {
        "mt5_package_version": _json_safe(version),
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
            "path": _redact_path(_field(terminal_info, "path")),
            "data_path": _redact_path(_field(terminal_info, "data_path")),
            "commondata_path": _redact_path(_field(terminal_info, "commondata_path")),
            "connected": _field(terminal_info, "connected"),
            "build": _field(terminal_info, "build"),
            "maxbars": _field(terminal_info, "maxbars"),
            "trade_allowed": _field(terminal_info, "trade_allowed"),
        },
        "symbol": {
            "name": symbol,
            "visible": _field(symbol_info, "visible"),
            "point": _field(symbol_info, "point"),
            "digits": _field(symbol_info, "digits"),
            "trade_tick_size": _field(symbol_info, "trade_tick_size"),
            "trade_tick_value": _field(symbol_info, "trade_tick_value"),
            "trade_contract_size": _field(symbol_info, "trade_contract_size"),
            "trade_stops_level": _field(symbol_info, "trade_stops_level"),
            "trade_freeze_level": _field(symbol_info, "trade_freeze_level"),
            "volume_min": _field(symbol_info, "volume_min"),
            "volume_step": _field(symbol_info, "volume_step"),
        },
    }


def _ticket_set(rows: Any) -> dict[str, Any]:
    if rows is None:
        return {"available": False, "tickets": []}
    try:
        tickets = sorted(str(_field(row, "ticket")) for row in rows if _field(row, "ticket") is not None)
    except TypeError:
        tickets = []
    return {"available": True, "tickets": tickets}


def _safe_last_error(client: Any) -> str:
    value = _safe_call(client.last_error)
    return json.dumps(_json_safe(value), sort_keys=True)


def _safe_call(callback: Callable[[], Any]) -> Any:
    try:
        return callback()
    except Exception:
        return None


def _field(value: Any, name: str) -> Any:
    if value is None:
        return None
    if isinstance(value, dict):
        return value.get(name)
    return getattr(value, name, None)


def _matching_pids(expected_exe: str, processes: list[RunningProcess]) -> list[int]:
    expected = _normalize_path(expected_exe)
    return sorted(process.pid for process in processes if _normalize_path(process.exe) == expected)


def _normalize_path(value: str) -> str:
    return str(value).replace("\\", "/").rstrip("/").casefold()


def _redact_path(value: Any) -> Any:
    if value is None:
        return None
    return re.sub(r"(?i)([A-Z]:[\\/]+Users[\\/]+)[^\\/]+", r"\1<USER>", str(value))


def _json_safe(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if hasattr(value, "_asdict"):
        return _json_safe(value._asdict())
    return str(value)


def _pass(account: Any, code: str, detail: str) -> VerificationResult:
    return VerificationResult("PASS", code, account.account_label, account.account_scope, detail)


def _fail(account: Any, code: str, detail: str) -> VerificationResult:
    return VerificationResult("FAIL_CLOSED", code, account.account_label, account.account_scope, detail)


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _table(rows: list[dict[str, str]], columns: list[str]) -> str:
    if not rows:
        return "No rows."
    header = "| " + " | ".join(columns) + " |"
    separator = "| " + " | ".join("---" for _ in columns) + " |"
    body = ["| " + " | ".join(str(row.get(column, "")).replace("|", "\\|") for column in columns) + " |" for row in rows]
    return "\n".join([header, separator, *body])
