from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


DEFAULT_ACTUAL_TRADES = Path("outputs") / "reports" / "PHASE2_DEMO_ACTUAL_BROKER_TRADES.csv"
DEFAULT_OUTPUT_PREFIX = Path("outputs") / "reports" / "XAUUSD_DEDUPED_REAL_FILL_EVIDENCE_2026_06_16"

ROUND_FAMILY = {"round_number_retest_v0", "symbol_normalized_round_retest_v0"}
BREAKOUT_CORE = {"breakout_retest", "swing_breakout_retest_v0"}
WATCHLIST_SMALL_SAMPLE = {"p2weakness_br_v1", "session_extreme_retest_v0_repair_v1"}

DEDUP_KEEP_PRIORITY = {
    "breakout_retest": 10,
    "swing_breakout_retest_v0": 20,
    "symbol_normalized_round_retest_v0": 30,
    "round_number_retest_v0": 40,
    "session_extreme_retest_v0": 50,
    "p2weakness_br_v1": 60,
    "symbol_normalized_round_retest_v0_repair_v1": 65,
    "session_extreme_retest_v0_repair_v1": 66,
    "WR50_BreakoutEvening_v0": 70,
    "WR50_BreakoutQuality_v0": 80,
    "WR50_BreakoutExit1R_v0": 90,
}


def generate_xauusd_deduped_evidence(
    phase1_root: Path,
    *,
    actual_trades_csv: Path | None = None,
    output_prefix: Path | None = None,
) -> Path:
    phase1_root = phase1_root.resolve()
    actual_trades_csv = (actual_trades_csv or phase1_root / DEFAULT_ACTUAL_TRADES).resolve()
    output_prefix = (output_prefix or phase1_root / DEFAULT_OUTPUT_PREFIX).resolve()

    raw_rows = [
        _normalise_row(row)
        for row in _read_csv(actual_trades_csv)
        if row.get("state") == "CLOSED" and str(row.get("symbol", "")).upper().startswith("XAU")
    ]
    groups = _dedup_groups(raw_rows)
    dedup_rows = [_group_summary(group_key, items) for group_key, items in groups.items()]

    payload = {
        "status": "PASS" if raw_rows else "NO_CLOSED_XAUUSD_ROWS",
        "created_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "authority": (
            "Analysis-only XAUUSD real-fill evidence recut. It reads exported broker fills only and does not touch "
            "MT5 runtime, charts, orders, positions, presets, or running EAs."
        ),
        "actual_trades_csv": str(actual_trades_csv),
        "dedup_definition": "same entry minute + symbol + direction + volume",
        "raw_baseline": _summary(raw_rows, value_key="profit_aed"),
        "dedup_baseline": _summary(dedup_rows, value_key="selected_profit_aed"),
        "duplicate_inflation": _duplicate_inflation(raw_rows, dedup_rows),
        "candidate_raw_vs_dedup_selected": _candidate_raw_vs_dedup(raw_rows, dedup_rows),
        "family_dedup_selected": _group_table(dedup_rows, ["selected_family"]),
        "session_dedup_selected": _group_table(dedup_rows, ["time_bucket"]),
        "direction_session_dedup_selected": _group_table(dedup_rows, ["direction", "time_bucket"]),
        "candidate_session_dedup_selected": _group_table(dedup_rows, ["selected_candidate", "time_bucket"], min_rows=3),
        "counterfactuals": _counterfactuals(raw_rows, dedup_rows),
        "best_day_stress": _best_day_stress(dedup_rows),
        "protected_cluster_impact": _protected_cluster_impact(dedup_rows),
        "watchlist_artifact_checks": _watchlist_artifact_checks(raw_rows, dedup_rows),
        "dedup_rows": dedup_rows,
    }

    json_path = output_prefix.with_suffix(".json")
    md_path = output_prefix.with_suffix(".md")
    csv_path = output_prefix.with_name(output_prefix.name + "_ROWS").with_suffix(".csv")
    output_prefix.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    _write_csv(csv_path, dedup_rows, _dedup_fields())
    md_path.write_text(_render_markdown(payload, csv_path), encoding="utf-8")
    return json_path


def _normalise_row(row: dict[str, str]) -> dict[str, str]:
    normalised = dict(row)
    normalised["profit_aed"] = _fmt(_float(row.get("profit_aed")) or 0.0)
    normalised["duplicate_key_recomputed"] = _duplicate_key(row)
    normalised["entry_date"] = str(row.get("entry_time", ""))[:10]
    normalised["family"] = _family(row.get("candidate", ""))
    return normalised


def _dedup_groups(rows: list[dict[str, str]]) -> dict[str, list[dict[str, str]]]:
    groups: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        groups[row["duplicate_key_recomputed"]].append(row)
    return groups


def _group_summary(group_key: str, items: list[dict[str, str]]) -> dict[str, str]:
    selected = min(
        items,
        key=lambda row: (
            DEDUP_KEEP_PRIORITY.get(row.get("candidate", ""), 999),
            row.get("position_ticket", ""),
        ),
    )
    raw_group_pnl = sum(_float(row.get("profit_aed")) or 0.0 for row in items)
    candidates = sorted({row.get("candidate", "") for row in items})
    families = sorted({_family(row.get("candidate", "")) for row in items})
    return {
        "dedup_key": group_key,
        "entry_minute": str(selected.get("entry_time", ""))[:16],
        "entry_date": str(selected.get("entry_time", ""))[:10],
        "time_bucket": selected.get("time_bucket", ""),
        "symbol": selected.get("symbol", ""),
        "direction": selected.get("direction", ""),
        "volume": selected.get("volume", ""),
        "selected_candidate": selected.get("candidate", ""),
        "selected_family": _family(selected.get("candidate", "")),
        "selected_status": selected.get("status", ""),
        "selected_position_ticket": selected.get("position_ticket", ""),
        "selected_profit_aed": _fmt(_float(selected.get("profit_aed")) or 0.0),
        "selected_outcome": _outcome(selected),
        "group_size": str(len(items)),
        "duplicate_count": str(max(0, len(items) - 1)),
        "group_raw_profit_aed": _fmt(raw_group_pnl),
        "candidate_members": ";".join(candidates),
        "family_members": ";".join(families),
        "has_round_family": "true" if any(row.get("candidate") in ROUND_FAMILY for row in items) else "false",
        "has_breakout_core": "true" if any(row.get("candidate") in BREAKOUT_CORE for row in items) else "false",
        "has_p2weakness": "true" if any(row.get("candidate") == "p2weakness_br_v1" for row in items) else "false",
    }


def _summary(rows: list[dict[str, str]], *, value_key: str) -> dict[str, Any]:
    values = [_float(row.get(value_key)) or 0.0 for row in rows]
    wins = [value for value in values if value > 0.0]
    losses = [value for value in values if value < 0.0]
    return {
        "rows": len(rows),
        "wins": len(wins),
        "losses": len(losses),
        "win_rate_pct": _pct(len(wins), len(wins) + len(losses)),
        "pnl_aed": _fmt(sum(values)),
        "avg_win_aed": _fmt(sum(wins) / len(wins)) if wins else "n/a",
        "avg_loss_aed": _fmt(sum(losses) / len(losses)) if losses else "n/a",
        "profit_factor": _fmt(sum(wins) / abs(sum(losses))) if losses and sum(losses) else ("inf" if wins else "n/a"),
    }


def _duplicate_inflation(raw_rows: list[dict[str, str]], dedup_rows: list[dict[str, str]]) -> dict[str, Any]:
    raw = _summary(raw_rows, value_key="profit_aed")
    dedup = _summary(dedup_rows, value_key="selected_profit_aed")
    duplicate_rows = len(raw_rows) - len(dedup_rows)
    return {
        "raw_rows": len(raw_rows),
        "dedup_rows": len(dedup_rows),
        "duplicate_rows_removed": duplicate_rows,
        "raw_pnl_aed": raw["pnl_aed"],
        "dedup_selected_pnl_aed": dedup["pnl_aed"],
        "raw_minus_dedup_pnl_aed": _fmt((_float(raw["pnl_aed"]) or 0.0) - (_float(dedup["pnl_aed"]) or 0.0)),
        "row_inflation_multiple": _fmt(len(raw_rows) / len(dedup_rows)) if dedup_rows else "n/a",
    }


def _candidate_raw_vs_dedup(raw_rows: list[dict[str, str]], dedup_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    candidates = sorted({row.get("candidate", "") for row in raw_rows} | {row.get("selected_candidate", "") for row in dedup_rows})
    output = []
    for candidate in candidates:
        raw_items = [row for row in raw_rows if row.get("candidate") == candidate]
        dedup_items = [row for row in dedup_rows if row.get("selected_candidate") == candidate]
        raw_summary = _summary(raw_items, value_key="profit_aed")
        dedup_summary = _summary(dedup_items, value_key="selected_profit_aed")
        output.append(
            {
                "candidate": candidate,
                "raw_trades": str(raw_summary["rows"]),
                "raw_win_rate_pct": raw_summary["win_rate_pct"],
                "raw_pnl_aed": raw_summary["pnl_aed"],
                "dedup_selected_trades": str(dedup_summary["rows"]),
                "dedup_selected_win_rate_pct": dedup_summary["win_rate_pct"],
                "dedup_selected_pnl_aed": dedup_summary["pnl_aed"],
                "raw_minus_dedup_pnl_aed": _fmt((_float(raw_summary["pnl_aed"]) or 0.0) - (_float(dedup_summary["pnl_aed"]) or 0.0)),
            }
        )
    return sorted(output, key=lambda row: _float(row["dedup_selected_pnl_aed"]) or 0.0)


def _group_table(rows: list[dict[str, str]], keys: list[str], *, min_rows: int = 1) -> list[dict[str, str]]:
    grouped: dict[tuple[str, ...], list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        grouped[tuple(row.get(key, "") or "UNKNOWN" for key in keys)].append(row)
    output = []
    for key, items in grouped.items():
        if len(items) < min_rows:
            continue
        summary = _summary(items, value_key="selected_profit_aed")
        output.append(
            {
                "group": " | ".join(key),
                "rows": str(summary["rows"]),
                "win_rate_pct": summary["win_rate_pct"],
                "pnl_aed": summary["pnl_aed"],
                "best_day_removed_pnl_aed": _fmt(_pnl_after_removing_best_days(items, 1)),
                "best_two_days_removed_pnl_aed": _fmt(_pnl_after_removing_best_days(items, 2)),
            }
        )
    return sorted(output, key=lambda row: _float(row["pnl_aed"]) or 0.0)


def _counterfactuals(raw_rows: list[dict[str, str]], dedup_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    scenarios: list[tuple[str, list[dict[str, str]], str, str]] = [
        ("raw_all_xau", raw_rows, "profit_aed", "Raw broker fills; duplicate stacks included."),
        ("dedup_all_xau", dedup_rows, "selected_profit_aed", "One selected representative per unique signal."),
        (
            "dedup_remove_round_selected",
            [row for row in dedup_rows if row.get("selected_candidate") not in ROUND_FAMILY],
            "selected_profit_aed",
            "Drops unique groups where the selected representative is a round-family EA.",
        ),
        (
            "dedup_breakout_core_only",
            [row for row in dedup_rows if row.get("selected_candidate") in BREAKOUT_CORE],
            "selected_profit_aed",
            "Only selected breakout_retest or swing_breakout_retest_v0 representatives.",
        ),
        (
            "dedup_breakout_evening_night_only",
            [
                row
                for row in dedup_rows
                if row.get("selected_candidate") in BREAKOUT_CORE
                and row.get("time_bucket") in {"Evening 16:00-19:59", "Night 20:00-05:59"}
            ],
            "selected_profit_aed",
            "Selected breakout core only in evening/night.",
        ),
        (
            "dedup_no_afternoon",
            [row for row in dedup_rows if row.get("time_bucket") != "Afternoon 12:00-15:59"],
            "selected_profit_aed",
            "Drops all selected afternoon representatives.",
        ),
        (
            "dedup_no_morning_afternoon",
            [row for row in dedup_rows if row.get("time_bucket") not in {"Morning 06:00-11:59", "Afternoon 12:00-15:59"}],
            "selected_profit_aed",
            "Selected evening/night representatives only.",
        ),
    ]
    rows = []
    for name, items, value_key, note in scenarios:
        summary = _summary(items, value_key=value_key)
        rows.append(
            {
                "scenario": name,
                "rows": str(summary["rows"]),
                "win_rate_pct": summary["win_rate_pct"],
                "pnl_aed": summary["pnl_aed"],
                "best_day_removed_pnl_aed": _fmt(_pnl_after_removing_best_days(items, 1, value_key=value_key)),
                "best_two_days_removed_pnl_aed": _fmt(_pnl_after_removing_best_days(items, 2, value_key=value_key)),
                "note": note,
            }
        )
    return rows


def _best_day_stress(dedup_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    scenarios = [
        ("dedup_all_xau", dedup_rows),
        ("dedup_remove_round_selected", [row for row in dedup_rows if row.get("selected_candidate") not in ROUND_FAMILY]),
        ("dedup_breakout_core_only", [row for row in dedup_rows if row.get("selected_candidate") in BREAKOUT_CORE]),
    ]
    output = []
    for name, rows in scenarios:
        day_pnl = _day_pnl(rows)
        best_days = sorted(day_pnl.items(), key=lambda item: item[1], reverse=True)
        worst_days = sorted(day_pnl.items(), key=lambda item: item[1])
        output.append(
            {
                "scenario": name,
                "days": str(len(day_pnl)),
                "total_pnl_aed": _fmt(sum(day_pnl.values())),
                "best_day": best_days[0][0] if best_days else "",
                "best_day_pnl_aed": _fmt(best_days[0][1]) if best_days else "",
                "best_day_removed_pnl_aed": _fmt(_pnl_after_removing_best_days(rows, 1)),
                "best_two_days_removed_pnl_aed": _fmt(_pnl_after_removing_best_days(rows, 2)),
                "worst_day": worst_days[0][0] if worst_days else "",
                "worst_day_pnl_aed": _fmt(worst_days[0][1]) if worst_days else "",
            }
        )
    return output


def _protected_cluster_impact(dedup_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    protected = [
        row
        for row in dedup_rows
        if row.get("selected_candidate") in BREAKOUT_CORE
        and row.get("time_bucket") in {"Evening 16:00-19:59", "Night 20:00-05:59"}
    ]
    scenarios = [
        ("round_family_quarantine", protected, [row for row in protected if row.get("selected_candidate") not in ROUND_FAMILY]),
        ("no_afternoon", protected, [row for row in protected if row.get("time_bucket") != "Afternoon 12:00-15:59"]),
        (
            "evening_night_only",
            protected,
            [row for row in protected if row.get("time_bucket") in {"Evening 16:00-19:59", "Night 20:00-05:59"}],
        ),
    ]
    output = []
    for name, before, after in scenarios:
        before_summary = _summary(before, value_key="selected_profit_aed")
        after_summary = _summary(after, value_key="selected_profit_aed")
        output.append(
            {
                "rule": name,
                "protected_rows_before": str(before_summary["rows"]),
                "protected_rows_after": str(after_summary["rows"]),
                "protected_rows_removed": str(before_summary["rows"] - after_summary["rows"]),
                "protected_pnl_before_aed": before_summary["pnl_aed"],
                "protected_pnl_after_aed": after_summary["pnl_aed"],
                "protected_pnl_removed_aed": _fmt((_float(before_summary["pnl_aed"]) or 0.0) - (_float(after_summary["pnl_aed"]) or 0.0)),
            }
        )
    return output


def _watchlist_artifact_checks(raw_rows: list[dict[str, str]], dedup_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    output = []
    for candidate in sorted(WATCHLIST_SMALL_SAMPLE):
        raw_items = [row for row in raw_rows if row.get("candidate") == candidate]
        selected = [row for row in dedup_rows if row.get("selected_candidate") == candidate]
        participated = [row for row in dedup_rows if candidate in row.get("candidate_members", "").split(";")]
        output.append(
            {
                "candidate": candidate,
                "raw_trades": str(len(raw_items)),
                "raw_pnl_aed": _summary(raw_items, value_key="profit_aed")["pnl_aed"],
                "dedup_selected_trades": str(len(selected)),
                "dedup_selected_pnl_aed": _summary(selected, value_key="selected_profit_aed")["pnl_aed"],
                "dedup_participating_unique_signals": str(len(participated)),
                "participation_selected_ratio": _pct(len(selected), len(participated)),
                "interpretation": "watch_only_small_or_duplicate_inflated",
            }
        )
    return output


def _pnl_after_removing_best_days(rows: list[dict[str, str]], n: int, *, value_key: str = "selected_profit_aed") -> float:
    day_pnl = _day_pnl(rows, value_key=value_key)
    remove_days = {day for day, _value in sorted(day_pnl.items(), key=lambda item: item[1], reverse=True)[:n]}
    return sum(value for day, value in day_pnl.items() if day not in remove_days)


def _day_pnl(rows: list[dict[str, str]], *, value_key: str = "selected_profit_aed") -> dict[str, float]:
    totals: dict[str, float] = defaultdict(float)
    for row in rows:
        totals[row.get("entry_date", "") or "UNKNOWN"] += _float(row.get(value_key)) or 0.0
    return dict(totals)


def _family(candidate: str | None) -> str:
    value = str(candidate or "")
    if value in BREAKOUT_CORE:
        return "breakout_core"
    if value in ROUND_FAMILY:
        return "round_family"
    if value == "p2weakness_br_v1":
        return "p2weakness"
    if value == "session_extreme_retest_v0":
        return "session_extreme"
    if value.endswith("_repair_v1"):
        return "repair"
    if value.startswith("WR50_"):
        return "wr50"
    return "other"


def _outcome(row: dict[str, str]) -> str:
    profit = _float(row.get("profit_aed"))
    if profit is None:
        return "UNKNOWN"
    if profit > 0.0:
        return "WIN"
    if profit < 0.0:
        return "LOSS"
    return "FLAT"


def _duplicate_key(row: dict[str, str]) -> str:
    entry_minute = str(row.get("entry_time", ""))[:16]
    symbol = str(row.get("symbol", "")).upper()
    direction = str(row.get("direction", "")).upper()
    volume = str(row.get("volume", ""))
    return "|".join([entry_minute, symbol, direction, volume])


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


def _dedup_fields() -> list[str]:
    return [
        "dedup_key",
        "entry_minute",
        "entry_date",
        "time_bucket",
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
    ]


def _render_markdown(payload: dict[str, Any], csv_path: Path) -> str:
    raw = payload["raw_baseline"]
    dedup = payload["dedup_baseline"]
    inflation = payload["duplicate_inflation"]
    lines = [
        "# XAUUSD Deduped Real-Fill Evidence - 2026-06-16",
        "",
        f"Status: `{payload['status']}`",
        "",
        payload["authority"],
        "",
        f"Actual trades CSV: `{payload['actual_trades_csv']}`",
        f"Deduped rows CSV: `{csv_path}`",
        f"Dedup definition: `{payload['dedup_definition']}`",
        "",
        "## Baseline Recut",
        "",
        "| View | Rows | Win Rate | PnL AED | Profit Factor |",
        "| --- | ---: | ---: | ---: | ---: |",
        f"| Raw closed XAUUSD fills | {raw['rows']} | {raw['win_rate_pct']} | {raw['pnl_aed']} | {raw['profit_factor']} |",
        f"| Deduped selected unique signals | {dedup['rows']} | {dedup['win_rate_pct']} | {dedup['pnl_aed']} | {dedup['profit_factor']} |",
        "",
        "## Duplicate Inflation",
        "",
        _table([inflation], ["raw_rows", "dedup_rows", "duplicate_rows_removed", "row_inflation_multiple", "raw_pnl_aed", "dedup_selected_pnl_aed", "raw_minus_dedup_pnl_aed"]),
        "",
        "Interpretation: use deduped rows for decision-making. Raw PnL is still useful for account accounting, but not for judging whether a signal family has edge.",
        "",
        "## Candidate Raw vs Dedup-Selected",
        "",
        _table(payload["candidate_raw_vs_dedup_selected"], ["candidate", "raw_trades", "raw_win_rate_pct", "raw_pnl_aed", "dedup_selected_trades", "dedup_selected_win_rate_pct", "dedup_selected_pnl_aed", "raw_minus_dedup_pnl_aed"]),
        "",
        "## Deduped Family View",
        "",
        _table(payload["family_dedup_selected"], ["group", "rows", "win_rate_pct", "pnl_aed", "best_day_removed_pnl_aed", "best_two_days_removed_pnl_aed"]),
        "",
        "## Deduped Session View",
        "",
        _table(payload["session_dedup_selected"], ["group", "rows", "win_rate_pct", "pnl_aed", "best_day_removed_pnl_aed", "best_two_days_removed_pnl_aed"]),
        "",
        "## Deduped Direction x Session View",
        "",
        _table(payload["direction_session_dedup_selected"], ["group", "rows", "win_rate_pct", "pnl_aed", "best_day_removed_pnl_aed", "best_two_days_removed_pnl_aed"]),
        "",
        "## Deduped Candidate x Session View",
        "",
        _table(payload["candidate_session_dedup_selected"], ["group", "rows", "win_rate_pct", "pnl_aed", "best_day_removed_pnl_aed", "best_two_days_removed_pnl_aed"]),
        "",
        "## Counterfactuals",
        "",
        _table(payload["counterfactuals"], ["scenario", "rows", "win_rate_pct", "pnl_aed", "best_day_removed_pnl_aed", "best_two_days_removed_pnl_aed", "note"]),
        "",
        "## Best-Day Stress",
        "",
        _table(payload["best_day_stress"], ["scenario", "days", "total_pnl_aed", "best_day", "best_day_pnl_aed", "best_day_removed_pnl_aed", "best_two_days_removed_pnl_aed", "worst_day", "worst_day_pnl_aed"]),
        "",
        "## Protected Breakout-Cluster Impact",
        "",
        "Protected cluster is selected `breakout_retest` or `swing_breakout_retest_v0` in evening/night.",
        "",
        _table(payload["protected_cluster_impact"], ["rule", "protected_rows_before", "protected_rows_after", "protected_rows_removed", "protected_pnl_before_aed", "protected_pnl_after_aed", "protected_pnl_removed_aed"]),
        "",
        "## Watchlist Artifact Checks",
        "",
        _table(payload["watchlist_artifact_checks"], ["candidate", "raw_trades", "raw_pnl_aed", "dedup_selected_trades", "dedup_selected_pnl_aed", "dedup_participating_unique_signals", "participation_selected_ratio", "interpretation"]),
        "",
        "## Decision Notes",
        "",
        "- Round-family quarantine remains the first shadow-test candidate, but its benefit should be judged on deduped real fills.",
        "- `p2weakness_br_v1` and repair lanes should remain watchlist items until they have enough deduped independent signals.",
        "- Direction/session findings must not be converted into static long/short rules. Use dynamic trend-alignment shadow tags first.",
        "- Any proposed rule must report protected-breakout impact and best-day-removed performance before runtime promotion.",
        "",
        "## Boundary",
        "",
        "- Analysis-only.",
        "- Real broker fills only.",
        "- No MT5 runtime, chart, order, position, preset, magic-number, or EA behavior changes.",
        "",
    ]
    return "\n".join(lines)


def _table(rows: list[dict[str, Any]], columns: list[str]) -> str:
    if not rows:
        return "_No rows._"
    table = [
        "| " + " | ".join(columns) + " |",
        "| " + " | ".join("---" for _ in columns) + " |",
    ]
    for row in rows:
        table.append("| " + " | ".join(str(row.get(column, "")) for column in columns) + " |")
    return "\n".join(table)


def _float(value: str | None) -> float | None:
    try:
        return float(str(value or "").replace(",", "").strip())
    except ValueError:
        return None


def _fmt(value: float | None) -> str:
    if value is None:
        return ""
    return f"{value:.2f}"


def _pct(numerator: int, denominator: int) -> str:
    if denominator <= 0:
        return "n/a"
    return f"{(numerator / denominator * 100.0):.2f}%"


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate XAUUSD deduped real-fill evidence.")
    parser.add_argument("--phase1-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--actual-trades-csv", type=Path, default=None)
    parser.add_argument("--output-prefix", type=Path, default=None)
    args = parser.parse_args()
    output = generate_xauusd_deduped_evidence(
        args.phase1_root,
        actual_trades_csv=args.actual_trades_csv,
        output_prefix=args.output_prefix,
    )
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
