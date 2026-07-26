from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
CONFIG_PATH = ROOT / "config" / "causal_candidate_quality_ml_v1.json"
LOCK_INPUTS = (
    "README.md",
    "PREREGISTRATION.md",
    "config/causal_candidate_quality_ml_v1.json",
    "lock_contract.py",
    "tests/test_contract.py",
)
FORBIDDEN_STEP_1_OUTPUT_TERMS = (
    "dataset",
    "feature",
    "label",
    "model",
    "prediction",
    "result",
    "score",
    "trade",
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_config() -> dict[str, Any]:
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def build_payload() -> dict[str, Any]:
    config = load_config()
    output_dir = ROOT / config["outputs"]["directory"]
    lock_name = config["outputs"]["contract_lock"]
    if output_dir.is_dir():
        forbidden = [
            item.name
            for item in output_dir.iterdir()
            if item.is_file()
            and item.name != lock_name
            and any(term in item.name.lower() for term in FORBIDDEN_STEP_1_OUTPUT_TERMS)
        ]
        if forbidden:
            raise ValueError(
                "Refusing Step 1 lock after downstream outputs were opened: "
                + ", ".join(sorted(forbidden))
            )

    bound_files = config["baseline"]["bound_files"]
    baseline_hashes: dict[str, str] = {}
    for name, item in bound_files.items():
        path = (ROOT / item["path"]).resolve()
        observed = sha256(path)
        expected = str(item["sha256"])
        if observed != expected:
            raise ValueError(
                f"Frozen baseline hash mismatch for {name}: {observed} != {expected}"
            )
        baseline_hashes[name] = observed

    governance_hashes = {
        relative: sha256((ROOT / relative).resolve()) for relative in LOCK_INPUTS
    }
    combined = hashlib.sha256(
        json.dumps(
            {
                "baseline": baseline_hashes,
                "governance": governance_hashes,
            },
            sort_keys=True,
            separators=(",", ":"),
        ).encode("ascii")
    ).hexdigest()
    return {
        "schema_version": "xauusd_causal_candidate_quality_ml_lock_v1",
        "campaign_id": config["campaign_id"],
        "stage": config["stage"],
        "created_utc": config["created_utc"],
        "repository_base_commit": config["repository_base_commit"],
        "combined_sha256": combined,
        "baseline_files": baseline_hashes,
        "governance_files": governance_hashes,
        "registered_primary_pipelines_per_outer_fold": config["model_budget"][
            "registered_primary_pipelines_per_outer_fold"
        ],
        "registered_comex_pipelines_per_eligible_outer_fold": config[
            "model_budget"
        ]["registered_comex_pipelines_per_eligible_outer_fold"],
        "registered_total_architecture_feature_combinations": config[
            "model_budget"
        ]["registered_total_architecture_feature_combinations"],
        "economic_outcomes_opened_at_lock": False,
        "model_fitted_at_lock": False,
        "runtime_changed_at_lock": False,
        "next_stage": config["next_stage"]["name"],
    }


def lock_or_verify() -> tuple[str, dict[str, Any]]:
    config = load_config()
    output_dir = ROOT / config["outputs"]["directory"]
    lock_path = output_dir / config["outputs"]["contract_lock"]
    payload = build_payload()
    if lock_path.is_file():
        existing = json.loads(lock_path.read_text(encoding="utf-8"))
        if existing != payload:
            raise ValueError("Existing Step 1 lock does not match current contract")
        return "VERIFIED", payload
    output_dir.mkdir(parents=True, exist_ok=True)
    lock_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return "CREATED", payload


def main() -> int:
    status, payload = lock_or_verify()
    print(json.dumps({"status": status, **payload}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
