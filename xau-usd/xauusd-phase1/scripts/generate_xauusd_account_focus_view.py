from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEFAULT_OUTPUT_PREFIX = Path("outputs/reports/XAUUSD_ACCOUNT_FOCUS_VIEW_2026_06_17")
DEFAULT_CANONICAL_REPORT = Path("outputs/reports/XAUUSD_CANONICAL_LOSS_AVOIDANCE_2026_06_17.json")
DEFAULT_A2_HISTORY_ROWS = Path("outputs/reports/A2_TIER1_ACCOUNT_HISTORY_2026_06_17_ROWS.csv")
DEFAULT_A3_HISTORY_ROWS = Path("outputs/reports/A3_REPAIR_LANE_ACCOUNT_HISTORY_2026_06_17_CLOSED_ROWS.csv")
DAY1_FILES = [
    Path("outputs/reports/EOD_GOLD_A1_20260615.csv"),
    Path("outputs/reports/EOD_GOLD_A3_20260615.csv"),
]
DAY2_FILE = Path("outputs/reports/XAUUSD_DAILY_ROWS_2026_06_16.csv")

ACCOUNT_ROLES = {
    "1025742": "A1_LAB_OBSERVATION",
    "1033030": "A2_PRODUCTION_STYLE_CLEAN",
    "1033669": "A3_PRODUCTION_STYLE_EXPERIMENT",
}

ACCOUNT_LABELS = {
    "1025742": "A1",
    "1033030": "A2",
    "1033669": "A3",
}


def generate_report(
    phase1_root: Path,
    *,
    output_prefix: Path | None = None,
) -> dict[str, Path]:
    phase1_root = phase1_root.resolve()
    output_prefix = (output_prefix or phase1_root / DEFAULT_OUTPUT_PREFIX).resolve()
    canonical_path = phase1_root / DEFAULT_CANONICAL_REPORT

    rows = []
    rows.extend(_read_day1(phase1_root))
    rows.extend(_read_day2(phase1_root))
    rows = [row for row in rows if row["account"] not in {"1033030", "1033669"}]
    rows.extend(_read_a2_history(phase1_root))
    rows.extend(_read_a3_history(phase1_root))

    canonical = json.loads(canonical_path.read_text(encoding="utf-8")) if canonical_path.exists() else {}
    lab_long = canonical.get("account_focus", {}).get("views", [])

    payload = {
        "status": "PASS" if rows else "NO_ROWS",
        "created_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "boundary": (
            "Analysis only. A1 is treated as lab/noisy observation. A2 and A3 are treated as the "
            "production-style evidence lane. This report writes files only and does not touch MT5 runtime, "
            "EAs, presets, charts, orders, positions, profiles, or accounts."
        ),
        "source_files": [
            str(phase1_root / path)
            for path in [*DAY1_FILES, DAY2_FILE, DEFAULT_A2_HISTORY_ROWS, DEFAULT_A3_HISTORY_ROWS, DEFAULT_CANONICAL_REPORT]
        ],
        "production_definition": "A2 account 1033030 plus A3 account 1033669",
        "lab_definition": "A1 account 1025742",
        "tracking_rows": len(rows),
        "lab_long_window_reference": lab_long,
        "tracking_summary": {
            "all_rows": summarize(rows),
            "lab_a1": summarize([row for row in rows if row["account"] == "1025742"]),
            "production_a2_a3": summarize([row for row in rows if row["account"] in {"1033030", "1033669"}]),
            "a2_clean": summarize([row for row in rows if row["account"] == "1033030"]),
            "a3_experiment": summarize([row for row in rows if row["account"] == "1033669"]),
        },
        "production_by_day": group_table([row for row in rows if row["account"] in {"1033030", "1033669"}], ["trade_day"]),
        "production_by_account": group_table([row for row in rows if row["account"] in {"1033030", "1033669"}], ["account_label"]),
        "production_by_family": group_table([row for row in rows if row["account"] in {"1033030", "1033669"}], ["family"]),
        "production_by_session": group_table([row for row in rows if row["account"] in {"1033030", "1033669"}], ["session"]),
        "production_by_account_family": group_table([row for row in rows if row["account"] in {"1033030", "1033669"}], ["account_label", "family"]),
        "lab_by_family": group_table([row for row in rows if row["account"] == "1025742"], ["family"]),
        "lab_by_session": group_table([row for row in rows if row["account"] == "1025742"], ["session"]),
        "decision_notes": decision_notes(),
    }

    output_prefix.parent.mkdir(parents=True, exist_ok=True)
    rows_path = output_prefix.with_name(output_prefix.name + "_ROWS").with_suffix(".csv")
    json_path = output_prefix.with_suffix(".json")
    md_path = output_prefix.with_suffix(".md")
    write_csv(rows_path, rows, row_fields())
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    md_path.write_text(render_markdown(payload, rows_path), encoding="utf-8")
    return {"md": md_path, "json": json_path, "rows": rows_path}


def _read_day1(root: Path) -> list[dict[str, str]]:
    rows = []
    for path in DAY1_FILES:
        source = root / path
        if not source.exists():
            continue
        for row in read_csv(source):
            account = row.get("account", "")
            rows.append(
                normalize_row(
                    source_day="2026-06-15",
                    source_file=source,
                    account=account,
                    candidate=row.get("candidate", ""),
                    magic=row.get("magic", ""),
                    direction=row.get("direction", ""),
                    lots=row.get("lots", ""),
                    entry_time=row.get("entry_time_dubai", ""),
                    exit_time=row.get("exit_time_utc", ""),
                    session=session_bucket(row.get("entry_time_dubai", "")),
                    profit=row.get("profit_aed", ""),
                    cost_r=row.get("cost_r", ""),
                    exit_reason=row.get("exit_reason", ""),
                )
            )
    return rows


def _read_day2(root: Path) -> list[dict[str, str]]:
    source = root / DAY2_FILE
    if not source.exists():
        return []
    rows = []
    for row in read_csv(source):
        account = row.get("account_login", "")
        rows.append(
            normalize_row(
                source_day="2026-06-16",
                source_file=source,
                account=account,
                candidate=row.get("candidate", ""),
                magic=row.get("magic", ""),
                direction=row.get("direction", ""),
                lots=row.get("lots", ""),
                entry_time=row.get("entry_time_dubai", ""),
                exit_time=row.get("exit_time_dubai", ""),
                session=row.get("session", "") or session_bucket(row.get("entry_time_dubai", "")),
                profit=row.get("profit_aed_001", "") or row.get("profit_aed", ""),
                cost_r=row.get("cost_r", ""),
                exit_reason=row.get("exit_reason", ""),
            )
        )
    return rows


def _read_a2_history(root: Path) -> list[dict[str, str]]:
    source = root / DEFAULT_A2_HISTORY_ROWS
    if not source.exists():
        return []
    rows = []
    for row in read_csv(source):
        rows.append(
            normalize_row(
                source_day=row.get("entry_time_dubai", "")[:10] or "A2_HISTORY",
                source_file=source,
                account="1033030",
                candidate=row.get("candidate", ""),
                magic="920101",
                direction=row.get("direction", ""),
                lots=row.get("volume", ""),
                entry_time=row.get("entry_time_dubai", ""),
                exit_time=row.get("exit_time_dubai", ""),
                session=session_bucket(row.get("entry_time_dubai", "")),
                profit=row.get("profit_aed", ""),
                cost_r="",
                exit_reason=row.get("comments", ""),
            )
        )
    return rows


def _read_a3_history(root: Path) -> list[dict[str, str]]:
    source = root / DEFAULT_A3_HISTORY_ROWS
    if not source.exists():
        return []
    rows = []
    for row in read_csv(source):
        rows.append(
            normalize_row(
                source_day=row.get("entry_time_dubai", "")[:10] or "A3_HISTORY",
                source_file=source,
                account="1033669",
                candidate=row.get("candidate", ""),
                magic=a3_magic(row.get("candidate", "")),
                direction=row.get("direction", ""),
                lots=row.get("volume", ""),
                entry_time=row.get("entry_time_dubai", ""),
                exit_time=row.get("exit_time_dubai", ""),
                session=row.get("session", "") or session_bucket(row.get("entry_time_dubai", "")),
                profit=row.get("net_profit_aed", "") or row.get("gross_profit_aed", ""),
                cost_r="",
                exit_reason=row.get("comments", ""),
            )
        )
    return rows


def a3_magic(candidate: str) -> str:
    if candidate == "a3_breakout_plain":
        return "933200"
    if candidate == "a3_breakout_improved":
        return "933300"
    if candidate == "a3_round_retest_guarded_v1":
        return "921100"
    if candidate == "a3_round_retest_structured_v1":
        return "921200"
    return ""


def normalize_row(
    *,
    source_day: str,
    source_file: Path,
    account: str,
    candidate: str,
    magic: str,
    direction: str,
    lots: str,
    entry_time: str,
    exit_time: str,
    session: str,
    profit: str,
    cost_r: str,
    exit_reason: str,
) -> dict[str, str]:
    profit_value = to_float(profit) or 0.0
    return {
        "trade_day": source_day,
        "source_file": str(source_file),
        "account": account,
        "account_label": ACCOUNT_LABELS.get(account, account or "UNKNOWN"),
        "account_role": ACCOUNT_ROLES.get(account, "UNKNOWN"),
        "candidate": candidate,
        "family": family(candidate),
        "magic": magic,
        "direction": direction,
        "lots": lots,
        "entry_time_dubai": entry_time,
        "exit_time": exit_time,
        "session": session,
        "profit_aed_001": fmt(profit_value),
        "outcome": "WIN" if profit_value > 0 else ("LOSS" if profit_value < 0 else "FLAT"),
        "cost_r": cost_r,
        "exit_reason": exit_reason,
    }


def family(candidate: str) -> str:
    if candidate in {"breakout_retest", "swing_breakout_retest_v0", "a3_breakout_plain", "a3_breakout_improved"}:
        return "breakout_core"
    if candidate in {
        "symbol_normalized_round_retest_v0",
        "round_number_retest_v0",
        "a3_round_retest_guarded_v1",
        "a3_round_retest_structured_v1",
        "a3_round_guard_v1",
        "a3_round_structure_v1",
    }:
        return "round_family"
    if "session_extreme" in candidate:
        return "session_extreme"
    if "repair" in candidate:
        return "repair"
    if candidate == "":
        return "UNKNOWN"
    return "other"


def session_bucket(entry_time: str) -> str:
    try:
        hour = int(entry_time[11:13])
    except (ValueError, IndexError):
        return "UNKNOWN"
    if 6 <= hour <= 11:
        return "Morning 06:00-11:59"
    if 12 <= hour <= 15:
        return "Afternoon 12:00-15:59"
    if 16 <= hour <= 19:
        return "Evening 16:00-19:59"
    return "Night 20:00-05:59"


def summarize(rows: list[dict[str, str]]) -> dict[str, str]:
    values = [to_float(row.get("profit_aed_001")) or 0.0 for row in rows]
    wins = [value for value in values if value > 0]
    losses = [value for value in values if value < 0]
    return {
        "rows": str(len(rows)),
        "wins": str(len(wins)),
        "losses": str(len(losses)),
        "flats": str(len(values) - len(wins) - len(losses)),
        "win_rate_pct": pct(len(wins), len(wins) + len(losses)),
        "pnl_aed_001": fmt(sum(values)),
        "profit_factor": fmt(sum(wins) / abs(sum(losses))) if losses and sum(losses) else ("inf" if wins else "n/a"),
        "avg_win_aed": fmt(sum(wins) / len(wins)) if wins else "n/a",
        "avg_loss_aed": fmt(sum(losses) / len(losses)) if losses else "n/a",
    }


def group_table(rows: list[dict[str, str]], keys: list[str]) -> list[dict[str, str]]:
    grouped: dict[tuple[str, ...], list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        grouped[tuple(row.get(key, "") or "UNKNOWN" for key in keys)].append(row)
    table = []
    for key, items in grouped.items():
        summary = summarize(items)
        table.append({"group": " | ".join(key), **summary})
    return sorted(table, key=lambda row: to_float(row["pnl_aed_001"]) or 0.0)


def decision_notes() -> list[str]:
    return [
        "A1 remains useful for broad lab observation, especially to see what noisy/weak EAs do, but it should not drive production-style approval.",
        "A2 is the clean breakout-only lane; direct read-only A2 MT5 history currently shows 8 closed XAUUSD breakout_retest trades, 4 wins / 4 losses, and +104.92 AED closed PnL.",
        "A3 is the experiment lane; the current view now uses direct read-only A3 MT5 history instead of stale/partial day CSV rows.",
        "Round-family quarantine is still a strong lab finding for A1, but applying it to A2/A3 is currently less relevant because A2 has no round family and A3's old round lane has already been retired from new entries.",
        "The next useful production-style evidence is fresh A2 breakout-only and A3 breakout A/B data, not more A1 noise.",
    ]


def render_markdown(payload: dict[str, Any], rows_path: Path) -> str:
    lines = [
        "# XAUUSD Account Focus View - 2026-06-17",
        "",
        f"Status: `{payload['status']}`",
        "",
        payload["boundary"],
        "",
        f"Lab definition: `{payload['lab_definition']}`",
        f"Production-style definition: `{payload['production_definition']}`",
        "",
        f"Normalized rows CSV: `{rows_path}`",
        "",
        "## Tracking Summary",
        "",
        table(
            [
                {"view": "All tracked rows", **payload["tracking_summary"]["all_rows"]},
                {"view": "A1 lab observation", **payload["tracking_summary"]["lab_a1"]},
                {"view": "A2+A3 production-style", **payload["tracking_summary"]["production_a2_a3"]},
                {"view": "A2 clean account", **payload["tracking_summary"]["a2_clean"]},
                {"view": "A3 experiment account", **payload["tracking_summary"]["a3_experiment"]},
            ],
            ["view", "rows", "wins", "losses", "win_rate_pct", "pnl_aed_001", "profit_factor", "avg_win_aed", "avg_loss_aed"],
        ),
        "",
        "## Production-Style View: A2 + A3",
        "",
        "### By Day",
        "",
        table(payload["production_by_day"], ["group", "rows", "wins", "losses", "win_rate_pct", "pnl_aed_001", "profit_factor"]),
        "",
        "### By Account",
        "",
        table(payload["production_by_account"], ["group", "rows", "wins", "losses", "win_rate_pct", "pnl_aed_001", "profit_factor"]),
        "",
        "### By Family",
        "",
        table(payload["production_by_family"], ["group", "rows", "wins", "losses", "win_rate_pct", "pnl_aed_001", "profit_factor"]),
        "",
        "### By Session",
        "",
        table(payload["production_by_session"], ["group", "rows", "wins", "losses", "win_rate_pct", "pnl_aed_001", "profit_factor"]),
        "",
        "### By Account And Family",
        "",
        table(payload["production_by_account_family"], ["group", "rows", "wins", "losses", "win_rate_pct", "pnl_aed_001", "profit_factor"]),
        "",
        "## Lab View: A1",
        "",
        "A1 is intentionally noisy. Use this for weakness discovery, not production-style verdicts.",
        "",
        "### A1 By Family",
        "",
        table(payload["lab_by_family"], ["group", "rows", "wins", "losses", "win_rate_pct", "pnl_aed_001", "profit_factor"]),
        "",
        "### A1 By Session",
        "",
        table(payload["lab_by_session"], ["group", "rows", "wins", "losses", "win_rate_pct", "pnl_aed_001", "profit_factor"]),
        "",
        "## Long-Window A1 Lab Reference",
        "",
        "The canonical long-window report is A1-only in the currently matched data. It remains useful as lab evidence, not A2/A3 production evidence.",
        "",
        table(payload.get("lab_long_window_reference") or [], ["view", "rows", "win_rate_pct", "pnl_aed", "pf", "no_round_rows", "no_round_pnl_aed", "breakout_core_rows", "breakout_core_pnl_aed"]),
        "",
        "## Decision Notes",
        "",
    ]
    lines.extend(f"- {note}" for note in payload["decision_notes"])
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "Review only. No MT5 runtime, EA, preset, chart, order, position, profile, or account change is authorized by this report.",
            "",
        ]
    )
    return "\n".join(lines)


def table(rows: list[dict[str, Any]], columns: list[str]) -> str:
    if not rows:
        return "_No rows._"
    output = [
        "| " + " | ".join(columns) + " |",
        "| " + " | ".join("---" for _ in columns) + " |",
    ]
    for row in rows:
        output.append("| " + " | ".join(str(row.get(column, "")) for column in columns) + " |")
    return "\n".join(output)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, str]], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def row_fields() -> list[str]:
    return [
        "trade_day",
        "source_file",
        "account",
        "account_label",
        "account_role",
        "candidate",
        "family",
        "magic",
        "direction",
        "lots",
        "entry_time_dubai",
        "exit_time",
        "session",
        "profit_aed_001",
        "outcome",
        "cost_r",
        "exit_reason",
    ]


def to_float(value: Any) -> float | None:
    if value is None:
        return None
    text = str(value).strip()
    if text == "" or text.lower() == "n/a":
        return None
    try:
        return float(text)
    except ValueError:
        return None


def fmt(value: Any) -> str:
    number = to_float(value)
    if number is None:
        return "n/a"
    return f"{number:.2f}"


def pct(numerator: int, denominator: int) -> str:
    if denominator == 0:
        return "n/a"
    return f"{100.0 * numerator / denominator:.2f}%"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate A1 lab vs A2/A3 production-style XAUUSD report.")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output-prefix", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    outputs = generate_report(args.root, output_prefix=args.output_prefix)
    for label, path in outputs.items():
        print(f"{label}: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
