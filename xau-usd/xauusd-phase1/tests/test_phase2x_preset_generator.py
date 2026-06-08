from __future__ import annotations

import json
from pathlib import Path

from phase2x_test_helpers import load_script, valid_owner_json, write_json, write_presets


def test_phase2x_preset_generator_writes_only_local_strict_preset(tmp_path):
    root = tmp_path / "phase1"
    write_presets(root)
    owner_json = root / "local" / "phase2x_owner_authorization.local.json"
    output = root / "local" / "Phase2WeaknessBreakoutRetestExecutor.owner_authorized_demo_xauusd.local.set"
    write_json(owner_json, valid_owner_json())
    module = load_script("phase2x_make_owner_authorized_preset")

    payload = module.make_owner_authorized_preset(root, owner_json=owner_json, output=output)
    text = output.read_text(encoding="utf-8")

    assert payload["status"] == "PASS"
    assert "InpBrokerActionAllowed=true" in text
    assert "InpDryRunOnly=false" in text
    assert "InpMagicNumber=931000" in text
    assert "InpFixedLot=0.01" in text
    assert "InpMaxFamilyOpenPositions=1" in text
    assert "InpMaxEstimatedCostR=0.15" in text


def test_phase2x_preset_generator_rejects_committed_output_path(tmp_path):
    root = tmp_path / "phase1"
    write_presets(root)
    owner_json = root / "local" / "phase2x_owner_authorization.local.json"
    bad_output = root / "mt5" / "Presets" / "bad.owner_authorized_demo_xauusd.local.set"
    write_json(owner_json, valid_owner_json())
    module = load_script("phase2x_make_owner_authorized_preset")

    payload = module.make_owner_authorized_preset(root, owner_json=owner_json, output=bad_output)

    assert payload["status"] == "FAIL"
    assert not bad_output.exists()
