from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from audit_wr50_boundaries import run_audit


def _write_required_docs(repo: Path) -> None:
    docs = repo / "xau-usd" / "xauusd-wr50-experimental" / "docs"
    docs.mkdir(parents=True, exist_ok=True)
    text = (
        "demo-only lane\n"
        "WR50 results do not authorize canonical Phase 2.\n"
        "WR50 results do not authorize live trading.\n"
        "breakout_retest_family = COST_SUSPENDED_CANONICAL\n"
    )
    (repo / "xau-usd" / "xauusd-wr50-experimental" / "README.md").write_text(text, encoding="utf-8")
    (docs / "WR50_EXPERIMENTAL_LANE_RULES.md").write_text(text, encoding="utf-8")
    (docs / "WR50_PHASE_BOUNDARY.md").write_text(text, encoding="utf-8")


def test_order_send_in_phase1_dry_run_folder_fails_boundary_audit(tmp_path: Path) -> None:
    _write_required_docs(tmp_path)
    ea = tmp_path / "xau-usd" / "xauusd-phase1" / "mt5" / "Experts" / "Phase1DryRunShell.mq5"
    ea.parent.mkdir(parents=True, exist_ok=True)
    ea.write_text("void OnTick(){ OrderSend(request, result); }\n", encoding="utf-8")

    audit = run_audit(tmp_path)
    assert not audit.ok
    assert any("outside WR50 allowlist" in error for error in audit.errors)


def test_order_send_in_wr50_allowlist_passes_boundary_audit(tmp_path: Path) -> None:
    _write_required_docs(tmp_path)
    ea = tmp_path / "xau-usd" / "xauusd-wr50-experimental" / "mt5" / "Experts" / "WR50_Test.mq5"
    ea.parent.mkdir(parents=True, exist_ok=True)
    ea.write_text("void OnTick(){ OrderSend(request, result); }\n", encoding="utf-8")

    audit = run_audit(tmp_path)
    assert audit.ok, audit.errors

