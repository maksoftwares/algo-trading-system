from __future__ import annotations

from phase2x_test_helpers import load_script, write_csv


def test_phase2x_kill_switch_report_pending_without_block_evidence(tmp_path):
    root = tmp_path / "phase1"
    order_log = tmp_path / "order.csv"
    startup_log = tmp_path / "startup.csv"
    write_csv(order_log, [])
    write_csv(startup_log, [])
    module = load_script("phase2x_kill_switch_block_test_report")

    payload = module.generate_phase2x_kill_switch_block_test_report(root, order_log=order_log, startup_log=startup_log)

    assert payload["status"] == "PENDING"


def test_phase2x_kill_switch_report_passes_on_startup_refusal(tmp_path):
    root = tmp_path / "phase1"
    order_log = tmp_path / "order.csv"
    startup_log = tmp_path / "startup.csv"
    write_csv(order_log, [])
    write_csv(startup_log, [{"startup_status": "REFUSED_KILL_SWITCH_ACTIVE"}])
    module = load_script("phase2x_kill_switch_block_test_report")

    payload = module.generate_phase2x_kill_switch_block_test_report(root, order_log=order_log, startup_log=startup_log)

    assert payload["status"] == "PASS"
    assert payload["startup_refusal_rows"] == 1


def test_phase2x_kill_switch_report_fails_on_order_send_during_kill(tmp_path):
    root = tmp_path / "phase1"
    order_log = tmp_path / "order.csv"
    startup_log = tmp_path / "startup.csv"
    write_csv(order_log, [{"guard_reason": "kill_switch_active", "action": "ORDER_SEND_OK"}])
    write_csv(startup_log, [])
    module = load_script("phase2x_kill_switch_block_test_report")

    payload = module.generate_phase2x_kill_switch_block_test_report(root, order_log=order_log, startup_log=startup_log)

    assert payload["status"] == "FAIL"
