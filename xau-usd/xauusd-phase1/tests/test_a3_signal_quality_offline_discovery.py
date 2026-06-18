from __future__ import annotations

from phase2x_test_helpers import ROOT, load_script


def test_offline_discovery_candidate_ids_match_locked_sweep() -> None:
    module = load_script("run_a3_signal_quality_offline_discovery")
    sweep = (ROOT / "docs" / "A3_SIGNAL_QUALITY_DIAGNOSTIC_SWEEP_V1_2026_06_18.md").read_text(encoding="utf-8")

    assert module.CANDIDATE_IDS == [
        "B0_RAW_ALL_SESSION",
        "B1_EVENING_BASELINE",
        "F_LOOSE_CT_VETO",
        "F_H1_ALIGN",
        "F_H1_M15_ALIGN",
        "F_RETEST_LIGHT",
        "F_LOOSE_CT_PLUS_RETEST_LIGHT",
        "A3_SQ_MTF_ONLY_V1",
        "A3_SQ_RETEST_ONLY_V1",
        "A3_SQ_COMBINED_V1",
    ]
    for candidate_id in module.CANDIDATE_IDS:
        assert candidate_id in sweep


def test_offline_discovery_script_has_no_runtime_mt5_calls() -> None:
    text = (ROOT / "scripts" / "run_a3_signal_quality_offline_discovery.py").read_text(encoding="utf-8")

    for forbidden in (
        "MetaTrader5",
        "mt5.initialize",
        "OrderSend",
        "CTrade",
        "TRADE_ACTION",
        "PositionClose",
        "PositionModify",
        "terminal64.exe",
        "MQL5\\Profiles",
        "MQL5\\Presets",
    ):
        assert forbidden not in text


def test_loss_class_separates_bad_signal_from_giveback() -> None:
    module = load_script("run_a3_signal_quality_offline_discovery")

    assert module.loss_class(1.5, mfe_r=0.0, mae_r=0.0) == "WIN"
    assert module.loss_class(-1.0, mfe_r=0.20, mae_r=0.80) == "BAD_SIGNAL"
    assert module.loss_class(-1.0, mfe_r=0.60, mae_r=1.00) == "MIXED"
    assert module.loss_class(-1.0, mfe_r=0.90, mae_r=1.00) == "BAD_EXIT_GIVEBACK"
    assert module.loss_class(-1.0, mfe_r=1.30, mae_r=1.00) == "NEAR_TP_GIVEBACK"


def test_v2_registration_keeps_frequency_floor_and_quality_gate() -> None:
    module = load_script("run_a3_signal_quality_offline_discovery")
    eligible = {
        "signal_retention_pct": 40.0,
        "virtual_trade_retention_pct": 35.0,
        "closed_trades": 100,
        "median_weekly_trade_retention_pct": 40.0,
        "profit_factor": 1.25,
        "expectancy_r": 0.15,
        "profit_factor_delta_vs_b0": 0.16,
        "expectancy_delta_vs_b0": 0.01,
        "blocked_bucket_worse_than_kept": True,
        "bad_signal_loss_share_improvement_pct": 20.0,
        "both_rising_and_falling_regimes": True,
    }

    assert module.v2_registration_eligible(eligible)
    assert not module.v2_registration_eligible({**eligible, "signal_retention_pct": 39.99})
    assert not module.v2_registration_eligible({**eligible, "virtual_trade_retention_pct": 34.99})
    assert not module.v2_registration_eligible({**eligible, "median_weekly_trade_retention_pct": 39.99})
    assert not module.v2_registration_eligible({**eligible, "bad_signal_loss_share_improvement_pct": 19.99})


def test_ema_seeds_from_simple_average_then_recurses() -> None:
    module = load_script("run_a3_signal_quality_offline_discovery")

    values = [float(i) for i in range(1, 23)]
    ema20 = module.ema(values, 20)
    multiplier = 2.0 / 21.0

    assert ema20[18] is None
    assert ema20[19] == 10.5
    assert ema20[20] == (21.0 - 10.5) * multiplier + 10.5


def test_apply_b0_comparisons_uses_one_position_b0_denominators() -> None:
    module = load_script("run_a3_signal_quality_offline_discovery")
    rows = [
        {
            "candidate_id": "B0_RAW_ALL_SESSION",
            "profit_factor": 1.50,
            "expectancy_r": 0.25,
            "bad_signal_loss_share_pct": 40.0,
            "opened_virtual_trades": 80,
            "median_weekly_trades": 20,
            "signal_retention_pct": 100.0,
            "closed_trades": 80,
            "blocked_bucket_worse_than_kept": False,
            "both_rising_and_falling_regimes": True,
        },
        {
            "candidate_id": "CANDIDATE",
            "profit_factor": 1.70,
            "expectancy_r": 0.32,
            "bad_signal_loss_share_pct": 30.0,
            "opened_virtual_trades": 40,
            "median_weekly_trades": 10,
            "signal_retention_pct": 60.0,
            "closed_trades": 40,
            "blocked_bucket_worse_than_kept": True,
            "both_rising_and_falling_regimes": True,
        },
    ]

    module.apply_b0_comparisons(rows)

    assert rows[0]["profit_factor_delta_vs_b0"] == 0.0
    assert rows[0]["virtual_trade_retention_pct"] == 100.0
    assert rows[1]["profit_factor_delta_vs_b0"] == 0.2
    assert rows[1]["expectancy_delta_vs_b0"] == 0.07
    assert rows[1]["bad_signal_loss_share_improvement_pct"] == 25.0
    assert rows[1]["virtual_trade_retention_pct"] == 50.0
    assert rows[1]["median_weekly_trade_retention_pct"] == 50.0
