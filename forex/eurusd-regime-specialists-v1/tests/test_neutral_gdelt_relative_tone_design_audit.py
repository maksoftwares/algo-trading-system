from __future__ import annotations

import json
import zipfile
from pathlib import Path

from run_neutral_gdelt_relative_tone_design_audit import (
    evaluate_candidate_transform,
    load_and_verify_preregistration,
    parse_tone_archive,
)


def _record(
    *,
    entry_date: str,
    batch: str,
    side: str,
    source_index: int,
    tone: float,
) -> dict[str, object]:
    return {
        "entry_date_utc": entry_date,
        "batch_timestamp_utc": batch,
        "record_id": f"{side}-{source_index}",
        "side": side,
        "source_common_name": f"{side.lower()}-{source_index}.example",
        "document_identifier": (
            f"https://{side.lower()}-{source_index}.example/{entry_date}"
        ),
        "tone": tone,
    }


def test_relative_tone_lock_verifies_before_inspection() -> None:
    config, lock = load_and_verify_preregistration()
    assert lock["locked_before_historical_gkg_tone_inspection"] is True
    assert config["eurusd_prices_allowed"] is False
    assert config["oracle_rows_allowed"] is False


def test_frozen_transform_can_pass_with_balanced_source_only_sample() -> None:
    config, _ = load_and_verify_preregistration()
    entry_dates = json.loads(
        (
            Path(__file__).resolve().parents[1]
            / "config"
            / "frozen_neutral_gdelt_coverage_census_v1.json"
        ).read_text(encoding="utf-8")
    )["sampling"]["entry_dates_utc"]
    rows: list[dict[str, object]] = []
    for date_index, entry_date in enumerate(entry_dates[:8]):
        batch = entry_date.replace("-", "") + "000000"
        long_candidate = date_index < 4
        ecb_tone = 3.0 if long_candidate else -3.0
        fed_tone = -1.0 if long_candidate else 1.0
        for source_index in range(2):
            rows.append(
                _record(
                    entry_date=entry_date,
                    batch=batch,
                    side="ECB",
                    source_index=source_index,
                    tone=ecb_tone,
                )
            )
            rows.append(
                _record(
                    entry_date=entry_date,
                    batch=batch,
                    side="FED",
                    source_index=source_index,
                    tone=fed_tone,
                )
            )
    result = evaluate_candidate_transform(config, rows)
    assert result["source_quorum_dates"] == 8
    assert result["candidate_signal_dates"] == 8
    assert result["candidate_side_counts"] == {"LONG": 4, "SHORT": 4}
    assert result["all_source_only_gates_passed"] is True


def test_frozen_transform_rejects_tiny_relative_tone() -> None:
    config, _ = load_and_verify_preregistration()
    entry_date = "2025-08-05"
    rows = [
        _record(
            entry_date=entry_date,
            batch="20250804230000",
            side=side,
            source_index=source_index,
            tone=(0.1 if side == "ECB" else 0.0),
        )
        for side in ("ECB", "FED")
        for source_index in range(2)
    ]
    result = evaluate_candidate_transform(config, rows)
    first = result["dates"][0]
    assert first["source_quorum"] is True
    assert first["strength"] == 0.2
    assert first["candidate_side"] is None


def test_tone_parser_rejects_no_schema_and_reads_only_source_data(
    tmp_path: Path,
) -> None:
    values = [""] * 27
    values[0] = "record"
    values[1] = "20260720230000"
    values[3] = "ecb.example"
    values[4] = "https://ecb.example/article"
    values[8] = "ECON_CENTRALBANK,1"
    values[13] = "European Central Bank"
    values[15] = "2.5,3.0,0.5"
    path = tmp_path / "tone.zip"
    with zipfile.ZipFile(
        path,
        "w",
        compression=zipfile.ZIP_DEFLATED,
    ) as archive:
        archive.writestr("tone.gkg.csv", "\t".join(values) + "\n")
    rows = parse_tone_archive(
        path,
        entry_date_utc="2026-07-21",
        batch_timestamp_utc="20260720230000",
    )
    assert rows[0]["tone"] == 2.5
    assert "price" not in json.dumps(rows).lower()
    assert "oracle" not in json.dumps(rows).lower()
