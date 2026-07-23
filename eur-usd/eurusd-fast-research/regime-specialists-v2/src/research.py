from __future__ import annotations

import hashlib
import importlib.util
import json
import math
from pathlib import Path
import sys
from typing import Any, Iterable

import numpy as np
import pandas as pd

PIP = 0.0001
PIP_VALUE_USD_001_LOT = 0.10
STAGE_ORDER = ("train", "validation", "internal", "exam")


def _load_v1_module(package_root: Path):
    path = package_root.parent / "thousand-strategy-campaign-v1" / "src" / "campaign.py"
    spec = importlib.util.spec_from_file_location("eurusd_hunt_v1_campaign", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load V1 execution engine: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _wilder(series: pd.Series, period: int) -> pd.Series:
    return series.ewm(alpha=1.0 / period, adjust=False, min_periods=period).mean()


def add_h4_regimes(frame: pd.DataFrame, contract: dict[str, Any]) -> tuple[pd.DataFrame, pd.DataFrame]:
    work = frame.copy()
    for field in ("open", "high", "low", "close"):
        work[f"mid_{field}"] = (work[f"bid_{field}"] + work[f"ask_{field}"]) / 2.0
    indexed = work.set_index("timestamp")
    h4 = pd.DataFrame(
        {
            "open": indexed["mid_open"].resample("4h", origin="epoch").first(),
            "high": indexed["mid_high"].resample("4h", origin="epoch").max(),
            "low": indexed["mid_low"].resample("4h", origin="epoch").min(),
            "close": indexed["mid_close"].resample("4h", origin="epoch").last(),
        }
    ).dropna()
    previous = h4["close"].shift(1)
    tr = pd.concat(
        [
            h4["high"] - h4["low"],
            (h4["high"] - previous).abs(),
            (h4["low"] - previous).abs(),
        ],
        axis=1,
    ).max(axis=1)
    period = int(contract["atr_period"])
    h4["atr"] = _wilder(tr, period)
    up = h4["high"].diff()
    down = -h4["low"].diff()
    plus_dm = pd.Series(np.where((up > down) & (up > 0), up, 0.0), index=h4.index)
    minus_dm = pd.Series(np.where((down > up) & (down > 0), down, 0.0), index=h4.index)
    plus_di = 100.0 * _wilder(plus_dm, period) / h4["atr"].replace(0, np.nan)
    minus_di = 100.0 * _wilder(minus_dm, period) / h4["atr"].replace(0, np.nan)
    dx = 100.0 * (plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, np.nan)
    h4["adx"] = _wilder(dx, int(contract["adx_period"]))
    h4["ema"] = h4["close"].ewm(span=int(contract["ema_period"]), adjust=False).mean()
    slope_bars = int(contract["slope_bars"])
    h4["slope_atr"] = (h4["ema"] - h4["ema"].shift(slope_bars)) / h4["atr"]
    efficiency_bars = int(contract["efficiency_lookback"])
    h4["efficiency"] = (
        (h4["close"] - h4["close"].shift(efficiency_bars)).abs()
        / h4["close"].diff().abs().rolling(efficiency_bars).sum().replace(0, np.nan)
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

    valid = h4[["atr", "adx", "slope_atr", "efficiency", "width_atr", "atr_ratio"]].notna().all(axis=1)
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
    trend_up = trend_common & (h4["slope_atr"] >= float(contract["trend_slope_atr_min"]))
    trend_down = trend_common & (h4["slope_atr"] <= -float(contract["trend_slope_atr_min"]))
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
    mapped = pd.merge_asof(
        work[["timestamp"]].sort_values("timestamp"),
        states[["available_time", "regime"]].sort_values("available_time"),
        left_on="timestamp",
        right_on="available_time",
        direction="backward",
    )
    work["regime"] = mapped["regime"].fillna("transition").to_numpy()
    return work, h4.reset_index()


def _candidate(module, spec: dict[str, Any]):
    payload = {
        "candidate_id": spec["specialist_id"],
        "attempt": 1001 + int(list_id(spec["specialist_id"])),
        "archetype": spec["archetype"],
        "direction": spec["direction"],
        "threshold": float(spec["threshold"]),
        "stop_atr": float(spec["stop_atr"]),
        "target_r": float(spec["target_r"]),
        "max_hold_bars": int(spec["max_hold_bars"]),
    }
    digest_payload = {key: value for key, value in payload.items() if key not in {"candidate_id"}}
    payload["sha256"] = hashlib.sha256(
        json.dumps(digest_payload, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    return module.Candidate(**payload)


def list_id(identifier: str) -> int:
    return {
        "EURV2_TREND_UP": 1,
        "EURV2_TREND_DOWN": 2,
        "EURV2_COMPRESSION_UP": 3,
        "EURV2_COMPRESSION_DOWN": 4,
        "EURV2_CHOP_ROTATION": 5,
    }[identifier]


def _quarantine_filter(
    trades: list[dict[str, Any]], intervals: list[list[str]]
) -> list[dict[str, Any]]:
    parsed = [(pd.Timestamp(start), pd.Timestamp(end)) for start, end in intervals]
    result = []
    for trade in trades:
        entry = pd.Timestamp(trade["entry_time"])
        exit_time = pd.Timestamp(trade["exit_time"]) + pd.Timedelta(hours=1)
        if any(entry < end and exit_time > start for start, end in parsed):
            continue
        result.append(trade)
    return result


def profit_factor(values: Iterable[float]) -> float:
    values = list(values)
    gain = sum(value for value in values if value > 0)
    loss = -sum(value for value in values if value < 0)
    return math.inf if loss == 0 and gain > 0 else (gain / loss if loss else 0.0)


def measure(
    trades: list[dict[str, Any]], specialist: dict[str, Any], stage: str, gate: dict[str, Any]
) -> dict[str, Any]:
    for trade in trades:
        stop_pips = abs(float(trade["entry"]) - float(trade["stop"])) / PIP
        trade["net_r"] = float(trade["net_pips"]) / stop_pips
        trade["stress_r"] = float(trade["stress_net_pips"]) / stop_pips
        trade["specialist_id"] = specialist["specialist_id"]
        trade["owned_regime"] = specialist["owned_regime"]
    values = np.asarray([trade["stress_r"] for trade in trades], dtype=float)
    native = np.asarray([trade["net_r"] for trade in trades], dtype=float)
    months: dict[str, float] = {}
    for trade in trades:
        months[trade["exit_time"][:7]] = months.get(trade["exit_time"][:7], 0.0) + trade["stress_r"]
    positive_months = sum(value > 0 for value in months.values()) / len(months) if months else 0.0
    removed = np.sort(values)[::-1][min(int(gate["top_winners_removed"]), len(values)) :]
    if len(values):
        equity = np.cumsum(values)
        peak = np.maximum.accumulate(np.insert(equity, 0, 0.0))[1:]
        drawdown = float(np.max(peak - equity))
    else:
        drawdown = 0.0
    row = {
        "specialist_id": specialist["specialist_id"],
        "owned_regime": specialist["owned_regime"],
        "source_candidate": specialist["source_candidate"],
        "stage": stage,
        "status": "OPENED",
        "trades": len(trades),
        "wins": int(np.sum(native > 0)),
        "win_rate": float(np.mean(native > 0)) if len(native) else 0.0,
        "net_pips": float(sum(trade["net_pips"] for trade in trades)),
        "pnl_usd_001_lot": float(sum(trade["net_pips"] for trade in trades) * PIP_VALUE_USD_001_LOT),
        "stress_net_r": float(np.sum(values)),
        "average_r": float(np.mean(values)) if len(values) else 0.0,
        "stress_profit_factor": profit_factor(values),
        "positive_active_month_share": positive_months,
        "maximum_drawdown_r": drawdown,
        "removed_profit_factor": profit_factor(removed),
    }
    row["gate_pass"] = bool(
        row["trades"] >= int(gate["minimum_trades"])
        and row["stress_profit_factor"] >= float(gate["minimum_stress_profit_factor"])
        and row["average_r"] >= float(gate["minimum_average_r"])
        and row["positive_active_month_share"] >= float(gate["minimum_positive_active_month_share"])
        and row["maximum_drawdown_r"] <= float(gate["maximum_drawdown_r"])
        and row["removed_profit_factor"] >= float(gate["minimum_removed_profit_factor"])
    )
    return row


def sealed_row(specialist: dict[str, Any], stage: str) -> dict[str, Any]:
    return {
        "specialist_id": specialist["specialist_id"],
        "owned_regime": specialist["owned_regime"],
        "source_candidate": specialist["source_candidate"],
        "stage": stage,
        "status": "SEALED_PREDECESSOR_FAILED",
        "trades": "",
        "wins": "",
        "win_rate": "",
        "net_pips": "",
        "pnl_usd_001_lot": "",
        "stress_net_r": "",
        "average_r": "",
        "stress_profit_factor": "",
        "positive_active_month_share": "",
        "maximum_drawdown_r": "",
        "removed_profit_factor": "",
        "gate_pass": False,
    }


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    pd.DataFrame(rows).to_csv(path, index=False, lineterminator="\n")


def run_campaign(config: dict[str, Any], package_root: Path) -> dict[str, Any]:
    output = package_root / "outputs"
    output.mkdir(parents=True, exist_ok=True)
    source = config["source"]
    storage = Path(source["storage_root"])
    cache = storage / source["h1_cache"]
    metadata_path = storage / source["h1_cache_metadata"]
    if not cache.is_file() or not metadata_path.is_file():
        raise FileNotFoundError("Frozen V1 H1 bid/ask cache and metadata are required")
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    if hashlib.sha256(cache.read_bytes()).hexdigest() != metadata["cache_sha256"]:
        raise RuntimeError("H1 cache checksum does not match its metadata")
    frame = pd.read_csv(cache, compression="gzip", parse_dates=["timestamp"])
    frame["timestamp"] = pd.to_datetime(frame["timestamp"], utc=True)
    frame, h4 = add_h4_regimes(frame, config["regime_classifier"])
    module = _load_v1_module(package_root)
    featured = module.add_features(frame, config)

    census = (
        h4.assign(month=lambda value: value["timestamp"].dt.strftime("%Y-%m"))
        .groupby(["month", "regime"])
        .size()
        .rename("h4_bars")
        .reset_index()
    )
    census.to_csv(output / "REGIME_CENSUS.csv", index=False, lineterminator="\n")

    metrics_rows: list[dict[str, Any]] = []
    trade_rows: list[dict[str, Any]] = []
    qualified: list[str] = []
    for specialist in config["specialists"]:
        candidate = _candidate(module, specialist)
        base_mask = module.signal_mask(featured, candidate)
        regime_mask = (featured["regime"] == specialist["owned_regime"]).to_numpy()
        mask = base_mask & regime_mask
        still_open = True
        for stage in STAGE_ORDER:
            if not still_open:
                metrics_rows.append(sealed_row(specialist, stage))
                continue
            start, end = (pd.Timestamp(value) for value in config["windows"][stage])
            trades = module.simulate(featured, candidate, mask, start, end, config)
            trades = _quarantine_filter(trades, source["quarantined_utc_intervals"])
            row = measure(trades, specialist, stage, config["stage_gates"][stage])
            metrics_rows.append(row)
            trade_rows.extend({**trade, "stage": stage} for trade in trades)
            still_open = bool(row["gate_pass"])
        if still_open:
            qualified.append(specialist["specialist_id"])

    _write_csv(output / "SPECIALIST_STAGE_METRICS.csv", metrics_rows)
    _write_csv(output / "SPECIALIST_TRADES.csv", trade_rows)
    candidate_rows = []
    for spec in config["specialists"]:
        candidate = _candidate(module, spec)
        candidate_rows.append({**spec, "parameter_sha256": candidate.sha256})
    _write_csv(output / "FROZEN_SPECIALISTS.csv", candidate_rows)

    result = {
        "campaign_id": config["campaign_id"],
        "architecture": "MUTUALLY_EXCLUSIVE_H4_REGIMES_WITH_INDEPENDENT_SPECIALISTS",
        "source_cache_sha256": metadata["cache_sha256"],
        "source_raw_hour_files": metadata["raw_hour_files"],
        "source_nonempty_h1_rows": metadata["nonempty_h1_rows"],
        "quarantined_intervals": source["quarantined_utc_intervals"],
        "attempts_v1_prior": 1000,
        "attempts_v2": len(config["specialists"]),
        "qualified_specialists": qualified,
        "portfolio_opened": len(qualified) >= int(config["portfolio_gates"]["minimum_qualifying_specialists"]),
        "m5_replication_opened": False,
        "mt5_replication_opened": False,
        "demo_rehearsal_ready": False,
    }
    if result["portfolio_opened"]:
        result["verdict"] = "SPECIALISTS_QUALIFIED_PORTFOLIO_REPLICATION_REQUIRED"
    else:
        result["verdict"] = "NO_V2_SPECIALIST_PORTFOLIO_STOP"
    (output / "VERDICT.json").write_text(
        json.dumps(result, indent=2, allow_nan=False) + "\n", encoding="utf-8", newline="\n"
    )
    return result
