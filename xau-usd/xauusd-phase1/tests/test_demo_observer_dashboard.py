from __future__ import annotations

import csv
import importlib.util
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_demo_observer_dashboard_generates_html_and_reports(tmp_path: Path):
    module = _load_module()
    repo = tmp_path / "repo"
    terminal = tmp_path / "terminal"
    files = terminal / "MQL5" / "Files"
    files.mkdir(parents=True)
    _write_log(
        files / "experimental_demo_attachment_log_breakout_retest_xauusd.csv",
        candidate="breakout_retest",
        status="ACCEPTED",
        symbol="XAUUSD",
        rows=[
            ("2026.06.01 10:00:00", "100.00", "100.10", "LONG", "true", "100.00", "99.00", "102.00"),
            ("2026.06.01 10:05:00", "101.00", "101.10", "LONG", "false", "0", "0", "0"),
            ("2026.06.01 10:10:00", "102.00", "102.10", "LONG", "false", "0", "0", "0"),
        ],
    )
    _write_log(
        files / "experimental_demo_attachment_log_round_number_retest_v0_usdjpy.csv",
        candidate="round_number_retest_v0",
        status="PROVISIONAL",
        symbol="USDJPY",
        rows=[
            ("2026.06.01 11:00:00", "199.90", "200.00", "SHORT", "true", "200.00", "202.00", "196.00"),
            ("2026.06.01 11:05:00", "201.80", "202.00", "SHORT", "false", "0", "0", "0"),
        ],
    )

    output = module.generate_demo_observer_dashboard(
        repo,
        terminal_data_dir=terminal,
        terminal_exe=tmp_path / "missing-terminal64.exe",
    )

    html = output.html_path.read_text(encoding="utf-8")
    assert output.log_file_count == 2
    assert output.signal_count == 2
    assert output.signals_today == 2
    assert "Demo Observer / Executor Dashboard" in html
    assert "demo-only" in html
    assert "breakout_retest" in html
    assert "round_number_retest_v0" in html
    assert "Actual Broker Trades" in html
    assert "Actual MT5 broker history is unavailable" in html
    assert "summaryStatus" in html
    assert "actualStatus" in html
    assert "orderStatus" in html
    assert "ledgerOutcome" in html
    assert "ledgerTable" in html
    assert "None" not in html
    assert output.json_path.exists()
    assert output.summary_csv_path.exists()
    assert output.ledger_csv_path.exists()
    assert output.actual_broker_csv_path.exists()

    ledger_rows = list(csv.DictReader(output.ledger_csv_path.open("r", encoding="utf-8", newline="")))
    assert [row["outcome"] for row in ledger_rows] == ["WIN_TP", "LOSS_STOP"]
    assert float(ledger_rows[0]["pnl_aed"]) > 0
    assert float(ledger_rows[1]["pnl_aed"]) < 0


def test_actual_broker_table_is_separate_from_signal_ledger():
    module = _load_module()

    html = module._actual_broker_table(
        {
            "status": "CONNECTED",
            "summary": {
                "actual_trades": 1,
                "closed_trades": 1,
                "open_trades": 0,
                "closed_win_rate_pct": "100.00",
                "total_pnl_aed": "12.34",
            },
            "trades": [
                {
                    "entry_time": "2026-06-01 15:00:00",
                    "exit_time": "2026-06-01 15:05:00",
                    "candidate": "breakout_retest",
                    "status": "ACCEPTED",
                    "symbol": "EURUSD",
                    "direction": "SELL",
                    "volume": "0.01",
                    "entry_price": "1.16418",
                    "exit_price": "1.16342",
                    "sl": "1.16518",
                    "tp": "1.16268",
                    "state": "CLOSED",
                    "profit_aed": "12.34",
                    "position_ticket": "123",
                    "exit_comment": "[tp 1.16342]",
                }
            ],
        }
    )

    assert "actualTable" in html
    assert "Actual MT5 summary" in html
    assert "breakout_retest" in html
    assert "+12.3400" in html


def test_actual_duplicate_marking_keeps_canonical_row():
    module = _load_module()
    rows = [
        {
            "entry_time": "2026-06-01 15:11:32",
            "candidate": "swing_breakout_retest_v0",
            "symbol": "EURUSD",
            "direction": "SELL",
            "volume": "0.01",
            "position_ticket": "2",
            "profit_aed": "4.88",
            "state": "CLOSED",
        },
        {
            "entry_time": "2026-06-01 15:11:32",
            "candidate": "breakout_retest",
            "symbol": "EURUSD",
            "direction": "SELL",
            "volume": "0.01",
            "position_ticket": "1",
            "profit_aed": "4.88",
            "state": "CLOSED",
        },
        {
            "entry_time": "2026-06-01 16:55:01",
            "candidate": "session_extreme_retest_v0",
            "symbol": "XAUUSD",
            "direction": "SELL",
            "volume": "0.01",
            "position_ticket": "3",
            "profit_aed": "29.29",
            "state": "CLOSED",
        },
    ]

    module._mark_duplicate_actual_trades(rows)

    by_candidate = {row["candidate"]: row for row in rows}
    assert by_candidate["breakout_retest"]["duplicate_role"] == "kept"
    assert by_candidate["breakout_retest"]["is_duplicate"] == "false"
    assert by_candidate["swing_breakout_retest_v0"]["duplicate_role"] == "duplicate"
    assert by_candidate["swing_breakout_retest_v0"]["is_duplicate"] == "true"
    assert by_candidate["session_extreme_retest_v0"]["duplicate_role"] == "unique"


def test_actual_broker_magic_parser_includes_p2weakness_and_wr50_experiments():
    module = _load_module()

    assert module._is_demo_magic(931000, "") is True
    assert module._is_demo_magic(930101, "") is True
    assert module._is_demo_magic(930100, "") is True
    assert module._is_demo_magic(0, "P2WEAKNESS_BR_V1") is True
    assert module._candidate_status_from_magic(931000, "") == ("p2weakness_br_v1", "EXPERIMENTAL")
    assert module._candidate_status_from_magic(930101, "") == ("p2weakness_br_v1", "EXPERIMENTAL")
    assert module._candidate_status_from_magic(930100, "") == ("WR50_BreakoutQuality_v0", "EXPERIMENTAL")

    filters = module._filters("actual")
    assert "Experimental" in filters
    assert "p2weakness_br_v1" in filters


def _write_log(path: Path, candidate: str, status: str, symbol: str, rows: list[tuple[str, str, str, str, str, str, str, str]]):
    fieldnames = [
        "timestamp_broker",
        "timestamp_utc",
        "timestamp_local",
        "run_id",
        "account_server",
        "symbol",
        "candidate",
        "candidate_status",
        "qualified_symbol",
        "dry_run",
        "broker_action_allowed",
        "observer_supported",
        "m5_bar_time",
        "bid",
        "ask",
        "spread_points",
        "stage",
        "direction",
        "would_signal",
        "reason_code",
        "level_kind",
        "level_price",
        "entry_price",
        "stop_loss",
        "take_profit",
        "stop_distance_points",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for timestamp, bid, ask, direction, signal, entry, stop, target in rows:
            writer.writerow(
                {
                    "timestamp_broker": timestamp,
                    "timestamp_utc": timestamp,
                    "timestamp_local": timestamp,
                    "run_id": "phase2-experimental-demo-attach-v0.1",
                    "account_server": "Capital.ComMena-Demo",
                    "symbol": symbol,
                    "candidate": candidate,
                    "candidate_status": status,
                    "qualified_symbol": "true",
                    "dry_run": "true",
                    "broker_action_allowed": "false",
                    "observer_supported": "true",
                    "m5_bar_time": timestamp,
                    "bid": bid,
                    "ask": ask,
                    "spread_points": "50.00",
                    "stage": "WOULD_SIGNAL" if signal == "true" else "WAIT_LEVEL_BREAK_RETEST",
                    "direction": direction,
                    "would_signal": signal,
                    "reason_code": f"{candidate.upper()}_{direction}_DRY_RUN",
                    "level_kind": "test",
                    "level_price": entry,
                    "entry_price": entry,
                    "stop_loss": stop,
                    "take_profit": target,
                    "stop_distance_points": "100.00",
                }
            )


def _load_module():
    path = ROOT / "scripts" / "generate_demo_observer_dashboard.py"
    spec = importlib.util.spec_from_file_location("generate_demo_observer_dashboard", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules["generate_demo_observer_dashboard"] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module
