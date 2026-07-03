from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


PHASE1_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PHASE1_ROOT.parents[1]
REPORTS_DIR = PHASE1_ROOT / "outputs" / "reports"
OUTPUT_STEM = "A1_XAU_M5_MOMENTUM_BUSINESS_GOAL_PROMOTION_PACKET_2026_07_02"

SCOREBOARD_JSON = REPORTS_DIR / "A1_XAU_M5_MOMENTUM_BUSINESS_GOAL_SCOREBOARD_2026_07_02.json"
PLUS75_JSON = REPORTS_DIR / "A1_XAU_M5_MOMENTUM_FEATURE_BAND_RESIDUAL_PLUS75_HIGH_NET_READINESS_2026_07_02.json"
PLUS50_JSON = REPORTS_DIR / "A1_XAU_M5_MOMENTUM_FEATURE_BAND_RESIDUAL_PLUS50_COOLDOWN10_READINESS_2026_07_02.json"
CALENDAR_CADENCE_JSON = (
    REPORTS_DIR / "A1_XAU_M5_MOMENTUM_BUSINESS_GOAL_CALENDAR_CADENCE_AUDIT_2026_07_02.json"
)
MARKET_DAY_COVERAGE_JSON = REPORTS_DIR / "A1_XAU_M5_MOMENTUM_MARKET_DAY_COVERAGE_SEARCH_CAUSAL_2026_07_03.json"
MARKET_DAY_COVERAGE_STRESS_JSON = REPORTS_DIR / "A1_XAU_M5_MOMENTUM_MARKET_DAY_COVERAGE_STRESS_CAUSAL_2026_07_03.json"


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO_ROOT)).replace("\\", "/")
    except ValueError:
        return str(path)


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def check(name: str, passed: bool, detail: str) -> dict[str, str]:
    return {"name": name, "status": "PASS" if passed else "FAIL", "detail": detail}


def by_name(rows: list[dict[str, Any]], name: str) -> dict[str, Any]:
    return next((row for row in rows if row.get("name") == name), {})


def build_payload() -> dict[str, Any]:
    scoreboard = load_json(SCOREBOARD_JSON)
    plus75 = load_json(PLUS75_JSON)
    plus50 = load_json(PLUS50_JSON)
    cadence = load_json(CALENDAR_CADENCE_JSON)
    market_day_coverage = load_json(MARKET_DAY_COVERAGE_JSON)
    market_day_stress = load_json(MARKET_DAY_COVERAGE_STRESS_JSON)
    rows = scoreboard.get("rows", [])
    top = rows[0] if rows else {}
    plus75_row = by_name(rows, "residual_plus75_high_net")
    plus50_row = by_name(rows, "residual_plus50_10m")
    cadence_candidates = {
        str(row.get("name")): row for row in cadence.get("candidates", []) if isinstance(row, dict)
    }
    plus75_cadence = cadence_candidates.get("residual_plus75_high_net", {})
    plus50_cadence = cadence_candidates.get("residual_plus50_10m", {})
    coverage_best = market_day_coverage.get("best_result", {})
    stress_summary = market_day_stress.get("summary", {})
    stress_rolling = market_day_stress.get("rolling", [])

    checks = [
        check(
            "scoreboard_available",
            scoreboard.get("status") == "PASS_SCOREBOARD_READY" and bool(rows),
            f"status={scoreboard.get('status')}, rows={len(rows)}",
        ),
        check(
            "top_candidate_is_plus75",
            top.get("name") == "residual_plus75_high_net",
            f"top={top.get('name')}",
        ),
        check(
            "plus75_readiness_pass",
            plus75.get("status") == "PASS_READY_FOR_REVIEW_NOT_ATTACHED",
            f"status={plus75.get('status')}",
        ),
        check(
            "plus75_frequency_pass",
            plus75_row.get("trades_per_active_day", 0) >= 3.0
            and plus75_row.get("three_plus_trade_day_pct", 0) >= 50.0,
            (
                f"tpa={plus75_row.get('trades_per_active_day')}, "
                f"three_plus={plus75_row.get('three_plus_trade_day_pct')}"
            ),
        ),
        check(
            "plus75_quality_pass",
            plus75_row.get("win_rate_pct", 0) >= 60.0
            and plus75_row.get("profit_factor", 0) >= 1.30
            and plus75_row.get("net", 0) > 0,
            (
                f"wr={plus75_row.get('win_rate_pct')}, pf={plus75_row.get('profit_factor')}, "
                f"net={plus75_row.get('net')}"
            ),
        ),
        check(
            "plus75_day_reliability_pass",
            plus75_row.get("positive_day_pct", 0) >= 60.0,
            f"positive_day_pct={plus75_row.get('positive_day_pct')}",
        ),
        check(
            "plus75_robustness_pass",
            plus75_row.get("top100_removed", 0) > 0
            and plus75_row.get("top200_removed", 0) > 0
            and plus75_row.get("older_net", 0) > 0
            and plus75_row.get("newer_net", 0) > 0,
            (
                f"top100={plus75_row.get('top100_removed')}, top200={plus75_row.get('top200_removed')}, "
                f"older={plus75_row.get('older_net')}, newer={plus75_row.get('newer_net')}"
            ),
        ),
        check(
            "plus75_distinct_magics",
            sorted(
                item.get("magic")
                for item in plus75.get("planned_variants", {}).values()
                if isinstance(item, dict)
            )
            == [932300, 932301],
            f"magics={plus75.get('planned_variants', {})}",
        ),
        check(
            "plus50_fallback_available",
            plus50.get("status") == "PASS_READY_FOR_REVIEW_NOT_ATTACHED"
            and plus50_row.get("owner_goal_status") == "OWNER_GOAL_PASS_REVIEW_READY",
            f"plus50_status={plus50.get('status')}, gate={plus50_row.get('owner_goal_status')}",
        ),
        check(
            "calendar_cadence_audit_available",
            cadence.get("status") == "PASS_CADENCE_AUDIT_READY",
            f"status={cadence.get('status')}",
        ),
        check(
            "plus75_market_day_cadence_declared",
            plus75_cadence.get("trades_per_market_day", 0) >= 2.0
            and plus75_cadence.get("trades_per_active_day", 0) >= 3.0,
            (
                f"market_day={plus75_cadence.get('trades_per_market_day')}, "
                f"active_day={plus75_cadence.get('trades_per_active_day')}, "
                f"three_plus_market={plus75_cadence.get('three_plus_market_day_pct')}"
            ),
        ),
        check(
            "market_day_coverage_search_available",
            market_day_coverage.get("status") == "PASS_COVERAGE_SEARCH_READY",
            f"status={market_day_coverage.get('status')}",
        ),
        check(
            "market_day_coverage_candidate_declared",
            coverage_best.get("trades_per_market_day", 0) >= 3.0
            and coverage_best.get("win_rate_pct", 0) >= 50.0
            and (coverage_best.get("profit_factor") or 0.0) >= 1.20,
            (
                f"candidate={coverage_best.get('portfolio_name')}, "
                f"guard={coverage_best.get('guard_name')}, "
                f"market_day={coverage_best.get('trades_per_market_day')}, "
                f"wr={coverage_best.get('win_rate_pct')}, pf={coverage_best.get('profit_factor')}"
            ),
        ),
        check(
            "market_day_coverage_stress_available",
            market_day_stress.get("status") == "PASS_CAUSAL_STRESS_REPORT_READY",
            f"status={market_day_stress.get('status')}, decision={market_day_stress.get('decision')}",
        ),
        check(
            "market_day_coverage_stress_reviewable",
            market_day_stress.get("decision") in {"REVISE_ROBUSTNESS", "REVIEW_READY_STRONG_CADENCE"}
            and stress_summary.get("top200_removed_usd", 0) > 0
            and (stress_summary.get("profit_factor") or 0.0) >= 1.20,
            (
                f"decision={market_day_stress.get('decision')}, "
                f"top200={stress_summary.get('top200_removed_usd')}, "
                f"top300={stress_summary.get('top300_removed_usd')}, "
                f"rolling={[(row.get('window'), row.get('negative_windows')) for row in stress_rolling]}"
            ),
        ),
    ]
    status = "PASS_PROMOTION_PACKET_REVIEW_READY"
    if any(item["status"] == "FAIL" for item in checks):
        status = "FAIL"

    return {
        "status": status,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "boundary": "No MT5 runtime, charts, presets, orders, or positions are touched by this promotion packet.",
        "decision": "review_owner_approval_required_before_demo_replacement",
        "recommended_primary": "residual_plus75_high_net",
        "recommended_fallback": "residual_plus50_10m",
        "current_sparse_lane_status": "RR2 long-only remains demoted for primary business goal because it is too sparse.",
        "primary": plus75_row,
        "fallback": plus50_row,
        "primary_readiness": {
            "status": plus75.get("status"),
            "draft": plus75.get("draft"),
            "draft_sha256": plus75.get("draft_sha256"),
            "planned_variants": plus75.get("planned_variants", {}),
            "report": plus75.get("report"),
        },
        "fallback_readiness": {
            "status": plus50.get("status"),
            "draft": plus50.get("draft"),
            "draft_sha256": plus50.get("draft_sha256"),
            "planned_variants": plus50.get("planned_variants", {}),
            "report": plus50.get("report"),
        },
        "calendar_cadence_audit": {
            "status": cadence.get("status"),
            "report": cadence.get("report"),
            "json": cadence.get("json"),
            "date_window": cadence.get("date_window", {}),
            "primary": plus75_cadence,
            "fallback": plus50_cadence,
            "caveat": (
                "Candidates are frequent on active days, but do not trade 3+ times on every market day. "
                "Forward test should judge real active-day coverage before any scale decision."
            ),
        },
        "market_day_coverage_search": {
            "status": market_day_coverage.get("status"),
            "guard_model": market_day_coverage.get("guard_model"),
            "report": market_day_coverage.get("report"),
            "json": market_day_coverage.get("json"),
            "csv": market_day_coverage.get("csv"),
            "best_kept_dropped_csv": market_day_coverage.get("best_kept_dropped_csv"),
            "best_result": coverage_best,
            "caveat": (
                "This causal rerun replaces the rejected 2026-07-02 guarded headline. The candidate "
                "still fits the owner's multiple-trades/day objective better than sparse systems, but "
                "the guard adds little versus no-guard and must not be treated as a proven edge."
            ),
        },
        "market_day_coverage_stress": {
            "status": market_day_stress.get("status"),
            "guard_model": market_day_stress.get("guard_model"),
            "report": market_day_stress.get("report"),
            "json": market_day_stress.get("json"),
            "selected_trades_csv": market_day_stress.get("selected_trades_csv"),
            "decision": market_day_stress.get("decision"),
            "summary": stress_summary,
            "rolling": stress_rolling,
            "caveat": (
                "Causal stress evidence is reviewable but weaker than the rejected headline: all "
                "half-years and quarters are positive and top200-winners-removed stays positive, but "
                "top300-winners-removed is negative and 250-trade rolling windows can go negative. "
                "This is a candidate to refine or forward-test cautiously, not a promotion pass."
            ),
        },
        "forward_demo_rules": {
            "account_scope": "A1 only unless owner separately authorizes a clean-control account.",
            "symbol": "XAUUSD",
            "timeframe": "M5",
            "lot": "0.01 fixed",
            "magics": [932300, 932301],
            "package_guard": "+75 USD target, no shared max-trade cap, 10-minute cooldown after any package loss.",
            "minimum_forward_sample": "At least 4 weeks and at least 150 closed trades before any promotion decision; prefer 8 weeks / 300 trades.",
            "pass_rule": "Forward PF >= 1.25, WR >= 55%, net positive, trades/active day >= 3, trades/market day >= 2 where market is open, positive active days >= 55%, and no single day contributes more than 30% of net.",
            "kill_rule": "Stop or revert if rolling 80-trade PF < 0.95, drawdown exceeds 1.5x historical package DD scaled to lot/account, net negative after 150 trades, or any broker/runtime safety violation appears.",
            "no_tuning_rule": "Do not change hours, filters, RR, package target, cooldown, lot, or magics during the forward window.",
        },
        "checks": checks,
        "inputs": {
            "scoreboard": rel(SCOREBOARD_JSON),
            "plus75_readiness": rel(PLUS75_JSON),
            "plus50_readiness": rel(PLUS50_JSON),
            "calendar_cadence_audit": rel(CALENDAR_CADENCE_JSON),
            "market_day_coverage_search": rel(MARKET_DAY_COVERAGE_JSON),
            "market_day_coverage_stress": rel(MARKET_DAY_COVERAGE_STRESS_JSON),
        },
    }


def render(payload: dict[str, Any]) -> str:
    primary = payload["primary"]
    fallback = payload["fallback"]
    rules = payload["forward_demo_rules"]
    cadence = payload.get("calendar_cadence_audit", {})
    cadence_primary = cadence.get("primary", {})
    cadence_fallback = cadence.get("fallback", {})
    coverage = payload.get("market_day_coverage_search", {})
    coverage_best = coverage.get("best_result", {})
    stress = payload.get("market_day_coverage_stress", {})
    stress_summary = stress.get("summary", {})
    lines = [
        "# A1 XAU M5 Momentum Business-Goal Promotion Packet - 2026-07-02",
        "",
        f"Status: `{payload['status']}`",
        "",
        payload["boundary"],
        "",
        "## Decision",
        "",
        f"Recommended primary forward-demo candidate: `{payload['recommended_primary']}`.",
        "",
        f"Recommended fallback: `{payload['recommended_fallback']}`.",
        "",
        f"Current sparse lane: {payload['current_sparse_lane_status']}",
        "",
        "No runtime replacement is authorized by this packet. Reviewer and owner approval are required first.",
        "",
        "2026-07-02 cadence update: the owner clarified that the replacement must be closer to the original multiple-trades/day vision. A stricter market-day coverage search now exists and should be reviewed before choosing between the simple +75/+50 package and the higher-cadence portfolio candidate.",
        "",
        "## Candidate Comparison",
        "",
        "| Metric | Primary +75 high-net | Fallback +50 smoother |",
        "|---|---:|---:|",
        f"| Trades | {primary.get('trades', 'n/a')} | {fallback.get('trades', 'n/a')} |",
        f"| Win rate | {primary.get('win_rate_pct', 'n/a')}% | {fallback.get('win_rate_pct', 'n/a')}% |",
        f"| Profit factor | {primary.get('profit_factor', 'n/a')} | {fallback.get('profit_factor', 'n/a')} |",
        f"| Net | {primary.get('net', 'n/a')} {primary.get('unit', '')} | {fallback.get('net', 'n/a')} {fallback.get('unit', '')} |",
        f"| Trades / active day | {primary.get('trades_per_active_day', 'n/a')} | {fallback.get('trades_per_active_day', 'n/a')} |",
        f"| 3+ trade active days | {primary.get('three_plus_trade_day_pct', 'n/a')}% | {fallback.get('three_plus_trade_day_pct', 'n/a')}% |",
        f"| Positive active days | {primary.get('positive_day_pct', 'n/a')}% | {fallback.get('positive_day_pct', 'n/a')}% |",
        f"| Top 100 removed | {primary.get('top100_removed', 'n/a')} | {fallback.get('top100_removed', 'n/a')} |",
        f"| Top 200 removed | {primary.get('top200_removed', 'n/a')} | {fallback.get('top200_removed', 'n/a')} |",
        f"| Max closed DD | {primary.get('max_closed_drawdown', 'n/a')} | {fallback.get('max_closed_drawdown', 'n/a')} |",
        f"| Trades / market day | {cadence_primary.get('trades_per_market_day', 'n/a')} | {cadence_fallback.get('trades_per_market_day', 'n/a')} |",
        f"| 3+ trade market days | {cadence_primary.get('three_plus_market_day_pct', 'n/a')}% | {cadence_fallback.get('three_plus_market_day_pct', 'n/a')}% |",
        "",
        "## Calendar Cadence Caveat",
        "",
        cadence.get("caveat", ""),
        "",
        f"Cadence audit: `{cadence.get('report', '')}`",
        "",
        "## Market-Day Coverage Search Candidate",
        "",
        coverage.get("caveat", ""),
        "",
        "| Metric | Value |",
        "|---|---:|",
        f"| Portfolio | `{coverage_best.get('portfolio_name', '')}` |",
        f"| Guard | `{coverage_best.get('guard_name', '')}` |",
        f"| Trades | {coverage_best.get('trades', 'n/a')} |",
        f"| Win rate | {coverage_best.get('win_rate_pct', 'n/a')}% |",
        f"| Profit factor | {coverage_best.get('profit_factor', 'n/a')} |",
        f"| Net | {coverage_best.get('net_usd', 'n/a')} USD |",
        f"| Trades / market day | {coverage_best.get('trades_per_market_day', 'n/a')} |",
        f"| Trades / active day | {coverage_best.get('trades_per_active_day', 'n/a')} |",
        f"| 3+ trade market days | {coverage_best.get('three_plus_market_day_pct', 'n/a')}% |",
        f"| Top 100 removed | {coverage_best.get('top100_removed_usd', 'n/a')} USD |",
        f"| Top 200 removed | {coverage_best.get('top200_removed_usd', 'n/a')} USD |",
        f"| Duplicate drops | {coverage_best.get('duplicate_drops', 'n/a')} |",
        "",
        f"Coverage report: `{coverage.get('report', '')}`",
        "",
        "## Market-Day Coverage Stress",
        "",
        stress.get("caveat", ""),
        "",
        "| Metric | Value |",
        "|---|---:|",
        f"| Stress decision | `{stress.get('decision', '')}` |",
        f"| Trades | {stress_summary.get('trades', 'n/a')} |",
        f"| Win rate | {stress_summary.get('win_rate_pct', 'n/a')}% |",
        f"| Profit factor | {stress_summary.get('profit_factor', 'n/a')} |",
        f"| Net | {stress_summary.get('net_usd', 'n/a')} USD |",
        f"| Top 300 removed | {stress_summary.get('top300_removed_usd', 'n/a')} USD |",
        f"| Max closed DD | {stress_summary.get('max_closed_drawdown_usd', 'n/a')} USD |",
        "",
        f"Stress report: `{stress.get('report', '')}`",
        "",
        "## Forward Demo Rules",
        "",
        "| Field | Rule |",
        "|---|---|",
    ]
    for key, value in rules.items():
        lines.append(f"| `{key}` | {value} |")
    lines.extend(["", "## Checks", "", "| Check | Status | Detail |", "|---|---|---|"])
    for item in payload["checks"]:
        lines.append(f"| `{item['name']}` | `{item['status']}` | {item['detail']} |")
    lines.extend(
        [
            "",
            "## Inputs",
            "",
            f"- Scoreboard: `{payload['inputs']['scoreboard']}`",
            f"- +75 readiness: `{payload['inputs']['plus75_readiness']}`",
            f"- +50 readiness: `{payload['inputs']['plus50_readiness']}`",
            f"- Calendar cadence audit: `{payload['inputs']['calendar_cadence_audit']}`",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> int:
    payload = build_payload()
    output_json = REPORTS_DIR / f"{OUTPUT_STEM}.json"
    output_md = REPORTS_DIR / f"{OUTPUT_STEM}.md"
    payload["report"] = rel(output_md)
    payload["json"] = rel(output_json)
    output_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    output_md.write_text(render(payload), encoding="utf-8")
    print(output_md)
    print(json.dumps({"status": payload["status"], "primary": payload["recommended_primary"]}, indent=2))
    return 0 if payload["status"].startswith("PASS") else 1


if __name__ == "__main__":
    raise SystemExit(main())
