from __future__ import annotations

from pathlib import Path

from phase2x_test_helpers import ROOT, load_script


def test_phase1_arming_audit_passes_current_repo_artifacts() -> None:
    audit = load_script("audit_phase1_arming")

    assert audit.audit_phase1_arming(ROOT) == []


def test_phase1_arming_audit_fails_committed_armed_preset(tmp_path: Path) -> None:
    audit = load_script("audit_phase1_arming")
    preset = tmp_path / "mt5" / "Presets" / "bad.set"
    preset.parent.mkdir(parents=True)
    preset.write_text(
        "\n".join(
            [
                "InpDryRunOnly=false",
                "InpBrokerActionAllowed=true",
                "InpExperimentalAuthorizationToken=OWNER_SECRET",
            ]
        ),
        encoding="utf-8",
    )

    findings = audit.audit_phase1_arming(tmp_path)

    assert any(item.term == "InpDryRunOnly=false" for item in findings)
    assert any(item.term == "InpBrokerActionAllowed=true" for item in findings)
    assert any(item.term == "InpExperimentalAuthorizationToken=nonblank" for item in findings)


def test_phase1_arming_scan_paths_cover_executable_artifact_roots() -> None:
    audit = load_script("audit_phase1_arming")

    assert {"mt5", "scripts", "config", "deployment", "deploy"}.issubset(set(audit.SCAN_ROOT_PARTS))
    assert {".set", ".ini", ".chr", ".args", ".env", ".json"}.issubset(set(audit.SCAN_SUFFIXES))
