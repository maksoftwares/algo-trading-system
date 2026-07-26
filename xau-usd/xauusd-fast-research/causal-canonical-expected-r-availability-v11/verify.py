from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from policy import (
    apply_availability,
    canonical_json_sha256,
    resolve_inputs,
    sha256_file,
    weekly_bootstrap,
)
from run_evaluation import (
    acceptance_checks,
    build_metrics,
    verify_lock,
)


ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parents[2]
CONFIG_PATH = ROOT / "config" / "availability_v11.json"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def close(left: object, right: object, name: str) -> None:
    if left is None or right is None:
        if left is not right:
            raise ValueError(f"Verification mismatch for {name}")
        return
    if not np.isclose(float(left), float(right), rtol=1e-11, atol=1e-11):
        raise ValueError(f"Verification mismatch for {name}: {left} != {right}")


def compare_frame(actual: pd.DataFrame, stored: pd.DataFrame, key: str) -> None:
    left = actual.sort_values(key, kind="mergesort").reset_index(drop=True)
    right = stored.sort_values(key, kind="mergesort").reset_index(drop=True)
    if left.columns.tolist() != right.columns.tolist():
        raise ValueError(f"{key} metric columns changed")
    for column in left.columns:
        if column == key or left[column].dtype == bool:
            if left[column].tolist() != right[column].tolist():
                raise ValueError(f"{key}.{column} changed")
        elif pd.api.types.is_numeric_dtype(left[column]):
            if not np.allclose(
                left[column].to_numpy(dtype=float),
                right[column].to_numpy(dtype=float),
                equal_nan=True,
                rtol=1e-11,
                atol=1e-11,
            ):
                raise ValueError(f"{key}.{column} changed")
        elif left[column].tolist() != right[column].tolist():
            raise ValueError(f"{key}.{column} changed")


def main() -> int:
    config = load_json(CONFIG_PATH)
    output = ROOT / str(config["outputs"]["directory"])
    lock = load_json(output / str(config["outputs"]["contract_lock"]))
    verify_lock(config, lock)
    manifest = load_json(output / str(config["outputs"]["manifest"]))
    if manifest["definition_contract_sha256"] != lock["definition_contract_sha256"]:
        raise ValueError("Manifest references another definition contract")
    for spec in manifest["inputs"].values():
        if sha256_file(REPO_ROOT / spec["path"]) != spec["sha256"]:
            raise ValueError(f"Input changed: {spec['path']}")
    for spec in manifest["artifacts"].values():
        if sha256_file(REPO_ROOT / spec["path"]) != spec["sha256"]:
            raise ValueError(f"Artifact changed: {spec['path']}")

    inputs = resolve_inputs(REPO_ROOT, config)
    v10_predictions = pd.read_parquet(inputs["v10_predictions"])
    v10_predictions["decision_time"] = pd.to_datetime(
        v10_predictions["decision_time"], utc=True
    )
    v10_folds = pd.read_parquet(inputs["v10_fold_metrics"])
    replay = (
        apply_availability(
            v10_predictions,
            v10_folds,
            int(config["availability"]["minimum_fit_rows"]),
        )
        .sort_values(["decision_time", "candidate_id"], kind="mergesort")
        .reset_index(drop=True)
    )
    stored_predictions = (
        pd.read_parquet(output / str(config["outputs"]["predictions"]))
        .sort_values(["decision_time", "candidate_id"], kind="mergesort")
        .reset_index(drop=True)
    )
    for column in ("model_score", "threshold"):
        if not np.allclose(
            replay[column].to_numpy(dtype=float),
            stored_predictions[column].to_numpy(dtype=float),
            rtol=1e-12,
            atol=1e-12,
        ):
            raise ValueError(f"Prediction replay failed for {column}")
    for column in (
        "selected",
        "v10_selected",
        "model_available",
        "availability_action",
    ):
        if replay[column].tolist() != stored_predictions[column].tolist():
            raise ValueError(f"Prediction replay failed for {column}")
    if not np.array_equal(
        v10_predictions["selected"].to_numpy(dtype=bool),
        replay["v10_selected"].to_numpy(dtype=bool),
    ):
        raise ValueError("V10 selections were not preserved")

    pooled, folds, families = build_metrics(replay)
    fit_rows = v10_folds.set_index("fold_id")["fit_rows"].astype(int).to_dict()
    folds["fit_rows"] = folds["fold_id"].map(fit_rows).astype(int)
    stored_folds = pd.read_parquet(output / str(config["outputs"]["fold_metrics"]))
    stored_families = pd.read_parquet(output / str(config["outputs"]["family_metrics"]))
    compare_frame(folds, stored_folds, "fold_id")
    compare_frame(families, stored_families, "family_id")
    result = load_json(output / str(config["outputs"]["result_json"]))
    for section in ("baseline", "selected"):
        for name, value in pooled[section].items():
            close(value, result["pooled"][section][name], f"pooled.{section}.{name}")
    for name in (
        "weighted_score_auc",
        "selected_weight_coverage",
        "selected_mean_lift_r",
        "drawdown_ratio_to_baseline",
    ):
        close(pooled[name], result["pooled"][name], f"pooled.{name}")

    bootstrap = weekly_bootstrap(
        replay,
        resamples=int(config["bootstrap"]["resamples"]),
        confidence=float(config["bootstrap"]["confidence"]),
        seed=int(config["bootstrap"]["seed"]),
    )
    stored_bootstrap = load_json(output / str(config["outputs"]["bootstrap"]))
    if canonical_json_sha256(bootstrap) != canonical_json_sha256(stored_bootstrap):
        raise ValueError("Bootstrap replay failed")
    checks = acceptance_checks(
        pooled, folds, families, bootstrap, config["acceptance_gates"]
    )
    acceptance = load_json(output / str(config["outputs"]["acceptance"]))
    if checks != acceptance["checks"]:
        raise ValueError("Acceptance replay failed")
    final_policy = load_json(output / str(config["outputs"]["final_policy"]))
    v10_result = load_json(inputs["v10_result"])
    if final_policy["actual_final_fit_rows"] != int(
        v10_result["final_research_model"]["fit_rows"]
    ):
        raise ValueError("Final fit-row evidence changed")
    if not final_policy["model_available"]:
        raise ValueError("Final model unexpectedly unavailable")
    if final_policy["runtime_authorized"]:
        raise ValueError("Final policy claims runtime authority")
    if result["runtime_changed"] or result["ml_shadow_or_execution_activated"]:
        raise ValueError("Result claims a forbidden runtime change")
    print("EXPECTED_R_AVAILABILITY_V11_VERIFICATION_PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
