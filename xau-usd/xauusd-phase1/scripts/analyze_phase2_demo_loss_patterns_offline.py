from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Any


LOSS_REVIEW_VERDICT = "PHASE2_DEMO_LOSS_REVIEW_VERDICT_2026_06_04.md"
SHADOW_FORWARD_TEST_PLAN = "PHASE2_DEMO_SHADOW_FORWARD_TEST_PLAN_2026_06_04.md"
DUPLICATE_FAMILY_ANALYSIS = "PHASE2_DEMO_DUPLICATE_FAMILY_ANALYSIS_2026_06_04.md"


@dataclass(frozen=True)
class OfflineAnalysisOutput:
    loss_review_path: Path
    shadow_plan_path: Path
    duplicate_analysis_path: Path


def analyze_loss_patterns_offline(
    trades_csv: Path,
    output_dir: Path,
) -> OfflineAnalysisOutput:
    trades_csv = trades_csv.resolve()
    output_dir = output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    trades = [normalize_row(row) for row in read_csv(trades_csv)]
    dedup_rows = [row for row in trades if not is_true(row.get("is_duplicate"))]
    shadow_rows = [with_shadow_rule(row) for row in dedup_rows]
    kept_rows = [row for row in shadow_rows if row["shadow_action"] == "KEEP"]
    blocked_rows = [row for row in shadow_rows if row["shadow_action"] == "BLOCK"]
    duplicate_groups = build_duplicate_groups(trades)

    raw_summary = summarize(trades)
    dedup_summary = summarize(dedup_rows)
    kept_summary = summarize(kept_rows)
    blocked_summary = summarize(blocked_rows)
    duplicate_summary = summarize(trades)

    source_artifacts = related_source_artifacts(trades_csv)
    loss_review_path = output_dir / LOSS_REVIEW_VERDICT
    shadow_plan_path = output_dir / SHADOW_FORWARD_TEST_PLAN
    duplicate_analysis_path = output_dir / DUPLICATE_FAMILY_ANALYSIS

    loss_review_path.write_text(
        render_loss_review_verdict(
            source_artifacts=source_artifacts,
            raw_summary=raw_summary,
            dedup_summary=dedup_summary,
            kept_summary=kept_summary,
            blocked_summary=blocked_summary,
            dedup_rows=dedup_rows,
        ),
        encoding="utf-8",
    )
    shadow_plan_path.write_text(
        render_shadow_forward_test_plan(
            source_artifacts=source_artifacts,
            dedup_summary=dedup_summary,
            kept_summary=kept_summary,
            blocked_summary=blocked_summary,
            shadow_rows=shadow_rows,
        ),
        encoding="utf-8",
    )
    duplicate_analysis_path.write_text(
        render_duplicate_family_analysis(
            source_artifacts=source_artifacts,
            actual_summary=duplicate_summary,
            dedup_summary=dedup_summary,
            duplicate_groups=duplicate_groups,
        ),
        encoding="utf-8",
    )
    return OfflineAnalysisOutput(
        loss_review_path=loss_review_path,
        shadow_plan_path=shadow_plan_path,
        duplicate_analysis_path=duplicate_analysis_path,
    )


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def normalize_row(row: dict[str, str]) -> dict[str, str]:
    normalized = dict(row)
    normalized.setdefault("time_bucket", time_bucket(normalized.get("entry_time", "")))
    if not normalized.get("time_bucket"):
        normalized["time_bucket"] = time_bucket(normalized.get("entry_time", ""))
    normalized.setdefault("outcome", outcome(normalized))
    if not normalized.get("outcome"):
        normalized["outcome"] = outcome(normalized)
    normalized.setdefault("volume", "n/a")
    return normalized


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


def is_true(value: Any) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def to_float(value: Any) -> float:
    try:
        return float(value or 0.0)
    except (TypeError, ValueError):
        return 0.0


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
        "net_including_open_aed": round(closed_pnl + floating, 2),
        "profit_factor": round(gross_win / abs(gross_loss), 2) if gross_loss else ("inf" if gross_win else None),
        "avg_win_aed": round(gross_win / len(wins), 2) if wins else None,
        "avg_loss_aed": round(gross_loss / len(losses), 2) if losses else None,
    }


def with_shadow_rule(row: dict[str, str]) -> dict[str, str]:
    enriched = dict(row)
    candidate = row.get("candidate", "")
    symbol = row.get("symbol", "")
    time_bucket = row.get("time_bucket", "")
    if candidate == "session_extreme_retest_v0":
        enriched["shadow_action"] = "BLOCK"
        enriched["shadow_reason"] = "BLOCK_PROVISIONAL_SESSION_EXTREME_RETEST"
    elif symbol == "XAUUSD" and time_bucket in {"Morning 06:00-11:59", "Afternoon 12:00-15:59"}:
        enriched["shadow_action"] = "BLOCK"
        enriched["shadow_reason"] = "BLOCK_XAUUSD_MORNING_AFTERNOON"
    else:
        enriched["shadow_action"] = "KEEP"
        enriched["shadow_reason"] = "KEEP"
    return enriched


def build_duplicate_groups(rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    groups: dict[str, list[dict[str, str]]] = {}
    for row in rows:
        key = row.get("duplicate_key") or duplicate_key(row)
        groups.setdefault(key, []).append(row)
    duplicate_groups = []
    for key, items in groups.items():
        if len(items) < 2:
            continue
        candidates = sorted({row.get("candidate", "") for row in items if row.get("candidate")})
        closed_items = [row for row in items if row.get("state") == "CLOSED"]
        duplicate_groups.append(
            {
                "key": key,
                "entry_minute": key.split("|")[0],
                "symbol": items[0].get("symbol", ""),
                "direction": items[0].get("direction", ""),
                "volume": items[0].get("volume", ""),
                "count": len(items),
                "closed": len(closed_items),
                "pnl_aed": round(sum(to_float(row.get("profit_aed")) for row in closed_items), 2),
                "candidates": ", ".join(candidates),
                "tickets": ", ".join(row.get("position_ticket", "") for row in items[:6]),
            }
        )
    return sorted(duplicate_groups, key=lambda row: row["pnl_aed"])


def duplicate_key(row: dict[str, str]) -> str:
    entry_minute = (row.get("entry_time", "") or "")[:16]
    return "|".join(
        [
            entry_minute,
            row.get("symbol", ""),
            row.get("direction", ""),
            row.get("volume", ""),
        ]
    )


def group_summary(rows: list[dict[str, str]], keys: list[str], reverse: bool = True, limit: int | None = None) -> str:
    grouped: dict[tuple[str, ...], list[dict[str, str]]] = {}
    for row in rows:
        key = tuple(row.get(field, "") for field in keys)
        grouped.setdefault(key, []).append(row)
    items = sorted(grouped.items(), key=lambda item: summarize(item[1])["closed_pnl_aed"], reverse=reverse)
    if limit:
        items = items[:limit]
    header = "| " + " | ".join(keys) + " | Closed | Open | Wins | Losses | Win Rate | Closed PnL AED | PF | Avg Win | Avg Loss |"
    divider = "|" + "|".join(["---"] * len(keys)) + "|---:|---:|---:|---:|---:|---:|---:|---:|---:|"
    lines = [header, divider]
    for key, grouped_rows in items:
        lines.append("| " + " | ".join(key) + metric_cells(summarize(grouped_rows)))
    return "\n".join(lines)


def metric_table(rows: list[tuple[str, dict[str, Any]]]) -> str:
    lines = [
        "| View | Total | Closed | Open | Wins | Losses | Win Rate | Closed PnL AED | Floating AED | PF | Avg Win | Avg Loss |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for label, summary in rows:
        lines.append(
            f"| {label} | {summary['total']} | {summary['closed']} | {summary['open']} | "
            f"{summary['wins']} | {summary['losses']} | {fmt(summary['win_rate_pct'], pct=True)} | "
            f"{fmt(summary['closed_pnl_aed'])} | {fmt(summary['floating_pnl_aed'])} | "
            f"{fmt(summary['profit_factor'])} | {fmt(summary['avg_win_aed'])} | {fmt(summary['avg_loss_aed'])} |"
        )
    return "\n".join(lines)


def metric_cells(summary: dict[str, Any]) -> str:
    return (
        f" | {summary['closed']} | {summary['open']} | {summary['wins']} | {summary['losses']} | "
        f"{fmt(summary['win_rate_pct'], pct=True)} | {fmt(summary['closed_pnl_aed'])} | "
        f"{fmt(summary['profit_factor'])} | {fmt(summary['avg_win_aed'])} | {fmt(summary['avg_loss_aed'])} |"
    )


def count_by(rows: list[dict[str, str]], field: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        key = row.get(field, "") or "UNKNOWN"
        counts[key] = counts.get(key, 0) + 1
    return dict(sorted(counts.items(), key=lambda item: (-item[1], item[0])))


def count_table(counts: dict[str, int], first_col: str) -> str:
    lines = [f"| {first_col} | Count |", "|---|---:|"]
    for key, count in counts.items():
        lines.append(f"| {key} | {count} |")
    return "\n".join(lines)


def duplicate_group_table(groups: list[dict[str, Any]], limit: int = 12) -> str:
    lines = [
        "| Entry Minute | Symbol | Direction | Volume | Count | Closed | Closed PnL AED | Candidates | Tickets Sample |",
        "|---|---|---|---:|---:|---:|---:|---|---|",
    ]
    for group in groups[:limit]:
        lines.append(
            f"| {group['entry_minute']} | {group['symbol']} | {group['direction']} | {group['volume']} | "
            f"{group['count']} | {group['closed']} | {fmt(group['pnl_aed'])} | {group['candidates']} | {group['tickets']} |"
        )
    return "\n".join(lines)


def source_artifact_list(paths: list[str]) -> str:
    return "\n".join(f"- `{path}`" for path in paths)


def related_source_artifacts(trades_csv: Path) -> list[str]:
    review_dir = trades_csv.parent
    phase1_docs = review_dir.parents[1] if review_dir.name.startswith("PHASE2_DEMO_ACTUAL_TRADES_REVIEW") else None
    artifacts = [
        str(trades_csv),
    ]
    if phase1_docs is not None:
        artifacts.extend(
            [
                str(phase1_docs / "PHASE2_DEMO_LOSS_CASE_STUDY_2026_06_04.md"),
                str(phase1_docs / "PHASE2_DEMO_SHADOW_FILTER_REPORT_2026_06_04.md"),
                str(review_dir.parent / "PHASE2_DEMO_ACTUAL_TRADES_REVIEW_2026_06_04.zip"),
                str(review_dir / "PHASE2_DEMO_LOSS_CASE_STUDY_TRADES_2026_06_04.csv"),
                str(review_dir / "PHASE2_DEMO_SHADOW_FILTER_TRADES.csv"),
            ]
        )
    return artifacts


def render_loss_review_verdict(
    source_artifacts: list[str],
    raw_summary: dict[str, Any],
    dedup_summary: dict[str, Any],
    kept_summary: dict[str, Any],
    blocked_summary: dict[str, Any],
    dedup_rows: list[dict[str, str]],
) -> str:
    return "\n".join(
        [
            "# Phase 2 Demo Loss Review Verdict - No Runtime Touch",
            "",
            "```text",
            "status: EXPERIMENTAL_LOSS_PATTERN_FOUND",
            "runtime_change_authorized: false",
            "current_demo_eas_touched: false",
            "mt5_terminal_touched: false",
            "mql5_source_touched: false",
            "canonical_phase2_authority: false",
            "router_change_authorized: false",
            "shadow_filter_enforced: false",
            "same_family_guard_implemented: false",
            "future_owner_decision_required: true",
            "```",
            "",
            "## Boundary",
            "",
            "This is a repo-only review of already committed CSV artifacts. It is experimental demo evidence only. It does not authorize canonical Phase 2, paper-mode execution, live trading, router/session-filter enforcement, touching currently running demo EAs, chart changes, EA input changes, position/order changes, attached-EA changes, or any broker-side action.",
            "",
            "The shadow filter is a measurement only. It was not enforced. MT5, charts, inputs, positions, orders, and attached EAs were not modified by this review task.",
            "",
            "## Source Artifacts",
            "",
            source_artifact_list(source_artifacts),
            "",
            "## Executive Summary",
            "",
            metric_table(
                [
                    ("Raw grouped actual trades", raw_summary),
                    ("Duplicate-hidden decision view", dedup_summary),
                    ("Shadow would-keep subset", kept_summary),
                    ("Shadow would-block subset", blocked_summary),
                ]
            ),
            "",
            f"- Duplicate-hidden baseline remains negative: {dedup_summary['closed']} closed trades, {fmt(dedup_summary['win_rate_pct'], pct=True)} win rate, {fmt(dedup_summary['closed_pnl_aed'])} AED closed PnL, PF {fmt(dedup_summary['profit_factor'])}.",
            f"- The measured shadow rule would keep {kept_summary['closed']} closed trades at {fmt(kept_summary['win_rate_pct'], pct=True)} win rate and {fmt(kept_summary['closed_pnl_aed'])} AED closed PnL, while the would-block subset produced {fmt(blocked_summary['closed_pnl_aed'])} AED.",
            "- This is enough to identify a loss pattern, not enough to deploy a runtime filter.",
            "",
            "## Main Loss Drivers",
            "",
            "1. `symbol_normalized_round_retest_v0` loss concentration.",
            "2. XAUUSD Morning/Afternoon weakness.",
            "3. `session_extreme_retest_v0` weakness.",
            "4. Same-family duplicate/correlated exposure.",
            "5. Missing spread/slippage/cost_R decomposition in current trade rows.",
            "",
            "### By Candidate",
            "",
            group_summary(dedup_rows, ["candidate"], reverse=False),
            "",
            "### By Symbol",
            "",
            group_summary(dedup_rows, ["symbol"], reverse=False),
            "",
            "### By Time Bucket",
            "",
            group_summary(dedup_rows, ["time_bucket"], reverse=False),
            "",
            "### Worst Candidate x Symbol x Time Clusters",
            "",
            group_summary(dedup_rows, ["candidate", "symbol", "time_bucket"], reverse=False, limit=12),
            "",
            "## Recommended Future Fixes",
            "",
            "- Future family-level duplicate guard. Not implemented in this task; requires explicit owner authorization if it affects runtime.",
            "- Future passive-only demotion for weak variants. Not implemented in this task; requires explicit owner authorization if it affects runtime.",
            "- Future pre-registered shadow filter forward test. Not implemented in this task; requires explicit owner authorization if it affects runtime.",
            "- Future enhanced trade ledger fields for spread, slippage, and cost_R decomposition. Not implemented in this task; requires explicit owner authorization if it affects runtime.",
            "- Future Phase 0R lower-cost independent research. Not implemented in this task; requires explicit owner authorization if it affects runtime.",
            "",
            "## Decision",
            "",
            "`EXPERIMENTAL_LOSS_PATTERN_FOUND`. The review found a plausible selection/timing and same-family duplication problem. The fix remains future-only and owner-reviewed. No runtime change is authorized by this document.",
            "",
            "- Keep current demo EAs untouched.",
            "- Keep shadow filter as measurement only.",
            "- Do not treat demo PnL as canonical evidence.",
            "- Continue Phase 0R replacement research.",
            "",
        ]
    )


def render_shadow_forward_test_plan(
    source_artifacts: list[str],
    dedup_summary: dict[str, Any],
    kept_summary: dict[str, Any],
    blocked_summary: dict[str, Any],
    shadow_rows: list[dict[str, str]],
) -> str:
    blocked_rows = [row for row in shadow_rows if row["shadow_action"] == "BLOCK"]
    return "\n".join(
        [
            "# Phase 2 Demo Shadow Forward Test Plan - 2026-06-04",
            "",
            "```text",
            "status: SHADOW_FORWARD_TEST_PLAN_ONLY",
            "runtime_change_authorized: false",
            "shadow_filter_enforced: false",
            "current_demo_eas_touched: false",
            "canonical_phase2_authority: false",
            "```",
            "",
            "## Boundary",
            "",
            "This is a plan for measurement only. It does not enforce a router/session filter, does not alter current demo EAs, and does not promote any cost-suspended family to canonical Phase 2.",
            "",
            "## Source Artifacts",
            "",
            source_artifact_list(source_artifacts),
            "",
            "## Hypothetical Rule Under Test",
            "",
            "- Block `session_extreme_retest_v0`.",
            "- Block XAUUSD entries in Morning `06:00-11:59` and Afternoon `12:00-15:59`.",
            "- Keep evening/night XAUUSD.",
            "- Keep non-XAUUSD unless the candidate is `session_extreme_retest_v0`.",
            "",
            "## Current Retrospective Measurement",
            "",
            metric_table(
                [
                    ("Baseline duplicate-hidden", dedup_summary),
                    ("Would keep", kept_summary),
                    ("Would block", blocked_summary),
                ]
            ),
            "",
            f"Current shadow delta: `{fmt(kept_summary['closed_pnl_aed'] - dedup_summary['closed_pnl_aed'])} AED` versus the duplicate-hidden baseline.",
            "",
            "## Block Reason Counts",
            "",
            count_table(count_by(blocked_rows, "shadow_reason"), "Reason"),
            "",
            "## Evidence Requirement",
            "",
            "- Collect at least 300 unique duplicate-hidden closed trades/events or 20 active market days, whichever is more conservative.",
            "- Do not change the rule while collecting the forward sample.",
            "- Record daily kept/blocked counts, raw and duplicate-hidden results, per candidate, per symbol, and per time bucket.",
            "- Keep open and floating PnL separate from closed-trade statistics.",
            "- Report raw duplicated trades and duplicate-hidden trades side by side.",
            "- Treat a positive retrospective result as overfit-risk until the forward sample survives.",
            "",
            "## Review Decision Required Later",
            "",
            "The future owner decision should be based on forward evidence, not this retrospective sample alone. Passing this plan would still not override canonical measured-cost suspension unless the cost evidence is separately repaired.",
            "",
        ]
    )


def render_duplicate_family_analysis(
    source_artifacts: list[str],
    actual_summary: dict[str, Any],
    dedup_summary: dict[str, Any],
    duplicate_groups: list[dict[str, Any]],
) -> str:
    duplicated_rows = sum(max(0, group["count"] - 1) for group in duplicate_groups)
    duplicate_closed_pnl_delta = round(actual_summary["closed_pnl_aed"] - dedup_summary["closed_pnl_aed"], 2)
    candidate_combo_counts: dict[str, int] = {}
    for group in duplicate_groups:
        candidate_combo_counts[group["candidates"]] = candidate_combo_counts.get(group["candidates"], 0) + 1
    return "\n".join(
        [
            "# Phase 2 Demo Duplicate Family Analysis - 2026-06-04",
            "",
            "```text",
            "status: DUPLICATE_FAMILY_RISK_FOUND",
            "runtime_change_authorized: false",
            "current_demo_eas_touched: false",
            "same_family_guard_implemented: false",
            "canonical_phase2_authority: false",
            "```",
            "",
            "## Boundary",
            "",
            "This analysis is generated from committed CSV artifacts only. It does not read terminal state, touch current demo EAs, change any chart, or implement the proposed guard.",
            "",
            "## Source Artifacts",
            "",
            source_artifact_list(source_artifacts),
            "",
            "## Duplicate Definition",
            "",
            "A duplicate family is defined as the same entry minute, same symbol, same direction, and same volume. This matches the committed actual-trade export `duplicate_key` when present.",
            "",
            "## Raw vs Duplicate-Hidden",
            "",
            metric_table(
                [
                    ("Raw grouped actual trades", actual_summary),
                    ("Duplicate-hidden decision view", dedup_summary),
                ]
            ),
            "",
            f"- Duplicate groups found: `{len(duplicate_groups)}`.",
            f"- Duplicate rows beyond the first kept event: `{duplicated_rows}`.",
            f"- Closed PnL difference raw minus duplicate-hidden: `{fmt(duplicate_closed_pnl_delta)} AED`.",
            "- Raw trade counts are useful for broker-account accounting. Duplicate-hidden counts are better for strategy decision review because they collapse same-family stack entries into one event.",
            "",
            "## Worst Duplicate Examples",
            "",
            duplicate_group_table(duplicate_groups),
            "",
            "## Candidate Combinations",
            "",
            count_table(dict(sorted(candidate_combo_counts.items(), key=lambda item: (-item[1], item[0]))), "Candidate Combination"),
            "",
            "## Future Guard",
            "",
            "A future family-level mutex should allow at most one open/entry event per duplicate key: same entry minute, symbol, direction, and volume. The guard must be designed, reviewed, tested, and explicitly authorized before any runtime deployment.",
            "",
            "No same-family mutex, router block, or one-event-one-trade guard was implemented by this analysis.",
            "",
        ]
    )


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
    parser = argparse.ArgumentParser(description="Analyze committed demo trade CSVs without touching runtime state.")
    parser.add_argument("--trades-csv", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    output = analyze_loss_patterns_offline(
        trades_csv=args.trades_csv,
        output_dir=args.output_dir,
    )
    print(f"Loss review verdict: {output.loss_review_path}")
    print(f"Shadow forward test plan: {output.shadow_plan_path}")
    print(f"Duplicate family analysis: {output.duplicate_analysis_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
