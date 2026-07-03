from __future__ import annotations

import argparse
import csv
import itertools
import json
from pathlib import Path
from typing import Any

from analyze_a1_momentum_portfolio_combinations import read_trades, summarize


PHASE1_ROOT = Path(__file__).resolve().parents[1]
REPORTS_DIR = PHASE1_ROOT / "outputs" / "reports"


def is_four_year_report(path: Path) -> bool:
    name = path.name.lower()
    if "oos" in name or "current" in name or "two_year" in name or "q2" in name or "june2026" in name:
        return False
    return "four_year" in name or "2022_07_2026_06" in name


def load_variants(report_paths: list[Path]) -> dict[str, dict[str, Any]]:
    variants: dict[str, dict[str, Any]] = {}
    for report_path in report_paths:
        try:
            report = json.loads(report_path.read_text(encoding="utf-8"))
        except Exception:
            continue
        for variant in report.get("variants", []):
            name = str(variant.get("name", ""))
            trade_csv = variant.get("trade_csv")
            if not name or not trade_csv:
                continue
            path = Path(trade_csv)
            if not path.exists():
                continue
            key = name
            trades = read_trades(path, name)
            if len(trades) < 100:
                continue
            summary = summarize(name, trades)
            # Keep the strongest instance if a variant appears in more than one report.
            existing = variants.get(key)
            if existing and existing["summary"].get("trades", 0) >= summary.get("trades", 0):
                continue
            variants[key] = {
                "name": name,
                "label": variant.get("label", ""),
                "report": str(report_path),
                "trade_csv": str(path),
                "trades": trades,
                "summary": summary,
            }
    return variants


def gate(summary: dict[str, Any]) -> str:
    if summary["trades"] < 500:
        return "FAIL_SAMPLE_FOR_PORTFOLIO"
    if summary.get("duplicate_like_trade_pct", 0) > 35:
        return "FAIL_DUPLICATE_STACKING"
    if summary["win_rate_pct"] < 55:
        return "FAIL_WIN_RATE"
    if summary["profit_factor"] is None or summary["profit_factor"] < 1.25:
        return "FAIL_PF"
    if summary["trades_per_active_day"] < 2.0:
        return "FAIL_ACTIVE_DAY_FREQUENCY"
    if summary["active_days"] < 250:
        return "FAIL_ACTIVE_DAY_COVERAGE"
    if summary["top25_removed_usd"] <= 0:
        return "FAIL_TOP_WINNER_ROBUSTNESS"
    if summary["negative_months"] > summary["positive_months"]:
        return "FAIL_MONTH_STABILITY"
    return "REVIEW_CANDIDATE"


def duplicate_like_stats(trades: list[dict[str, Any]]) -> dict[str, Any]:
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for row in trades:
        key = (row["entry_time"].strftime("%Y-%m-%d %H:%M"), row.get("direction", ""))
        grouped.setdefault(key, []).append(row)
    stacked_events = [rows for rows in grouped.values() if len({row["variant"] for row in rows}) > 1]
    duplicate_like_trades = sum(len(rows) for rows in stacked_events)
    return {
        "duplicate_like_events": len(stacked_events),
        "duplicate_like_trades": duplicate_like_trades,
        "duplicate_like_trade_pct": round(100.0 * duplicate_like_trades / len(trades), 2) if trades else 0.0,
    }


def score(summary: dict[str, Any]) -> float:
    pf = float(summary["profit_factor"] or 0)
    net = float(summary["net_usd"])
    active_days = float(summary["active_days"])
    trades_per_active = float(summary["trades_per_active_day"])
    dd = max(float(summary["max_closed_drawdown_usd"] or 1), 1.0)
    month_penalty = max(float(summary["negative_months"]), 1.0)
    return (pf * 1000.0) + (net / dd * 100.0) + active_days + (trades_per_active * 50.0) - (month_penalty * 12.0)


def build_single_rows(variants: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for item in variants.values():
        summary = dict(item["summary"])
        summary.update(duplicate_like_stats(item["trades"]))
        summary["members"] = [item["name"]]
        summary["labels"] = [item["label"]]
        summary["decision"] = gate(summary)
        summary["score"] = round(score(summary), 2)
        rows.append(summary)
    return rows


def build_pair_rows(variants: dict[str, dict[str, Any]], max_pairs: int = 5000) -> list[dict[str, Any]]:
    singles = sorted(
        variants.values(),
        key=lambda item: (
            item["summary"].get("profit_factor") or 0,
            item["summary"].get("net_usd") or 0,
            item["summary"].get("active_days") or 0,
        ),
        reverse=True,
    )
    # Limit search to the strongest single variants to avoid ranking thousands of near-duplicate weak variants.
    pool = singles[:80]
    rows = []
    for left, right in itertools.combinations(pool, 2):
        if left["name"] == right["name"]:
            continue
        trades = list(left["trades"]) + list(right["trades"])
        summary = summarize(f"{left['name']} + {right['name']}", trades)
        summary.update(duplicate_like_stats(trades))
        summary["members"] = [left["name"], right["name"]]
        summary["labels"] = [left["label"], right["label"]]
        summary["decision"] = gate(summary)
        summary["score"] = round(score(summary), 2)
        rows.append(summary)
        if len(rows) >= max_pairs:
            break
    return rows


def compact(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "name": row["name"],
        "decision": row["decision"],
        "score": row["score"],
        "members": row["members"],
        "trades": row["trades"],
        "win_rate_pct": row["win_rate_pct"],
        "net_usd": row["net_usd"],
        "profit_factor": row["profit_factor"],
        "active_days": row["active_days"],
        "trades_per_active_day": row["trades_per_active_day"],
        "multi_trade_days": row["multi_trade_days"],
        "positive_months": row["positive_months"],
        "negative_months": row["negative_months"],
        "worst_month_usd": row["worst_month_usd"],
        "top25_removed_usd": row["top25_removed_usd"],
        "max_closed_drawdown_usd": row["max_closed_drawdown_usd"],
        "duplicate_like_trade_pct": row.get("duplicate_like_trade_pct", 0),
        "duplicate_like_events": row.get("duplicate_like_events", 0),
    }


def render_markdown(rows: list[dict[str, Any]], reports: list[Path], output_json: Path) -> str:
    review = [row for row in rows if row["decision"] == "REVIEW_CANDIDATE"]
    top = review[:20] if review else rows[:20]
    lines = [
        "# A1 XAU M5 Momentum Broad Portfolio Search",
        "",
        "Generated: 2026-07-02",
        "",
        "Scope: offline portfolio search over exact MT5 Strategy Tester trade CSVs. No MT5 runtime, charts, presets, orders, or positions were changed.",
        "",
        "## Source reports",
        "",
    ]
    for report in reports:
        lines.append(f"- `{report}`")
    lines.extend(
        [
            "",
            "## Top Ranked Candidates",
            "",
            "| Rank | Decision | Score | Members | Trades | WR % | Net USD | PF | Active days | T/active | Dup-like % | +M | -M | Worst M | Top25 removed | Max DD |",
            "|---:|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for index, row in enumerate(top, 1):
        lines.append(
            "| {rank} | `{decision}` | {score:.2f} | {members} | {trades} | {wr:.2f} | {net:.2f} | {pf} | {active} | {tpa:.2f} | {dup:.2f} | {pm} | {nm} | {worst:.2f} | {top25:.2f} | {dd:.2f} |".format(
                rank=index,
                decision=row["decision"],
                score=row["score"],
                members="<br>".join(row["members"]),
                trades=row["trades"],
                wr=row["win_rate_pct"],
                net=row["net_usd"],
                pf=row["profit_factor"],
                active=row["active_days"],
                tpa=row["trades_per_active_day"],
                dup=row.get("duplicate_like_trade_pct", 0),
                pm=row["positive_months"],
                nm=row["negative_months"],
                worst=row["worst_month_usd"],
                top25=row["top25_removed_usd"],
                dd=row["max_closed_drawdown_usd"],
            )
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "This search is intentionally broad and therefore diagnostic. It is useful for finding candidate portfolio shapes, not for approving runtime by itself.",
            "",
            "A candidate is only review-worthy if it keeps frequency and quality together: more trades, win rate above 55%, PF at least 1.25, positive after top-winner removal, and no month-stability collapse.",
            "",
            f"Machine-readable output: `{output_json}`",
        ]
    )
    return "\n".join(lines) + "\n"


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    fieldnames = [
        "decision",
        "score",
        "name",
        "members",
        "trades",
        "win_rate_pct",
        "net_usd",
        "profit_factor",
        "active_days",
        "trades_per_active_day",
        "multi_trade_days",
        "positive_months",
        "negative_months",
        "worst_month_usd",
        "top25_removed_usd",
        "max_closed_drawdown_usd",
        "duplicate_like_trade_pct",
        "duplicate_like_events",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            compacted = compact(row)
            compacted["members"] = " + ".join(compacted["members"])
            writer.writerow(compacted)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", action="append", type=Path, default=[])
    parser.add_argument(
        "--output-json",
        type=Path,
        default=REPORTS_DIR / "A1_XAU_M5_MOMENTUM_BROAD_PORTFOLIO_SEARCH_2026_07_02.json",
    )
    parser.add_argument(
        "--output-md",
        type=Path,
        default=REPORTS_DIR / "A1_XAU_M5_MOMENTUM_BROAD_PORTFOLIO_SEARCH_2026_07_02.md",
    )
    parser.add_argument(
        "--output-csv",
        type=Path,
        default=REPORTS_DIR / "A1_XAU_M5_MOMENTUM_BROAD_PORTFOLIO_SEARCH_2026_07_02.csv",
    )
    args = parser.parse_args()

    report_paths = args.report or sorted(path for path in REPORTS_DIR.glob("A1_XAU_M5_MOMENTUM_VARIANT_BACKTEST_*.json") if is_four_year_report(path))
    variants = load_variants(report_paths)
    rows = build_single_rows(variants) + build_pair_rows(variants)
    rows.sort(key=lambda row: (row["decision"] != "REVIEW_CANDIDATE", -row["score"]))
    payload = {
        "status": "BROAD_PORTFOLIO_SEARCH_COMPLETE",
        "boundary": "offline_exact_mt5_trade_csv_analysis_only_no_runtime_change",
        "variant_count": len(variants),
        "candidate_count": len(rows),
        "source_reports": [str(path) for path in report_paths],
        "top_candidates": [compact(row) for row in rows[:100]],
    }
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    args.output_md.write_text(render_markdown(rows, report_paths, args.output_json), encoding="utf-8")
    write_csv(args.output_csv, rows)
    print(args.output_md)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
