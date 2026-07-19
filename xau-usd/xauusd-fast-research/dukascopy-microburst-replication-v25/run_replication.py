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
    VerifiedDukascopyStore,
    assert_frozen_rule_parity,
    canonical_hash,
    evaluate_replication_stage,
    first_runnable_stage,
    load_config,
    load_locked_v24,
    sha256_file,
    stage_artifact_names,
    storage_root,
    verify_record,
    verify_source_manifest,
)


def write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.write_bytes(
        (json.dumps(payload, allow_nan=False, indent=2, sort_keys=True) + "\n").encode(
            "utf-8"
        )
    )


def verify_contract(config: Mapping[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    output = ROOT / str(config["outputs"]["directory"])
    contract_path = output / str(config["outputs"]["contract_lock"])
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    if canonical_hash(contract, "contract_sha256") != str(contract["contract_sha256"]):
        raise ValueError("V25 contract self-hash changed")
    for record in contract["package_files"] + contract["dependency_files"]:
        verify_record(record, REPO, "V25 repository lock")
    source_manifest_path = verify_record(
        contract["source_manifest_file"], REPO, "V25 source manifest"
    )
    source_manifest = json.loads(source_manifest_path.read_text(encoding="utf-8"))
    verify_source_manifest(source_manifest, config)
    if str(source_manifest["manifest_sha256"]) != str(
        contract["source_manifest_sha256"]
    ):
        raise ValueError("V25 source manifest identity changed")
    external_root = storage_root(config)
    for record in contract["external_manifest_files"]:
        verify_record(record, external_root, "V25 external source manifest")
    assert_frozen_rule_parity(config)
    return contract, source_manifest


def _load_stage_audits(
    config: Mapping[str, Any], contract: Mapping[str, Any]
) -> dict[str, dict[str, Any]]:
    output = ROOT / str(config["outputs"]["directory"])
    audits: dict[str, dict[str, Any]] = {}
    prior_passed = True
    for stage in config["stages"]:
        stage_id = str(stage["id"])
        names = stage_artifact_names(stage)
        audit_path = output / names["audit"]
        if not audit_path.exists():
            later = [
                output / stage_artifact_names(candidate)["audit"]
                for candidate in config["stages"]
                if pd.Timestamp(candidate["start_inclusive_utc"])
                > pd.Timestamp(stage["start_inclusive_utc"])
            ]
            if any(path.exists() for path in later):
                raise ValueError("V25 later-stage outcome exists without its predecessor")
            break
        if not prior_passed:
            raise ValueError("V25 stage exists after a terminal prior failure")
        audit = json.loads(audit_path.read_text(encoding="utf-8"))
        if canonical_hash(audit, "audit_sha256") != str(audit["audit_sha256"]):
            raise ValueError(f"V25 stage audit self-hash changed: {stage_id}")
        if str(audit["contract_sha256"]) != str(contract["contract_sha256"]):
            raise ValueError(f"V25 stage contract changed: {stage_id}")
        if str(audit["evidence_partition"]) != stage_id:
            raise ValueError(f"V25 stage identity changed: {stage_id}")
        for artifact, record in audit["artifact_files"].items():
            path = output / names[artifact]
            if (
                not path.is_file()
                or int(path.stat().st_size) != int(record["bytes"])
                or sha256_file(path) != str(record["sha256"])
            ):
                raise ValueError(f"V25 stage artifact changed: {path}")
        audits[stage_id] = audit
        prior_passed = bool(audit["gate_passed"])
    return audits


def _artifact_record(path: Path) -> dict[str, Any]:
    return {"bytes": int(path.stat().st_size), "sha256": sha256_file(path)}


def _terminal_summary(
    config: Mapping[str, Any], audits: Mapping[str, Mapping[str, Any]]
) -> dict[str, Any]:
    failed = [audit for audit in audits.values() if not bool(audit["gate_passed"])]
    if failed:
        return {
            "decision": failed[0]["decision"],
            "failed_stage": failed[0]["evidence_partition"],
            "later_stages_opened": False,
            "same_version_tuning_authorized": False,
        }
    complete = len(audits) == len(config["stages"])
    return {
        "decision": (
            "V25_ALL_STAGES_PASS_HISTORICAL_REPLICATION_ONLY"
            if complete
            else "V25_NO_RUNNABLE_STAGE"
        ),
        "stages_opened": list(audits),
        "untouched_capital_forward_still_required": True,
        "model_training_authorized": False,
        "demo_authorized": False,
    }


def main() -> int:
    config = load_config(ROOT)
    contract, source_manifest = verify_contract(config)
    existing = _load_stage_audits(config, contract)
    stage = first_runnable_stage(config, existing)
    if stage is None:
        print(json.dumps(_terminal_summary(config, existing), indent=2, sort_keys=True))
        return 0

    output = ROOT / str(config["outputs"]["directory"])
    names = stage_artifact_names(stage)
    if any((output / name).exists() for name in names.values()):
        raise FileExistsError(f"V25 partial stage artifacts exist: {stage['id']}")
    v24 = load_locked_v24(config)
    store = VerifiedDukascopyStore(config, source_manifest)
    candidates, trades, daily, quality, audit = evaluate_replication_stage(
        config, stage, store, v24
    )

    frames = {
        "candidates": candidates,
        "trades": trades,
        "daily": daily,
        "quality": quality,
    }
    for artifact, frame in frames.items():
        (output / names[artifact]).write_bytes(
            frame.to_csv(index=False, lineterminator="\n").encode("utf-8")
        )
    audit.update(
        {
            "contract_sha256": contract["contract_sha256"],
            "source_manifest_sha256": source_manifest["manifest_sha256"],
            "artifact_files": {
                artifact: _artifact_record(output / names[artifact])
                for artifact in frames
            },
            "later_stage_outcomes_opened_by_this_invocation": False,
            "untouched_capital_forward_still_required": True,
        }
    )
    audit["audit_sha256"] = canonical_hash(audit, "audit_sha256")
    write_json(output / names["audit"], audit)
    summary = {
        "decision": audit["decision"],
        "stage": audit["evidence_partition"],
        "eligible_full_weekdays": audit["eligible_full_weekdays"],
        "candidate_count": audit["candidate_count_all_source_days"],
        "executable_trades": audit["executable_trade_count"],
        "metrics": audit["frozen_v24_1_gate_audit"]["metrics"],
        "gate_checks": audit["frozen_v24_1_gate_audit"]["gate_checks"],
        "later_stage_outcomes_opened": False,
        "model_training_authorized": False,
        "demo_authorized": False,
    }
    print(json.dumps(summary, allow_nan=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
