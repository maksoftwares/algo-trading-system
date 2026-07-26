from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from policy import canonical_json_sha256, comparison, resolve_inputs, sha256_file


ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parents[2]
CONFIG_PATH = ROOT / "config" / "profit_policy_v12.json"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def close(left: Any, right: Any) -> bool:
    if left is None or right is None:
        return left is right
    return bool(np.isclose(float(left), float(right), rtol=1e-10, atol=1e-10))


def verify_metric_group(
    actual: dict[str, Any],
    expected: dict[str, Any],
    name: str,
) -> None:
    if set(actual) != set(expected):
        raise ValueError(f"{name} metric keys differ")
    for key in actual:
        if isinstance(actual[key], (int, float)) or actual[key] is None:
            if not close(actual[key], expected[key]):
                raise ValueError(f"{name}.{key} changed")
        elif actual[key] != expected[key]:
            raise ValueError(f"{name}.{key} changed")


def main() -> int:
    config = load_json(CONFIG_PATH)
    output = ROOT / str(config["outputs"]["directory"])
    lock = load_json(output / str(config["outputs"]["contract_lock"]))
    result = load_json(output / str(config["outputs"]["result_json"]))
    manifest = load_json(output / str(config["outputs"]["manifest"]))

    if sha256_file(CONFIG_PATH) != str(lock["config_sha256"]):
        raise ValueError("Config hash does not match contract lock")
    if canonical_json_sha256(config["policy"]) != str(lock["policy_sha256"]):
        raise ValueError("Policy hash does not match contract lock")
    resolve_inputs(REPO_ROOT, config)
    for name, spec in manifest["inputs"].items():
        if sha256_file(REPO_ROOT / str(spec["path"])) != str(spec["sha256"]):
            raise ValueError(f"Manifest input changed: {name}")
    for name, spec in manifest["artifacts"].items():
        path = REPO_ROOT / str(spec["path"])
        if not path.is_file():
            raise FileNotFoundError(path)
        if sha256_file(path) != str(spec["sha256"]):
            raise ValueError(f"Manifest artifact changed: {name}")

    predictions = pd.read_parquet(output / str(config["outputs"]["predictions"]))
    if len(predictions) != int(result["out_of_time_rows"]):
        raise ValueError("Prediction row count changed")
    if predictions["candidate_id"].duplicated().any():
        raise ValueError("Predictions contain duplicate candidates")
    if predictions["selected"].isna().any():
        raise ValueError("Predictions contain missing decisions")
    recomputed = comparison(predictions)
    verify_metric_group(
        recomputed["baseline"], result["pooled"]["baseline"], "baseline"
    )
    verify_metric_group(
        recomputed["selected"], result["pooled"]["selected"], "selected"
    )
    for key in (
        "selected_weight_coverage",
        "selected_profit_delta_r",
        "selected_profit_delta_usd",
        "selected_mean_lift_r",
        "drawdown_ratio_to_baseline",
    ):
        if not close(recomputed[key], result["pooled"][key]):
            raise ValueError(f"Pooled comparison changed: {key}")

    authorization = result["authorization"]
    forbidden = (
        "python_serving_authorized",
        "ml_shadow_authorized",
        "ea_consumption_authorized",
        "demo_authorized",
        "live_authorized",
        "broker_action_authorized",
        "runtime_change_authorized",
    )
    if any(bool(authorization[key]) for key in forbidden):
        raise ValueError("A runtime or execution permission was enabled")
    if result["runtime_changed"] or result["ml_shadow_or_execution_activated"]:
        raise ValueError("Result claims a forbidden runtime change")
    if result["final_research_policy"]["runtime_authorized"]:
        raise ValueError("Final research policy is runtime authorized")

    payload = {
        "schema_version": "xauusd_profit_policy_v12_verification",
        "status": "PROFIT_POLICY_V12_VERIFICATION_PASS",
        "definition_contract_sha256": lock["definition_contract_sha256"],
        "artifact_count": int(len(manifest["artifacts"])),
        "prediction_rows": int(len(predictions)),
        "selected_rows": int(predictions["selected"].astype(bool).sum()),
        "runtime_authorized": False,
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
