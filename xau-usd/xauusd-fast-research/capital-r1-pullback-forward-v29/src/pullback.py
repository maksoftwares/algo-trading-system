from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
from statistics import median
from typing import Any, Iterable, Mapping, Sequence

import numpy as np
import pandas as pd


UTC = timezone.utc
REGIME_NAMES = ("UNKNOWN", "SHOCK", "UPTREND", "DOWNTREND", "COMPRESSION", "CHOP")
PARITY_COLUMNS = (
    "decision_time_utc",
    "raw_signal",
    "direction",
    "signal_reason",
    "regime",
    "guard_action",
    "guard_reason",
    "stop_points",
    "break_distance_atr",
    "estimated_cost_r",
    "spread_points",
)
CANDIDATE_COLUMNS = (
    "candidate_id",
    "specialist_id",
    "decision_time_utc",
    "confirmation_bar_time_utc",
    "direction",
    "signal_reason",
    "regime",
    "stop_points",
    "break_distance_atr",
    "estimated_cost_r",
    "spread_points",
    "rule_dependency_sha256",
    "trade_permission",
    "broker_action_allowed",
    "python_execution_authorized",
)


@dataclass(frozen=True)
class PullbackSettings:
    atr_period: int = 14
    h1_fast_period: int = 20
    h1_slow_period: int = 50
    slope_lag: int = 5
    lookback_bars: int = 6
    touch_atr: float = 0.25
    stop_buffer_atr: float = 0.25
    min_body_fraction: float = 0.35
    close_location: float = 0.65
    session_start_hour: int = 9
    session_end_hour: int = 15
    stop_floor_points: float = 350.0
    stop_ceiling_points: float = 2200.0
    max_spread_points: float = 75.0
    max_estimated_cost_r: float = 0.15
    point_size: float = 0.01
    regime_fast_period: int = 20
    regime_slow_period: int = 50
    regime_persistence_d1_bars: int = 2
    regime_shock_h1_range_atr_multiple: float = 3.0
    regime_shock_d1_atr_percentile_min: float = 95.0
    regime_shock_d1_lookback: int = 60
    regime_compression_d1_atr_percentile_max: float = 30.0
    regime_compression_box_days: int = 5
    regime_compression_range_median_max: float = 1.0

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "PullbackSettings":
        unknown = set(value) - set(cls.__dataclass_fields__)
        if unknown:
            raise ValueError(f"Unknown pullback settings: {sorted(unknown)}")
        return cls(**dict(value))


@dataclass(frozen=True)
class PreparedBars:
    m15: pd.DataFrame
    h1: pd.DataFrame
    h4: pd.DataFrame
    d1: pd.DataFrame


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def dependency_sha256(repo_root: Path, paths: Iterable[str]) -> str:
    digest = hashlib.sha256()
    for relative in sorted(paths):
        path = repo_root / relative
        if not path.is_file():
            raise FileNotFoundError(path)
        digest.update(relative.replace("\\", "/").encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def utc_timestamp(value: Any) -> pd.Timestamp:
    result = pd.Timestamp(value)
    if result.tzinfo is None:
        return result.tz_localize("UTC")
    return result.tz_convert("UTC")


def utc_text(value: Any) -> str:
    return utc_timestamp(value).isoformat().replace("+00:00", "Z")


def rates_to_frame(rates: Any) -> pd.DataFrame:
    frame = pd.DataFrame(rates)
    required = {"time", "open", "high", "low", "close"}
    if frame.empty or not required <= set(frame.columns):
        raise ValueError("MT5 rates are empty or malformed")
    result = frame.loc[:, ["time", "open", "high", "low", "close"]].copy()
    result["time"] = pd.to_datetime(result["time"], unit="s", utc=True)
    for column in ("open", "high", "low", "close"):
        result[column] = pd.to_numeric(result[column], errors="raise").astype(float)
    result = (
        result.drop_duplicates("time", keep="last")
        .sort_values("time")
        .reset_index(drop=True)
    )
    validate_bars(result)
    return result


def validate_bars(frame: pd.DataFrame) -> None:
    if frame.empty:
        raise ValueError("bar frame is empty")
    times = pd.DatetimeIndex(pd.to_datetime(frame["time"], utc=True))
    if not times.is_monotonic_increasing or times.has_duplicates:
        raise ValueError("bar timestamps must be unique and increasing")
    values = frame[["open", "high", "low", "close"]].to_numpy(dtype=float)
    if not np.isfinite(values).all() or (values <= 0.0).any():
        raise ValueError("bar OHLC must be finite and positive")
    opens, highs, lows, closes = values.T
    if (
        (highs < lows).any()
        or (lows > np.minimum(opens, closes)).any()
        or (highs < np.maximum(opens, closes)).any()
    ):
        raise ValueError("bar OHLC ranges are invalid")


def ema(values: Sequence[float] | np.ndarray, period: int) -> np.ndarray:
    source = np.asarray(values, dtype=float)
    if source.size == 0:
        return source.copy()
    if period < 1:
        raise ValueError("EMA period must be positive")
    output = np.empty(source.size, dtype=float)
    output[0] = source[0]
    alpha = 2.0 / (period + 1.0)
    for index in range(1, source.size):
        output[index] = alpha * source[index] + (1.0 - alpha) * output[index - 1]
    return output


def mt5_atr(frame: pd.DataFrame, period: int) -> np.ndarray:
    if period < 1:
        raise ValueError("ATR period must be positive")
    high = frame["high"].to_numpy(dtype=float)
    low = frame["low"].to_numpy(dtype=float)
    close = frame["close"].to_numpy(dtype=float)
    output = np.full(len(frame), np.nan, dtype=float)
    if len(frame) <= period:
        return output
    tr = np.full(len(frame), np.nan, dtype=float)
    tr[1:] = np.maximum.reduce(
        (
            high[1:] - low[1:],
            np.abs(high[1:] - close[:-1]),
            np.abs(low[1:] - close[:-1]),
        )
    )
    for index in range(period, len(frame)):
        output[index] = float(np.mean(tr[index - period + 1 : index + 1]))
    return output


def prepare_indicator_frame(
    frame: pd.DataFrame, settings: PullbackSettings
) -> pd.DataFrame:
    result = frame.copy().reset_index(drop=True)
    close = result["close"].to_numpy(dtype=float)
    result["atr"] = mt5_atr(result, settings.atr_period)
    result["ema_fast"] = ema(close, settings.regime_fast_period)
    result["ema_slow"] = ema(close, settings.regime_slow_period)
    result.attrs["time_ns"] = pd.DatetimeIndex(result["time"]).as_unit("ns").asi8.copy()
    return result


def prepare_bars(
    m15: pd.DataFrame,
    h1: pd.DataFrame,
    h4: pd.DataFrame,
    d1: pd.DataFrame,
    settings: PullbackSettings,
) -> PreparedBars:
    frames = [m15, h1, h4, d1]
    for frame in frames:
        validate_bars(frame)
    return PreparedBars(
        m15=prepare_indicator_frame(m15, settings),
        h1=prepare_indicator_frame(h1, settings),
        h4=prepare_indicator_frame(h4, settings),
        d1=prepare_indicator_frame(d1, settings),
    )


def completed_index(frame: pd.DataFrame, decision_time: Any) -> int:
    decision = utc_timestamp(decision_time).value
    times = frame.attrs.get("time_ns")
    if times is None:
        times = (
            pd.DatetimeIndex(pd.to_datetime(frame["time"], utc=True)).as_unit("ns").asi8
        )
    # Native shift 1 becomes complete only when the next native bar opens.
    return int(np.searchsorted(times, decision, side="right") - 2)


def percentile_rank(values: np.ndarray, current: float) -> float:
    valid = values[np.isfinite(values) & (values > 0.0)]
    if valid.size == 0 or not np.isfinite(current) or current <= 0.0:
        return 100.0
    return 100.0 * float(np.count_nonzero(valid <= current)) / float(valid.size)


def _trend_stack(
    frame: pd.DataFrame, index: int, uptrend: bool, settings: PullbackSettings
) -> bool:
    lag = settings.slope_lag
    if index < settings.regime_slow_period + lag:
        return False
    close = float(frame.at[index, "close"])
    fast = float(frame.at[index, "ema_fast"])
    slow = float(frame.at[index, "ema_slow"])
    fast_prior = float(frame.at[index - lag, "ema_fast"])
    slow_prior = float(frame.at[index - lag, "ema_slow"])
    if uptrend:
        return close > fast > slow and fast >= fast_prior and slow >= slow_prior
    return close < fast < slow and fast <= fast_prior and slow <= slow_prior


def classify_regime(
    prepared: PreparedBars, decision_time: Any, settings: PullbackSettings
) -> str:
    h1_i = completed_index(prepared.h1, decision_time)
    h4_i = completed_index(prepared.h4, decision_time)
    d1_i = completed_index(prepared.d1, decision_time)
    if (
        h1_i < settings.atr_period
        or h4_i < settings.regime_slow_period + settings.slope_lag
    ):
        return "UNKNOWN"
    if d1_i < max(251, settings.regime_slow_period + settings.slope_lag + 1):
        return "UNKNOWN"
    h1_atr = float(prepared.h1.at[h1_i, "atr"])
    d1_atr = float(prepared.d1.at[d1_i, "atr"])
    if (
        not np.isfinite(h1_atr)
        or not np.isfinite(d1_atr)
        or h1_atr <= 0.0
        or d1_atr <= 0.0
    ):
        return "UNKNOWN"
    h1_range = float(prepared.h1.at[h1_i, "high"] - prepared.h1.at[h1_i, "low"])
    if h1_range >= settings.regime_shock_h1_range_atr_multiple * h1_atr:
        return "SHOCK"
    d1_atrs = prepared.d1["atr"].to_numpy(dtype=float)
    shock_window = d1_atrs[d1_i - settings.regime_shock_d1_lookback + 1 : d1_i + 1]
    if (
        percentile_rank(shock_window, d1_atr)
        >= settings.regime_shock_d1_atr_percentile_min
    ):
        return "SHOCK"
    d1_up = all(
        _trend_stack(prepared.d1, d1_i - offset, True, settings)
        for offset in range(settings.regime_persistence_d1_bars)
    )
    if d1_up and _trend_stack(prepared.h4, h4_i, True, settings):
        return "UPTREND"
    d1_down = all(
        _trend_stack(prepared.d1, d1_i - offset, False, settings)
        for offset in range(settings.regime_persistence_d1_bars)
    )
    if d1_down and _trend_stack(prepared.h4, h4_i, False, settings):
        return "DOWNTREND"
    compression_window = d1_atrs[d1_i - 251 : d1_i + 1]
    box = prepared.d1.iloc[d1_i - settings.regime_compression_box_days + 1 : d1_i + 1]
    box_width = float(box["high"].max() - box["low"].min())
    recent_ranges = (
        prepared.d1.iloc[d1_i - 19 : d1_i + 1]["high"]
        - prepared.d1.iloc[d1_i - 19 : d1_i + 1]["low"]
    )
    median_range = float(median(recent_ranges.to_list()))
    if box_width <= 0.0 or median_range <= 0.0:
        return "UNKNOWN"
    if (
        percentile_rank(compression_window, d1_atr)
        <= settings.regime_compression_d1_atr_percentile_max
        and box_width / settings.regime_compression_box_days
        <= settings.regime_compression_range_median_max * median_range
    ):
        return "COMPRESSION"
    return "CHOP"


def evaluate_decision(
    prepared: PreparedBars,
    decision_time: Any,
    spread_points: float,
    settings: PullbackSettings,
) -> dict[str, Any]:
    decision = utc_timestamp(decision_time)
    result: dict[str, Any] = {
        "decision_time_utc": decision,
        "raw_signal": False,
        "direction": "NONE",
        "signal_reason": "no_m15_independent_candidate",
        "regime": "NOT_EVALUATED",
        "guard_action": "NO_SIGNAL",
        "guard_reason": "no_m15_independent_candidate",
        "stop_points": np.nan,
        "break_distance_atr": np.nan,
        "estimated_cost_r": np.nan,
        "spread_points": float(spread_points),
    }
    m15_i = completed_index(prepared.m15, decision)
    h1_i = completed_index(prepared.h1, decision)
    if (
        m15_i < settings.lookback_bars - 1
        or h1_i < settings.h1_slow_period + settings.slope_lag
    ):
        return result
    h1_close = float(prepared.h1.at[h1_i, "close"])
    h1_fast = float(prepared.h1.at[h1_i, "ema_fast"])
    h1_slow = float(prepared.h1.at[h1_i, "ema_slow"])
    h1_fast_prior = float(prepared.h1.at[h1_i - settings.slope_lag, "ema_fast"])
    h1_atr = float(prepared.h1.at[h1_i, "atr"])
    confirmation_atr = float(prepared.m15.at[m15_i, "atr"])
    if not all(
        np.isfinite(value) and value > 0.0
        for value in (
            h1_close,
            h1_fast,
            h1_slow,
            h1_fast_prior,
            h1_atr,
            confirmation_atr,
        )
    ):
        return result
    if not (h1_close > h1_fast > h1_slow and h1_fast >= h1_fast_prior):
        return result
    bar = prepared.m15.iloc[m15_i]
    bar_range = float(bar["high"] - bar["low"])
    if bar_range <= 0.0:
        return result
    body_fraction = abs(float(bar["close"] - bar["open"])) / bar_range
    close_location = float(bar["close"] - bar["low"]) / bar_range
    if (
        float(bar["close"]) <= float(bar["open"])
        or float(bar["close"]) <= h1_fast
        or body_fraction < settings.min_body_fraction
        or close_location < settings.close_location
    ):
        return result
    lookback = prepared.m15.iloc[m15_i - settings.lookback_bars + 1 : m15_i + 1]
    touch_zone = settings.touch_atr * h1_atr
    touched = bool(
        (
            (lookback["low"] <= h1_fast + touch_zone)
            & (lookback["high"] >= h1_fast - touch_zone)
        ).any()
    )
    if not touched:
        return result
    swing_low = float(lookback["low"].min())
    stop_distance = float(bar["close"]) - (
        swing_low - settings.stop_buffer_atr * confirmation_atr
    )
    if stop_distance <= 0.0:
        return result
    raw_stop_points = stop_distance / settings.point_size
    stop_points = max(raw_stop_points, settings.stop_floor_points)
    estimated_cost_r = float(spread_points) / stop_points
    break_distance_atr = (float(bar["close"]) - h1_fast) / h1_atr
    regime = classify_regime(prepared, decision, settings)
    result.update(
        {
            "raw_signal": True,
            "direction": "LONG",
            "signal_reason": "R1_H1_EMA_PULLBACK_LONG_M15",
            "regime": regime,
            "guard_action": "ORDER_SEND_OK",
            "guard_reason": "pass",
            "stop_points": stop_points,
            "break_distance_atr": break_distance_atr,
            "estimated_cost_r": estimated_cost_r,
        }
    )
    if not settings.session_start_hour <= decision.hour < settings.session_end_hour:
        result.update(
            guard_action="GUARD_BLOCK", guard_reason="directional_session_filter_block"
        )
    elif regime != "UPTREND":
        result.update(
            guard_action="GUARD_BLOCK",
            guard_reason=f"regime_router_block_long_r1_uptrend_only_state_{regime.lower()}",
        )
    elif spread_points > settings.max_spread_points:
        result.update(guard_action="GUARD_BLOCK", guard_reason="spread_too_high")
    elif estimated_cost_r > settings.max_estimated_cost_r:
        result.update(
            guard_action="GUARD_BLOCK", guard_reason="estimated_cost_r_too_high"
        )
    elif stop_points > settings.stop_ceiling_points:
        result.update(guard_action="GUARD_BLOCK", guard_reason="stop_ceiling_exceeded")
    return result


def evaluate_decisions(
    prepared: PreparedBars,
    decisions: pd.DataFrame,
    settings: PullbackSettings,
) -> pd.DataFrame:
    required = {"decision_time_utc", "spread_points"}
    if not required <= set(decisions.columns):
        raise ValueError(
            f"decision frame missing columns: {sorted(required - set(decisions.columns))}"
        )
    rows = [
        evaluate_decision(
            prepared, row.decision_time_utc, float(row.spread_points), settings
        )
        for row in decisions.itertuples(index=False)
    ]
    result = pd.DataFrame(rows, columns=PARITY_COLUMNS)
    if result["decision_time_utc"].duplicated().any():
        raise ValueError("decision timestamps are duplicated")
    return result


def candidate_id(decision_time: Any, dependency_digest: str) -> str:
    payload = (
        f"V29|R1_PULLBACK_LONG|{utc_text(decision_time)}|{dependency_digest}".encode(
            "ascii"
        )
    )
    return hashlib.sha256(payload).hexdigest()[:32]


def candidates_from_evaluations(
    evaluations: pd.DataFrame, dependency_digest: str
) -> pd.DataFrame:
    passed = evaluations.loc[
        evaluations["raw_signal"] & evaluations["guard_action"].eq("ORDER_SEND_OK")
    ].copy()
    rows: list[dict[str, Any]] = []
    for row in passed.itertuples(index=False):
        decision = utc_timestamp(row.decision_time_utc)
        rows.append(
            {
                "candidate_id": candidate_id(decision, dependency_digest),
                "specialist_id": "R1_PULLBACK_LONG_V2_M15_SESSION_09_15",
                "decision_time_utc": decision,
                "confirmation_bar_time_utc": decision - pd.Timedelta(minutes=15),
                "direction": "LONG",
                "signal_reason": row.signal_reason,
                "regime": row.regime,
                "stop_points": float(row.stop_points),
                "break_distance_atr": float(row.break_distance_atr),
                "estimated_cost_r": float(row.estimated_cost_r),
                "spread_points": float(row.spread_points),
                "rule_dependency_sha256": dependency_digest,
                "trade_permission": False,
                "broker_action_allowed": False,
                "python_execution_authorized": False,
            }
        )
    return pd.DataFrame(rows, columns=CANDIDATE_COLUMNS)


def canonical_sha(payload: Mapping[str, Any]) -> str:
    encoded = json.dumps(
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode("ascii")
    return hashlib.sha256(encoded).hexdigest()


def now_utc() -> datetime:
    return datetime.now(UTC)


def yearly_ranges(start: datetime, end: datetime) -> list[tuple[datetime, datetime]]:
    if start.tzinfo is None or end.tzinfo is None:
        raise ValueError("history bounds must be timezone-aware")
    ranges: list[tuple[datetime, datetime]] = []
    cursor = start
    while cursor < end:
        following = min(end, datetime(cursor.year + 1, 1, 1, tzinfo=UTC))
        if following <= cursor:
            following = min(end, cursor + timedelta(days=365))
        ranges.append((cursor, following))
        cursor = following
    return ranges
