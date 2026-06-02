from __future__ import annotations

from pathlib import Path

from phase0r.hypothesis_lock import (
    REQUIRED_FIELDS,
    locked_hypotheses_match_manifest,
    register_hypotheses,
    validate_hypotheses_complete,
)


ROOT = Path(__file__).resolve().parents[1]


def test_hypothesis_template_contains_required_fields():
    text = (ROOT / "docs" / "HYPOTHESIS_TEMPLATE_PHASE0R.md").read_text(encoding="utf-8")

    for field in REQUIRED_FIELDS:
        assert f"{field}:" in text


def test_candidate_hypotheses_contain_required_fields():
    validations = validate_hypotheses_complete(ROOT)

    assert len(validations) == 3
    assert all(validation.status == "PASS" for validation in validations)


def test_locked_hypothesis_change_is_detected_without_version_bump(tmp_path):
    root = tmp_path / "phase0r"
    hypotheses = root / "hypotheses"
    hypotheses.mkdir(parents=True)
    source = ROOT / "hypotheses" / "hypothesis_d1_compression_h4_expansion_v0.md"
    text = source.read_text(encoding="utf-8").replace("Status: DRAFT", "Status: LOCKED")
    target = hypotheses / source.name
    target.write_text(text, encoding="utf-8")

    register_hypotheses(root)
    assert locked_hypotheses_match_manifest(root) == []

    target.write_text(text + "\nPost-lock mutation: invalid.\n", encoding="utf-8")

    assert locked_hypotheses_match_manifest(root)
