from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LOCK = ROOT / "EURUSD_M15_REGIME_FORWARD_ADJUDICATION_LOCK_2026_07_30.sha256.json"
PRESTART = (
    ROOT
    / "outputs"
    / "m15_regime_forward_adjudication_prestart"
    / "FORWARD_SUMMARY.json"
)


def test_forward_adjudicator_lock_matches_every_frozen_file() -> None:
    lock = json.loads(LOCK.read_text(encoding="utf-8"))
    assert lock["locked_before_forward_floor"] is True
    assert lock["demo_order_authorized"] is False
    for relative, expected in lock["files"].items():
        actual = hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()
        assert actual == expected, relative


def test_captured_prestart_state_contains_no_outcome_or_authorization() -> None:
    summary = json.loads(PRESTART.read_text(encoding="utf-8"))
    assert summary["signals"] == 0
    assert summary["terminal_outcomes"] == 0
    assert summary["pending_signals"] == 0
    assert summary["admission"]["resolved_trades"] == 0
    assert summary["admission"]["invalid_outcomes"] == 0
    assert summary["admission"]["status"] == "WAITING_MINIMUM_EVIDENCE"
    assert summary["demo_order_authorized"] is False
