from __future__ import annotations

import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src import contract, downtrend  # noqa: E402


def test_attempt_ledger_is_contiguous_and_authority_is_closed() -> None:
    config = contract.load_config()
    controls = config["research_controls"]
    attempts = [int(item["attempt_no"]) for item in config["attempts"]]
    assert attempts == [11114, 11115, 11116, 11117]
    assert controls["campaign_attempts_before_v1"] == 11113
    assert controls["new_attempt_first"] == attempts[0]
    assert controls["new_attempt_last"] == attempts[-1]
    assert controls["parameter_search_count"] == 0
    assert not controls["same_version_post_outcome_tuning_authorized"]
    assert not controls["training_authorized"]
    assert not controls["execution_authorized"]


def test_package_and_mt5_dependencies_are_present_and_repo_scoped() -> None:
    config = contract.load_config()
    package_paths = contract.package_files()
    dependency_paths = contract.dependency_files(config)
    assert ROOT / "tests" / "test_downtrend.py" in package_paths
    assert ROOT / "run_research.py" in package_paths
    assert len(dependency_paths) == 6
    for path in dependency_paths:
        path.relative_to(contract.REPO)
        assert path.is_file()


def test_mt5_reference_counts_match_frozen_reports() -> None:
    config = contract.load_config()
    reference = config["mt5_reference"]["candidates"]
    pullback_path = (ROOT / config["mt5_reference"]["pullback_report"]).resolve()
    impulse_path = (ROOT / config["mt5_reference"]["impulse_report"]).resolve()
    pullback = json.loads(pullback_path.read_text(encoding="utf-8"))
    impulse = json.loads(impulse_path.read_text(encoding="utf-8"))
    report_rows = {
        row["name"]: row for row in pullback["standalone_rows"] + impulse["standalone_rows"]
    }
    for frozen in reference.values():
        observed = report_rows[frozen["mt5_variant"]]
        assert observed["signals"] == frozen["mt5_trades"]
        assert observed["pf"] == frozen["mt5_profit_factor"]


def test_old_contract_file_and_self_hash_are_valid() -> None:
    config = contract.load_config()
    assert len(contract._old_m5_records(config)) == 234
    assert len(contract._old_tick_records(config)) == 78


def test_new_raw_tick_manifests_are_complete_and_frozen() -> None:
    config = contract.load_config()
    records = contract._raw_manifest_records(config)
    assert len(records) == 120
    assert downtrend.canonical_json_sha256(records) == config["source"][
        "raw_tick_manifest_digest"
    ]


def test_definition_self_hash_is_order_independent() -> None:
    first = {"schema_version": "test", "value": 1}
    second = {"value": 1, "schema_version": "test"}
    assert contract._self_hash(first) == contract._self_hash(second)
    assert downtrend.canonical_json_sha256(first) == downtrend.canonical_json_sha256(
        second
    )
