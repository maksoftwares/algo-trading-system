from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEFAULT_FILES_DIR = Path("C:/MT5PortableShadowFixObservers/MQL5/Files")
DEFAULT_OUTPUT_JSON = Path("outputs") / "reports" / "PHASE2_SHADOW_FIX_OBSERVER_LIVE_REPORT.json"
DEFAULT_OUTPUT_MD = Path("outputs") / "reports" / "PHASE2_SHADOW_FIX_OBSERVER_LIVE_REPORT.md"


def generate_phase2_shadow_fix_observer_report(
    phase1_root: Path,
    files_dir: Path = DEFAULT_FILES_DIR,
    output_json: Path | None = None,
) -> Path:
    phase1_root = phase1_root.resolve()
    files_dir = files_dir.resolve()
    output_json = (output_json or phase1_root / DEFAULT_OUTPUT_JSON).resolve()
    output_md = output_json.with_suffix(".md") if output_json.name != DEFAULT_OUTPUT_JSON.name else phase1_root / DEFAULT_OUTPUT_MD
    output_json.parent.mkdir(parents=True, exist_ok=True)

    rows = _read_rows(files_dir)
    signal_rows = [row for row in rows if _truthy(row.get("would_signal"))]
    payload: dict[str, Any] = {
        "status": "SHADOW_FIX_OBSERVER_LOGS_READY" if rows else "NO_SHADOW_FIX_OBSERVER_ROWS",
        "created_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "authority": (
            "Read-only summary of isolated shadow-fix observer logs. It does not touch MT5 runtime, orders, "
            "positions, charts, or the standard demo trading terminal."
        ),
        "files_dir": str(files_dir),
        "file_count": len(list(files_dir.glob("shadow_fix_observer_signal_log_*.csv"))) if files_dir.exists() else 0,
        "row_count": len(rows),
        "signal_count": len(signal_rows),
        "latest_row": max((row.get("timestamp_broker", "") for row in rows), default="missing"),
        "by_shadow_action": _counter(rows, "shadow_action"),
        "signal_by_shadow_action": _counter(signal_rows, "shadow_action"),
        "signal_by_shadow_reason": _counter(signal_rows, "shadow_reason"),
        "signal_by_candidate": _counter(signal_rows, "candidate"),
        "signal_by_symbol": _counter(signal_rows, "symbol"),
        "signal_by_time_bucket": _counter(signal_rows, "time_bucket"),
        "signal_by_candidate_symbol_time": _counter(signal_rows, "candidate", "symbol", "time_bucket"),
    }
    output_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    output_md.write_text(_render_markdown(payload), encoding="utf-8")
    return output_json


def _read_rows(files_dir: Path) -> list[dict[str, str]]:
    if not files_dir.exists():
        return []
    rows: list[dict[str, str]] = []
    for path in sorted(files_dir.glob("shadow_fix_observer_signal_log_*.csv")):
        with path.open("r", encoding="utf-8", newline="") as handle:
            for row in csv.DictReader(handle):
                row["_source_file"] = path.name
                rows.append(row)
    return rows


def _truthy(value: str | None) -> bool:
    return str(value or "").strip().lower() in {"true", "1", "yes"}


def _counter(rows: list[dict[str, str]], *keys: str) -> list[dict[str, Any]]:
    counts: Counter[tuple[str, ...]] = Counter()
    for row in rows:
        counts[tuple(row.get(key, "UNKNOWN") or "UNKNOWN" for key in keys)] += 1
    result: list[dict[str, Any]] = []
    for key_tuple, count in counts.most_common():
        item = {key: value for key, value in zip(keys, key_tuple)}
        item["count"] = count
        result.append(item)
    return result


def _render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Phase 2 Shadow Fix Observer Live Report",
        "",
        f"Status: {payload['status']}",
        "",
        payload["authority"],
        "",
        f"Files dir: `{payload['files_dir']}`",
        f"File count: `{payload['file_count']}`",
        f"Rows: `{payload['row_count']}`",
        f"Signals: `{payload['signal_count']}`",
        f"Latest broker timestamp: `{payload['latest_row']}`",
        "",
        "## Signal Actions",
        "",
        _table(payload["signal_by_shadow_action"], ["shadow_action", "count"]),
        "",
        "## Signal Reasons",
        "",
        _table(payload["signal_by_shadow_reason"], ["shadow_reason", "count"]),
        "",
        "## Signal By Candidate",
        "",
        _table(payload["signal_by_candidate"], ["candidate", "count"]),
        "",
        "## Signal By Symbol",
        "",
        _table(payload["signal_by_symbol"], ["symbol", "count"]),
        "",
        "## Signal By Time Bucket",
        "",
        _table(payload["signal_by_time_bucket"], ["time_bucket", "count"]),
        "",
        "## Signal By Candidate x Symbol x Time",
        "",
        _table(payload["signal_by_candidate_symbol_time"], ["candidate", "symbol", "time_bucket", "count"]),
        "",
    ]
    return "\n".join(lines)


def _table(rows: list[dict[str, Any]], columns: list[str]) -> str:
    if not rows:
        return "_No rows yet._"
    lines = [
        "| " + " | ".join(columns) + " |",
        "| " + " | ".join("---" for _ in columns) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(str(row.get(column, "")) for column in columns) + " |")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a read-only report from shadow-fix observer logs.")
    parser.add_argument("--phase1-root", type=Path, default=Path("."))
    parser.add_argument("--files-dir", type=Path, default=DEFAULT_FILES_DIR)
    parser.add_argument("--output-json", type=Path, default=None)
    args = parser.parse_args()
    output = generate_phase2_shadow_fix_observer_report(args.phase1_root, args.files_dir, args.output_json)
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
