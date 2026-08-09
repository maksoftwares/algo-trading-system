from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "config" / "frozen_us500_v41_shared_demo_deployment.json"
SPEC = importlib.util.spec_from_file_location(
    "verify_us500_git_deployment", ROOT / "verify_us500_git_deployment.py"
)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_us500_deployment_manifest_hashes_every_rollback_artifact() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))

    assert manifest["schema_version"] == "us500_v41_shared_demo_deployment_v2"
    assert manifest["change_class"] == "observability_only"
    assert manifest["pre_observability_strategy_source_sha256"] == (
        "91926cd40f33840096478471ab806b8f2b3e91e10775e721eaaf7613bcbb40b7"
    )
    assert manifest["account_login"] == 1033030
    assert manifest["server"] == "Capital.ComMena-Demo"
    assert manifest["symbol"] == "US500"
    assert manifest["period"] == "M5"
    assert manifest["live_orders_authorized"] is False
    for relative, expected in manifest["artifacts"].items():
        actual = hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()
        assert actual == expected


def test_us500_verifier_is_read_only_and_requires_a_resolved_commit() -> None:
    source = (ROOT / "verify_us500_git_deployment.py").read_text(encoding="utf-8")

    assert "rev-parse" in source
    assert "^{{commit}}" in source
    assert '"git", "-C", str(REPO), "show"' in source
    assert "order_send" not in source.lower()
    assert "OrderSend" not in source
