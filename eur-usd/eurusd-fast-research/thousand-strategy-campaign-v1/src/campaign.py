from __future__ import annotations

import csv
import gzip
import hashlib
import json
import math
import os
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from itertools import product
from pathlib import Path
from statistics import NormalDist
from typing import Any, Iterable

import numpy as np
import pandas as pd


PIP = 0.0001
ARCHETYPES = (
    ("trend_pullback_long", "long", (0.00, 0.10, 0.20, 0.30, 0.40), 24),
    ("trend_pullback_short", "short", (0.00, 0.10, 0.20, 0.30, 0.40), 24),
    ("range_breakout_long", "long", (0.00, 0.05, 0.10, 0.15, 0.20), 18),
    ("range_breakout_short", "short", (0.00, 0.05, 0.10, 0.15, 0.20), 18),
    ("compression_breakout_long", "long", (0.55, 0.65, 0.75, 0.85, 0.95), 24),
    ("compression_breakout_short", "short", (0.55, 0.65, 0.75, 0.85, 0.95), 24),
    ("zscore_reversion_long", "long", (1.00, 1.25, 1.50, 1.75, 2.00), 18),
    ("zscore_reversion_short", "short", (1.00, 1.25, 1.50, 1.75, 2.00), 18),
    ("failed_break_reversion_long", "long", (0.00, 0.05, 0.10, 0.15, 0.20), 12),
    ("failed_break_reversion_short", "short", (0.00, 0.05, 0.10, 0.15, 0.20), 12),
)
STOP_ATR_VALUES = (0.75, 1.00, 1.25, 1.50)
TARGET_R_VALUES = (0.75, 1.00, 1.25, 1.50, 2.00)


@dataclass(frozen=True)
class Candidate:
    candidate_id: str
    attempt: int
    archetype: str
    direction: str
    threshold: float
    stop_atr: float
    target_r: float
    max_hold_bars: int
    sha256: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "candidate_id": self.candidate_id,
            "attempt": self.attempt,
            "archetype": self.archetype,
            "direction": self.direction,
            "threshold": self.threshold,
            "stop_atr": self.stop_atr,
            "target_r": self.target_r,
            "max_hold_bars": self.max_hold_bars,
            "sha256": self.sha256,
        }


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def build_candidate_manifest() -> list[Candidate]:
    candidates: list[Candidate] = []
    attempt = 0
    for archetype, direction, thresholds, hold in ARCHETYPES:
        for threshold, stop_atr, target_r in product(
            thresholds, STOP_ATR_VALUES, TARGET_R_VALUES
        ):
            attempt += 1
            payload = {
                "attempt": attempt,
                "archetype": archetype,
                "direction": direction,
                "threshold": threshold,
                "stop_atr": stop_atr,
                "target_r": target_r,
                "max_hold_bars": hold,
            }
            candidates.append(
                Candidate(
                    candidate_id=f"EURHUNT01_{attempt:04d}",
                    sha256=sha256_bytes(canonical_bytes(payload)),
                    **payload,
                )
            )
    if len(candidates) != 1000:
        raise RuntimeError(f"Expected 1,000 candidates, got {len(candidates)}")
    if len({candidate.sha256 for candidate in candidates}) != 1000:
        raise RuntimeError("Candidate manifest contains duplicate parameter sets")
    return candidates


def month_keys(start_utc: str, end_exclusive_utc: str) -> list[str]:
    start = pd.Timestamp(start_utc)
    end = pd.Timestamp(end_exclusive_utc)
    return [
        value.strftime("%Y-%m")
        for value in pd.date_range(start, end, freq="MS", inclusive="left")
    ]


def frozen_manifest_digest(
    raw_root: Path, expected_months: list[str]
) -> tuple[str, int, list[str]]:
    manifests = sorted(raw_root.glob("year=*/month=*/_FROZEN_MANIFEST.json"))
    if not manifests:
        raise FileNotFoundError(f"No frozen month manifests under {raw_root}")
    found = {
        f"{path.parent.parent.name.removeprefix('year=')}-"
        f"{path.parent.name.removeprefix('month=')}"
        for path in manifests
    }
    missing = sorted(set(expected_months) - found)
    digest = hashlib.sha256()
    for path in manifests:
        digest.update(path.relative_to(raw_root).as_posix().encode("utf-8"))
        digest.update(hashlib.sha256(path.read_bytes()).digest())
    return digest.hexdigest(), len(manifests), missing


def _decode_hour(path: Path) -> dict[str, Any] | None:
    payload = json.loads(path.read_bytes())
    arrays = ("times", "bids", "asks", "bidVolumes", "askVolumes")
    sizes = {len(payload.get(name, [])) for name in arrays}
    if len(sizes) != 1:
        raise ValueError(f"Parallel array mismatch: {path}")
    count = sizes.pop()
    if count == 0:
        return None
    if payload.get("bid") is None or payload.get("ask") is None:
        raise ValueError(f"Nonempty payload has null starting quote: {path}")
    multiplier = float(payload["multiplier"])
    bids = float(payload["bid"]) + np.cumsum(
        np.asarray(payload["bids"], dtype=np.float64)
    ) * multiplier
    asks = float(payload["ask"]) + np.cumsum(
        np.asarray(payload["asks"], dtype=np.float64)
    ) * multiplier
    if np.any(asks < bids):
        raise ValueError(f"Crossed source quotes: {path}")
    timestamp = datetime.fromtimestamp(
        int(payload["timestamp"]) / 1000, tz=timezone.utc
    )
    return {
        "timestamp": timestamp.isoformat().replace("+00:00", "Z"),
        "bid_open": bids[0],
        "bid_high": bids.max(),
        "bid_low": bids.min(),
        "bid_close": bids[-1],
        "ask_open": asks[0],
        "ask_high": asks.max(),
        "ask_low": asks.min(),
        "ask_close": asks[-1],
        "ticks": count,
    }


def build_or_load_h1_cache(
    storage_root: Path, config: dict[str, Any], force: bool = False
) -> tuple[pd.DataFrame, dict[str, Any]]:
    source = config["source"]
    raw_root = storage_root / "raw" / source["symbol"]
    cache = storage_root / source["external_cache"]
    metadata_path = storage_root / source["external_cache_metadata"]
    expected_months = month_keys(
        source["start_utc"], source["end_exclusive_utc"]
    )
    digest, frozen_months, missing_frozen_months = frozen_manifest_digest(
        raw_root, expected_months
    )
    opened_months = set(
        month_keys(
            source["start_utc"],
            config["windows"]["discovery_confirm"][1],
        )
    )
    missing_opened_months = sorted(opened_months & set(missing_frozen_months))
    if missing_opened_months:
        raise RuntimeError(
            f"Opened discovery months are not frozen: {missing_opened_months}"
        )
    if cache.exists() and metadata_path.exists() and not force:
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        if metadata.get("frozen_month_manifest_digest") == digest:
            metadata["expected_months"] = len(expected_months)
            metadata["missing_frozen_months"] = missing_frozen_months
            metadata["missing_opened_discovery_months"] = missing_opened_months
            metadata_path.write_text(
                json.dumps(metadata, indent=2) + "\n",
                encoding="utf-8",
                newline="\n",
            )
            frame = pd.read_csv(cache, compression="gzip", parse_dates=["timestamp"])
            return frame, metadata

    files = sorted(
        path
        for path in raw_root.glob("year=*/month=*/*.json")
        if not path.name.startswith("_")
    )
    rows: list[dict[str, Any]] = []
    for number, path in enumerate(files, start=1):
        row = _decode_hour(path)
        if row is not None:
            rows.append(row)
        if number % 10000 == 0:
            print(f"decoded {number:,}/{len(files):,} raw hours")
    frame = pd.DataFrame(rows)
    frame["timestamp"] = pd.to_datetime(frame["timestamp"], utc=True)
    frame = frame.sort_values("timestamp").drop_duplicates("timestamp").reset_index(
        drop=True
    )
    start = pd.Timestamp(source["start_utc"])
    end = pd.Timestamp(source["end_exclusive_utc"])
    frame = frame[(frame["timestamp"] >= start) & (frame["timestamp"] < end)].copy()
    if frame.empty or not frame["timestamp"].is_monotonic_increasing:
        raise RuntimeError("H1 cache is empty or not chronological")
    cache.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(
        cache,
        index=False,
        compression={"method": "gzip", "compresslevel": 6, "mtime": 0},
        float_format="%.8f",
    )
    metadata = {
        "schema_version": "eurusd_h1_bidask_cache_v1",
        "symbol": source["symbol"],
        "frozen_month_manifest_digest": digest,
        "frozen_months": frozen_months,
        "expected_months": len(expected_months),
        "missing_frozen_months": missing_frozen_months,
        "missing_opened_discovery_months": missing_opened_months,
        "raw_hour_files": len(files),
        "nonempty_h1_rows": len(frame),
        "start_utc": frame["timestamp"].iloc[0].isoformat(),
        "end_utc": frame["timestamp"].iloc[-1].isoformat(),
        "cache_sha256": hashlib.sha256(cache.read_bytes()).hexdigest(),
        "cache_bytes": cache.stat().st_size,
    }
    metadata_path.write_text(
        json.dumps(metadata, indent=2) + "\n", encoding="utf-8", newline="\n"
    )
    return frame, metadata


def add_features(frame: pd.DataFrame, config: dict[str, Any]) -> pd.DataFrame:
    feature = config["feature_contract"]
    result = frame.copy()
    for field in ("open", "high", "low", "close"):
        result[f"mid_{field}"] = (
            result[f"bid_{field}"] + result[f"ask_{field}"]
        ) / 2.0
    close = result["mid_close"]
    previous = close.shift(1)
    true_range = pd.concat(
        [
            result["mid_high"] - result["mid_low"],
            (result["mid_high"] - previous).abs(),
            (result["mid_low"] - previous).abs(),
        ],
        axis=1,
    ).max(axis=1)
    result["atr"] = true_range.ewm(
        alpha=1.0 / feature["atr_period"], adjust=False
    ).mean()
    result["ema_fast"] = close.ewm(
        span=feature["ema_fast_period"], adjust=False
    ).mean()
    result["ema_slow"] = close.ewm(
        span=feature["ema_slow_period"], adjust=False
    ).mean()
    result["ema_slope_atr"] = (
        result["ema_fast"] - result["ema_fast"].shift(feature["ema_slope_bars"])
    ) / result["atr"]
    lookback = feature["range_lookback"]
    result["prior_high"] = result["mid_high"].shift(1).rolling(lookback).max()
    result["prior_low"] = result["mid_low"].shift(1).rolling(lookback).min()
    zlookback = feature["zscore_lookback"]
    prior_mean = close.shift(1).rolling(zlookback).mean()
    prior_std = close.shift(1).rolling(zlookback).std(ddof=0)
    result["zscore"] = (close - prior_mean) / prior_std.replace(0, np.nan)
    differences = close.diff().abs()
    efficiency = feature["efficiency_lookback"]
    result["efficiency"] = (
        (close - close.shift(efficiency)).abs()
        / differences.rolling(efficiency).sum().replace(0, np.nan)
    )
    baseline = feature["volatility_baseline_bars"]
    result["volatility_ratio"] = result["atr"] / result["atr"].shift(1).rolling(
        baseline
    ).median()
    result["body_fraction"] = (
        (result["mid_close"] - result["mid_open"]).abs()
        / (result["mid_high"] - result["mid_low"]).replace(0, np.nan)
    )
    result["contiguous_next"] = (
        result["timestamp"].shift(-1) - result["timestamp"]
    ) == pd.Timedelta(hours=1)
    return result


def signal_mask(frame: pd.DataFrame, candidate: Candidate) -> np.ndarray:
    close = frame["mid_close"]
    atr = frame["atr"]
    threshold = candidate.threshold
    archetype = candidate.archetype
    trend_long = (
        (frame["ema_fast"] > frame["ema_slow"])
        & (frame["ema_slope_atr"] > 0.05)
    )
    trend_short = (
        (frame["ema_fast"] < frame["ema_slow"])
        & (frame["ema_slope_atr"] < -0.05)
    )
    if archetype == "trend_pullback_long":
        mask = trend_long & (close <= frame["ema_fast"] - threshold * atr) & (
            close > frame["ema_slow"]
        )
    elif archetype == "trend_pullback_short":
        mask = trend_short & (close >= frame["ema_fast"] + threshold * atr) & (
            close < frame["ema_slow"]
        )
    elif archetype == "range_breakout_long":
        mask = trend_long & (
            close > frame["prior_high"] + threshold * atr
        ) & (frame["body_fraction"] >= 0.50)
    elif archetype == "range_breakout_short":
        mask = trend_short & (
            close < frame["prior_low"] - threshold * atr
        ) & (frame["body_fraction"] >= 0.50)
    elif archetype == "compression_breakout_long":
        mask = (
            (frame["volatility_ratio"].shift(1) <= threshold)
            & (close > frame["prior_high"])
            & (frame["body_fraction"] >= 0.55)
        )
    elif archetype == "compression_breakout_short":
        mask = (
            (frame["volatility_ratio"].shift(1) <= threshold)
            & (close < frame["prior_low"])
            & (frame["body_fraction"] >= 0.55)
        )
    elif archetype == "zscore_reversion_long":
        mask = (
            (frame["zscore"] <= -threshold)
            & (frame["efficiency"] <= 0.35)
            & (close > frame["mid_low"])
        )
    elif archetype == "zscore_reversion_short":
        mask = (
            (frame["zscore"] >= threshold)
            & (frame["efficiency"] <= 0.35)
            & (close < frame["mid_high"])
        )
    elif archetype == "failed_break_reversion_long":
        mask = (
            (frame["mid_low"] < frame["prior_low"] - threshold * atr)
            & (close > frame["prior_low"])
            & (frame["body_fraction"] >= 0.25)
        )
    elif archetype == "failed_break_reversion_short":
        mask = (
            (frame["mid_high"] > frame["prior_high"] + threshold * atr)
            & (close < frame["prior_high"])
            & (frame["body_fraction"] >= 0.25)
        )
    else:
        raise ValueError(f"Unknown archetype: {archetype}")
    return (mask & frame["contiguous_next"] & atr.notna()).fillna(False).to_numpy()


def simulate(
    frame: pd.DataFrame,
    candidate: Candidate,
    mask: np.ndarray,
    start: pd.Timestamp,
    end: pd.Timestamp,
    config: dict[str, Any],
) -> list[dict[str, Any]]:
    execution = config["execution"]
    slippage = execution["entry_exit_slippage_pips_each"] * PIP
    maximum_spread = execution["maximum_entry_spread_pips"]
    timestamps = frame["timestamp"].to_numpy()
    atr = frame["atr"].to_numpy(dtype=float)
    arrays = {
        name: frame[name].to_numpy(dtype=float)
        for name in (
            "bid_open",
            "bid_high",
            "bid_low",
            "bid_close",
            "ask_open",
            "ask_high",
            "ask_low",
            "ask_close",
        )
    }
    eligible = np.flatnonzero(
        mask
        & (frame["timestamp"] >= start).to_numpy()
        & (frame["timestamp"].shift(-1) < end).fillna(False).to_numpy()
    )
    trades: list[dict[str, Any]] = []
    blocked_until = -1
    for signal_index in eligible:
        entry_index = signal_index + 1
        if entry_index <= blocked_until or entry_index >= len(frame):
            continue
        if (
            pd.Timestamp(timestamps[entry_index])
            - pd.Timestamp(timestamps[signal_index])
            != pd.Timedelta(hours=1)
        ):
            continue
        spread_pips = (
            arrays["ask_open"][entry_index] - arrays["bid_open"][entry_index]
        ) / PIP
        if spread_pips > maximum_spread:
            continue
        stop_distance = candidate.stop_atr * atr[signal_index]
        if not math.isfinite(stop_distance) or stop_distance <= 0:
            continue
        long = candidate.direction == "long"
        entry = (
            arrays["ask_open"][entry_index] + slippage
            if long
            else arrays["bid_open"][entry_index] - slippage
        )
        stop = entry - stop_distance if long else entry + stop_distance
        target = (
            entry + candidate.target_r * stop_distance
            if long
            else entry - candidate.target_r * stop_distance
        )
        final_index = min(
            entry_index + candidate.max_hold_bars - 1, len(frame) - 1
        )
        reason = "time"
        exit_price = (
            arrays["bid_close"][final_index] - slippage
            if long
            else arrays["ask_close"][final_index] + slippage
        )
        exit_index = final_index
        for index in range(entry_index, final_index + 1):
            if long:
                stop_hit = arrays["bid_low"][index] <= stop
                target_hit = arrays["bid_high"][index] >= target
            else:
                stop_hit = arrays["ask_high"][index] >= stop
                target_hit = arrays["ask_low"][index] <= target
            if stop_hit:
                exit_price = stop - slippage if long else stop + slippage
                exit_index = index
                reason = "stop"
                break
            if target_hit:
                exit_price = target - slippage if long else target + slippage
                exit_index = index
                reason = "target"
                break
        net_pips = (
            (exit_price - entry) / PIP if long else (entry - exit_price) / PIP
        )
        trades.append(
            {
                "candidate_id": candidate.candidate_id,
                "archetype": candidate.archetype,
                "direction": candidate.direction,
                "signal_time": pd.Timestamp(timestamps[signal_index]).isoformat(),
                "entry_time": pd.Timestamp(timestamps[entry_index]).isoformat(),
                "exit_time": pd.Timestamp(timestamps[exit_index]).isoformat(),
                "entry": entry,
                "exit": exit_price,
                "stop": stop,
                "target": target,
                "spread_pips": spread_pips,
                "net_pips": net_pips,
                "stress_net_pips": net_pips
                - execution["primary_stress_extra_pips_roundtrip"],
                "exit_reason": reason,
            }
        )
        blocked_until = exit_index
    return trades


def profit_factor(values: Iterable[float]) -> float:
    values = list(values)
    gross_profit = sum(value for value in values if value > 0)
    gross_loss = -sum(value for value in values if value < 0)
    if gross_loss == 0:
        return math.inf if gross_profit > 0 else 0.0
    return float(gross_profit / gross_loss)


def metrics(
    trades: list[dict[str, Any]], candidate: Candidate, stage: str
) -> dict[str, Any]:
    values = np.asarray([trade["net_pips"] for trade in trades], dtype=float)
    stress = np.asarray(
        [trade["stress_net_pips"] for trade in trades], dtype=float
    )
    if len(stress):
        months: dict[str, float] = {}
        for trade in trades:
            month = trade["exit_time"][:7]
            months[month] = months.get(month, 0.0) + trade["stress_net_pips"]
        positive_month_share = sum(value > 0 for value in months.values()) / len(
            months
        )
        ordered = np.sort(stress)[::-1]
        top5_removed_pf = profit_factor(ordered[min(5, len(ordered)) :])
        equity = np.cumsum(stress)
        peaks = np.maximum.accumulate(np.insert(equity, 0, 0.0))[1:]
        max_drawdown = float(np.max(peaks - equity))
        if len(stress) > 1 and np.std(stress, ddof=1) > 0:
            z_score = float(
                np.mean(stress) / (np.std(stress, ddof=1) / math.sqrt(len(stress)))
            )
            one_sided_p = 1.0 - NormalDist().cdf(z_score)
        else:
            one_sided_p = 1.0
    else:
        positive_month_share = 0.0
        top5_removed_pf = 0.0
        max_drawdown = 0.0
        one_sided_p = 1.0
    return {
        **candidate.as_dict(),
        "stage": stage,
        "trades": len(trades),
        "wins": int(np.sum(values > 0)) if len(values) else 0,
        "net_pips": float(np.sum(values)),
        "profit_factor": profit_factor(values),
        "stress_net_pips": float(np.sum(stress)),
        "stress_profit_factor": profit_factor(stress),
        "positive_active_month_share": positive_month_share,
        "top5_removed_profit_factor": top5_removed_pf,
        "maximum_closed_drawdown_pips": max_drawdown,
        "one_sided_mean_p_value": one_sided_p,
    }


def gate(row: dict[str, Any], config: dict[str, Any]) -> bool:
    gates = config["discovery_gates"]
    return bool(
        row["trades"] >= gates["minimum_trades"]
        and row["stress_profit_factor"]
        >= gates["minimum_stress_profit_factor"]
        and row["stress_net_pips"] > gates["minimum_stress_net_pips"]
        and row["positive_active_month_share"]
        >= gates["minimum_positive_active_month_share"]
        and row["top5_removed_profit_factor"]
        >= gates["minimum_top5_removed_profit_factor"]
    )


def benjamini_hochberg(p_values: dict[str, float]) -> dict[str, float]:
    ordered = sorted(p_values.items(), key=lambda item: item[1])
    total = len(ordered)
    adjusted: dict[str, float] = {}
    running = 1.0
    for rank, (candidate_id, p_value) in reversed(list(enumerate(ordered, start=1))):
        running = min(running, p_value * total / rank)
        adjusted[candidate_id] = min(1.0, running)
    return adjusted


def screen(
    frame: pd.DataFrame, candidates: list[Candidate], config: dict[str, Any]
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    windows = config["windows"]
    rows: list[dict[str, Any]] = []
    trade_cache: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for number, candidate in enumerate(candidates, start=1):
        mask = signal_mask(frame, candidate)
        for stage in ("discovery_fit", "discovery_confirm"):
            start, end = (pd.Timestamp(value) for value in windows[stage])
            trades = simulate(frame, candidate, mask, start, end, config)
            trade_cache[(candidate.candidate_id, stage)] = trades
            row = metrics(trades, candidate, stage)
            row["stage_gate_pass"] = gate(row, config)
            rows.append(row)
        if number % 100 == 0:
            print(f"screened {number:,}/{len(candidates):,} candidates")

    by_candidate: dict[str, dict[str, dict[str, Any]]] = {}
    for row in rows:
        by_candidate.setdefault(row["candidate_id"], {})[row["stage"]] = row
    p_values = {
        candidate_id: max(
            stages["discovery_fit"]["one_sided_mean_p_value"],
            stages["discovery_confirm"]["one_sided_mean_p_value"],
        )
        for candidate_id, stages in by_candidate.items()
    }
    adjusted = benjamini_hochberg(p_values)
    eligible: list[dict[str, Any]] = []
    for candidate in candidates:
        stages = by_candidate[candidate.candidate_id]
        weakest_pf = min(
            stages["discovery_fit"]["stress_profit_factor"],
            stages["discovery_confirm"]["stress_profit_factor"],
        )
        both_gates = all(stage["stage_gate_pass"] for stage in stages.values())
        eligible.append(
            {
                **candidate.as_dict(),
                "fit_trades": stages["discovery_fit"]["trades"],
                "fit_stress_pf": stages["discovery_fit"]["stress_profit_factor"],
                "confirm_trades": stages["discovery_confirm"]["trades"],
                "confirm_stress_pf": stages["discovery_confirm"][
                    "stress_profit_factor"
                ],
                "weakest_discovery_stress_pf": weakest_pf,
                "worst_one_sided_p_value": p_values[candidate.candidate_id],
                "bh_adjusted_p_value": adjusted[candidate.candidate_id],
                "both_stage_gates_pass": both_gates,
                "fdr_gate_pass": adjusted[candidate.candidate_id]
                <= config["selection"]["false_discovery_rate"],
            }
        )
    selected: list[dict[str, Any]] = []
    for archetype, *_ in ARCHETYPES:
        family = [
            row
            for row in eligible
            if row["archetype"] == archetype
            and row["both_stage_gates_pass"]
            and row["fdr_gate_pass"]
        ]
        family.sort(
            key=lambda row: (
                row["weakest_discovery_stress_pf"],
                row["fit_trades"] + row["confirm_trades"],
            ),
            reverse=True,
        )
        selected.extend(
            family[: config["selection"]["maximum_finalists_per_archetype"]]
        )
    selected_ids = {row["candidate_id"] for row in selected}
    selected_trades = [
        {**trade, "stage": stage}
        for (candidate_id, stage), trades in trade_cache.items()
        if candidate_id in selected_ids
        for trade in trades
    ]
    return rows, selected, selected_trades


def write_csv(
    path: Path,
    rows: list[dict[str, Any]],
    fieldnames: list[str] | None = None,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = fieldnames or (list(rows[0]) if rows else [])
    with path.open("w", encoding="utf-8", newline="") as handle:
        if fields:
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader()
            writer.writerows(rows)


def manifest_sha(candidates: list[Candidate]) -> str:
    return sha256_bytes(canonical_bytes([candidate.as_dict() for candidate in candidates]))


def summarize_family_results(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    summary = []
    for archetype, *_ in ARCHETYPES:
        family = [row for row in rows if row["archetype"] == archetype]
        minimum_trade_rows = [row for row in family if row["trades"] >= 60]
        finite_minimum_trade_pfs = [
            float(row["stress_profit_factor"])
            for row in minimum_trade_rows
            if math.isfinite(float(row["stress_profit_factor"]))
        ]
        passed = {
            row["candidate_id"]
            for row in family
            if row["stage_gate_pass"]
        }
        both = [
            candidate_id
            for candidate_id in passed
            if sum(
                row["candidate_id"] == candidate_id and row["stage_gate_pass"]
                for row in family
            )
            == 2
        ]
        summary.append(
            {
                "archetype": archetype,
                "stage_gate_pass_rows": sum(row["stage_gate_pass"] for row in family),
                "both_window_gate_pass_candidates": len(both),
                "best_minimum_trade_stress_pf": (
                    max(finite_minimum_trade_pfs)
                    if finite_minimum_trade_pfs
                    else None
                ),
            }
        )
    return summary
