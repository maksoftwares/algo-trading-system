from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean, median
from typing import Any


DEFAULT_CANONICAL_ROWS = Path("outputs/reports/XAUUSD_DEDUPED_REAL_FILL_EVIDENCE_2026_06_16_ROWS.csv")
DEFAULT_ACTUAL_TRADES = Path("outputs/reports/PHASE2_DEMO_ACTUAL_BROKER_TRADES.csv")
DEFAULT_COST_TRADES = Path("outputs/reports/COST_GATE_REAL_FILL_TRADES_2026_06_16.csv")
DEFAULT_OUTPUT_PREFIX = Path("outputs/reports/XAUUSD_CANONICAL_LOSS_AVOIDANCE_2026_06_17")

BREAKOUT_CORE = {"breakout_retest", "swing_breakout_retest_v0"}
ROUND_FAMILY = {"round_family"}
EVENING_NIGHT = {"Evening 16:00-19:59", "Night 20:00-05:59"}
MORNING_AFTERNOON = {"Morning 06:00-11:59", "Afternoon 12:00-15:59"}


def generate_report(
    phase1_root: Path,
    *,
    canonical_rows_csv: Path | None = None,
    actual_trades_csv: Path | None = None,
    cost_trades_csv: Path | None = None,
    output_prefix: Path | None = None,
) -> dict[str, Path]:
    phase1_root = phase1_root.resolve()
    canonical_rows_csv = (canonical_rows_csv or phase1_root / DEFAULT_CANONICAL_ROWS).resolve()
    actual_trades_csv = (actual_trades_csv or phase1_root / DEFAULT_ACTUAL_TRADES).resolve()
    cost_trades_csv = (cost_trades_csv or phase1_root / DEFAULT_COST_TRADES).resolve()
    output_prefix = (output_prefix or phase1_root / DEFAULT_OUTPUT_PREFIX).resolve()

    canonical_rows = read_csv(canonical_rows_csv)
    actual_by_ticket = {row.get("position_ticket", ""): row for row in read_csv(actual_trades_csv) if row.get("position_ticket")}
    cost_by_key = _cost_index(read_csv(cost_trades_csv))

    enriched_rows = [
        enrich_canonical_row(row, actual_by_ticket, cost_by_key)
        for row in canonical_rows
    ]

    payload: dict[str, Any] = {
        "status": "PASS" if enriched_rows else "NO_ROWS",
        "created_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "boundary": (
            "Analysis only. Reads exported CSV artifacts and writes reports. Does not touch MT5 runtime, "
            "EAs, presets, orders, positions, charts, profiles, or accounts."
        ),
        "source_files": {
            "canonical_rows_csv": str(canonical_rows_csv),
            "actual_trades_csv": str(actual_trades_csv),
            "cost_trades_csv": str(cost_trades_csv),
        },
        "universe": {
            "canonical_rows": len(enriched_rows),
            "ticket_matched_rows": sum(1 for row in enriched_rows if row["actual_join_status"] == "MATCHED"),
            "cost_matched_rows": sum(1 for row in enriched_rows if row["cost_join_status"] in {"COST_KNOWN", "COST_MISSING"}),
            "cost_known_rows": sum(1 for row in enriched_rows if row["cost_join_status"] == "COST_KNOWN"),
            "cost_missing_rows": sum(1 for row in enriched_rows if row["cost_join_status"] == "COST_MISSING"),
        },
        "baseline": summarize(enriched_rows),
        "family": group_table(enriched_rows, ["selected_family"]),
        "candidate": group_table(enriched_rows, ["selected_candidate"]),
        "session": group_table(enriched_rows, ["time_bucket"]),
        "afternoon_round_family_diagnosis": afternoon_round_family_diagnosis(enriched_rows),
        "direction_session": group_table(enriched_rows, ["direction", "time_bucket"]),
        "candidate_session": group_table(enriched_rows, ["selected_candidate", "time_bucket"], min_rows=3),
        "cost_by_bucket": cost_bucket_table(enriched_rows),
        "cost_cutoffs": cost_cutoff_table(enriched_rows),
        "cost_by_family": cost_group_table(enriched_rows, ["selected_family"]),
        "account_focus": account_focus(enriched_rows),
        "rule_scorecard": rule_scorecard(enriched_rows),
        "protected_cluster": protected_cluster(enriched_rows),
        "duplicate_exposure": duplicate_exposure(enriched_rows),
        "conclusions": conclusions(),
    }

    output_prefix.parent.mkdir(parents=True, exist_ok=True)
    rows_path = output_prefix.with_name(output_prefix.name + "_ROWS").with_suffix(".csv")
    json_path = output_prefix.with_suffix(".json")
    md_path = output_prefix.with_suffix(".md")
    write_csv(rows_path, enriched_rows, enriched_fields())
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    md_path.write_text(render_markdown(payload, rows_path), encoding="utf-8")
    return {"md": md_path, "json": json_path, "rows": rows_path}


def enrich_canonical_row(
    row: dict[str, str],
    actual_by_ticket: dict[str, dict[str, str]],
    cost_by_key: dict[str, dict[str, str]],
) -> dict[str, str]:
    enriched = dict(row)
    ticket = row.get("selected_position_ticket", "")
    actual = actual_by_ticket.get(ticket)
    if actual:
        enriched["actual_join_status"] = "MATCHED"
        enriched["entry_time"] = actual.get("entry_time", "")
        enriched["entry_price"] = actual.get("entry_price", "")
        enriched["sl"] = actual.get("sl", "")
        enriched["tp"] = actual.get("tp", "")
        enriched["magic"] = actual.get("magic", "")
        enriched["entry_comment"] = actual.get("entry_comment", "")
        enriched["exit_comment"] = actual.get("exit_comment", "")
    else:
        enriched["actual_join_status"] = "MISSING"
        enriched["entry_time"] = ""
        enriched["entry_price"] = ""
        enriched["sl"] = ""
        enriched["tp"] = ""
        enriched["magic"] = ""
        enriched["entry_comment"] = ""
        enriched["exit_comment"] = ""

    cost_row = cost_by_key.get(_cost_key_from_actual(actual)) if actual else None
    if cost_row and cost_row.get("cost_r", "") != "":
        enriched["account"] = cost_row.get("account", "")
        enriched["lane"] = cost_row.get("lane", "")
        enriched["account_role"] = account_role(cost_row.get("account", ""))
        enriched["cost_join_status"] = "COST_KNOWN"
        enriched["cost_r"] = cost_row.get("cost_r", "")
        enriched["spread_points"] = cost_row.get("spread_points", "")
        enriched["stop_distance_points"] = cost_row.get("stop_distance_points", "")
        enriched["result_r"] = cost_row.get("result_r", "")
    elif cost_row:
        enriched["account"] = cost_row.get("account", "")
        enriched["lane"] = cost_row.get("lane", "")
        enriched["account_role"] = account_role(cost_row.get("account", ""))
        enriched["cost_join_status"] = "COST_MISSING"
        enriched["cost_r"] = ""
        enriched["spread_points"] = cost_row.get("spread_points", "")
        enriched["stop_distance_points"] = cost_row.get("stop_distance_points", "")
        enriched["result_r"] = cost_row.get("result_r", "")
    else:
        enriched["account"] = ""
        enriched["lane"] = ""
        enriched["account_role"] = "UNKNOWN"
        enriched["cost_join_status"] = "NO_COST_MATCH"
        enriched["cost_r"] = ""
        enriched["spread_points"] = ""
        enriched["stop_distance_points"] = ""
        enriched["result_r"] = ""

    enriched["is_breakout_core"] = str(row.get("selected_candidate") in BREAKOUT_CORE).lower()
    enriched["is_round_family"] = str(row.get("selected_family") in ROUND_FAMILY).lower()
    enriched["is_evening_night"] = str(row.get("time_bucket") in EVENING_NIGHT).lower()
    enriched["is_morning_afternoon"] = str(row.get("time_bucket") in MORNING_AFTERNOON).lower()
    enriched["is_protected_breakout_cluster"] = str(
        row.get("selected_candidate") in BREAKOUT_CORE and row.get("time_bucket") in EVENING_NIGHT
    ).lower()
    enriched["is_mixed_family_group"] = str(";" in row.get("family_members", "")).lower()
    return enriched


def account_role(account: str) -> str:
    if account == "1025742":
        return "A1_LAB_OBSERVATION"
    if account in {"1033030", "1033669"}:
        return "A2_A3_PRODUCTION_STYLE"
    return "UNKNOWN"


def summarize(rows: list[dict[str, str]]) -> dict[str, Any]:
    values = [to_float(row.get("selected_profit_aed")) or 0.0 for row in rows]
    wins = [value for value in values if value > 0]
    losses = [value for value in values if value < 0]
    return {
        "rows": len(rows),
        "wins": len(wins),
        "losses": len(losses),
        "flats": len(values) - len(wins) - len(losses),
        "win_rate_pct": pct(len(wins), len(wins) + len(losses)),
        "pnl_aed": fmt(sum(values)),
        "profit_factor": fmt(sum(wins) / abs(sum(losses))) if losses and sum(losses) else ("inf" if wins else "n/a"),
        "avg_win_aed": fmt(sum(wins) / len(wins)) if wins else "n/a",
        "avg_loss_aed": fmt(sum(losses) / len(losses)) if losses else "n/a",
    }


def group_table(rows: list[dict[str, str]], keys: list[str], *, min_rows: int = 1) -> list[dict[str, str]]:
    grouped: dict[tuple[str, ...], list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        grouped[tuple(row.get(key, "") or "UNKNOWN" for key in keys)].append(row)
    table = []
    for key, items in grouped.items():
        if len(items) < min_rows:
            continue
        summary = summarize(items)
        table.append(
            {
                "group": " | ".join(key),
                "rows": str(summary["rows"]),
                "win_rate_pct": summary["win_rate_pct"],
                "pnl_aed": summary["pnl_aed"],
                "pf": summary["profit_factor"],
                "best_day_removed_pnl_aed": fmt(pnl_after_removing_best_days(items, 1)),
                "best_two_days_removed_pnl_aed": fmt(pnl_after_removing_best_days(items, 2)),
            }
        )
    return sorted(table, key=lambda item: to_float(item["pnl_aed"]) or 0.0)


def afternoon_round_family_diagnosis(rows: list[dict[str, str]]) -> dict[str, Any]:
    afternoon = [row for row in rows if row.get("time_bucket") == "Afternoon 12:00-15:59"]
    round_afternoon = [row for row in afternoon if row.get("selected_family") in ROUND_FAMILY]
    non_round_afternoon = [row for row in afternoon if row.get("selected_family") not in ROUND_FAMILY]
    breakout_afternoon = [row for row in afternoon if row.get("selected_candidate") in BREAKOUT_CORE]
    session_extreme_afternoon = [row for row in afternoon if row.get("selected_family") == "session_extreme"]
    protected_evening_night = [
        row
        for row in rows
        if row.get("selected_candidate") in BREAKOUT_CORE and row.get("time_bucket") in EVENING_NIGHT
    ]
    protected_after_round_quarantine = [
        row for row in protected_evening_night if row.get("selected_family") not in ROUND_FAMILY
    ]
    afternoon_pnl = sum(to_float(row.get("selected_profit_aed")) or 0.0 for row in afternoon)
    round_pnl = sum(to_float(row.get("selected_profit_aed")) or 0.0 for row in round_afternoon)
    residual_pnl = sum(to_float(row.get("selected_profit_aed")) or 0.0 for row in non_round_afternoon)
    rows_out = [
        _diagnosis_row("all_afternoon", afternoon, afternoon_pnl, afternoon_pnl, "Baseline afternoon exposure."),
        _diagnosis_row(
            "round_family_afternoon",
            round_afternoon,
            afternoon_pnl,
            round_pnl,
            "Primary loss source to quarantine first.",
        ),
        _diagnosis_row(
            "non_round_residual_after_round_quarantine",
            non_round_afternoon,
            afternoon_pnl,
            residual_pnl,
            "Remaining afternoon exposure after removing round-family rows.",
        ),
        _diagnosis_row(
            "breakout_core_afternoon",
            breakout_afternoon,
            afternoon_pnl,
            sum(to_float(row.get("selected_profit_aed")) or 0.0 for row in breakout_afternoon),
            "Small residual; do not block breakout core solely because it is afternoon.",
        ),
        _diagnosis_row(
            "session_extreme_afternoon",
            session_extreme_afternoon,
            afternoon_pnl,
            sum(to_float(row.get("selected_profit_aed")) or 0.0 for row in session_extreme_afternoon),
            "Residual weak-family slice; keep measuring separately.",
        ),
    ]
    protected_before = summarize(protected_evening_night)
    protected_after = summarize(protected_after_round_quarantine)
    return {
        "session": "Afternoon 12:00-15:59",
        "dedup_universe_rows": len(rows),
        "afternoon_rows": len(afternoon),
        "afternoon_pnl_aed": fmt(afternoon_pnl),
        "round_family_afternoon_rows": len(round_afternoon),
        "round_family_afternoon_pnl_aed": fmt(round_pnl),
        "round_family_loss_share_of_afternoon_loss_pct": _loss_share(round_pnl, afternoon_pnl),
        "residual_after_round_quarantine_rows": len(non_round_afternoon),
        "residual_after_round_quarantine_pnl_aed": fmt(residual_pnl),
        "protected_evening_night_rows_removed": str(int(protected_before["rows"]) - int(protected_after["rows"])),
        "protected_evening_night_pnl_removed_aed": fmt(
            (to_float(protected_before["pnl_aed"]) or 0.0) - (to_float(protected_after["pnl_aed"]) or 0.0)
        ),
        "decision": (
            "Round-family quarantine is the first measurable fix. Avoid a broad afternoon ban until the non-round "
            "residual has more evidence."
        ),
        "runtime_authorized": False,
        "rows": rows_out,
    }


def _diagnosis_row(
    segment: str,
    rows: list[dict[str, str]],
    afternoon_pnl: float,
    segment_pnl: float,
    interpretation: str,
) -> dict[str, str]:
    summary = summarize(rows)
    return {
        "segment": segment,
        "rows": str(summary["rows"]),
        "win_rate_pct": summary["win_rate_pct"],
        "pnl_aed": summary["pnl_aed"],
        "pf": summary["profit_factor"],
        "loss_share_of_afternoon_loss_pct": _loss_share(segment_pnl, afternoon_pnl),
        "best_day_removed_pnl_aed": fmt(pnl_after_removing_best_days(rows, 1)),
        "best_two_days_removed_pnl_aed": fmt(pnl_after_removing_best_days(rows, 2)),
        "interpretation": interpretation,
    }


def _loss_share(segment_pnl: float, baseline_pnl: float) -> str:
    if baseline_pnl >= 0 or segment_pnl >= 0:
        return "n/a"
    return f"{abs(segment_pnl) / abs(baseline_pnl) * 100.0:.2f}%"


def cost_bucket_table(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    buckets = [
        ("<=0.05", lambda value: value <= 0.05),
        ("0.05-0.07", lambda value: 0.05 < value <= 0.07),
        ("0.07-0.09", lambda value: 0.07 < value <= 0.09),
        ("0.09-0.11", lambda value: 0.09 < value <= 0.11),
        ("0.11-0.13", lambda value: 0.11 < value <= 0.13),
        (">0.13", lambda value: value > 0.13),
    ]
    known = [row for row in rows if row.get("cost_join_status") == "COST_KNOWN"]
    table = []
    for label, predicate in buckets:
        items = [row for row in known if predicate(to_float(row.get("cost_r")) or 0.0)]
        summary = summarize(items)
        costs = [to_float(row.get("cost_r")) or 0.0 for row in items]
        table.append(
            {
                "bucket": label,
                "rows": str(summary["rows"]),
                "win_rate_pct": summary["win_rate_pct"],
                "pnl_aed": summary["pnl_aed"],
                "pf": summary["profit_factor"],
                "median_cost_r": fmt(median(costs)) if costs else "n/a",
                "mean_cost_r": fmt(mean(costs)) if costs else "n/a",
                "best_day_removed_pnl_aed": fmt(pnl_after_removing_best_days(items, 1)),
            }
        )
    return table


def cost_cutoff_table(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    known = [row for row in rows if row.get("cost_join_status") == "COST_KNOWN"]
    cutoffs = [0.04, 0.05, 0.06, 0.07, 0.08, 0.09, 0.10, 0.11, 0.12, 0.13, 0.15]
    table = []
    for cutoff in cutoffs:
        kept = [row for row in known if (to_float(row.get("cost_r")) or 0.0) <= cutoff]
        blocked = [row for row in known if (to_float(row.get("cost_r")) or 0.0) > cutoff]
        kept_summary = summarize(kept)
        blocked_summary = summarize(blocked)
        table.append(
            {
                "cutoff": fmt(cutoff),
                "kept_rows": str(kept_summary["rows"]),
                "kept_wr": kept_summary["win_rate_pct"],
                "kept_pnl_aed": kept_summary["pnl_aed"],
                "blocked_rows": str(blocked_summary["rows"]),
                "blocked_pnl_aed": blocked_summary["pnl_aed"],
                "kept_best_day_removed_pnl_aed": fmt(pnl_after_removing_best_days(kept, 1)),
            }
        )
    return table


def cost_group_table(rows: list[dict[str, str]], keys: list[str]) -> list[dict[str, str]]:
    known = [row for row in rows if row.get("cost_join_status") == "COST_KNOWN"]
    grouped: dict[tuple[str, ...], list[dict[str, str]]] = defaultdict(list)
    for row in known:
        grouped[tuple(row.get(key, "") or "UNKNOWN" for key in keys)].append(row)
    table = []
    for key, items in grouped.items():
        summary = summarize(items)
        costs = [to_float(row.get("cost_r")) or 0.0 for row in items]
        table.append(
            {
                "group": " | ".join(key),
                "rows": str(summary["rows"]),
                "win_rate_pct": summary["win_rate_pct"],
                "pnl_aed": summary["pnl_aed"],
                "pf": summary["profit_factor"],
                "median_cost_r": fmt(median(costs)) if costs else "n/a",
                "mean_cost_r": fmt(mean(costs)) if costs else "n/a",
            }
        )
    return sorted(table, key=lambda item: to_float(item["pnl_aed"]) or 0.0)


def account_focus(rows: list[dict[str, str]]) -> dict[str, Any]:
    lab = [row for row in rows if row.get("account_role") == "A1_LAB_OBSERVATION"]
    production = [row for row in rows if row.get("account_role") == "A2_A3_PRODUCTION_STYLE"]
    a2 = [row for row in rows if row.get("account") == "1033030"]
    a3 = [row for row in rows if row.get("account") == "1033669"]
    views = [
        {"view": "A1 lab observation", **summary_with_rule_deltas(lab)},
        {"view": "A2+A3 production-style", **summary_with_rule_deltas(production)},
        {"view": "A2 clean account", **summary_with_rule_deltas(a2)},
        {"view": "A3 experiment account", **summary_with_rule_deltas(a3)},
    ]
    return {
        "views": views,
        "by_account": group_table(rows, ["account"]),
        "by_account_family": group_table(rows, ["account", "selected_family"]),
        "by_account_session": group_table(rows, ["account", "time_bucket"]),
        "note": (
            "A1 is treated as a broad/noisy lab account. A2 and A3 are treated as the production-style evidence lane. "
            "In this canonical XAU export, A2 has no closed XAU rows, so A2+A3 currently equals A3 only."
        ),
    }


def summary_with_rule_deltas(rows: list[dict[str, str]]) -> dict[str, str]:
    baseline = summarize(rows)
    no_round = [row for row in rows if row.get("selected_family") not in ROUND_FAMILY]
    breakout_core = [row for row in rows if row.get("selected_candidate") in BREAKOUT_CORE]
    protected = [
        row
        for row in rows
        if row.get("selected_candidate") in BREAKOUT_CORE and row.get("time_bucket") in EVENING_NIGHT
    ]
    no_afternoon = [row for row in rows if row.get("time_bucket") != "Afternoon 12:00-15:59"]
    return {
        "rows": str(baseline["rows"]),
        "win_rate_pct": baseline["win_rate_pct"],
        "pnl_aed": baseline["pnl_aed"],
        "pf": baseline["profit_factor"],
        "no_round_rows": str(len(no_round)),
        "no_round_pnl_aed": summarize(no_round)["pnl_aed"],
        "breakout_core_rows": str(len(breakout_core)),
        "breakout_core_pnl_aed": summarize(breakout_core)["pnl_aed"],
        "protected_breakout_en_rows": str(len(protected)),
        "protected_breakout_en_pnl_aed": summarize(protected)["pnl_aed"],
        "no_afternoon_pnl_aed": summarize(no_afternoon)["pnl_aed"],
    }


def rule_scorecard(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    baseline = summarize(rows)
    baseline_pnl = to_float(baseline["pnl_aed"]) or 0.0
    scenarios = [
        (
            "round_family_quarantine",
            lambda row: row.get("selected_family") not in ROUND_FAMILY,
            "Block selected round-family broker action; keep non-round selected rows.",
        ),
        (
            "breakout_core_only",
            lambda row: row.get("selected_candidate") in BREAKOUT_CORE,
            "Only selected breakout_retest and swing_breakout_retest_v0 rows.",
        ),
        (
            "protect_breakout_evening_night_cluster",
            lambda row: row.get("selected_candidate") in BREAKOUT_CORE and row.get("time_bucket") in EVENING_NIGHT,
            "Protected cluster view only; not a routing recommendation by itself.",
        ),
        (
            "no_afternoon",
            lambda row: row.get("time_bucket") != "Afternoon 12:00-15:59",
            "Remove all afternoon rows.",
        ),
        (
            "no_morning_afternoon",
            lambda row: row.get("time_bucket") not in MORNING_AFTERNOON,
            "Evening/night only across all selected rows.",
        ),
        (
            "cost_known_keep_lte_0_13",
            lambda row: row.get("cost_join_status") != "COST_KNOWN" or (to_float(row.get("cost_r")) or 999.0) <= 0.13,
            "Keep unknown-cost rows; block only known cost_r > 0.13.",
        ),
        (
            "round_quarantine_plus_cost_gt_0_13",
            lambda row: row.get("selected_family") not in ROUND_FAMILY
            and (row.get("cost_join_status") != "COST_KNOWN" or (to_float(row.get("cost_r")) or 999.0) <= 0.13),
            "Round quarantine plus worst-tier known cost veto.",
        ),
    ]
    table = []
    for name, keep_rule, note in scenarios:
        kept = [row for row in rows if keep_rule(row)]
        blocked = [row for row in rows if not keep_rule(row)]
        kept_summary = summarize(kept)
        blocked_summary = summarize(blocked)
        protected_before = protected_cluster(rows)
        protected_after = protected_cluster(kept)
        table.append(
            {
                "scenario": name,
                "kept_rows": str(kept_summary["rows"]),
                "kept_wr": kept_summary["win_rate_pct"],
                "kept_pnl_aed": kept_summary["pnl_aed"],
                "delta_vs_baseline_aed": fmt((to_float(kept_summary["pnl_aed"]) or 0.0) - baseline_pnl),
                "blocked_rows": str(blocked_summary["rows"]),
                "blocked_winners": str(blocked_summary["wins"]),
                "blocked_losses": str(blocked_summary["losses"]),
                "blocked_pnl_aed": blocked_summary["pnl_aed"],
                "kept_best_day_removed_pnl_aed": fmt(pnl_after_removing_best_days(kept, 1)),
                "protected_rows_removed": str(int(protected_before["rows"]) - int(protected_after["rows"])),
                "protected_pnl_removed_aed": fmt((to_float(protected_before["pnl_aed"]) or 0.0) - (to_float(protected_after["pnl_aed"]) or 0.0)),
                "note": note,
            }
        )
    return table


def protected_cluster(rows: list[dict[str, str]]) -> dict[str, str]:
    protected = [
        row
        for row in rows
        if row.get("selected_candidate") in BREAKOUT_CORE and row.get("time_bucket") in EVENING_NIGHT
    ]
    summary = summarize(protected)
    return {
        "definition": "selected breakout_retest or swing_breakout_retest_v0 in Evening/Night",
        "rows": str(summary["rows"]),
        "win_rate_pct": summary["win_rate_pct"],
        "pnl_aed": summary["pnl_aed"],
        "pf": summary["profit_factor"],
        "best_day_removed_pnl_aed": fmt(pnl_after_removing_best_days(protected, 1)),
        "best_two_days_removed_pnl_aed": fmt(pnl_after_removing_best_days(protected, 2)),
    }


def duplicate_exposure(rows: list[dict[str, str]]) -> dict[str, Any]:
    multirow = [row for row in rows if int(row.get("group_size") or "0") > 1]
    mixed = [row for row in rows if row.get("is_mixed_family_group") == "true"]
    mixed_breakout_round = [
        row
        for row in rows
        if row.get("has_breakout_core") == "true" and row.get("has_round_family") == "true"
    ]
    return {
        "multirow_groups": len(multirow),
        "multirow_group_pnl_aed": fmt(sum(to_float(row.get("selected_profit_aed")) or 0.0 for row in multirow)),
        "mixed_family_groups": len(mixed),
        "mixed_family_pnl_aed": fmt(sum(to_float(row.get("selected_profit_aed")) or 0.0 for row in mixed)),
        "breakout_round_mixed_groups": len(mixed_breakout_round),
        "breakout_round_mixed_pnl_aed": fmt(sum(to_float(row.get("selected_profit_aed")) or 0.0 for row in mixed_breakout_round)),
        "note": "Canonical rows already collapse same-minute symbol/direction/volume duplicates. Runtime exposure guard should still catch cross-family and adjacent-bar stacks before order send.",
    }


def conclusions() -> list[str]:
    return [
        "Round-family quarantine remains the strongest first promotion candidate.",
        "Evening/night breakout should be protected, but not converted into evening/night-only routing yet.",
        "Cost is useful as a worst-tier veto, but the exact threshold remains fragile and should stay shadow-only.",
        "Exposure control should use symbol + direction + bar + level band; family should remain an attribution field, not the exposure key.",
        "Hard short-block is still unproven until a down or range day is observed.",
    ]


def render_markdown(payload: dict[str, Any], rows_path: Path) -> str:
    lines: list[str] = [
        "# XAUUSD Canonical Loss-Avoidance Analysis - 2026-06-17",
        "",
        f"Status: `{payload['status']}`",
        "",
        payload["boundary"],
        "",
        "This report implements the post-Claude correction: family, session, duplicate, protected-cluster, and cost views are all tied back to the same canonical 586-row deduped XAUUSD universe. Cost conclusions use only the cost-known subset of that same universe.",
        "",
        "## Source Files",
        "",
        table([{"file": key, "path": value} for key, value in payload["source_files"].items()], ["file", "path"]),
        "",
        f"Enriched canonical rows CSV: `{rows_path}`",
        "",
        "## Universe",
        "",
        table([payload["universe"]], ["canonical_rows", "ticket_matched_rows", "cost_matched_rows", "cost_known_rows", "cost_missing_rows"]),
        "",
        "## Baseline",
        "",
        table([payload["baseline"]], ["rows", "wins", "losses", "flats", "win_rate_pct", "pnl_aed", "profit_factor", "avg_win_aed", "avg_loss_aed"]),
        "",
        "## Family View",
        "",
        table(payload["family"], ["group", "rows", "win_rate_pct", "pnl_aed", "pf", "best_day_removed_pnl_aed", "best_two_days_removed_pnl_aed"]),
        "",
        "## Candidate View",
        "",
        table(payload["candidate"], ["group", "rows", "win_rate_pct", "pnl_aed", "pf", "best_day_removed_pnl_aed", "best_two_days_removed_pnl_aed"]),
        "",
        "## Session View",
        "",
        table(payload["session"], ["group", "rows", "win_rate_pct", "pnl_aed", "pf", "best_day_removed_pnl_aed", "best_two_days_removed_pnl_aed"]),
        "",
        "## Afternoon Round-Family Diagnosis",
        "",
        "This is the focused decision view requested after the Review 12/Claude correction. It tests whether the afternoon loss is truly an afternoon problem, or mostly a round-family problem that happens to cluster in the afternoon.",
        "",
        table(
            [payload["afternoon_round_family_diagnosis"]],
            [
                "session",
                "dedup_universe_rows",
                "afternoon_rows",
                "afternoon_pnl_aed",
                "round_family_afternoon_rows",
                "round_family_afternoon_pnl_aed",
                "round_family_loss_share_of_afternoon_loss_pct",
                "residual_after_round_quarantine_rows",
                "residual_after_round_quarantine_pnl_aed",
                "protected_evening_night_rows_removed",
                "protected_evening_night_pnl_removed_aed",
                "runtime_authorized",
            ],
        ),
        "",
        table(
            payload["afternoon_round_family_diagnosis"]["rows"],
            [
                "segment",
                "rows",
                "win_rate_pct",
                "pnl_aed",
                "pf",
                "loss_share_of_afternoon_loss_pct",
                "best_day_removed_pnl_aed",
                "best_two_days_removed_pnl_aed",
                "interpretation",
            ],
        ),
        "",
        f"Decision: {payload['afternoon_round_family_diagnosis']['decision']}",
        "",
        "## Cost View On The Same Universe",
        "",
        "Cost rows below are the cost-known subset of the canonical 586-row universe. Missing-cost rows are not silently mixed into threshold claims.",
        "",
        "### Cost Buckets",
        "",
        table(payload["cost_by_bucket"], ["bucket", "rows", "win_rate_pct", "pnl_aed", "pf", "median_cost_r", "mean_cost_r", "best_day_removed_pnl_aed"]),
        "",
        "### Cost Cutoffs",
        "",
        table(payload["cost_cutoffs"], ["cutoff", "kept_rows", "kept_wr", "kept_pnl_aed", "blocked_rows", "blocked_pnl_aed", "kept_best_day_removed_pnl_aed"]),
        "",
        "### Cost By Family",
        "",
        table(payload["cost_by_family"], ["group", "rows", "win_rate_pct", "pnl_aed", "pf", "median_cost_r", "mean_cost_r"]),
        "",
        "## Account Focus: Lab vs Production-Style",
        "",
        payload["account_focus"]["note"],
        "",
        table(payload["account_focus"]["views"], ["view", "rows", "win_rate_pct", "pnl_aed", "pf", "no_round_rows", "no_round_pnl_aed", "breakout_core_rows", "breakout_core_pnl_aed", "protected_breakout_en_rows", "protected_breakout_en_pnl_aed", "no_afternoon_pnl_aed"]),
        "",
        "### By Account",
        "",
        table(payload["account_focus"]["by_account"], ["group", "rows", "win_rate_pct", "pnl_aed", "pf", "best_day_removed_pnl_aed", "best_two_days_removed_pnl_aed"]),
        "",
        "### By Account And Family",
        "",
        table(payload["account_focus"]["by_account_family"], ["group", "rows", "win_rate_pct", "pnl_aed", "pf", "best_day_removed_pnl_aed", "best_two_days_removed_pnl_aed"]),
        "",
        "## Rule Scorecard",
        "",
        "Positive `delta_vs_baseline_aed` means the retrospective filter improved the canonical duplicate-hidden baseline. This is not permission to change runtime; it is a review packet.",
        "",
        table(payload["rule_scorecard"], ["scenario", "kept_rows", "kept_wr", "kept_pnl_aed", "delta_vs_baseline_aed", "blocked_rows", "blocked_winners", "blocked_losses", "blocked_pnl_aed", "kept_best_day_removed_pnl_aed", "protected_rows_removed", "protected_pnl_removed_aed"]),
        "",
        "## Protected Cluster",
        "",
        table([payload["protected_cluster"]], ["definition", "rows", "win_rate_pct", "pnl_aed", "pf", "best_day_removed_pnl_aed", "best_two_days_removed_pnl_aed"]),
        "",
        "## Duplicate Exposure",
        "",
        table([payload["duplicate_exposure"]], ["multirow_groups", "multirow_group_pnl_aed", "mixed_family_groups", "mixed_family_pnl_aed", "breakout_round_mixed_groups", "breakout_round_mixed_pnl_aed", "note"]),
        "",
        "## Conclusions",
        "",
    ]
    lines.extend(f"- {item}" for item in payload["conclusions"])
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "Review only. No MT5 runtime, EA, preset, order, chart, profile, or account change is authorized by this report.",
            "",
        ]
    )
    return "\n".join(lines)


def _cost_index(rows: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    index = {}
    for row in rows:
        key = _cost_key(
            row.get("entry_time_dubai", ""),
            row.get("symbol", ""),
            row.get("direction", ""),
            row.get("candidate", ""),
            row.get("entry", ""),
        )
        index.setdefault(key, row)
    return index


def _cost_key_from_actual(row: dict[str, str] | None) -> str:
    if row is None:
        return ""
    return _cost_key(
        row.get("entry_time", ""),
        row.get("symbol", ""),
        row.get("direction", ""),
        row.get("candidate", ""),
        row.get("entry_price", ""),
    )


def _cost_key(entry_time: str, symbol: str, direction: str, candidate: str, entry: str) -> str:
    return "|".join([entry_time, symbol, direction, candidate, fmt_price(entry)])


def pnl_after_removing_best_days(rows: list[dict[str, str]], days_to_remove: int) -> float:
    by_day: dict[str, float] = defaultdict(float)
    for row in rows:
        by_day[row.get("entry_date", "")] += to_float(row.get("selected_profit_aed")) or 0.0
    ordered = sorted(by_day.items(), key=lambda item: item[1], reverse=True)
    remove_days = {day for day, _ in ordered[:days_to_remove]}
    return sum(value for day, value in by_day.items() if day not in remove_days)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, str]], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def enriched_fields() -> list[str]:
    return [
        "dedup_key",
        "entry_minute",
        "entry_date",
        "entry_time",
        "time_bucket",
        "account",
        "account_role",
        "lane",
        "symbol",
        "direction",
        "volume",
        "selected_candidate",
        "selected_family",
        "selected_status",
        "selected_position_ticket",
        "selected_profit_aed",
        "selected_outcome",
        "group_size",
        "duplicate_count",
        "group_raw_profit_aed",
        "candidate_members",
        "family_members",
        "has_round_family",
        "has_breakout_core",
        "has_p2weakness",
        "actual_join_status",
        "entry_price",
        "sl",
        "tp",
        "magic",
        "entry_comment",
        "exit_comment",
        "cost_join_status",
        "cost_r",
        "spread_points",
        "stop_distance_points",
        "result_r",
        "is_breakout_core",
        "is_round_family",
        "is_evening_night",
        "is_morning_afternoon",
        "is_protected_breakout_cluster",
        "is_mixed_family_group",
    ]


def table(rows: list[dict[str, Any]], columns: list[str]) -> str:
    if not rows:
        return "_No rows._"
    output = [
        "| " + " | ".join(columns) + " |",
        "| " + " | ".join("---" for _ in columns) + " |",
    ]
    for row in rows:
        output.append("| " + " | ".join(str(row.get(column, "")) for column in columns) + " |")
    return "\n".join(output)


def to_float(value: Any) -> float | None:
    if value is None:
        return None
    text = str(value).strip()
    if text == "" or text.lower() == "n/a":
        return None
    try:
        return float(text)
    except ValueError:
        return None


def fmt(value: Any) -> str:
    number = to_float(value)
    if number is None:
        return "n/a"
    return f"{number:.2f}"


def fmt_price(value: Any) -> str:
    number = to_float(value)
    if number is None:
        return ""
    return f"{number:.5f}"


def pct(numerator: int, denominator: int) -> str:
    if denominator == 0:
        return "n/a"
    return f"{100.0 * numerator / denominator:.2f}%"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate canonical XAUUSD loss-avoidance analysis.")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--canonical-rows-csv", type=Path)
    parser.add_argument("--actual-trades-csv", type=Path)
    parser.add_argument("--cost-trades-csv", type=Path)
    parser.add_argument("--output-prefix", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    outputs = generate_report(
        args.root,
        canonical_rows_csv=args.canonical_rows_csv,
        actual_trades_csv=args.actual_trades_csv,
        cost_trades_csv=args.cost_trades_csv,
        output_prefix=args.output_prefix,
    )
    for label, path in outputs.items():
        print(f"{label}: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
