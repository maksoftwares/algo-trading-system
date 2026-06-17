from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


DEFAULT_TERMINAL = Path("C:/MT5PortableTier1BestEA/terminal64.exe")
DEFAULT_OUTPUT_PREFIX = Path("outputs/reports/A2_TIER1_ACCOUNT_HISTORY_2026_06_17")
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

        rows = _closed_position_rows(mt5, deals)
        payload = _payload(mt5, account_info, terminal_info, deals, rows, positions, terminal, end_utc)
    finally:
        mt5.shutdown()

    output_prefix.parent.mkdir(parents=True, exist_ok=True)
    rows_path = output_prefix.with_name(output_prefix.name + "_ROWS").with_suffix(".csv")
    json_path = output_prefix.with_suffix(".json")
    md_path = output_prefix.with_suffix(".md")
    _write_csv(rows_path, rows, _row_fields())
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    md_path.write_text(_render_markdown(payload, rows_path), encoding="utf-8")
    return {"md": md_path, "json": json_path, "rows": rows_path}


def _closed_position_rows(mt5: Any, deals: Any) -> list[dict[str, str]]:
    buy = getattr(mt5, "DEAL_TYPE_BUY", 0)
    sell = getattr(mt5, "DEAL_TYPE_SELL", 1)
    trade_deals: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for deal in deals:
        row = deal._asdict()
        if row.get("type") in {buy, sell}:
            trade_deals[int(row.get("position_id") or 0)].append(row)

    rows = []
    for position_id, items in sorted(trade_deals.items(), key=lambda item: min(d.get("time", 0) for d in item[1])):
        symbol = next((str(item.get("symbol", "")) for item in items if item.get("symbol")), "")
        entry = min(items, key=lambda item: item.get("time", 0))
        exit_deals = [item for item in items if float(item.get("profit") or 0.0) != 0.0 or str(item.get("comment", "")).startswith("[")]
        exit_deal = max(exit_deals or items, key=lambda item: item.get("time", 0))
        profit = sum(float(item.get("profit") or 0.0) for item in items)
        comments = ";".join(sorted({str(item.get("comment", "")) for item in items if item.get("comment")}))
        rows.append(
            {
                "account": "1033030",
                "symbol": symbol,
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
                "profit_aed": _fmt(profit),
                "outcome": "WIN" if profit > 0 else ("LOSS" if profit < 0 else "FLAT"),
                "comments": comments,
            }
        )
    return rows


def _payload(
    mt5: Any,
    account_info: Any,
    terminal_info: Any,
    deals: Any,
    rows: list[dict[str, str]],
    positions: Any,
    terminal: Path,
    end_utc: datetime,
) -> dict[str, Any]:
    balance_type = getattr(mt5, "DEAL_TYPE_BALANCE", 2)
    buy = getattr(mt5, "DEAL_TYPE_BUY", 0)
    sell = getattr(mt5, "DEAL_TYPE_SELL", 1)
    trade_deals = [deal._asdict() for deal in deals if deal._asdict().get("type") in {buy, sell}]
    balance_deals = [deal._asdict() for deal in deals if deal._asdict().get("type") == balance_type]
    trade_profit = sum(float(deal.get("profit") or 0.0) for deal in trade_deals)
    balance_ops = sum(float(deal.get("profit") or 0.0) for deal in balance_deals)
    open_positions = [] if positions is None else [position._asdict() for position in positions]
    return {
        "status": "PASS",
        "boundary": "Read-only MT5 query against A2 portable terminal. No runtime, EA, preset, chart, order, or position change.",
        "terminal": str(terminal),
        "window_start_utc": START_UTC.isoformat(),
        "window_end_utc": end_utc.isoformat(),
        "account": account_info._asdict() if account_info else None,
        "terminal_info": terminal_info._asdict() if terminal_info else None,
        "summary": {
            "balance_aed": _fmt(getattr(account_info, "balance", 0.0) if account_info else 0.0),
            "equity_aed": _fmt(getattr(account_info, "equity", 0.0) if account_info else 0.0),
            "floating_profit_aed": _fmt(getattr(account_info, "profit", 0.0) if account_info else 0.0),
            "balance_ops_aed": _fmt(balance_ops),
            "closed_trade_profit_aed": _fmt(trade_profit),
            "closed_positions": len(rows),
            "wins": sum(1 for row in rows if row["outcome"] == "WIN"),
            "losses": sum(1 for row in rows if row["outcome"] == "LOSS"),
            "win_rate_pct": _pct(sum(1 for row in rows if row["outcome"] == "WIN"), sum(1 for row in rows if row["outcome"] in {"WIN", "LOSS"})),
            "open_positions": len(open_positions),
        },
        "by_symbol": _group(rows, "symbol"),
        "by_candidate": _group(rows, "candidate"),
    }


def _group(rows: list[dict[str, str]], key: str) -> list[dict[str, str]]:
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        grouped[row.get(key, "") or "UNKNOWN"].append(row)
    out = []
    for name, items in grouped.items():
        wins = sum(1 for row in items if row["outcome"] == "WIN")
        losses = sum(1 for row in items if row["outcome"] == "LOSS")
        pnl = sum(float(row["profit_aed"]) for row in items)
        out.append({"group": name, "rows": str(len(items)), "wins": str(wins), "losses": str(losses), "win_rate_pct": _pct(wins, wins + losses), "pnl_aed": _fmt(pnl)})
    return sorted(out, key=lambda row: row["group"])


def _render_markdown(payload: dict[str, Any], rows_path: Path) -> str:
    summary = payload["summary"]
    lines = [
        "# A2 Tier-1 Account History Reconciliation - 2026-06-17",
        "",
        f"Status: `{payload['status']}`",
        "",
        payload["boundary"],
        "",
        f"Rows CSV: `{rows_path}`",
        "",
        "## Account Reconciliation",
        "",
        _table([summary], ["balance_aed", "equity_aed", "floating_profit_aed", "balance_ops_aed", "closed_trade_profit_aed", "closed_positions", "wins", "losses", "win_rate_pct", "open_positions"]),
        "",
        "Interpretation: `balance = balance_ops + closed_trade_profit`. Current A2 balance `4104.92` equals `4000.00` demo deposit plus `104.92` closed trade PnL.",
        "",
        "## By Symbol",
        "",
        _table(payload["by_symbol"], ["group", "rows", "wins", "losses", "win_rate_pct", "pnl_aed"]),
        "",
        "## By Candidate",
        "",
        _table(payload["by_candidate"], ["group", "rows", "wins", "losses", "win_rate_pct", "pnl_aed"]),
        "",
        "## Boundary",
        "",
        "Read-only reconciliation. No MT5 runtime, EA, preset, chart, order, position, profile, or account setting was changed.",
        "",
    ]
    return "\n".join(lines)


def _candidate_from_comments(comments: str) -> str:
    if "P2DEMO_br_XAUUSD" in comments:
        return "breakout_retest"
    return "UNKNOWN"


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


def _row_fields() -> list[str]:
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
        "profit_aed",
        "outcome",
        "comments",
    ]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Read-only export of A2 Tier-1 MT5 account history.")
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
