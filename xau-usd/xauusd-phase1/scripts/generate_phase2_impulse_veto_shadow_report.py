from __future__ import annotations

import argparse
import bisect
import csv
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEFAULT_ACTUAL_TRADES = Path("outputs") / "reports" / "PHASE2_DEMO_ACTUAL_BROKER_TRADES.csv"
DEFAULT_BARS_DIR = Path("outputs") / "reports" / "m5_replay_bars"
DEFAULT_OUTPUT_JSON = Path("outputs") / "reports" / "PHASE2_IMPULSE_VETO_SHADOW_REPORT.json"
DEFAULT_OUTPUT_MD = Path("outputs") / "reports" / "PHASE2_IMPULSE_VETO_SHADOW_REPORT.md"
DEFAULT_OUTPUT_CSV = Path("outputs") / "reports" / "PHASE2_IMPULSE_VETO_SHADOW_ROWS.csv"

THRESHOLDS = (-1.0, -1.5, -2.0)
TARGET_FAMILIES = {"round_retest_family", "session_extreme_family"}

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
class ImpulseVetoOutput:
    status: str
    json_path: Path
    markdown_path: Path
    rows_csv_path: Path
    resolved_closed_rows: int


def generate_phase2_impulse_veto_shadow_report(
    phase1_root: Path,
    actual_trades_csv: Path | None = None,
    bars_dir: Path | None = None,
    output_json: Path | None = None,
) -> ImpulseVetoOutput:
    phase1_root = phase1_root.resolve()
    actual_trades_csv = (actual_trades_csv or phase1_root / DEFAULT_ACTUAL_TRADES).resolve()
    bars_dir = (bars_dir or phase1_root / DEFAULT_BARS_DIR).resolve()
    output_json = (output_json or phase1_root / DEFAULT_OUTPUT_JSON).resolve()
    output_md = output_json.with_suffix(".md") if output_json.name != DEFAULT_OUTPUT_JSON.name else phase1_root / DEFAULT_OUTPUT_MD
    rows_csv = output_json.with_suffix(".csv") if output_json.name != DEFAULT_OUTPUT_JSON.name else phase1_root / DEFAULT_OUTPUT_CSV
    output_json.parent.mkdir(parents=True, exist_ok=True)

    bars_by_symbol = _load_bars(bars_dir)
    raw_rows = [_normalize_trade(row) for row in _read_csv(actual_trades_csv)]
    enriched_rows = [_add_impulse(row, bars_by_symbol) for row in raw_rows]
    closed_resolved = [
        row
        for row in enriched_rows
        if row.get("state") == "CLOSED" and row.get("impulse_status") == "RESOLVED"
    ]
    target_rows = [row for row in closed_resolved if row.get("family") in TARGET_FAMILIES]
    status = "SHADOW_READY" if closed_resolved and target_rows else "INSUFFICIENT_DATA"
    payload = {
        "status": status,
        "created_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "authority": (
            "Shadow-only impulse-veto evidence. Reads broker-trade CSV and exported M5 bars only; "
            "does not read or modify terminals, charts, presets, orders, positions, or running EAs."
        ),
        "source_actual_trades_csv": str(actual_trades_csv),
        "source_bars_dir": str(bars_dir),
        "hypothesis_doc": "docs/FORWARD_WEEK_IMPULSE_VETO_HYPOTHESIS_2026_06_15.md",
        "thresholds": list(THRESHOLDS),
        "target_families": sorted(TARGET_FAMILIES),
        "non_target_policy": "breakout_retest family is scored as a control and is not blocked by this shadow rule.",
        "row_counts": {
            "raw_rows": len(raw_rows),
            "closed_rows": sum(1 for row in enriched_rows if row.get("state") == "CLOSED"),
            "resolved_closed_rows": len(closed_resolved),
            "target_resolved_closed_rows": len(target_rows),
            "unresolved_rows": sum(1 for row in enriched_rows if row.get("impulse_status") != "RESOLVED"),
        },
        "bar_quality": _bar_quality(bars_by_symbol),
        "dose_response_all": _dose_response(closed_resolved),
        "dose_response_by_family": _dose_response_by(closed_resolved, "family"),
        "threshold_scoreboard": _threshold_scoreboard(target_rows),
        "threshold_scoreboard_by_family": _threshold_scoreboard_by(target_rows, "family"),
        "threshold_scoreboard_by_candidate": _threshold_scoreboard_by(target_rows, "candidate"),
        "breakout_control": _summarize([row for row in closed_resolved if row.get("family") == "breakout_retest_family"]),
        "notes": [
            "ret12_atr = (last closed M5 close - close 12 completed M5 bars earlier) / ATR14.",
            "impulse_alignment = direction_sign * ret12_atr; negative values mean the trade fights the latest impulse.",
            "Thresholds are pre-registered for weak families only: round_retest_family and session_extreme_family.",
            "Open trades are enriched in the row CSV but excluded from threshold PnL scoreboards.",
            "Duplicate rows are retained in the raw row export; scoreboard rows also include duplicate-hidden summaries.",
        ],
    }

    _write_csv(rows_csv, enriched_rows, _row_fields())
    output_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    output_md.write_text(_render_markdown(payload), encoding="utf-8")
    return ImpulseVetoOutput(status, output_json, output_md, rows_csv, len(closed_resolved))


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def _write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def _normalize_trade(row: dict[str, str]) -> dict[str, Any]:
    enriched: dict[str, Any] = dict(row)
    enriched["family"] = _family(str(row.get("candidate", "")))
    enriched["profit_value"] = _to_float(row.get("profit_aed")) or 0.0
    enriched["direction_sign"] = _direction_sign(row.get("direction"))
    enriched["is_duplicate_bool"] = _truthy(row.get("is_duplicate"))
    enriched["time_bucket"] = row.get("time_bucket") or _time_bucket(row.get("entry_time", ""))
    return enriched


def _add_impulse(row: dict[str, Any], bars_by_symbol: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    enriched = dict(row)
    symbol = str(row.get("symbol", "")).upper()
    bars = bars_by_symbol.get(symbol, [])
    direction_sign = row.get("direction_sign")
    entry_dt = _parse_dt(row.get("entry_time"))
    if direction_sign is None:
        return _unresolved(enriched, "UNRESOLVED_UNKNOWN_DIRECTION")
    if entry_dt is None:
        return _unresolved(enriched, "UNRESOLVED_BAD_ENTRY_TIME")
    impulse = _compute_impulse(bars, entry_dt)
    if impulse is None:
        return _unresolved(enriched, "UNRESOLVED_NO_BAR_CONTEXT")
    ret12_atr, atr14, closed_bar_time = impulse
    alignment = direction_sign * ret12_atr
    enriched.update(
        {
            "impulse_status": "RESOLVED",
            "ret12_atr": _fmt(ret12_atr),
            "atr14_m5": _fmt(atr14),
            "impulse_alignment": _fmt(alignment),
            "impulse_bucket": _impulse_bucket(alignment),
            "impulse_closed_bar_utc": closed_bar_time.strftime("%Y-%m-%d %H:%M:%S"),
        }
    )
    for threshold in THRESHOLDS:
        key = _threshold_key(threshold)
        blocked = row.get("family") in TARGET_FAMILIES and alignment < threshold
        enriched[f"{key}_shadow_action"] = "BLOCK" if blocked else "KEEP"
    return enriched


def _unresolved(row: dict[str, Any], status: str) -> dict[str, Any]:
    row.update(
        {
            "impulse_status": status,
            "ret12_atr": "",
            "atr14_m5": "",
            "impulse_alignment": "",
            "impulse_bucket": "UNRESOLVED",
            "impulse_closed_bar_utc": "",
        }
    )
    for threshold in THRESHOLDS:
        row[f"{_threshold_key(threshold)}_shadow_action"] = "UNRESOLVED"
    return row


def _load_bars(bars_dir: Path) -> dict[str, list[dict[str, Any]]]:
    bars_by_symbol: dict[str, list[dict[str, Any]]] = {}
    if not bars_dir.exists():
        return bars_by_symbol
    for path in sorted(bars_dir.glob("*_M5_*.csv")):
        rows: list[dict[str, Any]] = []
        for row in _read_csv(path):
            start = _parse_dt(row.get("bar_start_utc"))
            if start is None:
                continue
            rows.append(
                {
                    "bar_start_utc": start,
                    "open": _to_float(row.get("open")) or 0.0,
                    "high": _to_float(row.get("high")) or 0.0,
                    "low": _to_float(row.get("low")) or 0.0,
                    "close": _to_float(row.get("close")) or 0.0,
                    "symbol": str(row.get("symbol", path.name.split("_")[0])).upper(),
                }
            )
        if rows:
            symbol = str(rows[0]["symbol"]).upper()
            bars_by_symbol[symbol] = sorted(rows, key=lambda item: item["bar_start_utc"])
    return bars_by_symbol


def _compute_impulse(bars: list[dict[str, Any]], entry_dt: datetime) -> tuple[float, float, datetime] | None:
    if len(bars) < 30:
        return None
    times = [bar["bar_start_utc"] for bar in bars]
    current_index = bisect.bisect_right(times, entry_dt) - 1
    closed_index = current_index - 1
    if closed_index < 14 or closed_index - 12 < 0:
        return None
    atr = _atr14(bars, closed_index)
    if atr is None or atr <= 0.0:
        return None
    ret12 = (bars[closed_index]["close"] - bars[closed_index - 12]["close"]) / atr
    return ret12, atr, bars[closed_index]["bar_start_utc"]


def _atr14(bars: list[dict[str, Any]], closed_index: int) -> float | None:
    first = closed_index - 13
    if first <= 0:
        return None
    trs = []
    for index in range(first, closed_index + 1):
        high = float(bars[index]["high"])
        low = float(bars[index]["low"])
        previous_close = float(bars[index - 1]["close"])
        trs.append(max(high - low, abs(high - previous_close), abs(low - previous_close)))
    return sum(trs) / len(trs) if trs else None


def _dose_response(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    buckets = [
        "hard_against_lt_-1_5",
        "mild_against_-1_5_to_-0_5",
        "fresh_flat_abs_lt_0_5",
        "mild_with_0_5_to_1_5",
        "extended_with_gt_1_5",
    ]
    return [{"bucket": bucket, **_summarize([row for row in rows if row.get("impulse_bucket") == bucket])} for bucket in buckets]


def _dose_response_by(rows: list[dict[str, Any]], field: str) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for value in sorted({str(row.get(field, "")) for row in rows}):
        if not value:
            continue
        for bucket_row in _dose_response([row for row in rows if str(row.get(field, "")) == value]):
            result.append({field: value, **bucket_row})
    return result


def _threshold_scoreboard(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result = []
    for threshold in THRESHOLDS:
        blocked = [row for row in rows if (_to_float(row.get("impulse_alignment")) or 0.0) < threshold]
        kept = [row for row in rows if (_to_float(row.get("impulse_alignment")) or 0.0) >= threshold]
        hidden_rows = [row for row in rows if not bool(row.get("is_duplicate_bool"))]
        hidden_blocked = [row for row in blocked if not bool(row.get("is_duplicate_bool"))]
        hidden_kept = [row for row in kept if not bool(row.get("is_duplicate_bool"))]
        result.append(
            {
                "threshold": threshold,
                "scope": "raw_all_target_rows",
                "baseline": _summarize(rows),
                "kept": _summarize(kept),
                "blocked": _summarize(blocked),
                "shadow_net_delta_aed": _fmt(_pnl(kept) - _pnl(rows)),
                "kept_share_pct": _fmt_pct(len(kept), len(rows)),
                "duplicate_hidden_baseline": _summarize(hidden_rows),
                "duplicate_hidden_kept": _summarize(hidden_kept),
                "duplicate_hidden_blocked": _summarize(hidden_blocked),
                "duplicate_hidden_shadow_net_delta_aed": _fmt(_pnl(hidden_kept) - _pnl(hidden_rows)),
                "duplicate_hidden_kept_share_pct": _fmt_pct(len(hidden_kept), len(hidden_rows)),
            }
        )
    return result


def _threshold_scoreboard_by(rows: list[dict[str, Any]], field: str) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for value in sorted({str(row.get(field, "")) for row in rows}):
        if not value:
            continue
        for row in _threshold_scoreboard([item for item in rows if str(item.get(field, "")) == value]):
            result.append({field: value, **row})
    return result


def _summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    closed = [row for row in rows if row.get("state") == "CLOSED"]
    wins = [row for row in closed if float(row.get("profit_value", 0.0)) > 0.0]
    losses = [row for row in closed if float(row.get("profit_value", 0.0)) < 0.0]
    gross_win = sum(float(row.get("profit_value", 0.0)) for row in wins)
    gross_loss = sum(float(row.get("profit_value", 0.0)) for row in losses)
    pnl = sum(float(row.get("profit_value", 0.0)) for row in closed)
    return {
        "closed": len(closed),
        "wins": len(wins),
        "losses": len(losses),
        "win_rate_pct": _fmt_pct(len(wins), len(closed)),
        "closed_pnl_aed": _fmt(pnl),
        "avg_pnl_aed": _fmt(pnl / len(closed)) if closed else "n/a",
        "profit_factor": _fmt(gross_win / abs(gross_loss)) if gross_loss else ("inf" if gross_win else "n/a"),
    }


def _pnl(rows: list[dict[str, Any]]) -> float:
    return sum(float(row.get("profit_value", 0.0)) for row in rows if row.get("state") == "CLOSED")


def _bar_quality(bars_by_symbol: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    rows = []
    for symbol, bars in sorted(bars_by_symbol.items()):
        times = [bar["bar_start_utc"] for bar in bars]
        gap_count = 0
        max_gap_minutes = 0.0
        duplicate_times = len(times) - len(set(times))
        for left, right in zip(times, times[1:]):
            gap = (right - left).total_seconds() / 60.0
            if gap > 5.0:
                gap_count += 1
                max_gap_minutes = max(max_gap_minutes, gap)
        rows.append(
            {
                "symbol": symbol,
                "rows": len(bars),
                "first_bar_utc": times[0].strftime("%Y-%m-%d %H:%M:%S") if times else "",
                "last_bar_utc": times[-1].strftime("%Y-%m-%d %H:%M:%S") if times else "",
                "gap_count_gt_5m": gap_count,
                "max_gap_minutes": _fmt(max_gap_minutes),
                "duplicate_bar_times": duplicate_times,
                "status": "PASS" if bars and duplicate_times == 0 and gap_count == 0 else "WARN_GAPS_OR_DUPLICATES",
            }
        )
    return rows


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


def _direction_sign(direction: Any) -> int | None:
    text = str(direction or "").strip().upper()
    if text in {"BUY", "LONG"}:
        return 1
    if text in {"SELL", "SHORT"}:
        return -1
    return None


def _impulse_bucket(value: float) -> str:
    if value < -1.5:
        return "hard_against_lt_-1_5"
    if value < -0.5:
        return "mild_against_-1_5_to_-0_5"
    if value <= 0.5:
        return "fresh_flat_abs_lt_0_5"
    if value <= 1.5:
        return "mild_with_0_5_to_1_5"
    return "extended_with_gt_1_5"


def _parse_dt(value: Any) -> datetime | None:
    text = str(value or "").strip().replace("T", " ").replace("Z", "")
    if not text:
        return None
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y.%m.%d %H:%M:%S"):
        try:
            return datetime.strptime(text[:19], fmt)
        except ValueError:
            continue
    return None


def _time_bucket(entry_time: Any) -> str:
    parsed = _parse_dt(entry_time)
    if parsed is None:
        return "UNKNOWN"
    hour = parsed.hour
    if hour >= 20 or hour < 6:
        return "Night 20:00-05:59"
    if hour < 12:
        return "Morning 06:00-11:59"
    if hour < 16:
        return "Afternoon 12:00-15:59"
    return "Evening 16:00-19:59"


def _to_float(value: Any) -> float | None:
    try:
        text = str(value).strip()
        if text == "" or text.lower() == "n/a":
            return None
        return float(text)
    except (TypeError, ValueError):
        return None


def _truthy(value: Any) -> bool:
    return str(value or "").strip().lower() in {"true", "1", "yes"}


def _fmt(value: float) -> str:
    return f"{value:.4f}"


def _fmt_pct(numerator: int, denominator: int) -> str:
    return f"{(numerator / denominator * 100.0):.2f}" if denominator else "n/a"


def _threshold_key(threshold: float) -> str:
    return f"lt_{str(threshold).replace('-', 'neg_').replace('.', '_')}"


def _row_fields() -> list[str]:
    return [
        "entry_time",
        "exit_time",
        "candidate",
        "family",
        "status",
        "symbol",
        "direction",
        "volume",
        "state",
        "profit_aed",
        "position_ticket",
        "duplicate_key",
        "duplicate_role",
        "is_duplicate",
        "time_bucket",
        "impulse_status",
        "impulse_closed_bar_utc",
        "ret12_atr",
        "atr14_m5",
        "impulse_alignment",
        "impulse_bucket",
        *[f"{_threshold_key(threshold)}_shadow_action" for threshold in THRESHOLDS],
    ]


def _render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Phase 2 Impulse Veto Shadow Report",
        "",
        f"Status: `{payload['status']}`",
        "",
        str(payload["authority"]),
        "",
        "## Boundary",
        "",
        "- Shadow-only analysis.",
        "- No terminal, chart, preset, order, position, or running-EA changes.",
        "- Applies only to weak families: `round_retest_family` and `session_extreme_family`.",
        "- `breakout_retest_family` is scored as a control and is not blocked by this rule.",
        "",
        "## Sources",
        "",
        f"- Actual trades CSV: `{payload['source_actual_trades_csv']}`",
        f"- M5 bars dir: `{payload['source_bars_dir']}`",
        f"- Hypothesis doc: `{payload['hypothesis_doc']}`",
        "",
        "## Row Counts",
        "",
        _dict_table(payload["row_counts"]),
        "",
        "## Bar Export Quality",
        "",
        _table(payload["bar_quality"], ["symbol", "status", "rows", "first_bar_utc", "last_bar_utc", "gap_count_gt_5m", "max_gap_minutes", "duplicate_bar_times"]),
        "",
        "## Dose Response - All Resolved Closed Rows",
        "",
        _table(payload["dose_response_all"], ["bucket", "closed", "wins", "losses", "win_rate_pct", "closed_pnl_aed", "avg_pnl_aed", "profit_factor"]),
        "",
        "## Threshold Scoreboard - Target Families",
        "",
        _threshold_table(payload["threshold_scoreboard"]),
        "",
        "## Threshold Scoreboard By Family",
        "",
        _threshold_by_table(payload["threshold_scoreboard_by_family"], "family"),
        "",
        "## Breakout Control",
        "",
        _dict_table(payload["breakout_control"]),
        "",
        "## Notes",
        "",
        *[f"- {note}" for note in payload["notes"]],
        "",
    ]
    return "\n".join(lines)


def _dict_table(row: dict[str, Any]) -> str:
    lines = ["| Metric | Value |", "|---|---:|"]
    for key, value in row.items():
        lines.append(f"| {key} | {value} |")
    return "\n".join(lines)


def _table(rows: list[dict[str, Any]], fields: list[str]) -> str:
    if not rows:
        return "_No rows._"
    lines = ["| " + " | ".join(fields) + " |", "|" + "|".join(["---"] * len(fields)) + "|"]
    for row in rows:
        lines.append("| " + " | ".join(str(row.get(field, "")) for field in fields) + " |")
    return "\n".join(lines)


def _threshold_table(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return "_No rows._"
    lines = [
        "| Threshold | Baseline PnL | Kept PnL | Blocked PnL | Delta | Kept Share | Dedup Baseline | Dedup Kept | Dedup Blocked | Dedup Delta |",
        "|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        lines.append(
            "| "
            + " | ".join(
                [
                    str(row["threshold"]),
                    str(row["baseline"]["closed_pnl_aed"]),
                    str(row["kept"]["closed_pnl_aed"]),
                    str(row["blocked"]["closed_pnl_aed"]),
                    str(row["shadow_net_delta_aed"]),
                    str(row["kept_share_pct"]),
                    str(row["duplicate_hidden_baseline"]["closed_pnl_aed"]),
                    str(row["duplicate_hidden_kept"]["closed_pnl_aed"]),
                    str(row["duplicate_hidden_blocked"]["closed_pnl_aed"]),
                    str(row["duplicate_hidden_shadow_net_delta_aed"]),
                ]
            )
            + " |"
        )
    return "\n".join(lines)


def _threshold_by_table(rows: list[dict[str, Any]], field: str) -> str:
    if not rows:
        return "_No rows._"
    lines = [
        f"| {field} | Threshold | Closed | Kept | Blocked | Baseline PnL | Kept PnL | Blocked PnL | Delta |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        lines.append(
            "| "
            + " | ".join(
                [
                    str(row.get(field, "")),
                    str(row["threshold"]),
                    str(row["baseline"]["closed"]),
                    str(row["kept"]["closed"]),
                    str(row["blocked"]["closed"]),
                    str(row["baseline"]["closed_pnl_aed"]),
                    str(row["kept"]["closed_pnl_aed"]),
                    str(row["blocked"]["closed_pnl_aed"]),
                    str(row["shadow_net_delta_aed"]),
                ]
            )
            + " |"
        )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate the Phase 2 impulse-veto shadow report.")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--actual-trades-csv", type=Path, default=None)
    parser.add_argument("--bars-dir", type=Path, default=None)
    parser.add_argument("--output-json", type=Path, default=None)
    args = parser.parse_args()
    output = generate_phase2_impulse_veto_shadow_report(
        args.root,
        actual_trades_csv=args.actual_trades_csv,
        bars_dir=args.bars_dir,
        output_json=args.output_json,
    )
    print(f"Status: {output.status}")
    print(f"JSON: {output.json_path}")
    print(f"Markdown: {output.markdown_path}")
    print(f"Rows CSV: {output.rows_csv_path}")
    print(f"Resolved closed rows: {output.resolved_closed_rows}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
