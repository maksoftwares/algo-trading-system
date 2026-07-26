from __future__ import annotations

import json
from pathlib import Path
import sys
import unittest

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parents[2]
sys.path.insert(0, str(ROOT / "src"))

from step_2b_contract import (  # noqa: E402
    build_source_corpus_manifest,
    canonical_json_sha256,
    compute_journey_weights,
    sha256_file,
    validate_closed_controls,
    validate_feature_contract,
)


class Step2BContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.config = json.loads(
            (ROOT / "config" / "step_2b_dataset_feature_contract_v1.json").read_text(
                encoding="utf-8"
            )
        )
        cls.step_1 = json.loads(
            (ROOT / "config" / "causal_candidate_quality_ml_v1.json").read_text(
                encoding="utf-8"
            )
        )

    def test_all_step_2b_execution_controls_remain_closed(self) -> None:
        validate_closed_controls(self.config)
        controls = self.config["controls"]
        self.assertFalse(controls["economic_outcomes_authorized"])
        self.assertFalse(controls["model_training_authorized"])
        self.assertFalse(controls["runtime_change_authorized"])
        self.assertFalse(controls["rejection_is_loss"])

    def test_exact_ordered_feature_surface_is_locked(self) -> None:
        audit = validate_feature_contract(self.config, self.step_1)
        self.assertEqual(audit["ordered_feature_count"], 59)
        self.assertEqual(audit["primary_blocks"], 3)
        self.assertEqual(audit["comex_research_blocks"], 1)
        self.assertEqual(
            len(audit["ordered_feature_sha256"]),
            64,
        )

    def test_failure_library_is_retained_but_cannot_overwhelm_primary(self) -> None:
        population = self.config["population_contract"]
        self.assertEqual(population["primary_fit_population"], "CANONICAL")
        self.assertEqual(population["primary_fit_candidate_rows"], 3752)
        self.assertTrue(population["primary_fit_includes_historical_policy_rejections"])
        self.assertEqual(population["journey_candidate_directions"], 51722)
        self.assertFalse(population["journey_rows_may_enter_primary_fit"])
        self.assertFalse(population["journey_rows_may_rescue_primary_failure"])

    def test_journey_weights_sum_to_one_per_event(self) -> None:
        frame = pd.DataFrame(
            {
                "action_row_id": ["a1", "a2", "b1", "b2", "c1"],
                "candidate_id": ["a", "a", "b", "b", "c"],
                "population": ["R"] * 5,
                "source_id": ["S"] * 5,
                "structural_episode_id": ["E", "E", "E", "E", "F"],
                "candidate_action_count": [2, 2, 2, 2, 1],
            }
        )
        weighted = compute_journey_weights(frame)
        sums = weighted.groupby("structural_episode_id")[
            "journey_diagnostic_weight"
        ].sum()
        self.assertEqual(sums.to_dict(), {"E": 1.0, "F": 1.0})

    def test_source_corpus_is_complete_and_frozen(self) -> None:
        manifest = build_source_corpus_manifest(self.config)
        self.assertEqual(manifest["record_count"], 378)
        self.assertEqual(manifest["by_symbol"]["XAUUSD"]["months"], 198)
        self.assertEqual(manifest["by_symbol"]["DOLLARIDXUSD"]["months"], 90)
        self.assertEqual(manifest["by_symbol"]["USTBONDTRUSD"]["months"], 90)
        self.assertTrue(manifest["physical_hour_file_sets_verified"])
        self.assertFalse(manifest["raw_files_opened"])
        self.assertFalse(manifest["economic_outcomes_opened"])

    def test_generated_split_and_weight_plans_match_contract(self) -> None:
        output = ROOT / "outputs" / "step_2b"
        split = json.loads(
            (output / "STEP_2B_OUTCOME_BLIND_SPLIT_PLAN.json").read_text(
                encoding="utf-8"
            )
        )
        expected = {
            era["fold_id"]: (
                era["expected_outcome_blind_fit_rows"],
                era["expected_outcome_blind_calibration_rows"],
                era["expected_test_candidate_rows"],
            )
            for era in self.config["split_contract"]["outer_eras"]
        }
        observed = {
            fold["fold_id"]: (
                fold["outcome_blind_counts"]["fit"],
                fold["outcome_blind_counts"]["calibration"],
                fold["outcome_blind_counts"]["test"],
            )
            for fold in split["folds"]
        }
        self.assertEqual(observed, expected)
        weights = pd.read_parquet(output / "STEP_2B_JOURNEY_WEIGHT_PLAN.parquet")
        self.assertEqual(len(weights), 117534)
        self.assertEqual(weights["candidate_id"].nunique(), 51722)
        self.assertEqual(weights["structural_episode_id"].nunique(), 40077)
        self.assertAlmostEqual(weights["journey_diagnostic_weight"].sum(), 40077.0)

    def test_generated_lock_and_artifacts_recalculate(self) -> None:
        output = ROOT / "outputs" / "step_2b"
        lock = json.loads(
            (output / "STEP_2B_DATASET_FEATURE_CONTRACT_LOCK.json").read_text(
                encoding="utf-8"
            )
        )
        unsigned = {
            key: value
            for key, value in lock.items()
            if key != "definition_contract_sha256"
        }
        self.assertEqual(
            lock["definition_contract_sha256"], canonical_json_sha256(unsigned)
        )
        self.assertFalse(lock["economic_outcomes_opened"])
        self.assertFalse(lock["model_fitted"])
        self.assertFalse(lock["runtime_changed"])
        manifest = json.loads(
            (output / "STEP_2B_ARTIFACT_MANIFEST.json").read_text(encoding="utf-8")
        )
        for artifact in manifest["artifacts"].values():
            path = REPO_ROOT / artifact["path"]
            self.assertEqual(path.stat().st_size, artifact["bytes"])
            self.assertEqual(sha256_file(path), artifact["sha256"])


if __name__ == "__main__":
    unittest.main()
