from __future__ import annotations

import csv
from pathlib import Path

from phase0.config import ProjectConfig
from phase0.hashing import sha256_file
from phase0.research_smoke import run_research_candidate_smoke


def test_research_candidate_smoke_requires_disabled_hash_locked_candidate(tmp_path: Path):
    docs = tmp_path / "docs"
    hashes = tmp_path / "outputs" / "hashes"
    docs.mkdir(parents=True)
    hashes.mkdir(parents=True)
    hypothesis = docs / "hypothesis_squeeze_breakout_long_v0.md"
    hypothesis.write_text(_complete_hypothesis_text(), encoding="utf-8")
    with (hashes / "research_hypothesis_hash_manifest.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=(
                "expert",
                "hypothesis_file",
                "sha256",
                "registered_at_utc",
                "file_size_bytes",
                "git_commit_if_available",
            ),
        )
        writer.writeheader()
        writer.writerow(
            {
                "expert": "squeeze_breakout_long_v0",
                "hypothesis_file": "docs/hypothesis_squeeze_breakout_long_v0.md",
                "sha256": sha256_file(hypothesis),
                "registered_at_utc": "2026-05-22T00:00:00+00:00",
                "file_size_bytes": hypothesis.stat().st_size,
                "git_commit_if_available": "",
            }
        )
    config = ProjectConfig(tmp_path, {}, {}, {}, {}, {})

    output = run_research_candidate_smoke(
        config,
        expert="squeeze_breakout_long_v0",
        hypothesis_file="docs/hypothesis_squeeze_breakout_long_v0.md",
    )

    assert output.status == "PASS"
    assert output.signal_count > 0
    assert not output.phase0_result_run_allowed
    assert output.report_path.exists()
    assert output.manifest_path.exists()


def _complete_hypothesis_text() -> str:
    return "\n".join(
        [
            "# Squeeze Breakout Long v0 Hypothesis",
            "",
            "Hypothesis date: 2026-05-22",
            "Hypothesis version: v0",
            "Author / owner: maksoftwares / Codex",
            "Expected trade count per year: 35-140",
            "Expected cost-adjusted PF: 1.10-1.45",
            "Expected losing-month percentage: 35%-55%",
            "Expected worst single month: -8R to -16R",
            "Expected max consecutive zero months: 2",
            "Expected R-multiple distribution: many small losses, fewer 1.5R wins",
            "",
            "## Mechanical Definition",
            "Long-only compression breakout using fixed completed-candle ranges.",
            "",
            "## Expected Behavior",
            "Moderate frequency and positive skew after compression releases.",
            "",
            "## Why This Hypothesis Should Exist",
            "Gold can reprice sharply after volatility compression.",
            "",
            "## What Would Falsify It",
            "Failure of the existing Phase 0 gates falsifies this candidate.",
            "",
        ]
    )
