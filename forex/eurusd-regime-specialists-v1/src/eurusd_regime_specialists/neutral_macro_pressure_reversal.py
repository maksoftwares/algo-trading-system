from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from .neutral_h4_quiet_state_transfer import (
    PIP,
    PIP_VALUE_USD_001_LOT,
    PRICE_COLUMNS,
    add_h4_regimes,
    aggregate_h1,
    evaluate_gates,
    load_m5,
    sha256_file,
    summarize,
)


def load_macro(config: dict[str, Any]) -> pd.DataFrame:
    frames: list[pd.DataFrame] = []
    for output_column, source in config["macro_sources"].items():
        path = Path(source["path"])
        if sha256_file(path) != source["sha256"]:
            raise RuntimeError(f"Macro source checksum mismatch: {path}")
        raw = pd.read_csv(path)
        required = {"observation_date", source["column"]}
        missing = required.difference(raw.columns)
        if missing:
            raise RuntimeError(f"{path} missing columns: {sorted(missing)}")
        frame = pd.DataFrame(
            {
                "observation_utc": pd.to_datetime(
                    raw["observation_date"], utc=True, errors="coerce"
                ),
                output_column: pd.to_numeric(
                    raw[source["column"]].replace(".", pd.NA), errors="coerce"
                ),
            }
        ).dropna()
        frames.append(frame)

    merged = frames[0]
    for frame in frames[1:]:
        merged = merged.merge(frame, on="observation_utc", how="outer")
    merged = merged.sort_values("observation_utc").ffill().dropna().reset_index(drop=True)
    merged["macro_available_utc"] = merged["observation_utc"] + pd.Timedelta(days=1)
    merged["real_yield_delta_20d"] = merged["real_yield_10y"].diff(20)
    merged["dollar_pct_20d"] = (
        merged["dollar_index_broad"].pct_change(20, fill_method=None) * 100.0
    )
    merged["macro_pressure_score"] = (
        merged["real_yield_delta_20d"]
        / float(config["candidate"]["real_yield_score_scale"])
        + merged["dollar_pct_20d"]
        / float(config["candidate"]["dollar_score_scale_pct"])
    )
    return merged.dropna(
        subset=[
            "real_yield_delta_20d",
            "dollar_pct_20d",
            "macro_pressure_score",
        ]
    ).reset_index(drop=True)


def aggregate_h4(m5: pd.DataFrame) -> pd.DataFrame:
    work = m5.copy()
    work["timestamp"] = work["timestamp"].dt.floor("4h")
    aggregation = {
        "bid_open": "first",
        "bid_high": "max",
        "bid_low": "min",
        "bid_close": "last",
        "ask_open": "first",
        "ask_high": "max",
        "ask_low": "min",
        "ask_close": "last",
    }
    h4 = work.groupby("timestamp", sort=True).agg(aggregation)
    h4["m5_bars"] = work.groupby("timestamp", sort=True).size()
    h4 = h4[h4["m5_bars"].eq(48)].reset_index()
    for field in ("open", "high", "low", "close"):
        h4[field] = (h4[f"bid_{field}"] + h4[f"ask_{field}"]) / 2.0
    previous = h4["close"].shift(1)
    true_range = pd.concat(
        [
            h4["high"] - h4["low"],
            (h4["high"] - previous).abs(),
            (h4["low"] - previous).abs(),
        ],
        axis=1,
    ).max(axis=1)
    h4["atr"] = true_range.rolling(14, min_periods=14).mean()
    return h4


def attach_macro_and_regime(
    h4: pd.DataFrame,
    macro: pd.DataFrame,
    regime_states: pd.DataFrame,
) -> pd.DataFrame:
    left = h4.sort_values("timestamp").copy()
    right = macro.sort_values("macro_available_utc").copy()
    left["timestamp"] = left["timestamp"].astype("datetime64[ns, UTC]")
    right["macro_available_utc"] = right["macro_available_utc"].astype(
        "datetime64[ns, UTC]"
    )
    merged = pd.merge_asof(
        left,
        right,
        left_on="timestamp",
        right_on="macro_available_utc",
        direction="backward",
    )
    states = regime_states[["timestamp", "regime"]].copy()
    states["timestamp"] = states["timestamp"].astype("datetime64[ns, UTC]")
    return merged.merge(states, on="timestamp", how="left").assign(
        regime=lambda frame: frame["regime"].fillna("transition")
    )


def generate_signals(h4: pd.DataFrame, candidate: dict[str, Any]) -> pd.DataFrame:
    records: list[dict[str, Any]] = []
    lookback = int(candidate["prior_extreme_h4_bars"])
    start = max(int(candidate["minimum_warmup_h4_bars"]), lookback)
    for index in range(start, len(h4) - 1):
        row = h4.iloc[index]
        required = (
            row["atr"],
            row["macro_pressure_score"],
            row["real_yield_delta_20d"],
            row["dollar_pct_20d"],
        )
        if not all(math.isfinite(float(value)) for value in required):
            continue
        atr = float(row["atr"])
        if atr <= 0.0:
            continue
        prior = h4.iloc[index - lookback : index]
        prior_high = float(prior["high"].max())
        prior_low = float(prior["low"].min())
        buffer = float(candidate["extreme_break_buffer_atr"]) * atr
        pressure = float(row["macro_pressure_score"])
        real_delta = float(row["real_yield_delta_20d"])
        dollar_delta = float(row["dollar_pct_20d"])
        direction = ""
        stop = math.nan
        prior_extreme = math.nan
        if (
            pressure >= float(candidate["positive_pressure_threshold"])
            and real_delta > float(candidate["positive_real_yield_delta_min"])
            and dollar_delta > float(candidate["positive_dollar_delta_min_pct"])
            and float(row["low"]) < prior_low - buffer
            and float(row["close"]) > prior_low
            and float(row["close"]) > float(row["open"])
        ):
            direction = "LONG"
            stop = float(row["low"]) - float(candidate["stop_buffer_atr"]) * atr
            prior_extreme = prior_low
        elif (
            pressure <= -float(candidate["positive_pressure_threshold"])
            and real_delta < -float(candidate["positive_real_yield_delta_min"])
            and dollar_delta < -float(candidate["positive_dollar_delta_min_pct"])
            and float(row["high"]) > prior_high + buffer
            and float(row["close"]) < prior_high
            and float(row["close"]) < float(row["open"])
        ):
            direction = "SHORT"
            stop = float(row["high"]) + float(candidate["stop_buffer_atr"]) * atr
            prior_extreme = prior_high
        if direction:
            records.append(
                {
                    "signal_index": index,
                    "signal_time_utc": row["timestamp"],
                    "direction": direction,
                    "stop": stop,
                    "prior_extreme": prior_extreme,
                    "signal_regime": row["regime"],
                    "atr": atr,
                    "macro_observation_utc": row["observation_utc"],
                    "macro_available_utc": row["macro_available_utc"],
                    "macro_pressure_score": pressure,
                    "real_yield_delta_20d": real_delta,
                    "dollar_pct_20d": dollar_delta,
                }
            )
    return pd.DataFrame(records)


def _effective_ask(bid: float, ask: float, spread_floor: float) -> float:
    return max(ask, bid + spread_floor)


def _overlaps_quarantine(
    entry: pd.Timestamp, exit_time: pd.Timestamp, source: dict[str, Any]
) -> bool:
    return any(
        entry < pd.Timestamp(interval["end_utc"])
        and exit_time > pd.Timestamp(interval["start_utc"])
        for interval in source["quarantine"]
    )


def simulate(
    h4: pd.DataFrame,
    m5: pd.DataFrame,
    signals: pd.DataFrame,
    config: dict[str, Any],
) -> tuple[pd.DataFrame, dict[str, int]]:
    candidate = config["candidate"]
    execution = config["execution"]
    spread_floor = float(execution["minimum_retail_spread_pips"]) * PIP
    slip = float(execution["adverse_slippage_pips_per_side"]) * PIP
    max_spread = float(execution["maximum_entry_spread_pips"])
    stress_extra = float(execution["extra_round_trip_stress_pips"])
    target_r = float(candidate["target_r_multiple"])
    hold_h4 = int(candidate["maximum_hold_h4_bars"])

    arrays = {name: m5[name].to_numpy(dtype=float) for name in PRICE_COLUMNS}
    times = m5["timestamp"].to_numpy()
    time_to_index = {pd.Timestamp(value): index for index, value in enumerate(times)}
    diagnostics = {
        "signals": int(len(signals)),
        "missing_entry_or_exit": 0,
        "spread_rejection": 0,
        "invalid_stop": 0,
        "overlap_rejection": 0,
        "quarantine_rejection": 0,
    }
    records: list[dict[str, Any]] = []
    blocked_until = -1

    for signal in signals.to_dict("records"):
        entry_h4_index = int(signal["signal_index"]) + 1
        final_h4_index = entry_h4_index + hold_h4 - 1
        if final_h4_index >= len(h4):
            diagnostics["missing_entry_or_exit"] += 1
            continue
        entry_time = pd.Timestamp(h4["timestamp"].iloc[entry_h4_index])
        final_time = pd.Timestamp(h4["timestamp"].iloc[final_h4_index]) + pd.Timedelta(
            hours=3, minutes=55
        )
        entry_index = time_to_index.get(entry_time)
        final_index = time_to_index.get(final_time)
        if entry_index is None or final_index is None:
            diagnostics["missing_entry_or_exit"] += 1
            continue
        if entry_index <= blocked_until:
            diagnostics["overlap_rejection"] += 1
            continue

        ask_open = _effective_ask(
            arrays["bid_open"][entry_index],
            arrays["ask_open"][entry_index],
            spread_floor,
        )
        entry_spread_pips = (
            ask_open - arrays["bid_open"][entry_index]
        ) / PIP
        if entry_spread_pips > max_spread:
            diagnostics["spread_rejection"] += 1
            continue

        direction = str(signal["direction"])
        stop = float(signal["stop"])
        if direction == "LONG":
            entry = ask_open + slip
            risk = entry - stop
            target = entry + target_r * risk
            valid_stop = stop < entry
        else:
            entry = arrays["bid_open"][entry_index] - slip
            risk = stop - entry
            target = entry - target_r * risk
            valid_stop = stop > entry
        if not valid_stop or not math.isfinite(risk) or risk <= 0.0:
            diagnostics["invalid_stop"] += 1
            continue

        exit_index = final_index
        exit_reason = "TIME"
        if direction == "LONG":
            exit_price = arrays["bid_close"][final_index] - slip
        else:
            final_ask = _effective_ask(
                arrays["bid_close"][final_index],
                arrays["ask_close"][final_index],
                spread_floor,
            )
            exit_price = final_ask + slip

        for position in range(entry_index, final_index + 1):
            if direction == "LONG":
                bid_open = arrays["bid_open"][position]
                if bid_open <= stop:
                    exit_index = position
                    exit_price = min(bid_open, stop) - slip
                    exit_reason = "STOP_GAP"
                    break
                if bid_open >= target:
                    exit_index = position
                    exit_price = max(bid_open, target) - slip
                    exit_reason = "TARGET_GAP"
                    break
                if arrays["bid_low"][position] <= stop:
                    exit_index = position
                    exit_price = stop - slip
                    exit_reason = "STOP"
                    break
                if arrays["bid_high"][position] >= target:
                    exit_index = position
                    exit_price = target - slip
                    exit_reason = "TARGET"
                    break
            else:
                ask_open_position = _effective_ask(
                    arrays["bid_open"][position],
                    arrays["ask_open"][position],
                    spread_floor,
                )
                ask_high = _effective_ask(
                    arrays["bid_high"][position],
                    arrays["ask_high"][position],
                    spread_floor,
                )
                ask_low = _effective_ask(
                    arrays["bid_low"][position],
                    arrays["ask_low"][position],
                    spread_floor,
                )
                if ask_open_position >= stop:
                    exit_index = position
                    exit_price = max(ask_open_position, stop) + slip
                    exit_reason = "STOP_GAP"
                    break
                if ask_open_position <= target:
                    exit_index = position
                    exit_price = min(ask_open_position, target) + slip
                    exit_reason = "TARGET_GAP"
                    break
                if ask_high >= stop:
                    exit_index = position
                    exit_price = stop + slip
                    exit_reason = "STOP"
                    break
                if ask_low <= target:
                    exit_index = position
                    exit_price = target + slip
                    exit_reason = "TARGET"
                    break

        exit_time = pd.Timestamp(times[exit_index])
        if _overlaps_quarantine(
            entry_time, exit_time + pd.Timedelta(minutes=5), config["source"]
        ):
            diagnostics["quarantine_rejection"] += 1
            continue
        net_pips = (
            (exit_price - entry) / PIP
            if direction == "LONG"
            else (entry - exit_price) / PIP
        )
        stop_pips = risk / PIP
        net_r = net_pips / stop_pips
        records.append(
            {
                "specialist_id": candidate["specialist_id"],
                "signal_time_utc": signal["signal_time_utc"],
                "entry_time_utc": entry_time,
                "exit_time_utc": exit_time,
                "direction": direction,
                "signal_regime": signal["signal_regime"],
                "entry": entry,
                "stop": stop,
                "target": target,
                "exit": exit_price,
                "entry_spread_pips": entry_spread_pips,
                "stop_pips": stop_pips,
                "net_pips": net_pips,
                "r": net_r,
                "stress_r": net_r - stress_extra / stop_pips,
                "pnl_usd_001_lot": net_pips * PIP_VALUE_USD_001_LOT,
                "exit_reason": exit_reason,
                "macro_observation_utc": signal["macro_observation_utc"],
                "macro_available_utc": signal["macro_available_utc"],
                "macro_pressure_score": signal["macro_pressure_score"],
                "real_yield_delta_20d": signal["real_yield_delta_20d"],
                "dollar_pct_20d": signal["dollar_pct_20d"],
            }
        )
        blocked_until = exit_index
    return pd.DataFrame(records), diagnostics


def _window_metrics(
    trades: pd.DataFrame, reporting_windows: dict[str, list[str]]
) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for name, (start, end) in reporting_windows.items():
        if trades.empty:
            subset = trades
        else:
            subset = trades[
                (trades["entry_time_utc"] >= pd.Timestamp(start))
                & (trades["entry_time_utc"] < pd.Timestamp(end))
            ]
        result[name] = summarize(subset)
    return result


def _json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if isinstance(value, float) and not math.isfinite(value):
        if math.isnan(value):
            return None
        return "Infinity" if value > 0.0 else "-Infinity"
    return value


def run(config_path: Path, output_dir: Path) -> dict[str, Any]:
    config_bytes = config_path.read_bytes()
    config = json.loads(config_bytes)
    frozen_hash = hashlib.sha256(config_bytes).hexdigest()
    m5 = load_m5(config["source"])
    macro = load_macro(config)
    h4 = aggregate_h4(m5)
    h1 = aggregate_h1(m5)
    _, regime_states = add_h4_regimes(h1, config["classifier"])
    h4 = attach_macro_and_regime(h4, macro, regime_states)
    signals = generate_signals(h4, config["candidate"])
    trades, diagnostics = simulate(h4, m5, signals, config)

    scopes: dict[str, pd.DataFrame] = {"ALL_REGIMES_REPLICATION": trades}
    neutral_regimes = set(config["ownership"]["neutral_regimes"])
    scopes["REGIME_1_NEUTRAL_OWNED"] = (
        trades[trades["signal_regime"].isin(neutral_regimes)].copy()
        if not trades.empty
        else trades.copy()
    )
    scope_results: dict[str, Any] = {}
    for name, scoped in scopes.items():
        windows = _window_metrics(scoped, config["reporting_windows"])
        gates = evaluate_gates(windows, config["historical_quality_gates"])
        scope_results[name] = {
            "windows": windows,
            "gate_results": gates,
            "all_historical_quality_gates_passed": all(gates.values()),
        }

    regime_attribution = {
        regime: summarize(trades[trades["signal_regime"].eq(regime)])
        for regime in config["ownership"]["all_regimes"]
    } if not trades.empty else {
        regime: summarize(trades) for regime in config["ownership"]["all_regimes"]
    }
    neutral_pass = scope_results["REGIME_1_NEUTRAL_OWNED"][
        "all_historical_quality_gates_passed"
    ]
    output_dir.mkdir(parents=True, exist_ok=True)
    trades.to_csv(output_dir / "TRADES.csv", index=False, lineterminator="\n")
    signals.to_csv(output_dir / "SIGNALS.csv", index=False, lineterminator="\n")
    result = {
        "schema_version": "eurusd_neutral_macro_pressure_reversal_result_v1",
        "frozen_config_sha256": frozen_hash,
        "source_sha256": config["source"]["sha256"],
        "source_rows": len(m5),
        "macro_rows": len(macro),
        "h4_complete_rows": len(h4),
        "diagnostics": diagnostics,
        "scopes": scope_results,
        "regime_attribution": regime_attribution,
        "retrospective_causal_not_pristine_oos": True,
        "broker_action_allowed": False,
        "status": (
            "REGIME_1_HISTORICAL_QUALITY_PASS_REQUIRES_PROSPECTIVE_CONFIRMATION"
            if neutral_pass
            else "REJECTED_NO_REGIME_1_HISTORICAL_QUALIFIER"
        ),
    }
    (output_dir / "RESULT.json").write_text(
        json.dumps(_json_safe(result), indent=2, allow_nan=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return result
