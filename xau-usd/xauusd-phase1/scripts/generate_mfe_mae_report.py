from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEFAULT_ACTUAL_TRADES = Path("outputs") / "reports" / "PHASE2_DEMO_ACTUAL_BROKER_TRADES.csv"
DEFAULT_POSITION_PATH_FILES = Path("C:/MT5PortablePositionPathObserver/MQL5/Files")
DEFAULT_OUTPUT_CSV = Path("outputs") / "reports" / "MFE_MAE_2026_06_16.csv"
DEFAULT_OUTPUT_JSON = Path("outputs") / "reports" / "MFE_MAE_2026_06_16.json"
DEFAULT_OUTPUT_MD = Path("outputs") / "reports" / "MFE_MAE_2026_06_16.md"
GREEN_THEN_LOST_THRESHOLD_R = 0.5


def generate_mfe_mae_report(
    phase1_root: Path,
    *,
    actual_trades_csv: Path | None = None,
    position_path_files: Path = DEFAULT_POSITION_PATH_FILES,
    output_csv: Path | None = None,
    output_json: Path | None = None,
    output_md: Path | None = None,
    threshold_r: float = GREEN_THEN_LOST_THRESHOLD_R,
) -> Path:
    phase1_root = phase1_root.resolve()
    actual_trades_csv = (actual_trades_csv or phase1_root / DEFAULT_ACTUAL_TRADES).resolve()
    output_csv = (output_csv or phase1_root / DEFAULT_OUTPUT_CSV).resolve()
    output_json = (output_json or phase1_root / DEFAULT_OUTPUT_JSON).resolve()
    output_md = (output_md or phase1_root / DEFAULT_OUTPUT_MD).resolve()
    position_path_files = position_path_files.resolve()

    trades = [
        row
        for row in _read_csv(actual_trades_csv)
        if row.get("state") == "CLOSED" and _is_gold(row.get("symbol", ""))
    ]
    snapshots_by_ticket = _load_path_snapshots(position_path_files)
    rows = [_mfe_mae_row(trade, snapshots_by_ticket.get(str(trade.get("position_ticket", "")), []), threshold_r) for trade in trades]
    summary = _summary(rows, threshold_r)
    payload = {
        "status": "PASS" if rows else "NO_CLOSED_GOLD_TRADES",
        "created_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "authority": (
            "Analysis-only MFE/MAE report. It reads exported broker trades and existing 10-second position-path "
            "snapshots; it does not touch MT5 runtime, charts, orders, positions, presets, or EA settings."
        ),
        "actual_trades_csv": str(actual_trades_csv),
        "position_path_files": str(position_path_files),
        "closed_gold_trades": len(trades),
        "rows_with_path_snapshots": sum(1 for row in rows if row.get("source") == "PATH_SNAPSHOTS"),
        "rows_without_path_snapshots": sum(1 for row in rows if row.get("source") != "PATH_SNAPSHOTS"),
        "green_then_lost_threshold_r": threshold_r,
        "summary": summary,
        "rows": rows,
    }
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    _write_csv(output_csv, rows, _fields())
    output_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    output_md.write_text(_render_markdown(payload), encoding="utf-8")
    return output_json


def _load_path_snapshots(files_dir: Path) -> dict[str, list[dict[str, str]]]:
    snapshots: dict[str, list[dict[str, str]]] = defaultdict(list)
    if not files_dir.exists():
        return snapshots
    for path in sorted(files_dir.glob("position_path_log_*.csv")):
        for row in _read_csv(path):
            ticket = str(row.get("position_ticket", "")).strip()
            if ticket:
                row["_source_file"] = path.name
                snapshots[ticket].append(row)
    for rows in snapshots.values():
        rows.sort(key=lambda row: row.get("ts_utc", ""))
    return snapshots


def _mfe_mae_row(trade: dict[str, str], snapshots: list[dict[str, str]], threshold_r: float) -> dict[str, str]:
    ticket = str(trade.get("position_ticket", ""))
    direction = str(trade.get("direction", "")).upper()
    symbol = str(trade.get("symbol", "")).upper()
    entry = _float(trade.get("entry_price"))
    stop = _float(trade.get("sl"))
    point = _point_size(symbol)
    stop_points = abs(entry - stop) / point if entry is not None and stop is not None and point > 0 else None
    candidate = str(trade.get("candidate", ""))
    profit = _float(trade.get("profit_aed"))

    if not snapshots:
        return {
            **_trade_identity(trade),
            "source": "NO_PATH_SNAPSHOTS",
            "snapshots_count": "0",
            "mfe_points": "",
            "mfe_r": "",
            "mae_points": "",
            "mae_r": "",
            "max_unrealized_r": "",
            "min_unrealized_r": "",
            "went_green_then_lost": "false",
            "note": "No matching 10-second position-path snapshots were found for this closed gold ticket.",
        }

    mfe_points = 0.0
    mae_points = 0.0
    unrealized_values: list[float] = []
    for snap in snapshots:
        current = _float(snap.get("price_current"))
        unrealized_r = _float(snap.get("unrealized_R"))
        if unrealized_r is not None:
            unrealized_values.append(unrealized_r)
        if current is None or entry is None:
            continue
        if direction == "BUY":
            favorable = (current - entry) / point
            adverse = (entry - current) / point
        elif direction == "SELL":
            favorable = (entry - current) / point
            adverse = (current - entry) / point
        else:
            continue
        mfe_points = max(mfe_points, favorable)
        mae_points = max(mae_points, adverse)

    max_unrealized_r = max(unrealized_values) if unrealized_values else None
    min_unrealized_r = min(unrealized_values) if unrealized_values else None
    mfe_r = mfe_points / stop_points if stop_points and stop_points > 0 else max_unrealized_r
    mae_r = mae_points / stop_points if stop_points and stop_points > 0 else (-min_unrealized_r if min_unrealized_r is not None else None)
    went_green_then_lost = bool(profit is not None and profit < 0.0 and mfe_r is not None and mfe_r >= threshold_r)
    return {
        **_trade_identity(trade),
        "source": "PATH_SNAPSHOTS",
        "snapshots_count": str(len(snapshots)),
        "mfe_points": _fmt(mfe_points),
        "mfe_r": _fmt(mfe_r),
        "mae_points": _fmt(mae_points),
        "mae_r": _fmt(mae_r),
        "max_unrealized_r": _fmt(max_unrealized_r),
        "min_unrealized_r": _fmt(min_unrealized_r),
        "went_green_then_lost": "true" if went_green_then_lost else "false",
        "note": f"Path snapshots from {snapshots[0].get('_source_file', '')}..{snapshots[-1].get('_source_file', '')}",
        "candidate": candidate,
    }


def _trade_identity(trade: dict[str, str]) -> dict[str, str]:
    return {
        "position_ticket": str(trade.get("position_ticket", "")),
        "candidate": str(trade.get("candidate", "")),
        "symbol": str(trade.get("symbol", "")),
        "direction": str(trade.get("direction", "")),
        "volume": str(trade.get("volume", "")),
        "entry_time": str(trade.get("entry_time", "")),
        "exit_time": str(trade.get("exit_time", "")),
        "entry_price": str(trade.get("entry_price", "")),
        "exit_price": str(trade.get("exit_price", "")),
        "sl": str(trade.get("sl", "")),
        "tp": str(trade.get("tp", "")),
        "profit_aed": str(trade.get("profit_aed", "")),
        "time_bucket": str(trade.get("time_bucket", "")),
    }


def _summary(rows: list[dict[str, str]], threshold_r: float) -> dict[str, Any]:
    path_rows = [row for row in rows if row.get("source") == "PATH_SNAPSHOTS"]
    winners = [row for row in path_rows if (_float(row.get("profit_aed")) or 0.0) > 0.0]
    losers = [row for row in path_rows if (_float(row.get("profit_aed")) or 0.0) < 0.0]
    green_then_lost = [row for row in losers if str(row.get("went_green_then_lost", "")).lower() == "true"]
    by_candidate = []
    for candidate in sorted({row.get("candidate", "") for row in path_rows}):
        items = [row for row in path_rows if row.get("candidate") == candidate]
        item_losers = [row for row in items if (_float(row.get("profit_aed")) or 0.0) < 0.0]
        item_green_lost = [row for row in item_losers if str(row.get("went_green_then_lost", "")).lower() == "true"]
        by_candidate.append(
            {
                "candidate": candidate or "UNKNOWN",
                "closed": len(items),
                "avg_mfe_r": _fmt(_avg(_float(row.get("mfe_r")) for row in items)),
                "avg_mae_r": _fmt(_avg(_float(row.get("mae_r")) for row in items)),
                "losers_green_then_lost_pct": _pct(len(item_green_lost), len(item_losers)),
            }
        )
    return {
        "rows": len(rows),
        "path_snapshot_rows": len(path_rows),
        "avg_mae_r_on_winners": _fmt(_avg(_float(row.get("mae_r")) for row in winners)),
        "avg_mfe_r_on_losers": _fmt(_avg(_float(row.get("mfe_r")) for row in losers)),
        "losers_green_then_lost_count": len(green_then_lost),
        "losers_green_then_lost_pct": _pct(len(green_then_lost), len(losers)),
        "green_then_lost_threshold_r": threshold_r,
        "by_candidate": by_candidate,
    }


def _render_markdown(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    lines = [
        "# MFE/MAE Report - 2026-06-16",
        "",
        f"Status: `{payload['status']}`",
        "",
        payload["authority"],
        "",
        f"Actual trades CSV: `{payload['actual_trades_csv']}`",
        f"Position path files: `{payload['position_path_files']}`",
        f"Closed gold trades: `{payload['closed_gold_trades']}`",
        f"Rows with path snapshots: `{payload['rows_with_path_snapshots']}`",
        f"Rows without path snapshots: `{payload['rows_without_path_snapshots']}`",
        "",
        "## Summary",
        "",
        f"- Avg MAE R on winners: `{summary['avg_mae_r_on_winners']}`",
        f"- Avg MFE R on losers: `{summary['avg_mfe_r_on_losers']}`",
        f"- Losers that went at least `{payload['green_then_lost_threshold_r']}`R green before loss: `{summary['losers_green_then_lost_count']}` (`{summary['losers_green_then_lost_pct']}`)",
        "",
        "## By Candidate",
        "",
        _table(summary["by_candidate"], ["candidate", "closed", "avg_mfe_r", "avg_mae_r", "losers_green_then_lost_pct"]),
        "",
        "## Boundary",
        "",
        "- This is analysis-only.",
        "- It reads exported broker trades and existing observer snapshots only.",
        "- It does not modify MT5 runtime, charts, orders, positions, presets, or EA settings.",
        "",
    ]
    return "\n".join(lines)


def _fields() -> list[str]:
    return [
        "position_ticket",
        "candidate",
        "symbol",
        "direction",
        "volume",
        "entry_time",
        "exit_time",
        "entry_price",
        "exit_price",
        "sl",
        "tp",
        "profit_aed",
        "time_bucket",
        "source",
        "snapshots_count",
        "mfe_points",
        "mfe_r",
        "mae_points",
        "mae_r",
        "max_unrealized_r",
        "min_unrealized_r",
        "went_green_then_lost",
        "note",
    ]


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", errors="replace", newline="") as handle:
        return list(csv.DictReader(handle))


def _write_csv(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def _table(rows: list[dict[str, Any]], columns: list[str]) -> str:
    if not rows:
        return "_No rows._"
    lines = [
        "| " + " | ".join(columns) + " |",
        "| " + " | ".join("---" for _ in columns) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(str(row.get(column, "")) for column in columns) + " |")
    return "\n".join(lines)


def _is_gold(symbol: str) -> bool:
    return str(symbol or "").upper().startswith("XAU")


def _point_size(symbol: str) -> float:
    if str(symbol or "").upper().endswith("JPY"):
        return 0.001
    if str(symbol or "").upper() in {"EURUSD", "GBPUSD"}:
        return 0.00001
    return 0.01


def _float(value: str | None) -> float | None:
    try:
        return float(str(value or "").strip())
    except ValueError:
        return None


def _fmt(value: float | None) -> str:
    if value is None:
        return ""
    return f"{value:.4f}"


def _avg(values: Any) -> float | None:
    filtered = [value for value in values if value is not None]
    if not filtered:
        return None
    return sum(filtered) / len(filtered)


def _pct(numerator: int, denominator: int) -> str:
    if denominator <= 0:
        return "n/a"
    return f"{(numerator / denominator * 100.0):.2f}%"


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate MFE/MAE evidence from broker trades and position-path snapshots.")
    parser.add_argument("--phase1-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--actual-trades-csv", type=Path, default=None)
    parser.add_argument("--position-path-files", type=Path, default=DEFAULT_POSITION_PATH_FILES)
    parser.add_argument("--output-csv", type=Path, default=None)
    parser.add_argument("--output-json", type=Path, default=None)
    parser.add_argument("--output-md", type=Path, default=None)
    parser.add_argument("--threshold-r", type=float, default=GREEN_THEN_LOST_THRESHOLD_R)
    args = parser.parse_args()
    output = generate_mfe_mae_report(
        args.phase1_root,
        actual_trades_csv=args.actual_trades_csv,
        position_path_files=args.position_path_files,
        output_csv=args.output_csv,
        output_json=args.output_json,
        output_md=args.output_md,
        threshold_r=args.threshold_r,
    )
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
