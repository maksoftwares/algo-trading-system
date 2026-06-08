from __future__ import annotations

from phase2x_test_helpers import load_script, valid_owner_json, write_json, write_presets, write_status_md


def test_phase2x_preflight_does_not_require_canonical_phase2_pass(tmp_path):
    root = tmp_path / "phase1"
    reports = root / "outputs" / "reports"
    write_presets(root)
    write_status_md(reports / "PHASE2_READINESS_REPORT.md", "FAIL")
    write_status_md(reports / "COST_SUSPENDED_LIFECYCLE_REPORT.md", "COST_SUSPENDED_CANONICAL")
    for name in [
        "P2WEAKNESS_BR_V1_SOURCE_GOVERNANCE_PARITY.md",
        "P2WEAKNESS_BR_V1_MAGIC_COLLISION_AUDIT.md",
        "P2WEAKNESS_BR_V1_CLEAN_CLONE_RECONCILIATION.md",
    ]:
        write_status_md(reports / name, "PASS")
    write_json(reports / "PHASE2X_SAFE_DEFAULTS_REPORT.json", {"status": "PASS"})
    write_json(reports / "PHASE2X_OWNER_AUTHORIZATION_STATUS.json", {"status": "PASS", "masked_authorized_account_login": "****742"})
    write_json(reports / "PHASE2X_RUNTIME_CLEANUP_REPORT.json", {"status": "PASS"})
    write_json(reports / "PHASE2X_KILL_SWITCH_BLOCK_TEST_REPORT.json", {"status": "PASS"})
    write_json(reports / "P2WEAKNESS_BR_V1_RUNTIME_ATTACHMENT_AUDIT.json", {"status": "PASS"})
    preset = root / "local" / "Phase2WeaknessBreakoutRetestExecutor.owner_authorized_demo_xauusd.local.set"
    preset.parent.mkdir(parents=True)
    preset.write_text(
        "\n".join(
            [
                "InpMagicNumber=931000",
                "InpFixedLot=0.01",
                "InpMaxOrdersPerDay=2",
                "InpMaxAccountOrdersPerDay=3",
                "InpMaxFamilyOpenPositions=1",
                "InpMaxEstimatedCostR=0.15",
                "InpMaxMeasuredSpreadPoints=75.0",
                "InpTargetSymbol=XAUUSD",
                "InpExpectedServerMarker=Demo",
            ]
        ),
        encoding="utf-8",
    )
    module = load_script("phase2x_demo_preflight")

    payload = module.generate_phase2x_demo_preflight(root, local_preset=preset)

    assert payload["status"] == "PASS"
    assert payload["canonical_phase2_authorized"] is False
    assert any(check["name"] == "canonical_phase2_readiness_is_fail_or_blocked" and check["status"] == "PASS" for check in payload["checks"])


def test_phase2x_preflight_pending_without_owner_preset(tmp_path):
    root = tmp_path / "phase1"
    reports = root / "outputs" / "reports"
    write_presets(root)
    write_status_md(reports / "PHASE2_READINESS_REPORT.md", "FAIL")
    module = load_script("phase2x_demo_preflight")

    payload = module.generate_phase2x_demo_preflight(root)

    assert payload["status"] in {"PENDING", "FAIL"}
    assert any(check["status"] == "PENDING_OWNER_ACTION" for check in payload["checks"])
