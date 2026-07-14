from __future__ import annotations

import json
import os
import shutil
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .foundation import (
    CLASSIFICATIONS,
    END_UTC,
    FORBIDDEN_FIELDS,
    INSTRUMENTS,
    MAX_CONCURRENCY,
    NORMALIZED_COLUMNS,
    OFFICIAL_HISTORY_DOC,
    OFFICIAL_ORIGIN,
    OFFICIAL_WIDGET,
    PHASE,
    PRICE_BASES,
    START_UTC,
    STORAGE_ENV,
    TIMEFRAMES_MINUTES,
    acquire_month,
    assert_no_forbidden_output_fields,
    build_source_contract,
    canonical_json_bytes,
    classify,
    compare_run_hashes,
    freeze_raw_month,
    git_value,
    hours_in_month,
    http_fetch,
    iso_utc,
    month_keys,
    normalize_month,
    official_instrument_url,
    official_tick_url,
    raw_hour_path,
    resolve_storage_root,
    sha256_bytes,
    sha256_file,
    storage_preflight,
    utc_now,
    validate_hour_payload,
    write_month_acquisition_manifest,
    write_csv,
    write_json,
)


OUTPUT_NAMES = (
    "DUKASCOPY_DATA_SOURCE_CONTRACT.md",
    "DUKASCOPY_DATA_SOURCE_CONTRACT.json",
    "DUKASCOPY_INSTRUMENT_INVENTORY.csv",
    "DUKASCOPY_ACQUISITION_INVENTORY.csv",
    "DUKASCOPY_PARTITION_MANIFEST.csv",
    "DUKASCOPY_NORMALIZED_PARTITION_MANIFEST.csv",
    "DUKASCOPY_COVERAGE_REPORT.csv",
    "DUKASCOPY_MONTHLY_COVERAGE.csv",
    "DUKASCOPY_TICK_INTEGRITY.csv",
    "DUKASCOPY_DUPLICATE_INVENTORY.csv",
    "DUKASCOPY_GAP_INVENTORY.csv",
    "DUKASCOPY_SPREAD_DIAGNOSTICS.csv",
    "DUKASCOPY_BAR_CENSUS.csv",
    "DUKASCOPY_BAR_PARTITION_MANIFEST.csv",
    "DUKASCOPY_DETERMINISM_REPORT.json",
    "DUKASCOPY_DATA_GATE_AUDIT.json",
    "DUKASCOPY_RUN_MANIFEST.json",
    "DUKASCOPY_FOUNDATION_RESULT.md",
    "DUKASCOPY_FOUNDATION_RESULT.json",
)


def _month_tuple(value: str) -> tuple[int, int]:
    try:
        parsed = datetime.strptime(value, "%Y-%m")
    except ValueError as exc:
        raise ValueError(f"invalid month {value!r}; expected YYYY-MM") from exc
    if value not in month_keys():
        raise ValueError(f"month {value} is outside the locked period")
    return parsed.year, parsed.month


def _fetch_official_json(url: str) -> tuple[bytes, dict[str, Any], dict[str, str]]:
    body, headers, status = http_fetch(url)
    if status != 200:
        raise RuntimeError(f"official source returned HTTP {status}: {url}")
    value = json.loads(body)
    if not isinstance(value, dict):
        raise RuntimeError(f"official source returned non-object JSON: {url}")
    return body, value, headers


def _source_preflight(storage_root: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    evidence_root = storage_root / "source-evidence"
    evidence_root.mkdir(parents=True, exist_ok=True)
    inventory: list[dict[str, Any]] = []
    source_hashes: dict[str, str] = {}
    for symbol, spec in INSTRUMENTS.items():
        body, metadata, headers = _fetch_official_json(official_instrument_url(symbol))
        expected_name = f"{symbol[:3]}/{symbol[3:]}"
        valid = (
            metadata.get("code") == spec["source_code"]
            and metadata.get("name") == expected_name
            and any(item.get("period") == "TICK" and int(item.get("from", 2**63 - 1)) <= int(START_UTC.timestamp() * 1000) for item in metadata.get("histories", []))
        )
        path = evidence_root / f"instrument-{symbol}.json"
        path.write_bytes(body)
        digest = sha256_bytes(body)
        source_hashes[f"instrument-{symbol}"] = digest
        inventory.append({
            "symbol": symbol,
            "source_code": metadata.get("code", ""),
            "source_name": metadata.get("name", ""),
            "description": metadata.get("description", ""),
            "pip_size": spec["pip_size"],
            "price_scale": metadata.get("priceScale", ""),
            "tick_history_from_utc": iso_utc(datetime.fromtimestamp(next((item["from"] for item in metadata.get("histories", []) if item.get("period") == "TICK"), 0) / 1000, UTC)),
            "official_instrument_url": official_instrument_url(symbol),
            "response_sha256": digest,
            "source_contract_valid": valid,
            "etag": headers.get("etag", ""),
        })
    fixture_hour = datetime(2024, 1, 2, 12, tzinfo=UTC)
    fixture_url = official_tick_url("EURUSD", fixture_hour)
    fixture_body, _, fixture_headers = _fetch_official_json(fixture_url)
    fixture_count = validate_hour_payload(fixture_body, "EURUSD", fixture_hour, "official-preflight-fixture")
    fixture_path = evidence_root / "official-EURUSD-2024010212.json"
    fixture_path.write_bytes(fixture_body)
    source_hashes["official-fixture-EURUSD-2024010212"] = sha256_bytes(fixture_body)
    sample_sizes: list[int] = []
    sample_counts: dict[str, int] = {}
    for symbol in INSTRUMENTS:
        url = official_tick_url(symbol, fixture_hour)
        body, _, _ = _fetch_official_json(url)
        count = validate_hour_payload(body, symbol, fixture_hour, f"size-fixture-{symbol}")
        sample_sizes.append(len(body))
        sample_counts[symbol] = count
        source_hashes[f"size-fixture-{symbol}"] = sha256_bytes(body)
    average_active_hour = sum(sample_sizes) / len(sample_sizes)
    total_calendar_hours = sum(len(hours_in_month(*_month_tuple(month))) for month in month_keys()) * len(INSTRUMENTS)
    # Conservative: active-hour sample applied to every calendar hour, then raw + normalized + bars/index overhead.
    estimated_raw = int(average_active_hour * total_calendar_hours)
    estimated_total = int(estimated_raw * 1.75)
    preflight = {
        "official_source_schema_established": all(row["source_contract_valid"] for row in inventory) and fixture_count > 0,
        "fixture_url": fixture_url,
        "fixture_tick_count": fixture_count,
        "fixture_sha256": sha256_bytes(fixture_body),
        "fixture_response_bytes": len(fixture_body),
        "fixture_etag": fixture_headers.get("etag", ""),
        "sample_tick_counts": sample_counts,
        "average_active_hour_response_bytes": average_active_hour,
        "estimated_raw_bytes_conservative": estimated_raw,
        "estimated_total_bytes_conservative": estimated_total,
        "source_hashes": source_hashes,
    }
    preflight["storage"] = storage_preflight(storage_root, estimated_total)
    return inventory, preflight


def _partition_rows(storage_root: Path, selected: list[str]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for symbol in INSTRUMENTS:
        for month in selected:
            year, month_number = _month_tuple(month)
            root = storage_root / "raw" / symbol / f"year={year:04d}" / f"month={month_number:02d}"
            files = sorted(path for path in root.glob("*.json") if not path.name.startswith("_"))
            frozen = root / "_FROZEN_MANIFEST.json"
            expected = len(hours_in_month(year, month_number))
            rows.append({
                "symbol": symbol, "month": month, "expected_hour_files": expected,
                "observed_hour_files": len(files), "complete": len(files) == expected,
                "frozen": frozen.exists(), "total_bytes": sum(path.stat().st_size for path in files),
                "partition_inventory_sha256": sha256_bytes(canonical_json_bytes([(path.name, sha256_file(path)) for path in files])),
                "relative_path": str(root.relative_to(storage_root)).replace("\\", "/"),
            })
    return rows


def _coverage_rows(partitions: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    by_key = {(row["symbol"], row["month"]): row for row in partitions}
    monthly: list[dict[str, Any]] = []
    for symbol in INSTRUMENTS:
        for month in month_keys():
            partition = by_key.get((symbol, month))
            monthly.append({
                "symbol": symbol, "month": month,
                "status": "COMPLETE_FROZEN" if partition and partition["complete"] and partition["frozen"] else "MISSING_OR_INCOMPLETE",
                "expected_hour_files": partition["expected_hour_files"] if partition else len(hours_in_month(*_month_tuple(month))),
                "observed_hour_files": partition["observed_hour_files"] if partition else 0,
            })
    report: list[dict[str, Any]] = []
    for symbol in INSTRUMENTS:
        rows = [row for row in monthly if row["symbol"] == symbol]
        complete = sum(row["status"] == "COMPLETE_FROZEN" for row in rows)
        report.append({
            "symbol": symbol, "required_months": len(rows), "complete_months": complete,
            "missing_or_incomplete_months": len(rows) - complete,
            "coverage_percent": round(100 * complete / len(rows), 6),
            "period_start_utc": iso_utc(START_UTC), "period_end_utc": iso_utc(END_UTC),
        })
    return report, monthly


def _run_derivation(storage_root: Path, run_root: Path, partitions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if run_root.exists():
        raise RuntimeError(f"independent derivation destination already exists: {run_root}")
    results: list[dict[str, Any]] = []
    for partition in partitions:
        if not (partition["complete"] and partition["frozen"]):
            continue
        year, month = _month_tuple(partition["month"])
        results.append(normalize_month(storage_root, run_root, partition["symbol"], year, month))
    return results


def _flatten(results: list[dict[str, Any]], key: str) -> list[dict[str, Any]]:
    values: list[dict[str, Any]] = []
    for result in results:
        value = result[key]
        values.extend(value if isinstance(value, list) else [value])
    return values


def _write_outputs(
    lane_root: Path,
    storage_root: Path,
    instrument_inventory: list[dict[str, Any]],
    source_preflight: dict[str, Any],
    acquisition_rows: list[dict[str, Any]],
    partitions: list[dict[str, Any]],
    run_one_results: list[dict[str, Any]],
    determinism: dict[str, Any],
    selected: list[str],
    invocation: dict[str, Any],
    started_at: str,
) -> str:
    outputs = lane_root / "outputs"
    outputs.mkdir(parents=True, exist_ok=True)
    contract = build_source_contract()
    write_json(outputs / "DUKASCOPY_DATA_SOURCE_CONTRACT.json", contract)
    notices = "\n\n".join(f"# {notice}" for notice in contract["notices"])
    contract_md = f"{notices}\n\nThis contract is machine-readable in `DUKASCOPY_DATA_SOURCE_CONTRACT.json`.\n\nOfficial service: {OFFICIAL_ORIGIN}\n\nOfficial widget: {OFFICIAL_WIDGET}\n\nOfficial historical-tick semantics: {OFFICIAL_HISTORY_DOC}\n"
    (outputs / "DUKASCOPY_DATA_SOURCE_CONTRACT.md").write_text(contract_md, encoding="utf-8", newline="\n")
    write_csv(outputs / "DUKASCOPY_INSTRUMENT_INVENTORY.csv", list(instrument_inventory[0]), instrument_inventory)
    acquisition_fields = [
        "symbol", "hour_utc", "source_file_id", "url", "status", "attempts", "http_status", "bytes",
        "sha256", "tick_count", "etag", "last_modified", "path", "error",
    ]
    write_csv(outputs / "DUKASCOPY_ACQUISITION_INVENTORY.csv", acquisition_fields, acquisition_rows)
    write_csv(outputs / "DUKASCOPY_PARTITION_MANIFEST.csv", list(partitions[0]), partitions)
    normalized = _flatten(run_one_results, "partition")
    normalized_fields = list(normalized[0]) if normalized else ["symbol", "month", "tick_count", "path", "sha256"]
    write_csv(outputs / "DUKASCOPY_NORMALIZED_PARTITION_MANIFEST.csv", normalized_fields, normalized)
    coverage, monthly = _coverage_rows(partitions)
    write_csv(outputs / "DUKASCOPY_COVERAGE_REPORT.csv", list(coverage[0]), coverage)
    write_csv(outputs / "DUKASCOPY_MONTHLY_COVERAGE.csv", list(monthly[0]), monthly)
    integrity = _flatten(run_one_results, "integrity")
    integrity_fields = list(integrity[0]) if integrity else ["symbol", "month", "tick_count"]
    write_csv(outputs / "DUKASCOPY_TICK_INTEGRITY.csv", integrity_fields, integrity)
    duplicates = [{
        "symbol": row["symbol"], "month": row["month"], "exact_duplicate_count": row["exact_duplicate_count"],
        "conflicting_same_timestamp_count": row["conflicting_same_timestamp_count"],
        "policy": "PRESERVED_AND_REPORTED",
    } for row in integrity]
    write_csv(outputs / "DUKASCOPY_DUPLICATE_INVENTORY.csv", ["symbol", "month", "exact_duplicate_count", "conflicting_same_timestamp_count", "policy"], duplicates)
    gaps = [{
        "symbol": row["symbol"], "month": row["month"], "gaps_over_60s": row["gaps_over_60s"],
        "longest_gap_ms": row["longest_gap_ms"], "unexplained_raw_hour_gap_count": 0,
        "interpretation": "inter-tick diagnostic includes scheduled closures; every raw hour file is present; no bars or ticks synthesized",
    } for row in integrity]
    write_csv(outputs / "DUKASCOPY_GAP_INVENTORY.csv", ["symbol", "month", "gaps_over_60s", "longest_gap_ms", "unexplained_raw_hour_gap_count", "interpretation"], gaps)
    spreads = _flatten(run_one_results, "spread")
    spread_fields = list(spreads[0]) if spreads else ["symbol", "month", "observations"]
    write_csv(outputs / "DUKASCOPY_SPREAD_DIAGNOSTICS.csv", spread_fields, spreads)
    bars = _flatten(run_one_results, "bars")
    bar_fields = list(bars[0]) if bars else ["symbol", "month", "basis", "timeframe", "bar_count", "path", "sha256"]
    write_csv(outputs / "DUKASCOPY_BAR_CENSUS.csv", ["symbol", "month", "basis", "timeframe", "bar_count", "first_bar_utc", "last_bar_utc"], bars)
    write_csv(outputs / "DUKASCOPY_BAR_PARTITION_MANIFEST.csv", bar_fields, bars)
    write_json(outputs / "DUKASCOPY_DETERMINISM_REPORT.json", determinism)
    expected_months = len(INSTRUMENTS) * len(month_keys())
    complete_months = sum(row["complete"] and row["frozen"] for row in partitions)
    material_failure = any(
        row.get("negative_spread_count", 0) > 0 or row.get("conflicting_same_timestamp_count", 0) > 0
        for row in integrity
    )
    classification = classify(
        source_preflight["official_source_schema_established"], material_failure, complete_months,
        expected_months, determinism["identical"],
    )
    gate_audit = {
        "phase": PHASE,
        "classification": classification,
        "allowed_classifications": list(CLASSIFICATIONS),
        "source_schema_established": source_preflight["official_source_schema_established"],
        "material_integrity_failure": material_failure,
        "deterministic_replay": determinism["identical"],
        "required_instruments_present": all(any(row["symbol"] == symbol and row["complete"] for row in partitions) for symbol in INSTRUMENTS),
        "complete_month_partitions": complete_months,
        "required_month_partitions": expected_months,
        "full_period_complete": complete_months == expected_months,
        "strategy_scoring_authorized": False,
        "mt5_strategy_tester_used": False,
        "broker_action_authorized": False,
        "deployment_authorized": False,
        "bulk_raw_files_committed": False,
        "small_official_test_fixture_committed": True,
    }
    assert_no_forbidden_output_fields(gate_audit)
    write_json(outputs / "DUKASCOPY_DATA_GATE_AUDIT.json", gate_audit)
    repo_root = lane_root.parents[2]
    completed_at = utc_now()
    run_manifest = {
        "phase": PHASE,
        "started_at_utc": started_at,
        "completed_at_utc": completed_at,
        "invocation": invocation,
        "python": sys.version,
        "execution_git_commit": git_value(repo_root, "rev-parse", "HEAD"),
        "execution_git_tree": git_value(repo_root, "rev-parse", "HEAD^{tree}"),
        "branch": git_value(repo_root, "branch", "--show-current"),
        "storage_environment_variable": STORAGE_ENV,
        "external_storage_root_recorded": False,
        "selected_months": selected,
        "source_preflight": source_preflight,
        "classification": classification,
        "output_files": list(OUTPUT_NAMES),
        "normalized_columns": list(NORMALIZED_COLUMNS),
        "price_bases": list(PRICE_BASES),
        "timeframes": list(TIMEFRAMES_MINUTES),
    }
    assert_no_forbidden_output_fields(run_manifest)
    write_json(outputs / "DUKASCOPY_RUN_MANIFEST.json", run_manifest)
    result = {
        "phase": PHASE,
        "classification": classification,
        "summary": "Official source and deterministic derivation are valid for acquired partitions, but the locked decade is incomplete." if classification == "PARTIAL_NOT_READY" else "See data gate audit.",
        "complete_month_partitions": complete_months,
        "required_month_partitions": expected_months,
        "missing_month_partitions": expected_months - complete_months,
        "coverage_percent": round(100 * complete_months / expected_months, 6),
        "official_fixture_sha256": source_preflight["fixture_sha256"],
        "deterministic_replay": determinism["identical"],
        "next_action": "Acquire and validate the remaining official Dukascopy monthly partitions; no strategy test is proposed.",
        "deployment_authorized": False,
    }
    assert_no_forbidden_output_fields(result)
    write_json(outputs / "DUKASCOPY_FOUNDATION_RESULT.json", result)
    result_md = (
        f"# Dukascopy Tick Data Foundation Result\n\n"
        f"Classification: `{classification}`\n\n"
        f"Complete monthly partitions: `{complete_months}/{expected_months}` ({result['coverage_percent']}%).\n\n"
        f"Deterministic replay: `{determinism['identical']}`.\n\n"
        f"This is a data-only result. It provides no strategy scoring and no deployment authorization.\n\n"
        f"Next action: acquire and validate the remaining official Dukascopy monthly partitions. No strategy test is proposed.\n"
    )
    (outputs / "DUKASCOPY_FOUNDATION_RESULT.md").write_text(result_md, encoding="utf-8", newline="\n")
    missing_outputs = [name for name in OUTPUT_NAMES if not (outputs / name).is_file()]
    if missing_outputs:
        raise RuntimeError(f"required outputs missing: {missing_outputs}")
    return classification


def run_pipeline(
    lane_root: Path,
    months: list[str] | None = None,
    all_months: bool = False,
    concurrency: int = MAX_CONCURRENCY,
    skip_acquisition: bool = False,
) -> int:
    started_at = utc_now()
    lane_root = lane_root.resolve()
    storage_root = resolve_storage_root(lane_root=lane_root)
    if not 1 <= concurrency <= MAX_CONCURRENCY:
        raise ValueError(f"concurrency must be between 1 and {MAX_CONCURRENCY}")
    selected = month_keys() if all_months else sorted(set(months or []))
    if not selected:
        raise ValueError("select at least one --month or use --all-months")
    for month in selected:
        _month_tuple(month)
    instrument_inventory, source_preflight = _source_preflight(storage_root)
    if not source_preflight["official_source_schema_established"]:
        raise RuntimeError("official source schema preflight failed")
    if all_months and not source_preflight["storage"]["passes"]:
        raise RuntimeError("full acquisition storage preflight failed the required 1.5x headroom")
    acquisition_rows: list[dict[str, Any]] = []
    if not skip_acquisition:
        for symbol in INSTRUMENTS:
            for month in selected:
                year, month_number = _month_tuple(month)
                rows = acquire_month(storage_root, symbol, year, month_number, concurrency=concurrency)
                acquisition_rows.extend(rows)
                if all(row["status"] in {"DOWNLOADED_VALID", "RESUMED_VALID"} for row in rows):
                    write_month_acquisition_manifest(storage_root, symbol, year, month_number, rows)
                    freeze_raw_month(storage_root, symbol, year, month_number)
    else:
        for symbol in INSTRUMENTS:
            for month in selected:
                year, month_number = _month_tuple(month)
                for hour in hours_in_month(year, month_number):
                    path = raw_hour_path(storage_root, symbol, hour)
                    acquisition_rows.append({
                        "symbol": symbol, "hour_utc": iso_utc(hour), "source_file_id": f"{symbol}-{hour:%Y%m%d%H}",
                        "url": official_tick_url(symbol, hour), "status": "PRESENT" if path.exists() else "MISSING",
                        "attempts": 0, "http_status": "", "bytes": path.stat().st_size if path.exists() else 0,
                        "sha256": sha256_file(path) if path.exists() else "", "tick_count": "", "etag": "",
                        "last_modified": "", "path": str(path.relative_to(storage_root)).replace("\\", "/"), "error": "",
                    })
    partitions = _partition_rows(storage_root, selected)
    run_stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    replay_root = storage_root / "replays" / run_stamp
    run_one = replay_root / "run-one"
    run_two = replay_root / "run-two"
    run_one_results = _run_derivation(storage_root, run_one, partitions)
    _run_derivation(storage_root, run_two, partitions)
    determinism = compare_run_hashes(run_one, run_two)
    invocation = {
        "selected_months": selected,
        "all_months": all_months,
        "concurrency": concurrency,
        "skip_acquisition": skip_acquisition,
    }
    classification = _write_outputs(
        lane_root, storage_root, instrument_inventory, source_preflight, acquisition_rows,
        partitions, run_one_results, determinism, selected, invocation, started_at,
    )
    print(classification)
    return 0 if classification in CLASSIFICATIONS else 2
