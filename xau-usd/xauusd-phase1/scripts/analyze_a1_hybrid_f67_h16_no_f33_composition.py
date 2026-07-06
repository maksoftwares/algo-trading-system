from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from analyze_a1_owner_goal_step3_portfolio_composition import (
    LAST12_MARKET_DAYS,
    LAST12_START,
    MARKET_DAYS,
    REPORTS_DIR,
    dedupe_signals,
    rel,
    summary_metrics,
)


PHASE1_ROOT = Path(__file__).resolve().parents[1]
PREREG = PHASE1_ROOT / "docs" / "A1_XAU_HYBRID_F67_H16_NO_F33_COMPOSITION_PREREG_2026_07_05.md"
INPUT_RAW = REPORTS_DIR / "A1_XAU_HYBRID_F67_H16_EXACT_REPAIR_202207_202606_HYBRID_RAW.csv"
OUTPUT_STEM = "A1_XAU_HYBRID_F67_H16_NO_F33_COMPOSITION_202207_202606"
REMOVED_SOURCE = "step1_f33_r30_be_never"


def parse_dt(value: str) -> datetime:
    return datetime.strptime(value, "%Y-%m-%d %H:%M:%S")


def read_raw_rows(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(newline="", encoding="utf-8-sig") as handle:
        for ordinal, row in enumerate(csv.DictReader(handle), start=2):
            entry_time = parse_dt(str(row["entry_time"]))
            rows.append(
                {
                    "component": row.get("component", ""),
                    "source_id": row.get("source_id", ""),
                    "upstream_source_id": row.get("upstream_source_id", ""),
                    "upstream_component": row.get("upstream_component", ""),
                    "family_group": row.get("family_group", ""),
                    "source_priority": int(row.get("source_priority") or 0),
                    "cell_id": row.get("cell_id", ""),
                    "component_priority": int(row.get("component_priority") or 0),
                    "variant_name": row.get("variant_name", ""),
                    "entry_time": entry_time,
                    "entry_date": entry_time.date(),
                    "direction": row.get("direction", ""),
                    "pnl_usd": float(row.get("pnl_usd") or 0.0),
                    "tickets": int(row.get("tickets") or 1),
                    "lots": float(row.get("lots") or 0.0),
                    "source_csv": row.get("source_csv", ""),
                    "source_row": ordinal,
                }
            )
    return rows


def is_removed_source(row: dict[str, Any]) -> bool:
    return row.get("source_id") == REMOVED_SOURCE or row.get("upstream_source_id") == REMOVED_SOURCE


def decision(metrics: dict[str, Any]) -> str:
    wr = float(metrics.get("win_rate_pct") or 0.0)
    wl = float(metrics.get("avg_win_loss") or 0.0)
    active = float(metrics.get("active_weekday_pct") or 0.0)
    net = float(metrics.get("net_usd") or 0.0)
    if net <= 0:
        return "EXACT_LEDGER_REJECT_NET"
    if wr >= 50.0 and wl >= 2.0 and active >= 90.0:
        return "EXACT_LEDGER_OWNER_GOAL_HIT_REVIEW_REQUIRED"
    if wr >= 50.0 and wl >= 2.0 and active >= 85.0:
        return "EXACT_LEDGER_CORE_FRONTIER_ACTIVITY_GAP_NO_REVIEW"
    if wr >= 49.9 and wl >= 1.99 and active >= 85.0:
        return "EXACT_LEDGER_NEAR_FRONTIER_NO_REVIEW"
    return "EXACT_LEDGER_REJECT_OWNER_SHAPE"


def csv_safe(row: dict[str, Any]) -> dict[str, Any]:
    out = dict(row)
    if isinstance(out.get("entry_time"), datetime):
        out["entry_time"] = out["entry_time"].strftime("%Y-%m-%d %H:%M:%S")
    if hasattr(out.get("entry_date"), "isoformat"):
        out["entry_date"] = out["entry_date"].isoformat()
    return out


def write_signal_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    keys = [
        "component",
        "source_id",
        "upstream_source_id",
        "upstream_component",
        "family_group",
        "source_priority",
        "cell_id",
        "component_priority",
        "variant_name",
        "entry_time",
        "entry_date",
        "direction",
        "pnl_usd",
        "tickets",
        "lots",
        "source_csv",
        "source_row",
        "drop_reason",
        "duplicate_of_source_id",
        "duplicate_of_entry_time",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=keys, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(csv_safe(row))


def render(payload: dict[str, Any]) -> str:
    metrics = payload["metrics"]
    lines = [
        "# A1 XAU Hybrid F67-H16 No-F33 Composition",
        "",
        f"Generated UTC: `{payload['generated_at_utc']}`",
        "",
        "Scope: exact-ledger portfolio composition only. The f67 hour-16 source was exact-MT5 replayed; unchanged component ledgers are reused from exact MT5 reports. No MT5 launch, live/demo runtime, chart, preset, order, position, or broker state was changed by this composition step.",
        "",
        f"Status: `{payload['status']}`",
        f"Preregistration: `{rel(Path(payload['preregistration']))}`",
        f"Input raw exact-ledger CSV: `{rel(Path(payload['input_raw_csv']))}`",
        "",
        "## Final Hybrid Metrics",
        "",
        "| Signals | WR% | W/L | Active% | PF | Net USD | Max DD | Last12 WR/WL/Active | Stress -0.30 W/L | Decision |",
        "| ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: | --- |",
        (
            f"| {metrics['signals']} | {metrics['win_rate_pct']} | {metrics['avg_win_loss']} | "
            f"{metrics['active_weekday_pct']} | {metrics['profit_factor']} | {metrics['net_usd']} | "
            f"{metrics['max_closed_drawdown_usd']} | {metrics['last12_win_rate_pct']}/"
            f"{metrics['last12_avg_win_loss']}/{metrics['last12_active_weekday_pct']} | "
            f"{metrics['stress_030_avg_win_loss']} | `{metrics['decision']}` |"
        ),
        "",
        "## Composition Counts",
        "",
        f"- Raw rows before f33 removal: `{payload['raw_rows_before_removal']}`",
        f"- Removed f33 raw rows: `{payload['removed_f33_raw_rows']}`",
        f"- Raw rows after f33 removal: `{payload['raw_rows_after_removal']}`",
        f"- Kept / dropped after dedupe: `{metrics['signals']}` / `{payload['dropped_overlap_signals']}`",
        "",
        "## Source Contributions",
        "",
        "| Source | Signals | Net USD |",
        "| --- | ---: | ---: |",
    ]
    for source_id, row in metrics.get("source_contributions", {}).items():
        lines.append(f"| `{source_id}` | {row['signals']} | {row['net_usd']} |")
    lines.extend(["", "## Verdict", "", payload["interpretation"], "", "## Artifacts", ""])
    for label, path in payload["outputs"].items():
        lines.append(f"- {label}: `{rel(Path(path))}`")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    if not PREREG.exists():
        raise FileNotFoundError(PREREG)
    if not INPUT_RAW.exists():
        raise FileNotFoundError(INPUT_RAW)

    raw = read_raw_rows(INPUT_RAW)
    kept_raw = [row for row in raw if not is_removed_source(row)]
    removed = [row for row in raw if is_removed_source(row)]
    kept, dropped = dedupe_signals(kept_raw)
    metrics = summary_metrics(kept, market_days=MARKET_DAYS)
    last12 = summary_metrics([row for row in kept if row["entry_date"] >= LAST12_START], market_days=LAST12_MARKET_DAYS)
    stress_010 = summary_metrics(kept, cost_per_ticket=0.10, market_days=MARKET_DAYS)
    stress_030 = summary_metrics(kept, cost_per_ticket=0.30, market_days=MARKET_DAYS)
    metrics.update(
        {
            "decision": decision(metrics),
            "last12_signals": last12["signals"],
            "last12_win_rate_pct": last12["win_rate_pct"],
            "last12_avg_win_loss": last12["avg_win_loss"],
            "last12_active_weekday_pct": last12["active_weekday_pct"],
            "last12_net_usd": last12["net_usd"],
            "stress_010_net_usd": stress_010["net_usd"],
            "stress_010_avg_win_loss": stress_010["avg_win_loss"],
            "stress_030_net_usd": stress_030["net_usd"],
            "stress_030_avg_win_loss": stress_030["avg_win_loss"],
        }
    )
    status = metrics["decision"]
    if status == "EXACT_LEDGER_OWNER_GOAL_HIT_REVIEW_REQUIRED":
        interpretation = "The exact-ledger composition reached all owner metrics. Reviewer reconstruction is required before any demo-spec drafting."
    elif status == "EXACT_LEDGER_CORE_FRONTIER_ACTIVITY_GAP_NO_REVIEW":
        interpretation = "The exact-ledger composition clears WR and W/L by a razor-thin margin but remains below the 90% active-day threshold and fails the +0.30/ticket W/L stress. Keep as frontier evidence; do not draft a demo spec."
    elif status == "EXACT_LEDGER_NEAR_FRONTIER_NO_REVIEW":
        interpretation = "The exact-ledger composition remains a near miss. Do not spend reviewer budget on it."
    else:
        interpretation = "The exact-ledger composition fails the owner shape. Do not spend reviewer budget on it."

    outputs = {
        "kept_csv": str(REPORTS_DIR / f"{OUTPUT_STEM}_KEPT.csv"),
        "dropped_csv": str(REPORTS_DIR / f"{OUTPUT_STEM}_DROPPED.csv"),
        "removed_f33_csv": str(REPORTS_DIR / f"{OUTPUT_STEM}_REMOVED_F33.csv"),
        "json": str(REPORTS_DIR / f"{OUTPUT_STEM}.json"),
        "md": str(REPORTS_DIR / f"{OUTPUT_STEM}.md"),
    }
    write_signal_csv(Path(outputs["kept_csv"]), kept)
    write_signal_csv(Path(outputs["dropped_csv"]), dropped)
    write_signal_csv(Path(outputs["removed_f33_csv"]), removed)
    payload = {
        "status": status,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "preregistration": str(PREREG),
        "input_raw_csv": str(INPUT_RAW),
        "boundary": "exact_mt5_ledgers_reused_no_runtime_touch",
        "removed_source": REMOVED_SOURCE,
        "raw_rows_before_removal": len(raw),
        "removed_f33_raw_rows": len(removed),
        "raw_rows_after_removal": len(kept_raw),
        "dropped_overlap_signals": len(dropped),
        "metrics": metrics,
        "interpretation": interpretation,
        "outputs": outputs,
    }
    Path(outputs["json"]).write_text(json.dumps(payload, indent=2), encoding="utf-8")
    Path(outputs["md"]).write_text(render(payload), encoding="utf-8")
    print(
        json.dumps(
            {
                "status": status,
                "signals": metrics["signals"],
                "win_rate_pct": metrics["win_rate_pct"],
                "avg_win_loss": metrics["avg_win_loss"],
                "active_weekday_pct": metrics["active_weekday_pct"],
                "net_usd": metrics["net_usd"],
                "report": outputs["md"],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
