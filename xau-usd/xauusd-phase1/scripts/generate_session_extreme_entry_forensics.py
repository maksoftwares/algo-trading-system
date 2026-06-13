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
DEFAULT_IMPULSE_ROWS = Path("outputs") / "reports" / "PHASE2_IMPULSE_VETO_SHADOW_ROWS.csv"
DEFAULT_BARS_DIR = Path("outputs") / "reports" / "m5_replay_bars"
DEFAULT_OUTPUT_DOC = Path("docs") / "SESSION_EXTREME_ENTRY_FORENSICS_2026_06_13.md"
DEFAULT_OUTPUT_JSON = Path("outputs") / "reports" / "SESSION_EXTREME_ENTRY_FORENSICS_2026_06_13.json"

SESSION_EXTREME_CANDIDATE = "session_extreme_retest_v0"


@dataclass(frozen=True)
class SessionExtremeForensicsOutput:
    status: str
    markdown_path: Path
    json_path: Path
    exact_duplicate_hidden_rows: int
    clone_rows: int


def generate_session_extreme_entry_forensics(
    phase1_root: Path,
    actual_trades_csv: Path | None = None,
    impulse_rows_csv: Path | None = None,
    bars_dir: Path | None = None,
    output_doc: Path | None = None,
    output_json: Path | None = None,
) -> SessionExtremeForensicsOutput:
    phase1_root = phase1_root.resolve()
    actual_trades_csv = (actual_trades_csv or phase1_root / DEFAULT_ACTUAL_TRADES).resolve()
    impulse_rows_csv = (impulse_rows_csv or phase1_root / DEFAULT_IMPULSE_ROWS).resolve()
    bars_dir = (bars_dir or phase1_root / DEFAULT_BARS_DIR).resolve()
    output_doc = (output_doc or phase1_root / DEFAULT_OUTPUT_DOC).resolve()
    output_json = (output_json or phase1_root / DEFAULT_OUTPUT_JSON).resolve()
    output_doc.parent.mkdir(parents=True, exist_ok=True)
    output_json.parent.mkdir(parents=True, exist_ok=True)

    actual_rows = [_normalize_trade(row) for row in _read_csv(actual_trades_csv)]
    impulse_by_ticket = {
        str(row.get("position_ticket", "")).strip(): row
        for row in _read_csv(impulse_rows_csv)
        if str(row.get("position_ticket", "")).strip()
    }
    bars_by_symbol = _load_m5_bars(bars_dir)

    exact_rows = [row for row in actual_rows if row.get("candidate") == SESSION_EXTREME_CANDIDATE]
    exact_keys = {row.get("duplicate_key") for row in exact_rows if row.get("duplicate_key")}
    clone_rows = [
        row
        for row in actual_rows
        if row.get("duplicate_key") in exact_keys and row.get("candidate") != SESSION_EXTREME_CANDIDATE
    ]
    exact_enriched = [
        _enrich_forensics_row(row, "SESSION_EXACT", impulse_by_ticket, bars_by_symbol)
        for row in exact_rows
    ]
    clone_enriched = [
        _enrich_forensics_row(row, "DUPLICATE_CLONE", impulse_by_ticket, bars_by_symbol)
        for row in clone_rows
    ]
    exact_duplicate_hidden = [row for row in exact_enriched if not row["is_duplicate_bool"]]
    clone_inclusive_rows = exact_enriched + clone_enriched
    clone_inclusive_duplicate_hidden = [
        row for row in clone_inclusive_rows if not row["is_duplicate_bool"]
    ]

    status = "FORENSICS_READY" if exact_duplicate_hidden else "INSUFFICIENT_DATA"
    payload = {
        "status": status,
        "generated_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "boundary": (
            "Research report only. No EA-T3 code, no presets, no chart changes, no orders, "
            "and no canonical Phase 2 or live-readiness change. Magic band 933200-933299 "
            "remains reserved but unused."
        ),
        "source_actual_trades_csv": str(actual_trades_csv),
        "source_impulse_rows_csv": str(impulse_rows_csv),
        "source_bars_dir": str(bars_dir),
        "candidate": SESSION_EXTREME_CANDIDATE,
        "row_counts": {
            "actual_trade_rows": len(actual_rows),
            "session_extreme_exact_rows": len(exact_enriched),
            "session_extreme_exact_duplicate_hidden_rows": len(exact_duplicate_hidden),
            "same_duplicate_key_clone_rows": len(clone_enriched),
            "clone_inclusive_rows": len(clone_inclusive_rows),
            "clone_inclusive_duplicate_hidden_rows": len(clone_inclusive_duplicate_hidden),
        },
        "summaries": {
            "session_extreme_exact_raw": _summarize(exact_enriched),
            "session_extreme_exact_duplicate_hidden": _summarize(exact_duplicate_hidden),
            "same_duplicate_key_clones": _summarize(clone_enriched),
            "clone_inclusive_raw": _summarize(clone_inclusive_rows),
            "clone_inclusive_duplicate_hidden": _summarize(clone_inclusive_duplicate_hidden),
        },
        "breakdowns": {
            "time_bucket": _group_summaries(exact_duplicate_hidden, ["time_bucket"]),
            "symbol_direction": _group_summaries(exact_duplicate_hidden, ["symbol", "direction"]),
            "session_extreme_level_type": _group_summaries(exact_duplicate_hidden, ["session_extreme_level_type"]),
            "session_level_availability": _group_summaries(exact_duplicate_hidden, ["session_level_availability"]),
            "impulse_bucket": _group_summaries(exact_duplicate_hidden, ["impulse_bucket"]),
            "impulse_threshold_neg_1_5": _group_summaries(
                exact_duplicate_hidden,
                ["lt_neg_1_5_shadow_action"],
            ),
            "distance_from_session_open_r_bucket": _group_summaries(
                exact_duplicate_hidden,
                ["distance_from_session_open_r_bucket"],
            ),
            "clone_candidates": _group_summaries(clone_enriched, ["candidate"]),
        },
        "worst_clusters": _worst_clusters(exact_duplicate_hidden),
        "observability_gaps": _observability_gaps(exact_duplicate_hidden),
        "candidate_fix_hypothesis": _candidate_fix_hypothesis(exact_duplicate_hidden),
    }

    output_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    output_doc.write_text(_render_markdown(payload), encoding="utf-8")
    return SessionExtremeForensicsOutput(
        status=status,
        markdown_path=output_doc,
        json_path=output_json,
        exact_duplicate_hidden_rows=len(exact_duplicate_hidden),
        clone_rows=len(clone_enriched),
    )


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def _normalize_trade(row: dict[str, str]) -> dict[str, Any]:
    enriched: dict[str, Any] = dict(row)
    enriched["profit_value"] = _to_float(row.get("profit_aed")) or 0.0
    enriched["is_duplicate_bool"] = _truthy(row.get("is_duplicate"))
    enriched["entry_dt"] = _parse_dt(row.get("entry_time"))
    enriched["time_bucket"] = row.get("time_bucket") or _time_bucket(row.get("entry_time", ""))
    enriched["outcome"] = _outcome(enriched)
    return enriched


def _enrich_forensics_row(
    row: dict[str, Any],
    source_group: str,
    impulse_by_ticket: dict[str, dict[str, str]],
    bars_by_symbol: dict[str, list[dict[str, Any]]],
) -> dict[str, Any]:
    enriched = dict(row)
    enriched["source_group"] = source_group
    direction = str(row.get("direction", "")).upper()
    enriched["session_extreme_level_type"] = {
        "BUY": "session_high_retest",
        "LONG": "session_high_retest",
        "SELL": "session_low_retest",
        "SHORT": "session_low_retest",
    }.get(direction, "unknown_level_type")
    entry_dt = row.get("entry_dt")
    minute = entry_dt.hour * 60 + entry_dt.minute if isinstance(entry_dt, datetime) else None
    enriched["session_level_availability"] = _session_level_availability(minute)
    open_context = _session_open_context(row, bars_by_symbol)
    enriched.update(open_context)

    impulse = impulse_by_ticket.get(str(row.get("position_ticket", "")).strip(), {})
    enriched["impulse_status"] = impulse.get("impulse_status", "UNRESOLVED_NO_IMPULSE_ROW")
    enriched["ret12_atr"] = impulse.get("ret12_atr", "")
    enriched["atr14_m5"] = impulse.get("atr14_m5", "")
    enriched["impulse_alignment"] = impulse.get("impulse_alignment", "")
    enriched["impulse_bucket"] = impulse.get("impulse_bucket", "UNRESOLVED")
    enriched["lt_neg_1_5_shadow_action"] = impulse.get("lt_neg_1_5_shadow_action", "UNRESOLVED")
    return enriched


def _session_level_availability(minute: int | None) -> str:
    if minute is None:
        return "unknown"
    if minute >= 13 * 60 + 30:
        return "asia_and_london_levels_available"
    if minute >= 7 * 60:
        return "asia_level_only_available"
    return "pre_07_00_no_session_level_expected_by_source"


def _session_open_context(
    row: dict[str, Any],
    bars_by_symbol: dict[str, list[dict[str, Any]]],
) -> dict[str, Any]:
    entry_dt = row.get("entry_dt")
    entry_price = _to_float(row.get("entry_price"))
    stop_loss = _to_float(row.get("sl"))
    if not isinstance(entry_dt, datetime) or entry_price is None:
        return {
            "session_open_label": "UNRESOLVED",
            "session_open_price": "",
            "distance_from_session_open_price": "",
            "distance_from_session_open_r": "",
            "distance_from_session_open_r_bucket": "UNRESOLVED",
        }
    minute = entry_dt.hour * 60 + entry_dt.minute
    open_hour = 7 if minute >= 13 * 60 + 30 else 0
    label = "london_07_00_bar_open" if open_hour == 7 else "asia_00_00_bar_open"
    anchor_dt = entry_dt.replace(hour=open_hour, minute=0, second=0, microsecond=0)
    bars = bars_by_symbol.get(str(row.get("symbol", "")).upper(), [])
    anchor_open = _bar_open_at_or_before(bars, anchor_dt)
    if anchor_open is None:
        return {
            "session_open_label": label,
            "session_open_price": "",
            "distance_from_session_open_price": "",
            "distance_from_session_open_r": "",
            "distance_from_session_open_r_bucket": "UNRESOLVED",
        }
    distance_price = abs(entry_price - anchor_open)
    risk_price = abs(entry_price - stop_loss) if stop_loss is not None else 0.0
    distance_r = distance_price / risk_price if risk_price > 0.0 else None
    return {
        "session_open_label": label,
        "session_open_price": _fmt(anchor_open),
        "distance_from_session_open_price": _fmt(distance_price),
        "distance_from_session_open_r": _fmt(distance_r) if distance_r is not None else "",
        "distance_from_session_open_r_bucket": _distance_bucket(distance_r),
    }


def _load_m5_bars(bars_dir: Path) -> dict[str, list[dict[str, Any]]]:
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
                    "symbol": str(row.get("symbol", path.name.split("_")[0])).upper(),
                }
            )
        if rows:
            symbol = str(rows[0]["symbol"]).upper()
            bars_by_symbol[symbol] = sorted(rows, key=lambda item: item["bar_start_utc"])
    return bars_by_symbol


def _bar_open_at_or_before(bars: list[dict[str, Any]], target_dt: datetime) -> float | None:
    if not bars:
        return None
    times = [bar["bar_start_utc"] for bar in bars]
    index = bisect.bisect_right(times, target_dt) - 1
    if index < 0:
        return None
    return float(bars[index]["open"])


def _summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    closed = [row for row in rows if row.get("state") == "CLOSED"]
    open_rows = [row for row in rows if row.get("state") == "OPEN"]
    wins = [row for row in closed if float(row.get("profit_value", 0.0)) > 0.0]
    losses = [row for row in closed if float(row.get("profit_value", 0.0)) < 0.0]
    gross_win = sum(float(row.get("profit_value", 0.0)) for row in wins)
    gross_loss = sum(float(row.get("profit_value", 0.0)) for row in losses)
    pnl = sum(float(row.get("profit_value", 0.0)) for row in closed)
    return {
        "total": len(rows),
        "closed": len(closed),
        "open": len(open_rows),
        "wins": len(wins),
        "losses": len(losses),
        "win_rate_pct": round(len(wins) / len(closed) * 100.0, 2) if closed else None,
        "closed_pnl_aed": round(pnl, 2),
        "profit_factor": round(gross_win / abs(gross_loss), 2) if gross_loss else ("inf" if gross_win else None),
        "avg_win_aed": round(gross_win / len(wins), 2) if wins else None,
        "avg_loss_aed": round(gross_loss / len(losses), 2) if losses else None,
    }


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
    return sorted(output, key=lambda item: (float(item["closed_pnl_aed"]), -int(item["closed"])))


def _worst_clusters(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    clusters = _group_summaries(
        rows,
        ["symbol", "direction", "time_bucket", "impulse_bucket", "distance_from_session_open_r_bucket"],
    )
    return [row for row in clusters if row["closed"] >= 3][:10]


def _observability_gaps(rows: list[dict[str, Any]]) -> list[str]:
    gaps = [
        "Broker-history rows do not carry the exact session-extreme label that fired; "
        "BUY implies a session-high retest and SELL implies a session-low retest, but "
        "`asia_high`, `asia_low`, `london_high`, or `london_low` is not recoverable per row.",
        "Distance from session open is reconstructed from exported M5 bar opens using the "
        "bar timestamp convention in the replay export; it is not an MT5 runtime field.",
    ]
    unresolved_impulse = sum(1 for row in rows if row.get("impulse_status") != "RESOLVED")
    unresolved_distance = sum(1 for row in rows if row.get("distance_from_session_open_r_bucket") == "UNRESOLVED")
    if unresolved_impulse:
        gaps.append(f"{unresolved_impulse} duplicate-hidden rows have unresolved impulse context.")
    if unresolved_distance:
        gaps.append(f"{unresolved_distance} duplicate-hidden rows have unresolved session-open distance.")
    return gaps


def _candidate_fix_hypothesis(rows: list[dict[str, Any]]) -> dict[str, Any]:
    summary = _summarize(rows)
    impulse_groups = _group_summaries(rows, ["lt_neg_1_5_shadow_action"])
    worst = _worst_clusters(rows)[:3]
    return {
        "status": "DESIGN_INPUT_ONLY_NO_EA_T3_CODE",
        "supported_by_current_data": bool(rows) and float(summary["closed_pnl_aed"]) < 0.0,
        "baseline_duplicate_hidden_summary": summary,
        "candidate_fix": (
            "Do not build EA-T3 yet. The data supports continued quarantine and a pre-registered "
            "observer rebuild that logs exact session level label plus impulse and session-open "
            "distance fields. A deployable filter is not supported until those level labels are "
            "captured and re-scored."
        ),
        "impulse_threshold_neg_1_5_shadow": impulse_groups,
        "worst_clusters": worst,
    }


def _render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Session Extreme Entry Forensics - 2026-06-13",
        "",
        f"Status: **{payload['status']}**",
        "",
        "## Boundary",
        "",
        str(payload["boundary"]),
        "",
        "## Sources",
        "",
        f"- Actual broker trades: `{payload['source_actual_trades_csv']}`",
        f"- Impulse rows: `{payload['source_impulse_rows_csv']}`",
        f"- M5 bars: `{payload['source_bars_dir']}`",
        "",
        "## Row Counts",
        "",
        _key_value_table(payload["row_counts"]),
        "",
        "## Summary",
        "",
        _summary_table(payload["summaries"]),
        "",
        "## Breakdowns",
        "",
    ]
    for name, rows in payload["breakdowns"].items():
        lines.extend([f"### {name}", "", _breakdown_table(rows), ""])
    lines.extend(
        [
            "## Worst Duplicate-Hidden Clusters",
            "",
            _breakdown_table(payload["worst_clusters"]),
            "",
            "## Observability Gaps",
            "",
        ]
    )
    lines.extend(f"- {gap}" for gap in payload["observability_gaps"])
    fix = payload["candidate_fix_hypothesis"]
    lines.extend(
        [
            "",
            "## Candidate Fix Hypothesis",
            "",
            f"Status: **{fix['status']}**",
            "",
            fix["candidate_fix"],
            "",
            "This is design input only. Magic band 933200-933299 remains reserved but unused.",
            "",
        ]
    )
    return "\n".join(lines)


def _key_value_table(values: dict[str, Any]) -> str:
    lines = ["| Field | Value |", "|---|---:|"]
    for key, value in values.items():
        lines.append(f"| {key} | {value} |")
    return "\n".join(lines)


def _summary_table(values: dict[str, dict[str, Any]]) -> str:
    lines = [
        "| View | Total | Closed | Open | Wins | Losses | Win Rate | Closed PnL AED | PF | Avg Win | Avg Loss |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for name, summary in values.items():
        lines.append(
            f"| {name} | {summary['total']} | {summary['closed']} | {summary['open']} | "
            f"{summary['wins']} | {summary['losses']} | {_fmt_cell(summary['win_rate_pct'])} | "
            f"{_fmt_cell(summary['closed_pnl_aed'])} | {_fmt_cell(summary['profit_factor'])} | "
            f"{_fmt_cell(summary['avg_win_aed'])} | {_fmt_cell(summary['avg_loss_aed'])} |"
        )
    return "\n".join(lines)


def _breakdown_table(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return "_No rows._"
    key_fields = [
        field
        for field in rows[0].keys()
        if field
        not in {
            "total",
            "closed",
            "open",
            "wins",
            "losses",
            "win_rate_pct",
            "closed_pnl_aed",
            "profit_factor",
            "avg_win_aed",
            "avg_loss_aed",
        }
    ]
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


def _time_bucket(entry_time: str) -> str:
    try:
        hour = int(str(entry_time)[11:13])
    except (TypeError, ValueError):
        return "UNKNOWN"
    if hour >= 20 or hour < 6:
        return "Night 20:00-05:59"
    if hour < 12:
        return "Morning 06:00-11:59"
    if hour < 16:
        return "Afternoon 12:00-15:59"
    return "Evening 16:00-19:59"


def _outcome(row: dict[str, Any]) -> str:
    if row.get("state") == "OPEN":
        return "OPEN"
    pnl = float(row.get("profit_value", 0.0))
    if pnl > 0.0:
        return "WIN"
    if pnl < 0.0:
        return "LOSS"
    return "FLAT"


def _distance_bucket(value: float | None) -> str:
    if value is None:
        return "UNRESOLVED"
    if value < 0.5:
        return "lt_0_5R_from_session_open"
    if value < 1.0:
        return "0_5_to_1R_from_session_open"
    if value < 2.0:
        return "1_to_2R_from_session_open"
    return "gte_2R_from_session_open"


def _truthy(value: Any) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def _to_float(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _fmt(value: float | None) -> str:
    if value is None:
        return ""
    return f"{value:.6f}".rstrip("0").rstrip(".")


def _fmt_cell(value: Any) -> str:
    if value is None:
        return "n/a"
    if isinstance(value, float):
        return f"{value:.2f}"
    return str(value)


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate session_extreme_retest_v0 entry-failure forensics.")
    parser.add_argument("--phase1-root", type=Path, default=Path.cwd())
    parser.add_argument("--actual-trades-csv", type=Path)
    parser.add_argument("--impulse-rows-csv", type=Path)
    parser.add_argument("--bars-dir", type=Path)
    parser.add_argument("--output-doc", type=Path)
    parser.add_argument("--output-json", type=Path)
    args = parser.parse_args()
    output = generate_session_extreme_entry_forensics(
        args.phase1_root,
        actual_trades_csv=args.actual_trades_csv,
        impulse_rows_csv=args.impulse_rows_csv,
        bars_dir=args.bars_dir,
        output_doc=args.output_doc,
        output_json=args.output_json,
    )
    print(f"{output.status}: {output.markdown_path} ({output.exact_duplicate_hidden_rows} duplicate-hidden rows)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
