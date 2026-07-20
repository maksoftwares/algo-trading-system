from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from src.audit import build_native_core


ROOT = Path(__file__).resolve().parents[1]


def _normalized() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "trade_id": "a",
                "specialist_id": "R1_UPTREND",
                "regime": "UPTREND",
                "source_strategy": "box",
                "pnl_basis": "legacy",
                "entry_time_utc": "2026-01-01T00:00:00Z",
                "exit_time_utc": "2026-01-01T01:00:00Z",
                "direction": "LONG",
                "pnl_usd_0p01_equiv": 1.0,
                "stress_net_r": None,
                "risk_usd": None,
            },
            {
                "trade_id": "b",
                "specialist_id": "R1_UPTREND",
                "regime": "UPTREND",
                "source_strategy": "box",
                "pnl_basis": "legacy",
                "entry_time_utc": "2026-01-02T00:00:00Z",
                "exit_time_utc": "2026-01-02T01:00:00Z",
                "direction": "LONG",
                "pnl_usd_0p01_equiv": 2.0,
                "stress_net_r": None,
                "risk_usd": None,
            },
        ]
    )


def _native(status: str = "VALID") -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "trade_id": "native-a",
                "source_id": "box",
                "direction": "LONG",
                "native_entry_time": "2026-01-01 00:00:00",
                "native_exit_time": "2026-01-03 00:00:00",
                "native_entry_price": 100.0,
                "native_exit_price": 99.0,
                "native_entry_volume": 0.01,
                "native_pnl_usd": -1.0,
                "native_fee_evidence_complete": False,
                "legacy_exit_deal_mismatch": True,
                "legacy_pnl_mismatch": True,
                "evidence_status": status,
            },
            {
                "trade_id": "native-b",
                "source_id": "box",
                "direction": "LONG",
                "native_entry_time": "2026-01-02 00:00:00",
                "native_exit_time": "2026-01-02 01:00:00",
                "native_entry_price": 101.0,
                "native_exit_price": 105.0,
                "native_entry_volume": 0.01,
                "native_pnl_usd": 4.0,
                "native_fee_evidence_complete": False,
                "legacy_exit_deal_mismatch": True,
                "legacy_pnl_mismatch": True,
                "evidence_status": status,
            },
        ]
    )


def _settings() -> dict:
    return {
        "specialist_id": "R1_UPTREND",
        "expected_rows": 2,
        "expected_total_pnl_usd": 3.0,
        "expected_evidence_status": "VALID",
        "expected_fee_evidence_complete": False,
        "source_controls": {"box": {"expected_rows": 2, "expected_pnl_usd": 3.0}},
    }


def _policy() -> dict:
    return {
        "policy_id": "TEST",
        "target_specialist_id": "R1_UPTREND",
        "target_source_strategy": "box",
        "maximum_concurrent_positions": 1,
        "maximum_entries_per_utc_day": 1,
    }


def test_native_exit_interval_controls_single_position_policy() -> None:
    core, decisions, audit = build_native_core(
        _normalized(), _native(), _settings(), _policy()
    )
    assert list(decisions["accepted"]) == [True, False]
    assert list(core["trade_id"]) == ["a"]
    assert float(core.iloc[0]["pnl_usd"]) == -1.0
    assert audit["legacy_pnl_mismatches"] == 2


def test_invalid_native_evidence_fails_closed() -> None:
    with pytest.raises(ValueError, match="invalid reconciliation"):
        build_native_core(_normalized(), _native("INVALID"), _settings(), _policy())


def test_config_retains_v57_frequency_and_drawdown_gates() -> None:
    config = json.loads(
        (ROOT / "config" / "one_trade_per_day_native_core_v58.json").read_text(
            encoding="utf-8"
        )
    )
    assert config["gates"]["minimum_combined_trades_per_weekday"] == 1.0
    assert config["account"]["maximum_combined_closed_drawdown_usd"] == 300.0
    assert config["research_controls"]["same_version_post_outcome_tuning_authorized"] is False


def test_preregistration_disclaims_execution_and_floating_proof() -> None:
    text = (ROOT / "PREREGISTRATION.md").read_text(encoding="utf-8")
    assert "no Python serving, EA, demo, live" in text
    assert "Whole-account floating-equity reconstruction" in text
