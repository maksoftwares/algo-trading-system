from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
import time
import urllib.error
import urllib.request
import zipfile
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta, timezone
from datetime import time as datetime_time
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from audit_neutral_gdelt_gkg_source import (
    EXPECTED_FIELDS,
    TRACKED_THEMES,
    _central_bank_side,
    _theme_tokens,
)

ROOT = Path(__file__).resolve().parent
CONFIG_PATH = ROOT / "config" / "frozen_neutral_gdelt_coverage_census_v1.json"
LOCK_PATH = (
    ROOT
    / "EURUSD_NEUTRAL_GDELT_COVERAGE_CENSUS_PREREG_2026_07_28.sha256.json"
)
DEFAULT_OUTPUT_ROOT = Path(
    "D:/AlgoTradingData/source-audits/gdelt-gkg-coverage-census-v1"
)
USER_AGENT = (
    "Mozilla/5.0 compatible; causal-market-research/1.0; "
    "public-source-capacity-census-only"
)
SCHEMA_VERSION = "eurusd_neutral_gdelt_coverage_census_result_v1"
MAX_CSV_FIELD_BYTES = 16 * 1024 * 1024
csv.field_size_limit(max(csv.field_size_limit(), MAX_CSV_FIELD_BYTES))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _json_bytes(value: Any) -> bytes:
    return (
        json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    ).encode("utf-8")


def load_and_verify_preregistration() -> tuple[dict[str, Any], dict[str, Any]]:
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    lock = json.loads(LOCK_PATH.read_text(encoding="utf-8"))
    if lock.get("locked_before_multi_date_download_and_eurusd_outcomes") is not True:
        raise RuntimeError("GDELT census was not locked before acquisition")
    for relative, expected in lock["files"].items():
        if sha256_file(ROOT / relative) != expected:
            raise RuntimeError(f"GDELT census lock mismatch: {relative}")
    source_audit = config["source_audit"]
    if sha256_file(ROOT / source_audit["path"]) != source_audit["sha256"]:
        raise RuntimeError("GDELT source-audit reference drift")
    if (
        config.get("eurusd_outcomes_allowed") is not False
        or config.get("oracle_matches_allowed") is not False
        or config.get("broker_action_allowed") is not False
        or config["decision_policy"].get("threshold_change_after_download_forbidden")
        is not True
    ):
        raise RuntimeError("GDELT census safety contract is incomplete")
    return config, lock


def build_targets(config: dict[str, Any]) -> list[dict[str, str]]:
    sampling = config["sampling"]
    source_times = [
        datetime_time.fromisoformat(value)
        for value in sampling["source_batch_times_utc"]
    ]
    targets: list[dict[str, str]] = []
    for entry_text in sampling["entry_dates_utc"]:
        entry_date = date.fromisoformat(entry_text)
        source_date = entry_date + timedelta(
            days=int(sampling["source_batch_date_offset_days"])
        )
        for source_time in source_times:
            timestamp = datetime.combine(
                source_date,
                source_time,
                tzinfo=timezone.utc,
            ).strftime("%Y%m%d%H%M%S")
            targets.append(
                {
                    "entry_date_utc": entry_date.isoformat(),
                    "batch_timestamp_utc": timestamp,
                    "url": config["source_contract"]["url_template"].format(
                        timestamp=timestamp
                    ),
                }
            )
    if len(targets) != int(sampling["target_files"]):
        raise RuntimeError("Frozen GDELT target count does not match enumeration")
    if len({target["batch_timestamp_utc"] for target in targets}) != len(
        targets
    ):
        raise RuntimeError("Frozen GDELT target timestamps are not unique")
    if len(targets) > int(
        config["decision_policy"]["maximum_target_files"]
    ):
        raise RuntimeError("Frozen GDELT maximum target-file count exceeded")
    return targets


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _fetch_archive(
    url: str,
    target_path: Path,
    *,
    timeout_seconds: float,
    attempts: int = 4,
) -> dict[str, Any]:
    if target_path.exists() and target_path.stat().st_size > 0:
        return {
            "network_request_attempts": 0,
            "archive_reused": True,
            "attempts": [
                {
                    "status": "REUSED_EXISTING_ARCHIVE",
                    "observed_at_utc": _utc_now().isoformat(),
                    "bytes": target_path.stat().st_size,
                }
            ],
        }
    target_path.parent.mkdir(parents=True, exist_ok=True)
    partial_path = target_path.with_suffix(target_path.suffix + ".part")
    attempt_rows: list[dict[str, Any]] = []
    for attempt_number in range(1, attempts + 1):
        observed_at = _utc_now()
        partial_bytes = (
            partial_path.stat().st_size if partial_path.exists() else 0
        )
        headers = {
            "User-Agent": USER_AGENT,
            "Accept": "application/zip, application/octet-stream",
        }
        if partial_bytes:
            headers["Range"] = f"bytes={partial_bytes}-"
        try:
            request = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(
                request,
                timeout=timeout_seconds,
            ) as response:
                status_code = int(response.getcode())
                append = partial_bytes > 0 and status_code == 206
                mode = "ab" if append else "wb"
                with partial_path.open(mode) as destination:
                    shutil.copyfileobj(response, destination, length=1024 * 1024)
            if partial_path.stat().st_size <= 0:
                raise RuntimeError("GDELT response was empty")
            with partial_path.open("rb") as stream:
                if stream.read(2) != b"PK":
                    raise RuntimeError("GDELT response was not a ZIP archive")
            partial_path.replace(target_path)
            attempt_rows.append(
                {
                    "attempt": attempt_number,
                    "observed_at_utc": observed_at.isoformat(),
                    "status": "DOWNLOADED",
                    "http_status": status_code,
                    "range_requested_from_byte": (
                        partial_bytes if partial_bytes else None
                    ),
                    "bytes": target_path.stat().st_size,
                }
            )
            return {
                "network_request_attempts": len(attempt_rows),
                "archive_reused": False,
                "attempts": attempt_rows,
            }
        except (
            OSError,
            RuntimeError,
            urllib.error.URLError,
        ) as exc:
            attempt_rows.append(
                {
                    "attempt": attempt_number,
                    "observed_at_utc": observed_at.isoformat(),
                    "status": "FAILED",
                    "error_type": type(exc).__name__,
                    "error": str(exc),
                    "partial_bytes": (
                        partial_path.stat().st_size
                        if partial_path.exists()
                        else 0
                    ),
                }
            )
            if attempt_number < attempts:
                time.sleep(1.5 * attempt_number)
    return {
        "network_request_attempts": len(attempt_rows),
        "archive_reused": False,
        "attempts": attempt_rows,
    }


def parse_archive(
    archive_path: Path,
    target: dict[str, str],
) -> tuple[dict[str, Any], list[dict[str, str]]]:
    rows = 0
    strict_rows: list[dict[str, str]] = []
    field_counts: Counter[int] = Counter()
    timestamps: Counter[str] = Counter()
    with zipfile.ZipFile(archive_path) as archive:
        members = archive.namelist()
        if len(members) != 1:
            raise RuntimeError("GDELT archive must contain exactly one member")
        member = members[0]
        with archive.open(member) as stream:
            for raw in stream:
                row = next(
                    csv.reader(
                        [raw.decode("utf-8", errors="strict")],
                        delimiter="\t",
                    )
                )
                rows += 1
                field_counts[len(row)] += 1
                if len(row) != EXPECTED_FIELDS:
                    raise RuntimeError("GDELT GKG row has unexpected width")
                timestamps[row[1]] += 1
                if row[1] != target["batch_timestamp_utc"]:
                    raise RuntimeError("GDELT row timestamp does not match batch")
                side = _central_bank_side(row)
                if side is None:
                    continue
                document_identifier = row[4].strip()
                if not document_identifier:
                    raise RuntimeError(
                        "Strict GDELT match has no document identifier"
                    )
                source = row[3].strip()
                if not source:
                    source = urlparse(document_identifier).hostname or ""
                if not source:
                    raise RuntimeError("Strict GDELT match has no source")
                themes = sorted(
                    theme
                    for theme in _theme_tokens(row)
                    if theme in TRACKED_THEMES
                    or "MONETARY_POLICY" in theme
                )
                strict_rows.append(
                    {
                        "entry_date_utc": target["entry_date_utc"],
                        "batch_timestamp_utc": target["batch_timestamp_utc"],
                        "record_id": row[0],
                        "side": side,
                        "source_common_name": source.lower(),
                        "document_identifier": document_identifier,
                        "qualifying_themes": ";".join(themes),
                    }
                )
    return (
        {
            "zip_members": members,
            "rows": rows,
            "field_count_distribution": {
                str(key): int(value)
                for key, value in sorted(field_counts.items())
            },
            "gkg_timestamp_counts": dict(sorted(timestamps.items())),
        },
        strict_rows,
    )


def _write_request_metadata(
    output_root: Path,
    target: dict[str, str],
    metadata: dict[str, Any],
) -> tuple[str, str]:
    payload = _json_bytes(metadata)
    observed = _utc_now().strftime("%Y%m%dT%H%M%SZ")
    digest = hashlib.sha256(payload).hexdigest()
    relative = (
        Path("request_metadata")
        / (
            f"{target['batch_timestamp_utc']}_{observed}_"
            f"{digest[:16]}.json"
        )
    )
    path = output_root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write(payload)
    return relative.as_posix(), digest


def _chain_hash(paths: list[Path], root: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(paths):
        relative = path.relative_to(root).as_posix()
        digest.update(relative.encode("utf-8"))
        digest.update(bytes.fromhex(sha256_file(path)))
    return digest.hexdigest()


def _deduplicate_rows(
    rows: list[dict[str, str]],
) -> list[dict[str, str]]:
    selected: dict[str, dict[str, str]] = {}
    for row in sorted(
        rows,
        key=lambda value: (
            value["batch_timestamp_utc"],
            value["record_id"],
            value["document_identifier"],
        ),
    ):
        selected.setdefault(row["document_identifier"], row)
    return sorted(
        selected.values(),
        key=lambda value: (
            value["entry_date_utc"],
            value["batch_timestamp_utc"],
            value["side"],
            value["document_identifier"],
        ),
    )


def _side_statistics(
    deduplicated_rows: list[dict[str, str]],
    side: str,
) -> dict[str, Any]:
    selected = [row for row in deduplicated_rows if row["side"] == side]
    sources = Counter(row["source_common_name"] for row in selected)
    largest_count = max(sources.values(), default=0)
    total = len(selected)
    return {
        "strict_articles": total,
        "unique_sources": len(sources),
        "largest_source": (
            min(
                sources.items(),
                key=lambda item: (-item[1], item[0]),
            )[0]
            if sources
            else None
        ),
        "largest_source_articles": largest_count,
        "largest_source_share": largest_count / total if total else 0.0,
        "source_counts": dict(
            sorted(sources.items(), key=lambda item: (-item[1], item[0]))
        ),
    }


def summarize_census(
    config: dict[str, Any],
    targets: list[dict[str, str]],
    file_results: list[dict[str, Any]],
    strict_rows: list[dict[str, str]],
) -> tuple[dict[str, Any], list[dict[str, str]]]:
    deduplicated = _deduplicate_rows(strict_rows)
    successful = [
        result
        for result in file_results
        if result["status"] == "SUCCESS_VALIDATED"
    ]
    successes_by_date: dict[str, int] = defaultdict(int)
    for result in successful:
        successes_by_date[result["entry_date_utc"]] += 1
    batches_per_date = len(config["sampling"]["source_batch_times_utc"])
    complete_dates = sorted(
        entry_date
        for entry_date, count in successes_by_date.items()
        if count == batches_per_date
    )
    sides_by_date: dict[str, set[str]] = defaultdict(set)
    for row in deduplicated:
        sides_by_date[row["entry_date_utc"]].add(row["side"])
    both_side_dates = sorted(
        entry_date
        for entry_date, sides in sides_by_date.items()
        if {"ECB", "FED"}.issubset(sides)
    )
    duplicate_count = len(strict_rows) - len(deduplicated)
    duplicate_share = (
        duplicate_count / len(strict_rows) if strict_rows else 0.0
    )
    side_stats = {
        side: _side_statistics(deduplicated, side)
        for side in ("ECB", "FED")
    }
    gates = config["capacity_gates"]
    gate_results = {
        "successful_file_rate": (
            len(successful) / len(targets)
            >= float(gates["minimum_successful_file_rate"])
        ),
        "complete_entry_dates": (
            len(complete_dates)
            >= int(gates["minimum_complete_entry_dates"])
        ),
        "dates_with_both_strict_sides": (
            len(both_side_dates)
            >= int(
                gates[
                    "minimum_dates_with_both_strict_ecb_and_fed_articles"
                ]
            )
        ),
        "total_strict_ecb_articles": (
            side_stats["ECB"]["strict_articles"]
            >= int(gates["minimum_total_strict_ecb_articles"])
        ),
        "total_strict_fed_articles": (
            side_stats["FED"]["strict_articles"]
            >= int(gates["minimum_total_strict_fed_articles"])
        ),
        "unique_ecb_sources": (
            side_stats["ECB"]["unique_sources"]
            >= int(gates["minimum_unique_sources_each_side"])
        ),
        "unique_fed_sources": (
            side_stats["FED"]["unique_sources"]
            >= int(gates["minimum_unique_sources_each_side"])
        ),
        "ecb_source_concentration": (
            side_stats["ECB"]["largest_source_share"]
            <= float(gates["maximum_largest_source_share_each_side"])
        ),
        "fed_source_concentration": (
            side_stats["FED"]["largest_source_share"]
            <= float(gates["maximum_largest_source_share_each_side"])
        ),
        "duplicate_document_share": (
            duplicate_share
            <= float(gates["maximum_duplicate_document_share"])
        ),
    }
    passed = all(gate_results.values())
    summary = {
        "target_files": len(targets),
        "successful_files": len(successful),
        "successful_file_rate": (
            len(successful) / len(targets) if targets else 0.0
        ),
        "complete_entry_dates": len(complete_dates),
        "complete_entry_date_values": complete_dates,
        "dates_with_both_strict_ecb_and_fed_articles": len(
            both_side_dates
        ),
        "dates_with_both_strict_ecb_and_fed_article_values": (
            both_side_dates
        ),
        "raw_strict_article_occurrences": len(strict_rows),
        "deduplicated_strict_articles": len(deduplicated),
        "duplicate_document_occurrences": duplicate_count,
        "duplicate_document_share": duplicate_share,
        "by_side": side_stats,
        "gate_results": gate_results,
        "all_capacity_gates_passed": passed,
        "decision": (
            "PASS_PREREGISTER_SEPARATE_PROSPECTIVE_DESIGN"
            if passed
            else "FAIL_CLOSE_GDELT_SOURCE_LANE"
        ),
    }
    return summary, deduplicated


def run_census(
    output_root: Path,
    *,
    timeout_seconds: float = 120.0,
    maximum_targets: int | None = None,
) -> dict[str, Any]:
    config, lock = load_and_verify_preregistration()
    targets = build_targets(config)
    if maximum_targets is not None and maximum_targets != len(targets):
        raise RuntimeError(
            "Partial target selection is forbidden by the frozen census"
        )
    output_root.mkdir(parents=True, exist_ok=True)
    file_results: list[dict[str, Any]] = []
    strict_rows: list[dict[str, str]] = []
    network_attempts = 0
    for target in targets:
        timestamp = target["batch_timestamp_utc"]
        relative_archive = (
            Path("raw") / f"{timestamp}.gkg.csv.zip"
        )
        archive_path = output_root / relative_archive
        fetch = _fetch_archive(
            target["url"],
            archive_path,
            timeout_seconds=timeout_seconds,
        )
        network_attempts += int(fetch["network_request_attempts"])
        metadata: dict[str, Any] = {
            "schema_version": (
                "eurusd_neutral_gdelt_coverage_request_metadata_v1"
            ),
            **target,
            "archive_relative_path": relative_archive.as_posix(),
            "archive_reused": fetch["archive_reused"],
            "attempts": fetch["attempts"],
            "eurusd_outcomes_loaded": False,
            "oracle_rows_loaded": False,
            "broker_action_allowed": False,
        }
        result: dict[str, Any] = {
            **target,
            "archive_relative_path": relative_archive.as_posix(),
        }
        if archive_path.exists():
            try:
                validation, archive_rows = parse_archive(
                    archive_path,
                    target,
                )
                archive_hash = sha256_file(archive_path)
                metadata.update(
                    {
                        "status": "SUCCESS_VALIDATED",
                        "archive_bytes": archive_path.stat().st_size,
                        "archive_sha256": archive_hash,
                        "validation": validation,
                    }
                )
                result.update(
                    {
                        "status": "SUCCESS_VALIDATED",
                        "archive_bytes": archive_path.stat().st_size,
                        "archive_sha256": archive_hash,
                        "rows": validation["rows"],
                        "strict_rows": len(archive_rows),
                    }
                )
                strict_rows.extend(archive_rows)
            except (
                OSError,
                RuntimeError,
                UnicodeError,
                csv.Error,
                zipfile.BadZipFile,
            ) as exc:
                metadata.update(
                    {
                        "status": "FAILED_VALIDATION",
                        "error_type": type(exc).__name__,
                        "error": str(exc),
                        "archive_bytes": archive_path.stat().st_size,
                        "archive_sha256": sha256_file(archive_path),
                    }
                )
                result.update(
                    {
                        "status": "FAILED_VALIDATION",
                        "error_type": type(exc).__name__,
                        "error": str(exc),
                    }
                )
        else:
            partial_path = archive_path.with_suffix(
                archive_path.suffix + ".part"
            )
            metadata.update(
                {
                    "status": "MISSING_ARCHIVE",
                    "partial_bytes": (
                        partial_path.stat().st_size
                        if partial_path.exists()
                        else 0
                    ),
                    "partial_sha256": (
                        sha256_file(partial_path)
                        if partial_path.exists()
                        else None
                    ),
                }
            )
            result["status"] = "MISSING_ARCHIVE"
        metadata_path, metadata_hash = _write_request_metadata(
            output_root,
            target,
            metadata,
        )
        result["request_metadata_relative_path"] = metadata_path
        result["request_metadata_sha256"] = metadata_hash
        file_results.append(result)

    summary, deduplicated_rows = summarize_census(
        config,
        targets,
        file_results,
        strict_rows,
    )
    normalized_path = output_root / "GDELT_STRICT_CENTRAL_BANK_ARTICLES.jsonl"
    with normalized_path.open("wb") as stream:
        for row in deduplicated_rows:
            stream.write(
                (
                    json.dumps(
                        row,
                        sort_keys=True,
                        ensure_ascii=False,
                    )
                    + "\n"
                ).encode("utf-8")
            )
    raw_paths = [
        output_root / result["archive_relative_path"]
        for result in file_results
        if result["status"] == "SUCCESS_VALIDATED"
    ]
    metadata_paths = [
        output_root / result["request_metadata_relative_path"]
        for result in file_results
    ]
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "captured_at_utc": _utc_now().isoformat(),
        "status": "CENSUS_COMPLETE",
        "research_only": True,
        "source_census_only": True,
        "strategy_preregistered": False,
        "eurusd_prices_loaded": False,
        "eurusd_returns_loaded": False,
        "eurusd_outcomes_loaded": False,
        "oracle_rows_loaded": False,
        "pnl_loaded": False,
        "signal_generated": False,
        "broker_action_allowed": False,
        "config_path": CONFIG_PATH.relative_to(ROOT).as_posix(),
        "config_sha256": sha256_file(CONFIG_PATH),
        "preregistration_lock_path": LOCK_PATH.name,
        "preregistration_lock_sha256": sha256_file(LOCK_PATH),
        "preregistration_locked_at_utc": lock["locked_at_utc"],
        "download_concurrency": 1,
        "network_request_attempts": network_attempts,
        "raw_archive_chain_sha256": _chain_hash(raw_paths, output_root),
        "request_metadata_chain_sha256": _chain_hash(
            metadata_paths,
            output_root,
        ),
        "normalized_relative_path": normalized_path.relative_to(
            output_root
        ).as_posix(),
        "normalized_sha256": sha256_file(normalized_path),
        "summary": summary,
        "files": file_results,
    }
    manifest_path = output_root / "MANIFEST.json"
    manifest_path.write_bytes(_json_bytes(manifest))
    result = {
        **manifest,
        "manifest_path": manifest_path.as_posix(),
        "manifest_sha256": sha256_file(manifest_path),
    }
    return result


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("capture", "status"))
    parser.add_argument(
        "--output-root",
        type=Path,
        default=DEFAULT_OUTPUT_ROOT,
    )
    parser.add_argument("--timeout-seconds", type=float, default=120.0)
    parser.add_argument("--maximum-targets", type=int)
    return parser


def main() -> int:
    args = _parser().parse_args()
    if args.command == "status":
        manifest_path = args.output_root / "MANIFEST.json"
        if not manifest_path.exists():
            print(
                json.dumps(
                    {
                        "schema_version": SCHEMA_VERSION,
                        "status": "NOT_CAPTURED",
                        "output_root": args.output_root.as_posix(),
                        "strategy_preregistered": False,
                        "eurusd_outcomes_loaded": False,
                        "broker_action_allowed": False,
                    },
                    indent=2,
                )
            )
            return 0
        result = json.loads(manifest_path.read_text(encoding="utf-8"))
        result["manifest_path"] = manifest_path.as_posix()
        result["manifest_sha256"] = sha256_file(manifest_path)
    else:
        result = run_census(
            args.output_root,
            timeout_seconds=args.timeout_seconds,
            maximum_targets=args.maximum_targets,
        )
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
