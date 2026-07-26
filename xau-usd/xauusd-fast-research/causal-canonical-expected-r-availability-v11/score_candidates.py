from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

import joblib
import pandas as pd


ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parents[2]
V10_ROOT = ROOT.parent / "causal-canonical-expected-r-v10"
sys.path.insert(0, str(V10_ROOT))

from src.expected_r import apply_thresholds, require_columns  # noqa: E402


DEFAULT_POLICY = ROOT / "outputs" / "AVAILABILITY_V11_FINAL_RESEARCH_POLICY.json"


def score(input_path: Path, output_path: Path, policy_path: Path) -> None:
    policy = json.loads(policy_path.read_text(encoding="utf-8"))
    model_path = REPO_ROOT / str(policy["v10_model_path"])
    payload = joblib.load(model_path)
    frame = pd.read_parquet(input_path)
    require_columns(
        frame,
        ["candidate_id", "family_id", *payload["numeric_features"]],
        "V11 offline candidate score input",
    )
    result = frame[["candidate_id", "family_id"]].copy()
    if int(policy["actual_final_fit_rows"]) < int(policy["minimum_fit_rows"]):
        result["model_score"] = pd.NA
        result["threshold"] = pd.NA
        result["selected"] = True
        result["availability_action"] = "ML_ABSTAIN_RETAIN_ALL"
    else:
        result["model_score"] = payload["model"].predict(frame)
        result = apply_thresholds(
            result,
            payload["family_thresholds"],
            float(payload["pooled_threshold"]),
        )
        result["availability_action"] = "APPLY_FROZEN_V10_SELECTION"
    result["ml_research_recommendation"] = result["selected"].map(
        {True: "RETAIN", False: "VETO"}
    )
    result["runtime_authorized"] = False
    result.to_parquet(output_path, index=False)


def main() -> int:
    parser = argparse.ArgumentParser(description="Offline V11 expected-R scorer")
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--policy", type=Path, default=DEFAULT_POLICY)
    args = parser.parse_args()
    score(args.input, args.output, args.policy)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
