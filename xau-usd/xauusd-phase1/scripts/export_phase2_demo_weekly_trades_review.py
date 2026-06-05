from __future__ import annotations

import argparse
import csv
import shutil
import zipfile
from pathlib import Path
from typing import Any


DEFAULT_INPUT = Path("outputs") / "reports" / "PHASE2_DEMO_ACTUAL_BROKER_TRADES.csv"


def export_weekly_trades_review(root: Path, export_date: str, history_start: str) -> dict[str, Path]:
    root = root.resolve()
    source_csv = root / DEFAULT_INPUT
    if not source_csv.exists():
        raise FileNotFoundError(f"Actual broker trades CSV not found: {source_csv}")

    rows = [enrich_row(row) for row in read_csv(source_csv)]
    export_name = f"PHASE2_DEMO_WEEKLY_TRADES_REVIEW_{export_date}"
    export_dir = root / "docs" / "review_exports" / export_name
    export_dir.mkdir(parents=True, exist_ok=True)

    all_csv = export_dir / f"PHASE2_DEMO_WEEKLY_ALL_TRADES_{export_date}.csv"
    unique_csv = export_dir / f"PHASE2_DEMO_WEEKLY_UNIQUE_TRADES_{export_date}.csv"
    summary_md = export_dir / f"PHASE2_DEMO_WEEKLY_TRADES_SUMMARY_{export_date}.md"
    readme_md = export_dir / "README_REVIEW_EXPORT.md"
    zip_path = export_dir.with_suffix(".zip")

    unique_rows = [row for row in rows if str(row.get("is_duplicate", "")).lower() != "true"]
    write_csv(all_csv, rows)
    write_csv(unique_csv, unique_rows)
    summary_md.write_text(render_summary(export_date, history_start, rows, unique_rows), encoding="utf-8")
    readme_md.write_text(render_readme(export_date, history_start, all_csv, unique_csv, summary_md), encoding="utf-8")

    if zip_path.exists():
        zip_path.unlink()
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in (readme_md, summary_md, all_csv, unique_csv):
            archive.write(path, arcname=path.name)

    return {
        "export_dir": export_dir,
        "zip": zip_path,
        "all_csv": all_csv,
        "unique_csv": unique_csv,
        "summary_md": summary_md,
        "readme_md": readme_md,
    }


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fields = [
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
        "time_bucket",
        "outcome",
        "position_ticket",
        "magic",
        "duplicate_key",
        "duplicate_role",
        "is_duplicate",
        "entry_comment",
        "exit_comment",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def enrich_row(row: dict[str, str]) -> dict[str, str]:
    enriched = dict(row)
    enriched["time_bucket"] = time_bucket(enriched.get("entry_time", ""))
    enriched["outcome"] = outcome(enriched)
    return enriched


def time_bucket(entry_time: str) -> str:
    try:
        hour = int(entry_time[11:13])
    except (TypeError, ValueError):
        return "UNKNOWN"
    if hour >= 20 or hour < 6:
        return "Night 20:00-05:59"
    if hour < 12:
        return "Morning 06:00-11:59"
    if hour < 16:
        return "Afternoon 12:00-15:59"
    return "Evening 16:00-19:59"


def outcome(row: dict[str, str]) -> str:
    if row.get("state") == "OPEN":
        return "OPEN"
    pnl = to_float(row.get("profit_aed"))
    if pnl > 0.0:
        return "WIN"
    if pnl < 0.0:
        return "LOSS"
    return "FLAT"


def summarize(rows: list[dict[str, str]]) -> dict[str, Any]:
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
        "win_rate_pct": round(len(wins) / len(closed) * 100.0, 2) if closed else None,
        "closed_pnl_aed": round(closed_pnl, 2),
        "floating_pnl_aed": round(floating, 2),
        "net_with_open_aed": round(closed_pnl + floating, 2),
        "profit_factor": round(gross_win / abs(gross_loss), 2) if gross_loss else ("inf" if gross_win else None),
        "avg_win_aed": round(gross_win / len(wins), 2) if wins else None,
        "avg_loss_aed": round(gross_loss / len(losses), 2) if losses else None,
    }


def group_summary(rows: list[dict[str, str]], keys: list[str], limit: int | None = None) -> str:
    grouped: dict[tuple[str, ...], list[dict[str, str]]] = {}
    for row in rows:
        key = tuple(row.get(field, "") for field in keys)
        grouped.setdefault(key, []).append(row)
    items = sorted(grouped.items(), key=lambda item: summarize(item[1])["closed_pnl_aed"], reverse=True)
    if limit is not None:
        items = items[:limit]
    header = "| " + " | ".join(keys) + " | Total | Closed | Open | Wins | Losses | Win Rate | Closed PnL AED | Floating AED | Net AED | PF | Avg Win | Avg Loss |"
    divider = "|" + "|".join(["---"] * len(keys)) + "|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|"
    lines = [header, divider]
    for key, grouped_rows in items:
        summary = summarize(grouped_rows)
        lines.append("| " + " | ".join(key) + metric_cells(summary))
    return "\n".join(lines)


def render_summary(export_date: str, history_start: str, rows: list[dict[str, str]], unique_rows: list[dict[str, str]]) -> str:
    duplicate_count = len(rows) - len(unique_rows)
    return "\n".join(
        [
            f"# Phase 2 Demo Weekly Trades Summary - {export_date}",
            "",
            "This packet is actual demo broker trade evidence for reviewer inspection.",
            "",
            f"- History start: `{history_start}`",
            "- Source: refreshed MT5 broker-history export written to `outputs/reports/PHASE2_DEMO_ACTUAL_BROKER_TRADES.csv`.",
            "- Boundary: experimental demo evidence only; not canonical Phase 2 evidence and not live-trading authorization.",
            f"- Duplicate rows marked: `{duplicate_count}`.",
            "",
            "## Overall",
            "",
            metric_table([("Raw broker trades", summarize(rows)), ("Duplicate-hidden unique trades", summarize(unique_rows))]),
            "",
            "## Unique Trades by Symbol",
            "",
            group_summary(unique_rows, ["symbol"]),
            "",
            "## Unique Trades by Candidate",
            "",
            group_summary(unique_rows, ["candidate"]),
            "",
            "## Unique Trades by Time Bucket",
            "",
            group_summary(unique_rows, ["time_bucket"]),
            "",
            "## Unique Trades by Candidate and Symbol",
            "",
            group_summary(unique_rows, ["candidate", "symbol"]),
            "",
        ]
    )


def render_readme(export_date: str, history_start: str, all_csv: Path, unique_csv: Path, summary_md: Path) -> str:
    return "\n".join(
        [
            f"# Phase 2 Demo Weekly Trades Review Export - {export_date}",
            "",
            "This folder lists all actual demo broker trades captured in the configured week-to-date history window.",
            "",
            f"- History start: `{history_start}`",
            "- Evidence type: experimental demo account broker-history export.",
            "- Canonical boundary: this is not Phase 2 authorization, paper-mode approval, or live-trading evidence.",
            "",
            "Files:",
            "",
            f"- `{all_csv.name}` - all raw grouped broker trades, including duplicates and open positions.",
            f"- `{unique_csv.name}` - duplicate-hidden trade/event view.",
            f"- `{summary_md.name}` - summary tables by symbol, candidate, and time bucket.",
            "",
        ]
    )


def metric_table(rows: list[tuple[str, dict[str, Any]]]) -> str:
    lines = [
        "| View | Total | Closed | Open | Wins | Losses | Win Rate | Closed PnL AED | Floating AED | Net AED | PF | Avg Win | Avg Loss |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for label, summary in rows:
        lines.append(f"| {label}{metric_cells(summary)}")
    return "\n".join(lines)


def metric_cells(summary: dict[str, Any]) -> str:
    return (
        f" | {summary['total']} | {summary['closed']} | {summary['open']} | {summary['wins']} | {summary['losses']} | "
        f"{fmt(summary['win_rate_pct'], pct=True)} | {fmt(summary['closed_pnl_aed'])} | {fmt(summary['floating_pnl_aed'])} | "
        f"{fmt(summary['net_with_open_aed'])} | {fmt(summary['profit_factor'])} | {fmt(summary['avg_win_aed'])} | {fmt(summary['avg_loss_aed'])} |"
    )


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
    parser = argparse.ArgumentParser(description="Export week-to-date demo broker trades for reviewer inspection.")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--export-date", required=True)
    parser.add_argument("--history-start", default="2026-06-01 00:00:00")
    args = parser.parse_args()
    output = export_weekly_trades_review(args.root, args.export_date, args.history_start)
    for label, path in output.items():
        print(f"{label}: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
