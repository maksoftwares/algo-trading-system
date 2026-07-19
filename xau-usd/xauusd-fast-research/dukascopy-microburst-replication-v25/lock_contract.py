from __future__ import annotations

import json
from pathlib import Path
import sys
from typing import Any, Mapping

import pandas as pd


ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]
sys.path.insert(0, str(ROOT / "src"))

from replication import (  # noqa: E402
    assert_frozen_rule_parity,
    canonical_hash,
    file_record,
    frozen_v24_root,
    load_config,
    load_locked_v24,
    stage_artifact_names,
    storage_root,
    verify_record,
    verify_source_manifest,
)


PACKAGE_FILES = (
    "README.md",
    "PREREGISTRATION.md",
    "requirements.txt",
    "config/dukascopy_microburst_replication_v25.json",
    "src/__init__.py",
    "src/replication.py",
    "prepare_source_manifest.py",
    "lock_contract.py",
    "run_replication.py",
    "tests/test_replication.py",
)


def _validate_stage_protocol(config: Mapping[str, Any]) -> None:
    source = config["source"]
    stages = list(config["stages"])
    if len(stages) != 3:
        raise ValueError("V25 requires exactly three chronological stages")
    source_start = pd.Timestamp(source["start_inclusive_utc"])
    source_end = pd.Timestamp(source["end_exclusive_utc"])
    prior_end = source_start
    for stage in stages:
        start = pd.Timestamp(stage["start_inclusive_utc"])
        end = pd.Timestamp(stage["end_exclusive_utc"])
        if start != prior_end or end <= start:
            raise ValueError(f"V25 stage windows are not contiguous: {stage['id']}")
        prior_end = end
    if prior_end != source_end:
        raise ValueError("V25 stages do not cover the frozen source window")


def _external_records(
    source_manifest: Mapping[str, Any], config: Mapping[str, Any]
) -> list[dict[str, Any]]:
    root = storage_root(config)
    records = [dict(source_manifest["source_inventory"])]
    for month in source_manifest["months"]:
        records.append(dict(month["acquisition_manifest"]))
        records.append(dict(month["frozen_manifest"]))
    for record in records:
        verify_record(record, root, "V25 external source manifest")
    return sorted(records, key=lambda item: str(item["path"]))


def build_lock(config: dict[str, Any]) -> dict[str, Any]:
    controls = config["research_controls"]
    required_false = (
        "replication_rule_selected_from_dukascopy_outcomes",
        "untouched_archive_claimed",
        "parameter_grid_allowed",
        "same_version_tuning_authorized",
        "paid_data_used",
        "model_training_authorized",
        "python_predictions_authorized",
        "ea_consumption_authorized",
        "demo_authorized",
        "live_authorized",
        "broker_action_authorized",
    )
    if any(bool(controls[key]) for key in required_false):
        raise ValueError("V25 prohibited research permission is enabled")
    required_true = (
        "dukascopy_archive_previously_used_for_other_research",
        "one_stage_per_invocation",
        "later_stage_requires_prior_pass",
        "stage_boundary_label_purge_required",
    )
    if not all(bool(controls[key]) for key in required_true):
        raise ValueError("V25 anti-overfit control is disabled")
    if int(controls["hypothesis_count"]) != 1:
        raise ValueError("V25 must contain exactly one replication hypothesis")
    _validate_stage_protocol(config)
    v24 = load_locked_v24(config)
    assert_frozen_rule_parity(config, v24)

    output = ROOT / config["outputs"]["directory"]
    source_manifest_path = output / config["outputs"]["source_manifest"]
    source_manifest = json.loads(source_manifest_path.read_text(encoding="utf-8"))
    verify_source_manifest(source_manifest, config)
    for stage in config["stages"]:
        for name in stage_artifact_names(stage).values():
            if (output / name).exists():
                raise ValueError(f"V25 stage outcome existed before lock: {name}")

    package_paths = [(ROOT / relative).resolve() for relative in PACKAGE_FILES]
    missing = [str(path) for path in package_paths if not path.is_file()]
    if missing:
        raise FileNotFoundError(missing)
    frozen = config["frozen_v24_1"]
    dependency_root = frozen_v24_root(config)
    dependency_paths = [
        dependency_root / str(frozen["config_relative"]),
        dependency_root / str(frozen["module_relative"]),
        dependency_root / str(frozen["contract_relative"]),
    ]
    payload: dict[str, Any] = {
        "schema_version": "xauusd_dukascopy_microburst_v25_contract_lock",
        "frozen_v24_1_contract_sha256": frozen["contract_sha256"],
        "frozen_rule_sections": {
            key: config[key]
            for key in ("data_quality", "feature", "episode", "simulation", "gates")
        },
        "stages": config["stages"],
        "research_controls": controls,
        "package_files": [file_record(path, REPO) for path in package_paths],
        "dependency_files": [file_record(path, REPO) for path in dependency_paths],
        "source_manifest_file": file_record(source_manifest_path, REPO),
        "source_manifest_sha256": source_manifest["manifest_sha256"],
        "external_manifest_files": _external_records(source_manifest, config),
        "dukascopy_archive_previously_used_for_other_research": True,
        "mechanism_level_replication_not_untouched_archive": True,
        "dukascopy_microburst_pnl_opened_before_lock": False,
        "candidate_generation_performed_before_lock": False,
        "same_version_tuning_authorized": False,
        "model_training_authorized": False,
        "python_predictions_authorized": False,
        "ea_consumption_authorized": False,
        "demo_authorized": False,
        "live_authorized": False,
        "broker_action_authorized": False,
    }
    payload["contract_sha256"] = canonical_hash(payload, "contract_sha256")
    return payload


def main() -> int:
    config = load_config(ROOT)
    output = ROOT / config["outputs"]["directory"] / config["outputs"]["contract_lock"]
    if output.exists():
        raise FileExistsError("V25 contract already exists")
    lock = build_lock(config)
    output.write_bytes(
        (json.dumps(lock, allow_nan=False, indent=2, sort_keys=True) + "\n").encode(
            "utf-8"
        )
    )
    print(json.dumps(lock, allow_nan=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
