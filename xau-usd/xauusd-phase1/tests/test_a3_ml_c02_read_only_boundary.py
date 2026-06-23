from __future__ import annotations

import json
import sys
from pathlib import Path
from types import SimpleNamespace

from phase2x_test_helpers import ROOT, load_script


if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ml.a3_meta_v1.account_registry import RegistryError, load_mt5_account_registry, parse_mt5_account_registry
from ml.a3_meta_v1.mt5_readonly import FORBIDDEN_MT5_CALLS, READ_ONLY_MT5_CALLS, ReadOnlyMT5Client, assert_read_only_method
from ml.a3_meta_v1.safety import scan_c02_python_safety
from ml.a3_meta_v1.terminal_verification import (
    RunningProcess,
    verify_mt5_identity,
    verify_no_new_terminal_process,
    verify_terminal_already_running,
)


REGISTRY = ROOT / "config" / "ml" / "mt5_accounts.yaml"


def test_c02_registry_uses_numeric_account_scopes_and_no_secret_keys() -> None:
    registry = load_mt5_account_registry(REGISTRY)

    assert [account.account_label for account in registry.accounts] == ["A1", "A2", "A3"]
    assert [account.account_scope for account in registry.accounts] == ["1025742", "1033030", "1033669"]
    assert all(account.account_scope == account.expected_login for account in registry.accounts)
    assert registry.common.allow_mt5_login_call is False
    assert registry.common.allow_symbol_select_call is False
    assert registry.common.symbol == "XAUUSD"

    raw = REGISTRY.read_text(encoding="utf-8").lower()
    for token in ("password", "secret", "api_key", "authorization_token"):
        assert token not in raw


def test_c02_registry_rejects_label_as_account_scope() -> None:
    payload = json.loads(REGISTRY.read_text(encoding="utf-8"))
    payload["accounts"]["A1"]["account_scope"] = "A1"

    try:
        parse_mt5_account_registry(payload)
    except RegistryError as exc:
        assert "numeric expected_login" in str(exc)
    else:
        raise AssertionError("registry accepted nonnumeric account_scope")


def test_c02_readonly_facade_exposes_only_allowlisted_methods() -> None:
    assert "initialize" in READ_ONLY_MT5_CALLS
    assert "history_deals_get" in READ_ONLY_MT5_CALLS
    assert "order_send" in FORBIDDEN_MT5_CALLS

    for name in READ_ONLY_MT5_CALLS:
        assert_read_only_method(name)
    for name in FORBIDDEN_MT5_CALLS:
        try:
            assert_read_only_method(name)
        except Exception as exc:
            assert "not in the C02 read-only allowlist" in str(exc) or "explicitly forbidden" in str(exc)
        else:
            raise AssertionError(f"forbidden MT5 call accepted: {name}")

    public_methods = {
        name
        for name in dir(ReadOnlyMT5Client)
        if not name.startswith("_") and callable(getattr(ReadOnlyMT5Client, name))
    }
    assert "order_send" not in public_methods
    assert "login" not in public_methods
    assert "symbol_select" not in public_methods
    assert "order_check" not in public_methods


def test_c02_safety_scan_has_no_forbidden_calls_outside_facade() -> None:
    findings = scan_c02_python_safety(ROOT / "ml" / "a3_meta_v1")

    assert findings == []


def test_c02_terminal_process_preflight_requires_existing_exact_path() -> None:
    account = load_mt5_account_registry(REGISTRY).by_label()["A2"]
    processes = [RunningProcess(pid=10, exe="C:/MT5PortableTier1BestEA/terminal64.exe")]

    assert verify_terminal_already_running(account, processes).passed
    assert verify_terminal_already_running(account, []).code == "TERMINAL_NOT_ALREADY_RUNNING"


def test_c02_terminal_process_preflight_detects_unexpected_launch() -> None:
    account = load_mt5_account_registry(REGISTRY).by_label()["A2"]
    before = [RunningProcess(pid=10, exe=account.terminal_exe)]
    after = [RunningProcess(pid=10, exe=account.terminal_exe), RunningProcess(pid=11, exe=account.terminal_exe)]

    result = verify_no_new_terminal_process(account, before, after)

    assert result.status == "FAIL_CLOSED"
    assert result.code == "UNEXPECTED_TERMINAL_LAUNCH"


def test_c02_identity_verification_fails_closed_on_mismatch() -> None:
    registry = load_mt5_account_registry(REGISTRY)
    account = registry.by_label()["A2"]
    good_client = _FakeClient(
        account_info={"login": "1033030", "server": "Capital.ComMena-Demo", "trade_mode": 0},
        terminal_info={"connected": True, "path": "C:/MT5PortableTier1BestEA", "data_path": "C:/MT5PortableTier1BestEA"},
        symbol_info={"point": 0.01, "digits": 2, "visible": True},
    )
    assert verify_mt5_identity(account, registry.common, good_client).passed

    bad_login = _FakeClient(
        account_info={"login": "1025742", "server": "Capital.ComMena-Demo", "trade_mode": 0},
        terminal_info={"connected": True, "path": "C:/MT5PortableTier1BestEA", "data_path": "C:/MT5PortableTier1BestEA"},
        symbol_info={"point": 0.01, "digits": 2, "visible": True},
    )
    assert verify_mt5_identity(account, registry.common, bad_login).code == "ACCOUNT_LOGIN_MISMATCH"

    bad_server = _FakeClient(
        account_info={"login": "1033030", "server": "Capital.ComMena-Live", "trade_mode": 0},
        terminal_info={"connected": True, "path": "C:/MT5PortableTier1BestEA", "data_path": "C:/MT5PortableTier1BestEA"},
        symbol_info={"point": 0.01, "digits": 2, "visible": True},
    )
    assert verify_mt5_identity(account, registry.common, bad_server).code == "ACCOUNT_SERVER_MISMATCH"

    missing_symbol = _FakeClient(
        account_info={"login": "1033030", "server": "Capital.ComMena-Demo", "trade_mode": 0},
        terminal_info={"connected": True, "path": "C:/MT5PortableTier1BestEA", "data_path": "C:/MT5PortableTier1BestEA"},
        symbol_info=None,
    )
    assert verify_mt5_identity(account, registry.common, missing_symbol).code == "SYMBOL_NOT_ALREADY_AVAILABLE"


def test_c02_boundary_report_states_no_connection_or_training(tmp_path: Path) -> None:
    module = load_script("generate_a3_ml_c02_read_only_boundary_report")
    output = module.generate_c02_read_only_boundary_report(
        ROOT,
        registry_path=REGISTRY,
        output_json=tmp_path / "C02_READ_ONLY_BOUNDARY_BUILD.json",
    )
    payload = json.loads(output.read_text(encoding="utf-8"))
    report = output.with_suffix(".md").read_text(encoding="utf-8")

    assert payload["status"] == "PASS"
    assert payload["boundary"]["mt5_connection_attempted"] is False
    assert payload["boundary"]["data_exported"] is False
    assert payload["boundary"]["model_training_authorized"] is False
    assert "MT5 connection attempted: false" in report
    assert "Data exported: false" in report


class _FakeClient:
    def __init__(self, *, account_info, terminal_info, symbol_info):
        self._account_info = _namespace(account_info)
        self._terminal_info = _namespace(terminal_info)
        self._symbol_info = _namespace(symbol_info)

    def account_info(self):
        return self._account_info

    def terminal_info(self):
        return self._terminal_info

    def symbol_info(self, symbol: str):
        assert symbol == "XAUUSD"
        return self._symbol_info


def _namespace(value):
    if value is None:
        return None
    return SimpleNamespace(**value)
