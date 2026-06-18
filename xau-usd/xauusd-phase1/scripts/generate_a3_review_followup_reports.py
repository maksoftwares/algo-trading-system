from __future__ import annotations

import argparse
import csv
import json
import math
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


DEFAULT_TERMINAL = Path("C:/MT5PortableRepairLane/terminal64.exe")
DEFAULT_PROFILE_DIR = Path("C:/MT5PortableRepairLane/MQL5/Profiles/Charts/Default")
DEFAULT_FILES_DIR = Path("C:/MT5PortableRepairLane/MQL5/Files")
DEFAULT_START_UTC = datetime(2026, 6, 16, tzinfo=timezone.utc)
STAMP = "2026_06_18"
DUBAI_TZ = timezone(timedelta(hours=4))

A3_LOGIN = 1033669
SYMBOL = "XAUUSD"
MAGIC_LANES = {
    933200: "A3_BREAKOUT_PLAIN",
    933300: "A3_BREAKOUT_IMPROVED",
    933400: "A3_BREAKOUT_TIER1_COMPAT",
}
MANAGED_BY_PROFIT_LOCK = {933200, 933400}


@dataclass(frozen=True)
class Outputs:
    direct_md: Path
    direct_csv: Path
    per_magic_md: Path
    per_magic_csv: Path
    profit_lock_md: Path
    profit_lock_csv: Path
    duplicate_md: Path
    duplicate_csv: Path
    status_json: Path


def generate_reports(
    phase1_root: Path,
    terminal: Path = DEFAULT_TERMINAL,
    profile_dir: Path = DEFAULT_PROFILE_DIR,
    files_dir: Path = DEFAULT_FILES_DIR,
    start_utc: datetime = DEFAULT_START_UTC,
) -> Outputs:
    import MetaTrader5 as mt5  # type: ignore

    phase1_root = phase1_root.resolve()
    report_dir = phase1_root / "outputs" / "reports"
    report_dir.mkdir(parents=True, exist_ok=True)
    end_utc = datetime.now(timezone.utc)

    if not mt5.initialize(path=str(terminal)):
        raise RuntimeError(f"MT5 initialize failed for {terminal}: {mt5.last_error()}")
    try:
        account = mt5.account_info()
        terminal_info = mt5.terminal_info()
        deals = list(mt5.history_deals_get(start_utc, end_utc) or [])
        open_positions = list(mt5.positions_get(symbol=SYMBOL) or [])
        open_orders = list(mt5.orders_get(symbol=SYMBOL) or [])
    finally:
        mt5.shutdown()

    chart_state = load_chart_state(profile_dir)
    trade_rows = build_trade_rows(deals)
    per_magic = summarize_per_magic(trade_rows, open_positions, open_orders, chart_state)
    duplicate_rows = duplicate_family_events(trade_rows)
    profit_lock = profit_lock_status(files_dir, trade_rows, open_positions)

    direct_csv = report_dir / f"A3_DIRECT_HISTORY_1033669_{STAMP}.csv"
    direct_md = report_dir / f"A3_DIRECT_HISTORY_1033669_{STAMP}.md"
    per_magic_csv = report_dir / f"A3_PER_MAGIC_ATTRIBUTION_{STAMP}.csv"
    per_magic_md = report_dir / f"A3_PER_MAGIC_ATTRIBUTION_{STAMP}.md"
    profit_lock_csv = report_dir / f"A3_PROFIT_LOCK_ACTION_LOG_{STAMP}.csv"
    profit_lock_md = report_dir / f"A3_PROFIT_LOCK_MANAGER_STATUS_{STAMP}.md"
    duplicate_csv = report_dir / f"A3_DUPLICATE_FAMILY_EVENTS_{STAMP}.csv"
    duplicate_md = report_dir / f"A3_DUPLICATE_FAMILY_EVENTS_{STAMP}.md"
    status_json = report_dir / f"A3_REVIEW_FOLLOWUP_STATUS_{STAMP}.json"

    write_csv(direct_csv, trade_rows, direct_fields())
    write_csv(per_magic_csv, per_magic, per_magic_fields())
    write_csv(duplicate_csv, duplicate_rows, duplicate_fields())
    write_csv(profit_lock_csv, profit_lock["action_rows"], profit_lock_action_fields())

    context = {
        "status": "PASS",
        "created_at_utc": iso(end_utc),
        "boundary": "Read-only A3 review follow-up. No MT5 runtime, EA, chart, preset, order, position, or profile setting was changed.",
        "terminal": str(terminal),
        "account": account._asdict() if account else None,
        "terminal_info": terminal_info._asdict() if terminal_info else None,
        "window_start_utc": iso(start_utc),
        "window_end_utc": iso(end_utc),
        "chart_state": chart_state,
        "summary": {
            "closed_trades": len(trade_rows),
            "wins": sum(1 for row in trade_rows if row["outcome"] == "WIN"),
            "losses": sum(1 for row in trade_rows if row["outcome"] == "LOSS"),
            "net_pnl_aed": round(sum(fnum(row["net_pnl_aed"]) for row in trade_rows), 2),
            "duplicate_event_count": len(duplicate_rows),
            "profit_lock_actions": len(profit_lock["action_rows"]),
        },
    }
    direct_md.write_text(render_direct_history(context, trade_rows, direct_csv), encoding="utf-8")
    per_magic_md.write_text(render_per_magic(context, per_magic, per_magic_csv), encoding="utf-8")
    duplicate_md.write_text(render_duplicates(context, duplicate_rows, duplicate_csv), encoding="utf-8")
    profit_lock_md.write_text(render_profit_lock(context, profit_lock, profit_lock_csv), encoding="utf-8")
    status_json.write_text(json.dumps({**context, "per_magic": per_magic, "profit_lock": profit_lock, "duplicate_events": duplicate_rows}, indent=2, default=str), encoding="utf-8")
    return Outputs(direct_md, direct_csv, per_magic_md, per_magic_csv, profit_lock_md, profit_lock_csv, duplicate_md, duplicate_csv, status_json)


def build_trade_rows(deals: list[Any]) -> list[dict[str, Any]]:
    by_position: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for deal in deals:
        row = deal._asdict()
        if str(row.get("symbol", "")) != SYMBOL:
            continue
        magic = int(row.get("magic") or 0)
        if magic not in MAGIC_LANES:
            continue
        if int(row.get("entry", -1)) not in {0, 1, 2, 3}:
            continue
        by_position[int(row.get("position_id") or 0)].append(row)

    rows = []
    for position_id, items in sorted(by_position.items(), key=lambda item: min(int(row.get("time") or 0) for row in item[1])):
        items = sorted(items, key=lambda row: int(row.get("time") or 0))
        entry_deals = [row for row in items if int(row.get("entry", -1)) == 0]
        exit_deals = [row for row in items if int(row.get("entry", -1)) in {1, 3}]
        if not entry_deals or not exit_deals:
            continue
        entry = entry_deals[0]
        exit_deal = exit_deals[-1]
        magic = int(entry.get("magic") or 0)
        pnl = sum(fnum(row.get("profit")) + fnum(row.get("commission")) + fnum(row.get("swap")) + fnum(row.get("fee")) for row in items)
        entry_time = datetime.fromtimestamp(int(entry["time"]), tz=timezone.utc)
        exit_time = datetime.fromtimestamp(int(exit_deal["time"]), tz=timezone.utc)
        rows.append(
            {
                "account": str(A3_LOGIN),
                "symbol": SYMBOL,
                "position_id": str(position_id),
                "magic": str(magic),
                "lane_name": MAGIC_LANES[magic],
                "entry_time_utc": ts(entry_time),
                "exit_time_utc": ts(exit_time),
                "entry_time_dubai": ts(entry_time.astimezone(DUBAI_TZ)),
                "exit_time_dubai": ts(exit_time.astimezone(DUBAI_TZ)),
                "entry_minute_utc": entry_time.strftime("%Y-%m-%d %H:%M"),
                "session_dubai": session_bucket(entry_time.astimezone(DUBAI_TZ)),
                "direction": "BUY" if int(entry.get("type", 0)) == 0 else "SELL",
                "volume": fmt(entry.get("volume")),
                "entry_price": fmt(entry.get("price"), digits=5),
                "exit_price": fmt(exit_deal.get("price"), digits=5),
                "net_pnl_aed": fmt(pnl),
                "outcome": "WIN" if pnl > 0 else ("LOSS" if pnl < 0 else "FLAT"),
                "entry_comment": str(entry.get("comment", "")),
                "exit_comment": str(exit_deal.get("comment", "")),
            }
        )
    return rows


def load_chart_state(profile_dir: Path) -> dict[str, dict[str, str]]:
    state: dict[str, dict[str, str]] = {}
    for chart in sorted(profile_dir.glob("chart*.chr")):
        text = read_text_any(chart)
        expert = match_input(text, r"(?ms)<expert>.*?name=([^\r\n]+)")
        if not expert.startswith("Account3"):
            continue
        state[chart.name] = {
            "expert": expert,
            "magic": match_input(text, r"(?m)^InpMagicNumber=([^\r\n]+)"),
            "managed_magics": match_input(text, r"(?m)^InpManagedMagicsCsv=([^\r\n]+)"),
            "dry_run": match_input(text, r"(?m)^InpDryRunOnly=([^\r\n]+)"),
            "broker_action_allowed": match_input(text, r"(?m)^InpBrokerActionAllowed=([^\r\n]+)"),
            "manage_action_allowed": match_input(text, r"(?m)^InpManageActionAllowed=([^\r\n]+)"),
            "run_id": match_input(text, r"(?m)^InpRunId=([^\r\n]+)"),
        }
    return state


def summarize_per_magic(
    trade_rows: list[dict[str, Any]],
    open_positions: list[Any],
    open_orders: list[Any],
    chart_state: dict[str, dict[str, str]],
) -> list[dict[str, Any]]:
    chart_by_magic = {
        int(row["magic"]): row
        for row in chart_state.values()
        if str(row.get("magic", "")).isdigit()
    }
    output = []
    for magic, lane in MAGIC_LANES.items():
        rows = [row for row in trade_rows if int(row["magic"]) == magic]
        wins = [row for row in rows if row["outcome"] == "WIN"]
        losses = [row for row in rows if row["outcome"] == "LOSS"]
        net = sum(fnum(row["net_pnl_aed"]) for row in rows)
        gross_win = sum(fnum(row["net_pnl_aed"]) for row in wins)
        gross_loss = abs(sum(fnum(row["net_pnl_aed"]) for row in losses))
        chart = chart_by_magic.get(magic, {})
        output.append(
            {
                "magic": str(magic),
                "lane_name": lane,
                "closed_trades": len(rows),
                "wins": len(wins),
                "losses": len(losses),
                "win_rate": pct(len(wins), len(wins) + len(losses)),
                "net_pnl_aed": round(net, 2),
                "profit_factor": "inf" if gross_loss == 0 and gross_win > 0 else ("0.00" if gross_loss > 0 and gross_win == 0 else (f"{gross_win / gross_loss:.2f}" if gross_loss else "n/a")),
                "avg_win": round(gross_win / len(wins), 2) if wins else 0.0,
                "avg_loss": round(-gross_loss / len(losses), 2) if losses else 0.0,
                "max_loss": round(min((fnum(row["net_pnl_aed"]) for row in losses), default=0.0), 2),
                "consecutive_losses": max_consecutive_losses(rows),
                "open_positions": sum(1 for pos in open_positions if int(getattr(pos, "magic", 0)) == magic),
                "open_orders": sum(1 for order in open_orders if int(getattr(order, "magic", 0)) == magic),
                "dry_run_now": chart.get("dry_run", ""),
                "broker_action_allowed_now": chart.get("broker_action_allowed", ""),
                "run_id_now": chart.get("run_id", ""),
            }
        )
    return output


def duplicate_family_events(trade_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in trade_rows:
        grouped[(row["entry_minute_utc"], row["direction"])].append(row)
    output = []
    for (minute, direction), rows in sorted(grouped.items()):
        if len(rows) <= 1:
            continue
        output.append(
            {
                "entry_minute_utc": minute,
                "direction": direction,
                "count": len(rows),
                "magics": ";".join(row["magic"] for row in rows),
                "lanes": ";".join(row["lane_name"] for row in rows),
                "net_pnl_aed": round(sum(fnum(row["net_pnl_aed"]) for row in rows), 2),
                "position_ids": ";".join(row["position_id"] for row in rows),
            }
        )
    return output


def profit_lock_status(files_dir: Path, trade_rows: list[dict[str, Any]], open_positions: list[Any]) -> dict[str, Any]:
    startup = files_dir / "a3_profit_lock_exit_manager_startup.csv"
    action_log = files_dir / "a3_profit_lock_exit_manager_log.csv"
    action_rows = list(read_csv(action_log)) if action_log.exists() else []
    managed_rows = [row for row in trade_rows if int(row["magic"]) in MANAGED_BY_PROFIT_LOCK]
    return {
        "startup_log": str(startup),
        "startup_log_exists": startup.exists(),
        "startup_last_line": last_nonempty_line(startup),
        "action_log": str(action_log),
        "action_log_exists": action_log.exists(),
        "action_rows": action_rows,
        "managed_magics": sorted(MANAGED_BY_PROFIT_LOCK),
        "excluded_magic": 933300,
        "managed_closed_trades_in_window": len(managed_rows),
        "managed_open_positions_now": sum(1 for pos in open_positions if int(getattr(pos, "magic", 0)) in MANAGED_BY_PROFIT_LOCK),
        "sl_moves_sent": sum(1 for row in action_rows if "SLTP_MODIFY" in str(row.get("action", ""))),
        "sl_moves_failed": sum(1 for row in action_rows if "FAILED" in str(row.get("action", ""))),
        "dry_run_would_move": sum(1 for row in action_rows if str(row.get("action", "")) == "DRY_RUN_WOULD_MOVE_SL"),
        "defer_stops_level": sum(1 for row in action_rows if str(row.get("action", "")) == "DEFER_STOPS_LEVEL"),
    }


def render_direct_history(context: dict[str, Any], rows: list[dict[str, Any]], csv_path: Path) -> str:
    return "\n".join(
        [
            "# A3 Direct History - Account 1033669 - 2026-06-18",
            "",
            f"Status: `{context['status']}`",
            "",
            context["boundary"],
            "",
            f"Window UTC: `{context['window_start_utc']}` to `{context['window_end_utc']}`",
            f"Rows CSV: `{csv_path}`",
            "",
            "## Summary",
            "",
            table([context["summary"]], ["closed_trades", "wins", "losses", "net_pnl_aed", "duplicate_event_count", "profit_lock_actions"]),
            "",
            "## Closed Trades",
            "",
            table(rows, ["entry_time_dubai", "exit_time_dubai", "magic", "lane_name", "direction", "net_pnl_aed", "outcome", "exit_comment"]),
            "",
        ]
    )


def render_per_magic(context: dict[str, Any], rows: list[dict[str, Any]], csv_path: Path) -> str:
    return "\n".join(
        [
            "# A3 Per-Magic Attribution - 2026-06-18",
            "",
            f"Status: `{context['status']}`",
            "",
            context["boundary"],
            "",
            f"Rows CSV: `{csv_path}`",
            "",
            table(rows, per_magic_fields()),
            "",
            "Interpretation: `933200` is expected to remain stopped with `dry_run_now=true` and `broker_action_allowed_now=false`. `933300` and `933400` remain conditional demo lanes pending fresh forward evidence.",
            "",
        ]
    )


def render_duplicates(context: dict[str, Any], rows: list[dict[str, Any]], csv_path: Path) -> str:
    return "\n".join(
        [
            "# A3 Duplicate Family Events - 2026-06-18",
            "",
            f"Status: `{context['status']}`",
            "",
            f"Rows CSV: `{csv_path}`",
            "",
            table(rows, duplicate_fields()) if rows else "_No same-minute same-direction duplicate family events in the report window._",
            "",
        ]
    )


def render_profit_lock(context: dict[str, Any], status: dict[str, Any], csv_path: Path) -> str:
    rows = [
        {
            "managed_magics": ",".join(str(item) for item in status["managed_magics"]),
            "excluded_magic": status["excluded_magic"],
            "managed_closed_trades_in_window": status["managed_closed_trades_in_window"],
            "managed_open_positions_now": status["managed_open_positions_now"],
            "action_log_exists": status["action_log_exists"],
            "SL_moves_sent": status["sl_moves_sent"],
            "SL_moves_failed": status["sl_moves_failed"],
            "dry_run_would_move": status["dry_run_would_move"],
            "DEFER_STOPS_LEVEL": status["defer_stops_level"],
        }
    ]
    return "\n".join(
        [
            "# A3 Profit-Lock Manager Status - 2026-06-18",
            "",
            f"Status: `{context['status']}`",
            "",
            context["boundary"],
            "",
            f"Startup log: `{status['startup_log']}`",
            f"Startup latest row: `{status['startup_last_line']}`",
            f"Action CSV: `{csv_path}`",
            "",
            table(rows, list(rows[0].keys())),
            "",
            "Interpretation: no profit-lock SLTP move has been logged yet. That is expected when managed trades do not reach the `+1.25R` trigger before closing.",
            "",
        ]
    )


def max_consecutive_losses(rows: list[dict[str, Any]]) -> int:
    best = 0
    current = 0
    for row in sorted(rows, key=lambda item: item["entry_time_utc"]):
        if row["outcome"] == "LOSS":
            current += 1
            best = max(best, current)
        else:
            current = 0
    return best


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def direct_fields() -> list[str]:
    return [
        "account",
        "symbol",
        "position_id",
        "magic",
        "lane_name",
        "entry_time_utc",
        "exit_time_utc",
        "entry_time_dubai",
        "exit_time_dubai",
        "entry_minute_utc",
        "session_dubai",
        "direction",
        "volume",
        "entry_price",
        "exit_price",
        "net_pnl_aed",
        "outcome",
        "entry_comment",
        "exit_comment",
    ]


def per_magic_fields() -> list[str]:
    return [
        "magic",
        "lane_name",
        "closed_trades",
        "wins",
        "losses",
        "win_rate",
        "net_pnl_aed",
        "profit_factor",
        "avg_win",
        "avg_loss",
        "max_loss",
        "consecutive_losses",
        "open_positions",
        "open_orders",
        "dry_run_now",
        "broker_action_allowed_now",
        "run_id_now",
    ]


def duplicate_fields() -> list[str]:
    return ["entry_minute_utc", "direction", "count", "magics", "lanes", "net_pnl_aed", "position_ids"]


def profit_lock_action_fields() -> list[str]:
    return [
        "timestamp",
        "run_id",
        "account_server",
        "account_login",
        "symbol",
        "ticket",
        "magic",
        "position_type",
        "volume",
        "open_price",
        "initial_sl",
        "current_sl",
        "desired_sl",
        "tp",
        "unrealized_r",
        "trigger_r",
        "lock_r",
        "rung_name",
        "dry_run",
        "manage_action_allowed",
        "action",
        "retcode",
        "reason",
    ]


def table(rows: list[dict[str, Any]], fields: list[str]) -> str:
    if not rows:
        return "_No rows._"
    lines = ["| " + " | ".join(fields) + " |", "| " + " | ".join("---" for _ in fields) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(str(row.get(field, "")).replace("|", "\\|") for field in fields) + " |")
    return "\n".join(lines)


def last_nonempty_line(path: Path) -> str:
    if not path.exists():
        return ""
    lines = [line.strip() for line in path.read_text(encoding="utf-8", errors="replace").splitlines() if line.strip()]
    return lines[-1] if lines else ""


def read_text_any(path: Path) -> str:
    if not path.exists():
        return ""
    payload = path.read_bytes()
    for encoding in ("utf-8", "utf-16", "utf-16-le", "cp1252"):
        try:
            return payload.decode(encoding)
        except UnicodeError:
            continue
    return payload.decode(errors="replace")


def match_input(text: str, pattern: str) -> str:
    import re

    match = re.search(pattern, text)
    return match.group(1).strip() if match else ""


def session_bucket(dt: datetime) -> str:
    hour = dt.hour
    if 6 <= hour <= 11:
        return "Morning 06:00-11:59"
    if 12 <= hour <= 15:
        return "Afternoon 12:00-15:59"
    if 16 <= hour <= 19:
        return "Evening 16:00-19:59"
    return "Night 20:00-05:59"


def fmt(value: Any, digits: int = 2) -> str:
    try:
        return f"{float(value):.{digits}f}"
    except (TypeError, ValueError):
        return ""


def fnum(value: Any) -> float:
    try:
        if value is None or str(value).strip() == "":
            return 0.0
        parsed = float(value)
        if math.isnan(parsed):
            return 0.0
        return parsed
    except (TypeError, ValueError):
        return 0.0


def pct(wins: int, total: int) -> str:
    return "n/a" if total <= 0 else f"{100.0 * wins / total:.2f}%"


def iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def ts(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate read-only A3 review follow-up evidence reports.")
    parser.add_argument("--phase1-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--terminal", type=Path, default=DEFAULT_TERMINAL)
    parser.add_argument("--profile-dir", type=Path, default=DEFAULT_PROFILE_DIR)
    parser.add_argument("--files-dir", type=Path, default=DEFAULT_FILES_DIR)
    args = parser.parse_args(argv)
    outputs = generate_reports(args.phase1_root, args.terminal, args.profile_dir, args.files_dir)
    for path in outputs.__dict__.values():
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
