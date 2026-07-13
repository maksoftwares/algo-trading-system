from __future__ import annotations

import argparse
import csv
import json
import re
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

from analyze_a1_r1_box_r3_overlap_priority_audit import ledger_book
from analyze_a1_owner_goal_step3_portfolio_composition import REPORTS_DIR
from analyze_a1_xau_source_monthly_firewall import read_ledger
from run_a1_h4_d1_review_repair_exact import period_stats


RISK_UNIT_USD = 50.0
OVERLAP_WINDOW_SECONDS = 15 * 60
SIGNAL_MATCH_WINDOW_SECONDS = 5 * 60
OUTPUT_STEM = "A1_XAU_R2_PRIOR_D1_LOW_FIRST_RETEST_SHORT_V1_EXACT_20260710"
VARIANT_NAME = "r2_pdl_first_retest_structural_v1"

NORMALIZED_CSV = REPORTS_DIR / f"{OUTPUT_STEM}_{VARIANT_NAME}_NORMALIZED_TRADES.csv"
MT5_COMPONENTS_JSON = REPORTS_DIR / f"{OUTPUT_STEM}_MT5_COMPONENTS.json"
REPORT_MD = REPORTS_DIR / f"{OUTPUT_STEM}_EPISODE_AUDIT.md"
REPORT_JSON = REPORTS_DIR / f"{OUTPUT_STEM}_EPISODE_AUDIT.json"

CONTROL_PATHS = {
    "r2_pullback_v2_hours05_18": REPORTS_DIR
    / "A1_XAU_R2_PULLBACK_REJECTION_SHORT_V2_REPAIR_EXACT_20260709_r2_h1_m5_body58_hours05_18_NORMALIZED_TRADES.csv",
    "r2_continuation_v1_body45": REPORTS_DIR
    / "A1_XAU_R2_CONTINUATION_SHORT_V1_EXACT_20260709_r2_impulse_retest_body45_NORMALIZED_TRADES.csv",
    "r2_continuation_v2_break15_30": REPORTS_DIR
    / "A1_XAU_R2_CONTINUATION_SHORT_V2_REPAIR_EXACT_20260709_r2_impulse_break15_30_cap20_NORMALIZED_TRADES.csv",
    "r2_continuation_v4_atr45": REPORTS_DIR
    / "A1_XAU_R2_CONTINUATION_SHORT_V4_VOLATILITY_GATE_EXACT_20260709_r2_impulse_body45_atr45_NORMALIZED_TRADES.csv",
    "r2_continuation_v4_atr50": REPORTS_DIR
    / "A1_XAU_R2_CONTINUATION_SHORT_V4_VOLATILITY_GATE_EXACT_20260709_r2_impulse_body45_atr50_NORMALIZED_TRADES.csv",
    "r2_continuation_v4_atr45_daily_loss10": REPORTS_DIR
    / "A1_XAU_R2_CONTINUATION_SHORT_V4_VOLATILITY_GATE_EXACT_20260709_r2_impulse_body45_atr45_daily_loss10_NORMALIZED_TRADES.csv",
}

PARTITIONS = {
    "development_2022h2_2023": (date(2022, 7, 1), date(2023, 12, 31)),
    "locked_replication_2024_2026h1": (date(2024, 1, 1), date(2026, 6, 30)),
}

EPISODES = {
    "downtrend_2022": (date(2022, 7, 1), date(2022, 11, 4)),
    "downtrend_2023_oct": (date(2023, 10, 2), date(2023, 10, 13)),
    "downtrend_2026": (date(2026, 3, 1), date(2026, 6, 30)),
}


def require_file(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(path)


def parse_signal_time(value: str) -> datetime:
    value = value.strip()
    for fmt in ("%Y.%m.%d %H:%M:%S", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            pass
    raise ValueError(value)


def basic_period(rows: list[dict[str, Any]], name: str, start: date, end: date) -> dict[str, Any]:
    row = period_stats(rows, start, end)
    return {"name": name, "start": start.isoformat(), "end": end.isoformat(), **row}


def longest_losing_streak(rows: list[dict[str, Any]]) -> int:
    current = 0
    longest = 0
    for row in sorted(rows, key=lambda item: (item["exit_time"], item["entry_time"])):
        if float(row.get("pnl_usd") or 0.0) < 0.0:
            current += 1
            longest = max(longest, current)
        else:
            current = 0
    return longest


def parse_money_prefix(value: Any) -> float | None:
    match = re.search(r"[-+]?\d[\d ]*(?:\.\d+)?", str(value or ""))
    if not match:
        return None
    return float(match.group(0).replace(" ", ""))


def max_equity_dd_from_mt5(path: Path) -> float | None:
    payload = json.loads(path.read_text(encoding="utf-8"))
    variants = payload.get("variants", [])
    if len(variants) != 1:
        return None
    metrics = variants[0].get("mt5_report_metrics", {})
    return parse_money_prefix(metrics.get("Equity Drawdown Maximal"))


def read_signal_reasons(path: Path) -> list[dict[str, Any]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        rows = csv.DictReader(handle, delimiter="\t")
        output: list[dict[str, Any]] = []
        for row in rows:
            if row.get("stage") != "WOULD_SIGNAL":
                continue
            output.append(
                {
                    "timestamp": parse_signal_time(row["timestamp_broker"]),
                    "direction": str(row.get("direction", "")).upper(),
                    "reason": row.get("reason", ""),
                }
            )
        return output


def native_regime_purity(rows: list[dict[str, Any]], signal_reasons: list[dict[str, Any]]) -> dict[str, Any]:
    matched = 0
    downtrend = 0
    missing: list[str] = []
    for row in rows:
        entry_time = row["entry_time"]
        direction = str(row.get("direction", "")).upper()
        candidates = [
            signal
            for signal in signal_reasons
            if signal["direction"] == direction
            and abs((entry_time - signal["timestamp"]).total_seconds()) <= SIGNAL_MATCH_WINDOW_SECONDS
        ]
        if not candidates:
            missing.append(entry_time.strftime("%Y-%m-%d %H:%M:%S"))
            continue
        nearest = min(candidates, key=lambda signal: abs((entry_time - signal["timestamp"]).total_seconds()))
        reason = nearest["reason"]
        matched += 1
        if reason.endswith("_STATE_downtrend"):
            downtrend += 1
    purity = 100.0 * downtrend / len(rows) if rows else 0.0
    return {
        "trades": len(rows),
        "matched_signal_reasons": matched,
        "downtrend_reasons": downtrend,
        "purity_pct": round(purity, 2),
        "missing_entry_times": missing,
    }


def overlap_with_control(candidate: list[dict[str, Any]], control: list[dict[str, Any]], name: str) -> dict[str, Any]:
    control_by_direction: dict[str, list[datetime]] = {}
    for row in control:
        control_by_direction.setdefault(str(row.get("direction", "")), []).append(row["entry_time"])
    for times in control_by_direction.values():
        times.sort()

    overlaps = 0
    for row in candidate:
        entry = row["entry_time"]
        times = control_by_direction.get(str(row.get("direction", "")), [])
        if any(abs((entry - other).total_seconds()) <= OVERLAP_WINDOW_SECONDS for other in times):
            overlaps += 1
    return {
        "control": name,
        "candidate_trades": len(candidate),
        "overlap_trades": overlaps,
        "overlap_pct": round(100.0 * overlaps / len(candidate), 2) if candidate else 0.0,
    }


def episode_concentration(episode_rows: list[dict[str, Any]]) -> float:
    positive = [max(0.0, float(row["net_usd"])) for row in episode_rows]
    denominator = sum(positive)
    return round(100.0 * max(positive, default=0.0) / denominator, 2) if denominator > 0.0 else 0.0


def build_audit(
    normalized_csv: Path,
    signal_csv: Path,
    mt5_components_json: Path,
    control_paths: dict[str, Path] | None = None,
) -> dict[str, Any]:
    require_file(normalized_csv)
    require_file(signal_csv)
    require_file(mt5_components_json)
    rows = read_ledger(normalized_csv)
    full = ledger_book(VARIANT_NAME, rows)
    partitions = [basic_period(rows, name, *window) for name, window in PARTITIONS.items()]
    episodes = [basic_period(rows, name, *window) for name, window in EPISODES.items()]
    positive_episodes = sum(1 for row in episodes if row["net_usd"] > 0.0)
    episode_share = episode_concentration(episodes)
    equity_dd = max_equity_dd_from_mt5(mt5_components_json)
    losing_streak = longest_losing_streak(rows)
    regime = native_regime_purity(rows, read_signal_reasons(signal_csv))

    overlap_rows: list[dict[str, Any]] = []
    for name, path in (control_paths or CONTROL_PATHS).items():
        require_file(path)
        overlap_rows.append(overlap_with_control(rows, read_ledger(path), name))

    locked = next(row for row in partitions if row["name"].startswith("locked_replication"))
    checks = {
        "trades_ge_80": full["signals"] >= 80,
        "locked_trades_ge_20": locked["signals"] >= 20,
        "wr_ge_50": full["wr"] >= 50.0,
        "wl_ge_1p90": (full["wl"] or 0.0) >= 1.90,
        "pf_ge_2": (full["pf"] or 0.0) >= 2.00,
        "stress_pf_ge_1p90": (full["stress_030_pf"] or 0.0) >= 1.90,
        "stress_net_gt_0": full["stress_030_net"] > 0.0,
        "locked_net_gt_0": locked["net_usd"] > 0.0,
        "locked_pf_ge_1p50": (locked["profit_factor"] or 0.0) >= 1.50,
        "positive_episodes_ge_2": positive_episodes >= 2,
        "episode_positive_net_share_lte_60pct": episode_share <= 60.0,
        "native_regime_purity_100pct": regime["purity_pct"] == 100.0 and not regime["missing_entry_times"],
        "closed_dd_lte_12r": full["max_closed_dd"] <= 12.0 * RISK_UNIT_USD,
        "equity_dd_field_present": equity_dd is not None,
        "equity_dd_lte_15r": equity_dd is not None and equity_dd <= 15.0 * RISK_UNIT_USD,
        "longest_losing_streak_lte_8": losing_streak <= 8,
        "top10_removed_net_gt_0": full["top10_removed_net"] > 0.0,
        "top3_days_removed_net_gt_0": full["top3_days_removed_net"] > 0.0,
        "best_month_share_lte_30pct": full["best_month_share_pct"] is not None and full["best_month_share_pct"] <= 30.0,
        "all_control_overlap_lte_30pct": all(row["overlap_pct"] <= 30.0 for row in overlap_rows),
    }
    return {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "normalized_csv": str(normalized_csv),
        "signal_csv": str(signal_csv),
        "mt5_components_json": str(mt5_components_json),
        "full": full,
        "partitions": partitions,
        "episodes": episodes,
        "positive_episodes": positive_episodes,
        "episode_positive_net_share_pct": episode_share,
        "max_equity_dd": round(equity_dd, 2) if equity_dd is not None else None,
        "max_closed_dd_r": round(full["max_closed_dd"] / RISK_UNIT_USD, 4),
        "max_equity_dd_r": round(equity_dd / RISK_UNIT_USD, 4) if equity_dd is not None else None,
        "longest_losing_streak": losing_streak,
        "native_regime": regime,
        "overlap_rows": overlap_rows,
        "checks": checks,
        "passed": all(checks.values()),
    }


def render(payload: dict[str, Any]) -> str:
    full = payload["full"]
    equity_dd = payload["max_equity_dd"]
    equity_dd_r = payload["max_equity_dd_r"]
    equity_dd_display = f"{equity_dd:.2f} / {equity_dd_r:.2f}" if equity_dd is not None else "missing / missing"
    lines = [
        "# A1 XAU R2 Prior-D1-Low First-Retest Episode Audit",
        "",
        f"Generated UTC: `{payload['generated_at_utc']}`",
        f"Passed: `{payload['passed']}`",
        "",
        "## Full Standalone",
        "",
        "| Trades | WR% | W/L | PF | Net | Stress PF | Closed DD / R | Equity DD / R | Losing streak |",
        "| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
        f"| {full['signals']} | {full['wr']:.2f} | {full['wl'] or 0.0:.4f} | {full['pf'] or 0.0:.4f} | {full['net']:.2f} | {full['stress_030_pf'] or 0.0:.4f} | {full['max_closed_dd']:.2f} / {payload['max_closed_dd_r']:.2f} | {equity_dd_display} | {payload['longest_losing_streak']} |",
        "",
        "## Chronology and Episodes",
        "",
        "| Bucket | Trades | WR% | W/L | PF | Net |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in payload["partitions"] + payload["episodes"]:
        lines.append(
            f"| `{row['name']}` | {row['signals']} | {row['win_rate_pct']:.2f} | {row['avg_win_loss'] or 0.0:.4f} | {row['profit_factor'] or 0.0:.4f} | {row['net_usd']:.2f} |"
        )
    lines.extend(["", "## Control Overlap", "", "| Control | Overlap | Candidate | Share% |", "| --- | ---: | ---: | ---: |"])
    for row in payload["overlap_rows"]:
        lines.append(f"| `{row['control']}` | {row['overlap_trades']} | {row['candidate_trades']} | {row['overlap_pct']:.2f} |")
    lines.extend(["", "## Checks", ""])
    for key, value in payload["checks"].items():
        lines.append(f"- `{key}`: {value}")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit R2 PDL first-retest episodes, regime purity, DD, and overlap.")
    parser.add_argument("--normalized-csv", type=Path, default=NORMALIZED_CSV)
    parser.add_argument("--signal-csv", type=Path, required=True)
    parser.add_argument("--mt5-components-json", type=Path, default=MT5_COMPONENTS_JSON)
    parser.add_argument("--report-md", type=Path, default=REPORT_MD)
    parser.add_argument("--report-json", type=Path, default=REPORT_JSON)
    args = parser.parse_args()

    payload = build_audit(args.normalized_csv, args.signal_csv, args.mt5_components_json)
    args.report_json.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    args.report_md.write_text(render(payload), encoding="utf-8")
    print(json.dumps({"passed": payload["passed"], "report_md": str(args.report_md)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
