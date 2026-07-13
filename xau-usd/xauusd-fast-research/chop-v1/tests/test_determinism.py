from __future__ import annotations

import hashlib
from pathlib import Path

import pandas as pd


def test_identical_inputs_create_identical_csv_bytes(tmp_path: Path) -> None:
    frame = pd.DataFrame([{"strategy": "A", "net_r": 1.25}, {"strategy": "B", "net_r": -0.5}])
    first, second = tmp_path / "first.csv", tmp_path / "second.csv"
    frame.to_csv(first, index=False, lineterminator="\n")
    frame.to_csv(second, index=False, lineterminator="\n")
    assert hashlib.sha256(first.read_bytes()).digest() == hashlib.sha256(second.read_bytes()).digest()


def test_output_ordering_is_stable() -> None:
    frame = pd.DataFrame([{"time": 2, "strategy": "B"}, {"time": 1, "strategy": "A"}])
    one = frame.sort_values(["time", "strategy"], kind="mergesort").reset_index(drop=True)
    two = frame.sample(frac=1, random_state=7).sort_values(["time", "strategy"], kind="mergesort").reset_index(drop=True)
    pd.testing.assert_frame_equal(one, two)
