from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = ROOT / "config" / "frozen_crosspair_strength_daily.json"
OUTPUT_ROOT = ROOT / "outputs" / "crosspair_strength_daily"
PIP = 0.0001


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_config() -> dict[str, Any]:
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    if config["status"] != "LOCKED_BEFORE_EURUSD_OUTCOME_INSPECTION":
        raise RuntimeError("Cross-pair contract is not frozen")
    return config


def verify_sources(config: dict[str, Any]) -> dict[str, str]:
    root = Path(config["source_root"])
    actual: dict[str, str] = {}
    for name, expected in config["source_sha256"].items():
        path = root / name
        value = sha256(path)
        if value != expected:
            raise RuntimeError(f"Source hash mismatch for {path}: {value} != {expected}")
        actual[name] = value
    return actual


def load_bars(
    root: Path, symbol: str, *, execution: bool = False
) -> pd.DataFrame:
    columns = ["timestamp_ms", "bid_open", "ask_open", "bid_close", "ask_close"]
    if execution:
        columns.extend(["bid_high", "bid_low", "ask_high", "ask_low"])
    frame = pd.read_parquet(root / f"{symbol}_M5_BIDASK.parquet", columns=columns)
    frame["timestamp"] = pd.to_datetime(frame.pop("timestamp_ms"), unit="ms", utc=True)
    frame = frame.set_index("timestamp").sort_index()
    if frame.index.has_duplicates:
        raise RuntimeError(f"Duplicate timestamps in {symbol}")
    frame["mid_close"] = (frame["bid_close"] + frame["ask_close"]) / 2.0
    return frame


def vote_direction(votes: list[int]) -> int:
    score = sum(votes)
    if score >= 2:
        return 1
    if score <= -2:
        return -1
    return 0


def build_candidates(config: dict[str, Any]) -> tuple[pd.DataFrame, int]:
    root = Path(config["source_root"])
    symbols = list(config["signal"]["predictor_symbols"])
    closes = []
    for symbol in symbols:
        frame = load_bars(root, symbol)
        closes.append(frame[["mid_close"]].rename(columns={"mid_close": symbol}))
    joined = pd.concat(closes, axis=1, join="inner").sort_index()

    lag_bars = int(config["signal"]["return_minutes"] // 5)
    lagged = joined.shift(lag_bars)
    timestamps = joined.index.to_series()
    exact_lag = timestamps - timestamps.shift(lag_bars) == pd.Timedelta(
        minutes=int(config["signal"]["return_minutes"])
    )
    returns = np.log(joined) - np.log(lagged)
    returns = returns.loc[exact_lag]

    decision_hours = set(int(value) for value in config["signal"]["decision_hours_utc"])
    signal_hours = {(hour - 1) % 24 for hour in decision_hours}
    eligible = returns[
        (returns.index.minute == 55)
        & (returns.index.hour.isin(signal_hours))
        & (returns.index.dayofweek < 5)
    ].copy()

    votes = pd.DataFrame(index=eligible.index)
    votes["vote_eurgbp"] = np.sign(eligible["EURGBP"]).astype(int)
    votes["vote_eurjpy"] = np.sign(eligible["EURJPY"]).astype(int)
    votes["vote_gbpusd"] = np.sign(eligible["GBPUSD"]).astype(int)
    votes["vote_usdjpy"] = -np.sign(eligible["USDJPY"]).astype(int)
    votes["vote_score"] = votes.sum(axis=1)
    votes["direction_code"] = votes[
        ["vote_eurgbp", "vote_eurjpy", "vote_gbpusd", "vote_usdjpy"]
    ].apply(lambda row: vote_direction(row.tolist()), axis=1)
    votes = votes[votes["direction_code"] != 0].copy()
    votes["signal_time"] = votes.index
    votes["entry_time"] = votes.index + pd.Timedelta(minutes=5)
    votes["utc_date"] = votes["entry_time"].dt.date
    candidates = votes.groupby("utc_date", sort=True, as_index=False).head(1).copy()
    candidates["direction"] = np.where(
        candidates["direction_code"] > 0, "LONG", "SHORT"
    )

    synchronized_dates = int(
        eligible.index.to_series().dt.normalize().nunique()
    )
    expected = config["source_only_census"]
    actual_counts = {
        "synchronized_weekdays": synchronized_dates,
        "candidates": int(len(candidates)),
        "long": int((candidates["direction"] == "LONG").sum()),
        "short": int((candidates["direction"] == "SHORT").sum()),
    }
    for key, value in actual_counts.items():
        if int(expected[key]) != value:
            raise RuntimeError(
                f"Source-only census mismatch {key}: {value} != {expected[key]}"
            )
    return candidates.reset_index(drop=True), synchronized_dates


def simulate(
    candidates: pd.DataFrame,
    eurusd: pd.DataFrame,
    config: dict[str, Any],
) -> pd.DataFrame:
    execution = config["execution"]
    risk_price = float(execution["risk_pips"]) * PIP
    target_price = float(execution["target_pips"]) * PIP
    entry_slippage = float(execution["entry_adverse_slippage_pips"]) * PIP
    exit_slippage = float(execution["exit_adverse_slippage_pips"]) * PIP
    max_hold = pd.Timedelta(minutes=int(execution["maximum_hold_minutes"]))
    rows: list[dict[str, Any]] = []

    for candidate in candidates.itertuples(index=False):
        entry_time = pd.Timestamp(candidate.entry_time)
        if entry_time not in eurusd.index:
            continue
        entry_bar = eurusd.loc[entry_time]
        long_side = candidate.direction == "LONG"
        if long_side:
            entry_price = float(entry_bar["ask_open"]) + entry_slippage
            stop_price = entry_price - risk_price
            target = entry_price + target_price
        else:
            entry_price = float(entry_bar["bid_open"]) - entry_slippage
            stop_price = entry_price + risk_price
            target = entry_price - target_price

        path = eurusd.loc[
            (eurusd.index >= entry_time)
            & (eurusd.index < entry_time + max_hold)
        ]
        if path.empty:
            continue

        exit_time = path.index[-1]
        exit_reason = "TIME"
        if long_side:
            exit_price = float(path.iloc[-1]["bid_close"]) - exit_slippage
        else:
            exit_price = float(path.iloc[-1]["ask_close"]) + exit_slippage

        for timestamp, bar in path.iterrows():
            if long_side:
                open_price = float(bar["bid_open"])
                stop_hit = float(bar["bid_low"]) <= stop_price
                target_hit = float(bar["bid_high"]) >= target
                if stop_hit:
                    exit_time = timestamp
                    exit_price = (
                        open_price if open_price < stop_price else stop_price
                    ) - exit_slippage
                    exit_reason = "STOP"
                    break
                if target_hit:
                    exit_time = timestamp
                    exit_price = target - exit_slippage
                    exit_reason = "TARGET"
                    break
            else:
                open_price = float(bar["ask_open"])
                stop_hit = float(bar["ask_high"]) >= stop_price
                target_hit = float(bar["ask_low"]) <= target
                if stop_hit:
                    exit_time = timestamp
                    exit_price = (
                        open_price if open_price > stop_price else stop_price
                    ) + exit_slippage
                    exit_reason = "STOP"
                    break
                if target_hit:
                    exit_time = timestamp
                    exit_price = target + exit_slippage
                    exit_reason = "TARGET"
                    break

        pnl_price = (
            exit_price - entry_price if long_side else entry_price - exit_price
        )
        net_r = pnl_price / risk_price
        rows.append(
            {
                "signal_time": candidate.signal_time,
                "entry_time": entry_time,
                "exit_time": exit_time,
                "direction": candidate.direction,
                "vote_score": int(candidate.vote_score),
                "vote_eurgbp": int(candidate.vote_eurgbp),
                "vote_eurjpy": int(candidate.vote_eurjpy),
                "vote_gbpusd": int(candidate.vote_gbpusd),
                "vote_usdjpy": int(candidate.vote_usdjpy),
                "entry_price": entry_price,
                "stop_price": stop_price,
                "target_price": target,
                "exit_price": exit_price,
                "exit_reason": exit_reason,
                "net_r": net_r,
                "pnl_usd_0_01_lot": net_r
                * float(execution["risk_pips"])
                * 0.10,
            }
        )
    return pd.DataFrame(rows)


def metrics(frame: pd.DataFrame, column: str = "net_r") -> dict[str, Any]:
    values = frame[column].astype(float)
    winners = values[values > 0]
    losers = values[values < 0]
    gross_profit = float(winners.sum())
    gross_loss = float(-losers.sum())
    curve = values.cumsum()
    drawdown = curve.cummax() - curve
    payoff = (
        float(winners.mean() / -losers.mean())
        if len(winners) and len(losers)
        else 0.0
    )
    return {
        "trades": int(len(values)),
        "wins": int(len(winners)),
        "losses": int(len(losers)),
        "win_rate": float(len(winners) / len(values)) if len(values) else 0.0,
        "net_r": float(values.sum()),
        "net_usd_0_01_lot": float(values.sum() * 0.8),
        "profit_factor": gross_profit / gross_loss if gross_loss > 0 else 0.0,
        "payoff_ratio": payoff,
        "maximum_drawdown_r": float(drawdown.max()) if len(drawdown) else 0.0,
    }


def evaluate(
    trades: pd.DataFrame,
    synchronized_dates: int,
    config: dict[str, Any],
) -> dict[str, Any]:
    ordered = trades.sort_values("exit_time").reset_index(drop=True)
    primary = metrics(ordered)
    primary["trades_per_synchronized_weekday"] = (
        len(ordered) / synchronized_dates
    )

    stress_r = (
        float(config["primary_stress"]["additional_round_trip_pips"])
        / float(config["execution"]["risk_pips"])
    )
    ordered["stressed_r"] = ordered["net_r"] - stress_r
    stress = metrics(ordered, "stressed_r")

    block_definitions = {
        "B1_2016H2_2018": ("2016-07-01", "2019-01-01"),
        "B2_2019_2021": ("2019-01-01", "2022-01-01"),
        "B3_2022_2024": ("2022-01-01", "2025-01-01"),
        "B4_2025_2026H1": ("2025-01-01", "2026-07-01"),
    }
    blocks = {}
    for name, (start, end) in block_definitions.items():
        subset = ordered[
            (ordered["exit_time"] >= pd.Timestamp(start, tz="UTC"))
            & (ordered["exit_time"] < pd.Timestamp(end, tz="UTC"))
        ]
        blocks[name] = metrics(subset)

    latest_12 = metrics(
        ordered[
            (ordered["exit_time"] >= pd.Timestamp("2025-07-01", tz="UTC"))
            & (ordered["exit_time"] < pd.Timestamp("2026-07-01", tz="UTC"))
        ]
    )
    month_values = ordered.assign(
        month=ordered["exit_time"].dt.to_period("M")
    ).groupby("month")["net_r"].sum()
    positive_month_share = float((month_values > 0).mean())

    remove_count = max(1, int(math.ceil(0.05 * len(ordered))))
    removed = ordered.drop(
        ordered.nlargest(remove_count, "net_r").index
    ).sort_values("exit_time")
    removed_metrics = metrics(removed)

    gates_cfg = config["gates"]
    gates = {
        "minimum_frequency": primary["trades_per_synchronized_weekday"]
        >= float(gates_cfg["minimum_trades_per_synchronized_weekday"]),
        "maximum_frequency": primary["trades_per_synchronized_weekday"]
        <= float(gates_cfg["maximum_trades_per_synchronized_weekday"]),
        "full_profit_factor": primary["profit_factor"]
        >= float(gates_cfg["minimum_full_profit_factor"]),
        "win_rate_floor": primary["win_rate"]
        >= float(gates_cfg["minimum_win_rate"]),
        "win_rate_ceiling": primary["win_rate"]
        <= float(gates_cfg["maximum_win_rate"]),
        "payoff_floor": primary["payoff_ratio"]
        >= float(gates_cfg["minimum_payoff_ratio"]),
        "payoff_ceiling": primary["payoff_ratio"]
        <= float(gates_cfg["maximum_payoff_ratio"]),
        "positive_full_net": primary["net_r"] > 0,
        "stressed_profit_factor": stress["profit_factor"]
        >= float(gates_cfg["minimum_stressed_profit_factor"]),
        "positive_stressed_net": stress["net_r"] > 0,
        "positive_each_block": all(value["net_r"] > 0 for value in blocks.values()),
        "minimum_blocks_pf_1_15": sum(
            value["profit_factor"] >= 1.15 for value in blocks.values()
        )
        >= int(gates_cfg["minimum_blocks_pf_1_15"]),
        "last_12_month_profit_factor": latest_12["profit_factor"]
        >= float(gates_cfg["minimum_last_12_month_profit_factor"]),
        "positive_active_month_share": positive_month_share
        >= float(gates_cfg["minimum_positive_active_month_share"]),
        "top_5pct_removed_profit_factor": removed_metrics["profit_factor"]
        >= float(gates_cfg["minimum_top_5pct_removed_profit_factor"]),
        "maximum_drawdown": primary["maximum_drawdown_r"]
        <= float(gates_cfg["maximum_drawdown_r"]),
    }
    return {
        "schema_version": "eurusd_crosspair_strength_daily_result_v1",
        "campaign_id": config["campaign_id"],
        "status": (
            "HISTORICAL_GATES_PASS_MT5_PARITY_REQUIRED"
            if all(gates.values())
            else "REJECT_CROSSPAIR_STRENGTH"
        ),
        "synchronized_weekdays": synchronized_dates,
        "primary": primary,
        "stress_plus_0_5_pip": stress,
        "chronological_blocks": blocks,
        "latest_12_months": latest_12,
        "positive_active_month_share": positive_month_share,
        "top_5pct_removed": removed_metrics,
        "gates": gates,
        "all_gates_pass": all(gates.values()),
    }


def render_markdown(result: dict[str, Any]) -> str:
    primary = result["primary"]
    stress = result["stress_plus_0_5_pip"]
    lines = [
        "# EURUSD cross-pair strength daily verdict",
        "",
        f"Status: `{result['status']}`",
        "",
        "| Metric | Result |",
        "|---|---:|",
        f"| Trades | {primary['trades']:,} |",
        f"| Trades/synchronized weekday | {primary['trades_per_synchronized_weekday']:.3f} |",
        f"| Win rate | {primary['win_rate']:.2%} |",
        f"| Payoff ratio | {primary['payoff_ratio']:.3f} |",
        f"| Profit factor | {primary['profit_factor']:.4f} |",
        f"| Net R | {primary['net_r']:.2f} |",
        f"| P&L at 0.01 lot | ${primary['net_usd_0_01_lot']:.2f} |",
        f"| Maximum drawdown | {primary['maximum_drawdown_r']:.2f}R |",
        f"| +0.5 pip PF | {stress['profit_factor']:.4f} |",
        f"| +0.5 pip net | {stress['net_r']:.2f}R |",
        "",
        "## Chronological blocks",
        "",
        "| Block | Trades | Win rate | PF | Net R |",
        "|---|---:|---:|---:|---:|",
    ]
    for name, value in result["chronological_blocks"].items():
        lines.append(
            f"| {name} | {value['trades']:,} | {value['win_rate']:.2%} | "
            f"{value['profit_factor']:.4f} | {value['net_r']:.2f} |"
        )
    lines.extend(
        [
            "",
            "## Gates",
            "",
            *[
                f"- [{'x' if passed else ' '}] `{name}`"
                for name, passed in result["gates"].items()
            ],
            "",
            (
                "The candidate may proceed only to MT5 parity work."
                if result["all_gates_pass"]
                else "The frozen candidate is rejected. No parameter rescue or demo promotion is authorized."
            ),
            "",
        ]
    )
    return "\n".join(lines)


def run() -> tuple[dict[str, Any], dict[str, Path]]:
    config = load_config()
    hashes = verify_sources(config)
    candidates, synchronized_dates = build_candidates(config)
    eurusd = load_bars(Path(config["source_root"]), "EURUSD", execution=True)
    trades = simulate(candidates, eurusd, config)
    result = evaluate(trades, synchronized_dates, config)
    result["source_sha256_verified"] = hashes

    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    candidate_path = OUTPUT_ROOT / "CANDIDATES.csv"
    trade_path = OUTPUT_ROOT / "TRADES.csv"
    result_path = OUTPUT_ROOT / "RESULT.json"
    markdown_path = OUTPUT_ROOT / "VERDICT.md"
    candidates.to_csv(candidate_path, index=False)
    trades.to_csv(trade_path, index=False)
    result_path.write_text(
        json.dumps(result, indent=2) + "\n", encoding="utf-8"
    )
    markdown_path.write_text(render_markdown(result), encoding="utf-8")
    return result, {
        "candidates": candidate_path,
        "trades": trade_path,
        "result": result_path,
        "verdict": markdown_path,
    }

