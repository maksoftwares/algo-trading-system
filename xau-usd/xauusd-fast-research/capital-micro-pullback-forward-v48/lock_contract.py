from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]
sys.path.insert(0, str(ROOT / "src"))

from pullback import canonical_hash, load_config, sha256_file  # noqa: E402


PACKAGE_FILES = (
    ".gitattributes",
    ".gitignore",
    "PREREGISTRATION.md",
    "README.md",
    "requirements.txt",
    "config/capital_micro_pullback_forward_v48.json",
    "prepare_calibration.py",
    "lock_contract.py",
    "run_forward_evaluation.py",
    "src/__init__.py",
    "src/pullback.py",
    "tests/test_pullback.py",
)


def build_contract() -> dict[str, object]:
    config = load_config(ROOT)
    output = ROOT / config["outputs"]["directory"]
    calibration_names = (
        config["outputs"]["calibration_source_manifest"],
        config["outputs"]["calibration_grid"],
        config["outputs"]["calibration_candidates"],
        config["outputs"]["calibration_audit"],
    )
    package_files = [
        {
            "path": str((ROOT / relative).relative_to(REPO)).replace("\\", "/"),
            "bytes": int((ROOT / relative).stat().st_size),
            "sha256": sha256_file(ROOT / relative),
        }
        for relative in PACKAGE_FILES
    ]
    calibration_files = [
        {
            "path": str((output / name).relative_to(REPO)).replace("\\", "/"),
            "bytes": int((output / name).stat().st_size),
            "sha256": sha256_file(output / name),
        }
        for name in calibration_names
    ]
    audit = json.loads(
        (output / config["outputs"]["calibration_audit"]).read_text(encoding="utf-8")
    )
    if canonical_hash(audit, "audit_sha256") != audit["audit_sha256"]:
        raise ValueError("V48 calibration audit self-hash mismatch")
    if not audit["calibration_structure_passed"]:
        raise ValueError("V48 calibration did not select a policy")
    payload: dict[str, object] = {
        "schema_version": config["schema_version"],
        "package_files": package_files,
        "calibration_files": calibration_files,
        "selected_policy": audit["selected_policy"],
        "calibration_audit_sha256": audit["audit_sha256"],
        "forward": config["forward"],
        "simulation": config["simulation"],
        "gates": config["gates"],
        "multiple_testing": config["multiple_testing"],
        "research_controls": config["research_controls"],
    }
    payload["contract_sha256"] = canonical_hash(payload, "contract_sha256")
    return payload


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    config = load_config(ROOT)
    path = ROOT / config["outputs"]["directory"] / config["outputs"]["contract_lock"]
    contract = build_contract()
    if args.write:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(contract, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
    if args.verify:
        locked = json.loads(path.read_text(encoding="utf-8"))
        if locked != contract:
            raise ValueError("V48 contract lock does not match current files")
    json.dump(contract, sys.stdout, indent=2, sort_keys=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
