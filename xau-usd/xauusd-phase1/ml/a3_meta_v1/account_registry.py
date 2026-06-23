from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any


DEFAULT_REGISTRY_PATH = Path("config") / "ml" / "mt5_accounts.yaml"
EXPECTED_ACCOUNT_SCOPES = ("1025742", "1033030", "1033669")
EXPECTED_ACCOUNT_LABELS = ("A1", "A2", "A3")
SECRET_KEY_PARTS = ("password", "token", "secret", "key")


class RegistryError(ValueError):
    """Raised when the MT5 account registry is unsafe or malformed."""


@dataclass(frozen=True)
class MT5CommonConfig:
    symbol: str
    expected_server_regex: str
    require_demo_trade_mode: bool
    require_existing_terminal_process: bool
    allow_mt5_login_call: bool
    allow_symbol_select_call: bool
    export_timezone: str
    snapshot_safety_lag_minutes: int


@dataclass(frozen=True)
class MT5AccountSpec:
    account_scope: str
    account_label: str
    expected_login: str
    terminal_exe: str
    expected_data_path: str | None
    portable: bool
    role: str
    symbol: str
    files_roots: tuple[str, ...]
    log_catalog: str


@dataclass(frozen=True)
class MT5AccountRegistry:
    schema_version: str
    common: MT5CommonConfig
    accounts: tuple[MT5AccountSpec, ...]

    def by_label(self) -> dict[str, MT5AccountSpec]:
        return {account.account_label: account for account in self.accounts}

    def by_scope(self) -> dict[str, MT5AccountSpec]:
        return {account.account_scope: account for account in self.accounts}


def load_mt5_account_registry(path: Path) -> MT5AccountRegistry:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return parse_mt5_account_registry(payload)


def parse_mt5_account_registry(payload: dict[str, Any]) -> MT5AccountRegistry:
    _reject_secret_keys(payload)
    schema_version = _required_str(payload, "schema_version")
    if schema_version != "mt5_multi_account_registry_v1":
        raise RegistryError(f"unsupported registry schema_version {schema_version!r}")

    common_payload = _required_map(payload, "common")
    common = MT5CommonConfig(
        symbol=_required_str(common_payload, "symbol"),
        expected_server_regex=_required_str(common_payload, "expected_server_regex"),
        require_demo_trade_mode=_required_bool(common_payload, "require_demo_trade_mode"),
        require_existing_terminal_process=_required_bool(common_payload, "require_existing_terminal_process"),
        allow_mt5_login_call=_required_bool(common_payload, "allow_mt5_login_call"),
        allow_symbol_select_call=_required_bool(common_payload, "allow_symbol_select_call"),
        export_timezone=_required_str(common_payload, "export_timezone"),
        snapshot_safety_lag_minutes=_required_int(common_payload, "snapshot_safety_lag_minutes"),
    )
    if common.symbol != "XAUUSD":
        raise RegistryError("C02 registry must be XAUUSD-only")
    if common.export_timezone != "UTC":
        raise RegistryError("C02 registry must export in UTC")
    if common.allow_mt5_login_call:
        raise RegistryError("MT5 login calls are prohibited")
    if common.allow_symbol_select_call:
        raise RegistryError("MT5 symbol_select calls are prohibited")
    re.compile(common.expected_server_regex)

    accounts_payload = _required_map(payload, "accounts")
    accounts = tuple(_parse_account(label, value, common.symbol) for label, value in sorted(accounts_payload.items()))
    _validate_account_set(accounts)
    return MT5AccountRegistry(schema_version=schema_version, common=common, accounts=accounts)


def _parse_account(label: str, payload: Any, common_symbol: str) -> MT5AccountSpec:
    if not isinstance(payload, dict):
        raise RegistryError(f"account {label!r} must be a map")
    account_scope = _required_str(payload, "account_scope")
    account_label = _required_str(payload, "account_label")
    expected_login = _required_str(payload, "expected_login")
    if account_label != label:
        raise RegistryError(f"account key {label!r} must match account_label {account_label!r}")
    if account_scope != expected_login:
        raise RegistryError(f"{account_label} account_scope must be the numeric expected_login")
    if not account_scope.isdigit():
        raise RegistryError(f"{account_label} account_scope must be numeric")
    symbol = _required_str(payload, "symbol")
    if symbol != common_symbol:
        raise RegistryError(f"{account_label} symbol must equal common symbol {common_symbol}")
    files_roots = payload.get("files_roots", [])
    if not isinstance(files_roots, list) or not all(isinstance(value, str) for value in files_roots):
        raise RegistryError(f"{account_label} files_roots must be a list of strings")
    expected_data_path = payload.get("expected_data_path")
    if expected_data_path is not None and not isinstance(expected_data_path, str):
        raise RegistryError(f"{account_label} expected_data_path must be a string or null")
    return MT5AccountSpec(
        account_scope=account_scope,
        account_label=account_label,
        expected_login=expected_login,
        terminal_exe=_required_str(payload, "terminal_exe"),
        expected_data_path=expected_data_path,
        portable=_required_bool(payload, "portable"),
        role=_required_str(payload, "role"),
        symbol=symbol,
        files_roots=tuple(files_roots),
        log_catalog=_required_str(payload, "log_catalog"),
    )


def _validate_account_set(accounts: tuple[MT5AccountSpec, ...]) -> None:
    scopes = tuple(account.account_scope for account in accounts)
    labels = tuple(account.account_label for account in accounts)
    if scopes != EXPECTED_ACCOUNT_SCOPES:
        raise RegistryError(f"registry account scopes must be {EXPECTED_ACCOUNT_SCOPES}, got {scopes}")
    if labels != EXPECTED_ACCOUNT_LABELS:
        raise RegistryError(f"registry account labels must be {EXPECTED_ACCOUNT_LABELS}, got {labels}")
    if len(set(scopes)) != len(scopes):
        raise RegistryError("account scopes must be unique")
    if len(set(account.terminal_exe for account in accounts)) != len(accounts):
        raise RegistryError("terminal_exe values must be unique per account")


def _reject_secret_keys(value: Any, path: str = "") -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            key_text = str(key).lower()
            if any(part in key_text for part in SECRET_KEY_PARTS):
                raise RegistryError(f"secret-like registry key is prohibited: {path}{key}")
            _reject_secret_keys(item, f"{path}{key}.")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _reject_secret_keys(item, f"{path}{index}.")


def _required_map(payload: dict[str, Any], key: str) -> dict[str, Any]:
    value = payload.get(key)
    if not isinstance(value, dict):
        raise RegistryError(f"missing or invalid map field {key!r}")
    return value


def _required_str(payload: dict[str, Any], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value:
        raise RegistryError(f"missing or invalid string field {key!r}")
    return value


def _required_bool(payload: dict[str, Any], key: str) -> bool:
    value = payload.get(key)
    if not isinstance(value, bool):
        raise RegistryError(f"missing or invalid boolean field {key!r}")
    return value


def _required_int(payload: dict[str, Any], key: str) -> int:
    value = payload.get(key)
    if not isinstance(value, int):
        raise RegistryError(f"missing or invalid integer field {key!r}")
    return value
