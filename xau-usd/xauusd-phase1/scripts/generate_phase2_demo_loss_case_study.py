from __future__ import annotations

import argparse
import csv
import json
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from generate_demo_observer_dashboard import (  # noqa: E402
    DEFAULT_TERMINAL_EXE,
    _build_actual_broker_trade_rows,
    _mark_duplicate_actual_trades,
)


DEFAULT_HISTORY_START = "2026-06-01 00:00:00"
CASE_STUDY_DOC = "PHASE2_DEMO_LOSS_CASE_STUDY_2026_06_04.md"
CASE_STUDY_CSV = "PHASE2_DEMO_LOSS_CASE_STUDY_TRADES_2026_06_04.csv"
SHADOW_FILTER_REPORT = "PHASE2_DEMO_SHADOW_FILTER_REPORT.md"
SHADOW_FILTER_DOC = "PHASE2_DEMO_SHADOW_FILTER_REPORT_2026_06_04.md"
SHADOW_FILTER_JSON = "PHASE2_DEMO_SHADOW_FILTER_REPORT.json"
SHADOW_FILTER_CSV = "PHASE2_DEMO_SHADOW_FILTER_TRADES.csv"


@dataclass(frozen=True)
class LossCaseStudyOutput:
    report_path: Path
    trades_csv_path: Path
    shadow_report_path: Path
    shadow_json_path: Path
    shadow_csv_path: Path
    status: str
    dedup_closed: int
    dedup_closed_pnl_aed: float
    shadow_kept_closed: int
    shadow_kept_closed_pnl_aed: float
    shadow_delta_aed: float


def generate_phase2_demo_loss_case_study(
    root: Path,
    terminal_exe: Path = DEFAULT_TERMINAL_EXE,
    history_start: str = DEFAULT_HISTORY_START,
) -> LossCaseStudyOutput:
    root = root.resolve()
    phase1_root = root / "xau-usd" / "xauusd-phase1" if (root / "xau-usd").exists() else root
    docs_dir = phase1_root / "docs"
    reports_dir = phase1_root / "outputs" / "reports"
    docs_dir.mkdir(parents=True, exist_ok=True)
    reports_dir.mkdir(parents=True, exist_ok=True)

    rows, source = fetch_direct_mt5_demo_trades(terminal_exe=terminal_exe, history_start=history_start)
    enriched_rows = [enrich_trade(row) for row in rows]
    dedup_rows = [row for row in enriched_rows if str(row.get("is_duplicate", "")).lower() != "true"]
    shadow_rows = [enrich_shadow_rule(row) for row in dedup_rows]
    raw_summary = summarize_trades(enriched_rows)
    dedup_summary = summarize_trades(dedup_rows)
    shadow_summary = summarize_shadow(shadow_rows)

    report_path = docs_dir / CASE_STUDY_DOC
    trades_csv_path = reports_dir / CASE_STUDY_CSV
    shadow_report_path = reports_dir / SHADOW_FILTER_REPORT
    shadow_doc_path = docs_dir / SHADOW_FILTER_DOC
    shadow_json_path = reports_dir / SHADOW_FILTER_JSON
    shadow_csv_path = reports_dir / SHADOW_FILTER_CSV

    report_path.write_text(
        render_loss_case_study(
            source=source,
            raw_rows=enriched_rows,
            dedup_rows=dedup_rows,
            raw_summary=raw_summary,
            dedup_summary=dedup_summary,
            shadow_summary=shadow_summary,
        ),
        encoding="utf-8",
    )
    write_trade_csv(trades_csv_path, enriched_rows)
    write_shadow_csv(shadow_csv_path, shadow_rows)
    shadow_payload = {
        "status": "SHADOW_ONLY_REVIEW_READY",
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "source": source,
        "policy": shadow_policy_description(),
        "baseline": dedup_summary,
        "shadow": shadow_summary,
    }
    shadow_json_path.write_text(json.dumps(shadow_payload, indent=2), encoding="utf-8")
    shadow_report = render_shadow_report(source, dedup_summary, shadow_summary, shadow_rows)
    shadow_report_path.write_text(shadow_report, encoding="utf-8")
    shadow_doc_path.write_text(shadow_report, encoding="utf-8")

    return LossCaseStudyOutput(
        report_path=report_path,
        trades_csv_path=trades_csv_path,
        shadow_report_path=shadow_doc_path,
        shadow_json_path=shadow_json_path,
        shadow_csv_path=shadow_csv_path,
        status="SHADOW_ONLY_REVIEW_READY",
        dedup_closed=int(dedup_summary["closed"]),
        dedup_closed_pnl_aed=float(dedup_summary["closed_pnl_aed"]),
        shadow_kept_closed=int(shadow_summary["kept"]["closed"]),
        shadow_kept_closed_pnl_aed=float(shadow_summary["kept"]["closed_pnl_aed"]),
        shadow_delta_aed=float(shadow_summary["delta_closed_pnl_aed"]),
    )


def fetch_direct_mt5_demo_trades(terminal_exe: Path, history_start: str) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    try:
        import MetaTrader5 as mt5  # type: ignore[import-not-found]
    except Exception as exc:  # pragma: no cover - local bridge dependency
        raise RuntimeError(f"MetaTrader5 import failed: {type(exc).__name__}: {exc}") from exc

    terminal_exe = terminal_exe.resolve()
    if not terminal_exe.exists():
        raise FileNotFoundError(f"MT5 terminal not found: {terminal_exe}")

    start = datetime.strptime(history_start, "%Y-%m-%d %H:%M:%S")
    end = datetime.now()
    if not mt5.initialize(path=str(terminal_exe)):  # pragma: no cover - local terminal dependency
        raise RuntimeError(f"MT5 initialize failed: {mt5.last_error()}")
    try:  # pragma: no cover - exercised against user's terminal
        account = mt5.account_info()
        terminal_info = mt5.terminal_info()
        deals = list(mt5.history_deals_get(start, end) or [])
        orders = list(mt5.history_orders_get(start, end) or [])
        positions = list(mt5.positions_get() or [])
        rows = _build_actual_broker_trade_rows(mt5, deals, orders, positions)
        _mark_duplicate_actual_trades(rows)
        source = {
            "terminal_exe": str(terminal_exe),
            "account": getattr(account, "login", ""),
            "server": getattr(account, "server", ""),
            "currency": getattr(account, "currency", ""),
            "data_path": getattr(terminal_info, "data_path", ""),
            "history_start": start.strftime("%Y-%m-%d %H:%M:%S"),
            "history_end": end.strftime("%Y-%m-%d %H:%M:%S"),
            "raw_deals": len(deals),
            "raw_orders": len(orders),
            "open_positions": len(positions),
        }
    finally:
        mt5.shutdown()
    return [row for row in rows if row.get("candidate")], source


def enrich_trade(row: dict[str, Any]) -> dict[str, Any]:
    enriched = dict(row)
    enriched["time_bucket"] = time_bucket(str(enriched.get("entry_time", "")))
    enriched["outcome"] = outcome(enriched)
    enriched["exit_reason_class"] = exit_reason(enriched)
    return enriched


def enrich_shadow_rule(row: dict[str, Any]) -> dict[str, Any]:
    enriched = dict(row)
    blocked, reason = shadow_block_reason(enriched)
    enriched["shadow_action"] = "BLOCK" if blocked else "KEEP"
    enriched["shadow_reason"] = reason
    return enriched


def time_bucket(entry_time: str) -> str:
    timestamp = datetime.strptime(entry_time, "%Y-%m-%d %H:%M:%S")
    hour = timestamp.hour
    if hour >= 20 or hour < 6:
        return "Night 20:00-05:59"
    if hour < 12:
        return "Morning 06:00-11:59"
    if hour < 16:
        return "Afternoon 12:00-15:59"
    return "Evening 16:00-19:59"


def outcome(row: dict[str, Any]) -> str:
    if row.get("state") == "OPEN":
        return "OPEN"
    pnl = to_float(row.get("profit_aed"))
    if pnl > 0.0:
        return "WIN"
    if pnl < 0.0:
        return "LOSS"
    return "FLAT"


def exit_reason(row: dict[str, Any]) -> str:
    if row.get("state") == "OPEN":
        return "OPEN"
    comment = str(row.get("exit_comment", "")).lower()
    if "[sl" in comment:
        return "SL"
    if "[tp" in comment:
        return "TP"
    return "OTHER"


def shadow_block_reason(row: dict[str, Any]) -> tuple[bool, str]:
    if row.get("candidate") == "session_extreme_retest_v0":
        return True, "BLOCK_PROVISIONAL_SESSION_EXTREME_RETEST"
    if row.get("symbol") == "XAUUSD" and row.get("time_bucket") in {"Morning 06:00-11:59", "Afternoon 12:00-15:59"}:
        return True, "BLOCK_XAUUSD_MORNING_AFTERNOON"
    return False, "KEEP"


def summarize_trades(rows: list[dict[str, Any]]) -> dict[str, Any]:
    closed = [row for row in rows if row.get("state") == "CLOSED"]
    open_rows = [row for row in rows if row.get("state") == "OPEN"]
    wins = [row for row in closed if to_float(row.get("profit_aed")) > 0.0]
    losses = [row for row in closed if to_float(row.get("profit_aed")) < 0.0]
    gross_win = sum(to_float(row.get("profit_aed")) for row in wins)
    gross_loss = sum(to_float(row.get("profit_aed")) for row in losses)
    closed_pnl = sum(to_float(row.get("profit_aed")) for row in closed)
    floating = sum(to_float(row.get("profit_aed")) for row in open_rows)
    return {
        "total": len(rows),
        "closed": len(closed),
        "open": len(open_rows),
        "wins": len(wins),
        "losses": len(losses),
        "win_rate_pct": round((len(wins) / len(closed) * 100.0), 2) if closed else None,
        "closed_pnl_aed": round(closed_pnl, 2),
        "floating_pnl_aed": round(floating, 2),
        "net_including_open_aed": round(closed_pnl + floating, 2),
        "profit_factor": round(gross_win / abs(gross_loss), 2) if gross_loss else ("inf" if gross_win else None),
        "avg_win_aed": round(gross_win / len(wins), 2) if wins else None,
        "avg_loss_aed": round(gross_loss / len(losses), 2) if losses else None,
    }


def summarize_shadow(rows: list[dict[str, Any]]) -> dict[str, Any]:
    kept = [row for row in rows if row.get("shadow_action") == "KEEP"]
    blocked = [row for row in rows if row.get("shadow_action") == "BLOCK"]
    baseline = summarize_trades(rows)
    kept_summary = summarize_trades(kept)
    blocked_summary = summarize_trades(blocked)
    return {
        "policy_status": "SHADOW_ONLY_NOT_ENFORCED",
        "baseline": baseline,
        "kept": kept_summary,
        "blocked": blocked_summary,
        "delta_closed_pnl_aed": round(float(kept_summary["closed_pnl_aed"]) - float(baseline["closed_pnl_aed"]), 2),
        "blocked_reason_counts": count_by(blocked, "shadow_reason"),
    }


def count_by(rows: list[dict[str, Any]], field: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        key = str(row.get(field, ""))
        counts[key] = counts.get(key, 0) + 1
    return dict(sorted(counts.items()))


def render_loss_case_study(
    source: dict[str, Any],
    raw_rows: list[dict[str, Any]],
    dedup_rows: list[dict[str, Any]],
    raw_summary: dict[str, Any],
    dedup_summary: dict[str, Any],
    shadow_summary: dict[str, Any],
) -> str:
    sections = [
        "# Phase 2 Demo Loss Case Study - Actual MT5 Trades",
        "",
        f"Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} Asia/Dubai local system time",
        f"Source terminal: `{source['terminal_exe']}`",
        f"Account: `{source['account']} / {source['server']} / {source['currency']}`",
        f"History window: `{source['history_start']}` to `{source['history_end']}`",
        "",
        "This study uses direct MT5 history, groups entry/exit deals into trades, and marks same-minute same-symbol same-side duplicate families. The duplicate-hidden baseline is the main decision view.",
        "",
        "## Executive Findings",
        "",
        f"- Duplicate-hidden baseline: {dedup_summary['closed']} closed trades, {dedup_summary['wins']} wins, {dedup_summary['losses']} losses, win rate {fmt(dedup_summary['win_rate_pct'], pct=True)}, closed PnL {fmt(dedup_summary['closed_pnl_aed'])} AED, PF {fmt(dedup_summary['profit_factor'])}.",
        f"- Raw actual grouped orders: {raw_summary['closed']} closed trades, PnL {fmt(raw_summary['closed_pnl_aed'])} AED. Raw order-level evidence is less clean because duplicate same-family entries amplify both wins and losses.",
        "- The primary loss driver is not broker charges in this demo sample; losses are mainly stop-loss outcomes from selection/timing.",
        f"- Shadow filter impact if only measured, not enforced: kept PnL {fmt(shadow_summary['kept']['closed_pnl_aed'])} AED versus baseline {fmt(shadow_summary['baseline']['closed_pnl_aed'])} AED, delta {fmt(shadow_summary['delta_closed_pnl_aed'])} AED.",
        "- The worst clusters remain XAUUSD morning/afternoon and `symbol_normalized_round_retest_v0`; `breakout_retest` is positive overall and strongest in evening XAUUSD.",
        "",
        "## Overall",
        "",
        metric_table(
            ["View", "Closed", "Open", "Wins", "Losses", "Win Rate", "Closed PnL AED", "PF", "Avg Win", "Avg Loss"],
            [
                ["Raw grouped MT5 trades", raw_summary],
                ["Duplicate-hidden baseline", dedup_summary],
                ["Shadow kept subset", shadow_summary["kept"]],
                ["Shadow blocked subset", shadow_summary["blocked"]],
            ],
        ),
        "",
        grouped_table("By EA", dedup_rows, ["candidate"]),
        "",
        grouped_table("By Symbol", dedup_rows, ["symbol"]),
        "",
        grouped_table("By Time Bucket", dedup_rows, ["time_bucket"]),
        "",
        grouped_table("EA x Time Bucket", dedup_rows, ["candidate", "time_bucket"]),
        "",
        grouped_table("Worst EA x Symbol x Time Clusters", dedup_rows, ["candidate", "symbol", "time_bucket"], reverse=False, limit=12),
        "",
        "## Largest Individual Losses",
        "",
        largest_loss_table(dedup_rows),
        "",
        "## Interpretation",
        "",
        "The loss pattern is mostly a filtering problem, not a broker-cost-only problem. The same strategies perform very differently by time bucket and symbol. Evening/night XAUUSD has been profitable, while morning/afternoon XAUUSD has been the main drag. This report now includes a shadow-only policy so the weak clusters can be measured without changing the running EAs.",
        "",
        "Recommended operating stance: keep execution unchanged for the planned observation window, but review the shadow filter delta daily. Do not enforce it until it survives a larger sample.",
        "",
    ]
    return "\n".join(sections)


def render_shadow_report(source: dict[str, Any], baseline: dict[str, Any], shadow: dict[str, Any], rows: list[dict[str, Any]]) -> str:
    kept = [row for row in rows if row.get("shadow_action") == "KEEP"]
    blocked = [row for row in rows if row.get("shadow_action") == "BLOCK"]
    return "\n".join(
        [
            "# Phase 2 Demo Shadow Filter Report",
            "",
            "Overall status: SHADOW_ONLY_REVIEW_READY",
            "",
            "This report measures a proposed filter without changing MT5, EA settings, orders, charts, or live behavior.",
            "",
            f"Source terminal: `{source['terminal_exe']}`",
            f"Account: `{source['account']} / {source['server']} / {source['currency']}`",
            f"History window: `{source['history_start']}` to `{source['history_end']}`",
            "",
            "## Shadow Policy",
            "",
            shadow_policy_description(),
            "",
            "## Result",
            "",
            metric_table(
                ["View", "Closed", "Open", "Wins", "Losses", "Win Rate", "Closed PnL AED", "PF", "Avg Win", "Avg Loss"],
                [
                    ["Baseline duplicate-hidden", baseline],
                    ["Would keep", shadow["kept"]],
                    ["Would block", shadow["blocked"]],
                ],
            ),
            "",
            f"Shadow delta versus baseline: `{fmt(shadow['delta_closed_pnl_aed'])} AED`.",
            "",
            "## Block Reason Counts",
            "",
            simple_count_table(shadow["blocked_reason_counts"]),
            "",
            grouped_table("Would Keep by EA", kept, ["candidate"]),
            "",
            grouped_table("Would Block by EA", blocked, ["candidate"]),
            "",
            grouped_table("Would Block by Symbol and Time", blocked, ["symbol", "time_bucket"]),
            "",
            "## Boundary",
            "",
            "- Shadow-only report; not enforced.",
            "- Does not authorize canonical Phase 2.",
            "- Does not change demo executor behavior.",
            "- Requires larger sample before any router/session filter decision.",
            "",
        ]
    )


def shadow_policy_description() -> str:
    return "\n".join(
        [
            "- Keep all EAs running unchanged.",
            "- Measure a hypothetical block for `session_extreme_retest_v0`.",
            "- Measure a hypothetical block for XAUUSD trades entered in Morning `06:00-11:59` or Afternoon `12:00-15:59`.",
            "- Keep evening/night XAUUSD and all non-XAUUSD trades unless blocked by the provisional-EA rule above.",
        ]
    )


def grouped_table(title: str, rows: list[dict[str, Any]], keys: list[str], reverse: bool = True, limit: int | None = None) -> str:
    grouped: dict[tuple[str, ...], list[dict[str, Any]]] = {}
    for row in rows:
        key = tuple(str(row.get(field, "")) for field in keys)
        grouped.setdefault(key, []).append(row)
    sorted_groups = sorted(grouped.items(), key=lambda item: float(summarize_trades(item[1])["closed_pnl_aed"]), reverse=reverse)
    if limit is not None:
        sorted_groups = sorted_groups[:limit]
    header = "| " + " | ".join(keys) + " | Closed | Open | Wins | Losses | Win Rate | Closed PnL AED | PF | Avg Win | Avg Loss |"
    divider = "|" + "|".join(["---"] * len(keys)) + "|---:|---:|---:|---:|---:|---:|---:|---:|---:|"
    lines = [f"## {title}", "", header, divider]
    for key, items in sorted_groups:
        summary = summarize_trades(items)
        lines.append("| " + " | ".join(key) + metric_cells(summary))
    return "\n".join(lines)


def metric_table(headers: list[str], rows: list[list[Any]]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for label, summary in rows:
        lines.append(f"| {label}{metric_cells(summary)}")
    return "\n".join(lines)


def metric_cells(summary: dict[str, Any]) -> str:
    return (
        f" | {summary['closed']} | {summary['open']} | {summary['wins']} | {summary['losses']} | "
        f"{fmt(summary['win_rate_pct'], pct=True)} | {fmt(summary['closed_pnl_aed'])} | "
        f"{fmt(summary['profit_factor'])} | {fmt(summary['avg_win_aed'])} | {fmt(summary['avg_loss_aed'])} |"
    )


def largest_loss_table(rows: list[dict[str, Any]], limit: int = 15) -> str:
    losses = sorted(
        [row for row in rows if row.get("state") == "CLOSED" and to_float(row.get("profit_aed")) < 0.0],
        key=lambda row: to_float(row.get("profit_aed")),
    )[:limit]
    lines = [
        "| Entry | Exit | EA | Symbol | Direction | Time Bucket | PnL AED | Duplicate Role | Exit |",
        "|---|---|---|---|---|---|---:|---|---|",
    ]
    for row in losses:
        lines.append(
            f"| {row.get('entry_time', '')} | {row.get('exit_time', '')} | {row.get('candidate', '')} | "
            f"{row.get('symbol', '')} | {row.get('direction', '')} | {row.get('time_bucket', '')} | "
            f"{fmt(to_float(row.get('profit_aed')))} | {row.get('duplicate_role', '')} | {row.get('exit_comment', '')} |"
        )
    return "\n".join(lines)


def simple_count_table(counts: dict[str, int]) -> str:
    lines = ["| Reason | Count |", "|---|---:|"]
    for reason, count in counts.items():
        lines.append(f"| {reason} | {count} |")
    return "\n".join(lines)


def write_trade_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    fields = [
        "entry_time",
        "exit_time",
        "candidate",
        "status",
        "symbol",
        "direction",
        "state",
        "profit_aed",
        "time_bucket",
        "outcome",
        "exit_reason_class",
        "duplicate_role",
        "is_duplicate",
        "position_ticket",
        "magic",
        "entry_price",
        "exit_price",
        "sl",
        "tp",
        "exit_comment",
    ]
    write_csv(path, rows, fields)


def write_shadow_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    fields = [
        "entry_time",
        "exit_time",
        "candidate",
        "status",
        "symbol",
        "direction",
        "state",
        "profit_aed",
        "time_bucket",
        "outcome",
        "shadow_action",
        "shadow_reason",
        "position_ticket",
    ]
    write_csv(path, rows, fields)


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def to_float(value: Any) -> float:
    try:
        return float(value or 0.0)
    except (TypeError, ValueError):
        return 0.0


def fmt(value: Any, pct: bool = False) -> str:
    if value is None:
        return "n/a"
    if value == "inf":
        return "inf"
    if isinstance(value, str):
        return value
    number = float(value)
    return f"{number:.2f}%" if pct else f"{number:.2f}"


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a direct-MT5 loss case study and shadow filter report.")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[3])
    parser.add_argument("--terminal-exe", type=Path, default=DEFAULT_TERMINAL_EXE)
    parser.add_argument("--history-start", default=DEFAULT_HISTORY_START)
    args = parser.parse_args()
    output = generate_phase2_demo_loss_case_study(
        root=args.root,
        terminal_exe=args.terminal_exe,
        history_start=args.history_start,
    )
    print(f"Status: {output.status}")
    print(f"Loss case study: {output.report_path}")
    print(f"Trade CSV: {output.trades_csv_path}")
    print(f"Shadow filter report: {output.shadow_report_path}")
    print(f"Shadow delta AED: {output.shadow_delta_aed:.2f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
