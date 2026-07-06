from __future__ import annotations

import csv
import itertools
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from analyze_a1_best_of_each_hybrid_frontier import build_components
from analyze_a1_owner_goal_step3_portfolio_composition import (
    MARKET_DAYS,
    REPORTS_DIR,
    dedupe_signals,
    summary_metrics,
)


PHASE1_ROOT = Path(__file__).resolve().parents[1]
PREREG = PHASE1_ROOT / "docs" / "A1_XAU_HYBRID_CATEGORICAL_GATE_DIAGNOSTIC_PREREG_2026_07_05.md"
OUTPUT_STEM = "A1_XAU_HYBRID_CATEGORICAL_GATE_DIAGNOSTIC_2026_07_05"
MIN_SIGNALS = 3000

BASELINES = {
    "broad_rank4": (
        "freq_step3_frontier",
        "hp_v13_orrev",
        "split_high_payout_f33_r30_be_never",
        "h4_d1_long_best_box2_atr80",
        "h4_d1_long_broad_box3_atr60",
    ),
    "wr_rank16": (
        "freq_step3_frontier",
        "split_high_payout_f33_r30_be_never",
        "h4_d1_long_best_box2_atr80",
        "h4_d1_long_broad_box3_atr60",
    ),
}


def hour(row: dict[str, Any]) -> int:
    return int(row["entry_time"].hour)


def weekday(row: dict[str, Any]) -> int:
    return int(row["entry_time"].weekday())


def raw_rows(combo: tuple[str, ...], components: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for component in combo:
        rows.extend(components[component])
    return rows


def gate_catalog(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    components = sorted({str(row["component"]) for row in rows})
    directions = sorted({str(row["direction"]) for row in rows})
    hours = sorted({hour(row) for row in rows})
    weekdays = sorted({weekday(row) for row in rows})
    families = sorted({str(row.get("family_group") or "") for row in rows})

    gates: list[dict[str, Any]] = []

    def add(label: str, kind: str, values: dict[str, Any]) -> None:
        gates.append({"label": label, "kind": kind, "values": values})

    for component in components:
        add(f"block_component={component}", "component", {"component": component})
    for direction in directions:
        add(f"block_direction={direction}", "direction", {"direction": direction})
    for h in hours:
        add(f"block_hour={h}", "hour", {"hour": h})
    for day in weekdays:
        add(f"block_weekday={day}", "weekday", {"weekday": day})
    for component, direction in itertools.product(components, directions):
        add(
            f"block_component_direction={component}|{direction}",
            "component_direction",
            {"component": component, "direction": direction},
        )
    for component, h in itertools.product(components, hours):
        add(f"block_component_hour={component}|{h}", "component_hour", {"component": component, "hour": h})
    for component, day in itertools.product(components, weekdays):
        add(
            f"block_component_weekday={component}|{day}",
            "component_weekday",
            {"component": component, "weekday": day},
        )
    for family, h in itertools.product(families, hours):
        add(f"block_family_hour={family}|{h}", "family_hour", {"family_group": family, "hour": h})
    for direction, h in itertools.product(directions, hours):
        add(f"block_direction_hour={direction}|{h}", "direction_hour", {"direction": direction, "hour": h})
    return gates


def gate_matches(row: dict[str, Any], gate: dict[str, Any]) -> bool:
    values = gate["values"]
    kind = gate["kind"]
    if kind == "component":
        return row["component"] == values["component"]
    if kind == "direction":
        return row["direction"] == values["direction"]
    if kind == "hour":
        return hour(row) == values["hour"]
    if kind == "weekday":
        return weekday(row) == values["weekday"]
    if kind == "component_direction":
        return row["component"] == values["component"] and row["direction"] == values["direction"]
    if kind == "component_hour":
        return row["component"] == values["component"] and hour(row) == values["hour"]
    if kind == "component_weekday":
        return row["component"] == values["component"] and weekday(row) == values["weekday"]
    if kind == "family_hour":
        return row.get("family_group") == values["family_group"] and hour(row) == values["hour"]
    if kind == "direction_hour":
        return row["direction"] == values["direction"] and hour(row) == values["hour"]
    raise ValueError(kind)


def decision(metrics: dict[str, Any]) -> str:
    wr = float(metrics.get("win_rate_pct") or 0.0)
    wl = float(metrics.get("avg_win_loss") or 0.0)
    active = float(metrics.get("active_weekday_pct") or 0.0)
    pf = float(metrics.get("profit_factor") or 0.0)
    net = float(metrics.get("net_usd") or 0.0)
    signals = int(metrics.get("signals") or 0)
    if signals < MIN_SIGNALS or net <= 0:
        return "FAIL_FLOOR"
    if wr >= 50.0 and wl >= 2.0 and active >= 90.0 and pf >= 1.30:
        return "DIAGNOSTIC_OWNER_SHAPE_HIT"
    if wr >= 50.0 and wl >= 2.0 and active >= 85.0 and pf >= 1.30:
        return "DIAGNOSTIC_CORE_NEAR_ACTIVITY"
    if wr >= 50.0 and wl >= 1.90 and active >= 85.0 and pf >= 1.30:
        return "DIAGNOSTIC_NEAR_FRONTIER"
    if wr >= 50.0 and wl < 2.0:
        return "FAIL_WIN_LOSS"
    if wr < 50.0 and wl >= 2.0:
        return "FAIL_WIN_RATE"
    return "FAIL_OWNER_SHAPE"


def score(metrics: dict[str, Any]) -> float:
    return round(
        min(float(metrics.get("win_rate_pct") or 0.0) / 50.0, 1.2) * 350
        + min(float(metrics.get("avg_win_loss") or 0.0) / 2.0, 1.35) * 350
        + min(float(metrics.get("active_weekday_pct") or 0.0) / 90.0, 1.1) * 250
        + min(float(metrics.get("profit_factor") or 0.0) / 1.4, 1.4) * 100,
        4,
    )


def evaluate(raw: list[dict[str, Any]], gates: tuple[dict[str, Any], ...], baseline_name: str) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    blocked = []
    kept_raw = []
    for row in raw:
        if any(gate_matches(row, gate) for gate in gates):
            blocked.append(row)
        else:
            kept_raw.append(row)
    kept, dropped = dedupe_signals(kept_raw)
    metrics = summary_metrics(kept, market_days=MARKET_DAYS)
    metrics.update(
        {
            "baseline": baseline_name,
            "gate_count": len(gates),
            "gates": " + ".join(gate["label"] for gate in gates) if gates else "BASELINE",
            "raw_rows": len(raw),
            "blocked_raw_rows": len(blocked),
            "dedupe_dropped_rows": len(dropped),
        }
    )
    metrics["decision"] = decision(metrics)
    metrics["score"] = score(metrics)
    return metrics, kept


def write_rows(path: Path, rows: list[dict[str, Any]]) -> None:
    keys = [
        "decision",
        "score",
        "baseline",
        "gate_count",
        "gates",
        "signals",
        "win_rate_pct",
        "avg_win_loss",
        "active_weekday_pct",
        "profit_factor",
        "net_usd",
        "max_closed_drawdown_usd",
        "top25_removed_net_usd",
        "top100_removed_net_usd",
        "raw_rows",
        "blocked_raw_rows",
        "dedupe_dropped_rows",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=keys, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def render(payload: dict[str, Any]) -> str:
    lines = [
        "# A1 XAU Hybrid Categorical Gate Diagnostic",
        "",
        f"Generated UTC: `{payload['generated_at_utc']}`",
        "",
        "Scope: diagnostic-only composition of existing exact MT5 ledgers. No MT5 launch, runtime attach, chart, preset, order, position, or broker state was changed.",
        "",
        f"Status: `{payload['status']}`",
        f"Preregistration: `{payload['preregistration']}`",
        "",
        "## Best Rows",
        "",
        "| Rank | Decision | Baseline | Gates | Signals | WR% | W/L | Active% | PF | Net USD |",
        "| ---: | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for index, row in enumerate(payload["top_rows"], start=1):
        lines.append(
            f"| {index} | `{row['decision']}` | `{row['baseline']}` | `{row['gates']}` | "
            f"{row['signals']} | {row['win_rate_pct']} | {row['avg_win_loss']} | "
            f"{row['active_weekday_pct']} | {row['profit_factor']} | {row['net_usd']} |"
        )
    lines.extend(["", "## Verdict", "", payload["interpretation"], ""])
    lines.append(f"CSV: `{payload['outputs']['csv']}`")
    lines.append(f"JSON: `{payload['outputs']['json']}`")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    if not PREREG.exists():
        raise FileNotFoundError(PREREG)

    components, _inventory = build_components()
    rows: list[dict[str, Any]] = []
    for baseline_name, combo in BASELINES.items():
        raw = raw_rows(combo, components)
        gates = gate_catalog(raw)
        baseline, _ = evaluate(raw, tuple(), baseline_name)
        rows.append(baseline)

        single_rows: list[tuple[dict[str, Any], dict[str, Any]]] = []
        for gate in gates:
            row, _kept = evaluate(raw, (gate,), baseline_name)
            rows.append(row)
            if row["signals"] >= MIN_SIGNALS and row["net_usd"] > 0:
                single_rows.append((row, gate))

        single_rows.sort(key=lambda item: item[0]["score"], reverse=True)
        top_gates = [gate for _row, gate in single_rows[:60]]
        for gate_a, gate_b in itertools.combinations(top_gates, 2):
            row, _kept = evaluate(raw, (gate_a, gate_b), baseline_name)
            rows.append(row)

    decision_rank = {
        "DIAGNOSTIC_OWNER_SHAPE_HIT": 5,
        "DIAGNOSTIC_CORE_NEAR_ACTIVITY": 4,
        "DIAGNOSTIC_NEAR_FRONTIER": 3,
        "FAIL_WIN_LOSS": 2,
        "FAIL_WIN_RATE": 1,
        "FAIL_OWNER_SHAPE": 0,
        "FAIL_FLOOR": -1,
    }
    rows.sort(
        key=lambda row: (
            decision_rank.get(str(row.get("decision")), -2),
            row.get("score") or 0.0,
            row.get("active_weekday_pct") or 0.0,
            row.get("avg_win_loss") or 0.0,
        ),
        reverse=True,
    )
    best = rows[0]
    status = "REJECT_HYBRID_CATEGORICAL_GATE_NO_REPAIR"
    interpretation = "No fixed categorical gate reached the diagnostic owner/core-near frontier. Do not spend reviewer or exact MT5 implementation time on this gate family."
    if best["decision"] == "DIAGNOSTIC_OWNER_SHAPE_HIT":
        status = "DIAGNOSTIC_OWNER_SHAPE_HIT_EXACT_REPLAY_REQUIRED"
        interpretation = "A categorical gate reached the full diagnostic owner shape. Convert it into an exact MT5 implementation/replay before reviewer spend."
    elif best["decision"] == "DIAGNOSTIC_CORE_NEAR_ACTIVITY":
        status = "DIAGNOSTIC_CORE_NEAR_ACTIVITY_EXACT_REPLAY_REQUIRED"
        interpretation = "A categorical gate reached WR>=50 and W/L>=2 with near-owner activity. Convert it into exact MT5 replay only if the activity gap is acceptable."
    elif best["decision"] == "DIAGNOSTIC_NEAR_FRONTIER":
        status = "DIAGNOSTIC_NEAR_FRONTIER_NO_REVIEW"
        interpretation = "A categorical gate improved the frontier but still missed W/L 2.0. Keep as diagnostic context, not a reviewer candidate."

    output_csv = REPORTS_DIR / f"{OUTPUT_STEM}.csv"
    output_json = REPORTS_DIR / f"{OUTPUT_STEM}.json"
    output_md = REPORTS_DIR / f"{OUTPUT_STEM}.md"
    write_rows(output_csv, rows)
    payload = {
        "status": status,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "preregistration": str(PREREG),
        "searched_rows": len(rows),
        "baselines": {key: list(value) for key, value in BASELINES.items()},
        "min_signals": MIN_SIGNALS,
        "best_row": best,
        "top_rows": rows[:30],
        "interpretation": interpretation,
        "outputs": {
            "csv": str(output_csv),
            "json": str(output_json),
            "markdown": str(output_md),
        },
    }
    output_json.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    output_md.write_text(render(payload), encoding="utf-8")
    print(json.dumps({"status": status, "best_decision": best["decision"], "report": str(output_md)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
