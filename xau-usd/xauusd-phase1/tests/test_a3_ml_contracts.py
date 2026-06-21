from __future__ import annotations

import csv
from pathlib import Path

from phase2x_test_helpers import ROOT


CONTRACTS = (
    "A3_ML_META_LABEL_HYPOTHESIS_V1.md",
    "A3_ML_DATA_CONTRACT_V1.md",
    "A3_ML_SIGNAL_GROUPING_CONTRACT_V1.md",
    "A3_ML_EXECUTION_LABEL_CONTRACT_V1.md",
    "A3_ML_SLIPPAGE_MODEL_CONTRACT_V1.md",
    "A3_ML_FEATURE_REGISTRY_V1.csv",
    "A3_ML_FEATURE_BUDGET_CONTRACT_V1.md",
    "A3_ML_REGIME_CONTRACT_V1.md",
    "A3_ML_DIRECTION_ASYMMETRY_PROTOCOL_V1.md",
    "A3_ML_VALIDATION_PROTOCOL_V1.md",
    "A3_ML_POWER_MDE_PROTOCOL_V1.md",
    "A3_ML_DETERMINISTIC_BENCHMARK_PROTOCOL_V1.md",
    "A3_ML_MODEL_SELECTION_PROTOCOL_V1.md",
    "A3_ML_SHADOW_GOVERNANCE_V1.md",
    "A3_ML_RETRAINING_POLICY_V1.md",
    "A3_ML_OWNER_TIMELINE_EXPECTATION_V1.md",
)


def _doc(name: str) -> Path:
    return ROOT / "docs" / name


def _text(name: str) -> str:
    return _doc(name).read_text(encoding="utf-8")


def test_a3_ml_contract_set_exists_and_is_prelock() -> None:
    for name in CONTRACTS:
        path = _doc(name)
        assert path.exists(), name
        if path.suffix == ".md":
            text = path.read_text(encoding="utf-8")
            assert "Status: PRELOCK_CONTRACT" in text


def test_a3_ml_contracts_keep_single_source_of_truth_shape() -> None:
    ownership = {
        "A3_ML_META_LABEL_HYPOTHESIS_V1.md": ("Research Question", "Runtime Boundary"),
        "A3_ML_DATA_CONTRACT_V1.md": (
            "Source Universe",
            "Required Row Times",
            "Per-Fold Class-Count Schema",
            "must not maintain a second copy of the field list",
        ),
        "A3_ML_SIGNAL_GROUPING_CONTRACT_V1.md": ("Exact Signal ID", "Fuzzy Setup Group"),
        "A3_ML_EXECUTION_LABEL_CONTRACT_V1.md": ("Entry", "Holding Horizon", "Holding-Horizon Change Governance"),
        "A3_ML_SLIPPAGE_MODEL_CONTRACT_V1.md": ("Measurements", "Candidate Adequacy", "Leakage Control"),
        "A3_ML_FEATURE_BUDGET_CONTRACT_V1.md": ("Post-Calibration Minority Count", "Earliest-Fold Starvation"),
        "A3_ML_REGIME_CONTRACT_V1.md": ("Regime Labels", "UNKNOWN does not satisfy regime coverage"),
        "A3_ML_VALIDATION_PROTOCOL_V1.md": ("Walk-Forward Structure", "Forward Evidence"),
        "A3_ML_POWER_MDE_PROTOCOL_V1.md": ("Paired Comparison Unit", "Minimum Detectable Effect"),
        "A3_ML_DETERMINISTIC_BENCHMARK_PROTOCOL_V1.md": ("Loose Counter-Trend Veto", "Light Retest"),
        "A3_ML_MODEL_SELECTION_PROTOCOL_V1.md": ("Eligible Models", "Final Historical OOS Gates"),
        "A3_ML_SHADOW_GOVERNANCE_V1.md": ("Runtime Boundary", "Live Python Shadow"),
        "A3_ML_RETRAINING_POLICY_V1.md": ("No Online Learning", "Retraining Eligibility"),
        "A3_ML_OWNER_TIMELINE_EXPECTATION_V1.md": ("CONTINUE_EVIDENCE", "No deadline may override"),
    }
    for name, tokens in ownership.items():
        text = _text(name)
        for token in tokens:
            assert token in text, f"{name}: {token}"


def test_a3_ml_feature_registry_is_ordered_numeric_and_has_one_interaction() -> None:
    with _doc("A3_ML_FEATURE_REGISTRY_V1.csv").open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))

    numeric_rows = [row for row in rows if row["priority"].isdigit()]
    assert [int(row["priority"]) for row in numeric_rows] == list(range(1, 17))
    assert all(row["feature_name"] for row in numeric_rows)
    assert all(row["timing"] for row in numeric_rows)
    assert all(row["criticality"] in {"critical", "noncritical"} for row in numeric_rows)

    interactions = [row for row in rows if "interaction" in row["feature_name"]]
    assert [row["feature_name"] for row in interactions] == ["h1_slope_direction_interaction"]


def test_a3_ml_contracts_do_not_authorize_training_or_broker_action() -> None:
    combined = "\n".join(_text(name) for name in CONTRACTS if name.endswith(".md"))
    assert "No model training" in combined
    assert "No broker action" in combined
    assert "A3 lanes 933200, 933300, and 933400 remain paused" in combined
    assert "Profit-lock remains DRY_RUN_DISARMED" in combined


def test_a3_ml_duplicate_sensitive_clauses_have_single_contract_owners() -> None:
    data = _text("A3_ML_DATA_CONTRACT_V1.md")
    feature_budget = _text("A3_ML_FEATURE_BUDGET_CONTRACT_V1.md")
    execution = _text("A3_ML_EXECUTION_LABEL_CONTRACT_V1.md")
    slippage = _text("A3_ML_SLIPPAGE_MODEL_CONTRACT_V1.md")

    assert "purged_overlap_groups" not in data
    assert "purged_overlap_groups" in feature_budget
    assert "must not maintain a second copy of the field list" in data

    assert "Expected labels use adverse P50" not in execution
    assert "P95-stress labels use adverse P95" not in execution
    assert "Expected labels use adverse P50" in slippage
    assert "P95-stress labels use adverse P95" in slippage
