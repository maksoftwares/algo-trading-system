from __future__ import annotations

import hashlib
import json

from phase0.cli import build_parser, main


def test_cli_registers_required_commands():
    help_text = build_parser().format_help()

    assert "validate-config" in help_text
    assert "run-matrix" in help_text
    assert "normalize-bars" in help_text
    assert "import-required-bars" in help_text
    assert "generate-data-requirements" in help_text
    assert "generate-data-readiness" in help_text
    assert "generate-data-manifest" in help_text
    assert "generate-mt5-bar-presets" in help_text
    assert "generate-verdict" in help_text
    assert "generate-result-manifest" in help_text
    assert "generate-snapshot" in help_text
    assert "analyze-spread-logs" in help_text
    assert "generate-measured-cost-model" in help_text
    assert "generate-measured-cost-revalidation" in help_text
    assert "generate-measured-cost-sanity-check" in help_text
    assert "check-passive-spread-logger" in help_text
    assert "generate-independent-reproduction" in help_text
    assert "audit-true-holdout" in help_text
    assert "run-cpcv-validation" in help_text
    assert "run-reality-check" in help_text
    assert "register-research-hypothesis" in help_text
    assert "run-research-candidate-smoke" in help_text
    assert "run-research-matrix" in help_text
    assert "generate-fixed-notional-report" in help_text
    assert "second-ea-run-preflight" in help_text


def test_validate_config_command(project_root, capsys):
    exit_code = main(["--root", str(project_root), "validate-config"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Config OK" in captured.out


def test_cli_writes_run_log(project_root, tmp_path, capsys):
    root = tmp_path / "project"
    (root / "config").mkdir(parents=True)
    for path in (project_root / "config").glob("*.yaml"):
        (root / "config" / path.name).write_text(path.read_text(encoding="utf-8"), encoding="utf-8")

    exit_code = main(["--root", str(root), "validate-config"])

    assert exit_code == 0
    assert list((root / "outputs" / "logs").glob("phase0_run_*.log"))


def test_second_ea_run_preflight_cli_blocks_unsigned_partial_data(tmp_path, capsys):
    root = tmp_path / "project"
    _write_blocked_second_ea_preflight_inputs(root)

    exit_code = main(["--root", str(root), "second-ea-run-preflight"])

    captured = capsys.readouterr()
    report = root / "outputs" / "reports" / "SECOND_EA_RUN_PREFLIGHT.md"
    assert exit_code == 1
    assert "Second EA run preflight: BLOCKED" in captured.out
    assert report.exists()
    assert "Status: BLOCKED" in report.read_text(encoding="utf-8")


def test_second_ea_campaign_research_matrix_blocks_before_candidate_run(tmp_path, capsys):
    root = tmp_path / "project"
    _write_blocked_second_ea_preflight_inputs(root)

    exit_code = main(
        [
            "--root",
            str(root),
            "run-research-matrix",
            "--expert",
            "d1_momentum_h4_pullback_v1_fullhist",
            "--hypothesis-file",
            "docs/hypothesis_d1_momentum_h4_pullback_v1_fullhist.md",
        ]
    )

    captured = capsys.readouterr()
    report = root / "outputs" / "reports" / "SECOND_EA_RUN_PREFLIGHT.md"
    assert exit_code == 1
    assert "Second EA campaign result run blocked: BLOCKED" in captured.out
    assert "M1 data readiness is PARTIAL" in captured.out
    assert report.exists()


def _write_blocked_second_ea_preflight_inputs(root):
    reports_dir = root / "outputs" / "reports"
    reports_dir.mkdir(parents=True)
    (reports_dir / "SECOND_EA_NO_RUNTIME_TOUCH_AUDIT.md").write_text("Status: PASS\n", encoding="utf-8")
    (reports_dir / "SECOND_EA_DATA_EXTENSION_READINESS.md").write_text(
        "Overall status: PARTIAL\n",
        encoding="utf-8",
    )
    (reports_dir / "SECOND_EA_DATA_EXTENSION_READINESS.json").write_text(
        json.dumps({"overall_status": "PARTIAL", "readiness_content_sha256": "a" * 64}),
        encoding="utf-8",
    )
    docs_dir = root / "docs"
    docs_dir.mkdir()
    gate_doc = docs_dir / "PHASE0_LOWFREQ_GATE_SET_V1.md"
    gate_doc.write_text("# Gate Set\n\nStatus: LOCKED_FOR_SECOND_EA_RESEARCH\n", encoding="utf-8")
    (docs_dir / "PHASE0_LOWFREQ_GATE_SET_V1.sha256.json").write_text(
        json.dumps({"status": "LOCKED", "sha256": hashlib.sha256(gate_doc.read_bytes()).hexdigest()}),
        encoding="utf-8",
    )
    (docs_dir / "SECOND_EA_PARTIAL_DATA_OWNER_DECISION.md").write_text(
        "\n".join(
            [
                "decision_status: NOT_SIGNED",
                "owner_decision: NOT_ACCEPTED",
                f"accepted_readiness_content_sha256: {'a' * 64}",
            ]
        ),
        encoding="utf-8",
    )
