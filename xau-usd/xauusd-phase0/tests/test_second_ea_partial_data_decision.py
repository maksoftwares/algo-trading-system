from __future__ import annotations

from pathlib import Path

from phase0.second_ea_partial_data import validate_partial_data_decision


def test_partial_data_decision_unsigned_by_default(tmp_path: Path):
    _write_readiness(tmp_path, "readiness")
    decision = tmp_path / "docs" / "SECOND_EA_PARTIAL_DATA_OWNER_DECISION.md"
    decision.parent.mkdir(parents=True)
    decision.write_text(
        "\n".join(
            [
                "decision_status: NOT_SIGNED",
                "owner_decision: NOT_ACCEPTED",
                "accepted_readiness_content_sha256: " + "0" * 64,
            ]
        ),
        encoding="utf-8",
    )

    output = validate_partial_data_decision(tmp_path)

    assert output.status == "NOT_SIGNED"


def test_partial_data_decision_ignores_instructional_signing_example(tmp_path: Path):
    _write_readiness(tmp_path, "readiness")
    current_hash = _sha256(tmp_path / "outputs" / "reports" / "SECOND_EA_DATA_EXTENSION_READINESS.md")
    decision = tmp_path / "docs" / "SECOND_EA_PARTIAL_DATA_OWNER_DECISION.md"
    decision.parent.mkdir(parents=True)
    decision.write_text(
        "\n".join(
            [
                "decision_status: NOT_SIGNED",
                "owner_decision: NOT_ACCEPTED",
                f"accepted_readiness_content_sha256: {current_hash}",
                "",
                "## How To Sign",
                "",
                "decision_status: SIGNED",
                "owner_decision: OWNER_ACCEPTED_PARTIAL_DATA",
            ]
        ),
        encoding="utf-8",
    )

    output = validate_partial_data_decision(tmp_path)

    assert output.status == "NOT_SIGNED"


def test_partial_data_decision_requires_current_readiness_hash(tmp_path: Path):
    readiness = _write_readiness(tmp_path, "readiness")
    stale_hash = "0" * 64
    decision = tmp_path / "docs" / "SECOND_EA_PARTIAL_DATA_OWNER_DECISION.md"
    decision.parent.mkdir(parents=True)
    decision.write_text(
        "\n".join(
            [
                "decision_status: SIGNED",
                "owner_decision: OWNER_ACCEPTED_PARTIAL_DATA",
                f"accepted_readiness_content_sha256: {stale_hash}",
            ]
        ),
        encoding="utf-8",
    )

    output = validate_partial_data_decision(tmp_path)

    assert readiness.exists()
    assert output.status == "STALE_SIGNATURE"


def test_partial_data_decision_accepts_signed_current_hash(tmp_path: Path):
    readiness = _write_readiness(tmp_path, "readiness")
    current_hash = _sha256(readiness)
    decision = tmp_path / "docs" / "SECOND_EA_PARTIAL_DATA_OWNER_DECISION.md"
    decision.parent.mkdir(parents=True)
    decision.write_text(
        "\n".join(
            [
                "decision_status: SIGNED",
                "owner_decision: OWNER_ACCEPTED_PARTIAL_DATA",
                f"accepted_readiness_content_sha256: {current_hash}",
            ]
        ),
        encoding="utf-8",
    )

    output = validate_partial_data_decision(tmp_path)

    assert output.status == "OWNER_ACCEPTED_PARTIAL"


def _write_readiness(root: Path, text: str) -> Path:
    path = root / "outputs" / "reports" / "SECOND_EA_DATA_EXTENSION_READINESS.md"
    path.parent.mkdir(parents=True)
    path.write_text(text, encoding="utf-8")
    return path


def _sha256(path: Path) -> str:
    import hashlib

    return hashlib.sha256(path.read_bytes()).hexdigest()
