from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from xau_crossasset_residual.correction import (
    CORRECTION_OUTPUTS, model_binding, parquet_semantic_sha256, substantive_test_functions,
)

LANE = Path(__file__).resolve().parents[1]


def test_required_correction_output_contract_is_complete_and_unique():
    assert len(CORRECTION_OUTPUTS) == 10
    assert len(set(CORRECTION_OUTPUTS)) == 10
    assert "XAU_CROSSASSET_MODEL_DETERMINISM.json" in CORRECTION_OUTPUTS
    assert "XAU_CROSSASSET_RAW_PROVENANCE.csv" in CORRECTION_OUTPUTS


def test_parquet_semantic_hash_is_order_sensitive_and_repeatable(tmp_path):
    first = tmp_path / "first.parquet"
    second = tmp_path / "second.parquet"
    frame = pd.DataFrame({"timestamp_ms": [1, 2], "value": [1.5, 2.5]})
    frame.to_parquet(first, index=False)
    frame.to_parquet(second, index=False)
    assert parquet_semantic_sha256(first) == parquet_semantic_sha256(second)
    frame.iloc[::-1].to_parquet(second, index=False)
    assert parquet_semantic_sha256(first) != parquet_semantic_sha256(second)


def test_model_binding_records_byte_semantic_schema_and_range(tmp_path):
    path = tmp_path / "model-ledger.parquet"
    frame = pd.DataFrame({"timestamp_ms": [1, 2], "model_valid": [False, True], "residual_z": [float("nan"), 1.0]})
    frame.to_parquet(path, index=False)
    binding = model_binding(path, frame, "corrected-run-one")
    assert binding["row_count"] == 2 and binding["column_count"] == 3
    assert len(binding["Parquet_SHA256"]) == len(binding["semantic_ordered_row_SHA256"]) == len(binding["schema_SHA256"]) == 64
    assert binding["valid_model_row_count"] == binding["valid_residual_z_row_count"] == 1


def test_substantive_test_inventory_contains_no_placeholder_matrix():
    functions = substantive_test_functions(LANE)
    assert len(functions) >= 50
    assert all(name != "test_frozen_contract_matrix" for _, name in functions)


def test_lane_source_and_committed_outputs_have_no_username_or_credentials():
    for path in list((LANE / "src").rglob("*.py")) + list((LANE / "outputs").glob("*")):
        if not path.is_file() or path.suffix.lower() in {".pyc", ".parquet"}:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore").lower()
        assert ("zhao" + " zhu information") not in text
        assert ("c:" + "\\users\\") not in text
        assert ("authorization" + ": bearer") not in text
        assert ("api_" + "secret") not in text


def test_correction_source_has_no_stage_b_acquisition_or_scoring_call():
    source = (LANE / "src" / "xau_crossasset_residual" / "correction.py").read_text(encoding="utf-8")
    assert "acquire_stage_a(" not in source
    assert '"stage_b_acquisitions": 0' in source
    assert '"stage_b_scoring_runs": 0' in source
