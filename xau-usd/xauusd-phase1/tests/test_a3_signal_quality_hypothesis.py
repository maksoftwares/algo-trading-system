from __future__ import annotations

import hashlib
import json
from pathlib import Path

from phase2x_test_helpers import ROOT


def test_a3_signal_quality_hypothesis_is_hash_locked() -> None:
    doc = ROOT / "docs" / "A3_SIGNAL_QUALITY_HYPOTHESES_V1_2026_06_18.md"
    manifest = ROOT / "outputs" / "manifests" / "A3_SIGNAL_QUALITY_HYPOTHESES_V1.sha256.json"

    payload = json.loads(manifest.read_text(encoding="utf-8"))
    digest = hashlib.sha256(doc.read_bytes()).hexdigest()

    assert payload["status"] == "LOCKED"
    assert payload["file"] == "docs/A3_SIGNAL_QUALITY_HYPOTHESES_V1_2026_06_18.md"
    assert payload["sha256"] == digest


def test_a3_signal_quality_hypothesis_keeps_shadow_only_boundary() -> None:
    text = (ROOT / "docs" / "A3_SIGNAL_QUALITY_HYPOTHESES_V1_2026_06_18.md").read_text(encoding="utf-8")

    for token in (
        "A3_SQ_COMBINED_V1",
        "A3_SQ_MTF_ONLY_V1",
        "A3_SQ_RETEST_ONLY_V1",
        "No real `OrderSend`",
        "No `CTrade`",
        "One virtual breakout-family position at a time",
        "TimeGMT()+240",
        "A3_ENTRY_LANES_PAUSED",
    ):
        assert token in text


def test_a3_signal_quality_v1_contract_manifest_hashes_match() -> None:
    manifest = ROOT / "outputs" / "manifests" / "A3_SIGNAL_QUALITY_V1_IMPLEMENTATION_CONTRACT.sha256.json"
    payload = json.loads(manifest.read_text(encoding="utf-8"))

    assert payload["status"] == "LOCKED"
    for row in payload["files"]:
        path = ROOT / row["file"]
        assert path.exists()
        assert hashlib.sha256(path.read_bytes()).hexdigest() == row["sha256"]


def test_a3_signal_quality_v1_lock_note_records_header_manifest_discrepancy() -> None:
    note = (ROOT / "docs" / "A3_SIGNAL_QUALITY_V1_LOCK_NOTE_2026_06_18.md").read_text(encoding="utf-8")

    assert "PRE_REGISTERED_LOCK_PENDING_MANIFEST" in note
    assert "status `LOCKED`" in note
    assert "not edited" in note
