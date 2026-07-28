from __future__ import annotations

import pandas as pd

from download_neutral_bls_initial_releases import (
    expected_releases,
    parse_release_metric,
)


def test_parse_cpi_and_ppi_headline_direction() -> None:
    cpi, _ = parse_release_metric(
        "CPI",
        (
            "The Consumer Price Index for All Urban Consumers (CPI-U) "
            "declined 0.1 percent in May on a seasonally adjusted basis."
        ),
    )
    ppi, _ = parse_release_metric(
        "PPI",
        (
            "The Producer Price Index for final demand rose 0.8 percent "
            "in May, seasonally adjusted."
        ),
    )
    assert cpi == -0.1
    assert ppi == 0.8
    unchanged, _ = parse_release_metric(
        "CPI",
        (
            "The Consumer Price Index for All Urban Consumers (CPI-U) "
            "was unchanged in January on a seasonally adjusted basis."
        ),
    )
    reordered, _ = parse_release_metric(
        "CPI",
        (
            "The Consumer Price Index for All Urban Consumers (CPI-U) "
            "increased 0.4 percent on a seasonally adjusted basis in "
            "December."
        ),
    )
    edged, _ = parse_release_metric(
        "PPI",
        (
            "The Producer Price Index for final demand edged down "
            "0.1 percent in January."
        ),
    )
    assert unchanged == 0.0
    assert reordered == 0.4
    assert edged == -0.1


def test_parse_nfp_headline_direction() -> None:
    value, evidence = parse_release_metric(
        "NFP",
        (
            "The unemployment rate declined to 3.5 percent, and total "
            "nonfarm payroll employment rose by 136,000, the U.S. "
            "Bureau of Labor Statistics reported today."
        ),
    )
    assert value == 136_000
    assert "136,000" in evidence
    changed_little, _ = parse_release_metric(
        "NFP",
        (
            "Total nonfarm payroll employment changed little in "
            "February (+20,000), and the unemployment rate declined."
        ),
    )
    edged_down, _ = parse_release_metric(
        "NFP",
        (
            "Total nonfarm payroll employment edged down by 92,000 "
            "in February."
        ),
    )
    assert changed_little == 20_000
    assert edged_down == -92_000
    pdf_spacing, _ = parse_release_metric(
        "CPI",
        (
            "The Cons umer Price Index for All Urban Consumers "
            "(CPI-U) increased 0.4 percent in March."
        ),
    )
    nfp_parenthetical, _ = parse_release_metric(
        "NFP",
        (
            "Total nonfarm payroll employment edged up in May "
            "(+75,000), and unemployment was unchanged."
        ),
    )
    nfp_essentially_unchanged, _ = parse_release_metric(
        "NFP",
        (
            "Total nonfarm payroll employment was essentially "
            "unchanged in October (+12,000)."
        ),
    )
    assert pdf_spacing == 0.4
    assert nfp_parenthetical == 75_000
    assert nfp_essentially_unchanged == 12_000
    covid_loss, _ = parse_release_metric(
        "NFP",
        (
            "Total nonfarm payroll employment fell by 20.5 million "
            "in April."
        ),
    )
    covid_rebound, _ = parse_release_metric(
        "NFP",
        (
            "Total nonfarm payroll employment rose by 2.7 million "
            "in May."
        ),
    )
    assert covid_loss == -20_500_000
    assert covid_rebound == 2_700_000


def test_expected_releases_deduplicates_same_event_cluster() -> None:
    events = pd.DataFrame(
        {
            "event_time_utc": [
                "2026-06-10T12:30:00Z",
                "2026-06-10T12:30:00Z",
            ],
            "event_id": ["1", "2"],
            "currency": ["USD", "USD"],
            "title": ["Consumer Price Index", "Consumer Price Index"],
        }
    )
    result = expected_releases(events)
    cpi = result[result["family"].eq("CPI")]
    assert len(cpi) == 1
    assert cpi.iloc[0]["event_ids"] == "1|2"
    assert cpi.iloc[0]["source_url"].endswith("cpi_06102026.pdf")
