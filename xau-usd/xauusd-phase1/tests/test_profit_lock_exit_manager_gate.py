from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "replay_profit_lock_exit_manager_gate.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("replay_profit_lock_exit_manager_gate", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _write_csv(path: Path, header: str, rows: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join([header, *rows]) + "\n", encoding="utf-8")


def test_profit_lock_replay_saves_loser_after_late_trigger(tmp_path: Path):
    mod = _load_module()
    row = {
        "position_ticket": "T1",
        "entry_time": "2026-06-17 10:00:00",
        "exit_time": "2026-06-17 10:20:00",
        "candidate": "breakout_retest",
        "direction": "BUY",
        "entry_price": "100",
        "exit_price": "90",
        "sl": "90",
        "profit_aed": "-20",
        "duplicate_role": "unique",
        "is_duplicate": "false",
    }
    row["control_r"] = mod.control_r_from_prices(row)
    row["control_aed"] = -20.0
    row["aed_per_r"] = 20.0
    path = [
        mod.PathPoint("2026.06.17 10:05:00", 1.30, "SNAPSHOT", "1025742", "920101"),
        mod.PathPoint("2026.06.17 10:10:00", 0.75, "SNAPSHOT", "1025742", "920101"),
    ]

    replay = mod.replay_trade(row, path, trigger_r=1.25, lock_r=0.80)

    assert replay["status"] == "LOCK_EXIT_AT_FLOOR"
    assert replay["replay_r"] == 0.8
    assert replay["replay_aed"] == 16.0
    assert replay["delta_aed"] == 36.0


def test_gate_uses_duplicate_hidden_view_and_best_day_removed(tmp_path: Path):
    mod = _load_module()
    phase1_root = tmp_path / "xauusd-phase1"
    trades = phase1_root / "outputs" / "reports" / "PHASE2_DEMO_ACTUAL_BROKER_TRADES.csv"
    logs = tmp_path / "logs"
    header = (
        "entry_time,exit_time,candidate,status,symbol,direction,volume,entry_price,exit_price,sl,tp,state,"
        "profit_aed,position_ticket,magic,duplicate_role,is_duplicate,time_bucket"
    )
    _write_csv(
        trades,
        header,
        [
            "2026-06-16 10:00:00,2026-06-16 10:20:00,breakout_retest,ACCEPTED,XAUUSD,BUY,0.01,100,90,90,115,CLOSED,-20,T1,920101,unique,false,Morning",
            "2026-06-17 10:00:00,2026-06-17 10:20:00,breakout_retest,ACCEPTED,XAUUSD,BUY,0.01,100,90,90,115,CLOSED,-20,T2,920101,unique,false,Morning",
            "2026-06-17 11:00:00,2026-06-17 11:20:00,breakout_retest,ACCEPTED,XAUUSD,BUY,0.01,100,115,90,115,CLOSED,30,T3,920101,unique,false,Morning",
            "2026-06-17 12:00:00,2026-06-17 12:20:00,breakout_retest,ACCEPTED,XAUUSD,BUY,0.01,100,90,90,115,CLOSED,-20,T4,920101,duplicate,true,Morning",
        ],
    )
    path_header = (
        "ts_utc,account_login,position_ticket,magic,candidate,symbol,direction,entry_price,sl_initial,"
        "tp_initial,unrealized_R,row_type"
    )
    _write_csv(
        logs / "position_path_log_20260617.csv",
        path_header,
        [
            "2026.06.16 10:05:00,1025742,T1,920101,breakout_retest,XAUUSD,BUY,100,90,115,1.30,SNAPSHOT",
            "2026.06.16 10:10:00,1025742,T1,920101,breakout_retest,XAUUSD,BUY,100,90,115,0.70,SNAPSHOT",
            "2026.06.17 10:05:00,1025742,T2,920101,breakout_retest,XAUUSD,BUY,100,90,115,1.30,SNAPSHOT",
            "2026.06.17 10:10:00,1025742,T2,920101,breakout_retest,XAUUSD,BUY,100,90,115,0.70,SNAPSHOT",
            "2026.06.17 11:05:00,1025742,T3,920101,breakout_retest,XAUUSD,BUY,100,90,115,1.50,SNAPSHOT",
            "2026.06.17 11:10:00,1025742,T3,920101,breakout_retest,XAUUSD,BUY,100,90,115,0.70,SNAPSHOT",
            "2026.06.17 12:05:00,1025742,T4,920101,breakout_retest,XAUUSD,BUY,100,90,115,1.30,SNAPSHOT",
            "2026.06.17 12:10:00,1025742,T4,920101,breakout_retest,XAUUSD,BUY,100,90,115,0.70,SNAPSHOT",
        ],
    )

    payload = mod.run_profit_lock_gate(phase1_root=phase1_root, path_log_dir=logs)

    dedup = payload["views"]["duplicate_hidden"]
    raw = payload["views"]["raw_including_duplicates"]
    assert dedup["rows"] == 3
    assert raw["rows"] == 4
    assert dedup["delta_aed"] == 58.0
    assert dedup["best_day_removed_delta_aed"] == 22.0
    assert payload["status"] == "PASS"
    assert json.loads((phase1_root / mod.DEFAULT_OUTPUT_JSON).read_text(encoding="utf-8"))["status"] == "PASS"


def test_gate_holds_when_best_day_removed_turns_negative(tmp_path: Path):
    mod = _load_module()
    phase1_root = tmp_path / "xauusd-phase1"
    trades = phase1_root / "outputs" / "reports" / "PHASE2_DEMO_ACTUAL_BROKER_TRADES.csv"
    logs = tmp_path / "logs"
    _write_csv(
        trades,
        "entry_time,exit_time,candidate,status,symbol,direction,volume,entry_price,exit_price,sl,tp,state,profit_aed,position_ticket,magic,duplicate_role,is_duplicate,time_bucket",
        [
            "2026-06-16 10:00:00,2026-06-16 10:20:00,breakout_retest,ACCEPTED,XAUUSD,BUY,0.01,100,90,90,115,CLOSED,-20,T1,920101,unique,false,Morning",
            "2026-06-17 10:00:00,2026-06-17 10:20:00,breakout_retest,ACCEPTED,XAUUSD,BUY,0.01,100,115,90,115,CLOSED,30,T2,920101,unique,false,Morning",
        ],
    )
    _write_csv(
        logs / "position_path_log_20260617.csv",
        "ts_utc,account_login,position_ticket,magic,candidate,symbol,direction,entry_price,sl_initial,tp_initial,unrealized_R,row_type",
        [
            "2026.06.16 10:05:00,1025742,T1,920101,breakout_retest,XAUUSD,BUY,100,90,115,1.30,SNAPSHOT",
            "2026.06.16 10:10:00,1025742,T1,920101,breakout_retest,XAUUSD,BUY,100,90,115,0.70,SNAPSHOT",
            "2026.06.17 10:05:00,1025742,T2,920101,breakout_retest,XAUUSD,BUY,100,90,115,1.50,SNAPSHOT",
            "2026.06.17 10:10:00,1025742,T2,920101,breakout_retest,XAUUSD,BUY,100,90,115,0.70,SNAPSHOT",
        ],
    )

    payload = mod.run_profit_lock_gate(phase1_root=phase1_root, path_log_dir=logs)

    assert payload["views"]["duplicate_hidden"]["delta_aed"] == 22.0
    assert payload["views"]["duplicate_hidden"]["best_day_removed_delta_aed"] == -14.0
    assert payload["status"] == "HOLD_DO_NOT_ARM"
