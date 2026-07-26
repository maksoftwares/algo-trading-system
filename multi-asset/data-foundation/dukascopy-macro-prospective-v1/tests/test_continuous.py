from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from run_continuous import latest_feature


def test_latest_feature_uses_snapshot_end(tmp_path: Path) -> None:
    feature_dir = tmp_path / "features"
    feature_dir.mkdir()
    config = {"output": {"feature_directory": "features"}}
    for suffix, end in (
        ("A", "2026-07-25T23:00:00Z"),
        ("B", "2026-07-27T02:00:00Z"),
    ):
        snapshot = tmp_path / f"{suffix}.snapshot.json"
        snapshot.write_text(json.dumps({"end_exclusive_utc": end}), encoding="utf-8")
        (feature_dir / f"MACRO_{suffix}_M5_FEATURES_V1.manifest.json").write_text(
            json.dumps({"snapshot_manifest": str(snapshot)}),
            encoding="utf-8",
        )
    observed, manifest = latest_feature(tmp_path, config)
    assert observed == datetime(2026, 7, 27, 2, tzinfo=UTC)
    assert manifest is not None and "MACRO_B_" in manifest.name
