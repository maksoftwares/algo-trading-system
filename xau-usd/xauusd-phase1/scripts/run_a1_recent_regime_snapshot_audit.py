from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import run_a1_xau_m5_momentum_backtest_variants as a1
from analyze_a1_owner_goal_step3_portfolio_composition import REPORTS_DIR, parse_dt, rel
from run_a1_h4_d1_geometry_v2_weekly_shape import sha256_file
from run_a1_regime_router_v1_exact import ROUTER_INPUTS


PHASE1_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_STEM = "A1_XAU_RECENT_REGIME_SNAPSHOT_AUDIT_20260708"
TAG = "OWNER_GOAL_RECENT_REGIME_SNAPSHOT_AUDIT_202601_202606"
FROM_DATE = "2026.01.01"
TO_DATE = "2026.06.30"
LAST3_START = date(2026, 4, 1)
LAST3_END = date(2026, 6, 30)
LAST6_START = date(2026, 1, 1)
LAST6_END = date(2026, 6, 30)

REGIME_ORDER = ["shock", "uptrend", "downtrend", "compression", "chop", "unknown"]


def build_variants() -> list[a1.Variant]:
    return [
        a1.Variant(
            name="recent_regime_snapshot_m5",
            label="Recent router regime snapshot, one row per completed M5 bar",
            run_id="BT_A1_XAU_RECENT_REGIME_SNAPSHOT_M5",
            tester_inputs={
                **ROUTER_INPUTS,
                "InpSignalMode": "0",
                "InpRegimeRouterMode": "0",
                "InpRegimeSnapshotLogEnabled": "true",
                "InpAllowDemoTrading": "false",
                "InpMinAtrAbsoluteForEntry": "0.00",
            },
        )
    ]


def week_start(value: date) -> date:
    return value - timedelta(days=value.weekday())


def month_key(value: date) -> str:
    return f"{value.year:04d}-{value.month:02d}"


def read_snapshots(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(newline="", encoding="utf-8-sig") as handle:
        for ordinal, row in enumerate(csv.DictReader(handle, delimiter="\t"), start=2):
            if row.get("stage") != "REGIME_SNAPSHOT":
                continue
            timestamp = parse_dt(row["timestamp_broker"])
            regime = str(row.get("reason") or "unknown").strip().lower()
            rows.append(
                {
                    "timestamp_broker": timestamp,
                    "date": timestamp.date(),
                    "hour": timestamp.hour,
                    "regime": regime,
                    "bid": float(row.get("bid") or 0.0),
                    "ask": float(row.get("ask") or 0.0),
                    "spread_points": int(float(row.get("spread_points") or 0.0)),
                    "signal_open": float(row.get("signal_open") or 0.0),
                    "signal_high": float(row.get("signal_high") or 0.0),
                    "signal_low": float(row.get("signal_low") or 0.0),
                    "signal_close": float(row.get("signal_close") or 0.0),
                    "atr": float(row.get("atr") or 0.0),
                    "body_fraction": float(row.get("body_fraction") or 0.0),
                    "close_location": float(row.get("close_location") or 0.0),
                    "source_row": ordinal,
                }
            )
    return rows


def dominant_regime(regimes: list[str]) -> tuple[str, float]:
    if not regimes:
        return "unknown", 0.0
    counts = Counter(regimes)
    regime, count = counts.most_common(1)[0]
    return regime, round(100.0 * count / len(regimes), 2)


def percent_rows(counter: Counter[str], total: int) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for regime in REGIME_ORDER:
        count = counter.get(regime, 0)
        output.append({"regime": regime, "bars": count, "bar_pct": round(100.0 * count / total, 2) if total else 0.0})
    for regime, count in sorted(counter.items()):
        if regime not in REGIME_ORDER:
            output.append({"regime": regime, "bars": count, "bar_pct": round(100.0 * count / total, 2) if total else 0.0})
    return output


def summarize_period(name: str, rows: list[dict[str, Any]], start: date, end: date) -> dict[str, Any]:
    selected = [row for row in rows if start <= row["date"] <= end]
    bar_counts = Counter(row["regime"] for row in selected)

    by_day: dict[date, list[str]] = defaultdict(list)
    by_week: dict[date, list[str]] = defaultdict(list)
    by_month: dict[str, list[str]] = defaultdict(list)
    by_hour: dict[int, list[str]] = defaultdict(list)
    for row in selected:
        by_day[row["date"]].append(row["regime"])
        by_week[week_start(row["date"])].append(row["regime"])
        by_month[month_key(row["date"])].append(row["regime"])
        by_hour[row["hour"]].append(row["regime"])

    day_rows = []
    day_counts: Counter[str] = Counter()
    for day, regimes in sorted(by_day.items()):
        regime, share = dominant_regime(regimes)
        day_counts[regime] += 1
        day_rows.append({"period": name, "date": day.isoformat(), "dominant_regime": regime, "dominant_share_pct": share, "bars": len(regimes)})

    week_rows = []
    for week, regimes in sorted(by_week.items()):
        regime, share = dominant_regime(regimes)
        week_rows.append({"period": name, "week_start": week.isoformat(), "dominant_regime": regime, "dominant_share_pct": share, "bars": len(regimes)})

    month_rows = []
    for month, regimes in sorted(by_month.items()):
        regime, share = dominant_regime(regimes)
        counts = Counter(regimes)
        month_rows.append(
            {
                "period": name,
                "month": month,
                "dominant_regime": regime,
                "dominant_share_pct": share,
                "bars": len(regimes),
                **{f"{item}_pct": round(100.0 * counts.get(item, 0) / len(regimes), 2) for item in REGIME_ORDER},
            }
        )

    hour_rows = []
    for hour, regimes in sorted(by_hour.items()):
        regime, share = dominant_regime(regimes)
        hour_rows.append({"period": name, "hour": hour, "dominant_regime": regime, "dominant_share_pct": share, "bars": len(regimes)})

    dominant_bar_regime, dominant_bar_share = dominant_regime([row["regime"] for row in selected])
    dominant_day_regime, dominant_day_share = dominant_regime([row["dominant_regime"] for row in day_rows])
    return {
        "name": name,
        "start": start.isoformat(),
        "end": end.isoformat(),
        "bars": len(selected),
        "active_days": len(by_day),
        "dominant_bar_regime": dominant_bar_regime,
        "dominant_bar_share_pct": dominant_bar_share,
        "dominant_day_regime": dominant_day_regime,
        "dominant_day_share_pct": dominant_day_share,
        "bar_distribution": percent_rows(bar_counts, len(selected)),
        "day_distribution": percent_rows(day_counts, len(day_rows)),
        "day_rows": day_rows,
        "week_rows": week_rows,
        "month_rows": month_rows,
        "hour_rows": hour_rows,
    }


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fieldnames: list[str] = []
    for row in rows:
        for key in row:
            if key not in fieldnames:
                fieldnames.append(key)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def next_direction(last3: dict[str, Any], last6: dict[str, Any]) -> tuple[str, str]:
    recent = last3["dominant_day_regime"]
    if recent == "compression":
        return (
            "R3_COMPRESSION_SPECIALIST_NEXT",
            "Recent market days are dominated by compression. Next test should be a compression breakout or failed-break/range specialist, not another R1 long.",
        )
    if recent == "chop":
        return (
            "R4_CHOP_SPECIALIST_NEXT",
            "Recent market days are dominated by chop. Next test should be a range-fade or failed-break specialist with strict cost and top-winner robustness.",
        )
    if recent == "downtrend":
        return (
            "R2_DOWNTREND_SPECIALIST_NEXT",
            "Recent market days are dominated by downtrend. Reopen short-specialist work only under strict R2; do not relax the router.",
        )
    if recent == "shock":
        return (
            "R0_SHOCK_NO_TRADE_OR_EVENT_SPECIALIST_NEXT",
            "Recent market days are shock-dominated. Keep ordinary specialists flat and only test an explicit event/shock playbook.",
        )
    if recent == "uptrend":
        return (
            "R1_UPTREND_REPAIR_NEXT",
            "Recent market days are still uptrend-dominated, so the issue is the R1 entries being too restrictive rather than a missing regime specialist.",
        )
    return (
        "MIXED_REGIME_ROUTER_AUDIT_NEXT",
        "No dominant recent regime is clear. First inspect day/week transitions before building another specialist.",
    )


def render(payload: dict[str, Any]) -> str:
    lines = [
        "# A1 XAU Recent Regime Snapshot Audit",
        "",
        f"Generated UTC: `{payload['generated_at_utc']}`",
        f"Status: `{payload['status']}`",
        "",
        "Scope: exact-MT5 snapshot run using the EA-side Router V1 classifier. Snapshot mode logs regime state and returns before signal/trade logic.",
        "",
        "## Summary",
        "",
        "| Window | Bars | Active days | Dominant by bars | Bar share% | Dominant by days | Day share% |",
        "| --- | ---: | ---: | --- | ---: | --- | ---: |",
    ]
    for item in payload["periods"]:
        lines.append(
            f"| `{item['name']}` | {item['bars']} | {item['active_days']} | `{item['dominant_bar_regime']}` | "
            f"{item['dominant_bar_share_pct']:.2f} | `{item['dominant_day_regime']}` | {item['dominant_day_share_pct']:.2f} |"
        )

    for item in payload["periods"]:
        lines.extend(["", f"## {item['name']} Bar Distribution", "", "| Regime | Bars | Bar % |", "| --- | ---: | ---: |"])
        for row in item["bar_distribution"]:
            lines.append(f"| `{row['regime']}` | {row['bars']} | {row['bar_pct']:.2f} |")
        lines.extend(["", f"## {item['name']} Day Distribution", "", "| Regime | Days | Day % |", "| --- | ---: | ---: |"])
        for row in item["day_distribution"]:
            lines.append(f"| `{row['regime']}` | {row['bars']} | {row['bar_pct']:.2f} |")

    lines.extend(["", "## Monthly Dominant Regime", "", "| Period | Month | Dominant | Share% | Uptrend% | Downtrend% | Compression% | Chop% | Shock% |", "| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |"])
    for item in payload["periods"]:
        for row in item["month_rows"]:
            lines.append(
                f"| `{item['name']}` | {row['month']} | `{row['dominant_regime']}` | {row['dominant_share_pct']:.2f} | "
                f"{row['uptrend_pct']:.2f} | {row['downtrend_pct']:.2f} | {row['compression_pct']:.2f} | "
                f"{row['chop_pct']:.2f} | {row['shock_pct']:.2f} |"
            )

    lines.extend(["", "## Next Direction", "", f"Decision: `{payload['status']}`", "", payload["interpretation"], "", "## Artifacts", ""])
    for key, path in payload["outputs"].items():
        lines.append(f"- {key}: `{path}`")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run exact-MT5 recent regime snapshot audit.")
    parser.add_argument("--variant-timeout-seconds", type=int, default=900)
    args = parser.parse_args()

    variants = build_variants()
    a1.VARIANTS = variants
    report_md = REPORTS_DIR / f"{OUTPUT_STEM}.md"
    report_json = REPORTS_DIR / f"{OUTPUT_STEM}.json"
    snapshots_csv = REPORTS_DIR / f"{OUTPUT_STEM}_SNAPSHOTS.csv"
    period_csv = REPORTS_DIR / f"{OUTPUT_STEM}_PERIOD_SUMMARY.csv"
    days_csv = REPORTS_DIR / f"{OUTPUT_STEM}_DAYS.csv"
    weeks_csv = REPORTS_DIR / f"{OUTPUT_STEM}_WEEKS.csv"
    months_csv = REPORTS_DIR / f"{OUTPUT_STEM}_MONTHS.csv"
    hours_csv = REPORTS_DIR / f"{OUTPUT_STEM}_HOURS.csv"
    mt5_report_md = REPORTS_DIR / f"{OUTPUT_STEM}_MT5.md"
    mt5_report_json = REPORTS_DIR / f"{OUTPUT_STEM}_MT5.json"

    mt5_payload = a1.run_variants(
        from_date=FROM_DATE,
        to_date=TO_DATE,
        tag=a1.safe_name(TAG),
        report_md=mt5_report_md,
        report_json=mt5_report_json,
        variant_timeout_seconds=args.variant_timeout_seconds,
        deposit="1000",
        currency="USD",
    )
    result = mt5_payload["variants"][0]
    snapshots = read_snapshots(Path(result["signal_csv"]))

    last6 = summarize_period("last_6_months_2026_01_01_to_2026_06_30", snapshots, LAST6_START, LAST6_END)
    last3 = summarize_period("last_3_months_2026_04_01_to_2026_06_30", snapshots, LAST3_START, LAST3_END)
    status, interpretation = next_direction(last3, last6)

    write_csv(snapshots_csv, snapshots)
    write_csv(period_csv, [
        {
            "name": item["name"],
            "start": item["start"],
            "end": item["end"],
            "bars": item["bars"],
            "active_days": item["active_days"],
            "dominant_bar_regime": item["dominant_bar_regime"],
            "dominant_bar_share_pct": item["dominant_bar_share_pct"],
            "dominant_day_regime": item["dominant_day_regime"],
            "dominant_day_share_pct": item["dominant_day_share_pct"],
        }
        for item in [last6, last3]
    ])
    write_csv(days_csv, last6["day_rows"] + last3["day_rows"])
    write_csv(weeks_csv, last6["week_rows"] + last3["week_rows"])
    write_csv(months_csv, last6["month_rows"] + last3["month_rows"])
    write_csv(hours_csv, last6["hour_rows"] + last3["hour_rows"])

    outputs = {
        "report_md": rel(report_md),
        "report_json": rel(report_json),
        "snapshots_csv": rel(snapshots_csv),
        "period_csv": rel(period_csv),
        "days_csv": rel(days_csv),
        "weeks_csv": rel(weeks_csv),
        "months_csv": rel(months_csv),
        "hours_csv": rel(hours_csv),
        "mt5_report_md": rel(mt5_report_md),
        "mt5_report_json": rel(mt5_report_json),
        "mt5_signal_csv": result["signal_csv"],
    }
    payload = {
        "status": status,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "mt5_scope": mt5_payload["scope"],
        "compile_log": mt5_payload["compile_log"],
        "mt5_result": result,
        "mt5_signal_sha256": sha256_file(Path(result["signal_csv"])),
        "periods": [last6, last3],
        "interpretation": interpretation,
        "outputs": outputs,
    }
    report_json.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    report_md.write_text(render(payload), encoding="utf-8")
    print(
        json.dumps(
            {
                "status": status,
                "periods": [
                    {
                        "name": item["name"],
                        "bars": item["bars"],
                        "active_days": item["active_days"],
                        "dominant_bar_regime": item["dominant_bar_regime"],
                        "dominant_bar_share_pct": item["dominant_bar_share_pct"],
                        "dominant_day_regime": item["dominant_day_regime"],
                        "dominant_day_share_pct": item["dominant_day_share_pct"],
                    }
                    for item in [last6, last3]
                ],
                "report": str(report_md),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
