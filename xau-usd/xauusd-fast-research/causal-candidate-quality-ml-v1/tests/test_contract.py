from __future__ import annotations

import importlib.util
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "config" / "causal_candidate_quality_ml_v1.json"


def load_lock_module():
    spec = importlib.util.spec_from_file_location(
        "candidate_quality_lock", ROOT / "lock_contract.py"
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load contract lock module")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))

    def test_v59_v60_is_immutable_and_execution_is_unauthorized(self) -> None:
        task = self.config["primary_task"]
        controls = self.config["step_1_controls"]
        self.assertEqual(self.config["baseline"]["accepted_trades"], 2194)
        self.assertFalse(task["core_filtering_execution_authorized"])
        self.assertFalse(task["entry_generation_authorized"])
        self.assertFalse(task["portfolio_override_authorized"])
        self.assertFalse(controls["runtime_changed"])
        self.assertFalse(controls["demo_ml_authorized"])
        self.assertFalse(controls["live_ml_authorized"])
        self.assertFalse(controls["broker_action_authorized"])

    def test_history_and_prospective_boundaries_fail_closed(self) -> None:
        evidence = self.config["evidence"]
        prospective = self.config["prospective"]
        self.assertEqual(
            evidence["historical_development_cutoff_utc"],
            "2026-07-01T00:00:00Z",
        )
        self.assertFalse(evidence["history_is_pristine_holdout"])
        self.assertTrue(evidence["prospective_start_requires_final_model_lock"])
        self.assertFalse(prospective["authorized_by_step_1"])
        self.assertFalse(prospective["pass_grants_execution"])

    def test_data_and_feature_freedom_is_bounded(self) -> None:
        data = self.config["data_policy"]
        features = self.config["features"]
        budget = self.config["model_budget"]
        self.assertFalse(data["comex_live_delivery_verified"])
        self.assertFalse(data["comex_required_for_deployment"])
        self.assertIn("RAW_EVENT_NEURAL_ENCODER_V1", data["forbidden"])
        self.assertLessEqual(features["maximum_primary_columns"], 64)
        self.assertEqual(len(features["nested_blocks"]), 4)
        self.assertEqual(budget["registered_primary_pipelines_per_outer_fold"], 6)
        self.assertEqual(
            budget["registered_comex_pipelines_per_eligible_outer_fold"], 2
        )
        self.assertEqual(
            budget["registered_total_architecture_feature_combinations"], 8
        )
        self.assertFalse(budget["comex_can_compete_as_full_history_winner"])
        self.assertFalse(budget["comex_can_authorize_deployment"])
        self.assertFalse(budget["hyperparameter_search_authorized"])
        self.assertFalse(budget["threshold_search_authorized"])
        self.assertFalse(budget["same_version_rescue_authorized"])

    def test_rejections_are_not_losses_and_labels_are_side_correct(self) -> None:
        labels = self.config["labels"]
        self.assertFalse(labels["rejection_is_loss"])
        self.assertEqual(labels["long_entry_side"], "ASK")
        self.assertEqual(labels["long_exit_side"], "BID")
        self.assertEqual(labels["short_entry_side"], "BID")
        self.assertEqual(labels["short_exit_side"], "ASK")
        self.assertTrue(labels["spread_double_charge_prohibited"])

    def test_random_splits_quotas_and_core_changes_are_forbidden(self) -> None:
        splits = self.config["historical_splits"]
        decision = self.config["decision"]
        gates = self.config["historical_nomination_gates"]
        self.assertEqual(len(splits["outer_test_eras"]), 6)
        self.assertFalse(splits["random_or_shuffled_split_authorized"])
        self.assertTrue(splits["label_interval_purge_required"])
        self.assertTrue(splits["episode_group_purge_required"])
        self.assertFalse(decision["daily_quota_authorized"])
        self.assertTrue(gates["v59_v60_trade_identity_required"])

    def test_lock_payload_binds_governance_and_baseline_files(self) -> None:
        module = load_lock_module()
        payload = module.build_payload()
        self.assertEqual(len(payload["baseline_files"]), 5)
        self.assertEqual(len(payload["governance_files"]), 5)
        self.assertFalse(payload["economic_outcomes_opened_at_lock"])
        self.assertFalse(payload["model_fitted_at_lock"])
        self.assertFalse(payload["runtime_changed_at_lock"])


if __name__ == "__main__":
    unittest.main()
