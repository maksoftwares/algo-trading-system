from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path


PHASE1_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PHASE1_ROOT.parents[1]


def test_a3_net_cost_falsification_manifest_matches_committed_head_when_git_available():
    module = _load_module()
    try:
        subprocess.check_call(
            ["git", "cat-file", "-e", "HEAD^{commit}"],
            cwd=REPO_ROOT,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except (FileNotFoundError, subprocess.CalledProcessError):
        return

    result = module.verify_manifest(REPO_ROOT, git_ref="HEAD")

    assert result.status == "PASS"
    assert result.checked_files == 4
    assert result.mismatches == ()


def _load_module():
    path = PHASE1_ROOT / "scripts" / "verify_a3_net_cost_falsification_manifest.py"
    spec = importlib.util.spec_from_file_location("verify_a3_net_cost_falsification_manifest", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module
