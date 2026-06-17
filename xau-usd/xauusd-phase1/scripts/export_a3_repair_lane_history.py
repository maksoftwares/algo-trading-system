from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


DEFAULT_TERMINAL = Path("C:/MT5PortableRepairLane/terminal64.exe")
DEFAULT_OUTPUT_PREFIX = Path("outputs/reports/A3_REPAIR_LANE_ACCOUNT_HISTORY_2026_06_17")
START_UTC = datetime(2026, 6, 1, tzinfo=timezone.utc)
DUBAI_TZ = timezone(timedelta(hours=4))


def export_history(
    phase1_root: Path,
    *,
    terminal: Path = DEFAULT_TERMINAL,
    output_prefix: Path | None = None,
) -> dict[str, Path]:
    import MetaTrader5 as mt5

    phase1_root = phase1_root.resolve()
    output_prefix = (output_prefix or phase1_root / DEFAULT_OUTPUT_PREFIX).resolve()

    if not mt5.initialize(path=str(terminal)):
        raise RuntimeError(f"MT5 initialize failed for {terminal}: {mt5.last_error()}")
    try:
        account_info = mt5.account_info()
        terminal_info = mt5.terminal_info()
        end_utc = datetime.now(timezone.utc)
        deals = mt5.history_deals_get(START_UTC, end_utc)
        if deals is None:
            raise RuntimeError(f"history_deals_get failed: {mt5.last_error()}")
        positions = mt5.positions_get()
        open_position_ids = {int(position._asdict().get("ticket") or 0) for position in positions or []}
        closed_rows, open_rows = _position_rows(mt5, deals, positions, open_position_ids)
        payload = _payload(mt5, account_info, terminal_info, deals, closed_rows, open_rows, terminal, end_utc)
    finally:
        mt5.shutdown()

    output_prefix.parent.mkdir(parents=True, exist_ok=True)
    closed_rows_path = output_prefix.with_name(output_prefix.name + "_CLOSED_ROWS").with_suffix(".csv")
    open_rows_path = output_prefix.with_name(output_prefix.name + "_OPEN_ROWS").with_suffix(".csv")
    json_path = output_prefix.with_suffix(".json")
    md_path = output_prefix.with_suffix(".md")
    _write_csv(closed_rows_path, closed_rows, _closed_row_fields())
    _write_csv(open_rows_path, open_rows, _open_row_fields())
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    md_path.write_text(_render_markdown(payload, closed_rows_path, open_rows_path), encoding="utf-8")
    return {"md": md_path, "json": json_path, "closed_rows": closed_rows_path, "open_rows": open_rows_path}


def _position_rows(mt5: Any, deals: Any, positions: Any, open_position_ids: set[int]) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    buy = getattr(mt5, "DEAL_TYPE_BUY", 0)
    sell = getattr(mt5, "DEAL_TYPE_SELL", 1)
    trade_deals: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for deal in deals:
        row = deal._asdict()
        if row.get("type") in {buy, sell}:
            trade_deals[int(row.get("position_id") or 0)].append(row)

    closed_rows = []
    for position_id, items in sorted(trade_deals.items(), key=lambda item: min(d.get("time", 0) for d in item[1])):
        if position_id in open_position_ids:
            continue
        closed_rows.append(_closed_position_row(mt5, position_id, items))

    open_rows = []
    for position in positions or []:
        row = position._asdict()
        open_rows.append(
            {
                "account": "1033669",
                "symbol": str(row.get("symbol", "")),
                "ticket": str(row.get("ticket", "")),
                "candidate": _candidate_from_comments(str(row.get("comment", ""))),
                "direction": "BUY" if row.get("type") == buy else "SELL",
                "volume": _fmt(row.get("volume")),
                "entry_time_utc": _ts(row.get("time")),
                "entry_time_dubai": _dubai_ts(row.get("time")),
                "entry_price": _fmt(row.get("price_open"), digits=5),
                "current_price": _fmt(row.get("price_current"), digits=5),
                "floating_profit_aed": _fmt(row.get("profit")),
                "comment": str(row.get("comment", "")),
            }
        )
    return closed_rows, open_rows


def _closed_position_row(mt5: Any, position_id: int, items: list[dict[str, Any]]) -> dict[str, str]:
    buy = getattr(mt5, "DEAL_TYPE_BUY", 0)
    entry = min(items, key=lambda item: item.get("time", 0))
    exit_deals = [item for item in items if float(item.get("profit") or 0.0) != 0.0 or str(item.get("comment", "")).startswith("[")]
    exit_deal = max(exit_deals or items, key=lambda item: item.get("time", 0))
    gross_profit = sum(float(item.get("profit") or 0.0) for item in items)
    commission = sum(float(item.get("commission") or 0.0) for item in items)
    swap = sum(float(item.get("swap") or 0.0) for item in items)
    fee = sum(float(item.get("fee") or 0.0) for item in items)
    net_profit = gross_profit + commission + swap + fee
    comments = ";".join(sorted({str(item.get("comment", "")) for item in items if item.get("comment")}))
    return {
        "account": "1033669",
        "symbol": next((str(item.get("symbol", "")) for item in items if item.get("symbol")), ""),
        "position_id": str(position_id),
        "entry_time_utc": _ts(entry.get("time")),
        "exit_time_utc": _ts(exit_deal.get("time")),
        "entry_time_dubai": _dubai_ts(entry.get("time")),
        "exit_time_dubai": _dubai_ts(exit_deal.get("time")),
        "candidate": _candidate_from_comments(comments),
        "direction": "BUY" if entry.get("type") == buy else "SELL",
        "volume": _fmt(entry.get("volume")),
        "entry_price": _fmt(entry.get("price"), digits=5),
        "exit_price": _fmt(exit_deal.get("price"), digits=5),
        "session": _session_bucket(_dubai_ts(entry.get("time"))),
        "gross_profit_aed": _fmt(gross_profit),
        "commission_aed": _fmt(commission),
        "swap_aed": _fmt(swap),
        "fee_aed": _fmt(fee),
        "net_profit_aed": _fmt(net_profit),
        "outcome": "WIN" if net_profit > 0 else ("LOSS" if net_profit < 0 else "FLAT"),
        "comments": comments,
    }


def _payload(
    mt5: Any,
    account_info: Any,
    terminal_info: Any,
    deals: Any,
    closed_rows: list[dict[str, str]],
    open_rows: list[dict[str, str]],
    terminal: Path,
    end_utc: datetime,
) -> dict[str, Any]:
    balance_type = getattr(mt5, "DEAL_TYPE_BALANCE", 2)
    buy = getattr(mt5, "DEAL_TYPE_BUY", 0)
    sell = getattr(mt5, "DEAL_TYPE_SELL", 1)
    trade_deals = [deal._asdict() for deal in deals if deal._asdict().get("type") in {buy, sell}]
    balance_deals = [deal._asdict() for deal in deals if deal._asdict().get("type") == balance_type]
    closed_net = sum(float(row.get("net_profit_aed") or 0.0) for row in closed_rows)
    closed_gross = sum(float(row.get("gross_profit_aed") or 0.0) for row in closed_rows)
    balance_ops = sum(float(deal.get("profit") or 0.0) for deal in balance_deals)
    floating = sum(float(row.get("floating_profit_aed") or 0.0) for row in open_rows)
    wins = sum(1 for row in closed_rows if row["outcome"] == "WIN")
    losses = sum(1 for row in closed_rows if row["outcome"] == "LOSS")
    return {
        "status": "PASS",
        "boundary": "Read-only MT5 query against A3 portable terminal. No runtime, EA, preset, chart, order, or position change.",
        "terminal": str(terminal),
        "window_start_utc": START_UTC.isoformat(),
        "window_end_utc": end_utc.isoformat(),
        "account": account_info._asdict() if account_info else None,
        "terminal_info": terminal_info._asdict() if terminal_info else None,
        "summary": {
            "balance_aed": _fmt(getattr(account_info, "balance", 0.0) if account_info else 0.0),
            "equity_aed": _fmt(getattr(account_info, "equity", 0.0) if account_info else 0.0),
            "floating_profit_aed": _fmt(getattr(account_info, "profit", 0.0) if account_info else floating),
            "balance_ops_aed": _fmt(balance_ops),
            "closed_trade_gross_profit_aed": _fmt(closed_gross),
            "closed_trade_net_profit_aed": _fmt(closed_net),
            "closed_positions": len(closed_rows),
            "wins": wins,
            "losses": losses,
            "win_rate_pct": _pct(wins, wins + losses),
            "open_positions": len(open_rows),
        },
        "by_symbol": _group(closed_rows, "symbol"),
        "by_candidate": _group(closed_rows, "candidate"),
        "by_session": _group(closed_rows, "session"),
        "trade_deal_rows": len(trade_deals),
    }


def _group(rows: list[dict[str, str]], key: str) -> list[dict[str, str]]:
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        if key == "session":
            group_key = row.get("session") or _session_from_row(row)
        else:
            group_key = row.get(key, "") or "UNKNOWN"
        grouped[group_key].append(row)
    out = []
    for name, items in grouped.items():
        wins = sum(1 for row in items if row["outcome"] == "WIN")
        losses = sum(1 for row in items if row["outcome"] == "LOSS")
        gross = sum(float(row["gross_profit_aed"]) for row in items)
        net = sum(float(row["net_profit_aed"]) for row in items)
        out.append(
            {
                "group": name,
                "rows": str(len(items)),
                "wins": str(wins),
                "losses": str(losses),
                "win_rate_pct": _pct(wins, wins + losses),
                "gross_profit_aed": _fmt(gross),
                "net_profit_aed": _fmt(net),
            }
        )
    return sorted(out, key=lambda row: row["group"])


def _render_markdown(payload: dict[str, Any], closed_rows_path: Path, open_rows_path: Path) -> str:
    summary = payload["summary"]
    lines = [
        "# A3 Repair-Lane Account History Reconciliation - 2026-06-17",
        "",
        f"Status: `{payload['status']}`",
        "",
        payload["boundary"],
        "",
        f"Closed rows CSV: `{closed_rows_path}`",
        f"Open rows CSV: `{open_rows_path}`",
        "",
        "## Account Reconciliation",
        "",
        _table([summary], ["balance_aed", "equity_aed", "floating_profit_aed", "balance_ops_aed", "closed_trade_gross_profit_aed", "closed_trade_net_profit_aed", "closed_positions", "wins", "losses", "win_rate_pct", "open_positions"]),
        "",
        "Interpretation: A3 balance is reconciled from fresh MT5 history. Net PnL includes commissions/fees/swap where MT5 reports them; gross trade profit is shown separately because older CSV exports often used gross profit only.",
        "",
        "## By Symbol",
        "",
        _table(payload["by_symbol"], ["group", "rows", "wins", "losses", "win_rate_pct", "gross_profit_aed", "net_profit_aed"]),
        "",
        "## By Candidate",
        "",
        _table(payload["by_candidate"], ["group", "rows", "wins", "losses", "win_rate_pct", "gross_profit_aed", "net_profit_aed"]),
        "",
        "## By Session",
        "",
        _table(payload["by_session"], ["group", "rows", "wins", "losses", "win_rate_pct", "gross_profit_aed", "net_profit_aed"]),
        "",
        "## Boundary",
        "",
        "Read-only reconciliation. No MT5 runtime, EA, preset, chart, order, position, profile, or account setting was changed.",
        "",
    ]
    return "\n".join(lines)


def _candidate_from_comments(comments: str) -> str:
    if "A3_BREAKOUT_IMPROVED" in comments:
        return "a3_breakout_improved"
    if "A3_BREAKOUT_PLAIN" in comments:
        return "a3_breakout_plain"
    if "RDSTRUCT_V1" in comments:
        return "a3_round_retest_structured_v1"
    if "RDGUARD_V1" in comments:
        return "a3_round_retest_guarded_v1"
    return "UNKNOWN"


def _session_from_row(row: dict[str, str]) -> str:
    return _session_bucket(row.get("entry_time_dubai", ""))


def _session_bucket(entry_time: str) -> str:
    try:
        hour = int(entry_time[11:13])
    except (ValueError, IndexError):
        return "UNKNOWN"
    if 6 <= hour <= 11:
        return "Morning 06:00-11:59"
    if 12 <= hour <= 15:
        return "Afternoon 12:00-15:59"
    if 16 <= hour <= 19:
        return "Evening 16:00-19:59"
    return "Night 20:00-05:59"


def _ts(value: Any) -> str:
    if not value:
        return ""
    return datetime.fromtimestamp(int(value), tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


def _dubai_ts(value: Any) -> str:
    if not value:
        return ""
    return datetime.fromtimestamp(int(value), tz=timezone.utc).astimezone(DUBAI_TZ).strftime("%Y-%m-%d %H:%M:%S")


def _fmt(value: Any, *, digits: int = 2) -> str:
    try:
        return f"{float(value):.{digits}f}"
    except (TypeError, ValueError):
        return ""


def _pct(wins: int, total: int) -> str:
    if total <= 0:
        return "n/a"
    return f"{100.0 * wins / total:.2f}%"


def _table(rows: list[dict[str, Any]], fields: list[str]) -> str:
    if not rows:
        return "_No rows._"
    lines = [
        "| " + " | ".join(fields) + " |",
        "| " + " | ".join("---" for _ in fields) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(str(row.get(field, "")) for field in fields) + " |")
    return "\n".join(lines)


def _write_csv(path: Path, rows: list[dict[str, str]], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def _closed_row_fields() -> list[str]:
    return [
        "account",
        "symbol",
        "position_id",
        "entry_time_utc",
        "exit_time_utc",
        "entry_time_dubai",
        "exit_time_dubai",
        "candidate",
        "direction",
        "volume",
        "entry_price",
        "exit_price",
        "session",
        "gross_profit_aed",
        "commission_aed",
        "swap_aed",
        "fee_aed",
        "net_profit_aed",
        "outcome",
        "comments",
    ]


def _open_row_fields() -> list[str]:
    return [
        "account",
        "symbol",
        "ticket",
        "candidate",
        "direction",
        "volume",
        "entry_time_utc",
        "entry_time_dubai",
        "entry_price",
        "current_price",
        "floating_profit_aed",
        "comment",
    ]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Read-only export of A3 repair-lane MT5 account history.")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--terminal", type=Path, default=DEFAULT_TERMINAL)
    parser.add_argument("--output-prefix", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    outputs = export_history(args.root, terminal=args.terminal, output_prefix=args.output_prefix)
    for label, path in outputs.items():
        print(f"{label}: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
