from __future__ import annotations

import csv
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from statistics import median
from typing import Any


PHASE1_ROOT = Path(__file__).resolve().parents[1]
REPORTS = PHASE1_ROOT / "outputs" / "reports"

V1_COMPONENTS = REPORTS / "A1_XAU_R2_CONTINUATION_SHORT_V1_EXACT_20260709_MT5_COMPONENTS.json"
V4_COMPONENTS = REPORTS / "A1_XAU_R2_CONTINUATION_SHORT_V4_VOLATILITY_GATE_EXACT_20260709_MT5_COMPONENTS.json"
REPORT_MD = REPORTS / "A1_XAU_R2_V4_ATR_FLOOR_AUDIT_20260709.md"
REPORT_JSON = REPORTS / "A1_XAU_R2_V4_ATR_FLOOR_AUDIT_20260709.json"

THRESHOLDS = (4.50, 5.00)


def parse_time(value: str) -> datetime:
    return datetime.strptime(value, "%Y.%m.%d %H:%M:%S")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def variant_by_name(payload: dict[str, Any], name: str) -> dict[str, Any]:
    for variant in payload["variants"]:
        if variant["name"] == name:
            return variant
    raise KeyError(name)


def read_tab_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def pct_rank(values: list[float], threshold: float) -> float:
    if not values:
        return 0.0
    return 100.0 * sum(1 for value in values if value <= threshold) / len(values)


def percentile(values: list[float], q: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = round((len(ordered) - 1) * q)
    return ordered[index]


def stats(rows: list[dict[str, Any]]) -> dict[str, Any]:
    trades = len(rows)
    wins = sum(1 for row in rows if row["pnl"] > 0)
    losses = sum(1 for row in rows if row["pnl"] < 0)
    gross_profit = sum(row["pnl"] for row in rows if row["pnl"] > 0)
    gross_loss = -sum(row["pnl"] for row in rows if row["pnl"] < 0)
    avg_win = gross_profit / wins if wins else 0.0
    avg_loss = gross_loss / losses if losses else 0.0
    return {
        "trades": trades,
        "wins": wins,
        "losses": losses,
        "wr": 100.0 * wins / trades if trades else 0.0,
        "wl": avg_win / avg_loss if avg_loss else 0.0,
        "pf": gross_profit / gross_loss if gross_loss else 0.0,
        "net": sum(row["pnl"] for row in rows),
    }


def load_v1_trade_features() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    v1 = variant_by_name(read_json(V1_COMPONENTS), "r2_impulse_retest_body45")
    signal_rows = read_tab_csv(Path(v1["signal_csv"]))
    order_rows = read_tab_csv(Path(v1["order_csv"]))
    trade_rows = read_csv(Path(v1["trade_csv"]))

    would_by_time: dict[datetime, dict[str, str]] = {}
    would_rows: list[dict[str, Any]] = []
    for row in signal_rows:
        if row.get("stage") != "WOULD_SIGNAL":
            continue
        timestamp = parse_time(row["timestamp_broker"])
        atr = float(row["atr"])
        item = {
            "time": timestamp,
            "year": timestamp.year,
            "month": timestamp.strftime("%Y-%m"),
            "atr": atr,
            "break_distance_atr": float(row["break_distance_atr"]),
            "body_fraction": float(row["body_fraction"]),
            "close_location": float(row["close_location"]),
        }
        would_rows.append(item)
        would_by_time[timestamp] = row

    order_by_time = {
        parse_time(row["timestamp_broker"]): row
        for row in order_rows
        if row.get("action") == "ORDER_SEND_OK"
    }

    trade_features: list[dict[str, Any]] = []
    for row in trade_rows:
        timestamp = parse_time(row["entry_time"])
        signal = would_by_time.get(timestamp)
        order = order_by_time.get(timestamp)
        if signal is None or order is None:
            continue
        trade_features.append(
            {
                "time": timestamp,
                "year": timestamp.year,
                "month": timestamp.strftime("%Y-%m"),
                "pnl": float(row["profit_aed"]),
                "atr": float(signal["atr"]),
                "break_distance_atr": float(signal["break_distance_atr"]),
                "body_fraction": float(signal["body_fraction"]),
                "close_location": float(signal["close_location"]),
                "stop_points": float(order["stop_points"]),
            }
        )
    return would_rows, trade_features


def atr_floor_blocks() -> list[dict[str, Any]]:
    payload = read_json(V4_COMPONENTS)
    rows: list[dict[str, Any]] = []
    for variant in payload["variants"]:
        signal_rows = read_tab_csv(Path(variant["signal_csv"]))
        by_month: dict[str, int] = defaultdict(int)
        block_count = 0
        for row in signal_rows:
            if row.get("stage") == "NO_SIGNAL" and row.get("reason") == "atr_below_entry_floor":
                block_count += 1
                by_month[parse_time(row["timestamp_broker"]).strftime("%Y-%m")] += 1
        rows.append(
            {
                "variant": variant["name"],
                "signal_rows": len(signal_rows),
                "atr_floor_blocks": block_count,
                "block_pct": 100.0 * block_count / len(signal_rows) if signal_rows else 0.0,
                "april_blocks": by_month.get("2026-04", 0),
                "may_blocks": by_month.get("2026-05", 0),
                "june_blocks": by_month.get("2026-06", 0),
                "monthly_blocks": dict(sorted(by_month.items())),
            }
        )
    return rows


def threshold_trade_impact(trades: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for threshold in THRESHOLDS:
        kept = [row for row in trades if row["atr"] >= threshold]
        removed = [row for row in trades if row["atr"] < threshold]
        may_kept = [row for row in kept if row["month"] == "2026-05"]
        may_removed = [row for row in removed if row["month"] == "2026-05"]
        june_kept = [row for row in kept if row["month"] == "2026-06"]
        june_removed = [row for row in removed if row["month"] == "2026-06"]
        output.append(
            {
                "threshold": threshold,
                "kept": stats(kept),
                "removed": stats(removed),
                "may_kept": stats(may_kept),
                "may_removed": stats(may_removed),
                "june_kept": stats(june_kept),
                "june_removed": stats(june_removed),
            }
        )
    return output


def atr_distribution(rows: list[dict[str, Any]], field: str = "atr") -> list[dict[str, Any]]:
    by_year: dict[int, list[float]] = defaultdict(list)
    for row in rows:
        by_year[row["year"]].append(row[field])

    output: list[dict[str, Any]] = []
    for year, values in sorted(by_year.items()):
        output.append(
            {
                "year": year,
                "count": len(values),
                "median": median(values) if values else 0.0,
                "p25": percentile(values, 0.25),
                "p75": percentile(values, 0.75),
                "pct_lte_4p50": pct_rank(values, 4.50),
                "pct_lte_5p00": pct_rank(values, 5.00),
            }
        )
    return output


def monthly_v1_signal_floor_counts(would_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    months = sorted({row["month"] for row in would_rows})
    output: list[dict[str, Any]] = []
    for month in months:
        values = [row["atr"] for row in would_rows if row["month"] == month]
        if not values:
            continue
        output.append(
            {
                "month": month,
                "would_signals": len(values),
                "below_4p50": sum(1 for value in values if value < 4.50),
                "below_5p00": sum(1 for value in values if value < 5.00),
                "median_atr": median(values),
            }
        )
    return output


def fmt_money(value: float) -> str:
    return f"{value:,.2f}"


def render(payload: dict[str, Any]) -> str:
    lines = [
        "# A1 XAU R2 V4 ATR Floor Audit",
        "",
        "Date: 2026-07-09",
        "",
        "Scope: report-only audit from existing exact-MT5 V1/V4 signal, order, and trade CSVs. No new MT5 test and no strategy change.",
        "",
        "## Verdict",
        "",
        "The ATR floor did what V4 intended: it blocked a very large set of low-ATR bars and narrowed R2 continuation to high-participation downside conditions. The tradeoff is severe concentration: V4 quality improved, but standalone evidence is mostly recent 2026 exposure.",
        "",
        "## ATR Floor Block Counts",
        "",
        "| Variant | Signal rows | ATR-floor blocks | Block % | Apr 2026 | May 2026 | Jun 2026 |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in payload["atr_floor_blocks"]:
        lines.append(
            f"| `{row['variant']}` | {row['signal_rows']} | {row['atr_floor_blocks']} | "
            f"{row['block_pct']:.2f}% | {row['april_blocks']} | {row['may_blocks']} | {row['june_blocks']} |"
        )

    lines.extend(
        [
            "",
            "## V1 Trade Impact By ATR Floor",
            "",
            "This table is a V1 executed-trade postfilter audit, not a replacement for the exact V4 run. Exact V4 can differ slightly because skipped low-ATR trades can change one-position/open-slot sequencing.",
            "",
            "| ATR floor | Kept trades | Kept WR | Kept PF | Kept net | Removed trades | Removed WR | Removed PF | Removed net |",
            "| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for row in payload["threshold_trade_impact"]:
        kept = row["kept"]
        removed = row["removed"]
        lines.append(
            f"| {row['threshold']:.2f} | {kept['trades']} | {kept['wr']:.2f}% | {kept['pf']:.4f} | "
            f"{fmt_money(kept['net'])} | {removed['trades']} | {removed['wr']:.2f}% | "
            f"{removed['pf']:.4f} | {fmt_money(removed['net'])} |"
        )

    lines.extend(
        [
            "",
            "## May/June Analog On V1 Trades",
            "",
            "| ATR floor | May kept net | May removed net | June kept net | June removed net |",
            "| ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for row in payload["threshold_trade_impact"]:
        lines.append(
            f"| {row['threshold']:.2f} | {fmt_money(row['may_kept']['net'])} | "
            f"{fmt_money(row['may_removed']['net'])} | {fmt_money(row['june_kept']['net'])} | "
            f"{fmt_money(row['june_removed']['net'])} |"
        )

    lines.extend(
        [
            "",
            "## V1 WOULD_SIGNAL ATR Distribution By Year",
            "",
            "| Year | Candidates | P25 ATR | Median ATR | P75 ATR | <=4.50 pct | <=5.00 pct |",
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for row in payload["v1_would_signal_atr_by_year"]:
        lines.append(
            f"| {row['year']} | {row['count']} | {row['p25']:.2f} | {row['median']:.2f} | "
            f"{row['p75']:.2f} | {row['pct_lte_4p50']:.2f}% | {row['pct_lte_5p00']:.2f}% |"
        )

    lines.extend(
        [
            "",
            "## V1 Executed Trade ATR Distribution By Year",
            "",
            "| Year | Trades | P25 ATR | Median ATR | P75 ATR | <=4.50 pct | <=5.00 pct |",
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for row in payload["v1_trade_atr_by_year"]:
        lines.append(
            f"| {row['year']} | {row['count']} | {row['p25']:.2f} | {row['median']:.2f} | "
            f"{row['p75']:.2f} | {row['pct_lte_4p50']:.2f}% | {row['pct_lte_5p00']:.2f}% |"
        )

    lines.extend(
        [
            "",
            "## Key Interpretation",
            "",
            "- V4's ATR floor is causally clean as a pre-entry participation gate.",
            "- The audit supports the reviewer view: ATR45/ATR50 are plausible diagnostics, not final production thresholds.",
            "- The floor removes many V1 trades and should not be tuned further inside R2.",
            "- R2 should now remain frozen as V1 raw control plus V4 quality shadow candidates.",
            "- New market coverage should come from a separate chop / failed-breakdown specialist, not another R2 filter.",
            "",
            "## Artifacts",
            "",
            f"- JSON payload: `{REPORT_JSON.relative_to(PHASE1_ROOT.parents[1])}`",
            f"- V1 component source: `{V1_COMPONENTS.relative_to(PHASE1_ROOT.parents[1])}`",
            f"- V4 component source: `{V4_COMPONENTS.relative_to(PHASE1_ROOT.parents[1])}`",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    would_rows, trade_features = load_v1_trade_features()
    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "scope": "report-only audit from existing exact-MT5 artifacts; no new MT5 run",
        "atr_floor_blocks": atr_floor_blocks(),
        "threshold_trade_impact": threshold_trade_impact(trade_features),
        "v1_would_signal_atr_by_year": atr_distribution(would_rows),
        "v1_trade_atr_by_year": atr_distribution(trade_features),
        "v1_monthly_signal_floor_counts": monthly_v1_signal_floor_counts(would_rows),
    }
    REPORT_JSON.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    REPORT_MD.write_text(render(payload), encoding="utf-8")
    print(json.dumps({"report_md": str(REPORT_MD), "report_json": str(REPORT_JSON)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
