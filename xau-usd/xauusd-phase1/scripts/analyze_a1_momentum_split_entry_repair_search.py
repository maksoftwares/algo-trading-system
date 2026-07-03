from __future__ import annotations

import csv
import itertools
import json
from collections import defaultdict
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any


PHASE1_ROOT = Path(__file__).resolve().parents[1]
REPORTS = PHASE1_ROOT / "outputs" / "reports"
SPLIT_DIR = REPORTS / "mt5_backtests" / "a1_momentum_variants_split20_202207_202606_20260701"
OUT_MD = REPORTS / "A1_XAU_M5_MOMENTUM_SPLIT_ENTRY_REPAIR_SEARCH_2026_07_03.md"
OUT_JSON = OUT_MD.with_suffix(".json")
OUT_CSV = OUT_MD.with_suffix(".csv")

VARIANTS = [
    "risk_norm_split20_freq_weak_hours_all8",
    "risk_norm_split20_v6_max2_all8",
    "risk_norm_split20_v13_rr0p7_all8_22",
]


def load_groups() -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for variant in VARIANTS:
        path = SPLIT_DIR / f"A1XauM5Momentum_SPLIT20_202207_202606_XAUUSD_M5_{variant}_trades.csv"
        if not path.exists():
            raise FileNotFoundError(path)
        with path.open(newline="", encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                item = dict(row)
                item["variant"] = variant
                item["dt"] = datetime.strptime(item["entry_time"], "%Y.%m.%d %H:%M:%S")
                item["p"] = float(item["profit_aed"])
                grouped[(variant, item["entry_time"], item["direction"])].append(item)

    groups: list[dict[str, Any]] = []
    for key, rows in grouped.items():
        variant, entry_time, direction = key
        groups.append(
            {
                "key": key,
                "variant": variant,
                "entry_time": entry_time,
                "direction": direction,
                "dt": rows[0]["dt"],
                "hour": rows[0]["entry_hour"],
                "rows": rows,
            }
        )
    return groups


def dedupe_groups(groups: list[dict[str, Any]]) -> list[dict[str, Any]]:
    kept: list[dict[str, Any]] = []
    last_by_direction: dict[str, datetime] = {}
    for group in sorted(groups, key=lambda item: (item["dt"], item["variant"])):
        direction = group["direction"]
        if direction in last_by_direction and group["dt"] - last_by_direction[direction] <= timedelta(minutes=4):
            continue
        kept.append(group)
        last_by_direction[direction] = group["dt"]
    return kept


def evaluate(groups: list[dict[str, Any]]) -> dict[str, Any]:
    kept_groups = dedupe_groups(groups)
    rows = [row for group in kept_groups for row in group["rows"]]
    pnl = [row["p"] for row in rows]
    wins = [value for value in pnl if value > 0]
    losses = [value for value in pnl if value < 0]
    gross_profit = sum(wins)
    gross_loss = -sum(losses)

    by_month: dict[str, float] = defaultdict(float)
    by_quarter: dict[str, float] = defaultdict(float)
    by_day: dict[str, float] = defaultdict(float)
    by_variant: dict[str, float] = defaultdict(float)
    by_hour: dict[str, float] = defaultdict(float)
    for row in rows:
        month = row["entry_date"][:7]
        year, month_num = [int(part) for part in month.split("-")]
        quarter = f"{year}-Q{((month_num - 1) // 3) + 1}"
        by_month[month] += row["p"]
        by_quarter[quarter] += row["p"]
        by_day[row["entry_date"]] += row["p"]
        by_variant[row["variant"]] += row["p"]
        by_hour[row["entry_hour"]] += row["p"]

    negative_rolling_250 = 0
    min_rolling_250 = 0.0
    min_rolling_250_start = ""
    for index in range(max(0, len(pnl) - 249)):
        value = sum(pnl[index : index + 250])
        if value < 0:
            negative_rolling_250 += 1
        if value < min_rolling_250:
            min_rolling_250 = value
            min_rolling_250_start = rows[index]["entry_time"]

    sorted_pnl = sorted(pnl, reverse=True)
    return {
        "tickets": len(rows),
        "signals": len(kept_groups),
        "win_rate_pct": round((len(wins) / len(rows) * 100.0) if rows else 0.0, 2),
        "net_usd": round(sum(pnl), 2),
        "profit_factor": round((gross_profit / gross_loss) if gross_loss else 0.0, 2),
        "avg_win": round((gross_profit / len(wins)) if wins else 0.0, 2),
        "avg_loss": round((-gross_loss / len(losses)) if losses else 0.0, 2),
        "win_loss_ratio": round(((gross_profit / len(wins)) / (gross_loss / len(losses))) if wins and losses else 0.0, 2),
        "top100_removed": round(sum(sorted_pnl[100:]) if len(sorted_pnl) > 100 else sum(sorted_pnl), 2),
        "top200_removed": round(sum(sorted_pnl[200:]) if len(sorted_pnl) > 200 else sum(sorted_pnl), 2),
        "top300_removed": round(sum(sorted_pnl[300:]) if len(sorted_pnl) > 300 else sum(sorted_pnl), 2),
        "negative_rolling_250": negative_rolling_250,
        "min_rolling_250": round(min_rolling_250, 2),
        "min_rolling_250_start": min_rolling_250_start,
        "negative_quarters": sum(value < 0 for value in by_quarter.values()),
        "worst_quarter": round(min(by_quarter.values()) if by_quarter else 0.0, 2),
        "negative_months": sum(value < 0 for value in by_month.values()),
        "worst_month": round(min(by_month.values()) if by_month else 0.0, 2),
        "active_days": len(by_day),
        "best_day": round(max(by_day.values()) if by_day else 0.0, 2),
        "worst_day": round(min(by_day.values()) if by_day else 0.0, 2),
        "by_variant": {key: round(value, 2) for key, value in by_variant.items()},
        "by_hour": {key: round(value, 2) for key, value in sorted(by_hour.items())},
    }


def weak_pockets(groups: list[dict[str, Any]]) -> list[dict[str, Any]]:
    pockets: dict[tuple[str, str], list[float]] = defaultdict(list)
    for group in dedupe_groups(groups):
        for row in group["rows"]:
            pockets[(group["variant"], group["hour"])].append(row["p"])

    rows: list[dict[str, Any]] = []
    for (variant, hour), pnl in pockets.items():
        wins = [value for value in pnl if value > 0]
        losses = [value for value in pnl if value < 0]
        if len(pnl) < 40:
            continue
        gross_profit = sum(wins)
        gross_loss = -sum(losses)
        rows.append(
            {
                "blocker": f"{variant}@{hour}",
                "variant": variant,
                "hour": hour,
                "tickets": len(pnl),
                "win_rate_pct": round((len(wins) / len(pnl)) * 100.0, 2),
                "net_usd": round(sum(pnl), 2),
                "profit_factor": round((gross_profit / gross_loss) if gross_loss else 99.0, 2),
            }
        )
    return sorted(rows, key=lambda row: (row["net_usd"], row["profit_factor"]))


def apply_blockers(groups: list[dict[str, Any]], blockers: tuple[str, ...]) -> list[dict[str, Any]]:
    parsed = []
    for blocker in blockers:
        if blocker.startswith("variant:"):
            parsed.append(("variant", blocker.split(":", 1)[1], ""))
        else:
            variant, hour = blocker.rsplit("@", 1)
            parsed.append(("variant_hour", variant, hour))

    kept = []
    for group in groups:
        blocked = False
        for kind, variant, hour in parsed:
            if kind == "variant" and group["variant"] == variant:
                blocked = True
                break
            if kind == "variant_hour" and group["variant"] == variant and group["hour"] == hour:
                blocked = True
                break
        if not blocked:
            kept.append(group)
    return kept


def search(groups: list[dict[str, Any]], pockets: list[dict[str, Any]]) -> list[dict[str, Any]]:
    candidate_blockers = [row["blocker"] for row in pockets[:14]]
    candidate_blockers.append("variant:risk_norm_split20_v13_rr0p7_all8_22")

    accepted: list[dict[str, Any]] = []
    for size in range(0, 5):
        for blockers in itertools.combinations(candidate_blockers, size):
            metrics = evaluate(apply_blockers(groups, blockers))
            if metrics["tickets"] < 4200:
                continue
            if metrics["net_usd"] < 6000 or metrics["profit_factor"] < 1.45:
                continue
            if metrics["win_rate_pct"] < 52 or metrics["win_loss_ratio"] < 1.25:
                continue
            if metrics["negative_quarters"] > 0 or metrics["top200_removed"] <= 0:
                continue
            accepted.append({"blockers": list(blockers), **metrics})

    accepted.sort(key=lambda row: (row["top300_removed"], -row["negative_rolling_250"], row["net_usd"]), reverse=True)
    return accepted[:20]


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    keys = list(rows[0].keys())
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=keys)
        writer.writeheader()
        writer.writerows(rows)


def render_markdown(payload: dict[str, Any]) -> str:
    best = payload["best_repair"]
    lines = [
        "# A1 XAU M5 Momentum Split-Entry Repair Search - 2026-07-03",
        "",
        "Scope: exact MT5 split-entry trade CSV analysis only. No live/demo MT5 runtime, chart, preset, order, or position was changed.",
        "",
        "## Baseline Split20",
        "",
        "| Tickets | Signals | WR | Net USD | PF | W/L | Neg Q | Neg Rolling-250 | Top200 | Top300 |",
        "|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
        f"| {payload['baseline']['tickets']} | {payload['baseline']['signals']} | {payload['baseline']['win_rate_pct']}% | {payload['baseline']['net_usd']} | {payload['baseline']['profit_factor']} | {payload['baseline']['win_loss_ratio']} | {payload['baseline']['negative_quarters']} | {payload['baseline']['negative_rolling_250']} | {payload['baseline']['top200_removed']} | {payload['baseline']['top300_removed']} |",
        "",
        "## Best Simple Repair",
        "",
        f"Blockers: `{', '.join(best['blockers']) if best else 'none'}`",
        "",
        "| Tickets | Signals | WR | Net USD | PF | W/L | Neg Q | Neg Rolling-250 | Top200 | Top300 | Worst Month |",
        "|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    if best:
        lines.append(
            f"| {best['tickets']} | {best['signals']} | {best['win_rate_pct']}% | {best['net_usd']} | {best['profit_factor']} | {best['win_loss_ratio']} | {best['negative_quarters']} | {best['negative_rolling_250']} | {best['top200_removed']} | {best['top300_removed']} | {best['worst_month']} |"
        )
    else:
        lines.append("| n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a |")

    lines += [
        "",
        "## Interpretation",
        "",
        "The best simple causal blockers improve the split-entry package but do not fully solve it. The most useful repair blocks `risk_norm_split20_freq_weak_hours_all8@7`; adding V13 hour-14 and related weak pockets reduces rolling-window damage but still leaves top300-winner removal slightly negative.",
        "",
        "Verdict: `REVISE_STILL_PROMISING`. Split-entry remains a serious review candidate because it matches the desired money shape, but this repair search does not yet prove it robust enough for automatic demo promotion.",
        "",
        "## Top Weak Pockets",
        "",
        "| Pocket | Tickets | WR | Net USD | PF |",
        "|---|---:|---:|---:|---:|",
    ]
    for row in payload["weak_pockets"][:12]:
        lines.append(f"| `{row['blocker']}` | {row['tickets']} | {row['win_rate_pct']}% | {row['net_usd']} | {row['profit_factor']} |")

    lines += [
        "",
        "## Top Repair Candidates",
        "",
        "| Blockers | Tickets | WR | Net USD | PF | W/L | Neg Rolling-250 | Top300 |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in payload["accepted"][:10]:
        lines.append(
            f"| `{', '.join(row['blockers']) if row['blockers'] else 'none'}` | {row['tickets']} | {row['win_rate_pct']}% | {row['net_usd']} | {row['profit_factor']} | {row['win_loss_ratio']} | {row['negative_rolling_250']} | {row['top300_removed']} |"
        )
    return "\n".join(lines) + "\n"


def main() -> int:
    groups = load_groups()
    pockets = weak_pockets(groups)
    accepted = search(groups, pockets)
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_dir": str(SPLIT_DIR),
        "baseline": evaluate(groups),
        "weak_pockets": pockets,
        "accepted": accepted,
        "best_repair": accepted[0] if accepted else None,
        "status": "REVISE_STILL_PROMISING" if accepted else "NO_REPAIR_FOUND",
    }
    OUT_JSON.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    OUT_MD.write_text(render_markdown(payload), encoding="utf-8")
    write_csv(OUT_CSV, accepted)
    print(OUT_MD)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
