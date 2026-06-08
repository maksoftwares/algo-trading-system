from __future__ import annotations

from phase2x_test_helpers import load_script, write_csv


def test_phase2x_owner_execution_status_passes_attached_demo_no_orders(tmp_path):
    root = tmp_path / "phase1"
    owner_root = tmp_path / "owner"
    write_csv(
        owner_root / "MQL5" / "Files" / "p2weakness_br_v1_startup_xauusd.csv",
        [
            {
                "startup_status": "ATTACHED_OWNER_AUTHORIZED_WEAKNESS_REVIEW_DEMO_EXECUTOR_ENABLED",
                "account_server": "Capital.ComMena-Demo",
                "account_login": "1025742",
                "symbol": "XAUUSD",
                "magic": "931000",
                "dry_run": "false",
                "broker_action_allowed": "true",
                "max_estimated_cost_R": "0.15",
                "max_family_open_positions": "1",
            }
        ],
    )
    write_csv(owner_root / "MQL5" / "Files" / "p2weakness_br_v1_signal_log_xauusd.csv", [{"account_login": "1025742"}])
    write_csv(owner_root / "MQL5" / "Files" / "p2weakness_br_v1_order_log_xauusd.csv", [])
    module = load_script("phase2x_owner_execution_status_report")

    payload = module.generate_phase2x_owner_execution_status_report(root, owner_exec_root=owner_root)

    assert payload["status"] == "PASS"
    assert payload["phase2x_demo_execution_attached"] is True
    assert payload["latest_startup"]["account_login"] == "****742"


def test_phase2x_owner_execution_status_fails_live_server_or_large_lot(tmp_path):
    root = tmp_path / "phase1"
    owner_root = tmp_path / "owner"
    write_csv(
        owner_root / "MQL5" / "Files" / "p2weakness_br_v1_startup_xauusd.csv",
        [
            {
                "startup_status": "ATTACHED_OWNER_AUTHORIZED_WEAKNESS_REVIEW_DEMO_EXECUTOR_ENABLED",
                "account_server": "Capital.ComMena-Live",
                "account_login": "1025742",
                "symbol": "XAUUSD",
                "magic": "931000",
                "dry_run": "false",
                "broker_action_allowed": "true",
                "max_estimated_cost_R": "0.15",
                "max_family_open_positions": "1",
            }
        ],
    )
    write_csv(owner_root / "MQL5" / "Files" / "p2weakness_br_v1_signal_log_xauusd.csv", [{"account_login": "1025742"}])
    write_csv(
        owner_root / "MQL5" / "Files" / "p2weakness_br_v1_order_log_xauusd.csv",
        [{"action": "ORDER_SEND_OK", "magic": "931000", "symbol": "XAUUSD", "volume": "0.02", "estimated_cost_R": "0.10"}],
    )
    module = load_script("phase2x_owner_execution_status_report")

    payload = module.generate_phase2x_owner_execution_status_report(root, owner_exec_root=owner_root)

    assert payload["status"] == "FAIL"
