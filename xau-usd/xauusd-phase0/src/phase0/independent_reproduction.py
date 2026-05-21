from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from phase0.backtester import matrix_output_stem
from phase0.config import ConfigError, ProjectConfig, build_cell_configs


@dataclass(frozen=True)
class IndependentReproductionOutput:
    status: str
    report_path: Path
    manifest_path: Path
    expert: str
    cell_id: int
    comparisons: tuple[dict[str, object], ...]


def generate_independent_reproduction(
    config: ProjectConfig,
    expert: str = "breakout_retest",
    cell_id: int = 2,
    tolerance_pct: float = 5.0,
) -> IndependentReproductionOutput:
    if expert != "breakout_retest":
        raise ConfigError("Independent reproduction currently supports breakout_retest only.")
    if tolerance_pct < 0:
        raise ConfigError("Tolerance must be non-negative.")

    cell = _cell_by_id(config, cell_id)
    stem = matrix_output_stem(cell.cell_id, expert, cell.broker, cell.cost_model)
    source_summary_path = config.root / "outputs" / "matrix_results" / expert / f"{stem}.csv"
    source_trades_path = config.root / "outputs" / "matrix_results" / expert / f"{stem}_trades.csv"
    if not source_summary_path.exists():
        raise ConfigError(f"Reference matrix summary is missing: {source_summary_path}")

    reference = pd.read_csv(source_summary_path).iloc[0].to_dict()
    bars_path = _m5_bars_path(config, cell.broker, cell.symbol)
    bars = _load_reproduction_bars(bars_path, cell.end_utc)
    trades = _simulate_breakout_retest(config, bars, cell, expert)
    metrics = _metrics_from_rows(trades, float(config.phase0["project"]["starting_equity_usd"]))
    comparisons = _compare_metrics(reference, metrics, tolerance_pct)
    status = "PASS" if all(row["status"] == "PASS" for row in comparisons) else "FAIL"

    report_path = config.root / "outputs" / "reports" / "PHASE0_INDEPENDENT_REPRODUCTION.md"
    manifest_path = (
        config.root / "outputs" / "manifests" / "PHASE0_INDEPENDENT_REPRODUCTION_MANIFEST.json"
    )
    report_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        _render_report(
            status=status,
            expert=expert,
            cell_id=cell_id,
            broker=cell.broker,
            cost_model=cell.cost_model,
            symbol=cell.symbol,
            bars_path=bars_path,
            source_summary_path=source_summary_path,
            source_trades_path=source_trades_path,
            metrics=metrics,
            comparisons=comparisons,
            trade_count=len(trades),
            tolerance_pct=tolerance_pct,
        ),
        encoding="utf-8",
    )
    manifest = {
        "generated_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "status": status,
        "expert": expert,
        "cell_id": cell_id,
        "broker": cell.broker,
        "cost_model": cell.cost_model,
        "symbol": cell.symbol,
        "method": "standalone_pandas_event_replay",
        "tolerance_pct": tolerance_pct,
        "report_path": str(report_path.relative_to(config.root)),
        "bars_path": str(bars_path.relative_to(config.root)),
        "source_summary_path": str(source_summary_path.relative_to(config.root)),
        "source_trades_path": (
            str(source_trades_path.relative_to(config.root)) if source_trades_path.exists() else ""
        ),
        "bars_sha256": _sha256(bars_path),
        "source_summary_sha256": _sha256(source_summary_path),
        "source_trades_sha256": _sha256(source_trades_path) if source_trades_path.exists() else "",
        "report_sha256": _sha256(report_path),
        "metrics": metrics,
        "comparisons": list(comparisons),
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    return IndependentReproductionOutput(
        status=status,
        report_path=report_path,
        manifest_path=manifest_path,
        expert=expert,
        cell_id=cell_id,
        comparisons=tuple(comparisons),
    )


def _cell_by_id(config: ProjectConfig, cell_id: int):
    matches = [cell for cell in build_cell_configs(config, symbol="XAUUSD") if cell.cell_id == cell_id]
    if not matches:
        raise ConfigError(f"Unknown matrix cell id: {cell_id}")
    return matches[0]


def _m5_bars_path(config: ProjectConfig, broker: str, symbol: str) -> Path:
    directory = config.root / "data" / "processed" / "bars" / broker / symbol / "M5"
    files = sorted(directory.glob("*.csv")) if directory.exists() else []
    if not files:
        raise ConfigError(f"No processed M5 bars found in {directory}.")
    if len(files) > 1:
        raise ConfigError(f"Independent reproduction expected one M5 file in {directory}, found {len(files)}.")
    return files[0]


def _load_reproduction_bars(path: Path, period_end: datetime) -> pd.DataFrame:
    bars = pd.read_csv(path)
    for column in ("timestamp_utc", "bar_start_utc", "bar_end_utc"):
        bars[column] = pd.to_datetime(bars[column], utc=True, errors="coerce")
    numeric_columns = ("open", "high", "low", "close")
    for column in numeric_columns:
        bars[column] = pd.to_numeric(bars[column], errors="coerce")
    bars = bars.dropna(subset=["timestamp_utc", "bar_start_utc", *numeric_columns])
    bars = bars.sort_values("timestamp_utc").reset_index(drop=True)
    return bars[bars["timestamp_utc"] <= pd.Timestamp(period_end)].reset_index(drop=True)


def _simulate_breakout_retest(
    config: ProjectConfig,
    bars: pd.DataFrame,
    cell: Any,
    expert: str,
) -> list[dict[str, object]]:
    featured = _add_breakout_features(bars)
    signals = _breakout_signals(
        featured,
        expert=expert,
        symbol=cell.symbol,
        point_size=float(config.symbols["symbols"][cell.symbol]["point_size"]),
        period_start=pd.Timestamp(cell.start_utc),
        period_end=pd.Timestamp(cell.end_utc),
    )

    current_equity = float(config.phase0["project"]["starting_equity_usd"])
    risk_pct = float(config.phase0["project"]["phase0_risk_per_trade_pct"])
    symbol_details = config.symbols["symbols"][cell.symbol]
    cost_model = config.cost_models["cost_models"][cell.cost_model]
    cost = {
        "spread_points": float(cost_model["spread_points"][cell.symbol]),
        "entry_slippage_price": float(cost_model.get("slippage_points_entry", 0.0))
        * float(symbol_details["point_size"]),
        "exit_slippage_price": float(cost_model.get("slippage_points_exit", 0.0))
        * float(symbol_details["point_size"]),
        "commission": float(cost_model.get("commission_usd_per_round_turn_lot", 0.0)),
    }

    trades: list[dict[str, object]] = []
    open_until: pd.Timestamp | None = None
    for signal in signals:
        signal_time = pd.Timestamp(signal["timestamp_utc"])
        if open_until is not None and signal_time <= open_until:
            continue
        trade = _simulate_signal(
            bars=featured,
            signal=signal,
            expert=expert,
            symbol=cell.symbol,
            current_equity=current_equity,
            risk_pct=risk_pct,
            contract_size=float(symbol_details["contract_size_per_lot"]),
            min_lot=float(symbol_details["min_lot"]),
            lot_step=float(symbol_details["lot_step"]),
            cost=cost,
        )
        if trade is None:
            continue
        trades.append(trade)
        current_equity += float(trade["net_pnl_usd"])
        open_until = pd.Timestamp(trade["exit_time_utc"])
    return trades


def _add_breakout_features(bars: pd.DataFrame) -> pd.DataFrame:
    result = bars.copy()
    result["atr14"] = _wilder_atr(result["high"], result["low"], result["close"], period=14)

    day = result["timestamp_utc"].dt.floor("D")
    daily = result.assign(_day=day).groupby("_day").agg(
        previous_daily_high_source=("high", "max"),
        previous_daily_low_source=("low", "min"),
    )
    result["previous_daily_high"] = day.map(daily["previous_daily_high_source"].shift(1))
    result["previous_daily_low"] = day.map(daily["previous_daily_low_source"].shift(1))

    normalized = result["timestamp_utc"].dt.floor("D")
    week_start = normalized - pd.to_timedelta(result["timestamp_utc"].dt.weekday, unit="D")
    weekly = result.assign(_week_start=week_start).groupby("_week_start").agg(
        previous_weekly_high_source=("high", "max"),
        previous_weekly_low_source=("low", "min"),
    )
    result["previous_weekly_high"] = week_start.map(weekly["previous_weekly_high_source"].shift(1))
    result["previous_weekly_low"] = week_start.map(weekly["previous_weekly_low_source"].shift(1))
    return _add_latest_swings(result, left=4, right=4)


def _wilder_atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int) -> pd.Series:
    previous_close = close.shift(1)
    true_range = pd.concat(
        [high - low, (high - previous_close).abs(), (low - previous_close).abs()],
        axis=1,
    ).max(axis=1)
    result = pd.Series(math.nan, index=true_range.index, dtype="float64")
    if len(true_range) < period:
        return result
    seed = true_range.iloc[:period]
    if seed.isna().any():
        return result
    result.iloc[period - 1] = seed.mean()
    for position in range(period, len(true_range)):
        current = true_range.iloc[position]
        previous = result.iloc[position - 1]
        result.iloc[position] = ((previous * (period - 1)) + current) / period
    return result


def _add_latest_swings(bars: pd.DataFrame, left: int, right: int) -> pd.DataFrame:
    result = bars.copy()
    result["_timestamp_for_merge"] = result["timestamp_utc"]
    result["_original_order"] = range(len(result))
    result = _merge_latest_swing(result, _confirmed_swings(result, "HIGH", left, right), "high")
    result = _merge_latest_swing(result, _confirmed_swings(result, "LOW", left, right), "low")
    return result.drop(columns=["_timestamp_for_merge", "_original_order"])


def _confirmed_swings(bars: pd.DataFrame, kind: str, left: int, right: int) -> pd.DataFrame:
    price_col = "high" if kind == "HIGH" else "low"
    prices = pd.to_numeric(bars[price_col], errors="coerce")
    mask = pd.Series(True, index=bars.index)
    for offset in range(1, left + 1):
        mask &= prices > prices.shift(offset) if kind == "HIGH" else prices < prices.shift(offset)
    for offset in range(1, right + 1):
        mask &= prices > prices.shift(-offset) if kind == "HIGH" else prices < prices.shift(-offset)

    rows: list[dict[str, object]] = []
    positions = {index: position for position, index in enumerate(bars.index)}
    for index in bars.index[mask.fillna(False)]:
        position = positions[index]
        available_position = position + right
        if available_position >= len(bars):
            continue
        rows.append(
            {
                "level_price": prices.loc[index],
                "swing_time_utc": bars["timestamp_utc"].iloc[position],
                "available_time_utc": bars["timestamp_utc"].iloc[available_position],
            }
        )
    return pd.DataFrame(rows, columns=("level_price", "swing_time_utc", "available_time_utc"))


def _merge_latest_swing(bars: pd.DataFrame, swings: pd.DataFrame, label: str) -> pd.DataFrame:
    price_col = f"latest_swing_{label}"
    time_col = f"latest_swing_{label}_time_utc"
    available_col = f"latest_swing_{label}_available_time_utc"
    if swings.empty:
        bars[price_col] = pd.NA
        bars[time_col] = pd.NaT
        bars[available_col] = pd.NaT
        return bars

    right = swings.sort_values("available_time_utc").rename(
        columns={
            "level_price": price_col,
            "swing_time_utc": time_col,
            "available_time_utc": available_col,
        }
    )
    merged = pd.merge_asof(
        bars.sort_values("_timestamp_for_merge"),
        right[[available_col, price_col, time_col]].sort_values(available_col),
        left_on="_timestamp_for_merge",
        right_on=available_col,
        direction="backward",
    )
    return merged.sort_values("_original_order").reset_index(drop=True)


def _breakout_signals(
    bars: pd.DataFrame,
    expert: str,
    symbol: str,
    point_size: float,
    period_start: pd.Timestamp,
    period_end: pd.Timestamp,
) -> list[dict[str, object]]:
    arrays = {
        "timestamp": bars["timestamp_utc"].to_numpy(),
        "open": bars["open"].to_numpy(dtype=float),
        "high": bars["high"].to_numpy(dtype=float),
        "low": bars["low"].to_numpy(dtype=float),
        "close": bars["close"].to_numpy(dtype=float),
        "atr14": bars["atr14"].to_numpy(dtype=float),
        "previous_daily_high": bars["previous_daily_high"].to_numpy(dtype=float),
        "previous_daily_low": bars["previous_daily_low"].to_numpy(dtype=float),
        "previous_weekly_high": bars["previous_weekly_high"].to_numpy(dtype=float),
        "previous_weekly_low": bars["previous_weekly_low"].to_numpy(dtype=float),
        "latest_swing_high": bars["latest_swing_high"].to_numpy(dtype=float),
        "latest_swing_low": bars["latest_swing_low"].to_numpy(dtype=float),
        "latest_swing_high_time_utc": bars["latest_swing_high_time_utc"].to_numpy(),
        "latest_swing_low_time_utc": bars["latest_swing_low_time_utc"].to_numpy(),
    }
    signals: list[dict[str, object]] = []
    for confirmation_position in range(2, len(bars)):
        confirmation_time = pd.Timestamp(arrays["timestamp"][confirmation_position])
        if confirmation_time < period_start or confirmation_time > period_end:
            continue
        retest_position = confirmation_position - 1
        candidates: list[dict[str, object]] = []
        if float(arrays["close"][confirmation_position]) > float(arrays["open"][confirmation_position]):
            candidates.extend(_long_candidates(arrays, retest_position, point_size))
        if float(arrays["close"][confirmation_position]) < float(arrays["open"][confirmation_position]):
            candidates.extend(_short_candidates(arrays, retest_position, point_size))
        if not candidates:
            continue
        candidates.sort(key=lambda item: (float(item["stop_distance"]), pd.Timestamp(item["level_time_utc"])))
        selected = candidates[0]
        signals.append(
            {
                **selected,
                "expert": expert,
                "symbol": symbol,
                "timestamp_utc": confirmation_time,
                "confirmation_index": confirmation_position,
                "retest_index": retest_position,
            }
        )
    return signals


def _long_candidates(arrays: dict[str, Any], retest_position: int, point_size: float) -> list[dict[str, object]]:
    retest_atr = float(arrays["atr14"][retest_position])
    if not math.isfinite(retest_atr):
        return []
    retest_low = float(arrays["low"][retest_position])
    retest_high = float(arrays["high"][retest_position])
    retest_close = float(arrays["close"][retest_position])
    candidates: list[dict[str, object]] = []
    for break_position in range(max(0, retest_position - 20), retest_position):
        break_atr = float(arrays["atr14"][break_position])
        if not math.isfinite(break_atr):
            continue
        for level in _candidate_levels(arrays, break_position, "LONG", point_size):
            price = float(level["level_price"])
            if float(arrays["close"][break_position]) < price + 0.3 * break_atr:
                continue
            if not (retest_low <= price + 5.0 * point_size):
                continue
            if retest_close < price:
                continue
            entry_price = retest_high + point_size
            stop_loss = retest_low - 0.1 * retest_atr
            risk_price = entry_price - stop_loss
            if risk_price <= 0:
                continue
            candidates.append(
                {
                    "direction": "LONG",
                    "reason_code": "BREAKOUT_RETEST_LONG",
                    "level_price": price,
                    "level_kind": level["level_kind"],
                    "level_time_utc": level["level_time_utc"],
                    "break_index": break_position,
                    "break_time_utc": arrays["timestamp"][break_position],
                    "entry_price": entry_price,
                    "stop_loss": stop_loss,
                    "stop_distance": risk_price,
                    "expires_after_bars": 5,
                }
            )
    return candidates


def _short_candidates(arrays: dict[str, Any], retest_position: int, point_size: float) -> list[dict[str, object]]:
    retest_atr = float(arrays["atr14"][retest_position])
    if not math.isfinite(retest_atr):
        return []
    retest_low = float(arrays["low"][retest_position])
    retest_high = float(arrays["high"][retest_position])
    retest_close = float(arrays["close"][retest_position])
    candidates: list[dict[str, object]] = []
    for break_position in range(max(0, retest_position - 20), retest_position):
        break_atr = float(arrays["atr14"][break_position])
        if not math.isfinite(break_atr):
            continue
        for level in _candidate_levels(arrays, break_position, "SHORT", point_size):
            price = float(level["level_price"])
            if float(arrays["close"][break_position]) > price - 0.3 * break_atr:
                continue
            if not (retest_high >= price - 5.0 * point_size):
                continue
            if retest_close > price:
                continue
            entry_price = retest_low - point_size
            stop_loss = retest_high + 0.1 * retest_atr
            risk_price = stop_loss - entry_price
            if risk_price <= 0:
                continue
            candidates.append(
                {
                    "direction": "SHORT",
                    "reason_code": "BREAKOUT_RETEST_SHORT",
                    "level_price": price,
                    "level_kind": level["level_kind"],
                    "level_time_utc": level["level_time_utc"],
                    "break_index": break_position,
                    "break_time_utc": arrays["timestamp"][break_position],
                    "entry_price": entry_price,
                    "stop_loss": stop_loss,
                    "stop_distance": risk_price,
                    "expires_after_bars": 5,
                }
            )
    return candidates


def _candidate_levels(
    arrays: dict[str, Any],
    position: int,
    direction: str,
    point_size: float,
) -> list[dict[str, object]]:
    timestamp = arrays["timestamp"][position]
    if direction == "LONG":
        raw = (
            ("previous_daily_high", arrays["previous_daily_high"][position], timestamp),
            ("previous_weekly_high", arrays["previous_weekly_high"][position], timestamp),
            (
                "latest_swing_high",
                arrays["latest_swing_high"][position],
                arrays["latest_swing_high_time_utc"][position],
            ),
        )
    else:
        raw = (
            ("previous_daily_low", arrays["previous_daily_low"][position], timestamp),
            ("previous_weekly_low", arrays["previous_weekly_low"][position], timestamp),
            (
                "latest_swing_low",
                arrays["latest_swing_low"][position],
                arrays["latest_swing_low_time_utc"][position],
            ),
        )

    levels = [
        {"level_kind": kind, "level_price": float(price), "level_time_utc": level_time}
        for kind, price, level_time in raw
        if pd.notna(price) and pd.notna(level_time)
    ]
    if not levels:
        return []

    tolerance_price = 10.0 * point_size
    kept: list[dict[str, object]] = []
    kept_prices: list[float] = []
    for level in sorted(levels, key=lambda item: pd.Timestamp(item["level_time_utc"]), reverse=True):
        price = float(level["level_price"])
        if all(abs(price - kept_price) > tolerance_price for kept_price in kept_prices):
            kept.append(level)
            kept_prices.append(price)
    return sorted(kept, key=lambda item: pd.Timestamp(item["level_time_utc"]))


def _simulate_signal(
    bars: pd.DataFrame,
    signal: dict[str, object],
    expert: str,
    symbol: str,
    current_equity: float,
    risk_pct: float,
    contract_size: float,
    min_lot: float,
    lot_step: float,
    cost: dict[str, float],
) -> dict[str, object] | None:
    direction = str(signal["direction"])
    entry_price = float(signal["entry_price"])
    stop_loss = float(signal["stop_loss"])
    take_profit = entry_price + 1.5 * (entry_price - stop_loss) if direction == "LONG" else entry_price - 1.5 * (stop_loss - entry_price)
    entry = _find_entry(bars, signal, entry_price, direction, cost["entry_slippage_price"])
    if entry is None:
        return None
    price_risk = entry["price"] - stop_loss if direction == "LONG" else stop_loss - entry["price"]
    if price_risk <= 0:
        return None
    risk_money = current_equity * risk_pct
    raw_lots = risk_money / (price_risk * contract_size)
    lots = _floor_to_step(raw_lots, lot_step)
    if lots < min_lot:
        return None
    exit_fill = _find_exit(
        bars,
        int(entry["bar_index"]),
        direction,
        stop_loss,
        take_profit,
        cost["exit_slippage_price"],
    )
    gross = (
        (float(exit_fill["price"]) - float(entry["price"])) * lots * contract_size
        if direction == "LONG"
        else (float(entry["price"]) - float(exit_fill["price"])) * lots * contract_size
    )
    net = gross - (lots * cost["commission"])
    return {
        "expert": expert,
        "symbol": symbol,
        "direction": direction,
        "entry_time_utc": entry["time_utc"],
        "exit_time_utc": exit_fill["time_utc"],
        "entry_price": entry["price"],
        "exit_price": exit_fill["price"],
        "stop_loss": stop_loss,
        "take_profit": take_profit,
        "lots": lots,
        "gross_pnl_usd": gross,
        "costs_usd": gross - net,
        "net_pnl_usd": net,
        "r_multiple": net / risk_money,
        "exit_reason": exit_fill["reason"],
    }


def _find_entry(
    bars: pd.DataFrame,
    signal: dict[str, object],
    entry_price: float,
    direction: str,
    slippage: float,
) -> dict[str, object] | None:
    signal_time = pd.Timestamp(signal["timestamp_utc"])
    starts = bars["bar_start_utc"]
    position = int(starts.searchsorted(signal_time, side="left"))
    if position >= len(bars):
        return None
    expires = int(signal.get("expires_after_bars", 5))
    candidates = bars.iloc[position : position + expires]
    for index, row in candidates.iterrows():
        triggered = (
            float(row["high"]) >= entry_price if direction == "LONG" else float(row["low"]) <= entry_price
        )
        if triggered:
            adjusted = entry_price + slippage if direction == "LONG" else entry_price - slippage
            return {"time_utc": row["bar_start_utc"], "price": adjusted, "bar_index": int(index)}
    return None


def _find_exit(
    bars: pd.DataFrame,
    start_index: int,
    direction: str,
    stop_loss: float,
    take_profit: float,
    slippage: float,
) -> dict[str, object]:
    for index in range(start_index, len(bars)):
        row = bars.iloc[index]
        high = float(row["high"])
        low = float(row["low"])
        if direction == "LONG":
            stop_hit = low <= stop_loss
            target_hit = high >= take_profit
        else:
            stop_hit = high >= stop_loss
            target_hit = low <= take_profit
        if stop_hit:
            price = stop_loss - slippage if direction == "LONG" else stop_loss + slippage
            return {"time_utc": row["timestamp_utc"], "price": price, "bar_index": index, "reason": "stop_loss"}
        if target_hit:
            price = take_profit - slippage if direction == "LONG" else take_profit + slippage
            return {"time_utc": row["timestamp_utc"], "price": price, "bar_index": index, "reason": "take_profit"}
    final = bars.iloc[-1]
    close_price = float(final["bid_close"]) if direction == "LONG" and "bid_close" in final else float(final["close"])
    if direction == "SHORT" and "ask_close" in final:
        close_price = float(final["ask_close"])
    price = close_price - slippage if direction == "LONG" else close_price + slippage
    return {
        "time_utc": final["timestamp_utc"],
        "price": price,
        "bar_index": len(bars) - 1,
        "reason": "end_of_test_period",
    }


def _floor_to_step(value: float, lot_step: float) -> float:
    decimals = max(0, len(f"{lot_step:.10f}".rstrip("0").split(".", maxsplit=1)[1]))
    return round(math.floor((value / lot_step) + 1e-12) * lot_step, decimals)


def _metrics_from_rows(trades: list[dict[str, object]], starting_equity: float) -> dict[str, float | int]:
    if not trades:
        return {
            "trade_count": 0,
            "profit_factor": 0.0,
            "win_rate": 0.0,
            "total_pnl_usd": 0.0,
            "total_return_pct": 0.0,
            "max_drawdown_pct": 0.0,
            "avg_trade_R": 0.0,
            "median_trade_R": 0.0,
        }
    pnl = pd.Series([float(trade["net_pnl_usd"]) for trade in trades], dtype="float64")
    r_values = pd.Series([float(trade["r_multiple"]) for trade in trades], dtype="float64")
    gross_profit = float(pnl[pnl > 0].sum())
    gross_loss = abs(float(pnl[pnl < 0].sum()))
    profit_factor = gross_profit / gross_loss if gross_loss > 0 else (math.inf if gross_profit > 0 else 0.0)
    equity = starting_equity + pnl.cumsum()
    equity = pd.concat([pd.Series([starting_equity]), equity], ignore_index=True)
    drawdown_pct = ((equity.cummax() - equity) / equity.cummax().replace(0, pd.NA) * 100.0).fillna(0.0)
    total_pnl = float(pnl.sum())
    return {
        "trade_count": int(len(trades)),
        "profit_factor": float(profit_factor),
        "win_rate": float((pnl > 0).mean()),
        "total_pnl_usd": total_pnl,
        "total_return_pct": float(total_pnl / starting_equity * 100.0),
        "max_drawdown_pct": float(drawdown_pct.max()),
        "avg_trade_R": float(r_values.mean()),
        "median_trade_R": float(r_values.median()),
    }


def _compare_metrics(
    reference: dict[str, object],
    observed: dict[str, float | int],
    tolerance_pct: float,
) -> tuple[dict[str, object], ...]:
    metrics = ("trade_count", "profit_factor", "win_rate", "total_pnl_usd", "max_drawdown_pct")
    rows: list[dict[str, object]] = []
    for metric in metrics:
        expected = float(reference[metric])
        actual = float(observed[metric])
        delta_pct = _relative_delta_pct(expected, actual)
        rows.append(
            {
                "metric": metric,
                "reference": expected,
                "independent": actual,
                "delta_pct": delta_pct,
                "tolerance_pct": tolerance_pct,
                "status": "PASS" if delta_pct <= tolerance_pct else "FAIL",
            }
        )
    return tuple(rows)


def _relative_delta_pct(expected: float, actual: float) -> float:
    if expected == actual:
        return 0.0
    if expected == 0:
        return math.inf
    return abs(actual - expected) / abs(expected) * 100.0


def _render_report(
    status: str,
    expert: str,
    cell_id: int,
    broker: str,
    cost_model: str,
    symbol: str,
    bars_path: Path,
    source_summary_path: Path,
    source_trades_path: Path,
    metrics: dict[str, float | int],
    comparisons: tuple[dict[str, object], ...],
    trade_count: int,
    tolerance_pct: float,
) -> str:
    return "\n".join(
        [
            "# Phase 0 Independent Reproduction",
            "",
            f"Overall status: {status}",
            "",
            "## Scope",
            "",
            _markdown_table(
                [
                    {
                        "Field": "expert",
                        "Value": expert,
                    },
                    {"Field": "cell_id", "Value": str(cell_id)},
                    {"Field": "broker", "Value": broker},
                    {"Field": "cost_model", "Value": cost_model},
                    {"Field": "symbol", "Value": symbol},
                    {"Field": "method", "Value": "standalone_pandas_event_replay"},
                    {"Field": "tolerance_pct", "Value": f"{tolerance_pct:.2f}"},
                ],
                ["Field", "Value"],
            ),
            "",
            "## Source Artifacts",
            "",
            _markdown_table(
                [
                    {"Artifact": "M5 bars", "Path": str(bars_path)},
                    {"Artifact": "Reference matrix summary", "Path": str(source_summary_path)},
                    {"Artifact": "Reference trade ledger", "Path": str(source_trades_path)},
                ],
                ["Artifact", "Path"],
            ),
            "",
            "## Comparison",
            "",
            _markdown_table(
                [
                    {
                        "Metric": str(row["metric"]),
                        "Reference": _format_number(float(row["reference"])),
                        "Independent": _format_number(float(row["independent"])),
                        "Delta %": _format_number(float(row["delta_pct"])),
                        "Tolerance %": _format_number(float(row["tolerance_pct"])),
                        "Status": str(row["status"]),
                    }
                    for row in comparisons
                ],
                ["Metric", "Reference", "Independent", "Delta %", "Tolerance %", "Status"],
            ),
            "",
            "## Independent Metrics",
            "",
            _markdown_table(
                [{"Metric": key, "Value": _format_number(float(value))} for key, value in metrics.items()],
                ["Metric", "Value"],
            ),
            "",
            "## Notes",
            "",
            f"- Independent trade rows simulated: {trade_count}",
            "- This replay does not call the Phase 0 strategy class, execution simulator, or metrics module.",
            "- It uses the same processed M5 bars and the same pre-registered mechanical rules for the selected approved cell.",
            "- This closes D4 for the selected cell if every comparison row is PASS.",
            "",
        ]
    )


def _format_number(value: float) -> str:
    if math.isinf(value):
        return "inf"
    if abs(value) >= 1000:
        return f"{value:.2f}"
    return f"{value:.6g}"


def _markdown_table(rows: list[dict[str, str]], columns: list[str]) -> str:
    if not rows:
        return "No rows."
    header = "| " + " | ".join(columns) + " |"
    separator = "| " + " | ".join("---" for _ in columns) + " |"
    body = [
        "| " + " | ".join(str(row.get(column, "")).replace("|", "\\|") for column in columns) + " |"
        for row in rows
    ]
    return "\n".join([header, separator, *body])


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()
