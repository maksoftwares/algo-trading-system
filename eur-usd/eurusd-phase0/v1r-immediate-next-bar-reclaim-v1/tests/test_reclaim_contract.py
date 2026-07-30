from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_runner():
    spec = importlib.util.spec_from_file_location("eurusd_v1r_reclaim_runner", ROOT / "run_reclaim.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


RUNNER = load_runner()


def test_input_contract_is_exact_and_unchanged_except_identity() -> None:
    preset = RUNNER.load_preset()
    schema = RUNNER.source_input_schema()
    executed = RUNNER.validate_input_contract(preset, schema)
    assert len(schema) == 34
    assert len(executed) == 34
    assert preset["InpSignalMode"] == "0"
    assert preset["InpDirectionMode"] == "1"
    assert preset["InpRiskReward"] == "0.80"
    assert preset["InpBlockedEntryHoursCsv"] == ""
    assert preset["InpMinBodyFraction"] == "0.40"


def test_frozen_reclaim_state_machine_is_present() -> None:
    source = RUNNER.SOURCE.read_text(encoding="utf-8")
    assert "DetectRawSetupShift1" in source
    assert "EvaluateReclaimTransition" in source
    assert 'confirmation_close > confirmation_lower_band' in source
    assert "stored_shift_two != old_setup" in source
    assert "RecentLow(1, 6)" in source
    assert "CopyOne(g_atr_handle, 0, 1, atr)" in source
    assert "PENDING_DISCARDED_ON_DEINIT" in source
    assert "g_skip_first_observed_transition = true" in source
    assert "if(!MQLInfoInteger(MQL_TESTER))" in source


def test_no_forbidden_reclaim_variants() -> None:
    source = RUNNER.SOURCE.read_text(encoding="utf-8")
    assert "reclaim_buffer" not in source.lower()
    assert "confirmation_rsi" not in source.lower()
    assert "confirmation_body" not in source.lower()
    assert "confirmation_color" not in source.lower()
    assert "multi_bar" not in source.lower()

