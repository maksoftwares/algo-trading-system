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


def test_a3_signal_quality_v1_addendum_manifest_hashes_match() -> None:
    manifest = ROOT / "outputs" / "manifests" / "A3_SIGNAL_QUALITY_V1_IMPLEMENTATION_ADDENDUM_01.sha256.json"
    payload = json.loads(manifest.read_text(encoding="utf-8"))

    assert payload["status"] == "LOCKED"
    for row in payload["files"]:
        path = ROOT / row["file"]
        assert path.exists()
        assert hashlib.sha256(path.read_bytes()).hexdigest() == row["sha256"]


def test_a3_signal_quality_v1_addendum_resolves_implementation_seams() -> None:
    text = (ROOT / "docs" / "A3_SIGNAL_QUALITY_V1_IMPLEMENTATION_ADDENDUM_01.md").read_text(encoding="utf-8")

    for token in (
        "First-Retest Definition",
        "Signal Timestamp",
        "Entry Tick Eligibility",
        "Indicator Seeding And Warm-Up",
        "Timezone And DST Mapping",
        "Weekend And Gap Behavior",
        "Restart Recovery",
        "Tick Freshness",
        "Rounding And Points",
        "Holding Duration",
        "Gap Exit Pricing",
        "one-trading-week language is an implementation-validation minimum only",
        "At least 4 calendar weeks",
        "does not authorize A3 reactivation",
    ):
        assert token in text


def test_a3_signal_quality_diagnostic_sweep_manifest_hashes_match() -> None:
    manifest = ROOT / "outputs" / "manifests" / "A3_SIGNAL_QUALITY_DIAGNOSTIC_SWEEP_V1.sha256.json"
    payload = json.loads(manifest.read_text(encoding="utf-8"))

    assert payload["status"] == "LOCKED"
    for row in payload["files"]:
        path = ROOT / row["file"]
        assert path.exists()
        assert hashlib.sha256(path.read_bytes()).hexdigest() == row["sha256"]


def test_a3_signal_quality_diagnostic_sweep_registers_frequency_preserving_candidates() -> None:
    text = (ROOT / "docs" / "A3_SIGNAL_QUALITY_DIAGNOSTIC_SWEEP_V1_2026_06_18.md").read_text(encoding="utf-8")

    for token in (
        "B0_RAW_ALL_SESSION",
        "B1_EVENING_BASELINE",
        "F_LOOSE_CT_VETO",
        "F_H1_ALIGN",
        "F_H1_M15_ALIGN",
        "F_RETEST_LIGHT",
        "F_LOOSE_CT_PLUS_RETEST_LIGHT",
        "A3_SQ_MTF_ONLY_V1",
        "A3_SQ_RETEST_ONLY_V1",
        "A3_SQ_COMBINED_V1",
        "signal retention >= 40% of B0",
        "virtual-trade retention >= 35% of B0",
        "not promotion evidence",
        "STOP_NO_CANDIDATE",
        "A3 remains paused",
    ):
        assert token in text


def test_a3_signal_quality_v1_lock_note_records_header_manifest_discrepancy() -> None:
    note = (ROOT / "docs" / "A3_SIGNAL_QUALITY_V1_LOCK_NOTE_2026_06_18.md").read_text(encoding="utf-8")

    assert "PRE_REGISTERED_LOCK_PENDING_MANIFEST" in note
    assert "status `LOCKED`" in note
    assert "not edited" in note
