from __future__ import annotations

import argparse
import csv
import json
import math
import statistics
import zipfile
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from audit_neutral_gdelt_gkg_source import (
    EXPECTED_FIELDS,
    TONE_INDEX,
    _central_bank_side,
)
from run_neutral_gdelt_coverage_census import MAX_CSV_FIELD_BYTES, sha256_file

ROOT = Path(__file__).resolve().parent
CONFIG_PATH = (
    ROOT
    / "config"
    / "frozen_neutral_gdelt_relative_tone_design_audit_v1.json"
)
LOCK_PATH = (
    ROOT
    / (
        "EURUSD_NEUTRAL_GDELT_RELATIVE_TONE_DESIGN_AUDIT_"
        "PREREG_2026_07_28.sha256.json"
    )
)
DEFAULT_OUTPUT_PATH = Path(
    "D:/AlgoTradingData/source-audits/gdelt-gkg-coverage-census-v1/"
    "RELATIVE_TONE_DESIGN_AUDIT.json"
)
SCHEMA_VERSION = "eurusd_neutral_gdelt_relative_tone_design_audit_result_v1"
csv.field_size_limit(max(csv.field_size_limit(), MAX_CSV_FIELD_BYTES))


def _json_bytes(value: Any) -> bytes:
    return (
        json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    ).encode("utf-8")


def load_and_verify_preregistration() -> tuple[dict[str, Any], dict[str, Any]]:
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    lock = json.loads(LOCK_PATH.read_text(encoding="utf-8"))
    if lock.get("locked_before_historical_gkg_tone_inspection") is not True:
        raise RuntimeError("Relative-tone audit was not locked before inspection")
    for relative, expected in lock["files"].items():
        if sha256_file(ROOT / relative) != expected:
            raise RuntimeError(f"Relative-tone lock mismatch: {relative}")
    source = config["source_census"]
    source_path = Path(source["manifest_path"])
    if sha256_file(source_path) != source["manifest_sha256"]:
        raise RuntimeError("GDELT census manifest drift")
    if (
        config.get("eurusd_prices_allowed") is not False
        or config.get("eurusd_returns_allowed") is not False
        or config.get("oracle_rows_allowed") is not False
        or config.get("pnl_allowed") is not False
        or config.get("broker_action_allowed") is not False
    ):
        raise RuntimeError("Relative-tone safety contract is incomplete")
    return config, lock


def parse_tone_archive(
    archive_path: Path,
    *,
    entry_date_utc: str,
    batch_timestamp_utc: str,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with zipfile.ZipFile(archive_path) as archive:
        members = archive.namelist()
        if len(members) != 1:
            raise RuntimeError("GDELT archive must contain exactly one member")
        with archive.open(members[0]) as stream:
            for raw in stream:
                row = next(
                    csv.reader(
                        [raw.decode("utf-8", errors="strict")],
                        delimiter="\t",
                    )
                )
                if len(row) != EXPECTED_FIELDS:
                    raise RuntimeError("GDELT GKG row has unexpected width")
                if row[1] != batch_timestamp_utc:
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
                tone: float | None
                try:
                    tone = float(row[TONE_INDEX].split(",", 1)[0])
                except ValueError:
                    tone = None
                if tone is not None and not math.isfinite(tone):
                    tone = None
                rows.append(
                    {
                        "entry_date_utc": entry_date_utc,
                        "batch_timestamp_utc": batch_timestamp_utc,
                        "record_id": row[0],
                        "side": side,
                        "source_common_name": source.lower(),
                        "document_identifier": document_identifier,
                        "tone": tone,
                    }
                )
    return rows


def _deduplicate_documents(
    rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    selected: dict[str, dict[str, Any]] = {}
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
            value["side"],
            value["source_common_name"],
            value["document_identifier"],
        ),
    )


def _median_absolute_deviation(values: list[float]) -> float:
    center = statistics.median(values)
    return statistics.median(abs(value - center) for value in values)


def evaluate_candidate_transform(
    config: dict[str, Any],
    rows: list[dict[str, Any]],
) -> dict[str, Any]:
    documents = _deduplicate_documents(rows)
    finite_documents = [
        row for row in documents if row["tone"] is not None
    ]
    tone_parse_rate = (
        len(finite_documents) / len(documents) if documents else 0.0
    )
    by_date: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in finite_documents:
        by_date[row["entry_date_utc"]].append(row)
    candidate_config = config["frozen_candidate_transform"]
    minimum_sources = int(
        candidate_config["minimum_unique_sources_per_side_per_date"]
    )
    maximum_source_share = float(
        candidate_config[
            "maximum_largest_source_share_per_side_per_date"
        ]
    )
    dispersion_floor = float(candidate_config["dispersion_floor"])
    minimum_strength = float(candidate_config["minimum_strength"])
    date_results: list[dict[str, Any]] = []
    configured_dates = json.loads(
        (
            ROOT
            / "config"
            / "frozen_neutral_gdelt_coverage_census_v1.json"
        ).read_text(encoding="utf-8")
    )["sampling"]["entry_dates_utc"]
    for entry_date in configured_dates:
        date_rows = by_date.get(entry_date, [])
        side_values: dict[str, dict[str, Any]] = {}
        source_quorum = True
        for side in ("ECB", "FED"):
            selected = [row for row in date_rows if row["side"] == side]
            source_documents = Counter(
                row["source_common_name"] for row in selected
            )
            unique_sources = len(source_documents)
            largest_source_share = (
                max(source_documents.values()) / len(selected)
                if selected
                else 0.0
            )
            source_scores = [
                statistics.median(
                    [
                        float(row["tone"])
                        for row in selected
                        if row["source_common_name"] == source
                    ]
                )
                for source in sorted(source_documents)
            ]
            side_values[side] = {
                "strict_documents_with_finite_tone": len(selected),
                "unique_sources": unique_sources,
                "largest_source_share": largest_source_share,
                "source_scores": source_scores,
                "side_score": (
                    statistics.median(source_scores)
                    if source_scores
                    else None
                ),
            }
            if (
                unique_sources < minimum_sources
                or largest_source_share > maximum_source_share
            ):
                source_quorum = False
        relative_tone: float | None = None
        pooled_dispersion: float | None = None
        effective_dispersion: float | None = None
        strength: float | None = None
        candidate_side: str | None = None
        if source_quorum:
            all_source_scores = [
                *side_values["ECB"]["source_scores"],
                *side_values["FED"]["source_scores"],
            ]
            pooled_dispersion = _median_absolute_deviation(
                all_source_scores
            )
            effective_dispersion = max(
                dispersion_floor,
                pooled_dispersion,
            )
            relative_tone = (
                float(side_values["ECB"]["side_score"])
                - float(side_values["FED"]["side_score"])
            )
            strength = abs(relative_tone) / effective_dispersion
            if strength >= minimum_strength:
                if relative_tone > 0:
                    candidate_side = "LONG"
                elif relative_tone < 0:
                    candidate_side = "SHORT"
        date_results.append(
            {
                "entry_date_utc": entry_date,
                "source_quorum": source_quorum,
                "by_side": side_values,
                "relative_tone": relative_tone,
                "pooled_dispersion": pooled_dispersion,
                "effective_dispersion": effective_dispersion,
                "strength": strength,
                "candidate_side": candidate_side,
            }
        )
    candidates = [
        row for row in date_results if row["candidate_side"] is not None
    ]
    side_counts = Counter(row["candidate_side"] for row in candidates)
    largest_direction_share = (
        max(side_counts.values()) / len(candidates) if candidates else 0.0
    )
    gates = config["source_only_capacity_gates"]
    source_quorum_dates = sum(
        bool(row["source_quorum"]) for row in date_results
    )
    gate_results = {
        "finite_tone_parse_rate": (
            tone_parse_rate
            >= float(gates["minimum_finite_tone_parse_rate"])
        ),
        "dates_with_two_sources_each_side": (
            source_quorum_dates
            >= int(gates["minimum_dates_with_two_sources_each_side"])
        ),
        "candidate_signal_dates": (
            len(candidates)
            >= int(gates["minimum_candidate_signal_dates"])
        ),
        "long_candidate_dates": (
            side_counts["LONG"]
            >= int(gates["minimum_long_candidate_dates"])
        ),
        "short_candidate_dates": (
            side_counts["SHORT"]
            >= int(gates["minimum_short_candidate_dates"])
        ),
        "largest_direction_share": (
            largest_direction_share
            <= float(gates["maximum_largest_direction_share"])
        ),
    }
    passed = all(gate_results.values())
    return {
        "strict_deduplicated_documents": len(documents),
        "finite_tone_documents": len(finite_documents),
        "finite_tone_parse_rate": tone_parse_rate,
        "source_quorum_dates": source_quorum_dates,
        "candidate_signal_dates": len(candidates),
        "candidate_side_counts": {
            side: int(side_counts[side]) for side in ("LONG", "SHORT")
        },
        "largest_direction_share": largest_direction_share,
        "gate_results": gate_results,
        "all_source_only_gates_passed": passed,
        "decision": (
            "PASS_PREREGISTER_PROSPECTIVE_GDELT_RELATIVE_TONE_EXPERT"
            if passed
            else "FAIL_CLOSE_GDELT_RELATIVE_TONE_LANE"
        ),
        "dates": date_results,
    }


def run_audit(output_path: Path = DEFAULT_OUTPUT_PATH) -> dict[str, Any]:
    if output_path.exists():
        raise RuntimeError(
            "Relative-tone audit already exists; use status instead"
        )
    config, lock = load_and_verify_preregistration()
    census_path = Path(config["source_census"]["manifest_path"])
    census = json.loads(census_path.read_text(encoding="utf-8"))
    if census["summary"].get("all_capacity_gates_passed") is not True:
        raise RuntimeError("GDELT source census did not pass capacity gates")
    if any(
        census.get(field) is not False
        for field in (
            "eurusd_prices_loaded",
            "eurusd_returns_loaded",
            "eurusd_outcomes_loaded",
            "oracle_rows_loaded",
            "pnl_loaded",
            "signal_generated",
            "broker_action_allowed",
        )
    ):
        raise RuntimeError("GDELT census contains forbidden strategy evidence")
    census_root = census_path.parent
    rows: list[dict[str, Any]] = []
    for file_result in census["files"]:
        if file_result["status"] != "SUCCESS_VALIDATED":
            continue
        archive_path = census_root / file_result["archive_relative_path"]
        if sha256_file(archive_path) != file_result["archive_sha256"]:
            raise RuntimeError(
                f"GDELT archive drift: {file_result['archive_relative_path']}"
            )
        rows.extend(
            parse_tone_archive(
                archive_path,
                entry_date_utc=file_result["entry_date_utc"],
                batch_timestamp_utc=file_result["batch_timestamp_utc"],
            )
        )
    evaluation = evaluate_candidate_transform(config, rows)
    result = {
        "schema_version": SCHEMA_VERSION,
        "evaluated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "SOURCE_ONLY_DESIGN_AUDIT_COMPLETE",
        "source_census_manifest_path": census_path.as_posix(),
        "source_census_manifest_sha256": sha256_file(census_path),
        "preregistration_lock_path": LOCK_PATH.name,
        "preregistration_lock_sha256": sha256_file(LOCK_PATH),
        "preregistration_locked_at_utc": lock["locked_at_utc"],
        "strategy_preregistered": False,
        "eurusd_prices_loaded": False,
        "eurusd_returns_loaded": False,
        "oracle_rows_loaded": False,
        "pnl_loaded": False,
        "signal_generated": False,
        "broker_action_allowed": False,
        "evaluation": evaluation,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(_json_bytes(result))
    return {
        **result,
        "result_path": output_path.as_posix(),
        "result_sha256": sha256_file(output_path),
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("run", "status"))
    parser.add_argument(
        "--output-path",
        type=Path,
        default=DEFAULT_OUTPUT_PATH,
    )
    return parser


def main() -> int:
    args = _parser().parse_args()
    if args.command == "run":
        result = run_audit(args.output_path)
    elif not args.output_path.exists():
        result = {
            "schema_version": SCHEMA_VERSION,
            "status": "NOT_RUN",
            "strategy_preregistered": False,
            "eurusd_prices_loaded": False,
            "oracle_rows_loaded": False,
            "broker_action_allowed": False,
        }
    else:
        result = json.loads(args.output_path.read_text(encoding="utf-8"))
        result["result_path"] = args.output_path.as_posix()
        result["result_sha256"] = sha256_file(args.output_path)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
