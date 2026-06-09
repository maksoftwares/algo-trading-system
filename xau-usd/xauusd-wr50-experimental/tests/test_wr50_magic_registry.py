from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from validate_wr50_registry import parse_registry_markdown, validate_registry_file, validate_rows


def test_actual_wr50_registry_passes() -> None:
    result = validate_registry_file(ROOT / "docs" / "WR50_EA_REGISTRY.md")
    assert result.ok, result.errors
    rows = parse_registry_markdown(ROOT / "docs" / "WR50_EA_REGISTRY.md")
    assert {row["active_magic"] for row in rows} == {"930000", "930100", "930200", "930300", "930400", "930500"}
    assert {row["ea_id"] for row in rows if row["experiment_status"] == "DISABLED"} == {"wr50_pbe0"}


def test_magic_outside_range_fails() -> None:
    rows = [
        {
            "ea_id": "bad_magic",
            "ea_name": "BadMagic",
            "version": "v0",
            "magic_start": "931000",
            "magic_end": "931099",
            "active_magic": "931000",
            "strategy_family": "breakout_retest_wr50_experimental",
            "experiment_status": "DEMO_EXPERIMENT_ONLY",
            "allowed_account": "OWNER_AUTHORIZATION_REQUIRED",
            "symbol": "XAUUSD",
            "entry_timeframe": "M5",
            "risk_profile": "fixed",
            "comment_prefix": "WR50|BAD0",
            "owner_authorized": "false",
            "live_authorized": "false",
            "canonical_phase2_authorized": "false",
            "max_fixed_lot": "0.01",
        }
    ]
    result = validate_rows(rows)
    assert not result.ok
    assert any("outside WR50 namespace" in error for error in result.errors)


def test_duplicate_magic_fails() -> None:
    base = {
        "version": "v0",
        "magic_start": "930000",
        "magic_end": "930099",
        "active_magic": "930000",
        "strategy_family": "breakout_retest_wr50_experimental",
        "experiment_status": "DEMO_EXPERIMENT_ONLY",
        "allowed_account": "OWNER_AUTHORIZATION_REQUIRED",
        "symbol": "XAUUSD",
        "entry_timeframe": "M5",
        "risk_profile": "fixed",
        "owner_authorized": "false",
        "live_authorized": "false",
        "canonical_phase2_authorized": "false",
        "max_fixed_lot": "0.01",
    }
    rows = [
        {**base, "ea_id": "a", "ea_name": "A", "comment_prefix": "WR50|AAA0"},
        {**base, "ea_id": "b", "ea_name": "B", "comment_prefix": "WR50|BBB0"},
    ]
    result = validate_rows(rows)
    assert not result.ok
    assert any("duplicate active_magic" in error for error in result.errors)
