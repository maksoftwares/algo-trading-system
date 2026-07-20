from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

import pandas as pd


def canonical_hash(payload: Mapping[str, Any], field: str) -> str:
    clean = {key: value for key, value in payload.items() if key != field}
    encoded = json.dumps(clean, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object: {path}")
    return payload


def invert_direction(value: str) -> str:
    if value == "LONG":
        return "SHORT"
    if value == "SHORT":
        return "LONG"
    raise ValueError(f"Unsupported source direction: {value}")


def prepare_source_candidates(
    candidates: pd.DataFrame,
    *,
    source: str,
    antisignal_family: str,
) -> pd.DataFrame:
    if candidates.empty:
        return pd.DataFrame(
            columns=[
                "candidate_id",
                "source_candidate_id",
                "source_family",
                "original_direction",
                "family",
                "direction",
                "feature_time_utc",
            ]
        )
    required = {"candidate_id", "family", "direction", "feature_time_utc"}
    if missing := sorted(required - set(candidates.columns)):
        raise ValueError(f"Source candidates are missing columns: {missing}")
    result = candidates.copy()
    result["source_candidate_id"] = result["candidate_id"].astype(str)
    result["source_family"] = source
    result["original_direction"] = result["direction"].astype(str)
    result["direction"] = result["original_direction"].map(invert_direction)
    result["family"] = antisignal_family
    result["candidate_id"] = (
        "V68:"
        + source
        + ":"
        + result["source_candidate_id"]
        + ":"
        + result["direction"]
    )
    if result["candidate_id"].duplicated().any():
        raise ValueError("V68 source preparation produced duplicate IDs")
    return result


def route_one_per_day(
    candidates: pd.DataFrame, *, source_priority: Sequence[str]
) -> tuple[pd.DataFrame, dict[str, Any]]:
    required = {
        "candidate_id",
        "source_family",
        "direction",
        "feature_time_utc",
    }
    if missing := sorted(required - set(candidates.columns)):
        raise ValueError(f"V68 candidates are missing columns: {missing}")
    priority = {source: index for index, source in enumerate(source_priority)}
    unknown = sorted(set(candidates["source_family"].astype(str)) - set(priority))
    if unknown:
        raise ValueError(f"Unknown V68 source families: {unknown}")
    if candidates.empty:
        return candidates.copy(), {
            "raw_candidate_rows": 0,
            "selected_candidate_rows": 0,
            "raw_rows_by_source": {},
            "selected_rows_by_source": {},
            "multi_source_dates": 0,
            "same_timestamp_ties": 0,
        }
    routed = candidates.copy()
    routed["feature_time_utc"] = pd.to_datetime(routed["feature_time_utc"], utc=True)
    routed["date_utc"] = routed["feature_time_utc"].dt.date.astype(str)
    routed["source_priority"] = routed["source_family"].map(priority).astype(int)
    routed = routed.sort_values(
        ["feature_time_utc", "source_priority", "candidate_id"], kind="stable"
    ).reset_index(drop=True)
    source_counts_by_date = routed.groupby("date_utc")["source_family"].nunique()
    tie_sizes = routed.groupby(["date_utc", "feature_time_utc"]).size()
    selected = routed.groupby("date_utc", sort=True, as_index=False).head(1).copy()
    selected = selected.sort_values(
        ["feature_time_utc", "source_priority", "candidate_id"], kind="stable"
    ).reset_index(drop=True)
    if selected["date_utc"].duplicated().any():
        raise ValueError("V68 router selected more than one candidate per UTC date")
    audit = {
        "raw_candidate_rows": int(len(routed)),
        "selected_candidate_rows": int(len(selected)),
        "raw_rows_by_source": {
            str(key): int(value)
            for key, value in routed["source_family"].value_counts().items()
        },
        "selected_rows_by_source": {
            str(key): int(value)
            for key, value in selected["source_family"].value_counts().items()
        },
        "multi_source_dates": int((source_counts_by_date > 1).sum()),
        "same_timestamp_ties": int((tie_sizes > 1).sum()),
    }
    return selected, audit
