from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from macro_consensus import (
    build_consensus_features,
    generate_candidates,
    policy_grid,
    session_quality,
)
from run_source_audit import (
    SCOPES,
    audit_month_bounds,
    source_audit_decision,
    source_audit_output_path,
)


ROOT = Path(__file__).resolve().parents[1]


def quote_frame(rows: list[tuple[int, float]]) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "timestamp_ms": [row[0] for row in rows],
            "mid": [row[1] for row in rows],
        }
    )


def rule() -> dict[str, object]:
    return {
        "session_start_utc": "00:00",
        "session_end_utc": "00:01",
        "maximum_baseline_staleness_ms": 1000,
        "maximum_current_source_staleness_ms": 1000,
        "maximum_current_xau_staleness_ms": 1000,
        "minimum_session_coverage_minutes": 0.0,
        "minimum_quotes_by_symbol": {key: 1 for key in ("dxy", "bond", "xag", "xau")},
    }


def prefilter() -> dict[str, object]:
    return {
        "minimum_dxy_move_bps": 0.05,
        "minimum_bond_move_bps": 0.05,
        "minimum_xag_move_bps": 0.5,
        "maximum_signed_xau_response_ratio": 0.25,
        "minimum_source_quote_count": 1,
    }


def test_session_quality_requires_all_four_symbols() -> None:
    date = pd.Timestamp("2024-01-02", tz="UTC")
    frame = quote_frame([(int(date.timestamp() * 1000), 1.0)])
    empty = frame.iloc[0:0]
    assert session_quality(date, frame, frame, frame, frame, rule())[
        "eligible_full_weekday"
    ]
    assert not session_quality(date, frame, empty, frame, frame, rule())[
        "eligible_full_weekday"
    ]


def test_feature_is_causal_and_requires_three_source_consensus() -> None:
    date = pd.Timestamp("2024-01-02", tz="UTC")
    base = int(date.timestamp() * 1000)
    dxy = quote_frame([(base, 100.0), (base + 1000, 100.01)])
    bond = quote_frame([(base, 100.0), (base + 900, 99.99)])
    xag = quote_frame([(base, 20.0), (base + 900, 19.99)])
    xau = quote_frame(
        [(base, 2000.0), (base + 900, 2000.0), (base + 1000, 1900.0)]
    )
    features = build_consensus_features(
        date,
        dxy,
        bond,
        xag,
        xau,
        horizons_ms=[1000],
        rule=rule(),
        prefilter=prefilter(),
    )
    assert len(features) == 1
    row = features.iloc[0]
    assert row["direction"] == "SHORT"
    assert row["dollar_direction"] == "STRENGTH"
    assert int(row["xau_current_timestamp_ms"]) == base + 900
    assert int(row["decision_timestamp_ms"]) == base + 1000

    disagreeing_bond = quote_frame([(base, 100.0), (base + 900, 100.01)])
    assert build_consensus_features(
        date,
        dxy,
        disagreeing_bond,
        xag,
        xau,
        horizons_ms=[1000],
        rule=rule(),
        prefilter=prefilter(),
    ).empty


def test_policy_grid_has_exactly_one_thousand_members() -> None:
    calibration = {
        "horizon_ms_grid": [1, 2, 3, 4],
        "minimum_dxy_move_bps_grid": [1, 2, 3, 4, 5],
        "minimum_bond_move_bps_grid": [1, 2, 3, 4, 5],
        "minimum_xag_move_bps_grid": [1, 2, 3, 4, 5],
        "maximum_signed_xau_response_ratio_grid": [0.0, 0.25],
    }
    policies = policy_grid(calibration)
    assert len(policies) == 1000
    assert len({tuple(sorted(policy.items())) for policy in policies}) == 1000


def test_candidate_generation_keeps_first_event_per_date() -> None:
    features = pd.DataFrame(
        {
            "feature_time_utc": pd.to_datetime(
                ["2024-01-02T08:00:00Z", "2024-01-02T09:00:00Z"]
            ),
            "decision_timestamp_ms": [1, 2],
            "horizon_ms": [1000, 1000],
            "dxy_magnitude_bps": [0.2, 0.3],
            "bond_directional_bps": [0.2, 0.3],
            "xag_directional_bps": [1.0, 1.5],
            "signed_xau_response_ratio": [0.0, 0.1],
            "source_quote_count": [5, 5],
            "direction": ["LONG", "SHORT"],
        }
    )
    policy = {
        "horizon_ms": 1000,
        "minimum_dxy_move_bps": 0.1,
        "minimum_bond_move_bps": 0.1,
        "minimum_xag_move_bps": 0.5,
        "maximum_signed_xau_response_ratio": 0.25,
    }
    candidates = generate_candidates(features, policy=policy, family="TEST")
    assert len(candidates) == 1
    assert int(candidates.iloc[0]["decision_timestamp_ms"]) == 1


def test_source_audits_are_sliced_on_registered_stage_boundaries() -> None:
    config = json.loads(
        (ROOT / "config" / "macro_consensus_xau_catchup_v82.json").read_text(
            encoding="utf-8"
        )
    )
    assert SCOPES == (
        "calibration",
        "development",
        "confirmation",
        "validation",
        "exam",
        "forward_confirmation",
        "forward_final",
        "full",
    )
    assert audit_month_bounds(config, "calibration") == ("2019-02", "2019-02")
    assert audit_month_bounds(config, "development") == ("2019-03", "2021-06")
    assert audit_month_bounds(config, "confirmation") == ("2021-07", "2022-06")
    assert audit_month_bounds(config, "validation") == ("2022-07", "2023-06")
    assert audit_month_bounds(config, "exam") == ("2023-07", "2024-06")
    assert audit_month_bounds(config, "forward_confirmation") == (
        "2024-07",
        "2025-06",
    )
    assert audit_month_bounds(config, "forward_final") == ("2025-07", "2026-06")
    assert audit_month_bounds(config, "full") == ("2019-02", "2026-06")
    assert source_audit_decision("development") == (
        "V82_DEVELOPMENT_SOURCE_AUDIT_PASS"
    )
    assert source_audit_output_path(config, "exam").name == (
        "MACRO_CONSENSUS_XAU_V82_EXAM_SOURCE_AUDIT.json"
    )
    shared = config["shared_portfolio_gates"]
    assert shared["minimum_accepted_trades_per_full_weekday"] == 2.0
    assert shared["minimum_base_profit_factor"] == 1.5
    assert shared["maximum_shared_buffered_stress_floating_drawdown_usd"] == 600.0
    assert not shared["blocked_or_conflicted_entries_count_as_frequency"]
