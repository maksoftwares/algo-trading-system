from __future__ import annotations

import bisect
import hashlib
import json
from dataclasses import asdict
from pathlib import Path
from typing import Any, Mapping, Sequence

import pandas as pd

from ml.a3_meta_v1.dukascopy_label_factory import (
    Candidate,
    VerifiedTickStore,
    _load_foundation,
    _month_range,
    _validate_candidates,
    _write_rows,
    prepare_verified_h1_bars,
    replay_candidates,
)
from ml.a3_meta_v1.dukascopy_m5_discovery import (
    _build_report,
    _render,
    _utc_ms,
    _validate_contract as _validate_discovery_contract,
    apply_profile_execution_controls,
)
from ml.a3_meta_v1.dukascopy_m5_momentum_portability import (
    M5_MS,
    _iso_ms,
    _resolve_storage_root,
    prepare_verified_m5_bars,
)


DEFAULT_CONTRACT = Path("config/ml/a3_ml_dukascopy_m5_mean_reversion_train.json")
PATTERNS = {"BAND_FADE", "IMPULSE_FADE", "SWEEP_FADE"}
REGIMES = {"ANY", "H1_RANGE"}


def run_dukascopy_m5_mean_reversion_train(
    root: Path, contract_path: Path | None = None
) -> Path:
    root = root.resolve()
    contract_file = (contract_path or root / DEFAULT_CONTRACT).resolve()
    contract = json.loads(contract_file.read_text(encoding="utf-8"))
    _validate_contract(contract)
    storage_root = _resolve_storage_root(contract)
    months = _month_range(contract["period"]["start_month"], contract["period"]["end_month"])
    foundation = _load_foundation(root.parents[1])
    h1_bars, h1_audits = prepare_verified_h1_bars(
        storage_root,
        storage_root / "research" / "xau-label-factory-v1" / "bars",
        str(contract["symbol"]),
        months,
        foundation,
    )
    m5_bars, m5_audits = prepare_verified_m5_bars(
        storage_root,
        storage_root / str(contract["m5_cache_subdirectory"]),
        str(contract["symbol"]),
        months,
        foundation,
    )
    candidates = generate_mean_reversion_candidates(m5_bars, h1_bars, contract)
    _validate_candidates(candidates)
    store = VerifiedTickStore(
        storage_root=storage_root,
        symbol=str(contract["symbol"]),
        foundation=foundation,
        prevalidated_months=set(months),
    )
    raw_labels = replay_candidates(candidates, h1_bars, store, contract)
    candidate_by_id = {row.candidate_id: row for row in candidates}
    executed_labels, execution_reasons = apply_profile_execution_controls(
        raw_labels, candidate_by_id, contract
    )
    outputs = {key: (root / value).resolve() for key, value in contract["outputs"].items()}
    _write_rows(outputs["raw_candidates_csv"], [asdict(row) for row in candidates])
    _write_rows(outputs["raw_labels_csv"], [asdict(row) for row in raw_labels])
    _write_rows(outputs["executed_labels_csv"], [asdict(row) for row in executed_labels])
    payload = _build_report(
        contract=contract,
        contract_file=contract_file,
        storage_root=storage_root,
        h1_audits=h1_audits,
        m5_audits=m5_audits,
        m5_bars=m5_bars,
        candidates=candidates,
        raw_labels=raw_labels,
        executed_labels=executed_labels,
        execution_reasons=execution_reasons,
        outputs=outputs,
    )
    outputs["report_json"].parent.mkdir(parents=True, exist_ok=True)
    outputs["report_json"].write_text(json.dumps(payload, indent=2), encoding="utf-8")
    outputs["report_markdown"].write_text(_render(payload), encoding="utf-8")
    return outputs["report_json"]


def generate_mean_reversion_candidates(
    m5_bars: Sequence[Mapping[str, Any]],
    h1_bars: Sequence[Mapping[str, Any]],
    contract: Mapping[str, Any],
) -> list[Candidate]:
    m5 = _m5_frame(m5_bars, contract)
    h1 = _h1_regime_frame(h1_bars, contract)
    if m5.empty or h1.empty:
        return []
    h1_ends = [int(value) for value in h1["end_timestamp_ms"]]
    signal = contract["signal"]
    start_ms = _utc_ms(contract["training_window"]["start_utc"])
    end_ms = _utc_ms(contract["training_window"]["end_exclusive_utc"])
    lookback = max(
        int(signal["bollinger_period"]),
        int(signal["rsi_period"]),
        int(signal["sweep_lookback_m5_bars"]),
        3,
    )
    point = float(signal["point_size"])
    profiles = sorted(contract["profiles"], key=lambda row: str(row["family_id"]))
    output: list[Candidate] = []
    for index in range(lookback, len(m5)):
        row = m5.iloc[index]
        decision_ms = int(row["timestamp_ms"]) + M5_MS
        if not start_ms <= decision_ms < end_ms or pd.isna(row["atr"]):
            continue
        h1_index = bisect.bisect_right(h1_ends, decision_ms) - 1
        if h1_index < 0:
            continue
        h1_row = h1.iloc[h1_index]
        required = ("ema_fast", "ema_slow", "ema_fast_prior", "atr")
        if any(pd.isna(h1_row[name]) for name in required):
            continue
        atr = float(row["atr"])
        bar_range = float(row["bid_high"] - row["bid_low"])
        if atr <= 0.0 or bar_range < float(signal["minimum_range_atr"]) * atr:
            continue
        opened = float(row["bid_open"])
        closed = float(row["bid_close"])
        body_fraction = abs(closed - opened) / bar_range
        if body_fraction < float(signal["minimum_body_fraction"]):
            continue
        close_location = (closed - float(row["bid_low"])) / bar_range
        stop_distance = max(
            float(signal["stop_atr_multiple"]) * atr,
            int(signal["stop_floor_points"]) * point,
        )
        if stop_distance / point > int(signal["stop_ceiling_points"]):
            continue
        for profile in profiles:
            if str(profile["regime"]) == "H1_RANGE" and not _h1_range_allows(
                h1_row, signal
            ):
                continue
            direction, distance_atr = _fade_signal(
                str(profile["pattern"]), row, signal
            )
            if direction is None:
                continue
            family_id = str(profile["family_id"])
            candidate_id = hashlib.sha256(
                f"{family_id}|{contract['symbol']}|{decision_ms}|{direction}".encode("ascii")
            ).hexdigest()[:24]
            output.append(
                Candidate(
                    candidate_id=candidate_id,
                    family_id=family_id,
                    symbol=str(contract["symbol"]),
                    split="train",
                    direction=direction,
                    signal_bar_start_utc=_iso_ms(int(row["timestamp_ms"])),
                    decision_time_utc=_iso_ms(decision_ms),
                    decision_timestamp_ms=decision_ms,
                    signal_open=opened,
                    signal_high=float(row["bid_high"]),
                    signal_low=float(row["bid_low"]),
                    signal_close=closed,
                    ema_fast=float(h1_row["ema_fast"]),
                    ema_slow=float(h1_row["ema_slow"]),
                    ema_fast_slope_atr=(
                        float(h1_row["ema_fast"]) - float(h1_row["ema_fast_prior"])
                    )
                    / float(h1_row["atr"]),
                    atr=atr,
                    body_fraction=body_fraction,
                    close_location=close_location,
                    touch_distance_atr=distance_atr,
                    stop_distance=stop_distance,
                    stop_distance_atr=stop_distance / atr,
                    reward_r=float(profile["reward_r"]),
                    signal_tick_count=int(row["tick_count"]),
                )
            )
    output.sort(key=lambda row: (row.decision_timestamp_ms, row.direction, row.family_id))
    return output


def _m5_frame(
    bars: Sequence[Mapping[str, Any]], contract: Mapping[str, Any]
) -> pd.DataFrame:
    frame = pd.DataFrame(bars).copy()
    if frame.empty:
        return frame
    for name in ("timestamp_ms", "tick_count"):
        frame[name] = pd.to_numeric(frame[name], errors="raise").astype("int64")
    for name in ("bid_open", "bid_high", "bid_low", "bid_close"):
        frame[name] = pd.to_numeric(frame[name], errors="raise").astype(float)
    frame = frame.sort_values("timestamp_ms").reset_index(drop=True)
    previous_close = frame["bid_close"].shift(1)
    true_range = pd.concat(
        [
            frame["bid_high"] - frame["bid_low"],
            (frame["bid_high"] - previous_close).abs(),
            (frame["bid_low"] - previous_close).abs(),
        ],
        axis=1,
    ).max(axis=1)
    signal = contract["signal"]
    atr_period = int(signal["atr_period"])
    frame["atr"] = true_range.ewm(
        alpha=1.0 / atr_period, adjust=False, min_periods=atr_period
    ).mean()
    band_period = int(signal["bollinger_period"])
    frame["band_mean"] = frame["bid_close"].rolling(band_period).mean()
    frame["band_std"] = frame["bid_close"].rolling(band_period).std(ddof=0)
    frame["zscore"] = (frame["bid_close"] - frame["band_mean"]) / frame["band_std"]
    delta = frame["bid_close"].diff()
    gain = delta.clip(lower=0.0)
    loss = -delta.clip(upper=0.0)
    rsi_period = int(signal["rsi_period"])
    average_gain = gain.ewm(
        alpha=1.0 / rsi_period, adjust=False, min_periods=rsi_period
    ).mean()
    average_loss = loss.ewm(
        alpha=1.0 / rsi_period, adjust=False, min_periods=rsi_period
    ).mean()
    relative_strength = average_gain / average_loss.replace(0.0, float("nan"))
    frame["rsi"] = 100.0 - 100.0 / (1.0 + relative_strength)
    frame.loc[(average_loss == 0.0) & (average_gain > 0.0), "rsi"] = 100.0
    frame.loc[(average_gain == 0.0) & (average_loss > 0.0), "rsi"] = 0.0
    sweep_lookback = int(signal["sweep_lookback_m5_bars"])
    frame["prior_high"] = frame["bid_high"].shift(1).rolling(sweep_lookback).max()
    frame["prior_low"] = frame["bid_low"].shift(1).rolling(sweep_lookback).min()
    frame["three_bar_move"] = frame["bid_close"] - frame["bid_close"].shift(3)
    return frame


def _h1_regime_frame(
    bars: Sequence[Mapping[str, Any]], contract: Mapping[str, Any]
) -> pd.DataFrame:
    frame = pd.DataFrame(bars).copy()
    if frame.empty:
        return frame
    for name in ("timestamp_ms",):
        frame[name] = pd.to_numeric(frame[name], errors="raise").astype("int64")
    for name in ("bid_high", "bid_low", "bid_close"):
        frame[name] = pd.to_numeric(frame[name], errors="raise").astype(float)
    frame = frame.sort_values("timestamp_ms").reset_index(drop=True)
    previous_close = frame["bid_close"].shift(1)
    true_range = pd.concat(
        [
            frame["bid_high"] - frame["bid_low"],
            (frame["bid_high"] - previous_close).abs(),
            (frame["bid_low"] - previous_close).abs(),
        ],
        axis=1,
    ).max(axis=1)
    signal = contract["signal"]
    atr_period = int(signal["h1_atr_period"])
    frame["atr"] = true_range.ewm(
        alpha=1.0 / atr_period, adjust=False, min_periods=atr_period
    ).mean()
    fast = int(signal["h1_ema_fast_period"])
    slow = int(signal["h1_ema_slow_period"])
    frame["ema_fast"] = frame["bid_close"].ewm(
        span=fast, adjust=False, min_periods=fast
    ).mean()
    frame["ema_slow"] = frame["bid_close"].ewm(
        span=slow, adjust=False, min_periods=slow
    ).mean()
    frame["ema_fast_prior"] = frame["ema_fast"].shift(int(signal["h1_slope_bars"]))
    frame["end_timestamp_ms"] = frame["timestamp_ms"] + 3_600_000
    return frame


def _h1_range_allows(row: Mapping[str, Any], signal: Mapping[str, Any]) -> bool:
    atr = float(row["atr"])
    if atr <= 0.0:
        return False
    separation = abs(float(row["ema_fast"]) - float(row["ema_slow"])) / atr
    slope = abs(float(row["ema_fast"]) - float(row["ema_fast_prior"])) / atr
    return separation <= float(
        signal["h1_range_maximum_ema_separation_atr"]
    ) and slope <= float(signal["h1_range_maximum_fast_slope_atr"])


def _fade_signal(
    pattern: str, row: Mapping[str, Any], signal: Mapping[str, Any]
) -> tuple[str | None, float]:
    required = ("atr", "zscore", "rsi", "prior_high", "prior_low")
    if any(pd.isna(row[name]) for name in required):
        return None, 0.0
    atr = float(row["atr"])
    opened = float(row["bid_open"])
    high = float(row["bid_high"])
    low = float(row["bid_low"])
    closed = float(row["bid_close"])
    bar_range = high - low
    location = (closed - low) / bar_range if bar_range > 0.0 else 0.5
    if pattern == "BAND_FADE":
        zscore = float(row["zscore"])
        rsi = float(row["rsi"])
        threshold = float(signal["bollinger_z_threshold"])
        if zscore >= threshold and rsi >= float(signal["rsi_upper"]):
            return "SHORT", abs(zscore)
        if zscore <= -threshold and rsi <= float(signal["rsi_lower"]):
            return "LONG", abs(zscore)
        return None, 0.0
    if pattern == "IMPULSE_FADE":
        move_atr = float(row["three_bar_move"]) / atr
        threshold = float(signal["impulse_three_bar_atr"])
        extreme = float(signal["impulse_close_location"])
        if move_atr >= threshold and location >= extreme:
            return "SHORT", abs(move_atr)
        if move_atr <= -threshold and location <= 1.0 - extreme:
            return "LONG", abs(move_atr)
        return None, 0.0
    if pattern == "SWEEP_FADE":
        prior_high = float(row["prior_high"])
        prior_low = float(row["prior_low"])
        sweep = float(signal["sweep_atr_multiple"]) * atr
        reclaim = float(signal["reclaim_atr_multiple"]) * atr
        if (
            high >= prior_high + sweep
            and closed <= prior_high - reclaim
            and closed < opened
            and location <= 0.45
        ):
            return "SHORT", (high - prior_high) / atr
        if (
            low <= prior_low - sweep
            and closed >= prior_low + reclaim
            and closed > opened
            and location >= 0.55
        ):
            return "LONG", (prior_low - low) / atr
        return None, 0.0
    raise ValueError(f"unsupported mean-reversion pattern: {pattern}")


def _validate_contract(contract: Mapping[str, Any]) -> None:
    if contract.get("schema_version") != "a3_ml_dukascopy_m5_mean_reversion_train_v1":
        raise ValueError("unexpected M5 mean-reversion contract version")
    proxy = json.loads(json.dumps(contract))
    proxy["schema_version"] = "a3_ml_dukascopy_m5_discovery_train_v1"
    proxy["profiles"] = [
        {
            "family_id": row["family_id"],
            "pattern": {
                "BAND_FADE": "TREND_PULLBACK",
                "IMPULSE_FADE": "CONTINUATION_BREAKOUT",
                "SWEEP_FADE": "TREND_SWEEP_RECLAIM",
            }[str(row["pattern"])],
            "trend_scope": {"ANY": "H1", "H1_RANGE": "H1_H4"}[str(row["regime"])],
            "reward_r": row["reward_r"],
        }
        for row in contract.get("profiles", [])
    ]
    _validate_discovery_contract(proxy)
    profiles = list(contract.get("profiles", []))
    combinations = {
        (str(row["pattern"]), str(row["regime"]), float(row["reward_r"]))
        for row in profiles
    }
    expected = {
        (pattern, regime, reward)
        for pattern in PATTERNS
        for regime in REGIMES
        for reward in (1.0, 1.5)
    }
    if combinations != expected:
        raise ValueError("mean-reversion profile matrix is incomplete")
    if contract.get("classification_prefix") != "DUKASCOPY_M5_MEAN_REVERSION_TRAIN":
        raise ValueError("mean-reversion classification prefix changed")
