from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest


PHASE1_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PHASE1_ROOT.parents[1]
SCRIPT = PHASE1_ROOT / "scripts" / "build_a1_xau_fee_evidence_source.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("a1_xau_fee_evidence_source", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


F = _load_module()


def test_fee_instrumentation_is_exactly_reversible_and_changes_only_deal_log():
    pinned = F.read_pinned_source(REPO_ROOT)
    instrumented = F.instrument_deal_fee(pinned)
    assert F.remove_deal_fee_instrumentation(instrumented) == pinned
    assert instrumented.count(b"DEAL_FEE") == pinned.count(b"DEAL_FEE") + 1
    assert b"ArrayResize(values, 20);" in instrumented
    assert b'"swap", "fee", "order_ticket"' in instrumented
    assert b"DEAL_FEE), 16)" in instrumented
    assert b"MQLInfoInteger(MQL_TESTER)" in instrumented
    assert b"case 20: FileWrite" in instrumented


def test_nonpinned_source_is_rejected():
    with pytest.raises(F.FeeEvidenceSourceError, match="not the pinned source"):
        F.instrument_deal_fee(b"not the EA")


def test_builder_records_source_hash_and_reversibility(tmp_path: Path):
    source = tmp_path / f"{F.GENERATED_EXPERT_NAME}.mq5"
    manifest_path = tmp_path / "manifest.json"
    manifest = F.build_fee_evidence_source(REPO_ROOT, source, manifest_path)
    assert manifest["pinned_source_sha256"] == F.PINNED_SOURCE_SHA256
    assert manifest["reversible_to_pinned_source"] is True
    assert manifest["strategy_change"] is False
    assert manifest["instrumentation"]["deal_fee_appended_at_decimal_places"] == 16
    assert manifest["instrumentation"]["strategy_tester_only_guard"] is True
    assert json.loads(manifest_path.read_text(encoding="utf-8")) == manifest
