from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "comex_spot_leadlag_campaign_test_module", ROOT / "src" / "campaign.py"
)
if SPEC is None or SPEC.loader is None:
    raise ImportError(ROOT / "src" / "campaign.py")
CAMPAIGN = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = CAMPAIGN
SPEC.loader.exec_module(CAMPAIGN)


def _spot(starts: pd.DatetimeIndex) -> pd.DataFrame:
    mid = 100.0 + np.arange(len(starts), dtype=float) * 0.05
    return pd.DataFrame(
        {
            "bar_start_utc": starts,
            "bar_end_utc": starts + pd.Timedelta(minutes=5),
            "bid_open": mid - 0.05,
            "bid_high": mid + 0.20,
            "bid_low": mid - 0.20,
            "bid_close": mid,
            "ask_open": mid + 0.05,
            "ask_high": mid + 0.30,
            "ask_low": mid - 0.10,
            "ask_close": mid + 0.10,
            "mid_open": mid,
            "mid_high": mid + 0.25,
            "mid_low": mid - 0.15,
            "mid_close": mid + 0.05,
        }
    )


def _comex(starts: pd.DatetimeIndex, session_dates: list[str], closes: np.ndarray) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "bucket": starts,
            "available_time_utc": starts + pd.Timedelta(minutes=5),
            "close": closes,
            "volume": np.full(len(starts), 100.0),
            "signed_volume": np.full(len(starts), 20.0),
            "session_date": session_dates,
            "session_bar_index": np.arange(len(starts)) % (len(starts) // len(set(session_dates))),
            "cumulative_delta_ratio": np.full(len(starts), 0.2),
            "cumulative_volume_ratio": np.full(len(starts), 1.0),
        }
    )


def _feature_config(minimum_aligned: int = 1) -> dict:
    return {
        "features": {"atr_period": 2, "return_windows_bars": [1, 3, 6, 12]},
        "comex_source": {
            "minimum_aligned_rows": minimum_aligned,
            "returns_reset_each_session": True,
            "overnight_basis_authorized": False,
        },
    }


def test_manifest_has_exactly_one_thousand_new_attempts() -> None:
    manifest = CAMPAIGN.generate_manifest(7093, 200)
    assert len(manifest) == 1000
    assert manifest["attempt_no"].min() == 7094
    assert manifest["attempt_no"].max() == 8093
    assert manifest["policy_id"].nunique() == 1000
    assert manifest.groupby("mechanic").size().eq(200).all()


def test_futures_returns_reset_at_each_session_boundary() -> None:
    first = pd.date_range("2024-01-02T13:20:00Z", periods=14, freq="5min")
    second = pd.date_range("2024-01-03T13:20:00Z", periods=14, freq="5min")
    starts = first.append(second)
    spot = _spot(starts)
    closes = np.concatenate((100.0 + np.arange(14), 200.0 + np.arange(14)))
    comex = _comex(starts, ["2024-01-02"] * 14 + ["2024-01-03"] * 14, closes)
    prepared = CAMPAIGN.prepare_features(spot, comex, _feature_config())
    second_open = prepared.index[prepared["bar_start_utc"].eq(second[0])][0]
    assert np.isnan(prepared.loc[second_open, "gc_return_1_atr"])
    assert np.isnan(prepared.loc[second_open, "relative_gap_1_atr"])
    assert np.isfinite(prepared.loc[second_open + 1, "gc_return_1_atr"])


def test_noncontiguous_futures_bars_do_not_create_return() -> None:
    starts = pd.DatetimeIndex(
        [
            pd.Timestamp("2024-01-02T13:20:00Z"),
            pd.Timestamp("2024-01-02T13:25:00Z"),
            pd.Timestamp("2024-01-02T13:35:00Z"),
        ]
    )
    prepared = CAMPAIGN.prepare_features(
        _spot(starts),
        _comex(starts, ["2024-01-02"] * 3, np.array([100.0, 101.0, 102.0])),
        _feature_config(),
    )
    assert np.isfinite(prepared.loc[1, "gc_return_1_atr"])
    assert np.isnan(prepared.loc[2, "gc_return_1_atr"])


def test_overnight_basis_authority_is_rejected() -> None:
    starts = pd.date_range("2024-01-02T13:20:00Z", periods=14, freq="5min")
    config = _feature_config()
    config["comex_source"]["overnight_basis_authorized"] = True
    try:
        CAMPAIGN.prepare_features(
            _spot(starts),
            _comex(starts, ["2024-01-02"] * 14, 100.0 + np.arange(14)),
            config,
        )
    except ValueError as exc:
        assert "Overnight" in str(exc)
    else:
        raise AssertionError("Overnight basis authority was accepted")


def test_gc_lead_signal_uses_completed_relative_gap() -> None:
    frame = pd.DataFrame(
        {
            "comex_session_minute": [600.0],
            "gc_return_3_atr": [0.30],
            "spot_return_3_atr": [0.08],
            "relative_gap_3_atr": [0.22],
            "gc_bar_delta_ratio": [0.20],
            "gc_cumulative_delta_ratio": [0.15],
            "gc_cumulative_volume_ratio": [1.20],
            "atr14": [1.0],
        }
    )
    params = {
        "window": 3,
        "gc_move_min": 0.10,
        "gap_min": 0.10,
        "spot_follow_max_ratio": 0.5,
        "spot_opposition_max": 0.0,
        "delta_min": 0.10,
        "delta_source": "BAR",
        "volume_min": 1.0,
        "session": "ALL",
    }
    mask, direction = CAMPAIGN.signal_mask_direction(
        frame, "GC_LEADS_XAU_CATCHUP", params
    )
    assert bool(mask.iloc[0])
    assert int(direction.iloc[0]) == 1


def test_convergence_signal_requires_gap_to_remain_on_original_side() -> None:
    frame = pd.DataFrame(
        {
            "comex_session_minute": [600.0, 600.0],
            "prior_relative_gap_6_atr": [0.40, 0.40],
            "relative_gap_6_atr": [0.25, -0.05],
            "spot_return_1_atr": [0.10, 0.10],
            "gc_return_1_atr": [0.01, 0.01],
            "gc_bar_delta_ratio": [0.10, 0.10],
            "gc_cumulative_delta_ratio": [0.10, 0.10],
            "atr14": [1.0, 1.0],
        }
    )
    params = {
        "gap_window": 6,
        "prior_gap_min": 0.25,
        "catchup_min": 0.05,
        "closure_min": 0.10,
        "gc_retrace_max": 0.05,
        "delta_min": 0.05,
        "delta_source": "BAR",
        "session": "ALL",
    }
    mask, direction = CAMPAIGN.signal_mask_direction(
        frame, "GAP_CONVERGENCE_IGNITION", params
    )
    assert bool(mask.iloc[0])
    assert not bool(mask.iloc[1])
    assert direction.tolist() == [1, 1]


def test_shared_simulator_enters_next_bar_ask_for_long() -> None:
    starts = pd.date_range("2024-01-02T13:20:00", periods=5, freq="5min").to_numpy()
    arrays = {
        "starts": starts,
        "ends": starts + np.timedelta64(5, "m"),
        "atr": np.ones(5),
        "bid_open": np.array([99.9, 100.0, 100.0, 100.0, 100.0]),
        "bid_high": np.array([100.0, 101.3, 100.0, 100.0, 100.0]),
        "bid_low": np.full(5, 99.8),
        "bid_close": np.full(5, 100.0),
        "ask_open": np.array([100.1, 100.2, 100.2, 100.2, 100.2]),
        "ask_high": np.full(5, 100.4),
        "ask_low": np.full(5, 100.0),
        "ask_close": np.full(5, 100.2),
    }
    outcome = CAMPAIGN.simulate_trade(
        arrays,
        0,
        1,
        {"stop_atr": 1.0, "target_r": 1.0, "hold_bars": 2},
        {
            "maximum_entry_spread_r": 0.3,
            "maximum_research_risk_usd": 50.0,
            "current_account_risk_usd": 8.0,
            "ounces_at_lot_size": 1.0,
            "extra_execution_cost_usd": 0.0,
            "holding_cost_per_24h_usd": 0.0,
            "stress_slippage_r": 0.0,
        },
        pd.Timestamp("2024-01-03T00:00:00Z"),
    )
    assert outcome is not None
    assert outcome["entry_price"] == 100.2
    assert outcome["entry_time"] == pd.Timestamp("2024-01-02T13:25:00Z")
    assert outcome["exit_reason"] == "TARGET"


def test_signal_census_reads_no_labels_or_outcomes() -> None:
    starts = pd.date_range("2024-01-02T13:20:00Z", periods=40, freq="5min")
    spot = _spot(starts)
    comex = _comex(
        starts,
        ["2024-01-02"] * 40,
        100.0 + np.arange(40, dtype=float) * 0.12,
    )
    frame = CAMPAIGN.prepare_features(spot, comex, _feature_config())
    params = {
        "window": 1,
        "gc_move_min": 0.01,
        "gap_min": 0.0,
        "spot_follow_max_ratio": 1.0,
        "spot_opposition_max": 0.1,
        "delta_min": 0.0,
        "delta_source": "BAR",
        "volume_min": 0.1,
        "session": "ALL",
    }
    manifest = pd.DataFrame(
        [
            {
                "attempt_no": 7094,
                "policy_id": "synthetic",
                "mechanic": "GC_LEADS_XAU_CATCHUP",
                "parameters_json": json.dumps(params, sort_keys=True),
            }
        ]
    )
    config = {
        "windows": {"discovery": ["2024-01-02", "2024-01-03"]},
        "features": {"return_windows_bars": [1, 3, 6, 12]},
    }
    census = CAMPAIGN.signal_census(frame, manifest, config)
    assert census["label_or_outcome_columns_read"] is False
    assert census["policy_count"] == 1


def test_contract_grants_no_data_purchase_training_or_execution_authority() -> None:
    config = json.loads(
        (ROOT / "config" / "comex_spot_leadlag_mechanics_v1.json").read_text(
            encoding="utf-8"
        )
    )
    controls = config["research_controls"]
    assert controls["registered_policy_count"] == 1000
    assert controls["campaign_attempts_before_v1"] == 7093
    assert controls["minimum_discovery_raw_signals_per_policy"] >= config["gates"][
        "discovery"
    ]["minimum_trades"]
    assert controls["same_version_post_outcome_tuning_authorized"] is False
    for name in (
        "network_data_acquisition_authorized",
        "paid_data_authorized",
        "databento_use_authorized",
        "broker_action_authorized",
        "python_predictions_authorized",
        "model_training_authorized",
        "ea_consumption_authorized",
    ):
        assert controls[name] is False


def test_drawdown_includes_starting_equity() -> None:
    assert CAMPAIGN.closed_drawdown(pd.Series([-2.0, 3.0])) == 2.0


def test_bh_adjustment_is_bounded() -> None:
    adjusted = CAMPAIGN.benjamini_hochberg(pd.Series([0.001, 0.02, 0.5]))
    assert adjusted.between(0.0, 1.0).all()
