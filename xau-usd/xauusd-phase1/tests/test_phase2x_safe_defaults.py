from __future__ import annotations

from phase2x_test_helpers import load_script, write_presets


def test_phase2x_safe_defaults_pass_for_non_executing_committed_presets(tmp_path):
    root = tmp_path / "phase1"
    write_presets(root)
    module = load_script("phase2x_validate_safe_defaults")

    payload = module.generate_phase2x_safe_defaults_report(root)

    assert payload["status"] == "PASS"
    assert all(check["status"] == "PASS" for check in payload["checks"])


def test_phase2x_safe_defaults_fail_if_committed_set_enables_broker_action(tmp_path):
    root = tmp_path / "phase1"
    write_presets(root, unsafe_committed=True)
    module = load_script("phase2x_validate_safe_defaults")

    payload = module.generate_phase2x_safe_defaults_report(root)

    assert payload["status"] == "FAIL"
    assert any(check["name"] == "no_committed_executing_set" and check["status"] == "FAIL" for check in payload["checks"])
