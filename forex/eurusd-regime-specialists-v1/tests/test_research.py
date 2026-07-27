from __future__ import annotations

import lzma
import struct
import sys
from pathlib import Path

import pandas as pd
import pytest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from eurusd_regime_specialists.research import (
    active_weekday_fx_days,
    generate_raw_signals,
    metric_block,
    verify_lock,
    wilder_average,
    walk_long_exit,
)
from eurusd_regime_specialists.ensemble import verify_ensemble_lock
from eurusd_regime_specialists.asymmetric import (
    payoff_metrics,
    verify_asymmetric_lock,
    walk_timed_long_exit,
)
from eurusd_regime_specialists.confirmed_reversal import verify_lock as verify_confirmation_lock
from eurusd_regime_specialists.crossasset_handoff import verify_lock as verify_handoff_lock
from eurusd_regime_specialists.neutral_causal import (
    add_causal_features,
    verify_lock as verify_neutral_lock,
    walk_exit as walk_neutral_exit,
)
from eurusd_regime_specialists.neutral_walkforward import (
    _labeled_outcome,
    choose_side,
    purged_training_rows,
    route_outcomes,
    verify_lock as verify_walkforward_lock,
)
from eurusd_regime_specialists.neutral_crosspair import (
    crosspair_features,
    verify_lock as verify_crosspair_lock,
)
from eurusd_regime_specialists.neutral_crosspair_nonlinear import (
    verify_lock as verify_nonlinear_lock,
)
from eurusd_regime_specialists.neutral_cot_flow import (
    load_config as load_cot_flow_config,
    prepare_cot_flow_context,
    verify_lock as verify_cot_flow_lock,
)
from eurusd_regime_specialists.neutral_cot_options_flow import (
    load_config as load_cot_options_flow_config,
    prepare_options_flow_context,
    verify_lock as verify_cot_options_flow_lock,
)
from eurusd_regime_specialists.neutral_tick_microstructure import (
    aggregate_tick_payload,
    verify_lock as verify_tick_microstructure_lock,
)
from eurusd_regime_specialists.neutral_tick_volatility import (
    verify_lock as verify_tick_volatility_lock,
)
from eurusd_regime_specialists.neutral_prospective import (
    decode_bi5_payload,
    dukascopy_url,
    verify_lock as verify_prospective_lock,
)
from eurusd_regime_specialists.neutral_oracle_imitation import (
    attach_oracle_labels,
    oracle_match_metrics,
    purged_oracle_training_rows,
    verify_lock as verify_oracle_imitation_lock,
)
from eurusd_regime_specialists.neutral_synchronous_crossasset import (
    attach_crossasset_features,
    build_crossasset_features,
    verify_lock as verify_synchronous_crossasset_lock,
)
from eurusd_regime_specialists.neutral_utc_open_vote import (
    attach_vote_sources,
    completed_return_vote,
    verify_lock as verify_utc_open_vote_lock,
)
from eurusd_regime_specialists.retrospective_overfit import (
    _dense_target_candidate,
    density_bucket,
    perfect_foresight_oracle,
    regime_attribution,
    resolve_portfolio,
    select_cells,
)


def test_lock():
    assert len(verify_lock()) == 2
    assert len(verify_ensemble_lock()) == 2
    assert len(verify_asymmetric_lock()) == 2
    assert len(verify_confirmation_lock()) == 2
    assert len(verify_handoff_lock()) == 2
    assert len(verify_neutral_lock()) == 2
    assert len(verify_walkforward_lock()) == 2
    assert len(verify_crosspair_lock()) == 2
    assert len(verify_nonlinear_lock()) == 2
    assert len(verify_tick_microstructure_lock()) == 2
    assert len(verify_tick_volatility_lock()) == 2
    assert len(verify_prospective_lock()) == 2
    assert len(verify_oracle_imitation_lock()) == 2
    assert len(verify_synchronous_crossasset_lock()) == 3
    assert len(verify_utc_open_vote_lock()) == 7
    assert len(verify_cot_flow_lock()) == 14
    assert len(verify_cot_options_flow_lock()) == 25


def test_dukascopy_bi5_url_and_decoder():
    hour = pd.Timestamp("2026-07-01T12:00:00Z")
    assert dukascopy_url("EURUSD", hour).endswith(
        "/EURUSD/2026/06/01/12h_ticks.bi5"
    )
    raw = struct.pack(
        ">IIIff",
        1_000,
        113_856,
        113_855,
        1.0,
        2.0,
    )
    frame = decode_bi5_payload(
        lzma.compress(raw), hour, "EURUSD"
    )
    assert len(frame) == 1
    assert frame.iloc[0]["timestamp_utc"] == pd.Timestamp(
        "2026-07-01T12:00:01Z"
    )
    assert frame.iloc[0]["ask"] == 1.13856
    assert frame.iloc[0]["bid"] == 1.13855
    assert frame.iloc[0]["ask_volume"] == 1.0
    assert frame.iloc[0]["bid_volume"] == 2.0


def test_oracle_imitation_label_and_purge_are_causal():
    entry = pd.Timestamp("2026-01-01T00:00:00Z")
    dataset = pd.DataFrame(
        {
            "entry_time_utc": [entry, entry],
            "side": ["LONG", "SHORT"],
        }
    )
    oracle = pd.DataFrame(
        {"entry_time_utc": [entry], "side": ["SHORT"]}
    )
    cfg = {
        "oracle_label": {
            "negative_label_known_after_hours": 12
        }
    }
    labeled = attach_oracle_labels(dataset, oracle, cfg)
    assert labeled["oracle_member"].tolist() == [0, 1]
    assert purged_oracle_training_rows(
        labeled, entry + pd.Timedelta(hours=12)
    ).empty
    assert len(
        purged_oracle_training_rows(
            labeled, entry + pd.Timedelta(hours=12, seconds=1)
        )
    ) == 2


def test_oracle_imitation_matching_is_side_aware_and_one_to_one():
    start = pd.Timestamp("2026-01-01T00:00:00Z")
    trades = pd.DataFrame(
        {
            "entry_time_utc": [
                start,
                start + pd.Timedelta(minutes=5),
            ],
            "side": ["LONG", "LONG"],
        }
    )
    oracle = pd.DataFrame(
        {
            "entry_time_utc": [start],
            "side": ["LONG"],
            "oracle_trade_number": [1],
        }
    )
    metrics, matches = oracle_match_metrics(
        trades,
        oracle,
        start,
        start + pd.Timedelta(days=1),
        tolerance_minutes=15,
    )
    assert metrics["exact_matches"] == 1
    assert metrics["tolerant_matches"] == 1
    assert len(matches) == 1


def test_synchronous_crossasset_features_are_completed_and_causal():
    index = pd.date_range(
        "2026-01-01", periods=30, freq="5min", tz="UTC"
    )
    macro = pd.DataFrame({"timestamp_utc": index})
    for prefix, start in (
        ("dollaridxusd", 100.0),
        ("ustbondtrusd", 110.0),
    ):
        close = pd.Series(
            [start + value * 0.01 for value in range(30)]
        )
        macro[f"{prefix}_mid_close"] = close
        macro[f"{prefix}_mid_high"] = close + 0.01
        macro[f"{prefix}_mid_low"] = close - 0.01
        macro[f"{prefix}_mid_tick_count"] = [10.0] * 29 + [20.0]
        macro[f"{prefix}_ask_close"] = close + 0.02
        macro[f"{prefix}_bid_close"] = close
        macro[f"{prefix}_available"] = True
    cfg = {
        "crossasset_features": {
            "atr_bars": 24,
            "return_horizons_bars": [1, 3, 6, 12],
            "tick_and_spread_baseline_bars": 24,
            "clip_standardized_input": 10.0,
            "columns": [
                "aligned_dxy_m5_return_1_atr",
                "aligned_dxy_m5_return_3_atr",
                "aligned_dxy_m5_return_6_atr",
                "aligned_dxy_m5_return_12_atr",
                "aligned_bond_m5_return_1_atr",
                "aligned_bond_m5_return_3_atr",
                "aligned_bond_m5_return_6_atr",
                "aligned_bond_m5_return_12_atr",
                "aligned_dxy_m5_close_location",
                "aligned_bond_m5_close_location",
                "dxy_m5_range_atr",
                "bond_m5_range_atr",
                "dxy_m5_tick_ratio_24",
                "bond_m5_tick_ratio_24",
                "dxy_m5_spread_ratio_24",
                "bond_m5_spread_ratio_24",
                "aligned_joint_pressure_1",
                "dxy_bond_support_agreement_1",
            ],
        }
    }
    features = build_crossasset_features(macro, cfg)
    assert features.iloc[-1]["dxy_m5_tick_ratio_24"] == 2.0
    signal = index[-1]
    dataset = pd.DataFrame(
        {
            "signal_time_utc": [signal, signal],
            "completion_time_utc": [
                signal + pd.Timedelta(minutes=5),
                signal + pd.Timedelta(minutes=5),
            ],
            "side": ["LONG", "SHORT"],
        }
    )
    augmented = attach_crossasset_features(dataset, features, cfg)
    long_value = augmented.iloc[0]["aligned_dxy_m5_return_1_atr"]
    short_value = augmented.iloc[1]["aligned_dxy_m5_return_1_atr"]
    assert long_value == -short_value


def test_utc_open_vote_uses_only_completed_bounded_sources():
    fx_index = pd.date_range(
        "2026-01-01T22:55:00Z", periods=18, freq="5min"
    )
    fx_frames = {}
    for symbol, start in (
        ("EURUSD", 1.10),
        ("EURGBP", 0.85),
        ("EURJPY", 160.0),
    ):
        close = pd.Series(
            [start + index * 0.001 for index in range(len(fx_index))],
            index=fx_index,
        )
        fx_frames[symbol] = pd.DataFrame(
            {
                "bid_close": close,
                "ask_close": close + 0.0002,
            },
            index=fx_index,
        )
    dxy_index = pd.date_range(
        "2026-01-01T20:55:00Z", periods=14, freq="5min"
    )
    dxy_macro = pd.DataFrame(
        {
            "timestamp_utc": list(dxy_index)
            + [pd.Timestamp("2026-01-02T00:00:00Z")],
            "dollaridxusd_available": [True] * 15,
            "dollaridxusd_mid_close": [
                100.0 + index * 0.01
                for index in range(len(dxy_index))
            ]
            + [50.0],
        }
    )
    candidates = pd.DataFrame(
        {
            "signal_time_utc": [
                pd.Timestamp("2026-01-01T23:55:00Z")
            ],
            "completion_time_utc": [
                pd.Timestamp("2026-01-02T00:00:00Z")
            ],
        }
    )
    cfg = {
        "candidate": {"return_horizon_minutes": 60},
        "sources": {"DXY": {"maximum_age_minutes": 240}},
    }
    actual = attach_vote_sources(
        candidates, fx_frames, dxy_macro, cfg
    ).iloc[0]
    assert actual["vote_eurusd"] == 1.0
    assert actual["vote_eurgbp"] == 1.0
    assert actual["vote_eurjpy"] == 1.0
    assert actual["vote_dxy"] == -1.0
    assert actual["vote_sum"] == 2.0
    assert actual["side"] == "LONG"
    assert actual["dxy_source_time_utc"] == dxy_index[-1]
    assert actual["dxy_age_minutes"] == 115.0

    gapped = fx_frames["EURUSD"].drop(fx_index[-2])
    vote = completed_return_vote(
        (gapped["bid_close"] + gapped["ask_close"]) / 2.0,
        60,
    )
    assert pd.isna(vote.iloc[-1])


def test_cot_flow_excludes_delayed_reports_before_change():
    raw = pd.DataFrame(
        {
            "Report_Date_as_YYYY-MM-DD": [
                "2023-01-24",
                "2023-01-31",
                "2023-03-21",
            ],
            "Open_Interest_All": [1000, 1000, 1000],
            "Dealer_Positions_Long_All": [400, 900, 350],
            "Dealer_Positions_Short_All": [300, 100, 300],
            "Asset_Mgr_Positions_Long_All": [200, 900, 350],
            "Asset_Mgr_Positions_Short_All": [300, 100, 300],
            "Lev_Money_Positions_Long_All": [200, 900, 100],
            "Lev_Money_Positions_Short_All": [300, 100, 300],
        }
    )
    context = prepare_cot_flow_context(
        raw, load_cot_flow_config()
    )
    assert list(
        context["report_date_utc"].dt.strftime("%Y-%m-%d")
    ) == ["2023-01-24", "2023-03-21"]
    actual = context.iloc[-1]
    assert actual["dealer_flow_change"] == pytest.approx(-0.05)
    assert actual["asset_flow_change"] == pytest.approx(0.15)
    assert actual["leveraged_flow_change"] == pytest.approx(
        -0.10
    )
    assert actual["vote_dealer"] == 1.0
    assert actual["vote_asset"] == 1.0
    assert actual["vote_leveraged"] == -1.0
    assert actual["vote_sum"] == 1.0
    assert actual["side"] == "LONG"
    assert actual["availability_utc"] == pd.Timestamp(
        "2023-03-29T00:00:00Z"
    )


def test_cot_options_flow_is_paired_and_delta_adjusted():
    def row(
        date: str,
        dealer: tuple[int, int],
        asset: tuple[int, int],
        leveraged: tuple[int, int],
    ) -> dict[str, object]:
        return {
            "Report_Date_as_YYYY-MM-DD": date,
            "Open_Interest_All": 1000,
            "Dealer_Positions_Long_All": dealer[0],
            "Dealer_Positions_Short_All": dealer[1],
            "Asset_Mgr_Positions_Long_All": asset[0],
            "Asset_Mgr_Positions_Short_All": asset[1],
            "Lev_Money_Positions_Long_All": leveraged[0],
            "Lev_Money_Positions_Short_All": leveraged[1],
        }

    futures = pd.DataFrame(
        [
            row(
                "2023-01-24",
                (400, 300),
                (200, 300),
                (200, 300),
            ),
            row(
                "2023-03-21",
                (400, 300),
                (200, 300),
                (200, 300),
            ),
        ]
    )
    combined = pd.DataFrame(
        [
            row(
                "2023-01-24",
                (450, 300),
                (250, 300),
                (200, 300),
            ),
            row(
                "2023-03-21",
                (420, 300),
                (320, 300),
                (150, 300),
            ),
        ]
    )
    context = prepare_options_flow_context(
        futures, combined, load_cot_options_flow_config()
    )
    actual = context.iloc[-1]
    assert actual["dealer_options_equivalent_net"] == 20
    assert actual["asset_options_equivalent_net"] == 120
    assert actual["leveraged_options_equivalent_net"] == -50
    assert actual["dealer_flow_change"] == -30
    assert actual["asset_flow_change"] == 70
    assert actual["leveraged_flow_change"] == -50
    assert actual["vote_dealer"] == 1.0
    assert actual["vote_asset"] == 1.0
    assert actual["vote_leveraged"] == -1.0
    assert actual["vote_sum"] == 1.0
    assert actual["side"] == "LONG"
    assert actual["availability_utc"] == pd.Timestamp(
        "2023-03-29T00:00:00Z"
    )


def test_wilder_seed_and_recursion():
    values = pd.Series([float("nan"), 1.0, 2.0, 3.0, 4.0])
    actual = wilder_average(values, 3)
    assert actual.iloc[3] == 2.0
    assert actual.iloc[4] == (2.0 * 2.0 + 4.0) / 3.0


def test_same_bar_is_stop_first():
    index = pd.date_range("2026-01-01", periods=1, freq="5min", tz="UTC")
    frame = pd.DataFrame(
        {"bid_open": [1.0], "bid_low": [0.8], "bid_high": [1.2], "bid_close": [1.0]},
        index=index,
    )
    _, price, reason = walk_long_exit(frame, 0, 0.9, 1.1, 0.01)
    assert reason == "STOP"
    assert price == 0.89


def test_timed_exit_uses_last_bid_close():
    index = pd.date_range("2026-01-01", periods=3, freq="5min", tz="UTC")
    frame = pd.DataFrame(
        {
            "bid_open": [1.0, 1.01, 1.02],
            "bid_low": [0.99, 1.0, 1.01],
            "bid_high": [1.01, 1.02, 1.03],
            "bid_close": [1.005, 1.015, 1.025],
        },
        index=index,
    )
    _, price, reason = walk_timed_long_exit(
        frame, 0, index[-1], 0.8, 1.2, 0.001
    )
    assert reason == "TIME_12H"
    assert price == 1.024


def test_realized_payoff_ratio_is_average_win_over_average_loss():
    result = payoff_metrics(pd.DataFrame({"r": [1.5, 1.5, -1.0, -1.0]}))
    assert result["win_rate"] == 0.5
    assert result["realized_payoff_ratio"] == 1.5
    assert result["profit_factor"] == 1.5


def test_drawdown_includes_zero_origin():
    assert metric_block(pd.DataFrame({"r": [-1.0, 0.2]}))["max_drawdown_r"] == 1.0


def test_active_day_denominator_excludes_sunday_fragment():
    index = pd.to_datetime(
        ["2026-01-04T22:00:00Z", "2026-01-05T00:00:00Z", "2026-01-06T00:00:00Z"]
    )
    frame = pd.DataFrame({"x": [1, 1, 1]}, index=index)
    assert active_weekday_fx_days(
        frame, pd.Timestamp("2026-01-04T00:00:00Z"), pd.Timestamp("2026-01-06T23:59:59Z")
    ) == 2


def test_signal_uses_latest_completed_state_across_context_gap():
    idx = pd.date_range("2026-01-01", periods=50, freq="30min", tz="UTC")
    m5_idx = pd.date_range("2026-01-01", periods=300, freq="5min", tz="UTC")
    price = [1.1] * 294 + [1.08] * 6
    m5 = pd.DataFrame(
        {
            "timestamp_ms": m5_idx.astype("int64") // 1_000_000,
            "bid_open": price,
            "bid_high": price,
            "bid_low": price,
            "bid_close": price,
            "ask_open": [x + 0.0001 for x in price],
            "ask_high": [x + 0.0001 for x in price],
            "ask_low": [x + 0.0001 for x in price],
            "ask_close": [x + 0.0001 for x in price],
            "tick_count": 1,
        },
        index=m5_idx,
    )
    state = pd.DataFrame(
        {
            "direction": ["NEUTRAL"],
            "phase": ["UNRESOLVED"],
            "shock": [False],
            "DXY_compressed": [False],
            "EURUSD_compressed": [False],
        },
        index=pd.DatetimeIndex([idx[-10]], name="timestamp_utc"),
    )
    cfg = {
        "seed": {
            "bands_period": 20,
            "bands_deviation": 2.0,
            "rsi_period": 14,
            "rsi_oversold": 35.0,
            "atr_period": 14,
            "recent_low_bars": 6,
        }
    }
    signals = generate_raw_signals(m5, state, cfg)
    assert not signals.empty
    assert signals.iloc[-1]["owner"] == "S4_NEUTRAL_AUCTION"


def test_retrospective_selector_uses_realized_cell_outcomes():
    rows = []
    for hour, results in (
        (8, [1.5] * 8 + [-1.0] * 7),
        (9, [1.5] * 4 + [-1.0] * 11),
    ):
        for index, result in enumerate(results):
            rows.append(
                {
                    "owner": "S1",
                    "seed_id": "FAST",
                    "entry_hour_utc": hour,
                    "entry_time_utc": pd.Timestamp(
                        "2020-01-01T00:00:00Z"
                    )
                    + pd.Timedelta(days=index),
                    "r": result,
                }
            )
    selected, _ = select_cells(pd.DataFrame(rows))
    assert selected["entry_hour_utc"].tolist() == [8]


def test_retrospective_portfolio_keeps_one_position_at_a_time():
    frame = pd.DataFrame(
        {
            "entry_time_utc": pd.to_datetime(
                [
                    "2026-01-01T00:00:00Z",
                    "2026-01-01T00:05:00Z",
                    "2026-01-01T01:05:00Z",
                ]
            ),
            "exit_time_utc": pd.to_datetime(
                [
                    "2026-01-01T01:00:00Z",
                    "2026-01-01T00:30:00Z",
                    "2026-01-01T02:00:00Z",
                ]
            ),
            "owner_priority": [0, 0, 0],
            "seed_priority": [0, 0, 0],
        }
    )
    resolved = resolve_portfolio(frame, maximum_trades_per_utc_day=12)
    assert len(resolved) == 2


def test_density_oracle_keeps_only_exact_count_days():
    frame = pd.DataFrame(
        {
            "entry_time_utc": pd.to_datetime(
                [
                    "2026-01-01T00:00:00Z",
                    "2026-01-01T01:00:00Z",
                    "2026-01-02T00:00:00Z",
                    "2026-01-02T01:00:00Z",
                    "2026-01-02T02:00:00Z",
                ]
            ),
            "owner_priority": [0, 0, 0, 0, 0],
            "seed_priority": [0, 0, 0, 0, 0],
        }
    )
    selected = density_bucket(frame, trades_per_day=2)
    assert len(selected) == 2
    assert selected["entry_time_utc"].dt.day.unique().tolist() == [1]


def test_perfect_foresight_oracle_discards_every_loss():
    frame = pd.DataFrame(
        {
            "entry_time_utc": pd.to_datetime(
                [f"2026-01-01T0{hour}:00:00Z" for hour in range(6)]
            ),
            "owner_priority": [0] * 6,
            "seed_priority": [0] * 6,
            "exit_reason": ["TARGET"] * 5 + ["STOP"],
            "r": [1.5] * 5 + [-1.0],
        }
    )
    selected = perfect_foresight_oracle(frame, winners_per_active_day=4)
    assert len(selected) == 4
    assert (selected["r"] > 0).all()


def test_regime_attribution_preserves_trade_total():
    frame = pd.DataFrame(
        {
            "owner": [
                "S1_COMPRESSION_REVERSION",
                "S2_SUPPORTIVE_PULLBACK",
                "S3_NEUTRAL_AUCTION",
                "S4_OPPOSING_CAPITULATION",
            ],
            "oracle_date": ["2026-01-01"] * 4,
            "entry_time_utc": pd.to_datetime(
                ["2026-01-01T00:00:00Z"] * 4
            ),
            "r": [1.5] * 4,
            "fixed_0p01_lot_usd": [1.0] * 4,
        }
    )
    attribution = regime_attribution(frame)
    assert attribution["trades"].sum() == 4
    assert attribution["trade_share"].sum() == 1.0


def test_dense_oracle_resolves_same_bar_against_both_sides():
    index = pd.date_range("2026-01-01", periods=1, freq="5min", tz="UTC")
    arrays = {
        "bid_open": [1.0],
        "bid_high": [1.0010],
        "bid_low": [0.9990],
        "ask_open": [1.0001],
        "ask_high": [1.0011],
        "ask_low": [0.9991],
    }
    candidate = _dense_target_candidate(
        0,
        index,
        arrays,
        risk_pips=4.0,
        spread_floor=0.00007,
        slippage=0.00001,
    )
    assert candidate is None


def test_neutral_features_exclude_current_bar_from_prior_extreme():
    index = pd.date_range("2026-01-01", periods=14, freq="5min", tz="UTC")
    highs = [1.0] * 13 + [2.0]
    lows = [0.9] * 14
    frame = pd.DataFrame(
        {
            "bid_open": [0.95] * 14,
            "bid_high": highs,
            "bid_low": lows,
            "bid_close": [0.95] * 14,
            "tick_count": [10] * 14,
        },
        index=index,
    )
    cfg = {
        "features": {
            "atr_bars": 2,
            "tick_median_bars": 2,
            "rolling_extreme_bars": 12,
            "ema_fast_bars": 2,
            "ema_slow_bars": 3,
        },
        "families": {
            "N2_ASIA_RANGE_FADE": {
                "asian_start_hour_utc": 0,
                "asian_end_hour_utc": 6,
            }
        },
    }
    features = add_causal_features(frame, cfg)
    assert features.iloc[-1]["prior_high"] == 1.0


def test_neutral_exit_is_stop_first_for_long_and_short():
    index = pd.date_range("2026-01-01", periods=1, freq="5min", tz="UTC")
    frame = pd.DataFrame(
        {
            "bid_open": [1.0],
            "bid_high": [1.01],
            "bid_low": [0.99],
            "bid_close": [1.0],
            "ask_open": [1.001],
            "ask_high": [1.011],
            "ask_low": [0.991],
            "ask_close": [1.001],
        },
        index=index,
    )
    long_exit = walk_neutral_exit(
        frame, 0, index[0], "LONG", 0.995, 1.005, 0.001, 0.0
    )
    short_exit = walk_neutral_exit(
        frame, 0, index[0], "SHORT", 1.006, 0.996, 0.001, 0.0
    )
    assert long_exit[2] == "STOP"
    assert short_exit[2] == "STOP"


def test_walkforward_training_purges_unfinished_labels():
    frame = pd.DataFrame(
        {
            "entry_time_utc": pd.to_datetime(
                [
                    "2025-12-31T20:00:00Z",
                    "2025-12-31T23:00:00Z",
                    "2026-01-01T00:00:00Z",
                ]
            ),
            "exit_time_utc": pd.to_datetime(
                [
                    "2025-12-31T21:00:00Z",
                    "2026-01-01T01:00:00Z",
                    "2026-01-01T02:00:00Z",
                ]
            ),
        }
    )
    purged = purged_training_rows(
        frame, pd.Timestamp("2026-01-01T00:00:00Z")
    )
    assert len(purged) == 1


def test_walkforward_chooses_one_higher_probability_side():
    timestamp = pd.Timestamp("2026-01-01T12:00:00Z")
    frame = pd.DataFrame(
        {
            "completion_time_utc": [timestamp, timestamp],
            "entry_time_utc": [timestamp, timestamp],
            "side": ["LONG", "SHORT"],
            "predicted_probability": [0.51, 0.57],
        }
    )
    selected = choose_side(frame, threshold=0.55)
    assert selected["side"].tolist() == ["SHORT"]


def test_routed_walkforward_trade_preserves_risk_pips():
    timestamp = pd.Timestamp("2026-01-05T12:00:00Z")
    prediction = pd.DataFrame(
        {
            "side": ["LONG"],
            "signal_time_utc": [timestamp - pd.Timedelta(minutes=5)],
            "completion_time_utc": [timestamp],
            "entry_time_utc": [timestamp],
            "exit_time_utc": [timestamp + pd.Timedelta(minutes=5)],
            "entry_price": [1.1],
            "stop_price": [1.099],
            "target_price": [1.1015],
            "exit_price": [1.099],
            "exit_reason": ["STOP"],
            "predicted_probability": [0.6],
            "risk_distance": [0.001],
            "risk_pips": [10.0],
            "outcome_r": [-1.01],
            "fixed_0p01_lot_usd": [-1.01],
        }
    )
    cfg = {"execution": {"max_trades_per_utc_day": 4}}
    routed = route_outcomes(prediction, cfg)
    assert routed.iloc[0]["risk_pips"] == 10.0


def test_crosspair_tick_baseline_excludes_current_bar():
    index = pd.date_range("2026-01-01", periods=25, freq="5min", tz="UTC")
    close = pd.Series(
        [1.0 + i * 0.0001 for i in range(25)], index=index
    )
    frame = pd.DataFrame(
        {
            "bid_high": close + 0.0001,
            "bid_low": close - 0.0001,
            "bid_close": close,
            "tick_count": [10] * 24 + [20],
        },
        index=index,
    )
    cfg = {
        "features": {
            "atr_bars": 2,
            "tick_median_bars": 24,
            "crosspair_return_horizons_bars": [3, 6, 12, 24],
        }
    }
    features = crosspair_features(frame, "test", cfg)
    assert features.iloc[-1]["test_tick_ratio"] == 2.0


def test_tick_payload_decodes_cumulative_time_and_price_deltas():
    payload = {
        "timestamp": 0,
        "multiplier": 0.0001,
        "bid": 1.0,
        "ask": 1.0002,
        "times": [0, 60_000, 60_000, 170_000],
        "bids": [0, 1, 1, 1],
        "asks": [0, 1, 1, 1],
        "bidVolumes": [1, 1, 1, 1],
        "askVolumes": [1, 1, 1, 1],
    }
    rows = aggregate_tick_payload(payload)
    assert len(rows) == 1
    assert rows[0]["timestamp_ms"] == 0
    assert rows[0]["quote_change_imbalance"] == 1.0
    assert rows[0]["path_efficiency"] == 1.0


def test_walkforward_label_honors_causal_dynamic_risk():
    index = pd.date_range("2026-01-01", periods=1, freq="5min", tz="UTC")
    arrays = {
        "bid_open": [1.0],
        "bid_high": [1.0],
        "bid_low": [1.0],
        "bid_close": [1.0],
        "ask_open": [1.0001],
        "ask_high": [1.0001],
        "ask_low": [1.0001],
        "ask_close": [1.0001],
    }
    cfg = {
        "label": {
            "risk_pips": 4.0,
            "target_r": 1.5,
            "maximum_hold_hours": 12,
            "minimum_retail_spread_pips": 0.7,
            "extra_slippage_pips_per_side": 0.1,
        }
    }
    outcome = _labeled_outcome(
        0, index, arrays, "LONG", cfg, risk_pips=10.0
    )
    assert outcome["risk_pips"] == 10.0
    assert outcome["risk_distance"] == 0.001
