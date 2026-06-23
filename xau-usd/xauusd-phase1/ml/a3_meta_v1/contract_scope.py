from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any


BASE_FAMILY = "breakout_retest"
DEFAULT_CONFIG = Path("config") / "ml" / "a3_ml_contract_expansion.json"
SCHEMA_VERSION = "a3_ml_contract_expansion_v1"
KNOWN_EXPANSION_FAMILIES = {
    "round_number_retest",
    "session_extreme_retest",
    "rdguard",
    "rdstruct",
}
_FAMILY_PATTERN = re.compile(r"^[a-z0-9_]+$")


@dataclass(frozen=True)
class ContractScope:
    schema_version: str
    contract_expansion_authorized: bool
    review_reference: str
    allowed_families: tuple[str, ...]
    accounts: dict[str, tuple[dict[str, Any], ...]]

    @property
    def active_families(self) -> tuple[str, ...]:
        if not self.contract_expansion_authorized:
            return (BASE_FAMILY,)
        return _unique((BASE_FAMILY, *self.allowed_families))

    @property
    def scope_name(self) -> str:
        if not self.contract_expansion_authorized:
            return "breakout_retest_only"
        return "reviewer_approved_multi_family"


def load_contract_scope(root: Path, config_path: Path | None = None) -> ContractScope:
    root = root.resolve()
    path = (config_path or root / DEFAULT_CONFIG).resolve()
    if not path.exists():
        return _default_scope()
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("schema_version") != SCHEMA_VERSION:
        raise ValueError(f"unsupported contract expansion schema: {path}")
    authorized = bool(payload.get("contract_expansion_authorized", False))
    review_reference = str(payload.get("review_reference", "")).strip()
    allowed = tuple(_normalize_family(item) for item in payload.get("allowed_families", []))
    allowed = tuple(family for family in _unique(allowed) if family != BASE_FAMILY)
    if authorized:
        _validate_authorized_scope(path, review_reference, allowed)
    accounts = _account_entries(payload.get("accounts", {}), allowed if authorized else ())
    return ContractScope(
        schema_version=SCHEMA_VERSION,
        contract_expansion_authorized=authorized,
        review_reference=review_reference,
        allowed_families=allowed if authorized else (),
        accounts=accounts if authorized else {},
    )


def approved_log_catalog_entries(root: Path, account_label: str) -> list[dict[str, Any]]:
    scope = load_contract_scope(root)
    return [dict(entry) for entry in scope.accounts.get(account_label, ())]


def normalize_family_name(*values: Any) -> str:
    fallback = ""
    for value in values:
        text = str(value or "").strip().lower()
        if not text:
            continue
        if "breakout_retest" in text:
            return BASE_FAMILY
        if "round_number" in text or "symbol_normalized_round" in text or "round_retest" in text:
            return "round_number_retest"
        if "session_extreme" in text:
            return "session_extreme_retest"
        if "rdguard" in text:
            return "rdguard"
        if "rdstruct" in text:
            return "rdstruct"
        if text in KNOWN_EXPANSION_FAMILIES:
            return text
        if not fallback and _FAMILY_PATTERN.match(text):
            fallback = text
    return fallback


def _default_scope() -> ContractScope:
    return ContractScope(
        schema_version=SCHEMA_VERSION,
        contract_expansion_authorized=False,
        review_reference="",
        allowed_families=(),
        accounts={},
    )


def _account_entries(accounts: Any, allowed_families: tuple[str, ...]) -> dict[str, tuple[dict[str, Any], ...]]:
    if not isinstance(accounts, dict):
        return {}
    allowed = set(allowed_families)
    result: dict[str, tuple[dict[str, Any], ...]] = {}
    for label, config in accounts.items():
        entries = []
        for entry in config.get("entries", []) if isinstance(config, dict) else []:
            family = normalize_family_name(entry.get("family"), entry.get("filename"), entry.get("logical_source_name"))
            if family not in allowed:
                raise ValueError(f"extra catalog entry family is not approved for {label}: {family}")
            source_type = str(entry.get("source_type", ""))
            if "signal_log" not in source_type:
                raise ValueError(f"extra catalog entry must be signal-log source only for {label}: {source_type}")
            normalized = {
                "logical_source_name": str(entry.get("logical_source_name", "")).strip(),
                "source_type": source_type,
                "filename": str(entry.get("filename", "")).strip(),
                "schema_version": str(entry.get("schema_version", "csv_runtime_log_v1") or "csv_runtime_log_v1"),
                "family": family,
                "append_active": bool(entry.get("append_active", False)),
            }
            if not normalized["logical_source_name"] or not normalized["filename"]:
                raise ValueError(f"extra catalog entry missing logical_source_name or filename for {label}")
            entries.append(normalized)
        if entries:
            result[str(label)] = tuple(entries)
    return result


def _validate_authorized_scope(path: Path, review_reference: str, allowed: tuple[str, ...]) -> None:
    if not review_reference:
        raise ValueError(f"contract expansion requires review_reference: {path}")
    if not allowed:
        raise ValueError(f"contract expansion requires at least one allowed family: {path}")
    unknown = sorted(set(allowed) - KNOWN_EXPANSION_FAMILIES)
    if unknown:
        raise ValueError(f"unknown contract expansion families in {path}: {', '.join(unknown)}")


def _normalize_family(value: Any) -> str:
    text = str(value or "").strip().lower()
    if not text or not _FAMILY_PATTERN.match(text):
        raise ValueError(f"invalid family name: {value!r}")
    return text


def _unique(values: tuple[str, ...]) -> tuple[str, ...]:
    seen: set[str] = set()
    output = []
    for value in values:
        if value and value not in seen:
            output.append(value)
            seen.add(value)
    return tuple(output)
