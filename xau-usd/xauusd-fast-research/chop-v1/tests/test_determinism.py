from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pandas as pd


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


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


def test_bounded_manifest_hashes_real_pipeline_inputs_and_outputs() -> None:
    root = Path(__file__).resolve().parents[1]
    manifest_path = root / "outputs" / "bounded_followup_v1" / "CHOP_BOUNDED_FOLLOWUP_MANIFEST.json"
    assert manifest_path.exists()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    repo_root = root.parents[2]
    for item in manifest["inputs"].values():
        path = repo_root / item["path"]
        assert _file_sha256(path) == item["sha256"]
        assert ":\\" not in item["path"] and "\\" not in item["path"]
    for item in manifest["outputs"].values():
        path = repo_root / item["path"]
        assert _file_sha256(path) == item["sha256"]
        assert ":\\" not in item["path"] and "\\" not in item["path"]
    directions = pd.read_csv(root / "outputs" / "bounded_followup_v1" / "CHOP_M30_DIRECTION_RESULTS.csv")
    assert set(directions["direction"]) == {"LONG", "SHORT"}
