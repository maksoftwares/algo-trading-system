from __future__ import annotations

import json
import math
import sys
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd


PACKAGE = Path(__file__).resolve().parent
REPO = PACKAGE.parents[2]
sys.path.insert(0, str(PACKAGE / "src"))

from step_3_common import sha256_file  # noqa: E402
from step_4_bootstrap import primary_block_bootstrap  # noqa: E402
from step_4_model import eligibility_mask, feature_names_for_blocks  # noqa: E402


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def close(left: float, right: float) -> bool:
    return math.isclose(float(left), float(right), rel_tol=1e-12, abs_tol=1e-12)


def main() -> None:
    contract_path = PACKAGE / "config/step_4_model_evaluation_contract_v1.json"
    contract = load_json(contract_path)
    output = PACKAGE / str(contract["outputs"]["directory"])
    lock_path = output / str(contract["outputs"]["contract_lock"])
    lock = load_json(lock_path)
    require(
        lock["definition"]["config_sha256"] == sha256_file(contract_path),
        "Step 4 configuration changed after lock",
    )
    for relative, expected in lock["definition"]["implementation_sha256"].items():
        require(
            sha256_file(PACKAGE / relative) == expected,
            f"Locked implementation changed: {relative}",
        )
    for name, spec in contract["bound_inputs"].items():
        require(
            sha256_file(REPO / str(spec["path"])) == str(spec["sha256"]),
            f"Bound input changed: {name}",
        )

    manifest_path = output / str(contract["outputs"]["artifact_manifest"])
    manifest = load_json(manifest_path)
    for name, record in manifest["artifacts"].items():
        path = REPO / str(record["path"])
        require(path.stat().st_size == int(record["bytes"]), f"Size changed: {name}")
        require(sha256_file(path) == str(record["sha256"]), f"Hash changed: {name}")

    step2b = load_json(REPO / contract["bound_inputs"]["step_2b_contract"]["path"])
    dataset = pd.read_parquet(REPO / contract["bound_inputs"]["step_3_dataset"]["path"])
    splits = pd.read_parquet(REPO / contract["bound_inputs"]["step_3_splits"]["path"])
    predictions = pd.read_parquet(output / str(contract["outputs"]["fold_predictions"]))
    metrics = pd.read_parquet(output / str(contract["outputs"]["fold_metrics"]))
    thresholds = pd.read_parquet(output / str(contract["outputs"]["thresholds"]))
    pooled = load_json(output / str(contract["outputs"]["pooled_metrics"]))
    bootstrap = load_json(output / str(contract["outputs"]["bootstrap"]))
    acceptance = load_json(output / str(contract["outputs"]["acceptance"]))
    result = load_json(output / str(contract["outputs"]["result_json"]))

    model_specs = {
        str(spec["model_id"]): spec for spec in contract["models"]["specifications"]
    }
    fold_ids = list(contract["outer_evaluation"]["fold_ids"])
    require(
        len(metrics) == len(model_specs) * len(fold_ids), "Fold metric count changed"
    )
    require(
        len(thresholds)
        == len(model_specs)
        * len(fold_ids)
        * len(contract["threshold_policy"]["candidate_probability_thresholds"]),
        "Threshold audit count changed",
    )
    require(
        not predictions.duplicated(["model_id", "candidate_id"]).any(),
        "Out-of-time predictions are duplicated",
    )
    require(
        predictions["probability"].between(0.0, 1.0).all(),
        "Probability is outside [0,1]",
    )
    require(
        predictions["selected"].equals(
            predictions["probability"].ge(predictions["threshold"])
        ),
        "Selection does not match locked threshold",
    )

    split_columns = [
        "fold_id",
        "candidate_id",
        "assignment",
        "resolved_label",
        "dataset_eligible",
    ]
    joined = splits[split_columns].merge(
        dataset, on="candidate_id", validate="many_to_one"
    )
    for model_id, spec in model_specs.items():
        names = feature_names_for_blocks(step2b, spec["feature_blocks"])
        require(
            not any(name.startswith("gc_") for name in names), f"COMEX in {model_id}"
        )
        for fold_id in fold_ids:
            expected = joined.loc[
                joined["fold_id"].eq(fold_id)
                & joined["assignment"].eq("TEST")
                & joined["dataset_eligible"]
                & eligibility_mask(joined, str(spec["eligibility"])),
                "candidate_id",
            ]
            observed = predictions.loc[
                predictions["model_id"].eq(model_id)
                & predictions["fold_id"].eq(fold_id),
                "candidate_id",
            ]
            require(
                set(expected) == set(observed),
                f"Prediction population changed: {model_id}/{fold_id}",
            )

    for (model_id, fold_id), audit in thresholds.groupby(
        ["model_id", "fold_id"], sort=True
    ):
        eligible = audit.loc[audit["eligible"]].copy()
        best_utility = eligible["utility"].max()
        best = eligible.loc[eligible["utility"].eq(best_utility)]
        best_fraction = best["selected_fraction"].max()
        best = best.loc[best["selected_fraction"].eq(best_fraction)]
        expected_threshold = float(best["threshold"].min())
        observed_threshold = float(
            metrics.loc[
                metrics["model_id"].eq(model_id) & metrics["fold_id"].eq(fold_id),
                "threshold",
            ].iloc[0]
        )
        require(
            close(expected_threshold, observed_threshold),
            f"Threshold choice changed: {model_id}/{fold_id}",
        )

    primary_id = str(contract["models"]["primary_model_id"])
    primary = predictions.loc[predictions["model_id"].eq(primary_id)].copy()
    reproduced_bootstrap = primary_block_bootstrap(primary, contract)
    require(reproduced_bootstrap == bootstrap, "Primary bootstrap is not deterministic")
    require(
        result["decision"] == acceptance["decision"],
        "Result and acceptance decisions differ",
    )
    require(
        acceptance["passed_checks"] == sum(acceptance["checks"].values()),
        "Acceptance count changed",
    )
    require(not result["comex_features_used"], "COMEX was reported as used")
    require(not result["databento_api_accessed"], "Databento API was reported as used")
    require(result["journey_rows_used_for_fit"] == 0, "Journey rows entered fit")
    require(not result["runtime_changed"], "Runtime changed")

    primary_spec = model_specs[primary_id]
    primary_features = feature_names_for_blocks(step2b, primary_spec["feature_blocks"])
    for fold_id in fold_ids:
        artifact = joblib.load(output / "models" / f"{primary_id}_{fold_id}.joblib")
        require(
            artifact["contract_lock_sha256"] == sha256_file(lock_path),
            f"Model lock differs: {fold_id}",
        )
        require(
            artifact["feature_names"] == primary_features,
            f"Model features differ: {fold_id}",
        )
        require(
            not artifact["runtime_authorized"], f"Model runtime authorized: {fold_id}"
        )
        expected_rows = joined.loc[
            joined["fold_id"].eq(fold_id)
            & joined["assignment"].eq("TEST")
            & joined["dataset_eligible"]
            & eligibility_mask(joined, str(primary_spec["eligibility"])),
        ].copy()
        expected_rows = expected_rows.sort_values(
            ["decision_time", "candidate_id"], kind="stable"
        )
        reproduced = artifact["model"].predict_proba(
            expected_rows,
            float(contract["probability_calibration"]["clip_probability"]),
        )
        observed = predictions.loc[
            predictions["model_id"].eq(primary_id) & predictions["fold_id"].eq(fold_id)
        ].sort_values(["decision_time", "candidate_id"], kind="stable")
        require(
            np.allclose(reproduced, observed["probability"], rtol=0.0, atol=1e-15),
            f"Serialized model does not reproduce predictions: {fold_id}",
        )

    summary = {
        "decision": "STEP_4_VERIFIED",
        "evidence_decision": result["decision"],
        "contract_definition_sha256": lock["definition_contract_sha256"],
        "artifact_manifest_sha256": sha256_file(manifest_path),
        "artifacts_verified": len(manifest["artifacts"]),
        "models_verified": len(fold_ids),
        "primary_out_of_time_rows": len(primary),
        "primary_selected_rows": int(primary["selected"].sum()),
        "primary_weighted_roc_auc": pooled[primary_id]["probability"][
            "weighted_roc_auc"
        ],
        "passed_acceptance_checks": acceptance["passed_checks"],
        "required_acceptance_checks": acceptance["required_checks"],
        "comex_features_used": False,
        "databento_api_accessed": False,
        "runtime_changed": False,
    }
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
