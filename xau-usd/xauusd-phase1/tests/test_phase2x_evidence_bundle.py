from __future__ import annotations

import zipfile

from phase2x_test_helpers import load_script, write_csv, write_status_md


def test_phase2x_evidence_bundle_masks_logs_and_excludes_local_preset_contents(tmp_path):
    root = tmp_path / "repo" / "xau-usd" / "xauusd-phase1"
    reports = root / "outputs" / "reports"
    reports.mkdir(parents=True)
    (root.parent.parent / ".git").mkdir(parents=True)
    write_status_md(reports / "PHASE2X_DEMO_PREFLIGHT_REPORT.md", "PENDING")
    local_preset = root / "local" / "Phase2WeaknessBreakoutRetestExecutor.owner_authorized_demo_xauusd.local.set"
    local_preset.parent.mkdir(parents=True)
    local_preset.write_text("SECRET_ACCOUNT=1025742\n", encoding="utf-8")
    order_log = tmp_path / "order.csv"
    write_csv(order_log, [{"timestamp_broker": "2026.06.08 10:00:00", "account_login": "1025742", "action": "GUARD_BLOCK"}])
    module = load_script("phase2x_generate_evidence_bundle")

    payload = module.generate_phase2x_evidence_bundle(root, order_log=order_log, signal_log=order_log, startup_log=order_log, local_preset=local_preset)

    assert payload["status"] == "PASS"
    with zipfile.ZipFile(payload["zip_path"], "r") as archive:
        names = archive.namelist()
        assert "manifest/private_local_preset_sha256.txt" in names
        assert not any(name.endswith(".local.set") for name in names)
        masked = archive.read("logs/order_log_masked.csv").decode("utf-8")
        assert "1025742" not in masked
        assert "****742" in masked
