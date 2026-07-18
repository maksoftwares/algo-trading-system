from __future__ import annotations

from datetime import UTC, datetime
import importlib.util
import json
import os
from pathlib import Path
import sys
from typing import Any, Mapping

import pandas as pd

from lock_definitions import (
    CONFIG_PATH,
    LOCK_PATH as DEFINITION_LOCK_PATH,
    REPO,
    ROOT,
    canonical_hash,
    sha256_file,
)


FINAL_LOCK_PATH = ROOT / "outputs" / "OUT_OF_ERA_BREAKOUT_FINAL_CONTRACT_LOCK.json"


def _load_module(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def load_config() -> dict[str, Any]:
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def expected_months(config: Mapping[str, Any]) -> list[str]:
    source = config["source"]
    start = pd.Timestamp(source["start_utc"])
    end = pd.Timestamp(source["end_exclusive_utc"])
    values = pd.period_range(
        start.tz_localize(None).to_period("M"),
        (end - pd.Timedelta(days=1)).tz_localize(None).to_period("M"),
        freq="M",
    ).astype(str).tolist()
    if len(values) != int(source["expected_months"]):
        raise ValueError("Expected-month count disagrees with source boundary")
    return values


def _validate_self_hash(
    payload: Mapping[str, Any], hash_key: str, label: str
) -> None:
    claimed = str(payload.get(hash_key, ""))
    body = dict(payload)
    body.pop(hash_key, None)
    if not claimed or canonical_hash(body) != claimed:
        raise ValueError(f"{label} canonical hash mismatch")


def validate_definition_lock(config: Mapping[str, Any]) -> dict[str, Any]:
    if not DEFINITION_LOCK_PATH.is_file():
        raise FileNotFoundError(DEFINITION_LOCK_PATH)
    lock = json.loads(DEFINITION_LOCK_PATH.read_text(encoding="utf-8"))
    if lock.get("schema_version") != "xauusd_out_of_era_breakout_definition_lock_v2":
        raise ValueError("Unexpected breakout definition-lock schema")
    _validate_self_hash(lock, "definition_contract_sha256", "Definition contract")
    if lock["config_sha256"] != sha256_file(CONFIG_PATH):
        raise ValueError("Configuration changed after definition lock")
    if lock["preregistration_sha256"] != sha256_file(ROOT / "PREREGISTRATION.md"):
        raise ValueError("Preregistration changed after definition lock")
    if lock["gates"] != config["gates"]:
        raise ValueError("Economic gates changed after definition lock")
    if lock["independence"] != config["independence"]:
        raise ValueError("Independence gates changed after definition lock")
    registered = [str(item["candidate_id"]) for item in config["candidates"]]
    if lock["registered_candidates"] != registered:
        raise ValueError("Candidate definitions changed after lock")
    for relative, expected in lock["file_hashes"].items():
        path = (REPO / relative).resolve()
        if not path.is_file() or sha256_file(path) != expected:
            raise ValueError(f"Definition file changed after lock: {relative}")
    if bool(lock.get("outcomes_opened")):
        raise ValueError("Definition lock says outcomes were opened")
    return lock


def upstream_contract(
    config: Mapping[str, Any]
) -> tuple[Any, dict[str, Any], Path]:
    source = config["source"]
    package = (ROOT / source["upstream_package"]).resolve()
    module = _load_module(
        "out_of_era_breakout_upstream_contract", package / "src" / "contract.py"
    )
    upstream_config = module.load_config()
    lock_path = (ROOT / source["upstream_final_lock"]).resolve()
    if not lock_path.is_file():
        raise FileNotFoundError(
            f"Upstream 2010-2016 final contract is not ready: {lock_path}"
        )
    lock = json.loads(lock_path.read_text(encoding="utf-8"))
    module.validate_final_lock(lock, upstream_config)
    return module, lock, lock_path


def build_final_lock(config: Mapping[str, Any]) -> dict[str, Any]:
    definition = validate_definition_lock(config)
    upstream_module, upstream, upstream_path = upstream_contract(config)
    months = expected_months(config)
    if months != upstream["expected_months"]:
        raise ValueError("Upstream data contract covers a different month set")
    repository_files = {
        relative: sha256_file((REPO / relative).resolve())
        for relative in definition["file_hashes"]
    }
    repository_files[
        str(DEFINITION_LOCK_PATH.relative_to(REPO)).replace("\\", "/")
    ] = sha256_file(DEFINITION_LOCK_PATH)
    lock: dict[str, Any] = {
        "schema_version": "xauusd_out_of_era_breakout_final_contract_v2",
        "locked_utc": datetime.now(UTC).isoformat(),
        "definition_contract_sha256": definition["definition_contract_sha256"],
        "expected_months": months,
        "upstream_final_contract_path": str(upstream_path.relative_to(REPO)).replace(
            "\\", "/"
        ),
        "upstream_final_contract_file_sha256": sha256_file(upstream_path),
        "upstream_final_contract_sha256": upstream["final_contract_sha256"],
        "upstream_runtime_versions": upstream["runtime_versions"],
        "repository_files": dict(sorted(repository_files.items())),
        "registered_candidates": definition["registered_candidates"],
        "parameter_search_count": 0,
        "outcomes_opened": False,
        "paid_data_request_made": False,
        "databento_used": False,
        "broker_action_performed": False,
        "training_authorized": False,
        "execution_authorized": False,
    }
    if upstream_module.runtime_versions() != upstream["runtime_versions"]:
        raise ValueError("Runtime changed during final-contract construction")
    lock["final_contract_sha256"] = canonical_hash(lock)
    return lock


def validate_final_lock(
    lock: Mapping[str, Any], config: Mapping[str, Any]
) -> None:
    if lock.get("schema_version") != "xauusd_out_of_era_breakout_final_contract_v2":
        raise ValueError("Unexpected breakout final-contract schema")
    _validate_self_hash(lock, "final_contract_sha256", "Final contract")
    definition = validate_definition_lock(config)
    if lock["definition_contract_sha256"] != definition["definition_contract_sha256"]:
        raise ValueError("Definition contract changed after final lock")
    _, upstream, upstream_path = upstream_contract(config)
    if sha256_file(upstream_path) != lock["upstream_final_contract_file_sha256"]:
        raise ValueError("Upstream final-contract file changed")
    if upstream["final_contract_sha256"] != lock["upstream_final_contract_sha256"]:
        raise ValueError("Upstream final-contract identity changed")
    if lock["expected_months"] != expected_months(config):
        raise ValueError("Final-contract month set changed")
    for relative, expected in lock["repository_files"].items():
        path = (REPO / relative).resolve()
        if not path.is_file() or sha256_file(path) != expected:
            raise ValueError(f"Final-contract repository file changed: {relative}")
    for flag in (
        "outcomes_opened",
        "paid_data_request_made",
        "databento_used",
        "broker_action_performed",
        "training_authorized",
        "execution_authorized",
    ):
        if bool(lock.get(flag)):
            raise ValueError(f"Final contract has prohibited flag: {flag}")


def main() -> int:
    if FINAL_LOCK_PATH.exists():
        raise RuntimeError("Breakout final contract was already locked")
    lock = build_final_lock(load_config())
    FINAL_LOCK_PATH.parent.mkdir(parents=True, exist_ok=True)
    temporary = FINAL_LOCK_PATH.with_suffix(FINAL_LOCK_PATH.suffix + ".part")
    temporary.write_text(
        json.dumps(lock, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    os.replace(temporary, FINAL_LOCK_PATH)
    print(json.dumps(lock, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
