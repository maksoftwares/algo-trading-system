from __future__ import annotations

import hashlib
import json
import zipfile
from pathlib import Path

from run_neutral_gdelt_coverage_census import (
    build_targets,
    load_and_verify_preregistration,
    parse_archive,
    summarize_census,
)


def _gkg_row(
    record_id: str,
    timestamp: str,
    *,
    side: str,
    source: str,
    document: str,
) -> str:
    values = [""] * 27
    values[0] = record_id
    values[1] = timestamp
    values[3] = source
    values[4] = document
    values[8] = "ECON_CENTRALBANK,1;EPU_CATS_MONETARY_POLICY,1"
    values[13] = (
        "European Central Bank" if side == "ECB" else "Federal Reserve"
    )
    return "\t".join(values)


def test_frozen_targets_are_exact_and_lock_verifies() -> None:
    config, _ = load_and_verify_preregistration()
    targets = build_targets(config)
    assert len(targets) == 96
    assert targets[0]["entry_date_utc"] == "2025-08-05"
    assert targets[0]["batch_timestamp_utc"] == "20250804230000"
    assert targets[3]["batch_timestamp_utc"] == "20250804234500"
    assert targets[-1]["entry_date_utc"] == "2026-07-21"
    assert targets[-1]["batch_timestamp_utc"] == "20260720234500"
    assert all(target["url"].startswith("http://") for target in targets)


def test_archive_parser_is_strict_and_keeps_source_only_fields(
    tmp_path: Path,
) -> None:
    target = {
        "entry_date_utc": "2026-07-21",
        "batch_timestamp_utc": "20260720230000",
        "url": "http://example.test/archive.zip",
    }
    archive_path = tmp_path / "sample.zip"
    rows = [
        _gkg_row(
            "one",
            target["batch_timestamp_utc"],
            side="ECB",
            source="ECB.example",
            document="https://ecb.example/one",
        ),
        _gkg_row(
            "two",
            target["batch_timestamp_utc"],
            side="FED",
            source="Fed.example",
            document="https://fed.example/two",
        ),
    ]
    with zipfile.ZipFile(
        archive_path,
        "w",
        compression=zipfile.ZIP_DEFLATED,
    ) as archive:
        archive.writestr("sample.gkg.csv", "\n".join(rows) + "\n")
    validation, strict = parse_archive(archive_path, target)
    assert validation["rows"] == 2
    assert validation["field_count_distribution"] == {"27": 2}
    assert [row["side"] for row in strict] == ["ECB", "FED"]
    assert all("tone" not in row for row in strict)
    assert hashlib.sha256(archive_path.read_bytes()).hexdigest()


def test_archive_parser_accepts_valid_large_gkg_field(tmp_path: Path) -> None:
    target = {
        "entry_date_utc": "2026-07-21",
        "batch_timestamp_utc": "20260720230000",
        "url": "http://example.test/archive.zip",
    }
    values = _gkg_row(
        "large",
        target["batch_timestamp_utc"],
        side="ECB",
        source="large.example",
        document="https://large.example/article",
    ).split("\t")
    values[23] = "X" * 200_000
    archive_path = tmp_path / "large.zip"
    with zipfile.ZipFile(
        archive_path,
        "w",
        compression=zipfile.ZIP_DEFLATED,
    ) as archive:
        archive.writestr("large.gkg.csv", "\t".join(values) + "\n")
    validation, strict = parse_archive(archive_path, target)
    assert validation["rows"] == 1
    assert strict[0]["document_identifier"] == (
        "https://large.example/article"
    )


def test_summary_applies_every_frozen_capacity_gate() -> None:
    config, _ = load_and_verify_preregistration()
    targets = build_targets(config)
    file_results = [
        {
            **target,
            "status": "SUCCESS_VALIDATED",
        }
        for target in targets
    ]
    strict_rows: list[dict[str, str]] = []
    entry_dates = config["sampling"]["entry_dates_utc"]
    for index, entry_date in enumerate(entry_dates):
        batch = next(
            target["batch_timestamp_utc"]
            for target in targets
            if target["entry_date_utc"] == entry_date
        )
        for side in ("ECB", "FED"):
            strict_rows.append(
                {
                    "entry_date_utc": entry_date,
                    "batch_timestamp_utc": batch,
                    "record_id": f"{side}-{index}",
                    "side": side,
                    "source_common_name": f"source-{index % 12}.example",
                    "document_identifier": (
                        f"https://{side.lower()}.example/{index}"
                    ),
                    "qualifying_themes": "ECON_CENTRALBANK",
                }
            )
    summary, normalized = summarize_census(
        config,
        targets,
        file_results,
        strict_rows,
    )
    assert len(normalized) == 48
    assert summary["all_capacity_gates_passed"] is True
    assert all(summary["gate_results"].values())
    assert summary["decision"] == (
        "PASS_PREREGISTER_SEPARATE_PROSPECTIVE_DESIGN"
    )
    assert "eurusd" not in json.dumps(summary).lower()


def test_duplicate_documents_and_concentrated_source_fail() -> None:
    config, _ = load_and_verify_preregistration()
    targets = build_targets(config)
    file_results = [
        {
            **target,
            "status": "SUCCESS_VALIDATED",
        }
        for target in targets
    ]
    repeated = {
        "entry_date_utc": "2025-08-05",
        "batch_timestamp_utc": "20250804230000",
        "record_id": "same",
        "side": "FED",
        "source_common_name": "single.example",
        "document_identifier": "https://single.example/same",
        "qualifying_themes": "ECON_CENTRALBANK",
    }
    summary, normalized = summarize_census(
        config,
        targets,
        file_results,
        [repeated.copy() for _ in range(10)],
    )
    assert len(normalized) == 1
    assert summary["duplicate_document_share"] == 0.9
    assert summary["gate_results"]["duplicate_document_share"] is False
    assert summary["gate_results"]["fed_source_concentration"] is False
    assert summary["all_capacity_gates_passed"] is False
    assert summary["decision"] == "FAIL_CLOSE_GDELT_SOURCE_LANE"
