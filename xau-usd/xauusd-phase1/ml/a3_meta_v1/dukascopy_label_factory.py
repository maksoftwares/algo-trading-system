from __future__ import annotations

import csv
import hashlib
import importlib
import json
import os
import sys
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from functools import lru_cache
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

import pandas as pd


HOUR_MS = 3_600_000
DAY_MS = 24 * HOUR_MS
BAR_CACHE_SCHEMA = "a3_ml_dukascopy_h1_bidask_cache_v1"
DEFAULT_CONTRACT = Path("config/ml/a3_ml_dukascopy_label_factory.json")


class LabelFactoryError(RuntimeError):
    pass


class TickDataUnavailable(LabelFactoryError):
    pass


@dataclass(frozen=True)
class Candidate:
    candidate_id: str
    family_id: str
    symbol: str
    split: str
    direction: str
    signal_bar_start_utc: str
    decision_time_utc: str
    decision_timestamp_ms: int
    signal_open: float
    signal_high: float
    signal_low: float
    signal_close: float
    ema_fast: float
    ema_slow: float
    ema_fast_slope_atr: float
    atr: float
    body_fraction: float
    close_location: float
    touch_distance_atr: float
    stop_distance: float
    stop_distance_atr: float
    reward_r: float
    signal_tick_count: int


@dataclass(frozen=True)
class Label:
    candidate_id: str
    family_id: str
    symbol: str
    split: str
    direction: str
    decision_time_utc: str
    status: str
    entry_time_utc: str
    exit_time_utc: str
    entry_price: float | None
    exit_price: float | None
    entry_bid: float | None
    entry_ask: float | None
    entry_spread: float | None
    planned_stop: float | None
    planned_target: float | None
    stop_distance: float
    reward_r: float
    exit_reason: str
    duration_hours: float | None
    gross_pnl_usd: float | None
    execution_stress_usd: float | None
    holding_stress_usd: float | None
    stress_net_pnl_usd: float | None
    gross_r: float | None
    stress_net_r: float | None
    mfe_r: float | None
    mae_r: float | None
    label_profitable_after_stress: int | None
    signal_open: float
    signal_high: float
    signal_low: float
    signal_close: float
    ema_fast: float
    ema_slow: float
    ema_fast_slope_atr: float
    atr: float
    body_fraction: float
    close_location: float
    touch_distance_atr: float
    stop_distance_atr: float
    signal_tick_count: int


def run_dukascopy_label_factory(root: Path, contract_path: Path | None = None) -> Path:
    root = root.resolve()
    contract_file = (contract_path or (root / DEFAULT_CONTRACT)).resolve()
    contract = json.loads(contract_file.read_text(encoding="utf-8"))
    _validate_contract(contract)

    storage_root = _resolve_storage_root(contract)
    external_root = storage_root / str(contract["external_output_subdirectory"])
    external_root.mkdir(parents=True, exist_ok=True)
    foundation = _load_foundation(root.parents[1])

    months = _month_range(contract["period"]["start_month"], contract["period"]["end_month"])
    bars, source_audits = prepare_verified_h1_bars(
        storage_root,
        external_root / "bars",
        str(contract["symbol"]),
        months,
        foundation,
    )
    candidates = generate_h1_pullback_candidates(bars, contract)
    _validate_candidates(candidates)

    prevalidated = {(year, month) for year, month in months}
    store = VerifiedTickStore(
        storage_root=storage_root,
        symbol=str(contract["symbol"]),
        foundation=foundation,
        prevalidated_months=prevalidated,
    )
    labels = replay_candidates(candidates, bars, store, contract)

    outputs = {key: (root / value).resolve() for key, value in contract["outputs"].items()}
    _write_rows(outputs["candidates_csv"], [asdict(row) for row in candidates])
    _write_rows(outputs["labels_csv"], [asdict(row) for row in labels])

    payload = _build_report(
        root=root,
        contract=contract,
        contract_file=contract_file,
        storage_root=storage_root,
        source_audits=source_audits,
        candidates=candidates,
        labels=labels,
        outputs=outputs,
    )
    outputs["report_json"].parent.mkdir(parents=True, exist_ok=True)
    outputs["report_json"].write_text(json.dumps(payload, indent=2), encoding="utf-8")
    outputs["report_markdown"].write_text(_render_report(payload), encoding="utf-8")
    return outputs["report_json"]


def prepare_verified_h1_bars(
    storage_root: Path,
    cache_root: Path,
    symbol: str,
    months: Sequence[tuple[int, int]],
    foundation: Any,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    all_bars: list[dict[str, Any]] = []
    audits: list[dict[str, Any]] = []
    for year, month in months:
        foundation.validate_month_acquisition_manifest(storage_root, symbol, year, month)
        source = _month_source_identity(storage_root, symbol, year, month)
        partition = cache_root / symbol / f"year={year:04d}" / f"month={month:02d}"
        bars_path = partition / "h1_bidask.csv"
        metadata_path = partition / "metadata.json"
        cached = _load_valid_bar_cache(
            bars_path,
            metadata_path,
            source,
            symbol=symbol,
            month=f"{year:04d}-{month:02d}",
        )
        if cached is None:
            bars = _derive_month_h1_bars(storage_root, symbol, year, month, foundation)
            partition.mkdir(parents=True, exist_ok=True)
            _write_rows(bars_path, bars)
            metadata = {
                "schema_version": BAR_CACHE_SCHEMA,
                "symbol": symbol,
                "month": f"{year:04d}-{month:02d}",
                **source,
                "bar_count": len(bars),
                "tick_count": sum(int(row["tick_count"]) for row in bars),
                "bars_sha256": _sha256_file(bars_path),
            }
            metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
            cache_reused = False
        else:
            bars, metadata = cached
            cache_reused = True
        all_bars.extend(bars)
        audits.append(
            {
                "month": f"{year:04d}-{month:02d}",
                "manifest_sha256": source["manifest_sha256"],
                "source_files_composite_sha256": source["source_files_composite_sha256"],
                "raw_hour_files": source["raw_hour_files"],
                "bar_count": len(bars),
                "tick_count": sum(int(row["tick_count"]) for row in bars),
                "bar_cache_sha256": metadata["bars_sha256"],
                "bar_cache_reused": cache_reused,
            }
        )
    all_bars.sort(key=lambda row: int(row["timestamp_ms"]))
    timestamps = [int(row["timestamp_ms"]) for row in all_bars]
    if len(timestamps) != len(set(timestamps)):
        raise LabelFactoryError("duplicate H1 timestamps across monthly caches")
    if timestamps != sorted(timestamps):
        raise LabelFactoryError("H1 cache is not chronological")
    return all_bars, audits


def generate_h1_pullback_candidates(
    bars: Sequence[Mapping[str, Any]], contract: Mapping[str, Any]
) -> list[Candidate]:
    family = contract["candidate_family"]
    frame = pd.DataFrame(bars).copy()
    if frame.empty:
        return []
    for column in ("timestamp_ms", "tick_count"):
        frame[column] = pd.to_numeric(frame[column], errors="raise").astype("int64")
    for column in ("bid_open", "bid_high", "bid_low", "bid_close"):
        frame[column] = pd.to_numeric(frame[column], errors="raise").astype(float)
    frame = frame.sort_values("timestamp_ms").reset_index(drop=True)

    fast_period = int(family["fast_ema_period"])
    slow_period = int(family["slow_ema_period"])
    atr_period = int(family["atr_period"])
    lag = int(family["slope_lag_bars"])
    close = frame["bid_close"]
    previous_close = close.shift(1)
    true_range = pd.concat(
        [
            frame["bid_high"] - frame["bid_low"],
            (frame["bid_high"] - previous_close).abs(),
            (frame["bid_low"] - previous_close).abs(),
        ],
        axis=1,
    ).max(axis=1)
    frame["ema_fast"] = close.ewm(span=fast_period, adjust=False, min_periods=fast_period).mean()
    frame["ema_slow"] = close.ewm(span=slow_period, adjust=False, min_periods=slow_period).mean()
    frame["atr"] = true_range.ewm(alpha=1.0 / atr_period, adjust=False, min_periods=atr_period).mean()
    frame["ema_fast_prior"] = frame["ema_fast"].shift(lag)

    lookback = int(family["touch_lookback_bars"])
    output: list[Candidate] = []
    split_config = contract["splits"]
    for index in range(max(slow_period + lag, lookback - 1), len(frame)):
        row = frame.iloc[index]
        if any(pd.isna(row[key]) for key in ("ema_fast", "ema_slow", "ema_fast_prior", "atr")):
            continue
        bar_range = float(row["bid_high"] - row["bid_low"])
        atr = float(row["atr"])
        if bar_range <= 0.0 or atr <= 0.0:
            continue
        body_fraction = abs(float(row["bid_close"] - row["bid_open"])) / bar_range
        close_location = float(row["bid_close"] - row["bid_low"]) / bar_range
        window = frame.iloc[index - lookback + 1 : index + 1]
        touch_zone = float(family["touch_zone_atr"]) * atr
        distances = []
        touched = False
        for _, touch_bar in window.iterrows():
            for ema in (float(row["ema_fast"]), float(row["ema_slow"])):
                if float(touch_bar["bid_high"]) >= ema - touch_zone and float(touch_bar["bid_low"]) <= ema + touch_zone:
                    touched = True
                if float(touch_bar["bid_low"]) > ema:
                    distances.append(float(touch_bar["bid_low"]) - ema)
                elif float(touch_bar["bid_high"]) < ema:
                    distances.append(ema - float(touch_bar["bid_high"]))
                else:
                    distances.append(0.0)
        if not touched:
            continue

        fast = float(row["ema_fast"])
        slow = float(row["ema_slow"])
        fast_prior = float(row["ema_fast_prior"])
        signal_open = float(row["bid_open"])
        signal_close = float(row["bid_close"])
        direction = ""
        if (
            signal_close > fast > slow
            and fast >= fast_prior
            and signal_close > signal_open
            and body_fraction >= float(family["minimum_body_fraction"])
            and close_location >= float(family["long_close_location_minimum"])
        ):
            direction = "LONG"
            projected_stop = float(window["bid_low"].min()) - float(family["stop_buffer_atr"]) * atr
            stop_distance = signal_close - projected_stop
        elif (
            signal_close < fast < slow
            and fast <= fast_prior
            and signal_close < signal_open
            and body_fraction >= float(family["minimum_body_fraction"])
            and close_location <= float(family["short_close_location_maximum"])
        ):
            direction = "SHORT"
            projected_stop = float(window["bid_high"].max()) + float(family["stop_buffer_atr"]) * atr
            stop_distance = projected_stop - signal_close
        else:
            continue
        if not float(family["minimum_stop_price"]) <= stop_distance <= float(family["maximum_stop_price"]):
            continue

        decision_ms = int(row["timestamp_ms"]) + HOUR_MS
        decision = datetime.fromtimestamp(decision_ms / 1000, UTC)
        split = _split_for_timestamp(decision, split_config)
        if split is None:
            continue
        family_id = str(family["family_id"])
        candidate_id = hashlib.sha256(
            f"{family_id}|{contract['symbol']}|{decision_ms}|{direction}".encode("ascii")
        ).hexdigest()[:24]
        output.append(
            Candidate(
                candidate_id=candidate_id,
                family_id=family_id,
                symbol=str(contract["symbol"]),
                split=split,
                direction=direction,
                signal_bar_start_utc=_iso_ms(int(row["timestamp_ms"])),
                decision_time_utc=_iso_ms(decision_ms),
                decision_timestamp_ms=decision_ms,
                signal_open=signal_open,
                signal_high=float(row["bid_high"]),
                signal_low=float(row["bid_low"]),
                signal_close=signal_close,
                ema_fast=fast,
                ema_slow=slow,
                ema_fast_slope_atr=(fast - fast_prior) / atr,
                atr=atr,
                body_fraction=body_fraction,
                close_location=close_location,
                touch_distance_atr=min(distances) / atr,
                stop_distance=stop_distance,
                stop_distance_atr=stop_distance / atr,
                reward_r=float(family["reward_r"]),
                signal_tick_count=int(row["tick_count"]),
            )
        )
    return output


class VerifiedTickStore:
    def __init__(
        self,
        *,
        storage_root: Path,
        symbol: str,
        foundation: Any,
        prevalidated_months: set[tuple[int, int]] | None = None,
    ) -> None:
        self.storage_root = storage_root.resolve()
        self.symbol = symbol
        self.foundation = foundation
        self.validated_months = set(prevalidated_months or set())

    def _ensure_month(self, year: int, month: int) -> None:
        key = (year, month)
        if key not in self.validated_months:
            try:
                self.foundation.validate_month_acquisition_manifest(
                    self.storage_root, self.symbol, year, month
                )
            except Exception as exc:
                raise TickDataUnavailable(f"unavailable or invalid Dukascopy month {year:04d}-{month:02d}") from exc
            self.validated_months.add(key)

    @lru_cache(maxsize=512)
    def load_hour(self, hour_timestamp_ms: int) -> tuple[Any, ...]:
        hour_timestamp_ms -= hour_timestamp_ms % HOUR_MS
        hour = datetime.fromtimestamp(hour_timestamp_ms / 1000, UTC)
        self._ensure_month(hour.year, hour.month)
        path = self.foundation.raw_hour_path(self.storage_root, self.symbol, hour)
        if not path.is_file():
            raise TickDataUnavailable(f"missing Dukascopy raw hour: {path}")
        try:
            ticks = tuple(self.foundation.decode_payload(path.read_bytes(), self.symbol, path.name))
        except Exception as exc:
            raise TickDataUnavailable(f"invalid Dukascopy raw hour: {path}") from exc
        if any(not hour_timestamp_ms <= int(tick.timestamp_ms) < hour_timestamp_ms + HOUR_MS for tick in ticks):
            raise TickDataUnavailable(f"Dukascopy tick outside raw-hour boundary: {path}")
        return ticks

    def first_tick_at_or_after(self, timestamp_ms: int, maximum_delay_ms: int) -> Any | None:
        end_ms = timestamp_ms + maximum_delay_ms
        hour_ms = timestamp_ms - timestamp_ms % HOUR_MS
        while hour_ms <= end_ms:
            for tick in self.load_hour(hour_ms):
                if timestamp_ms <= int(tick.timestamp_ms) <= end_ms:
                    return tick
            hour_ms += HOUR_MS
        return None


def replay_candidates(
    candidates: Sequence[Candidate],
    bars: Sequence[Mapping[str, Any]],
    tick_store: VerifiedTickStore,
    contract: Mapping[str, Any],
) -> list[Label]:
    execution = contract["execution"]
    bars_by_hour = {int(row["timestamp_ms"]): row for row in bars}
    labels = []
    for candidate in candidates:
        try:
            labels.append(_replay_one(candidate, bars_by_hour, tick_store, execution))
        except TickDataUnavailable:
            labels.append(_unresolved_label(candidate, "DATA_UNAVAILABLE"))
    return labels


def _replay_one(
    candidate: Candidate,
    bars_by_hour: Mapping[int, Mapping[str, Any]],
    tick_store: VerifiedTickStore,
    execution: Mapping[str, Any],
) -> Label:
    maximum_entry_delay_ms = int(execution["maximum_entry_delay_minutes"]) * 60_000
    entry_tick = tick_store.first_tick_at_or_after(
        candidate.decision_timestamp_ms, maximum_entry_delay_ms
    )
    if entry_tick is None:
        return _empty_label(candidate, "INELIGIBLE", "NO_QUOTE_WITHIN_ENTRY_WINDOW")
    entry_ms = int(entry_tick.timestamp_ms)
    entry_bid = float(entry_tick.bid)
    entry_ask = float(entry_tick.ask)
    entry_price = entry_ask if candidate.direction == "LONG" else entry_bid
    if candidate.direction == "LONG":
        planned_stop = entry_price - candidate.stop_distance
        planned_target = entry_price + candidate.reward_r * candidate.stop_distance
    else:
        planned_stop = entry_price + candidate.stop_distance
        planned_target = entry_price - candidate.reward_r * candidate.stop_distance

    deadline_ms = entry_ms + int(execution["maximum_hold_hours"]) * HOUR_MS
    grace_end_ms = deadline_ms + int(execution["maximum_timeout_exit_grace_hours"]) * HOUR_MS
    hour_ms = entry_ms - entry_ms % HOUR_MS
    maximum_favorable = 0.0
    maximum_adverse = 0.0
    exit_tick = None
    exit_price = None
    exit_reason = ""

    while hour_ms <= grace_end_ms:
        bar = bars_by_hour.get(hour_ms)
        side_prefix = "bid" if candidate.direction == "LONG" else "ask"
        low = float(bar[f"{side_prefix}_low"]) if bar is not None else None
        high = float(bar[f"{side_prefix}_high"]) if bar is not None else None
        boundary_possible = bool(
            bar is not None
            and (
                (candidate.direction == "LONG" and (low <= planned_stop or high >= planned_target))
                or (candidate.direction == "SHORT" and (high >= planned_stop or low <= planned_target))
            )
        )
        force_ticks = (
            hour_ms == entry_ms - entry_ms % HOUR_MS
            or boundary_possible
            or hour_ms <= deadline_ms < hour_ms + HOUR_MS
            or hour_ms > deadline_ms
        )
        if not force_ticks and bar is not None:
            if candidate.direction == "LONG":
                maximum_favorable = max(maximum_favorable, high - entry_price)
                maximum_adverse = max(maximum_adverse, entry_price - low)
            else:
                maximum_favorable = max(maximum_favorable, entry_price - low)
                maximum_adverse = max(maximum_adverse, high - entry_price)
            hour_ms += HOUR_MS
            continue

        for tick in tick_store.load_hour(hour_ms):
            tick_ms = int(tick.timestamp_ms)
            if tick_ms < entry_ms:
                continue
            side_price = float(tick.bid) if candidate.direction == "LONG" else float(tick.ask)
            if candidate.direction == "LONG":
                maximum_favorable = max(maximum_favorable, side_price - entry_price)
                maximum_adverse = max(maximum_adverse, entry_price - side_price)
            else:
                maximum_favorable = max(maximum_favorable, entry_price - side_price)
                maximum_adverse = max(maximum_adverse, side_price - entry_price)

            if tick_ms <= deadline_ms:
                if candidate.direction == "LONG" and side_price <= planned_stop:
                    exit_tick, exit_price, exit_reason = tick, side_price, "STOP"
                    break
                if candidate.direction == "LONG" and side_price >= planned_target:
                    exit_tick, exit_price, exit_reason = tick, side_price, "TARGET"
                    break
                if candidate.direction == "SHORT" and side_price >= planned_stop:
                    exit_tick, exit_price, exit_reason = tick, side_price, "STOP"
                    break
                if candidate.direction == "SHORT" and side_price <= planned_target:
                    exit_tick, exit_price, exit_reason = tick, side_price, "TARGET"
                    break
            if tick_ms >= deadline_ms:
                exit_tick, exit_price, exit_reason = tick, side_price, "TIMEOUT"
                break
        if exit_tick is not None:
            break
        hour_ms += HOUR_MS

    if exit_tick is None or exit_price is None:
        return _unresolved_label(candidate, "EXIT_UNAVAILABLE")

    exit_ms = int(exit_tick.timestamp_ms)
    duration_hours = (exit_ms - entry_ms) / HOUR_MS
    price_move = (
        exit_price - entry_price
        if candidate.direction == "LONG"
        else entry_price - exit_price
    )
    quantity_ounces = float(execution["lot_size"]) * float(
        execution["contract_size_ounces_per_lot"]
    )
    gross_pnl = price_move * quantity_ounces
    execution_stress = float(execution["extra_execution_cost_usd"])
    holding_stress = duration_hours / 24.0 * float(execution["holding_cost_per_24h_usd"])
    stress_net = gross_pnl - execution_stress - holding_stress
    risk_usd = candidate.stop_distance * quantity_ounces
    return Label(
        candidate_id=candidate.candidate_id,
        family_id=candidate.family_id,
        symbol=candidate.symbol,
        split=candidate.split,
        direction=candidate.direction,
        decision_time_utc=candidate.decision_time_utc,
        status="RESOLVED",
        entry_time_utc=_iso_ms(entry_ms),
        exit_time_utc=_iso_ms(exit_ms),
        entry_price=entry_price,
        exit_price=exit_price,
        entry_bid=entry_bid,
        entry_ask=entry_ask,
        entry_spread=entry_ask - entry_bid,
        planned_stop=planned_stop,
        planned_target=planned_target,
        stop_distance=candidate.stop_distance,
        reward_r=candidate.reward_r,
        exit_reason=exit_reason,
        duration_hours=duration_hours,
        gross_pnl_usd=gross_pnl,
        execution_stress_usd=execution_stress,
        holding_stress_usd=holding_stress,
        stress_net_pnl_usd=stress_net,
        gross_r=gross_pnl / risk_usd,
        stress_net_r=stress_net / risk_usd,
        mfe_r=maximum_favorable / candidate.stop_distance,
        mae_r=maximum_adverse / candidate.stop_distance,
        label_profitable_after_stress=int(stress_net > 0.0),
        signal_open=candidate.signal_open,
        signal_high=candidate.signal_high,
        signal_low=candidate.signal_low,
        signal_close=candidate.signal_close,
        ema_fast=candidate.ema_fast,
        ema_slow=candidate.ema_slow,
        ema_fast_slope_atr=candidate.ema_fast_slope_atr,
        atr=candidate.atr,
        body_fraction=candidate.body_fraction,
        close_location=candidate.close_location,
        touch_distance_atr=candidate.touch_distance_atr,
        stop_distance_atr=candidate.stop_distance_atr,
        signal_tick_count=candidate.signal_tick_count,
    )


def _unresolved_label(candidate: Candidate, reason: str) -> Label:
    return _empty_label(candidate, "UNRESOLVED", reason)


def _empty_label(candidate: Candidate, status: str, reason: str) -> Label:
    if status not in {"INELIGIBLE", "UNRESOLVED"}:
        raise ValueError(f"invalid empty-label status: {status}")
    values = asdict(candidate)
    return Label(
        candidate_id=candidate.candidate_id,
        family_id=candidate.family_id,
        symbol=candidate.symbol,
        split=candidate.split,
        direction=candidate.direction,
        decision_time_utc=candidate.decision_time_utc,
        status=status,
        entry_time_utc="",
        exit_time_utc="",
        entry_price=None,
        exit_price=None,
        entry_bid=None,
        entry_ask=None,
        entry_spread=None,
        planned_stop=None,
        planned_target=None,
        stop_distance=candidate.stop_distance,
        reward_r=candidate.reward_r,
        exit_reason=reason,
        duration_hours=None,
        gross_pnl_usd=None,
        execution_stress_usd=None,
        holding_stress_usd=None,
        stress_net_pnl_usd=None,
        gross_r=None,
        stress_net_r=None,
        mfe_r=None,
        mae_r=None,
        label_profitable_after_stress=None,
        signal_open=values["signal_open"],
        signal_high=values["signal_high"],
        signal_low=values["signal_low"],
        signal_close=values["signal_close"],
        ema_fast=values["ema_fast"],
        ema_slow=values["ema_slow"],
        ema_fast_slope_atr=values["ema_fast_slope_atr"],
        atr=values["atr"],
        body_fraction=values["body_fraction"],
        close_location=values["close_location"],
        touch_distance_atr=values["touch_distance_atr"],
        stop_distance_atr=values["stop_distance_atr"],
        signal_tick_count=values["signal_tick_count"],
    )


def _build_report(
    *,
    root: Path,
    contract: Mapping[str, Any],
    contract_file: Path,
    storage_root: Path,
    source_audits: Sequence[Mapping[str, Any]],
    candidates: Sequence[Candidate],
    labels: Sequence[Label],
    outputs: Mapping[str, Path],
) -> dict[str, Any]:
    resolved = [row for row in labels if row.status == "RESOLVED"]
    eligible = [row for row in labels if row.status != "INELIGIBLE"]
    by_split = {split: _label_stats([row for row in resolved if row.split == split]) for split in ("train", "validation", "test")}
    by_direction = {direction: _label_stats([row for row in resolved if row.direction == direction]) for direction in ("LONG", "SHORT")}
    all_stats = _label_stats(resolved)
    quality = contract["quality_gates"]
    label_counts = Counter(int(row.label_profitable_after_stress or 0) for row in resolved)
    minority_share = min(label_counts.values()) / len(resolved) if len(label_counts) == 2 and resolved else 0.0
    quality_gates = {
        "verified_months_eq_expected": len(source_audits) == int(quality["expected_months"]),
        "total_candidates_ge_minimum": len(candidates) >= int(quality["minimum_total_candidates"]),
        "resolved_share_ge_minimum": len(resolved) / len(eligible) >= float(quality["minimum_resolved_share"]) if eligible else False,
        "each_split_rows_ge_minimum": all(by_split[name]["trades"] >= int(quality["minimum_rows_per_split"]) for name in by_split),
        "each_direction_rows_ge_minimum": all(by_direction[name]["trades"] >= int(quality["minimum_rows_per_direction"]) for name in by_direction),
        "minority_label_share_ge_minimum": minority_share >= float(quality["minimum_minority_label_share"]),
        "candidate_ids_unique": len({row.candidate_id for row in candidates}) == len(candidates),
        "candidate_keys_unique": len({(row.family_id, row.decision_timestamp_ms, row.direction) for row in candidates}) == len(candidates),
        "all_resolved_entries_at_or_after_decision": all(row.entry_time_utc >= row.decision_time_utc for row in resolved),
    }
    strategy = contract["strategy_research_gates"]
    strategy_gates = {
        "train_stress_pf_ge_minimum": (by_split["train"]["stress_profit_factor"] or 0.0) >= float(strategy["minimum_train_stress_profit_factor"]),
        "validation_stress_pf_ge_minimum": (by_split["validation"]["stress_profit_factor"] or 0.0) >= float(strategy["minimum_validation_stress_profit_factor"]),
        "test_stress_pf_ge_minimum": (by_split["test"]["stress_profit_factor"] or 0.0) >= float(strategy["minimum_test_stress_profit_factor"]),
        "validation_average_stress_r_ge_minimum": by_split["validation"]["average_stress_r"] >= float(strategy["minimum_validation_average_stress_r"]),
        "test_average_stress_r_ge_minimum": by_split["test"]["average_stress_r"] >= float(strategy["minimum_test_average_stress_r"]),
        "test_closed_drawdown_r_lte_maximum": by_split["test"]["max_closed_drawdown_r"] <= float(strategy["maximum_test_closed_drawdown_r"]),
    }
    quality_pass = all(quality_gates.values())
    strategy_pass = quality_pass and all(strategy_gates.values())
    if not quality_pass:
        classification = "DUKASCOPY_LABEL_FACTORY_NOT_READY"
    elif strategy_pass:
        classification = "DUKASCOPY_CANDIDATE_FAMILY_RESEARCH_SURVIVOR"
    else:
        classification = "DUKASCOPY_LABEL_DATASET_READY_FAMILY_NO_SURVIVOR"

    source_composite = _sha256_json(
        [(row["month"], row["source_files_composite_sha256"]) for row in source_audits]
    )
    return {
        "schema_version": str(contract["schema_version"]),
        "classification": classification,
        "created_at_utc": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "contract": str(contract_file),
        "contract_sha256": _sha256_file(contract_file),
        "storage_root": str(storage_root),
        "source_months": len(source_audits),
        "source_composite_sha256": source_composite,
        "source_audits": list(source_audits),
        "candidate_count": len(candidates),
        "eligible_candidate_count": len(eligible),
        "ineligible_candidate_count": len(candidates) - len(eligible),
        "resolved_count": len(resolved),
        "resolved_share": len(resolved) / len(eligible) if eligible else 0.0,
        "ineligible_reasons": dict(Counter(row.exit_reason for row in labels if row.status == "INELIGIBLE")),
        "unresolved_reasons": dict(Counter(row.exit_reason for row in labels if row.status == "UNRESOLVED")),
        "minority_label_share": minority_share,
        "all": all_stats,
        "by_split": by_split,
        "by_direction": by_direction,
        "quality_gates": quality_gates,
        "strategy_research_gates": strategy_gates,
        "artifacts": {
            key: {"path": str(path), "sha256": _sha256_file(path)}
            for key, path in outputs.items()
            if key in {"candidates_csv", "labels_csv"}
        },
        "authorization": {
            **contract["authorization"],
            "model_training_authorized": bool(quality_pass),
            "candidate_family_promotion_authorized": False,
        },
        "limitations": [
            "Candidates are independently labelled counterfactuals; overlapping rows are not a shared-account equity curve.",
            "Dukascopy is the historical price source, but future broker-feed and execution differences still require demo calibration.",
            "The holding-cost stress is a fixed research proxy, not a broker swap guarantee.",
            "A research-survivor classification would still require portfolio, cost, Monte Carlo, shadow, and demo gates.",
        ],
    }


def _label_stats(rows: Sequence[Label]) -> dict[str, Any]:
    if not rows:
        return {
            "trades": 0,
            "wins": 0,
            "win_rate_pct": 0.0,
            "stress_net_usd": 0.0,
            "stress_profit_factor": None,
            "average_stress_r": 0.0,
            "max_closed_drawdown_usd": 0.0,
            "max_closed_drawdown_r": 0.0,
            "average_duration_hours": 0.0,
            "exit_reasons": {},
        }
    pnl = [float(row.stress_net_pnl_usd or 0.0) for row in rows]
    risk_returns = [float(row.stress_net_r or 0.0) for row in rows]
    gross_profit = sum(value for value in pnl if value > 0.0)
    gross_loss = -sum(value for value in pnl if value < 0.0)
    wins = sum(1 for value in pnl if value > 0.0)
    return {
        "trades": len(rows),
        "wins": wins,
        "win_rate_pct": 100.0 * wins / len(rows),
        "stress_net_usd": sum(pnl),
        "stress_profit_factor": gross_profit / gross_loss if gross_loss > 0.0 else None,
        "average_stress_r": sum(risk_returns) / len(risk_returns),
        "max_closed_drawdown_usd": _max_drawdown(pnl),
        "max_closed_drawdown_r": _max_drawdown(risk_returns),
        "average_duration_hours": sum(float(row.duration_hours or 0.0) for row in rows) / len(rows),
        "exit_reasons": dict(Counter(row.exit_reason for row in rows)),
    }


def _max_drawdown(values: Iterable[float]) -> float:
    equity = 0.0
    peak = 0.0
    maximum = 0.0
    for value in values:
        equity += value
        peak = max(peak, equity)
        maximum = max(maximum, peak - equity)
    return maximum


def _render_report(payload: Mapping[str, Any]) -> str:
    lines = [
        "# A3 ML Dukascopy Candidate-Label Factory V1",
        "",
        f"Classification: `{payload['classification']}`",
        "",
        "This is historical research based on verified Dukascopy bid/ask data. It does not authorize demo or live trading.",
        "",
        "## Dataset",
        "",
        f"- Verified months: `{payload['source_months']}`",
        f"- Candidates: `{payload['candidate_count']}`",
        f"- Entry-window eligible candidates: `{payload['eligible_candidate_count']}`",
        f"- Entry-window ineligible candidates: `{payload['ineligible_candidate_count']}`",
        f"- Resolved eligible labels: `{payload['resolved_count']}` ({payload['resolved_share'] * 100.0:.2f}%)",
        f"- Minority label share: `{payload['minority_label_share'] * 100.0:.2f}%`",
        "",
        "## Chronological Evidence",
        "",
        "| Split | Trades | Win rate | Stress net USD | Stress PF | Avg stress R | Max closed DD R |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for split in ("train", "validation", "test"):
        row = payload["by_split"][split]
        lines.append(
            f"| {split} | {row['trades']} | {row['win_rate_pct']:.2f}% | {row['stress_net_usd']:.2f} | "
            f"{(row['stress_profit_factor'] or 0.0):.4f} | {row['average_stress_r']:.4f} | {row['max_closed_drawdown_r']:.2f} |"
        )
    lines.extend(["", "## Dataset Quality Gates", ""])
    for name, passed in payload["quality_gates"].items():
        lines.append(f"- `{name}`: {'PASS' if passed else 'FAIL'}")
    lines.extend(["", "## Strategy Research Gates", ""])
    for name, passed in payload["strategy_research_gates"].items():
        lines.append(f"- `{name}`: {'PASS' if passed else 'FAIL'}")
    lines.extend(
        [
            "",
            "## Decision Boundary",
            "",
            f"- ML training authorized by label quality: `{payload['authorization']['model_training_authorized']}`",
            "- Candidate-family promotion: `false`",
            "- Python demo predictions: `false`",
            "- EA or broker action: `false`",
            "",
        ]
    )
    return "\n".join(lines)


def _derive_month_h1_bars(
    storage_root: Path,
    symbol: str,
    year: int,
    month: int,
    foundation: Any,
) -> list[dict[str, Any]]:
    rows = []
    for path, raw in foundation.iter_raw_month(storage_root, symbol, year, month):
        try:
            hour = datetime.strptime(path.stem, "%Y%m%d%H").replace(tzinfo=UTC)
        except ValueError as exc:
            raise LabelFactoryError(f"unexpected raw Dukascopy file name: {path}") from exc
        ticks = foundation.decode_payload(raw, symbol, path.name)
        start_ms = int(hour.timestamp() * 1000)
        if any(not start_ms <= int(tick.timestamp_ms) < start_ms + HOUR_MS for tick in ticks):
            raise LabelFactoryError(f"tick outside source hour: {path}")
        if not ticks:
            continue
        bids = [float(tick.bid) for tick in ticks]
        asks = [float(tick.ask) for tick in ticks]
        rows.append(
            {
                "timestamp_utc": _iso_ms(start_ms),
                "timestamp_ms": start_ms,
                "bid_open": bids[0],
                "bid_high": max(bids),
                "bid_low": min(bids),
                "bid_close": bids[-1],
                "ask_open": asks[0],
                "ask_high": max(asks),
                "ask_low": min(asks),
                "ask_close": asks[-1],
                "tick_count": len(ticks),
            }
        )
    return rows


def _month_source_identity(storage_root: Path, symbol: str, year: int, month: int) -> dict[str, Any]:
    partition = storage_root / "raw" / symbol / f"year={year:04d}" / f"month={month:02d}"
    manifest_path = partition / "_ACQUISITION_MANIFEST.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    files = sorted((str(row["path"]), str(row["sha256"])) for row in manifest["rows"])
    return {
        "manifest_sha256": _sha256_file(manifest_path),
        "source_files_composite_sha256": _sha256_json(files),
        "raw_hour_files": len(files),
    }


def _load_valid_bar_cache(
    bars_path: Path,
    metadata_path: Path,
    source: Mapping[str, Any],
    *,
    symbol: str,
    month: str,
) -> tuple[list[dict[str, Any]], dict[str, Any]] | None:
    if not bars_path.is_file() or not metadata_path.is_file():
        return None
    try:
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    expected = {
        "schema_version": BAR_CACHE_SCHEMA,
        "symbol": symbol,
        "month": month,
        "manifest_sha256": source["manifest_sha256"],
        "source_files_composite_sha256": source["source_files_composite_sha256"],
        "raw_hour_files": source["raw_hour_files"],
    }
    if any(metadata.get(key) != value for key, value in expected.items()):
        return None
    if metadata.get("bars_sha256") != _sha256_file(bars_path):
        return None
    with bars_path.open("r", encoding="utf-8", newline="") as handle:
        bars = list(csv.DictReader(handle))
    if len(bars) != int(metadata.get("bar_count", -1)):
        return None
    return bars, metadata


def _validate_contract(contract: Mapping[str, Any]) -> None:
    if contract.get("schema_version") != "a3_ml_dukascopy_label_factory_v1":
        raise ValueError("unexpected Dukascopy label-factory contract version")
    if contract.get("symbol") != "XAUUSD":
        raise ValueError("label factory V1 is locked to XAUUSD")
    if not contract.get("authorization", {}).get("research_only"):
        raise ValueError("label factory must remain research-only")
    for forbidden in ("python_demo_predictions_authorized", "ea_consumption_authorized", "broker_action_authorized"):
        if contract["authorization"].get(forbidden):
            raise ValueError(f"forbidden authorization in label-factory contract: {forbidden}")
    if float(contract["candidate_family"]["reward_r"]) <= 0.0:
        raise ValueError("reward_r must be positive")
    if int(contract["execution"]["maximum_hold_hours"]) <= 0:
        raise ValueError("maximum hold must be positive")


def _validate_candidates(candidates: Sequence[Candidate]) -> None:
    ids = [row.candidate_id for row in candidates]
    keys = [(row.family_id, row.decision_timestamp_ms, row.direction) for row in candidates]
    if len(ids) != len(set(ids)):
        raise LabelFactoryError("duplicate candidate IDs")
    if len(keys) != len(set(keys)):
        raise LabelFactoryError("duplicate candidate keys")
    if any(row.direction not in {"LONG", "SHORT"} for row in candidates):
        raise LabelFactoryError("invalid candidate direction")
    if any(row.stop_distance <= 0.0 for row in candidates):
        raise LabelFactoryError("non-positive candidate stop distance")
    if list(candidates) != sorted(candidates, key=lambda row: (row.decision_timestamp_ms, row.direction)):
        raise LabelFactoryError("candidates are not chronological")


def _load_foundation(repo_root: Path) -> Any:
    source = repo_root / "multi-asset" / "data-foundation" / "dukascopy-ticks-v1" / "src"
    if not source.is_dir():
        raise FileNotFoundError(source)
    if str(source) not in sys.path:
        sys.path.insert(0, str(source))
    return importlib.import_module("dukascopy_tick_foundation.foundation")


def _resolve_storage_root(contract: Mapping[str, Any]) -> Path:
    name = str(contract["storage_environment_variable"])
    configured = os.environ.get(name, "").strip() or str(contract["default_storage_root"])
    root = Path(configured).expanduser().resolve()
    if not root.is_dir():
        raise FileNotFoundError(root)
    return root


def _month_range(start: str, end: str) -> list[tuple[int, int]]:
    start_year, start_month = (int(value) for value in start.split("-"))
    end_year, end_month = (int(value) for value in end.split("-"))
    result = []
    year, month = start_year, start_month
    while (year, month) <= (end_year, end_month):
        result.append((year, month))
        month += 1
        if month == 13:
            year += 1
            month = 1
    return result


def _split_for_timestamp(value: datetime, split_config: Mapping[str, Any]) -> str | None:
    train_end = _parse_utc(split_config["train_end_exclusive_utc"])
    validation_end = _parse_utc(split_config["validation_end_exclusive_utc"])
    test_end = _parse_utc(split_config["test_end_exclusive_utc"])
    if value < train_end:
        return "train"
    if value < validation_end:
        return "validation"
    if value < test_end:
        return "test"
    return None


def _write_rows(path: Path, rows: Sequence[Mapping[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def _parse_utc(value: Any) -> datetime:
    parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError(f"timestamp must be timezone-aware: {value}")
    return parsed.astimezone(UTC)


def _iso_ms(timestamp_ms: int) -> str:
    return datetime.fromtimestamp(timestamp_ms / 1000, UTC).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def _sha256_json(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("ascii")
    return hashlib.sha256(payload).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()
