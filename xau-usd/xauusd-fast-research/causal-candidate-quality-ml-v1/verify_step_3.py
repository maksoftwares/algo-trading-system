from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


PACKAGE = Path(__file__).resolve().parent
REPO = PACKAGE.parents[2]
OUTPUT = PACKAGE / "outputs" / "step_3"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def main() -> None:
    manifest_path = OUTPUT / "STEP_3_ARTIFACT_MANIFEST.json"
    manifest = load_json(manifest_path)
    for name, record in manifest["artifacts"].items():
        path = REPO / str(record["path"])
        require(path.stat().st_size == int(record["bytes"]), f"Size changed: {name}")
        require(sha256(path) == str(record["sha256"]), f"Hash changed: {name}")

    contract = load_json(PACKAGE / "config/step_2b_dataset_feature_contract_v1.json")
    features = pd.read_parquet(OUTPUT / "STEP_3_CANONICAL_FEATURES.parquet")
    labels = pd.read_parquet(OUTPUT / "STEP_3_CANONICAL_LABELS.parquet")
    dataset = pd.read_parquet(OUTPUT / "STEP_3_CANONICAL_DATASET.parquet")
    journey = pd.read_parquet(OUTPUT / "STEP_3_JOURNEY_ACTION_LABELS.parquet")
    splits = pd.read_parquet(OUTPUT / "STEP_3_SPLIT_ASSIGNMENTS.parquet")

    expected_features = [
        name
        for block in contract["feature_contract"]["ordered_blocks"]
        for name in block["features"]
    ]
    metadata = {
        "candidate_id",
        "xau_feature_status",
        "crossasset_feature_status",
        "comex_feature_status",
    }
    require(
        [name for name in features.columns if name not in metadata]
        == expected_features,
        "Locked feature order changed",
    )
    require(
        all(name in dataset.columns for name in expected_features),
        "Canonical dataset is missing a locked feature",
    )
    require(
        not any(name.startswith("family_id_") for name in dataset.columns),
        "Canonical dataset contains suffixed family IDs",
    )
    for name, frame, identity, count in (
        ("features", features, "candidate_id", 3752),
        ("labels", labels, "candidate_id", 3752),
        ("dataset", dataset, "candidate_id", 3752),
        ("journey", journey, "action_row_id", 117534),
    ):
        require(len(frame) == count, f"{name} row count changed")
        require(frame[identity].nunique() == count, f"{name} identity changed")
    numeric = features.select_dtypes(include=[np.number]).to_numpy(dtype=float)
    require(not np.isinf(numeric).any(), "Feature matrix contains infinity")

    check = labels.merge(
        dataset[["candidate_id", "direction"]],
        on="candidate_id",
        validate="one_to_one",
    )
    resolved = check["label_status"].str.startswith("RESOLVED_")
    sign = np.where(check["direction"].eq("LONG"), 1.0, -1.0)
    gross = sign * (check["exit_price"] - check["entry_price"]) / check[
        "initial_risk_price"
    ]
    require(
        np.allclose(
            gross[resolved], check.loc[resolved, "gross_r"], rtol=1e-12, atol=1e-12
        ),
        "Gross R formula failed",
    )
    base_cost = (
        0.30 + check["holding_minutes"] / 1440.0 * 0.35
    ) / check["initial_risk_usd_0p01"]
    require(
        np.allclose(
            base_cost[resolved],
            check.loc[resolved, "base_cost_r"],
            rtol=1e-12,
            atol=1e-12,
        ),
        "Base cost formula failed",
    )
    require(
        np.allclose(
            check.loc[resolved, "stress_net_r"],
            check.loc[resolved, "gross_r"]
            - check.loc[resolved, "base_cost_r"]
            - 0.05,
            rtol=1e-12,
            atol=1e-12,
        ),
        "Stress R formula failed",
    )
    require(
        bool(
            (
                check.loc[resolved, "entry_time"]
                <= check.loc[resolved, "label_end_time"]
            ).all()
        ),
        "Label clocks are reversed",
    )
    require(
        not bool(
            (
                splits.groupby(["fold_id", "structural_episode_id"])["assignment"]
                .nunique()
                .gt(1)
            ).any()
        ),
        "Structural siblings cross a split",
    )

    quality = load_json(OUTPUT / "STEP_3_DATA_QUALITY_AUDIT.json")
    source = load_json(OUTPUT / "STEP_3_SOURCE_AUDIT.json")
    opened = source["opened_source_verification"]
    print(
        json.dumps(
            {
                "decision": "STEP_3_VERIFIED",
                "artifact_manifest_sha256": sha256(manifest_path),
                "manifest_artifacts_verified": len(manifest["artifacts"]),
                "canonical": quality["canonical"],
                "journey": quality["journey"],
                "xau_status_counts": quality["features"]["xau_status_counts"],
                "verified_xau_hours": opened["xauusd"]["verified_hour_files"],
                "verified_crossasset_hours": opened["dollaridxusd"][
                    "verified_hour_files"
                ]
                + opened["ustbondtrusd"]["verified_hour_files"],
                "verified_comex_days": opened["comex_gc"]["verified_daily_files"],
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
