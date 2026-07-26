from __future__ import annotations

import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from run_experiment import acceptance_checks, verify_lock
from src.loss_only import (
    canonical_json_sha256,
    fit_loss_model,
    loss_similarity,
    loss_veto_metrics,
    partition_for,
    prepare_dataset,
    resolve_inputs,
    sha256_file,
    weekly_block_bootstrap,
    weighted_quantile,
)


ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parents[2]
CONFIG_PATH = ROOT / "config" / "loss_signature_one_class_v1.json"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def close(left: object, right: object, name: str) -> None:
    if left is None or right is None:
        if left is not right:
            raise ValueError(f"Verification mismatch for {name}")
        return
    if not np.isclose(float(left), float(right), rtol=1e-11, atol=1e-11):
        raise ValueError(f"Verification mismatch for {name}: {left} != {right}")


def main() -> int:
    config = load_json(CONFIG_PATH)
    output = ROOT / str(config["outputs"]["directory"])
    lock = load_json(output / str(config["outputs"]["contract_lock"]))
    verify_lock(config, lock)
    manifest = load_json(output / str(config["outputs"]["manifest"]))
    if manifest["definition_contract_sha256"] != lock["definition_contract_sha256"]:
        raise ValueError("Manifest references a different definition contract")
    for name, spec in manifest["inputs"].items():
        if sha256_file(REPO_ROOT / spec["path"]) != spec["sha256"]:
            raise ValueError(f"Input artifact changed: {name}")
    for spec in manifest["artifacts"].values():
        if sha256_file(REPO_ROOT / spec["path"]) != spec["sha256"]:
            raise ValueError(f"Output artifact changed: {spec['path']}")

    inputs = resolve_inputs(REPO_ROOT, config)
    v4_config = load_json(inputs["v4_dataset_config"])
    features = list(v4_config["model_features"])
    if canonical_json_sha256(features) != config["population"]["feature_sha256"]:
        raise ValueError("Verified feature surface changed")
    source = prepare_dataset(
        pd.read_parquet(inputs["v4_action_dataset"]), config, features
    ).set_index("candidate_id", drop=False)
    splits = pd.read_parquet(inputs["v4_split_assignments"])
    predictions = pd.read_parquet(
        output / str(config["outputs"]["predictions"])
    ).sort_values(["fold_id", "candidate_id"], kind="mergesort")
    fold_metrics = pd.read_parquet(output / str(config["outputs"]["fold_metrics"]))
    result = load_json(output / str(config["outputs"]["result_json"]))
    bootstrap = load_json(output / str(config["outputs"]["bootstrap"]))
    acceptance = load_json(output / str(config["outputs"]["acceptance"]))
    if predictions["candidate_id"].duplicated().any():
        raise ValueError("Out-of-time predictions contain duplicate candidates")

    model_spec = dict(config["training"]["model"])
    primary_quantile = float(config["training"]["primary_weighted_loss_quantile"])
    for fold_index, fold_id in enumerate(config["folds"]):
        stored = predictions.loc[predictions["fold_id"].eq(fold_id)].sort_values(
            "candidate_id", kind="mergesort"
        )
        replay_source = (
            source.loc[stored["candidate_id"]]
            .reset_index(drop=True)
            .sort_values("candidate_id", kind="mergesort")
        )
        model_path = (
            output
            / str(config["outputs"]["model_directory"])
            / f"LOSS_ONLY_ISOLATION_FOREST_{fold_id}.joblib"
        )
        payload = joblib.load(model_path)
        if int(payload["fit_winner_rows"]) != 0:
            raise ValueError("Serialized model claims winner rows in fitting")
        replay_scores = loss_similarity(payload["estimator"], replay_source, features)
        if not np.allclose(
            replay_scores,
            stored["loss_similarity"].to_numpy(dtype=float),
            rtol=1e-12,
            atol=1e-12,
        ):
            raise ValueError(f"Serialized score replay failed for {fold_id}")

        fit = partition_for(
            source.reset_index(drop=True), splits, fold_id=fold_id, partition="FIT"
        )
        losses = fit.loc[~fit["stress_net_r_positive"].astype(bool)].copy()
        if losses["stress_net_r_positive"].astype(bool).any():
            raise ValueError("Winner entered independent loss-only refit")
        local_spec = dict(model_spec)
        local_spec["random_state"] = int(local_spec["random_state"]) + fold_index
        refitted = fit_loss_model(losses, features=features, model_config=local_spec)
        refit_scores = loss_similarity(refitted, replay_source, features)
        if not np.allclose(
            refit_scores,
            stored["loss_similarity"].to_numpy(dtype=float),
            rtol=1e-12,
            atol=1e-12,
        ):
            raise ValueError(f"Independent loss-only refit failed for {fold_id}")
        threshold = weighted_quantile(
            loss_similarity(refitted, losses, features),
            losses["structural_weight"].to_numpy(dtype=float),
            primary_quantile,
        )
        close(threshold, payload["threshold"], f"{fold_id}.threshold")
        expected_flags = refit_scores >= threshold
        if not np.array_equal(expected_flags, stored["flagged"].to_numpy(dtype=bool)):
            raise ValueError(f"Veto flags failed replay for {fold_id}")

    ordered = predictions.sort_values(["signal_time", "candidate_id"], kind="mergesort")
    pooled = loss_veto_metrics(ordered, ordered["flagged"].to_numpy())
    for key in (
        "weighted_loss_auc",
        "weighted_loss_average_precision",
        "baseline_loss_rate",
        "flagged_loss_precision",
        "loss_precision_lift",
        "loss_recall",
        "winner_collateral_rate",
        "flagged_coverage",
        "retained_coverage",
        "retained_ev_lift_r",
    ):
        close(pooled[key], result["pooled"][key], f"pooled.{key}")
    replay_bootstrap = weekly_block_bootstrap(
        ordered,
        resamples=int(config["bootstrap"]["resamples"]),
        confidence=float(config["bootstrap"]["confidence"]),
        seed=int(config["bootstrap"]["seed"]),
    )
    if canonical_json_sha256(replay_bootstrap) != canonical_json_sha256(bootstrap):
        raise ValueError("Weekly bootstrap replay mismatch")
    checks = acceptance_checks(
        pooled, fold_metrics, replay_bootstrap, config["acceptance_gates"]
    )
    if checks != acceptance["checks"]:
        raise ValueError("Acceptance checks failed replay")
    if result["fit_winner_rows"] != 0:
        raise ValueError("Result claims winner rows in fitting")
    if result["runtime_changed"] or result["ml_shadow_or_execution_activated"]:
        raise ValueError("Result claims a forbidden runtime change")
    print("LOSS_ONLY_V1_VERIFICATION_PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
