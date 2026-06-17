from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_afternoon_round_family_diagnosis_isolates_round_loss():
    module = _load_module()
    rows = [
        _row("symbol_normalized_round_retest_v0", "round_family", "Afternoon 12:00-15:59", "-50.00"),
        _row("round_number_retest_v0", "round_family", "Afternoon 12:00-15:59", "-30.00"),
        _row("breakout_retest", "breakout_core", "Afternoon 12:00-15:59", "10.00"),
        _row("session_extreme_retest_v0", "session_extreme", "Afternoon 12:00-15:59", "-30.00"),
        _row("breakout_retest", "breakout_core", "Evening 16:00-19:59", "100.00"),
    ]

    diagnosis = module.afternoon_round_family_diagnosis(rows)
    by_segment = {row["segment"]: row for row in diagnosis["rows"]}

    assert diagnosis["afternoon_rows"] == 4
    assert diagnosis["afternoon_pnl_aed"] == "-100.00"
    assert diagnosis["round_family_afternoon_rows"] == 2
    assert diagnosis["round_family_afternoon_pnl_aed"] == "-80.00"
    assert diagnosis["round_family_loss_share_of_afternoon_loss_pct"] == "80.00%"
    assert diagnosis["residual_after_round_quarantine_rows"] == 2
    assert diagnosis["residual_after_round_quarantine_pnl_aed"] == "-20.00"
    assert diagnosis["protected_evening_night_rows_removed"] == "0"
    assert diagnosis["protected_evening_night_pnl_removed_aed"] == "0.00"
    assert diagnosis["runtime_authorized"] is False
    assert by_segment["round_family_afternoon"]["loss_share_of_afternoon_loss_pct"] == "80.00%"
    assert by_segment["non_round_residual_after_round_quarantine"]["pnl_aed"] == "-20.00"


def test_afternoon_round_family_diagnosis_does_not_force_loss_share_when_profitable():
    module = _load_module()
    rows = [
        _row("symbol_normalized_round_retest_v0", "round_family", "Afternoon 12:00-15:59", "-20.00"),
        _row("breakout_retest", "breakout_core", "Afternoon 12:00-15:59", "40.00"),
    ]

    diagnosis = module.afternoon_round_family_diagnosis(rows)

    assert diagnosis["afternoon_pnl_aed"] == "20.00"
    assert diagnosis["round_family_loss_share_of_afternoon_loss_pct"] == "n/a"


def _row(candidate: str, family: str, bucket: str, pnl: str) -> dict[str, str]:
    return {
        "entry_date": "2026-06-16",
        "time_bucket": bucket,
        "selected_candidate": candidate,
        "selected_family": family,
        "selected_profit_aed": pnl,
    }


def _load_module():
    path = ROOT / "scripts" / "generate_xauusd_canonical_loss_avoidance.py"
    spec = importlib.util.spec_from_file_location("generate_xauusd_canonical_loss_avoidance", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules["generate_xauusd_canonical_loss_avoidance"] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module
