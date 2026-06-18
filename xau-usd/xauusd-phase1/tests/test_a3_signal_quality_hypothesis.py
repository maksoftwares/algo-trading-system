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
