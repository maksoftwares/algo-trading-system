from __future__ import annotations

import bisect
import hashlib
import json
import math
import os
import random
from collections import Counter, defaultdict
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Mapping, Sequence

import pandas as pd

from ml.a3_meta_v1.dukascopy_label_factory import (
    DAY_MS,
    HOUR_MS,
    Candidate,
    VerifiedTickStore,
    _load_foundation,
    _month_range,
    _sha256_file,
    _split_for_timestamp,
    _validate_candidates,
    _write_rows,
    prepare_verified_h1_bars,
    replay_candidates,
)


DEFAULT_CONTRACT = Path("config/ml/a3_ml_dukascopy_compression_breakout.json")


class CompressionBreakoutError(RuntimeError):
    pass


def run_dukascopy_compression_breakout(
    root: Path, contract_path: Path | None = None
) -> Path:
    root = root.resolve()
    contract_file = (contract_path or root / DEFAULT_CONTRACT).resolve()
    contract = json.loads(contract_file.read_text(encoding="utf-8"))
    _validate_contract(contract)
    storage_root = _resolve_storage_root(contract)
    external_root = storage_root / str(contract["external_output_subdirectory"])
    foundation = _load_foundation(root.parents[1])
    months = _month_range(contract["period"]["start_month"], contract["period"]["end_month"])
    h1_bars, source_audits = prepare_verified_h1_bars(
        storage_root,
        external_root / "bars",
        str(contract["symbol"]),
        months,
        foundation,
    )
    h4_bars = aggregate_h1_bid_bars(
        h1_bars,
        width_hours=4,
        minimum_active_hours=int(contract["strategy"]["minimum_active_h1_bars_per_h4"]),
    )
    d1_bars = aggregate_h1_bid_bars(
        h1_bars,
        width_hours=24,
        minimum_active_hours=int(contract["strategy"]["minimum_active_h1_bars_per_d1"]),
    )
    candidates = generate_compression_breakout_candidates(h4_bars, d1_bars, contract)
    _validate_candidates(candidates)
    store = VerifiedTickStore(
        storage_root=storage_root,
        symbol=str(contract["symbol"]),
        foundation=foundation,
        prevalidated_months=set(months),
    )
    labels = replay_candidates(candidates, h1_bars, store, contract)

    outputs = {key: (root / value).resolve() for key, value in contract["outputs"].items()}
    _write_rows(outputs["candidates_csv"], [asdict(row) for row in candidates])
    _write_rows(outputs["labels_csv"], [asdict(row) for row in labels])
    payload = _build_report(
        contract=contract,
        contract_file=contract_file,
        storage_root=storage_root,
        source_audits=source_audits,
        h1_bars=h1_bars,
        h4_bars=h4_bars,
        d1_bars=d1_bars,
        candidates=candidates,
        labels=labels,
        outputs=outputs,
    )
    outputs["report_json"].write_text(json.dumps(payload, indent=2), encoding="utf-8")
    outputs["report_markdown"].write_text(_render(payload), encoding="utf-8")
    return outputs["report_json"]


def aggregate_h1_bid_bars(
    h1_bars: Sequence[Mapping[str, Any]],
    *,
    width_hours: int,
    minimum_active_hours: int,
) -> list[dict[str, Any]]:
    if width_hours not in {4, 24}:
        raise ValueError("compression breakout supports H4 and D1 aggregation only")
    width_ms = width_hours * HOUR_MS
    groups: dict[int, list[Mapping[str, Any]]] = defaultdict(list)
    for row in h1_bars:
        timestamp = int(row["timestamp_ms"])
        groups[timestamp - timestamp % width_ms].append(row)
    output = []
    for timestamp, rows in sorted(groups.items()):
        ordered = sorted(rows, key=lambda row: int(row["timestamp_ms"]))
        if len(ordered) < minimum_active_hours:
            continue
        output.append(
            {
                "timestamp_ms": timestamp,
                "open": float(ordered[0]["bid_open"]),
                "high": max(float(row["bid_high"]) for row in ordered),
                "low": min(float(row["bid_low"]) for row in ordered),
                "close": float(ordered[-1]["bid_close"]),
                "tick_count": sum(int(row["tick_count"]) for row in ordered),
                "active_h1_bars": len(ordered),
            }
        )
    return output


def generate_compression_breakout_candidates(
    h4_bars: Sequence[Mapping[str, Any]],
    d1_bars: Sequence[Mapping[str, Any]],
    contract: Mapping[str, Any],
) -> list[Candidate]:
    strategy = contract["strategy"]
    h4 = _indicator_frame(h4_bars, int(strategy["h4_atr_period"]), ema_period=None)
    d1 = _indicator_frame(
        d1_bars,
        int(strategy["d1_atr_period"]),
        ema_period=int(strategy["d1_trend_ema_period"]),
    )
    if h4.empty or d1.empty:
        return []
    slope_lag = int(strategy["d1_trend_slope_lag_bars"])
    median_lookback = int(strategy["d1_range_median_lookback"])
    percentile_lookback = int(strategy["d1_atr_percentile_lookback"])
    d1["ema_prior"] = d1["ema"].shift(slope_lag)
    d1["median_range"] = (d1["high"] - d1["low"]).rolling(
        median_lookback, min_periods=median_lookback
    ).median()
    d1["atr_percentile"] = d1["atr"].rolling(
        percentile_lookback, min_periods=percentile_lookback
    ).apply(lambda values: 100.0 * float((values <= values[-1]).sum()) / len(values), raw=True)

    d1_end_ms = [int(value) + DAY_MS for value in d1["timestamp_ms"]]
    box_days = int(strategy["d1_box_days"])
    output: list[Candidate] = []
    for index in range(1, len(h4)):
        row = h4.iloc[index]
        previous = h4.iloc[index - 1]
        decision_ms = int(row["timestamp_ms"]) + 4 * HOUR_MS
        d1_index = bisect.bisect_right(d1_end_ms, decision_ms) - 1
        if d1_index < max(box_days - 1, slope_lag, percentile_lookback - 1):
            continue
        daily = d1.iloc[d1_index]
        required = ("atr", "ema", "ema_prior", "median_range", "atr_percentile")
        if any(pd.isna(daily[name]) for name in required) or pd.isna(row["atr"]):
            continue
        if float(daily["atr_percentile"]) > float(strategy["d1_atr_percentile_maximum"]):
            continue
        box = d1.iloc[d1_index - box_days + 1 : d1_index + 1]
        box_high = float(box["high"].max())
        box_low = float(box["low"].min())
        box_average = (box_high - box_low) / box_days
        median_range = float(daily["median_range"])
        if median_range <= 0.0 or box_average > float(
            strategy["d1_box_average_to_median_maximum"]
        ) * median_range:
            continue

        h4_range = float(row["high"] - row["low"])
        h4_atr = float(row["atr"])
        if h4_range <= 0.0 or h4_atr <= 0.0:
            continue
        body_fraction = abs(float(row["close"] - row["open"])) / h4_range
        if body_fraction < float(strategy["h4_minimum_body_fraction"]):
            continue
        close_location = float(row["close"] - row["low"]) / h4_range
        ema = float(daily["ema"])
        ema_prior = float(daily["ema_prior"])
        direction = ""
        if (
            float(daily["close"]) > ema
            and ema >= ema_prior
            and float(row["close"]) > float(row["open"])
            and float(row["close"]) > box_high
            and float(previous["close"]) <= box_high
        ):
            direction = "LONG"
            stop_distance = max(float(row["close"]) - box_low, h4_atr)
            breakout_distance = float(row["close"]) - box_high
        elif (
            float(daily["close"]) < ema
            and ema <= ema_prior
            and float(row["close"]) < float(row["open"])
            and float(row["close"]) < box_low
            and float(previous["close"]) >= box_low
        ):
            direction = "SHORT"
            stop_distance = max(box_high - float(row["close"]), h4_atr)
            breakout_distance = box_low - float(row["close"])
        else:
            continue
        if stop_distance / h4_atr > float(strategy["maximum_stop_h4_atr"]):
            continue
        decision = datetime.fromtimestamp(decision_ms / 1000, UTC)
        split = _split_for_timestamp(decision, contract["splits"])
        if split is None:
            continue
        family_id = str(strategy["family_id"])
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
                signal_open=float(row["open"]),
                signal_high=float(row["high"]),
                signal_low=float(row["low"]),
                signal_close=float(row["close"]),
                ema_fast=ema,
                ema_slow=ema_prior,
                ema_fast_slope_atr=(ema - ema_prior) / float(daily["atr"]),
                atr=h4_atr,
                body_fraction=body_fraction,
                close_location=close_location,
                touch_distance_atr=breakout_distance / h4_atr,
                stop_distance=stop_distance,
                stop_distance_atr=stop_distance / h4_atr,
                reward_r=float(strategy["reward_r"]),
                signal_tick_count=int(row["tick_count"]),
            )
        )
    return output


def _indicator_frame(
    bars: Sequence[Mapping[str, Any]], atr_period: int, ema_period: int | None
) -> pd.DataFrame:
    frame = pd.DataFrame(bars).copy()
    if frame.empty:
        return frame
    for name in ("timestamp_ms", "tick_count"):
        frame[name] = pd.to_numeric(frame[name], errors="raise").astype("int64")
    for name in ("open", "high", "low", "close"):
        frame[name] = pd.to_numeric(frame[name], errors="raise").astype(float)
    frame = frame.sort_values("timestamp_ms").reset_index(drop=True)
    previous_close = frame["close"].shift(1)
    true_range = pd.concat(
        [
            frame["high"] - frame["low"],
            (frame["high"] - previous_close).abs(),
            (frame["low"] - previous_close).abs(),
        ],
        axis=1,
    ).max(axis=1)
    frame["atr"] = true_range.ewm(
        alpha=1.0 / atr_period, adjust=False, min_periods=atr_period
    ).mean()
    if ema_period is not None:
        frame["ema"] = frame["close"].ewm(
            span=ema_period, adjust=False, min_periods=ema_period
        ).mean()
    return frame


def _build_report(
    *,
    contract: Mapping[str, Any],
    contract_file: Path,
    storage_root: Path,
    source_audits: Sequence[Mapping[str, Any]],
    h1_bars: Sequence[Mapping[str, Any]],
    h4_bars: Sequence[Mapping[str, Any]],
    d1_bars: Sequence[Mapping[str, Any]],
    candidates: Sequence[Candidate],
    labels: Sequence[Any],
    outputs: Mapping[str, Path],
) -> dict[str, Any]:
    resolved = [row for row in labels if row.status == "RESOLVED"]
    eligible = [row for row in labels if row.status != "INELIGIBLE"]
    by_split = {
        name: _stats([row for row in resolved if row.split == name])
        for name in ("train", "validation", "test")
    }
    by_direction = {
        name: _stats([row for row in resolved if row.direction == name])
        for name in ("LONG", "SHORT")
    }
    quality = contract["quality_gates"]
    quality_gates = {
        "verified_months_eq_expected": len(source_audits) == int(quality["expected_months"]),
        "candidates_ge_minimum": len(candidates) >= int(quality["minimum_candidates"]),
        "resolved_share_ge_minimum": len(resolved) / len(eligible) >= float(quality["minimum_resolved_share"]) if eligible else False,
        "each_split_rows_ge_minimum": all(row["trades"] >= int(quality["minimum_resolved_rows_per_split"]) for row in by_split.values()),
        "each_direction_rows_ge_minimum": all(row["trades"] >= int(quality["minimum_resolved_rows_per_direction"]) for row in by_direction.values()),
        "candidate_ids_unique": len({row.candidate_id for row in candidates}) == len(candidates),
        "candidate_keys_unique": len({(row.family_id, row.decision_timestamp_ms, row.direction) for row in candidates}) == len(candidates),
    }
    bootstrap = _month_bootstrap(
        [row for row in resolved if row.split == "test"],
        samples=int(contract["bootstrap"]["calendar_month_samples"]),
        seed=int(contract["bootstrap"]["seed"]),
    )
    configured = contract["strategy_gates"]
    test_directions = Counter(row.direction for row in resolved if row.split == "test")
    strategy_gates = {
        "train_pf_ge_minimum": (by_split["train"]["stress_profit_factor"] or 0.0) >= float(configured["minimum_train_stress_profit_factor"]),
        "validation_pf_ge_minimum": (by_split["validation"]["stress_profit_factor"] or 0.0) >= float(configured["minimum_validation_stress_profit_factor"]),
        "test_pf_ge_minimum": (by_split["test"]["stress_profit_factor"] or 0.0) >= float(configured["minimum_test_stress_profit_factor"]),
        "train_average_r_ge_minimum": by_split["train"]["average_stress_r"] >= float(configured["minimum_train_average_stress_r"]),
        "validation_average_r_ge_minimum": by_split["validation"]["average_stress_r"] >= float(configured["minimum_validation_average_stress_r"]),
        "test_average_r_ge_minimum": by_split["test"]["average_stress_r"] >= float(configured["minimum_test_average_stress_r"]),
        "test_drawdown_r_lte_maximum": by_split["test"]["max_closed_drawdown_r"] <= float(configured["maximum_test_closed_drawdown_r"]),
        "validation_positive_month_share_ge_minimum": by_split["validation"]["positive_exit_month_share"] >= float(configured["minimum_validation_positive_exit_month_share"]),
        "test_positive_month_share_ge_minimum": by_split["test"]["positive_exit_month_share"] >= float(configured["minimum_test_positive_exit_month_share"]),
        "test_each_direction_rows_ge_minimum": all(test_directions.get(direction, 0) >= int(configured["minimum_test_rows_each_direction"]) for direction in ("LONG", "SHORT")),
        "test_average_r_bootstrap_p025_above_zero": bootstrap.get("average_stress_r_p025") is not None and float(bootstrap["average_stress_r_p025"]) > 0.0,
    }
    quality_pass = all(quality_gates.values())
    if not quality_pass:
        classification = "DUKASCOPY_COMPRESSION_BREAKOUT_INVALID"
    elif all(strategy_gates.values()):
        classification = "DUKASCOPY_COMPRESSION_BREAKOUT_RESEARCH_SURVIVOR"
    else:
        classification = "DUKASCOPY_COMPRESSION_BREAKOUT_NO_SURVIVOR"
    source_hash = _sha256_json(
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
        "source_composite_sha256": source_hash,
        "bar_counts": {"H1": len(h1_bars), "H4": len(h4_bars), "D1": len(d1_bars)},
        "candidate_count": len(candidates),
        "eligible_candidate_count": len(eligible),
        "resolved_count": len(resolved),
        "resolved_share": len(resolved) / len(eligible) if eligible else 0.0,
        "ineligible_reasons": dict(Counter(row.exit_reason for row in labels if row.status == "INELIGIBLE")),
        "unresolved_reasons": dict(Counter(row.exit_reason for row in labels if row.status == "UNRESOLVED")),
        "all": _stats(resolved),
        "by_split": by_split,
        "by_direction": by_direction,
        "test_calendar_month_bootstrap": bootstrap,
        "quality_gates": quality_gates,
        "strategy_gates": strategy_gates,
        "artifacts": {
            key: {"path": str(path), "sha256": _sha256_file(path)}
            for key, path in outputs.items()
            if key in {"candidates_csv", "labels_csv"}
        },
        "authorization": {
            **contract["authorization"],
            "strategy_promotion_authorized": False,
        },
        "limitations": [
            "Fixed-lot candidate labels are not a shared-account portfolio simulation.",
            "Dukascopy-to-broker feed differences still require shadow and demo calibration.",
            "A research survivor would require cost, overlap, Monte Carlo, portfolio, and forward gates.",
        ],
    }


def _stats(rows: Sequence[Any]) -> dict[str, Any]:
    ordered = sorted(rows, key=lambda row: (row.exit_time_utc, row.candidate_id))
    pnl = [float(row.stress_net_pnl_usd) for row in ordered]
    returns = [float(row.stress_net_r) for row in ordered]
    gross_profit = sum(value for value in pnl if value > 0.0)
    gross_loss = -sum(value for value in pnl if value < 0.0)
    months = defaultdict(float)
    for row in ordered:
        months[row.exit_time_utc[:7]] += float(row.stress_net_pnl_usd)
    positive_months = sum(value > 0.0 for value in months.values())
    return {
        "trades": len(ordered),
        "wins": sum(value > 0.0 for value in pnl),
        "win_rate_pct": 100.0 * sum(value > 0.0 for value in pnl) / len(pnl) if pnl else 0.0,
        "stress_net_usd": sum(pnl),
        "stress_profit_factor": gross_profit / gross_loss if gross_loss > 0.0 else None,
        "average_stress_r": sum(returns) / len(returns) if returns else 0.0,
        "max_closed_drawdown_r": _max_drawdown(returns),
        "active_exit_months": len(months),
        "positive_exit_months": positive_months,
        "positive_exit_month_share": positive_months / len(months) if months else 0.0,
    }


def _month_bootstrap(rows: Sequence[Any], *, samples: int, seed: int) -> dict[str, Any]:
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


def _render(payload: Mapping[str, Any]) -> str:
    lines = [
        "# A3 ML Dukascopy D1 Compression H4 Breakout V1",
        "",
        f"Classification: `{payload['classification']}`",
        "",
        "Historical Dukascopy research only. No demo or broker action is authorized.",
        "",
        "## Population",
        "",
        f"- Candidates: `{payload['candidate_count']}`",
        f"- Eligible candidates: `{payload['eligible_candidate_count']}`",
        f"- Resolved: `{payload['resolved_count']}` ({payload['resolved_share'] * 100.0:.2f}%)",
        "",
        "## Chronological Evidence",
        "",
        "| Split | Trades | Win rate | Stress net USD | Stress PF | Average stress R | Max DD R | Positive months |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for split in ("train", "validation", "test"):
        row = payload["by_split"][split]
        lines.append(
            f"| {split} | {row['trades']} | {row['win_rate_pct']:.2f}% | {row['stress_net_usd']:.2f} | "
            f"{(row['stress_profit_factor'] or 0.0):.4f} | {row['average_stress_r']:.4f} | "
            f"{row['max_closed_drawdown_r']:.2f} | {row['positive_exit_months']}/{row['active_exit_months']} |"
        )
    lines.extend(["", "## Quality Gates", ""])
    for name, passed in payload["quality_gates"].items():
        lines.append(f"- `{name}`: {'PASS' if passed else 'FAIL'}")
    lines.extend(["", "## Strategy Gates", ""])
    for name, passed in payload["strategy_gates"].items():
        lines.append(f"- `{name}`: {'PASS' if passed else 'FAIL'}")
    bootstrap = payload["test_calendar_month_bootstrap"]
    lines.extend(
        [
            "",
            f"Test month-bootstrap average-R interval: `{bootstrap['average_stress_r_p025']}` to `{bootstrap['average_stress_r_p975']}`.",
            "",
            "Strategy promotion, demo prediction, EA consumption, and broker action remain disabled.",
            "",
        ]
    )
    return "\n".join(lines)


def _validate_contract(contract: Mapping[str, Any]) -> None:
    if contract.get("schema_version") != "a3_ml_dukascopy_compression_breakout_v1":
        raise ValueError("unexpected compression-breakout contract version")
    if contract.get("symbol") != "XAUUSD":
        raise ValueError("compression breakout V1 is locked to XAUUSD")
    if not contract["authorization"].get("research_only"):
        raise ValueError("compression breakout must remain research-only")
    if any(contract["authorization"].get(key) for key in ("python_demo_predictions_authorized", "ea_consumption_authorized", "broker_action_authorized")):
        raise ValueError("compression-breakout contract contains forbidden authorization")
    if int(contract["strategy"]["d1_atr_percentile_lookback"]) != 252:
        raise ValueError("compression breakout V1 requires the frozen 252-day percentile")
    if float(contract["strategy"]["reward_r"]) != 2.0:
        raise ValueError("compression breakout V1 requires the frozen 2R target")


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


def _sha256_json(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("ascii")
    return hashlib.sha256(payload).hexdigest()


def _iso_ms(timestamp_ms: int) -> str:
    return datetime.fromtimestamp(timestamp_ms / 1000, UTC).isoformat(timespec="milliseconds").replace(
        "+00:00", "Z"
    )
