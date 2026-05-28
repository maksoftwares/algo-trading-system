from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_phase2_transition_artifact_verifier_passes_committed_artifacts():
    module = _load_module()

    errors = module.verify_phase2_transition_artifacts(ROOT, ROOT.parents[1], ROOT.parents[1] / "status.html")

    assert errors == []


def test_phase2_transition_artifact_verifier_ignores_generated_timestamps(tmp_path: Path):
    module = _load_module()
    committed = tmp_path / "committed.json"
    generated = tmp_path / "generated.json"
    committed.write_text(json.dumps({"status": "PENDING", "created_at_utc": "old"}), encoding="utf-8")
    generated.write_text(json.dumps({"status": "PENDING", "created_at_utc": "new"}), encoding="utf-8")

    assert module._compare_json("sample", committed, generated) == []


def test_phase2_transition_artifact_verifier_detects_stale_payload(tmp_path: Path):
    module = _load_module()
    committed = tmp_path / "committed.json"
    generated = tmp_path / "generated.json"
    committed.write_text(json.dumps({"status": "PENDING", "checks": [{"status": "PENDING"}]}), encoding="utf-8")
    generated.write_text(json.dumps({"status": "PENDING", "checks": [{"status": "PASS"}]}), encoding="utf-8")

    errors = module._compare_json("sample", committed, generated)

    assert errors == ["sample is stale relative to canonical inputs; regenerate and commit it."]


def _load_module():
    scripts_dir = ROOT / "scripts"
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))
    path = scripts_dir / "verify_phase2_transition_artifacts.py"
    spec = importlib.util.spec_from_file_location("verify_phase2_transition_artifacts", path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["verify_phase2_transition_artifacts"] = module
    spec.loader.exec_module(module)
    return module
