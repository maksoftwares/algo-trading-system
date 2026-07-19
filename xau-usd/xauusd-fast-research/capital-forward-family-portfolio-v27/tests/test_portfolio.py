from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import sys

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[2]
sys.path.insert(0, str(ROOT / "src"))

from portfolio import (  # noqa: E402
    circular_block_bootstrap_pvalue,
    evaluate_fixed_union,
    load_config,
    route_fixed_union,
    sha256_file,
    verify_core_reference,
)


def trade_frame(
    lane: str,
    dates: list[str],
    offsets: list[int],
    *,
    base_pnl: float = 1.0,
    stress_pnl: float = 0.8,
) -> pd.DataFrame:
    rows = []
    for day_index, date in enumerate(dates):
        start = int(pd.Timestamp(f"{date}T12:00:00Z").timestamp() * 1000)
        for offset_index, offset in enumerate(offsets):
            candidate = start + offset
            rows.append(
                {
                    "evidence_partition": "FORWARD_VALIDATION",
                    "date_utc": date,
                    "candidate_time_utc": pd.Timestamp(
                        candidate, unit="ms", tz="UTC"
                    ).isoformat(),
                    "candidate_time_msc": candidate,
                    "side": "LONG"
                    if (day_index + offset_index + (lane == "V26")) % 2 == 0
                    else "SHORT",
                    "entry_time_msc": candidate + 100,
                    "exit_time_msc": candidate + 500,
                    "base_pnl_dollars": base_pnl,
                    "stress_pnl_dollars": stress_pnl,
                    "reference_lot": 0.01,
                }
            )
    return pd.DataFrame(rows)


def test_family_alpha_is_divided_across_all_three_claims() -> None:
    config = load_config(ROOT)
    multiple = config["multiple_testing"]
    expected = multiple["family_alpha"] / multiple["registered_forward_claims"]
    assert multiple["maximum_one_sided_pvalue"] == expected
    assert multiple["registered_forward_claims"] == 3
    assert config["router"]["outcome_based_single_lane_fallback_allowed"] is False


def test_block_bootstrap_accepts_uniform_edge_and_rejects_zero_mean() -> None:
    positive = circular_block_bootstrap_pvalue(
        np.ones(20), samples=10_000, seed=2703, block_length=5
    )
    zero_mean = circular_block_bootstrap_pvalue(
        np.tile([1.0, -1.0], 10), samples=10_000, seed=2703, block_length=5
    )
    assert positive <= 0.016666666666666666
    assert zero_mean > 0.016666666666666666


def test_router_uses_fixed_priority_overlap_guard_and_daily_cap() -> None:
    config = load_config(ROOT)
    date = ["2026-07-20"]
    v24 = trade_frame("V24_1", date, [1_000, 7_000])
    v26 = trade_frame("V26", date, [1_000, 4_000, 7_200, 9_000])
    selected, audit = route_fixed_union(v24, v26, config)
    assert selected["source_lane"].tolist() == ["V24_1", "V26", "V24_1"]
    assert selected["route_rank_utc_day"].tolist() == [1, 2, 3]
    assert audit["overlap_rejections"] == 2
    assert audit["daily_cap_rejections"] == 1
    assert audit["maximum_selected_on_one_utc_day"] == 3


def test_locked_core_reference_is_exact() -> None:
    config = load_config(ROOT)
    path = REPO / config["core"]["ledger_path"]
    assert sha256_file(path) == config["core"]["ledger_sha256"]
    reference, metrics = verify_core_reference(pd.read_parquet(path), config)
    assert len(reference) == 160
    assert (
        metrics["trades_per_weekday"] == config["core"]["reference_trades_per_weekday"]
    )
    assert (
        metrics["profit_factor"] == config["core"]["expected_reference_profit_factor"]
    )


def test_fixed_union_passes_only_when_frequency_and_edge_survive() -> None:
    config = deepcopy(load_config(ROOT))
    dates = pd.date_range("2026-07-20", periods=20, freq="B").strftime("%Y-%m-%d")
    v24 = trade_frame("V24_1", dates.tolist(), [1_000, 5_000])
    v26 = trade_frame("V26", dates.tolist(), [3_000, 7_000])
    selected, route_audit = route_fixed_union(v24, v26, config)
    core_reference = pd.DataFrame(
        {
            "exit_time_utc": pd.to_datetime(["2026-06-30T12:00:00Z"]),
            "pnl_usd_0p01_equiv": [10.0],
        }
    )
    core_metrics = {
        "rows": 1,
        "weekdays": 261,
        "trades_per_weekday": config["core"]["reference_trades_per_weekday"],
        "net_dollars": 10.0,
        "profit_factor": 999999.0,
        "closed_drawdown_dollars": 0.0,
    }
    config["gates"]["minimum_core_plus_satellite_net_dollars"] = 10.0
    config["gates"]["minimum_core_plus_satellite_profit_factor"] = 1.0
    audit, daily = evaluate_fixed_union(
        selected,
        dates.tolist(),
        "FORWARD_VALIDATION",
        core_reference,
        core_metrics,
        route_audit,
        config,
    )
    assert len(selected) == 60
    assert daily["trades"].eq(3).all()
    assert audit["metrics"]["satellite_trades_per_weekday"] == 3.0
    assert (
        audit["metrics"]["projected_core_plus_satellite_trades_per_weekday"]
        == 3.6130268199233716
    )
    assert audit["gate_passed"]


def test_research_controls_never_authorize_training_or_trading() -> None:
    controls = load_config(ROOT)["research_controls"]
    for key in (
        "component_economic_outcomes_present_at_lock",
        "portfolio_economic_outcomes_present_at_lock",
        "same_version_tuning_authorized",
        "single_lane_fallback_authorized",
        "model_training_authorized",
        "python_predictions_authorized",
        "ea_consumption_authorized",
        "demo_authorized",
        "live_authorized",
        "broker_action_authorized",
    ):
        assert controls[key] is False
