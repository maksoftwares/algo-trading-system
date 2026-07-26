from __future__ import annotations

import json
import sys
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
    if not lock_path.is_file():
        raise ValueError("Exploratory contract must be locked before analysis")
    lock = load_json(lock_path)
    if lock["definition"]["config_sha256"] != sha256_file(config_path):
        raise ValueError("Diagnostic config differs from its lock")
    for relative, expected in lock["definition"]["implementation_sha256"].items():
        if sha256_file((PACKAGE / relative).resolve()) != expected:
            raise ValueError(f"Locked diagnostic implementation differs: {relative}")
    result_path = output_dir / outputs["result_json"]
    if result_path.exists():
        raise ValueError("Diagnostic outputs already exist; refusing to overwrite")

    result = run_diagnostic(
        REPO,
        PACKAGE,
        config_path,
        output_dir,
        verify_bound_file=verify_bound_file,
        stable_parquet=stable_parquet,
        write_json=write_json,
    )
    artifacts = {}
    excluded = {outputs["contract_lock"], outputs["artifact_manifest"]}
    for path in sorted(output_dir.iterdir()):
        if path.is_file() and path.name not in excluded:
            artifacts[path.name] = {
                "path": path.relative_to(REPO).as_posix(),
                "bytes": path.stat().st_size,
                "sha256": sha256_file(path),
            }
    manifest = {
        "schema_version": "xauusd_causal_specialist_win_loss_manifest_v1",
        "decision": result["decision"],
        "contract_lock_sha256": sha256_file(lock_path),
        "runtime_changed": False,
        "artifacts": artifacts,
    }
    write_json(output_dir / outputs["artifact_manifest"], manifest)
    print(json.dumps(result, indent=2, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
