from __future__ import annotations

import argparse
from pathlib import Path

import joblib
import pandas as pd

from src.expected_r import apply_thresholds, require_columns


ROOT = Path(__file__).resolve().parent
DEFAULT_MODEL = ROOT / "outputs" / "EXPECTED_R_V10_FINAL_RESEARCH_MODEL.joblib"


def score(input_path: Path, output_path: Path, model_path: Path) -> None:
    payload = joblib.load(model_path)
    if payload.get("runtime_authorized") is not False:
        raise ValueError("Expected a research-only model artifact")
    frame = pd.read_parquet(input_path)
    require_columns(
        frame,
        ["candidate_id", "family_id", *payload["numeric_features"]],
        "Offline candidate score input",
    )
    result = frame[["candidate_id", "family_id"]].copy()
    result["model_score"] = payload["model"].predict(frame)
    result = apply_thresholds(
        result,
        payload["family_thresholds"],
        float(payload["pooled_threshold"]),
    )
    result["ml_research_recommendation"] = result["selected"].map(
        {True: "RETAIN", False: "VETO"}
    )
    result["runtime_authorized"] = False
    result.to_parquet(output_path, index=False)


def main() -> int:
    parser = argparse.ArgumentParser(description="Offline Expected-R V10 scorer")
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--model", type=Path, default=DEFAULT_MODEL)
    args = parser.parse_args()
    score(args.input, args.output, args.model)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
