from __future__ import annotations

import json
import sys
from pathlib import Path


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PACKAGE_ROOT))

from src.evidence_audit import DEFAULT_CONFIG, run_audit  # noqa: E402


def test_config_freezes_expected_strategy() -> None:
    config = json.loads(DEFAULT_CONFIG.read_text(encoding="utf-8"))
    strategy = config["strategy"]
    assert config["candidate_id"] == "EURUSD_M30_RSI_BB_CLOSE_FADE_LONG_V1"
    assert strategy["symbol"] == "EURUSD"
    assert strategy["signal_timeframe"] == "M30"
    assert strategy["direction"] == "LONG_ONLY"
    assert strategy["blocked_entry_hours"] == [6, 7, 10, 13]
    assert strategy["risk_reward"] == 0.8
    assert not config["authorization"]["demo_authorized"]
    assert not config["authorization"]["live_authorized"]


def test_inherited_mt5_evidence_passes_working_research_gate() -> None:
    report = run_audit()
    assert report["status"] == "WORKING_RESEARCH_STRATEGY_FORWARD_NOT_AUTHORIZED"
    assert report["mt5_economics"]["trades"] == 831
    assert report["mt5_economics"]["profit_factor"] == 1.20
    assert report["mt5_economics"]["net_profit_usd"] == 101.82
    assert report["working_research_gates"]["ex5_hash_match"]
    assert report["working_research_gates"]["zero_warning_compile"]
    assert report["working_research_gates"]["exact_trade_ledger_parity"]
    assert all(report["working_research_gates"].values())


def test_concentration_and_split_diagnostics_are_positive() -> None:
    report = run_audit()
    parsed = report["parsed_trade_diagnostics"]
    assert parsed["top10_winners_removed_net_usd"] > 0
    assert report["chronological_splits"]["design_2022_2024"]["pnl"] > 0
    assert report["chronological_splits"]["current_2024_2026"]["pnl"] > 0
    assert report["promotion_blockers"]
