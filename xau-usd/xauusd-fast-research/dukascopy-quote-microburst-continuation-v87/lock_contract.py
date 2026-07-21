from __future__ import annotations

import json
from pathlib import Path
import sys
from typing import Any, Mapping


ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parents[2]
V72_SRC = ROOT.parent / "xag-xau-eventtime-catchup-v72" / "src"
for source in (ROOT / "src", V72_SRC):
    sys.path.insert(0, str(source))

from catchup import canonical_hash, load_json, sha256_file  # noqa: E402
from run_source_audit import (  # noqa: E402
    audit_month_bounds,
    source_audit_decision,
    source_audit_output_path,
)


CONFIG = ROOT / "config" / "dukascopy_quote_microburst_continuation_v87.json"
PACKAGE_FILES = (
    "README.md",
    "PREREGISTRATION.md",
    "PRELOCK_STAGED_SOURCE_AMENDMENT.md",
    "SHARED_PORTFOLIO_PRECOMMITMENT.md",
    "requirements.txt",
    "config/dukascopy_quote_microburst_continuation_v87.json",
    "src/__init__.py",
    "src/quote_microburst.py",
    "run_source_audit.py",
    "run_calibration.py",
    "lock_contract.py",
    "run_stage.py",
    "tests/conftest.py",
    "tests/test_quote_microburst.py",
)


def record(path: Path, base: Path) -> dict[str, Any]:
    resolved = path.resolve()
    return {
        "path": resolved.relative_to(base.resolve()).as_posix(),
        "bytes": int(resolved.stat().st_size),
        "sha256": sha256_file(resolved),
    }


def build_contract(config: Mapping[str, Any]) -> dict[str, Any]:
    package_paths = [ROOT / path for path in PACKAGE_FILES]
    if missing := [str(path) for path in package_paths if not path.is_file()]:
        raise FileNotFoundError(missing)
    output = ROOT / str(config["outputs"]["directory"])
    source_path = source_audit_output_path(dict(config), "development")
    calibration_source_path = output / str(
        config["outputs"]["calibration_source_audit"]
    )
    calibration_path = output / str(config["outputs"]["calibration_audit"])
    source_audit = load_json(source_path)
    calibration_source_audit = load_json(calibration_source_path)
    calibration = load_json(calibration_path)
    if (
        source_audit.get("decision") != source_audit_decision("development")
        or canonical_hash(source_audit, "audit_sha256")
        != source_audit.get("audit_sha256")
    ):
        raise ValueError("V87 source audit is invalid")
    if source_audit.get("symbols") != config["source"]["symbols"]:
        raise ValueError("V87 source audit symbol semantics changed")
    first_month, last_month = audit_month_bounds(dict(config), "development")
    if source_audit.get("first_month") != first_month:
        raise ValueError("V87 development source audit start month changed")
    if source_audit.get("last_month") != last_month:
        raise ValueError("V87 development source audit end month changed")
    if (
        calibration_source_audit.get("decision")
        != "V87_CALIBRATION_SOURCE_AUDIT_PASS"
        or canonical_hash(calibration_source_audit, "audit_sha256")
        != calibration_source_audit.get("audit_sha256")
    ):
        raise ValueError("V87 calibration source audit is invalid")
    if source_audit.get("instrument_evidence") != calibration_source_audit.get(
        "instrument_evidence"
    ):
        raise ValueError("V87 instrument evidence changed after calibration")
    if calibration.get("source_audit_sha256") != sha256_file(
        calibration_source_path
    ):
        raise ValueError("V87 calibration source audit changed")
    if (
        calibration.get("decision") != "V87_CALIBRATION_POLICY_SELECTED"
        or calibration.get("selected_policy") is None
        or canonical_hash(calibration, "audit_sha256")
        != calibration.get("audit_sha256")
    ):
        raise ValueError("V87 calibration did not select a policy")
    if bool(calibration.get("post_candidate_prices_used_for_label_or_outcome")):
        raise ValueError("V87 calibration opened post-candidate outcomes")
    candidate_path = output / str(config["outputs"]["calibration_candidates"])
    grid_path = output / str(config["outputs"]["calibration_grid"])
    if sha256_file(candidate_path) != calibration["selected_candidates_sha256"]:
        raise ValueError("V87 calibration candidates changed")
    if sha256_file(grid_path) != calibration["grid_sha256"]:
        raise ValueError("V87 calibration grid changed")
    dependencies: list[dict[str, Any]] = []
    for dependency in config["locked_dependencies"].values():
        path = REPO_ROOT / str(dependency["path"])
        if sha256_file(path) != dependency["sha256"]:
            raise ValueError(f"V87 dependency changed: {path}")
        dependencies.append(record(path, REPO_ROOT))
    contract: dict[str, Any] = {
        "schema_version": "xauusd_dukascopy_quote_microburst_continuation_v87_contract_lock",
        "package_files": [record(path, ROOT) for path in package_paths],
        "calibration_source_audit": record(calibration_source_path, ROOT),
        "development_source_audit": record(source_path, ROOT),
        "instrument_evidence": source_audit["instrument_evidence"],
        "calibration_audit": record(calibration_path, ROOT),
        "calibration_candidates": record(candidate_path, ROOT),
        "calibration_grid": record(grid_path, ROOT),
        "selected_policy": calibration["selected_policy"],
        "dependencies": dependencies,
        "splits": config["splits"],
        "candidate_rule": config["candidate_rule"],
        "execution": config["execution"],
        "gates": config["gates"],
        "shared_portfolio_gates": config["shared_portfolio_gates"],
        "development_outcomes_present_at_lock": False,
        "confirmation_outcomes_present_at_lock": False,
        "validation_outcomes_present_at_lock": False,
        "exam_outcomes_present_at_lock": False,
        "forward_confirmation_outcomes_present_at_lock": False,
        "forward_final_outcomes_present_at_lock": False,
        **config["research_controls"],
    }
    contract["contract_sha256"] = canonical_hash(contract, "contract_sha256")
    return contract


def verify_lock(config: Mapping[str, Any]) -> dict[str, Any]:
    path = ROOT / str(config["outputs"]["directory"]) / str(
        config["outputs"]["contract_lock"]
    )
    lock = load_json(path)
    expected = build_contract(config)
    if lock != expected:
        raise ValueError("V87 immutable contract verification failed")
    return lock


def main() -> int:
    config = load_json(CONFIG)
    output = ROOT / str(config["outputs"]["directory"])
    path = output / str(config["outputs"]["contract_lock"])
    if path.exists():
        raise FileExistsError("V87 contract already exists")
    economic_outputs = [
        output / f"QUOTE_MICROBURST_V87_{stage.upper()}_{suffix}"
        for stage in (
            "development",
            "confirmation",
            "validation",
            "exam",
            "forward_confirmation",
            "forward_final",
        )
        for suffix in ("CANDIDATES.parquet", "LABELS.parquet", "AUDIT.json")
    ]
    if existing := [str(path) for path in economic_outputs if path.exists()]:
        raise ValueError(f"V87 economic outputs existed before lock: {existing}")
    contract = build_contract(config)
    output.mkdir(parents=True, exist_ok=True)
    path.write_bytes((json.dumps(contract, indent=2, sort_keys=True) + "\n").encode())
    print(json.dumps({"contract_sha256": contract["contract_sha256"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
