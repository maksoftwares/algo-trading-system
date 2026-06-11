from __future__ import annotations

import hashlib
import json
from pathlib import Path

from phase0.second_ea_preflight import evaluate_second_ea_preflight


def test_second_ea_preflight_blocks_unsigned_partial_data(tmp_path: Path):
    _write_common_files(tmp_path, readiness_status="PARTIAL")
    _write_decision(tmp_path, decision_status="NOT_SIGNED", owner_decision="NOT_ACCEPTED")

    result = evaluate_second_ea_preflight(tmp_path)

    assert result.status == "BLOCKED"
    assert not result.matrix_runs_allowed
    assert result.partial_data_decision_status == "NOT_SIGNED"


def test_second_ea_preflight_blocks_stale_partial_signature(tmp_path: Path):
    _write_common_files(tmp_path, readiness_status="PARTIAL")
    _write_decision(
        tmp_path,
        decision_status="SIGNED",
        owner_decision="OWNER_ACCEPTED_PARTIAL_DATA",
        accepted_hash="0" * 64,
    )

    result = evaluate_second_ea_preflight(tmp_path)

    assert result.status == "BLOCKED"
    assert result.partial_data_decision_status == "STALE_SIGNATURE"


def test_second_ea_preflight_blocks_stale_lowfreq_gate_hash(tmp_path: Path):
    _write_common_files(tmp_path, readiness_status="PASS")
    _write_decision(tmp_path, decision_status="NOT_SIGNED", owner_decision="NOT_ACCEPTED")
    (tmp_path / "docs" / "PHASE0_LOWFREQ_GATE_SET_V1.sha256.json").write_text(
        json.dumps({"status": "LOCKED", "sha256": "0" * 64}),
        encoding="utf-8",
    )

    result = evaluate_second_ea_preflight(tmp_path)

    assert result.status == "BLOCKED"
    assert not result.matrix_runs_allowed
    assert result.lowfreq_gate_hash_status == "STALE_SHA256"


def test_second_ea_preflight_allows_pass_readiness_without_partial_signature(tmp_path: Path):
    _write_common_files(tmp_path, readiness_status="PASS")
    _write_decision(tmp_path, decision_status="NOT_SIGNED", owner_decision="NOT_ACCEPTED")

    result = evaluate_second_ea_preflight(tmp_path)

    assert result.status == "PASS"
    assert result.matrix_runs_allowed


def test_second_ea_preflight_allows_signed_current_partial_data(tmp_path: Path):
    readiness_path = _write_common_files(tmp_path, readiness_status="PARTIAL")
    _write_decision(
        tmp_path,
        decision_status="SIGNED",
        owner_decision="OWNER_ACCEPTED_PARTIAL_DATA",
        accepted_hash=hashlib.sha256(readiness_path.read_bytes()).hexdigest(),
    )

    result = evaluate_second_ea_preflight(tmp_path)

    assert result.status == "PASS"
    assert result.matrix_runs_allowed


def _write_common_files(root: Path, readiness_status: str) -> Path:
    safety = root / "outputs" / "reports" / "SECOND_EA_NO_RUNTIME_TOUCH_AUDIT.md"
    safety.parent.mkdir(parents=True)
    safety.write_text("Status: PASS\n", encoding="utf-8")
    readiness_md = root / "outputs" / "reports" / "SECOND_EA_DATA_EXTENSION_READINESS.md"
    readiness_md.write_text(f"Overall status: {readiness_status}\n", encoding="utf-8")
    readiness_json = root / "outputs" / "reports" / "SECOND_EA_DATA_EXTENSION_READINESS.json"
    readiness_json.write_text(json.dumps({"overall_status": readiness_status}), encoding="utf-8")
    gate_hash = root / "docs" / "PHASE0_LOWFREQ_GATE_SET_V1.sha256.json"
    gate_hash.parent.mkdir(parents=True)
    gate_doc = root / "docs" / "PHASE0_LOWFREQ_GATE_SET_V1.md"
    gate_doc.write_text("# Gate Set\n\nStatus: LOCKED_FOR_SECOND_EA_RESEARCH\n", encoding="utf-8")
    gate_hash.write_text(
        json.dumps({"status": "LOCKED", "sha256": hashlib.sha256(gate_doc.read_bytes()).hexdigest()}),
        encoding="utf-8",
    )
    return readiness_md


def _write_decision(
    root: Path,
    decision_status: str,
    owner_decision: str,
    accepted_hash: str = "",
) -> None:
    path = root / "docs" / "SECOND_EA_PARTIAL_DATA_OWNER_DECISION.md"
    path.write_text(
        "\n".join(
            [
                f"decision_status: {decision_status}",
                f"owner_decision: {owner_decision}",
                f"accepted_readiness_content_sha256: {accepted_hash}",
            ]
        ),
        encoding="utf-8",
    )
