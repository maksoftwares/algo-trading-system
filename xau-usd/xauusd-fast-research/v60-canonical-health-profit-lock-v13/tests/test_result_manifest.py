from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_result_manifest_seals_files_and_disarms_actions() -> None:
    manifest = json.loads(
        (ROOT / "outputs" / "RESULT_MANIFEST.json").read_text(encoding="utf-8")
    )
    assert manifest["decision"] == "KEEP_DEPLOYED_V60"
    assert not manifest["deployment_authorized"]
    assert not manifest["broker_action_authorized"]
    for relative, item in manifest["files"].items():
        path = ROOT / relative
        assert path.stat().st_size == item["bytes"]
        assert hashlib.sha256(path.read_bytes()).hexdigest() == item["sha256"]
