from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd

from src.drift import (
    build_findings,
    canonical_json_sha256,
    categorical_drift_rows,
    decomposition_table,
    feature_drift_table,
    label_metrics_table,
    monthly_metrics_table,
    prepare_actions,
    replay_policy,
    resolve_inputs,
    score_bin_table,
    score_metrics_table,
    sha256_file,
    write_json,
)


ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parents[2]
CONFIG_PATH = ROOT / "config" / "drift_audit_v3.json"


def verify_lock(config: dict[str, Any], lock: dict[str, Any]) -> None:
    if sha256_file(CONFIG_PATH) != lock["config_sha256"]:
        raise ValueError("Drift config changed after contract lock")
    if sha256_file(ROOT / "PREREGISTRATION.md") != lock["preregistration_sha256"]:
        raise ValueError("Drift preregistration changed after contract lock")
    for name, record in lock["implementation"].items():
        path = REPO_ROOT / record["path"]
        if sha256_file(path) != record["sha256"]:
            raise ValueError(f"Locked implementation changed: {name}")
    expected = canonical_json_sha256(
        {
            "schema_version": config["schema_version"],
            "inputs": lock["input_sha256"],
            "feature_sha256": lock["model_feature_sha256"],
            "periods": config["periods"],
            "sessions_utc": config["sessions_utc"],
            "numeric_drift": config["numeric_drift"],
            "categorical_drift": config["categorical_drift"],
            "failure_rules": config["failure_rules"],
            "authorization": config["authorization"],
            "implementation": lock["implementation"],
            "versions": lock["versions"],
        }
    )
    if expected != lock["definition_contract_sha256"]:
        raise ValueError("Drift definition contract is inconsistent")


def load_policies(
    policies: pd.DataFrame, config: dict[str, Any]
) -> dict[str, dict[str, Any]]:
    chosen = policies.loc[
        policies["fold_id"].eq(config["target_fold"]) & policies["chosen"]
    ]
    result: dict[str, dict[str, Any]] = {}
    for lane in config["expected"]["lanes"]:
        rows = chosen.loc[chosen["model_lane"].eq(lane)]
        if len(rows) != 1:
            raise ValueError(f"Expected one F2026 policy for {lane}")
        row = rows.iloc[0]
        result[lane] = {
            "model_id": str(row["model_id"]),
            "score_threshold": float(row["score_threshold"]),
            "calibration_gate_pass": bool(row["calibration_gate_pass"]),
            "diagnostic_fallback": bool(row["diagnostic_fallback"]),
        }
    return result


def model_record(
    manifest: dict[str, Any], lane: str, policy: dict[str, Any]
) -> dict[str, Any]:
    name = f"{lane}_F2026_{policy['model_id']}.joblib"
    records = {
        Path(record["path"]).name: record for record in manifest["artifacts"]["models"]
    }
    if name not in records:
        raise ValueError(f"Action V3 manifest lacks model {name}")
    return records[name]


def verify_current_replay(
    scored: pd.DataFrame,
    stored_predictions: pd.DataFrame,
    lane: str,
    config: dict[str, Any],
) -> None:
    actual = scored.loc[scored["period"].eq("CURRENT")].sort_values(
        "candidate_id", kind="mergesort"
    )
    stored = stored_predictions.loc[
        stored_predictions["fold_id"].eq(config["target_fold"])
        & stored_predictions["model_lane"].eq(lane)
    ].sort_values("candidate_id", kind="mergesort")
    if actual["candidate_id"].tolist() != stored["candidate_id"].tolist():
        raise ValueError(f"F2026 replay candidates changed for {lane}")
    if not np.allclose(
        actual["model_score"], stored["model_score"], rtol=1e-12, atol=1e-12
    ):
        raise ValueError(f"F2026 replay scores changed for {lane}")
    if actual["chosen_action_flag"].tolist() != stored["chosen_action"].tolist():
        raise ValueError(f"F2026 chosen actions changed for {lane}")
    if actual["selected"].tolist() != stored["selected"].tolist():
        raise ValueError(f"F2026 selected actions changed for {lane}")


def write_result_markdown(path: Path, findings: dict[str, Any]) -> None:
    lines = [
        "# Action V3 F2026 Drift Audit",
        "",
        f"Decision: `{findings['decision']}`",
        "",
        "| Lane | Diagnosis | Ref coverage | Current coverage | Ref AUC | Current AUC | Ref mean R | Current mean R |",
        "|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    for lane, value in findings["lanes"].items():
        score = value["score_and_outcome"]
        lines.append(
            "| {lane} | {diagnosis} | {ref_cov:.3f} | {cur_cov:.3f} | "
            "{ref_auc:.3f} | {cur_auc:.3f} | {ref_r:.4f} | {cur_r:.4f} |".format(
                lane=lane,
                diagnosis=value["diagnosis"],
                ref_cov=score["reference_selected_fraction"],
                cur_cov=score["current_selected_fraction"],
                ref_auc=score["reference_auc"],
                cur_auc=score["current_auc"],
                ref_r=score["reference_selected_mean_r"],
                cur_r=score["current_selected_mean_r"],
            )
        )
    lines.extend(
        [
            "",
            "This is an explanatory audit on exposed development history. It does not",
            "authorize model fitting, threshold changes, MT5 shadowing, demo, or live use.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    output = ROOT / config["outputs"]["directory"]
    lock_path = output / config["outputs"]["contract_lock"]
    if not lock_path.is_file():
        raise FileNotFoundError("Run lock_contract.py before the F2026 drift audit")
    lock = json.loads(lock_path.read_text(encoding="utf-8"))
    verify_lock(config, lock)
    inputs = resolve_inputs(REPO_ROOT, config)
    v3_config = json.loads(inputs["v3_dataset_config"].read_text(encoding="utf-8"))
    action_config = json.loads(inputs["action_v3_config"].read_text(encoding="utf-8"))
    action_manifest = json.loads(
        inputs["action_v3_manifest"].read_text(encoding="utf-8")
    )
    features = list(v3_config["model_features"])
    actions = prepare_actions(
        pd.read_parquet(inputs["v3_action_dataset"]),
        pd.read_parquet(inputs["v3_split_assignments"]),
        v3_config,
        action_config,
        config,
    )
    policies = load_policies(pd.read_parquet(inputs["action_v3_policies"]), config)
    stored_predictions = pd.read_parquet(inputs["action_v3_predictions"])

    scored_frames: list[pd.DataFrame] = []
    chosen_frames: list[pd.DataFrame] = []
    for lane in config["expected"]["lanes"]:
        policy = policies[lane]
        record = model_record(action_manifest, lane, policy)
        model_path = REPO_ROOT / record["path"]
        if sha256_file(model_path) != record["sha256"]:
            raise ValueError(f"Action V3 model hash changed: {model_path.name}")
        model = joblib.load(model_path)
        lane_actions = actions.loc[actions["model_lane"].eq(lane)].copy()
        scored, chosen = replay_policy(
            model, lane_actions, features, float(policy["score_threshold"])
        )
        scored["chosen_model_id"] = policy["model_id"]
        scored["score_threshold"] = policy["score_threshold"]
        chosen["chosen_model_id"] = policy["model_id"]
        chosen["score_threshold"] = policy["score_threshold"]
        verify_current_replay(scored, stored_predictions, lane, config)
        scored_frames.append(scored)
        chosen_frames.append(chosen)

    scored_all = pd.concat(scored_frames, ignore_index=True)
    chosen_all = pd.concat(chosen_frames, ignore_index=True)
    feature_metrics = feature_drift_table(actions, features, config)
    categorical_metrics = categorical_drift_rows(chosen_all, config)
    score_metrics = score_metrics_table(chosen_all, policies, config)
    score_bins = score_bin_table(chosen_all, config)
    monthly_metrics = monthly_metrics_table(chosen_all)
    label_metrics = label_metrics_table(actions, chosen_all, config)
    decomposition = decomposition_table(chosen_all, config)
    findings = build_findings(
        feature_metrics,
        categorical_metrics,
        score_metrics,
        decomposition,
        config,
    )
    findings["counts"] = {
        "source_action_rows": len(actions),
        "scored_action_rows": len(scored_all),
        "replayed_events": len(chosen_all),
        "selected_events": int(chosen_all["selected"].sum()),
        "feature_metrics": len(feature_metrics),
    }
    result = {
        "schema_version": config["schema_version"],
        "decision": findings["decision"],
        "diagnoses": {
            lane: {
                "diagnosis": value["diagnosis"],
                "v4_disposition": value["v4_disposition"],
                "flags": value["flags"],
            }
            for lane, value in findings["lanes"].items()
        },
        "runtime_changed": False,
        "authorization": config["authorization"],
    }

    output.mkdir(parents=True, exist_ok=True)
    paths = {
        "contract_lock": lock_path,
        "feature_metrics": output / config["outputs"]["feature_metrics"],
        "categorical_metrics": output / config["outputs"]["categorical_metrics"],
        "score_metrics": output / config["outputs"]["score_metrics"],
        "score_bins": output / config["outputs"]["score_bins"],
        "monthly_metrics": output / config["outputs"]["monthly_metrics"],
        "label_metrics": output / config["outputs"]["label_metrics"],
        "decomposition": output / config["outputs"]["decomposition"],
        "replayed_events": output / config["outputs"]["replayed_events"],
        "findings": output / config["outputs"]["findings"],
        "result_json": output / config["outputs"]["result_json"],
        "result_md": output / config["outputs"]["result_md"],
    }
    feature_metrics.to_parquet(paths["feature_metrics"], index=False)
    categorical_metrics.to_parquet(paths["categorical_metrics"], index=False)
    score_metrics.to_parquet(paths["score_metrics"], index=False)
    score_bins.to_parquet(paths["score_bins"], index=False)
    monthly_metrics.to_parquet(paths["monthly_metrics"], index=False)
    label_metrics.to_parquet(paths["label_metrics"], index=False)
    decomposition.to_parquet(paths["decomposition"], index=False)
    replay_columns = [
        "period",
        "model_lane",
        "candidate_id",
        "event_id",
        "structural_episode_id",
        "signal_time",
        "regime",
        "session_utc",
        "direction",
        "action_availability",
        "chosen_action",
        "stress_net_r",
        "stress_net_r_positive",
        "mfe_r",
        "mae_r",
        "exit_reason",
        "event_eval_weight",
        "model_score",
        "selected",
        "chosen_model_id",
        "score_threshold",
    ]
    chosen_all[replay_columns].sort_values(
        ["model_lane", "period", "candidate_id"], kind="mergesort"
    ).to_parquet(paths["replayed_events"], index=False)
    write_json(paths["findings"], findings)
    write_json(paths["result_json"], result)
    write_result_markdown(paths["result_md"], findings)

    artifacts = {
        name: {
            "path": str(path.relative_to(REPO_ROOT)).replace("\\", "/"),
            "sha256": sha256_file(path),
        }
        for name, path in paths.items()
    }
    manifest = {
        "schema_version": config["schema_version"],
        "decision": findings["decision"],
        "definition_contract_sha256": lock["definition_contract_sha256"],
        "inputs": {
            name: {
                "path": str(path.relative_to(REPO_ROOT)).replace("\\", "/"),
                "sha256": sha256_file(path),
            }
            for name, path in inputs.items()
        },
        "artifacts": artifacts,
        "counts": findings["counts"],
        "authorization": config["authorization"],
    }
    manifest_path = output / config["outputs"]["manifest"]
    write_json(manifest_path, manifest)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
