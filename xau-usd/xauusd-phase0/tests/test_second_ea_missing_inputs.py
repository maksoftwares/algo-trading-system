from __future__ import annotations

from pathlib import Path

from phase0.second_ea_missing_inputs import (
    REQUIRED_SOURCE_DOCUMENTS,
    find_required_source_documents,
    generate_missing_inputs_report,
)


def test_missing_inputs_report_finds_all_exact_docs(project_root: Path):
    # SECOND_EA_RESEARCH_LANES_DOC_REVIEW_2026_06_10.md was authored on 2026-06-10
    # (reviewer takeover), so every required exact-name input now resolves.
    # (This test previously pinned the state where that file was missing.)
    report = generate_missing_inputs_report(project_root)

    assert report.status == "PASS"
    assert report.missing_documents == ()
    assert {path.name for path in report.found_paths} == set(REQUIRED_SOURCE_DOCUMENTS)
    text = report.report_path.read_text(encoding="utf-8")
    assert "SECOND_EA_RESEARCH_LANES_DOC_REVIEW_2026_06_10.md" in text


def test_required_source_document_finder_deduplicates_repo_and_downloads(tmp_path: Path):
    repo = tmp_path / "repo"
    phase0_docs = repo / "xau-usd" / "xauusd-phase0" / "docs"
    phase0_docs.mkdir(parents=True)
    downloads = tmp_path / "Downloads"
    downloads.mkdir()
    (phase0_docs / "TRUE_HOLDOUT_POLICY.md").write_text("repo", encoding="utf-8")
    (downloads / "TRUE_HOLDOUT_POLICY.md").write_text("downloads duplicate", encoding="utf-8")
    (downloads / "CODEX_BRIEF_SECOND_EA_RESEARCH_LANES_2026_06_10.md").write_text(
        "brief",
        encoding="utf-8",
    )

    found = find_required_source_documents(repo, downloads)

    assert found["TRUE_HOLDOUT_POLICY.md"] == phase0_docs / "TRUE_HOLDOUT_POLICY.md"
    assert found["CODEX_BRIEF_SECOND_EA_RESEARCH_LANES_2026_06_10.md"] == (
        downloads / "CODEX_BRIEF_SECOND_EA_RESEARCH_LANES_2026_06_10.md"
    )
