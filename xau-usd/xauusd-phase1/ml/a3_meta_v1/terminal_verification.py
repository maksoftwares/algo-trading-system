from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import PureWindowsPath
from typing import Any

from .account_registry import MT5AccountSpec, MT5CommonConfig


DEMO_TRADE_MODE_VALUES = {0, "0", "DEMO", "ACCOUNT_TRADE_MODE_DEMO"}


@dataclass(frozen=True)
class RunningProcess:
    pid: int
    exe: str


@dataclass(frozen=True)
class VerificationResult:
    status: str
    code: str
    account_label: str
    account_scope: str
    detail: str

    @property
    def passed(self) -> bool:
        return self.status == "PASS"


def verify_terminal_already_running(
    account: MT5AccountSpec,
    processes: list[RunningProcess],
) -> VerificationResult:
    matching = _matching_processes(account.terminal_exe, processes)
    if not matching:
        return _fail(account, "TERMINAL_NOT_ALREADY_RUNNING", "expected terminal executable is not already running")
    return _pass(account, "TERMINAL_PROCESS_ALREADY_RUNNING", f"matching_pids={','.join(str(p.pid) for p in matching)}")


def verify_no_new_terminal_process(
    account: MT5AccountSpec,
    before: list[RunningProcess],
    after: list[RunningProcess],
) -> VerificationResult:
    before_pids = {process.pid for process in _matching_processes(account.terminal_exe, before)}
    after_pids = {process.pid for process in _matching_processes(account.terminal_exe, after)}
    new_pids = sorted(after_pids - before_pids)
    if new_pids:
        return _fail(account, "UNEXPECTED_TERMINAL_LAUNCH", f"new_pids={','.join(str(pid) for pid in new_pids)}")
    return _pass(account, "NO_NEW_TERMINAL_PROCESS", f"matching_pids={','.join(str(pid) for pid in sorted(after_pids))}")


def verify_terminal_executable_exists(account: MT5AccountSpec, exists: bool) -> VerificationResult:
    if not exists:
        return _fail(account, "TERMINAL_EXECUTABLE_NOT_FOUND", f"terminal_exe={account.terminal_exe!r}")
    return _pass(account, "TERMINAL_EXECUTABLE_EXISTS", f"terminal_exe={account.terminal_exe!r}")


def verify_mt5_identity(
    account: MT5AccountSpec,
    common: MT5CommonConfig,
    client: Any,
) -> VerificationResult:
    account_info = client.account_info()
    if account_info is None:
        return _fail(account, "ACCOUNT_INFO_UNAVAILABLE", "account_info returned None")
    terminal_info = client.terminal_info()
    if terminal_info is None:
        return _fail(account, "TERMINAL_INFO_UNAVAILABLE", "terminal_info returned None")
    login = str(_field(account_info, "login", ""))
    if login != account.expected_login:
        return _fail(account, "ACCOUNT_LOGIN_MISMATCH", f"expected={account.expected_login} observed={login}")
    server = str(_field(account_info, "server", ""))
    if re.fullmatch(common.expected_server_regex, server) is None:
        return _fail(account, "ACCOUNT_SERVER_MISMATCH", f"server={server!r}")
    if common.require_demo_trade_mode and not _is_demo_trade_mode(_field(account_info, "trade_mode", None), server):
        return _fail(account, "ACCOUNT_NOT_DEMO", "trade_mode/server did not prove demo mode")
    connected = _field(terminal_info, "connected", True)
    if connected is False:
        return _fail(account, "TERMINAL_NOT_CONNECTED", "terminal_info.connected is false")
    observed_terminal_path = _field(terminal_info, "path", "")
    if not _terminal_root_matches(str(observed_terminal_path), account.terminal_exe):
        return _fail(account, "TERMINAL_PATH_MISMATCH", f"observed={observed_terminal_path!r}")
    if account.expected_data_path:
        observed_data_path = _field(terminal_info, "data_path", "")
        if not _same_windows_path(str(observed_data_path), account.expected_data_path):
            return _fail(account, "TERMINAL_DATA_PATH_MISMATCH", f"observed={observed_data_path!r}")
    symbol_info = client.symbol_info(account.symbol)
    if symbol_info is None:
        return _fail(account, "SYMBOL_NOT_ALREADY_AVAILABLE", f"symbol={account.symbol}")
    visible = _field(symbol_info, "visible", True)
    if visible is False:
        return _fail(account, "SYMBOL_NOT_ALREADY_AVAILABLE", f"symbol={account.symbol} is not visible/available")
    point = _field(symbol_info, "point", None)
    digits = _field(symbol_info, "digits", None)
    if point is None or float(point) <= 0:
        return _fail(account, "SYMBOL_POINT_INVALID", f"point={point!r}")
    if digits is None:
        return _fail(account, "SYMBOL_DIGITS_INVALID", "digits unavailable")
    try:
        if int(digits) < 0:
            return _fail(account, "SYMBOL_DIGITS_INVALID", f"digits={digits!r}")
    except (TypeError, ValueError):
        return _fail(account, "SYMBOL_DIGITS_INVALID", f"digits={digits!r}")
    return _pass(account, "ACCOUNT_TERMINAL_SYMBOL_VERIFIED", "read-only identity checks passed")


def _matching_processes(expected_exe: str, processes: list[RunningProcess]) -> list[RunningProcess]:
    return [process for process in processes if _same_windows_path(process.exe, expected_exe)]


def _same_windows_path(left: str, right: str) -> bool:
    return _normalize_windows_path(left) == _normalize_windows_path(right)


def _terminal_root_matches(observed_path: str, terminal_exe: str) -> bool:
    if not observed_path:
        return False
    expected_exe = str(PureWindowsPath(terminal_exe))
    expected_root = str(PureWindowsPath(terminal_exe).parent)
    return _same_windows_path(observed_path, expected_root) or _same_windows_path(observed_path, expected_exe)


def _normalize_windows_path(value: str) -> str:
    text = str(PureWindowsPath(value)).replace("\\", "/").rstrip("/")
    return text.casefold()


def _field(value: Any, name: str, default: Any = None) -> Any:
    if isinstance(value, dict):
        return value.get(name, default)
    return getattr(value, name, default)


def _is_demo_trade_mode(value: Any, server: str) -> bool:
    if value in DEMO_TRADE_MODE_VALUES:
        return True
    text = str(value).upper()
    return text in DEMO_TRADE_MODE_VALUES or "DEMO" in server.upper()


def _pass(account: MT5AccountSpec, code: str, detail: str) -> VerificationResult:
    return VerificationResult("PASS", code, account.account_label, account.account_scope, detail)


def _fail(account: MT5AccountSpec, code: str, detail: str) -> VerificationResult:
    return VerificationResult("FAIL_CLOSED", code, account.account_label, account.account_scope, detail)
