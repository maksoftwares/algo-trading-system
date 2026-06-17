from __future__ import annotations

import csv
import argparse
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path
from typing import Any

import MetaTrader5 as mt5


REPO_ROOT = Path(__file__).resolve().parents[3]
REPORTS_DIR = REPO_ROOT / "xau-usd" / "xauusd-phase1" / "outputs" / "reports"
MATCHING_START_UTC = datetime(2026, 6, 1, 0, 0, 0, tzinfo=timezone.utc)
DUBAI_TZ = timezone(timedelta(hours=4))
DEFAULT_SCAN_DATE = "2026-06-15"

EXPORT_COLUMNS = [
    "account",
    "entry_time_utc",
    "entry_time_dubai",
    "exit_time_utc",
    "candidate",
    "magic",
    "direction",
    "lots",
    "entry_price",
    "exit_price",
    "sl",
    "tp",
    "stop_distance_points",
    "spread_points",
    "cost_r",
    "exit_reason",
    "profit_aed",
    "dirstate_regime",
]

JOIN_COLUMNS = [
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
    "time_bucket",
    "weakness_shadow_action",
    "weakness_shadow_reason",
    "entry_comment",
    "exit_comment",
]


@dataclass(frozen=True)
class AccountSpec:
    label: str
    login: int
    terminal_exe: Path
    files_dir: Path
    signal_globs: tuple[str, ...]
    order_globs: tuple[str, ...]


ACCOUNT_SPECS = [
    AccountSpec(
        label="A1",
        login=1025742,
        terminal_exe=Path(r"C:\Program Files\MetaTrader 5\terminal64.exe"),
        files_dir=Path(
            r"C:\Users\ZHAO ZHU INFORMATION\AppData\Roaming\MetaQuotes\Terminal"
            r"\D0E8209F77C8CF37AD8BF550E51FF075\MQL5\Files"
        ),
        signal_globs=(
            "experimental_demo_executor_signal_log_v02_*_xauusd.csv",
            "phase2_demo_repair_executor_signal_log_v1_*_xauusd.csv",
        ),
        order_globs=(
            "experimental_demo_executor_order_log_v02_*_xauusd.csv",
            "phase2_demo_repair_executor_order_log_v1_*_xauusd.csv",
        ),
    ),
    AccountSpec(
        label="A2",
        login=1033030,
        terminal_exe=Path(r"C:\MT5PortableTier1BestEA\terminal64.exe"),
        files_dir=Path(r"C:\MT5PortableTier1BestEA\MQL5\Files"),
        signal_globs=("tier1_bestea_signal_log_xauusd.csv",),
        order_globs=("tier1_bestea_order_log_xauusd.csv",),
    ),
    AccountSpec(
        label="A3",
        login=1033669,
        terminal_exe=Path(r"C:\MT5PortableRepairLane\terminal64.exe"),
        files_dir=Path(r"C:\MT5PortableRepairLane\MQL5\Files"),
        signal_globs=("a3_*_signal_log.csv",),
        order_globs=("a3_*_order_log.csv",),
    ),
]


def _fmt_dt(value: datetime | None) -> str:
    if value is None:
        return ""
    return value.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


def _fmt_dubai(value: datetime | None) -> str:
    if value is None:
        return ""
    return value.astimezone(DUBAI_TZ).strftime("%Y-%m-%d %H:%M:%S")


def _csv_date_label(scan_date: date) -> str:
    return scan_date.strftime("%Y%m%d")


def _report_date_label(scan_date: date) -> str:
    return scan_date.strftime("%Y_%m_%d")


def _scan_window(scan_date: date, first_night: bool, end_utc: datetime | None = None) -> tuple[datetime, datetime]:
    end_utc = end_utc or datetime.now(timezone.utc)
    if first_night:
        return datetime(2026, 6, 14, 22, 0, 0, tzinfo=timezone.utc), end_utc
    dubai_start = datetime.combine(scan_date, time.min, tzinfo=DUBAI_TZ)
    dubai_end = dubai_start + timedelta(days=1)
    if dubai_end.astimezone(timezone.utc) > end_utc:
        dubai_end = end_utc.astimezone(DUBAI_TZ)
    return dubai_start.astimezone(timezone.utc), dubai_end.astimezone(timezone.utc)


def _dt_from_epoch(value: int | float | None) -> datetime | None:
    if value in (None, 0):
        return None
    return datetime.fromtimestamp(int(value), tz=timezone.utc)


def _parse_log_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    text = value.strip()
    for fmt in ("%Y.%m.%d %H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S"):
        try:
            return datetime.strptime(text[:19], fmt).replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    return None


def _session_bucket_from_dubai(value: datetime | None) -> str:
    if value is None:
        return "Unknown"
    hour = value.astimezone(DUBAI_TZ).hour
    if 6 <= hour <= 11:
        return "Morning 06:00-11:59"
    if 12 <= hour <= 15:
        return "Afternoon 12:00-15:59"
    if 16 <= hour <= 19:
        return "Evening 16:00-19:59"
    return "Night 20:00-05:59"


def _deal_total_pnl(deal: Any) -> float:
    return (
        float(getattr(deal, "profit", 0.0) or 0.0)
        + float(getattr(deal, "commission", 0.0) or 0.0)
        + float(getattr(deal, "swap", 0.0) or 0.0)
        + float(getattr(deal, "fee", 0.0) or 0.0)
    )


def _int_attr(obj: Any, name: str, default: int = 0) -> int:
    value = getattr(obj, name, default)
    if value is None:
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", errors="replace", newline="") as handle:
        return list(csv.DictReader(handle))


def _iter_files(base: Path, patterns: tuple[str, ...]) -> list[Path]:
    files: list[Path] = []
    for pattern in patterns:
        files.extend(sorted(base.glob(pattern)))
    return sorted(set(files), key=lambda p: p.name.lower())


def _is_xau_symbol(symbol: str | None) -> bool:
    return (symbol or "").upper().startswith("XAU")


def _candidate_from_magic_comment(magic: int, comment: str) -> str:
    comment_l = (comment or "").lower()
    if 920100 <= magic <= 920199:
        return "breakout_retest"
    if 920200 <= magic <= 920299:
        return "swing_breakout_retest_v0"
    if 920300 <= magic <= 920399:
        return "symbol_normalized_round_retest_v0"
    if 920400 <= magic <= 920499:
        return "round_number_retest_v0"
    if 920500 <= magic <= 920599:
        return "session_extreme_retest_v0"
    if 921100 <= magic <= 921199:
        return "symbol_normalized_round_retest_v0_repair_v1"
    if 921200 <= magic <= 921299:
        return "session_extreme_retest_v0_repair_v1"
    if magic in {930101, 931000}:
        return "p2weakness_br_v1"
    if magic == 930000:
        return "WR50_BreakoutEvening_v0"
    if magic == 930100:
        return "WR50_BreakoutQuality_v0"
    if magic == 930200:
        return "WR50_BreakoutExit1R_v0"
    if 933000 <= magic <= 933099:
        return "a3_round_retest_guarded_v1"
    if 933100 <= magic <= 933199:
        return "a3_round_retest_structured_v1"
    if "sn_round" in comment_l or "snr" in comment_l:
        return "symbol_normalized_round_retest_v0"
    if "swing_br" in comment_l:
        return "swing_breakout_retest_v0"
    if "sess_ext" in comment_l:
        return "session_extreme_retest_v0"
    if "rdguard" in comment_l:
        return "a3_round_retest_guarded_v1"
    if "rdstruct" in comment_l:
        return "a3_round_retest_structured_v1"
    if "round" in comment_l:
        return "round_number_retest_v0"
    if "br" in comment_l:
        return "breakout_retest"
    return comment or "UNKNOWN"


def _exit_reason(deal: Any) -> str:
    comment = str(getattr(deal, "comment", "") or "").lower()
    if "[tp" in comment or "take profit" in comment:
        return "TP"
    if "[sl" in comment or "stop loss" in comment:
        return "SL"
    reason = _int_attr(deal, "reason", -1)
    if reason == getattr(mt5, "DEAL_REASON_TP", object()):
        return "TP"
    if reason == getattr(mt5, "DEAL_REASON_SL", object()):
        return "SL"
    return "other"


def _entry_direction(entry_deal: Any | None, exit_deal: Any) -> str:
    deal_type = _int_attr(entry_deal, "type", -1) if entry_deal is not None else -1
    if deal_type == getattr(mt5, "DEAL_TYPE_BUY", 0):
        return "BUY"
    if deal_type == getattr(mt5, "DEAL_TYPE_SELL", 1):
        return "SELL"
    exit_type = _int_attr(exit_deal, "type", -1)
    if exit_type == getattr(mt5, "DEAL_TYPE_SELL", 1):
        return "BUY"
    if exit_type == getattr(mt5, "DEAL_TYPE_BUY", 0):
        return "SELL"
    return ""


def _load_order_log_evidence(
    spec: AccountSpec, window_start_utc: datetime, window_end_utc: datetime
) -> tuple[dict[str, dict[str, str]], dict[str, dict[str, str]], dict[str, Any]]:
    by_deal: dict[str, dict[str, str]] = {}
    by_order: dict[str, dict[str, str]] = {}
    files = _iter_files(spec.files_dir, spec.order_globs)
    rows_in_window: list[dict[str, str]] = []
    guard_reasons: Counter[str] = Counter()
    tails: list[dict[str, str]] = []
    for path in files:
        rows = _read_csv_rows(path)
        if rows:
            for row in rows[-3:]:
                tails.append({"file": path.name, **row})
        for row in rows:
            if not _is_xau_symbol(row.get("symbol")):
                continue
            timestamp = _parse_log_dt(row.get("timestamp_utc"))
            if timestamp is not None and window_start_utc <= timestamp <= window_end_utc:
                rows_in_window.append(row)
                if row.get("action") == "GUARD_BLOCK":
                    reason = row.get("guard_reason") or row.get("reason_code") or "UNKNOWN"
                    guard_reasons[reason] += 1
            deal_ticket = (row.get("deal_ticket") or "").strip()
            order_ticket = (row.get("order_ticket") or "").strip()
            if deal_ticket and deal_ticket != "0":
                by_deal[deal_ticket] = row
            if order_ticket and order_ticket != "0":
                by_order[order_ticket] = row
    orders_sent = sum(1 for row in rows_in_window if row.get("action") == "ORDER_SEND_OK")
    orders_filled = sum(
        1
        for row in rows_in_window
        if row.get("action") == "ORDER_SEND_OK"
        and (row.get("deal_ticket") or "0").strip() not in {"", "0"}
        and (row.get("retcode") or "").strip() in {"10009", "10008", "10010"}
    )
    stats = {
        "order_files": files,
        "order_rows": len(rows_in_window),
        "orders_sent": orders_sent,
        "orders_filled": orders_filled,
        "guard_blocks": sum(guard_reasons.values()),
        "guard_reasons": dict(sorted(guard_reasons.items())),
        "order_tails": tails[-12:],
    }
    return by_deal, by_order, stats


def _load_signal_stats(spec: AccountSpec, window_start_utc: datetime, window_end_utc: datetime) -> dict[str, Any]:
    files = _iter_files(spec.files_dir, spec.signal_globs)
    rows_in_window: list[dict[str, str]] = []
    tails: list[dict[str, str]] = []
    for path in files:
        rows = _read_csv_rows(path)
        if rows:
            for row in rows[-2:]:
                tails.append({"file": path.name, **row})
        for row in rows:
            if not _is_xau_symbol(row.get("symbol")):
                continue
            timestamp = _parse_log_dt(row.get("timestamp_utc"))
            if timestamp is not None and window_start_utc <= timestamp <= window_end_utc:
                rows_in_window.append(row)
    would_signals = sum(1 for row in rows_in_window if (row.get("would_signal") or "").lower() == "true")
    return {
        "signal_files": files,
        "signal_rows": len(rows_in_window),
        "would_signals": would_signals,
        "signal_tails": tails[-8:],
    }


def _order_price_info(entry_order: Any | None, log_row: dict[str, str] | None) -> tuple[str, str]:
    sl = getattr(entry_order, "sl", None) if entry_order is not None else None
    tp = getattr(entry_order, "tp", None) if entry_order is not None else None
    if (not sl or float(sl) == 0.0) and log_row:
        sl = log_row.get("sl")
    if (not tp or float(tp) == 0.0) and log_row:
        tp = log_row.get("tp")
    return _fmt_num(sl), _fmt_num(tp)


def _first_nonempty(row: dict[str, str] | None, keys: tuple[str, ...]) -> str:
    if not row:
        return ""
    for key in keys:
        value = str(row.get(key, "") or "").strip()
        if value:
            return value
    return ""


def _to_float(value: Any) -> float | None:
    try:
        if value is None or str(value).strip() == "":
            return None
        return float(str(value))
    except ValueError:
        return None


def _stop_distance_points(entry_price: Any, sl: Any, point: float, log_row: dict[str, str] | None) -> str:
    from_log = _first_nonempty(log_row, ("stop_distance_points",))
    if from_log:
        return _fmt_num(from_log)
    entry = _to_float(entry_price)
    stop = _to_float(sl)
    if entry is None or stop is None or point <= 0:
        return ""
    return f"{abs(entry - stop) / point:.2f}"


def _spread_points(log_row: dict[str, str] | None) -> str:
    value = _first_nonempty(log_row, ("spread_at_order_points", "spread_points", "spread_at_signal_points"))
    return _fmt_num(value) if value else ""


def _cost_r(spread_points: str, stop_distance_points: str, log_row: dict[str, str] | None) -> str:
    from_log = _first_nonempty(log_row, ("estimated_cost_R", "cost_r", "estimated_cost_r"))
    if from_log:
        return f"{float(from_log):.4f}"
    spread = _to_float(spread_points)
    stop = _to_float(stop_distance_points)
    if spread is None or stop in (None, 0.0):
        return ""
    return f"{spread / stop:.4f}"


def _fmt_num(value: Any) -> str:
    try:
        return f"{float(value):.5f}"
    except (TypeError, ValueError):
        return ""


def _query_account(spec: AccountSpec, window_start_utc: datetime, end_utc: datetime) -> dict[str, Any]:
    mt5.shutdown()
    if not mt5.initialize(path=str(spec.terminal_exe)):
        raise RuntimeError(f"{spec.label} MT5 initialize failed: {mt5.last_error()}")
    account = mt5.account_info()
    terminal = mt5.terminal_info()
    if account is None:
        raise RuntimeError(f"{spec.label} account_info unavailable")
    if int(account.login) != spec.login:
        raise RuntimeError(f"{spec.label} expected login {spec.login}, got {account.login}")

    symbol_info = mt5.symbol_info("XAUUSD")
    point = float(getattr(symbol_info, "point", 0.01) or 0.01)
    wide_deals = list(mt5.history_deals_get(MATCHING_START_UTC, end_utc) or [])
    window_deals = list(mt5.history_deals_get(window_start_utc, end_utc) or [])
    wide_orders = list(mt5.history_orders_get(MATCHING_START_UTC, end_utc) or [])
    open_positions = list(mt5.positions_get(symbol="XAUUSD") or [])

    entries_by_position: dict[int, Any] = {}
    for deal in wide_deals:
        if not _is_xau_symbol(getattr(deal, "symbol", "")):
            continue
        if _int_attr(deal, "entry", -1) == getattr(mt5, "DEAL_ENTRY_IN", 0):
            entries_by_position.setdefault(_int_attr(deal, "position_id", 0), deal)

    orders_by_ticket = {_int_attr(order, "ticket", 0): order for order in wide_orders}
    by_deal, by_order, order_stats = _load_order_log_evidence(spec, window_start_utc, end_utc)
    signal_stats = _load_signal_stats(spec, window_start_utc, end_utc)

    closed_rows: list[dict[str, str]] = []
    join_rows: list[dict[str, str]] = []
    for deal in window_deals:
        if not _is_xau_symbol(getattr(deal, "symbol", "")):
            continue
        entry_code = _int_attr(deal, "entry", -1)
        if entry_code not in {
            getattr(mt5, "DEAL_ENTRY_OUT", 1),
            getattr(mt5, "DEAL_ENTRY_OUT_BY", 3),
            getattr(mt5, "DEAL_ENTRY_INOUT", 2),
        }:
            continue
        position_id = _int_attr(deal, "position_id", 0)
        entry_deal = entries_by_position.get(position_id)
        entry_order = orders_by_ticket.get(_int_attr(entry_deal, "order", 0)) if entry_deal is not None else None
        log_row = None
        if entry_deal is not None:
            log_row = by_deal.get(str(getattr(entry_deal, "ticket", ""))) or by_order.get(str(getattr(entry_deal, "order", "")))
        log_row = log_row or by_deal.get(str(getattr(deal, "ticket", ""))) or by_order.get(str(getattr(deal, "order", "")))

        magic = _int_attr(entry_deal, "magic", _int_attr(deal, "magic", 0)) if entry_deal is not None else _int_attr(deal, "magic", 0)
        comment = str(getattr(entry_deal, "comment", "") if entry_deal is not None else getattr(deal, "comment", ""))
        sl, tp = _order_price_info(entry_order, log_row)
        entry_time = _dt_from_epoch(getattr(entry_deal, "time", None)) if entry_deal is not None else None
        exit_time = _dt_from_epoch(getattr(deal, "time", None))
        candidate = _candidate_from_magic_comment(magic, comment)
        direction = _entry_direction(entry_deal, deal)
        entry_price = _fmt_num(getattr(entry_deal, "price", "")) if entry_deal is not None else ""
        stop_distance = _stop_distance_points(entry_price, sl, point, log_row)
        spread = _spread_points(log_row)
        cost = _cost_r(spread, stop_distance, log_row)
        profit = f"{_deal_total_pnl(deal):.2f}"
        position_ticket = str(position_id)
        entry_order_ticket = str(getattr(entry_deal, "order", "")) if entry_deal is not None else ""
        entry_deal_ticket = str(getattr(entry_deal, "ticket", "")) if entry_deal is not None else ""
        exit_order_ticket = str(getattr(deal, "order", ""))
        exit_deal_ticket = str(getattr(deal, "ticket", ""))
        session_bucket = _session_bucket_from_dubai(entry_time)
        closed_rows.append(
            {
                "account": str(spec.login),
                "entry_time_utc": _fmt_dt(entry_time),
                "entry_time_dubai": _fmt_dubai(entry_time),
                "exit_time_utc": _fmt_dt(exit_time),
                "candidate": candidate,
                "magic": str(magic),
                "direction": direction,
                "lots": _fmt_num(getattr(deal, "volume", "")),
                "entry_price": entry_price,
                "exit_price": _fmt_num(getattr(deal, "price", "")),
                "sl": sl,
                "tp": tp,
                "stop_distance_points": stop_distance,
                "spread_points": spread,
                "cost_r": cost,
                "exit_reason": _exit_reason(deal),
                "profit_aed": profit,
                "dirstate_regime": (log_row or {}).get("dirstate_regime", ""),
            }
        )
        join_rows.append(
            {
                "entry_time": _fmt_dt(entry_time),
                "exit_time": _fmt_dt(exit_time),
                "candidate": candidate,
                "status": "EXPORTED",
                "symbol": "XAUUSD",
                "direction": direction,
                "volume": _fmt_num(getattr(deal, "volume", "")),
                "entry_price": entry_price,
                "exit_price": _fmt_num(getattr(deal, "price", "")),
                "sl": sl,
                "tp": tp,
                "state": "CLOSED",
                "profit_aed": profit,
                "position_ticket": position_ticket,
                "magic": str(magic),
                "entry_order": entry_order_ticket,
                "exit_order": exit_order_ticket,
                "entry_deal": entry_deal_ticket,
                "exit_deal": exit_deal_ticket,
                "duplicate_key": f"{_fmt_dt(entry_time)[:16]}|XAUUSD|{direction}|{_fmt_num(getattr(deal, 'volume', ''))}",
                "duplicate_role": "",
                "is_duplicate": "",
                "time_bucket": session_bucket,
                "weakness_shadow_action": "",
                "weakness_shadow_reason": "",
                "entry_comment": comment,
                "exit_comment": str(getattr(deal, "comment", "") or ""),
            }
        )

    open_rows: list[dict[str, str]] = []
    for position in open_positions:
        if not _is_xau_symbol(getattr(position, "symbol", "")):
            continue
        magic = _int_attr(position, "magic", 0)
        comment = str(getattr(position, "comment", "") or "")
        direction = "BUY" if _int_attr(position, "type", -1) == getattr(mt5, "POSITION_TYPE_BUY", 0) else "SELL"
        open_rows.append(
            {
                "ticket": str(getattr(position, "ticket", "")),
                "magic": str(magic),
                "candidate": _candidate_from_magic_comment(magic, comment),
                "direction": direction,
                "lots": _fmt_num(getattr(position, "volume", "")),
                "entry": _fmt_num(getattr(position, "price_open", "")),
                "current_floating_pnl_aed": f"{float(getattr(position, 'profit', 0.0) or 0.0):.2f}",
                "comment": comment,
            }
        )

    result = {
        "spec": spec,
        "account_login": int(account.login),
        "server": account.server,
        "currency": account.currency,
        "trade_allowed": bool(account.trade_allowed),
        "terminal_trade_allowed": bool(terminal.trade_allowed) if terminal else None,
        "window_deals": len(window_deals),
        "wide_deals": len(wide_deals),
        "wide_orders": len(wide_orders),
        "closed_rows": closed_rows,
        "join_rows": join_rows,
        "open_rows": open_rows,
        **signal_stats,
        **order_stats,
    }
    mt5.shutdown()
    return result


def _write_account_csv(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=EXPORT_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def _write_join_csv(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=JOIN_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def _query_gold_context(terminal_exe: Path, window_start_utc: datetime, end_utc: datetime, scan_date: date) -> dict[str, str]:
    mt5.shutdown()
    if not mt5.initialize(path=str(terminal_exe)):
        raise RuntimeError(f"MT5 initialize failed for gold context: {mt5.last_error()}")
    symbol_info = mt5.symbol_info("XAUUSD")
    point = float(getattr(symbol_info, "point", 0.01) or 0.01)
    rates_raw = mt5.copy_rates_range("XAUUSD", mt5.TIMEFRAME_M5, window_start_utc, end_utc)
    rates = list(rates_raw) if rates_raw is not None else []
    mt5.shutdown()
    if not rates:
        return {
            "date": scan_date.isoformat(),
            "gold_open": "",
            "gold_high": "",
            "gold_low": "",
            "gold_close": "",
            "net_move_pts": "",
            "day_type": "unknown",
            "bar_rows": "0",
            "first_bar_utc": "",
            "last_bar_utc": "",
        }
    gold_open = float(rates[0]["open"])
    gold_close = float(rates[-1]["close"])
    gold_high = max(float(row["high"]) for row in rates)
    gold_low = min(float(row["low"]) for row in rates)
    net_move_pts = (gold_close - gold_open) / point if point > 0 else 0.0
    if abs(net_move_pts) <= 100:
        day_type = "range"
    else:
        day_type = "up" if net_move_pts > 0 else "down"
    return {
        "date": scan_date.isoformat(),
        "gold_open": _fmt_num(gold_open),
        "gold_high": _fmt_num(gold_high),
        "gold_low": _fmt_num(gold_low),
        "gold_close": _fmt_num(gold_close),
        "net_move_pts": f"{net_move_pts:.2f}",
        "day_type": day_type,
        "bar_rows": str(len(rates)),
        "first_bar_utc": _fmt_dt(_dt_from_epoch(int(rates[0]["time"]))),
        "last_bar_utc": _fmt_dt(_dt_from_epoch(int(rates[-1]["time"]))),
    }


def _write_context_csv(path: Path, row: dict[str, str]) -> None:
    fields = [
        "date",
        "gold_open",
        "gold_high",
        "gold_low",
        "gold_close",
        "net_move_pts",
        "day_type",
        "bar_rows",
        "first_bar_utc",
        "last_bar_utc",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerow(row)


def _run_direction_state_scoreboard(scan_date: date, join_path: Path) -> list[str]:
    import importlib.util

    script_path = Path(__file__).resolve().with_name("generate_direction_state_shadow_scoreboard.py")
    spec = importlib.util.spec_from_file_location("generate_direction_state_shadow_scoreboard", script_path)
    if spec is None or spec.loader is None:
        return ["DirectionState scoreboard refresh skipped: script could not be loaded."]
    module = importlib.util.module_from_spec(spec)
    sys.modules["generate_direction_state_shadow_scoreboard"] = module
    spec.loader.exec_module(module)
    output_json = REPORTS_DIR / f"DIRECTION_STATE_SHADOW_SCOREBOARD_{_report_date_label(scan_date)}.json"
    payload = module.generate_direction_state_shadow_scoreboard(
        Path(__file__).resolve().parents[1],
        trade_history_csv=join_path,
        output_json=output_json,
    )
    return [
        f"DirectionState scoreboard refreshed: `{output_json.as_posix()}`",
        f"DirectionState scoreboard status: `{payload.get('status', 'UNKNOWN')}`; rows: `{len(payload.get('scoreboard', []))}`",
    ]


def _run_observer_outcome_resolution(scan_date: date, join_path: Path) -> list[str]:
    import importlib.util

    script_path = Path(__file__).resolve().with_name("generate_observer_outcome_resolution.py")
    spec = importlib.util.spec_from_file_location("generate_observer_outcome_resolution", script_path)
    if spec is None or spec.loader is None:
        return ["Observer outcome resolution skipped: script could not be loaded."]
    module = importlib.util.module_from_spec(spec)
    sys.modules["generate_observer_outcome_resolution"] = module
    spec.loader.exec_module(module)
    output_json = REPORTS_DIR / f"OBSERVER_OUTCOME_RESOLUTION_REPORT_{_report_date_label(scan_date)}.json"
    scoreboard_json = REPORTS_DIR / f"OBSERVER_SHADOW_POLICY_SCOREBOARD_{_report_date_label(scan_date)}.json"
    output_path = module.generate_observer_outcome_resolution(
        Path(__file__).resolve().parents[1],
        actual_trades_csv=join_path,
        output_json=output_json,
        scoreboard_json=scoreboard_json,
        scoreboard_mode="broker_joined_only",
    )
    try:
        import json

        payload = json.loads(output_json.read_text(encoding="utf-8"))
        return [
            f"Observer outcome resolution refreshed as dated broker-joined-only output: `{output_path.as_posix()}`",
            f"Resolution status: `{payload.get('status', 'UNKNOWN')}`; signals: `{payload.get('signal_count', 0)}`; broker-joined: `{payload.get('broker_join_resolved_count', 0)}`; unresolved: `{payload.get('unresolved_count', 0)}`",
            "Replay bars were not supplied for this nightly scan; unresolved rows remain unresolved rather than replay-filled.",
        ]
    except Exception as exc:  # pragma: no cover - defensive reporting for operator runs.
        return [
            f"Observer outcome resolution refreshed as dated broker-joined-only output: `{output_path.as_posix()}`",
            f"Resolution summary could not be parsed: `{exc}`",
        ]


def _md_table(headers: list[str], rows: list[list[Any]]) -> list[str]:
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(str(cell) for cell in row) + " |")
    return lines


def _win_rate(rows: list[dict[str, str]]) -> str:
    if not rows:
        return "n/a"
    wins = sum(1 for row in rows if _to_float(row.get("profit_aed")) is not None and (_to_float(row.get("profit_aed")) or 0.0) > 0)
    return f"{(wins / len(rows)) * 100:.2f}%"


def _pnl(rows: list[dict[str, str]]) -> float:
    return sum(_to_float(row.get("profit_aed")) or 0.0 for row in rows)


def _best_worst_session(rows: list[dict[str, str]]) -> tuple[str, str]:
    if not rows:
        return "n/a", "n/a"
    buckets: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        entry = _parse_log_dt(row.get("entry_time_utc"))
        buckets[_session_bucket_from_dubai(entry)].append(row)
    scored = [(bucket, _pnl(items), len(items)) for bucket, items in buckets.items()]
    best = max(scored, key=lambda item: item[1])
    worst = min(scored, key=lambda item: item[1])
    return f"{best[0]} ({best[1]:.2f} AED, {best[2]} trades)", f"{worst[0]} ({worst[1]:.2f} AED, {worst[2]} trades)"


def _long_short_pnl(rows: list[dict[str, str]]) -> tuple[str, str]:
    long_rows = [row for row in rows if row.get("direction") == "BUY"]
    short_rows = [row for row in rows if row.get("direction") == "SELL"]
    return f"{_pnl(long_rows):.2f}", f"{_pnl(short_rows):.2f}"


def _write_report(
    results: list[dict[str, Any]],
    end_utc: datetime,
    csv_paths: dict[str, Path],
    join_path: Path,
    context_path: Path,
    context_row: dict[str, str],
    scan_date: date,
    window_start_utc: datetime,
    observer_notes: list[str],
) -> Path:
    report_path = REPORTS_DIR / f"EOD_GOLD_SCAN_REPORT_{_report_date_label(scan_date)}.md"
    total_closed = sum(len(result["closed_rows"]) for result in results)
    lines: list[str] = [
        f"# EOD GOLD Scan Report - {scan_date.isoformat()}",
        "",
        f"Generated UTC: {_fmt_dt(end_utc)}",
        f"Generated Dubai: {_fmt_dubai(end_utc)}",
        f"Window UTC: {_fmt_dt(window_start_utc)} through {_fmt_dt(end_utc)}",
        f"Entry lookup window UTC: {_fmt_dt(MATCHING_START_UTC)} through {_fmt_dt(end_utc)}",
        "",
        "Boundary: read-only export. No EA, preset, chart, terminal, or broker setting was changed.",
        "",
        "## Gold Day Context",
        "",
    ]
    lines.extend(
        _md_table(
            ["Date", "Open", "High", "Low", "Close", "Net move pts", "Day type", "M5 rows", "First bar UTC", "Last bar UTC"],
            [
                [
                    context_row["date"],
                    context_row["gold_open"],
                    context_row["gold_high"],
                    context_row["gold_low"],
                    context_row["gold_close"],
                    context_row["net_move_pts"],
                    context_row["day_type"],
                    context_row["bar_rows"],
                    context_row["first_bar_utc"],
                    context_row["last_bar_utc"],
                ]
            ],
        )
    )
    lines += [
        "",
        f"Context CSV: `{context_path.as_posix()}`",
        "",
        "## Summary",
        "",
    ]
    summary_rows = []
    for result in results:
        pnl = sum(float(row["profit_aed"] or 0.0) for row in result["closed_rows"])
        csv_path = csv_paths[result["spec"].label]
        best_session, worst_session = _best_worst_session(result["closed_rows"])
        long_pnl, short_pnl = _long_short_pnl(result["closed_rows"])
        summary_rows.append(
            [
                result["spec"].label,
                result["account_login"],
                csv_path.as_posix(),
                len(result["closed_rows"]),
                f"{pnl:.2f}",
                _win_rate(result["closed_rows"]),
                best_session,
                worst_session,
                long_pnl,
                short_pnl,
                len(result["open_rows"]),
                result["would_signals"],
                result["orders_sent"],
                result["orders_filled"],
                result["guard_blocks"],
            ]
        )
    lines.extend(
        _md_table(
            [
                "Lane",
                "Account",
                "CSV",
                "Closed XAUUSD rows",
                "Closed PnL AED",
                "Win rate",
                "Best session",
                "Worst session",
                "Long PnL AED",
                "Short PnL AED",
                "Open XAUUSD",
                "Would-signals",
                "Orders sent",
                "Orders filled",
                "Guard-blocks",
            ],
            summary_rows,
        )
    )
    lines += ["", f"Total closed XAUUSD rows: {total_closed}", f"Observer/broker join input CSV: `{join_path.as_posix()}`", ""]

    lines += ["## Observer Evidence Refresh", ""]
    if observer_notes:
        lines.extend(f"- {note}" for note in observer_notes)
    else:
        lines.append("- No observer refresh step was run.")
    lines.append("")

    lines += ["## Open XAUUSD Positions", ""]
    open_rows = []
    for result in results:
        for row in result["open_rows"]:
            open_rows.append(
                [
                    result["spec"].label,
                    result["account_login"],
                    row["ticket"],
                    row["candidate"],
                    row["magic"],
                    row["direction"],
                    row["lots"],
                    row["entry"],
                    row["current_floating_pnl_aed"],
                ]
            )
    if open_rows:
        lines.extend(
            _md_table(
                ["Lane", "Account", "Ticket", "Candidate", "Magic", "Direction", "Lots", "Entry", "Floating PnL AED"],
                open_rows,
            )
        )
    else:
        lines.append("No open XAUUSD positions found.")
    lines.append("")

    lines += ["## Guard Blocks By Reason", ""]
    for result in results:
        lines += [f"### {result['spec'].label} - {result['account_login']}", ""]
        guard_rows = [[reason, count] for reason, count in result["guard_reasons"].items()]
        if guard_rows:
            lines.extend(_md_table(["Reason", "Count"], guard_rows))
        else:
            lines.append("No guard-block rows in the requested window.")
        lines.append("")

    lines += ["## Raw Broker Query Evidence", ""]
    query_rows = []
    for result in results:
        query_rows.append(
            [
                result["spec"].label,
                result["account_login"],
                result["server"],
                result["currency"],
                result["trade_allowed"],
                result["terminal_trade_allowed"],
                result["window_deals"],
                result["wide_deals"],
                result["wide_orders"],
                result["spec"].terminal_exe,
            ]
        )
    lines.extend(
        _md_table(
            [
                "Lane",
                "Account",
                "Server",
                "Currency",
                "Account trade allowed",
                "Terminal trade allowed",
                "Window deals queried",
                "Wide deals queried",
                "Wide orders queried",
                "Terminal",
            ],
            query_rows,
        )
    )
    lines.append("")

    lines += ["## Signal And Order Log Sources", ""]
    source_rows = []
    for result in results:
        source_rows.append(
            [
                result["spec"].label,
                len(result["signal_files"]),
                len(result["order_files"]),
                result["signal_rows"],
                result["order_rows"],
                result["spec"].files_dir,
            ]
        )
    lines.extend(
        _md_table(
            ["Lane", "Signal files", "Order files", "Signal rows in window", "Order rows in window", "Files dir"],
            source_rows,
        )
    )
    lines.append("")

    lines += ["## Latest Order Log Tails", ""]
    for result in results:
        lines += [f"### {result['spec'].label} - {result['account_login']}", ""]
        tail_rows = []
        for row in result["order_tails"][-8:]:
            tail_rows.append(
                [
                    row.get("file", ""),
                    row.get("timestamp_utc", ""),
                    row.get("candidate", row.get("comment", "")),
                    row.get("action", ""),
                    row.get("direction", ""),
                    row.get("volume", ""),
                    row.get("order_ticket", ""),
                    row.get("deal_ticket", ""),
                    row.get("guard_reason", row.get("reason_code", "")),
                ]
            )
        if tail_rows:
            lines.extend(
                _md_table(
                    ["File", "UTC", "Candidate/comment", "Action", "Direction", "Volume", "Order", "Deal", "Reason"],
                    tail_rows,
                )
            )
        else:
            lines.append("No order-log tail rows available.")
        lines.append("")

    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return report_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Read-only nightly XAUUSD EOD export across A1/A2/A3 demo accounts.")
    parser.add_argument("--date", default=DEFAULT_SCAN_DATE, help="Dubai trading day to scan, YYYY-MM-DD.")
    parser.add_argument(
        "--first-night",
        action="store_true",
        help="Use Sunday market-open UTC through now instead of Dubai 00:00-24:00.",
    )
    parser.add_argument(
        "--regular-day",
        action="store_true",
        help="Use Dubai 00:00-24:00 window for the supplied date.",
    )
    parser.add_argument("--skip-observers", action="store_true", help="Skip read-only observer evidence refresh.")
    args = parser.parse_args()

    scan_date = datetime.strptime(args.date, "%Y-%m-%d").date()
    first_night = (args.first_night or scan_date == date(2026, 6, 15)) and not args.regular_day
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    end_utc = datetime.now(timezone.utc)
    window_start_utc, window_end_utc = _scan_window(scan_date, first_night, end_utc)
    results = [_query_account(spec, window_start_utc, window_end_utc) for spec in ACCOUNT_SPECS]
    csv_paths: dict[str, Path] = {}
    for result in results:
        path = REPORTS_DIR / f"EOD_GOLD_{result['spec'].label}_{_csv_date_label(scan_date)}.csv"
        _write_account_csv(path, result["closed_rows"])
        csv_paths[result["spec"].label] = path
    join_rows = [row for result in results for row in result["join_rows"]]
    join_path = REPORTS_DIR / f"EOD_GOLD_OBSERVER_JOIN_INPUT_{_csv_date_label(scan_date)}.csv"
    _write_join_csv(join_path, join_rows)
    context_path = REPORTS_DIR / f"EOD_GOLD_CONTEXT_{_csv_date_label(scan_date)}.csv"
    context_row = _query_gold_context(ACCOUNT_SPECS[0].terminal_exe, window_start_utc, window_end_utc, scan_date)
    _write_context_csv(context_path, context_row)
    observer_notes: list[str] = []
    if args.skip_observers:
        observer_notes.append("Observer refresh skipped by operator flag.")
    else:
        for runner in (_run_direction_state_scoreboard, _run_observer_outcome_resolution):
            try:
                observer_notes.extend(runner(scan_date, join_path))
            except Exception as exc:
                observer_notes.append(f"{runner.__name__} failed without changing runtime: `{exc}`")
    report_path = _write_report(
        results,
        window_end_utc,
        csv_paths,
        join_path,
        context_path,
        context_row,
        scan_date,
        window_start_utc,
        observer_notes,
    )
    print(f"Report: {report_path}")
    for result in results:
        pnl = sum(float(row["profit_aed"] or 0.0) for row in result["closed_rows"])
        print(
            f"{result['spec'].label} {result['account_login']} rows={len(result['closed_rows'])} "
            f"pnl_aed={pnl:.2f} open={len(result['open_rows'])} "
            f"would_signals={result['would_signals']} orders_sent={result['orders_sent']} "
            f"guard_blocks={result['guard_blocks']}"
        )


if __name__ == "__main__":
    main()
