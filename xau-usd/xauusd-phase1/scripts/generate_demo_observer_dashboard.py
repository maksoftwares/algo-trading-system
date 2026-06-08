from __future__ import annotations

import argparse
import csv
import html
import json
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEFAULT_TERMINAL_DATA_DIR = Path(
    "C:/Users/ZHAO ZHU INFORMATION/AppData/Roaming/MetaQuotes/Terminal/D0E8209F77C8CF37AD8BF550E51FF075"
)
DEFAULT_TERMINAL_EXE = Path("C:/Program Files/MetaTrader 5/terminal64.exe")
DEFAULT_OUTPUT_NAME = "demo-observer-dashboard.html"
DEFAULT_LIVE_REFRESH_URL = "http://127.0.0.1:8777/demo-observer-dashboard.html"
DEFAULT_MARGIN_AED = 100.0
DEFAULT_LEVERAGE = 50.0
DEFAULT_ACTUAL_HISTORY_START = "2026-06-01 00:00:00"
DEMO_MAGIC_MIN = 920000
DEMO_MAGIC_MAX = 929999
P2WEAKNESS_LEGACY_MAGIC = 930101
P2WEAKNESS_MAGIC_MIN = 931000
P2WEAKNESS_MAGIC_MAX = 931099
CANDIDATE_MAGIC_CODES = {
    10: ("breakout_retest", "ACCEPTED"),
    20: ("swing_breakout_retest_v0", "ACCEPTED"),
    30: ("symbol_normalized_round_retest_v0", "ACCEPTED"),
    40: ("round_number_retest_v0", "PROVISIONAL"),
    50: ("session_extreme_retest_v0", "PROVISIONAL"),
}
EXPERIMENTAL_MAGIC_CODES = {
    930000: ("WR50_BreakoutEvening_v0", "EXPERIMENTAL"),
    930100: ("WR50_BreakoutQuality_v0", "EXPERIMENTAL"),
    930200: ("WR50_BreakoutExit1R_v0", "EXPERIMENTAL"),
    P2WEAKNESS_LEGACY_MAGIC: ("p2weakness_br_v1", "EXPERIMENTAL"),
    P2WEAKNESS_MAGIC_MIN: ("p2weakness_br_v1", "EXPERIMENTAL"),
}
SYMBOL_MAGIC_CODES = {1: "XAUUSD", 2: "EURUSD", 3: "USDJPY"}
ACTUAL_BROKER_TRADE_FIELDS = [
    "entry_time",
    "exit_time",
    "candidate",
    "status",
    "symbol",
    "direction",
    "volume",
    "entry_price",
    "exit_price",
    "sl",
    "tp",
    "state",
    "profit_aed",
    "position_ticket",
    "magic",
    "entry_order",
    "exit_order",
    "entry_deal",
    "exit_deal",
    "duplicate_key",
    "duplicate_role",
    "is_duplicate",
    "entry_comment",
    "exit_comment",
]
DEDUP_KEEP_PRIORITY = {
    "breakout_retest": 10,
    "symbol_normalized_round_retest_v0": 20,
    "swing_breakout_retest_v0": 30,
    "session_extreme_retest_v0": 40,
    "round_number_retest_v0": 50,
    "p2weakness_br_v1": 60,
    "WR50_BreakoutEvening_v0": 70,
    "WR50_BreakoutQuality_v0": 80,
    "WR50_BreakoutExit1R_v0": 90,
}


@dataclass(frozen=True)
class DashboardOutput:
    html_path: Path
    json_path: Path
    summary_csv_path: Path
    ledger_csv_path: Path
    actual_broker_csv_path: Path
    log_file_count: int
    signal_count: int
    signals_today: int


def generate_demo_observer_dashboard(
    repo_root: Path,
    terminal_data_dir: Path = DEFAULT_TERMINAL_DATA_DIR,
    output_path: Path | None = None,
    margin_aed: float = DEFAULT_MARGIN_AED,
    leverage: float = DEFAULT_LEVERAGE,
    focus_date: str | None = None,
    terminal_exe: Path = DEFAULT_TERMINAL_EXE,
    include_broker_history: bool = True,
    actual_history_start: str = DEFAULT_ACTUAL_HISTORY_START,
) -> DashboardOutput:
    repo_root = repo_root.resolve()
    terminal_data_dir = terminal_data_dir.resolve()
    output_path = (output_path or repo_root / DEFAULT_OUTPUT_NAME).resolve()
    phase1_reports = repo_root / "xau-usd" / "xauusd-phase1" / "outputs" / "reports"
    files_dir = terminal_data_dir / "MQL5" / "Files"
    log_paths = sorted(
        [
            *files_dir.glob("experimental_demo_attachment_log_*.csv"),
            *files_dir.glob("experimental_demo_executor_signal_log_*.csv"),
        ]
    )
    order_log_paths = sorted(files_dir.glob("experimental_demo_executor_order_log_*.csv"))

    logs = [_read_observer_log(path) for path in log_paths]
    order_rows = _read_order_logs(order_log_paths)
    latest_date = focus_date or _latest_broker_date(logs)
    notional_aed = margin_aed * leverage
    ledger = _build_signal_ledger(logs, margin_aed=margin_aed, leverage=leverage, notional_aed=notional_aed)
    actual_broker = (
        _read_actual_broker_trades(terminal_exe, latest_date, actual_history_start=actual_history_start)
        if include_broker_history
        else _actual_unavailable("disabled_by_cli")
    )
    summary_rows = _build_summary_rows(logs, ledger, latest_date)
    symbol_rows = _build_symbol_rows(ledger, latest_date)
    candidate_rows = _build_candidate_rows(ledger, latest_date)
    coverage_rows = [_coverage_row(log, latest_date) for log in logs]

    payload = {
        "status": "GENERATED",
        "generated_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "terminal_data_dir": str(terminal_data_dir),
        "files_dir": str(files_dir),
        "live_refresh_url": DEFAULT_LIVE_REFRESH_URL,
        "focus_date": latest_date,
        "margin_aed": margin_aed,
        "leverage": leverage,
        "notional_aed": notional_aed,
        "log_file_count": len(logs),
        "signals_total": len(ledger),
        "signals_focus_date": sum(1 for row in ledger if row["date"] == latest_date),
        "latest_log_write": _latest_log_write(logs),
        "oldest_log_write": _oldest_log_write(logs),
        "coverage": coverage_rows,
        "orders": order_rows,
        "orders_focus_date": sum(1 for row in order_rows if _date_part(row.get("timestamp_broker")) == latest_date),
        "orders_sent_focus_date": sum(
            1
            for row in order_rows
            if _date_part(row.get("timestamp_broker")) == latest_date and str(row.get("action", "")).upper() == "ORDER_SEND_OK"
        ),
        "summary": summary_rows,
        "candidate_summary": candidate_rows,
        "symbol_summary": symbol_rows,
        "actual_broker": actual_broker,
        "ledger": ledger,
        "notes": [
            "This dashboard can read both telemetry-only observer logs and demo executor logs.",
            "Actual Broker Trades are direct MT5 account history/open-position evidence when the terminal bridge is available.",
            f"For refresh-time updates, open the live dashboard URL: {DEFAULT_LIVE_REFRESH_URL}",
            "Signal Ledger PnL is estimated from logged bid/ask snapshots, not broker fills.",
            "Open trades are marked to the latest logged bid/ask in the same observer file.",
            "Executor order rows are demo-only evidence; live/real server names are refused by the EA.",
        ],
    }

    phase1_reports.mkdir(parents=True, exist_ok=True)
    json_path = phase1_reports / "PHASE2_DEMO_OBSERVER_DASHBOARD.json"
    summary_csv_path = phase1_reports / "PHASE2_DEMO_OBSERVER_DASHBOARD_SUMMARY.csv"
    ledger_csv_path = phase1_reports / "PHASE2_DEMO_OBSERVER_DASHBOARD_LEDGER.csv"
    actual_broker_csv_path = phase1_reports / "PHASE2_DEMO_ACTUAL_BROKER_TRADES.csv"
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    _write_csv(summary_csv_path, summary_rows)
    _write_csv(ledger_csv_path, ledger)
    _write_csv(actual_broker_csv_path, actual_broker["trades"], ACTUAL_BROKER_TRADE_FIELDS)
    output_path.write_text(_render_html(payload), encoding="utf-8")

    return DashboardOutput(
        html_path=output_path,
        json_path=json_path,
        summary_csv_path=summary_csv_path,
        ledger_csv_path=ledger_csv_path,
        actual_broker_csv_path=actual_broker_csv_path,
        log_file_count=len(logs),
        signal_count=len(ledger),
        signals_today=sum(1 for row in ledger if row["date"] == latest_date),
    )


def _read_observer_log(path: Path) -> dict[str, Any]:
    rows: list[dict[str, str]] = []
    if path.exists():
        with path.open("r", encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
    first = rows[0] if rows else {}
    return {
        "path": path,
        "file": path.name,
        "kind": "executor" if "executor_signal" in path.name else "observer",
        "last_write": path.stat().st_mtime if path.exists() else 0.0,
        "last_write_text": _format_mtime(path),
        "candidate": first.get("candidate", _candidate_from_file(path.name)),
        "status": first.get("candidate_status", "UNKNOWN"),
        "symbol": first.get("symbol", _symbol_from_file(path.name)),
        "run_id": first.get("run_id", "UNKNOWN"),
        "account_server": first.get("account_server", "UNKNOWN"),
        "dry_run": first.get("dry_run", "UNKNOWN"),
        "broker_action_allowed": first.get("broker_action_allowed", "UNKNOWN"),
        "rows": rows,
    }


def _read_order_logs(paths: list[Path]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in paths:
        if not path.exists():
            continue
        with path.open("r", encoding="utf-8", newline="") as handle:
            for row in csv.DictReader(handle):
                enriched = dict(row)
                enriched["source_log"] = path.name
                rows.append(enriched)
    rows.sort(key=lambda item: str(item.get("timestamp_broker", "")))
    return rows


def _read_actual_broker_trades(terminal_exe: Path, focus_date: str, actual_history_start: str = DEFAULT_ACTUAL_HISTORY_START) -> dict[str, Any]:
    terminal_exe = terminal_exe.resolve()
    if not terminal_exe.exists():
        return _actual_unavailable(f"terminal_exe_missing:{terminal_exe}")
    try:
        import MetaTrader5 as mt5  # type: ignore[import-not-found]
    except Exception as exc:  # pragma: no cover - depends on local MT5 bridge
        return _actual_unavailable(f"MetaTrader5_import_failed:{type(exc).__name__}:{exc}")

    if not mt5.initialize(path=str(terminal_exe)):  # pragma: no cover - depends on local terminal state
        return _actual_unavailable(f"mt5_initialize_failed:{mt5.last_error()}", terminal_exe=terminal_exe)

    try:  # pragma: no cover - exercised against the user's local demo terminal
        account = mt5.account_info()
        start = _actual_history_start(focus_date=focus_date, actual_history_start=actual_history_start)
        end = datetime.now()
        deals = list(mt5.history_deals_get(start, end) or [])
        orders = list(mt5.history_orders_get(start, end) or [])
        positions = list(mt5.positions_get() or [])
        trades = _build_actual_broker_trade_rows(mt5, deals, orders, positions)
        _mark_duplicate_actual_trades(trades)
        summary = _actual_broker_summary(trades)
        deduped_trades = [row for row in trades if str(row.get("is_duplicate", "")).lower() != "true"]
        return {
            "status": "CONNECTED",
            "reason": "",
            "terminal_exe": str(terminal_exe),
            "focus_date": focus_date,
            "history_start": start.strftime("%Y-%m-%d %H:%M:%S"),
            "history_end": end.strftime("%Y-%m-%d %H:%M:%S"),
            "account": {
                "login": getattr(account, "login", ""),
                "server": getattr(account, "server", ""),
                "currency": getattr(account, "currency", ""),
                "balance": f"{float(getattr(account, 'balance', 0.0)):.2f}" if account else "0.00",
                "equity": f"{float(getattr(account, 'equity', 0.0)):.2f}" if account else "0.00",
                "floating_profit": f"{float(getattr(account, 'profit', 0.0)):.2f}" if account else "0.00",
                "trade_allowed": bool(getattr(account, "trade_allowed", False)) if account else False,
            },
            "summary": summary,
            "deduped_summary": _actual_broker_summary(deduped_trades),
            "duplicate_count": len(trades) - len(deduped_trades),
            "trades": trades,
        }
    except Exception as exc:
        return _actual_unavailable(f"mt5_history_query_failed:{type(exc).__name__}:{exc}", terminal_exe=terminal_exe)
    finally:
        mt5.shutdown()


def _build_actual_broker_trade_rows(mt5: Any, deals: list[Any], orders: list[Any], positions: list[Any]) -> list[dict[str, Any]]:
    order_by_ticket = {getattr(order, "ticket", 0): order for order in orders}
    open_by_ticket = {
        getattr(position, "ticket", 0): position
        for position in positions
        if _is_demo_magic(getattr(position, "magic", 0), getattr(position, "comment", ""))
    }
    grouped: dict[int, list[Any]] = defaultdict(list)
    for deal in deals:
        if _is_demo_magic(getattr(deal, "magic", 0), getattr(deal, "comment", "")):
            grouped[int(getattr(deal, "position_id", 0))].append(deal)

    rows: list[dict[str, Any]] = []
    for position_id, position_deals in grouped.items():
        position_deals = sorted(position_deals, key=lambda item: getattr(item, "time", 0))
        entry_deal = next(
            (deal for deal in position_deals if getattr(deal, "entry", None) == getattr(mt5, "DEAL_ENTRY_IN", 0)),
            None,
        )
        if entry_deal is None:
            continue
        exit_deals = [
            deal
            for deal in position_deals
            if getattr(deal, "entry", None)
            in (
                getattr(mt5, "DEAL_ENTRY_OUT", 1),
                getattr(mt5, "DEAL_ENTRY_INOUT", 2),
                getattr(mt5, "DEAL_ENTRY_OUT_BY", 3),
            )
        ]
        open_position = open_by_ticket.get(position_id)
        entry_order = order_by_ticket.get(getattr(entry_deal, "order", 0))
        exit_deal = exit_deals[-1] if exit_deals else None
        exit_order = order_by_ticket.get(getattr(exit_deal, "order", 0)) if exit_deal else None
        candidate, status = _candidate_status_from_magic(
            int(getattr(entry_deal, "magic", 0)), str(getattr(entry_deal, "comment", ""))
        )
        state = "OPEN" if open_position else "CLOSED"
        realized_pnl = sum(_deal_total_pnl(deal) for deal in position_deals)
        floating_pnl = float(getattr(open_position, "profit", 0.0)) if open_position else 0.0
        profit = floating_pnl if state == "OPEN" else realized_pnl
        sl = getattr(open_position, "sl", "") if open_position else getattr(entry_order, "sl", "")
        tp = getattr(open_position, "tp", "") if open_position else getattr(entry_order, "tp", "")
        rows.append(
            {
                "entry_time": _timestamp_text(getattr(entry_deal, "time", 0)),
                "exit_time": _timestamp_text(getattr(exit_deal, "time", 0)) if exit_deal else "",
                "candidate": candidate,
                "status": status,
                "symbol": getattr(entry_deal, "symbol", ""),
                "direction": _deal_direction(mt5, getattr(entry_deal, "type", "")),
                "volume": f"{float(getattr(entry_deal, 'volume', 0.0)):.2f}",
                "entry_price": _fmt_price(float(getattr(entry_deal, "price", 0.0))),
                "exit_price": _fmt_price(float(getattr(exit_deal, "price", 0.0))) if exit_deal else "",
                "sl": _fmt_price(float(sl)) if _to_float(sl) is not None else "",
                "tp": _fmt_price(float(tp)) if _to_float(tp) is not None else "",
                "state": state,
                "profit_aed": f"{profit:.2f}",
                "position_ticket": str(position_id),
                "magic": str(getattr(entry_deal, "magic", "")),
                "entry_order": str(getattr(entry_deal, "order", "")),
                "exit_order": str(getattr(exit_deal, "order", "")) if exit_deal else "",
                "entry_deal": str(getattr(entry_deal, "ticket", "")),
                "exit_deal": str(getattr(exit_deal, "ticket", "")) if exit_deal else "",
                "duplicate_key": "",
                "duplicate_role": "unique",
                "is_duplicate": "false",
                "entry_comment": str(getattr(entry_deal, "comment", "")),
                "exit_comment": str(getattr(exit_deal, "comment", "")) if exit_deal else "",
            }
        )
    rows.sort(key=lambda item: str(item["entry_time"]), reverse=True)
    return rows


def _mark_duplicate_actual_trades(rows: list[dict[str, Any]]) -> None:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        key = _actual_duplicate_key(row)
        row["duplicate_key"] = key
        groups[key].append(row)

    for key, items in groups.items():
        if len(items) == 1:
            items[0]["duplicate_role"] = "unique"
            items[0]["is_duplicate"] = "false"
            continue
        keep = min(
            items,
            key=lambda item: (
                DEDUP_KEEP_PRIORITY.get(str(item.get("candidate", "")), 999),
                str(item.get("position_ticket", "")),
            ),
        )
        for item in items:
            item["duplicate_role"] = "kept" if item is keep else "duplicate"
            item["is_duplicate"] = "false" if item is keep else "true"


def _actual_duplicate_key(row: dict[str, Any]) -> str:
    entry_time = str(row.get("entry_time", ""))
    entry_minute = entry_time[:16]
    symbol = str(row.get("symbol", "")).upper()
    direction = str(row.get("direction", "")).upper()
    volume = str(row.get("volume", ""))
    return "|".join([entry_minute, symbol, direction, volume])


def _actual_broker_summary(trades: list[dict[str, Any]]) -> dict[str, Any]:
    closed = [row for row in trades if row.get("state") == "CLOSED"]
    open_rows = [row for row in trades if row.get("state") == "OPEN"]
    wins = [row for row in closed if (_to_float(row.get("profit_aed")) or 0.0) > 0.0]
    losses = [row for row in closed if (_to_float(row.get("profit_aed")) or 0.0) < 0.0]
    closed_pnl = sum(_to_float(row.get("profit_aed")) or 0.0 for row in closed)
    floating_pnl = sum(_to_float(row.get("profit_aed")) or 0.0 for row in open_rows)
    return {
        "actual_trades": len(trades),
        "closed_trades": len(closed),
        "open_trades": len(open_rows),
        "wins": len(wins),
        "losses": len(losses),
        "closed_win_rate_pct": f"{(len(wins) / len(closed) * 100.0):.2f}" if closed else "n/a",
        "closed_pnl_aed": f"{closed_pnl:.2f}",
        "floating_pnl_aed": f"{floating_pnl:.2f}",
        "total_pnl_aed": f"{closed_pnl + floating_pnl:.2f}",
    }


def _actual_unavailable(reason: str, terminal_exe: Path | None = None) -> dict[str, Any]:
    return {
        "status": "UNAVAILABLE",
        "reason": reason,
        "terminal_exe": str(terminal_exe) if terminal_exe else "",
        "focus_date": "",
        "history_start": "",
        "history_end": "",
        "account": {},
        "summary": _actual_broker_summary([]),
        "deduped_summary": _actual_broker_summary([]),
        "duplicate_count": 0,
        "trades": [],
    }


def _focus_date_start(focus_date: str) -> datetime:
    try:
        return datetime.strptime(focus_date, "%Y.%m.%d")
    except ValueError:
        return datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)


def _actual_history_start(focus_date: str, actual_history_start: str) -> datetime:
    try:
        return datetime.strptime(actual_history_start, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        return _focus_date_start(focus_date)


def _is_demo_magic(magic: Any, comment: Any) -> bool:
    try:
        magic_int = int(magic)
    except (TypeError, ValueError):
        magic_int = 0
    comment_text = str(comment)
    return (
        DEMO_MAGIC_MIN <= magic_int <= DEMO_MAGIC_MAX
        or magic_int in EXPERIMENTAL_MAGIC_CODES
        or P2WEAKNESS_MAGIC_MIN <= magic_int <= P2WEAKNESS_MAGIC_MAX
        or comment_text.startswith("P2DEMO_")
        or comment_text.startswith("P2WEAKNESS_BR_V1")
        or comment_text.startswith("WR50_")
    )


def _candidate_status_from_magic(magic: int, comment: str) -> tuple[str, str]:
    if magic in EXPERIMENTAL_MAGIC_CODES:
        return EXPERIMENTAL_MAGIC_CODES[magic]
    if P2WEAKNESS_MAGIC_MIN <= magic <= P2WEAKNESS_MAGIC_MAX:
        return "p2weakness_br_v1", "EXPERIMENTAL"
    if comment.startswith("P2WEAKNESS_BR_V1"):
        return "p2weakness_br_v1", "EXPERIMENTAL"
    if comment.startswith("WR50_"):
        return comment.split("|", 1)[0], "EXPERIMENTAL"
    candidate_code = (magic - DEMO_MAGIC_MIN) // 10
    if candidate_code in CANDIDATE_MAGIC_CODES:
        return CANDIDATE_MAGIC_CODES[candidate_code]
    if "sn_round" in comment:
        return "symbol_normalized_round_retest_v0", "ACCEPTED"
    if "swing_br" in comment:
        return "swing_breakout_retest_v0", "ACCEPTED"
    if "sess_ext" in comment:
        return "session_extreme_retest_v0", "PROVISIONAL"
    if "round" in comment:
        return "round_number_retest_v0", "PROVISIONAL"
    if "br" in comment:
        return "breakout_retest", "ACCEPTED"
    return comment or "UNKNOWN", "UNKNOWN"


def _deal_direction(mt5: Any, deal_type: Any) -> str:
    if deal_type == getattr(mt5, "DEAL_TYPE_BUY", 0):
        return "BUY"
    if deal_type == getattr(mt5, "DEAL_TYPE_SELL", 1):
        return "SELL"
    return str(deal_type)


def _deal_total_pnl(deal: Any) -> float:
    return (
        float(getattr(deal, "profit", 0.0))
        + float(getattr(deal, "commission", 0.0))
        + float(getattr(deal, "swap", 0.0))
        + float(getattr(deal, "fee", 0.0))
    )


def _timestamp_text(timestamp: Any) -> str:
    try:
        return datetime.fromtimestamp(int(timestamp)).strftime("%Y-%m-%d %H:%M:%S")
    except (OSError, TypeError, ValueError):
        return ""


def _build_signal_ledger(
    logs: list[dict[str, Any]],
    margin_aed: float,
    leverage: float,
    notional_aed: float,
) -> list[dict[str, Any]]:
    ledger: list[dict[str, Any]] = []
    trade_no = 1
    for log in logs:
        rows = list(log["rows"])
        for idx, row in enumerate(rows):
            if str(row.get("would_signal", "")).lower() != "true":
                continue
            entry = _to_float(row.get("entry_price"))
            stop = _to_float(row.get("stop_loss"))
            target = _to_float(row.get("take_profit"))
            if entry is None or stop is None or target is None or entry <= 0:
                continue
            outcome = _resolve_outcome(row, rows[idx + 1 :], entry, stop, target, notional_aed)
            pnl = outcome["pnl_aed"]
            ledger.append(
                {
                    "trade_no": trade_no,
                    "date": _date_part(row.get("timestamp_broker")),
                    "timestamp_broker": row.get("timestamp_broker", ""),
                    "timestamp_local": row.get("timestamp_local", ""),
                    "candidate": log["candidate"],
                    "status": log["status"],
                    "symbol": log["symbol"],
                    "direction": row.get("direction", ""),
                    "entry_price": _fmt_price(entry),
                    "stop_loss": _fmt_price(stop),
                    "take_profit": _fmt_price(target),
                    "exit_price": _fmt_price(outcome["exit_price"]),
                    "outcome": outcome["outcome"],
                    "exit_source": outcome["exit_source"],
                    "exit_time": outcome["exit_time"],
                    "bars_to_outcome": outcome["bars_to_outcome"],
                    "margin_aed": f"{margin_aed:.2f}",
                    "leverage": f"{leverage:.2f}",
                    "notional_aed": f"{notional_aed:.2f}",
                    "pnl_aed": f"{pnl:.4f}",
                    "return_on_margin_pct": f"{(pnl / margin_aed * 100.0):.4f}" if margin_aed else "0.0000",
                    "reason_code": row.get("reason_code", ""),
                    "spread_points": row.get("spread_points", ""),
                    "source_log": log["file"],
                }
            )
            trade_no += 1
    return ledger


def _resolve_outcome(
    signal: dict[str, str],
    future_rows: list[dict[str, str]],
    entry: float,
    stop: float,
    target: float,
    notional_aed: float,
) -> dict[str, Any]:
    direction = str(signal.get("direction", "")).upper()
    for bar_index, row in enumerate(future_rows, start=1):
        bid = _to_float(row.get("bid"))
        ask = _to_float(row.get("ask"))
        if bid is None or ask is None:
            continue
        if direction == "LONG":
            if bid <= stop:
                return _outcome("LOSS_STOP", "stop_loss", row, bar_index, stop, entry, direction, notional_aed)
            if bid >= target:
                return _outcome("WIN_TP", "take_profit", row, bar_index, target, entry, direction, notional_aed)
        elif direction == "SHORT":
            if ask >= stop:
                return _outcome("LOSS_STOP", "stop_loss", row, bar_index, stop, entry, direction, notional_aed)
            if ask <= target:
                return _outcome("WIN_TP", "take_profit", row, bar_index, target, entry, direction, notional_aed)

    latest = future_rows[-1] if future_rows else signal
    bid = _to_float(latest.get("bid")) or entry
    ask = _to_float(latest.get("ask")) or entry
    exit_price = bid if direction == "LONG" else ask
    return _outcome("OPEN_MARK", "latest_snapshot", latest, len(future_rows), exit_price, entry, direction, notional_aed)


def _outcome(
    outcome: str,
    exit_source: str,
    row: dict[str, str],
    bars_to_outcome: int,
    exit_price: float,
    entry: float,
    direction: str,
    notional_aed: float,
) -> dict[str, Any]:
    if direction == "LONG":
        pnl = ((exit_price - entry) / entry) * notional_aed
    else:
        pnl = ((entry - exit_price) / entry) * notional_aed
    return {
        "outcome": outcome,
        "exit_source": exit_source,
        "exit_time": row.get("timestamp_broker", ""),
        "bars_to_outcome": bars_to_outcome,
        "exit_price": exit_price,
        "pnl_aed": pnl,
    }


def _build_summary_rows(
    logs: list[dict[str, Any]],
    ledger: list[dict[str, Any]],
    focus_date: str,
) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in ledger:
        grouped[(str(row["candidate"]), str(row["symbol"]))].append(row)

    rows: list[dict[str, Any]] = []
    for log in sorted(logs, key=lambda item: (str(item["candidate"]), str(item["symbol"]))):
        key = (str(log["candidate"]), str(log["symbol"]))
        trades = grouped.get(key, [])
        today = [row for row in trades if row["date"] == focus_date]
        rows.append(_rollup_row(log["candidate"], log["status"], log["symbol"], today, log))
    return rows


def _build_candidate_rows(ledger: list[dict[str, Any]], focus_date: str) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in ledger:
        if row["date"] == focus_date:
            grouped[(str(row["candidate"]), str(row["status"]))].append(row)
    return [_rollup_row(candidate, status, "ALL", rows, None) for (candidate, status), rows in sorted(grouped.items())]


def _build_symbol_rows(ledger: list[dict[str, Any]], focus_date: str) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in ledger:
        if row["date"] == focus_date:
            grouped[str(row["symbol"])].append(row)
    return [_rollup_row("ALL", "ALL", symbol, rows, None) for symbol, rows in sorted(grouped.items())]


def _rollup_row(
    candidate: str,
    status: str,
    symbol: str,
    trades: list[dict[str, Any]],
    log: dict[str, Any] | None,
) -> dict[str, Any]:
    wins = [row for row in trades if row["outcome"] == "WIN_TP"]
    losses = [row for row in trades if row["outcome"] == "LOSS_STOP"]
    open_rows = [row for row in trades if row["outcome"] == "OPEN_MARK"]
    closed = len(wins) + len(losses)
    pnl = sum(_to_float(row.get("pnl_aed")) or 0.0 for row in trades)
    closed_pnl = sum(_to_float(row.get("pnl_aed")) or 0.0 for row in wins + losses)
    open_pnl = sum(_to_float(row.get("pnl_aed")) or 0.0 for row in open_rows)
    p_values = [_to_float(row.get("pnl_aed")) or 0.0 for row in trades]
    return {
        "candidate": candidate,
        "status": status,
        "symbol": symbol,
        "rows_today": _rows_today(log) if log else "",
        "signals": len(trades),
        "longs": sum(1 for row in trades if row["direction"] == "LONG"),
        "shorts": sum(1 for row in trades if row["direction"] == "SHORT"),
        "wins": len(wins),
        "losses": len(losses),
        "open": len(open_rows),
        "closed_win_rate_pct": f"{(len(wins) / closed * 100.0):.2f}" if closed else "n/a",
        "pnl_aed": f"{pnl:.4f}",
        "closed_pnl_aed": f"{closed_pnl:.4f}",
        "open_mark_pnl_aed": f"{open_pnl:.4f}",
        "best_trade_aed": f"{max(p_values):.4f}" if p_values else "n/a",
        "worst_trade_aed": f"{min(p_values):.4f}" if p_values else "n/a",
        "latest_log_write": log["last_write_text"] if log else "",
    }


def _coverage_row(log: dict[str, Any], focus_date: str) -> dict[str, Any]:
    rows = list(log["rows"])
    today = [row for row in rows if _date_part(row.get("timestamp_broker")) == focus_date]
    signals = [row for row in today if str(row.get("would_signal", "")).lower() == "true"]
    latest_row = rows[-1] if rows else {}
    return {
        "candidate": log["candidate"],
        "status": log["status"],
        "symbol": log["symbol"],
        "file": log["file"],
        "rows_total": len(rows),
        "rows_today": len(today),
        "signals_today": len(signals),
        "dry_run": log["dry_run"],
        "broker_action_allowed": log["broker_action_allowed"],
        "latest_bar": latest_row.get("m5_bar_time", ""),
        "latest_write": log["last_write_text"],
    }


def _rows_today(log: dict[str, Any] | None) -> int:
    if not log:
        return 0
    latest_date = _latest_broker_date([log])
    return sum(1 for row in log["rows"] if _date_part(row.get("timestamp_broker")) == latest_date)


def _latest_broker_date(logs: list[dict[str, Any]]) -> str:
    dates = [
        _date_part(row.get("timestamp_broker"))
        for log in logs
        for row in log["rows"]
        if _date_part(row.get("timestamp_broker"))
    ]
    return max(dates) if dates else datetime.now().strftime("%Y.%m.%d")


def _latest_log_write(logs: list[dict[str, Any]]) -> str:
    if not logs:
        return "n/a"
    return max(str(log["last_write_text"]) for log in logs)


def _oldest_log_write(logs: list[dict[str, Any]]) -> str:
    if not logs:
        return "n/a"
    return min(str(log["last_write_text"]) for log in logs)


def _render_html(payload: dict[str, Any]) -> str:
    summary_rows = payload["summary"]
    coverage_rows = payload["coverage"]
    order_rows = payload["orders"]
    actual_broker = payload.get("actual_broker", _actual_unavailable("payload_missing"))
    actual_rows = list(actual_broker.get("trades", []))
    actual_summary = actual_broker.get("summary", _actual_broker_summary([]))
    actual_account = actual_broker.get("account", {})
    ledger = payload["ledger"]
    candidate_rows = payload["candidate_summary"]
    symbol_rows = payload["symbol_summary"]
    total_pnl = sum(_to_float(row.get("pnl_aed")) or 0.0 for row in ledger if row.get("date") == payload["focus_date"])
    closed = [row for row in ledger if row.get("date") == payload["focus_date"] and row.get("outcome") != "OPEN_MARK"]
    wins = [row for row in closed if row.get("outcome") == "WIN_TP"]
    win_rate = (len(wins) / len(closed) * 100.0) if closed else 0.0
    accepted_signals = sum(
        1
        for row in ledger
        if row.get("date") == payload["focus_date"] and str(row.get("status")).upper() == "ACCEPTED"
    )
    provisional_signals = sum(
        1
        for row in ledger
        if row.get("date") == payload["focus_date"] and str(row.get("status")).upper() == "PROVISIONAL"
    )
    data_json = html.escape(
        json.dumps(
            {
                "summary": summary_rows,
                "coverage": coverage_rows,
                "ledger": ledger,
                "orders": order_rows,
                "actual_broker": actual_broker,
            },
            separators=(",", ":"),
        )
    )
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Demo Observer / Executor Dashboard</title>
  <style>
    :root {{
      --bg: #f5f7f8;
      --surface: #ffffff;
      --surface-2: #edf2f4;
      --ink: #1e2528;
      --muted: #657278;
      --line: #d9e0e3;
      --green: #147a4a;
      --red: #b93636;
      --amber: #9b6b00;
      --blue: #245c8f;
      --shadow: 0 12px 30px rgba(25, 39, 48, 0.10);
    }}
    [data-theme="dark"] {{
      --bg: #11181b;
      --surface: #182226;
      --surface-2: #213036;
      --ink: #eef4f5;
      --muted: #9badb4;
      --line: #304249;
      --green: #5bd29a;
      --red: #ff7d7d;
      --amber: #f4c45f;
      --blue: #87bef0;
      --shadow: 0 14px 32px rgba(0, 0, 0, 0.28);
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      background: var(--bg);
      color: var(--ink);
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      letter-spacing: 0;
    }}
    a {{ color: var(--blue); }}
    .shell {{ width: min(1440px, calc(100% - 32px)); margin: 0 auto; padding: 24px 0 56px; }}
    .hero {{
      display: grid;
      grid-template-columns: minmax(0, 1fr) auto;
      gap: 20px;
      align-items: end;
      padding: 22px 0 18px;
      border-bottom: 1px solid var(--line);
    }}
    h1 {{ margin: 0; font-size: 30px; line-height: 1.08; }}
    .subtitle {{ margin: 8px 0 0; color: var(--muted); max-width: 820px; line-height: 1.5; }}
    .actions {{ display: flex; gap: 8px; flex-wrap: wrap; justify-content: flex-end; }}
    button, select, input {{
      border: 1px solid var(--line);
      background: var(--surface);
      color: var(--ink);
      border-radius: 6px;
      padding: 9px 10px;
      font: inherit;
    }}
    button {{ cursor: pointer; }}
    .nav {{
      position: sticky;
      top: 0;
      z-index: 5;
      display: flex;
      gap: 8px;
      padding: 10px 0;
      background: color-mix(in srgb, var(--bg) 90%, transparent);
      backdrop-filter: blur(12px);
      overflow-x: auto;
    }}
    .nav a {{
      flex: 0 0 auto;
      text-decoration: none;
      color: var(--ink);
      border: 1px solid var(--line);
      background: var(--surface);
      border-radius: 6px;
      padding: 8px 10px;
      font-size: 13px;
    }}
    .cards {{ display: grid; grid-template-columns: repeat(6, minmax(0, 1fr)); gap: 12px; margin: 18px 0; }}
    .card, .panel {{
      background: var(--surface);
      border: 1px solid var(--line);
      border-radius: 8px;
      box-shadow: var(--shadow);
    }}
    .card {{ padding: 14px; min-height: 104px; }}
    .label {{ color: var(--muted); font-size: 12px; text-transform: uppercase; }}
    .value {{ margin-top: 9px; font-size: 24px; font-weight: 760; }}
    .hint {{ margin-top: 8px; color: var(--muted); font-size: 12px; line-height: 1.35; }}
    .panel {{ margin-top: 16px; padding: 16px; }}
    .panel-head {{ display: flex; gap: 14px; justify-content: space-between; align-items: start; margin-bottom: 14px; }}
    h2 {{ margin: 0; font-size: 18px; }}
    .filters {{ display: flex; gap: 8px; flex-wrap: wrap; justify-content: flex-end; }}
    .filters input {{ min-width: 220px; }}
    .check-filter {{
      display: inline-flex;
      align-items: center;
      gap: 8px;
      min-height: 38px;
      padding: 0 10px;
      border: 1px solid var(--line);
      background: var(--surface);
      border-radius: 6px;
      color: var(--ink);
      font-size: 13px;
      white-space: nowrap;
    }}
    .check-filter input {{ min-width: 0; width: 16px; height: 16px; }}
    .table-wrap {{ overflow-x: auto; border: 1px solid var(--line); border-radius: 8px; }}
    table {{ width: 100%; border-collapse: collapse; min-width: 900px; }}
    th, td {{ padding: 9px 10px; border-bottom: 1px solid var(--line); text-align: left; vertical-align: top; font-size: 13px; }}
    th {{ background: var(--surface-2); color: var(--muted); font-size: 12px; text-transform: uppercase; position: sticky; top: 43px; z-index: 2; }}
    td.num, th.num {{ text-align: right; font-variant-numeric: tabular-nums; }}
    tr[hidden] {{ display: none; }}
    .pill {{ display: inline-flex; align-items: center; border-radius: 999px; padding: 4px 8px; font-size: 12px; font-weight: 700; border: 1px solid var(--line); }}
    .accepted, .win {{ color: var(--green); }}
    .provisional, .open, .experimental {{ color: var(--amber); }}
    .loss, .negative {{ color: var(--red); }}
    .flat {{ color: var(--muted); }}
    .note-grid {{ display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 10px; margin-top: 10px; }}
    .note {{ background: var(--surface-2); border-radius: 8px; padding: 10px; color: var(--muted); font-size: 13px; line-height: 1.45; }}
    .bar {{
      height: 8px;
      background: var(--surface-2);
      border-radius: 999px;
      overflow: hidden;
      margin-top: 8px;
    }}
    .bar span {{ display: block; height: 100%; background: var(--blue); width: var(--w); }}
    .status-row {{ display: flex; align-items: center; gap: 8px; }}
    .dot {{ width: 9px; height: 9px; border-radius: 999px; background: var(--green); }}
    .footer {{ color: var(--muted); font-size: 12px; margin-top: 20px; }}
    @media (max-width: 1060px) {{
      .cards {{ grid-template-columns: repeat(3, minmax(0, 1fr)); }}
      .hero {{ grid-template-columns: 1fr; }}
      .actions, .filters {{ justify-content: flex-start; }}
    }}
    @media (max-width: 680px) {{
      .shell {{ width: min(100% - 20px, 1440px); padding-top: 10px; }}
      h1 {{ font-size: 25px; }}
      .cards {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
      .card {{ min-height: 96px; }}
      .value {{ font-size: 21px; }}
      .panel {{ padding: 12px; }}
      .panel-head {{ display: block; }}
      .filters {{ margin-top: 12px; }}
      .filters input, .filters select {{ width: 100%; min-width: 0; }}
      .note-grid {{ grid-template-columns: 1fr; }}
      th {{ position: static; }}
    }}
  </style>
</head>
<body>
  <main class="shell">
    <header class="hero">
      <div>
        <h1>Demo Observer / Executor Dashboard</h1>
        <p class="subtitle">All 14 Capital.com demo EAs in one place. This page reads experimental observer/executor CSV logs and shows coverage, would-signal activity, demo order attempts, retcodes, and estimated 50x / AED 100 margin PnL.</p>
      </div>
      <div class="actions">
        <button id="themeBtn" type="button">Theme</button>
        <a href="status.html"><button type="button">Main Status</button></a>
      </div>
    </header>
    <nav class="nav" aria-label="Page sections">
      <a href="#overview">Overview</a>
      <a href="#coverage">Coverage</a>
      <a href="#summary">EA Summary</a>
      <a href="#actual-broker">Actual Broker Trades</a>
      <a href="#orders">Orders</a>
      <a href="#candidate">Candidate Rollup</a>
      <a href="#symbol">Symbol Rollup</a>
      <a href="#ledger">Signal Ledger</a>
      <a href="#notes">Notes</a>
    </nav>
    <section id="overview" class="cards">
      {_metric_card("Active logs", payload["log_file_count"], "Expected: 14 observer log files")}
      {_metric_card("Signals today", payload["signals_focus_date"], f"Focus date: {html.escape(str(payload['focus_date']))}")}
      {_metric_card("Accepted signals", accepted_signals, "Accepted candidate rows only")}
      {_metric_card("Provisional signals", provisional_signals, "Gate-9 pending / provisional candidates")}
      {_metric_card("Orders today", payload["orders_sent_focus_date"], f"{payload['orders_focus_date']} order-log rows")}
      {_metric_card("Est. PnL today", f"{total_pnl:+.2f} AED", "Includes open mark-to-market")}
      {_metric_card("Actual trades", actual_summary.get("actual_trades", 0), f"{actual_summary.get('closed_trades', 0)} closed / {actual_summary.get('open_trades', 0)} open")}
      {_metric_card("Actual PnL", f"{actual_summary.get('total_pnl_aed', '0.00')} AED", "Direct MT5 realized + floating PnL")}
    </section>
    <section class="panel">
      <div class="note-grid">
        <div class="note"><strong>Latest write:</strong><br>{html.escape(str(payload["latest_log_write"]))}</div>
        <div class="note"><strong>Source folder:</strong><br>{html.escape(str(payload["files_dir"]))}</div>
        <div class="note"><strong>Actual broker account:</strong><br>{html.escape(str(actual_account.get("login", "n/a")))} / {html.escape(str(actual_account.get("server", actual_broker.get("status", "UNKNOWN"))))}</div>
        <div class="note"><strong>Live refresh URL:</strong><br><a href="{html.escape(str(payload.get("live_refresh_url", DEFAULT_LIVE_REFRESH_URL)))}">{html.escape(str(payload.get("live_refresh_url", DEFAULT_LIVE_REFRESH_URL)))}</a></div>
        <div class="note"><strong>Execution mode:</strong><br>Observer rows are telemetry-only; executor rows are demo-only and must refuse live/real servers.</div>
      </div>
    </section>
    <section id="coverage" class="panel">
      <div class="panel-head">
        <div><h2>Coverage</h2><div class="hint">Confirms every expected candidate-symbol logger is writing rows.</div></div>
      </div>
      {_coverage_table(coverage_rows)}
    </section>
    <section id="summary" class="panel">
      <div class="panel-head">
        <div><h2>EA Summary</h2><div class="hint">Per candidate and symbol for the focus date.</div></div>
        {_filters("summary")}
      </div>
      {_summary_table(summary_rows, "summaryTable")}
    </section>
    <section id="actual-broker" class="panel">
      <div class="panel-head">
        <div><h2>Actual Broker Trades</h2><div class="hint">Direct MT5 account history and open-position evidence. This is the real broker PnL source, separate from simulated signal outcomes.</div></div>
        {_filters("actual")}
      </div>
      {_actual_broker_table(actual_broker)}
    </section>
    <section id="orders" class="panel">
      <div class="panel-head">
        <div><h2>Order Execution</h2><div class="hint">Actual demo order attempts, guard blocks, and broker retcodes from executor logs.</div></div>
        {_filters("order")}
      </div>
      {_order_table(order_rows)}
    </section>
    <section id="candidate" class="panel">
      <div class="panel-head">
        <div><h2>Candidate Rollup</h2><div class="hint">Aggregates all symbols for each EA.</div></div>
      </div>
      {_summary_table(candidate_rows, "candidateTable")}
    </section>
    <section id="symbol" class="panel">
      <div class="panel-head">
        <div><h2>Symbol Rollup</h2><div class="hint">Aggregates all EAs for each symbol.</div></div>
      </div>
      {_summary_table(symbol_rows, "symbolTable")}
    </section>
    <section id="ledger" class="panel">
      <div class="panel-head">
        <div><h2>Signal Ledger</h2><div class="hint">Every would-signal in the observer logs. Open rows are marked to the latest logged snapshot.</div></div>
        {_filters("ledger")}
      </div>
      {_ledger_table(ledger)}
    </section>
    <section id="notes" class="panel">
      <div class="panel-head"><div><h2>Notes</h2></div></div>
      <ul>
        {"".join(f"<li>{html.escape(str(item))}</li>" for item in payload["notes"])}
      </ul>
      <p class="footer">Generated at {html.escape(str(payload["generated_at_utc"]))}. JSON/CSV mirrors are in `xau-usd/xauusd-phase1/outputs/reports/`.</p>
    </section>
  </main>
  <script id="dashboardData" type="application/json">{data_json}</script>
  <script>
    const root = document.documentElement;
    const savedTheme = localStorage.getItem('demoObserverTheme');
    if (savedTheme) root.dataset.theme = savedTheme;
    document.getElementById('themeBtn').addEventListener('click', () => {{
      root.dataset.theme = root.dataset.theme === 'dark' ? 'light' : 'dark';
      localStorage.setItem('demoObserverTheme', root.dataset.theme);
    }});

    function installFilters(prefix, tableId) {{
      const status = document.getElementById(prefix + 'Status');
      const candidate = document.getElementById(prefix + 'Candidate');
        const symbol = document.getElementById(prefix + 'Symbol');
        const outcome = document.getElementById(prefix + 'Outcome');
        const dedupe = document.getElementById(prefix + 'Dedupe');
        const search = document.getElementById(prefix + 'Search');
        const table = document.getElementById(tableId);
        if (!table) return;
      const controls = [status, candidate, symbol, outcome, dedupe, search].filter(Boolean);
      function apply() {{
        const s = status ? status.value : 'all';
        const c = candidate ? candidate.value : 'all';
        const y = symbol ? symbol.value : 'all';
        const o = outcome ? outcome.value : 'all';
        const hideDuplicates = dedupe ? dedupe.checked : false;
        const q = search ? search.value.trim().toLowerCase() : '';
        for (const row of table.querySelectorAll('tbody tr')) {{
          const keep =
            (s === 'all' || row.dataset.status === s) &&
            (c === 'all' || row.dataset.candidate === c) &&
            (y === 'all' || row.dataset.symbol === y) &&
            (o === 'all' || row.dataset.outcome === o) &&
            (!hideDuplicates || row.dataset.duplicate !== 'true') &&
            (!q || row.innerText.toLowerCase().includes(q));
          row.hidden = !keep;
        }}
        if (prefix === 'actual') updateActualSummary(table, hideDuplicates);
      }}
      controls.forEach(control => control.addEventListener('input', apply));
      apply();
    }}
    function updateActualSummary(table, hideDuplicates) {{
      const target = document.getElementById('actualVisibleSummary');
      if (!target) return;
      const rows = Array.from(table.querySelectorAll('tbody tr')).filter(row => !row.hidden);
      const closed = rows.filter(row => row.dataset.state === 'CLOSED');
      const openRows = rows.filter(row => row.dataset.state === 'OPEN');
      const wins = closed.filter(row => Number(row.dataset.pnl || 0) > 0);
      const losses = closed.filter(row => Number(row.dataset.pnl || 0) < 0);
      const pnl = rows.reduce((total, row) => total + Number(row.dataset.pnl || 0), 0);
      const winRate = closed.length ? (wins.length / closed.length * 100).toFixed(2) : 'n/a';
      const label = hideDuplicates ? 'Deduplicated visible view' : 'Visible view';
      target.textContent = `${{label}}: ${{rows.length}} trades, ${{closed.length}} closed, ${{openRows.length}} open, ${{wins.length}} wins / ${{losses.length}} losses, win rate ${{winRate}}%, PnL ${{pnl >= 0 ? '+' : ''}}${{pnl.toFixed(2)}} AED.`;
    }}
    installFilters('summary', 'summaryTable');
    installFilters('actual', 'actualTable');
    installFilters('order', 'orderTable');
    installFilters('ledger', 'ledgerTable');
  </script>
</body>
</html>
"""


def _metric_card(label: str, value: Any, hint: str) -> str:
    css = _money_class(value) if "PnL" in label else ""
    return (
        '<article class="card">'
        f'<div class="label">{html.escape(label)}</div>'
        f'<div class="value {css}">{html.escape(str(value))}</div>'
        f'<div class="hint">{html.escape(hint)}</div>'
        "</article>"
    )


def _filters(prefix: str) -> str:
    outcome = ""
    if prefix == "ledger":
        outcome = (
            f'<select id="{prefix}Outcome" aria-label="Outcome filter">'
            '<option value="all">All outcomes</option>'
            '<option value="WIN_TP">Wins</option>'
            '<option value="LOSS_STOP">Losses</option>'
            '<option value="OPEN_MARK">Open</option>'
            "</select>"
        )
    dedupe = ""
    if prefix == "actual":
        dedupe = (
            '<label class="check-filter">'
            f'<input id="{prefix}Dedupe" type="checkbox">'
            "<span>Hide duplicates</span>"
            "</label>"
        )
    return "".join(
        [
            '<div class="filters">',
            f'<select id="{prefix}Status" aria-label="Status filter">',
            '<option value="all">All statuses</option>',
            '<option value="ACCEPTED">Accepted</option>',
            '<option value="PROVISIONAL">Provisional</option>',
            '<option value="EXPERIMENTAL">Experimental</option>',
            "</select>",
            f'<select id="{prefix}Candidate" aria-label="Candidate filter">{_candidate_options()}</select>',
            f'<select id="{prefix}Symbol" aria-label="Symbol filter">',
            '<option value="all">All symbols</option><option value="EURUSD">EURUSD</option><option value="USDJPY">USDJPY</option><option value="XAUUSD">XAUUSD</option>',
            "</select>",
            outcome,
            dedupe,
            f'<input id="{prefix}Search" type="search" placeholder="Search">',
            "</div>",
        ]
    )


def _candidate_options() -> str:
    candidates = [
        "breakout_retest",
        "swing_breakout_retest_v0",
        "symbol_normalized_round_retest_v0",
        "round_number_retest_v0",
        "session_extreme_retest_v0",
        "p2weakness_br_v1",
        "WR50_BreakoutEvening_v0",
        "WR50_BreakoutQuality_v0",
        "WR50_BreakoutExit1R_v0",
    ]
    return '<option value="all">All EAs</option>' + "".join(
        f'<option value="{html.escape(item)}">{html.escape(item)}</option>' for item in candidates
    )


def _coverage_table(rows: list[dict[str, Any]]) -> str:
    body = "\n".join(
        "<tr>"
        f"<td>{_status_dot(row)}</td>"
        f"<td>{html.escape(str(row.get('kind', 'observer')))}</td>"
        f"<td>{html.escape(str(row['candidate']))}</td>"
        f"<td>{_pill(row['status'])}</td>"
        f"<td>{html.escape(str(row['symbol']))}</td>"
        f"<td class=\"num\">{row['rows_today']}</td>"
        f"<td class=\"num\">{row['signals_today']}</td>"
        f"<td>{html.escape(str(row['latest_bar']))}</td>"
        f"<td>{html.escape(str(row['latest_write']))}</td>"
        f"<td>{html.escape(str(row['file']))}</td>"
        "</tr>"
        for row in rows
    )
    return (
        '<div class="table-wrap"><table><thead><tr>'
        "<th>Live</th><th>Mode</th><th>Candidate</th><th>Status</th><th>Symbol</th><th class=\"num\">Rows Today</th>"
        "<th class=\"num\">Signals</th><th>Latest Bar</th><th>Latest Write</th><th>File</th>"
        f"</tr></thead><tbody>{body}</tbody></table></div>"
    )


def _summary_table(rows: list[dict[str, Any]], table_id: str) -> str:
    body = "\n".join(
        f'<tr data-status="{html.escape(str(row["status"]))}" data-candidate="{html.escape(str(row["candidate"]))}" data-symbol="{html.escape(str(row["symbol"]))}">'
        f"<td>{html.escape(str(row['candidate']))}</td>"
        f"<td>{_pill(row['status'])}</td>"
        f"<td>{html.escape(str(row['symbol']))}</td>"
        f"<td class=\"num\">{row['signals']}</td>"
        f"<td class=\"num\">{row['longs']}</td>"
        f"<td class=\"num\">{row['shorts']}</td>"
        f"<td class=\"num accepted\">{row['wins']}</td>"
        f"<td class=\"num loss\">{row['losses']}</td>"
        f"<td class=\"num open\">{row['open']}</td>"
        f"<td class=\"num\">{row['closed_win_rate_pct']}</td>"
        f"<td class=\"num {_money_class(row['pnl_aed'])}\">{_signed(row['pnl_aed'])}</td>"
        f"<td class=\"num {_money_class(row['closed_pnl_aed'])}\">{_signed(row['closed_pnl_aed'])}</td>"
        f"<td class=\"num {_money_class(row['open_mark_pnl_aed'])}\">{_signed(row['open_mark_pnl_aed'])}</td>"
        f"<td>{html.escape(str(row.get('latest_log_write', '')))}</td>"
        "</tr>"
        for row in rows
    )
    return (
        f'<div class="table-wrap"><table id="{table_id}"><thead><tr>'
        "<th>Candidate</th><th>Status</th><th>Symbol</th><th class=\"num\">Signals</th><th class=\"num\">Long</th><th class=\"num\">Short</th>"
        "<th class=\"num\">Wins</th><th class=\"num\">Losses</th><th class=\"num\">Open</th><th class=\"num\">Win Rate</th>"
        "<th class=\"num\">Total PnL</th><th class=\"num\">Closed PnL</th><th class=\"num\">Open PnL</th><th>Latest Write</th>"
        f"</tr></thead><tbody>{body}</tbody></table></div>"
    )


def _ledger_table(rows: list[dict[str, Any]]) -> str:
    body = "\n".join(
        f'<tr data-status="{html.escape(str(row["status"]))}" data-candidate="{html.escape(str(row["candidate"]))}" data-symbol="{html.escape(str(row["symbol"]))}" data-outcome="{html.escape(str(row["outcome"]))}">'
        f"<td class=\"num\">{row['trade_no']}</td>"
        f"<td>{html.escape(str(row['timestamp_broker']))}</td>"
        f"<td>{html.escape(str(row['candidate']))}</td>"
        f"<td>{_pill(row['status'])}</td>"
        f"<td>{html.escape(str(row['symbol']))}</td>"
        f"<td>{html.escape(str(row['direction']))}</td>"
        f"<td>{_outcome_pill(row['outcome'])}</td>"
        f"<td class=\"num\">{row['entry_price']}</td>"
        f"<td class=\"num\">{row['stop_loss']}</td>"
        f"<td class=\"num\">{row['take_profit']}</td>"
        f"<td class=\"num\">{row['exit_price']}</td>"
        f"<td class=\"num {_money_class(row['pnl_aed'])}\">{_signed(row['pnl_aed'])}</td>"
        f"<td class=\"num\">{row['bars_to_outcome']}</td>"
        f"<td>{html.escape(str(row['reason_code']))}</td>"
        "</tr>"
        for row in rows
    )
    return (
        '<div class="table-wrap"><table id="ledgerTable"><thead><tr>'
        "<th class=\"num\">#</th><th>Broker Time</th><th>Candidate</th><th>Status</th><th>Symbol</th><th>Direction</th><th>Outcome</th>"
        "<th class=\"num\">Entry</th><th class=\"num\">SL</th><th class=\"num\">TP</th><th class=\"num\">Exit/Mark</th>"
        "<th class=\"num\">PnL AED</th><th class=\"num\">Bars</th><th>Reason</th>"
        f"</tr></thead><tbody>{body}</tbody></table></div>"
    )


def _actual_broker_table(actual_broker: dict[str, Any]) -> str:
    rows = list(actual_broker.get("trades", []))
    if actual_broker.get("status") != "CONNECTED":
        reason = html.escape(str(actual_broker.get("reason", "unknown")))
        return f'<p class="muted">Actual MT5 broker history is unavailable for this refresh: {reason}</p>'
    if not rows:
        return '<p class="muted">No actual MT5 demo trades were found for the configured history window.</p>'
    body = "\n".join(
        f'<tr data-status="{html.escape(str(row.get("status", "")))}" data-candidate="{html.escape(str(row.get("candidate", "")))}" data-symbol="{html.escape(str(row.get("symbol", "")))}" data-state="{html.escape(str(row.get("state", "")))}" data-duplicate="{html.escape(str(row.get("is_duplicate", "false")).lower())}" data-pnl="{html.escape(str(row.get("profit_aed", "0")))}">'
        f"<td>{html.escape(str(row.get('entry_time', '')))}</td>"
        f"<td>{html.escape(str(row.get('exit_time', '')))}</td>"
        f"<td>{html.escape(str(row.get('candidate', '')))}</td>"
        f"<td>{_pill(row.get('status', ''))}</td>"
        f"<td>{html.escape(str(row.get('symbol', '')))}</td>"
        f"<td>{html.escape(str(row.get('direction', '')))}</td>"
        f"<td class=\"num\">{html.escape(str(row.get('volume', '')))}</td>"
        f"<td>{_outcome_pill(row.get('state', ''))}</td>"
        f"<td class=\"num\">{html.escape(str(row.get('entry_price', '')))}</td>"
        f"<td class=\"num\">{html.escape(str(row.get('exit_price', '')))}</td>"
        f"<td class=\"num\">{html.escape(str(row.get('sl', '')))}</td>"
        f"<td class=\"num\">{html.escape(str(row.get('tp', '')))}</td>"
        f"<td class=\"num {_money_class(row.get('profit_aed', ''))}\">{_signed(row.get('profit_aed', ''))}</td>"
        f"<td>{html.escape(str(row.get('position_ticket', '')))}</td>"
        f"<td>{html.escape(str(row.get('duplicate_role', 'unique')))}</td>"
        f"<td>{html.escape(str(row.get('exit_comment', '')))}</td>"
        "</tr>"
        for row in rows
    )
    summary = actual_broker.get("summary", _actual_broker_summary([]))
    deduped = actual_broker.get("deduped_summary", _actual_broker_summary([]))
    history_start = html.escape(str(actual_broker.get("history_start", "")))
    history_end = html.escape(str(actual_broker.get("history_end", "")))
    history_line = (
        f"<p class=\"hint\">Actual MT5 history window: {history_start} to {history_end}.</p>"
        if history_start or history_end
        else ""
    )
    summary_line = (
        history_line
        + f"<p class=\"hint\">Actual MT5 summary: {html.escape(str(summary.get('actual_trades', 0)))} trades, "
        f"{html.escape(str(summary.get('closed_trades', 0)))} closed, "
        f"{html.escape(str(summary.get('open_trades', 0)))} open, "
        f"closed win rate {html.escape(str(summary.get('closed_win_rate_pct', 'n/a')))}%, "
        f"total PnL {_signed(summary.get('total_pnl_aed', '0.00'))} AED. "
        f"Deduplicated baseline: {html.escape(str(deduped.get('actual_trades', 0)))} trades, "
        f"win rate {html.escape(str(deduped.get('closed_win_rate_pct', 'n/a')))}%, "
        f"PnL {_signed(deduped.get('total_pnl_aed', '0.00'))} AED; "
        f"{html.escape(str(actual_broker.get('duplicate_count', 0)))} duplicate rows marked.</p>"
        '<p id="actualVisibleSummary" class="hint"></p>'
    )
    return (
        summary_line
        + '<div class="table-wrap"><table id="actualTable"><thead><tr>'
        "<th>Entry Time</th><th>Exit Time</th><th>Candidate</th><th>Status</th><th>Symbol</th><th>Side</th>"
        "<th class=\"num\">Lot</th><th>State</th><th class=\"num\">Entry</th><th class=\"num\">Exit</th>"
        "<th class=\"num\">SL</th><th class=\"num\">TP</th><th class=\"num\">PnL AED</th><th>Position</th><th>Duplicate</th><th>Exit Note</th>"
        f"</tr></thead><tbody>{body}</tbody></table></div>"
    )


def _order_table(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return '<p class="muted">No executor order-log rows exist yet. They will appear after a signal reaches the order-sending gate.</p>'
    body = "\n".join(
        f'<tr data-status="{html.escape(str(row.get("candidate_status", "")))}" data-candidate="{html.escape(str(row.get("candidate", "")))}" data-symbol="{html.escape(str(row.get("symbol", "")))}">'
        f"<td>{html.escape(str(row.get('timestamp_broker', '')))}</td>"
        f"<td>{html.escape(str(row.get('candidate', '')))}</td>"
        f"<td>{_pill(row.get('candidate_status', ''))}</td>"
        f"<td>{html.escape(str(row.get('symbol', '')))}</td>"
        f"<td>{html.escape(str(row.get('action', '')))}</td>"
        f"<td>{html.escape(str(row.get('direction', '')))}</td>"
        f"<td class=\"num\">{html.escape(str(row.get('volume', '')))}</td>"
        f"<td class=\"num\">{html.escape(str(row.get('request_price', '')))}</td>"
        f"<td class=\"num\">{html.escape(str(row.get('sl', '')))}</td>"
        f"<td class=\"num\">{html.escape(str(row.get('tp', '')))}</td>"
        f"<td>{html.escape(str(row.get('retcode', '')))}</td>"
        f"<td>{html.escape(str(row.get('retcode_description', '')))}</td>"
        f"<td>{html.escape(str(row.get('order_ticket', '')))}</td>"
        f"<td>{html.escape(str(row.get('deal_ticket', '')))}</td>"
        f"<td>{html.escape(str(row.get('guard_reason', '')))}</td>"
        "</tr>"
        for row in rows
    )
    return (
        '<div class="table-wrap"><table id="orderTable"><thead><tr>'
        "<th>Broker Time</th><th>Candidate</th><th>Status</th><th>Symbol</th><th>Action</th><th>Direction</th>"
        "<th class=\"num\">Volume</th><th class=\"num\">Request</th><th class=\"num\">SL</th><th class=\"num\">TP</th>"
        "<th>Retcode</th><th>Description</th><th>Order</th><th>Deal</th><th>Guard</th>"
        f"</tr></thead><tbody>{body}</tbody></table></div>"
    )


def _status_dot(row: dict[str, Any]) -> str:
    allowed = str(row.get("broker_action_allowed", "")).lower()
    dry = str(row.get("dry_run", "")).lower()
    if dry == "true" and allowed == "false":
        title = "dry-run telemetry active"
    elif dry == "false" and allowed == "true":
        title = "demo executor active"
    else:
        title = "review required"
    return f'<span class="status-row"><span class="dot"></span>{html.escape(title)}</span>'


def _pill(value: Any) -> str:
    label = str(value)
    upper = label.upper()
    css = (
        "accepted"
        if upper == "ACCEPTED"
        else "provisional"
        if upper == "PROVISIONAL"
        else "experimental"
        if upper == "EXPERIMENTAL"
        else "flat"
    )
    return f'<span class="pill {css}">{html.escape(label)}</span>'


def _outcome_pill(value: Any) -> str:
    label = str(value)
    css = "win" if label == "WIN_TP" else "loss" if label == "LOSS_STOP" else "open" if label == "OPEN" or label == "OPEN_MARK" else "flat"
    return f'<span class="pill {css}">{html.escape(label)}</span>'


def _write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = fieldnames or sorted({key for row in rows for key in row.keys()})
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _date_part(value: Any) -> str:
    text = str(value or "").strip()
    return text[:10] if len(text) >= 10 else ""


def _to_float(value: Any) -> float | None:
    try:
        text = str(value).strip()
        if text == "" or text.lower() == "n/a":
            return None
        return float(text)
    except (TypeError, ValueError):
        return None


def _fmt_price(value: float) -> str:
    return f"{value:.5f}" if abs(value) < 100 else f"{value:.2f}"


def _signed(value: Any) -> str:
    numeric = _to_float(value)
    if numeric is None:
        return "n/a"
    return f"{numeric:+.4f}"


def _money_class(value: Any) -> str:
    numeric = _to_float(str(value).replace(" AED", ""))
    if numeric is None:
        return "flat"
    if numeric > 0.000001:
        return "accepted"
    if numeric < -0.000001:
        return "negative"
    return "flat"


def _format_mtime(path: Path) -> str:
    if not path.exists():
        return ""
    return datetime.fromtimestamp(path.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S")


def _candidate_from_file(name: str) -> str:
    text = name.removeprefix("experimental_demo_attachment_log_")
    text = text.removeprefix("experimental_demo_executor_signal_log_").removesuffix(".csv")
    for suffix in ("_xauusd", "_eurusd", "_usdjpy"):
        if text.endswith(suffix):
            return text[: -len(suffix)]
    return text


def _symbol_from_file(name: str) -> str:
    text = name.removesuffix(".csv").upper()
    for symbol in ("XAUUSD", "EURUSD", "USDJPY"):
        if text.endswith(symbol):
            return symbol
    return "UNKNOWN"


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate the 14-EA experimental demo observer dashboard.")
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[3])
    parser.add_argument("--terminal-data-dir", type=Path, default=DEFAULT_TERMINAL_DATA_DIR)
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument("--margin-aed", type=float, default=DEFAULT_MARGIN_AED)
    parser.add_argument("--leverage", type=float, default=DEFAULT_LEVERAGE)
    parser.add_argument("--focus-date", default=None, help="Broker date in YYYY.MM.DD format; defaults to latest log date.")
    parser.add_argument("--terminal-exe", type=Path, default=DEFAULT_TERMINAL_EXE)
    parser.add_argument("--skip-broker-history", action="store_true")
    parser.add_argument(
        "--actual-history-start",
        default=DEFAULT_ACTUAL_HISTORY_START,
        help="Actual MT5 broker history start in YYYY-MM-DD HH:MM:SS format.",
    )
    args = parser.parse_args()
    output = generate_demo_observer_dashboard(
        repo_root=args.repo_root,
        terminal_data_dir=args.terminal_data_dir,
        output_path=args.output,
        margin_aed=args.margin_aed,
        leverage=args.leverage,
        focus_date=args.focus_date,
        terminal_exe=args.terminal_exe,
        include_broker_history=not args.skip_broker_history,
        actual_history_start=args.actual_history_start,
    )
    print(f"Dashboard: {output.html_path}")
    print(f"JSON: {output.json_path}")
    print(f"Summary CSV: {output.summary_csv_path}")
    print(f"Ledger CSV: {output.ledger_csv_path}")
    print(f"Actual broker trades CSV: {output.actual_broker_csv_path}")
    print(f"Logs: {output.log_file_count}; signals: {output.signal_count}; focus-date signals: {output.signals_today}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
