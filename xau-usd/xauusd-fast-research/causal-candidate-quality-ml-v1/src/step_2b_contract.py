from __future__ import annotations

import calendar
import hashlib
import json
import math
import os
from pathlib import Path
from typing import Any, Iterable, Mapping

import numpy as np
import pandas as pd
import pyarrow.parquet as pq


PACKAGE_FILES = [
    "STEP_2B_CONTRACT.md",
    "config/step_2b_dataset_feature_contract_v1.json",
    "run_step_2b_lock.py",
    "src/step_2b_contract.py",
    "tests/test_step_2b_contract.py",
]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def canonical_json_sha256(value: Any) -> str:
    payload = json.dumps(
        json_ready(value), sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


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


def write_json(path: Path, value: Mapping[str, Any]) -> None:
    path.write_text(
        json.dumps(json_ready(value), indent=2, sort_keys=True, allow_nan=False) + "\n",
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
        raise ValueError(f"Step 2B requested economic columns: {overlap}")


def load_parquet_columns(
    path: Path, columns: list[str], forbidden: Iterable[str]
) -> pd.DataFrame:
    validate_allowed_columns(columns, forbidden)
    available = set(pq.ParquetFile(path).schema_arrow.names)
    missing = sorted(set(columns) - available)
    if missing:
        raise ValueError(f"Missing metadata columns in {path}: {missing}")
    return pd.read_parquet(path, columns=columns)


def validate_closed_controls(config: Mapping[str, Any]) -> None:
    controls = config["controls"]
    required_false = [
        "economic_outcomes_authorized",
        "counterfactual_label_build_authorized",
        "feature_value_build_authorized",
        "model_training_authorized",
        "threshold_fitting_authorized",
        "portfolio_simulation_authorized",
        "runtime_change_authorized",
        "new_data_acquisition_authorized",
        "rejection_is_loss",
        "archive_rows_are_independent_training_rows",
        "same_version_contract_change_after_outcomes",
    ]
    enabled = [key for key in required_false if bool(controls[key])]
    if enabled:
        raise ValueError(f"Step 2B prohibited controls are enabled: {enabled}")


def validate_feature_contract(
    config: Mapping[str, Any], step_1: Mapping[str, Any]
) -> dict[str, Any]:
    feature_contract = config["feature_contract"]
    blocks = feature_contract["ordered_blocks"]
    ordered = [feature for block in blocks for feature in block["features"]]
    expected = int(feature_contract["exact_raw_column_count"])
    maximum = int(feature_contract["maximum_raw_columns"])
    if len(ordered) != expected or len(set(ordered)) != expected:
        raise ValueError("Step 2B feature names are duplicated or count drifted")
    if expected > maximum or maximum != int(
        step_1["features"]["maximum_primary_columns"]
    ):
        raise ValueError("Step 2B feature cap no longer matches Step 1")
    definitions = config["feature_definitions"]
    if set(ordered) != set(definitions):
        raise ValueError("Exact feature names and definitions do not reconcile")
    forbidden = {item.lower() for item in feature_contract["forbidden_predictors"]}
    overlap = sorted({item.lower() for item in ordered} & forbidden)
    if overlap:
        raise ValueError(f"Forbidden predictors entered the feature list: {overlap}")
    expected_blocks = [
        "B1_DETERMINISTIC_CANDIDATE_AND_REGIME",
        "B2_PLUS_XAU_MICROSTRUCTURE_AND_COST",
        "B3_PLUS_COMPLETED_CROSS_ASSET_STATE",
        "B4_PLUS_COMEX_RESEARCH_ABLATION",
    ]
    if [block["block_id"] for block in blocks] != expected_blocks:
        raise ValueError("Feature block order changed")
    if sum(bool(block.get("primary")) for block in blocks) != 3:
        raise ValueError("Step 1 requires exactly three primary feature blocks")
    if bool(blocks[-1].get("primary")) or not bool(blocks[-1].get("research_only")):
        raise ValueError("COMEX block must remain research-only")
    return {
        "ordered_feature_count": len(ordered),
        "ordered_feature_sha256": canonical_json_sha256(ordered),
        "definition_sha256": canonical_json_sha256(definitions),
        "primary_blocks": 3,
        "comex_research_blocks": 1,
    }


def _month_periods(start: str, end_exclusive: str) -> pd.PeriodIndex:
    first = pd.Timestamp(start).tz_localize(None).to_period("M")
    last = pd.Timestamp(end_exclusive).tz_localize(None).to_period("M") - 1
    return pd.period_range(first, last, freq="M")


def build_source_corpus_manifest(config: Mapping[str, Any]) -> dict[str, Any]:
    source = config["source_corpora"]
    root = Path(
        os.environ.get(
            str(source["storage_environment_variable"]),
            str(source["default_storage_root"]),
        )
    ).resolve()
    records: list[dict[str, Any]] = []
    by_symbol: dict[str, Any] = {}
    for corpus in source["included"]:
        symbol = str(corpus["symbol"])
        periods = _month_periods(
            str(corpus["start_inclusive_utc"]),
            str(corpus["end_exclusive_utc"]),
        )
        if len(periods) != int(corpus["expected_months"]):
            raise ValueError(f"Configured month count drifted for {symbol}")
        symbol_records = []
        for period in periods:
            path = (
                root
                / "raw"
                / symbol
                / f"year={period.year:04d}"
                / f"month={period.month:02d}"
                / str(source["monthly_manifest_name"])
            )
            if not path.is_file():
                raise FileNotFoundError(path)
            payload = json.loads(path.read_text(encoding="utf-8"))
            expected_hours = calendar.monthrange(period.year, period.month)[1] * 24
            valid = (
                payload.get("symbol") == symbol
                and payload.get("month") == str(period)
                and bool(payload.get("complete"))
                and bool(payload.get("frozen"))
                and int(payload.get("expected_hour_files", -1)) == expected_hours
                and int(payload.get("observed_hour_files", -1)) == expected_hours
                and len(str(payload.get("files_sha256", ""))) == 64
            )
            if not valid:
                raise ValueError(f"Source month is not complete and frozen: {path}")
            expected_names = {
                f"{period.year:04d}{period.month:02d}{day:02d}{hour:02d}.json"
                for day in range(
                    1, calendar.monthrange(period.year, period.month)[1] + 1
                )
                for hour in range(24)
            }
            physical_names = {
                item.name
                for item in path.parent.iterdir()
                if item.is_file()
                and item.suffix.lower() == ".json"
                and len(item.stem) == 10
                and item.stem.isdigit()
            }
            if physical_names != expected_names:
                raise ValueError(
                    f"Physical hourly source set is incomplete: {path.parent}"
                )
            record = {
                "symbol": symbol,
                "role": str(corpus["role"]),
                "month": str(period),
                "path": path.relative_to(root).as_posix(),
                "bytes": int(path.stat().st_size),
                "manifest_sha256": sha256_file(path),
                "hour_files": expected_hours,
                "physical_hour_files_verified": True,
                "hour_file_set_sha256": str(payload["files_sha256"]),
            }
            symbol_records.append(record)
            records.append(record)
        by_symbol[symbol] = {
            "role": str(corpus["role"]),
            "months": len(symbol_records),
            "hours": int(sum(row["hour_files"] for row in symbol_records)),
            "start_inclusive_utc": str(corpus["start_inclusive_utc"]),
            "end_exclusive_utc": str(corpus["end_exclusive_utc"]),
            "manifest_set_sha256": canonical_json_sha256(symbol_records),
        }
    return {
        "schema_version": "xauusd_step_2b_source_corpus_manifest_v1",
        "storage_root": str(root),
        "records": records,
        "record_count": len(records),
        "by_symbol": by_symbol,
        "excluded_from_v1_features": list(source["excluded_from_v1_features"]),
        "record_set_sha256": canonical_json_sha256(records),
        "physical_hour_file_sets_verified": True,
        "raw_files_opened": False,
        "economic_outcomes_opened": False,
    }


def build_split_plan(
    canonical_path: Path,
    config: Mapping[str, Any],
    forbidden: Iterable[str],
) -> dict[str, Any]:
    columns = [
        "candidate_id",
        "family_id",
        "decision_time",
        "planned_observation_end",
        "structural_episode_id",
    ]
    frame = load_parquet_columns(canonical_path, columns, forbidden)
    if len(frame) != int(config["population_contract"]["primary_fit_candidate_rows"]):
        raise ValueError("Canonical row count changed before Step 2B")
    if frame["candidate_id"].duplicated().any():
        raise ValueError("Canonical candidate identity is duplicated")
    frame["decision_time"] = pd.to_datetime(frame["decision_time"], utc=True)
    frame["planned_observation_end"] = pd.to_datetime(
        frame["planned_observation_end"], utc=True
    )
    split = config["split_contract"]
    data_start = pd.Timestamp(split["data_start_inclusive_utc"])
    cutoff = pd.Timestamp(split["development_cutoff_exclusive_utc"])
    if (frame["decision_time"] < data_start).any() or (
        frame["decision_time"] >= cutoff
    ).any():
        raise ValueError("Canonical decisions escaped the frozen development interval")

    folds = []
    for era in split["outer_eras"]:
        test_start = pd.Timestamp(era["test_start"])
        test_end = pd.Timestamp(era["test_end_exclusive"])
        calibration_start = test_start - pd.DateOffset(
            months=int(split["calibration_months"])
        )
        raw_fit = frame["decision_time"] < calibration_start
        fit = raw_fit & (frame["planned_observation_end"] < calibration_start)
        raw_calibration = frame["decision_time"].between(
            calibration_start, test_start, inclusive="left"
        )
        calibration = raw_calibration & (frame["planned_observation_end"] < test_start)
        test = frame["decision_time"].between(test_start, test_end, inclusive="left")
        observed = {
            "fit": int(fit.sum()),
            "calibration": int(calibration.sum()),
            "test": int(test.sum()),
        }
        expected = {
            "fit": int(era["expected_outcome_blind_fit_rows"]),
            "calibration": int(era["expected_outcome_blind_calibration_rows"]),
            "test": int(era["expected_test_candidate_rows"]),
        }
        if observed != expected:
            raise ValueError(
                f"Outcome-blind split count changed for {era['fold_id']}: "
                f"{observed} != {expected}"
            )

        def family_counts(mask: pd.Series) -> dict[str, int]:
            values = frame.loc[mask, "family_id"].value_counts().sort_index()
            return {str(key): int(value) for key, value in values.items()}

        folds.append(
            {
                "fold_id": str(era["fold_id"]),
                "calibration_start": calibration_start,
                "test_start": test_start,
                "test_end_exclusive": test_end,
                "outcome_blind_counts": observed,
                "planned_interval_purged_from_fit": int((raw_fit & ~fit).sum()),
                "planned_interval_purged_from_calibration": int(
                    (raw_calibration & ~calibration).sum()
                ),
                "fit_by_family": family_counts(fit),
                "calibration_by_family": family_counts(calibration),
                "test_by_family": family_counts(test),
                "actual_label_end_purge_status": "DEFERRED_UNTIL_STEP_3_LABELS",
            }
        )
    return {
        "schema_version": "xauusd_step_2b_outcome_blind_split_plan_v1",
        "mode": str(split["mode"]),
        "candidate_rows": int(len(frame)),
        "structural_episodes": int(frame["structural_episode_id"].nunique()),
        "data_start_inclusive_utc": data_start,
        "development_cutoff_exclusive_utc": cutoff,
        "folds": folds,
        "planned_interval_purge_applied": True,
        "actual_label_interval_purge_required_in_step_3": True,
        "random_or_shuffled_split_authorized": False,
        "economic_outcomes_opened": False,
    }


def compute_journey_weights(actions: pd.DataFrame) -> pd.DataFrame:
    required = {
        "action_row_id",
        "candidate_id",
        "population",
        "source_id",
        "structural_episode_id",
        "candidate_action_count",
    }
    missing = sorted(required - set(actions.columns))
    if missing:
        raise ValueError(f"Journey weighting is missing columns: {missing}")
    result = actions.copy()
    observed_actions = result.groupby("candidate_id", sort=False).size()
    declared_actions = result.groupby("candidate_id", sort=False)[
        "candidate_action_count"
    ].first()
    if not observed_actions.equals(declared_actions.astype("int64")):
        raise ValueError("Journey candidate action multiplicity changed")
    directions = result.groupby("structural_episode_id", sort=False)[
        "candidate_id"
    ].nunique()
    result["candidate_directions_per_structural_event"] = result[
        "structural_episode_id"
    ].map(directions)
    result["journey_diagnostic_weight"] = 1.0 / (
        result["candidate_action_count"].astype(float)
        * result["candidate_directions_per_structural_event"].astype(float)
    )
    event_weights = result.groupby("structural_episode_id", sort=False)[
        "journey_diagnostic_weight"
    ].sum()
    if not np.allclose(event_weights.to_numpy(), 1.0, rtol=0.0, atol=1e-12):
        raise ValueError("Journey diagnostic weights do not sum to one per event")
    return result[
        [
            "action_row_id",
            "candidate_id",
            "population",
            "source_id",
            "structural_episode_id",
            "candidate_action_count",
            "candidate_directions_per_structural_event",
            "journey_diagnostic_weight",
        ]
    ].copy()


def build_journey_weight_plan(
    journey_path: Path,
    config: Mapping[str, Any],
    forbidden: Iterable[str],
) -> tuple[pd.DataFrame, dict[str, Any]]:
    columns = [
        "action_row_id",
        "candidate_id",
        "population",
        "source_id",
        "structural_episode_id",
        "candidate_action_count",
    ]
    actions = load_parquet_columns(journey_path, columns, forbidden)
    weights = compute_journey_weights(actions)
    population = config["population_contract"]
    if len(weights) != int(population["journey_action_rows"]):
        raise ValueError("Journey action count changed before Step 2B")
    if weights["candidate_id"].nunique() != int(
        population["journey_candidate_directions"]
    ):
        raise ValueError("Journey candidate-direction count changed")
    events = int(weights["structural_episode_id"].nunique())
    if events != int(population["journey_structural_events"]):
        raise ValueError("Journey structural event count changed")
    weight_sum = float(weights["journey_diagnostic_weight"].sum())
    expected_sum = float(config["weight_contract"]["journey_diagnostic_weight_sum"])
    if not math.isclose(weight_sum, expected_sum, rel_tol=0.0, abs_tol=1e-9):
        raise ValueError("Journey diagnostic weight sum changed")
    report = {
        "action_rows": int(len(weights)),
        "candidate_directions": int(weights["candidate_id"].nunique()),
        "structural_events": events,
        "diagnostic_weight_sum": weight_sum,
        "minimum_weight": float(weights["journey_diagnostic_weight"].min()),
        "maximum_weight": float(weights["journey_diagnostic_weight"].max()),
        "one_weight_unit_per_structural_event": True,
        "economic_outcomes_opened": False,
    }
    return weights, report


def _file_record(path: Path, base: Path) -> dict[str, Any]:
    return {
        "path": path.resolve().relative_to(base.resolve()).as_posix(),
        "bytes": int(path.stat().st_size),
        "sha256": sha256_file(path),
    }


def build_definition_lock(
    repo_root: Path,
    package_root: Path,
    config: Mapping[str, Any],
    source_manifest_path: Path,
    split_plan_path: Path,
    journey_weights_path: Path,
    bound_hashes: Mapping[str, str],
    feature_audit: Mapping[str, Any],
) -> dict[str, Any]:
    package_records = [
        _file_record(package_root / relative, repo_root) for relative in PACKAGE_FILES
    ]
    payload: dict[str, Any] = {
        "schema_version": "xauusd_step_2b_dataset_feature_definition_lock_v1",
        "campaign_id": str(config["campaign_id"]),
        "stage": str(config["stage"]),
        "created_utc": str(config["created_utc"]),
        "package_files": package_records,
        "bound_inputs": dict(bound_hashes),
        "source_corpus_manifest": _file_record(source_manifest_path, repo_root),
        "outcome_blind_split_plan": _file_record(split_plan_path, repo_root),
        "journey_weight_plan": _file_record(journey_weights_path, repo_root),
        "feature_audit": dict(feature_audit),
        "label_contract_sha256": canonical_json_sha256(config["label_contract"]),
        "deduplication_contract_sha256": canonical_json_sha256(
            config["deduplication_contract"]
        ),
        "weight_contract_sha256": canonical_json_sha256(config["weight_contract"]),
        "split_contract_sha256": canonical_json_sha256(config["split_contract"]),
        "economic_outcomes_opened": False,
        "features_materialized": False,
        "model_fitted": False,
        "threshold_fitted": False,
        "runtime_changed": False,
        "next_stage": str(config["next_stage"]["name"]),
    }
    payload["definition_contract_sha256"] = canonical_json_sha256(payload)
    return payload


def render_result(result: Mapping[str, Any]) -> str:
    return "\n".join(
        [
            "# Causal Candidate Quality ML V1 - Step 2B Result",
            "",
            f"Decision: `{result['decision']}`",
            "",
            "The dataset, label, feature, deduplication, weighting, and split definitions are now locked before economic outcomes.",
            "",
            f"- Canonical primary candidates: `{result['canonical_candidates']}`",
            f"- Journey action rows retained: `{result['journey_action_rows']}`",
            f"- Journey candidate-directions retained: `{result['journey_candidate_directions']}`",
            f"- Journey structural events: `{result['journey_structural_events']}`",
            f"- Ordered raw features: `{result['ordered_feature_count']}`",
            f"- Frozen Dukascopy monthly manifests: `{result['source_monthly_manifests']}`",
            f"- Definition contract SHA-256: `{result['definition_contract_sha256']}`",
            "",
            "Primary fitting remains canonical. Journey failures are retained as a separately weighted diagnostic library; rejection is never a loss label.",
            "",
            f"Next authorized work: `{result['next_authorized_work']}`.",
            "",
        ]
    )


def build_artifact_manifest(
    repo_root: Path, output_paths: Mapping[str, Path], result: Mapping[str, Any]
) -> dict[str, Any]:
    artifacts = {}
    for name, path in output_paths.items():
        if name == "artifact_manifest":
            continue
        artifacts[name] = _file_record(path, repo_root)
    return {
        "schema_version": "xauusd_step_2b_artifact_manifest_v1",
        "decision": result["decision"],
        "definition_contract_sha256": result["definition_contract_sha256"],
        "artifacts": artifacts,
        "economic_outcomes_opened": False,
        "model_fitted": False,
        "runtime_changed": False,
    }


def run_step_2b(repo_root: Path, package_root: Path) -> dict[str, Any]:
    config_path = package_root / "config" / "step_2b_dataset_feature_contract_v1.json"
    config = json.loads(config_path.read_text(encoding="utf-8"))
    validate_closed_controls(config)
    forbidden = config["controls"]["forbidden_read_columns"]
    bound_paths: dict[str, Path] = {}
    bound_hashes: dict[str, str] = {}
    for label, spec in config["bound_inputs"].items():
        path = verify_bound_file(repo_root, spec, label)
        bound_paths[label] = path
        bound_hashes[label] = sha256_file(path)

    step_1 = json.loads(bound_paths["step_1_contract"].read_text(encoding="utf-8"))
    step_2a = json.loads(bound_paths["step_2a_result"].read_text(encoding="utf-8"))
    if step_2a["decision"] != "STEP_2A_METADATA_REPAIR_COMPLETE":
        raise ValueError("Step 2A is not complete")
    if bool(step_2a["economic_outcomes_opened"]) or bool(step_2a["model_fitted"]):
        raise ValueError("Step 2A violated the outcome-blind boundary")
    feature_audit = validate_feature_contract(config, step_1)

    source_manifest = build_source_corpus_manifest(config)
    split_plan = build_split_plan(bound_paths["canonical_registry"], config, forbidden)
    journey_weights, journey_report = build_journey_weight_plan(
        bound_paths["journey_action_registry"], config, forbidden
    )

    output = package_root / config["outputs"]["directory"]
    output.mkdir(parents=True, exist_ok=True)
    output_paths = {
        name: output / filename
        for name, filename in config["outputs"].items()
        if name != "directory"
    }
    write_json(output_paths["source_corpus_manifest"], source_manifest)
    write_json(output_paths["split_plan"], split_plan)
    journey_weights.to_parquet(output_paths["journey_weight_plan"], index=False)

    lock = build_definition_lock(
        repo_root,
        package_root,
        config,
        output_paths["source_corpus_manifest"],
        output_paths["split_plan"],
        output_paths["journey_weight_plan"],
        bound_hashes,
        feature_audit,
    )
    lock_path = output_paths["contract_lock"]
    if lock_path.is_file():
        existing = json.loads(lock_path.read_text(encoding="utf-8"))
        if existing != lock:
            raise ValueError("Existing Step 2B lock does not match current definitions")
    else:
        write_json(lock_path, lock)
    if json.loads(lock_path.read_text(encoding="utf-8")) != lock:
        raise ValueError("Step 2B lock failed its post-write verification")

    result = {
        "schema_version": "xauusd_causal_candidate_quality_step_2b_result_v1",
        "stage": str(config["stage"]),
        "created_utc": str(config["created_utc"]),
        "decision": "STEP_2B_DATASET_FEATURE_CONTRACT_LOCKED",
        "lock_status": "VERIFIED",
        "definition_contract_sha256": str(lock["definition_contract_sha256"]),
        "canonical_candidates": int(step_2a["canonical_candidates"]),
        "journey_action_rows": int(journey_report["action_rows"]),
        "journey_candidate_directions": int(journey_report["candidate_directions"]),
        "journey_structural_events": int(journey_report["structural_events"]),
        "journey_diagnostic_weight_sum": float(journey_report["diagnostic_weight_sum"]),
        "ordered_feature_count": int(feature_audit["ordered_feature_count"]),
        "source_monthly_manifests": int(source_manifest["record_count"]),
        "source_manifest_sha256": str(source_manifest["record_set_sha256"]),
        "outer_folds": int(len(split_plan["folds"])),
        "primary_fit_population": str(
            config["population_contract"]["primary_fit_population"]
        ),
        "research_failure_library_retained": True,
        "research_failure_library_enters_primary_fit": False,
        "rejection_is_loss": False,
        "economic_outcomes_opened": False,
        "labels_built": False,
        "features_materialized": False,
        "model_fitted": False,
        "threshold_fitted": False,
        "portfolio_simulated": False,
        "runtime_changed": False,
        "ml_execution_authorized": False,
        "next_authorized_work": str(config["next_stage"]["name"]),
    }
    write_json(output_paths["result_json"], result)
    output_paths["result_markdown"].write_text(render_result(result), encoding="utf-8")
    artifact_manifest = build_artifact_manifest(repo_root, output_paths, result)
    write_json(output_paths["artifact_manifest"], artifact_manifest)
    return result
