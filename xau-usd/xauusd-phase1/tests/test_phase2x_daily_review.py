from __future__ import annotations

import json

from phase2x_test_helpers import load_script, write_csv


def test_phase2x_daily_review_pending_on_empty_logs(tmp_path):
    root = tmp_path / "phase1"
    order_log = tmp_path / "order.csv"
    write_csv(order_log, [])
    module = load_script("phase2x_daily_demo_review")

    payload = module.generate_phase2x_daily_demo_review(root, review_date="2026_06_08", order_log=order_log)

    assert payload["status"] == "PENDING"


def test_phase2x_daily_review_fails_on_wrong_magic_and_lot(tmp_path):
    root = tmp_path / "phase1"
    order_log = tmp_path / "order.csv"
    write_csv(
        order_log,
        [
            {
                "timestamp_broker": "2026.06.08 10:00:00",
                "action": "ORDER_SEND_OK",
                "magic": "930101",
                "symbol": "XAUUSD",
                "lot": "0.02",
                "family_open_exposure": "2",
                "estimated_cost_R": "0.20",
                "account_server": "Capital.ComMena-Live",
            }
        ],
    )
    module = load_script("phase2x_daily_demo_review")

    payload = module.generate_phase2x_daily_demo_review(root, review_date="2026_06_08", order_log=order_log)

    assert payload["status"] == "FAIL"
    assert payload["continue_tomorrow"] == "NO"


def test_phase2x_daily_review_excludes_pre_owner_authorization_legacy_rows(tmp_path):
    root = tmp_path / "phase1"
    owner_json = root / "local" / "phase2x_owner_authorization.local.json"
    owner_json.parent.mkdir(parents=True)
    owner_json.write_text(json.dumps({"approved_at_utc": "2026-06-08T11:18:36Z"}), encoding="utf-8")
    order_log = tmp_path / "order.csv"
    write_csv(
        order_log,
        [
            {
                "timestamp_utc": "2026.06.08 08:54:56",
                "action": "GUARD_BLOCK",
                "magic": "930101",
                "symbol": "XAUUSD",
                "lot": "0.00",
                "family_open_exposure": "2",
                "estimated_cost_R": "0.10",
                "account_server": "Capital.ComMena-Demo",
            }
        ],
    )
    module = load_script("phase2x_daily_demo_review")

    payload = module.generate_phase2x_daily_demo_review(root, review_date="2026_06_08", order_log=order_log, owner_json=owner_json)

    assert payload["status"] == "PENDING"
    assert payload["legacy_pre_authorization_rows"] == 1
    assert payload["order_summary"]["rows"] == 0


def test_phase2x_daily_review_fails_on_post_owner_authorization_wrong_magic(tmp_path):
    root = tmp_path / "phase1"
    owner_json = root / "local" / "phase2x_owner_authorization.local.json"
    owner_json.parent.mkdir(parents=True)
    owner_json.write_text(json.dumps({"approved_at_utc": "2026-06-08T11:18:36Z"}), encoding="utf-8")
    order_log = tmp_path / "order.csv"
    write_csv(
        order_log,
        [
            {
                "timestamp_utc": "2026.06.08 11:20:00",
                "action": "ORDER_SEND_OK",
                "magic": "930101",
                "symbol": "XAUUSD",
                "lot": "0.01",
                "family_open_exposure": "1",
                "estimated_cost_R": "0.10",
                "account_server": "Capital.ComMena-Demo",
            }
        ],
    )
    module = load_script("phase2x_daily_demo_review")

    payload = module.generate_phase2x_daily_demo_review(root, review_date="2026_06_08", order_log=order_log, owner_json=owner_json)

    assert payload["status"] == "FAIL"
    assert payload["legacy_pre_authorization_rows"] == 0
