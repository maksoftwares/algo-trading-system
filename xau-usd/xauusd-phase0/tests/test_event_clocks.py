from __future__ import annotations

from pathlib import Path

import pytest

from phase0.config import ConfigError
from phase0.constants import SECOND_EA_LANE_B_CANDIDATES
from phase0.event_clocks import generate_event_clock_validation, load_event_clocks


def test_event_clock_validation_samples_dst_windows(project_root: Path):
    validation = generate_event_clock_validation(project_root)
    clocks = load_event_clocks(project_root / "config" / "event_clocks.yaml")

    assert validation.status == "PASS"
    assert validation.event_count == 3
    assert {clock.linked_candidate_id for clock in clocks} == set(SECOND_EA_LANE_B_CANDIDATES)
    sample_names = {sample.sample_name for sample in validation.samples}
    assert "normal_month" in sample_names
    assert "us_dst_only_divergence_window" in sample_names
    assert "uk_dst_active_window" in sample_names
    assert "post_november_overlap_window" in sample_names

    by_event_sample = {(sample.event_id, sample.sample_name): sample for sample in validation.samples}
    assert by_event_sample[("xau_london_open", "normal_month")].utc_time.endswith("08:00:00Z")
    assert by_event_sample[("xau_london_open", "uk_dst_active_window")].utc_time.endswith("07:00:00Z")
    assert by_event_sample[("xau_comex_gold_settlement", "normal_month")].utc_time.endswith("18:30:00Z")
    assert by_event_sample[
        ("xau_comex_gold_settlement", "us_dst_only_divergence_window")
    ].utc_time.endswith("17:30:00Z")


def test_event_clock_config_requires_core_fields(tmp_path: Path):
    path = tmp_path / "event_clocks.yaml"
    path.write_text(
        "\n".join(
            [
                "event_clocks:",
                "  - event_id: bad_clock",
                "    market_timezone: Europe/London",
                "    canonical_local_time: '08:00'",
            ]
        ),
        encoding="utf-8",
    )

    with pytest.raises(ConfigError, match="missing required field"):
        load_event_clocks(path)


def test_event_clock_config_rejects_duplicate_event_ids(tmp_path: Path):
    path = tmp_path / "event_clocks.yaml"
    path.write_text(
        "\n".join(
            [
                "event_clocks:",
                *_valid_clock_item(event_id="xau_london_open"),
                *_valid_clock_item(event_id="xau_london_open"),
                "",
            ]
        ),
        encoding="utf-8",
    )

    with pytest.raises(ConfigError, match="duplicated"):
        load_event_clocks(path)


def test_event_clock_config_rejects_mt5_server_time_rule(tmp_path: Path):
    path = tmp_path / "event_clocks.yaml"
    path.write_text(
        _valid_clock_yaml(server_time_conversion_rule="Use the broker server clock."),
        encoding="utf-8",
    )

    with pytest.raises(ConfigError, match="no MT5 runtime"):
        load_event_clocks(path)


def test_event_clock_config_requires_lane_b_candidate_link(tmp_path: Path):
    path = tmp_path / "event_clocks.yaml"
    path.write_text(_valid_clock_yaml(linked_candidate_id="not_a_lane_b_candidate"), encoding="utf-8")

    with pytest.raises(ConfigError, match="Lane B campaign candidate"):
        load_event_clocks(path)


def _valid_clock_yaml(
    *,
    event_id: str = "xau_london_open",
    server_time_conversion_rule: str = "Use UTC-normalized offline bar timestamps only; no MT5 runtime query is authorized.",
    linked_candidate_id: str = "xau_london_open_expansion_flow_v0",
) -> str:
    return "\n".join(
        ["event_clocks:", *_valid_clock_item(event_id, server_time_conversion_rule, linked_candidate_id), ""]
    )


def _valid_clock_item(
    event_id: str,
    server_time_conversion_rule: str = "Use UTC-normalized offline bar timestamps only; no MT5 runtime query is authorized.",
    linked_candidate_id: str = "xau_london_open_expansion_flow_v0",
) -> list[str]:
    return [
        f"  - event_id: {event_id}",
        "    market_timezone: Europe/London",
        "    canonical_local_time: '08:00'",
        "    utc_conversion_rule: Convert 08:00 Europe/London to UTC with IANA timezone rules.",
        f"    server_time_conversion_rule: {server_time_conversion_rule}",
        "    dst_handling_note: Europe/London changes UTC offset across DST.",
        "    source_rationale_note: Test event clock.",
        f"    linked_candidate_id: {linked_candidate_id}",
    ]
