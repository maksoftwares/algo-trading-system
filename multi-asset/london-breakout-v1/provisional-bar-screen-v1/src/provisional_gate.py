from __future__ import annotations

import csv
from datetime import datetime, timedelta, timezone
import hashlib
import json
import math
from pathlib import Path
from typing import Any


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def portable(path: Path, repo_root: Path) -> str:
    return path.relative_to(repo_root).as_posix()


def parse_timestamp(row: list[str]) -> datetime:
    return datetime.strptime(f"{row[0]} {row[1]}", "%Y.%m.%d %H:%M:%S").replace(tzinfo=timezone.utc)


def inspect_file(path: Path, repo_root: Path, required_start: datetime, required_last_open: datetime,
                 timeframe: str, point: float | None, digits: int | None) -> dict[str, Any]:
    expected = ["<DATE>", "<TIME>", "<OPEN>", "<HIGH>", "<LOW>", "<CLOSE>", "<TICKVOL>", "<SPREAD>"]
    duration = {"H1": 3600, "M15": 900, "M5": 300}[timeframe]
    row_count = duplicates = decreasing = invalid_prices = negative_spreads = nonfinite_spreads = 0
    off_grid_intervals = 0
    maximum_gap_seconds = 0
    first_time = last_time = previous = None
    seen: set[datetime] = set()
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.reader(handle)
        header = next(reader)
        missing = len(set(expected) - {value.strip().upper() for value in header})
        for row in reader:
            if not row:
                continue
            row_count += 1
            timestamp = parse_timestamp(row)
            if first_time is None:
                first_time = timestamp
            if timestamp in seen:
                duplicates += 1
            seen.add(timestamp)
            if previous is not None:
                delta = int((timestamp - previous).total_seconds())
                if delta < 0:
                    decreasing += 1
                elif delta > 0:
                    maximum_gap_seconds = max(maximum_gap_seconds, delta)
                    if delta % duration:
                        off_grid_intervals += 1
            previous = last_time = timestamp
            try:
                o, h, low, close = map(float, row[2:6])
                if not all(math.isfinite(v) and v > 0 for v in (o, h, low, close)) or h < max(o, low, close) or low > min(o, h, close):
                    invalid_prices += 1
            except (ValueError, IndexError):
                invalid_prices += 1
            try:
                spread = float(row[7])
                if not math.isfinite(spread):
                    nonfinite_spreads += 1
                elif spread < 0:
                    negative_spreads += 1
            except (ValueError, IndexError):
                nonfinite_spreads += 1
    point_digits_valid = point is not None and digits is not None and math.isclose(point, 10 ** (-digits), rel_tol=0, abs_tol=1e-12)
    assert first_time is not None and last_time is not None
    return {
        "path": portable(path, repo_root), "size_bytes": path.stat().st_size, "sha256": sha256_file(path),
        "timeframe": timeframe, "header": header, "row_count": row_count,
        "first_timestamp_utc": first_time.isoformat().replace("+00:00", "Z"),
        "final_timestamp_utc": last_time.isoformat().replace("+00:00", "Z"),
        "timestamp_contract": "BAR_OPEN_UTC_FROM_COMMITTED_EXPORTER",
        "nominal_bar_duration_seconds": duration, "maximum_observed_gap_seconds": maximum_gap_seconds,
        "off_grid_interval_count": off_grid_intervals, "duplicate_timestamp_count": duplicates,
        "decreasing_timestamp_count": decreasing, "invalid_price_count": invalid_prices,
        "missing_required_column_count": missing, "negative_spread_count": negative_spreads,
        "nonfinite_or_missing_spread_count": nonfinite_spreads, "quote_basis": "UNKNOWN",
        "spread_units": "MQLRATES_SPREAD_FIELD_REPORTED_AS_POINTS_NOT_INDEPENDENTLY_DOCUMENTED_IN_REPOSITORY",
        "point_size": point, "digits": digits, "point_digits_consistent": point_digits_valid,
        "starts_on_or_before_required_start": first_time <= required_start,
        "ends_on_or_after_required_last_open": last_time >= required_last_open,
    }


def inspect_inventory(repo_root: Path, lane_root: Path, config: dict[str, Any]) -> list[dict[str, Any]]:
    required_start = datetime.fromisoformat(config["required_start"].replace("Z", "+00:00"))
    required_end = datetime.fromisoformat(config["required_end_exclusive"].replace("Z", "+00:00"))
    durations = {"H1": timedelta(hours=1), "M15": timedelta(minutes=15), "M5": timedelta(minutes=5)}
    data_root = repo_root / config["raw_data_root"]
    snapshot = json.loads((repo_root / "multi-asset/london-breakout-v1/evidence/CAPITAL_COM_CONTRACT_AND_TICK_PROBE.json").read_text(encoding="utf-8"))
    rows: list[dict[str, Any]] = []
    for symbol in config["declared_universe"]:
        pre_outcome = config["pre_outcome_unavailable"].get(symbol, "")
        contract = snapshot.get("symbols", {}).get(symbol, {})
        files: dict[str, Any] = {}
        reasons: list[str] = []
        for timeframe in config["required_timeframes"]:
            matches = sorted(data_root.glob(config["file_pattern"].format(symbol=symbol, timeframe=timeframe)))
            if len(matches) != 1:
                files[timeframe] = {"timeframe": timeframe, "match_count": len(matches), "exists": False}
                reasons.append(f"{timeframe}_FILE_COUNT_{len(matches)}")
                continue
            details = inspect_file(matches[0], repo_root, required_start, required_end - durations[timeframe], timeframe,
                                   contract.get("point"), contract.get("digits"))
            details["exists"] = True
            files[timeframe] = details
            checks = {
                "START_INCOMPLETE": not details["starts_on_or_before_required_start"],
                "END_INCOMPLETE": not details["ends_on_or_after_required_last_open"],
                "DUPLICATE_TIMESTAMPS": details["duplicate_timestamp_count"] > 0,
                "DECREASING_TIMESTAMPS": details["decreasing_timestamp_count"] > 0,
                "INVALID_PRICES": details["invalid_price_count"] > 0,
                "MISSING_COLUMNS": details["missing_required_column_count"] > 0,
                "INVALID_SPREADS": details["negative_spread_count"] > 0 or details["nonfinite_or_missing_spread_count"] > 0,
                "POINT_DIGITS_INCONSISTENT": not details["point_digits_consistent"],
                "OFF_GRID_INTERVALS": details["off_grid_interval_count"] > 0,
            }
            reasons.extend(f"{timeframe}_{label}" for label, failed in checks.items() if failed)
        quote_status = "NOT_APPLICABLE_PRE_OUTCOME_UNAVAILABLE" if pre_outcome else "QUOTE_BASIS_UNRESOLVED_NOT_SCORED"
        if not pre_outcome:
            reasons.extend(["QUOTE_BASIS_NOT_ESTABLISHED", "SPREAD_UNITS_NOT_INDEPENDENTLY_ESTABLISHED"])
        complete = not pre_outcome and not reasons
        rows.append({"symbol": symbol, "scoring_status": pre_outcome or ("DATA_GATE_PASS" if complete else "PROVISIONAL_DATA_INVALID_NOT_SCORED"),
                     "quote_basis_status": quote_status, "complete_quote_valid_dataset": complete,
                     "point_size": contract.get("point"), "digits": contract.get("digits"),
                     "failure_reasons": sorted(set(reasons)), "files": files})
    return rows


def canonical_hash(paths: list[Path]) -> str:
    digest = hashlib.sha256()
    for path in sorted(paths, key=lambda value: value.name):
        digest.update(path.name.encode()); digest.update(b"\0"); digest.update(path.read_bytes()); digest.update(b"\0")
    return digest.hexdigest()


def json_write(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def csv_write(path: Path, fieldnames: list[str], rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n"); writer.writeheader(); writer.writerows(rows)
