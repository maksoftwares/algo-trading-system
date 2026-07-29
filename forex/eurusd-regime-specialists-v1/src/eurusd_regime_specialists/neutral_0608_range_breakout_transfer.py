from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from .research import PACKAGE_ROOT, PIP, load_inputs, serialize, sha256_file


FAMILY = "N48_NEUTRAL_0608_UTC_RANGE_BREAKOUT_TRANSFER"
CONFIG_PATH = (
    PACKAGE_ROOT
    / "config"
    / "frozen_neutral_0608_range_breakout_transfer.json"
)
LOCK_PATH = (
    PACKAGE_ROOT
    / "EURUSD_NEUTRAL_0608_RANGE_BREAKOUT_TRANSFER_"
    "PREREG_2026_07_29.sha256.json"
)
PARENT_CONFIG_PATH = (
    PACKAGE_ROOT / "config" / "frozen_two_clock_ensemble.json"
)
OUTPUT_ROOT = (
    PACKAGE_ROOT / "outputs" / "neutral_0608_range_breakout_transfer"
)


def load_config() -> dict[str, Any]:
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def load_parent_config() -> dict[str, Any]:
    return json.loads(PARENT_CONFIG_PATH.read_text(encoding="utf-8"))


def verify_lock() -> dict[str, str]:
    lock = json.loads(LOCK_PATH.read_text(encoding="utf-8"))
    if (
        lock.get("locked_before_first_eurusd_candidate_count") is not True
        or lock.get("census_forbids_outcome_loading") is not True
        or lock.get("broker_action_allowed") is not False
    ):
        raise RuntimeError("Range-breakout transfer was not locked in time")
    checked: dict[str, str] = {}
    for relative, expected in lock["files"].items():
        actual = sha256_file(PACKAGE_ROOT / relative)
        if actual != expected:
            raise RuntimeError(
                "Range-breakout transfer preregistration mismatch: "
                f"{relative}"
            )
        checked[relative] = actual
    return checked


def _wilder_atr(frame: pd.DataFrame, period: int) -> pd.Series:
    previous = frame["close"].shift(1)
    true_range = pd.concat(
        [
            frame["high"] - frame["low"],
            (frame["high"] - previous).abs(),
            (frame["low"] - previous).abs(),
        ],
        axis=1,
    ).max(axis=1)
    return true_range.ewm(
        alpha=1.0 / period,
        adjust=False,
        min_periods=period,
    ).mean()


def _midpoint_bars(
    m5: pd.DataFrame,
    rule: str,
    *,
    required_source_bars: int | None,
) -> pd.DataFrame:
    mid = pd.DataFrame(index=m5.index)
    mid["open"] = (m5["bid_open"] + m5["ask_open"]) / 2.0
    mid["high"] = (m5["bid_high"] + m5["ask_high"]) / 2.0
    mid["low"] = (m5["bid_low"] + m5["ask_low"]) / 2.0
    mid["close"] = (m5["bid_close"] + m5["ask_close"]) / 2.0
    bars = mid.resample(rule, label="left", closed="left").agg(
        open=("open", "first"),
        high=("high", "max"),
        low=("low", "min"),
        close=("close", "last"),
        source_bars=("close", "count"),
    )
    bars = bars.dropna(subset=["open", "high", "low", "close"])
    if required_source_bars is not None:
        bars = bars[bars["source_bars"].eq(required_source_bars)]
    return bars


def generate_session_signals(
    m5: pd.DataFrame,
    cfg: dict[str, Any],
) -> pd.DataFrame:
    strategy = cfg["strategy"]
    minutes = int(strategy["signal_timeframe_minutes"])
    m15 = _midpoint_bars(
        m5,
        f"{minutes}min",
        required_source_bars=minutes // 5,
    )
    daily = _midpoint_bars(
        m5,
        "1D",
        required_source_bars=None,
    )
    m15["atr"] = _wilder_atr(
        m15,
        int(strategy["atr_period_m15"]),
    )
    daily["atr"] = _wilder_atr(
        daily,
        int(strategy["d1_atr_period"]),
    )
    expected_range_bars = (
        int(strategy["range_minutes"]) // minutes
    )
    rows: list[dict[str, Any]] = []
    for bar_time, bar in m15.iterrows():
        completion = bar_time + pd.Timedelta(minutes=minutes)
        if (
            pd.isna(bar["atr"])
            or (
                bool(strategy["weekdays_only"])
                and bar_time.weekday() >= 5
            )
            or not (
                int(strategy["trade_start_hour_utc"])
                <= bar_time.hour
                < int(strategy["trade_end_hour_utc"])
            )
        ):
            continue
        day = bar_time.floor("D")
        previous_day = day - pd.Timedelta(days=1)
        if (
            previous_day not in daily.index
            or pd.isna(daily.at[previous_day, "atr"])
            or float(daily.at[previous_day, "atr"]) <= 0.0
        ):
            continue
        range_start = day + pd.Timedelta(
            hours=int(strategy["range_start_hour_utc"])
        )
        range_end = range_start + pd.Timedelta(
            minutes=int(strategy["range_minutes"])
        )
        range_bars = m15.loc[
            (m15.index >= range_start) & (m15.index < range_end)
        ]
        if (
            len(range_bars) != expected_range_bars
            or range_bars.index[0] != range_start
            or range_bars.index[-1]
            != range_end - pd.Timedelta(minutes=minutes)
        ):
            continue
        range_high = float(range_bars["high"].max())
        range_low = float(range_bars["low"].min())
        session_range = range_high - range_low
        atr = float(bar["atr"])
        range_atr = session_range / atr if atr > 0 else np.nan
        prior_day_atr = float(daily.at[previous_day, "atr"])
        daily_range_atr = session_range / prior_day_atr
        if (
            not (
                float(strategy["range_atr_min"])
                <= range_atr
                <= float(strategy["range_atr_max"])
            )
            or daily_range_atr
            < float(strategy["daily_range_atr_min"])
        ):
            continue
        point = float(strategy["point"])
        bar_range = max(
            float(bar["high"]) - float(bar["low"]),
            point,
        )
        body_fraction = (
            abs(float(bar["close"]) - float(bar["open"]))
            / bar_range
        )
        if body_fraction < float(strategy["body_fraction_min"]):
            continue
        close_location = (
            float(bar["close"]) - float(bar["low"])
        ) / bar_range
        buffer = float(strategy["break_buffer_atr"]) * atr
        side = "CASH"
        if (
            float(bar["close"]) > range_high + buffer
            and close_location
            >= float(strategy["long_close_location_min"])
        ):
            side = "LONG"
        elif (
            float(bar["close"]) < range_low - buffer
            and close_location
            <= float(strategy["short_close_location_max"])
        ):
            side = "SHORT"
        if side == "CASH":
            continue
        rows.append(
            {
                "family": FAMILY,
                "signal_time_utc": bar_time,
                "signal_complete_utc": completion,
                "entry_time_utc": completion,
                "state_latest_allowed_utc": (
                    completion.floor("h") - pd.Timedelta(hours=1)
                ),
                "side": side,
                "atr": atr,
                "prior_day_atr": prior_day_atr,
                "range_high": range_high,
                "range_low": range_low,
                "session_range": session_range,
                "range_atr": range_atr,
                "daily_range_atr": daily_range_atr,
                "body_fraction": body_fraction,
                "close_location": close_location,
            }
        )
    return pd.DataFrame(rows)


def assign_neutral_ownership(
    signals: pd.DataFrame,
    state: pd.DataFrame,
    cfg: dict[str, Any],
) -> pd.DataFrame:
    if signals.empty:
        return signals.copy()
    state_columns = [
        "direction",
        "phase",
        "shock",
        "DXY_compressed",
        "EURUSD_compressed",
    ]
    signal_order = signals.sort_values(
        "state_latest_allowed_utc"
    ).copy()
    signal_order["state_latest_allowed_utc"] = signal_order[
        "state_latest_allowed_utc"
    ].dt.as_unit("ns")
    states = (
        state[state_columns]
        .reset_index()
        .rename(columns={"timestamp_utc": "matched_state_time_utc"})
        .sort_values("matched_state_time_utc")
    )
    states["matched_state_time_utc"] = states[
        "matched_state_time_utc"
    ].dt.as_unit("ns")
    joined = pd.merge_asof(
        signal_order,
        states,
        left_on="state_latest_allowed_utc",
        right_on="matched_state_time_utc",
        direction="backward",
        allow_exact_matches=True,
    )
    joined["state_known_at_utc"] = (
        joined["matched_state_time_utc"] + pd.Timedelta(hours=1)
    )
    joined["state_known_lag_hours"] = (
        joined["signal_complete_utc"] - joined["state_known_at_utc"]
    ).dt.total_seconds() / 3600.0
    shock = joined["shock"].astype("boolean").fillna(True)
    compression = (
        joined["DXY_compressed"]
        .astype("boolean")
        .fillna(False)
        & joined["EURUSD_compressed"]
        .astype("boolean")
        .fillna(False)
    )
    ownership = cfg["neutral_ownership"]
    joined["neutral_owned"] = (
        joined["direction"].eq(ownership["requires_direction"])
        & joined["phase"].eq(ownership["requires_phase"])
        & ~shock
        & ~compression
        & joined["state_known_at_utc"].le(
            joined["signal_complete_utc"]
        )
        & joined["state_known_lag_hours"].ge(0.0)
    )
    return joined.sort_values("signal_complete_utc").reset_index(
        drop=True
    )


def add_decision_time_risk(
    owned: pd.DataFrame,
    m5: pd.DataFrame,
    cfg: dict[str, Any],
) -> pd.DataFrame:
    if owned.empty:
        return owned.copy()
    strategy = cfg["strategy"]
    execution = cfg["execution_contract_locked_before_census"]
    spread_floor = float(
        execution["minimum_retail_spread_pips"]
    ) * PIP
    slippage = float(
        execution["extra_slippage_pips_per_side"]
    ) * PIP
    rows: list[dict[str, Any]] = []
    for _, signal in owned.iterrows():
        record = signal.to_dict()
        completion = signal["signal_complete_utc"]
        position = int(
            m5.index.searchsorted(completion, side="left")
        )
        record["entry_bar_available"] = False
        record["risk_eligible"] = False
        record["entry_position"] = position
        if (
            position >= len(m5)
            or m5.index[position] != completion
        ):
            rows.append(record)
            continue
        record["entry_bar_available"] = True
        bar = m5.iloc[position]
        side = str(signal["side"])
        if side == "LONG":
            effective_ask = max(
                float(bar["ask_open"]),
                float(bar["bid_open"]) + spread_floor,
            )
            entry = effective_ask + slippage
        else:
            entry = float(bar["bid_open"]) - slippage
        base_distance = max(
            float(strategy["stop_atr_multiple"])
            * float(signal["atr"]),
            float(strategy["stop_range_multiple"])
            * float(signal["session_range"]),
            float(strategy["stop_floor_points"])
            * float(strategy["point"]),
        )
        if side == "LONG":
            stop = min(
                float(signal["range_low"]),
                entry - base_distance,
            )
            risk_distance = entry - stop
        else:
            stop = max(
                float(signal["range_high"]),
                entry + base_distance,
            )
            risk_distance = stop - entry
        risk_points = risk_distance / float(strategy["point"])
        record["entry_price_decision_time"] = entry
        record["stop_price_decision_time"] = stop
        record["risk_distance"] = risk_distance
        record["risk_pips"] = risk_distance / PIP
        record["risk_points"] = risk_points
        record["risk_eligible"] = bool(
            signal["neutral_owned"]
            and np.isfinite(risk_points)
            and risk_points > 0
            and risk_points
            <= float(strategy["stop_ceiling_points"])
        )
        rows.append(record)
    return pd.DataFrame(rows).sort_values(
        "signal_complete_utc"
    ).reset_index(drop=True)


def build_candidates(
    m5: pd.DataFrame,
    state: pd.DataFrame,
    cfg: dict[str, Any],
) -> pd.DataFrame:
    signals = generate_session_signals(m5, cfg)
    owned = assign_neutral_ownership(signals, state, cfg)
    candidates = add_decision_time_risk(owned, m5, cfg)
    if not candidates.empty:
        candidates["window"] = "OUTSIDE"
        for name, (start_raw, end_raw) in cfg["windows"].items():
            mask = candidates["entry_time_utc"].between(
                pd.Timestamp(start_raw),
                pd.Timestamp(end_raw),
                inclusive="both",
            )
            candidates.loc[mask, "window"] = name
    return candidates


def _count_by_window(
    eligible: pd.DataFrame,
    cfg: dict[str, Any],
) -> dict[str, int]:
    return {
        name: int(eligible["window"].eq(name).sum())
        for name in cfg["windows"]
    }


def summarize_census(
    candidates: pd.DataFrame,
    cfg: dict[str, Any],
    *,
    parent_manifests: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if candidates.empty:
        eligible = pd.DataFrame(
            {
                "entry_time_utc": pd.to_datetime([], utc=True),
                "side": pd.Series(dtype="object"),
                "window": pd.Series(dtype="object"),
                "state_known_lag_hours": pd.Series(dtype="float64"),
            }
        )
    else:
        eligible = candidates[
            candidates.get(
                "risk_eligible",
                pd.Series(False, index=candidates.index),
            ).astype(bool)
        ].copy()
    by_window = _count_by_window(eligible, cfg)
    recent_start, recent_end = cfg["recent_six_months"]
    recent = eligible["entry_time_utc"].between(
        pd.Timestamp(recent_start),
        pd.Timestamp(recent_end),
        inclusive="both",
    )
    counts_per_date = (
        eligible.groupby(eligible["entry_time_utc"].dt.date)
        .size()
        .value_counts()
        .sort_index()
    )
    maximum_lag = (
        float(eligible["state_known_lag_hours"].max())
        if len(eligible)
        else 0.0
    )
    gates = cfg["outcome_blind_capacity_gates"]
    gate_results = {
        "minimum_risk_eligible_candidates_total": len(eligible)
        >= int(gates["minimum_risk_eligible_candidates_total"]),
        "minimum_distinct_candidate_dates_total": (
            eligible["entry_time_utc"].dt.date.nunique()
            >= int(gates["minimum_distinct_candidate_dates_total"])
        ),
        "minimum_candidates_development_2019_2022": (
            by_window["development_2019_2022"]
            >= int(gates["minimum_candidates_development_2019_2022"])
        ),
        "minimum_candidates_each_full_oos_year": all(
            by_window[name]
            >= int(gates["minimum_candidates_each_full_oos_year"])
            for name in (
                "validation_2023",
                "validation_2024",
                "pseudo_oos_2025",
            )
        ),
        "minimum_candidates_pseudo_oos_2026h1": (
            by_window["pseudo_oos_2026h1"]
            >= int(gates["minimum_candidates_pseudo_oos_2026h1"])
        ),
        "minimum_candidates_each_side": all(
            int(eligible["side"].eq(side).sum())
            >= int(gates["minimum_candidates_each_side"])
            for side in ("LONG", "SHORT")
        ),
        "minimum_recent_six_month_candidates": int(recent.sum())
        >= int(gates["minimum_recent_six_month_candidates"]),
        "maximum_candidate_state_known_lag_hours": maximum_lag
        <= float(gates["maximum_candidate_state_known_lag_hours"]),
    }
    census_pass = all(gate_results.values())
    decision_columns = [
        column
        for column in eligible.columns
        if column
        not in {
            "r",
            "pnl",
            "return",
            "exit_time_utc",
            "exit_price",
            "exit_reason",
            "oracle_member",
        }
    ]
    manifest_bytes = eligible[decision_columns].to_csv(
        index=False
    ).encode("utf-8")
    return {
        "schema_version": (
            "eurusd_neutral_0608_range_breakout_transfer_census_v1"
        ),
        "campaign_id": cfg["campaign_id"],
        "family": FAMILY,
        "status": (
            "CENSUS_PASS_EXECUTION_MAY_BE_SEPARATELY_LOCKED"
            if census_pass
            else "CENSUS_FAIL_NO_PNL_ALLOWED"
        ),
        "session_signals_total": int(len(candidates)),
        "neutral_owned_signals": int(
            candidates.get(
                "neutral_owned",
                pd.Series(False, index=candidates.index),
            )
            .astype(bool)
            .sum()
        ),
        "risk_eligible_candidates_total": int(len(eligible)),
        "distinct_candidate_dates_total": int(
            eligible["entry_time_utc"].dt.date.nunique()
        ),
        "long_candidates": int(eligible["side"].eq("LONG").sum()),
        "short_candidates": int(
            eligible["side"].eq("SHORT").sum()
        ),
        "recent_six_month_candidates": int(recent.sum()),
        "by_window": by_window,
        "candidate_count_per_date_distribution": {
            str(int(count)): int(frequency)
            for count, frequency in counts_per_date.items()
        },
        "state_known_lag_hours": {
            "minimum": (
                float(eligible["state_known_lag_hours"].min())
                if len(eligible)
                else 0.0
            ),
            "median": (
                float(eligible["state_known_lag_hours"].median())
                if len(eligible)
                else 0.0
            ),
            "maximum": maximum_lag,
        },
        "candidate_manifest_sha256": hashlib.sha256(
            manifest_bytes
        ).hexdigest(),
        "parent_source_manifests": parent_manifests or {},
        "gate_results": gate_results,
        "census_pass": census_pass,
        "stop_or_target_path_loaded": False,
        "trade_exit_loaded": False,
        "eurusd_return_loaded": False,
        "eurusd_pnl_loaded": False,
        "oracle_rows_loaded": False,
        "performance_gate_evaluated": False,
        "broker_action_allowed": False,
    }


def run_census() -> tuple[
    dict[str, Any],
    dict[str, pd.DataFrame],
]:
    verify_lock()
    cfg = load_config()
    parent = load_parent_config()
    if sha256_file(PARENT_CONFIG_PATH) != cfg[
        "parent_data_and_classifier"
    ]["sha256"]:
        raise RuntimeError("Parent classifier contract drift")
    m5, state, manifests = load_inputs(parent)
    candidates = build_candidates(m5, state, cfg)
    census = summarize_census(
        candidates,
        cfg,
        parent_manifests=manifests,
    )
    eligible = candidates[
        candidates["risk_eligible"].astype(bool)
    ].copy()
    forbidden = {
        "r",
        "pnl",
        "return",
        "exit_time_utc",
        "exit_price",
        "exit_reason",
        "oracle_member",
    }
    if forbidden & set(eligible.columns):
        raise RuntimeError("Outcome field entered candidate manifest")
    return census, {
        "CANDIDATES": eligible,
        "ALL_SESSION_SIGNALS": candidates,
    }


def write_census(
    census: dict[str, Any],
    artifacts: dict[str, pd.DataFrame],
) -> None:
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    payload = (
        json.dumps(
            serialize(census),
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )
    (OUTPUT_ROOT / "CENSUS.json").write_text(
        payload,
        encoding="utf-8",
    )
    for name, frame in artifacts.items():
        frame.to_csv(OUTPUT_ROOT / f"{name}.csv", index=False)


__all__ = [
    "add_decision_time_risk",
    "assign_neutral_ownership",
    "build_candidates",
    "generate_session_signals",
    "load_config",
    "run_census",
    "summarize_census",
    "verify_lock",
    "write_census",
]
