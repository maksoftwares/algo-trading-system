from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
import unittest

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from step_2a_repair import (  # noqa: E402
    action_is_complete,
    conservative_episode_ids,
    load_mt5_tsv,
    sha256_file,
    validate_allowed_columns,
)


class Step2ARepairTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.config = json.loads(
            (ROOT / "config" / "step_2a_metadata_repair_v1.json").read_text(
                encoding="utf-8"
            )
        )

    def test_stage_cannot_open_outcomes_or_change_runtime(self) -> None:
        controls = self.config["controls"]
        self.assertFalse(controls["economic_outcomes_authorized"])
        self.assertFalse(controls["counterfactual_label_build_authorized"])
        self.assertFalse(controls["feature_value_build_authorized"])
        self.assertFalse(controls["model_training_authorized"])
        self.assertFalse(controls["threshold_fitting_authorized"])
        self.assertFalse(controls["portfolio_simulation_authorized"])
        self.assertFalse(controls["runtime_change_authorized"])
        self.assertFalse(controls["rejection_is_loss"])

    def test_economic_columns_are_rejected(self) -> None:
        forbidden = self.config["controls"]["forbidden_read_columns"]
        with self.assertRaises(ValueError):
            validate_allowed_columns(["candidate_id", "pnl_usd"], forbidden)
        validate_allowed_columns(["candidate_id", "decision_time"], forbidden)

    def test_mt5_trailing_tab_does_not_shift_columns(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            path = Path(temporary_directory) / "orders.tsv"
            path.write_text(
                "timestamp_broker\taction\tdirection\t\n"
                "2026.01.01 00:00:00\tORDER_SEND_OK\tLONG\t\n",
                encoding="utf-8",
            )
            frame = load_mt5_tsv(path, ["timestamp_broker", "action", "direction"])
        self.assertEqual(frame.loc[0, "timestamp_broker"], "2026.01.01 00:00:00")
        self.assertEqual(frame.loc[0, "action"], "ORDER_SEND_OK")
        self.assertEqual(frame.loc[0, "direction"], "LONG")

    def test_barrier_and_fixed_horizon_actions_are_complete(self) -> None:
        frame = pd.DataFrame(
            {
                "stop_mode": ["NATIVE_PRETRADE_POINTS", "ATR"],
                "stop_atr": [np.nan, 1.5],
                "stop_value": [320.0, np.nan],
                "target_mode": ["R_MULTIPLE", "NONE"],
                "target_r": [2.0, np.nan],
                "maximum_hold_mode": [
                    "BARRIER_ONLY_NO_TIME_STOP",
                    "FIXED",
                ],
                "maximum_hold_minutes": [np.nan, 720.0],
                "label_observation_cap_minutes": [129600.0, 720.0],
            }
        )
        self.assertTrue(action_is_complete(frame).all())

    def test_episode_anchor_uses_same_time_maximum_but_does_not_chain(self) -> None:
        frame = pd.DataFrame(
            {
                "candidate_id": ["a", "b", "c", "d"],
                "decision_time": pd.to_datetime(
                    [
                        "2026-01-01T00:00:00Z",
                        "2026-01-01T00:00:00Z",
                        "2026-01-01T05:00:00Z",
                        "2026-01-01T15:00:00Z",
                    ],
                    utc=True,
                ),
                "planned_observation_end": pd.to_datetime(
                    [
                        "2026-01-01T01:00:00Z",
                        "2026-01-01T10:00:00Z",
                        "2026-01-01T20:00:00Z",
                        "2026-01-01T16:00:00Z",
                    ],
                    utc=True,
                ),
            }
        )
        episodes = conservative_episode_ids(frame)
        self.assertEqual(episodes.iloc[0], episodes.iloc[1])
        self.assertEqual(episodes.iloc[1], episodes.iloc[2])
        self.assertNotEqual(episodes.iloc[2], episodes.iloc[3])

    def test_generated_registries_preserve_identity_without_outcomes(self) -> None:
        output = ROOT / "outputs" / "step_2a"
        forbidden = set(self.config["controls"]["forbidden_read_columns"])
        expected = {
            "STEP_2A_CANONICAL_CANDIDATE_REGISTRY.parquet": (
                3752,
                "candidate_id",
                3752,
            ),
            "STEP_2A_R1_GUARD_DECISION_REGISTRY.parquet": (
                3951,
                "candidate_id",
                3951,
            ),
            "STEP_2A_R5_PREPOLICY_REGISTRY.parquet": (799, "candidate_id", 799),
            "STEP_2A_JOURNEY_ACTION_REGISTRY.parquet": (
                117534,
                "action_row_id",
                117534,
            ),
            "STEP_2A_JOURNEY_CANDIDATE_REGISTRY.parquet": (
                51722,
                "candidate_id",
                51722,
            ),
        }
        for filename, (rows, identity, unique) in expected.items():
            frame = pd.read_parquet(output / filename)
            self.assertEqual(len(frame), rows)
            self.assertEqual(frame[identity].nunique(), unique)
            self.assertFalse({column.lower() for column in frame.columns} & forbidden)

    def test_generated_artifact_manifest_recalculates(self) -> None:
        output = ROOT / "outputs" / "step_2a"
        manifest = json.loads(
            (output / "STEP_2A_ARTIFACT_MANIFEST.json").read_text(encoding="utf-8")
        )
        self.assertFalse(manifest["economic_outcomes_opened"])
        self.assertFalse(manifest["model_fitted"])
        self.assertFalse(manifest["runtime_changed"])
        for artifact in manifest["artifacts"].values():
            path = ROOT.parents[2] / artifact["path"]
            self.assertEqual(path.stat().st_size, artifact["bytes"])
            self.assertEqual(sha256_file(path), artifact["sha256"])


if __name__ == "__main__":
    unittest.main()
