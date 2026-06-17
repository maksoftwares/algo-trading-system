from __future__ import annotations

import argparse
import csv
import json
import math
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEFAULT_TRADES_CSV = Path("outputs") / "reports" / "PHASE2_DEMO_ACTUAL_BROKER_TRADES.csv"
DEFAULT_PATH_LOG_DIR = Path("C:/MT5PortablePositionPathObserver/MQL5/Files")
DEFAULT_OUTPUT_JSON = Path("outputs") / "reports" / "A3_PROFIT_LOCK_EXIT_MANAGER_GATE_2026_06_17.json"
DEFAULT_OUTPUT_CSV = Path("outputs") / "reports" / "A3_PROFIT_LOCK_EXIT_MANAGER_GATE_2026_06_17.csv"

SYMBOL = "XAUUSD"
TRIGGER_R = 1.25
LOCK_R = 0.80

REPLAY_COLUMNS = [
    "position_ticket",
    "entry_time",
    "exit_time",
    "candidate",
    "direction",
    "magic",
    "path_account_login",
    "control_r",
    "control_aed",
    "replay_r",
    "replay_aed",
    "delta_aed",
    "max_unrealized_r",
    "min_unrealized_r",
    "path_rows",
    "status",
    "arm_time",
    "lock_exit_time",
    "duplicate_role",
    "is_duplicate",
    "time_bucket",
]


@dataclass(frozen=True)
class PathPoint:
    timestamp: str
    unrealized_r: float
    row_type: str
    account_login: str
    magic: str


def run_profit_lock_gate(
    phase1_root: Path,
    trades_csv: Path | None = None,
    path_log_dir: Path = DEFAULT_PATH_LOG_DIR,
    output_json: Path | None = None,
    output_csv: Path | None = None,
    trigger_r: float = TRIGGER_R,
    lock_r: float = LOCK_R,
) -> dict[str, Any]:
    phase1_root = phase1_root.resolve()
    trades_csv = (trades_csv or phase1_root / DEFAULT_TRADES_CSV).resolve()
    output_json = (output_json or phase1_root / DEFAULT_OUTPUT_JSON).resolve()
    output_csv = (output_csv or phase1_root / DEFAULT_OUTPUT_CSV).resolve()
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_csv.parent.mkdir(parents=True, exist_ok=True)

    trades = load_closed_xauusd_trades(trades_csv)
    paths = load_position_paths(path_log_dir, {row["position_ticket"] for row in trades})
    replay_rows = [replay_trade(row, paths.get(row["position_ticket"], []), trigger_r, lock_r) for row in trades]
    covered_rows = [row for row in replay_rows if int(row["path_rows"]) > 0]
    dedup_rows = [row for row in covered_rows if is_duplicate_hidden(row)]

    raw_stats = summarize_view("raw_including_duplicates", covered_rows)
    dedup_stats = summarize_view("duplicate_hidden", dedup_rows)
    status = "PASS" if dedup_stats["delta_aed"] > 0 and dedup_stats["best_day_removed_delta_aed"] > 0 else "HOLD_DO_NOT_ARM"

    payload: dict[str, Any] = {
        "status": status,
        "created_at_utc": now_utc(),
        "scope": {
            "symbol": SYMBOL,
            "trades_csv": str(trades_csv),
            "path_log_dir": str(path_log_dir),
            "closed_xauusd_rows": len(trades),
            "path_covered_raw_rows": len(covered_rows),
            "path_covered_duplicate_hidden_rows": len(dedup_rows),
            "trigger_r": trigger_r,
            "lock_r": lock_r,
        },
        "gate": {
            "dedup_net_positive": dedup_stats["delta_aed"] > 0,
            "dedup_best_day_removed_positive": dedup_stats["best_day_removed_delta_aed"] > 0,
            "decision": status,
        },
        "views": {
            "duplicate_hidden": dedup_stats,
            "raw_including_duplicates": raw_stats,
        },
        "candidate_breakdown_duplicate_hidden": candidate_breakdown(dedup_rows),
        "changed_trades_duplicate_hidden": [
            row for row in dedup_rows if abs(fnum(row["delta_aed"], 0.0)) > 0.005
        ],
        "reconciliation": {
            "prior_partial_be_report": "xau-usd/xauusd-phase1/docs/DYNAMIC_EXIT_DEPLOYMENT_VERDICT_2026_06_09.md",
            "prior_partial_be_duplicate_hidden_delta_aed": -134.14,
            "note": (
                "The prior +1R partial/breakeven replay clipped winners and saved zero logged losers. "
                "This gate tests a later +1.25R trigger with a +0.80R SL floor and no partial close."
            ),
        },
    }

    write_csv(output_csv, covered_rows, REPLAY_COLUMNS)
    output_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    output_json.with_suffix(".md").write_text(render_gate_report(payload, output_csv), encoding="utf-8")
    return payload


def load_closed_xauusd_trades(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(newline="", encoding="utf-8-sig") as handle:
        for row in csv.DictReader(handle):
            if row.get("symbol") != SYMBOL or row.get("state") != "CLOSED":
                continue
            control_r = control_r_from_prices(row)
            control_aed = fnum(row.get("profit_aed"))
            if math.isnan(control_r) or abs(control_r) <= 1e-9 or math.isnan(control_aed):
                continue
            row["control_r"] = control_r
            row["control_aed"] = control_aed
            row["aed_per_r"] = control_aed / control_r
            rows.append(row)
    return rows


def load_position_paths(path_log_dir: Path, tickets: set[str]) -> dict[str, list[PathPoint]]:
    paths: dict[str, list[PathPoint]] = defaultdict(list)
    if not path_log_dir.exists():
        return paths
    for path in sorted(path_log_dir.glob("position_path_log_*.csv")):
        with path.open(newline="", encoding="utf-8-sig") as handle:
            for row in csv.DictReader(handle):
                ticket = row.get("position_ticket", "")
                if ticket not in tickets or row.get("symbol") != SYMBOL:
                    continue
                unrealized_r = fnum(row.get("unrealized_R"))
                if math.isnan(unrealized_r):
                    continue
                timestamp = row.get("ts_utc") or row.get("ts_broker") or row.get("ts_local") or ""
                paths[ticket].append(
                    PathPoint(
                        timestamp=timestamp,
                        unrealized_r=unrealized_r,
                        row_type=row.get("row_type", ""),
                        account_login=row.get("account_login", ""),
                        magic=row.get("magic", ""),
                    )
                )
    for points in paths.values():
        points.sort(key=lambda item: item.timestamp)
    return paths


def replay_trade(row: dict[str, Any], path: list[PathPoint], trigger_r: float, lock_r: float) -> dict[str, Any]:
    control_r = float(row["control_r"])
    control_aed = float(row["control_aed"])
    aed_per_r = float(row["aed_per_r"])
    replay_r = control_r
    status = "UNCHANGED_NO_ARM"
    arm_time = ""
    lock_exit_time = ""
    armed = False

    for point in path:
        if not armed and point.unrealized_r >= trigger_r:
            armed = True
            arm_time = point.timestamp
            status = "ARMED_NO_LOCK_EXIT"
        if armed and point.unrealized_r <= lock_r:
            replay_r = lock_r
            lock_exit_time = point.timestamp
            status = "LOCK_EXIT_AT_FLOOR"
            break

    if not path:
        status = "NO_PATH"

    replay_aed = replay_r * aed_per_r
    return {
        "position_ticket": row.get("position_ticket", ""),
        "entry_time": row.get("entry_time", ""),
        "exit_time": row.get("exit_time", ""),
        "candidate": row.get("candidate", ""),
        "direction": row.get("direction", ""),
        "magic": row.get("magic", ""),
        "path_account_login": next((point.account_login for point in path if point.account_login), ""),
        "control_r": round(control_r, 6),
        "control_aed": round(control_aed, 2),
        "replay_r": round(replay_r, 6),
        "replay_aed": round(replay_aed, 2),
        "delta_aed": round(replay_aed - control_aed, 2),
        "max_unrealized_r": round(max((point.unrealized_r for point in path), default=math.nan), 6) if path else "",
        "min_unrealized_r": round(min((point.unrealized_r for point in path), default=math.nan), 6) if path else "",
        "path_rows": len(path),
        "status": status,
        "arm_time": arm_time,
        "lock_exit_time": lock_exit_time,
        "duplicate_role": row.get("duplicate_role", ""),
        "is_duplicate": row.get("is_duplicate", ""),
        "time_bucket": row.get("time_bucket", ""),
    }


def summarize_view(label: str, rows: list[dict[str, Any]]) -> dict[str, Any]:
    control_aed = round(sum(fnum(row["control_aed"], 0.0) for row in rows), 2)
    replay_aed = round(sum(fnum(row["replay_aed"], 0.0) for row in rows), 2)
    delta_aed = round(replay_aed - control_aed, 2)
    day_deltas: dict[str, float] = defaultdict(float)
    for row in rows:
        day_deltas[str(row.get("entry_time", ""))[:10]] += fnum(row.get("delta_aed"), 0.0)
    rounded_days = {day: round(delta, 2) for day, delta in sorted(day_deltas.items())}
    best_day, best_delta = ("", 0.0)
    worst_day, worst_delta = ("", 0.0)
    if rounded_days:
        best_day, best_delta = max(rounded_days.items(), key=lambda item: item[1])
        worst_day, worst_delta = min(rounded_days.items(), key=lambda item: item[1])
    return {
        "label": label,
        "rows": len(rows),
        "control_aed": control_aed,
        "replay_aed": replay_aed,
        "delta_aed": delta_aed,
        "changed_rows": sum(1 for row in rows if abs(fnum(row.get("delta_aed"), 0.0)) > 0.005),
        "lock_exit_rows": sum(1 for row in rows if row.get("status") == "LOCK_EXIT_AT_FLOOR"),
        "armed_no_lock_exit_rows": sum(1 for row in rows if row.get("status") == "ARMED_NO_LOCK_EXIT"),
        "unchanged_no_arm_rows": sum(1 for row in rows if row.get("status") == "UNCHANGED_NO_ARM"),
        "day_deltas": rounded_days,
        "best_delta_day": best_day,
        "best_delta_day_aed": best_delta,
        "worst_delta_day": worst_day,
        "worst_delta_day_aed": worst_delta,
        "best_day_removed_delta_aed": round(delta_aed - best_delta, 2),
    }


def candidate_breakdown(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    buckets: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        buckets[row.get("candidate", "")].append(row)
    output = []
    for candidate in sorted(buckets):
        stats = summarize_view(candidate, buckets[candidate])
        output.append(
            {
                "candidate": candidate,
                "rows": stats["rows"],
                "control_aed": stats["control_aed"],
                "replay_aed": stats["replay_aed"],
                "delta_aed": stats["delta_aed"],
                "changed_rows": stats["changed_rows"],
            }
        )
    return output


def control_r_from_prices(row: dict[str, str]) -> float:
    direction = row.get("direction", "").upper()
    entry = fnum(row.get("entry_price"))
    stop = fnum(row.get("sl"))
    exit_price = fnum(row.get("exit_price"))
    risk = abs(entry - stop) if not math.isnan(entry) and not math.isnan(stop) else math.nan
    if math.isnan(risk) or risk <= 0.0 or math.isnan(exit_price):
        return math.nan
    if direction == "BUY":
        return (exit_price - entry) / risk
    if direction == "SELL":
        return (entry - exit_price) / risk
    return math.nan


def is_duplicate_hidden(row: dict[str, Any]) -> bool:
    return str(row.get("is_duplicate", "")).lower() != "true" and str(row.get("duplicate_role", "")).lower() != "duplicate"


def write_csv(path: Path, rows: list[dict[str, Any]], columns: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def render_gate_report(payload: dict[str, Any], output_csv: Path) -> str:
    dedup = payload["views"]["duplicate_hidden"]
    raw = payload["views"]["raw_including_duplicates"]
    lines = [
        "# A3 Profit-Lock Exit Manager Replay Gate",
        "",
        f"Status: `{payload['status']}`",
        "",
        "Rule replayed: arm at `+1.25R`, then lock stop to `+0.80R`; no partial close, no TP change.",
        "",
        "## Gate Summary",
        "",
        "| View | Rows | Control AED | Replay AED | Delta AED | Changed | Lock exits | Best day removed delta AED |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
        view_row("Duplicate-hidden", dedup),
        view_row("Raw incl duplicates", raw),
        "",
        "Gate condition: duplicate-hidden net delta must be positive and must remain positive after removing the best delta day.",
        "",
        "## Duplicate-Hidden Candidate Breakdown",
        "",
        "| Candidate | Rows | Control AED | Replay AED | Delta AED | Changed |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in payload["candidate_breakdown_duplicate_hidden"]:
        lines.append(
            f"| {escape_md(row['candidate'])} | {row['rows']} | {row['control_aed']:.2f} | {row['replay_aed']:.2f} | {row['delta_aed']:.2f} | {row['changed_rows']} |"
        )
    lines.extend(
        [
            "",
            "## Prior Exit-Replay Reconciliation",
            "",
            "- Prior rejected BE/partial path: duplicate-hidden delta `-134.14 AED`, with winner drag and zero logged losers saved.",
            "- This rule is later and simpler: `+1.25R` trigger, `+0.80R` SL floor, no partial close.",
            f"- Replay CSV: `{output_csv}`",
            "",
            "## Changed Duplicate-Hidden Trades",
            "",
            "| Entry | Ticket | Candidate | Side | Control AED | Max R | Status | Delta AED |",
            "| --- | ---: | --- | --- | ---: | ---: | --- | ---: |",
        ]
    )
    for row in payload["changed_trades_duplicate_hidden"]:
        lines.append(
            f"| {row['entry_time']} | {row['position_ticket']} | {escape_md(row['candidate'])} | {row['direction']} | {float(row['control_aed']):.2f} | {float(row['max_unrealized_r']):.3f} | {row['status']} | {float(row['delta_aed']):.2f} |"
        )
    lines.append("")
    return "\n".join(lines)


def view_row(label: str, stats: dict[str, Any]) -> str:
    return (
        f"| {label} | {stats['rows']} | {stats['control_aed']:.2f} | {stats['replay_aed']:.2f} | "
        f"{stats['delta_aed']:.2f} | {stats['changed_rows']} | {stats['lock_exit_rows']} | "
        f"{stats['best_day_removed_delta_aed']:.2f} |"
    )


def fnum(value: object, default: float = math.nan) -> float:
    try:
        if value is None or str(value).strip() == "":
            return default
        return float(str(value).replace(",", ""))
    except (TypeError, ValueError):
        return default


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def escape_md(value: object) -> str:
    return str(value).replace("|", "\\|").replace("\n", "<br>")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Replay A3 profit-lock exit manager gate.")
    parser.add_argument("--phase1-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--trades-csv", type=Path, default=None)
    parser.add_argument("--path-log-dir", type=Path, default=DEFAULT_PATH_LOG_DIR)
    parser.add_argument("--output-json", type=Path, default=None)
    parser.add_argument("--output-csv", type=Path, default=None)
    args = parser.parse_args(argv)
    payload = run_profit_lock_gate(
        phase1_root=args.phase1_root,
        trades_csv=args.trades_csv,
        path_log_dir=args.path_log_dir,
        output_json=args.output_json,
        output_csv=args.output_csv,
    )
    print(f"A3 profit-lock replay gate: {payload['status']}")
    print(json.dumps(payload["views"]["duplicate_hidden"], indent=2))
    return 0 if payload["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
