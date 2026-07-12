"""Read-only NP1-D1 forensics for the stopped NP1-C native packet.

The raw packet must already exist below ``raw_packet``.  This module verifies
every raw byte against the stopped packet's inner manifest before it writes any
derived diagnostic output.  It never invokes MT5 and never writes below
``raw_packet``.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import html
import json
import re
from collections import Counter
from datetime import datetime, timedelta
from html.parser import HTMLParser
from pathlib import Path
from typing import Any, Iterable, Sequence


EXPECTED_INNER_MANIFEST_SHA256 = "8479fb5dc17ceb1888521fe91344e636c02eac9d756a2dc99ea8d5d72714069c"
EXPECTED_STATUS = "R6_NP1_EVIDENCE_INVALID"
STATUS_FILE = "A1_XAU_R6_MARKET_ONLY_NATIVE_PARITY_EXACT_20260712.json"
TIMEFRAMES = {"H1": 3600, "H4": 14400, "D1": 86400}
BAR_COLUMNS = (
    "schema_version", "timeframe", "open_time_broker", "open", "high", "low", "close",
    "tick_volume", "spread", "real_volume",
)
VALUE_COLUMNS = ("open", "high", "low", "close", "tick_volume", "spread", "real_volume")
OHLC_COLUMNS = ("open", "high", "low", "close")
METADATA_COLUMNS = ("tick_volume", "spread", "real_volume")


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"JSON root must be an object: {path}")
    return value


def _json_bytes(value: Any) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(_json_bytes(value))


def write_csv(path: Path, columns: Sequence[str], rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(columns), lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({column: row.get(column, "") for column in columns})


def verify_nonrecursive_manifest(root: Path, expected_sha256: str | None = None) -> dict[str, Any]:
    """Verify an artifact manifest that excludes only its own pair."""
    manifest_path, sidecar_path = root / "manifest.json", root / "manifest.sha256"
    if not manifest_path.is_file() or not sidecar_path.is_file():
        raise ValueError("manifest pair missing")
    actual_manifest_sha = sha256_file(manifest_path)
    sidecar = sidecar_path.read_text(encoding="ascii").strip().split()
    if sidecar != [actual_manifest_sha]:
        raise ValueError("manifest.sha256 mismatch")
    if expected_sha256 is not None and actual_manifest_sha != expected_sha256:
        raise ValueError("raw packet manifest SHA256 mismatch")
    payload = read_json(manifest_path)
    artifacts = payload.get("artifacts")
    if not isinstance(artifacts, list):
        raise ValueError("manifest artifacts must be a list")
    listed: set[str] = set()
    for item in artifacts:
        if not isinstance(item, dict):
            raise ValueError("manifest artifact must be an object")
        relative = item.get("relative_path")
        if not isinstance(relative, str) or not relative or "\\" in relative:
            raise ValueError("invalid manifest relative path")
        candidate = Path(relative)
        if candidate.is_absolute() or ".." in candidate.parts or relative in listed:
            raise ValueError("unsafe or duplicate manifest relative path")
        if relative in {"manifest.json", "manifest.sha256"}:
            raise ValueError("manifest must exclude its own pair")
        listed.add(relative)
        path = root / candidate
        if not path.is_file():
            raise ValueError(f"manifest artifact missing: {relative}")
        if path.stat().st_size != item.get("size_bytes") or sha256_file(path) != item.get("sha256"):
            raise ValueError(f"manifest artifact mismatch: {relative}")
    actual = {
        path.relative_to(root).as_posix()
        for path in root.rglob("*") if path.is_file()
    } - {"manifest.json", "manifest.sha256"}
    if actual != listed:
        missing = sorted(listed - actual)
        extra = sorted(actual - listed)
        raise ValueError(f"manifest tree mismatch: missing={missing} extra={extra}")
    return payload


def verify_raw_packet(raw_packet: Path) -> dict[str, Any]:
    verify_nonrecursive_manifest(raw_packet, EXPECTED_INNER_MANIFEST_SHA256)
    status = read_json(raw_packet / STATUS_FILE)
    if status.get("status") != EXPECTED_STATUS:
        raise ValueError("raw packet terminal status mismatch")
    boundary = status.get("boundary")
    expected_boundary = {"census_generated": False, "pnl_calculated": False, "broker_action": False}
    if boundary != expected_boundary:
        raise ValueError("raw packet zero-result/broker-action boundary violation")
    errors = status.get("errors")
    if not isinstance(errors, dict) or errors.get("source") != [] or errors.get("zero_action") != []:
        raise ValueError("raw packet source-equivalence or zero-action errors present")
    return status


class _Mt5CellParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.cells: list[str] = []
        self._depth = 0
        self._parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() == "td":
            self._depth, self._parts = 1, []
        elif self._depth:
            self._depth += 1

    def handle_endtag(self, tag: str) -> None:
        if not self._depth:
            return
        self._depth -= 1
        if tag.lower() == "td" and self._depth == 0:
            self.cells.append(" ".join("".join(self._parts).split()))

    def handle_data(self, data: str) -> None:
        if self._depth:
            self._parts.append(data)


def _decode_text(path: Path) -> str:
    raw = path.read_bytes()
    if raw.startswith((b"\xff\xfe", b"\xfe\xff")):
        return raw.decode("utf-16")
    return raw.decode("utf-8-sig", errors="strict")


def parse_native_report(path: Path) -> dict[str, Any]:
    text = _decode_text(path)
    parser = _Mt5CellParser()
    parser.feed(text)
    fields: dict[str, list[str]] = {}
    for index, cell in enumerate(parser.cells[:-1]):
        if cell.endswith(":") and cell[:-1]:
            fields.setdefault(cell[:-1], []).append(parser.cells[index + 1])

    def field(label: str) -> str:
        values = fields.get(label, [])
        if len(values) != 1:
            raise ValueError(f"native report requires exactly one {label} field")
        return values[0]

    def integer(label: str) -> int:
        match = re.search(r"[0-9][0-9,\s]*", field(label))
        if match is None:
            raise ValueError(f"native report invalid {label}")
        return int(re.sub(r"[\s,]", "", match.group(0)))

    return {
        "period": field("Period"), "bars": integer("Bars"), "ticks": integer("Ticks"),
        "total_trades": integer("Total Trades"), "total_deals": integer("Total Deals"),
    }


def _read_bars(path: Path, timeframe: str) -> tuple[list[dict[str, str]], dict[str, dict[str, str]]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if tuple(reader.fieldnames or ()) != BAR_COLUMNS:
            raise ValueError(f"bar TSV header mismatch: {path}")
        rows = list(reader)
    indexed: dict[str, dict[str, str]] = {}
    previous: datetime | None = None
    for row in rows:
        if row["timeframe"] != timeframe:
            raise ValueError(f"bar timeframe mismatch: {path}")
        timestamp = row["open_time_broker"]
        try:
            current = datetime.fromisoformat(timestamp)
        except ValueError as exc:
            raise ValueError(f"invalid bar timestamp: {timestamp}") from exc
        if timestamp in indexed:
            raise ValueError(f"duplicate bar timestamp: {path}: {timestamp}")
        if previous is not None and current <= previous:
            raise ValueError(f"bar timestamps not strictly increasing: {path}")
        indexed[timestamp] = row
        previous = current
    if not rows:
        raise ValueError(f"empty bar file: {path}")
    return rows, indexed


def _bool(value: bool) -> str:
    return "true" if value else "false"


def _gap_rows(timeframe: str, rows_by_run: dict[str, list[dict[str, str]]]) -> list[dict[str, Any]]:
    step = TIMEFRAMES[timeframe]
    gaps: dict[tuple[str, str], dict[str, Any]] = {}
    patterns: Counter[tuple[int, int, int, int, int]] = Counter()
    for run_id, rows in rows_by_run.items():
        for prior_row, next_row in zip(rows, rows[1:]):
            prior = datetime.fromisoformat(prior_row["open_time_broker"])
            nxt = datetime.fromisoformat(next_row["open_time_broker"])
            duration = int((nxt - prior).total_seconds())
            if duration <= step:
                continue
            pattern = (duration, prior.weekday(), prior.hour, nxt.weekday(), nxt.hour)
            patterns[pattern] += 1
            key = (prior.isoformat(), nxt.isoformat())
            item = gaps.setdefault(key, {
                "timeframe": timeframe, "prior_bar_time": prior.isoformat(),
                "next_bar_time": nxt.isoformat(), "duration_seconds": duration,
                "prior_weekday": prior.weekday(), "prior_hour": prior.hour,
                "next_weekday": nxt.weekday(), "next_hour": nxt.hour,
                "_pattern": pattern, "present_in_run1": False, "present_in_run2": False,
            })
            item[f"present_in_{run_id}"] = True
    result: list[dict[str, Any]] = []
    for item in sorted(gaps.values(), key=lambda value: (value["prior_bar_time"], value["next_bar_time"])):
        pattern = item.pop("_pattern")
        item["occurrence_count"] = patterns[pattern]
        item["present_in_run1"] = _bool(bool(item["present_in_run1"]))
        item["present_in_run2"] = _bool(bool(item["present_in_run2"]))
        result.append(item)
    return result


def analyze_packet(raw_packet: Path) -> dict[str, Any]:
    status = verify_raw_packet(raw_packet)
    file_hash_rows: list[dict[str, Any]] = []
    row_summary_rows: list[dict[str, Any]] = []
    timestamp_diff_rows: list[dict[str, Any]] = []
    common_diff_rows: list[dict[str, Any]] = []
    first_last_rows: list[dict[str, Any]] = []
    gap_rows: list[dict[str, Any]] = []
    per_timeframe: dict[str, Any] = {}
    all_difference_times: list[datetime] = []
    any_ohlc_drift = False
    any_metadata_drift = False
    all_files_identical = True

    for timeframe in TIMEFRAMES:
        lower = timeframe.lower()
        paths = {
            run: raw_packet / "runs" / run / f"native_{lower}_bars.tsv"
            for run in ("run1", "run2")
        }
        rows1, index1 = _read_bars(paths["run1"], timeframe)
        rows2, index2 = _read_bars(paths["run2"], timeframe)
        hashes = {run: sha256_file(path) for run, path in paths.items()}
        identical = hashes["run1"] == hashes["run2"]
        all_files_identical &= identical
        file_hash_rows.append({"timeframe": timeframe, "run1_sha256": hashes["run1"], "run2_sha256": hashes["run2"], "identical": _bool(identical)})
        for run, rows in (("run1", rows1), ("run2", rows2)):
            row_summary_rows.append({
                "timeframe": timeframe, "run": run, "row_count": len(rows),
                "first_timestamp": rows[0]["open_time_broker"], "last_timestamp": rows[-1]["open_time_broker"],
            })
        keys1, keys2 = set(index1), set(index2)
        only1, only2, common = sorted(keys1 - keys2), sorted(keys2 - keys1), sorted(keys1 & keys2)
        for side, values in (("run1_only", only1), ("run2_only", only2)):
            timestamp_diff_rows.extend({"timeframe": timeframe, "side": side, "timestamp": value} for value in values)
        changed_counts = Counter({column: 0 for column in VALUE_COLUMNS})
        differing_common: list[str] = []
        for timestamp in common:
            changed = [column for column in VALUE_COLUMNS if index1[timestamp][column] != index2[timestamp][column]]
            if not changed:
                continue
            differing_common.append(timestamp)
            for column in changed:
                changed_counts[column] += 1
            any_ohlc_drift |= any(column in OHLC_COLUMNS for column in changed)
            any_metadata_drift |= any(column in METADATA_COLUMNS for column in changed)
            common_diff_rows.append({
                "timeframe": timeframe, "timestamp": timestamp, "changed_fields": ";".join(changed),
                **{f"run1_{column}": index1[timestamp][column] for column in VALUE_COLUMNS},
                **{f"run2_{column}": index2[timestamp][column] for column in VALUE_COLUMNS},
            })
        difference_times = [datetime.fromisoformat(value) for value in (*only1, *only2, *differing_common)]
        all_difference_times.extend(difference_times)
        first_difference = min(difference_times).isoformat() if difference_times else ""
        last_difference = max(difference_times).isoformat() if difference_times else ""
        first_last_rows.append({
            "timeframe": timeframe, "first_difference": first_difference,
            "last_difference": last_difference, "difference_timestamp_count": len(set((*only1, *only2, *differing_common))),
        })
        run2_superset = keys1 < keys2
        run1_superset = keys2 < keys1
        per_timeframe[timeframe] = {
            "run1_sha256": hashes["run1"], "run2_sha256": hashes["run2"],
            "run1_row_count": len(rows1), "run2_row_count": len(rows2),
            "timestamps_only_in_run1": len(only1), "timestamps_only_in_run2": len(only2),
            "common_timestamps": len(common), "duplicate_timestamps": 0,
            "first_differing_timestamp": first_difference, "last_differing_timestamp": last_difference,
            "changed_common_timestamp_count": len(differing_common),
            "changed_field_counts": dict(changed_counts),
            "run2_timestamp_strict_superset": run2_superset,
            "run1_timestamp_strict_superset": run1_superset,
            "common_timestamp_ohlc_identical": not any(changed_counts[column] for column in OHLC_COLUMNS),
            "common_timestamp_metadata_identical": not any(changed_counts[column] for column in METADATA_COLUMNS),
            "run_files_identical": identical,
        }
        gap_rows.extend(_gap_rows(timeframe, {"run1": rows1, "run2": rows2}))

    reports = {
        run: parse_native_report(raw_packet / "runs" / run / "native_report.htm")
        for run in ("run1", "run2")
    }
    ex5_sha = sha256_file(raw_packet / "compiled" / "A1XauR6MarketOnlyNativeParityOracle.ex5")
    source_equivalence = read_json(raw_packet / "compiled" / "source_equivalence.json")
    report_comparison = {
        "run1": reports["run1"], "run2": reports["run2"],
        "tick_delta_run2_minus_run1": reports["run2"]["ticks"] - reports["run1"]["ticks"],
        "bars_delta_run2_minus_run1": reports["run2"]["bars"] - reports["run1"]["bars"],
        "ex5_sha256": ex5_sha,
        "source_equivalence_status": "PASS" if all(row.get("exact_equal") is True for row in source_equivalence.get("blocks", [])) else "FAIL",
    }
    flags: list[str] = []
    if any(value["run2_timestamp_strict_superset"] for value in per_timeframe.values()):
        flags.append("RUN2_TIMESTAMP_STRICT_SUPERSET")
    if any(value["run1_timestamp_strict_superset"] for value in per_timeframe.values()):
        flags.append("RUN1_TIMESTAMP_STRICT_SUPERSET")
    if any_ohlc_drift:
        flags.append("COMMON_TIMESTAMP_OHLC_DRIFT")
    if any_metadata_drift:
        flags.append("COMMON_TIMESTAMP_VOLUME_OR_SPREAD_DRIFT")
    if all_difference_times:
        latest_history = max(
            datetime.fromisoformat(value["last_timestamp"])
            for value in row_summary_rows
        )
        if min(all_difference_times) >= latest_history.replace(tzinfo=None) - timedelta(days=30):
            flags.append("DIFFERENCES_LOCALIZED_NEAR_END")
        if (max(all_difference_times) - min(all_difference_times)).days >= 365:
            flags.append("DIFFERENCES_SPAN_HISTORY")
    if all_files_identical:
        flags.append("RUN_FILES_IDENTICAL")
    return {
        "status": "NP1_D1_DIAGNOSTIC_COMPLETE",
        "source_packet_terminal_status": status["status"],
        "source_packet_manifest_sha256": EXPECTED_INNER_MANIFEST_SHA256,
        "boundary": status["boundary"],
        "native_report_comparison": report_comparison,
        "per_timeframe": per_timeframe,
        "stability_flags": flags,
        "_tables": {
            "file_hashes": file_hash_rows, "row_summary": row_summary_rows,
            "timestamp_diff": timestamp_diff_rows, "common_diff": common_diff_rows,
            "first_last": first_last_rows, "gaps": gap_rows,
        },
    }


def _outer_manifest(root: Path) -> dict[str, Any]:
    artifacts = []
    for path in sorted((path for path in root.rglob("*") if path.is_file()), key=lambda item: item.relative_to(root).as_posix()):
        relative = path.relative_to(root).as_posix()
        if relative in {"manifest.json", "manifest.sha256"}:
            continue
        artifacts.append({"relative_path": relative, "sha256": sha256_file(path), "size_bytes": path.stat().st_size})
    return {"schema_version": "a1_xau_r6_np1c_stop_diagnostic_manifest_v1", "artifacts": artifacts}


def build_diagnostic(diagnostic_root: Path) -> dict[str, Any]:
    raw_packet = diagnostic_root / "raw_packet"
    if not raw_packet.is_dir():
        raise ValueError("raw_packet directory missing")
    analysis = analyze_packet(raw_packet)
    tables = analysis.pop("_tables")
    analysis_dir = diagnostic_root / "analysis"
    analysis_dir.mkdir(parents=True, exist_ok=True)
    write_json(analysis_dir / "native_report_comparison.json", analysis["native_report_comparison"])
    write_csv(analysis_dir / "bar_file_hashes.csv", ("timeframe", "run1_sha256", "run2_sha256", "identical"), tables["file_hashes"])
    write_csv(analysis_dir / "bar_row_count_summary.csv", ("timeframe", "run", "row_count", "first_timestamp", "last_timestamp"), tables["row_summary"])
    write_csv(analysis_dir / "bar_timestamp_set_diff.csv", ("timeframe", "side", "timestamp"), tables["timestamp_diff"])
    common_columns = ("timeframe", "timestamp", "changed_fields", *(f"run1_{column}" for column in VALUE_COLUMNS), *(f"run2_{column}" for column in VALUE_COLUMNS))
    write_csv(analysis_dir / "bar_common_timestamp_value_diff.csv", common_columns, tables["common_diff"])
    write_csv(analysis_dir / "bar_first_last_difference.csv", ("timeframe", "first_difference", "last_difference", "difference_timestamp_count"), tables["first_last"])
    write_csv(analysis_dir / "market_gap_inventory.csv", (
        "timeframe", "prior_bar_time", "next_bar_time", "duration_seconds", "prior_weekday", "prior_hour",
        "next_weekday", "next_hour", "occurrence_count", "present_in_run1", "present_in_run2",
    ), tables["gaps"])
    stability = {"schema_version": "a1_xau_r6_np1d1_history_stability_v1", "stability_flags": analysis["stability_flags"], "per_timeframe": analysis["per_timeframe"]}
    write_json(analysis_dir / "two_run_stability_classification.json", stability)
    result = {"schema_version": "a1_xau_r6_np1c_stop_diagnostic_result_v1", **analysis}
    write_json(diagnostic_root / "result.json", result)
    readme = (
        "# A1 XAU R6 NP1-C Stop Diagnostic\n\n"
        "This packet preserves the stopped NP1-C packet byte-for-byte under `raw_packet/` and records only read-only market-history forensics.\n\n"
        f"- Source terminal status: `{EXPECTED_STATUS}`\n"
        f"- Source manifest SHA256: `{EXPECTED_INNER_MANIFEST_SHA256}`\n"
        "- MT5 rerun: `NOT AUTHORIZED / NOT PERFORMED`\n"
        "- Census, P/L, broker action: `NOT PERFORMED`\n"
        f"- Stability flags: `{', '.join(result['stability_flags']) or 'NONE'}`\n"
    )
    (diagnostic_root / "README.md").write_text(readme, encoding="utf-8", newline="\n")
    manifest = _outer_manifest(diagnostic_root)
    write_json(diagnostic_root / "manifest.json", manifest)
    (diagnostic_root / "manifest.sha256").write_text(sha256_file(diagnostic_root / "manifest.json") + "\n", encoding="ascii", newline="\n")
    verify_nonrecursive_manifest(diagnostic_root)
    return result


def _main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("diagnostic_root", type=Path)
    parser.add_argument("--verify-only", action="store_true")
    args = parser.parse_args()
    if args.verify_only:
        verify_nonrecursive_manifest(args.diagnostic_root)
        verify_raw_packet(args.diagnostic_root / "raw_packet")
        return 0
    result = build_diagnostic(args.diagnostic_root)
    print(json.dumps({"status": result["status"], "stability_flags": result["stability_flags"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
