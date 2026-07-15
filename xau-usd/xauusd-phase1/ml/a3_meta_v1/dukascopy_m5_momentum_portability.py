from __future__ import annotations

import bisect
import csv
import hashlib
import json
import math
import os
import random
from collections import Counter, defaultdict
from dataclasses import asdict
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, Mapping, Sequence

import pandas as pd

from ml.a3_meta_v1.dukascopy_compression_breakout import aggregate_h1_bid_bars
from ml.a3_meta_v1.dukascopy_label_factory import (
    HOUR_MS,
    Candidate,
    VerifiedTickStore,
    _load_foundation,
    _month_range,
    _month_source_identity,
    _sha256_file,
    _validate_candidates,
    _write_rows,
    prepare_verified_h1_bars,
    replay_candidates,
)


M5_MS = 5 * 60_000
M5_CACHE_SCHEMA = "a3_ml_dukascopy_m5_bidask_cache_v1"
DEFAULT_CONTRACT = Path("config/ml/a3_ml_dukascopy_m5_momentum_portability.json")


class M5PortabilityError(RuntimeError):
    pass


def run_dukascopy_m5_momentum_portability(
    root: Path, contract_path: Path | None = None
) -> Path:
    root = root.resolve()
    contract_file = (contract_path or root / DEFAULT_CONTRACT).resolve()
    contract = json.loads(contract_file.read_text(encoding="utf-8"))
    _validate_contract(root, contract)
    storage_root = _resolve_storage_root(contract)
    external_root = storage_root / str(contract["external_output_subdirectory"])
    foundation = _load_foundation(root.parents[1])
    months = _month_range(contract["period"]["start_month"], contract["period"]["end_month"])
    h1_bars, h1_audits = prepare_verified_h1_bars(
        storage_root,
        storage_root / "research" / "xau-label-factory-v1" / "bars",
        str(contract["symbol"]),
        months,
        foundation,
    )
    m5_bars, m5_audits = prepare_verified_m5_bars(
        storage_root,
        external_root / "bars",
        str(contract["symbol"]),
        months,
        foundation,
    )
    candidates = generate_m5_momentum_candidates(m5_bars, h1_bars, contract)
    _validate_candidates(candidates)
    store = VerifiedTickStore(
        storage_root=storage_root,
        symbol=str(contract["symbol"]),
        foundation=foundation,
        prevalidated_months=set(months),
    )
    raw_labels = replay_candidates(candidates, h1_bars, store, contract)
    candidate_by_id = {row.candidate_id: row for row in candidates}
    selected_labels, selection_reasons = apply_lane_execution_controls(
        raw_labels, candidate_by_id, contract
    )

    outputs = {key: (root / value).resolve() for key, value in contract["outputs"].items()}
    _write_rows(outputs["raw_candidates_csv"], [asdict(row) for row in candidates])
    _write_rows(outputs["raw_labels_csv"], [asdict(row) for row in raw_labels])
    _write_rows(outputs["selected_labels_csv"], [asdict(row) for row in selected_labels])
    payload = _build_report(
        root=root,
        contract=contract,
        contract_file=contract_file,
        storage_root=storage_root,
        h1_audits=h1_audits,
        m5_audits=m5_audits,
        m5_bars=m5_bars,
        candidates=candidates,
        raw_labels=raw_labels,
        selected_labels=selected_labels,
        selection_reasons=selection_reasons,
        outputs=outputs,
    )
    outputs["report_json"].parent.mkdir(parents=True, exist_ok=True)
    outputs["report_json"].write_text(json.dumps(payload, indent=2), encoding="utf-8")
    outputs["report_markdown"].write_text(_render(payload), encoding="utf-8")
    return outputs["report_json"]


def prepare_verified_m5_bars(
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
        bars_path = partition / "m5_bidask.csv"
        metadata_path = partition / "metadata.json"
        cached = _load_valid_m5_cache(
            bars_path,
            metadata_path,
            source,
            symbol=symbol,
            month=f"{year:04d}-{month:02d}",
        )
        if cached is None:
            bars = _derive_month_m5_bars(storage_root, symbol, year, month, foundation)
            partition.mkdir(parents=True, exist_ok=True)
            _write_rows(bars_path, bars)
            metadata = {
                "schema_version": M5_CACHE_SCHEMA,
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
                "source_files_composite_sha256": source[
                    "source_files_composite_sha256"
                ],
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
        raise M5PortabilityError("duplicate M5 timestamps across monthly caches")
    if timestamps != sorted(timestamps):
        raise M5PortabilityError("M5 cache is not chronological")
    return all_bars, audits


def _derive_month_m5_bars(
    storage_root: Path,
    symbol: str,
    year: int,
    month: int,
    foundation: Any,
) -> list[dict[str, Any]]:
    output = []
    for path, raw in foundation.iter_raw_month(storage_root, symbol, year, month):
        try:
            hour = datetime.strptime(path.stem, "%Y%m%d%H").replace(tzinfo=UTC)
        except ValueError as exc:
            raise M5PortabilityError(f"unexpected raw Dukascopy file name: {path}") from exc
        ticks = foundation.decode_payload(raw, symbol, path.name)
        hour_ms = int(hour.timestamp() * 1000)
        if any(
            not hour_ms <= int(tick.timestamp_ms) < hour_ms + HOUR_MS for tick in ticks
        ):
            raise M5PortabilityError(f"tick outside source hour: {path}")
        output.extend(_aggregate_ticks_to_m5(ticks))
    output.sort(key=lambda row: int(row["timestamp_ms"]))
    return output


def _aggregate_ticks_to_m5(ticks: Sequence[Any]) -> list[dict[str, Any]]:
    bars: dict[int, dict[str, Any]] = {}
    previous_ms = -1
    for tick in ticks:
        timestamp_ms = int(tick.timestamp_ms)
        if timestamp_ms < previous_ms:
            raise M5PortabilityError("raw ticks are not chronological")
        previous_ms = timestamp_ms
        start_ms = timestamp_ms - timestamp_ms % M5_MS
        bid = float(tick.bid)
        ask = float(tick.ask)
        row = bars.get(start_ms)
        if row is None:
            bars[start_ms] = {
                "timestamp_utc": _iso_ms(start_ms),
                "timestamp_ms": start_ms,
                "bid_open": bid,
                "bid_high": bid,
                "bid_low": bid,
                "bid_close": bid,
                "ask_open": ask,
                "ask_high": ask,
                "ask_low": ask,
                "ask_close": ask,
                "tick_count": 1,
            }
        else:
            row["bid_high"] = max(float(row["bid_high"]), bid)
            row["bid_low"] = min(float(row["bid_low"]), bid)
            row["bid_close"] = bid
            row["ask_high"] = max(float(row["ask_high"]), ask)
            row["ask_low"] = min(float(row["ask_low"]), ask)
            row["ask_close"] = ask
            row["tick_count"] = int(row["tick_count"]) + 1
    return [bars[key] for key in sorted(bars)]


def _load_valid_m5_cache(
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
        "schema_version": M5_CACHE_SCHEMA,
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


def generate_m5_momentum_candidates(
    m5_bars: Sequence[Mapping[str, Any]],
    h1_bars: Sequence[Mapping[str, Any]],
    contract: Mapping[str, Any],
) -> list[Candidate]:
    m5 = _m5_indicator_frame(m5_bars, contract)
    h1 = _trend_frame(
        [
            {
                "timestamp_ms": row["timestamp_ms"],
                "close": row["bid_close"],
            }
            for row in h1_bars
        ],
        width_hours=1,
        fast_period=int(contract["signal"]["h1_ema_fast_period"]),
        slow_period=int(contract["signal"]["h1_ema_slow_period"]),
        slope_bars=int(contract["signal"]["h1_slope_bars"]),
    )
    h4_bars = aggregate_h1_bid_bars(
        h1_bars, width_hours=4, minimum_active_hours=1
    )
    h4 = _trend_frame(
        [
            {"timestamp_ms": row["timestamp_ms"], "close": row["close"]}
            for row in h4_bars
        ],
        width_hours=4,
        fast_period=int(contract["signal"]["h4_ema_fast_period"]),
        slow_period=int(contract["signal"]["h4_ema_slow_period"]),
        slope_bars=int(contract["signal"]["h4_slope_bars"]),
    )
    if m5.empty or h1.empty or h4.empty:
        return []
    h1_ends = [int(value) for value in h1["end_timestamp_ms"]]
    h4_ends = [int(value) for value in h4["end_timestamp_ms"]]
    signal = contract["signal"]
    lookback = int(signal["break_lookback_m5_bars"])
    point = float(signal["point_size"])
    output: list[Candidate] = []

    for index in range(max(lookback, 3), len(m5)):
        row = m5.iloc[index]
        if pd.isna(row["atr"]):
            continue
        start_ms = int(row["timestamp_ms"])
        decision_ms = start_ms + M5_MS
        window = _window_for_timestamp(decision_ms, contract)
        if window is None:
            continue
        h1_index = bisect.bisect_right(h1_ends, decision_ms) - 1
        h4_index = bisect.bisect_right(h4_ends, decision_ms) - 1
        if h1_index < 0 or h4_index < 0:
            continue
        h1_row = h1.iloc[h1_index]
        h4_row = h4.iloc[h4_index]
        required = ("ema_fast", "ema_slow", "ema_fast_prior")
        if any(pd.isna(h1_row[name]) or pd.isna(h4_row[name]) for name in required):
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
        prior = m5.iloc[index - lookback : index]
        recent_high = float(prior["bid_high"].max())
        recent_low = float(prior["bid_low"].min())
        three_bar_move_atr = (closed - float(m5.iloc[index - 3]["bid_close"])) / atr
        server_hour = _server_time(decision_ms, contract).hour

        for lane in contract["lanes"]:
            if server_hour in {int(value) for value in lane["blocked_server_hours"]}:
                continue
            direction = str(lane["direction"])
            minimum_move = float(lane["minimum_three_bar_move_atr"])
            break_distance_atr = 0.0
            if direction == "LONG":
                if not (
                    closed > opened
                    and close_location >= float(signal["long_close_location"])
                    and closed
                    >= recent_high + float(signal["break_atr_multiple"]) * atr
                    and three_bar_move_atr >= minimum_move
                    and _trend_allows(h1_row, "LONG")
                    and _trend_allows(h4_row, "LONG")
                ):
                    continue
                break_distance_atr = (closed - recent_high) / atr
            elif direction == "SHORT":
                if not (
                    closed < opened
                    and close_location <= float(signal["short_close_location"])
                    and closed
                    <= recent_low - float(signal["break_atr_multiple"]) * atr
                    and three_bar_move_atr <= -minimum_move
                    and _trend_allows(h1_row, "SHORT")
                    and _trend_allows(h4_row, "SHORT")
                ):
                    continue
                break_distance_atr = (recent_low - closed) / atr
            else:
                raise ValueError(f"unsupported lane direction: {direction}")
            stop_distance = max(
                float(signal["stop_atr_multiple"]) * atr,
                int(signal["stop_floor_points"]) * point,
            )
            stop_points = stop_distance / point
            if stop_points > int(signal["stop_ceiling_points"]):
                continue
            family_id = str(lane["family_id"])
            candidate_id = hashlib.sha256(
                f"{family_id}|{contract['symbol']}|{decision_ms}|{direction}".encode("ascii")
            ).hexdigest()[:24]
            output.append(
                Candidate(
                    candidate_id=candidate_id,
                    family_id=family_id,
                    symbol=str(contract["symbol"]),
                    split=window,
                    direction=direction,
                    signal_bar_start_utc=_iso_ms(start_ms),
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
                    / atr,
                    atr=atr,
                    body_fraction=body_fraction,
                    close_location=close_location,
                    touch_distance_atr=break_distance_atr,
                    stop_distance=stop_distance,
                    stop_distance_atr=stop_distance / atr,
                    reward_r=float(lane["reward_r"]),
                    signal_tick_count=int(row["tick_count"]),
                )
            )
    return output


def _m5_indicator_frame(
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
    period = int(contract["signal"]["atr_period"])
    frame["atr"] = true_range.ewm(
        alpha=1.0 / period, adjust=False, min_periods=period
    ).mean()
    return frame


def _trend_frame(
    bars: Sequence[Mapping[str, Any]],
    *,
    width_hours: int,
    fast_period: int,
    slow_period: int,
    slope_bars: int,
) -> pd.DataFrame:
    frame = pd.DataFrame(bars).copy()
    if frame.empty:
        return frame
    frame["timestamp_ms"] = pd.to_numeric(
        frame["timestamp_ms"], errors="raise"
    ).astype("int64")
    frame["close"] = pd.to_numeric(frame["close"], errors="raise").astype(float)
    frame = frame.sort_values("timestamp_ms").reset_index(drop=True)
    frame["end_timestamp_ms"] = frame["timestamp_ms"] + width_hours * HOUR_MS
    frame["ema_fast"] = frame["close"].ewm(
        span=fast_period, adjust=False, min_periods=fast_period
    ).mean()
    frame["ema_slow"] = frame["close"].ewm(
        span=slow_period, adjust=False, min_periods=slow_period
    ).mean()
    frame["ema_fast_prior"] = frame["ema_fast"].shift(slope_bars)
    return frame


def _trend_allows(row: Mapping[str, Any], direction: str) -> bool:
    close = float(row["close"])
    fast = float(row["ema_fast"])
    slow = float(row["ema_slow"])
    prior = float(row["ema_fast_prior"])
    if direction == "LONG":
        return close > fast > slow and fast >= prior
    if direction == "SHORT":
        return close < fast < slow and fast <= prior
    return False


def apply_lane_execution_controls(
    labels: Sequence[Any],
    candidates: Mapping[str, Candidate],
    contract: Mapping[str, Any],
) -> tuple[list[Any], dict[str, int]]:
    signal = contract["signal"]
    point = float(signal["point_size"])
    lane_by_family = {str(row["family_id"]): row for row in contract["lanes"]}
    selected: list[Any] = []
    reasons: Counter[str] = Counter()
    for family_id, lane in lane_by_family.items():
        lane_rows = sorted(
            [row for row in labels if row.family_id == family_id],
            key=lambda row: (
                candidates[row.candidate_id].decision_timestamp_ms,
                row.candidate_id,
            ),
        )
        open_until: datetime | None = None
        last_trade: datetime | None = None
        daily_entries: Counter[str] = Counter()
        for row in lane_rows:
            if row.status != "RESOLVED":
                reasons[f"raw_{row.status.lower()}_{row.exit_reason}"] += 1
                continue
            if row.entry_spread is None or row.entry_time_utc == "":
                reasons["missing_entry_quote"] += 1
                continue
            spread_points = float(row.entry_spread) / point
            if spread_points > float(signal["maximum_spread_points"]):
                reasons["spread_above_maximum"] += 1
                continue
            if float(row.entry_spread) / float(row.stop_distance) > float(
                signal["maximum_estimated_cost_r"]
            ):
                reasons["estimated_cost_r_above_maximum"] += 1
                continue
            entry = _parse_utc(row.entry_time_utc)
            exit_time = _parse_utc(row.exit_time_utc)
            if bool(lane["one_position_at_a_time"]) and open_until is not None and entry < open_until:
                reasons["lane_position_already_open"] += 1
                continue
            cooldown = timedelta(minutes=int(lane["cooldown_minutes"]))
            if last_trade is not None and entry - last_trade < cooldown:
                reasons["lane_cooldown"] += 1
                continue
            server_day = (entry + timedelta(hours=int(contract["server_time"]["utc_offset_hours"]))).date().isoformat()
            if daily_entries[server_day] >= int(lane["maximum_trades_per_server_day"]):
                reasons["lane_daily_cap"] += 1
                continue
            selected.append(row)
            daily_entries[server_day] += 1
            last_trade = entry
            open_until = exit_time
    selected.sort(key=lambda row: (row.entry_time_utc, row.candidate_id))
    return selected, dict(reasons)


def _build_report(
    *,
    root: Path,
    contract: Mapping[str, Any],
    contract_file: Path,
    storage_root: Path,
    h1_audits: Sequence[Mapping[str, Any]],
    m5_audits: Sequence[Mapping[str, Any]],
    m5_bars: Sequence[Mapping[str, Any]],
    candidates: Sequence[Candidate],
    raw_labels: Sequence[Any],
    selected_labels: Sequence[Any],
    selection_reasons: Mapping[str, int],
    outputs: Mapping[str, Path],
) -> dict[str, Any]:
    candidate_by_id = {row.candidate_id: row for row in candidates}
    source_days = _source_days_by_window(m5_bars, contract)
    evidence = {
        window: _stats(
            [row for row in selected_labels if row.split == window],
            source_days.get(window, 0),
            contract,
        )
        for window in ("prehistory", "replication")
    }
    lane_evidence = {
        window: {
            str(lane["family_id"]): _basic_stats(
                [
                    row
                    for row in selected_labels
                    if row.split == window and row.family_id == str(lane["family_id"])
                ]
            )
            for lane in contract["lanes"]
        }
        for window in ("prehistory", "replication")
    }
    bootstrap = {
        window: _month_bootstrap(
            [row for row in selected_labels if row.split == window],
            samples=int(contract["bootstrap"]["calendar_month_samples"]),
            seed=int(contract["bootstrap"]["seed"]),
        )
        for window in ("prehistory", "replication")
    }
    raw_eligible = [row for row in raw_labels if row.status != "INELIGIBLE"]
    raw_resolved = [row for row in raw_labels if row.status == "RESOLVED"]
    timeout_share = (
        sum(row.exit_reason == "TIMEOUT" for row in selected_labels) / len(selected_labels)
        if selected_labels
        else 0.0
    )
    quality = contract["quality_gates"]
    source_lock = contract["source_lock"]
    quality_gates = {
        "verified_h1_months_eq_expected": len(h1_audits) == int(quality["expected_months"]),
        "verified_m5_months_eq_expected": len(m5_audits) == int(quality["expected_months"]),
        "raw_candidates_ge_minimum": len(candidates) >= int(quality["minimum_raw_candidates"]),
        "resolved_share_ge_minimum": (
            len(raw_resolved) / len(raw_eligible) >= float(quality["minimum_resolved_share"])
            if raw_eligible
            else False
        ),
        "selected_timeout_share_lte_maximum": timeout_share
        <= float(quality["maximum_selected_timeout_share"]),
        "candidate_ids_unique": len(candidate_by_id) == len(candidates),
        "selected_candidate_ids_unique": len({row.candidate_id for row in selected_labels})
        == len(selected_labels),
        "ea_source_hash_matches": _sha256_file(root / source_lock["ea_path"])
        == str(source_lock["ea_sha256"]),
        "portfolio_spec_hash_matches": _sha256_file(
            root / source_lock["portfolio_spec_path"]
        )
        == str(source_lock["portfolio_spec_sha256"]),
        "all_lanes_represented": {row.family_id for row in selected_labels}
        == {str(row["family_id"]) for row in contract["lanes"]},
    }
    strategy_gates = _strategy_gates(
        evidence, lane_evidence, bootstrap, contract["strategy_gates"]
    )
    if not all(quality_gates.values()):
        classification = "DUKASCOPY_M5_MOMENTUM_PORTABILITY_INVALID"
    elif all(strategy_gates.values()):
        classification = "DUKASCOPY_M5_MOMENTUM_PORTABILITY_RESEARCH_SURVIVOR"
    else:
        classification = "DUKASCOPY_M5_MOMENTUM_PORTABILITY_NO_SURVIVOR"
    return {
        "schema_version": str(contract["schema_version"]),
        "classification": classification,
        "created_at_utc": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "contract": str(contract_file),
        "contract_sha256": _sha256_file(contract_file),
        "source_lock": source_lock,
        "storage_root": str(storage_root),
        "source_months": len(m5_audits),
        "source_composite_sha256": _sha256_json(
            [(row["month"], row["source_files_composite_sha256"]) for row in m5_audits]
        ),
        "m5_bar_count": len(m5_bars),
        "m5_cache_reused_months": sum(bool(row["bar_cache_reused"]) for row in m5_audits),
        "source_days_by_window": source_days,
        "raw_candidate_count": len(candidates),
        "raw_resolved_count": len(raw_resolved),
        "raw_resolved_share": len(raw_resolved) / len(raw_eligible) if raw_eligible else 0.0,
        "selected_trade_count": len(selected_labels),
        "selected_timeout_share": timeout_share,
        "raw_candidates_by_lane": dict(Counter(row.family_id for row in candidates)),
        "selected_trades_by_lane": dict(Counter(row.family_id for row in selected_labels)),
        "selection_reasons": dict(selection_reasons),
        "quality_gates": quality_gates,
        "evidence": evidence,
        "lane_evidence": lane_evidence,
        "calendar_month_bootstrap": bootstrap,
        "strategy_gates": strategy_gates,
        "artifacts": {
            key: {"path": str(path), "sha256": _sha256_file(path)}
            for key, path in outputs.items()
            if key in {"raw_candidates_csv", "raw_labels_csv", "selected_labels_csv"}
        },
        "authorization": {
            **contract["authorization"],
            "strategy_promotion_authorized": False,
        },
        "limitations": [
            "Prehistory is a backcast and replication dates overlap prior MT5 research.",
            "A survivor is cross-feed evidence, not prospective demo or live proof.",
            "The 720-hour research timeout approximates an EA that otherwise holds until stop or target.",
            "Fixed 0.01-lot results are not account-relative sizing or risk-of-ruin evidence.",
        ],
    }


def _strategy_gates(
    evidence: Mapping[str, Mapping[str, Any]],
    lane_evidence: Mapping[str, Mapping[str, Mapping[str, Any]]],
    bootstrap: Mapping[str, Mapping[str, Any]],
    configured: Mapping[str, Any],
) -> dict[str, bool]:
    prehistory = evidence["prehistory"]
    replication = evidence["replication"]
    return {
        "prehistory_rows_ge_minimum": prehistory["trades"]
        >= int(configured["minimum_prehistory_trades"]),
        "replication_rows_ge_minimum": replication["trades"]
        >= int(configured["minimum_replication_trades"]),
        "each_window_trades_per_source_day_ge_minimum": all(
            row["trades_per_source_day"] >= float(configured["minimum_trades_per_source_day"])
            for row in evidence.values()
        ),
        "each_window_trades_per_active_day_ge_minimum": all(
            row["trades_per_active_trade_day"]
            >= float(configured["minimum_trades_per_active_trade_day"])
            for row in evidence.values()
        ),
        "each_window_active_day_coverage_ge_minimum": all(
            row["active_trade_day_coverage"]
            >= float(configured["minimum_active_trade_day_coverage"])
            for row in evidence.values()
        ),
        "prehistory_win_rate_ge_minimum": prehistory["win_rate_pct"]
        >= float(configured["minimum_prehistory_win_rate_pct"]),
        "replication_win_rate_ge_minimum": replication["win_rate_pct"]
        >= float(configured["minimum_replication_win_rate_pct"]),
        "prehistory_pf_ge_minimum": (prehistory["stress_profit_factor"] or 0.0)
        >= float(configured["minimum_prehistory_stress_profit_factor"]),
        "replication_pf_ge_minimum": (replication["stress_profit_factor"] or 0.0)
        >= float(configured["minimum_replication_stress_profit_factor"]),
        "each_window_positive_month_share_ge_minimum": all(
            row["positive_exit_month_share"]
            >= float(configured["minimum_positive_exit_month_share"])
            for row in evidence.values()
        ),
        "prehistory_drawdown_usd_lte_maximum": prehistory["max_closed_drawdown_usd"]
        <= float(configured["maximum_prehistory_closed_drawdown_usd"]),
        "replication_drawdown_usd_lte_maximum": replication["max_closed_drawdown_usd"]
        <= float(configured["maximum_replication_closed_drawdown_usd"]),
        "concurrent_trades_lte_maximum": max(
            row["maximum_concurrent_trades"] for row in evidence.values()
        )
        <= int(configured["maximum_concurrent_trades"]),
        "each_lane_net_nonnegative_each_window": all(
            row["stress_net_usd"] >= 0.0
            for window in lane_evidence.values()
            for row in window.values()
        ),
        "top25_removed_net_positive_each_window": all(
            row["top25_winners_removed_net_usd"] > 0.0 for row in evidence.values()
        ),
        "bootstrap_p025_above_zero_each_window": all(
            row.get("average_stress_r_p025") is not None
            and float(row["average_stress_r_p025"]) > 0.0
            for row in bootstrap.values()
        ),
    }


def _stats(
    rows: Sequence[Any], source_days: int, contract: Mapping[str, Any]
) -> dict[str, Any]:
    base = _basic_stats(rows)
    offset = int(contract["server_time"]["utc_offset_hours"])
    entry_days = Counter(
        (_parse_utc(row.entry_time_utc) + timedelta(hours=offset)).date().isoformat()
        for row in rows
    )
    active_days = len(entry_days)
    by_month: dict[str, float] = defaultdict(float)
    for row in rows:
        by_month[row.exit_time_utc[:7]] += float(row.stress_net_pnl_usd)
    positive_months = sum(value > 0.0 for value in by_month.values())
    events = []
    for row in rows:
        events.append((_parse_utc(row.entry_time_utc), 1))
        events.append((_parse_utc(row.exit_time_utc), -1))
    base.update(
        {
            "source_days": source_days,
            "trades_per_source_day": len(rows) / source_days if source_days else 0.0,
            "active_trade_days": active_days,
            "active_trade_day_coverage": active_days / source_days if source_days else 0.0,
            "trades_per_active_trade_day": len(rows) / active_days if active_days else 0.0,
            "maximum_entries_one_server_day": max(entry_days.values(), default=0),
            "active_exit_months": len(by_month),
            "positive_exit_months": positive_months,
            "positive_exit_month_share": positive_months / len(by_month) if by_month else 0.0,
            "maximum_concurrent_trades": _maximum_concurrency(events),
            "timeout_exits": sum(row.exit_reason == "TIMEOUT" for row in rows),
        }
    )
    return base


def _basic_stats(rows: Sequence[Any]) -> dict[str, Any]:
    ordered = sorted(rows, key=lambda row: (row.exit_time_utc, row.candidate_id))
    pnl = [float(row.stress_net_pnl_usd) for row in ordered]
    returns = [float(row.stress_net_r) for row in ordered]
    gross_profit = sum(value for value in pnl if value > 0.0)
    gross_loss = -sum(value for value in pnl if value < 0.0)
    top_winners = sorted((value for value in pnl if value > 0.0), reverse=True)[:25]
    return {
        "trades": len(ordered),
        "wins": sum(value > 0.0 for value in pnl),
        "win_rate_pct": 100.0 * sum(value > 0.0 for value in pnl) / len(pnl) if pnl else 0.0,
        "stress_net_usd": sum(pnl),
        "stress_profit_factor": gross_profit / gross_loss if gross_loss > 0.0 else None,
        "average_stress_r": sum(returns) / len(returns) if returns else 0.0,
        "max_closed_drawdown_r": _max_drawdown(returns),
        "max_closed_drawdown_usd": _max_drawdown(pnl),
        "top25_winners_removed_net_usd": sum(pnl) - sum(top_winners),
    }


def _month_bootstrap(
    rows: Sequence[Any], *, samples: int, seed: int
) -> dict[str, Any]:
    groups: dict[str, list[float]] = defaultdict(list)
    for row in rows:
        groups[row.exit_time_utc[:7]].append(float(row.stress_net_r))
    months = sorted(groups)
    if len(months) < 6:
        return {
            "samples": samples,
            "seed": seed,
            "active_exit_months": len(months),
            "average_stress_r_p025": None,
            "average_stress_r_p50": None,
            "average_stress_r_p975": None,
        }
    rng = random.Random(seed)
    estimates = []
    for _ in range(samples):
        selected = [rng.choice(months) for _ in months]
        values = [value for month in selected for value in groups[month]]
        estimates.append(sum(values) / len(values))
    estimates.sort()
    return {
        "samples": samples,
        "seed": seed,
        "active_exit_months": len(months),
        "average_stress_r_p025": _percentile(estimates, 0.025),
        "average_stress_r_p50": _percentile(estimates, 0.5),
        "average_stress_r_p975": _percentile(estimates, 0.975),
    }


def _source_days_by_window(
    m5_bars: Sequence[Mapping[str, Any]], contract: Mapping[str, Any]
) -> dict[str, int]:
    offset = int(contract["server_time"]["utc_offset_hours"])
    minimum = int(contract["quality_gates"]["minimum_m5_bars_per_source_day"])
    counts: dict[str, Counter[str]] = defaultdict(Counter)
    for row in m5_bars:
        timestamp_ms = int(row["timestamp_ms"])
        window = _window_for_timestamp(timestamp_ms + M5_MS, contract)
        if window is None:
            continue
        server_date = (
            datetime.fromtimestamp(timestamp_ms / 1000, UTC) + timedelta(hours=offset)
        ).date().isoformat()
        counts[window][server_date] += 1
    return {
        window: sum(value >= minimum for value in counts.get(window, {}).values())
        for window in ("prehistory", "replication")
    }


def _render(payload: Mapping[str, Any]) -> str:
    lines = [
        "# A3 ML Dukascopy M5 Momentum Portability V1",
        "",
        f"Classification: `{payload['classification']}`",
        "",
        "Historical cross-feed research only. No demo or broker action is authorized.",
        "",
        "## Population",
        "",
        f"- M5 bars: `{payload['m5_bar_count']}`",
        f"- Raw candidates: `{payload['raw_candidate_count']}`",
        f"- Raw resolved: `{payload['raw_resolved_count']}` ({payload['raw_resolved_share'] * 100.0:.2f}%)",
        f"- Selected executable trades: `{payload['selected_trade_count']}`",
        "",
        "## Evidence",
        "",
        "| Window | Trades | Trades/source day | Trades/active day | Coverage | Win rate | Net USD | PF | Avg R | DD USD | Positive months |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for window in ("prehistory", "replication"):
        row = payload["evidence"][window]
        lines.append(
            f"| {window} | {row['trades']} | {row['trades_per_source_day']:.3f} | "
            f"{row['trades_per_active_trade_day']:.3f} | {row['active_trade_day_coverage'] * 100.0:.2f}% | "
            f"{row['win_rate_pct']:.2f}% | {row['stress_net_usd']:.2f} | "
            f"{(row['stress_profit_factor'] or 0.0):.4f} | {row['average_stress_r']:.4f} | "
            f"{row['max_closed_drawdown_usd']:.2f} | {row['positive_exit_months']}/{row['active_exit_months']} |"
        )
    lines.extend(["", "## Quality Gates", ""])
    for name, passed in payload["quality_gates"].items():
        lines.append(f"- `{name}`: {'PASS' if passed else 'FAIL'}")
    lines.extend(["", "## Strategy Gates", ""])
    for name, passed in payload["strategy_gates"].items():
        lines.append(f"- `{name}`: {'PASS' if passed else 'FAIL'}")
    lines.extend(
        [
            "",
            "Strategy promotion, demo prediction, EA consumption, and broker action remain disabled.",
            "",
        ]
    )
    return "\n".join(lines)


def _validate_contract(root: Path, contract: Mapping[str, Any]) -> None:
    if contract.get("schema_version") != "a3_ml_dukascopy_m5_momentum_portability_v1":
        raise ValueError("unexpected M5 portability contract version")
    if contract.get("symbol") != "XAUUSD":
        raise ValueError("M5 portability V1 is locked to XAUUSD")
    if int(contract["server_time"]["utc_offset_hours"]) != 4:
        raise ValueError("M5 portability V1 requires the frozen UTC+4 server mapping")
    expected_lanes = {
        (
            "dukascopy_clean_long_v5_move12",
            "LONG",
            0.7,
            1.2,
        ),
        (
            "dukascopy_clean_short_core",
            "SHORT",
            0.7,
            0.7,
        ),
    }
    actual_lanes = {
        (
            str(row["family_id"]),
            str(row["direction"]),
            float(row["reward_r"]),
            float(row["minimum_three_bar_move_atr"]),
        )
        for row in contract["lanes"]
    }
    if actual_lanes != expected_lanes:
        raise ValueError("M5 portability lane set differs from the frozen lock")
    source = contract["source_lock"]
    if _sha256_file(root / source["ea_path"]) != str(source["ea_sha256"]):
        raise ValueError("locked M5 EA source hash mismatch")
    if _sha256_file(root / source["portfolio_spec_path"]) != str(
        source["portfolio_spec_sha256"]
    ):
        raise ValueError("locked M5 portfolio spec hash mismatch")
    if not contract["authorization"].get("research_only"):
        raise ValueError("M5 portability must remain research-only")
    if any(
        contract["authorization"].get(key)
        for key in (
            "python_demo_predictions_authorized",
            "ea_consumption_authorized",
            "broker_action_authorized",
        )
    ):
        raise ValueError("M5 portability contract contains forbidden authorization")
    if int(contract["execution"]["maximum_hold_hours"]) != 720:
        raise ValueError("M5 portability V1 requires the frozen 720-hour research horizon")


def _window_for_timestamp(timestamp_ms: int, contract: Mapping[str, Any]) -> str | None:
    value = datetime.fromtimestamp(timestamp_ms / 1000, UTC)
    prehistory_end = _parse_utc(contract["windows"]["prehistory_end_exclusive_utc"])
    replication_end = _parse_utc(contract["windows"]["replication_end_exclusive_utc"])
    if value < prehistory_end:
        return "prehistory"
    if value < replication_end:
        return "replication"
    return None


def _server_time(timestamp_ms: int, contract: Mapping[str, Any]) -> datetime:
    return datetime.fromtimestamp(timestamp_ms / 1000, UTC) + timedelta(
        hours=int(contract["server_time"]["utc_offset_hours"])
    )


def _maximum_concurrency(events: Sequence[tuple[datetime, int]]) -> int:
    current = maximum = 0
    for _, delta in sorted(events, key=lambda item: (item[0], item[1])):
        current += delta
        maximum = max(maximum, current)
    return maximum


def _resolve_storage_root(contract: Mapping[str, Any]) -> Path:
    name = str(contract["storage_environment_variable"])
    value = os.environ.get(name, "").strip() or str(contract["default_storage_root"])
    root = Path(value).expanduser().resolve()
    if not root.is_dir():
        raise FileNotFoundError(root)
    return root


def _max_drawdown(values: Sequence[float]) -> float:
    equity = peak = maximum = 0.0
    for value in values:
        equity += value
        peak = max(peak, equity)
        maximum = max(maximum, peak - equity)
    return maximum


def _percentile(values: Sequence[float], probability: float) -> float:
    position = probability * (len(values) - 1)
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return float(values[lower])
    weight = position - lower
    return float(values[lower] * (1.0 - weight) + values[upper] * weight)


def _parse_utc(value: Any) -> datetime:
    parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError(f"timestamp must be timezone-aware: {value}")
    return parsed.astimezone(UTC)


def _sha256_json(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("ascii")
    return hashlib.sha256(payload).hexdigest()


def _iso_ms(timestamp_ms: int) -> str:
    return datetime.fromtimestamp(timestamp_ms / 1000, UTC).isoformat(
        timespec="milliseconds"
    ).replace("+00:00", "Z")
