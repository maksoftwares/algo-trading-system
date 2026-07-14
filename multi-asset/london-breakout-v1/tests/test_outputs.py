from __future__ import annotations

import hashlib
import json
from pathlib import Path


def test_result_stops_before_scoring() -> None:
    root = Path(__file__).resolve().parents[1]
    result = json.loads((root / "outputs" / "LONDON_BREAKOUT_RESULT.json").read_text(encoding="utf-8"))
    assert result["classification"] == "LONDON_BREAKOUT_V1_DATA_INADEQUATE_NO_SCORING"
    assert result["strategy_scoring_performed"] is False
    assert result["complete_trustworthy_instruments"] < result["minimum_required_instruments"]


def test_run_manifest_is_portable_and_all_hashes_match() -> None:
    root = Path(__file__).resolve().parents[1]
    repo = root.parents[1]
    manifest = json.loads((root / "outputs" / "LONDON_BREAKOUT_RUN_MANIFEST.json").read_text(encoding="utf-8"))
    serialized = json.dumps(manifest)
    assert "\\" not in serialized
    items = [manifest["config"], manifest["contract_and_tick_probe"]]
    items += manifest["code_and_tests"] + manifest["source_data"] + manifest["outputs"]
    for item in items:
        path = repo / item["path"]
        assert path.stat().st_size == item["size_bytes"]
        assert hashlib.sha256(path.read_bytes()).hexdigest() == item["sha256"]
