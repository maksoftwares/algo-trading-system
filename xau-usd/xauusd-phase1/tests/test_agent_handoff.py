from __future__ import annotations

import re
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
AGENT_MD = REPO_ROOT / "agent.md"


def test_agent_handoff_points_changing_metrics_to_canonical_reports():
    text = AGENT_MD.read_text(encoding="utf-8")

    assert "Current changing Phase 1 runtime, soak, and would-signal counters must be read from" in text
    assert "Current changing measured-cost counters must be read from" in text
    assert "Current Phase 2 readiness must be read from" in text

    stale_current_patterns = (
        r"Latest refreshed runtime snapshot.*decision rows",
        r"Latest soak evidence:",
        r"Latest would-signal observer conflict counts:",
        r"Latest measured cost model snapshot.*fresh rows",
    )
    for pattern in stale_current_patterns:
        assert re.search(pattern, text, flags=re.IGNORECASE | re.DOTALL) is None


def test_agent_handoff_marks_old_numeric_snapshots_as_historical():
    text = AGENT_MD.read_text(encoding="utf-8")

    assert "Historical 2026-05-27 refreshed runtime snapshot" in text
    assert "Historical 2026-05-27 soak evidence" in text
    assert "Historical 2026-05-27 would-signal observer conflict counts" in text
