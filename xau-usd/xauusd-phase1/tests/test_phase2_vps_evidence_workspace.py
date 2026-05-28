from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_prepare_vps_evidence_workspace_script_preserves_verified_evidence():
    text = (ROOT / "scripts" / "prepare_phase2_vps_evidence_workspace.ps1").read_text(encoding="utf-8")

    assert "vps_ntp_sync.template.txt" in text
    assert "vps_backup_config.template.txt" in text
    assert "vps_rdp_recovery.template.txt" in text
    assert "vps_periodic_task.template.txt" in text
    assert "SKIPPED_VERIFIED" in text
    assert "AllowOverwriteVerified" in text
    assert "vps_evidence_workspace_manifest.json" in text
    assert "System.Text.UTF8Encoding($false)" in text
    assert "[System.IO.File]::WriteAllText" in text
    assert "does not authorize Phase 2, demo trading, broker execution, live capital, or MT5 runtime changes" in text
