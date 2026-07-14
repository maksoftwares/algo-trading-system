from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[2]
OUTPUT = ROOT / "outputs"


def test_exact_invalid_classification_and_no_scoring() -> None:
    result = json.loads((OUTPUT / "LONDON_PROVISIONAL_RESULT.json").read_text(encoding="utf-8"))
    assert result["classification"] == "LONDON_BREAKOUT_V1_PROVISIONAL_DATA_INVALID"
    assert result["strategy_scoring_performed"] is False
    assert result["signals_generated"] == result["trades_generated"] == 0
    assert result["parameter_search_count"] == 0


def test_inventory_preserves_universe_and_detects_missing_year() -> None:
    with (OUTPUT / "LONDON_PROVISIONAL_DATA_INVENTORY.csv").open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert [row["symbol"] for row in rows] == ["XAUUSD", "EURUSD", "GBPUSD", "USDJPY"]
    assert rows[2]["scoring_status"] == "PRE_OUTCOME_DATA_UNAVAILABLE_NOT_SCORED"
    for row in (rows[0], rows[1], rows[3]):
        assert row["m5_final_timestamp_utc"].startswith("2025-06-30")
        assert "M5_END_INCOMPLETE" in row["failure_reasons"]


def test_required_empty_ledgers_are_header_only() -> None:
    for name in ["LONDON_PROVISIONAL_SIGNAL_LEDGER.csv", "LONDON_PROVISIONAL_TRADE_LEDGER.csv"]:
        assert len((OUTPUT / name).read_text(encoding="utf-8").splitlines()) == 1


def test_manifest_hashes_and_determinism() -> None:
    manifest = json.loads((OUTPUT / "LONDON_PROVISIONAL_RUN_MANIFEST.json").read_text(encoding="utf-8"))
    assert manifest["base_commit"] == "11055777a30c193640cdf546898071fb10dfc59d"
    assert manifest["base_tree"] == "1bfdeb5e797df793318638bc81b1c791565a5234"
    assert manifest["deterministic_replay_match"] is True
    assert manifest["run_one_hashes"] == manifest["run_two_hashes"]
    records = [manifest["configuration"]] + manifest["contract_snapshots"]
    records += manifest["quote_basis_evidence"] + manifest["source_data"] + manifest["code_and_tests"] + manifest["outputs"]
    for record in records:
        path = REPO / record["path"]
        assert path.stat().st_size == record["size_bytes"]
        assert hashlib.sha256(path.read_bytes()).hexdigest() == record["sha256"]


def test_parent_stopped_packet_unchanged_from_base() -> None:
    parent_manifest = json.loads((ROOT.parent / "outputs" / "LONDON_BREAKOUT_RUN_MANIFEST.json").read_text(encoding="utf-8"))
    records = [parent_manifest["config"], parent_manifest["contract_and_tick_probe"]]
    records += parent_manifest["code_and_tests"] + parent_manifest["source_data"] + parent_manifest["outputs"]
    for record in records:
        path = REPO / record["path"]
        assert path.stat().st_size == record["size_bytes"]
        assert hashlib.sha256(path.read_bytes()).hexdigest() == record["sha256"]
    assert ROOT.relative_to(REPO).as_posix() == "multi-asset/london-breakout-v1/provisional-bar-screen-v1"
