from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parents[2]


def test_overlay_is_locked_disarmed_and_midpoint_only() -> None:
    overlay = json.loads((ROOT / "config" / "overlay.json").read_text())
    assert not any(overlay["authorization"].values())
    assert overlay["v2_policy_overrides"] == {
        "maximum_prior_profit_factor_exclusive": 0.95
    }
    for name in ("parent_config", "dynamic_runner"):
        item = overlay[name]
        path = Path(item["path"])
        path = path if path.is_absolute() else REPO_ROOT / path
        assert hashlib.sha256(path.read_bytes()).hexdigest() == item["sha256"]
