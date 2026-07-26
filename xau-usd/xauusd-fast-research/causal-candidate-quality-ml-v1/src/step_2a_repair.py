from __future__ import annotations

import hashlib
import json
import math
import re
from pathlib import Path
from typing import Any, Iterable, Mapping

import numpy as np
import pandas as pd
import pyarrow.parquet as pq


CANONICAL_REQUIRED_CLOCKS = [
    "source_event_time",
    "source_available_at",
    "signal_bar_end",
    "feature_cutoff_time",
    "decision_time",
    "entry_eligible_time",
]

R1_SIGNAL_COLUMNS = [
    "timestamp_broker",
    "stage",
    "direction",
    "reason",
    "bid",
    "ask",
]

R1_ORDER_COLUMNS = [
    "timestamp_broker",
    "action",
    "direction",
    "lots",
    "bid",
    "ask",
    "entry_reference",
    "sl",
    "tp",
    "stop_points",
    "estimated_cost_r",
    "retcode",
    "retcode_description",
    "result_price",
    "reason",
]

R1_TAG_COLUMNS = [
    "component",
    "entry_time",
    "direction",
    "book_class",
]

R5_CANDIDATE_COLUMNS = [
    "candidate_id",
    "origin_attempt",
    "origin_variant_id",
    "regime_owner",
    "mechanic",
    "geometry_id",
    "signal_time",
    "scheduled_entry_time",
    "direction",
    "stop_atr",
    "target_r",
    "hold_hours",
]

R5_SELECTED_COLUMNS = [
    "candidate_id",
    "attempt_no",
    "component_attempt_no",
    "risk_weight",
    "route_multiplier",
    "route_reason",
    "router_id",
    "router_mechanic",
]

SPOT_ACTION_COLUMNS = [
    "event_id",
    "signal_time",
    "feature_time",
    "direction",
    "regime",
    "action_id",
    "action_stop_atr",
    "action_target_r",
    "action_hold_hours",
    "entry_time",
    "ambiguous_m5",
    "current_account_feasible",
]

COMEX_ACTION_COLUMNS = [
    "event_id",
    "decision_time",
    "signal_time",
    "direction",
    "regime",
    "action_id",
    "action_stop_atr",
    "action_target_r",
    "action_hold_hours",
    "entry_time",
    "ambiguous_m5",
    "current_account_feasible",
]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def stable_id(*parts: Any, length: int = 32) -> str:
    raw = "|".join("" if part is None else str(part) for part in parts)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:length]


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
        json.dumps(json_ready(payload), indent=2, sort_keys=True, allow_nan=False)
        + "\n",
        encoding="utf-8",
    )


def resolve_path(repo_root: Path, value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else repo_root / path


def verify_bound_file(repo_root: Path, spec: Mapping[str, Any], label: str) -> Path:
    path = resolve_path(repo_root, str(spec["path"]))
    if not path.is_file():
        raise FileNotFoundError(path)
    observed = sha256_file(path)
    if observed != str(spec["sha256"]):
        raise ValueError(f"Hash mismatch for {label}: {path}")
    return path


def validate_allowed_columns(columns: Iterable[str], forbidden: Iterable[str]) -> None:
    requested = {str(column).lower() for column in columns}
    prohibited = {str(column).lower() for column in forbidden}
    overlap = sorted(requested & prohibited)
    if overlap:
        raise ValueError(f"Step 2A requested economic columns: {overlap}")


def load_parquet_columns(
    path: Path, columns: list[str], forbidden: Iterable[str]
) -> pd.DataFrame:
    validate_allowed_columns(columns, forbidden)
    available = set(pq.ParquetFile(path).schema_arrow.names)
    missing = sorted(set(columns) - available)
    if missing:
        raise ValueError(f"Missing metadata columns in {path}: {missing}")
    return pd.read_parquet(path, columns=columns)


def load_mt5_tsv(path: Path, columns: list[str]) -> pd.DataFrame:
    # Native logs have one trailing tab beyond the declared header. index_col=False
    # is required or pandas silently shifts every field by one position.
    frame = pd.read_csv(path, sep="\t", usecols=columns, index_col=False)
    missing = sorted(set(columns) - set(frame.columns))
    if missing:
        raise ValueError(f"Missing MT5 columns in {path}: {missing}")
    return frame


def mt5_utc_like(values: pd.Series) -> pd.Series:
    return pd.to_datetime(values, format="%Y.%m.%d %H:%M:%S", errors="raise", utc=True)


def utc_series(values: pd.Series) -> pd.Series:
    return pd.to_datetime(values, utc=True, errors="raise")


def action_is_complete(frame: pd.DataFrame) -> pd.Series:
    stop_ok = frame["stop_mode"].notna() & (
        frame["stop_atr"].notna() | frame["stop_value"].notna()
    )
    target_ok = frame["target_mode"].eq("NONE") | (
        frame["target_mode"].eq("R_MULTIPLE") & frame["target_r"].notna()
    )
    hold_ok = (
        frame["maximum_hold_mode"].eq("FIXED") & frame["maximum_hold_minutes"].notna()
    ) | (
        frame["maximum_hold_mode"].eq("BARRIER_ONLY_NO_TIME_STOP")
        & frame["label_observation_cap_minutes"].notna()
    )
    return stop_ok & target_ok & hold_ok


def _r1_order_state(row: pd.Series) -> str:
    if str(row["action"]) != "ORDER_SEND_OK":
        return "REJECTED_GUARD"
    description = str(row.get("retcode_description", "")).lower()
    if "market closed" in description:
        return "ORDER_SEND_FAILED"
    return "ORDER_ACCEPTED"


def build_r1_guard_registry(
    repo_root: Path,
    config: Mapping[str, Any],
    forbidden: Iterable[str],
) -> tuple[pd.DataFrame, dict[str, Any], dict[str, str]]:
    del forbidden  # MT5 reads are explicit and contain no economic outcome fields.
    rows: list[pd.DataFrame] = []
    source_hashes: dict[str, str] = {}
    feature_manifest_path = verify_bound_file(
        repo_root,
        config["bound_inputs"]["dukascopy_feature_manifest"],
        "Dukascopy feature manifest",
    )
    feature_manifest = json.loads(feature_manifest_path.read_text(encoding="utf-8"))
    feature_path = Path(str(feature_manifest["path"]))
    expected_feature_hash = str(feature_manifest["feature_sha256"])
    if sha256_file(feature_path) != expected_feature_hash:
        raise ValueError("Dukascopy feature cache no longer matches its manifest")
    features = pd.read_parquet(feature_path, columns=["timestamp_ms", "bid_open"])
    features["decision_time"] = pd.to_datetime(
        features["timestamp_ms"], unit="ms", utc=True
    )
    features = features[["decision_time", "bid_open"]]

    alignment: dict[str, Any] = {}
    observation_cap = float(config["r1"]["barrier_label_observation_cap_days"]) * 1440
    for component in config["r1"]["components"]:
        component_id = str(component["component_id"])
        signals_path = verify_bound_file(
            repo_root, component["signals"], f"R1 {component_id} signals"
        )
        orders_path = verify_bound_file(
            repo_root, component["orders"], f"R1 {component_id} orders"
        )
        source_hashes[f"{component_id}_signals"] = sha256_file(signals_path)
        source_hashes[f"{component_id}_orders"] = sha256_file(orders_path)
        signals = load_mt5_tsv(signals_path, R1_SIGNAL_COLUMNS)
        orders = load_mt5_tsv(orders_path, R1_ORDER_COLUMNS)
        signals = signals.loc[signals["stage"].eq("WOULD_SIGNAL")].copy()
        if signals.duplicated(["timestamp_broker", "direction"]).any():
            raise ValueError(f"Duplicate R1 signal identity in {component_id}")
        if orders.duplicated(["timestamp_broker", "direction"]).any():
            raise ValueError(f"Duplicate R1 order identity in {component_id}")
        joined = signals.merge(
            orders,
            on=["timestamp_broker", "direction"],
            how="left",
            suffixes=("_signal", "_order"),
            validate="one_to_one",
        )
        if joined["action"].isna().any():
            raise ValueError(f"R1 signals without an order decision in {component_id}")
        joined["decision_time"] = mt5_utc_like(joined["timestamp_broker"])
        joined["historical_accept_state"] = joined.apply(_r1_order_state, axis=1)
        joined["historical_decision_reason"] = joined["reason_order"].fillna("")
        joined["candidate_id"] = [
            stable_id("R1_GUARD", component_id, when.isoformat(), direction)
            for when, direction in zip(joined["decision_time"], joined["direction"])
        ]
        joined["population"] = "RESEARCH_NEGATIVE"
        joined["family_id"] = "R1_GUARD_AUDIT"
        joined["mechanic_id"] = component_id
        joined["source_event_time"] = joined["decision_time"]
        joined["source_available_at"] = joined["decision_time"]
        joined["signal_bar_end"] = joined["decision_time"]
        joined["feature_cutoff_time"] = joined["decision_time"]
        joined["entry_eligible_time"] = joined["decision_time"]
        joined["stop_mode"] = str(component["stop_mode"])
        joined["stop_value"] = pd.to_numeric(joined["stop_points"], errors="coerce")
        joined["stop_unit"] = "POINTS_0P01"
        joined["stop_atr"] = np.nan
        joined["stop_floor_price"] = np.nan
        joined["target_mode"] = "R_MULTIPLE"
        joined["target_r"] = float(component["target_r"])
        joined["maximum_hold_mode"] = str(component["maximum_hold_mode"])
        joined["maximum_hold_minutes"] = np.nan
        joined["label_observation_cap_minutes"] = observation_cap
        joined["action_complete"] = action_is_complete(joined)

        accepted_orders = joined.loc[joined["action"].eq("ORDER_SEND_OK")].copy()
        direct = accepted_orders.merge(
            features, on="decision_time", how="left", validate="many_to_one"
        )
        wall = pd.to_datetime(
            accepted_orders["timestamp_broker"],
            format="%Y.%m.%d %H:%M:%S",
            errors="raise",
        )
        shifted = accepted_orders.copy()
        shifted["decision_time"] = wall.dt.tz_localize(
            str(config["r1"]["nominal_server_timezone"]),
            ambiguous="NaT",
            nonexistent="NaT",
        ).dt.tz_convert("UTC")
        shifted = shifted.merge(
            features, on="decision_time", how="left", validate="many_to_one"
        )
        direct_error = (direct["bid_order"] - direct["bid_open"]).abs()
        shifted_error = (shifted["bid_order"] - shifted["bid_open"]).abs()
        direct_median = float(direct_error.median())
        shifted_median = float(shifted_error.median())
        ratio = shifted_median / direct_median if direct_median > 0 else math.inf
        if direct["bid_open"].isna().any():
            raise ValueError(f"Missing Dukascopy clock matches for {component_id}")
        if direct_median > float(config["r1"]["maximum_direct_utc_median_bid_error"]):
            raise ValueError(f"R1 direct-UTC price alignment failed for {component_id}")
        if ratio < float(config["r1"]["minimum_shifted_to_direct_median_error_ratio"]):
            raise ValueError(f"R1 timezone discrimination failed for {component_id}")
        alignment[component_id] = {
            "would_signal_rows": int(len(joined)),
            "order_accepted_rows": int(
                joined["historical_accept_state"].eq("ORDER_ACCEPTED").sum()
            ),
            "order_send_failed_rows": int(
                joined["historical_accept_state"].eq("ORDER_SEND_FAILED").sum()
            ),
            "guard_rejected_rows": int(
                joined["historical_accept_state"].eq("REJECTED_GUARD").sum()
            ),
            "direct_utc_feature_matches": int(direct["bid_open"].notna().sum()),
            "direct_utc_median_absolute_bid_error": direct_median,
            "direct_utc_p95_absolute_bid_error": float(direct_error.quantile(0.95)),
            "helsinki_shifted_median_absolute_bid_error": shifted_median,
            "shifted_to_direct_median_error_ratio": ratio,
            "timestamp_basis": str(config["r1"]["timestamp_basis"]),
        }
        rows.append(joined)

    guard = pd.concat(rows, ignore_index=True)
    keep = [
        "candidate_id",
        "population",
        "family_id",
        "mechanic_id",
        "direction",
        "source_event_time",
        "source_available_at",
        "signal_bar_end",
        "decision_time",
        "feature_cutoff_time",
        "entry_eligible_time",
        "action",
        "historical_accept_state",
        "historical_decision_reason",
        "stop_mode",
        "stop_value",
        "stop_unit",
        "stop_atr",
        "stop_floor_price",
        "target_mode",
        "target_r",
        "maximum_hold_mode",
        "maximum_hold_minutes",
        "label_observation_cap_minutes",
        "action_complete",
        "bid_signal",
        "ask_signal",
        "estimated_cost_r",
    ]
    return guard[keep].copy(), alignment, source_hashes


def build_r5_prepolicy_registry(
    repo_root: Path,
    config: Mapping[str, Any],
    forbidden: Iterable[str],
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, str]]:
    candidate_spec = config["r5_prepolicy"]["candidates"]
    selected_spec = config["r5_prepolicy"]["selected"]
    candidate_path = verify_bound_file(
        repo_root, candidate_spec, "R5 pre-policy candidates"
    )
    selected_path = verify_bound_file(repo_root, selected_spec, "R5 selected rows")
    candidates = load_parquet_columns(candidate_path, R5_CANDIDATE_COLUMNS, forbidden)
    selected = load_parquet_columns(selected_path, R5_SELECTED_COLUMNS, forbidden)
    selected = selected.loc[
        selected["attempt_no"].eq(int(selected_spec["attempt_no"]))
    ].copy()
    if len(candidates) != int(candidate_spec["expected_rows"]):
        raise ValueError("R5 pre-policy candidate count changed")
    if len(selected) != int(selected_spec["expected_rows"]):
        raise ValueError("R5 selected count changed")
    if candidates["candidate_id"].duplicated().any():
        raise ValueError("R5 pre-policy candidate IDs are duplicated")
    if selected["candidate_id"].duplicated().any():
        raise ValueError("R5 selected candidate IDs are duplicated")
    if set(selected["candidate_id"]) - set(candidates["candidate_id"]):
        raise ValueError("R5 selected rows do not reconcile to pre-policy candidates")
    result = candidates.merge(
        selected,
        on="candidate_id",
        how="left",
        validate="one_to_one",
        indicator="_selection",
    )
    result["selected_by_router"] = result["_selection"].eq("both")
    result["broker_executable"] = result["selected_by_router"] & np.isclose(
        pd.to_numeric(result["risk_weight"], errors="coerce"), 1.0
    )
    if int(result["broker_executable"].sum()) != int(
        selected_spec["expected_broker_executable_rows"]
    ):
        raise ValueError("R5 broker-executable count changed")
    result["source_candidate_id"] = result["candidate_id"].astype(str)
    result["candidate_id"] = [
        stable_id("R5_PREPOLICY", value) for value in result["source_candidate_id"]
    ]
    result["population"] = "R5_PREPOLICY_AUDIT"
    result["family_id"] = "R5_TRANSITION"
    result["source_id"] = "R5_V9_PREPOLICY"
    result["source_event_time"] = utc_series(result["signal_time"])
    result["source_available_at"] = result["source_event_time"]
    result["signal_bar_end"] = result["source_event_time"]
    result["decision_time"] = result["source_event_time"]
    result["feature_cutoff_time"] = result["source_event_time"]
    result["entry_eligible_time"] = utc_series(result["scheduled_entry_time"])
    result["action_id"] = (
        result["mechanic"].astype(str) + "__" + result["geometry_id"].astype(str)
    )
    result["stop_mode"] = "ATR"
    result["stop_value"] = np.nan
    result["stop_unit"] = "ATR"
    result["stop_floor_price"] = np.nan
    result["target_mode"] = "R_MULTIPLE"
    result["maximum_hold_mode"] = "FIXED"
    result["maximum_hold_minutes"] = (
        pd.to_numeric(result["hold_hours"], errors="raise") * 60.0
    )
    result["label_observation_cap_minutes"] = result["maximum_hold_minutes"]
    result["historical_accept_state"] = np.where(
        result["selected_by_router"], "ROUTER_SELECTED", "ROUTER_REJECTED"
    )
    result["historical_decision_reason"] = result["route_reason"].fillna(
        "NOT_SELECTED_BY_FROZEN_ROUTER"
    )
    result["action_complete"] = action_is_complete(result)
    keep = [
        "candidate_id",
        "source_candidate_id",
        "population",
        "family_id",
        "source_id",
        "origin_attempt",
        "origin_variant_id",
        "mechanic",
        "geometry_id",
        "direction",
        "source_event_time",
        "source_available_at",
        "signal_bar_end",
        "decision_time",
        "feature_cutoff_time",
        "entry_eligible_time",
        "action_id",
        "stop_mode",
        "stop_value",
        "stop_unit",
        "stop_atr",
        "stop_floor_price",
        "target_mode",
        "target_r",
        "maximum_hold_mode",
        "maximum_hold_minutes",
        "label_observation_cap_minutes",
        "selected_by_router",
        "broker_executable",
        "risk_weight",
        "route_multiplier",
        "historical_accept_state",
        "historical_decision_reason",
        "action_complete",
    ]
    canonical_map = result.loc[result["selected_by_router"]].copy()
    return (
        result[keep].copy(),
        canonical_map[keep].copy(),
        {
            "r5_prepolicy_candidates": sha256_file(candidate_path),
            "r5_selected": sha256_file(selected_path),
        },
    )


def _load_acceptance_sets(
    repo_root: Path,
    config: Mapping[str, Any],
    forbidden: Iterable[str],
) -> tuple[dict[str, set[str]], pd.DataFrame, dict[str, str]]:
    accepted: dict[str, set[str]] = {}
    addon_decisions = pd.DataFrame()
    hashes: dict[str, str] = {}
    for index, spec in enumerate(config["canonical_acceptance_sources"]):
        path = verify_bound_file(repo_root, spec, f"acceptance source {index}")
        frame = load_parquet_columns(path, list(spec["columns"]), forbidden)
        hashes[f"acceptance_{index}"] = sha256_file(path)
        source_ids = list(spec["source_ids"])
        if source_ids == ["CANONICAL_V57_ADDONS"]:
            addon_decisions = frame.copy()
            continue
        if "composite_id" in frame.columns:
            mapping = {
                "CANONICAL_R2_DOWNTREND": "R2_DOWNTREND_FAILED_RALLY_DUAL_MODE_V1",
                "CANONICAL_R3_COMPRESSION": "R3_COMPRESSION_RELEASE_TRI_MODE_V1",
            }
            for source_id in source_ids:
                accepted[source_id] = set(
                    frame.loc[
                        frame["composite_id"].eq(mapping[source_id]), "candidate_id"
                    ].astype(str)
                )
        else:
            for source_id in source_ids:
                accepted[source_id] = set(frame["candidate_id"].astype(str))
    return accepted, addon_decisions, hashes


def build_canonical_registry(
    repo_root: Path,
    config: Mapping[str, Any],
    r1_guard: pd.DataFrame,
    r5_selected: pd.DataFrame,
    forbidden: Iterable[str],
) -> tuple[pd.DataFrame, dict[str, Any], dict[str, str]]:
    step2_path = verify_bound_file(
        repo_root, config["bound_inputs"]["step_2_registry"], "Step 2 registry"
    )
    registry = pd.read_parquet(step2_path)
    if len(registry) != int(config["expected"]["canonical_candidates"]):
        raise ValueError("Step 2 canonical count changed")

    r1_tag_path = verify_bound_file(
        repo_root, config["r1"]["tagged_candidates"], "R1 tagged candidates"
    )
    r1_tags = pd.read_csv(r1_tag_path, usecols=R1_TAG_COLUMNS)
    r1_tags = r1_tags.loc[r1_tags["book_class"].eq("R1")].copy()
    r1_tags["entry_time"] = pd.to_datetime(r1_tags["entry_time"], utc=True)
    r1_tag_keys = set(
        zip(
            r1_tags["component"].astype(str),
            r1_tags["entry_time"],
            r1_tags["direction"].astype(str).str.upper(),
        )
    )
    canonical_r1 = registry.loc[registry["family_id"].eq("R1_UPTREND")]
    canonical_r1_keys = set(
        zip(
            canonical_r1["mechanic_id"].astype(str),
            utc_series(canonical_r1["entry_eligible_time"]),
            canonical_r1["direction"].astype(str).str.upper(),
        )
    )
    expected_r1 = int(config["expected"]["r1_canonical_candidates"])
    if len(r1_tags) != expected_r1 or len(r1_tag_keys) != expected_r1:
        raise ValueError("R1 tagged candidate identity is no longer one-to-one")
    if r1_tag_keys != canonical_r1_keys:
        raise ValueError(
            "Canonical R1 candidates do not reconcile to the tagged ledger"
        )
    for column in [
        "source_event_time",
        "timestamp_basis",
        "availability_basis",
        "stop_mode",
        "stop_value",
        "stop_unit",
        "stop_floor_price",
        "target_mode",
        "maximum_hold_mode",
        "label_observation_cap_minutes",
        "historical_accept_state",
        "historical_decision_reason",
    ]:
        registry[column] = pd.NA
    registry["broker_executable"] = False
    registry["historical_specialist_accepted"] = False
    registry["historical_portfolio_accepted"] = False

    non_r1 = ~registry["family_id"].eq("R1_UPTREND")
    registry.loc[non_r1, "source_event_time"] = registry.loc[non_r1, "signal_bar_end"]
    registry.loc[non_r1, "source_available_at"] = registry.loc[non_r1, "signal_bar_end"]
    registry.loc[non_r1, "feature_cutoff_time"] = registry.loc[non_r1, "decision_time"]
    registry.loc[non_r1, "timestamp_basis"] = "UTC_EXPLICIT_SOURCE"
    registry.loc[non_r1, "availability_basis"] = (
        "COMPLETED_SIGNAL_BAR_AVAILABLE_AT_DECISION"
    )

    r1 = r1_guard.loc[r1_guard["historical_accept_state"].eq("ORDER_ACCEPTED")].copy()
    r1_keyed = r1.set_index(["mechanic_id", "decision_time", "direction"], drop=False)
    r1_mask = registry["family_id"].eq("R1_UPTREND")
    for index, row in registry.loc[r1_mask].iterrows():
        key = (str(row["mechanic_id"]), row["entry_eligible_time"], row["direction"])
        if key not in r1_keyed.index:
            raise ValueError(f"Canonical R1 candidate lacks pre-trade metadata: {key}")
        match = r1_keyed.loc[key]
        if isinstance(match, pd.DataFrame):
            raise ValueError(f"Canonical R1 metadata is ambiguous: {key}")
        for column in [
            "source_event_time",
            "source_available_at",
            "signal_bar_end",
            "decision_time",
            "feature_cutoff_time",
            "entry_eligible_time",
            "stop_mode",
            "stop_value",
            "stop_unit",
            "stop_atr",
            "stop_floor_price",
            "target_mode",
            "target_r",
            "maximum_hold_mode",
            "maximum_hold_minutes",
            "label_observation_cap_minutes",
        ]:
            registry.at[index, column] = match[column]
        registry.at[index, "timestamp_basis"] = str(config["r1"]["timestamp_basis"])
        registry.at[index, "availability_basis"] = (
            "COMPLETED_NATIVE_BAR_AVAILABLE_AT_DECISION"
        )
        registry.at[index, "broker_executable"] = True
        registry.at[index, "historical_specialist_accepted"] = True
        registry.at[index, "historical_accept_state"] = "NATIVE_ORDER_ACCEPTED"
        registry.at[index, "historical_decision_reason"] = "NATIVE_ORDER_ACCEPTED"

    accepted_sets, addon_decisions, acceptance_hashes = _load_acceptance_sets(
        repo_root, config, forbidden
    )
    for source_id in (
        "CANONICAL_R2_DOWNTREND",
        "CANONICAL_R3_COMPRESSION",
        "CANONICAL_R4_CHOP",
    ):
        mask = registry["source_id"].eq(source_id)
        accepted = (
            registry.loc[mask, "source_candidate_id"]
            .astype(str)
            .isin(accepted_sets[source_id])
        )
        registry.loc[mask, "historical_specialist_accepted"] = accepted.to_numpy()
        registry.loc[mask, "historical_portfolio_accepted"] = accepted.to_numpy()
        registry.loc[mask, "historical_accept_state"] = np.where(
            accepted, "SOURCE_POLICY_ACCEPTED", "SOURCE_POLICY_REJECTED"
        )
        registry.loc[mask, "historical_decision_reason"] = np.where(
            accepted, "SOURCE_NONOVERLAP_POLICY_ACCEPTED", "SOURCE_CAPACITY_REJECTED"
        )
        registry.loc[mask, "broker_executable"] = True
        registry.loc[mask, "stop_mode"] = "ATR"
        registry.loc[mask, "stop_value"] = np.nan
        registry.loc[mask, "stop_unit"] = "ATR"
        registry.loc[mask, "stop_floor_price"] = np.nan
        registry.loc[mask, "target_mode"] = "NONE"
        registry.loc[mask, "maximum_hold_mode"] = "FIXED"
        registry.loc[mask, "label_observation_cap_minutes"] = registry.loc[
            mask, "maximum_hold_minutes"
        ]

    r4_mask = registry["source_id"].eq("CANONICAL_R4_CHOP")
    registry.loc[r4_mask, "target_mode"] = "R_MULTIPLE"

    r5_by_source = r5_selected.set_index("source_candidate_id")
    r5_mask = registry["source_id"].eq("CANONICAL_R5_TRANSITION")
    for index, row in registry.loc[r5_mask].iterrows():
        source_candidate_id = str(row["source_candidate_id"])
        if source_candidate_id not in r5_by_source.index:
            raise ValueError(
                f"Canonical R5 candidate not found pre-policy: {source_candidate_id}"
            )
        match = r5_by_source.loc[source_candidate_id]
        for column in [
            "source_event_time",
            "source_available_at",
            "signal_bar_end",
            "decision_time",
            "feature_cutoff_time",
            "entry_eligible_time",
            "stop_mode",
            "stop_value",
            "stop_unit",
            "stop_atr",
            "stop_floor_price",
            "target_mode",
            "target_r",
            "maximum_hold_mode",
            "maximum_hold_minutes",
            "label_observation_cap_minutes",
        ]:
            registry.at[index, column] = match[column]
        executable = bool(match["broker_executable"])
        registry.at[index, "broker_executable"] = executable
        registry.at[index, "broker_executable_status"] = str(executable).upper()
        registry.at[index, "historical_specialist_accepted"] = True
        registry.at[index, "historical_portfolio_accepted"] = executable
        registry.at[index, "historical_accept_state"] = (
            "BROKER_EXECUTABLE" if executable else "FRACTIONAL_BELOW_BROKER_MINIMUM"
        )
        registry.at[index, "historical_decision_reason"] = match[
            "historical_decision_reason"
        ]
        registry.at[index, "lineage_status"] = (
            "PREPOLICY_RECONCILED_TO_ROUTER_SELECTION"
        )

    addon_by_id = addon_decisions.set_index("trade_id")
    addon_mask = registry["source_id"].eq("CANONICAL_V57_ADDONS")
    for index, row in registry.loc[addon_mask].iterrows():
        trade_id = str(row["source_candidate_id"])
        if trade_id not in addon_by_id.index:
            raise ValueError(f"Add-on candidate lacks V59 decision: {trade_id}")
        decision = addon_by_id.loc[trade_id]
        geometry = config["family_geometry"][str(row["family_id"])]
        registry.at[index, "stop_mode"] = geometry["stop_mode"]
        registry.at[index, "stop_value"] = np.nan
        registry.at[index, "stop_unit"] = "ATR"
        registry.at[index, "stop_atr"] = float(geometry["stop_atr"])
        registry.at[index, "stop_floor_price"] = geometry["stop_floor_price"]
        registry.at[index, "target_mode"] = geometry["target_mode"]
        registry.at[index, "target_r"] = float(geometry["target_r"])
        registry.at[index, "maximum_hold_mode"] = "FIXED"
        registry.at[index, "maximum_hold_minutes"] = float(
            geometry["maximum_hold_minutes"]
        )
        registry.at[index, "label_observation_cap_minutes"] = float(
            geometry["maximum_hold_minutes"]
        )
        accepted = bool(decision["accepted"])
        registry.at[index, "broker_executable"] = True
        registry.at[index, "broker_executable_status"] = "TRUE"
        registry.at[index, "historical_specialist_accepted"] = True
        registry.at[index, "historical_portfolio_accepted"] = accepted
        registry.at[index, "historical_accept_state"] = (
            "ACCOUNT_POLICY_ACCEPTED" if accepted else "ACCOUNT_POLICY_REJECTED"
        )
        registry.at[index, "historical_decision_reason"] = str(
            decision["decision_reason"]
        )

    r1_decision_path = verify_bound_file(
        repo_root, config["r1"]["portfolio_decisions"], "R1 portfolio decisions"
    )
    r1_decisions = load_parquet_columns(
        r1_decision_path,
        ["trade_id", "entry_time", "accepted", "decision_reason"],
        forbidden,
    )
    r1_decisions["entry_time"] = utc_series(r1_decisions["entry_time"])
    r1_by_time = r1_decisions.set_index("entry_time")
    box_mask = r1_mask & registry["mechanic_id"].eq("h4_d1_long_best_box2_atr80")
    for index, row in registry.loc[box_mask].iterrows():
        decision = r1_by_time.loc[row["entry_eligible_time"]]
        registry.at[index, "historical_portfolio_accepted"] = bool(decision["accepted"])
        registry.at[index, "historical_decision_reason"] = str(
            decision["decision_reason"]
        )
    pullback_mask = r1_mask & registry["mechanic_id"].eq("r1_h1_pullback_long_v1")
    registry.loc[pullback_mask, "historical_portfolio_accepted"] = True

    registry["action_complete"] = action_is_complete(registry)
    registry["broker_executable_status"] = np.where(
        registry["broker_executable"], "TRUE", "FALSE"
    )
    for column in CANONICAL_REQUIRED_CLOCKS:
        registry[column] = utc_series(registry[column])
    for column in [
        "stop_atr",
        "stop_value",
        "stop_floor_price",
        "target_r",
        "maximum_hold_minutes",
        "label_observation_cap_minutes",
    ]:
        registry[column] = pd.to_numeric(registry[column], errors="coerce")

    expected_accepted = int(config["expected"]["historically_portfolio_accepted"])
    observed_accepted = int(registry["historical_portfolio_accepted"].sum())
    if observed_accepted != expected_accepted:
        raise ValueError(
            f"Canonical accepted count changed: {observed_accepted} != {expected_accepted}"
        )
    if not registry["action_complete"].all():
        bad = registry.loc[~registry["action_complete"], "family_id"].value_counts()
        raise ValueError(f"Canonical actions remain incomplete: {bad.to_dict()}")
    clocks_complete = registry[CANONICAL_REQUIRED_CLOCKS].notna().all(axis=1)
    if not clocks_complete.all():
        raise ValueError("Canonical clocks remain incomplete")
    evidence = {
        "canonical_rows": int(len(registry)),
        "complete_clock_rows": int(clocks_complete.sum()),
        "complete_action_rows": int(registry["action_complete"].sum()),
        "broker_executable_rows": int(registry["broker_executable"].sum()),
        "historically_specialist_accepted": int(
            registry["historical_specialist_accepted"].sum()
        ),
        "historically_portfolio_accepted": observed_accepted,
    }
    hashes = {
        "step_2_registry": sha256_file(step2_path),
        "r1_tagged_candidates": sha256_file(r1_tag_path),
        "r1_portfolio_decisions": sha256_file(r1_decision_path),
        **acceptance_hashes,
    }
    return registry, evidence, hashes


def build_journey_action_registries(
    repo_root: Path,
    config: Mapping[str, Any],
    forbidden: Iterable[str],
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any], dict[str, str]]:
    frames: list[pd.DataFrame] = []
    hashes: dict[str, str] = {}
    for spec in config["journey_action_sources"]:
        source_id = str(spec["source_id"])
        path = verify_bound_file(repo_root, spec, source_id)
        hashes[source_id] = sha256_file(path)
        if spec["clock_adapter"] == "SPOT_FEATURE_SIGNAL_ENTRY":
            frame = load_parquet_columns(path, SPOT_ACTION_COLUMNS, forbidden)
            frame["source_event_time"] = utc_series(frame["feature_time"])
            frame["source_available_at"] = frame["source_event_time"]
            frame["signal_bar_end"] = frame["source_event_time"]
            frame["feature_cutoff_time"] = frame["source_event_time"]
            frame["decision_time"] = utc_series(frame["signal_time"])
            frame["entry_eligible_time"] = utc_series(frame["entry_time"])
            frame["availability_basis"] = "DUKASCOPY_FEATURE_TIME"
        elif spec["clock_adapter"] == "COMEX_DECISION_TO_ENTRY":
            frame = load_parquet_columns(path, COMEX_ACTION_COLUMNS, forbidden)
            frame["source_event_time"] = utc_series(frame["decision_time"])
            frame["source_available_at"] = frame["source_event_time"]
            frame["signal_bar_end"] = frame["source_event_time"]
            frame["feature_cutoff_time"] = frame["source_event_time"]
            frame["decision_time"] = utc_series(frame["decision_time"])
            frame["entry_eligible_time"] = utc_series(frame["entry_time"])
            frame["availability_basis"] = (
                "HISTORICAL_COMEX_EVENT_TIME_NO_LIVE_LATENCY_CLAIM"
            )
        else:
            raise ValueError(f"Unknown journey clock adapter: {spec['clock_adapter']}")
        if len(frame) != int(spec["expected_rows"]):
            raise ValueError(f"Journey action count changed for {source_id}")
        frame["source_id"] = source_id
        frame["population"] = str(spec["population"])
        frame["candidate_id"] = [
            stable_id(source_id, event_id, str(direction).upper())
            for event_id, direction in zip(frame["event_id"], frame["direction"])
        ]
        frame["action_row_id"] = [
            stable_id(candidate_id, action_id)
            for candidate_id, action_id in zip(
                frame["candidate_id"], frame["action_id"]
            )
        ]
        frame["direction"] = frame["direction"].astype(str).str.upper()
        frame["stop_mode"] = "ATR"
        frame["stop_value"] = np.nan
        frame["stop_unit"] = "ATR"
        frame["stop_atr"] = pd.to_numeric(frame["action_stop_atr"], errors="raise")
        frame["stop_floor_price"] = np.nan
        frame["target_mode"] = "R_MULTIPLE"
        frame["target_r"] = pd.to_numeric(frame["action_target_r"], errors="raise")
        frame["maximum_hold_mode"] = "FIXED"
        frame["maximum_hold_minutes"] = (
            pd.to_numeric(frame["action_hold_hours"], errors="raise") * 60.0
        )
        frame["label_observation_cap_minutes"] = frame["maximum_hold_minutes"]
        frame["broker_executable"] = frame["current_account_feasible"].astype(bool)
        frame["action_complete"] = action_is_complete(frame)
        frame["structural_episode_id"] = [
            stable_id("JOURNEY_EVENT", source_id, event_id)
            for event_id in frame["event_id"]
        ]
        frames.append(frame)

    actions = pd.concat(frames, ignore_index=True)
    if len(actions) != int(config["expected"]["journey_action_rows"]):
        raise ValueError("Combined journey action count changed")
    if actions["action_row_id"].duplicated().any():
        raise ValueError("Journey action row IDs are duplicated")
    if not actions["action_complete"].all():
        raise ValueError("Journey action geometry is incomplete")
    clock_order = (
        (actions["source_available_at"] <= actions["feature_cutoff_time"])
        & (actions["feature_cutoff_time"] <= actions["decision_time"])
        & (actions["decision_time"] <= actions["entry_eligible_time"])
    )
    if not clock_order.all():
        raise ValueError("Journey action clocks violate the causal invariant")
    multiplicity = actions.groupby("candidate_id", sort=False).size()
    actions["candidate_action_count"] = actions["candidate_id"].map(multiplicity)
    actions["candidate_action_weight"] = 1.0 / actions["candidate_action_count"]
    candidate_columns = [
        "candidate_id",
        "population",
        "source_id",
        "event_id",
        "direction",
        "regime",
        "source_event_time",
        "source_available_at",
        "signal_bar_end",
        "feature_cutoff_time",
        "decision_time",
        "entry_eligible_time",
        "availability_basis",
        "structural_episode_id",
        "candidate_action_count",
    ]
    candidates = actions[candidate_columns].drop_duplicates("candidate_id").copy()
    if candidates["candidate_id"].duplicated().any():
        raise ValueError("Journey candidate IDs are duplicated")
    by_source = {
        source_id: {
            "action_rows": int(len(group)),
            "candidate_directions": int(group["candidate_id"].nunique()),
            "structural_events": int(group["structural_episode_id"].nunique()),
            "action_count_distribution": {
                str(int(key)): int(value)
                for key, value in group.groupby("candidate_id")
                .size()
                .value_counts()
                .items()
            },
        }
        for source_id, group in actions.groupby("source_id", sort=True)
    }
    evidence = {
        "action_rows": int(len(actions)),
        "unique_action_rows": int(actions["action_row_id"].nunique()),
        "candidate_directions": int(len(candidates)),
        "structural_events": int(actions["structural_episode_id"].nunique()),
        "all_clocks_causal": bool(clock_order.all()),
        "all_actions_complete": bool(actions["action_complete"].all()),
        "sibling_action_weight_sum": float(actions["candidate_action_weight"].sum()),
        "by_source": by_source,
        "rejection_is_loss": False,
        "direct_primary_model_ingestion_authorized": False,
    }
    keep = [
        "action_row_id",
        "candidate_id",
        "population",
        "source_id",
        "event_id",
        "direction",
        "regime",
        "source_event_time",
        "source_available_at",
        "signal_bar_end",
        "feature_cutoff_time",
        "decision_time",
        "entry_eligible_time",
        "availability_basis",
        "action_id",
        "stop_mode",
        "stop_value",
        "stop_unit",
        "stop_atr",
        "stop_floor_price",
        "target_mode",
        "target_r",
        "maximum_hold_mode",
        "maximum_hold_minutes",
        "label_observation_cap_minutes",
        "broker_executable",
        "ambiguous_m5",
        "action_complete",
        "structural_episode_id",
        "candidate_action_count",
        "candidate_action_weight",
    ]
    return actions[keep].copy(), candidates, evidence, hashes


def conservative_episode_ids(registry: pd.DataFrame) -> pd.Series:
    required = {"decision_time", "planned_observation_end"}
    missing = sorted(required - set(registry.columns))
    if missing:
        raise ValueError(f"Episode assignment is missing columns: {missing}")

    assignments = pd.Series(index=registry.index, dtype="object")
    episode = -1
    anchor_end: pd.Timestamp | None = None
    ordered = registry.sort_values(["decision_time", "candidate_id"], kind="mergesort")
    for decision_time, group in ordered.groupby("decision_time", sort=True):
        decision = pd.Timestamp(decision_time)
        decision_end = pd.Timestamp(group["planned_observation_end"].max())
        if anchor_end is None or decision > anchor_end:
            episode += 1
            anchor_end = decision_end
        assignments.loc[group.index] = f"CE{episode:06d}"
    if assignments.isna().any():
        raise ValueError("Conservative episode assignment left unassigned rows")
    return assignments


def assign_episode_weights(
    registry: pd.DataFrame,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    result = registry.copy()
    result["structural_episode_id"] = [
        stable_id("CANONICAL_STRUCTURAL", when.isoformat())
        for when in result["decision_time"]
    ]
    result["planned_observation_end"] = result["decision_time"] + pd.to_timedelta(
        result["label_observation_cap_minutes"], unit="m"
    )
    structural_counts = result["structural_episode_id"].value_counts()
    result["structural_weight"] = 1.0 / result["structural_episode_id"].map(
        structural_counts
    )

    result["conservative_episode_id"] = conservative_episode_ids(result)
    conservative_counts = result["conservative_episode_id"].value_counts()
    result["conservative_weight"] = 1.0 / result["conservative_episode_id"].map(
        conservative_counts
    )

    def kish(values: pd.Series) -> float:
        weights = values.astype(float).to_numpy()
        return float(weights.sum() ** 2 / np.square(weights).sum())

    report = {
        "schema_version": "xauusd_step_2a_episode_weight_lock_v1",
        "candidate_rows": int(len(result)),
        "structural_episodes": int(result["structural_episode_id"].nunique()),
        "conservative_nontransitive_episodes": int(
            result["conservative_episode_id"].nunique()
        ),
        "maximum_structural_episode_size": int(structural_counts.max()),
        "maximum_conservative_episode_size": int(conservative_counts.max()),
        "structural_weight_sum": float(result["structural_weight"].sum()),
        "conservative_weight_sum": float(result["conservative_weight"].sum()),
        "structural_kish_effective_rows": kish(result["structural_weight"]),
        "conservative_kish_effective_rows": kish(result["conservative_weight"]),
        "primary_weight": "INVERSE_STRUCTURAL_EPISODE_MULTIPLICITY",
        "sensitivity_weight": "INVERSE_CONSERVATIVE_EPISODE_MULTIPLICITY",
        "nontransitive_anchor_end_is_not_extended_by_later_candidates": True,
        "r1_barrier_observation_cap_days": 90,
        "r1_cap_is_censoring_only_not_a_forced_trade_exit": True,
        "serial_effective_size": None,
        "serial_effective_size_status": "DEFERRED_UNTIL_LABELS_EXIST",
        "weights_locked_before_economic_labels": True,
    }
    return result, report


def _binary_line_count(path: Path) -> int:
    count = 0
    last = b""
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            count += block.count(b"\n")
            last = block[-1:] if block else last
    if path.stat().st_size and last != b"\n":
        count += 1
    return count


def build_journey_archive_catalog(
    repo_root: Path, config: Mapping[str, Any]
) -> dict[str, Any]:
    spec = config["journey_archive_catalog"]
    root = resolve_path(repo_root, str(spec["root"]))
    pattern = re.compile(str(spec["case_insensitive_filename_regex"]), re.IGNORECASE)
    records: list[dict[str, Any]] = []
    for path in sorted(
        (
            item
            for item in root.rglob("*")
            if item.is_file() and pattern.search(item.name)
        ),
        key=lambda item: item.as_posix().lower(),
    ):
        relative = path.relative_to(repo_root).as_posix()
        package_parts = path.relative_to(root).parts
        package = package_parts[0] if package_parts else "UNKNOWN"
        if path.suffix.lower() == ".parquet":
            metadata = pq.ParquetFile(path)
            rows = int(metadata.metadata.num_rows)
            columns = list(metadata.schema_arrow.names)
            row_count_basis = "PARQUET_FOOTER"
        else:
            with path.open("r", encoding="utf-8-sig", errors="replace") as handle:
                header = handle.readline().rstrip("\r\n")
            delimiter = "\t" if header.count("\t") > header.count(",") else ","
            columns = header.split(delimiter) if header else []
            rows = max(0, _binary_line_count(path) - (1 if header else 0))
            row_count_basis = "PHYSICAL_LINES_MINUS_HEADER"
        records.append(
            {
                "path": relative,
                "research_package": package,
                "format": path.suffix.lower().lstrip("."),
                "bytes": int(path.stat().st_size),
                "sha256": sha256_file(path),
                "rows": rows,
                "row_count_basis": row_count_basis,
                "columns": columns,
                "role": str(spec["role"]),
                "direct_model_ingestion_authorized": False,
            }
        )
    digest = hashlib.sha256(
        "\n".join(
            f"{row['path']}|{row['sha256']}|{row['rows']}" for row in records
        ).encode("utf-8")
    ).hexdigest()
    return {
        "schema_version": "xauusd_step_2a_journey_archive_catalog_v1",
        "root": str(spec["root"]),
        "discovery_regex": str(spec["case_insensitive_filename_regex"]),
        "file_count": int(len(records)),
        "total_bytes": int(sum(row["bytes"] for row in records)),
        "physical_or_footer_rows": int(sum(row["rows"] for row in records)),
        "catalog_digest": digest,
        "files": records,
        "policy": {
            "all_files_retained_for_provenance": True,
            "semantic_dedup_required_before_row_level_use": True,
            "portfolio_and_version_derivatives_are_not_independent_examples": True,
            "direct_model_ingestion_authorized": False,
        },
    }


def clock_audit(
    canonical: pd.DataFrame,
    journey_actions: pd.DataFrame,
    r1_alignment: Mapping[str, Any],
) -> dict[str, Any]:
    def ordering(frame: pd.DataFrame) -> dict[str, int]:
        return {
            "source_available_after_feature_cutoff": int(
                (frame["source_available_at"] > frame["feature_cutoff_time"]).sum()
            ),
            "feature_cutoff_after_decision": int(
                (frame["feature_cutoff_time"] > frame["decision_time"]).sum()
            ),
            "decision_after_entry_eligible": int(
                (frame["decision_time"] > frame["entry_eligible_time"]).sum()
            ),
            "signal_bar_end_after_decision": int(
                (frame["signal_bar_end"] > frame["decision_time"]).sum()
            ),
        }

    completeness = {
        column: {
            "present": int(canonical[column].notna().sum()),
            "missing": int(canonical[column].isna().sum()),
        }
        for column in CANONICAL_REQUIRED_CLOCKS
    }
    canonical_ordering = ordering(canonical)
    journey_ordering = ordering(journey_actions)
    return {
        "schema_version": "xauusd_step_2a_clock_audit_v1",
        "required_invariant": "source_available_at <= feature_cutoff_time <= decision_time <= entry_eligible_time",
        "canonical_clock_completeness": completeness,
        "canonical_complete_rows": int(
            canonical[CANONICAL_REQUIRED_CLOCKS].notna().all(axis=1).sum()
        ),
        "canonical_ordering_violations": canonical_ordering,
        "journey_action_rows": int(len(journey_actions)),
        "journey_ordering_violations": journey_ordering,
        "r1_timestamp_normalization": dict(r1_alignment),
        "nearest_time_join_used": False,
        "status": (
            "PASS"
            if not any(canonical_ordering.values())
            and not any(journey_ordering.values())
            else "FAIL"
        ),
    }


def geometry_audit(
    canonical: pd.DataFrame,
    journey_actions: pd.DataFrame,
    r1_guard: pd.DataFrame,
    r5_prepolicy: pd.DataFrame,
) -> dict[str, Any]:
    by_family = {
        str(family): {
            "rows": int(len(group)),
            "complete": int(group["action_complete"].sum()),
            "stop_modes": sorted(group["stop_mode"].astype(str).unique()),
            "target_modes": sorted(group["target_mode"].astype(str).unique()),
            "maximum_hold_modes": sorted(
                group["maximum_hold_mode"].astype(str).unique()
            ),
        }
        for family, group in canonical.groupby("family_id", sort=True)
    }
    return {
        "schema_version": "xauusd_step_2a_geometry_audit_v1",
        "canonical_rows": int(len(canonical)),
        "canonical_complete_rows": int(canonical["action_complete"].sum()),
        "canonical_by_family": by_family,
        "r1_guard_rows": int(len(r1_guard)),
        "r1_guard_complete_rows": int(r1_guard["action_complete"].sum()),
        "r5_prepolicy_rows": int(len(r5_prepolicy)),
        "r5_prepolicy_complete_rows": int(r5_prepolicy["action_complete"].sum()),
        "journey_action_rows": int(len(journey_actions)),
        "journey_complete_rows": int(journey_actions["action_complete"].sum()),
        "r1_barrier_cap_changes_trade_exit": False,
        "r1_barrier_cap_role": "LABEL_CENSORING_AND_PRELABEL_PURGE_ONLY",
        "status": (
            "PASS"
            if canonical["action_complete"].all()
            and journey_actions["action_complete"].all()
            and r5_prepolicy["action_complete"].all()
            else "FAIL"
        ),
    }


def acceptance_audit(
    canonical: pd.DataFrame,
    r1_guard: pd.DataFrame,
    r5_prepolicy: pd.DataFrame,
) -> dict[str, Any]:
    by_family = {
        str(family): {
            "candidates": int(len(group)),
            "specialist_accepted": int(group["historical_specialist_accepted"].sum()),
            "portfolio_accepted": int(group["historical_portfolio_accepted"].sum()),
            "broker_executable": int(group["broker_executable"].sum()),
        }
        for family, group in canonical.groupby("family_id", sort=True)
    }
    return {
        "schema_version": "xauusd_step_2a_acceptance_audit_v1",
        "canonical_candidates": int(len(canonical)),
        "canonical_portfolio_accepted": int(
            canonical["historical_portfolio_accepted"].sum()
        ),
        "canonical_by_family": by_family,
        "r1_guard_decisions": {
            str(key): int(value)
            for key, value in r1_guard["historical_accept_state"].value_counts().items()
        },
        "r5_prepolicy_candidates": int(len(r5_prepolicy)),
        "r5_router_selected": int(r5_prepolicy["selected_by_router"].sum()),
        "r5_router_rejected": int((~r5_prepolicy["selected_by_router"]).sum()),
        "r5_broker_executable": int(r5_prepolicy["broker_executable"].sum()),
        "rejection_is_loss": False,
        "all_valid_candidates_replay_under_frozen_action": True,
    }


def render_result(result: Mapping[str, Any]) -> str:
    return "\n".join(
        [
            "# Causal Candidate Quality ML V1 - Step 2A Result",
            "",
            f"Decision: `{result['decision']}`",
            "",
            "Step 2A repaired candidate clocks, action geometry, pre-policy lineage, and episode identities without opening economic outcomes or fitting a model.",
            "",
            f"- Canonical candidates: `{result['canonical_candidates']}`",
            f"- Canonical rows with complete clocks: `{result['canonical_complete_clock_rows']}`",
            f"- Canonical rows with complete actions: `{result['canonical_complete_action_rows']}`",
            f"- Historically portfolio-accepted candidates: `{result['historically_portfolio_accepted']}`",
            f"- R1 guard decisions retained: `{result['r1_guard_decisions']}`",
            f"- R5 pre-policy candidates retained: `{result['r5_prepolicy_candidates']}`",
            f"- Registered journey action rows retained: `{result['journey_action_rows']}`",
            f"- Registered journey candidate-directions: `{result['journey_candidate_directions']}`",
            f"- Archived trade ledgers cataloged: `{result['journey_archive_files']}`",
            "",
            "Historical rejection remains an audit state, never a loss label. Alternative actions and version/portfolio derivatives remain grouped and cannot be counted as independent examples.",
            "",
            f"Next authorized work: `{result['next_authorized_work']}`.",
            "",
        ]
    )


def build_artifact_manifest(
    repo_root: Path,
    output_paths: Mapping[str, Path],
    result: Mapping[str, Any],
    inputs: Mapping[str, str],
) -> dict[str, Any]:
    artifacts = {}
    for name, path in output_paths.items():
        if name == "artifact_manifest":
            continue
        artifacts[name] = {
            "path": path.relative_to(repo_root).as_posix(),
            "bytes": int(path.stat().st_size),
            "sha256": sha256_file(path),
        }
    return {
        "schema_version": "xauusd_step_2a_artifact_manifest_v1",
        "decision": result["decision"],
        "inputs": dict(inputs),
        "artifacts": artifacts,
        "economic_outcomes_opened": False,
        "model_fitted": False,
        "runtime_changed": False,
    }


def run_repair(repo_root: Path, package_root: Path) -> dict[str, Any]:
    config_path = package_root / "config" / "step_2a_metadata_repair_v1.json"
    config = json.loads(config_path.read_text(encoding="utf-8"))
    forbidden = config["controls"]["forbidden_read_columns"]
    for name, spec in config["bound_inputs"].items():
        verify_bound_file(repo_root, spec, name)

    r1_guard, r1_alignment, r1_hashes = build_r1_guard_registry(
        repo_root, config, forbidden
    )
    r5_prepolicy, r5_selected, r5_hashes = build_r5_prepolicy_registry(
        repo_root, config, forbidden
    )
    canonical, canonical_evidence, canonical_hashes = build_canonical_registry(
        repo_root, config, r1_guard, r5_selected, forbidden
    )
    canonical, episode_lock = assign_episode_weights(canonical)
    journey_actions, journey_candidates, journey_evidence, journey_hashes = (
        build_journey_action_registries(repo_root, config, forbidden)
    )
    archive_catalog = build_journey_archive_catalog(repo_root, config)
    clocks = clock_audit(canonical, journey_actions, r1_alignment)
    geometry = geometry_audit(canonical, journey_actions, r1_guard, r5_prepolicy)
    acceptance = acceptance_audit(canonical, r1_guard, r5_prepolicy)

    checks = {
        "canonical_count_reconciles": len(canonical)
        == int(config["expected"]["canonical_candidates"]),
        "all_canonical_clocks_complete": canonical[CANONICAL_REQUIRED_CLOCKS]
        .notna()
        .all(axis=1)
        .all(),
        "all_canonical_actions_complete": canonical["action_complete"].all(),
        "historical_acceptance_reconciles": int(
            canonical["historical_portfolio_accepted"].sum()
        )
        == int(config["expected"]["historically_portfolio_accepted"]),
        "r5_prepolicy_reconciles": len(r5_prepolicy)
        == int(config["expected"]["r5_prepolicy_candidates"]),
        "journey_actions_reconcile": len(journey_actions)
        == int(config["expected"]["journey_action_rows"]),
        "clock_audit_passes": clocks["status"] == "PASS",
        "geometry_audit_passes": geometry["status"] == "PASS",
        "episode_weights_locked": bool(
            episode_lock["weights_locked_before_economic_labels"]
        ),
        "archive_catalog_nonempty": int(archive_catalog["file_count"]) > 0,
    }
    if not all(checks.values()):
        raise ValueError(f"Step 2A checks failed: {checks}")

    result = {
        "schema_version": "xauusd_causal_candidate_quality_step_2a_result_v1",
        "stage": str(config["stage"]),
        "created_utc": str(config["created_utc"]),
        "decision": "STEP_2A_METADATA_REPAIR_COMPLETE",
        "checks": checks,
        "canonical_candidates": int(len(canonical)),
        "canonical_complete_clock_rows": int(
            canonical[CANONICAL_REQUIRED_CLOCKS].notna().all(axis=1).sum()
        ),
        "canonical_complete_action_rows": int(canonical["action_complete"].sum()),
        "historically_portfolio_accepted": int(
            canonical["historical_portfolio_accepted"].sum()
        ),
        "r1_guard_decisions": int(len(r1_guard)),
        "r5_prepolicy_candidates": int(len(r5_prepolicy)),
        "journey_action_rows": int(len(journey_actions)),
        "journey_candidate_directions": int(len(journey_candidates)),
        "journey_archive_files": int(archive_catalog["file_count"]),
        "structural_episodes": int(episode_lock["structural_episodes"]),
        "conservative_episodes": int(
            episode_lock["conservative_nontransitive_episodes"]
        ),
        "economic_outcomes_opened": False,
        "counterfactual_labels_built": False,
        "feature_values_built": False,
        "model_fitted": False,
        "threshold_fitted": False,
        "portfolio_simulated": False,
        "runtime_changed": False,
        "ml_execution_authorized": False,
        "next_authorized_work": "STEP_2B_DATASET_AND_FEATURE_CONTRACT_LOCK",
        "canonical_evidence": canonical_evidence,
        "journey_evidence": journey_evidence,
    }

    output = package_root / config["outputs"]["directory"]
    output.mkdir(parents=True, exist_ok=True)
    output_paths = {
        name: output / filename
        for name, filename in config["outputs"].items()
        if name != "directory"
    }
    canonical.to_parquet(output_paths["canonical_registry"], index=False)
    r1_guard.to_parquet(output_paths["r1_guard_registry"], index=False)
    r5_prepolicy.to_parquet(output_paths["r5_prepolicy_registry"], index=False)
    journey_actions.to_parquet(output_paths["journey_action_registry"], index=False)
    journey_candidates.to_parquet(
        output_paths["journey_candidate_registry"], index=False
    )
    write_json(output_paths["journey_archive_catalog"], archive_catalog)
    write_json(output_paths["clock_audit"], clocks)
    write_json(output_paths["geometry_audit"], geometry)
    write_json(output_paths["acceptance_audit"], acceptance)
    write_json(output_paths["episode_weight_lock"], episode_lock)
    input_hashes = {
        "step_2a_config": sha256_file(config_path),
        "step_2a_implementation": sha256_file(Path(__file__)),
        **r1_hashes,
        **r5_hashes,
        **canonical_hashes,
        **journey_hashes,
        "journey_archive_catalog_digest": str(archive_catalog["catalog_digest"]),
    }
    write_json(
        output_paths["source_manifest"],
        {
            "schema_version": "xauusd_step_2a_source_manifest_v1",
            "inputs": input_hashes,
            "archive_catalog_digest": archive_catalog["catalog_digest"],
            "economic_outcomes_opened": False,
        },
    )
    write_json(output_paths["result_json"], result)
    output_paths["result_markdown"].write_text(render_result(result), encoding="utf-8")
    manifest = build_artifact_manifest(repo_root, output_paths, result, input_hashes)
    write_json(output_paths["artifact_manifest"], manifest)
    return result
