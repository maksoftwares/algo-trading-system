from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Any, Iterable, Mapping

import numpy as np
import pandas as pd
import pyarrow.parquet as pq


REGISTRY_COLUMNS = [
    "candidate_id",
    "population",
    "family_id",
    "mechanic_id",
    "source_id",
    "source_candidate_id",
    "direction",
    "source_available_at",
    "signal_bar_end",
    "decision_time",
    "feature_cutoff_time",
    "entry_eligible_time",
    "action_id",
    "stop_atr",
    "target_r",
    "maximum_hold_minutes",
    "broker_executable_status",
    "lineage_status",
    "decision_time_inferred",
    "action_complete",
]

TIMESTAMP_COLUMNS = [
    "source_available_at",
    "signal_bar_end",
    "decision_time",
    "feature_cutoff_time",
    "entry_eligible_time",
]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def stable_id(*parts: Any) -> str:
    raw = "|".join("" if part is None else str(part) for part in parts)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def json_ready(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): json_ready(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_ready(item) for item in value]
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    if isinstance(value, np.generic):
        return json_ready(value.item())
    if isinstance(value, float) and not math.isfinite(value):
        return None
    if value is pd.NA or value is pd.NaT:
        return None
    return value


def write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.write_text(
        json.dumps(
            json_ready(payload),
            indent=2,
            sort_keys=True,
            allow_nan=False,
        )
        + "\n",
        encoding="utf-8",
    )


def resolve_path(repo_root: Path, value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else repo_root / path


def validate_allowed_columns(columns: Iterable[str], forbidden: Iterable[str]) -> None:
    requested = {str(column).lower() for column in columns}
    prohibited = {str(column).lower() for column in forbidden}
    overlap = sorted(requested & prohibited)
    if overlap:
        raise ValueError(f"Step 2 requested economic columns: {overlap}")


def load_metadata_frame(
    path: Path,
    file_format: str,
    columns: list[str],
    forbidden: Iterable[str],
) -> pd.DataFrame:
    validate_allowed_columns(columns, forbidden)
    if file_format == "parquet":
        available = set(pq.ParquetFile(path).schema_arrow.names)
        missing = sorted(set(columns) - available)
        if missing:
            raise ValueError(f"Missing metadata columns in {path}: {missing}")
        return pd.read_parquet(path, columns=columns)
    if file_format == "csv":
        header = set(pd.read_csv(path, nrows=0).columns)
        missing = sorted(set(columns) - header)
        if missing:
            raise ValueError(f"Missing metadata columns in {path}: {missing}")
        return pd.read_csv(path, usecols=columns)
    raise ValueError(f"Unsupported metadata format: {file_format}")


def apply_filter(frame: pd.DataFrame, values: Mapping[str, Any]) -> pd.DataFrame:
    selected = frame
    for column, value in values.items():
        if column not in selected.columns:
            raise ValueError(f"Filter column {column} is absent")
        selected = selected.loc[selected[column].eq(value)]
    return selected.copy()


def utc_series(values: pd.Series) -> pd.Series:
    return pd.to_datetime(values, utc=True, errors="raise")


def empty_time() -> pd.NaT:
    return pd.NaT


def candidate_record(
    *,
    source: Mapping[str, Any],
    source_candidate_id: str,
    family_id: str,
    mechanic_id: str,
    direction: str,
    signal_bar_end: Any = None,
    decision_time: Any = None,
    entry_eligible_time: Any = None,
    action_id: str,
    stop_atr: Any = None,
    target_r: Any = None,
    maximum_hold_minutes: Any = None,
    broker_executable_status: str = "UNKNOWN",
    decision_time_inferred: bool = False,
    action_complete: bool = False,
) -> dict[str, Any]:
    return {
        "candidate_id": stable_id(source["source_id"], source_candidate_id),
        "population": str(source["population"]),
        "family_id": str(family_id),
        "mechanic_id": str(mechanic_id),
        "source_id": str(source["source_id"]),
        "source_candidate_id": str(source_candidate_id),
        "direction": str(direction).upper(),
        "source_available_at": empty_time(),
        "signal_bar_end": signal_bar_end
        if signal_bar_end is not None
        else empty_time(),
        "decision_time": decision_time if decision_time is not None else empty_time(),
        "feature_cutoff_time": empty_time(),
        "entry_eligible_time": (
            entry_eligible_time if entry_eligible_time is not None else empty_time()
        ),
        "action_id": str(action_id),
        "stop_atr": stop_atr,
        "target_r": target_r,
        "maximum_hold_minutes": maximum_hold_minutes,
        "broker_executable_status": str(broker_executable_status),
        "lineage_status": str(source["lineage_status"]),
        "decision_time_inferred": bool(decision_time_inferred),
        "action_complete": bool(action_complete),
    }


def adapt_r1(frame: pd.DataFrame, source: Mapping[str, Any]) -> list[dict[str, Any]]:
    frame = frame.copy()
    frame["entry_time"] = utc_series(frame["entry_time"])
    records: list[dict[str, Any]] = []
    for row in frame.itertuples(index=False):
        source_candidate_id = stable_id(
            row.source_id,
            row.entry_time.isoformat(),
            str(row.direction).upper(),
        )
        records.append(
            candidate_record(
                source=source,
                source_candidate_id=source_candidate_id,
                family_id="R1_UPTREND",
                mechanic_id=str(row.source_id),
                direction=str(row.direction),
                entry_eligible_time=row.entry_time,
                action_id=f"R1_NATIVE_{row.source_id}",
                broker_executable_status="HISTORICALLY_EXECUTED_ONLY",
            )
        )
    return records


def adapt_regime_composite(
    frame: pd.DataFrame, source: Mapping[str, Any]
) -> list[dict[str, Any]]:
    family_map = {
        "CANONICAL_R2_DOWNTREND": "R2_DOWNTREND",
        "CANONICAL_R3_COMPRESSION": "R3_COMPRESSION",
    }
    frame = frame.copy()
    frame["signal_time"] = utc_series(frame["signal_time"])
    frame["scheduled_entry_time"] = utc_series(frame["scheduled_entry_time"])
    records: list[dict[str, Any]] = []
    for row in frame.itertuples(index=False):
        records.append(
            candidate_record(
                source=source,
                source_candidate_id=str(row.candidate_id),
                family_id=family_map[str(source["source_id"])],
                mechanic_id=str(row.mechanic),
                direction=str(row.direction),
                signal_bar_end=row.signal_time,
                decision_time=row.signal_time,
                entry_eligible_time=row.scheduled_entry_time,
                action_id=str(row.composite_id),
                stop_atr=float(row.stop_atr),
                maximum_hold_minutes=float(row.hold_hours) * 60.0,
                decision_time_inferred=True,
                action_complete=False,
            )
        )
    return records


def adapt_r4(frame: pd.DataFrame, source: Mapping[str, Any]) -> list[dict[str, Any]]:
    frame = frame.copy()
    frame["signal_time"] = utc_series(frame["signal_time"])
    frame["scheduled_entry_time"] = utc_series(frame["scheduled_entry_time"])
    records: list[dict[str, Any]] = []
    for row in frame.itertuples(index=False):
        action_id = f"{row.mechanic}__{row.geometry_id}"
        records.append(
            candidate_record(
                source=source,
                source_candidate_id=str(row.candidate_id),
                family_id="R4_CHOP",
                mechanic_id=str(row.mechanic),
                direction=str(row.direction),
                signal_bar_end=row.signal_time,
                decision_time=row.signal_time,
                entry_eligible_time=row.scheduled_entry_time,
                action_id=action_id,
                stop_atr=float(row.stop_atr),
                target_r=float(row.target_r),
                maximum_hold_minutes=float(row.hold_hours) * 60.0,
                decision_time_inferred=True,
                action_complete=True,
            )
        )
    return records


def adapt_r5(frame: pd.DataFrame, source: Mapping[str, Any]) -> list[dict[str, Any]]:
    frame = frame.copy()
    frame["signal_time"] = utc_series(frame["signal_time"])
    frame["scheduled_entry_time"] = utc_series(frame["scheduled_entry_time"])
    records: list[dict[str, Any]] = []
    for row in frame.itertuples(index=False):
        executable = "TRUE" if math.isclose(float(row.risk_weight), 1.0) else "FALSE"
        action_id = f"{row.router_id}__{row.geometry_id}"
        records.append(
            candidate_record(
                source=source,
                source_candidate_id=str(row.candidate_id),
                family_id="R5_TRANSITION",
                mechanic_id=str(row.router_mechanic),
                direction=str(row.direction),
                signal_bar_end=row.signal_time,
                decision_time=row.signal_time,
                entry_eligible_time=row.scheduled_entry_time,
                action_id=action_id,
                broker_executable_status=executable,
                decision_time_inferred=True,
                action_complete=False,
            )
        )
    return records


def adapt_v57(frame: pd.DataFrame, source: Mapping[str, Any]) -> list[dict[str, Any]]:
    action_map: dict[str, tuple[str, float | None]] = {
        "V7_SWING_HEALTH": ("SWING_2R_36H", 36.0 * 60.0),
        "V8_RETEST_HEALTH": ("INTRADAY_1P5R_12H", 12.0 * 60.0),
        "V25_CHOP": ("V25_FROZEN_CHOP_ACTION", None),
        "V57_BREAK_SWING_H4ADX_HIGH": ("SWING_2R_36H", 36.0 * 60.0),
    }
    frame = frame.copy()
    frame["signal_time"] = utc_series(frame["signal_time"])
    frame["entry_time"] = utc_series(frame["entry_time"])
    records: list[dict[str, Any]] = []
    for row in frame.itertuples(index=False):
        action_id, hold = action_map[str(row.sleeve_id)]
        records.append(
            candidate_record(
                source=source,
                source_candidate_id=str(row.trade_id),
                family_id=str(row.sleeve_id),
                mechanic_id=str(row.sleeve_id),
                direction=str(row.direction),
                signal_bar_end=row.signal_time,
                decision_time=row.signal_time,
                entry_eligible_time=row.entry_time,
                action_id=action_id,
                maximum_hold_minutes=hold,
                broker_executable_status="FROZEN_0P01_EQUIVALENT_UNVERIFIED",
                decision_time_inferred=True,
                action_complete=False,
            )
        )
    return records


ADAPTERS = {
    "R1_TAGGED_BOOK": adapt_r1,
    "REGIME_COMPOSITE_CANDIDATES": adapt_regime_composite,
    "R4_CANDIDATES": adapt_r4,
    "R5_ROUTER_SELECTED_METADATA": adapt_r5,
    "V57_ADDON_CANDIDATES": adapt_v57,
}


def build_candidate_registry(
    repo_root: Path, config: Mapping[str, Any]
) -> tuple[pd.DataFrame, dict[str, str]]:
    forbidden = config["audit_controls"]["forbidden_read_columns"]
    records: list[dict[str, Any]] = []
    source_hashes: dict[str, str] = {}
    for source in config["candidate_sources"]:
        path = resolve_path(repo_root, str(source["path"]))
        observed = sha256_file(path)
        if observed != str(source["sha256"]):
            raise ValueError(f"Candidate source hash mismatch: {source['source_id']}")
        source_hashes[str(source["source_id"])] = observed
        frame = load_metadata_frame(
            path,
            str(source["format"]),
            list(source["columns"]),
            forbidden,
        )
        frame = apply_filter(frame, source.get("filter", {}))
        if len(frame) != int(source["expected_candidates"]):
            raise ValueError(
                f"Candidate count changed for {source['source_id']}: {len(frame)}"
            )
        adapted = ADAPTERS[str(source["adapter"])](frame, source)
        if len(adapted) != len(frame):
            raise ValueError(f"Adapter dropped candidates for {source['source_id']}")
        records.extend(adapted)
    registry = pd.DataFrame(records, columns=REGISTRY_COLUMNS)
    for column in TIMESTAMP_COLUMNS:
        registry[column] = pd.to_datetime(registry[column], utc=True)
    for column in ("stop_atr", "target_r", "maximum_hold_minutes"):
        registry[column] = pd.to_numeric(registry[column], errors="coerce")
    if registry["candidate_id"].duplicated().any():
        raise ValueError("Namespaced canonical candidate IDs are not unique")
    return registry, source_hashes


def parquet_metadata(path: Path) -> dict[str, Any]:
    metadata = pq.ParquetFile(path)
    return {
        "rows": int(metadata.metadata.num_rows),
        "row_groups": int(metadata.metadata.num_row_groups),
        "columns": list(metadata.schema_arrow.names),
    }


def evidence_summary(source_id: str, path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    if source_id == "DUKASCOPY_XAU_BID_ASK":
        return {
            "symbol": payload["symbol"],
            "start_inclusive_utc": payload["window"]["start_inclusive_utc"],
            "end_exclusive_utc": payload["window"]["end_exclusive_utc"],
            "month_count": int(payload["month_count"]),
            "hour_file_count": int(payload["hour_file_count"]),
            "raw_event_count": int(payload["tick_count"]),
            "raw_bytes": int(payload["raw_bytes"]),
            "paid_data_used": bool(payload["paid_data_used"]),
        }
    if source_id == "DATABENTO_COMEX_GC_TRADES":
        job = payload["job"]
        return {
            "dataset": job["dataset"],
            "schema": job["schema"],
            "symbol": job["symbols"],
            "start_inclusive_utc": job["start"],
            "end_exclusive_utc": job["end"],
            "raw_event_count": int(job["record_count"]),
            "downloaded_files": int(
                len(payload["downloaded_files"])
                if isinstance(payload["downloaded_files"], list)
                else payload["downloaded_files"]
            ),
            "status": payload["status"],
            "live_delivery_verified": False,
        }
    if source_id == "CAPITAL_DUKASCOPY_TRANSFER":
        return {
            "start_inclusive_utc": payload["window"]["start_inclusive_utc"],
            "end_exclusive_utc": payload["window"]["end_exclusive_utc"],
            "capital_file_count": int(payload["capital_file_count"]),
            "dukascopy_file_count": int(payload["dukascopy_file_count"]),
            "missing_capital_dates": list(payload["missing_capital_dates"]),
        }
    if source_id == "C_TO_D_MIGRATION":
        return {
            "state": payload["state"],
            "destination_root": payload["destination_root"],
            "migrated_files": int(sum(item["files"] for item in payload["entries"])),
            "migrated_bytes": int(sum(item["bytes"] for item in payload["entries"])),
            "junctions_verified": int(payload["final_junctions_verified"]),
        }
    raise ValueError(f"Unknown source evidence adapter: {source_id}")


def build_source_inventory(
    repo_root: Path,
    config: Mapping[str, Any],
    candidate_hashes: Mapping[str, str],
) -> dict[str, Any]:
    artifacts: list[dict[str, Any]] = []
    seen_paths: set[str] = set()
    groups = (
        ("candidate", config["candidate_sources"]),
        ("decision_audit", config["decision_audits"]),
        ("action_inventory", config["action_inventories"]),
        ("source_evidence", config["source_evidence"]),
    )
    hash_mismatches = 0
    for kind, records in groups:
        for record in records:
            path = resolve_path(repo_root, str(record["path"])).resolve()
            path_key = str(path).lower()
            observed = sha256_file(path)
            expected = str(record["sha256"])
            if observed != expected:
                hash_mismatches += 1
            if path_key in seen_paths:
                continue
            seen_paths.add(path_key)
            item: dict[str, Any] = {
                "kind": kind,
                "source_id": str(record["source_id"]),
                "path": str(path),
                "exists": path.is_file(),
                "bytes": int(path.stat().st_size),
                "sha256": observed,
                "hash_matches": observed == expected,
            }
            if path.suffix.lower() == ".parquet":
                item["parquet_metadata"] = parquet_metadata(path)
            if kind == "source_evidence":
                item["role"] = str(record["role"])
                item["coverage"] = evidence_summary(str(record["source_id"]), path)
            artifacts.append(item)
    return {
        "schema_version": "xauusd_step_2_source_inventory_v1",
        "stage": config["stage"],
        "metadata_only": True,
        "candidate_source_hashes": dict(candidate_hashes),
        "artifact_count": len(artifacts),
        "hash_mismatches": hash_mismatches,
        "artifacts": artifacts,
    }


def candidate_registry_counts(
    repo_root: Path,
    config: Mapping[str, Any],
    registry: pd.DataFrame,
) -> dict[str, Any]:
    forbidden = config["audit_controls"]["forbidden_read_columns"]
    decision_reports: dict[str, Any] = {}
    addon_ids: set[str] | None = None
    for source in config["decision_audits"]:
        path = resolve_path(repo_root, str(source["path"]))
        if sha256_file(path) != str(source["sha256"]):
            raise ValueError(f"Decision audit hash mismatch: {source['source_id']}")
        frame = load_metadata_frame(
            path,
            "parquet",
            list(source["columns"]),
            forbidden,
        )
        if len(frame) != int(source["expected_rows"]):
            raise ValueError(f"Decision count changed for {source['source_id']}")
        report = {
            "rows": int(len(frame)),
            "unique_trade_ids": int(frame["trade_id"].astype(str).nunique()),
            "accepted": int(frame["accepted"].astype(bool).sum()),
            "rejected": int((~frame["accepted"].astype(bool)).sum()),
            "decision_reason_counts": {
                str(key): int(value)
                for key, value in frame["decision_reason"]
                .value_counts()
                .sort_index()
                .items()
            },
        }
        decision_reports[str(source["source_id"])] = report
        if source["source_id"] == "V59_ADDON_ACCOUNT_DECISIONS":
            addon_ids = set(frame["trade_id"].astype(str))

    registry_addon_ids = set(
        registry.loc[
            registry["source_id"].eq("CANONICAL_V57_ADDONS"),
            "source_candidate_id",
        ].astype(str)
    )
    by_family = {
        str(key): int(value)
        for key, value in registry.groupby("family_id", sort=True).size().items()
    }
    by_source = {
        str(key): int(value)
        for key, value in registry.groupby("source_id", sort=True).size().items()
    }
    by_direction = {
        str(key): int(value)
        for key, value in registry["direction"].value_counts().sort_index().items()
    }
    expected_by_family = next(
        item["expected_by_family"]
        for item in config["candidate_sources"]
        if item["source_id"] == "CANONICAL_V57_ADDONS"
    )
    addon_family_reconciles = all(
        by_family.get(family, 0) == int(expected)
        for family, expected in expected_by_family.items()
    )
    return {
        "schema_version": "xauusd_step_2_candidate_registry_counts_v1",
        "population": "CANONICAL",
        "candidate_rows": int(len(registry)),
        "unique_candidate_ids": int(registry["candidate_id"].nunique()),
        "duplicate_candidate_ids": int(registry["candidate_id"].duplicated().sum()),
        "by_source": by_source,
        "by_family": by_family,
        "by_direction": by_direction,
        "by_lineage_status": {
            str(key): int(value)
            for key, value in registry.groupby("lineage_status", sort=True)
            .size()
            .items()
        },
        "broker_executable_status": {
            str(key): int(value)
            for key, value in registry["broker_executable_status"]
            .value_counts()
            .sort_index()
            .items()
        },
        "action_identity_present": int(registry["action_id"].notna().sum()),
        "complete_action_geometry": int(registry["action_complete"].sum()),
        "decision_audits": decision_reports,
        "reconciliation": {
            "total_matches_expected": len(registry)
            == int(config["expected"]["canonical_candidates"]),
            "unique_ids_match_total": registry["candidate_id"].nunique()
            == len(registry),
            "addon_family_counts_match": addon_family_reconciles,
            "v59_addon_decision_ids_match_candidate_ids": addon_ids
            == registry_addon_ids,
            "v59_v60_accepted_trade_control": int(
                config["expected"]["v59_v60_accepted_trades"]
            ),
        },
    }


def action_multiplicity(
    repo_root: Path,
    config: Mapping[str, Any],
    registry: pd.DataFrame,
) -> dict[str, Any]:
    forbidden = config["audit_controls"]["forbidden_read_columns"]
    reports: dict[str, Any] = {}
    for source in config["action_inventories"]:
        path = resolve_path(repo_root, str(source["path"]))
        if sha256_file(path) != str(source["sha256"]):
            raise ValueError(f"Action source hash mismatch: {source['source_id']}")
        frame = load_metadata_frame(
            path,
            "parquet",
            list(source["columns"]),
            forbidden,
        )
        if len(frame) != int(source["expected_rows"]):
            raise ValueError(f"Action row count changed for {source['source_id']}")
        candidate_key = ["event_id", "direction"]
        multiplicity = frame.groupby(candidate_key, sort=False).size()
        reports[str(source["source_id"])] = {
            "population": str(source["population"]),
            "action_rows": int(len(frame)),
            "unique_event_ids": int(frame["event_id"].nunique()),
            "unique_candidate_directions": int(len(multiplicity)),
            "duplicate_event_direction_action_rows": int(
                frame.duplicated([*candidate_key, "action_id"]).sum()
            ),
            "actions_per_candidate_distribution": {
                str(key): int(value)
                for key, value in multiplicity.value_counts().sort_index().items()
            },
            "action_id_counts": {
                str(key): int(value)
                for key, value in frame["action_id"].value_counts().sort_index().items()
            },
            "statistical_treatment": "SIBLING_ACTIONS_ARE_NOT_INDEPENDENT",
        }
    return {
        "schema_version": "xauusd_step_2_action_multiplicity_v1",
        "canonical": {
            "candidate_rows": int(len(registry)),
            "action_rows": int(len(registry)),
            "one_primary_action_per_candidate": True,
            "missing_action_identity": int(registry["action_id"].isna().sum()),
        },
        "separate_populations": reports,
    }


def timestamp_audit(registry: pd.DataFrame) -> dict[str, Any]:
    def greater_than_count(frame: pd.DataFrame, left: str, right: str) -> int:
        if frame.empty:
            return 0
        left_values = pd.to_datetime(frame[left], utc=True, errors="raise")
        right_values = pd.to_datetime(frame[right], utc=True, errors="raise")
        return int((left_values > right_values).sum())

    counts = {
        column: {
            "present": int(registry[column].notna().sum()),
            "missing": int(registry[column].isna().sum()),
        }
        for column in TIMESTAMP_COLUMNS
    }
    decision_entry = registry.loc[
        registry["decision_time"].notna() & registry["entry_eligible_time"].notna()
    ]
    signal_decision = registry.loc[
        registry["signal_bar_end"].notna() & registry["decision_time"].notna()
    ]
    source_cutoff = registry.loc[
        registry["source_available_at"].notna()
        & registry["feature_cutoff_time"].notna()
    ]
    cutoff_decision = registry.loc[
        registry["feature_cutoff_time"].notna() & registry["decision_time"].notna()
    ]
    prelabel_complete = (
        registry[
            [
                "source_available_at",
                "signal_bar_end",
                "decision_time",
                "feature_cutoff_time",
                "entry_eligible_time",
            ]
        ]
        .notna()
        .all(axis=1)
    )
    return {
        "schema_version": "xauusd_step_2_timestamp_availability_audit_v1",
        "required_invariant": "source_available_at <= feature_cutoff_time <= decision_time <= entry_eligible_time",
        "clock_completeness": counts,
        "prelabel_complete_clock_rows": int(prelabel_complete.sum()),
        "prelabel_incomplete_clock_rows": int((~prelabel_complete).sum()),
        "available_ordering_checks": {
            "signal_bar_end_after_decision": greater_than_count(
                signal_decision, "signal_bar_end", "decision_time"
            ),
            "source_available_after_feature_cutoff": greater_than_count(
                source_cutoff, "source_available_at", "feature_cutoff_time"
            ),
            "feature_cutoff_after_decision": greater_than_count(
                cutoff_decision, "feature_cutoff_time", "decision_time"
            ),
            "decision_after_entry_eligible": greater_than_count(
                decision_entry, "decision_time", "entry_eligible_time"
            ),
        },
        "join_policy": {
            "allowed": ["EXACT", "BACKWARD_ASOF"],
            "nearest_time_join_authorized": False,
        },
        "decision_time_inferred_from_signal_time": int(
            registry["decision_time_inferred"].sum()
        ),
        "status": "REPAIR_REQUIRED",
        "blocking_findings": [
            "No canonical row has source_available_at or feature_cutoff_time.",
            "R1 exposes entry time but no distinct signal-bar or decision time.",
            "R5 is represented by a post-selection trade ledger, not a complete pre-policy candidate ledger.",
            "The label_end_time clock is intentionally absent until the separately authorized label stage.",
        ],
    }


def anchored_episode_ids(frame: pd.DataFrame, anchor_hours: int) -> pd.Series:
    result = pd.Series(pd.NA, index=frame.index, dtype="string")
    ordered = frame.loc[frame["decision_time"].notna()].sort_values(
        ["decision_time", "candidate_id"], kind="mergesort"
    )
    anchor: pd.Timestamp | None = None
    episode_number = -1
    for row in ordered.itertuples():
        decision = pd.Timestamp(row.decision_time)
        if anchor is None or decision >= anchor + pd.Timedelta(hours=anchor_hours):
            anchor = decision
            episode_number += 1
        result.at[row.Index] = f"CE{episode_number:06d}"
    return result


def duplicate_episode_census(
    registry: pd.DataFrame, anchor_hours: int
) -> tuple[pd.DataFrame, dict[str, Any]]:
    result = registry.copy()
    known = result.loc[result["decision_time"].notna()].copy()
    exact_key = ["decision_time", "direction"]
    exact_sizes = known.groupby(exact_key, sort=False).size()
    result["structural_episode_proxy_id"] = pd.Series(
        pd.NA, index=result.index, dtype="string"
    )
    for index, row in known.iterrows():
        result.at[index, "structural_episode_proxy_id"] = (
            "SE_" + stable_id(row["decision_time"].isoformat(), row["direction"])[:20]
        )
    result["conservative_episode_proxy_id"] = anchored_episode_ids(result, anchor_hours)
    conservative_sizes = (
        result.loc[result["conservative_episode_proxy_id"].notna()]
        .groupby("conservative_episode_proxy_id", sort=False)
        .size()
    )
    result["provisional_structural_weight"] = np.nan
    structural_counts = result["structural_episode_proxy_id"].value_counts()
    structural_known = result["structural_episode_proxy_id"].notna()
    result.loc[structural_known, "provisional_structural_weight"] = result.loc[
        structural_known, "structural_episode_proxy_id"
    ].map(lambda value: 1.0 / float(structural_counts[value]))
    result["provisional_conservative_weight"] = np.nan
    conservative_counts = result["conservative_episode_proxy_id"].value_counts()
    conservative_known = result["conservative_episode_proxy_id"].notna()
    result.loc[conservative_known, "provisional_conservative_weight"] = result.loc[
        conservative_known, "conservative_episode_proxy_id"
    ].map(lambda value: 1.0 / float(conservative_counts[value]))

    direction_count_per_time = known.groupby("decision_time")["direction"].nunique()
    opposite_times = direction_count_per_time.loc[direction_count_per_time > 1]
    source_key_duplicates = int(
        result.duplicated(["source_id", "source_candidate_id"]).sum()
    )
    return result, {
        "schema_version": "xauusd_step_2_duplicate_episode_census_v1",
        "candidate_rows": int(len(result)),
        "candidate_id_duplicates": int(result["candidate_id"].duplicated().sum()),
        "source_candidate_key_duplicates": source_key_duplicates,
        "decision_time_missing": int(result["decision_time"].isna().sum()),
        "exact_time_direction_proxy": {
            "episodes": int(len(exact_sizes)),
            "candidate_rows": int(exact_sizes.sum()),
            "duplicate_rows_beyond_first": int((exact_sizes - 1).clip(lower=0).sum()),
            "multi_candidate_episodes": int((exact_sizes > 1).sum()),
            "maximum_episode_size": int(exact_sizes.max()) if len(exact_sizes) else 0,
            "size_distribution": {
                str(key): int(value)
                for key, value in exact_sizes.value_counts().sort_index().items()
            },
        },
        "opposite_direction_same_time": {
            "timestamps": int(len(opposite_times)),
            "candidate_rows": int(
                known["decision_time"].isin(opposite_times.index).sum()
            ),
        },
        "conservative_nontransitive_anchor": {
            "anchor_hours": int(anchor_hours),
            "episodes": int(len(conservative_sizes)),
            "candidate_rows": int(conservative_sizes.sum()),
            "maximum_episode_size": (
                int(conservative_sizes.max()) if len(conservative_sizes) else 0
            ),
            "size_distribution": {
                str(key): int(value)
                for key, value in conservative_sizes.value_counts().sort_index().items()
            },
            "unbounded_transitive_chaining": False,
        },
        "episode_status": "PROVISIONAL_NOT_WEIGHT_LOCK",
        "reason": "R1 decision clocks and multiple families' planned maximum holds are incomplete.",
    }


def effective_sample_plan(
    registry: pd.DataFrame, episode_census: Mapping[str, Any]
) -> dict[str, Any]:
    weights = registry["provisional_conservative_weight"].dropna().astype(float)
    kish = (
        float(weights.sum() ** 2 / np.square(weights).sum())
        if len(weights) and float(np.square(weights).sum()) > 0.0
        else 0.0
    )
    family_counts = registry["family_id"].value_counts()
    shares = family_counts / float(len(registry))
    conservative_episodes = int(
        episode_census["conservative_nontransitive_anchor"]["episodes"]
    )
    return {
        "schema_version": "xauusd_step_2_outcome_blind_effective_sample_plan_v1",
        "nominal_canonical_candidates": int(len(registry)),
        "candidates_with_decision_time": int(registry["decision_time"].notna().sum()),
        "candidates_without_decision_time": int(registry["decision_time"].isna().sum()),
        "exact_time_direction_proxy_episodes": int(
            episode_census["exact_time_direction_proxy"]["episodes"]
        ),
        "conservative_36h_proxy_episodes": conservative_episodes,
        "provisional_kish_effective_rows": kish,
        "provisional_effective_upper_bound": min(conservative_episodes, kish),
        "family_concentration_hhi": float(np.square(shares).sum()),
        "largest_family": str(family_counts.index[0]),
        "largest_family_share": float(shares.iloc[0]),
        "serial_effective_size": None,
        "final_effective_size": None,
        "weight_lock_status": "NOT_LOCKED",
        "why_not_locked": [
            "The R1 candidate decision clock is missing.",
            "Planned hold intervals are incomplete for R1, R5, and part of the add-on population.",
            "Structural anchors are not represented consistently across source families.",
            "Serial effective size requires chronological episode outcomes or residuals, which Step 2 is forbidden to read.",
        ],
        "locked_future_formula": "min(N_structural, N_conservative, N_kish, N_serial)",
        "required_reports_after_labels": [
            "BY_REGIME",
            "BY_FAMILY",
            "BY_DIRECTION",
            "BY_ACTION_GEOMETRY",
            "BY_CALENDAR_ERA",
            "PROSPECTIVE_VERSUS_HISTORICAL",
        ],
    }


def feature_availability_matrix(
    repo_root: Path, config: Mapping[str, Any]
) -> dict[str, Any]:
    roots = {
        "DUKASCOPY_XAU": Path("C:/DukascopyTickDataFoundationV1/raw/XAUUSD"),
        "DUKASCOPY_FOREX": Path("C:/DukascopyTickDataFoundationV1/raw/EURUSD"),
        "DUKASCOPY_XAG": Path("C:/DukascopyTickDataFoundationV1/raw/XAGUSD"),
        "DUKASCOPY_DOLLAR": Path("C:/DukascopyTickDataFoundationV1/raw/DOLLARIDXUSD"),
        "DUKASCOPY_BOND": Path("C:/DukascopyTickDataFoundationV1/raw/USTBONDTRUSD"),
        "COMEX": Path("C:/ComexGoldFuturesFoundationV1/raw"),
        "CAPITAL_PAIRED": repo_root
        / "xau-usd/xauusd-fast-research/capital-dukas-crossvenue-foundation-v22-1/outputs/CROSSVENUE_V22_1_PAIRED_QUOTES.parquet",
    }
    return {
        "schema_version": "xauusd_step_2_feature_availability_matrix_v1",
        "maximum_primary_columns": 64,
        "raw_event_windows_seconds": [30, 300, 900, 3600],
        "source_roots": {
            key: {"path": str(path), "exists": path.exists()}
            for key, path in roots.items()
        },
        "blocks": list(config["feature_availability"]),
        "exact_ordered_feature_list_locked": False,
        "features_materialized": False,
        "future_or_nearest_time_joins_performed": False,
        "status": "REPAIR_AND_CAUSAL_AGGREGATION_REQUIRED",
    }


def markdown_result(result: Mapping[str, Any]) -> str:
    checks = result["checks"]
    failed = [name for name, passed in checks.items() if not passed]
    return "\n".join(
        [
            "# Causal Candidate Quality ML V1 - Step 2 Result",
            "",
            f"Decision: `{result['decision']}`",
            "",
            "Step 2 completed the metadata-only source and candidate audit. It did not read economic outcomes, build labels or features, fit a model, change thresholds, simulate a portfolio, or alter the demo runtime.",
            "",
            f"- Canonical candidate rows: `{result['canonical_candidates']}`",
            f"- Unique candidate IDs: `{result['unique_candidate_ids']}`",
            f"- Candidates with a decision-time proxy: `{result['decision_time_rows']}`",
            f"- Candidates with all pre-label causal clocks: `{result['complete_prelabel_clock_rows']}`",
            f"- Provisional conservative episodes: `{result['provisional_conservative_episodes']}`",
            f"- Failed readiness checks: `{failed}`",
            "",
            "## Decision",
            "",
            "The source inventory and candidate counts reconcile, but the training dataset is not ready. The immediate successor must build metadata adapters for missing candidate clocks, complete action geometry, complete pre-policy candidate lineage, and source-availability rules. Counterfactual labels remain unauthorized until that repair is locked and re-audited.",
            "",
            "ML remains offline and detached from MT5.",
            "",
        ]
    )


def run_step_2(
    root: Path,
    repo_root: Path,
    config: Mapping[str, Any],
) -> dict[str, Any]:
    step_1_config = root / config["step_1_contract"]["path"]
    step_1_lock = root / config["step_1_contract"]["lock_path"]
    if not step_1_config.is_file() or not step_1_lock.is_file():
        raise FileNotFoundError("Step 1 contract and lock are required")
    step_1 = json.loads(step_1_config.read_text(encoding="utf-8"))
    if step_1["next_stage"]["name"] != config["stage"]:
        raise ValueError("Step 1 does not authorize this Step 2 stage")
    if config["audit_controls"]["economic_outcomes_authorized"]:
        raise ValueError("Step 2 cannot authorize economic outcomes")

    output = root / config["outputs"]["directory"]
    output.mkdir(parents=True, exist_ok=True)
    registry, candidate_hashes = build_candidate_registry(repo_root, config)
    source_inventory = build_source_inventory(repo_root, config, candidate_hashes)
    counts = candidate_registry_counts(repo_root, config, registry)
    multiplicity = action_multiplicity(repo_root, config, registry)
    timestamps = timestamp_audit(registry)
    registry, episodes = duplicate_episode_census(
        registry, int(config["episode_diagnostics"]["conservative_anchor_hours"])
    )
    features = feature_availability_matrix(repo_root, config)
    effective = effective_sample_plan(registry, episodes)

    checks = {
        "all_source_hashes_match": source_inventory["hash_mismatches"] == 0,
        "canonical_count_reconciles": counts["reconciliation"][
            "total_matches_expected"
        ],
        "canonical_candidate_ids_unique": counts["reconciliation"][
            "unique_ids_match_total"
        ],
        "addon_candidate_ids_reconcile": counts["reconciliation"][
            "v59_addon_decision_ids_match_candidate_ids"
        ],
        "one_primary_action_per_canonical_candidate": multiplicity["canonical"][
            "one_primary_action_per_candidate"
        ],
        "all_prelabel_causal_clocks_complete": timestamps[
            "prelabel_complete_clock_rows"
        ]
        == len(registry),
        "all_canonical_sources_are_pre_policy_candidate_ledgers": not registry[
            "lineage_status"
        ]
        .isin(["COMPLETED_TRADE_SOURCE_ONLY", "POST_SELECTION_TRADE_LEDGER_ONLY"])
        .any(),
        "all_action_geometry_complete": bool(registry["action_complete"].all()),
        "episode_weights_ready_to_lock": config["episode_diagnostics"][
            "weights_locked"
        ],
        "features_ready_to_build": features["exact_ordered_feature_list_locked"],
    }
    decision = "STEP_2_METADATA_AUDIT_COMPLETE_REPAIR_REQUIRED"
    result = {
        "schema_version": "xauusd_causal_candidate_quality_step_2_result_v1",
        "decision": decision,
        "stage": config["stage"],
        "created_utc": config["created_utc"],
        "canonical_candidates": int(len(registry)),
        "unique_candidate_ids": int(registry["candidate_id"].nunique()),
        "decision_time_rows": int(registry["decision_time"].notna().sum()),
        "complete_prelabel_clock_rows": int(timestamps["prelabel_complete_clock_rows"]),
        "provisional_conservative_episodes": int(
            episodes["conservative_nontransitive_anchor"]["episodes"]
        ),
        "checks": checks,
        "economic_outcomes_opened": False,
        "counterfactual_labels_built": False,
        "features_built": False,
        "model_fitted": False,
        "threshold_fitted": False,
        "portfolio_simulated": False,
        "runtime_changed": False,
        "ml_execution_authorized": False,
        "next_authorized_work": "STEP_2A_METADATA_REPAIR_AND_CANDIDATE_ADAPTERS",
        "counterfactual_label_build_authorized_next": False,
    }

    output_paths = {
        "candidate_registry": output / config["outputs"]["candidate_registry"],
        "source_inventory": output / config["outputs"]["source_inventory"],
        "candidate_registry_counts": output
        / config["outputs"]["candidate_registry_counts"],
        "action_multiplicity": output / config["outputs"]["action_multiplicity"],
        "timestamp_audit": output / config["outputs"]["timestamp_audit"],
        "duplicate_episode_census": output
        / config["outputs"]["duplicate_episode_census"],
        "feature_availability_matrix": output
        / config["outputs"]["feature_availability_matrix"],
        "effective_sample_plan": output / config["outputs"]["effective_sample_plan"],
        "result_json": output / config["outputs"]["result_json"],
        "result_markdown": output / config["outputs"]["result_markdown"],
    }
    registry.to_parquet(output_paths["candidate_registry"], index=False)
    write_json(output_paths["source_inventory"], source_inventory)
    write_json(output_paths["candidate_registry_counts"], counts)
    write_json(output_paths["action_multiplicity"], multiplicity)
    write_json(output_paths["timestamp_audit"], timestamps)
    write_json(output_paths["duplicate_episode_census"], episodes)
    write_json(output_paths["feature_availability_matrix"], features)
    write_json(output_paths["effective_sample_plan"], effective)
    write_json(output_paths["result_json"], result)
    output_paths["result_markdown"].write_text(
        markdown_result(result), encoding="utf-8"
    )

    manifest_path = output / config["outputs"]["artifact_manifest"]
    manifest = {
        "schema_version": "xauusd_step_2_artifact_manifest_v1",
        "decision": decision,
        "inputs": {
            "step_1_config": sha256_file(step_1_config),
            "step_1_lock": sha256_file(step_1_lock),
            "step_2_config": sha256_file(root / "config/step_2_metadata_audit_v1.json"),
            "step_2_implementation": sha256_file(Path(__file__)),
        },
        "artifacts": {
            key: {
                "path": str(path.relative_to(repo_root)).replace("\\", "/"),
                "bytes": int(path.stat().st_size),
                "sha256": sha256_file(path),
            }
            for key, path in sorted(output_paths.items())
        },
        "economic_outcomes_opened": False,
        "model_fitted": False,
        "runtime_changed": False,
    }
    write_json(manifest_path, manifest)
    return result
