from __future__ import annotations

import csv
import json
from pathlib import Path

from xau_crossasset_residual.core import COMBINED_ID, LONG_ID, SHORT_ID
from xau_crossasset_residual.correction import CORRECTION_OUTPUTS, PRIMARY_COMPLETE

LANE = Path(__file__).resolve().parents[1]
OUTPUTS = LANE / "outputs"


def read_csv(name):
    with (OUTPUTS / name).open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def test_full_replay_required_outputs_are_present():
    assert all((OUTPUTS / name).is_file() for name in CORRECTION_OUTPUTS)


def test_full_replay_binds_all_144_raw_partitions_with_hashes_and_bytes():
    rows = read_csv("XAU_CROSSASSET_RAW_PROVENANCE.csv")
    assert len(rows) == 144
    assert {row["instrument"] for row in rows} == {"XAUUSD", "XAGUSD", "EURUSD", "USDJPY"}
    assert all(int(row["total_raw_bytes"]) > 0 and len(row["hour_file_hash_map_SHA256"]) == 64 for row in rows)
    assert all(row["hash_validation_status"] == "SHA256_VERIFIED" for row in rows)


def test_full_replay_binds_both_model_ledgers_and_semantic_equality():
    evidence = json.loads((OUTPUTS / "XAU_CROSSASSET_MODEL_DETERMINISM.json").read_text(encoding="utf-8"))
    assert evidence["parquet_byte_identical"] and evidence["semantic_rows_identical"] and evidence["schema_identical"]
    assert evidence["run_one"]["Parquet_SHA256"] == evidence["run_two"]["Parquet_SHA256"]
    assert evidence["run_one"]["semantic_ordered_row_SHA256"] == evidence["run_two"]["semantic_ordered_row_SHA256"]


def test_full_replay_principal_ledgers_and_derived_data_are_deterministic():
    manifest = json.loads((OUTPUTS / "XAU_CROSSASSET_CORRECTION_RUN_MANIFEST.json").read_text(encoding="utf-8"))
    assert manifest["normalized_data_deterministic"] and manifest["bar_data_deterministic"]
    assert manifest["signal_ledger_deterministic"] and manifest["trade_ledger_deterministic"]


def test_full_replay_reconciliation_is_complete_for_every_trade():
    reviewed = read_csv("XAU_CROSSASSET_CORRECTION_TRADE_RECONCILIATION.csv")
    corrected = read_csv("XAU_CROSSASSET_TRADE_LEDGER.csv")
    assert len(reviewed) == len(corrected)
    assert all(row["change_reason"] for row in reviewed)


def test_full_replay_capability_profile_has_both_rejected_directions():
    rows = read_csv("XAU_CROSSASSET_CAPABILITY_PROFILE.csv")
    assert {row["specialist_id"] for row in rows} == {LONG_ID, SHORT_ID}
    assert all(row["development_status"] == "REJECTED" and row["validation_status"] == "NOT_ACQUIRED" for row in rows)
    assert all(row["router_compatible"] == "false" for row in rows)


def test_full_replay_correction_gate_audit_has_every_required_category():
    audit = json.loads((OUTPUTS / "XAU_CROSSASSET_CORRECTION_GATE_AUDIT.json").read_text(encoding="utf-8"))
    categories = {row["category"] for row in audit["gates"]}
    required = {"base identity", "scope", "raw provenance", "raw immutability", "synchronization", "model causality", "model determinism", "episode construction", "source-sequence ordering", "same-millisecond ambiguity", "MFE/MAE lifecycle", "entry execution", "exit execution", "baseline costs", "ordinary stress", "broker transfer", "winner concentration", "account contract", "test substance", "long Stage A", "short Stage A", "combined Stage A", "Stage B prohibition", "manifest integrity", "security/path hygiene"}
    assert required <= categories


def test_full_replay_result_retains_rejection_and_blocks_stage_b():
    result = json.loads((OUTPUTS / "XAU_CROSSASSET_CORRECTION_RESULT.json").read_text(encoding="utf-8"))
    assert result["primary_correction_classification"] == PRIMARY_COMPLETE
    assert result["stage_a_survivors"] == []
    assert result["stage_b_files_accessed"] == [] and not result["stage_b_accessed"]


def test_full_replay_direction_results_cover_long_short_and_combined():
    rows = read_csv("XAU_CROSSASSET_DIRECTION_RESULTS.csv")
    assert {row["specialist_id"] for row in rows} == {LONG_ID, SHORT_ID, COMBINED_ID}
    assert all(row["stage_a_pass"] == "false" for row in rows)
