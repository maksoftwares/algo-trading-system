from __future__ import annotations

import argparse
import csv
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEFAULT_ACTUAL_TRADES_CSV = Path("outputs") / "reports" / "PHASE2_DEMO_ACTUAL_BROKER_TRADES.csv"
DEFAULT_REPORT_JSON = Path("outputs") / "reports" / "PHASE2_REPAIR_CANDIDATE_RESEARCH.json"
DEFAULT_REPORT_MD = Path("outputs") / "reports" / "PHASE2_REPAIR_CANDIDATE_RESEARCH.md"
DEFAULT_RULES_CSV = Path("outputs") / "reports" / "PHASE2_REPAIR_CANDIDATE_RULES.csv"

TARGET_CANDIDATES = (
    "session_extreme_retest_v0",
    "symbol_normalized_round_retest_v0",
    "round_number_retest_v0",
)

MIN_CLUSTER_CLOSED = 3
MIN_KEEP_PF = 1.10
MIN_KEEP_WIN_RATE = 40.0


@dataclass(frozen=True)
class RepairResearchOutput:
    status: str
    json_path: Path
    markdown_path: Path
    rules_csv_path: Path
    candidate_count: int


def generate_repair_candidate_research(
    phase1_root: Path,
    actual_trades_csv: Path | None = None,
    output_json: Path | None = None,
) -> RepairResearchOutput:
    phase1_root = phase1_root.resolve()
    actual_trades_csv = (actual_trades_csv or phase1_root / DEFAULT_ACTUAL_TRADES_CSV).resolve()
    output_json = (output_json or phase1_root / DEFAULT_REPORT_JSON).resolve()
    output_md = output_json.with_suffix(".md") if output_json.name != DEFAULT_REPORT_JSON.name else phase1_root / DEFAULT_REPORT_MD
    rules_csv = output_json.with_name(DEFAULT_RULES_CSV.name)
    output_json.parent.mkdir(parents=True, exist_ok=True)

    rows = [normalize_trade(row) for row in read_csv(actual_trades_csv)]
    target_rows = [row for row in rows if row.get("candidate") in TARGET_CANDIDATES]
    duplicate_hidden_rows = [row for row in target_rows if not is_true(row.get("is_duplicate"))]
    candidate_reports = [
        candidate_repair_report(candidate, target_rows, duplicate_hidden_rows)
        for candidate in TARGET_CANDIDATES
    ]
    rules = [rule for report in candidate_reports for rule in report["rules"]]
    payload = {
        "status": "REPAIR_RESEARCH_READY",
        "generated_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "source_csv": str(actual_trades_csv),
        "boundary": (
            "Research only. This report does not change MT5 charts, EA inputs, presets, orders, "
            "open positions, canonical Phase 2 status, or live-capital permissions."
        ),
        "promotion_rule": [
            "Create a versioned repair hypothesis before implementation.",
            "Forward-test as observer-only first.",
            "Promote to demo execution only if duplicate-hidden PF and PnL improve.",
            "Do not destroy trade count.",
            "Improve or preserve win rate.",
            "Survive at least one fresh week of actual demo data.",
            "Record owner/reviewer approval before runtime changes.",
        ],
        "repair_candidates": candidate_reports,
        "portfolio_view": portfolio_repair_view(duplicate_hidden_rows, candidate_reports),
        "rules": rules,
    }
    output_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    output_md.write_text(render_markdown(payload), encoding="utf-8")
    write_csv(rules_csv, rules, fieldnames=repair_rule_fields())
    return RepairResearchOutput(
        status=str(payload["status"]),
        json_path=output_json,
        markdown_path=output_md,
        rules_csv_path=rules_csv,
        candidate_count=len(candidate_reports),
    )


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def normalize_trade(row: dict[str, Any]) -> dict[str, Any]:
    enriched = dict(row)
    enriched["profit_value"] = to_float(enriched.get("profit_aed"))
    enriched["time_bucket"] = enriched.get("time_bucket") or time_bucket(enriched.get("entry_time", ""))
    enriched["stop_distance"] = stop_distance(enriched)
    enriched["risk_reward"] = risk_reward(enriched)
    return enriched


def candidate_repair_report(
    candidate: str,
    raw_rows: list[dict[str, Any]],
    duplicate_hidden_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    candidate_raw = [row for row in raw_rows if row.get("candidate") == candidate]
    candidate_dedup = [row for row in duplicate_hidden_rows if row.get("candidate") == candidate]
    symbol_groups = group_summaries(candidate_dedup, ["symbol"])
    time_groups = group_summaries(candidate_dedup, ["time_bucket"])
    direction_groups = group_summaries(candidate_dedup, ["direction"])
    cluster_groups = group_summaries(candidate_dedup, ["symbol", "time_bucket", "direction"])
    rules = repair_rules_for(candidate, cluster_groups)
    if candidate_raw and not candidate_dedup:
        rules = [
            make_rule(
                candidate=candidate,
                rule_type="DUPLICATE_ONLY_REBUILD",
                symbol="ANY",
                time_bucket="ANY",
                direction="ANY",
                summary=summarize(candidate_raw),
                rationale=(
                    "Raw broker rows exist, but all are duplicate-hidden under the current priority; "
                    "rebuild with standalone observer evidence before any demo execution."
                ),
            )
        ]
    scenario = apply_repair_rules(candidate_dedup, rules)
    return {
        "candidate": candidate,
        "repair_id": f"{candidate}_repair_v1",
        "status": repair_status(scenario, candidate_dedup, candidate_raw),
        "hypothesis_status": "RESEARCH_HYPOTHESIS_ONLY",
        "raw_summary": summarize(candidate_raw),
        "duplicate_hidden_summary": summarize(candidate_dedup),
        "repair_shadow_summary": scenario,
        "by_symbol": symbol_groups,
        "by_time_bucket": time_groups,
        "by_direction": direction_groups,
        "clusters": cluster_groups,
        "worst_clusters": sorted(cluster_groups, key=lambda row: row["closed_pnl_aed"])[:8],
        "best_clusters": sorted(cluster_groups, key=lambda row: row["closed_pnl_aed"], reverse=True)[:8],
        "rules": rules,
        "hypothesis": hypothesis_for(candidate, rules, scenario),
    }


def repair_rules_for(candidate: str, clusters: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rules: list[dict[str, Any]] = []
    for cluster in clusters:
        closed = int(cluster["closed"])
        if closed < MIN_CLUSTER_CLOSED:
            continue
        pf = cluster["profit_factor_value"]
        pnl = cluster["closed_pnl_aed"]
        win_rate = cluster["win_rate_pct"]
        symbol = cluster.get("symbol", "")
        time_value = cluster.get("time_bucket", "")
        direction = cluster.get("direction", "")
        if pnl < 0.0 and (pf < 1.0 or win_rate < MIN_KEEP_WIN_RATE):
            rules.append(
                make_rule(
                    candidate=candidate,
                    rule_type="BLOCK_CLUSTER",
                    symbol=symbol,
                    time_bucket=time_value,
                    direction=direction,
                    summary=cluster,
                    rationale="Negative duplicate-hidden cluster with weak PF/win-rate.",
                )
            )
        elif pnl > 0.0 and pf >= MIN_KEEP_PF and win_rate >= MIN_KEEP_WIN_RATE:
            rules.append(
                make_rule(
                    candidate=candidate,
                    rule_type="PREFERRED_CLUSTER",
                    symbol=symbol,
                    time_bucket=time_value,
                    direction=direction,
                    summary=cluster,
                    rationale="Positive duplicate-hidden cluster worth observer-forward testing.",
                )
            )
    if not any(rule["rule_type"] == "PREFERRED_CLUSTER" for rule in rules):
        rules.append(
            make_rule(
                candidate=candidate,
                rule_type="OBSERVER_ONLY_REBUILD",
                symbol="ANY",
                time_bucket="ANY",
                direction="ANY",
                summary=summarize([]),
                rationale="No sufficiently strong keep cluster found; rebuild before demo execution.",
            )
        )
    return rules


def make_rule(
    *,
    candidate: str,
    rule_type: str,
    symbol: str,
    time_bucket: str,
    direction: str,
    summary: dict[str, Any],
    rationale: str,
) -> dict[str, Any]:
    return {
        "candidate": candidate,
        "repair_id": f"{candidate}_repair_v1",
        "rule_type": rule_type,
        "symbol": symbol,
        "time_bucket": time_bucket,
        "direction": direction,
        "closed": summary.get("closed", 0),
        "wins": summary.get("wins", 0),
        "losses": summary.get("losses", 0),
        "win_rate_pct": summary.get("win_rate_pct", "n/a"),
        "closed_pnl_aed": summary.get("closed_pnl_aed", 0.0),
        "profit_factor": summary.get("profit_factor", "n/a"),
        "avg_win_aed": summary.get("avg_win_aed", "n/a"),
        "avg_loss_aed": summary.get("avg_loss_aed", "n/a"),
        "rationale": rationale,
        "runtime_action": "NONE_SHADOW_ONLY",
    }


def apply_repair_rules(rows: list[dict[str, Any]], rules: list[dict[str, Any]]) -> dict[str, Any]:
    block_rules = [rule for rule in rules if rule["rule_type"] == "BLOCK_CLUSTER"]
    kept: list[dict[str, Any]] = []
    blocked: list[dict[str, Any]] = []
    for row in rows:
        if any(rule_matches(rule, row) for rule in block_rules):
            blocked.append(row)
        else:
            kept.append(row)
    baseline = summarize(rows)
    kept_summary = summarize(kept)
    blocked_summary = summarize(blocked)
    return {
        "baseline": baseline,
        "would_keep": kept_summary,
        "would_block": blocked_summary,
        "delta_closed_pnl_aed": round(float(kept_summary["closed_pnl_aed"]) - float(baseline["closed_pnl_aed"]), 2),
        "kept_closed_trade_pct": round(
            (int(kept_summary["closed"]) / int(baseline["closed"]) * 100.0), 2
        )
        if int(baseline["closed"])
        else None,
        "shadow_status": shadow_status(baseline, kept_summary),
    }


def rule_matches(rule: dict[str, Any], row: dict[str, Any]) -> bool:
    return (
        row.get("candidate") == rule.get("candidate")
        and row.get("symbol") == rule.get("symbol")
        and row.get("time_bucket") == rule.get("time_bucket")
        and row.get("direction") == rule.get("direction")
    )


def shadow_status(baseline: dict[str, Any], kept: dict[str, Any]) -> str:
    baseline_closed = int(baseline["closed"])
    kept_closed = int(kept["closed"])
    if baseline_closed == 0:
        return "NO_DATA"
    if kept_closed / baseline_closed < 0.35:
        return "FAIL_TRADE_COUNT"
    baseline_pf = profit_factor_value(baseline["profit_factor"])
    kept_pf = profit_factor_value(kept["profit_factor"])
    if float(kept["closed_pnl_aed"]) > float(baseline["closed_pnl_aed"]) and kept_pf >= baseline_pf:
        return "REPAIR_SHADOW_CANDIDATE"
    return "KEEP_MEASURING_OR_REBUILD"


def repair_status(
    scenario: dict[str, Any],
    duplicate_hidden_rows: list[dict[str, Any]],
    raw_rows: list[dict[str, Any]],
) -> str:
    if not raw_rows:
        return "NO_ACTUAL_DEMO_EVIDENCE"
    if not duplicate_hidden_rows:
        return "DUPLICATE_ONLY_REBUILD_REQUIRED"
    if scenario["shadow_status"] == "REPAIR_SHADOW_CANDIDATE":
        return "REPAIR_CANDIDATE_FOR_OBSERVER_FORWARD_TEST"
    if scenario["shadow_status"] == "FAIL_TRADE_COUNT":
        return "REPAIR_TOO_NARROW"
    return "REBUILD_OR_KEEP_MEASURING"


def portfolio_repair_view(rows: list[dict[str, Any]], candidate_reports: list[dict[str, Any]]) -> dict[str, Any]:
    rules = [rule for report in candidate_reports for rule in report["rules"] if rule["rule_type"] == "BLOCK_CLUSTER"]
    target_rows = [row for row in rows if row.get("candidate") in TARGET_CANDIDATES]
    kept = [row for row in target_rows if not any(rule_matches(rule, row) for rule in rules)]
    blocked = [row for row in target_rows if any(rule_matches(rule, row) for rule in rules)]
    return {
        "baseline": summarize(target_rows),
        "would_keep": summarize(kept),
        "would_block": summarize(blocked),
        "rule_count": len(rules),
    }


def group_summaries(rows: list[dict[str, Any]], keys: list[str]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, ...], list[dict[str, Any]]] = {}
    for row in rows:
        key = tuple(str(row.get(field, "")) for field in keys)
        grouped.setdefault(key, []).append(row)
    output = []
    for key, group_rows in grouped.items():
        summary = summarize(group_rows)
        for index, field in enumerate(keys):
            summary[field] = key[index]
        output.append(summary)
    return sorted(output, key=lambda item: item["closed_pnl_aed"])


def summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    closed = [row for row in rows if row.get("state") == "CLOSED"]
    open_rows = [row for row in rows if row.get("state") == "OPEN"]
    wins = [row for row in closed if row["profit_value"] > 0.0]
    losses = [row for row in closed if row["profit_value"] < 0.0]
    gross_win = sum(row["profit_value"] for row in wins)
    gross_loss = sum(row["profit_value"] for row in losses)
    closed_pnl = sum(row["profit_value"] for row in closed)
    floating_pnl = sum(row["profit_value"] for row in open_rows)
    pf = gross_win / abs(gross_loss) if gross_loss else (float("inf") if gross_win else None)
    return {
        "total": len(rows),
        "closed": len(closed),
        "open": len(open_rows),
        "wins": len(wins),
        "losses": len(losses),
        "win_rate_pct": round(len(wins) / (len(wins) + len(losses)) * 100.0, 2) if wins or losses else None,
        "closed_pnl_aed": round(closed_pnl, 2),
        "floating_pnl_aed": round(floating_pnl, 2),
        "total_pnl_aed": round(closed_pnl + floating_pnl, 2),
        "profit_factor": "inf" if pf == float("inf") else (round(pf, 2) if pf is not None else None),
        "profit_factor_value": pf if pf is not None and pf != float("inf") else (999999.0 if pf == float("inf") else 0.0),
        "avg_win_aed": round(gross_win / len(wins), 2) if wins else None,
        "avg_loss_aed": round(gross_loss / len(losses), 2) if losses else None,
        "avg_stop_distance": round(sum(row["stop_distance"] for row in closed if row["stop_distance"] > 0.0) / len([row for row in closed if row["stop_distance"] > 0.0]), 5)
        if [row for row in closed if row["stop_distance"] > 0.0]
        else None,
        "avg_rr": round(sum(row["risk_reward"] for row in closed if row["risk_reward"] > 0.0) / len([row for row in closed if row["risk_reward"] > 0.0]), 2)
        if [row for row in closed if row["risk_reward"] > 0.0]
        else None,
    }


def hypothesis_for(candidate: str, rules: list[dict[str, Any]], scenario: dict[str, Any]) -> dict[str, Any]:
    preferred = [rule for rule in rules if rule["rule_type"] == "PREFERRED_CLUSTER"]
    blocked = [rule for rule in rules if rule["rule_type"] == "BLOCK_CLUSTER"]
    falsification = [
        "Fails if observer-forward duplicate-hidden PF does not improve over the current candidate.",
        "Fails if win rate falls below current duplicate-hidden baseline.",
        "Fails if kept trade count is too small for a useful demo comparison.",
        "Fails if reviewer finds lookahead, tuning, or post-hoc parameter changes beyond the listed filters.",
    ]
    if scenario["shadow_status"] == "NO_DATA":
        falsification = [
            "Raw broker rows exist only as duplicate-hidden entries or no rows exist at all.",
            "Do not promote from duplicate-only evidence; rebuild as standalone observer evidence first.",
            "Fails if a fresh observer-forward sample cannot produce unique duplicate-hidden decisions.",
        ]
    return {
        "name": f"{candidate}_repair_v1",
        "status": "NOT_REGISTERED_NOT_HASHED",
        "mechanical_change": [
            "Keep original entry/SL/TP mechanics unchanged.",
            "Apply only pre-entry symbol/session/direction filters derived from actual demo weakness clusters.",
            "Run observer-only before any demo-order promotion.",
        ],
        "preferred_clusters": preferred,
        "blocked_clusters": blocked,
        "falsification": falsification,
        "shadow_result": scenario,
    }


def time_bucket(entry_time: Any) -> str:
    text = str(entry_time or "")
    try:
        hour = int(text[11:13])
    except (TypeError, ValueError):
        return "UNKNOWN"
    if hour >= 20 or hour < 6:
        return "Night 20:00-05:59"
    if hour < 12:
        return "Morning 06:00-11:59"
    if hour < 16:
        return "Afternoon 12:00-15:59"
    return "Evening 16:00-19:59"


def stop_distance(row: dict[str, Any]) -> float:
    entry = to_float(row.get("entry_price"))
    sl = to_float(row.get("sl"))
    if entry == 0.0 or sl == 0.0:
        return 0.0
    return abs(entry - sl)


def risk_reward(row: dict[str, Any]) -> float:
    entry = to_float(row.get("entry_price"))
    sl = to_float(row.get("sl"))
    tp = to_float(row.get("tp"))
    risk = abs(entry - sl)
    reward = abs(tp - entry)
    if risk <= 0.0 or reward <= 0.0:
        return 0.0
    return reward / risk


def to_float(value: Any) -> float:
    try:
        return float(value or 0.0)
    except (TypeError, ValueError):
        return 0.0


def is_true(value: Any) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def profit_factor_value(value: Any) -> float:
    if value == "inf":
        return 999999.0
    return to_float(value)


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def repair_rule_fields() -> list[str]:
    return [
        "candidate",
        "repair_id",
        "rule_type",
        "symbol",
        "time_bucket",
        "direction",
        "closed",
        "wins",
        "losses",
        "win_rate_pct",
        "closed_pnl_aed",
        "profit_factor",
        "avg_win_aed",
        "avg_loss_aed",
        "rationale",
        "runtime_action",
    ]


def render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Phase 2 Repair Candidate Research",
        "",
        f"Status: `{payload['status']}`",
        "",
        str(payload["boundary"]),
        "",
        f"Generated at UTC: `{payload['generated_at_utc']}`",
        f"Source CSV: `{payload['source_csv']}`",
        "",
        "## Promotion Rule",
        "",
    ]
    lines.extend(f"- {item}" for item in payload["promotion_rule"])
    lines.extend(["", "## Portfolio View", "", metrics_table([("Repair targets baseline", payload["portfolio_view"]["baseline"]), ("Repair targets would keep", payload["portfolio_view"]["would_keep"]), ("Repair targets would block", payload["portfolio_view"]["would_block"])]), ""])
    for report in payload["repair_candidates"]:
        lines.extend(render_candidate_section(report))
    lines.extend(
        [
            "## Rules CSV",
            "",
            "`PHASE2_REPAIR_CANDIDATE_RULES.csv` contains the machine-readable shadow rules. All rows have `runtime_action=NONE_SHADOW_ONLY`.",
            "",
        ]
    )
    return "\n".join(lines)


def render_candidate_section(report: dict[str, Any]) -> list[str]:
    lines = [
        f"## {report['candidate']}",
        "",
        f"Repair ID: `{report['repair_id']}`",
        f"Status: `{report['status']}`",
        f"Hypothesis status: `{report['hypothesis_status']}`",
        "",
        metrics_table(
            [
                ("Raw actual trades", report["raw_summary"]),
                ("Duplicate-hidden baseline", report["duplicate_hidden_summary"]),
                ("Repair would keep", report["repair_shadow_summary"]["would_keep"]),
                ("Repair would block", report["repair_shadow_summary"]["would_block"]),
            ]
        ),
        "",
        f"Shadow delta closed PnL AED: `{report['repair_shadow_summary']['delta_closed_pnl_aed']}`",
        f"Kept closed trade pct: `{fmt(report['repair_shadow_summary']['kept_closed_trade_pct'], pct=True)}`",
        f"Shadow status: `{report['repair_shadow_summary']['shadow_status']}`",
        "",
        "### Proposed v1 Rules",
        "",
        rules_table(report["rules"]),
        "",
        "### Worst Clusters",
        "",
        group_table(report["worst_clusters"], ["symbol", "time_bucket", "direction"]),
        "",
        "### Best Clusters",
        "",
        group_table(report["best_clusters"], ["symbol", "time_bucket", "direction"]),
        "",
        "### v1 Hypothesis Notes",
        "",
    ]
    lines.extend(f"- {item}" for item in report["hypothesis"]["mechanical_change"])
    lines.extend(["", "Falsification:", ""])
    lines.extend(f"- {item}" for item in report["hypothesis"]["falsification"])
    lines.append("")
    return lines


def metrics_table(rows: list[tuple[str, dict[str, Any]]]) -> str:
    lines = [
        "| View | Total | Closed | Open | Wins | Losses | Win Rate | Closed PnL | Floating | Total PnL | PF | Avg Win | Avg Loss |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for label, summary in rows:
        lines.append(
            f"| {label} | {summary['total']} | {summary['closed']} | {summary['open']} | {summary['wins']} | {summary['losses']} | "
            f"{fmt(summary['win_rate_pct'], pct=True)} | {fmt(summary['closed_pnl_aed'])} | {fmt(summary['floating_pnl_aed'])} | "
            f"{fmt(summary['total_pnl_aed'])} | {fmt(summary['profit_factor'])} | {fmt(summary['avg_win_aed'])} | {fmt(summary['avg_loss_aed'])} |"
        )
    return "\n".join(lines)


def rules_table(rules: list[dict[str, Any]]) -> str:
    lines = [
        "| Rule | Symbol | Time | Direction | Closed | Win Rate | PnL | PF | Rationale |",
        "|---|---|---|---|---:|---:|---:|---:|---|",
    ]
    for rule in rules:
        lines.append(
            f"| {rule['rule_type']} | {rule['symbol']} | {rule['time_bucket']} | {rule['direction']} | "
            f"{rule['closed']} | {fmt(rule['win_rate_pct'], pct=True)} | {fmt(rule['closed_pnl_aed'])} | {fmt(rule['profit_factor'])} | {rule['rationale']} |"
        )
    return "\n".join(lines)


def group_table(rows: list[dict[str, Any]], keys: list[str]) -> str:
    lines = [
        "| " + " | ".join(keys) + " | Closed | Wins | Losses | Win Rate | PnL | PF | Avg Win | Avg Loss |",
        "|" + "|".join(["---"] * len(keys)) + "|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        key_text = " | ".join(str(row.get(key, "")) for key in keys)
        lines.append(
            f"| {key_text} | {row['closed']} | {row['wins']} | {row['losses']} | {fmt(row['win_rate_pct'], pct=True)} | "
            f"{fmt(row['closed_pnl_aed'])} | {fmt(row['profit_factor'])} | {fmt(row['avg_win_aed'])} | {fmt(row['avg_loss_aed'])} |"
        )
    return "\n".join(lines)


def fmt(value: Any, pct: bool = False) -> str:
    if value is None:
        return "n/a"
    if value == "inf":
        return "inf"
    if isinstance(value, str):
        return value
    suffix = "%" if pct else ""
    return f"{float(value):.2f}{suffix}"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate repair research for weak Phase 2 demo EAs.")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--actual-trades-csv", type=Path, default=None)
    parser.add_argument("--output-json", type=Path, default=None)
    args = parser.parse_args(argv)
    output = generate_repair_candidate_research(args.root, args.actual_trades_csv, args.output_json)
    print(f"Phase 2 repair candidate research: {output.status}")
    print(output.markdown_path)
    print(output.json_path)
    print(output.rules_csv_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
