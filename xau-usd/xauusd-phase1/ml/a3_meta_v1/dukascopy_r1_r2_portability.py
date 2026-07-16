from __future__ import annotations

import bisect
import csv
import hashlib
import json
import math
from collections import Counter, defaultdict
from dataclasses import asdict
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, Mapping, Sequence

import pandas as pd

from ml.a3_meta_v1.dukascopy_label_factory import (
    Candidate,
    VerifiedTickStore,
    _load_foundation,
    _month_range,
    _parse_utc,
    _sha256_file,
    _validate_candidates,
    _write_rows,
    prepare_verified_h1_bars,
    replay_candidates,
)
from ml.a3_meta_v1.dukascopy_xau_history_inventory import (
    DEFAULT_CONTRACT,
    inventory_history,
    resolve_storage_root,
    validate_contract,
)


HOUR_MS = 60 * 60_000
DAY_MS = 24 * HOUR_MS
R1 = "r1_box_clean_strict_uptrend"
R2 = "r2_pullback_short_h1_confirm"


class R1R2PortabilityError(RuntimeError):
    pass


def run_r1_r2_portability(
    phase1_root: Path, contract_path: Path | None = None
) -> Path:
    phase1_root = phase1_root.resolve()
    contract_file = (contract_path or phase1_root / DEFAULT_CONTRACT).resolve()
    contract = json.loads(contract_file.read_text(encoding="utf-8"))
    validate_contract(phase1_root, contract)
    storage_root = resolve_storage_root(contract)
    foundation = _load_foundation(phase1_root.parents[1])
    months = _month_range(contract["period"]["start_month"], contract["period"]["end_month"])
    inventory = inventory_history(
        storage_root, str(contract["symbol"]), months, foundation
    )
    if not inventory["ready"]:
        raise R1R2PortabilityError(
            f"Dukascopy source is not ready: {inventory['valid_months']}/{inventory['expected_months']} months"
        )

    external = storage_root / str(contract["external_output_subdirectory"])
    h1_bars, source_audits = prepare_verified_h1_bars(
        storage_root,
        external / "h1-bars",
        str(contract["symbol"]),
        months,
        foundation,
    )
    candidates = generate_r1_r2_candidates(h1_bars, contract)
    _validate_candidates(candidates)
    store = VerifiedTickStore(
        storage_root=storage_root,
        symbol=str(contract["symbol"]),
        foundation=foundation,
        prevalidated_months=set(months),
    )
    raw_labels = replay_candidates(candidates, h1_bars, store, contract)
    selected, selection_reasons = apply_specialist_controls(
        raw_labels, {row.candidate_id: row for row in candidates}, contract
    )

    outputs = {
        key: (phase1_root / value).resolve()
        for key, value in contract["outputs"].items()
        if key not in {"inventory_json", "inventory_markdown"}
    }
    _write_rows(outputs["raw_candidates_csv"], [asdict(row) for row in candidates])
    _write_rows(outputs["raw_labels_csv"], [asdict(row) for row in raw_labels])
    _write_rows(outputs["selected_labels_csv"], [asdict(row) for row in selected])
    payload = build_report(
        phase1_root,
        contract,
        contract_file,
        source_audits,
        candidates,
        raw_labels,
        selected,
        selection_reasons,
        outputs,
    )
    outputs["portability_json"].parent.mkdir(parents=True, exist_ok=True)
    outputs["portability_json"].write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    outputs["portability_markdown"].write_text(render_report(payload), encoding="utf-8")
    return outputs["portability_json"]


def aggregate_h1_bidask_bars(
    h1_bars: Sequence[Mapping[str, Any]], *, width_hours: int, utc_offset_hours: int
) -> list[dict[str, Any]]:
    width_ms = width_hours * HOUR_MS
    offset_ms = utc_offset_hours * HOUR_MS
    bars: dict[int, dict[str, Any]] = {}
    for source in sorted(h1_bars, key=lambda row: int(row["timestamp_ms"])):
        timestamp_ms = int(source["timestamp_ms"])
        start_ms = ((timestamp_ms + offset_ms) // width_ms) * width_ms - offset_ms
        row = bars.get(start_ms)
        if row is None:
            row = {
                "timestamp_ms": start_ms,
                "timestamp_utc": _iso_ms(start_ms),
                "bid_open": float(source["bid_open"]),
                "bid_high": float(source["bid_high"]),
                "bid_low": float(source["bid_low"]),
                "bid_close": float(source["bid_close"]),
                "ask_open": float(source["ask_open"]),
                "ask_high": float(source["ask_high"]),
                "ask_low": float(source["ask_low"]),
                "ask_close": float(source["ask_close"]),
                "tick_count": int(source["tick_count"]),
            }
            bars[start_ms] = row
        else:
            row["bid_high"] = max(float(row["bid_high"]), float(source["bid_high"]))
            row["bid_low"] = min(float(row["bid_low"]), float(source["bid_low"]))
            row["bid_close"] = float(source["bid_close"])
            row["ask_high"] = max(float(row["ask_high"]), float(source["ask_high"]))
            row["ask_low"] = min(float(row["ask_low"]), float(source["ask_low"]))
            row["ask_close"] = float(source["ask_close"])
            row["tick_count"] = int(row["tick_count"]) + int(source["tick_count"])
    return [bars[key] for key in sorted(bars)]


def indicator_frame(bars: Sequence[Mapping[str, Any]]) -> pd.DataFrame:
    frame = pd.DataFrame(bars).copy()
    if frame.empty:
        return frame
    numeric = (
        "timestamp_ms",
        "bid_open",
        "bid_high",
        "bid_low",
        "bid_close",
        "tick_count",
    )
    for name in numeric:
        frame[name] = pd.to_numeric(frame[name], errors="raise")
    frame = frame.sort_values("timestamp_ms").reset_index(drop=True)
    frame["ema20"] = frame["bid_close"].ewm(span=20, adjust=False).mean()
    frame["ema50"] = frame["bid_close"].ewm(span=50, adjust=False).mean()
    frame["ema20_lag5"] = frame["ema20"].shift(5)
    frame["ema50_lag5"] = frame["ema50"].shift(5)
    frame["atr14"] = wilder_atr(frame, 14)
    frame["atr_pct_60"] = rolling_percentile_rank(frame["atr14"], 60)
    frame["atr_pct_252"] = rolling_percentile_rank(frame["atr14"], 252)
    frame["median_range20"] = (
        (frame["bid_high"] - frame["bid_low"]).rolling(20, min_periods=1).median()
    )
    frame["available_timestamp_ms"] = frame["timestamp_ms"].shift(-1)
    return frame


def wilder_atr(frame: pd.DataFrame, period: int) -> pd.Series:
    previous = frame["bid_close"].shift(1)
    true_range = pd.concat(
        [
            frame["bid_high"] - frame["bid_low"],
            (frame["bid_high"] - previous).abs(),
            (frame["bid_low"] - previous).abs(),
        ],
        axis=1,
    ).max(axis=1)
    values = [math.nan] * len(frame)
    if len(frame) < period:
        return pd.Series(values, index=frame.index, dtype=float)
    values[period - 1] = float(true_range.iloc[:period].mean())
    for index in range(period, len(frame)):
        values[index] = (
            values[index - 1] * (period - 1) + float(true_range.iloc[index])
        ) / period
    return pd.Series(values, index=frame.index, dtype=float)


def rolling_percentile_rank(values: pd.Series, lookback: int) -> pd.Series:
    output: list[float] = []
    for index, current in enumerate(values):
        if pd.isna(current):
            output.append(math.nan)
            continue
        window = values.iloc[max(0, index - lookback + 1) : index + 1].dropna()
        output.append(100.0 * float((window <= current).sum()) / len(window))
    return pd.Series(output, index=values.index, dtype=float)


def generate_r1_r2_candidates(
    h1_bars: Sequence[Mapping[str, Any]], contract: Mapping[str, Any]
) -> list[Candidate]:
    offset = int(contract["server_time"]["utc_offset_hours"])
    h1 = indicator_frame(h1_bars)
    h4 = indicator_frame(
        aggregate_h1_bidask_bars(h1_bars, width_hours=4, utc_offset_hours=offset)
    )
    d1 = indicator_frame(
        aggregate_h1_bidask_bars(h1_bars, width_hours=24, utc_offset_hours=offset)
    )
    if h1.empty or h4.empty or d1.empty:
        return []
    h1_available = _available_values(h1)
    h4_available = _available_values(h4)
    d1_available = _available_values(d1)
    output: list[Candidate] = []

    for index in range(len(h4) - 1):
        decision_ms = int(h4.iloc[index]["available_timestamp_ms"])
        h1_index = _latest_available_index(h1_available, decision_ms)
        d1_index = _latest_available_index(d1_available, decision_ms)
        if h1_index < 0 or d1_index < 0:
            continue
        signal = r1_signal(h4, index, d1, d1_index)
        if signal is None or not regime_allows(
            "LONG", h1, h1_index, h4, index, d1, d1_index
        ):
            continue
        split = _window(decision_ms, contract)
        if split is not None:
            output.append(
                _candidate(R1, "LONG", h4.iloc[index], decision_ms, signal, split, contract)
            )

    for index in range(len(h1) - 1):
        decision_ms = int(h1.iloc[index]["available_timestamp_ms"])
        h4_index = _latest_available_index(h4_available, decision_ms)
        d1_index = _latest_available_index(d1_available, decision_ms)
        if h4_index < 0 or d1_index < 0:
            continue
        signal = r2_signal(h1, index)
        if signal is None or not regime_allows(
            "SHORT", h1, index, h4, h4_index, d1, d1_index
        ):
            continue
        split = _window(decision_ms, contract)
        if split is not None:
            output.append(
                _candidate(R2, "SHORT", h1.iloc[index], decision_ms, signal, split, contract)
            )
    return sorted(output, key=lambda row: (row.decision_timestamp_ms, row.direction))


def r1_signal(
    h4: pd.DataFrame, h4_index: int, d1: pd.DataFrame, d1_index: int
) -> dict[str, float] | None:
    if h4_index < 14 or d1_index < 278:
        return None
    d1_row = d1.iloc[d1_index]
    h4_row = h4.iloc[h4_index]
    if pd.isna(d1_row["atr_pct_252"]) or float(d1_row["atr_pct_252"]) > 80.0:
        return None
    box = d1.iloc[d1_index - 1 : d1_index + 1]
    box_high = float(box["bid_high"].max())
    box_low = float(box["bid_low"].min())
    box_average = (box_high - box_low) / 2.0
    if box_average > 1.5 * float(d1_row["median_range20"]):
        return None
    bar_range = float(h4_row["bid_high"] - h4_row["bid_low"])
    if bar_range <= 0.0:
        return None
    body_fraction = abs(float(h4_row["bid_close"] - h4_row["bid_open"])) / bar_range
    if (
        body_fraction < 0.35
        or float(h4_row["bid_close"]) <= box_high
        or float(h4_row["bid_close"]) <= float(h4_row["bid_open"])
        or pd.isna(h4_row["atr14"])
    ):
        return None
    stop = max(float(h4_row["bid_close"]) - box_low, float(h4_row["atr14"]), 3.5)
    return {
        "stop_distance": stop,
        "touch_distance_atr": (float(h4_row["bid_close"]) - box_high)
        / float(h4_row["atr14"]),
        "body_fraction": body_fraction,
        "close_location": (float(h4_row["bid_close"]) - float(h4_row["bid_low"]))
        / bar_range,
    }


def r2_signal(h1: pd.DataFrame, index: int) -> dict[str, float] | None:
    if index < 55:
        return None
    row = h1.iloc[index]
    required = ("ema20", "ema50", "ema20_lag5", "atr14")
    if any(pd.isna(row[name]) for name in required):
        return None
    if not (
        float(row["bid_close"]) < float(row["ema20"]) < float(row["ema50"])
        and float(row["ema20"]) <= float(row["ema20_lag5"])
    ):
        return None
    bar_range = float(row["bid_high"] - row["bid_low"])
    if bar_range <= 0.0:
        return None
    body_fraction = abs(float(row["bid_close"] - row["bid_open"])) / bar_range
    close_location = (float(row["bid_close"]) - float(row["bid_low"])) / bar_range
    if (
        float(row["bid_close"]) >= float(row["bid_open"])
        or float(row["bid_close"]) >= float(row["ema20"])
        or body_fraction < 0.35
        or close_location > 0.35
    ):
        return None
    recent = h1.iloc[index - 2 : index + 1]
    zone = 0.25 * float(row["atr14"])
    touched = any(
        (
            float(item.bid_high) >= float(row["ema20"]) - zone
            and float(item.bid_low) <= float(row["ema20"]) + zone
        )
        or (
            float(item.bid_high) >= float(row["ema50"]) - zone
            and float(item.bid_low) <= float(row["ema50"]) + zone
        )
        for item in recent.itertuples()
    )
    if not touched:
        return None
    swing_high = float(recent["bid_high"].max())
    stop = max(swing_high + 0.25 * float(row["atr14"]) - float(row["bid_close"]), 3.5)
    return {
        "stop_distance": stop,
        "touch_distance_atr": (float(row["ema20"]) - float(row["bid_close"]))
        / float(row["atr14"]),
        "body_fraction": body_fraction,
        "close_location": close_location,
    }


def regime_allows(
    direction: str,
    h1: pd.DataFrame,
    h1_index: int,
    h4: pd.DataFrame,
    h4_index: int,
    d1: pd.DataFrame,
    d1_index: int,
) -> bool:
    if h1_index < 14 or h4_index < 55 or d1_index < 276:
        return False
    h1_row = h1.iloc[h1_index]
    d1_row = d1.iloc[d1_index]
    if any(pd.isna(value) for value in (h1_row["atr14"], d1_row["atr_pct_60"])):
        return False
    if (
        float(h1_row["bid_high"] - h1_row["bid_low"]) >= 3.0 * float(h1_row["atr14"])
        or float(d1_row["atr_pct_60"]) >= 95.0
    ):
        return False
    uptrend = direction == "LONG"
    if direction not in {"LONG", "SHORT"}:
        return False
    if not all(trend_stack(d1.iloc[index], uptrend) for index in (d1_index, d1_index - 1)):
        return False
    if not trend_stack(h4.iloc[h4_index], uptrend):
        return False
    if uptrend and not (
        float(d1_row["bid_close"]) > float(d1_row["ema20"])
        and float(d1_row["ema20"]) >= float(d1_row["ema20_lag5"])
    ):
        return False
    return True


def trend_stack(row: Mapping[str, Any], uptrend: bool) -> bool:
    names = ("bid_close", "ema20", "ema50", "ema20_lag5", "ema50_lag5")
    if any(pd.isna(row[name]) for name in names):
        return False
    close, fast, slow, fast_prior, slow_prior = (float(row[name]) for name in names)
    if uptrend:
        return close > fast > slow and fast >= fast_prior and slow >= slow_prior
    return close < fast < slow and fast <= fast_prior and slow <= slow_prior


def _candidate(
    family: str,
    direction: str,
    row: Mapping[str, Any],
    decision_ms: int,
    signal: Mapping[str, float],
    split: str,
    contract: Mapping[str, Any],
) -> Candidate:
    stop = float(signal["stop_distance"])
    atr = float(row["atr14"])
    identity = f"{family}|{contract['symbol']}|{decision_ms}|{direction}"
    return Candidate(
        candidate_id=hashlib.sha256(identity.encode("ascii")).hexdigest()[:24],
        family_id=family,
        symbol=str(contract["symbol"]),
        split=split,
        direction=direction,
        signal_bar_start_utc=_iso_ms(int(row["timestamp_ms"])),
        decision_time_utc=_iso_ms(decision_ms),
        decision_timestamp_ms=decision_ms,
        signal_open=float(row["bid_open"]),
        signal_high=float(row["bid_high"]),
        signal_low=float(row["bid_low"]),
        signal_close=float(row["bid_close"]),
        ema_fast=float(row["ema20"]),
        ema_slow=float(row["ema50"]),
        ema_fast_slope_atr=(float(row["ema20"]) - float(row["ema20_lag5"])) / atr,
        atr=atr,
        body_fraction=float(signal["body_fraction"]),
        close_location=float(signal["close_location"]),
        touch_distance_atr=float(signal["touch_distance_atr"]),
        stop_distance=stop,
        stop_distance_atr=stop / atr,
        reward_r=2.0,
        signal_tick_count=int(row["tick_count"]),
    )


def apply_specialist_controls(
    labels: Sequence[Any],
    candidates: Mapping[str, Candidate],
    contract: Mapping[str, Any],
) -> tuple[list[Any], dict[str, int]]:
    execution = contract["execution"]
    controls = contract["specialist_controls"]
    point = float(execution["point_size"])
    maximum_spread = int(execution["maximum_spread_points"]) * point
    maximum_cost_r = float(execution["maximum_estimated_cost_r"])
    offset = int(contract["server_time"]["utc_offset_hours"])
    active: dict[str, list[datetime]] = defaultdict(list)
    daily: Counter[tuple[str, str]] = Counter()
    reasons: Counter[str] = Counter()
    selected: list[Any] = []
    resolved = sorted(
        (row for row in labels if row.status == "RESOLVED"),
        key=lambda row: (row.entry_time_utc, row.candidate_id),
    )
    for label in resolved:
        candidate = candidates[label.candidate_id]
        family = candidate.family_id
        rule = controls[family]
        entry = _parse_utc(label.entry_time_utc)
        exit_time = _parse_utc(label.exit_time_utc)
        active[family] = [value for value in active[family] if value > entry]
        if float(label.entry_spread) > maximum_spread + 1e-9:
            reasons["spread_too_high"] += 1
            continue
        if float(label.entry_spread) / candidate.stop_distance > maximum_cost_r + 1e-12:
            reasons["estimated_cost_r_too_high"] += 1
            continue
        ceiling = int(rule["stop_ceiling_points"])
        if ceiling > 0 and candidate.stop_distance / point > ceiling + 1e-9:
            reasons["stop_ceiling_exceeded"] += 1
            continue
        day = (entry + timedelta(hours=offset)).date().isoformat()
        key = (family, day)
        if daily[key] >= int(rule["maximum_trades_per_server_day"]):
            reasons["daily_trade_cap_reached"] += 1
            continue
        if len(active[family]) >= int(rule["maximum_open_positions"]):
            reasons["max_open_positions_reached"] += 1
            continue
        selected.append(label)
        daily[key] += 1
        active[family].append(exit_time)
    reasons["unresolved_or_ineligible"] = len(labels) - len(resolved)
    return selected, dict(reasons)


def build_report(
    phase1_root: Path,
    contract: Mapping[str, Any],
    contract_file: Path,
    source_audits: Sequence[Mapping[str, Any]],
    candidates: Sequence[Candidate],
    raw_labels: Sequence[Any],
    selected: Sequence[Any],
    selection_reasons: Mapping[str, int],
    outputs: Mapping[str, Path],
) -> dict[str, Any]:
    windows = ("historical_backcast", "recent_cross_feed")
    families = (R1, R2)
    evidence = {
        window: {
            "portfolio": trade_stats([row for row in selected if row.split == window]),
            "specialists": {
                family: trade_stats(
                    [row for row in selected if row.split == window and row.family_id == family]
                )
                for family in families
            },
        }
        for window in windows
    }
    concentration = {
        family: episode_stats([row for row in selected if row.family_id == family])
        for family in families
    }
    stability = stability_stats(selected, contract)
    reconciliation = reference_reconciliation(phase1_root, selected, contract)
    gates = portability_gates(evidence, concentration, stability, reconciliation, contract)
    quality = {
        "source_months_eq_120": len(source_audits) == int(contract["period"]["expected_months"]),
        "candidate_ids_unique": len({row.candidate_id for row in candidates}) == len(candidates),
        "all_selected_entries_not_before_decision": all(
            row.entry_time_utc >= row.decision_time_utc for row in selected
        ),
        "all_selected_resolved": all(row.status == "RESOLVED" for row in selected),
    }
    passed = all(quality.values()) and all(gates.values())
    return {
        "schema_version": contract["schema_version"],
        "generated_at_utc": datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "classification": "PORTABILITY_PASS" if passed else "PORTABILITY_FAIL",
        "contract": str(contract_file.relative_to(phase1_root)).replace("\\", "/"),
        "contract_sha256": _sha256_file(contract_file),
        "source_months": len(source_audits),
        "raw_candidates": len(candidates),
        "raw_labels": len(raw_labels),
        "selected_trades": len(selected),
        "selection_reasons": dict(selection_reasons),
        "evidence": evidence,
        "concentration": concentration,
        "stability": stability,
        "reference_reconciliation": reconciliation,
        "quality_gates": quality,
        "portability_gates": gates,
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
            "MT5 outcomes through 2026-06 are already known, so this is cross-feed evidence rather than an untouched holdout.",
            "EMA and ATR calculations causally reproduce the EA formulas but broker session microstructure can shift candidate timestamps.",
            "A portability pass advances research only and does not authorize demo or broker action.",
        ],
    }


def trade_stats(rows: Sequence[Any]) -> dict[str, Any]:
    ordered = sorted(rows, key=lambda row: (row.exit_time_utc, row.candidate_id))
    pnl = [float(row.stress_net_pnl_usd) for row in ordered]
    gross_profit = sum(value for value in pnl if value > 0.0)
    gross_loss = -sum(value for value in pnl if value < 0.0)
    net = sum(pnl)
    return {
        "trades": len(rows),
        "wins": sum(value > 0.0 for value in pnl),
        "win_rate_pct": 100.0 * sum(value > 0.0 for value in pnl) / len(pnl) if pnl else 0.0,
        "stress_net_usd": net,
        "stress_profit_factor": gross_profit / gross_loss if gross_loss > 0.0 else None,
        "average_stress_r": sum(float(row.stress_net_r) for row in ordered) / len(rows)
        if rows
        else 0.0,
        "max_closed_drawdown_usd": max_drawdown(pnl),
        "closed_drawdown_to_net_ratio": max_drawdown(pnl) / net if net > 0.0 else None,
    }


def episode_stats(rows: Sequence[Any]) -> dict[str, Any]:
    ordered = sorted(rows, key=lambda row: (row.entry_time_utc, row.candidate_id))
    episodes: list[dict[str, Any]] = []
    for row in ordered:
        entry = _parse_utc(row.entry_time_utc)
        exit_time = _parse_utc(row.exit_time_utc)
        pnl = float(row.stress_net_pnl_usd)
        if not episodes or entry > episodes[-1]["end"]:
            episodes.append({"start": entry, "end": exit_time, "trades": 1, "net": pnl})
        else:
            episodes[-1]["end"] = max(episodes[-1]["end"], exit_time)
            episodes[-1]["trades"] += 1
            episodes[-1]["net"] += pnl
    net = sum(row["net"] for row in episodes)
    winners = sorted((row["net"] for row in episodes if row["net"] > 0.0), reverse=True)
    return {
        "episodes": len(episodes),
        "net_usd": net,
        "top_episode_profit_share": winners[0] / net if winners and net > 0.0 else None,
        "top_three_episodes_removed_net_usd": net - sum(winners[:3]),
        "largest_episode_trades": max((row["trades"] for row in episodes), default=0),
    }


def stability_stats(rows: Sequence[Any], contract: Mapping[str, Any]) -> dict[str, Any]:
    pnl_by_month: defaultdict[str, float] = defaultdict(float)
    for row in rows:
        pnl_by_month[row.exit_time_utc[:7]] += float(row.stress_net_pnl_usd)
    months = [f"{year:04d}-{month:02d}" for year, month in _month_range(
        contract["period"]["start_month"], contract["period"]["end_month"]
    )]
    year_values: defaultdict[str, float] = defaultdict(float)
    for month in months:
        year_values[month[:4]] += pnl_by_month[month]
    six_month = [sum(pnl_by_month[month] for month in months[index : index + 6]) for index in range(len(months) - 5)]
    return {
        "calendar_years": len(year_values),
        "positive_calendar_year_share": sum(value > 0.0 for value in year_values.values())
        / len(year_values),
        "rolling_six_month_blocks": len(six_month),
        "positive_six_month_block_share": sum(value > 0.0 for value in six_month) / len(six_month),
    }


def reference_reconciliation(
    phase1_root: Path, rows: Sequence[Any], contract: Mapping[str, Any]
) -> dict[str, Any]:
    offset = timedelta(hours=int(contract["server_time"]["utc_offset_hours"]))
    result: dict[str, Any] = {}
    for family, relative in contract["reference_trade_paths"].items():
        with (phase1_root / relative).open("r", encoding="utf-8-sig", newline="") as handle:
            reference = list(csv.DictReader(handle))
        reference_times = sorted(
            datetime.strptime(row["entry_time"], "%Y.%m.%d %H:%M:%S").replace(tzinfo=UTC)
            - offset
            for row in reference
        )
        observed = sorted(_parse_utc(row.entry_time_utc) for row in rows if row.family_id == family)
        deltas = []
        for value in observed:
            index = bisect.bisect_left(reference_times, value)
            nearby = reference_times[max(0, index - 1) : min(len(reference_times), index + 1)]
            if nearby:
                deltas.append(min(abs((value - other).total_seconds()) for other in nearby) / 60.0)
        result[family] = {
            "reference_trades": len(reference_times),
            "dukascopy_selected_trades": len(observed),
            "count_ratio": len(observed) / len(reference_times) if reference_times else None,
            "nearest_timestamp_median_delta_minutes": percentile(sorted(deltas), 0.5)
            if deltas
            else None,
        }
    return result


def portability_gates(
    evidence: Mapping[str, Any],
    concentration: Mapping[str, Any],
    stability: Mapping[str, Any],
    reconciliation: Mapping[str, Any],
    contract: Mapping[str, Any],
) -> dict[str, bool]:
    gates = contract["portability_gates"]
    families = (R1, R2)
    return {
        "portfolio_stress_pf_each_window": all(
            (evidence[window]["portfolio"]["stress_profit_factor"] or 0.0)
            >= float(gates["minimum_portfolio_stress_profit_factor_each_window"])
            for window in evidence
        ),
        "specialist_stress_pf_each_window": all(
            (evidence[window]["specialists"][family]["stress_profit_factor"] or 0.0)
            >= float(gates["minimum_specialist_stress_profit_factor_each_window"])
            for window in evidence
            for family in families
        ),
        "specialist_stress_net_positive_each_window": all(
            evidence[window]["specialists"][family]["stress_net_usd"] > 0.0
            for window in evidence
            for family in families
        ),
        "drawdown_to_net_each_window": all(
            evidence[window]["portfolio"]["closed_drawdown_to_net_ratio"] is not None
            and evidence[window]["portfolio"]["closed_drawdown_to_net_ratio"]
            <= float(gates["maximum_closed_drawdown_to_net_ratio"])
            for window in evidence
        ),
        "positive_calendar_year_share": stability["positive_calendar_year_share"]
        >= float(gates["minimum_positive_calendar_year_share"]),
        "positive_six_month_block_share": stability["positive_six_month_block_share"]
        >= float(gates["minimum_positive_six_month_block_share"]),
        "episode_concentration": all(
            concentration[family]["top_episode_profit_share"] is not None
            and concentration[family]["top_episode_profit_share"]
            <= float(gates["maximum_top_episode_profit_share"])
            for family in families
        ),
        "top_three_episodes_removed_net_positive": all(
            concentration[family]["top_three_episodes_removed_net_usd"] > 0.0
            for family in families
        ),
        "reference_count_ratio": all(
            reconciliation[family]["count_ratio"] is not None
            and float(gates["minimum_candidate_count_ratio_to_mt5"])
            <= reconciliation[family]["count_ratio"]
            <= float(gates["maximum_candidate_count_ratio_to_mt5"])
            for family in families
        ),
        "reference_timestamp_delta": all(
            reconciliation[family]["nearest_timestamp_median_delta_minutes"] is not None
            and reconciliation[family]["nearest_timestamp_median_delta_minutes"]
            <= float(gates["maximum_candidate_timestamp_median_delta_minutes"])
            for family in families
        ),
    }


def render_report(payload: Mapping[str, Any]) -> str:
    lines = [
        "# A3 ML R1/R2 Dukascopy Portability V1",
        "",
        f"Classification: `{payload['classification']}`",
        "",
        "Cross-feed research only. Demo prediction, EA consumption, and broker action remain disabled.",
        "",
        "## Evidence",
        "",
        "| Window | Scope | Trades | Stress net | PF | Win rate | Closed DD |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for window, group in payload["evidence"].items():
        for scope, row in [("portfolio", group["portfolio"]), *group["specialists"].items()]:
            lines.append(
                f"| {window} | {scope} | {row['trades']} | {row['stress_net_usd']:.2f} | "
                f"{(row['stress_profit_factor'] or 0.0):.4f} | {row['win_rate_pct']:.2f}% | "
                f"{row['max_closed_drawdown_usd']:.2f} |"
            )
    lines.extend(["", "## Gates", ""])
    for name, passed in {**payload["quality_gates"], **payload["portability_gates"]}.items():
        lines.append(f"- `{name}`: {'PASS' if passed else 'FAIL'}")
    lines.extend(["", "No demo or broker authorization was changed.", ""])
    return "\n".join(lines)


def _window(timestamp_ms: int, contract: Mapping[str, Any]) -> str | None:
    value = datetime.fromtimestamp(timestamp_ms / 1000, UTC)
    recent = _parse_utc(contract["windows"]["recent_cross_feed_start_utc"])
    end = _parse_utc(contract["windows"]["recent_cross_feed_end_exclusive_utc"])
    if value < recent:
        return "historical_backcast"
    if value < end:
        return "recent_cross_feed"
    return None


def _available_values(frame: pd.DataFrame) -> list[int]:
    return [int(value) for value in frame["available_timestamp_ms"].dropna()]


def _latest_available_index(values: Sequence[int], decision_ms: int) -> int:
    return bisect.bisect_right(values, decision_ms) - 1


def max_drawdown(values: Sequence[float]) -> float:
    equity = peak = maximum = 0.0
    for value in values:
        equity += value
        peak = max(peak, equity)
        maximum = max(maximum, peak - equity)
    return maximum


def percentile(values: Sequence[float], probability: float) -> float:
    if not values:
        raise ValueError("cannot calculate percentile of empty values")
    position = probability * (len(values) - 1)
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return float(values[lower])
    weight = position - lower
    return float(values[lower] * (1.0 - weight) + values[upper] * weight)


def _iso_ms(timestamp_ms: int) -> str:
    return datetime.fromtimestamp(timestamp_ms / 1000, UTC).isoformat(
        timespec="milliseconds"
    ).replace("+00:00", "Z")
