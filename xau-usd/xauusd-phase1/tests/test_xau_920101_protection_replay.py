from __future__ import annotations

import csv
import importlib.util
import sys
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "replay_xau_920101_protection_variants.py"


def load_module():
    spec = importlib.util.spec_from_file_location("replay_xau_920101_protection_variants", SCRIPT)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def write_csv(path: Path, rows: list[dict[str, object]], columns: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def test_replay_protects_round_trip_short_after_mfe(tmp_path: Path) -> None:
    module = load_module()
    order_log = tmp_path / "a1_order_log.csv"
    path_dir = tmp_path / "paths"
    output_json = tmp_path / "out.json"
    output_csv = tmp_path / "out.csv"
    output_md = tmp_path / "out.md"

    order_columns = [
        "timestamp_broker",
        "timestamp_local",
        "run_id",
        "account_login",
        "symbol",
        "candidate",
        "magic",
        "action",
        "direction",
        "signal_entry_price",
        "result_price",
        "sl",
        "tp",
        "estimated_cost_R",
        "order_ticket",
    ]
    write_csv(
        order_log,
        [
            {
                "timestamp_broker": "2026.06.29 12:20:01",
                "timestamp_local": "2026.06.29 16:19:56",
                "run_id": "A1_XAU_920101_EVENING_H1_ONLY_TREND_V2_20260629",
                "account_login": "1025742",
                "symbol": "XAUUSD",
                "candidate": "breakout_retest",
                "magic": "920101",
                "action": "ORDER_SEND_OK",
                "direction": "SHORT",
                "signal_entry_price": "4047.39",
                "result_price": "4043.30",
                "sl": "4048.94",
                "tp": "4035.29",
                "estimated_cost_R": "0.0916",
                "order_ticket": "4311724",
            }
        ],
        order_columns,
    )
    path_columns = [
        "ts_broker",
        "position_ticket",
        "symbol",
        "row_type",
        "unrealized_R",
        "unrealized_pnl_aed",
    ]
    write_csv(
        path_dir / "position_path_log_20260629.csv",
        [
            {"ts_broker": "2026.06.29 12:20:10", "position_ticket": "4311724", "symbol": "XAUUSD", "row_type": "FIRST_SEEN", "unrealized_R": "-0.23", "unrealized_pnl_aed": "-4.78"},
            {"ts_broker": "2026.06.29 12:29:50", "position_ticket": "4311724", "symbol": "XAUUSD", "row_type": "SNAPSHOT", "unrealized_R": "0.8865", "unrealized_pnl_aed": "18.36"},
            {"ts_broker": "2026.06.29 12:58:00", "position_ticket": "4311724", "symbol": "XAUUSD", "row_type": "SNAPSHOT", "unrealized_R": "0.10", "unrealized_pnl_aed": "2.07"},
            {"ts_broker": "2026.06.29 13:00:20", "position_ticket": "4311724", "symbol": "XAUUSD", "row_type": "CLOSE_DETECTED", "unrealized_R": "-1.0213", "unrealized_pnl_aed": "-21.16"},
        ],
        path_columns,
    )

    payload = module.run_replay(
        phase1_root=tmp_path,
        path_log_dir=path_dir,
        order_logs=[("A1", order_log)],
        output_json=output_json,
        output_csv=output_csv,
        output_md=output_md,
    )

    row = payload["trade_rows"][0]
    assert row["planned_chase_r"] > 0.70
    assert row["CHASE_GUARD_050R_status"] == "SKIPPED_CHASE_GT_0.50R"
    assert row["BE_AFTER_080R_r"] == 0.0
    assert row["PARTIAL_075R_BE_r"] == 0.375
    assert row["GIVEBACK_075_TO_020R_r"] == 0.2
    assert payload["variant_summary_closed_path"][0]["net_aed"] == -21.16


def test_chase_guard_leaves_non_chased_trade_unchanged(tmp_path: Path) -> None:
    module = load_module()
    trade = module.OrderTrade(
        lane="A1",
        account_login="1025742",
        ticket="1",
        entry_time_broker="",
        entry_time_local="",
        run_id="",
        direction="BUY",
        signal_entry=100.0,
        fill_price=100.10,
        sl=99.0,
        tp=101.5,
        estimated_cost_r=0.0,
    )
    assert module.planned_chase_r(trade) < 0.10
    result = module.replay_chase_guard(module.planned_chase_r(trade), 0.30, 1.5)
    assert result.final_r == 1.5
    assert result.status == "UNCHANGED"
