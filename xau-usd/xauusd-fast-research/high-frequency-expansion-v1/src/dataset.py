from __future__ import annotations

from collections import defaultdict
import hashlib
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


FAMILIES = (
    "BREAK_AND_RUN",
    "DOWNSIDE_IMPULSE_RETEST",
    "OPENING_RANGE_REVERSAL",
)
REGIMES = (
    "UNSAFE_SHOCK",
    "TREND_UP",
    "TREND_DOWN",
    "COMPRESSION",
    "CHOP",
    "TRANSITION_UNKNOWN",
)
ACTIONS = (
    "FAST_1R_4H",
    "INTRADAY_1P5R_12H",
    "SWING_2R_36H",
)

MODEL_FEATURES = (
    "direction_sign",
    "mechanism_break_and_run",
    "mechanism_downside_impulse_retest",
    "mechanism_opening_range_reversal",
    "signal_source_count",
    "log_body_fraction",
    "log_dir_close_location",
    "log_dir_three_bar_move_atr",
    "log_break_distance_atr",
    "log_estimated_cost_r",
    "log_spread_atr",
    "dir_return_15m_atr",
    "dir_return_1h_atr",
    "dir_return_4h_atr",
    "dir_return_24h_atr",
    "range_1h_atr",
    "range_4h_atr",
    "dir_ema20_distance_atr",
    "dir_ema50_distance_atr",
    "efficiency_1h",
    "efficiency_4h",
    "atr_ratio_m5",
    "quote_intensity_ratio",
    "dir_tick_imbalance_5m",
    "dir_tick_imbalance_15m",
    "dir_book_imbalance_mean",
    "dir_microprice_edge_atr",
    "price_efficiency_5m",
    "spread_atr",
    "h1_adx",
    "h1_efficiency",
    "dir_h1_ema_slope_atr",
    "dir_h1_ema_distance_atr",
    "h4_adx",
    "h4_efficiency",
    "dir_h4_ema_slope_atr",
    "h4_range_width_atr",
    "h4_displacement_atr",
    "regime_unsafe_shock",
    "regime_trend_up",
    "regime_trend_down",
    "regime_compression",
    "regime_chop",
    "regime_transition_unknown",
    "hour_sin",
    "hour_cos",
    "weekday_sin",
    "weekday_cos",
    "prior_events_1h",
    "prior_events_4h",
    "prior_same_direction_1h",
    "minutes_since_prior_event_log1p",
    "action_stop_atr",
    "action_target_r",
    "action_hold_hours",
    "action_fast",
    "action_intraday",
    "action_swing",
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(4 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _wilder(values: pd.Series, period: int) -> pd.Series:
    return values.ewm(alpha=1.0 / period, adjust=False, min_periods=period).mean()


def _atr(frame: pd.DataFrame, period: int = 14) -> pd.Series:
    previous = frame["mid_close"].shift(1)
    true_range = pd.concat(
        [
            frame["mid_high"] - frame["mid_low"],
            (frame["mid_high"] - previous).abs(),
            (frame["mid_low"] - previous).abs(),
        ],
        axis=1,
    ).max(axis=1)
    return _wilder(true_range, period)


def _adx(frame: pd.DataFrame, period: int = 14) -> pd.Series:
    up = frame["mid_high"].diff()
    down = -frame["mid_low"].diff()
    plus_dm = pd.Series(np.where((up > down) & (up > 0), up, 0.0), index=frame.index)
    minus_dm = pd.Series(np.where((down > up) & (down > 0), down, 0.0), index=frame.index)
    atr_value = _atr(frame, period)
    plus_di = 100.0 * _wilder(plus_dm, period) / atr_value.replace(0.0, np.nan)
    minus_di = 100.0 * _wilder(minus_dm, period) / atr_value.replace(0.0, np.nan)
    dx = 100.0 * (plus_di - minus_di).abs() / (plus_di + minus_di).replace(0.0, np.nan)
    return _wilder(dx, period)


def _efficiency(close: pd.Series, bars: int) -> pd.Series:
    movement = close.diff().abs().rolling(bars, min_periods=bars).sum()
    return (close - close.shift(bars)).abs() / movement.replace(0.0, np.nan)


def prepare_market_features(
    m5: pd.DataFrame,
    h1: pd.DataFrame,
    classified_h4: pd.DataFrame,
) -> pd.DataFrame:
    frame = m5.copy()
    frame["atr_m5"] = _atr(frame, 14)
    atr_value = frame["atr_m5"].replace(0.0, np.nan)
    for bars, label in ((3, "15m"), (12, "1h"), (48, "4h"), (288, "24h")):
        frame[f"return_{label}_atr"] = (frame["mid_close"] - frame["mid_close"].shift(bars)) / atr_value
    frame["range_1h_atr"] = (
        frame["mid_high"].rolling(12, min_periods=12).max()
        - frame["mid_low"].rolling(12, min_periods=12).min()
    ) / atr_value
    frame["range_4h_atr"] = (
        frame["mid_high"].rolling(48, min_periods=48).max()
        - frame["mid_low"].rolling(48, min_periods=48).min()
    ) / atr_value
    frame["efficiency_1h"] = _efficiency(frame["mid_close"], 12)
    frame["efficiency_4h"] = _efficiency(frame["mid_close"], 48)
    frame["ema20_m5"] = frame["mid_close"].ewm(span=20, adjust=False, min_periods=20).mean()
    frame["ema50_m5"] = frame["mid_close"].ewm(span=50, adjust=False, min_periods=50).mean()
    frame["ema20_distance_atr"] = (frame["mid_close"] - frame["ema20_m5"]) / atr_value
    frame["ema50_distance_atr"] = (frame["mid_close"] - frame["ema50_m5"]) / atr_value
    frame["spread_atr"] = (frame["ask_close"] - frame["bid_close"]) / atr_value
    if "atr_ratio" not in frame:
        frame["atr_ratio"] = frame["atr_m5"] / frame["atr_m5"].shift(1).rolling(288, min_periods=144).median()

    hourly = h1.copy()
    hourly["h1_atr"] = _atr(hourly, 14)
    hourly["h1_adx"] = _adx(hourly, 14)
    hourly["h1_efficiency"] = _efficiency(hourly["mid_close"], 24)
    hourly["h1_ema20"] = hourly["mid_close"].ewm(span=20, adjust=False, min_periods=20).mean()
    hourly["h1_ema50"] = hourly["mid_close"].ewm(span=50, adjust=False, min_periods=50).mean()
    hourly["h1_ema_slope_atr"] = (
        hourly["h1_ema20"] - hourly["h1_ema20"].shift(3)
    ) / hourly["h1_atr"].replace(0.0, np.nan)
    hourly["h1_ema_distance_atr"] = (
        hourly["mid_close"] - hourly["h1_ema50"]
    ) / hourly["h1_atr"].replace(0.0, np.nan)
    h1_columns = [
        "timestamp_utc",
        "h1_adx",
        "h1_efficiency",
        "h1_ema_slope_atr",
        "h1_ema_distance_atr",
    ]
    frame = pd.merge_asof(
        frame.sort_values("timestamp_utc"),
        hourly[h1_columns].sort_values("timestamp_utc"),
        on="timestamp_utc",
        direction="backward",
        allow_exact_matches=True,
    )
    h4_columns = [
        "timestamp_utc",
        "regime",
        "adx_h4",
        "er_h4",
        "ema_slope_atr_h4",
        "range_width_atr_h4",
        "displacement_atr_h4",
    ]
    frame = pd.merge_asof(
        frame.sort_values("timestamp_utc"),
        classified_h4[h4_columns].sort_values("timestamp_utc"),
        on="timestamp_utc",
        direction="backward",
        allow_exact_matches=True,
    )
    return frame.sort_values("timestamp_utc", kind="mergesort").reset_index(drop=True)


def _read_source(repo_root: Path, source: dict[str, Any]) -> pd.DataFrame:
    path = repo_root / str(source["path"])
    if not path.is_file():
        raise FileNotFoundError(path)
    actual = sha256_file(path)
    if actual != str(source["sha256"]):
        raise ValueError(f"Candidate source hash mismatch for {path}: {actual}")
    columns = [
        "timestamp_broker",
        "stage",
        "direction",
        "spread_points",
        "signal_close",
        "atr",
        "body_fraction",
        "close_location",
        "three_bar_move_atr",
        "break_distance_atr",
        "estimated_cost_r",
    ]
    frame = pd.read_csv(path, sep="\t", usecols=columns)
    frame = frame.loc[frame["stage"].eq("WOULD_SIGNAL")].copy()
    frame["family_id"] = str(source["family_id"])
    frame["signal_time"] = pd.to_datetime(
        frame.pop("timestamp_broker"), format="%Y.%m.%d %H:%M:%S", utc=True
    )
    for column in columns[3:]:
        frame[column] = pd.to_numeric(frame[column], errors="coerce")
    return frame


def _prior_event_features(events: pd.DataFrame) -> pd.DataFrame:
    result = events.sort_values(["signal_time", "direction"], kind="mergesort").reset_index(drop=True)
    nanoseconds = result["signal_time"].astype("int64").to_numpy()
    first_at_time = np.searchsorted(nanoseconds, nanoseconds, side="left")
    hour_ns = int(pd.Timedelta(hours=1).value)
    four_hour_ns = int(pd.Timedelta(hours=4).value)
    result["prior_events_1h"] = first_at_time - np.searchsorted(
        nanoseconds, nanoseconds - hour_ns, side="left"
    )
    result["prior_events_4h"] = first_at_time - np.searchsorted(
        nanoseconds, nanoseconds - four_hour_ns, side="left"
    )

    same_direction_counts = np.zeros(len(result), dtype=int)
    prior_minutes = np.full(len(result), 24.0 * 60.0, dtype=float)
    direction_times: dict[str, list[int]] = defaultdict(list)
    prior_time: int | None = None
    for index, row in enumerate(result.itertuples(index=False)):
        timestamp = int(pd.Timestamp(row.signal_time).value)
        history = direction_times[str(row.direction)]
        same_direction_counts[index] = len(history) - int(np.searchsorted(history, timestamp - hour_ns, side="left"))
        if prior_time is not None and timestamp > prior_time:
            prior_minutes[index] = min(24.0 * 60.0, (timestamp - prior_time) / 60_000_000_000)
        history.append(timestamp)
        prior_time = timestamp if prior_time is None else max(prior_time, timestamp)
    result["prior_same_direction_1h"] = same_direction_counts
    result["minutes_since_prior_event_log1p"] = np.log1p(prior_minutes)
    return result


def build_candidate_events(
    repo_root: Path,
    config: dict[str, Any],
    market: pd.DataFrame,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    raw = pd.concat(
        [_read_source(repo_root, source) for source in config["candidate_sources"]],
        ignore_index=True,
    )
    start = pd.Timestamp(config["source"]["start_utc"])
    end = pd.Timestamp(config["source"]["end_exclusive_utc"])
    raw = raw.loc[
        (raw["signal_time"] >= start)
        & (raw["signal_time"] < end)
        & (raw["signal_time"].dt.weekday < 5)
        & raw["direction"].isin(["LONG", "SHORT"])
    ].copy()
    raw["feature_time"] = raw["signal_time"].dt.floor("5min")
    seconds_after_boundary = (raw["signal_time"] - raw["feature_time"]).dt.total_seconds()
    if seconds_after_boundary.max() >= 5 * 60:
        raise ValueError("Candidate timestamp cannot be assigned to a completed M5 boundary")

    numeric = [
        "spread_points",
        "signal_close",
        "atr",
        "body_fraction",
        "close_location",
        "three_bar_move_atr",
        "break_distance_atr",
        "estimated_cost_r",
    ]
    grouped = raw.groupby(["signal_time", "feature_time", "direction"], sort=True, observed=True)
    events = grouped[numeric].median().reset_index()
    family_flags = (
        raw.assign(value=1)
        .pivot_table(
            index=["signal_time", "feature_time", "direction"],
            columns="family_id",
            values="value",
            aggfunc="max",
            fill_value=0,
        )
        .reset_index()
    )
    family_flags.columns.name = None
    events = events.merge(
        family_flags,
        on=["signal_time", "feature_time", "direction"],
        how="left",
        validate="one_to_one",
    )
    events["signal_source_count"] = grouped["family_id"].nunique().to_numpy()
    for family in FAMILIES:
        if family not in events:
            events[family] = 0
    events["mechanism_break_and_run"] = events["BREAK_AND_RUN"].astype(float)
    events["mechanism_downside_impulse_retest"] = events["DOWNSIDE_IMPULSE_RETEST"].astype(float)
    events["mechanism_opening_range_reversal"] = events["OPENING_RANGE_REVERSAL"].astype(float)
    events["direction_sign"] = np.where(events["direction"].eq("LONG"), 1.0, -1.0)
    events["event_id"] = (
        events["signal_time"].dt.strftime("%Y%m%dT%H%M%SZ") + "_" + events["direction"]
    )
    events = _prior_event_features(events)

    market_columns = [
        "timestamp_utc",
        "mid_close",
        "atr_m5",
        "return_15m_atr",
        "return_1h_atr",
        "return_4h_atr",
        "return_24h_atr",
        "range_1h_atr",
        "range_4h_atr",
        "efficiency_1h",
        "efficiency_4h",
        "ema20_distance_atr",
        "ema50_distance_atr",
        "atr_ratio",
        "quote_intensity_ratio",
        "tick_imbalance_5m",
        "tick_imbalance_15m",
        "tick_book_imbalance_mean",
        "tick_microprice_edge_mean",
        "price_efficiency_5m",
        "spread_atr",
        "h1_adx",
        "h1_efficiency",
        "h1_ema_slope_atr",
        "h1_ema_distance_atr",
        "regime",
        "adx_h4",
        "er_h4",
        "ema_slope_atr_h4",
        "range_width_atr_h4",
        "displacement_atr_h4",
    ]
    events = events.merge(
        market[market_columns],
        left_on="feature_time",
        right_on="timestamp_utc",
        how="left",
        validate="many_to_one",
    ).drop(columns="timestamp_utc")
    sign = events["direction_sign"]
    events["log_body_fraction"] = events["body_fraction"]
    events["log_dir_close_location"] = np.where(
        sign > 0, events["close_location"], 1.0 - events["close_location"]
    )
    events["log_dir_three_bar_move_atr"] = sign * events["three_bar_move_atr"]
    events["log_break_distance_atr"] = events["break_distance_atr"]
    events["log_estimated_cost_r"] = events["estimated_cost_r"]
    events["log_spread_atr"] = (
        events["spread_points"] * 0.01 / events["atr"].replace(0.0, np.nan)
    )
    for horizon in ("15m", "1h", "4h", "24h"):
        events[f"dir_return_{horizon}_atr"] = sign * events[f"return_{horizon}_atr"]
    events["dir_ema20_distance_atr"] = sign * events["ema20_distance_atr"]
    events["dir_ema50_distance_atr"] = sign * events["ema50_distance_atr"]
    events["atr_ratio_m5"] = events["atr_ratio"]
    events["dir_tick_imbalance_5m"] = sign * events["tick_imbalance_5m"]
    events["dir_tick_imbalance_15m"] = sign * events["tick_imbalance_15m"]
    events["dir_book_imbalance_mean"] = sign * events["tick_book_imbalance_mean"]
    events["dir_microprice_edge_atr"] = (
        sign * events["tick_microprice_edge_mean"] / events["atr_m5"].replace(0.0, np.nan)
    )
    events["dir_h1_ema_slope_atr"] = sign * events["h1_ema_slope_atr"]
    events["dir_h1_ema_distance_atr"] = sign * events["h1_ema_distance_atr"]
    events["h4_adx"] = events["adx_h4"]
    events["h4_efficiency"] = events["er_h4"]
    events["dir_h4_ema_slope_atr"] = sign * events["ema_slope_atr_h4"]
    events["h4_range_width_atr"] = events["range_width_atr_h4"]
    events["h4_displacement_atr"] = events["displacement_atr_h4"]
    for regime in REGIMES:
        events[f"regime_{regime.lower()}"] = events["regime"].eq(regime).astype(float)
    hour = events["signal_time"].dt.hour + events["signal_time"].dt.minute / 60.0
    weekday = events["signal_time"].dt.weekday
    events["hour_sin"] = np.sin(2.0 * np.pi * hour / 24.0)
    events["hour_cos"] = np.cos(2.0 * np.pi * hour / 24.0)
    events["weekday_sin"] = np.sin(2.0 * np.pi * weekday / 5.0)
    events["weekday_cos"] = np.cos(2.0 * np.pi * weekday / 5.0)
    events["alignment_error_usd"] = (events["signal_close"] - events["mid_close"]).abs()
    events["alignment_error_atr"] = events["alignment_error_usd"] / events["atr_m5"].replace(0.0, np.nan)

    base_features = [column for column in MODEL_FEATURES if not column.startswith("action_")]
    finite = np.isfinite(events[base_features]).all(axis=1)
    events = events.loc[finite].sort_values(["signal_time", "direction"], kind="mergesort").reset_index(drop=True)
    if events["event_id"].duplicated().any():
        raise ValueError("Duplicate candidate event IDs detected")
    evidence = {
        "raw_would_signal_rows_in_window": int(len(raw)),
        "event_rows": int(len(events)),
        "start": events["signal_time"].min().isoformat(),
        "end": events["signal_time"].max().isoformat(),
        "alignment_error_usd_median": float(events["alignment_error_usd"].median()),
        "alignment_error_usd_p95": float(events["alignment_error_usd"].quantile(0.95)),
        "alignment_error_atr_median": float(events["alignment_error_atr"].median()),
        "alignment_error_atr_p95": float(events["alignment_error_atr"].quantile(0.95)),
        "family_candidate_rows": {
            family: int(raw["family_id"].eq(family).sum()) for family in FAMILIES
        },
    }
    return events, evidence


def _execution_arrays(m5: pd.DataFrame) -> dict[str, Any]:
    return {
        "starts": m5["bar_start_utc"].dt.tz_localize(None).to_numpy(),
        "ends": m5["bar_end_utc"].dt.tz_localize(None).to_numpy(),
        **{
            column: m5[column].to_numpy(dtype=float)
            for column in (
                "bid_open",
                "bid_high",
                "bid_low",
                "bid_close",
                "ask_open",
                "ask_high",
                "ask_low",
                "ask_close",
            )
        },
    }


def label_action(
    arrays: dict[str, Any],
    row: Any,
    action: dict[str, Any],
    execution: dict[str, Any],
) -> dict[str, Any] | None:
    signal_time = pd.Timestamp(row.signal_time).tz_localize(None).to_datetime64()
    entry_index = int(np.searchsorted(arrays["starts"], signal_time, side="left"))
    if entry_index >= len(arrays["starts"]):
        return None
    gap_minutes = float((arrays["starts"][entry_index] - signal_time) / np.timedelta64(1, "m"))
    if gap_minutes < 0 or gap_minutes > float(execution["maximum_entry_gap_minutes"]):
        return None
    direction = str(row.direction)
    sign = 1.0 if direction == "LONG" else -1.0
    entry = float(arrays["ask_open"][entry_index] if direction == "LONG" else arrays["bid_open"][entry_index])
    atr_value = float(row.atr_m5)
    risk = max(float(action["stop_atr"]) * atr_value, float(action["minimum_stop_usd"]))
    if not np.isfinite(risk) or risk <= 0 or risk > float(execution["maximum_research_risk_usd"]):
        return None
    spread = float(arrays["ask_open"][entry_index] - arrays["bid_open"][entry_index])
    if spread / risk > float(execution["maximum_entry_spread_r"]):
        return None
    stop = entry - sign * risk
    target = entry + sign * float(action["target_r"]) * risk
    deadline = arrays["starts"][entry_index] + np.timedelta64(
        int(float(action["maximum_hold_hours"]) * 60), "m"
    )
    end_index = min(
        len(arrays["starts"]),
        int(np.searchsorted(arrays["starts"], deadline, side="right")) + 1,
    )
    exit_index = entry_index
    exit_price = entry
    exit_reason = "END_OF_DATA"
    exit_at_open = False
    ambiguous = False
    maximum_favorable = 0.0
    maximum_adverse = 0.0
    for position in range(entry_index, end_index):
        if arrays["starts"][position] >= deadline:
            exit_index = position
            exit_reason = "MAX_HOLD"
            exit_at_open = True
            exit_price = float(
                arrays["bid_open"][position] if direction == "LONG" else arrays["ask_open"][position]
            )
            break
        if direction == "LONG":
            favorable = float(arrays["bid_high"][position] - entry)
            adverse = float(entry - arrays["bid_low"][position])
            if arrays["bid_open"][position] < stop:
                exit_index, exit_price, exit_reason, exit_at_open = (
                    position,
                    float(arrays["bid_open"][position]),
                    "GAP_THROUGH_STOP",
                    True,
                )
                break
            if arrays["bid_open"][position] >= target:
                exit_index, exit_price, exit_reason, exit_at_open = position, target, "TARGET_GAP", True
                break
            stop_hit = arrays["bid_low"][position] <= stop
            target_hit = arrays["bid_high"][position] >= target
        else:
            favorable = float(entry - arrays["ask_low"][position])
            adverse = float(arrays["ask_high"][position] - entry)
            if arrays["ask_open"][position] > stop:
                exit_index, exit_price, exit_reason, exit_at_open = (
                    position,
                    float(arrays["ask_open"][position]),
                    "GAP_THROUGH_STOP",
                    True,
                )
                break
            if arrays["ask_open"][position] <= target:
                exit_index, exit_price, exit_reason, exit_at_open = position, target, "TARGET_GAP", True
                break
            stop_hit = arrays["ask_high"][position] >= stop
            target_hit = arrays["ask_low"][position] <= target
        maximum_favorable = max(maximum_favorable, favorable)
        maximum_adverse = max(maximum_adverse, adverse)
        if stop_hit:
            exit_index, exit_price = position, stop
            ambiguous = bool(target_hit)
            exit_reason = "AMBIGUOUS_M5_STOP_FIRST" if ambiguous else "STOP"
            break
        if target_hit:
            exit_index, exit_price, exit_reason = position, target, "TARGET"
            break
        exit_index = position
        exit_price = float(
            arrays["bid_close"][position] if direction == "LONG" else arrays["ask_close"][position]
        )
    exit_time = arrays["starts"][exit_index] if exit_at_open else arrays["ends"][exit_index]
    net_r = sign * (exit_price - entry) / risk
    holding_days = max(
        0.0,
        float((exit_time - arrays["starts"][entry_index]) / np.timedelta64(1, "D")),
    )
    risk_usd = risk * float(execution["ounces_at_lot_size"])
    extra_cost_r = (
        float(execution["extra_execution_cost_usd"])
        + holding_days * float(execution["holding_cost_per_24h_usd"])
    ) / risk_usd
    stress_net_r = net_r - extra_cost_r - float(execution["stress_slippage_r"])
    return {
        "entry_time": pd.Timestamp(arrays["starts"][entry_index], tz="UTC"),
        "exit_time": pd.Timestamp(exit_time, tz="UTC"),
        "entry_price": entry,
        "exit_price": exit_price,
        "stop_price": stop,
        "target_price": target,
        "risk_usd": risk_usd,
        "entry_spread_r": spread / risk,
        "net_r": net_r,
        "stress_net_r": stress_net_r,
        "mfe_r": maximum_favorable / risk,
        "mae_r": maximum_adverse / risk,
        "holding_minutes": float(
            (exit_time - arrays["starts"][entry_index]) / np.timedelta64(1, "m")
        ),
        "exit_reason": exit_reason,
        "ambiguous_m5": ambiguous,
        "current_account_feasible": risk_usd <= float(execution["current_account_risk_usd"]),
    }


def build_action_labels(
    events: pd.DataFrame,
    m5: pd.DataFrame,
    actions: list[dict[str, Any]],
    execution: dict[str, Any],
) -> pd.DataFrame:
    arrays = _execution_arrays(m5)
    rows: list[dict[str, Any]] = []
    for event in events.itertuples(index=False):
        base = event._asdict()
        for action in actions:
            outcome = label_action(arrays, event, action, execution)
            if outcome is None:
                continue
            action_id = str(action["action_id"])
            row = {
                **base,
                "action_id": action_id,
                "action_stop_atr": float(action["stop_atr"]),
                "action_target_r": float(action["target_r"]),
                "action_hold_hours": float(action["maximum_hold_hours"]),
                "action_fast": float(action_id == "FAST_1R_4H"),
                "action_intraday": float(action_id == "INTRADAY_1P5R_12H"),
                "action_swing": float(action_id == "SWING_2R_36H"),
                **outcome,
            }
            rows.append(row)
    result = pd.DataFrame(rows).sort_values(
        ["signal_time", "direction", "action_id"], kind="mergesort"
    ).reset_index(drop=True)
    if not result.empty and not np.isfinite(result[list(MODEL_FEATURES)]).all(axis=None):
        raise ValueError("Non-finite model feature in action ledger")
    return result
