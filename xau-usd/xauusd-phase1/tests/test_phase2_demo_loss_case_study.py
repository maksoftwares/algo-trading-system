from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_shadow_filter_blocks_provisional_and_xau_morning_afternoon():
    module = _load_module()
    rows = [
        _row("2026-06-04 09:00:00", "breakout_retest", "ACCEPTED", "XAUUSD", "-10.00"),
        _row("2026-06-04 13:00:00", "breakout_retest", "ACCEPTED", "XAUUSD", "-11.00"),
        _row("2026-06-04 17:00:00", "breakout_retest", "ACCEPTED", "XAUUSD", "25.00"),
        _row("2026-06-04 21:00:00", "symbol_normalized_round_retest_v0", "ACCEPTED", "XAUUSD", "30.00"),
        _row("2026-06-04 21:05:00", "session_extreme_retest_v0", "PROVISIONAL", "EURUSD", "-4.00"),
    ]

    enriched = [module.enrich_shadow_rule(module.enrich_trade(row)) for row in rows]
    actions = [row["shadow_action"] for row in enriched]
    reasons = [row["shadow_reason"] for row in enriched]

    assert actions == ["BLOCK", "BLOCK", "KEEP", "KEEP", "BLOCK"]
    assert reasons[0] == "BLOCK_XAUUSD_MORNING_AFTERNOON"
    assert reasons[1] == "BLOCK_XAUUSD_MORNING_AFTERNOON"
    assert reasons[4] == "BLOCK_PROVISIONAL_SESSION_EXTREME_RETEST"

    summary = module.summarize_shadow(enriched)
    assert summary["baseline"]["closed_pnl_aed"] == 30.0
    assert summary["kept"]["closed_pnl_aed"] == 55.0
    assert summary["blocked"]["closed_pnl_aed"] == -25.0
    assert summary["delta_closed_pnl_aed"] == 25.0


def test_time_bucket_boundaries_are_dubai_session_labels():
    module = _load_module()

    assert module.time_bucket("2026-06-04 05:59:59") == "Night 20:00-05:59"
    assert module.time_bucket("2026-06-04 06:00:00") == "Morning 06:00-11:59"
    assert module.time_bucket("2026-06-04 12:00:00") == "Afternoon 12:00-15:59"
    assert module.time_bucket("2026-06-04 16:00:00") == "Evening 16:00-19:59"
    assert module.time_bucket("2026-06-04 20:00:00") == "Night 20:00-05:59"


def _row(entry_time: str, candidate: str, status: str, symbol: str, pnl: str) -> dict[str, str]:
    return {
        "entry_time": entry_time,
        "exit_time": entry_time,
        "candidate": candidate,
        "status": status,
        "symbol": symbol,
        "direction": "BUY",
        "state": "CLOSED",
        "profit_aed": pnl,
        "exit_comment": "[tp 1.0]" if float(pnl) > 0 else "[sl 1.0]",
        "duplicate_role": "unique",
        "is_duplicate": "false",
    }


def _load_module():
    scripts_dir = ROOT / "scripts"
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))
    path = scripts_dir / "generate_phase2_demo_loss_case_study.py"
    spec = importlib.util.spec_from_file_location("generate_phase2_demo_loss_case_study", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules["generate_phase2_demo_loss_case_study"] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module
