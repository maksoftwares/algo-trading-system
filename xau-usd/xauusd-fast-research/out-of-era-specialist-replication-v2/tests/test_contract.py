from __future__ import annotations

import importlib.util
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "src" / "contract.py"
SPEC = importlib.util.spec_from_file_location("out_of_era_v2_contract_tests", MODULE_PATH)
if SPEC is None or SPEC.loader is None:
    raise ImportError(MODULE_PATH)
CONTRACT = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = CONTRACT
SPEC.loader.exec_module(CONTRACT)


def test_month_contract_is_exact() -> None:
    config = CONTRACT.load_config()
    months = CONTRACT.expected_months(config)
    assert len(months) == 78
    assert months[0] == "2010-01"
    assert months[-1] == "2016-06"


def test_candidates_and_authorities_are_fixed() -> None:
    config = CONTRACT.load_config()
    CONTRACT._assert_controls(config)
    assert [item["candidate_id"] for item in config["candidates"]] == [
        "R1_UPTREND_PORTABILITY_EXACT",
        "R1B_STRICT_COMPRESSION_EXACT",
        "COMPRESSION_LONG_PORTABILITY_EXACT",
        "FOMC_IMPULSE_CHOP_RR2_V6",
        "FOMC_IMPULSE_STABLE_NON_UPTREND_RR2_V7",
    ]


def test_repository_and_official_source_sets_are_complete() -> None:
    config = CONTRACT.load_config()
    repository = CONTRACT.repository_paths(config)
    public = CONTRACT.public_input_paths(config)
    assert ROOT / "run_research.py" in repository
    assert len(public) == 62


def test_canonical_hash_is_order_independent() -> None:
    assert CONTRACT.canonical_hash({"a": 1, "b": 2}) == CONTRACT.canonical_hash(
        {"b": 2, "a": 1}
    )
