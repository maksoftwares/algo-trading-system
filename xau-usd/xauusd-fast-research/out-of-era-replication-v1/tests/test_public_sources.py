from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from public_sources import parse_bls_nfp_archive  # noqa: E402


def test_bls_parser_prefers_html_and_filters_window() -> None:
    html = """
    <a href="/news.release/archives/empsit_01082010.pdf">December 2009</a>
    <a href="/news.release/archives/empsit_01082010.htm">December 2009 HTML</a>
    <a href="/news.release/archives/empsit_02052010.htm">January 2010</a>
    <a href="/news.release/archives/empsit_07082016.htm">June 2016</a>
    """
    rows = parse_bls_nfp_archive(
        html,
        "https://www.bls.gov/bls/news-release/empsit.htm",
        "2010-01-01",
        "2016-07-01",
    )
    assert [row["date"] for row in rows] == ["2010-01-08", "2010-02-05"]
    assert rows[0]["primaryUrl"].endswith("empsit_01082010.htm")
    assert rows[0]["release_time_rule"] == "08:30 America/New_York"


def test_bls_parser_deduplicates_same_release_date() -> None:
    html = """
    <a href="/news.release/archives/empsit_03052010.htm">First</a>
    <a href="/news.release/archives/empsit_03052010.pdf">Duplicate</a>
    """
    rows = parse_bls_nfp_archive(
        html,
        "https://www.bls.gov/",
        "2010-01-01",
        "2010-04-01",
    )
    assert len(rows) == 1
    assert rows[0]["primaryUrl"].endswith(".htm")
