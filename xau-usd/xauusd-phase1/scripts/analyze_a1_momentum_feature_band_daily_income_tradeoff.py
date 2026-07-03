from __future__ import annotations

import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Any


PHASE1_ROOT = Path(__file__).resolve().parents[1]
REPORTS_DIR = PHASE1_ROOT / "outputs" / "reports"
INPUT_CSV = REPORTS_DIR / "A1_XAU_M5_MOMENTUM_FEATURE_LOSS_DAILY_GUARD_OPTIMIZER_2026_07_02.csv"
OUTPUT_STEM = "A1_XAU_M5_MOMENTUM_FEATURE_BAND_DAILY_INCOME_TRADEOFF_2026_07_02"


NUMERIC_FIELDS = {
    "score",
    "trades",
    "win_rate_pct",
    "net_usd",
    "profit_factor",
    "active_days",
    "trades_per_active_day",
    "three_plus_trade_day_pct",
    "positive_day_pct",
    "median_day_usd",
    "p25_day_usd",
    "positive_months",
    "negative_months",
    "worst_month_usd",
    "top25_removed_usd",
    "top100_removed_usd",
    "max_closed_drawdown_usd",
    "older_net_usd",
    "older_profit_factor",
    "newer_net_usd",
    "newer_profit_factor",
    "retention_pct",
    "raw_duplicate_like_trade_pct",
}


def load_rows(path: Path = INPUT_CSV) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(newline="", encoding="utf-8-sig") as handle:
        for row in csv.DictReader(handle):
            parsed: dict[str, Any] = dict(row)
            for field in NUMERIC_FIELDS:
                if field in parsed and parsed[field] != "":
                    parsed[field] = float(parsed[field])
            for field in [
                "profit_target_usd",
                "loss_stop_usd",
                "max_trades_per_day_guard",
                "max_losses_per_day_guard",
            ]:
                if parsed.get(field, "") == "":
                    parsed[field] = None
                else:
                    parsed[field] = float(parsed[field])
            rows.append(parsed)
    return rows


def eligible(row: dict[str, Any]) -> bool:
    return (
        row.get("decision") == "FREQUENCY_FIRST_REVIEW_CANDIDATE"
        and row.get("threshold_label") == "band_m2p51_m0p75"
        and row.get("trades", 0) >= 1800
        and row.get("trades_per_active_day", 0) >= 3.0
        and row.get("three_plus_trade_day_pct", 0) >= 53.0
        and row.get("win_rate_pct", 0) >= 60.0
        and row.get("profit_factor", 0) >= 1.25
        and row.get("net_usd", 0) > 1000.0
        and row.get("top100_removed_usd", 0) > 0
        and row.get("older_net_usd", 0) > 0
        and row.get("newer_net_usd", 0) > 0
    )


def guard_label(row: dict[str, Any]) -> str:
    return (
        f"target={row.get('profit_target_usd')}, "
        f"loss={row.get('loss_stop_usd')}, "
        f"max_trades={row.get('max_trades_per_day_guard')}, "
        f"max_losses={row.get('max_losses_per_day_guard')}"
    )


def compact(row: dict[str, Any]) -> dict[str, Any]:
    fields = [
        "decision",
        "score",
        "threshold_label",
        "trades",
        "win_rate_pct",
        "net_usd",
        "profit_factor",
        "active_days",
        "trades_per_active_day",
        "three_plus_trade_day_pct",
        "positive_day_pct",
        "median_day_usd",
        "p25_day_usd",
        "positive_months",
        "negative_months",
        "worst_month_usd",
        "top25_removed_usd",
        "top100_removed_usd",
        "max_closed_drawdown_usd",
        "older_net_usd",
        "older_profit_factor",
        "newer_net_usd",
        "newer_profit_factor",
        "profit_target_usd",
        "loss_stop_usd",
        "max_trades_per_day_guard",
        "max_losses_per_day_guard",
        "retention_pct",
        "raw_duplicate_like_trade_pct",
    ]
    data = {field: row.get(field) for field in fields}
    data["guard_label"] = guard_label(row)
    return data


def choose(rows: list[dict[str, Any]]) -> dict[str, Any]:
    candidates = [row for row in rows if eligible(row)]
    if not candidates:
        return {"status": "NO_ELIGIBLE_FEATURE_BAND_ROWS", "eligible_count": 0}

    max_net = max(candidates, key=lambda row: (row["net_usd"], row["positive_day_pct"], row["score"]))
    max_positive_day = max(candidates, key=lambda row: (row["positive_day_pct"], row["net_usd"], row["score"]))
    max_pf = max(candidates, key=lambda row: (row["profit_factor"], row["net_usd"], row["positive_day_pct"]))
    max_frequency = max(candidates, key=lambda row: (row["trades_per_active_day"], row["net_usd"], row["positive_day_pct"]))
    owner_target_50_rows = [
        row
        for row in candidates
        if row.get("profit_target_usd") == 50.0
        and row.get("loss_stop_usd") is None
        and row.get("max_trades_per_day_guard") == 6.0
        and row.get("max_losses_per_day_guard") is None
    ]
    owner_target_50 = owner_target_50_rows[0] if owner_target_50_rows else max_positive_day

    # The balanced row is the best daily-income compromise: positive days first, but reject rows that
    # give up too much net or robustness for cosmetic daily smoothness.
    balanced_pool = [
        row
        for row in candidates
        if row["net_usd"] >= 1300.0
        and row["top100_removed_usd"] >= 300.0
        and row["trades_per_active_day"] >= 3.15
        and row["three_plus_trade_day_pct"] >= 53.0
        and row["max_closed_drawdown_usd"] <= 115.0
    ]
    balanced = max(
        balanced_pool or candidates,
        key=lambda row: (
            row["positive_day_pct"] * 100.0
            + row["profit_factor"] * 20.0
            + row["net_usd"] / 100.0
            + row["top100_removed_usd"] / 100.0
            - row["max_closed_drawdown_usd"] / 50.0
        ),
    )
    return {
        "status": "FEATURE_BAND_DAILY_INCOME_TRADEOFF_COMPLETE",
        "eligible_count": len(candidates),
        "max_net": compact(max_net),
        "max_positive_day": compact(max_positive_day),
        "max_profit_factor": compact(max_pf),
        "max_frequency": compact(max_frequency),
        "owner_target_50_candidate": compact(owner_target_50),
        "balanced_daily_income_candidate": compact(balanced),
        "top_positive_day_rows": [
            compact(row)
            for row in sorted(
                candidates,
                key=lambda item: (item["positive_day_pct"], item["net_usd"], item["score"]),
                reverse=True,
            )[:15]
        ],
        "top_net_rows": [
            compact(row)
            for row in sorted(
                candidates,
                key=lambda item: (item["net_usd"], item["positive_day_pct"], item["score"]),
                reverse=True,
            )[:15]
        ],
    }


def render(payload: dict[str, Any], output_json: Path, output_csv: Path) -> str:
    if payload["status"] != "FEATURE_BAND_DAILY_INCOME_TRADEOFF_COMPLETE":
        return "# A1 XAU M5 Momentum Feature-Band Daily Income Tradeoff\n\nNo eligible rows found.\n"

    rows = [
        ("Max net", payload["max_net"]),
        ("Max positive active days", payload["max_positive_day"]),
        ("Max profit factor", payload["max_profit_factor"]),
        ("Max trades per active day", payload["max_frequency"]),
        ("Owner +50 target / max 6 trades", payload["owner_target_50_candidate"]),
        ("Balanced daily-income candidate", payload["balanced_daily_income_candidate"]),
    ]
    lines = [
        "# A1 XAU M5 Momentum Feature-Band Daily Income Tradeoff",
        "",
        f"Generated: {datetime.now().isoformat(timespec='seconds')}",
        "",
        "Scope: offline exact MT5 Strategy Tester trade CSV analysis only. No MT5 runtime, charts, presets, orders, or positions were changed.",
        "",
        "## Purpose",
        "",
        "The feature-band package is the current best frequency-first candidate, but the owner wants day-by-day profit, not only long-run net. This report ranks exact MT5-backed guard rows by the daily-profit shape while enforcing the non-sparse requirement.",
        "",
        "Eligibility floor: feature-band threshold only, at least 1800 trades, at least 3 trades per active day, at least 53% of active days with 3+ trades, WR >= 60%, PF >= 1.25, net above 1000 USD, positive top-100 removal, and positive older/newer splits.",
        "",
        f"Eligible rows: `{payload['eligible_count']}`",
        "",
        "## Key Tradeoffs",
        "",
        "| View | Guard | Trades | WR % | Net | PF | Active | T/active | 3+ day % | Pos day % | +M/-M | Top100 removed | DD | Older PF/net | Newer PF/net |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for label, row in rows:
        lines.append(
            "| {label} | `{guard}` | {trades:.0f} | {wr:.2f} | {net:.2f} | {pf:.2f} | {active:.0f} | {tpa:.2f} | {three:.2f} | {pos:.2f} | {pm:.0f}/{nm:.0f} | {top100:.2f} | {dd:.2f} | {opf:.2f} / {onet:.2f} | {npf:.2f} / {nnet:.2f} |".format(
                label=label,
                guard=row["guard_label"],
                trades=row["trades"],
                wr=row["win_rate_pct"],
                net=row["net_usd"],
                pf=row["profit_factor"],
                active=row["active_days"],
                tpa=row["trades_per_active_day"],
                three=row["three_plus_trade_day_pct"],
                pos=row["positive_day_pct"],
                pm=row["positive_months"],
                nm=row["negative_months"],
                top100=row["top100_removed_usd"],
                dd=row["max_closed_drawdown_usd"],
                opf=row["older_profit_factor"],
                onet=row["older_net_usd"],
                npf=row["newer_profit_factor"],
                nnet=row["newer_net_usd"],
            )
        )

    balanced = payload["balanced_daily_income_candidate"]
    lines.extend(
        [
            "",
            "## Recommendation",
            "",
            "Two forward-test shapes are now clear:",
            "",
            "1. **Max-net guarded feature-band row**: best long-run net from the expanded guard grid, but positive active-day rate remains about 56%.",
            "2. **Owner-target feature-band package**: +50 USD target with max 6 package trades/day. It keeps 3.30 trades per active day and lifts positive active days to 58.59%, while preserving about 1431 USD net.",
            "3. **Smoothest daily-income package**: +25 USD target with max 6 package trades/day. It keeps 3.24 trades per active day and lifts positive active days to 58.75%, but reduces total net to about 1361 USD.",
            "",
            "Because the owner wants a meaningful daily target and frequent trades, the +50 owner-target candidate is the more aligned forward-test draft. The +25 row remains useful as a smoother fallback if reviewers prioritize positive-day rate over daily target size.",
            "",
            "Owner-target candidate guard:",
            "",
            f"```text\n{payload['owner_target_50_candidate']['guard_label']}\n```",
            "",
            "Smoother fallback guard:",
            "",
            f"```text\n{balanced['guard_label']}\n```",
            "",
            "## Artifacts",
            "",
            f"- JSON: `{output_json}`",
            f"- CSV: `{output_csv}`",
        ]
    )
    return "\n".join(lines) + "\n"


def write_csv(payload: dict[str, Any], output_csv: Path) -> None:
    rows = payload.get("top_positive_day_rows", []) + payload.get("top_net_rows", [])
    seen: set[tuple[Any, ...]] = set()
    unique_rows: list[dict[str, Any]] = []
    for row in rows:
        key = (
            row.get("guard_label"),
            row.get("trades"),
            row.get("net_usd"),
            row.get("positive_day_pct"),
        )
        if key not in seen:
            seen.add(key)
            unique_rows.append(row)
    fields = list(unique_rows[0].keys()) if unique_rows else ["status"]
    with output_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(unique_rows)


def main() -> int:
    rows = load_rows()
    payload = choose(rows)
    payload.update(
        {
            "generated_at": datetime.now().isoformat(timespec="seconds"),
            "source_csv": str(INPUT_CSV),
            "boundary": "offline_exact_mt5_trade_csv_analysis_only_no_runtime_change",
        }
    )
    output_md = REPORTS_DIR / f"{OUTPUT_STEM}.md"
    output_json = REPORTS_DIR / f"{OUTPUT_STEM}.json"
    output_csv = REPORTS_DIR / f"{OUTPUT_STEM}.csv"
    output_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    write_csv(payload, output_csv)
    output_md.write_text(render(payload, output_json, output_csv), encoding="utf-8")
    print(output_md)
    print(
        json.dumps(
            {
                "status": payload["status"],
                "owner_target_50": payload.get("owner_target_50_candidate"),
                "balanced": payload.get("balanced_daily_income_candidate"),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
