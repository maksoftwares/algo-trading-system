from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any

import joblib
import pandas as pd

ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parents[2]
ML_ROOT = REPO_ROOT / "xau-usd/xauusd-fast-research/causal-candidate-quality-ml-v1"
V10_ROOT = REPO_ROOT / "xau-usd/xauusd-fast-research/causal-canonical-expected-r-v10"
V60_ROOT = REPO_ROOT / "xau-usd/xauusd-fast-research/v60-canonical-demo-portfolio-v2"

CANONICAL_PATH = ML_ROOT / "outputs/step_3/STEP_3_CANONICAL_DATASET.parquet"
FEATURE_CONTRACT_PATH = ML_ROOT / "config/step_2b_dataset_feature_contract_v1.json"
V10_CONFIG_PATH = V10_ROOT / "config/canonical_expected_r_v10.json"
EXPECTED_R_PATH = V10_ROOT / "src/expected_r.py"
B123_REPORT_PATH = V60_ROOT / "reports/V60_ML_B123_EXPECTED_R_COMPARISON.json"

EXPECTED_SHA256 = {
    CANONICAL_PATH: "fc4771063013cf3633192715d2124c374cf37b44b1be9c1fddde7f67741fbc45",
    FEATURE_CONTRACT_PATH: "f1cafa6375db1597e9721397bb6c2f7e54b25ead9016df6fdc670a94584317de",
    V10_CONFIG_PATH: "3af418d65876277711b5a480c015275c8df70bfcd84dea467c7499bb2684ae97",
    EXPECTED_R_PATH: "2ea01130ab139fc6795909724ae375ad03cf69e3e17b09bd66b8905446a66f0a",
}
SOURCE_BLOCKS = [
    "B1_DETERMINISTIC_CANDIDATE_AND_REGIME",
    "B2_PLUS_XAU_MICROSTRUCTURE_AND_COST",
    "B3_PLUS_COMPLETED_CROSS_ASSET_STATE",
]
FIT_END_EXCLUSIVE = pd.Timestamp("2026-07-01T00:00:00Z")
VETO_QUANTILE = 0.05
OUTPUT = ROOT / "outputs"
MODEL_PATH = OUTPUT / "MACRO_EXPECTED_R_V14_FINAL_RESEARCH_MODEL.joblib"
MANIFEST_PATH = OUTPUT / "MACRO_EXPECTED_R_V14_FINAL_MODEL_MANIFEST.json"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def relative(path: Path) -> str:
    return path.resolve().relative_to(REPO_ROOT.resolve()).as_posix()


def verify_inputs() -> dict[str, str]:
    observed: dict[str, str] = {}
    for path, expected in EXPECTED_SHA256.items():
        actual = sha256_file(path)
        if actual != expected:
            raise ValueError(f"Input changed: {relative(path)}")
        observed[relative(path)] = actual
    if not B123_REPORT_PATH.is_file():
        raise FileNotFoundError(B123_REPORT_PATH)
    report = json.loads(B123_REPORT_PATH.read_text(encoding="utf-8"))
    if report["status"] != "HISTORICAL_DIAGNOSTIC_POSITIVE_LATEST_WINDOW_FAIL":
        raise ValueError("B123 comparison status changed")
    if report["deployment_eligible"] is not False:
        raise ValueError("B123 comparison unexpectedly authorizes deployment")
    observed[relative(B123_REPORT_PATH)] = sha256_file(B123_REPORT_PATH)
    return observed


def build() -> tuple[dict[str, Any], dict[str, Any]]:
    inputs = verify_inputs()
    sys.path.insert(0, str(V10_ROOT))
    from src import expected_r

    config = json.loads(V10_CONFIG_PATH.read_text(encoding="utf-8"))
    config["features"]["source_blocks"] = SOURCE_BLOCKS
    contract = json.loads(FEATURE_CONTRACT_PATH.read_text(encoding="utf-8"))
    _, numeric_features = expected_r.feature_surface(contract, config)
    dataset = pd.read_parquet(CANONICAL_PATH)
    population = expected_r.prepare_population(dataset, config, numeric_features)
    fit = population.loc[
        population["decision_time"].lt(FIT_END_EXCLUSIVE)
        & population["label_end_time"].lt(FIT_END_EXCLUSIVE)
    ].copy()
    if len(fit) < 2500:
        raise ValueError("Final B123 fit population is unexpectedly small")
    model = expected_r.PartialPoolingExpectedR.fit(
        fit,
        numeric_features=numeric_features,
        families=config["population"]["families"],
        alpha=300.0,
        interaction_scale=0.25,
        target_clip=(-3.0, 3.0),
    )
    fit_scores = model.predict(fit)
    threshold = expected_r.weighted_quantile(
        fit_scores,
        fit["structural_weight"],
        VETO_QUANTILE,
    )
    selected = fit_scores >= threshold
    selected_weight_fraction = float(
        fit.loc[selected, "structural_weight"].sum() / fit["structural_weight"].sum()
    )
    if selected_weight_fraction < 0.94:
        raise ValueError("Final B123 policy does not preserve enough fit weight")

    payload = {
        "schema_version": "xauusd_macro_expected_r_v14_final_research_model",
        "model": model,
        "numeric_features": numeric_features,
        "families": list(config["population"]["families"]),
        "pooled_threshold": float(threshold),
        "family_thresholds": {},
        "threshold_scope": "POOLED_GLOBAL_EXPECTED_R_SCORE",
        "veto_quantile": VETO_QUANTILE,
        "fit_rows": len(fit),
        "fit_weight": float(fit["structural_weight"].sum()),
        "fit_selected_rows": int(selected.sum()),
        "fit_selected_weight_fraction": selected_weight_fraction,
        "fit_decision_end_exclusive_utc": FIT_END_EXCLUSIVE.isoformat(),
        "historical_outcomes_exposed_before_design": True,
        "post_outcome_parameter_selection_disclosed": True,
        "research_only": True,
        "python_serving_authorized": False,
        "ml_shadow_authorized": False,
        "ea_consumption_authorized": False,
        "broker_action_authorized": False,
        "demo_authorized": False,
        "live_authorized": False,
    }
    manifest = {
        "schema_version": "xauusd_macro_expected_r_v14_final_model_manifest",
        "inputs": inputs,
        "source_blocks": SOURCE_BLOCKS,
        "model_settings": {
            "kind": "RIDGE_PARTIAL_POOLING_EXPECTED_R",
            "alpha": 300.0,
            "family_interaction_scale": 0.25,
            "target_clip_r": [-3.0, 3.0],
            "threshold_scope": "POOLED_GLOBAL_EXPECTED_R_SCORE",
            "veto_quantile": VETO_QUANTILE,
        },
        "numeric_feature_count": len(numeric_features),
        "numeric_features": numeric_features,
        "fit_rows": len(fit),
        "fit_weight": float(fit["structural_weight"].sum()),
        "fit_selected_rows": int(selected.sum()),
        "fit_selected_weight_fraction": selected_weight_fraction,
        "pooled_threshold": float(threshold),
        "fit_decision_end_exclusive_utc": FIT_END_EXCLUSIVE.isoformat(),
        "model_path": relative(MODEL_PATH),
        "limitations": [
            "Historical outcomes informed selection of this B123 design.",
            "The final fit score is in-sample and is not deployment evidence.",
            "Only untouched prospective comparison may authorize later use.",
            "The latest historical three-month window underperformed raw V60.",
        ],
        "authorization": {
            "offline_model_fit_authorized": True,
            "prospective_research_scoring_authorized": True,
            "python_serving_authorized": False,
            "ml_shadow_authorized": False,
            "ea_consumption_authorized": False,
            "broker_action_authorized": False,
            "demo_authorized": False,
            "live_authorized": False,
        },
    }
    return payload, manifest


def main() -> int:
    payload, manifest = build()
    OUTPUT.mkdir(parents=True, exist_ok=True)
    joblib.dump(payload, MODEL_PATH, compress=3)
    manifest["model_sha256"] = sha256_file(MODEL_PATH)
    MANIFEST_PATH.write_text(
        json.dumps(manifest, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(manifest, indent=2, sort_keys=True, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
