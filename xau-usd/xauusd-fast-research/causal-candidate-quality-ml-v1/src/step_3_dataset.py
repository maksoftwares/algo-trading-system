from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

import numpy as np
import pandas as pd

from step_3_common import (
    canonical_json_sha256,
    resolve_path,
    sha256_file,
    stable_parquet,
    timestamp_ms,
    verify_bound_file,
    write_json,
)
from step_3_features import (
    CompletedAtrReference,
    build_atr_reference,
    build_feature_frame,
)
from step_3_labels import label_frame
from step_3_sources import (
    ComexTradeStore,
    LockedDukascopyStore,
    load_bound_decoder,
    resolve_source_roots,
)


RESOLVED_STATUSES = {
    "RESOLVED_STOP",
    "RESOLVED_STOP_SLIPPAGE",
    "RESOLVED_TARGET",
    "RESOLVED_FIXED_HORIZON",
}

DATASET_METADATA_COLUMNS = [
    "candidate_id",
    "population",
    "direction",
    "source_id",
    "source_available_at",
    "signal_bar_end",
    "decision_time",
    "feature_cutoff_time",
    "entry_eligible_time",
    "structural_episode_id",
    "conservative_episode_id",
    "structural_weight",
    "conservative_weight",
    "broker_executable",
    "historical_accept_state",
    "historical_decision_reason",
    "historical_portfolio_accepted",
]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_controls(config: Mapping[str, Any]) -> None:
    controls = config["controls"]
    required_true = [
        "economic_outcomes_authorized",
        "counterfactual_label_build_authorized",
        "feature_value_build_authorized",
    ]
    required_false = [
        "model_training_authorized",
        "threshold_fitting_authorized",
        "portfolio_simulation_authorized",
        "runtime_change_authorized",
        "new_data_acquisition_authorized",
        "historical_rejection_is_loss",
        "journey_rows_enter_primary_fit",
        "archive_direct_ingestion_authorized",
    ]
    failed = [key for key in required_true if not bool(controls[key])]
    failed.extend(key for key in required_false if bool(controls[key]))
    if failed:
        raise ValueError(f"Step 3 controls fail closed: {failed}")


def _read_bound_parquet(
    repo_root: Path,
    step2b: Mapping[str, Any],
    key: str,
    columns: list[str] | None = None,
) -> pd.DataFrame:
    path = verify_bound_file(repo_root, step2b["bound_inputs"][key], key)
    return pd.read_parquet(path, columns=columns)


def attach_canonical_geometry(
    canonical: pd.DataFrame,
    *,
    repo_root: Path,
    step2b: Mapping[str, Any],
) -> pd.DataFrame:
    result = canonical.copy()
    result["planned_stop_price"] = np.nan
    result["geometry_source_value"] = np.nan

    r1 = result["family_id"].eq("R1_UPTREND")
    result.loc[r1, "planned_stop_price"] = (
        pd.to_numeric(result.loc[r1, "stop_value"], errors="coerce") * 0.01
    )
    result.loc[r1, "geometry_source_value"] = pd.to_numeric(
        result.loc[r1, "stop_value"], errors="coerce"
    )

    source_specs = [
        ("r2_r3_candidates", {"R2_DOWNTREND", "R3_COMPRESSION"}),
        ("r4_candidates", {"R4_CHOP"}),
        ("r5_candidates", {"R5_TRANSITION"}),
    ]
    for key, families in source_specs:
        source = _read_bound_parquet(
            repo_root, step2b, key, ["candidate_id", "signal_atr"]
        )
        if source["candidate_id"].duplicated().any():
            raise ValueError(f"Geometry source IDs are duplicated: {key}")
        mapping = source.set_index("candidate_id")["signal_atr"]
        mask = result["family_id"].isin(families)
        signal_atr = result.loc[mask, "source_candidate_id"].map(mapping)
        result.loc[mask, "geometry_source_value"] = signal_atr.to_numpy()
        result.loc[mask, "planned_stop_price"] = (
            signal_atr.to_numpy(dtype=float)
            * pd.to_numeric(result.loc[mask, "stop_atr"], errors="coerce").to_numpy()
        )

    v57 = _read_bound_parquet(
        repo_root, step2b, "v57_candidates", ["trade_id", "risk_usd"]
    )
    if v57["trade_id"].duplicated().any():
        raise ValueError("V57 geometry source IDs are duplicated")
    v57_risk = v57.set_index("trade_id")["risk_usd"]
    addon = result["source_id"].eq("CANONICAL_V57_ADDONS")
    risk = result.loc[addon, "source_candidate_id"].map(v57_risk)
    result.loc[addon, "geometry_source_value"] = risk.to_numpy()
    result.loc[addon, "planned_stop_price"] = risk.to_numpy()

    invalid = ~np.isfinite(result["planned_stop_price"].to_numpy(dtype=float)) | result[
        "planned_stop_price"
    ].le(0.0)
    if invalid.any():
        bad = result.loc[invalid, ["candidate_id", "family_id"]].head(10)
        raise ValueError(f"Canonical geometry is incomplete:\n{bad}")
    if len(result) != 3752 or result["candidate_id"].duplicated().any():
        raise ValueError("Canonical geometry cardinality changed")
    return result


def attach_journey_geometry(
    journey: pd.DataFrame,
    *,
    repo_root: Path,
    step2a_manifest: Mapping[str, Any],
) -> pd.DataFrame:
    config_path = repo_root / (
        "xau-usd/xauusd-fast-research/causal-candidate-quality-ml-v1/"
        "config/step_2a_metadata_repair_v1.json"
    )
    expected_config = str(step2a_manifest["inputs"]["step_2a_config"])
    if sha256_file(config_path) != expected_config:
        raise ValueError(
            "Step 2A config changed after the repaired registry was locked"
        )
    step2a = load_json(config_path)
    frames: list[pd.DataFrame] = []
    for spec in step2a["journey_action_sources"]:
        path = resolve_path(repo_root, str(spec["path"])).resolve()
        source_id = str(spec["source_id"])
        expected = str(step2a_manifest["inputs"][source_id])
        if sha256_file(path) != expected:
            raise ValueError(f"Journey geometry source changed: {path}")
        source = pd.read_parquet(
            path, columns=["event_id", "direction", "action_id", "atr_m5"]
        )
        source["source_id"] = source_id
        frames.append(source)
    geometry = pd.concat(frames, ignore_index=True)
    keys = ["source_id", "event_id", "direction", "action_id"]
    if geometry.duplicated(keys).any():
        raise ValueError("Journey source geometry keys are duplicated")
    result = journey.merge(geometry, on=keys, how="left", validate="one_to_one")
    result["planned_stop_price"] = pd.to_numeric(
        result["atr_m5"], errors="coerce"
    ) * pd.to_numeric(result["stop_atr"], errors="coerce")
    if result["planned_stop_price"].isna().any():
        raise ValueError("Journey action geometry is incomplete")
    result["family_id"] = ""
    return result


def assign_splits(
    canonical: pd.DataFrame,
    labels: pd.DataFrame,
    split_plan: Mapping[str, Any],
) -> tuple[pd.DataFrame, list[dict[str, Any]]]:
    frame = canonical[
        [
            "candidate_id",
            "family_id",
            "decision_time",
            "planned_observation_end",
            "structural_episode_id",
        ]
    ].merge(
        labels[["candidate_id", "label_end_time", "label_status"]],
        on="candidate_id",
        validate="one_to_one",
    )
    episode = frame.groupby("structural_episode_id", sort=False).agg(
        episode_decision_time=("decision_time", "min"),
        episode_planned_end=("planned_observation_end", "max"),
        episode_actual_end=("label_end_time", "max"),
    )
    frame = frame.join(episode, on="structural_episode_id")
    rows: list[pd.DataFrame] = []
    audits: list[dict[str, Any]] = []
    for fold in split_plan["folds"]:
        fold_id = str(fold["fold_id"])
        calibration_start = pd.Timestamp(fold["calibration_start"])
        test_start = pd.Timestamp(fold["test_start"])
        test_end = pd.Timestamp(fold["test_end_exclusive"])
        decision = frame["episode_decision_time"]
        planned = frame["episode_planned_end"]
        actual = frame["episode_actual_end"]
        assignment = pd.Series("OUTSIDE", index=frame.index, dtype="string")
        test = decision.ge(test_start) & decision.lt(test_end)
        calibration_clock = decision.ge(calibration_start) & decision.lt(test_start)
        fit_clock = decision.lt(calibration_start)
        calibration = calibration_clock & planned.lt(test_start) & actual.lt(test_start)
        fit = fit_clock & planned.lt(calibration_start) & actual.lt(calibration_start)
        assignment.loc[test] = "TEST"
        assignment.loc[calibration] = "CALIBRATION"
        assignment.loc[fit] = "FIT"
        purged = (calibration_clock | fit_clock) & assignment.eq("OUTSIDE")
        assignment.loc[purged] = "PURGED_LABEL_INTERVAL"
        resolved = frame["label_status"].isin(RESOLVED_STATUSES)
        eligible = resolved & assignment.isin(["FIT", "CALIBRATION", "TEST"])
        part = pd.DataFrame(
            {
                "fold_id": fold_id,
                "candidate_id": frame["candidate_id"],
                "structural_episode_id": frame["structural_episode_id"],
                "assignment": assignment,
                "resolved_label": resolved,
                "dataset_eligible": eligible,
            }
        )
        rows.append(part)
        expected = fold["outcome_blind_counts"]
        observed = {
            name.lower(): int(assignment.eq(name).sum())
            for name in ("FIT", "CALIBRATION", "TEST")
        }
        eligible_counts = {
            name.lower(): int((assignment.eq(name) & resolved).sum())
            for name in ("FIT", "CALIBRATION", "TEST")
        }
        if observed["fit"] > int(expected["fit"]) or observed["calibration"] > int(
            expected["calibration"]
        ):
            raise ValueError(
                f"Actual label-end purge increased a locked split: {fold_id}"
            )
        if observed["test"] != int(expected["test"]):
            raise ValueError(f"Test candidate count changed: {fold_id}")
        audits.append(
            {
                "fold_id": fold_id,
                "outcome_blind_expected": expected,
                "after_actual_label_end_purge": observed,
                "resolved_dataset_eligible": eligible_counts,
                "purged_label_interval": int(
                    assignment.eq("PURGED_LABEL_INTERVAL").sum()
                ),
            }
        )
    result = pd.concat(rows, ignore_index=True)
    siblings = result.groupby(["fold_id", "structural_episode_id"])[
        "assignment"
    ].nunique()
    if int((siblings > 1).sum()):
        raise ValueError("Structural episode siblings crossed a split")
    return result, audits


def _kish(weights: np.ndarray) -> float:
    denominator = float(np.square(weights).sum())
    return float(weights.sum() ** 2 / denominator) if denominator > 0.0 else 0.0


def _serial_effective_size(
    values: np.ndarray, maximum_lag: int
) -> tuple[float, list[float]]:
    values = np.asarray(values, dtype=float)
    values = values[np.isfinite(values)]
    count = len(values)
    if count < 3:
        return float(count), []
    centered = values - float(np.mean(values))
    denominator = float(np.dot(centered, centered))
    if denominator <= 0.0:
        return float(count), []
    correlations: list[float] = []
    for lag in range(1, min(maximum_lag, count - 1) + 1):
        correlations.append(
            float(np.dot(centered[:-lag], centered[lag:]) / denominator)
        )
    retained: list[float] = []
    for start in range(0, len(correlations), 2):
        pair = correlations[start : start + 2]
        if len(pair) < 2 or sum(pair) <= 0.0:
            break
        retained.extend(pair)
    tau = max(1.0, 1.0 + 2.0 * sum(retained))
    return min(float(count), float(count) / tau), retained


def effective_sample_report(
    canonical: pd.DataFrame, labels: pd.DataFrame, contract: Mapping[str, Any]
) -> dict[str, Any]:
    frame = canonical[
        ["candidate_id", "decision_time", "structural_episode_id", "structural_weight"]
    ].merge(
        labels[["candidate_id", "label_status", "stress_net_r"]],
        on="candidate_id",
        validate="one_to_one",
    )
    frame = frame.loc[frame["label_status"].isin(RESOLVED_STATUSES)].copy()
    episode = (
        frame.assign(weighted=frame["stress_net_r"] * frame["structural_weight"])
        .groupby("structural_episode_id", as_index=False)
        .agg(decision_time=("decision_time", "min"), outcome=("weighted", "sum"))
        .sort_values("decision_time", kind="stable")
    )
    weights = frame["structural_weight"].to_numpy(dtype=float)
    kish = _kish(weights)
    serial, retained = _serial_effective_size(
        episode["outcome"].to_numpy(dtype=float),
        int(contract["serial_effective_size_contract"]["maximum_lag"]),
    )
    episode_count = len(episode)
    return {
        "schema_version": "xauusd_step_3_effective_sample_v1",
        "resolved_candidate_rows": len(frame),
        "resolved_structural_episodes": episode_count,
        "kish_effective_size": kish,
        "serial_effective_size": serial,
        "conservative_effective_size": min(float(episode_count), kish, serial),
        "serial_rule": contract["serial_effective_size_contract"][
            "autocorrelation_rule"
        ],
        "serial_retained_autocorrelations": retained,
        "maximum_lag": int(contract["serial_effective_size_contract"]["maximum_lag"]),
    }


def build_quality_audit(
    canonical: pd.DataFrame,
    labels: pd.DataFrame,
    features: pd.DataFrame,
    journey_labels: pd.DataFrame,
    feature_names: list[str],
    split_audits: list[dict[str, Any]],
) -> dict[str, Any]:
    resolved = labels["label_status"].isin(RESOLVED_STATUSES)
    journey_resolved = journey_labels["label_status"].isin(RESOLVED_STATUSES)
    numeric_features = [
        name
        for name in feature_names
        if name not in {"family_id", "broad_mechanic", "stop_mode", "target_mode"}
    ]
    missing = {
        name: {
            "missing_rows": int(features[name].isna().sum()),
            "missing_fraction": float(features[name].isna().mean()),
        }
        for name in numeric_features
    }
    clocks = (
        canonical["source_available_at"].le(canonical["feature_cutoff_time"])
        & canonical["feature_cutoff_time"].le(canonical["decision_time"])
        & canonical["decision_time"].le(canonical["entry_eligible_time"])
    )
    rejected = ~canonical["historical_portfolio_accepted"]
    merged = canonical[["candidate_id", "historical_portfolio_accepted"]].merge(
        labels[["candidate_id", "label_status", "stress_net_r_positive"]],
        on="candidate_id",
        validate="one_to_one",
    )
    rejected_resolved = merged.loc[
        ~merged["historical_portfolio_accepted"]
        & merged["label_status"].isin(RESOLVED_STATUSES)
    ]
    return {
        "schema_version": "xauusd_step_3_data_quality_audit_v1",
        "canonical": {
            "candidate_rows": len(canonical),
            "resolved_rows": int(resolved.sum()),
            "unresolved_rows": int((~resolved).sum()),
            "winner_rows": int(
                labels.loc[resolved, "stress_net_r_positive"].eq(True).sum()
            ),
            "failing_rows": int(
                labels.loc[resolved, "stress_net_r_positive"].eq(False).sum()
            ),
            "label_status_counts": labels["label_status"]
            .value_counts()
            .sort_index()
            .to_dict(),
            "historically_rejected_rows": int(rejected.sum()),
            "resolved_historically_rejected_rows": len(rejected_resolved),
            "winning_historically_rejected_rows": int(
                rejected_resolved["stress_net_r_positive"].eq(True).sum()
            ),
            "historical_rejection_used_as_loss": False,
        },
        "journey": {
            "action_rows": len(journey_labels),
            "resolved_rows": int(journey_resolved.sum()),
            "unresolved_rows": int((~journey_resolved).sum()),
            "winner_rows": int(
                journey_labels.loc[journey_resolved, "stress_net_r_positive"]
                .eq(True)
                .sum()
            ),
            "failing_rows": int(
                journey_labels.loc[journey_resolved, "stress_net_r_positive"]
                .eq(False)
                .sum()
            ),
            "label_status_counts": journey_labels["label_status"]
            .value_counts()
            .sort_index()
            .to_dict(),
            "enters_primary_fit": False,
        },
        "features": {
            "rows": len(features),
            "exact_raw_feature_columns": len(feature_names),
            "ordered_feature_sha256": canonical_json_sha256(feature_names),
            "numeric_missingness": missing,
            "xau_status_counts": features["xau_feature_status"]
            .value_counts()
            .to_dict(),
            "crossasset_status_counts": features["crossasset_feature_status"]
            .value_counts()
            .to_dict(),
            "comex_status_counts": features["comex_feature_status"]
            .value_counts()
            .to_dict(),
        },
        "causality": {
            "complete_clock_rows": int(clocks.sum()),
            "clock_violations": int((~clocks).sum()),
            "future_or_nearest_join_authorized": False,
            "forming_bar_authorized": False,
            "outcome_columns_used_as_features": False,
        },
        "split_audit": split_audits,
        "model_fitted": False,
        "threshold_fitted": False,
        "runtime_changed": False,
    }


def assemble_canonical_dataset(
    canonical: pd.DataFrame,
    features: pd.DataFrame,
    labels: pd.DataFrame,
) -> pd.DataFrame:
    family_check = canonical[["candidate_id", "family_id"]].merge(
        features[["candidate_id", "family_id"]],
        on="candidate_id",
        validate="one_to_one",
        suffixes=("_registry", "_feature"),
    )
    if not family_check["family_id_registry"].equals(
        family_check["family_id_feature"]
    ):
        raise ValueError("Canonical registry and feature family IDs differ")
    dataset = (
        canonical[DATASET_METADATA_COLUMNS]
        .merge(features, on="candidate_id", validate="one_to_one")
        .merge(labels, on="candidate_id", validate="one_to_one")
    )
    if "family_id" not in dataset or any(
        name.startswith("family_id_") for name in dataset.columns
    ):
        raise ValueError("Canonical dataset does not expose one exact family_id")
    return dataset.sort_values(
        ["decision_time", "candidate_id"], kind="stable"
    ).reset_index(drop=True)


def artifact_manifest(
    *, output_dir: Path, repo_root: Path, result: Mapping[str, Any]
) -> dict[str, Any]:
    artifacts: dict[str, Any] = {}
    for path in sorted(output_dir.iterdir()):
        if not path.is_file() or path.name == "STEP_3_ARTIFACT_MANIFEST.json":
            continue
        artifacts[path.stem.lower()] = {
            "path": path.relative_to(repo_root).as_posix(),
            "bytes": path.stat().st_size,
            "sha256": sha256_file(path),
        }
    return {
        "schema_version": "xauusd_step_3_artifact_manifest_v1",
        "decision": result["decision"],
        "definition_lock_sha256": result["definition_lock_sha256"],
        "economic_outcomes_opened": True,
        "model_fitted": False,
        "runtime_changed": False,
        "artifacts": artifacts,
    }


def run_step_3(
    repo_root: Path, package_root: Path, config_path: Path
) -> dict[str, Any]:
    config = load_json(config_path)
    validate_controls(config)
    bound = {
        key: verify_bound_file(repo_root, spec, key)
        for key, spec in config["bound_inputs"].items()
    }
    step2b = load_json(bound["step_2b_contract"])
    step2b_lock = load_json(bound["step_2b_lock"])
    if step2b_lock["next_stage"] != "STEP_3_COUNTERFACTUAL_LABEL_AND_CAUSAL_FEATURE_BUILD":
        raise ValueError("Step 2B did not authorize Step 3")

    canonical = _read_bound_parquet(repo_root, step2b, "canonical_registry")
    journey = _read_bound_parquet(repo_root, step2b, "journey_action_registry")
    source_manifest_path = (
        package_root / "outputs/step_2b/STEP_2B_SOURCE_CORPUS_MANIFEST.json"
    )
    split_plan_path = (
        package_root / "outputs/step_2b/STEP_2B_OUTCOME_BLIND_SPLIT_PLAN.json"
    )
    step2a_manifest_path = (
        package_root / "outputs/step_2a/STEP_2A_ARTIFACT_MANIFEST.json"
    )
    source_manifest = load_json(source_manifest_path)
    split_plan = load_json(split_plan_path)
    step2a_manifest = load_json(step2a_manifest_path)
    definition_lock_sha = str(step2b_lock["definition_contract_sha256"])

    canonical = attach_canonical_geometry(canonical, repo_root=repo_root, step2b=step2b)
    journey = attach_journey_geometry(
        journey, repo_root=repo_root, step2a_manifest=step2a_manifest
    )

    dukascopy_root, _ = resolve_source_roots(config)
    decoder_path = verify_bound_file(
        repo_root, step2b["bound_inputs"]["dukascopy_decoder"], "dukascopy_decoder"
    )
    decoder = load_bound_decoder(decoder_path)
    build = config["build"]

    def make_store(symbol: str, cache_size: int) -> LockedDukascopyStore:
        return LockedDukascopyStore(
            root=dukascopy_root,
            symbol=symbol,
            source_manifest=source_manifest,
            decoder=decoder,
            price_decimals=int(config["source"]["price_decimals"]),
            cache_size=cache_size,
        )

    xau_store = make_store("XAUUSD", int(build["xau_hour_cache_size"]))
    dollar_store = make_store("DOLLARIDXUSD", int(build["crossasset_hour_cache_size"]))
    bond_store = make_store("USTBONDTRUSD", int(build["crossasset_hour_cache_size"]))
    comex_manifest = verify_bound_file(
        repo_root,
        step2b["bound_inputs"]["comex_source_manifest"],
        "comex_source_manifest",
    )
    comex_store = ComexTradeStore(
        manifest_path=comex_manifest, cache_size=int(build["comex_day_cache_size"])
    )

    output_dir = package_root / str(config["outputs"]["directory"])
    output_dir.mkdir(parents=True, exist_ok=True)
    outputs = {
        key: output_dir / str(value)
        for key, value in config["outputs"].items()
        if key != "directory"
    }
    source_corpus_sha = sha256_file(source_manifest_path)
    atr_frame = build_atr_reference(
        output_path=outputs["xau_atr_reference"],
        manifest_path=outputs["xau_atr_reference_manifest"],
        xau_store=xau_store,
        post2016_cache_path=bound["xau_m5_cache"],
        source_corpus_sha256=source_corpus_sha,
        pre2016_end_ms=timestamp_ms(build["pre2016_end_exclusive_utc"]),
    )
    atr_source = CompletedAtrReference(atr_frame)

    canonical_labels = (
        label_frame(
            canonical.assign(action_row_id=""),
            store=xau_store,
            label_contract=step2b["label_contract"],
        )
        .sort_values("candidate_id", kind="stable")
        .reset_index(drop=True)
    )
    stable_parquet(canonical_labels, outputs["canonical_labels"])

    features = (
        build_feature_frame(
            canonical,
            contract=step2b,
            atr_source=atr_source,
            xau_store=xau_store,
            dollar_store=dollar_store,
            bond_store=bond_store,
            comex_store=comex_store,
        )
        .sort_values("candidate_id", kind="stable")
        .reset_index(drop=True)
    )
    stable_parquet(features, outputs["canonical_features"])

    journey_labels_only = label_frame(
        journey,
        store=xau_store,
        label_contract=step2b["label_contract"],
        progress_every=int(build["progress_every_rows"]),
    )
    journey_audit_columns = [
        "action_row_id",
        "candidate_id",
        "population",
        "source_id",
        "event_id",
        "direction",
        "regime",
        "action_id",
        "broker_executable",
        "structural_episode_id",
        "candidate_action_weight",
    ]
    journey_labels = journey[journey_audit_columns].merge(
        journey_labels_only.drop(columns=["candidate_id"]),
        on="action_row_id",
        validate="one_to_one",
    )
    journey_labels = journey_labels.sort_values(
        "action_row_id", kind="stable"
    ).reset_index(drop=True)
    stable_parquet(journey_labels, outputs["journey_labels"])

    split_assignments, split_audits = assign_splits(
        canonical, canonical_labels, split_plan
    )
    stable_parquet(split_assignments, outputs["split_assignments"])
    effective = effective_sample_report(canonical, canonical_labels, step2b)
    write_json(outputs["effective_sample"], effective)

    feature_names = [
        name
        for block in step2b["feature_contract"]["ordered_blocks"]
        for name in block["features"]
    ]
    quality = build_quality_audit(
        canonical,
        canonical_labels,
        features,
        journey_labels,
        feature_names,
        split_audits,
    )
    write_json(outputs["data_quality_audit"], quality)

    dataset = assemble_canonical_dataset(canonical, features, canonical_labels)
    stable_parquet(dataset, outputs["canonical_dataset"])

    source_audit = {
        "schema_version": "xauusd_step_3_source_audit_v1",
        "step_2b_source_corpus_sha256": source_corpus_sha,
        "step_2b_source_months": len(source_manifest["records"]),
        "step_2b_physical_hour_files": int(
            sum(int(row["hour_files"]) for row in source_manifest["records"])
        ),
        "dukascopy_raw_hour_verification": "SHA256_AND_TICK_COUNT_ON_EVERY_OPEN",
        "comex_daily_file_verification": "SHA256_AND_SIZE_ON_EVERY_OPEN",
        "bound_decoder_sha256": sha256_file(decoder_path),
        "xau_atr_reference_sha256": sha256_file(outputs["xau_atr_reference"]),
        "opened_source_verification": {
            "xauusd": xau_store.audit(),
            "dollaridxusd": dollar_store.audit(),
            "ustbondtrusd": bond_store.audit(),
            "comex_gc": comex_store.audit(),
        },
        "no_new_data_acquired": True,
        "paid_data_used": False,
    }
    write_json(outputs["source_audit"], source_audit)

    resolved = canonical_labels["label_status"].isin(RESOLVED_STATUSES)
    journey_resolved = journey_labels["label_status"].isin(RESOLVED_STATUSES)
    result = {
        "schema_version": "xauusd_step_3_result_v1",
        "decision": "STEP_3_COUNTERFACTUAL_LABEL_AND_CAUSAL_FEATURE_BUILD_COMPLETE",
        "definition_lock_sha256": definition_lock_sha,
        "canonical_candidate_rows": len(canonical),
        "canonical_resolved_labels": int(resolved.sum()),
        "canonical_unresolved_labels": int((~resolved).sum()),
        "canonical_winners": int(
            canonical_labels.loc[resolved, "stress_net_r_positive"].eq(True).sum()
        ),
        "canonical_failures": int(
            canonical_labels.loc[resolved, "stress_net_r_positive"].eq(False).sum()
        ),
        "journey_action_rows": len(journey_labels),
        "journey_resolved_labels": int(journey_resolved.sum()),
        "journey_unresolved_labels": int((~journey_resolved).sum()),
        "journey_structural_events": int(
            journey_labels["structural_episode_id"].nunique()
        ),
        "raw_feature_columns": len(feature_names),
        "feature_rows": len(features),
        "effective_sample": effective,
        "model_fitted": False,
        "threshold_fitted": False,
        "portfolio_simulated": False,
        "runtime_changed": False,
        "next_stage_authorized": "STEP_4_MODEL_FIT_AND_LOCKED_WALK_FORWARD_EVALUATION",
    }
    write_json(outputs["result_json"], result)
    markdown = "\n".join(
        [
            "# Step 3 Counterfactual Labels And Causal Features",
            "",
            f"Decision: `{result['decision']}`",
            "",
            f"- Canonical labels: `{result['canonical_resolved_labels']}` resolved, "
            f"`{result['canonical_unresolved_labels']}` unresolved from "
            f"`{result['canonical_candidate_rows']}` candidates.",
            f"- Canonical stressed winners/failures: `{result['canonical_winners']}` / "
            f"`{result['canonical_failures']}`.",
            f"- Journey labels: `{result['journey_resolved_labels']}` resolved, "
            f"`{result['journey_unresolved_labels']}` unresolved from "
            f"`{result['journey_action_rows']}` action rows.",
            f"- Causal feature matrix: `{result['feature_rows']}` rows and "
            f"`{result['raw_feature_columns']}` locked raw features.",
            f"- Conservative effective sample: "
            f"`{effective['conservative_effective_size']:.2f}`.",
            "- Journey failures remain a separate diagnostic library and do not enter the primary fit.",
            "- No model, threshold, portfolio, demo, or runtime action was performed.",
            "",
        ]
    )
    outputs["result_markdown"].write_text(markdown, encoding="utf-8")
    manifest = artifact_manifest(
        output_dir=output_dir, repo_root=repo_root, result=result
    )
    write_json(outputs["artifact_manifest"], manifest)
    result["artifact_manifest_sha256"] = sha256_file(outputs["artifact_manifest"])
    return result
