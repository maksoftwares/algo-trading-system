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
    assert {".py", ".ps1", ".bat", ".cmd", ".yaml", ".yml", ".toml", ".cfg"}.issubset(
        set(audit.SCAN_SUFFIXES)
    )


def test_phase1_arming_audit_fails_unpolicy_gated_a3_script(tmp_path: Path) -> None:
    audit = load_script("audit_phase1_arming")
    script = tmp_path / "scripts" / "attach_a3_bad.py"
    script.parent.mkdir(parents=True)
    script.write_text(
        "\n".join(
            [
                "ACCOUNT_LOGIN = '1033669'",
                "ARMED_INPUTS = {",
                '    "InpDryRunOnly": "false",',
                '    "InpBrokerActionAllowed": "true",',
                "}",
            ]
        ),
        encoding="utf-8",
    )

    findings = audit.audit_phase1_arming(tmp_path)

    assert any(item.term == "script_policy_missing:explicit_apply_flag" for item in findings)
    assert any(item.term == "script_policy_missing:owner_packet_hash_required" for item in findings)
    assert any(item.term == "script_policy_missing:current_a3_pause_ack_required" for item in findings)


def test_phase1_arming_audit_allows_policy_gated_a3_script(tmp_path: Path) -> None:
    audit = load_script("audit_phase1_arming")
    script = tmp_path / "scripts" / "attach_a3_policy_gated.py"
    script.parent.mkdir(parents=True)
    script.write_text(
        "\n".join(
            [
                "ACCOUNT_LOGIN = '1033669'",
                "ARMED_INPUTS = {",
                '    "InpDryRunOnly": "false",',
                '    "InpBrokerActionAllowed": "true",',
                "}",
                "parser.add_argument('--apply', action='store_true')",
                "parser.add_argument('--owner-packet', dest='owner_packet')",
                "parser.add_argument('--owner-packet-sha256', dest='owner_packet_sha256')",
                "parser.add_argument('--review-hash', dest='review_hash')",
                "parser.add_argument('--acknowledge-current-a3-pause', dest='acknowledge_current_a3_pause')",
                "if not args.apply:",
                "    raise SystemExit(0)",
                "def broker_a3_exposure_state(): pass",
                "def backup_profile(): pass",
                "required_pause = 'A3_ENTRY_LANES_PAUSED'",
            ]
        ),
        encoding="utf-8",
    )

    assert audit.audit_phase1_arming(tmp_path) == []
