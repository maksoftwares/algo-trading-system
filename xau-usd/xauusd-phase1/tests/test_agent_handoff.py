from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
AGENT = REPO_ROOT / "agent.md"


def test_agent_handoff_points_changing_runtime_metrics_to_canonical_reports():
    text = AGENT.read_text(encoding="utf-8")

    assert "Current changing Phase 1 runtime, soak, and would-signal counters must be read from" in text
    assert "Current changing measured-cost counters must be read from" in text
    assert "Current Phase 2 readiness must be read from" in text
    assert "Current changing Phase 3 metrics must be read from" in text
    assert "do not copy decision-row, soak, health, would-signal, or acceptance counters from this handoff" in text


def test_agent_handoff_does_not_pin_stale_current_phase1_counts():
    text = AGENT.read_text(encoding="utf-8")

    stale_current_phrases = (
        "Latest status summary shows 816 decision rows",
        "Current v0.7 would-signal report has 85 dry-run would-signal rows",
        "Latest would-signal status: PASS with 81 rows",
        "Latest decision row confirms",
    )
    for phrase in stale_current_phrases:
        assert phrase not in text
