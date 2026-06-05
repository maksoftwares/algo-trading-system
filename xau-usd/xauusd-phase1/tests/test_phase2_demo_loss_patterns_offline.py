from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_offline_analyzer_generates_required_docs_without_runtime_bridge(tmp_path):
    module = _load_module()
    source_text = (ROOT / "scripts" / "analyze_phase2_demo_loss_patterns_offline.py").read_text(encoding="utf-8")

    assert "MetaTrader5" not in source_text
    assert "mt5.initialize" not in source_text
    assert "terminal64" not in source_text
    assert "MetaQuotes" not in source_text

    trades_csv = tmp_path / "loss_trades.csv"
    actual_csv = tmp_path / "actual_trades.csv"
    trades_csv.write_text(
        "\n".join(
            [
                "entry_time,exit_time,candidate,status,symbol,direction,state,profit_aed,time_bucket,outcome,duplicate_role,is_duplicate,position_ticket",
                "2026-06-04 09:00:00,2026-06-04 09:30:00,breakout_retest,ACCEPTED,XAUUSD,BUY,CLOSED,-10.00,Morning 06:00-11:59,LOSS,kept,false,1",
                "2026-06-04 18:00:00,2026-06-04 18:30:00,breakout_retest,ACCEPTED,XAUUSD,BUY,CLOSED,30.00,Evening 16:00-19:59,WIN,kept,false,2",
                "2026-06-04 21:00:00,2026-06-04 21:30:00,session_extreme_retest_v0,PROVISIONAL,EURUSD,SELL,CLOSED,-4.00,Night 20:00-05:59,LOSS,unique,false,3",
                "2026-06-04 18:00:00,2026-06-04 18:31:00,round_number_retest_v0,PROVISIONAL,XAUUSD,BUY,CLOSED,28.00,Evening 16:00-19:59,WIN,duplicate,true,4",
            ]
        ),
        encoding="utf-8",
    )
    actual_csv.write_text(
        "\n".join(
                [
                    "entry_time,exit_time,candidate,status,symbol,direction,volume,state,profit_aed,position_ticket,duplicate_key,duplicate_role,is_duplicate",
                    "2026-06-04 18:00:00,2026-06-04 18:30:00,breakout_retest,ACCEPTED,XAUUSD,BUY,0.01,CLOSED,30.00,2,2026-06-04 18:00|XAUUSD|BUY|0.01,kept,false",
                    "2026-06-04 18:00:01,2026-06-04 18:31:00,round_number_retest_v0,PROVISIONAL,XAUUSD,BUY,0.01,CLOSED,28.00,4,2026-06-04 18:00|XAUUSD|BUY|0.01,duplicate,true",
                    "2026-06-04 09:00:00,2026-06-04 09:30:00,breakout_retest,ACCEPTED,XAUUSD,BUY,0.01,CLOSED,-10.00,1,2026-06-04 09:00|XAUUSD|BUY|0.01,unique,false",
                    "2026-06-04 21:00:00,2026-06-04 21:30:00,session_extreme_retest_v0,PROVISIONAL,EURUSD,SELL,0.01,CLOSED,-4.00,3,2026-06-04 21:00|EURUSD|SELL|0.01,unique,false",
                ]
            ),
        encoding="utf-8",
    )

    output = module.analyze_loss_patterns_offline(actual_csv, tmp_path)

    loss_review = output.loss_review_path.read_text(encoding="utf-8")
    shadow_plan = output.shadow_plan_path.read_text(encoding="utf-8")
    duplicate_analysis = output.duplicate_analysis_path.read_text(encoding="utf-8")

    assert "status: EXPERIMENTAL_LOSS_PATTERN_FOUND" in loss_review
    assert "runtime_change_authorized: false" in loss_review
    assert "# Phase 2 Demo Loss Review Verdict - No Runtime Touch" in loss_review
    assert "Missing spread/slippage/cost_R decomposition" in loss_review
    assert "BLOCK_XAUUSD_MORNING_AFTERNOON" in shadow_plan
    assert "BLOCK_PROVISIONAL_SESSION_EXTREME_RETEST" in shadow_plan
    assert "status: DUPLICATE_FAMILY_RISK_FOUND" in duplicate_analysis
    assert "| 2026-06-04 18:00 | XAUUSD | BUY | 0.01 | 2 |" in duplicate_analysis
    assert "breakout_retest, round_number_retest_v0" in duplicate_analysis


def _load_module():
    scripts_dir = ROOT / "scripts"
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))
    path = scripts_dir / "analyze_phase2_demo_loss_patterns_offline.py"
    spec = importlib.util.spec_from_file_location("analyze_phase2_demo_loss_patterns_offline", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules["analyze_phase2_demo_loss_patterns_offline"] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module
