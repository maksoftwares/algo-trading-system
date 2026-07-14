from __future__ import annotations

import hashlib
import json
from pathlib import Path


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def test_manifest_paths_are_portable_and_output_hashes_match() -> None:
    lane = Path(__file__).resolve().parents[1]
    repo = lane.parents[2]
    manifest_path = lane / "outputs" / "MULTIREGIME_MANIFEST.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    for item in [manifest["config"], *manifest["outputs"].values()]:
        assert not Path(item["path"]).is_absolute()
        assert "\\" not in item["path"]
        assert _sha256(repo / item["path"]) == item["sha256"]


def test_locked_exam_tail_and_contract_snapshot_are_hashed_inputs() -> None:
    lane = Path(__file__).resolve().parents[1]
    manifest = json.loads((lane / "outputs" / "MULTIREGIME_MANIFEST.json").read_text(encoding="utf-8"))
    assert manifest["inputs"]["M5"]["locked_tail"]["sha256"]
    assert manifest["inputs"]["contract_snapshot"]["sha256"]


def test_review_run_manifest_binds_every_listed_file() -> None:
    lane = Path(__file__).resolve().parents[1]
    repo = lane.parents[2]
    manifest = json.loads((lane / "evidence" / "MULTIREGIME_RUN_MANIFEST.json").read_text(encoding="utf-8-sig"))
    for group in manifest["inventory"].values():
        for entry in group:
            assert "\\" not in entry["path"]
            path = repo / entry["path"]
            assert path.stat().st_size == entry["size_bytes"]
            assert _sha256(path) == entry["sha256"]


def test_sizing_evidence_reconciles_exactly() -> None:
    lane = Path(__file__).resolve().parents[1]
    audit = json.loads((lane / "outputs" / "MULTIREGIME_GATE_AUDIT.json").read_text(encoding="utf-8"))
    assert audit["sizing_reconciliation_valid"] is True
    assert (
        audit["sizing_accepted_opportunities"]
        + audit["contract_granularity_rejects"]
        + audit["margin_rejects"]
        + audit["other_sizing_rejects"]
        == audit["sizing_evaluated_opportunities"]
    )
