from __future__ import annotations

import csv
import json
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import pandas as pd


PHASE1_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PHASE1_ROOT.parents[1]
REPORTS_DIR = PHASE1_ROOT / "outputs" / "reports"
DOC_PATH = (
    PHASE1_ROOT
    / "docs"
    / "A1_XAU_CURRENT_FRONTIER_QUIET_DAY_2R_COMPANION_DIAGNOSTIC_PREREG_2026_07_05.md"
)
BASE_CSV = REPORTS_DIR / "A1_XAU_HYBRID_F67_H16_NO_F33_COMPOSITION_202207_202606_KEPT.csv"
LSR_CSV = REPORTS_DIR / "A1_XAU_M5_LIQUIDITY_SWEEP_RECLAIM_2R_DIAGNOSTIC_2026_07_05_BEST_EXAM_TRADES.csv"
HTF_CSV = REPORTS_DIR / "A1_XAU_M5_HTF_PULLBACK_RECLAIM_2R_DIAGNOSTIC_2026_07_05_BEST_EXAM_TRADES.csv"
OUTPUT_STEM = "A1_XAU_CURRENT_FRONTIER_QUIET_DAY_2R_COMPANION_DIAGNOSTIC_2026_07_05"

WINDOW_START = pd.Timestamp("2022-07-01T00:00:00Z")
WINDOW_END = pd.Timestamp("2025-06-30T23:59:59Z")
LAST12_START = pd.Timestamp("2024-07-01T00:00:00Z")
LAST12_END = pd.Timestamp("2025-06-30T23:59:59Z")


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO_ROOT)).replace("\\", "/")
    except ValueError:
        return str(path)


def market_days(start: date, end: date) -> list[str]:
    days: list[str] = []
    current = start
    while current <= end:
        if current.weekday() < 5:
            days.append(current.isoformat())
        current += timedelta(days=1)
    return days


MARKET_DAYS = market_days(WINDOW_START.date(), WINDOW_END.date())
LAST12_MARKET_DAYS = market_days(LAST12_START.date(), LAST12_END.date())


def parse_time(value: str) -> pd.Timestamp:
    ts = pd.to_datetime(value, utc=True)
    if isinstance(ts, pd.Timestamp):
        return ts
    raise ValueError(f"could not parse timestamp {value!r}")


def load_base() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with BASE_CSV.open(newline="", encoding="utf-8") as handle:
        for raw in csv.DictReader(handle):
            entry_time = parse_time(str(raw["entry_time"]))
            if not (WINDOW_START <= entry_time <= WINDOW_END):
                continue
            rows.append(
                {
                    "source": "base_f67_h16_no_f33",
                    "priority": 0,
                    "variant": raw.get("variant_name") or raw.get("source_id") or "base",
                    "entry_time": entry_time.isoformat(),
                    "entry_date": str(raw["entry_date"]),
                    "direction": raw.get("direction", ""),
                    "pnl_usd": float(raw.get("pnl_usd") or 0.0),
                    "origin_csv": rel(BASE_CSV),
                    "origin_row": raw.get("source_row", ""),
                }
            )
    return sorted(rows, key=lambda row: (row["entry_time"], row["priority"]))


def load_addon(path: Path, source: str, priority: int) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(newline="", encoding="utf-8") as handle:
        for index, raw in enumerate(csv.DictReader(handle), start=2):
            entry_time = parse_time(str(raw["entry_time_utc"]))
            if not (WINDOW_START <= entry_time <= WINDOW_END):
                continue
            rows.append(
                {
                    "source": source,
                    "priority": priority,
                    "variant": raw.get("variant") or source,
                    "entry_time": entry_time.isoformat(),
                    "entry_date": str(raw["entry_date"]),
                    "direction": raw.get("direction", ""),
                    "pnl_usd": float(raw.get("pnl_usd_001lot") or 0.0),
                    "origin_csv": rel(path),
                    "origin_row": index,
                }
            )
    return sorted(rows, key=lambda row: (row["entry_time"], row["priority"]))


def first_per_day(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    seen: set[str] = set()
    for row in sorted(rows, key=lambda item: item["entry_time"]):
        day = str(row["entry_date"])
        if day in seen:
            continue
        selected.append(row)
        seen.add(day)
    return selected


def quiet_only(base: list[dict[str, Any]], addon: list[dict[str, Any]], cadence: str) -> list[dict[str, Any]]:
    base_days = {str(row["entry_date"]) for row in base}
    missing_rows = [row for row in addon if row["entry_date"] not in base_days and row["entry_date"] in set(MARKET_DAYS)]
    if cadence == "first_per_missing_day":
        return first_per_day(missing_rows)
    if cadence == "all_on_missing_day":
        return missing_rows
    raise ValueError(cadence)


def dedupe(rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    kept: list[dict[str, Any]] = []
    dropped: list[dict[str, Any]] = []
    seen: dict[tuple[str, str], dict[str, Any]] = {}
    for row in sorted(rows, key=lambda item: (item["entry_time"], item["priority"])):
        key = (str(row["entry_time"]), str(row["direction"]))
        if key in seen:
            out = dict(row)
            out["drop_reason"] = "same_time_direction_lower_priority"
            out["duplicate_of"] = seen[key]["source"]
            dropped.append(out)
            continue
        seen[key] = row
        kept.append(row)
    return kept, dropped


def max_drawdown(values: list[float]) -> float:
    peak = 0.0
    equity = 0.0
    worst = 0.0
    for value in values:
        equity += value
        peak = max(peak, equity)
        worst = max(worst, peak - equity)
    return worst


def profit_factor(values: list[float]) -> float | None:
    wins = sum(value for value in values if value > 0)
    losses = -sum(value for value in values if value < 0)
    if losses <= 0:
        return None
    return wins / losses


def summary(rows: list[dict[str, Any]], market_day_list: list[str], cost_per_trade: float = 0.0) -> dict[str, Any]:
    values = [float(row["pnl_usd"]) - cost_per_trade for row in rows]
    wins = [value for value in values if value > 0]
    losses = [value for value in values if value < 0]
    market_day_set = set(market_day_list)
    active_days = {str(row["entry_date"]) for row in rows if row["entry_date"] in market_day_set}
    avg_win = sum(wins) / len(wins) if wins else 0.0
    avg_loss = -sum(losses) / len(losses) if losses else 0.0
    return {
        "signals": len(rows),
        "wins": len(wins),
        "losses": len(losses),
        "win_rate_pct": 100.0 * len(wins) / len(rows) if rows else 0.0,
        "avg_win": avg_win,
        "avg_loss": avg_loss,
        "avg_win_loss": avg_win / avg_loss if avg_loss else None,
        "profit_factor": profit_factor(values),
        "net_usd": sum(values),
        "max_dd_usd": max_drawdown(values),
        "active_weekdays": len(active_days),
        "active_weekday_pct": 100.0 * len(active_days) / len(market_day_list) if market_day_list else 0.0,
    }


def subset_last12(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for row in rows:
        ts = parse_time(str(row["entry_time"]))
        if LAST12_START <= ts <= LAST12_END:
            out.append(row)
    return out


def round_metrics(row: dict[str, Any]) -> dict[str, Any]:
    return {key: (round(value, 4) if isinstance(value, float) else value) for key, value in row.items()}


def decide(row: dict[str, Any]) -> str:
    wr = float(row.get("win_rate_pct") or 0.0)
    wl = float(row.get("avg_win_loss") or 0.0)
    active = float(row.get("active_weekday_pct") or 0.0)
    last_wr = float(row.get("last12_win_rate_pct") or 0.0)
    last_wl = float(row.get("last12_avg_win_loss") or 0.0)
    if wr >= 50.0 and wl >= 2.0 and active >= 90.0 and last_wr >= 48.0 and last_wl >= 1.85:
        return "EXACT_MT5_REPLAY_CANDIDATE_DIAGNOSTIC"
    if wr >= 50.0 and wl >= 2.0:
        return "CORE_SHAPE_ACTIVITY_GAP"
    if active >= 90.0 and wl >= 2.0:
        return "ACTIVITY_PAYOFF_WR_FAIL"
    return "REJECT_NO_OWNER_SHAPE"


def score(row: dict[str, Any]) -> float:
    return round(
        min(float(row.get("win_rate_pct") or 0.0) / 50.0, 1.1) * 350.0
        + min(float(row.get("avg_win_loss") or 0.0) / 2.0, 1.1) * 300.0
        + min(float(row.get("active_weekday_pct") or 0.0) / 90.0, 1.1) * 275.0
        + min(float(row.get("profit_factor") or 0.0) / 1.5, 1.1) * 75.0,
        4,
    )


def evaluate(name: str, rows: list[dict[str, Any]], dropped: list[dict[str, Any]], addon_rows: list[dict[str, Any]]) -> dict[str, Any]:
    full = summary(rows, MARKET_DAYS)
    last12 = summary(subset_last12(rows), LAST12_MARKET_DAYS)
    stress = summary(rows, MARKET_DAYS, cost_per_trade=0.30)
    out = {
        "name": name,
        **round_metrics(full),
        "addon_signals": len(addon_rows),
        "dropped_rows": len(dropped),
        "last12_win_rate_pct": round(last12["win_rate_pct"], 4),
        "last12_avg_win_loss": round(last12["avg_win_loss"] or 0.0, 4),
        "last12_active_weekday_pct": round(last12["active_weekday_pct"], 4),
        "stress_030_avg_win_loss": round(stress["avg_win_loss"] or 0.0, 4),
    }
    out["decision"] = decide(out)
    out["score"] = score(out)
    return out


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fields is None:
        keys: list[str] = []
        for row in rows:
            for key in row:
                if key not in keys:
                    keys.append(key)
        fields = keys
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    base = load_base()
    htf = load_addon(HTF_CSV, "htf_pullback_reclaim_2r_best", 1)
    lsr = load_addon(LSR_CSV, "liquidity_sweep_reclaim_2r_best", 2)

    candidates: list[tuple[str, list[dict[str, Any]]]] = [("base_only_common_window", [])]
    for cadence in ("first_per_missing_day", "all_on_missing_day"):
        htf_quiet = quiet_only(base, htf, cadence)
        lsr_quiet = quiet_only(base, lsr, cadence)
        candidates.extend(
            [
                (f"base_plus_htf_{cadence}", htf_quiet),
                (f"base_plus_lsr_{cadence}", lsr_quiet),
                (f"base_plus_htf_then_lsr_{cadence}", htf_quiet + lsr_quiet),
            ]
        )

    results: list[dict[str, Any]] = []
    kept_by_name: dict[str, list[dict[str, Any]]] = {}
    dropped_by_name: dict[str, list[dict[str, Any]]] = {}
    for name, addon_rows in candidates:
        kept, dropped = dedupe(base + addon_rows)
        kept_by_name[name] = kept
        dropped_by_name[name] = dropped
        results.append(evaluate(name, kept, dropped, addon_rows))

    results.sort(key=lambda row: float(row["score"]), reverse=True)
    best = results[0]
    verdict = "NO_QUIET_DAY_2R_COMPANION_BRIDGE"
    if best["decision"] == "EXACT_MT5_REPLAY_CANDIDATE_DIAGNOSTIC":
        verdict = "DIAGNOSTIC_EXACT_MT5_REPLAY_CANDIDATE_FOUND"

    csv_path = REPORTS_DIR / f"{OUTPUT_STEM}.csv"
    kept_path = REPORTS_DIR / f"{OUTPUT_STEM}_BEST_KEPT.csv"
    dropped_path = REPORTS_DIR / f"{OUTPUT_STEM}_BEST_DROPPED.csv"
    json_path = REPORTS_DIR / f"{OUTPUT_STEM}.json"
    md_path = REPORTS_DIR / f"{OUTPUT_STEM}.md"

    write_csv(csv_path, results)
    write_csv(kept_path, kept_by_name[str(best["name"])])
    write_csv(dropped_path, dropped_by_name[str(best["name"])])

    payload = {
        "status": verdict,
        "generated_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "prereg": rel(DOC_PATH),
        "common_window": [WINDOW_START.isoformat(), WINDOW_END.isoformat()],
        "base_csv": rel(BASE_CSV),
        "addon_csvs": [rel(HTF_CSV), rel(LSR_CSV)],
        "base_common_window": next(row for row in results if row["name"] == "base_only_common_window"),
        "best_result": best,
        "reports": {
            "md": rel(md_path),
            "json": rel(json_path),
            "csv": rel(csv_path),
            "best_kept_csv": rel(kept_path),
            "best_dropped_csv": rel(dropped_path),
        },
    }
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    lines = [
        "# A1 XAU Current Frontier Quiet-Day 2R Companion Diagnostic - 2026-07-05",
        "",
        f"Status: `{verdict}`",
        "",
        "Scope: offline diagnostic composition only. No MT5 terminal, chart, preset, order, position, or broker runtime was touched.",
        "",
        "## Best Result",
        "",
        "| Field | Value |",
        "|---|---:|",
        f"| Decision | `{best['decision']}` |",
        f"| Row | `{best['name']}` |",
        f"| Signals | {best['signals']} |",
        f"| Addon signals | {best['addon_signals']} |",
        f"| Win rate | {best['win_rate_pct']:.2f}% |",
        f"| Avg win/loss | {best['avg_win_loss']:.4f} |",
        f"| Active weekdays | {best['active_weekday_pct']:.2f}% |",
        f"| PF | {best['profit_factor']:.4f} |",
        f"| Net USD | {best['net_usd']:.2f} |",
        f"| Last12 WR/W-L/active | {best['last12_win_rate_pct']:.2f}% / {best['last12_avg_win_loss']:.4f} / {best['last12_active_weekday_pct']:.2f}% |",
        f"| Stress -0.30 W/L | {best['stress_030_avg_win_loss']:.4f} |",
        "",
        "## Rows",
        "",
        "| Rank | Decision | Row | Signals | Addon | WR | W/L | Active | PF | Net | Last12 WR/W-L/Active |",
        "|---:|---|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for index, row in enumerate(results, start=1):
        lines.append(
            "| {index} | `{decision}` | `{name}` | {signals} | {addon_signals} | {win_rate_pct:.2f} | {avg_win_loss:.4f} | {active_weekday_pct:.2f} | {profit_factor:.4f} | {net_usd:.2f} | {last12_win_rate_pct:.2f}/{last12_avg_win_loss:.4f}/{last12_active_weekday_pct:.2f} |".format(
                index=index,
                **row,
            )
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- This tests only base-missing days, using previously frozen diagnostic rows.",
            "- Add-on ledgers are not exact MT5 and cannot support headline claims.",
            f"- Verdict: `{verdict}`",
            "",
            "## Artifacts",
            "",
            f"- Prereg: `{rel(DOC_PATH)}`",
            f"- JSON: `{rel(json_path)}`",
            f"- CSV: `{rel(csv_path)}`",
            f"- Best kept CSV: `{rel(kept_path)}`",
            f"- Best dropped CSV: `{rel(dropped_path)}`",
            f"- Report: `{rel(md_path)}`",
            "",
        ]
    )
    md_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {md_path}", flush=True)


if __name__ == "__main__":
    main()
