from __future__ import annotations

from phase2x_test_helpers import load_script, write_json


def test_phase2x_runtime_cleanup_blocks_old_open_exposure(tmp_path):
    root = tmp_path / "phase1"
    reports = root / "outputs" / "reports"
    write_json(
        reports / "P2WEAKNESS_BR_V1_RUNTIME_ATTACHMENT_AUDIT.json",
        {
            "reviewer_questions": {"is_any_old_930101_ea_still_attached": "NO"},
            "old_magic_930101": {"open_positions": 1, "open_orders": 0},
            "hardened_magic_931000": {"deployed_source_hardened": False},
            "open_exposure_audit": {"positions": [{"magic": 930101}], "orders": []},
        },
    )
    module = load_script("phase2x_runtime_cleanup_report")

    payload = module.generate_phase2x_runtime_cleanup_report(root)

    assert payload["status"] == "FAIL"
    assert any(check["name"] == "old_magic_930101_positions_closed_or_absent" and check["status"] == "FAIL" for check in payload["checks"])
