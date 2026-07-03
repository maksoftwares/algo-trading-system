"""Broker-join XAU factor rows to realized fills and produce an action plan.

This is intentionally conservative:
- broker fills remain the money truth,
- factor rows are joined only by account, direction, and time proximity,
- unmatched fills are reported, not hidden,
- the output is a forward-test action plan, not a runtime deployment approval.
"""

from __future__ import annotations

import csv
import json
import math
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from analyze_demo_trade_factor_commonality import (
    C01_SNAPSHOT_ROWS,
    MAGIC_NAMES,
    OUT_JSON as COMMONALITY_JSON,
    PHASE1_ROOT,
    REPORTS,
    dubai_bucket_from_utc,
    fmt_money,
    fmt_num,
    fmt_pct,
    load_fresh_c02_xau_trades,
    mean,
    parse_time_text,
    profit_factor,
    read_csv,
    summarize_profit_rows,
    to_float,
)


OUT_MD = REPORTS / "BROKER_JOINED_FACTOR_ACTION_PLAN_2026_06_27.md"
OUT_JSON = REPORTS / "BROKER_JOINED_FACTOR_ACTION_PLAN_2026_06_27.json"
OUT_JOINED = REPORTS / "BROKER_JOINED_XAU_FACTOR_ROWS_2026_06_27.csv"
OUT_SPEC = PHASE1_ROOT / "docs" / "XAU_EVENING_TREND_ALIGNMENT_FORWARD_TEST_V0_2026_06_27.md"

JOIN_TOLERANCE_MINUTES = 30


def parse_dt(value: object) -> datetime | None:
    return parse_time_text(value)


def direction_to_side(value: object) -> str:
    text = str(value or "").strip().upper()
    if text == "LONG":
        return "BUY"
    if text == "SHORT":
        return "SELL"
    return text


def fmt_pf(value: float) -> str:
    if math.isnan(value):
        return "n/a"
    if math.isinf(value):
        return "inf"
    return f"{value:.2f}"


def metric_row(name: str, rows: list[dict[str, object]]) -> dict[str, object]:
    s = summarize_profit_rows(rows)
    return {
        "slice": name,
        "trades": s["trades"],
        "wins": s["wins"],
        "losses": s["losses"],
        "win_rate": s["win_rate"],
        "pnl": s["pnl"],
        "avg_win": s["avg_win"],
        "avg_loss": s["avg_loss"],
        "profit_factor": s["profit_factor"],
    }


def table(rows: list[dict[str, object]], columns: list[tuple[str, str]]) -> str:
    lines = [
        "| " + " | ".join(label for _, label in columns) + " |",
        "| " + " | ".join("---" for _ in columns) + " |",
    ]
    for row in rows:
        cells = []
        for key, _ in columns:
            value = row.get(key, "")
            if key == "win_rate":
                value = fmt_pct(float(value)) if isinstance(value, (int, float)) else str(value)
            elif key in {"pnl", "avg_win", "avg_loss"}:
                value = fmt_money(float(value)) if isinstance(value, (int, float)) and not math.isnan(float(value)) else "n/a"
            elif key == "profit_factor":
                value = fmt_pf(float(value)) if isinstance(value, (int, float)) else str(value)
            elif isinstance(value, float):
                value = fmt_num(value, 3)
            cells.append(str(value))
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def load_snapshot_signals() -> list[dict[str, object]]:
    rows = read_csv(C01_SNAPSHOT_ROWS)
    out: list[dict[str, object]] = []
    for row in rows:
        if str(row.get("base_family", "")).strip() != "breakout_retest":
            continue
        decision_dt = parse_dt(row.get("entry_eligible_from_utc") or row.get("decision_time_utc"))
        if decision_dt is None:
            continue
        rec: dict[str, object] = dict(row)
        rec["join_time_utc"] = decision_dt
        rec["side"] = direction_to_side(row.get("direction"))
        rec["account_label"] = str(row.get("account_label", "")).strip()
        for col in (
            "d1_trend_score_aligned",
            "h1_ema20_slope_aligned_atr",
            "m15_ema20_slope_aligned_atr",
            "price_h1_ema20_distance_aligned_atr",
            "m5_atr_percentile_trailing_20d",
            "break_distance_atr",
            "tick_volume_ratio_20",
            "range_compression_ratio_20",
            "cost_R",
            "confirmation_body_ratio",
            "confirmation_close_location_aligned",
            "minutes_from_session_start_scaled",
        ):
            rec[col] = to_float(row.get(col))
        out.append(rec)
    out.sort(key=lambda r: r["join_time_utc"])
    return out


def one_to_one_join(
    fills: list[dict[str, object]], signals: list[dict[str, object]], tolerance_minutes: int
) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    by_key: dict[tuple[str, str], list[dict[str, object]]] = defaultdict(list)
    for signal in signals:
        by_key[(str(signal.get("account_label")), str(signal.get("side")))].append(signal)

    used_signal_ids: set[str] = set()
    joined: list[dict[str, object]] = []
    unmatched: list[dict[str, object]] = []
    tolerance_seconds = tolerance_minutes * 60

    for fill in sorted(fills, key=lambda r: str(r.get("entry_time_utc"))):
        entry_dt = parse_dt(fill.get("entry_time_utc"))
        if entry_dt is None:
            unmatched.append(fill)
            continue
        key = (str(fill.get("account_label")), str(fill.get("direction")))
        candidates = []
        for signal in by_key.get(key, []):
            signal_id = str(signal.get("exact_signal_id"))
            if signal_id in used_signal_ids:
                continue
            delta = (entry_dt - signal["join_time_utc"]).total_seconds()
            if 0 <= delta <= tolerance_seconds:
                candidates.append((delta, signal))
        if not candidates:
            unmatched.append(fill)
            continue
        candidates.sort(key=lambda x: x[0])
        delta, signal = candidates[0]
        used_signal_ids.add(str(signal.get("exact_signal_id")))
        rec = dict(fill)
        rec.update(
            {
                "matched_signal_id": signal.get("exact_signal_id"),
                "matched_source_signal_id": signal.get("source_signal_id"),
                "signal_time_utc": signal["join_time_utc"].isoformat(),
                "join_delta_seconds": int(delta),
                "signal_session_bucket": signal.get("session_bucket"),
                "signal_label_status": signal.get("label_status"),
            }
        )
        for col in (
            "d1_trend_score_aligned",
            "h1_ema20_slope_aligned_atr",
            "m15_ema20_slope_aligned_atr",
            "price_h1_ema20_distance_aligned_atr",
            "m5_atr_percentile_trailing_20d",
            "break_distance_atr",
            "tick_volume_ratio_20",
            "range_compression_ratio_20",
            "cost_R",
            "confirmation_body_ratio",
            "confirmation_close_location_aligned",
            "minutes_from_session_start_scaled",
        ):
            rec[col] = signal.get(col)
        joined.append(rec)
    return joined, unmatched


def group_by(rows: list[dict[str, object]], key: str) -> list[dict[str, object]]:
    grouped: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in rows:
        grouped[str(row.get(key, "") or "UNKNOWN")].append(row)
    out = []
    for value, group in grouped.items():
        rec = metric_row(value, group)
        rec[key] = value
        out.append(rec)
    out.sort(key=lambda r: float(r.get("pnl", 0)), reverse=True)
    return out


def top_winner_stress(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    ordered = sorted(rows, key=lambda r: to_float(r.get("profit_aed")), reverse=True)
    out = []
    for n in (0, 1, 3, 5):
        subset = ordered[n:]
        rec = metric_row(f"remove_top_{n}_winners", subset)
        out.append(rec)
    return out


def remove_june_10(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    out = []
    for row in rows:
        dt = parse_dt(row.get("entry_time_utc"))
        if dt and dt.date().isoformat() == "2026-06-10":
            continue
        out.append(row)
    return out


def chrono_halves(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    ordered = sorted(rows, key=lambda r: str(r.get("entry_time_utc")))
    mid = len(ordered) // 2
    return [metric_row("first_half", ordered[:mid]), metric_row("second_half", ordered[mid:])]


def proposed_take(row: dict[str, object]) -> bool:
    return (
        str(row.get("time_bucket")) == "EVENING"
        and to_float(row.get("d1_trend_score_aligned")) >= 0.25
        and to_float(row.get("h1_ema20_slope_aligned_atr")) >= 0.35
    )


def main() -> None:
    fills, fill_meta = load_fresh_c02_xau_trades()
    breakout_fills = [
        row
        for row in fills
        if str(row.get("symbol")) == "XAUUSD"
        and (str(row.get("candidate")) == "breakout_retest" or str(row.get("magic")) == "920101")
    ]
    signals = load_snapshot_signals()

    join_counts = []
    joins_by_tol: dict[int, tuple[list[dict[str, object]], list[dict[str, object]]]] = {}
    for tolerance in (5, 15, 30, 60):
        joined, unmatched = one_to_one_join(breakout_fills, signals, tolerance)
        joins_by_tol[tolerance] = (joined, unmatched)
        join_counts.append(
            {
                "tolerance_minutes": tolerance,
                "breakout_fills": len(breakout_fills),
                "joined": len(joined),
                "unmatched": len(unmatched),
                "join_rate": len(joined) / len(breakout_fills) if breakout_fills else math.nan,
            }
        )

    joined, unmatched = joins_by_tol[JOIN_TOLERANCE_MINUTES]
    for row in joined:
        row["forward_test_take_v0"] = proposed_take(row)

    take_rows = [row for row in joined if row["forward_test_take_v0"]]
    skip_rows = [row for row in joined if not row["forward_test_take_v0"]]
    evening_rows = [row for row in joined if row.get("time_bucket") == "EVENING"]
    trend_rows = [
        row
        for row in joined
        if to_float(row.get("d1_trend_score_aligned")) >= 0.25
        and to_float(row.get("h1_ema20_slope_aligned_atr")) >= 0.35
    ]

    metric_rows = [
        metric_row("all_joined_breakout_fills", joined),
        metric_row("evening_only", evening_rows),
        metric_row("trend_aligned_only", trend_rows),
        metric_row("proposed_take_evening_plus_trend", take_rows),
        metric_row("proposed_skip", skip_rows),
        metric_row("unmatched_breakout_fills", unmatched),
    ]
    stress_rows = top_winner_stress(take_rows)
    stress_rows.append(metric_row("take_without_june_10", remove_june_10(take_rows)))
    stress_rows.extend(chrono_halves(take_rows))

    joined_fields = [
        "account_label",
        "account_scope",
        "symbol",
        "candidate",
        "magic",
        "direction",
        "volume",
        "entry_time_utc",
        "exit_time_utc",
        "time_bucket",
        "entry_price",
        "exit_price",
        "profit_aed",
        "position_id",
        "matched_signal_id",
        "matched_source_signal_id",
        "signal_time_utc",
        "join_delta_seconds",
        "signal_session_bucket",
        "signal_label_status",
        "forward_test_take_v0",
        "d1_trend_score_aligned",
        "h1_ema20_slope_aligned_atr",
        "m15_ema20_slope_aligned_atr",
        "price_h1_ema20_distance_aligned_atr",
        "m5_atr_percentile_trailing_20d",
        "break_distance_atr",
        "tick_volume_ratio_20",
        "range_compression_ratio_20",
        "cost_R",
        "confirmation_body_ratio",
        "confirmation_close_location_aligned",
        "minutes_from_session_start_scaled",
    ]
    write_csv(OUT_JOINED, joined, joined_fields)

    decision = "NO_RUNTIME_CHANGE"
    reason = "insufficient broker-joined sample for proposed_take"
    if len(take_rows) >= 30:
        take_stats = summarize_profit_rows(take_rows)
        without_june_10 = summarize_profit_rows(remove_june_10(take_rows))
        if (
            take_stats["profit_factor"] >= 1.10
            and without_june_10["profit_factor"] >= 1.00
            and take_stats["pnl"] > 0
        ):
            decision = "LOCK_FORWARD_TEST_SPEC_ONLY"
            reason = "broker-joined slice is positive but still not deployment-grade"

    OUT_SPEC.parent.mkdir(parents=True, exist_ok=True)
    OUT_SPEC.write_text(
        "\n".join(
            [
                "# XAU Evening Trend Alignment Forward Test V0",
                "",
                "Status: PROPOSED_LOCK_PENDING_REVIEW",
                "",
                "This is not a runtime deployment approval. It is a forward-test hypothesis",
                "created after broker-joining available factor rows to realized XAU fills.",
                "",
                "## Rule",
                "",
                "For XAUUSD breakout_retest-family signals, mark TAKE only when:",
                "",
                "- Dubai session is Evening 16:00-19:59.",
                "- d1_trend_score_aligned >= 0.25.",
                "- h1_ema20_slope_aligned_atr >= 0.35.",
                "- Direction is already encoded as aligned in the factor columns.",
                "",
                "All other signals are marked SKIP.",
                "",
                "## Forward-Test Minimum",
                "",
                "- Minimum 150 broker-joined forward trades or 6 full weeks, whichever comes later.",
                "- Must be positive after removing the top 3 winners.",
                "- Must not depend on one day for more than 35% of total net PnL.",
                "- Must show PF >= 1.10 at interim review and PF >= 1.25 for promotion.",
                "- Must remain account-transferable, not A1-only.",
                "",
                "## Kill Rule",
                "",
                "- Rolling 50-trade PF < 0.90.",
                "- Any one day contributes more than 50% of cumulative net PnL.",
                "- Second half PF is more than 0.30 below first half PF.",
                "- A3 or clean-control evidence remains materially negative while A1 is positive.",
                "",
                "## Guardrails",
                "",
                "- No lot increase.",
                "- No extra symbols.",
                "- No threshold tuning on the same historical window.",
                "- No runtime filter until separately approved by owner and reviewer.",
                "",
            ]
        ),
        encoding="utf-8",
    )

    lines = []
    lines.append("# Broker-Joined Factor Action Plan")
    lines.append("")
    lines.append(f"Generated UTC: `{datetime.now(timezone.utc).replace(microsecond=0).isoformat()}`")
    lines.append("")
    lines.append("## Boundary")
    lines.append("")
    lines.append("- No MT5 runtime, EA, chart, preset, order, or position was touched.")
    lines.append("- This report joins available XAU breakout factor rows to realized broker fills by account, direction, and time proximity.")
    lines.append("- The primary join tolerance is 30 minutes; 5/15/30/60 minute join rates are reported.")
    lines.append("- The output is an action plan for a locked forward test, not a deployment instruction.")
    lines.append("")
    lines.append("## Join Coverage")
    lines.append("")
    lines.append(table(join_counts, [("tolerance_minutes", "Tolerance Min"), ("breakout_fills", "Breakout Fills"), ("joined", "Joined"), ("unmatched", "Unmatched"), ("join_rate", "Join Rate")]))
    lines.append("")
    lines.append("## Broker-Joined Money Results")
    lines.append("")
    lines.append(table(metric_rows, [("slice", "Slice"), ("trades", "Trades"), ("wins", "Wins"), ("losses", "Losses"), ("win_rate", "WR"), ("pnl", "PnL AED"), ("avg_win", "Avg Win"), ("avg_loss", "Avg Loss"), ("profit_factor", "PF")]))
    lines.append("")
    lines.append("## Proposed TAKE Stress")
    lines.append("")
    lines.append(table(stress_rows, [("slice", "Stress"), ("trades", "Trades"), ("wins", "Wins"), ("losses", "Losses"), ("win_rate", "WR"), ("pnl", "PnL AED"), ("profit_factor", "PF")]))
    lines.append("")
    lines.append("## Proposed TAKE By Account")
    lines.append("")
    lines.append(table(group_by(take_rows, "account_label"), [("account_label", "Account"), ("trades", "Trades"), ("win_rate", "WR"), ("pnl", "PnL AED"), ("profit_factor", "PF")]))
    lines.append("")
    lines.append("## Proposed TAKE By Direction")
    lines.append("")
    lines.append(table(group_by(take_rows, "direction"), [("direction", "Direction"), ("trades", "Trades"), ("win_rate", "WR"), ("pnl", "PnL AED"), ("profit_factor", "PF")]))
    lines.append("")
    lines.append("## Decision")
    lines.append("")
    lines.append(f"`{decision}`")
    lines.append("")
    lines.append(f"Reason: {reason}.")
    lines.append("")
    lines.append("Actionable output:")
    lines.append("")
    lines.append(f"- Review and lock the proposed forward-test spec: `{OUT_SPEC}`")
    lines.append(f"- Inspect broker-joined rows: `{OUT_JOINED}`")
    lines.append("- Do not deploy a runtime filter from this historical sample.")
    lines.append("- If owner/reviewer agree, start a shadow-only forward-test scoreboard using this exact rule.")
    lines.append("")
    lines.append("## Artifacts")
    lines.append("")
    lines.append(f"- Report: `{OUT_MD}`")
    lines.append(f"- JSON: `{OUT_JSON}`")
    lines.append(f"- Joined CSV: `{OUT_JOINED}`")
    lines.append(f"- Forward-test spec: `{OUT_SPEC}`")
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    payload = {
        "decision": decision,
        "reason": reason,
        "join_tolerance_minutes": JOIN_TOLERANCE_MINUTES,
        "fill_meta": fill_meta,
        "join_counts": join_counts,
        "metric_rows": metric_rows,
        "stress_rows": stress_rows,
        "take_by_account": group_by(take_rows, "account_label"),
        "take_by_direction": group_by(take_rows, "direction"),
        "artifacts": {
            "report": str(OUT_MD),
            "json": str(OUT_JSON),
            "joined_csv": str(OUT_JOINED),
            "forward_test_spec": str(OUT_SPEC),
            "commonality_json": str(COMMONALITY_JSON),
        },
    }
    OUT_JSON.write_text(json.dumps(payload, indent=2, allow_nan=True), encoding="utf-8")

    print(f"Wrote {OUT_MD}")
    print(f"Wrote {OUT_JSON}")
    print(f"Wrote {OUT_JOINED}")
    print(f"Wrote {OUT_SPEC}")


if __name__ == "__main__":
    main()
