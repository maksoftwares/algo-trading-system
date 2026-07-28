from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import zipfile
from collections import Counter
from pathlib import Path
from typing import Any

DEFAULT_SAMPLE = Path(
    "D:/AlgoTradingData/source-audits/gdelt-gkg-v1/raw/"
    "20260728183000.gkg.csv.zip"
)
DEFAULT_EXPECTED_MD5 = "51b4d4a4dde88aeab93506f5468003ec"
DEFAULT_OBSERVED_AT = "2026-07-28T18:32:10.333130Z"

THEME_INDEX = 8
ORGANIZATION_INDEXES = (13, 14)
TONE_INDEX = 15
ALL_NAMES_INDEX = 23
EXPECTED_FIELDS = 27
TRACKED_THEMES = (
    "EPU_POLICY_FEDERAL_RESERVE",
    "ECON_CENTRALBANK",
    "ECON_WORLDCURRENCIES_EURO",
    "ECON_WORLDCURRENCIES_US_DOLLAR",
)


def _theme_tokens(row: list[str]) -> set[str]:
    return {
        block.split(",", 1)[0].upper()
        for block in row[THEME_INDEX].split(";")
        if block
    }


def _names(row: list[str]) -> str:
    values = [row[index] for index in ORGANIZATION_INDEXES]
    values.append(row[ALL_NAMES_INDEX])
    return ";".join(values).upper()


def _central_bank_side(row: list[str]) -> str | None:
    themes = _theme_tokens(row)
    if not (
        "ECON_CENTRALBANK" in themes
        or any("MONETARY_POLICY" in theme for theme in themes)
    ):
        return None
    names = _names(row)
    if "EUROPEAN CENTRAL BANK" in names or re.search(
        r"(^|[;,])ECB([,;]|$)", names
    ):
        return "ECB"
    if "FEDERAL RESERVE" in names or re.search(
        r"(^|[;,])FED([,;]|$)", names
    ):
        return "FED"
    return None


def audit_gkg_sample(
    sample_path: Path = DEFAULT_SAMPLE,
    *,
    expected_md5: str = DEFAULT_EXPECTED_MD5,
    observed_at_utc: str = DEFAULT_OBSERVED_AT,
) -> dict[str, Any]:
    payload = sample_path.read_bytes()
    actual_md5 = hashlib.md5(payload).hexdigest()
    if actual_md5 != expected_md5.lower():
        raise RuntimeError("GDELT sample does not match provider MD5")
    theme_counts: Counter[str] = Counter()
    side_counts: Counter[str] = Counter()
    examples: dict[str, list[dict[str, Any]]] = {"ECB": [], "FED": []}
    field_counts: Counter[int] = Counter()
    timestamps: Counter[str] = Counter()
    with zipfile.ZipFile(sample_path) as archive:
        members = archive.namelist()
        if len(members) != 1:
            raise RuntimeError("GDELT sample must contain exactly one member")
        member = members[0]
        member_info = archive.getinfo(member)
        with archive.open(member) as stream:
            for raw in stream:
                row = next(
                    csv.reader(
                        [raw.decode("utf-8", errors="strict")],
                        delimiter="\t",
                    )
                )
                field_counts[len(row)] += 1
                if len(row) != EXPECTED_FIELDS:
                    raise RuntimeError("GDELT GKG row has unexpected width")
                timestamps[row[1]] += 1
                themes = _theme_tokens(row)
                for theme in TRACKED_THEMES:
                    if theme in themes:
                        theme_counts[theme] += 1
                side = _central_bank_side(row)
                if side is None:
                    continue
                side_counts[side] += 1
                if len(examples[side]) < 3:
                    examples[side].append(
                        {
                            "record_id": row[0],
                            "source_common_name": row[3],
                            "document_identifier": row[4],
                            "tone": float(row[TONE_INDEX].split(",", 1)[0]),
                        }
                    )
    return {
        "schema_version": "eurusd_neutral_gdelt_gkg_source_audit_v1",
        "status": (
            "FREE_TIMESTAMPED_SOURCE_ACCEPTED_FOR_PROSPECTIVE_CENSUS_ONLY"
        ),
        "source_audit_only": True,
        "strategy_preregistered": False,
        "eurusd_outcomes_loaded": False,
        "broker_action_allowed": False,
        "provider": "GDELT Project",
        "provider_lastupdate_url": (
            "http://data.gdeltproject.org/gdeltv2/lastupdate.txt"
        ),
        "sample_url": (
            "http://data.gdeltproject.org/gdeltv2/"
            "20260728183000.gkg.csv.zip"
        ),
        "sample_observed_at_utc": observed_at_utc,
        "sample_path": sample_path.as_posix(),
        "provider_expected_bytes": 7563257,
        "sample_bytes": len(payload),
        "provider_md5": expected_md5.lower(),
        "sample_md5": actual_md5,
        "sample_sha256": hashlib.sha256(payload).hexdigest(),
        "zip_members": members,
        "zip_member_compressed_bytes": member_info.compress_size,
        "zip_member_uncompressed_bytes": member_info.file_size,
        "rows": int(sum(field_counts.values())),
        "field_count_distribution": {
            str(key): int(value) for key, value in field_counts.items()
        },
        "gkg_timestamp_counts": dict(timestamps),
        "tracked_theme_counts": {
            theme: int(theme_counts[theme]) for theme in TRACKED_THEMES
        },
        "strict_central_bank_article_counts": {
            side: int(side_counts[side]) for side in ("ECB", "FED")
        },
        "strict_central_bank_examples": examples,
        "semantic_finding": (
            "GKG tone is document-level and strict ECB/Fed coverage can be "
            "asymmetric; no causal EURUSD side rule is justified by this "
            "single schema sample."
        ),
        "next_allowed_step": (
            "FREEZE AN OUTCOME-BLIND MULTI-DATE COVERAGE CENSUS BEFORE ANY "
            "EURUSD RETURN OR ORACLE MATCH IS LOADED"
        ),
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sample", type=Path, default=DEFAULT_SAMPLE)
    parser.add_argument("--expected-md5", default=DEFAULT_EXPECTED_MD5)
    parser.add_argument("--observed-at-utc", default=DEFAULT_OBSERVED_AT)
    return parser


def main() -> None:
    args = _parser().parse_args()
    result = audit_gkg_sample(
        args.sample,
        expected_md5=args.expected_md5,
        observed_at_utc=args.observed_at_utc,
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
