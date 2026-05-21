from __future__ import annotations

from pathlib import Path

from phase0.config import ProjectConfig
from phase0.research_hypotheses import register_research_hypothesis


def test_register_research_hypothesis_writes_manifest(tmp_path: Path):
    docs = tmp_path / "docs"
    docs.mkdir()
    hypothesis = docs / "hypothesis_squeeze_breakout_long_v0.md"
    hypothesis.write_text(
        "\n".join(
            [
                "# Squeeze Breakout Long v0 Hypothesis",
                "",
                "Hypothesis date: 2026-05-22",
                "Hypothesis version: v0",
                "Author / owner: maksoftwares / Codex",
                "Expected trade count per year: 30-120",
                "Expected cost-adjusted PF: 1.10-1.45",
                "Expected losing-month percentage: 35%-55%",
                "Expected worst single month: -8R to -14R",
                "Expected max consecutive zero months: 2",
                "Expected R-multiple distribution: many small losses, fewer 1.5R wins",
                "",
                "## Mechanical Definition",
                "Long-only compression breakout using fixed ranges and completed candles.",
                "",
                "## Expected Behavior",
                "Moderate frequency and positive skew after compression release.",
                "",
                "## Why This Hypothesis Should Exist",
                "Gold can reprice sharply after volatility compression.",
                "",
                "## What Would Falsify It",
                "Low trade count, weak PF, or concentration above the Phase 0 thresholds.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    config = ProjectConfig(tmp_path, {}, {}, {}, {}, {})

    output = register_research_hypothesis(
        config,
        expert="squeeze_breakout_long_v0",
        hypothesis_file="docs/hypothesis_squeeze_breakout_long_v0.md",
    )

    assert output.status == "REGISTERED"
    assert output.manifest_path.exists()
    assert output.report_path.exists()
    assert not output.phase0_result_run_allowed
