from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any


PHASE1_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PHASE1_ROOT.parents[1]
REPORTS_DIR = PHASE1_ROOT / "outputs" / "reports"
OUTPUT_STEM = "A1_XAU_M5_MOMENTUM_BUSINESS_GOAL_SCOREBOARD_2026_07_02"


@dataclass(frozen=True)
class CandidateSource:
    name: str
    source_json: Path
    source_md: Path
    selector: str
    unit: str
    note: str


SOURCES = [
    CandidateSource(
        "freq_first_v4_combo_rank1",
        REPORTS_DIR / "A1_XAU_M5_MOMENTUM_FREQUENCY_FIRST_V4_COMBO_RANK1_VERDICT_2026_07_02.json",
        REPORTS_DIR / "A1_XAU_M5_MOMENTUM_FREQUENCY_FIRST_V4_COMBO_RANK1_VERDICT_2026_07_02.md",
        "repaired_variant",
        "USD",
        "Four-year frequency-first long-only MT5 exact rerun; strong quality but just under 3 trades/active-day.",
    ),
    CandidateSource(
        "feature_loss_daily_guard_best",
        REPORTS_DIR / "A1_XAU_M5_MOMENTUM_FEATURE_LOSS_DAILY_GUARD_OPTIMIZER_2026_07_02.json",
        REPORTS_DIR / "A1_XAU_M5_MOMENTUM_FEATURE_LOSS_DAILY_GUARD_OPTIMIZER_2026_07_02.md",
        "best_frequency_first_candidate",
        "USD",
        "Feature-loss daily guard optimizer best frequency-first candidate.",
    ),
    CandidateSource(
        "feature_band_owner_target_50",
        REPORTS_DIR / "A1_XAU_M5_MOMENTUM_FEATURE_BAND_DAILY_INCOME_TRADEOFF_2026_07_02.json",
        REPORTS_DIR / "A1_XAU_M5_MOMENTUM_FEATURE_BAND_DAILY_INCOME_TRADEOFF_2026_07_02.md",
        "owner_target_50_candidate",
        "USD",
        "Feature-band package with +50 target and max six package trades/day.",
    ),
    CandidateSource(
        "feature_band_max_net",
        REPORTS_DIR / "A1_XAU_M5_MOMENTUM_FEATURE_BAND_DAILY_INCOME_TRADEOFF_2026_07_02.json",
        REPORTS_DIR / "A1_XAU_M5_MOMENTUM_FEATURE_BAND_DAILY_INCOME_TRADEOFF_2026_07_02.md",
        "max_net",
        "USD",
        "Feature-band high-retention max-net row before residual package controls.",
    ),
    CandidateSource(
        "daily_reliability_50_15m",
        REPORTS_DIR / "A1_XAU_M5_MOMENTUM_FEATURE_BAND_DAY_STATE_SEARCH_2026_07_02.json",
        REPORTS_DIR / "A1_XAU_M5_MOMENTUM_FEATURE_BAND_DAY_STATE_SEARCH_2026_07_02.md",
        "best",
        "USD",
        "Daily-reliability package with +50 target, max six trades/day, 15m cooldown after loss.",
    ),
    CandidateSource(
        "residual_reliability_50_15m",
        REPORTS_DIR / "A1_XAU_M5_MOMENTUM_FEATURE_BAND_RELIABILITY_RESIDUAL_SEARCH_2026_07_02.json",
        REPORTS_DIR / "A1_XAU_M5_MOMENTUM_FEATURE_BAND_RELIABILITY_RESIDUAL_SEARCH_2026_07_02.md",
        "best",
        "USD",
        "Residual refinement over daily reliability: block long hour 18 and tighten short close-to-extreme band.",
    ),
    CandidateSource(
        "residual_plus50_10m",
        REPORTS_DIR / "A1_XAU_M5_MOMENTUM_FEATURE_BAND_RESIDUAL_PLUS50_COOLDOWN10_READINESS_2026_07_02.json",
        REPORTS_DIR / "A1_XAU_M5_MOMENTUM_FEATURE_BAND_RESIDUAL_PLUS50_COOLDOWN10_READINESS_2026_07_02.md",
        "candidate",
        "USD",
        "Preferred owner-target residual package: +50 target, max six trades/day, 10m cooldown.",
    ),
    CandidateSource(
        "residual_plus75_high_net",
        REPORTS_DIR / "A1_XAU_M5_MOMENTUM_FEATURE_BAND_RESIDUAL_PLUS75_HIGH_NET_READINESS_2026_07_02.json",
        REPORTS_DIR / "A1_XAU_M5_MOMENTUM_FEATURE_BAND_RESIDUAL_PLUS75_HIGH_NET_READINESS_2026_07_02.md",
        "candidate",
        "USD",
        "Higher-net residual package: +75 target, no shared max-trade cap, 10m cooldown.",
    ),
]


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO_ROOT)).replace("\\", "/")
    except ValueError:
        return str(path)


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def pick(data: dict[str, Any], selector: str) -> dict[str, Any]:
    current: Any = data
    for part in selector.split("."):
        if not isinstance(current, dict):
            return {}
        current = current.get(part, {})
    return current if isinstance(current, dict) else {}


def number(item: dict[str, Any], *keys: str, default: float = 0.0) -> float:
    for key in keys:
        value = item.get(key)
        if value is None:
            continue
        try:
            return float(value)
        except (TypeError, ValueError):
            continue
    return default


def owner_goal_status(row: dict[str, Any]) -> str:
    if row["trades"] < 1000:
        return "FAIL_SAMPLE"
    if row["trades_per_active_day"] < 2.0:
        return "FAIL_SPARSE"
    if row["win_rate_pct"] < 50.0 or row["profit_factor"] < 1.20 or row["net"] <= 0:
        return "FAIL_QUALITY"
    if row["trades_per_active_day"] >= 3.0 and row["three_plus_trade_day_pct"] >= 50.0:
        if row["positive_day_pct"] >= 60.0 and row["top100_removed"] > 0:
            return "OWNER_GOAL_PASS_REVIEW_READY"
        return "OWNER_GOAL_PASS_WITH_DAY_RATE_CAVEAT"
    return "FREQUENCY_BORDERLINE_REVIEW_ONLY"


def score(row: dict[str, Any]) -> float:
    status_bonus = {
        "OWNER_GOAL_PASS_REVIEW_READY": 300.0,
        "OWNER_GOAL_PASS_WITH_DAY_RATE_CAVEAT": 220.0,
        "FREQUENCY_BORDERLINE_REVIEW_ONLY": 120.0,
        "FAIL_SAMPLE": -500.0,
        "FAIL_SPARSE": -600.0,
        "FAIL_QUALITY": -800.0,
    }.get(row["owner_goal_status"], 0.0)
    return round(
        status_bonus
        + row["win_rate_pct"] * 2.0
        + row["profit_factor"] * 80.0
        + row["trades_per_active_day"] * 35.0
        + row["three_plus_trade_day_pct"] * 1.2
        + row["positive_day_pct"] * 1.6
        + min(row["net"], 2500.0) / 10.0
        + min(max(row["top100_removed"], 0.0), 1500.0) / 15.0
        - row["max_closed_drawdown"] / 4.0,
        2,
    )


def normalize(source: CandidateSource, data: dict[str, Any], candidate: dict[str, Any]) -> dict[str, Any]:
    row = {
        "name": source.name,
        "unit": source.unit,
        "source": rel(source.source_md),
        "source_json": rel(source.source_json),
        "note": source.note,
        "trades": number(candidate, "trades"),
        "win_rate_pct": number(candidate, "win_rate_pct"),
        "net": number(candidate, "net_usd", "pnl_aed", "net_profit_usd", "net_profit_aed"),
        "profit_factor": number(candidate, "profit_factor"),
        "active_days": number(candidate, "active_days"),
        "trades_per_active_day": number(candidate, "trades_per_active_day", "avg_trades_active_day"),
        "three_plus_trade_day_pct": number(candidate, "three_plus_trade_day_pct"),
        "positive_day_pct": number(candidate, "positive_day_pct"),
        "positive_months": number(candidate, "positive_months"),
        "negative_months": number(candidate, "negative_months"),
        "top100_removed": number(candidate, "top100_removed_usd", "net_ex_top_10"),
        "top200_removed": number(candidate, "top200_removed_usd"),
        "max_closed_drawdown": number(candidate, "max_closed_drawdown_usd"),
        "older_net": number(candidate, "older_net_usd"),
        "newer_net": number(candidate, "newer_net_usd"),
        "decision": str(candidate.get("decision", data.get("status", ""))),
    }
    if row["positive_day_pct"] == 0.0 and row["active_days"] > 0:
        positive_days = number(candidate, "positive_days")
        if positive_days > 0:
            row["positive_day_pct"] = round((positive_days / row["active_days"]) * 100.0, 2)
    row["owner_goal_status"] = owner_goal_status(row)
    row["business_score"] = score(row)
    return row


def collect_candidates() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for source in SOURCES:
        if not source.source_json.exists():
            continue
        data = load_json(source.source_json)
        candidate = pick(data, source.selector)
        if candidate:
            rows.append(normalize(source, data, candidate))
    rows.sort(key=lambda item: item["business_score"], reverse=True)
    for index, row in enumerate(rows, start=1):
        row["rank"] = index
    return rows


def render_markdown(payload: dict[str, Any]) -> str:
    rows = payload["rows"]
    best = rows[0] if rows else {}
    pass_rows = [row for row in rows if row["owner_goal_status"].startswith("OWNER_GOAL_PASS")]
    lines = [
        "# A1 XAU M5 Momentum Business-Goal Scoreboard - 2026-07-02",
        "",
        f"Status: `{payload['status']}`",
        "",
        "Purpose: rank the current XAU M5 momentum candidates by the owner's actual target: frequent intraday trading, win rate above 50%, positive PF/net, and robustness after removing large winners. Sparse strategies are penalized even when their PF looks good.",
        "",
        "## Business Gate",
        "",
        "| Requirement | Rule |",
        "|---|---|",
        "| Sample | At least 1000 trades for this historical screen |",
        "| Cadence | Hard minimum 2 trades/active day; preferred 3+ trades/active day |",
        "| Win rate | At least 50% |",
        "| Profit factor | At least 1.20 for this scoreboard |",
        "| Frequent-day shape | Preferred 3+ trade active days >= 50% |",
        "| Day reliability | Preferred positive active days >= 60% |",
        "| Robustness | Top-100 winners removed should remain positive where available |",
        "",
        "## Verdict",
        "",
    ]
    if best:
        lines.extend(
            [
                f"Current top-ranked candidate: `{best['name']}` with status `{best['owner_goal_status']}`.",
                "",
                f"It has `{best['trades']:.0f}` trades, `{best['win_rate_pct']:.2f}%` win rate, PF `{best['profit_factor']:.2f}`, net `{best['net']:.2f}` {best['unit']}, `{best['trades_per_active_day']:.2f}` trades/active day, and `{best['positive_day_pct']:.2f}%` positive active days.",
                "",
            ]
        )
    lines.extend(
        [
            f"Candidates passing the owner-frequency/quality gate: `{len(pass_rows)}` of `{len(rows)}`.",
            "",
            "## Ranked Candidates",
            "",
            "| Rank | Candidate | Status | Score | Trades | WR | PF | Net | T/active | 3+ days | Pos days | Top100 removed | DD | Note |",
            "|---:|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|",
        ]
    )
    for row in rows:
        lines.append(
            f"| {row['rank']} | `{row['name']}` | `{row['owner_goal_status']}` | {row['business_score']:.2f} | "
            f"{row['trades']:.0f} | {row['win_rate_pct']:.2f}% | {row['profit_factor']:.2f} | "
            f"{row['net']:.2f} {row['unit']} | {row['trades_per_active_day']:.2f} | "
            f"{row['three_plus_trade_day_pct']:.2f}% | {row['positive_day_pct']:.2f}% | "
            f"{row['top100_removed']:.2f} | {row['max_closed_drawdown']:.2f} | {row['note']} |"
        )
    lines.extend(
        [
            "",
            "## Actionable Reading",
            "",
            "- `residual_plus75_high_net` is the strongest match for the raw daily-trading vision because it has the highest net and highest cadence, but it carries the explicit trade-off of lower positive-day rate than the +50 package.",
            "- `residual_plus50_10m` is the smoother owner-target package: lower net, lower cadence, but better positive-day rate.",
            "- `freq_first_v4_combo_rank1` remains useful as a simpler long-only baseline, but it is borderline on the preferred 3 trades/active-day cadence.",
            "- Do not promote sparse RR2-style candidates as the primary path even if their PF is attractive.",
            "",
            "## Artifacts",
            "",
            f"- JSON: `{payload['json']}`",
            f"- CSV: `{payload['csv']}`",
        ]
    )
    return "\n".join(lines) + "\n"


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    fieldnames = [
        "rank",
        "name",
        "owner_goal_status",
        "business_score",
        "trades",
        "win_rate_pct",
        "profit_factor",
        "net",
        "unit",
        "active_days",
        "trades_per_active_day",
        "three_plus_trade_day_pct",
        "positive_day_pct",
        "positive_months",
        "negative_months",
        "top100_removed",
        "top200_removed",
        "max_closed_drawdown",
        "older_net",
        "newer_net",
        "source",
        "source_json",
        "note",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fieldnames})


def main() -> int:
    rows = collect_candidates()
    status = "PASS_SCOREBOARD_READY" if rows else "FAIL_NO_CANDIDATES"
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    output_md = REPORTS_DIR / f"{OUTPUT_STEM}.md"
    output_json = REPORTS_DIR / f"{OUTPUT_STEM}.json"
    output_csv = REPORTS_DIR / f"{OUTPUT_STEM}.csv"
    payload = {
        "status": status,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "business_requirement": {
            "hard_min_trades_per_active_day": 2.0,
            "preferred_min_trades_per_active_day": 3.0,
            "preferred_min_three_plus_trade_day_pct": 50.0,
            "min_win_rate_pct": 50.0,
            "min_profit_factor": 1.20,
            "sparse_strategy_policy": "Fail or demote any candidate that wins by starving trade count.",
        },
        "rows": rows,
        "report": rel(output_md),
        "json": rel(output_json),
        "csv": rel(output_csv),
    }
    output_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    output_md.write_text(render_markdown(payload), encoding="utf-8")
    write_csv(output_csv, rows)
    print(output_md)
    print(json.dumps({"status": status, "top": rows[0]["name"] if rows else None}, indent=2))
    return 0 if rows else 1


if __name__ == "__main__":
    raise SystemExit(main())
