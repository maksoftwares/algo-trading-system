from __future__ import annotations

import argparse
import csv
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


DEFAULT_FILES_DIR = Path(
    "C:/Users/ZHAO ZHU INFORMATION/AppData/Roaming/MetaQuotes/Terminal/D0E8209F77C8CF37AD8BF550E51FF075/MQL5/Files"
)
DEFAULT_OUTPUT = Path("outputs") / "paper_observer" / "passive_cost_observer_log.csv"
DEFAULT_REPORT = Path("outputs") / "reports" / "PHASE2B_PASSIVE_OBSERVER_IMPORT_REPORT.md"
DEFAULT_JSON = Path("outputs") / "reports" / "PHASE2B_PASSIVE_OBSERVER_IMPORT_REPORT.json"
DEFAULT_BASELINE_GROSS_EDGE_R = 0.5116

OUTPUT_COLUMNS = (
    "timestamp_utc",
    "timestamp_broker",
    "symbol",
    "candidate",
    "candidate_family",
    "candidate_status",
    "would_signal",
    "signal_direction",
    "signal_stage",
    "intended_entry_price",
    "intended_stop_loss",
    "intended_take_profit",
    "stop_distance_points",
    "stop_distance_price",
    "bid",
    "ask",
    "spread_points",
    "spread_price",
    "point_size",
    "digits",
    "estimated_entry_spread_R",
    "estimated_slippage_R",
    "estimated_total_cost_R",
    "estimated_gross_edge_R",
    "estimated_net_edge_R",
    "cost_gate_status",
    "session_label",
    "hour_utc",
    "is_rollover_window",
    "tick_fresh",
    "seconds_since_tick",
    "server_time_status",
    "reason_blocked",
    "source_file",
    "source_kind",
)


@dataclass(frozen=True)
class ImportOutput:
    status: str
    output_path: Path
    report_path: Path
    json_path: Path
    source_files: int
    imported_rows: int
    unique_events: int


def import_phase2b_passive_observer_logs(
    root: Path,
    files_dir: Path = DEFAULT_FILES_DIR,
    output_path: Path | None = None,
    report_path: Path | None = None,
    json_path: Path | None = None,
    baseline_gross_edge_r: float = DEFAULT_BASELINE_GROSS_EDGE_R,
) -> ImportOutput:
    root = root.resolve()
    files_dir = files_dir.resolve()
    output_path = (root / DEFAULT_OUTPUT if output_path is None else output_path).resolve()
    report_path = (root / DEFAULT_REPORT if report_path is None else report_path).resolve()
    json_path = (root / DEFAULT_JSON if json_path is None else json_path).resolve()

    source_files = sorted(files_dir.glob("experimental_demo_attachment_log*.csv")) if files_dir.exists() else []
    imported = _import_rows(source_files, baseline_gross_edge_r)
    unique_events = len({_event_key(row) for row in imported})
    status = "IMPORTED" if imported else "NO_PASSIVE_SIGNALS_FOUND"

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=OUTPUT_COLUMNS)
        writer.writeheader()
        writer.writerows(imported)

    payload = {
        "status": status,
        "created_at_utc": _now(),
        "files_dir": str(files_dir),
        "output_path": str(output_path),
        "source_files": len(source_files),
        "imported_rows": len(imported),
        "unique_events": unique_events,
        "passive_attachment_logs_used": True,
        "experimental_demo_order_logs_used": False,
        "experimental_demo_executor_signal_logs_used": False,
        "canonical_phase2_authorized": False,
        "paper_mode_execution_allowed": False,
        "baseline_gross_edge_R": baseline_gross_edge_r,
        "source_pattern": "experimental_demo_attachment_log*.csv",
    }
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    report_path.write_text(_render_report(payload), encoding="utf-8")
    return ImportOutput(status, output_path, report_path, json_path, len(source_files), len(imported), unique_events)


def _import_rows(source_files: list[Path], baseline_gross_edge_r: float) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    seen: set[str] = set()
    for source_file in source_files:
        with source_file.open("r", encoding="utf-8", errors="replace", newline="") as handle:
            for row in csv.DictReader(handle):
                if not _is_eligible_passive_signal(row):
                    continue
                mapped = _map_row(row, source_file.name, baseline_gross_edge_r)
                event_key = _event_key(mapped)
                if event_key in seen:
                    continue
                seen.add(event_key)
                rows.append(mapped)
    rows.sort(key=lambda item: (item["timestamp_utc"], item["candidate"], item["symbol"]))
    return rows


def _is_eligible_passive_signal(row: dict[str, str]) -> bool:
    return (
        _bool(row.get("dry_run"))
        and not _bool(row.get("broker_action_allowed"))
        and _bool(row.get("observer_supported"))
        and _bool(row.get("would_signal"))
        and _float(row.get("stop_distance_points")) > 0.0
    )


def _map_row(row: dict[str, str], source_file: str, baseline_gross_edge_r: float) -> dict[str, str]:
    entry = _float(row.get("entry_price"))
    stop = _float(row.get("stop_loss"))
    stop_points = _float(row.get("stop_distance_points"))
    spread_points = _float(row.get("spread_points"))
    point_size = abs(entry - stop) / stop_points if stop_points > 0 else 0.0
    spread_price = spread_points * point_size
    entry_spread_r = spread_points / stop_points if stop_points > 0 else 0.0
    slippage_r = 0.0
    total_cost_r = entry_spread_r + slippage_r
    net_edge_r = baseline_gross_edge_r - total_cost_r
    timestamp_utc = _normalize_time(row.get("timestamp_utc", ""))
    hour = _hour(timestamp_utc)
    return {
        "timestamp_utc": timestamp_utc,
        "timestamp_broker": _normalize_time(row.get("timestamp_broker", "")),
        "symbol": row.get("symbol", ""),
        "candidate": row.get("candidate", ""),
        "candidate_family": "breakout_retest_family",
        "candidate_status": row.get("candidate_status", ""),
        "would_signal": "true",
        "signal_direction": row.get("direction", ""),
        "signal_stage": row.get("stage", ""),
        "intended_entry_price": row.get("entry_price", ""),
        "intended_stop_loss": row.get("stop_loss", ""),
        "intended_take_profit": row.get("take_profit", ""),
        "stop_distance_points": _fmt(stop_points),
        "stop_distance_price": _fmt(abs(entry - stop)),
        "bid": row.get("bid", ""),
        "ask": row.get("ask", ""),
        "spread_points": _fmt(spread_points),
        "spread_price": _fmt(spread_price),
        "point_size": _fmt(point_size, precision=8),
        "digits": str(_digits(row.get("entry_price", ""))),
        "estimated_entry_spread_R": _fmt(entry_spread_r),
        "estimated_slippage_R": _fmt(slippage_r),
        "estimated_total_cost_R": _fmt(total_cost_r),
        "estimated_gross_edge_R": _fmt(baseline_gross_edge_r),
        "estimated_net_edge_R": _fmt(net_edge_r),
        "cost_gate_status": _cost_gate(total_cost_r),
        "session_label": _session_label(hour),
        "hour_utc": "" if hour is None else str(hour),
        "is_rollover_window": "true" if hour is not None and (hour >= 21 or hour < 1) else "false",
        "tick_fresh": "true",
        "seconds_since_tick": "0",
        "server_time_status": "PASSIVE_OBSERVER_IMPORTED",
        "reason_blocked": "",
        "source_file": source_file,
        "source_kind": "passive_demo_observer_attachment_log",
    }


def _event_key(row: dict[str, str]) -> str:
    return "|".join(
        [
            row.get("timestamp_utc", ""),
            row.get("candidate_family", ""),
            row.get("candidate", ""),
            row.get("symbol", ""),
            row.get("signal_direction", ""),
            row.get("intended_entry_price", ""),
            row.get("intended_stop_loss", ""),
        ]
    )


def _bool(value: str | None) -> bool:
    return str(value or "").strip().lower() == "true"


def _float(value: str | None) -> float:
    try:
        return float(str(value or "").strip())
    except ValueError:
        return 0.0


def _fmt(value: float, precision: int = 4) -> str:
    return f"{value:.{precision}f}"


def _digits(value: str) -> int:
    text = str(value)
    return len(text.split(".", 1)[1]) if "." in text else 0


def _normalize_time(value: str) -> str:
    value = str(value or "").strip()
    if not value:
        return ""
    return value.replace(".", "-", 2)


def _hour(timestamp: str) -> int | None:
    if not timestamp:
        return None
    try:
        return int(timestamp.split(" ", 1)[1].split(":", 1)[0])
    except (IndexError, ValueError):
        return None


def _session_label(hour: int | None) -> str:
    if hour is None:
        return "UNKNOWN"
    if 0 <= hour < 7:
        return "ASIA"
    if 7 <= hour < 13:
        return "LONDON"
    if 13 <= hour < 21:
        return "NEW_YORK"
    return "ROLLOVER"


def _cost_gate(total_cost_r: float) -> str:
    if total_cost_r <= 0.15:
        return "COST_OK_STRONG"
    if total_cost_r <= 0.20:
        return "COST_OK_ACCEPTABLE"
    if total_cost_r <= 0.30:
        return "COST_WARN"
    return "COST_BLOCK"


def _render_report(payload: dict[str, object]) -> str:
    rows = [
        ("Status", payload["status"]),
        ("Source Files directory", payload["files_dir"]),
        ("Source files", payload["source_files"]),
        ("Imported rows", payload["imported_rows"]),
        ("Unique events", payload["unique_events"]),
        ("Output path", payload["output_path"]),
        ("Passive attachment logs used", str(payload["passive_attachment_logs_used"]).lower()),
        ("Experimental demo order logs used", str(payload["experimental_demo_order_logs_used"]).lower()),
        ("Experimental executor signal logs used", str(payload["experimental_demo_executor_signal_logs_used"]).lower()),
        ("Canonical Phase 2 authorized", str(payload["canonical_phase2_authorized"]).lower()),
        ("Paper-mode execution allowed", str(payload["paper_mode_execution_allowed"]).lower()),
        ("Baseline gross edge R", payload["baseline_gross_edge_R"]),
    ]
    return "\n".join(
        [
            "# Phase 2B Passive Observer Import Report",
            "",
            f"Overall status: {payload['status']}",
            "",
            "This importer converts passive demo observer attachment logs into the Phase 2B passive observer CSV. It deliberately ignores experimental demo order logs and experimental executor signal logs.",
            "",
            "| Field | Value |",
            "| --- | --- |",
            *[f"| {key} | {_escape(str(value))} |" for key, value in rows],
            "",
            "## Boundary",
            "",
            "A successful import starts Phase 2B evidence collection. It does not authorize canonical Phase 2, demo execution as Phase 2 evidence, paper-mode execution, broker-side execution, or live trading.",
            "",
        ]
    )


def _escape(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", "<br>")


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Import passive demo observer logs into the Phase 2B passive observer CSV.")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--files-dir", type=Path, default=DEFAULT_FILES_DIR)
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument("--baseline-gross-edge-r", type=float, default=DEFAULT_BASELINE_GROSS_EDGE_R)
    args = parser.parse_args(argv)

    output = import_phase2b_passive_observer_logs(
        root=args.root,
        files_dir=args.files_dir,
        output_path=args.output,
        baseline_gross_edge_r=args.baseline_gross_edge_r,
    )
    print(f"Phase 2B passive observer import: {output.status}")
    print(f"Source files: {output.source_files}; imported rows: {output.imported_rows}; unique events: {output.unique_events}")
    print(output.output_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
