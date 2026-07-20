from __future__ import annotations

from pathlib import Path
import sys

import pandas as pd
import pytest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from antisignal import (  # noqa: E402
    canonical_hash,
    invert_direction,
    prepare_source_candidates,
    route_one_per_day,
)
from lock_contract import matching_artifacts  # noqa: E402


def source_frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "candidate_id": ["source-1", "source-2"],
            "family": ["source", "source"],
            "direction": ["LONG", "SHORT"],
            "feature_time_utc": pd.to_datetime(
                ["2025-01-02T12:00:00Z", "2025-01-03T12:00:00Z"], utc=True
            ),
        }
    )


def test_direction_inversion_is_exact_and_rejects_unknown() -> None:
    assert invert_direction("LONG") == "SHORT"
    assert invert_direction("SHORT") == "LONG"
    with pytest.raises(ValueError, match="Unsupported"):
        invert_direction("FLAT")


def test_prepare_source_candidates_preserves_provenance() -> None:
    prepared = prepare_source_candidates(
        source_frame(), source="V44", antisignal_family="ANTI"
    )
    assert prepared["source_family"].eq("V44").all()
    assert prepared["family"].eq("ANTI").all()
    assert prepared["original_direction"].tolist() == ["LONG", "SHORT"]
    assert prepared["direction"].tolist() == ["SHORT", "LONG"]
    assert prepared["candidate_id"].str.startswith("V68:V44:").all()


def test_router_keeps_earliest_candidate_per_day_and_fixed_tie_priority() -> None:
    candidates = pd.DataFrame(
        {
            "candidate_id": ["v45-early", "v44-tie", "v45-tie", "next-day"],
            "source_family": ["V45", "V44", "V45", "V45"],
            "direction": ["LONG", "SHORT", "LONG", "SHORT"],
            "feature_time_utc": pd.to_datetime(
                [
                    "2025-01-02T12:00:00Z",
                    "2025-01-02T12:10:00Z",
                    "2025-01-02T12:10:00Z",
                    "2025-01-03T12:00:00Z",
                ],
                utc=True,
            ),
        }
    )
    selected, audit = route_one_per_day(candidates, source_priority=["V44", "V45"])
    assert selected["candidate_id"].tolist() == ["v45-early", "next-day"]
    assert audit["selected_candidate_rows"] == 2
    assert audit["multi_source_dates"] == 1
    assert audit["same_timestamp_ties"] == 1


def test_router_uses_priority_when_earliest_timestamp_is_tied() -> None:
    candidates = pd.DataFrame(
        {
            "candidate_id": ["v45", "v44"],
            "source_family": ["V45", "V44"],
            "direction": ["LONG", "SHORT"],
            "feature_time_utc": pd.to_datetime(
                ["2025-01-02T12:00:00Z", "2025-01-02T12:00:00Z"], utc=True
            ),
        }
    )
    selected, _ = route_one_per_day(candidates, source_priority=["V44", "V45"])
    assert selected["candidate_id"].tolist() == ["v44"]


def test_contract_hash_excludes_only_hash_field() -> None:
    payload = {"value": 1}
    payload["contract_sha256"] = canonical_hash(payload, "contract_sha256")
    assert payload["contract_sha256"] == canonical_hash(payload, "contract_sha256")
    payload["value"] = 2
    assert payload["contract_sha256"] != canonical_hash(payload, "contract_sha256")


def test_source_firewall_searches_the_declared_output_directory(
    tmp_path: Path,
) -> None:
    output = tmp_path / "outputs"
    output.mkdir()
    artifact = output / "SOURCE_VALIDATION_AUDIT.json"
    artifact.write_text("{}", encoding="utf-8")

    assert matching_artifacts(tmp_path, "outputs/SOURCE_VALIDATION_") == [artifact]
