from __future__ import annotations

import argparse
import csv
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEFAULT_OUTPUT_JSON = Path("outputs") / "reports" / "OBSERVER_HEARTBEAT_REPORT.json"
DEFAULT_OUTPUT_MD = Path("outputs") / "reports" / "OBSERVER_HEARTBEAT_REPORT.md"


@dataclass(frozen=True)
class ObserverLane:
    name: str
    root: Path
    patterns: tuple[str, ...]
    expected_min_files: int
    warn_after_minutes: int = 15


DEFAULT_LANES = (
    ObserverLane(
        name="shadow_fix_observers",
        root=Path("C:/MT5PortableShadowFixObservers/MQL5/Files"),
        patterns=("shadow_fix_observer_signal_log_*.csv",),
        expected_min_files=14,
    ),
    ObserverLane(
        name="trend_guarded_fix_observers",
        root=Path("C:/MT5PortableTrendGuardedFixObservers/MQL5/Files"),
        patterns=("trend_guarded_fix_observer_v2_signal_log_*.csv",),
        expected_min_files=14,
    ),
    ObserverLane(
        name="position_path_observer",
        root=Path("C:/MT5PortablePositionPathObserver/MQL5/Files"),
        patterns=("position_path_log_*.csv", "position_path_summary.csv", "position_path_observer_startup.csv"),
        expected_min_files=3,
    ),
)


def generate_observer_heartbeat_report(
    phase1_root: Path,
    lanes: tuple[ObserverLane, ...] = DEFAULT_LANES,
    output_json: Path | None = None,
    now: datetime | None = None,
) -> Path:
    phase1_root = phase1_root.resolve()
    output_json = (output_json or phase1_root / DEFAULT_OUTPUT_JSON).resolve()
    output_md = output_json.with_suffix(".md") if output_json.name != DEFAULT_OUTPUT_JSON.name else phase1_root / DEFAULT_OUTPUT_MD
    output_json.parent.mkdir(parents=True, exist_ok=True)
    now = now or datetime.now(timezone.utc)

    lane_payloads = [_lane_payload(lane, now) for lane in lanes]
    status = _overall_status(lane_payloads)
    payload: dict[str, Any] = {
        "status": status,
        "created_at_utc": now.isoformat().replace("+00:00", "Z"),
        "authority": (
            "Read-only heartbeat report. It checks observer CSV freshness and row counts only; it does not touch "
            "MT5 terminals, charts, EA inputs, orders, or positions."
        ),
        "lanes": lane_payloads,
    }
    output_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    output_md.write_text(_render_markdown(payload), encoding="utf-8")
    return output_json


def _lane_payload(lane: ObserverLane, now: datetime) -> dict[str, Any]:
    files = _matching_files(lane)
    latest_mtime = max((path.stat().st_mtime for path in files), default=None)
    latest_age_minutes = None
    latest_file = "missing"
    if latest_mtime is not None:
        latest_dt = datetime.fromtimestamp(latest_mtime, tz=timezone.utc)
        latest_age_minutes = max(0.0, (now - latest_dt).total_seconds() / 60.0)
        latest_file = str(max(files, key=lambda path: path.stat().st_mtime))

    file_rows = [_file_payload(path, now) for path in files]
    checks = [
        {
            "name": "files_present",
            "status": "PASS" if len(files) >= lane.expected_min_files else "FAIL",
            "detail": f"{len(files)} files found, expected at least {lane.expected_min_files}",
        },
        {
            "name": "latest_file_fresh",
            "status": "PASS"
            if latest_age_minutes is not None and latest_age_minutes <= lane.warn_after_minutes
            else "WARN",
            "detail": "missing latest file"
            if latest_age_minutes is None
            else f"latest age {latest_age_minutes:.1f} minutes; threshold {lane.warn_after_minutes} minutes",
        },
    ]
    status = "FAIL" if any(check["status"] == "FAIL" for check in checks) else (
        "WARN" if any(check["status"] == "WARN" for check in checks) else "PASS"
    )
    return {
        "name": lane.name,
        "status": status,
        "root": str(lane.root),
        "patterns": list(lane.patterns),
        "expected_min_files": lane.expected_min_files,
        "warn_after_minutes": lane.warn_after_minutes,
        "file_count": len(files),
        "latest_file": latest_file,
        "latest_age_minutes": None if latest_age_minutes is None else round(latest_age_minutes, 2),
        "checks": checks,
        "files": file_rows,
    }


def _matching_files(lane: ObserverLane) -> list[Path]:
    if not lane.root.exists():
        return []
    files: list[Path] = []
    for pattern in lane.patterns:
        files.extend(lane.root.glob(pattern))
    return sorted({path.resolve() for path in files if path.is_file()})


def _file_payload(path: Path, now: datetime) -> dict[str, Any]:
    mtime = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
    return {
        "name": path.name,
        "path": str(path),
        "bytes": path.stat().st_size,
        "mtime_utc": mtime.isoformat().replace("+00:00", "Z"),
        "age_minutes": round(max(0.0, (now - mtime).total_seconds() / 60.0), 2),
        "row_count": _csv_row_count(path),
    }


def _csv_row_count(path: Path) -> int:
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            return sum(1 for _ in csv.DictReader(handle))
    except (OSError, UnicodeError, csv.Error):
        return 0


def _overall_status(lanes: list[dict[str, Any]]) -> str:
    if any(lane["status"] == "FAIL" for lane in lanes):
        return "FAIL"
    if any(lane["status"] == "WARN" for lane in lanes):
        return "WARN"
    return "PASS"


def _render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Observer Heartbeat Report",
        "",
        f"Status: `{payload['status']}`",
        "",
        payload["authority"],
        "",
        f"Generated at UTC: `{payload['created_at_utc']}`",
        "",
        "## Lanes",
        "",
        "| Lane | Status | Files | Latest age min | Latest file |",
        "| --- | --- | ---: | ---: | --- |",
    ]
    for lane in payload["lanes"]:
        lines.append(
            f"| {lane['name']} | {lane['status']} | {lane['file_count']} | "
            f"{lane.get('latest_age_minutes')} | `{Path(str(lane['latest_file'])).name}` |"
        )
    lines.extend(["", "## Checks", ""])
    for lane in payload["lanes"]:
        lines.extend([f"### {lane['name']}", "", "| Check | Status | Detail |", "| --- | --- | --- |"])
        for check in lane["checks"]:
            lines.append(f"| {check['name']} | {check['status']} | {check['detail']} |")
        lines.append("")
    lines.extend(
        [
            "## Boundary",
            "",
            "- This report is monitoring-only.",
            "- It does not restart terminals.",
            "- It does not attach or remove EAs.",
            "- It does not modify running demo EAs, orders, positions, presets, profiles, or charts.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a read-only heartbeat report for observer CSV logs.")
    parser.add_argument("--phase1-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output-json", type=Path, default=None)
    args = parser.parse_args()
    output = generate_observer_heartbeat_report(args.phase1_root, output_json=args.output_json)
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
