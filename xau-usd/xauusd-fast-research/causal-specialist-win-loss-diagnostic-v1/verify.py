from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path


PACKAGE = Path(__file__).resolve().parent
REPO = PACKAGE.parents[2]
sys.path.insert(0, str(PACKAGE / "src"))
sys.path.insert(0, str(PACKAGE.parent / "causal-candidate-quality-ml-v1" / "src"))

from diagnostic import load_json, run_diagnostic  # noqa: E402
from step_3_common import (  # noqa: E402
    sha256_file,
    stable_parquet,
    verify_bound_file,
    write_json,
)


def main() -> None:
    config_path = PACKAGE / "config" / "specialist_win_loss_v1.json"
    config = load_json(config_path)
    outputs = config["outputs"]
    output_dir = PACKAGE / outputs["directory"]
    lock_path = output_dir / outputs["contract_lock"]
    lock = load_json(lock_path)
    if lock["definition"]["config_sha256"] != sha256_file(config_path):
        raise ValueError("Diagnostic config differs from lock")
    for relative, expected in lock["definition"]["implementation_sha256"].items():
        if sha256_file((PACKAGE / relative).resolve()) != expected:
            raise ValueError(f"Locked implementation differs: {relative}")
    for name, spec in config["bound_inputs"].items():
        verify_bound_file(REPO, spec, name)

    manifest_path = output_dir / outputs["artifact_manifest"]
    manifest = load_json(manifest_path)
    for name, artifact in manifest["artifacts"].items():
        path = REPO / artifact["path"]
        if not path.is_file():
            raise FileNotFoundError(path)
        if path.stat().st_size != int(artifact["bytes"]):
            raise ValueError(f"Artifact size mismatch: {name}")
        if sha256_file(path) != artifact["sha256"]:
            raise ValueError(f"Artifact hash mismatch: {name}")

    result = load_json(output_dir / outputs["result_json"])
    if result["runtime_changed"] or result["ml_authorized"]:
        raise ValueError("Diagnostic crossed a runtime authority boundary")
    if result["model_trained"] or result["threshold_fitted"]:
        raise ValueError("Diagnostic unexpectedly trained or fitted a policy")

    with tempfile.TemporaryDirectory() as directory:
        replay_dir = Path(directory)
        replay = run_diagnostic(
            REPO,
            PACKAGE,
            config_path,
            replay_dir,
            verify_bound_file=verify_bound_file,
            stable_parquet=stable_parquet,
            write_json=write_json,
        )
        if replay != result:
            raise ValueError("Diagnostic result does not reproduce")
        for name, artifact in manifest["artifacts"].items():
            replay_path = replay_dir / name
            if not replay_path.is_file():
                raise FileNotFoundError(replay_path)
            if sha256_file(replay_path) != artifact["sha256"]:
                raise ValueError(f"Replayed artifact hash mismatch: {name}")

    print(
        json.dumps(
            {
                "decision": "SPECIALIST_WIN_LOSS_V1_VERIFIED",
                "evidence_decision": result["decision"],
                "artifacts_verified": len(manifest["artifacts"]),
                "families_tested": result["families_tested"],
                "features_tested": result["features_tested"],
                "matched_pairs": result["matched_pairs"],
                "stable_leads": result["stable_leads"],
                "near_leads": result["near_leads"],
                "runtime_changed": False,
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
