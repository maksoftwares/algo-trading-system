from __future__ import annotations

import csv
import copy
import importlib.util
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load_script(name: str, filename: str):
    specification = importlib.util.spec_from_file_location(name, ROOT / filename)
    assert specification and specification.loader
    module = importlib.util.module_from_spec(specification)
    sys.modules[specification.name] = module
    specification.loader.exec_module(module)
    return module


RUNNER = load_script("eurusd_v1r_runner", "run_v1r_baseline.py")
PARITY = load_script("eurusd_v1r_parity", "build_stage0_parity.py")


def test_declared_and_executed_inputs_are_exact() -> None:
    preset = RUNNER.load_preset()
    schema = RUNNER.source_input_schema()
    executed = RUNNER.validate_input_contract(preset, schema)

    assert len(schema) == 34
    assert len(executed) == 34
    assert preset["InpBlockedEntryHoursCsv"] == ""
    assert preset["InpMinBodyFraction"] == "0.40"
    assert preset["InpAtrPeriod"] == "14"
    assert preset["InpMinBandDistanceAtr"] == "0.0"


def test_source_is_tester_only_and_fail_closed() -> None:
    source = RUNNER.SOURCE.read_text(encoding="utf-8")

    assert "if(!MQLInfoInteger(MQL_TESTER))" in source
    assert "g_skip_first_observed_transition = true" in source
    assert 'LogState("STARTUP_TRANSITION_SKIPPED"' in source
    assert "RecentLow(1, 6)" in source
    assert "CopyOne(g_atr_handle, 0, 1, atr)" in source
    assert "stop_points > InpStopCeilingPoints" in source
    assert "IMMEDIATE_NEXT_BAR_RECLAIM" not in source


def test_exact_mt5_result_matches_stage0_target() -> None:
    result = json.loads(
        (ROOT / "outputs" / "mt5" / "EURUSD_V1R_EXACT_MT5_RESULT.json").read_text(
            encoding="utf-8"
        )
    )

    assert result["deal_ledger"]["trades"] == 1145
    assert result["deal_ledger"]["wins"] == 659
    assert result["deal_ledger"]["losses"] == 486
    assert result["deal_ledger"]["net_usd"] == 77.26
    assert result["input_contract"]["ini_leverage"] == "1:50"
    assert result["input_contract"]["report_leverage"] == "1:50"
    assert result["boundary"]["reclaim_implemented"] is False
    assert result["boundary"]["reclaim_run"] is False


def test_stage0_parity_passes_without_mismatches() -> None:
    audit = ROOT / "outputs" / "audit"
    result = json.loads((audit / "STAGE0_PARITY_RESULT.json").read_text(encoding="utf-8"))
    with (audit / "CANONICAL_MISMATCHES.csv").open(
        encoding="utf-8-sig", newline=""
    ) as handle:
        mismatches = list(csv.DictReader(handle))

    assert result["status"] == "STAGE0_PARITY_PASS_RECLAIM_NOT_RUN"
    assert result["all_gates_pass"] is True
    assert all(result["gates"].values())
    assert result["canonical_mismatches"] == 0
    assert mismatches == []


def test_startup_skips_preinitialization_bar() -> None:
    state_path = ROOT / "outputs" / "mt5" / "eurusd_v1r_state_log.csv"
    with state_path.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))

    assert rows[0]["event"] == "INIT_LATCH_ARMED"
    assert rows[1]["event"] == "STARTUP_TRANSITION_SKIPPED"
    assert rows[1]["processed_bar_open"] == "2022.06.30 23:30:00"
    assert rows[2]["event"] == "NATIVE_BAR_TRANSITION"
    assert rows[2]["processed_bar_open"] == "2022.07.01 00:00:00"


def test_source_ex5_chain_is_complete() -> None:
    chain = json.loads(
        (ROOT / "outputs" / "locked" / "SOURCE_EX5_CHAIN.json").read_text(
            encoding="utf-8"
        )
    )

    assert chain["compile_proof"]["compile_zero_errors_zero_warnings"] is True
    assert chain["repository_source"]["sha256"] == chain["tester_source"]["sha256"]
    assert chain["repository_source"]["sha256"] == chain["frozen_source"]["sha256"]
    assert chain["includes"]
    assert chain["frozen_ex5"]["bytes"] > 0


def test_source_chain_artifacts_match_git_blob_manifest() -> None:
    locked = ROOT / "outputs" / "locked"
    chain = json.loads((locked / "SOURCE_EX5_CHAIN.json").read_text(encoding="utf-8"))
    manifest = json.loads(
        (locked / "ARTIFACT_MANIFEST.json").read_text(encoding="utf-8")
    )

    validation = PARITY.validate_source_ex5_chain(chain, manifest)

    assert validation["passed"] is True
    assert validation["source_hashes_equal"] is True
    assert validation["ex5_hashes_equal"] is True
    assert validation["all_chain_artifacts_match_manifest"] is True
    assert all(
        comparison["present_in_manifest"]
        and comparison["bytes_equal"]
        and comparison["sha256_equal"]
        for comparison in validation["artifact_comparisons"]
    )


def test_source_chain_validator_rejects_any_manifest_mismatch() -> None:
    locked = ROOT / "outputs" / "locked"
    chain = json.loads((locked / "SOURCE_EX5_CHAIN.json").read_text(encoding="utf-8"))
    manifest = json.loads(
        (locked / "ARTIFACT_MANIFEST.json").read_text(encoding="utf-8")
    )
    mismatched_manifest = copy.deepcopy(manifest)
    include_path = chain["includes"][0]["frozen"]["path"]
    include_entry = next(
        artifact
        for artifact in mismatched_manifest["artifacts"]
        if artifact["path"] == include_path
    )
    include_entry["sha256"] = "0" * 64

    validation = PARITY.validate_source_ex5_chain(chain, mismatched_manifest)

    assert validation["passed"] is False
    assert validation["all_chain_artifacts_match_manifest"] is False
