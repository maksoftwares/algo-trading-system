from __future__ import annotations

import json
from pathlib import Path
import sys
import unittest

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from step_2_audit import (  # noqa: E402
    anchored_episode_ids,
    timestamp_audit,
    validate_allowed_columns,
)


class Step2AuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.config = json.loads(
            (ROOT / "config" / "step_2_metadata_audit_v1.json").read_text(
                encoding="utf-8"
            )
        )

    def test_stage_is_metadata_only_and_runtime_is_immutable(self) -> None:
        controls = self.config["audit_controls"]
        self.assertEqual(
            self.config["stage"],
            "STEP_2_METADATA_ONLY_DATA_AND_CANDIDATE_AUDIT",
        )
        self.assertFalse(controls["economic_outcomes_authorized"])
        self.assertFalse(controls["counterfactual_label_build_authorized"])
        self.assertFalse(controls["feature_build_authorized"])
        self.assertFalse(controls["model_training_authorized"])
        self.assertFalse(controls["runtime_change_authorized"])

    def test_economic_columns_are_rejected(self) -> None:
        forbidden = self.config["audit_controls"]["forbidden_read_columns"]
        with self.assertRaises(ValueError):
            validate_allowed_columns(["candidate_id", "stress_net_r"], forbidden)
        validate_allowed_columns(["candidate_id", "decision_time"], forbidden)

    def test_candidate_sources_reconcile_to_frozen_expected_total(self) -> None:
        total = sum(
            int(source["expected_candidates"])
            for source in self.config["candidate_sources"]
        )
        self.assertEqual(total, self.config["expected"]["canonical_candidates"])
        self.assertEqual(total, 3752)
        self.assertEqual(self.config["expected"]["r5_broker_executable"], 10)
        self.assertEqual(self.config["expected"]["r5_broker_ineligible"], 320)

    def test_conservative_episode_anchor_does_not_chain_transitively(self) -> None:
        frame = pd.DataFrame(
            {
                "candidate_id": ["a", "b", "c"],
                "decision_time": pd.to_datetime(
                    [
                        "2026-01-01T00:00:00Z",
                        "2026-01-02T00:00:00Z",
                        "2026-01-03T12:00:00Z",
                    ],
                    utc=True,
                ),
            }
        )
        episodes = anchored_episode_ids(frame, 36)
        self.assertEqual(episodes.iloc[0], episodes.iloc[1])
        self.assertNotEqual(episodes.iloc[1], episodes.iloc[2])

    def test_missing_source_and_cutoff_clocks_fail_closed(self) -> None:
        frame = pd.DataFrame(
            {
                "source_available_at": [pd.NaT],
                "signal_bar_end": pd.to_datetime(["2026-01-01T00:00:00Z"]),
                "decision_time": pd.to_datetime(["2026-01-01T00:00:00Z"]),
                "feature_cutoff_time": [pd.NaT],
                "entry_eligible_time": pd.to_datetime(["2026-01-01T00:00:01Z"]),
                "decision_time_inferred": [True],
            }
        )
        audit = timestamp_audit(frame)
        self.assertEqual(audit["prelabel_complete_clock_rows"], 0)
        self.assertEqual(audit["prelabel_incomplete_clock_rows"], 1)
        self.assertEqual(audit["status"], "REPAIR_REQUIRED")


if __name__ == "__main__":
    unittest.main()
