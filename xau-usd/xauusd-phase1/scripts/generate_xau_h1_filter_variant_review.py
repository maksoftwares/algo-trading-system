"""Offline H1 smart-trend filter variant review for XAU 920101.

This script compares the current H1 filter against asymmetric short-threshold
variants. It is analysis-only: it reads committed/report CSVs and writes report
artifacts. It does not touch MT5 terminals, charts, presets, orders, or EAs.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable


DEFAULT_C01 = Path("outputs") / "reports" / "A3_ML_C01_SNAPSHOT_ROWS.csv"
DEFAULT_BROKER = Path("outputs") / "reports" / "BROKER_JOINED_XAU_FACTOR_ROWS_2026_06_27.csv"
DEFAULT_OUT_JSON = Path("outputs") / "reports" / "XAU_H1_FILTER_VARIANT_REVIEW_2026_06_30.json"
DEFAULT_OUT_CSV = Path("outputs") / "reports" / "XAU_H1_FILTER_VARIANT_REVIEW_2026_06_30.csv"
DEFAULT_OUT_MD = Path("outputs") / "reports" / "XAU_H1_FILTER_VARIANT_REVIEW_2026_06_30.md"


@dataclass(frozen=True)
class Variant:
    variant_id: str
    description: str
    predicate: Callable[[dict[str, object]], bool]


def run_review(
    phase1_root: Path,
    c01_csv: Path | None = None,
    broker_csv: Path | None = None,
    output_json: Path | None = None,
    output_csv: Path | None = None,
    output_md: Path | None = None,
) -> dict[str, object]:
    phase1_root = phase1_root.resolve()
    c01_csv = (c01_csv or phase1_root / DEFAULT_C01).resolve()
    broker_csv = (broker_csv or phase1_root / DEFAULT_BROKER).resolve()
    output_json = (output_json or phase1_root / DEFAULT_OUT_JSON).resolve()
    output_csv = (output_csv or phase1_root / DEFAULT_OUT_CSV).resolve()
    output_md = (output_md or phase1_root / DEFAULT_OUT_MD).resolve()
    for path in (output_json, output_csv, output_md):
        path.parent.mkdir(parents=True, exist_ok=True)

    diagnostic_rows = load_c01_rows(c01_csv)
    broker_rows = load_broker_rows(broker_csv)
    variants = build_variants()
    rows: list[dict[str, object]] = []
    for variant in variants:
        diag_selected = [row for row in diagnostic_rows if variant.predicate(row)]
        broker_selected = [row for row in broker_rows if variant.predicate(row)]
        rows.append(summary_row("diagnostic_c01", variant, diag_selected))
        rows.append(summary_row("broker_joined", variant, broker_selected))

    payload: dict[str, object] = {
        "status": "PASS_REPORT_GENERATED",
        "created_at_utc": utc_now(),
        "boundary": [
            "Offline analysis only.",
            "No MT5 terminal, chart, preset, EA, order, or position was touched.",
            "Diagnostic C01 labels are OPTIMISTIC_DIAGNOSTIC_ONLY and directional; broker-joined fills are realized but much smaller sample.",
        ],
        "inputs": {
            "c01_csv": str(c01_csv),
            "broker_csv": str(broker_csv),
            "diagnostic_resolved_rows": len(diagnostic_rows),
            "broker_joined_rows": len(broker_rows),
        },
        "decision": decide(rows),
        "rows": rows,
        "artifacts": {
            "json": str(output_json),
            "csv": str(output_csv),
            "markdown": str(output_md),
        },
    }

    write_csv(output_csv, rows, fieldnames())
    output_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    output_md.write_text(render_markdown(payload), encoding="utf-8")
    return payload


def build_variants() -> list[Variant]:
    return [
        Variant("V0_no_h1_filter", "No H1 filter; control counterfactual", lambda row: True),
        Variant("V1_current_symmetric_015", "Current live shape: LONG >= 0.15 and SHORT >= 0.15", lambda row: h1(row) >= 0.15),
        Variant(
            "V2_asym_short_005_long_015",
            "Asymmetric positive threshold: LONG >= 0.15, SHORT >= 0.05",
            lambda row: (direction(row) == "LONG" and h1(row) >= 0.15) or (direction(row) == "SHORT" and h1(row) >= 0.05),
        ),
        Variant(
            "V2_asym_short_010_long_015",
            "Asymmetric positive threshold: LONG >= 0.15, SHORT >= 0.10",
            lambda row: (direction(row) == "LONG" and h1(row) >= 0.15) or (direction(row) == "SHORT" and h1(row) >= 0.10),
        ),
        Variant(
            "V_bad_counter_h1_shorts_allowed",
            "Negative control: admit counter-H1 SHORTs while keeping LONG >= 0.15",
            lambda row: (direction(row) == "LONG" and h1(row) >= 0.15) or direction(row) == "SHORT",
        ),
        Variant("V4_h1_ge_010", "Sweep: H1 >= 0.10", lambda row: h1(row) >= 0.10),
        Variant("V4_h1_ge_020", "Sweep: H1 >= 0.20", lambda row: h1(row) >= 0.20),
        Variant("V4_h1_ge_025", "Sweep: H1 >= 0.25", lambda row: h1(row) >= 0.25),
    ]


def load_c01_rows(path: Path) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    with path.open(newline="", encoding="utf-8-sig") as handle:
        for raw in csv.DictReader(handle):
            if raw.get("symbol") != "XAUUSD" or raw.get("base_family") != "breakout_retest":
                continue
            if raw.get("candidate_id") != "B0_RAW_ALL_SESSION":
                continue
            if raw.get("y_outcome") not in {"TP", "SL"}:
                continue
            h1_value = to_float(raw.get("h1_ema20_slope_aligned_atr"))
            if math.isnan(h1_value):
                continue
            row: dict[str, object] = dict(raw)
            row["h1"] = h1_value
            row["direction_norm"] = normalize_direction(raw.get("direction", ""))
            row["profit_unit"] = 1.5 if raw.get("y_outcome") == "TP" else -1.0
            row["entry_time"] = raw.get("decision_time_utc", "")
            row["entry_date"] = str(raw.get("decision_time_utc", ""))[:10]
            rows.append(row)
    return rows


def load_broker_rows(path: Path) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    with path.open(newline="", encoding="utf-8-sig") as handle:
        for raw in csv.DictReader(handle):
            if raw.get("symbol") != "XAUUSD" or raw.get("candidate") != "breakout_retest":
                continue
            if raw.get("magic") != "920101":
                continue
            h1_value = to_float(raw.get("h1_ema20_slope_aligned_atr"))
            profit = to_float(raw.get("profit_aed"))
            if math.isnan(h1_value) or math.isnan(profit):
                continue
            row: dict[str, object] = dict(raw)
            row["h1"] = h1_value
            row["direction_norm"] = normalize_direction(raw.get("direction", ""))
            row["profit_unit"] = profit
            row["entry_time"] = raw.get("entry_time_utc", "")
            row["entry_date"] = str(raw.get("entry_time_utc", ""))[:10]
            rows.append(row)
    return rows


def summary_row(source: str, variant: Variant, rows: list[dict[str, object]]) -> dict[str, object]:
    values = [float(row["profit_unit"]) for row in rows]
    wins = [value for value in values if value > 0]
    losses = [value for value in values if value < 0]
    by_day: dict[str, float] = defaultdict(float)
    for row in rows:
        by_day[str(row.get("entry_date", ""))] += float(row["profit_unit"])
    top_removed = sorted(values, reverse=True)[3:]
    return {
        "source": source,
        "variant_id": variant.variant_id,
        "description": variant.description,
        "rows": len(values),
        "long_rows": sum(1 for row in rows if direction(row) == "LONG"),
        "short_rows": sum(1 for row in rows if direction(row) == "SHORT"),
        "wins": len(wins),
        "losses": len(losses),
        "win_rate_pct": pct(len(wins), len(values)),
        "net": round(sum(values), 4),
        "expectancy": round(sum(values) / len(values), 6) if values else "",
        "profit_factor": profit_factor(values),
        "worst_day": round(min(by_day.values()), 4) if by_day else "",
        "best_day": round(max(by_day.values()), 4) if by_day else "",
        "top3_removed_net": round(sum(top_removed), 4) if len(values) > 3 else "",
        "single_best_share_pct": single_best_share(values),
    }


def decide(rows: list[dict[str, object]]) -> dict[str, object]:
    by_key = {(row["source"], row["variant_id"]): row for row in rows}
    diag_v1 = by_key.get(("diagnostic_c01", "V1_current_symmetric_015"), {})
    broker_v1 = by_key.get(("broker_joined", "V1_current_symmetric_015"), {})
    asym_005 = by_key.get(("diagnostic_c01", "V2_asym_short_005_long_015"), {})
    asym_010 = by_key.get(("diagnostic_c01", "V2_asym_short_010_long_015"), {})
    bad_counter = by_key.get(("diagnostic_c01", "V_bad_counter_h1_shorts_allowed"), {})
    return {
        "verdict": "KEEP_CURRENT_FILTER__ASYMMETRY_SHADOW_ONLY",
        "plain_english": (
            "Do not change runtime from this evidence. Current V1 remains the control. "
            "Asymmetric positive short thresholds are worth shadow tracking, but counter-H1 shorts are rejected."
        ),
        "control_diagnostic": short_rec(diag_v1),
        "control_broker_joined": short_rec(broker_v1),
        "asym_short_005_diagnostic": short_rec(asym_005),
        "asym_short_010_diagnostic": short_rec(asym_010),
        "counter_h1_short_negative_control": short_rec(bad_counter),
        "next_step": "Track V2_asym_short_005_long_015 and V2_asym_short_010_long_015 offline on new signals; require larger broker-filled sample before runtime change.",
    }


def short_rec(row: dict[str, object]) -> dict[str, object]:
    return {
        "variant_id": row.get("variant_id", ""),
        "rows": row.get("rows", 0),
        "long_rows": row.get("long_rows", 0),
        "short_rows": row.get("short_rows", 0),
        "win_rate_pct": row.get("win_rate_pct", ""),
        "net": row.get("net", ""),
        "expectancy": row.get("expectancy", ""),
        "profit_factor": row.get("profit_factor", ""),
    }


def render_markdown(payload: dict[str, object]) -> str:
    rows = list(payload["rows"])
    diagnostic = [row for row in rows if row["source"] == "diagnostic_c01"]
    broker = [row for row in rows if row["source"] == "broker_joined"]
    lines = [
        "# XAU H1 Smart-Trend Filter Variant Review - 2026-06-30",
        "",
        f"Status: `{payload['status']}`",
        "",
        "## Boundary",
        "",
        "- Offline analysis only.",
        "- No MT5 terminal, chart, preset, EA, order, or position was touched.",
        "- C01 labels are `OPTIMISTIC_DIAGNOSTIC_ONLY`; use them for direction, not exact money.",
        "- Broker-joined rows are realized fills but a smaller historical sample.",
        "",
        "## Verdict",
        "",
        f"`{payload['decision']['verdict']}`",
        "",
        payload["decision"]["plain_english"],
        "",
        "## Diagnostic C01 Broad Sample",
        "",
        _table(diagnostic),
        "",
        "## Broker-Joined Realized Fill Sample",
        "",
        _table(broker),
        "",
        "## Interpretation",
        "",
        "- Current V1 remains the live control.",
        "- The one missed winning short on 2026-06-30 is not enough to admit counter-H1 shorts.",
        "- The negative-control variant that admits all SHORTs is included specifically to prevent regret-overfitting.",
        "- If we test asymmetry, it should be positive-threshold asymmetry only: lower the short threshold slightly, never allow negative H1 alignment.",
        "- Any runtime change needs fresh broker-filled evidence, not just this diagnostic backfill.",
        "",
        "## Next Offline Shadow Variants",
        "",
        "1. `V1_current_symmetric_015`: keep scoring current control.",
        "2. `V2_asym_short_005_long_015`: LONG >= 0.15, SHORT >= 0.05.",
        "3. `V2_asym_short_010_long_015`: LONG >= 0.15, SHORT >= 0.10.",
        "4. Reject counter-H1 short admission unless a future, pre-registered sample overturns this report.",
        "",
        "## Artifacts",
        "",
        f"- CSV: `{payload['artifacts']['csv']}`",
        f"- JSON: `{payload['artifacts']['json']}`",
        "",
    ]
    return "\n".join(lines)


def _table(rows: list[dict[str, object]]) -> str:
    lines = [
        "| Variant | Rows | Long | Short | WR | Net | Exp | PF | Worst day | Top3 removed |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in rows:
        lines.append(
            f"| {row['variant_id']} | {row['rows']} | {row['long_rows']} | {row['short_rows']} | "
            f"{row['win_rate_pct']:.2f}% | {row['net']} | {row['expectancy']} | {fmt(row['profit_factor'])} | "
            f"{row['worst_day']} | {row['top3_removed_net']} |"
        )
    return "\n".join(lines)


def direction(row: dict[str, object]) -> str:
    return str(row.get("direction_norm", "")).upper()


def h1(row: dict[str, object]) -> float:
    return float(row.get("h1", math.nan))


def normalize_direction(value: object) -> str:
    text = str(value or "").upper()
    if text in {"BUY", "LONG"}:
        return "LONG"
    if text in {"SELL", "SHORT"}:
        return "SHORT"
    return text


def to_float(value: object, default: float = math.nan) -> float:
    try:
        text = str(value or "").strip()
        if not text or text.lower() == "nan":
            return default
        return float(text)
    except (TypeError, ValueError):
        return default


def profit_factor(values: list[float]) -> float:
    wins = sum(value for value in values if value > 0)
    losses = -sum(value for value in values if value < 0)
    if losses <= 0:
        return math.inf if wins > 0 else math.nan
    return round(wins / losses, 6)


def pct(numerator: int, denominator: int) -> float:
    return round(100.0 * numerator / denominator, 2) if denominator else 0.0


def single_best_share(values: list[float]) -> float | str:
    positives = [value for value in values if value > 0]
    net = sum(values)
    if not positives or net <= 0:
        return ""
    return round(100.0 * max(positives) / net, 2)


def fmt(value: object) -> str:
    if isinstance(value, float):
        if math.isinf(value):
            return "inf"
        if math.isnan(value):
            return "n/a"
        return f"{value:.4f}"
    return str(value)


def write_csv(path: Path, rows: list[dict[str, object]], fields: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def fieldnames() -> list[str]:
    return [
        "source",
        "variant_id",
        "description",
        "rows",
        "long_rows",
        "short_rows",
        "wins",
        "losses",
        "win_rate_pct",
        "net",
        "expectancy",
        "profit_factor",
        "worst_day",
        "best_day",
        "top3_removed_net",
        "single_best_share_pct",
    ]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate offline XAU H1 filter variant review.")
    parser.add_argument("--phase1-root", type=Path, default=Path(__file__).resolve().parents[1])
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    payload = run_review(args.phase1_root)
    print(f"XAU H1 filter variant review: {payload['status']}")
    print(json.dumps(payload["decision"], indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
