from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[3]
PHASE1_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TRADES = PHASE1_ROOT / "outputs" / "reports" / "PHASE2_DEMO_ACTUAL_BROKER_TRADES.csv"
DEFAULT_REPORT_MD = PHASE1_ROOT / "outputs" / "reports" / "EDGE_LOSS_AND_RECOVERY_FORENSIC_2026_07_01.md"
DEFAULT_REPORT_JSON = PHASE1_ROOT / "outputs" / "reports" / "EDGE_LOSS_AND_RECOVERY_FORENSIC_2026_07_01.json"


PERIODS = {
    "early_window_jun_01_07": ("2026-06-01", "2026-06-07"),
    "expansion_loss_jun_08_14": ("2026-06-08", "2026-06-14"),
    "guardrail_drift_jun_15_19": ("2026-06-15", "2026-06-19"),
}


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate edge-loss and recovery forensic from actual demo broker fills.")
    parser.add_argument("--trades-csv", type=Path, default=DEFAULT_TRADES)
    parser.add_argument("--report-md", type=Path, default=DEFAULT_REPORT_MD)
    parser.add_argument("--report-json", type=Path, default=DEFAULT_REPORT_JSON)
    args = parser.parse_args()
    payload = build_payload(args.trades_csv)
    args.report_json.parent.mkdir(parents=True, exist_ok=True)
    args.report_json.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    args.report_md.write_text(render_markdown(payload), encoding="utf-8")
    print(f"Wrote {args.report_md}")
    print(f"Wrote {args.report_json}")


def build_payload(trades_csv: Path) -> dict[str, Any]:
    rows = [normalize(row) for row in read_rows(trades_csv)]
    closed = [row for row in rows if row["state"].upper() == "CLOSED" and row["exit_time"]]
    deduped = [row for row in closed if not row["is_duplicate"]]
    raw = closed
    periods = {
        name: {
            "start": start,
            "end": end,
            "raw": aggregate(filter_date(raw, start, end)),
            "deduped": aggregate(filter_date(deduped, start, end)),
        }
        for name, (start, end) in PERIODS.items()
    }
    by_candidate = sorted_group(deduped, "candidate")
    by_candidate_symbol = sorted_group(deduped, ("candidate", "symbol"))
    by_magic_candidate_symbol = sorted_group(deduped, ("magic", "candidate", "symbol"))
    by_time_bucket = sorted_group(deduped, "time_bucket")
    breakout = [row for row in deduped if row["candidate"] == "breakout_retest"]
    breakout_xau_920101 = [
        row
        for row in breakout
        if row["symbol"] == "XAUUSD" and row["magic"] == "920101"
    ]
    positive_core = {
        "all_920101_xau": aggregate(breakout_xau_920101),
        "evening_920101_xau": aggregate([row for row in breakout_xau_920101 if row["time_bucket"].startswith("Evening")]),
        "by_period": {
            name: aggregate(filter_date(breakout_xau_920101, start, end))
            for name, (start, end) in PERIODS.items()
        },
        "by_time_bucket": sorted_group(breakout_xau_920101, "time_bucket"),
        "daily": sorted_group(breakout_xau_920101, "entry_date", reverse=False),
    }
    weak_lane_candidates = {
        "symbol_normalized_round_retest_v0",
        "session_extreme_retest_v0",
        "swing_breakout_retest_v0",
        "round_number_retest_v0",
    }
    weak_lanes = [row for row in deduped if row["candidate"] in weak_lane_candidates or row["candidate"].endswith("_repair_v1")]
    return {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "OFFLINE_FORENSIC_NO_RUNTIME_CHANGE",
        "source_trades_csv": str(trades_csv),
        "row_counts": {
            "raw_closed": len(raw),
            "deduped_closed": len(deduped),
            "duplicates_removed": len(raw) - len(deduped),
        },
        "raw_total": aggregate(raw),
        "deduped_total": aggregate(deduped),
        "periods": periods,
        "by_candidate": by_candidate,
        "by_candidate_symbol": by_candidate_symbol[:20],
        "by_magic_candidate_symbol": by_magic_candidate_symbol[:20],
        "by_time_bucket": by_time_bucket,
        "positive_core": positive_core,
        "weak_lanes": {
            "overall": aggregate(weak_lanes),
            "by_candidate": sorted_group(weak_lanes, "candidate"),
            "by_candidate_symbol": sorted_group(weak_lanes, ("candidate", "symbol"))[:15],
        },
        "runtime_log_findings": runtime_log_findings(),
        "diagnosis": diagnosis(),
        "recovery_configuration": recovery_configuration(),
    }


def read_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(path)
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def normalize(row: dict[str, str]) -> dict[str, Any]:
    entry_time = row.get("entry_time", "")
    entry_date = entry_time[:10]
    return {
        **row,
        "entry_date": entry_date,
        "profit_aed": to_float(row.get("profit_aed")),
        "is_duplicate": str(row.get("is_duplicate", "")).lower() == "true",
        "state": row.get("state", ""),
        "candidate": row.get("candidate", "") or "UNKNOWN",
        "symbol": row.get("symbol", "") or "UNKNOWN",
        "magic": row.get("magic", "") or "UNKNOWN",
        "time_bucket": row.get("time_bucket", "") or "UNKNOWN",
        "direction": row.get("direction", "") or "UNKNOWN",
    }


def to_float(value: Any) -> float:
    try:
        return float(str(value or "0").replace(",", ""))
    except ValueError:
        return 0.0


def filter_date(rows: list[dict[str, Any]], start: str, end: str) -> list[dict[str, Any]]:
    return [row for row in rows if start <= row["entry_date"] <= end]


def aggregate(rows: list[dict[str, Any]]) -> dict[str, Any]:
    wins = [row for row in rows if row["profit_aed"] > 0]
    losses = [row for row in rows if row["profit_aed"] < 0]
    gross_profit = sum(row["profit_aed"] for row in wins)
    gross_loss = -sum(row["profit_aed"] for row in losses)
    pnl = gross_profit - gross_loss
    return {
        "trades": len(rows),
        "wins": len(wins),
        "losses": len(losses),
        "win_rate_pct": round((len(wins) / len(rows)) * 100, 2) if rows else 0.0,
        "pnl_aed": round(pnl, 2),
        "profit_factor": round(gross_profit / gross_loss, 2) if gross_loss else None,
        "avg_pnl_aed": round(pnl / len(rows), 2) if rows else 0.0,
        "gross_profit": round(gross_profit, 2),
        "gross_loss": round(gross_loss, 2),
    }


def sorted_group(rows: list[dict[str, Any]], key: str | tuple[str, ...], reverse: bool = True) -> list[dict[str, Any]]:
    buckets: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        if isinstance(key, tuple):
            name = " / ".join(str(row.get(part, "")) for part in key)
        else:
            name = str(row.get(key, ""))
        buckets[name].append(row)
    ranked = [{"group": name, **aggregate(items)} for name, items in buckets.items()]
    return sorted(ranked, key=lambda item: item["pnl_aed"], reverse=reverse)


def runtime_log_findings() -> dict[str, Any]:
    a1_files = Path("C:/Users/ZHAO ZHU INFORMATION/AppData/Roaming/MetaQuotes/Terminal/D0E8209F77C8CF37AD8BF550E51FF075/MQL5/Files")
    tracked = {
        "old_a1_xau_breakout_order_log": a1_files / "experimental_demo_executor_order_log_v02_breakout_retest_xauusd.csv",
        "new_a1_920101_order_log": a1_files / "a1_920101_evening_order_log.csv",
        "old_a1_xau_breakout_signal_log": a1_files / "experimental_demo_executor_signal_log_v02_breakout_retest_xauusd.csv",
        "new_a1_920101_signal_log": a1_files / "a1_920101_evening_signal_log.csv",
        "btc_order_log": a1_files / "experimental_demo_executor_order_log_v02_breakout_retest_btcusd.csv",
        "momentum_signal_log": a1_files / "a1_xau_m5_momentum_signal_log.csv",
    }
    return {name: file_status(path) for name, path in tracked.items()}


def file_status(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"path": str(path), "exists": False}
    return {
        "path": str(path),
        "exists": True,
        "size": path.stat().st_size,
        "last_write_time": datetime.fromtimestamp(path.stat().st_mtime).isoformat(),
    }


def diagnosis() -> list[str]:
    return [
        "The early period was not a stable portfolio edge; it was almost flat at total-book level while one A1 XAU 920101 evening slice carried the good impression.",
        "The real portfolio damage came from expansion into weak same-family lanes, especially symbol_normalized_round_retest_v0 and losing FX breakout lanes.",
        "Later guardrails reduced some bleed, but they also changed the runtime contract, so account-to-account and before/after comparisons became invalid.",
        "A concrete operational mistake occurred: the old A1 XAU standard breakout executor stopped/vanished around the June 18 maintenance window and was later replaced by a different A1/A2 920101 contract.",
        "The Q2 MT5 backtest says full-day breakout-retest remains weak and outlier-sensitive, so restoring the old broad behavior would likely recreate the same instability.",
    ]


def recovery_configuration() -> list[dict[str, str]]:
    return [
        {
            "item": "Stop broad same-family portfolio trading",
            "action": "Keep weak round/swing/session-extreme repair lanes broker-off unless separately re-authorized.",
            "reason": "They created the largest realized bleed.",
        },
        {
            "item": "Do not run 920101 as a general all-day profit engine",
            "action": "Score it only as fixed slices: 24h H1, 16-19 H1, 16-19 H1 cost<=0.15, 16-19 H1 cost<=0.10.",
            "reason": "Backtest shows all-day H1 is PF 1.02 and top-winner fragile.",
        },
        {
            "item": "Use runtime identity as a hard gate",
            "action": "Before each forward week, verify account, terminal, chart, symbol, magic, source hash, session, cost, spread, caps, kill-switch, and startup logs.",
            "reason": "We lost comparability by treating different configs as the same strategy.",
        },
        {
            "item": "Let the new momentum lane run as the primary recovery experiment",
            "action": "Keep it frozen at 0.01 lot and judge after fresh forward trades.",
            "reason": "Its Q2 directional-session HTF variant is much stronger than current breakout-retest diagnostics.",
        },
        {
            "item": "Repair breakout-retest only with a targeted fast-stop filter",
            "action": "Build shadow tests for immediate-failure avoidance and profit protection; do not random tune entry thresholds.",
            "reason": "The current lane loses most badly in <=15 minute stopouts.",
        },
    ]


def render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Edge Loss And Recovery Forensic",
        "",
        f"Generated: `{payload['generated_at_utc']}`",
        f"Status: `{payload['status']}`",
        f"Source trades: `{payload['source_trades_csv']}`",
        "",
        "## Direct Answer",
        "",
        "We did not simply protect a good system until it stopped working. The early system was noisy and only looked good because one narrow A1 XAU `920101` slice was carrying the impression while weak lanes were not yet fully exposed. Then we expanded into too many same-family lanes, especially round-family/FX breakout lanes, and they overwhelmed the book. After that, maintenance and guard changes changed the runtime identity, so the later accounts were no longer running the same thing we were emotionally comparing against.",
        "",
        "The fix is not to go back to the broad old portfolio. The fix is to recover only the evidence-backed slices, kill the broad bleed, and make runtime identity impossible to drift silently.",
        "",
        "## What The Broker Fills Say",
        "",
        f"- Raw closed trades: `{payload['row_counts']['raw_closed']}`",
        f"- Duplicate-hidden closed trades: `{payload['row_counts']['deduped_closed']}`",
        f"- Duplicates removed: `{payload['row_counts']['duplicates_removed']}`",
        "",
        "### Period Timeline",
        "",
        "| Period | Deduped trades | WR | PnL AED | PF | Meaning |",
        "| --- | ---: | ---: | ---: | ---: | --- |",
    ]
    meaning = {
        "early_window_jun_01_07": "Looked promising but total book was nearly flat.",
        "expansion_loss_jun_08_14": "Main damage period; volume exploded into weak lanes.",
        "guardrail_drift_jun_15_19": "Still negative; guardrails and drift made comparisons messy.",
    }
    for name, data in payload["periods"].items():
        d = data["deduped"]
        lines.append(f"| `{name}` | {d['trades']} | {d['win_rate_pct']}% | {d['pnl_aed']} | {d['profit_factor']} | {meaning[name]} |")
    lines.extend(["", "### Candidates By Deduped PnL", ""])
    append_table(lines, payload["by_candidate"][:12])
    lines.extend(["", "### Worst Candidate/Symbol Lanes", ""])
    append_table(lines, sorted(payload["by_candidate_symbol"], key=lambda row: row["pnl_aed"])[:12])
    core = payload["positive_core"]
    lines.extend(
        [
            "",
            "## The Real Positive Slice",
            "",
            "| Slice | Trades | WR | PnL AED | PF |",
            "| --- | ---: | ---: | ---: | ---: |",
            f"| `A1-like 920101 / XAUUSD / all buckets` | {core['all_920101_xau']['trades']} | {core['all_920101_xau']['win_rate_pct']}% | {core['all_920101_xau']['pnl_aed']} | {core['all_920101_xau']['profit_factor']} |",
            f"| `A1-like 920101 / XAUUSD / evening only` | {core['evening_920101_xau']['trades']} | {core['evening_920101_xau']['win_rate_pct']}% | {core['evening_920101_xau']['pnl_aed']} | {core['evening_920101_xau']['profit_factor']} |",
            "",
            "### 920101 XAU By Period",
            "",
        ]
    )
    append_named_stats(lines, core["by_period"])
    lines.extend(["", "### 920101 XAU By Time Bucket", ""])
    append_table(lines, core["by_time_bucket"])
    lines.extend(["", "## Runtime Identity Break", ""])
    for name, status in payload["runtime_log_findings"].items():
        lines.append(f"- `{name}`: exists `{status.get('exists')}`, size `{status.get('size', 'n/a')}`, last write `{status.get('last_write_time', 'n/a')}`")
    lines.extend(["", "## Diagnosis", ""])
    for item in payload["diagnosis"]:
        lines.append(f"- {item}")
    lines.extend(["", "## Recovery Configuration", ""])
    for row in payload["recovery_configuration"]:
        lines.append(f"- **{row['item']}**: {row['action']} Reason: {row['reason']}")
    lines.extend(
        [
            "",
            "## What I Would Fix Now",
            "",
            "1. Stop trying to resurrect the old broad portfolio. It was not the edge.",
            "2. Keep weak same-family lanes off broker action unless a separate forward test approves them.",
            "3. Keep A1/A2 `920101` treated as a narrow experiment, not a solved strategy.",
            "4. Use the new A1 momentum lane as the main recovery experiment because its Q2 directional-session HTF profile is materially stronger.",
            "5. Build the next breakout-retest repair only around the proven failure mode: fast stopouts within 15 minutes, not generic parameter tuning.",
        ]
    )
    return "\n".join(lines) + "\n"


def append_table(lines: list[str], rows: list[dict[str, Any]]) -> None:
    lines.extend(
        [
            "| Group | Trades | WR | PnL AED | PF |",
            "| --- | ---: | ---: | ---: | ---: |",
        ]
    )
    for row in rows:
        lines.append(f"| `{row['group']}` | {row['trades']} | {row['win_rate_pct']}% | {row['pnl_aed']} | {row['profit_factor']} |")


def append_named_stats(lines: list[str], mapping: dict[str, dict[str, Any]]) -> None:
    lines.extend(
        [
            "| Period | Trades | WR | PnL AED | PF |",
            "| --- | ---: | ---: | ---: | ---: |",
        ]
    )
    for name, row in mapping.items():
        lines.append(f"| `{name}` | {row['trades']} | {row['win_rate_pct']}% | {row['pnl_aed']} | {row['profit_factor']} |")


if __name__ == "__main__":
    main()
