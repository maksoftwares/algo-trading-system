from __future__ import annotations

import json
import sys
from pathlib import Path

from phase2x_test_helpers import ROOT, load_script


if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def test_c28_confirms_demo_shadow_when_c22_and_c27_are_ready(tmp_path: Path, monkeypatch) -> None:
    from ml.a3_meta_v1 import demo_shadow_post_attach_monitor as module

    root = _root(tmp_path)
    _patch_runners(
        monkeypatch,
        module,
        c22_status="RUNTIME_EVIDENCE_PRESENT_ALL_ACCOUNTS",
        c27_status="RESEARCH_PREVIEW_READ_PATH_CONFIRMED_ALL_ACCOUNTS",
    )

    output = module.wait_for_demo_shadow_post_attach(root, timeout_seconds=0)
    payload = json.loads(output.read_text(encoding="utf-8"))
    pointer = json.loads((root / "outputs" / "reports" / "C02_DATASET_POINTER.json").read_text(encoding="utf-8"))

    assert payload["status"] == "DEMO_SHADOW_RUNTIME_CONFIRMED_ALL_ACCOUNTS"
    assert payload["runtime_evidence"]["post_attach_runtime_evidence_all_accounts"] is True
    assert payload["runtime_evidence"]["research_preview_read_path_confirmed_all_accounts"] is True
    assert payload["authorization"]["python_demo_predictions_authorized"] is False
    assert pointer["c28_demo_shadow_runtime_confirmed_all_accounts"] is True


def test_c28_waits_when_runtime_and_read_path_are_missing(tmp_path: Path, monkeypatch) -> None:
    from ml.a3_meta_v1 import demo_shadow_post_attach_monitor as module

    root = _root(tmp_path)
    _patch_runners(
        monkeypatch,
        module,
        c22_status="WAITING_FOR_MANUAL_ATTACH",
        c27_status="WAITING_FOR_MT5_RUNTIME_ATTACH",
    )

    output = module.wait_for_demo_shadow_post_attach(root, timeout_seconds=0)
    payload = json.loads(output.read_text(encoding="utf-8"))

    assert payload["status"] == "WAITING_FOR_MT5_RUNTIME_ATTACH"
    assert payload["monitor"]["attempt_count"] == 1
    assert payload["runtime_evidence"]["handoff_research_preview_ready_all_accounts"] is True
    assert payload["runtime_evidence"]["broker_shadow_tap_exists_all_accounts"] is False


def test_c28_blocks_when_c27_preflight_blocks(tmp_path: Path, monkeypatch) -> None:
    from ml.a3_meta_v1 import demo_shadow_post_attach_monitor as module

    root = _root(tmp_path)
    _patch_runners(
        monkeypatch,
        module,
        c22_status="WAITING_FOR_MANUAL_ATTACH",
        c27_status="PREFLIGHT_BLOCKED",
    )

    output = module.wait_for_demo_shadow_post_attach(root, timeout_seconds=0)
    payload = json.loads(output.read_text(encoding="utf-8"))

    assert payload["status"] == "PREFLIGHT_BLOCKED"
    assert payload["authorization"]["broker_action_authorized"] is False


def test_c28_script_loads() -> None:
    module = load_script("c28_wait_for_demo_shadow_post_attach")

    assert hasattr(module, "main")


def _root(tmp_path: Path) -> Path:
    root = tmp_path / "phase1"
    reports = root / "outputs" / "reports"
    reports.mkdir(parents=True)
    _write_json(reports / "C02_DATASET_POINTER.json", {"dataset_version": "TEST"})
    return root


def _patch_runners(monkeypatch, module, *, c22_status: str, c27_status: str) -> None:
    def fake_c22(root: Path, **_kwargs) -> Path:
        path = root / "outputs" / "reports" / "A3_ML_POST_ATTACH_RUNTIME_MONITOR_STATUS.json"
        _write_json(path, {"status": c22_status})
        return path

    def fake_c27(root: Path, **_kwargs) -> Path:
        path = root / "outputs" / "reports" / "A3_ML_RESEARCH_PREVIEW_RUNTIME_VERIFIER_STATUS.json"
        _write_json(
            path,
            {
                "status": c27_status,
                "runtime_evidence": {
                    "handoff_research_preview_ready_all_accounts": True,
                    "broker_shadow_tap_exists_all_accounts": c27_status
                    == "RESEARCH_PREVIEW_READ_PATH_CONFIRMED_ALL_ACCOUNTS",
                    "research_preview_read_path_confirmed_all_accounts": c27_status
                    == "RESEARCH_PREVIEW_READ_PATH_CONFIRMED_ALL_ACCOUNTS",
                },
            },
        )
        return path

    monkeypatch.setattr(module, "wait_for_post_attach_runtime_evidence", fake_c22)
    monkeypatch.setattr(module, "verify_research_preview_runtime_read_path", fake_c27)


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
