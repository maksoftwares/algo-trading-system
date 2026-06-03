from __future__ import annotations

import csv
import subprocess
import sys
from pathlib import Path

from phase0r.hypothesis_lock import sha256_file
from phase0r.refinement import (
    REPORT_FILENAMES,
    break_even_win_rate,
    cost_r_bucket,
    dedupe_family_events,
    expectancy_after_cost,
    generate_all_refinement_reports,
    guard_no_locked_candidate_mutations,
    load_refinement_data,
    stop_distance_bucket,
)


ROOT = Path(__file__).resolve().parents[1]


def test_win_rate_expectancy_formulas_use_cost():
    assert break_even_win_rate(1.5, -1.0) == 0.4
    assert round(expectancy_after_cost(0.5, 1.5, 1.0, 0.10), 6) == 0.15


def test_cost_and_stop_bucket_boundaries():
    assert cost_r_bucket(None) == "unknown"
    assert cost_r_bucket(0.15) == "<=0.15R"
    assert cost_r_bucket(0.30) == "0.15R_to_0.30R"
    assert cost_r_bucket(0.50) == "0.30R_to_0.50R"
    assert cost_r_bucket(0.51) == ">0.50R"

    assert stop_distance_bucket(None) == "unknown"
    assert stop_distance_bucket(249.99) == "<250"
    assert stop_distance_bucket(250) == "250_to_374"
    assert stop_distance_bucket(375) == "375_to_499"
    assert stop_distance_bucket(500) == "500_plus"


def test_duplicate_family_detection_keeps_primary_candidate():
    events = [
        {
            "candidate": "swing_breakout_retest_v0",
            "family": "breakout_retest_family",
            "status": "ACCEPTED",
            "symbol": "XAUUSD",
            "bar": "2026-06-02 10:00",
            "direction": "LONG",
            "level": "4520.00",
            "cost_r": 0.10,
            "is_duplicate": False,
            "duplicate_key": "",
            "duplicate_role": "",
        },
        {
            "candidate": "breakout_retest",
            "family": "breakout_retest_family",
            "status": "ACCEPTED",
            "symbol": "XAUUSD",
            "bar": "2026-06-02 10:00",
            "direction": "LONG",
            "level": "4520.00",
            "cost_r": 0.12,
            "is_duplicate": False,
            "duplicate_key": "",
            "duplicate_role": "",
        },
    ]

    deduped, details = dedupe_family_events(events)

    assert len(deduped) == 1
    assert len(details) == 1
    assert deduped[0]["candidate"] == "breakout_retest"
    assert details[0]["duplicates"][0]["candidate"] == "swing_breakout_retest_v0"


def test_locked_candidate_guard_detects_hash_mutation(tmp_path: Path):
    root = tmp_path / "phase0r"
    hypothesis = root / "hypotheses" / "hypothesis_sample_v0.md"
    manifest = root / "outputs" / "hypothesis_hash_manifest.csv"
    hypothesis.parent.mkdir(parents=True)
    manifest.parent.mkdir(parents=True)
    hypothesis.write_text("Expert candidate ID: sample_v0\nStatus: LOCKED\n", encoding="utf-8")
    _write_manifest(manifest, hypothesis, root, sha256_file(hypothesis))

    assert guard_no_locked_candidate_mutations(root, manifest) == []

    hypothesis.write_text("Expert candidate ID: sample_v0\nStatus: LOCKED\nChanged: true\n", encoding="utf-8")
    errors = guard_no_locked_candidate_mutations(root, manifest)

    assert errors
    assert "locked hypothesis hash changed" in errors[0]


def test_generate_all_reports_with_synthetic_demo_logs(tmp_path: Path):
    data = load_refinement_data(tmp_path / "phase0r", synthetic_sample=True)
    output = generate_all_refinement_reports(data)

    expected_names = {
        REPORT_FILENAMES["performance"],
        REPORT_FILENAMES["deduped"],
        REPORT_FILENAMES["expectancy"],
        REPORT_FILENAMES["loss_quality"],
        REPORT_FILENAMES["cost_bucket"],
        REPORT_FILENAMES["session_bucket"],
        REPORT_FILENAMES["stop_bucket"],
        REPORT_FILENAMES["duplicate_family"],
        REPORT_FILENAMES["vnext"],
        REPORT_FILENAMES["promotion_blockers"],
    }

    generated_names = {path.name for path in output.report_paths}
    assert expected_names == generated_names
    for path in output.report_paths:
        assert path.exists()
        assert "REFINEMENT_RESEARCH_ONLY" in path.read_text(encoding="utf-8") or "DRAFT_UNREGISTERED" in path.read_text(
            encoding="utf-8"
        )
    assert output.manifest_path.exists()


def test_required_scripts_run_on_synthetic_sample(tmp_path: Path):
    scripts = [
        "demo_ea_performance_review.py",
        "demo_ea_deduped_review.py",
        "ea_win_rate_expectancy_report.py",
        "ea_loss_quality_report.py",
        "ea_cost_r_bucket_report.py",
        "ea_stop_distance_bucket_report.py",
        "generate_vnext_candidate_proposals.py",
    ]
    for script in scripts:
        result = subprocess.run(
            [
                sys.executable,
                str(ROOT / "scripts" / script),
                "--root",
                str(tmp_path / "phase0r"),
                "--synthetic-sample",
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, result.stderr
        assert result.stdout.strip().endswith(".md")


def _write_manifest(manifest: Path, hypothesis: Path, root: Path, digest: str) -> None:
    with manifest.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "candidate_id",
                "version",
                "status",
                "hypothesis_path",
                "sha256",
                "registered_at_utc",
                "registered_by",
                "notes",
            ],
        )
        writer.writeheader()
        writer.writerow(
            {
                "candidate_id": "sample_v0",
                "version": "v0",
                "status": "LOCKED",
                "hypothesis_path": str(hypothesis.relative_to(root)).replace("\\", "/"),
                "sha256": digest,
                "registered_at_utc": "2026-06-02T00:00:00Z",
                "registered_by": "test",
                "notes": "locked test row",
            }
        )
