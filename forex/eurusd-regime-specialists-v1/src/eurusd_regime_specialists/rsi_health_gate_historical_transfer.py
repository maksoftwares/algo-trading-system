from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from .h4_chop_anchor_validation import _evaluation_subset, _scenario_summary
from .neutral_h4_quiet_state_transfer import (
    PIP,
    PIP_VALUE_USD_001_LOT,
    load_m5,
    sha256_file,
)


def utc_timestamp(value: str | pd.Timestamp) -> pd.Timestamp:
    result = pd.Timestamp(value)
    if result.tzinfo is None:
        return result.tz_localize("UTC")
    return result.tz_convert("UTC")


def profit_factor(values: np.ndarray | pd.Series) -> float:
    vector = np.asarray(values, dtype=float)
    gains = float(vector[vector > 0.0].sum())
    losses = float(-vector[vector < 0.0].sum())
    if losses == 0.0:
        return math.inf if gains > 0.0 else 0.0
    return gains / losses


def aggregate_m15(m5: pd.DataFrame, rule: dict[str, Any]) -> pd.DataFrame:
    work = m5.copy()
    work["m15_time"] = work["timestamp"].dt.floor("15min")
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
    result = work.groupby("m15_time", sort=True).agg(aggregation)
    result["m5_bars"] = work.groupby("m15_time", sort=True).size()
    result = result.reset_index().rename(columns={"m15_time": "timestamp"})
    result["complete"] = result["m5_bars"].eq(
        int(rule["signal_timeframe_minutes"]) // 5
    )
    prior_close = result["bid_close"].shift(1)
    true_range = pd.concat(
        [
            result["bid_high"] - result["bid_low"],
            (result["bid_high"] - prior_close).abs(),
            (result["bid_low"] - prior_close).abs(),
        ],
        axis=1,
    ).max(axis=1)
    atr_period = int(rule["atr_period"])
    result["atr"] = true_range.ewm(
        alpha=1.0 / atr_period,
        adjust=False,
        min_periods=atr_period,
    ).mean()
    delta = result["bid_close"].diff()
    gains = delta.clip(lower=0.0)
    losses = -delta.clip(upper=0.0)
    average_gain = gains.ewm(
        alpha=1.0 / int(rule["rsi_period"]),
        adjust=False,
        min_periods=int(rule["rsi_period"]),
    ).mean()
    average_loss = losses.ewm(
        alpha=1.0 / int(rule["rsi_period"]),
        adjust=False,
        min_periods=int(rule["rsi_period"]),
    ).mean()
    relative_strength = average_gain / average_loss.replace(0.0, np.nan)
    result["rsi"] = 100.0 - (100.0 / (1.0 + relative_strength))
    result["band_mid"] = result["bid_close"].rolling(
        int(rule["bands_period"])
    ).mean()
    result["body_fraction"] = (
        (result["bid_close"] - result["bid_open"]).abs()
        / (result["bid_high"] - result["bid_low"]).replace(0.0, np.nan)
    ).fillna(0.0)
    result["recent_low"] = result["bid_low"].rolling(
        int(rule["recent_stop_lookback_m15_bars"])
    ).min()
    return result


def build_rsi_signals(
    m15: pd.DataFrame, rule: dict[str, Any]
) -> pd.DataFrame:
    signal = (
        m15["complete"]
        & (m15["rsi"] <= float(rule["rsi_oversold_inclusive"]))
        & (m15["bid_close"] < m15["band_mid"])
        & (m15["body_fraction"] >= float(rule["minimum_body_fraction"]))
        & m15["atr"].notna()
        & m15["recent_low"].notna()
    )
    signals = m15.loc[
        signal,
        [
            "timestamp",
            "atr",
            "recent_low",
            "rsi",
            "band_mid",
            "body_fraction",
        ],
    ].copy()
    signals = signals.rename(columns={"timestamp": "signal_time_utc"})
    signals["entry_time_utc"] = signals["signal_time_utc"] + pd.Timedelta(
        minutes=int(rule["signal_timeframe_minutes"])
    )
    signals["side"] = "LONG"
    signals = signals[
        ~signals["entry_time_utc"].dt.hour.isin(
            [int(value) for value in rule["blocked_entry_hours_utc"]]
        )
    ]
    return signals.reset_index(drop=True)


def overlaps_quarantine(
    entry: pd.Timestamp,
    exit_time: pd.Timestamp,
    quarantine: list[dict[str, Any]],
) -> bool:
    return any(
        entry < utc_timestamp(item["end_utc"])
        and exit_time >= utc_timestamp(item["start_utc"])
        for item in quarantine
    )


def simulate_rsi_trades(
    m5: pd.DataFrame,
    signals: pd.DataFrame,
    rule: dict[str, Any],
    quarantine: list[dict[str, Any]],
) -> pd.DataFrame:
    timestamp_to_index = pd.Series(
        m5.index.to_numpy(), index=m5["timestamp"]
    ).to_dict()
    blocked_until: pd.Timestamp | None = None
    daily_count: dict[str, int] = {}
    records: list[dict[str, Any]] = []
    slippage = float(rule["adverse_slippage_pips_per_side"]) * PIP
    for row in signals.sort_values("entry_time_utc").itertuples():
        entry_time = row.entry_time_utc
        if blocked_until is not None and entry_time <= blocked_until:
            continue
        entry_index = timestamp_to_index.get(entry_time)
        if entry_index is None:
            continue
        entry_date = entry_time.strftime("%Y-%m-%d")
        if daily_count.get(entry_date, 0) >= int(
            rule["maximum_trades_per_utc_day"]
        ):
            continue
        bar = m5.iloc[int(entry_index)]
        spread_pips = float(bar["ask_open"] - bar["bid_open"]) / PIP
        if spread_pips > float(rule["maximum_entry_spread_pips"]):
            continue
        entry = float(bar["ask_open"]) + slippage
        minimum_distance = max(
            float(rule["stop_atr_multiple"]) * float(row.atr),
            float(rule["stop_floor_pips"]) * PIP,
        )
        stop = min(float(row.recent_low), entry - minimum_distance)
        stop_pips = (entry - stop) / PIP
        if stop_pips > float(rule["stop_ceiling_pips"]):
            continue
        target = entry + float(rule["target_r"]) * (entry - stop)
        exit_index = len(m5) - 1
        exit_price = float(m5.iloc[-1]["bid_close"]) - slippage
        exit_reason = "END_OF_DATA"
        for path_index in range(int(entry_index), len(m5)):
            path = m5.iloc[path_index]
            if float(path["bid_open"]) <= stop:
                exit_index = path_index
                exit_price = float(path["bid_open"]) - slippage
                exit_reason = "STOP_GAP"
                break
            stop_hit = float(path["bid_low"]) <= stop
            target_hit = float(path["bid_high"]) >= target
            if stop_hit:
                exit_index = path_index
                exit_price = stop - slippage
                exit_reason = "STOP"
                break
            if target_hit:
                exit_index = path_index
                exit_price = target - slippage
                exit_reason = "TARGET"
                break
        exit_time = m5.iloc[exit_index]["timestamp"]
        net_pips = (exit_price - entry) / PIP
        r_value = net_pips / stop_pips
        quarantined = overlaps_quarantine(
            entry_time, exit_time, quarantine
        )
        if quarantined:
            net_pips = 0.0
            r_value = 0.0
            exit_reason = "QUARANTINE_CASH"
        records.append(
            {
                "signal_time_utc": row.signal_time_utc,
                "entry_time_utc": entry_time,
                "exit_time_utc": exit_time,
                "entry_date": entry_date,
                "side": "LONG",
                "entry": entry,
                "stop": stop,
                "target": target,
                "exit": exit_price,
                "entry_spread_pips": spread_pips,
                "stop_pips": stop_pips,
                "net_pips": net_pips,
                "r": r_value,
                "stress_r": r_value,
                "pnl_usd_001_lot": net_pips * PIP_VALUE_USD_001_LOT,
                "exit_reason": exit_reason,
                "quarantined": quarantined,
            }
        )
        daily_count[entry_date] = daily_count.get(entry_date, 0) + 1
        blocked_until = exit_time
    return pd.DataFrame(records)


def causal_health_gate(
    trades: pd.DataFrame, contract: dict[str, Any]
) -> pd.DataFrame:
    ordered = trades.sort_values(
        ["entry_time_utc", "exit_time_utc"]
    ).reset_index(drop=True)
    exits = ordered.sort_values(
        ["exit_time_utc", "entry_time_utc"]
    ).reset_index(drop=True)
    exit_times = (
        exits["exit_time_utc"]
        .dt.as_unit("ns")
        .astype("int64")
        .to_numpy(dtype=np.int64)
    )
    exit_pnl = exits["pnl_usd_001_lot"].to_numpy(dtype=float)
    lookback = int(contract["lookback_completed_shadow_trades"])
    threshold = float(contract["minimum_trailing_profit_factor"])
    available_counts: list[int] = []
    trailing_factors: list[float] = []
    admitted: list[bool] = []
    for entry in ordered["entry_time_utc"]:
        count = int(
            np.searchsorted(exit_times, entry.value, side="right")
        )
        window = exit_pnl[:count][-lookback:]
        factor = profit_factor(window)
        available_counts.append(count)
        trailing_factors.append(factor)
        admitted.append(len(window) == lookback and factor >= threshold)
    ordered["available_completed_shadow_trades"] = available_counts
    ordered["trailing_shadow_profit_factor"] = trailing_factors
    ordered["health_gate_admitted"] = admitted
    return ordered


def apply_stress(trades: pd.DataFrame, extra_pips: float) -> pd.DataFrame:
    result = trades.copy()
    result["r"] = result["r"] - float(extra_pips) / result["stop_pips"]
    result["stress_r"] = result["r"]
    result["pnl_usd_001_lot"] = result["pnl_usd_001_lot"] - (
        float(extra_pips) * PIP_VALUE_USD_001_LOT
    )
    return result


def weekday_count(window: list[str]) -> int:
    start, end = map(utc_timestamp, window)
    return len(
        pd.bdate_range(
            start=start.normalize(),
            end=(end - pd.Timedelta(nanoseconds=1)).normalize(),
        )
    )


def window_economics(
    trades: pd.DataFrame,
    window: list[str],
    extra_pips: float,
) -> dict[str, Any]:
    subset = _evaluation_subset(trades, window)
    base = _scenario_summary(subset)
    stressed = _scenario_summary(apply_stress(subset, extra_pips))
    weekdays = weekday_count(window)
    dates = (
        subset["entry_time_utc"].dt.strftime("%Y-%m-%d").nunique()
        if not subset.empty
        else 0
    )
    base["trades_per_weekday"] = len(subset) / weekdays if weekdays else 0.0
    base["active_dates"] = int(dates)
    base["weekday_coverage"] = dates / weekdays if weekdays else 0.0
    return {"base": base, "stressed": stressed}


def nearest_signal_coverage(
    broker_entries: pd.Series,
    signal_entries: pd.Series,
    tolerance_minutes: int,
) -> dict[str, Any]:
    broker = np.sort(
        pd.to_datetime(broker_entries, utc=True)
        .dt.as_unit("ns")
        .astype("int64")
        .to_numpy()
    )
    signals = np.sort(
        pd.to_datetime(signal_entries, utc=True)
        .dt.as_unit("ns")
        .astype("int64")
        .to_numpy()
    )
    tolerance = int(pd.Timedelta(minutes=tolerance_minutes).value)
    matched = 0
    for value in broker:
        position = int(np.searchsorted(signals, value))
        neighbors = signals[max(0, position - 1) : min(len(signals), position + 1)]
        if len(neighbors) and int(np.min(np.abs(neighbors - value))) <= tolerance:
            matched += 1
    return {
        "broker_entries": len(broker),
        "matching_entries": matched,
        "coverage": matched / len(broker) if len(broker) else 0.0,
        "tolerance_minutes": int(tolerance_minutes),
    }


def parity_checks(
    parity: dict[str, Any], gates: dict[str, Any]
) -> dict[str, bool]:
    return {
        "minimum_broker_entry_signal_coverage": parity[
            "broker_entry_signal_coverage"
        ]["coverage"]
        >= float(gates["minimum_broker_entry_signal_coverage"]),
        "minimum_raw_trade_count_ratio_to_broker": parity[
            "raw_trade_count_ratio_to_broker"
        ]
        >= float(gates["minimum_raw_trade_count_ratio_to_broker"]),
        "maximum_raw_trade_count_ratio_to_broker": parity[
            "raw_trade_count_ratio_to_broker"
        ]
        <= float(gates["maximum_raw_trade_count_ratio_to_broker"]),
    }


def earlier_checks(
    windows: dict[str, dict[str, Any]], gates: dict[str, Any]
) -> dict[str, bool]:
    full = windows["FULL_EARLIER_TRANSFER"]["base"]
    return {
        "minimum_trades": full["trades"] >= int(gates["minimum_trades"]),
        "minimum_trades_per_weekday": full["trades_per_weekday"]
        >= float(gates["minimum_trades_per_weekday"]),
        "minimum_profit_factor": full["profit_factor"]
        >= float(gates["minimum_profit_factor"]),
        "minimum_stressed_profit_factor": windows[
            "FULL_EARLIER_TRANSFER"
        ]["stressed"]["profit_factor"]
        >= float(gates["minimum_stressed_profit_factor"]),
        "each_chronological_block_profit_factor": all(
            windows[name]["base"]["profit_factor"]
            > float(
                gates[
                    "minimum_each_chronological_block_profit_factor_exclusive"
                ]
            )
            for name in (
                "EARLY_2017_2019",
                "MIDDLE_2020_2022H1",
                "LATE_2022H2_2024H1",
            )
        ),
        "minimum_latest_12_month_profit_factor": windows[
            "EARLIER_LATEST_12_MONTHS"
        ]["base"]["profit_factor"]
        >= float(gates["minimum_latest_12_month_profit_factor"]),
        "minimum_top_5pct_winners_removed_profit_factor": full[
            "top_5pct_winners_removed_profit_factor"
        ]
        >= float(gates["minimum_top_5pct_winners_removed_profit_factor"]),
        "minimum_positive_active_month_share": full[
            "positive_active_month_share"
        ]
        >= float(gates["minimum_positive_active_month_share"]),
        "maximum_closed_trade_drawdown": full["maximum_drawdown_r"]
        <= float(gates["maximum_closed_trade_drawdown_r"]),
    }


def broker_window_checks(
    economics: dict[str, Any], gates: dict[str, Any]
) -> dict[str, bool]:
    return {
        "minimum_trades_per_weekday": economics["base"][
            "trades_per_weekday"
        ]
        >= float(gates["minimum_trades_per_weekday"]),
        "minimum_profit_factor": economics["base"]["profit_factor"]
        >= float(gates["minimum_profit_factor"]),
        "minimum_stressed_profit_factor": economics["stressed"][
            "profit_factor"
        ]
        >= float(gates["minimum_stressed_profit_factor"]),
    }


def render_report(result: dict[str, Any]) -> str:
    earlier = result["economics"]["FULL_EARLIER_TRANSFER"]
    recent = result["economics"]["BROKER_PORTABILITY"]
    base = earlier["base"]
    parity = result["parity"]
    block_rows = "\n".join(
        f'| {name} | {result["economics"][name]["base"]["trades"]} | '
        f'{result["economics"][name]["base"]["trades_per_weekday"]:.3f} | '
        f'{result["economics"][name]["base"]["profit_factor"]:.3f} |'
        for name in (
            "EARLY_2017_2019",
            "MIDDLE_2020_2022H1",
            "LATE_2022H2_2024H1",
        )
    )
    return f"""# EURUSD RSI health-gate historical transfer result

Status: **{result["status"]}**

Demo-order authorization: **false**

## Reconstruction parity

- Broker entries: {parity["broker_entries"]}
- Dukas raw trades: {parity["dukas_raw_trades"]}
- Raw count ratio: {parity["raw_trade_count_ratio_to_broker"]:.3f}
- Broker entries with a qualifying Dukas signal within {parity["broker_entry_signal_coverage"]["tolerance_minutes"]} minutes: {parity["broker_entry_signal_coverage"]["coverage"]:.2%}
- Parity admitted: {parity["admitted"]}

## Earlier 2017-2024 transfer

| Trades | Trades/weekday | Win rate | Payoff | PF | Stressed PF | Net R |
|---:|---:|---:|---:|---:|---:|---:|
| {base["trades"]} | {base["trades_per_weekday"]:.3f} | {base["win_rate"]:.2%} | {base["realized_payoff_ratio"]:.3f} | {base["profit_factor"]:.3f} | {earlier["stressed"]["profit_factor"]:.3f} | {base["net_r"]:.2f} |

| Chronological block | Trades | Trades/weekday | PF |
|---|---:|---:|---:|
{block_rows}

## 2024-2026 cross-broker transfer

| Trades | Trades/weekday | PF | Stressed PF |
|---:|---:|---:|---:|
| {recent["base"]["trades"]} | {recent["base"]["trades_per_weekday"]:.3f} | {recent["base"]["profit_factor"]:.3f} | {recent["stressed"]["profit_factor"]:.3f} |

The 30-trade/PF-1.05 gate is unchanged and uses only completed shadow
outcomes. This is a reverse historical transfer of a mined gate, not pristine
validation and not authority for demo orders.
"""


def run(config_path: Path, output_dir: Path) -> dict[str, Any]:
    config_bytes = config_path.read_bytes()
    config = json.loads(config_bytes)
    root = config_path.parent.parent
    anchor_path = root / config["anchor_config"]["path"]
    ea_path = root / config["ea_source"]["path"]
    broker_path = root / config["broker_shadow_ledger"]["path"]
    for path, expected in (
        (anchor_path, config["anchor_config"]["sha256"]),
        (ea_path, config["ea_source"]["sha256"]),
        (broker_path, config["broker_shadow_ledger"]["sha256"]),
    ):
        if sha256_file(path) != expected:
            raise RuntimeError(f"Source checksum mismatch: {path}")
    anchor = json.loads(anchor_path.read_bytes())
    m5 = load_m5(anchor["source"])
    m15 = aggregate_m15(m5, config["rsi_rule"])
    signals = build_rsi_signals(m15, config["rsi_rule"])
    raw_trades = simulate_rsi_trades(
        m5,
        signals,
        config["rsi_rule"],
        anchor["source"]["quarantine"],
    )
    gated = causal_health_gate(raw_trades, config["health_gate"])
    admitted_trades = gated[gated["health_gate_admitted"]].copy()

    broker = pd.read_csv(broker_path)
    broker = broker[
        broker["sleeve"].eq(config["broker_shadow_ledger"]["sleeve"])
    ].copy()
    broker["entry_time"] = pd.to_datetime(broker["entry_time"], utc=True)
    portability_window = config["windows"]["BROKER_PORTABILITY"]
    portability_start, portability_end = map(
        utc_timestamp, portability_window
    )
    broker = broker[
        (broker["entry_time"] >= portability_start)
        & (broker["entry_time"] < portability_end)
    ].copy()
    if len(broker) != int(
        config["broker_shadow_ledger"]["expected_rows_before_transfer_end"]
    ):
        raise RuntimeError("Broker RSI ledger row count mismatch")
    recent_signals = signals[
        (signals["entry_time_utc"] >= portability_start)
        & (signals["entry_time_utc"] < portability_end)
    ]
    recent_raw = _evaluation_subset(raw_trades, portability_window)
    coverage = nearest_signal_coverage(
        broker["entry_time"],
        recent_signals["entry_time_utc"],
        int(config["parity_admission"]["matching_tolerance_minutes"]),
    )
    parity = {
        "broker_entries": len(broker),
        "dukas_qualifying_signals": len(recent_signals),
        "dukas_raw_trades": len(recent_raw),
        "raw_trade_count_ratio_to_broker": len(recent_raw) / len(broker),
        "broker_entry_signal_coverage": coverage,
    }
    parity["checks"] = parity_checks(parity, config["parity_admission"])
    parity["admitted"] = all(parity["checks"].values())

    economics = {
        name: window_economics(
            admitted_trades,
            window,
            float(config["stress"]["extra_round_trip_pips"]),
        )
        for name, window in config["windows"].items()
    }
    earlier_gate_checks = earlier_checks(
        economics, config["earlier_transfer_admission"]
    )
    broker_gate_checks = broker_window_checks(
        economics["BROKER_PORTABILITY"],
        config["broker_window_transfer_admission"],
    )
    earlier_admitted = all(earlier_gate_checks.values())
    broker_window_admitted = all(broker_gate_checks.values())
    if not parity["admitted"]:
        status = "RECONSTRUCTION_PARITY_REJECTED"
    elif not earlier_admitted:
        status = "HISTORICAL_TRANSFER_REJECTED"
    elif not broker_window_admitted:
        status = "BROKER_WINDOW_PORTABILITY_REJECTED"
    else:
        status = "HISTORICAL_TRANSFER_CANDIDATE_REQUIRES_FRESH_CONFIRMATION"

    result = {
        "schema_version": "eurusd_rsi_health_gate_historical_transfer_result_v1",
        "frozen_config_sha256": hashlib.sha256(config_bytes).hexdigest(),
        "market_source_sha256": anchor["source"]["sha256"],
        "ea_source_sha256": config["ea_source"]["sha256"],
        "broker_ledger_sha256": config["broker_shadow_ledger"]["sha256"],
        "research_boundary": "RETROSPECTIVE_REVERSE_TRANSFER_NOT_PRISTINE_OOS",
        "broker_action_allowed": False,
        "demo_order_authorized": False,
        "raw_trade_count": len(raw_trades),
        "gated_trade_count": len(admitted_trades),
        "parity": parity,
        "economics": economics,
        "earlier_transfer": {
            "checks": earlier_gate_checks,
            "admitted": earlier_admitted,
        },
        "broker_window_transfer": {
            "checks": broker_gate_checks,
            "admitted": broker_window_admitted,
        },
        "status": status,
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    signals.to_csv(output_dir / "QUALIFYING_SIGNALS.csv", index=False)
    gated.to_csv(output_dir / "RAW_TRADES_WITH_GATE.csv", index=False)
    admitted_trades.to_csv(output_dir / "GATED_TRADES.csv", index=False)
    (output_dir / "RESULT.json").write_text(
        json.dumps(result, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    (output_dir / "RESULT.md").write_text(
        render_report(result), encoding="utf-8"
    )
    return result
