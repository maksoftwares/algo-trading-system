from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))


def load(name: str):
    path = SCRIPTS / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


fee = load("build_a1_xau_fee_evidence_source")
repair = load("build_a1_xau_h4_episode_repair_source")


def repaired_text() -> str:
    pinned = fee.read_source(repair.REPO_ROOT if hasattr(repair, "REPO_ROOT") else ROOT.parents[1], commit=repair.SOURCE_COMMIT, expected_sha256=repair.SOURCE_SHA256)
    instrumented = fee.instrument_deal_fee(pinned, expected_sha256=repair.SOURCE_SHA256)
    return repair.apply_episode_repair(instrumented).decode("utf-8")


def test_repair_requires_first_completed_h4_cross() -> None:
    text = repaired_text()
    assert "h4_previous_close <= box_high && h4_close > box_high" in text
    assert "h4_previous_close >= box_low && h4_close < box_low" in text
    assert text.count("const double h4_previous_close") == 1


def test_repair_has_fail_closed_market_session_expiry() -> None:
    text = repaired_text()
    assert "SymbolInfoSessionTrade" in text
    assert "market_session_closed_permanent_expiry" in text
    assert "GUARD_BLOCK" in text


def test_repair_blocks_minimum_lot_risk_excess() -> None:
    text = repaired_text()
    assert "requested_lots + 0.0000001 < min_lots" in text
    assert "minimum_lot_risk_excess" in text


def test_repair_retains_tester_only_fee_instrumentation() -> None:
    text = repaired_text()
    assert "MQL_TESTER" in text
    assert "DEAL_FEE" in text
