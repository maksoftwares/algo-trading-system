from __future__ import annotations

from datetime import datetime, timedelta, timezone

from phase2x_test_helpers import load_script, valid_owner_json


def test_phase2x_owner_authorization_valid_strict_json_passes():
    common = load_script("phase2x_common")

    checks = common.validate_owner_authorization(valid_owner_json())

    assert all(check["status"] == "PASS" for check in checks)


def test_phase2x_owner_authorization_rejects_bad_values():
    common = load_script("phase2x_common")
    expired = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat().replace("+00:00", "Z")

    checks = common.validate_owner_authorization(
        valid_owner_json(
            expires_at_utc=expired,
            authorized_account_login="",
            authorized_server_marker="Live",
            authorized_magic=930101,
            fixed_lot=0.02,
            max_orders_per_day=4,
            max_family_open_positions=2,
            max_estimated_cost_r=0.16,
            experimental_authorization_token="WRONG",
        )
    )

    failed = {check["name"] for check in checks if check["status"] == "FAIL"}
    assert "authorized_account_login_present" in failed
    assert "server_marker_demo_or_practice" in failed
    assert "authorized_magic_931000" in failed
    assert "fixed_lot_lte_0_01" in failed
    assert "max_orders_per_day_lte_3" in failed
    assert "max_family_open_positions_eq_1" in failed
    assert "max_estimated_cost_r_lte_0_15" in failed
    assert "experimental_authorization_token" in failed
    assert "authorization_not_expired" in failed
