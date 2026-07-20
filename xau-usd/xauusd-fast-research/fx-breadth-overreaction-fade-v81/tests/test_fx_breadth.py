from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from fx_breadth import (
    build_breadth_features,
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
        "minimum_quotes_per_symbol": 1,
    }


def prefilter() -> dict[str, object]:
    return {
        "minimum_leg_move_bps": 0.05,
        "minimum_breadth_sum_bps": 0.15,
        "minimum_signed_xau_response_ratio": 0.5,
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


def test_feature_is_causal_and_fades_completed_gold_overreaction() -> None:
    date = pd.Timestamp("2024-01-02", tz="UTC")
    base = int(date.timestamp() * 1000)
    eur = quote_frame([(base, 1.1000), (base + 1000, 1.0998)])
    gbp = quote_frame([(base, 1.2500), (base + 900, 1.2497)])
    jpy = quote_frame([(base, 145.00), (base + 900, 145.04)])
    xau = quote_frame(
        [(base, 2000.0), (base + 900, 1999.0), (base + 1000, 2100.0)]
    )
    features = build_breadth_features(
        date,
        eur,
        gbp,
        jpy,
        xau,
        horizons_ms=[1000],
        rule=rule(),
        prefilter=prefilter(),
    )
    assert len(features) == 1
    row = features.iloc[0]
    assert row["direction"] == "LONG"
    assert row["dollar_direction"] == "STRENGTH"
    assert int(row["xau_current_timestamp_ms"]) == base + 900
    assert int(row["decision_timestamp_ms"]) == base + 1000


def test_policy_grid_has_exactly_one_thousand_members() -> None:
    calibration = {
        "horizon_ms_grid": [1, 2, 3, 4, 5],
        "minimum_leg_move_bps_grid": [1, 2, 3, 4, 5],
        "minimum_breadth_sum_bps_grid": [1, 2, 3, 4, 5],
        "minimum_signed_xau_response_ratio_grid": [1, 2, 3, 4],
        "minimum_source_quote_count_grid": [2, 5],
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
            "minimum_leg_move_bps": [0.2, 0.3],
            "breadth_sum_bps": [0.8, 0.9],
            "signed_xau_response_ratio": [1.0, 1.5],
            "source_quote_count": [5, 5],
            "direction": ["LONG", "SHORT"],
        }
    )
    policy = {
        "horizon_ms": 1000,
        "minimum_leg_move_bps": 0.1,
        "minimum_breadth_sum_bps": 0.5,
        "minimum_signed_xau_response_ratio": 0.5,
        "minimum_source_quote_count": 2,
    }
    candidates = generate_candidates(features, policy=policy, family="TEST")
    assert len(candidates) == 1
    assert int(candidates.iloc[0]["decision_timestamp_ms"]) == 1


def test_source_audits_are_sliced_on_registered_stage_boundaries() -> None:
    config = json.loads(
        (ROOT / "config" / "fx_breadth_overreaction_fade_v81.json").read_text(
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
    assert audit_month_bounds(config, "calibration") == ("2018-07", "2018-08")
    assert audit_month_bounds(config, "development") == ("2018-09", "2021-06")
    assert audit_month_bounds(config, "confirmation") == ("2021-07", "2022-06")
    assert audit_month_bounds(config, "validation") == ("2022-07", "2023-06")
    assert audit_month_bounds(config, "exam") == ("2023-07", "2024-06")
    assert audit_month_bounds(config, "forward_confirmation") == (
        "2024-07",
        "2025-06",
    )
    assert audit_month_bounds(config, "forward_final") == ("2025-07", "2026-06")
    assert audit_month_bounds(config, "full") == ("2018-07", "2026-06")
    assert source_audit_decision("development") == (
        "V81_DEVELOPMENT_SOURCE_AUDIT_PASS"
    )
    assert source_audit_output_path(config, "exam").name == (
        "FX_BREADTH_XAU_V81_EXAM_SOURCE_AUDIT.json"
    )
    shared = config["shared_portfolio_gates"]
    assert shared["minimum_accepted_trades_per_full_weekday"] == 2.0
    assert shared["minimum_base_profit_factor"] == 1.5
    assert shared["maximum_shared_buffered_stress_floating_drawdown_usd"] == 600.0
    assert not shared["blocked_or_conflicted_entries_count_as_frequency"]
