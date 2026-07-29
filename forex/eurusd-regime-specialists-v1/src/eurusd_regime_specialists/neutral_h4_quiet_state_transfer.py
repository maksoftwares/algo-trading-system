from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Any, Iterable

import numpy as np
import pandas as pd

PIP = 0.0001
PIP_VALUE_USD_001_LOT = 0.10

PRICE_COLUMNS = (
    "bid_open",
    "bid_high",
    "bid_low",
    "bid_close",
    "ask_open",
    "ask_high",
    "ask_low",
    "ask_close",
)


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_m5(source: dict[str, Any]) -> pd.DataFrame:
    path = Path(source["path"])
    if sha256_file(path) != source["sha256"]:
        raise RuntimeError("EURUSD M5 source checksum mismatch")
    frame = pd.read_parquet(path, columns=["timestamp_ms", *PRICE_COLUMNS])
    if len(frame) != int(source["expected_rows"]):
        raise RuntimeError("EURUSD M5 source row count mismatch")
    frame["timestamp"] = pd.to_datetime(frame.pop("timestamp_ms"), unit="ms", utc=True)
    frame = frame.sort_values("timestamp").reset_index(drop=True)
    if frame["timestamp"].duplicated().any() or not frame["timestamp"].is_monotonic_increasing:
        raise RuntimeError("EURUSD M5 timestamps are not unique and chronological")
    if (frame["ask_low"] < frame["bid_low"]).any() or (frame["ask_high"] < frame["bid_high"]).any():
        raise RuntimeError("EURUSD M5 source contains crossed bid/ask bars")
    return frame


def aggregate_h1(m5: pd.DataFrame) -> pd.DataFrame:
    work = m5.copy()
    work["timestamp"] = work["timestamp"].dt.floor("h")
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
    h1 = work.groupby("timestamp", sort=True).agg(aggregation)
    h1["m5_bars"] = work.groupby("timestamp", sort=True).size()
    h1 = h1.reset_index()
    h1["complete_hour"] = h1["m5_bars"].eq(12)
    for field in ("open", "high", "low", "close"):
        h1[f"mid_{field}"] = (h1[f"bid_{field}"] + h1[f"ask_{field}"]) / 2.0
    previous = h1["mid_close"].shift(1)
    true_range = pd.concat(
        [
            h1["mid_high"] - h1["mid_low"],
            (h1["mid_high"] - previous).abs(),
            (h1["mid_low"] - previous).abs(),
        ],
        axis=1,
    ).max(axis=1)
    h1["atr"] = true_range.ewm(alpha=1.0 / 14.0, adjust=False).mean()
    h1["body_fraction"] = (
        (h1["mid_close"] - h1["mid_open"]).abs()
        / (h1["mid_high"] - h1["mid_low"]).replace(0.0, np.nan)
    )
    h1["contiguous_next"] = (
        h1["timestamp"].shift(-1) - h1["timestamp"]
    ).eq(pd.Timedelta(hours=1))
    return h1


def _wilder(series: pd.Series, period: int) -> pd.Series:
    return series.ewm(alpha=1.0 / period, adjust=False, min_periods=period).mean()


def add_h4_regimes(h1: pd.DataFrame, contract: dict[str, Any]) -> tuple[pd.DataFrame, pd.DataFrame]:
    indexed = h1.set_index("timestamp")
    h4 = pd.DataFrame(
        {
            "open": indexed["mid_open"].resample("4h", origin="epoch").first(),
            "high": indexed["mid_high"].resample("4h", origin="epoch").max(),
            "low": indexed["mid_low"].resample("4h", origin="epoch").min(),
            "close": indexed["mid_close"].resample("4h", origin="epoch").last(),
            "h1_bars": indexed["complete_hour"].resample("4h", origin="epoch").sum(),
        }
    )
    h4 = h4[h4["h1_bars"].eq(4)].dropna().copy()
    previous = h4["close"].shift(1)
    true_range = pd.concat(
        [
            h4["high"] - h4["low"],
            (h4["high"] - previous).abs(),
            (h4["low"] - previous).abs(),
        ],
        axis=1,
    ).max(axis=1)
    period = int(contract["atr_period"])
    h4["atr"] = _wilder(true_range, period)
    up = h4["high"].diff()
    down = -h4["low"].diff()
    plus_dm = pd.Series(np.where((up > down) & (up > 0), up, 0.0), index=h4.index)
    minus_dm = pd.Series(np.where((down > up) & (down > 0), down, 0.0), index=h4.index)
    plus_di = 100.0 * _wilder(plus_dm, period) / h4["atr"].replace(0.0, np.nan)
    minus_di = 100.0 * _wilder(minus_dm, period) / h4["atr"].replace(0.0, np.nan)
    dx = 100.0 * (plus_di - minus_di).abs() / (plus_di + minus_di).replace(0.0, np.nan)
    h4["adx"] = _wilder(dx, int(contract["adx_period"]))
    h4["ema"] = h4["close"].ewm(span=int(contract["ema_period"]), adjust=False).mean()
    h4["slope_atr"] = (
        h4["ema"] - h4["ema"].shift(int(contract["slope_bars"]))
    ) / h4["atr"]
    efficiency_bars = int(contract["efficiency_lookback"])
    h4["efficiency"] = (
        (h4["close"] - h4["close"].shift(efficiency_bars)).abs()
        / h4["close"].diff().abs().rolling(efficiency_bars).sum().replace(0.0, np.nan)
    )
    range_bars = int(contract["range_lookback"])
    h4["width_atr"] = (
        h4["high"].rolling(range_bars).max() - h4["low"].rolling(range_bars).min()
    ) / h4["atr"]
    h4["displacement_atr"] = (h4["close"] - h4["ema"]).abs() / h4["atr"]
    baseline = int(contract["volatility_baseline_bars"])
    h4["atr_ratio"] = h4["atr"] / h4["atr"].shift(1).rolling(baseline).median()
    h4["atr_p95"] = h4["atr"].shift(1).rolling(baseline).quantile(
        float(contract["unsafe_atr_percentile"])
    )
    h4["gap_atr"] = (h4["open"] - previous).abs() / h4["atr"]

    valid = h4[
        ["atr", "adx", "slope_atr", "efficiency", "width_atr", "atr_ratio", "atr_p95"]
    ].notna().all(axis=1)
    unsafe = valid & (
        (h4["atr"] >= h4["atr_p95"])
        | (h4["gap_atr"] >= float(contract["unsafe_gap_atr"]))
    )
    trend_common = (
        valid
        & ~unsafe
        & (h4["adx"] >= float(contract["trend_adx_min"]))
        & (h4["efficiency"] >= float(contract["trend_efficiency_min"]))
    )
    trend_up = trend_common & (
        h4["slope_atr"] >= float(contract["trend_slope_atr_min"])
    )
    trend_down = trend_common & (
        h4["slope_atr"] <= -float(contract["trend_slope_atr_min"])
    )
    compression = (
        valid
        & ~unsafe
        & ~trend_up
        & ~trend_down
        & (h4["adx"] <= float(contract["compression_adx_max"]))
        & (h4["atr_ratio"] <= float(contract["compression_atr_ratio_max"]))
        & (h4["width_atr"] <= float(contract["compression_width_atr_max"]))
    )
    chop = (
        valid
        & ~unsafe
        & ~trend_up
        & ~trend_down
        & ~compression
        & (h4["adx"] <= float(contract["chop_adx_max"]))
        & (h4["efficiency"] <= float(contract["chop_efficiency_max"]))
        & (h4["displacement_atr"] <= float(contract["chop_displacement_atr_max"]))
        & (h4["width_atr"] >= float(contract["chop_width_atr_min"]))
        & (h4["width_atr"] <= float(contract["chop_width_atr_max"]))
    )
    h4["regime"] = np.select(
        [unsafe, trend_up, trend_down, compression, chop],
        ["unsafe", "trend_up", "trend_down", "compression", "chop"],
        default="transition",
    )
    states = h4.reset_index()[["timestamp", "regime"]]
    states["available_time"] = states["timestamp"] + pd.Timedelta(hours=4)
    left_times = h1[["timestamp"]].sort_values("timestamp").copy()
    right_states = states[["available_time", "regime"]].sort_values("available_time").copy()
    left_times["timestamp"] = left_times["timestamp"].astype("datetime64[ns, UTC]")
    right_states["available_time"] = right_states["available_time"].astype(
        "datetime64[ns, UTC]"
    )
    mapped = pd.merge_asof(
        left_times,
        right_states,
        left_on="timestamp",
        right_on="available_time",
        direction="backward",
    )
    result = h1.copy()
    result["regime"] = mapped["regime"].fillna("transition").to_numpy()
    return result, h4.reset_index()


def build_signal_mask(h1: pd.DataFrame, candidate: dict[str, Any]) -> pd.Series:
    date = h1["timestamp"].dt.strftime("%Y-%m-%d")
    hour = h1["timestamp"].dt.hour
    reference = hour.isin(candidate["reference_hours_utc"]) & h1["complete_hour"]
    ref_high = h1["mid_high"].where(reference).groupby(date).transform("max")
    ref_low = h1["mid_low"].where(reference).groupby(date).transform("min")
    ref_count = reference.groupby(date).transform("sum")
    decision = hour.isin(candidate["decision_hours_utc"])
    raw = (
        (h1["mid_close"] < ref_low)
        & decision
        & ref_count.eq(len(candidate["reference_hours_utc"]))
        & h1["complete_hour"]
        & h1["contiguous_next"]
        & (h1["body_fraction"] >= float(candidate["body_fraction_minimum"]))
        & h1["regime"].eq(candidate["owned_regime"])
        & h1["atr"].notna()
    ).fillna(False)
    return raw & raw.groupby(date).cumsum().eq(1)


def _overlaps_quarantine(entry: pd.Timestamp, exit_time: pd.Timestamp, source: dict[str, Any]) -> bool:
    for interval in source["quarantine"]:
        start = pd.Timestamp(interval["start_utc"])
        end = pd.Timestamp(interval["end_utc"])
        if entry < end and exit_time > start:
            return True
    return False


def simulate_short(
    h1: pd.DataFrame,
    m5: pd.DataFrame,
    mask: pd.Series,
    candidate: dict[str, Any],
    config: dict[str, Any],
) -> tuple[pd.DataFrame, dict[str, int]]:
    execution = config["execution"]
    spread_floor = float(execution["minimum_retail_spread_pips"]) * PIP
    maximum_spread = float(execution["maximum_entry_spread_pips"])
    slip = float(execution["adverse_slippage_pips_per_side"]) * PIP
    stress_extra = float(execution["extra_round_trip_stress_pips"])
    maximum_bars = int(candidate["maximum_hold_hours"]) * 12

    times = m5["timestamp"].to_numpy()
    time_to_index = {pd.Timestamp(value): index for index, value in enumerate(times)}
    arrays = {name: m5[name].to_numpy(dtype=float) for name in PRICE_COLUMNS}
    eligible = np.flatnonzero(mask.to_numpy())
    blocked_until = -1
    records: list[dict[str, Any]] = []
    diagnostics = {
        "signals": int(len(eligible)),
        "missing_entry": 0,
        "incomplete_path": 0,
        "spread_rejection": 0,
        "overlap_rejection": 0,
        "quarantine_rejection": 0,
    }

    for signal_index in eligible:
        signal_time = pd.Timestamp(h1["timestamp"].iloc[signal_index])
        entry_time = signal_time + pd.Timedelta(hours=1)
        entry_index = time_to_index.get(entry_time)
        if entry_index is None:
            diagnostics["missing_entry"] += 1
            continue
        if entry_index <= blocked_until:
            diagnostics["overlap_rejection"] += 1
            continue
        final_index = entry_index + maximum_bars - 1
        if final_index >= len(m5) or (
            pd.Timestamp(times[final_index]) - entry_time
            != pd.Timedelta(minutes=5 * (maximum_bars - 1))
        ):
            diagnostics["incomplete_path"] += 1
            continue
        effective_ask_open = max(
            arrays["ask_open"][entry_index],
            arrays["bid_open"][entry_index] + spread_floor,
        )
        entry_spread_pips = (
            effective_ask_open - arrays["bid_open"][entry_index]
        ) / PIP
        if entry_spread_pips > maximum_spread:
            diagnostics["spread_rejection"] += 1
            continue

        stop_distance = (
            float(candidate["stop_atr_multiple"])
            * float(h1["atr"].iloc[signal_index])
        )
        if not math.isfinite(stop_distance) or stop_distance <= 0.0:
            diagnostics["incomplete_path"] += 1
            continue
        entry = arrays["bid_open"][entry_index] - slip
        stop = entry + stop_distance
        target = entry - float(candidate["target_r_multiple"]) * stop_distance
        exit_index = final_index
        final_ask_close = max(
            arrays["ask_close"][final_index],
            arrays["bid_close"][final_index] + spread_floor,
        )
        exit_price = final_ask_close + slip
        exit_reason = "TIME"

        for position in range(entry_index, final_index + 1):
            ask_open = max(
                arrays["ask_open"][position],
                arrays["bid_open"][position] + spread_floor,
            )
            ask_high = max(
                arrays["ask_high"][position],
                arrays["bid_high"][position] + spread_floor,
            )
            ask_low = max(
                arrays["ask_low"][position],
                arrays["bid_low"][position] + spread_floor,
            )
            if ask_open >= stop:
                exit_index = position
                exit_price = max(ask_open, stop) + slip
                exit_reason = "STOP_GAP"
                break
            if ask_high >= stop:
                exit_index = position
                exit_price = stop + slip
                exit_reason = "STOP"
                break
            if ask_low <= target:
                exit_index = position
                exit_price = min(ask_open, target) + slip
                exit_reason = "TARGET"
                break

        exit_time = pd.Timestamp(times[exit_index])
        if _overlaps_quarantine(entry_time, exit_time + pd.Timedelta(minutes=5), config["source"]):
            diagnostics["quarantine_rejection"] += 1
            continue
        net_pips = (entry - exit_price) / PIP
        stop_pips = stop_distance / PIP
        r = net_pips / stop_pips
        records.append(
            {
                "specialist_id": candidate["specialist_id"],
                "owned_regime": candidate["owned_regime"],
                "side": "SHORT",
                "signal_time_utc": signal_time,
                "entry_time_utc": entry_time,
                "exit_time_utc": exit_time,
                "entry": entry,
                "stop": stop,
                "target": target,
                "exit": exit_price,
                "entry_spread_pips": entry_spread_pips,
                "stop_pips": stop_pips,
                "net_pips": net_pips,
                "r": r,
                "stress_r": r - stress_extra / stop_pips,
                "pnl_usd_001_lot": net_pips * PIP_VALUE_USD_001_LOT,
                "exit_reason": exit_reason,
            }
        )
        blocked_until = exit_index
    return pd.DataFrame(records), diagnostics


def profit_factor(values: Iterable[float]) -> float:
    vector = np.asarray(list(values), dtype=float)
    gains = float(vector[vector > 0.0].sum())
    losses = float(-vector[vector < 0.0].sum())
    if losses == 0.0:
        return math.inf if gains > 0.0 else 0.0
    return gains / losses


def summarize(trades: pd.DataFrame) -> dict[str, Any]:
    if trades.empty:
        return {
            "trades": 0,
            "wins": 0,
            "win_rate": 0.0,
            "realized_payoff_ratio": 0.0,
            "profit_factor": 0.0,
            "stress_profit_factor": 0.0,
            "net_r": 0.0,
            "stress_net_r": 0.0,
            "pnl_usd_001_lot": 0.0,
            "maximum_drawdown_r": 0.0,
            "positive_active_month_share": 0.0,
            "top_5pct_winners_removed_profit_factor": 0.0,
        }
    ordered = trades.sort_values("exit_time_utc")
    values = ordered["r"].to_numpy(dtype=float)
    stress = ordered["stress_r"].to_numpy(dtype=float)
    wins = values[values > 0.0]
    losses = values[values < 0.0]
    equity = np.cumsum(values)
    peak = np.maximum.accumulate(np.insert(equity, 0, 0.0))[1:]
    month_values = ordered.assign(
        month=ordered["exit_time_utc"].dt.strftime("%Y-%m")
    ).groupby("month")["r"].sum()
    remove_count = max(1, int(math.ceil(len(values) * 0.05)))
    removed = np.delete(values, np.argsort(values)[-remove_count:])
    average_loss = float(-losses.mean()) if len(losses) else 0.0
    payoff = float(wins.mean() / average_loss) if len(wins) and average_loss else 0.0
    return {
        "trades": int(len(values)),
        "wins": int(len(wins)),
        "win_rate": float(len(wins) / len(values)),
        "realized_payoff_ratio": payoff,
        "profit_factor": profit_factor(values),
        "stress_profit_factor": profit_factor(stress),
        "net_r": float(values.sum()),
        "stress_net_r": float(stress.sum()),
        "pnl_usd_001_lot": float(ordered["pnl_usd_001_lot"].sum()),
        "maximum_drawdown_r": float(np.max(peak - equity)),
        "positive_active_month_share": float((month_values > 0.0).mean()),
        "top_5pct_winners_removed_profit_factor": profit_factor(removed),
    }


def evaluate_gates(
    windows: dict[str, dict[str, Any]], gates: dict[str, Any]
) -> dict[str, bool]:
    full = windows["FULL_AUDIT"]
    latest = windows["LATEST_12_MONTHS"]
    chronology = (
        "EARLY_2017_2019",
        "MIDDLE_2020_2022H1",
        "LATE_2022H2_2024H1",
        "RECENT_2024H2_2026H1",
    )
    return {
        "minimum_full_audit_trades": full["trades"]
        >= int(gates["minimum_full_audit_trades"]),
        "win_rate": float(gates["minimum_win_rate_inclusive"])
        <= full["win_rate"]
        <= float(gates["maximum_win_rate_inclusive"]),
        "realized_payoff_ratio": float(gates["minimum_realized_payoff_ratio_inclusive"])
        <= full["realized_payoff_ratio"]
        <= float(gates["maximum_realized_payoff_ratio_inclusive"]),
        "full_audit_profit_factor": full["profit_factor"]
        >= float(gates["minimum_full_audit_profit_factor"]),
        "stressed_profit_factor": full["stress_profit_factor"]
        >= float(gates["minimum_stressed_profit_factor"]),
        "each_chronological_block_profit_factor": all(
            windows[name]["profit_factor"]
            > float(gates["minimum_each_chronological_block_profit_factor_exclusive"])
            for name in chronology
        ),
        "latest_12_month_profit_factor": latest["profit_factor"]
        >= float(gates["minimum_latest_12_month_profit_factor"]),
        "latest_12_month_net_r": latest["net_r"]
        > float(gates["minimum_latest_12_month_net_r_exclusive"]),
        "positive_active_month_share": full["positive_active_month_share"]
        >= float(gates["minimum_positive_active_month_share"]),
        "top_5pct_winners_removed_profit_factor": full[
            "top_5pct_winners_removed_profit_factor"
        ]
        >= float(gates["minimum_top_5pct_winners_removed_profit_factor"]),
        "maximum_closed_trade_drawdown": full["maximum_drawdown_r"]
        <= float(gates["maximum_closed_trade_drawdown_r"]),
    }


def run(config_path: Path, output_dir: Path) -> dict[str, Any]:
    config_bytes = config_path.read_bytes()
    config = json.loads(config_bytes)
    package_root = config_path.parent.parent
    repository_root = package_root.parents[1]
    for item in config["provenance"].values():
        path = (package_root / item["path"]).resolve()
        if not path.is_file():
            path = (repository_root / item["path"].removeprefix("../../")).resolve()
        if sha256_file(path) != item["sha256"]:
            raise RuntimeError(f"Frozen provenance checksum mismatch: {path}")

    m5 = load_m5(config["source"])
    h1 = aggregate_h1(m5)
    h1, h4 = add_h4_regimes(h1, config["classifier"])
    all_trades = []
    candidates: dict[str, Any] = {}
    for candidate in config["candidates"]:
        mask = build_signal_mask(h1, candidate)
        trades, diagnostics = simulate_short(h1, m5, mask, candidate, config)
        all_trades.append(trades)
        window_metrics = {}
        for name, (start, end) in config["reporting_windows"].items():
            subset = trades[
                (trades["entry_time_utc"] >= pd.Timestamp(start))
                & (trades["entry_time_utc"] < pd.Timestamp(end))
            ]
            window_metrics[name] = summarize(subset)
        gate_results = evaluate_gates(
            window_metrics, config["historical_quality_gates"]
        )
        candidates[candidate["specialist_id"]] = {
            "parameters": candidate,
            "diagnostics": diagnostics,
            "windows": window_metrics,
            "gate_results": gate_results,
            "all_historical_quality_gates_passed": all(gate_results.values()),
        }

    output_dir.mkdir(parents=True, exist_ok=True)
    ledger = pd.concat(all_trades, ignore_index=True) if all_trades else pd.DataFrame()
    ledger.to_csv(output_dir / "TRADES.csv", index=False, lineterminator="\n")
    h4[["timestamp", "regime"]].to_csv(
        output_dir / "H4_REGIME_STATES.csv", index=False, lineterminator="\n"
    )
    passed = [
        name
        for name, result in candidates.items()
        if result["all_historical_quality_gates_passed"]
    ]
    result = {
        "schema_version": "eurusd_neutral_h4_quiet_state_transfer_result_v1",
        "frozen_config_sha256": hashlib.sha256(config_bytes).hexdigest(),
        "source_sha256": config["source"]["sha256"],
        "source_rows": len(m5),
        "h1_rows": len(h1),
        "h4_complete_rows": len(h4),
        "retrospective_causal_not_pristine_oos": True,
        "broker_action_allowed": False,
        "candidates": candidates,
        "qualified_specialists": passed,
        "status": (
            "HISTORICAL_QUALITY_SPECIALIST_QUALIFIED_REQUIRES_PROSPECTIVE_CONFIRMATION"
            if passed
            else "REJECTED_EXACT_H4_CONTROLS_NO_HISTORICAL_QUALIFIER"
        ),
    }
    (output_dir / "RESULT.json").write_text(
        json.dumps(result, indent=2, allow_nan=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return result
