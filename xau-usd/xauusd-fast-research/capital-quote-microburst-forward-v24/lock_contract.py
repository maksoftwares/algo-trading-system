from __future__ import annotations

import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]
sys.path.insert(0, str(ROOT / "src"))

from microburst import (  # noqa: E402
    canonical_hash,
    discover_source_files,
    load_config,
    sha256_file,
    source_date,
    verify_manifest_files,
)


PACKAGE_FILES = (
    "README.md",
    "PREREGISTRATION.md",
    "requirements.txt",
    "config/capital_quote_microburst_forward_v24.json",
    "src/__init__.py",
    "src/microburst.py",
    "prepare_calibration_manifest.py",
    "lock_contract.py",
    "run_frequency_calibration.py",
    "run_forward_evaluation.py",
    "tests/test_microburst.py",
)


def main() -> int:
    config = load_config(ROOT)
    output = ROOT / config["outputs"]["directory"]
    lock_path = output / config["outputs"]["contract_lock"]
    if lock_path.exists():
        raise FileExistsError("V24 contract already exists")
    manifest_path = ROOT / config["source"]["calibration_manifest"]
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if canonical_hash(manifest, "manifest_sha256") != manifest["manifest_sha256"]:
        raise ValueError("V24 calibration manifest self-hash mismatch")
    verify_manifest_files(manifest, "calibration_files")
    boundary = source_date(Path("xau_ticks_20260720.csv"))
    files_at_or_after_boundary = [
        str(path.resolve()).replace("\\", "/")
        for path in discover_source_files(config)
        if source_date(path) >= boundary
    ]
    if files_at_or_after_boundary:
        raise ValueError("V24 forward files existed before contract lock")
    package_records = []
    for relative in PACKAGE_FILES:
        path = ROOT / relative
        if not path.is_file():
            raise FileNotFoundError(path)
        package_records.append(
            {
                "path": str(path.relative_to(REPO)).replace("\\", "/"),
                "bytes": int(path.stat().st_size),
                "sha256": sha256_file(path),
            }
        )
    forward = config["forward"]
    for key in ("validation_audit", "confirmation_audit"):
        if (ROOT / forward[key]).exists():
            raise ValueError(f"V24 {key} existed before contract lock")
    contract = {
        "schema_version": "xauusd_v24_contract_lock",
        "package_files": package_records,
        "calibration_manifest_sha256": manifest["manifest_sha256"],
        "calibration_file_sha256": manifest["calibration_files"][0]["sha256"],
        "forward_start_inclusive_utc": forward["start_inclusive_utc"],
        "forward_files_present_at_lock": False,
        "forward_files_at_or_after_boundary": files_at_or_after_boundary,
        "validation_outcome_present_at_lock": False,
        "confirmation_outcome_present_at_lock": False,
        "hypothesis_count": 1,
        "direction_count": 1,
        "horizon_count": 1,
        "parameter_grid_allowed": False,
        "economic_outcomes_opened_before_lock": False,
        "same_version_tuning_authorized": False,
        "model_training_authorized": False,
        "python_predictions_authorized": False,
        "ea_consumption_authorized": False,
        "demo_authorized": False,
        "live_authorized": False,
        "broker_action_authorized": False,
    }
    contract["contract_sha256"] = canonical_hash(contract, "contract_sha256")
    output.mkdir(parents=True, exist_ok=True)
    lock_path.write_text(
        json.dumps(contract, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(contract, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
