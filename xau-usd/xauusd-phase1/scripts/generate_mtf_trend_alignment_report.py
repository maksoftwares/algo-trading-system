from __future__ import annotations

import argparse
import bisect
import csv
import json
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


DEFAULT_ACTUAL_TRADES = Path("outputs") / "reports" / "PHASE2_DEMO_ACTUAL_BROKER_TRADES.csv"
DEFAULT_BARS_DIR = Path("outputs") / "reports" / "m5_replay_bars"
DEFAULT_OUTPUT_DOC = Path("docs") / "MULTI_TIMEFRAME_TREND_ALIGNMENT_REPORT_2026_06_13.md"
DEFAULT_OUTPUT_JSON = Path("outputs") / "reports" / "MULTI_TIMEFRAME_TREND_ALIGNMENT_REPORT_2026_06_13.json"

TREND_TIMEFRAMES = ("H1", "H4")
SMA_PERIOD = 20

ROUND_RETEST_CANDIDATES = {
    "symbol_normalized_round_retest_v0",
    "round_number_retest_v0",
    "symbol_normalized_round_retest_v0_repair_v1",
    "round_number_retest_v0_repair_v1",
}
SESSION_EXTREME_CANDIDATES = {
    "session_extreme_retest_v0",
    "session_extreme_retest_v0_repair_v1",
}
BREAKOUT_CANDIDATES = {
    "breakout_retest",
    "swing_breakout_retest_v0",
    "p2weakness_br_v1",
}


@dataclass(frozen=True)
class MtfTrendAlignmentOutput:
    status: str
    markdown_path: Path
    json_path: Path
    closed_kept_rows: int
    resolved_tags: int


def generate_mtf_trend_alignment_report(
    phase1_root: Path,
    actual_trades_csv: Path | None = None,
    bars_dir: Path | None = None,
    output_doc: Path | None = None,
    output_json: Path | None = None,
) -> MtfTrendAlignmentOutput:
    phase1_root = phase1_root.resolve()
    actual_trades_csv = (actual_trades_csv or phase1_root / DEFAULT_ACTUAL_TRADES).resolve()
    bars_dir = (bars_dir or phase1_root / DEFAULT_BARS_DIR).resolve()
    output_doc = (output_doc or phase1_root / DEFAULT_OUTPUT_DOC).resolve()
    output_json = (output_json or phase1_root / DEFAULT_OUTPUT_JSON).resolve()
    output_doc.parent.mkdir(parents=True, exist_ok=True)
    output_json.parent.mkdir(parents=True, exist_ok=True)

    bars_by_timeframe = {
        timeframe: _load_bars(bars_dir, timeframe)
        for timeframe in TREND_TIMEFRAMES
    }
    raw_rows = [_normalize_trade(row) for row in _read_csv(actual_trades_csv)]
    closed_kept = [
        row
        for row in raw_rows
        if row.get("state") == "CLOSED" and not row["is_duplicate_bool"]
    ]
    trend_rows = [
        _trend_row(row, timeframe, bars_by_timeframe[timeframe])
        for row in closed_kept
        for timeframe in TREND_TIMEFRAMES
    ]
    resolved_rows = [row for row in trend_rows if row["trend_status"] == "RESOLVED"]
    status = "TREND_ALIGNMENT_READY" if resolved_rows else "INSUFFICIENT_DATA"
    payload = {
        "status": status,
        "generated_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "boundary": (
            "Research report only. Reads broker-history and exported OHLC bars; does not "
            "modify MT5 terminals, EAs, presets, orders, positions, or Phase 2 canonical status."
        ),
        "source_actual_trades_csv": str(actual_trades_csv),
        "source_bars_dir": str(bars_dir),
        "trend_definition": (
            "For each H1/H4 timeframe, use the latest completed bar at entry time. "
            "Trend is UP when that close is above its 20-bar simple moving average, "
            "DOWN when below, and FLAT when equal. BUY/LONG aligned with UP and "
            "SELL/SHORT aligned with DOWN are tagged WITH_TREND; the opposite side is "
            "AGAINST_TREND."
        ),
        "data_scope_note": (
            "T12 exported M5/H1/H4/D1 bars. This T16 analysis scores H1 and H4, per the "
            "requested with-trend vs against-trend split; D1 coverage is recorded as "
            "context and is not used for a trading rule."
        ),
        "row_counts": {
            "actual_trade_rows": len(raw_rows),
            "closed_duplicate_hidden_rows": len(closed_kept),
            "trend_tags": len(trend_rows),
            "resolved_trend_tags": len(resolved_rows),
            "unresolved_trend_tags": len(trend_rows) - len(resolved_rows),
        },
        "bar_coverage": {
            timeframe: _bar_coverage(symbol_bars)
            for timeframe, symbol_bars in bars_by_timeframe.items()
        },
        "d1_bar_coverage": _bar_coverage(_load_bars(bars_dir, "D1")),
        "overall_by_timeframe_alignment": _group_summaries(resolved_rows, ["timeframe", "trend_alignment"]),
        "by_family_timeframe_alignment": _group_summaries(
            resolved_rows,
            ["family", "timeframe", "trend_alignment"],
        ),
        "by_candidate_timeframe_alignment": _group_summaries(
            resolved_rows,
            ["candidate", "timeframe", "trend_alignment"],
        ),
        "unresolved_by_reason": _group_summaries(
            [row for row in trend_rows if row["trend_status"] != "RESOLVED"],
            ["timeframe", "trend_status"],
        ),
        "findings": _findings(resolved_rows),
    }

    output_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    output_doc.write_text(_render_markdown(payload), encoding="utf-8")
    return MtfTrendAlignmentOutput(
        status=status,
        markdown_path=output_doc,
        json_path=output_json,
        closed_kept_rows=len(closed_kept),
        resolved_tags=len(resolved_rows),
    )


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def _load_bars(bars_dir: Path, timeframe: str) -> dict[str, list[dict[str, Any]]]:
    bars_by_symbol: dict[str, list[dict[str, Any]]] = {}
    if not bars_dir.exists():
        return bars_by_symbol
    for path in sorted(bars_dir.glob(f"*_{timeframe}_*.csv")):
        rows: list[dict[str, Any]] = []
        for row in _read_csv(path):
            start = _parse_dt(row.get("bar_start_utc"))
            end = _parse_dt(row.get("bar_end_utc"))
            close = _to_float(row.get("close"))
            if start is None or end is None or close is None:
                continue
            rows.append(
                {
                    "bar_start_utc": start,
                    "bar_end_utc": end,
                    "close": close,
                    "symbol": str(row.get("symbol", path.name.split("_")[0])).upper(),
                    "timeframe": timeframe,
                }
            )
        if rows:
            symbol = str(rows[0]["symbol"]).upper()
            bars_by_symbol[symbol] = sorted(rows, key=lambda item: item["bar_end_utc"])
    return bars_by_symbol


def _normalize_trade(row: dict[str, str]) -> dict[str, Any]:
    enriched: dict[str, Any] = dict(row)
    enriched["profit_value"] = _to_float(row.get("profit_aed")) or 0.0
    enriched["is_duplicate_bool"] = _truthy(row.get("is_duplicate"))
    enriched["entry_dt"] = _parse_dt(row.get("entry_time"))
    enriched["family"] = _family(str(row.get("candidate", "")))
    enriched["direction_norm"] = _direction_norm(row.get("direction"))
    return enriched


def _trend_row(
    row: dict[str, Any],
    timeframe: str,
    bars_by_symbol: dict[str, list[dict[str, Any]]],
) -> dict[str, Any]:
    output = {
        "entry_time": row.get("entry_time", ""),
        "candidate": row.get("candidate", ""),
        "family": row.get("family", ""),
        "symbol": str(row.get("symbol", "")).upper(),
        "direction": row.get("direction", ""),
        "timeframe": timeframe,
        "state": row.get("state", ""),
        "profit_value": row.get("profit_value", 0.0),
        "position_ticket": row.get("position_ticket", ""),
    }
    entry_dt = row.get("entry_dt")
    direction = row.get("direction_norm")
    if not isinstance(entry_dt, datetime):
        return _unresolved(output, "UNRESOLVED_BAD_ENTRY_TIME")
    if direction not in {"BUY", "SELL"}:
        return _unresolved(output, "UNRESOLVED_UNKNOWN_DIRECTION")
    trend = _compute_trend(bars_by_symbol.get(output["symbol"], []), entry_dt)
    if trend is None:
        return _unresolved(output, "UNRESOLVED_NO_BAR_CONTEXT")
    close, sma20, trend_direction, bar_end = trend
    alignment = _alignment(direction, trend_direction)
    output.update(
        {
            "trend_status": "RESOLVED",
            "bar_end_utc": bar_end.strftime("%Y-%m-%d %H:%M:%S"),
            "trend_close": _fmt(close),
            "trend_sma20": _fmt(sma20),
            "trend_direction": trend_direction,
            "trend_alignment": alignment,
        }
    )
    return output


def _compute_trend(
    bars: list[dict[str, Any]],
    entry_dt: datetime,
) -> tuple[float, float, str, datetime] | None:
    if len(bars) < SMA_PERIOD:
        return None
    ends = [bar["bar_end_utc"] for bar in bars]
    index = bisect.bisect_right(ends, entry_dt) - 1
    if index < SMA_PERIOD - 1:
        return None
    window = bars[index - SMA_PERIOD + 1 : index + 1]
    close = float(bars[index]["close"])
    sma20 = sum(float(bar["close"]) for bar in window) / SMA_PERIOD
    if close > sma20:
        direction = "UP"
    elif close < sma20:
        direction = "DOWN"
    else:
        direction = "FLAT"
    return close, sma20, direction, bars[index]["bar_end_utc"]


def _unresolved(row: dict[str, Any], status: str) -> dict[str, Any]:
    row.update(
        {
            "trend_status": status,
            "bar_end_utc": "",
            "trend_close": "",
            "trend_sma20": "",
            "trend_direction": "UNRESOLVED",
            "trend_alignment": "UNRESOLVED",
        }
    )
    return row


def _alignment(direction: str, trend_direction: str) -> str:
    if trend_direction == "FLAT":
        return "FLAT_TREND"
    if direction == "BUY" and trend_direction == "UP":
        return "WITH_TREND"
    if direction == "SELL" and trend_direction == "DOWN":
        return "WITH_TREND"
    return "AGAINST_TREND"


def _group_summaries(rows: list[dict[str, Any]], keys: list[str]) -> list[dict[str, Any]]:
    groups: dict[tuple[str, ...], list[dict[str, Any]]] = {}
    for row in rows:
        key = tuple(str(row.get(field, "") or "UNKNOWN") for field in keys)
        groups.setdefault(key, []).append(row)
    output = []
    for key, items in groups.items():
        summary = _summarize(items)
        for field, value in zip(keys, key):
            summary[field] = value
        output.append(summary)
    return sorted(output, key=lambda item: (str(item.get(keys[0], "")), float(item["closed_pnl_aed"])))


def _summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    closed = [row for row in rows if row.get("state") == "CLOSED"]
    wins = [row for row in closed if float(row.get("profit_value", 0.0)) > 0.0]
    losses = [row for row in closed if float(row.get("profit_value", 0.0)) < 0.0]
    gross_win = sum(float(row.get("profit_value", 0.0)) for row in wins)
    gross_loss = sum(float(row.get("profit_value", 0.0)) for row in losses)
    pnl = sum(float(row.get("profit_value", 0.0)) for row in closed)
    return {
        "total": len(rows),
        "closed": len(closed),
        "wins": len(wins),
        "losses": len(losses),
        "win_rate_pct": round(len(wins) / len(closed) * 100.0, 2) if closed else None,
        "closed_pnl_aed": round(pnl, 2),
        "profit_factor": round(gross_win / abs(gross_loss), 2) if gross_loss else ("inf" if gross_win else None),
        "avg_win_aed": round(gross_win / len(wins), 2) if wins else None,
        "avg_loss_aed": round(gross_loss / len(losses), 2) if losses else None,
    }


def _bar_coverage(symbol_bars: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    output = []
    for symbol, rows in sorted(symbol_bars.items()):
        if not rows:
            continue
        output.append(
            {
                "symbol": symbol,
                "rows": len(rows),
                "first_bar_end_utc": rows[0]["bar_end_utc"].strftime("%Y-%m-%d %H:%M:%S"),
                "last_bar_end_utc": rows[-1]["bar_end_utc"].strftime("%Y-%m-%d %H:%M:%S"),
            }
        )
    return output


def _findings(rows: list[dict[str, Any]]) -> list[str]:
    findings: list[str] = []
    overall = _group_summaries(rows, ["timeframe", "trend_alignment"])
    for timeframe in TREND_TIMEFRAMES:
        with_rows = next(
            (row for row in overall if row.get("timeframe") == timeframe and row.get("trend_alignment") == "WITH_TREND"),
            None,
        )
        against_rows = next(
            (row for row in overall if row.get("timeframe") == timeframe and row.get("trend_alignment") == "AGAINST_TREND"),
            None,
        )
        if with_rows and against_rows:
            delta = round(float(with_rows["closed_pnl_aed"]) - float(against_rows["closed_pnl_aed"]), 2)
            findings.append(
                f"{timeframe}: WITH_TREND minus AGAINST_TREND closed PnL delta = {delta} AED "
                f"({with_rows['closed']} with-trend tags vs {against_rows['closed']} against-trend tags)."
            )
    if not findings:
        findings.append("No resolved with-vs-against trend comparison was available.")
    findings.append(
        "No EA code change is implied by this report; any shared trend-context guard needs a separate "
        "pre-registered hypothesis and forward test."
    )
    return findings


def _family(candidate: str) -> str:
    if candidate in ROUND_RETEST_CANDIDATES:
        return "round_retest_family"
    if candidate in SESSION_EXTREME_CANDIDATES:
        return "session_extreme_family"
    if candidate in BREAKOUT_CANDIDATES:
        return "breakout_retest_family"
    if candidate.startswith("WR50_"):
        return "wr50_family"
    return "other_family"


def _direction_norm(value: Any) -> str:
    text = str(value or "").upper()
    if text in {"BUY", "LONG"}:
        return "BUY"
    if text in {"SELL", "SHORT"}:
        return "SELL"
    return "UNKNOWN"


def _render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Multi-Timeframe Trend Alignment Report - 2026-06-13",
        "",
        f"Status: **{payload['status']}**",
        "",
        "## Boundary",
        "",
        str(payload["boundary"]),
        "",
        "## Trend Definition",
        "",
        str(payload["trend_definition"]),
        "",
        str(payload["data_scope_note"]),
        "",
        "## Sources",
        "",
        f"- Actual broker trades: `{payload['source_actual_trades_csv']}`",
        f"- H1/H4 bars: `{payload['source_bars_dir']}`",
        "",
        "## Row Counts",
        "",
        _key_value_table(payload["row_counts"]),
        "",
        "## Bar Coverage",
        "",
    ]
    for timeframe, rows in payload["bar_coverage"].items():
        lines.extend([f"### {timeframe}", "", _coverage_table(rows), ""])
    lines.extend(["### D1 Context", "", _coverage_table(payload["d1_bar_coverage"]), ""])
    lines.extend(
        [
            "## Overall Alignment",
            "",
            _breakdown_table(payload["overall_by_timeframe_alignment"]),
            "",
            "## Family Alignment",
            "",
            _breakdown_table(payload["by_family_timeframe_alignment"]),
            "",
            "## Candidate Alignment",
            "",
            _breakdown_table(payload["by_candidate_timeframe_alignment"]),
            "",
            "## Unresolved Context",
            "",
            _breakdown_table(payload["unresolved_by_reason"]),
            "",
            "## Findings",
            "",
        ]
    )
    lines.extend(f"- {finding}" for finding in payload["findings"])
    lines.append("")
    return "\n".join(lines)


def _key_value_table(values: dict[str, Any]) -> str:
    lines = ["| Field | Value |", "|---|---:|"]
    for key, value in values.items():
        lines.append(f"| {key} | {value} |")
    return "\n".join(lines)


def _coverage_table(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return "_No bars loaded._"
    lines = [
        "| Symbol | Rows | First Bar End UTC | Last Bar End UTC |",
        "|---|---:|---|---|",
    ]
    for row in rows:
        lines.append(
            f"| {row['symbol']} | {row['rows']} | {row['first_bar_end_utc']} | {row['last_bar_end_utc']} |"
        )
    return "\n".join(lines)


def _breakdown_table(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return "_No rows._"
    metric_fields = {
        "total",
        "closed",
        "wins",
        "losses",
        "win_rate_pct",
        "closed_pnl_aed",
        "profit_factor",
        "avg_win_aed",
        "avg_loss_aed",
    }
    key_fields = [field for field in rows[0].keys() if field not in metric_fields]
    lines = [
        "| " + " | ".join(key_fields + ["Closed", "Wins", "Losses", "WR", "PnL AED", "PF"]) + " |",
        "|" + "|".join(["---"] * len(key_fields) + ["---:"] * 6) + "|",
    ]
    for row in rows:
        key_values = [str(row.get(field, "")) for field in key_fields]
        metric_values = [
            str(row.get("closed", "")),
            str(row.get("wins", "")),
            str(row.get("losses", "")),
            _fmt_cell(row.get("win_rate_pct")),
            _fmt_cell(row.get("closed_pnl_aed")),
            _fmt_cell(row.get("profit_factor")),
        ]
        lines.append("| " + " | ".join(key_values + metric_values) + " |")
    return "\n".join(lines)


def _parse_dt(value: Any) -> datetime | None:
    text = str(value or "").strip().replace("T", " ").replace("Z", "")
    if not text:
        return None
    text = text.replace(".", "-")
    try:
        return datetime.strptime(text[:19], "%Y-%m-%d %H:%M:%S")
    except ValueError:
        return None


def _truthy(value: Any) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def _to_float(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _fmt(value: float) -> str:
    return f"{value:.6f}".rstrip("0").rstrip(".")


def _fmt_cell(value: Any) -> str:
    if value is None:
        return "n/a"
    if isinstance(value, float):
        return f"{value:.2f}"
    return str(value)


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate multi-timeframe trend alignment research.")
    parser.add_argument("--phase1-root", type=Path, default=Path.cwd())
    parser.add_argument("--actual-trades-csv", type=Path)
    parser.add_argument("--bars-dir", type=Path)
    parser.add_argument("--output-doc", type=Path)
    parser.add_argument("--output-json", type=Path)
    args = parser.parse_args()
    output = generate_mtf_trend_alignment_report(
        args.phase1_root,
        actual_trades_csv=args.actual_trades_csv,
        bars_dir=args.bars_dir,
        output_doc=args.output_doc,
        output_json=args.output_json,
    )
    print(f"{output.status}: {output.markdown_path} ({output.resolved_tags} resolved tags)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
