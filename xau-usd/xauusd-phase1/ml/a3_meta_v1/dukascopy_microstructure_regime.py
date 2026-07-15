from __future__ import annotations

import csv
import hashlib
import json
import math
import os
import re
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Mapping, Sequence

import joblib
import numpy as np
import pandas as pd
import pyarrow.parquet as pq
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.metrics import roc_auc_score


DEFAULT_CONTRACT = Path("config/ml/a3_ml_dukascopy_microstructure_regime_v1.json")
BAR_WIDTH_MS = 300_000
MONTH_RE = re.compile(r"year=(\d{4})[\\/]month=(\d{2})")


class MicrostructureRegimeError(RuntimeError):
    pass


def run_dukascopy_microstructure_regime(
    root: Path,
    contract_path: Path | None = None,
    *,
    rebuild_feature_cache: bool = False,
) -> Path:
    root = root.resolve()
    contract_file = (contract_path or root / DEFAULT_CONTRACT).resolve()
    contract = json.loads(contract_file.read_text(encoding="utf-8"))
    _validate_contract(contract)
    storage_root = _resolve_storage_root(contract)
    sources = _discover_sources(storage_root, contract)
    inventory = _source_inventory(storage_root, sources)
    source_digest = _canonical_sha256(inventory)
    frame, feature_cache = _load_or_build_feature_frame(
        storage_root,
        sources,
        source_digest,
        contract,
        rebuild=rebuild_feature_cache,
    )

    windows = contract["windows"]
    train = _generate_candidates(
        frame,
        windows["train_start_utc"],
        windows["train_end_exclusive_utc"],
        contract,
        "train",
    )
    validation = _generate_candidates(
        frame,
        windows["train_end_exclusive_utc"],
        windows["validation_end_exclusive_utc"],
        contract,
        "validation",
    )
    family_metrics = _family_metrics(train)
    eligible_families = _eligible_families(family_metrics, contract)
    train = [row for row in train if row["family_id"] in eligible_families]
    validation = [row for row in validation if row["family_id"] in eligible_families]
    source_days = {
        "train": _source_days(frame, windows["train_start_utc"], windows["train_end_exclusive_utc"]),
        "validation": _source_days(frame, windows["train_end_exclusive_utc"], windows["validation_end_exclusive_utc"]),
        "internal_test": _source_days(frame, windows["validation_end_exclusive_utc"], windows["internal_test_end_exclusive_utc"]),
        "exam": _source_days(frame, windows["internal_test_end_exclusive_utc"], windows["exam_end_exclusive_utc"]),
    }

    model: HistGradientBoostingRegressor | None = None
    validation_evaluations: list[dict[str, Any]] = []
    chosen: dict[str, Any] | None = None
    prediction_rows: list[dict[str, Any]] = []
    internal_payload: dict[str, Any] | None = None
    exam_payload: dict[str, Any] | None = None

    if train and validation and eligible_families:
        feature_names = list(contract["features"])
        model = _fit_model(train, feature_names, contract["model"])
        train_scores = model.predict(_matrix(train, feature_names))
        validation_scores = model.predict(_matrix(validation, feature_names))
        validation_predictive = _predictive_metrics(validation, validation_scores)
        for fraction in contract["selection"]["train_score_top_fractions"]:
            cutoff = _top_fraction_cutoff(train_scores, float(fraction))
            selected = _portfolio_select(validation, validation_scores, cutoff, contract["selection"])
            metrics = _economic_metrics(selected, source_days["validation"])
            gates = _segment_gates(validation_predictive, metrics, contract["validation_gates"])
            validation_evaluations.append(
                {
                    "top_fraction": float(fraction),
                    "train_score_cutoff": cutoff,
                    "predictive_metrics": validation_predictive,
                    "economic_metrics": metrics,
                    "gates": gates,
                    "passes": all(gates.values()),
                }
            )
        passing = [row for row in validation_evaluations if row["passes"]]
        passing.sort(
            key=lambda row: (
                -float(row["economic_metrics"]["stress_profit_factor"] or 0.0),
                -float(row["economic_metrics"]["average_stress_r"]),
                float(row["top_fraction"]),
            )
        )
        chosen = passing[0] if passing else None
        if chosen is not None:
            chosen_selected = _portfolio_select(
                validation,
                validation_scores,
                float(chosen["train_score_cutoff"]),
                contract["selection"],
            )
            prediction_rows.extend(_prediction_rows(chosen_selected, "validation"))
            internal = _generate_candidates(
                frame,
                windows["validation_end_exclusive_utc"],
                windows["internal_test_end_exclusive_utc"],
                contract,
                "internal_test",
            )
            internal = [row for row in internal if row["family_id"] in eligible_families]
            internal_scores = model.predict(_matrix(internal, feature_names))
            internal_selected = _portfolio_select(
                internal,
                internal_scores,
                float(chosen["train_score_cutoff"]),
                contract["selection"],
            )
            internal_predictive = _predictive_metrics(internal, internal_scores)
            internal_metrics = _economic_metrics(internal_selected, source_days["internal_test"])
            internal_gates = _segment_gates(
                internal_predictive, internal_metrics, contract["test_gates"]
            )
            internal_payload = {
                "population": len(internal),
                "predictive_metrics": internal_predictive,
                "economic_metrics": internal_metrics,
                "gates": internal_gates,
                "passes": all(internal_gates.values()),
            }
            prediction_rows.extend(_prediction_rows(internal_selected, "internal_test"))
            if internal_payload["passes"]:
                exam = _generate_candidates(
                    frame,
                    windows["internal_test_end_exclusive_utc"],
                    windows["exam_end_exclusive_utc"],
                    contract,
                    "exam",
                )
                exam = [row for row in exam if row["family_id"] in eligible_families]
                exam_scores = model.predict(_matrix(exam, feature_names))
                exam_selected = _portfolio_select(
                    exam,
                    exam_scores,
                    float(chosen["train_score_cutoff"]),
                    contract["selection"],
                )
                exam_predictive = _predictive_metrics(exam, exam_scores)
                exam_metrics = _economic_metrics(exam_selected, source_days["exam"])
                exam_gates = _segment_gates(
                    exam_predictive,
                    exam_metrics,
                    contract["exam_gates"],
                    predictive_gate_required=False,
                )
                exam_payload = {
                    "population": len(exam),
                    "predictive_metrics": exam_predictive,
                    "economic_metrics": exam_metrics,
                    "gates": exam_gates,
                    "passes": all(exam_gates.values()),
                }
                prediction_rows.extend(_prediction_rows(exam_selected, "exam"))

    classification = _classification(eligible_families, chosen, internal_payload, exam_payload)
    outputs = {key: (root / value).resolve() for key, value in contract["outputs"].items()}
    for path in outputs.values():
        path.parent.mkdir(parents=True, exist_ok=True)
    model_payload = {
        "model": model,
        "features": list(contract["features"]),
        "eligible_families": eligible_families,
        "selected_policy": chosen,
        "contract_sha256": _sha256_file(contract_file),
        "source_manifest_sha256": source_digest,
    }
    joblib.dump(model_payload, outputs["model_joblib"], compress=3)
    _write_csv(outputs["family_metrics_csv"], family_metrics)
    _write_csv(outputs["evaluations_csv"], _flatten_evaluations(validation_evaluations))
    _write_csv(outputs["predictions_csv"], prediction_rows)
    payload = {
        "schema_version": contract["schema_version"],
        "classification": classification,
        "created_at_utc": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "contract": str(contract_file),
        "contract_sha256": _sha256_file(contract_file),
        "source_manifest_sha256": source_digest,
        "source_inventory": {
            "files": len(inventory),
            "bytes": sum(int(row["size_bytes"]) for row in inventory),
            "first_month": min(row["month"] for row in inventory),
            "last_month": max(row["month"] for row in inventory),
        },
        "feature_cache": feature_cache,
        "market_rows": len(frame),
        "source_days": source_days,
        "train_population_before_family_gate": sum(int(row["trades"]) for row in family_metrics),
        "validation_population_after_family_gate": len(validation),
        "family_metrics": family_metrics,
        "eligible_families": eligible_families,
        "validation_evaluations": validation_evaluations,
        "selected_validation_policy": chosen,
        "internal_test_opened": chosen is not None,
        "internal_test": internal_payload,
        "exam_opened": bool(internal_payload and internal_payload["passes"]),
        "exam": exam_payload,
        "artifacts": {
            key: {"path": str(path), "sha256": _sha256_file(path)}
            for key, path in outputs.items()
            if key != "report_json" and path.exists()
        },
        "authorization": {
            **contract["authorization"],
            "strategy_promotion_authorized": False,
            "demo_or_live_authorized": False,
        },
    }
    outputs["report_json"].write_text(json.dumps(payload, indent=2), encoding="utf-8")
    outputs["report_markdown"].write_text(_render(payload), encoding="utf-8")
    return outputs["report_json"]


def _resolve_storage_root(contract: Mapping[str, Any]) -> Path:
    name = str(contract["storage_environment_variable"])
    raw = os.environ.get(name, "").strip()
    if not raw:
        raise MicrostructureRegimeError(f"{name} is required")
    root = Path(raw).resolve()
    if not root.is_dir():
        raise MicrostructureRegimeError(f"storage root does not exist: {root}")
    return root


def _discover_sources(storage_root: Path, contract: Mapping[str, Any]) -> dict[str, list[dict[str, Any]]]:
    roles: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for cache in contract["cache_sets"]:
        cache_root = storage_root / str(cache["relative_root"])
        for month in _month_keys(str(cache["start_month"]), str(cache["end_month"])):
            year, number = month.split("-")
            expected = {
                "xau_ticks": cache_root / "normalized" / "XAUUSD" / f"year={year}" / f"month={number}" / "ticks.parquet",
            }
            for symbol in contract["instruments"]:
                bases = ("mid", "bid", "ask") if symbol == "XAUUSD" else ("mid",)
                for basis in bases:
                    expected[f"{str(symbol).lower()}_{basis}_m5"] = (
                        cache_root / "bars" / str(symbol) / basis / "M5" / f"year={year}" / f"month={number}" / "bars.parquet"
                    )
            for role, path in expected.items():
                if not path.is_file():
                    raise MicrostructureRegimeError(f"missing required {role} input: {path}")
                roles[role].append({"month": month, "path": path})
    expected_months = _month_keys(
        str(contract["cache_sets"][0]["start_month"]),
        str(contract["cache_sets"][-1]["end_month"]),
    )
    for role, rows in roles.items():
        observed = [row["month"] for row in rows]
        if observed != expected_months:
            raise MicrostructureRegimeError(f"non-contiguous or duplicate months for {role}")
    return dict(roles)


def _source_inventory(
    storage_root: Path, sources: Mapping[str, Sequence[Mapping[str, Any]]]
) -> list[dict[str, Any]]:
    rows = []
    for role in sorted(sources):
        for item in sources[role]:
            path = Path(item["path"])
            rows.append(
                {
                    "role": role,
                    "month": item["month"],
                    "path": path.relative_to(storage_root).as_posix(),
                    "size_bytes": path.stat().st_size,
                    "sha256": _sha256_file(path),
                }
            )
    return rows


def _load_or_build_feature_frame(
    storage_root: Path,
    sources: Mapping[str, Sequence[Mapping[str, Any]]],
    source_digest: str,
    contract: Mapping[str, Any],
    *,
    rebuild: bool,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    aggregation = contract["aggregation"]
    cache_path = storage_root / str(aggregation["external_feature_cache"])
    manifest_path = storage_root / str(aggregation["external_feature_manifest"])
    if not rebuild and cache_path.is_file() and manifest_path.is_file():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if (
            manifest.get("schema_version") == "a3_microstructure_feature_cache_v1"
            and manifest.get("source_manifest_sha256") == source_digest
            and manifest.get("feature_sha256") == _sha256_file(cache_path)
        ):
            frame = pq.read_table(cache_path).to_pandas()
            return frame, {**manifest, "reused": True, "path": str(cache_path)}

    tick_parts = []
    for item in sources["xau_ticks"]:
        table = pq.read_table(
            item["path"],
            columns=["timestamp_ms", "bid", "ask", "bid_volume", "ask_volume"],
        )
        part = _aggregate_tick_arrays(
            table["timestamp_ms"].combine_chunks().to_numpy(zero_copy_only=False),
            table["bid"].combine_chunks().to_numpy(zero_copy_only=False),
            table["ask"].combine_chunks().to_numpy(zero_copy_only=False),
            table["bid_volume"].combine_chunks().to_numpy(zero_copy_only=False),
            table["ask_volume"].combine_chunks().to_numpy(zero_copy_only=False),
        )
        tick_parts.append(part)
    tick_features = pd.concat(tick_parts, ignore_index=True)
    frame = tick_features
    for role in (
        "xauusd_mid_m5",
        "xauusd_bid_m5",
        "xauusd_ask_m5",
        "xagusd_mid_m5",
        "eurusd_mid_m5",
        "usdjpy_mid_m5",
    ):
        bars = _load_bars(sources[role], role)
        frame = frame.merge(bars, on="timestamp_ms", how="inner", validate="one_to_one")
    frame = _enrich_market_frame(frame, contract)
    frame = frame.replace([np.inf, -np.inf], np.nan).reset_index(drop=True)
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_parquet(cache_path, index=False, compression="zstd")
    manifest = {
        "schema_version": "a3_microstructure_feature_cache_v1",
        "source_manifest_sha256": source_digest,
        "feature_sha256": _sha256_file(cache_path),
        "rows": len(frame),
        "columns": list(frame.columns),
        "reused": False,
        "path": str(cache_path),
    }
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return frame, manifest


def _aggregate_tick_arrays(
    timestamp_ms: np.ndarray,
    bid: np.ndarray,
    ask: np.ndarray,
    bid_volume: np.ndarray,
    ask_volume: np.ndarray,
) -> pd.DataFrame:
    if not len(timestamp_ms):
        return pd.DataFrame()
    if not (
        len(timestamp_ms) == len(bid) == len(ask) == len(bid_volume) == len(ask_volume)
    ):
        raise MicrostructureRegimeError("tick arrays have different lengths")
    if np.any(np.diff(timestamp_ms) < 0) or np.any(ask < bid):
        raise MicrostructureRegimeError("invalid tick ordering or negative spread")
    bucket = timestamp_ms - timestamp_ms % BAR_WIDTH_MS
    starts = np.r_[0, np.flatnonzero(np.diff(bucket)) + 1]
    counts = np.diff(np.r_[starts, len(bucket)])
    mid = (bid + ask) / 2.0
    spread = ask - bid
    delta = np.diff(mid, prepend=mid[0])
    delta[starts] = 0.0
    signed = np.sign(delta)
    move_count = np.add.reduceat((signed != 0).astype(np.int64), starts)
    signed_move = np.add.reduceat(signed, starts)
    absolute_move = np.add.reduceat(np.abs(delta), starts)
    realized = np.add.reduceat(np.square(delta), starts)
    total_volume = bid_volume + ask_volume
    book_imbalance = np.divide(
        bid_volume - ask_volume,
        total_volume,
        out=np.zeros_like(total_volume, dtype=float),
        where=total_volume > 0,
    )
    microprice = np.divide(
        ask * bid_volume + bid * ask_volume,
        total_volume,
        out=mid.copy(),
        where=total_volume > 0,
    )
    micro_edge = np.divide(
        microprice - mid,
        spread,
        out=np.zeros_like(mid, dtype=float),
        where=spread > 0,
    )
    net_move = mid[starts + counts - 1] - mid[starts]
    return pd.DataFrame(
        {
            "timestamp_ms": bucket[starts].astype(np.int64),
            "xau_tick_count": counts.astype(np.int64),
            "xau_mid_tick_open": mid[starts],
            "xau_mid_tick_close": mid[starts + counts - 1],
            "tick_signed_move": signed_move,
            "tick_move_count": move_count,
            "tick_realized_variance": realized,
            "tick_spread_mean": np.add.reduceat(spread, starts) / counts,
            "tick_spread_last": spread[starts + counts - 1],
            "tick_spread_max": np.maximum.reduceat(spread, starts),
            "tick_book_imbalance_mean": np.add.reduceat(book_imbalance, starts) / counts,
            "tick_book_imbalance_last": book_imbalance[starts + counts - 1],
            "tick_microprice_edge_mean": np.add.reduceat(micro_edge, starts) / counts,
            "tick_microprice_edge_last": micro_edge[starts + counts - 1],
            "price_efficiency_5m": np.divide(
                np.abs(net_move),
                absolute_move,
                out=np.zeros_like(net_move, dtype=float),
                where=absolute_move > 0,
            ),
        }
    )


def _load_bars(items: Sequence[Mapping[str, Any]], role: str) -> pd.DataFrame:
    prefix = role.removesuffix("_m5")
    parts = []
    for item in items:
        table = pq.read_table(
            item["path"],
            columns=["timestamp_ms", "open", "high", "low", "close", "tick_count"],
        ).to_pandas()
        table = table.rename(
            columns={name: f"{prefix}_{name}" for name in ("open", "high", "low", "close", "tick_count")}
        )
        parts.append(table)
    frame = pd.concat(parts, ignore_index=True).sort_values("timestamp_ms", kind="mergesort")
    if frame["timestamp_ms"].duplicated().any():
        raise MicrostructureRegimeError(f"duplicate bars in {role}")
    return frame.reset_index(drop=True)


def _enrich_market_frame(frame: pd.DataFrame, contract: Mapping[str, Any]) -> pd.DataFrame:
    frame = frame.sort_values("timestamp_ms", kind="mergesort").reset_index(drop=True)
    close = frame["xauusd_mid_close"]
    high = frame["xauusd_mid_high"]
    low = frame["xauusd_mid_low"]
    previous = close.shift(1)
    tr = pd.concat([(high - low).abs(), (high - previous).abs(), (low - previous).abs()], axis=1).max(axis=1)
    regime = contract["regimes"]
    frame["atr"] = tr.ewm(
        alpha=1.0 / int(regime["atr_bars"]),
        adjust=False,
        min_periods=int(regime["atr_bars"]),
    ).mean()
    frame["ema_fast"] = close.ewm(span=int(regime["ema_fast_bars"]), adjust=False).mean()
    frame["ema_slow"] = close.ewm(span=int(regime["ema_slow_bars"]), adjust=False).mean()
    frame["ema_fast_slope_3"] = frame["ema_fast"] - frame["ema_fast"].shift(3)
    frame["xau_return_5m_price"] = close - close.shift(1)
    frame["xau_return_15m_price"] = close - close.shift(3)
    frame["xau_return_60m_price"] = close - close.shift(12)
    frame["prior_high_12"] = high.shift(1).rolling(12, min_periods=12).max()
    frame["prior_low_12"] = low.shift(1).rolling(12, min_periods=12).min()
    mean24 = close.rolling(24, min_periods=24).mean()
    std24 = close.rolling(24, min_periods=24).std(ddof=1)
    frame["zscore_24"] = (close - mean24) / std24
    frame["atr_ratio_1d"] = frame["atr"] / frame["atr"].rolling(288, min_periods=96).median()
    frame["tick_imbalance_5m"] = frame["tick_signed_move"] / frame["tick_move_count"].replace(0, np.nan)
    for bars, label in ((3, "15m"), (12, "60m")):
        frame[f"tick_imbalance_{label}"] = (
            frame["tick_signed_move"].rolling(bars, min_periods=bars).sum()
            / frame["tick_move_count"].rolling(bars, min_periods=bars).sum().replace(0, np.nan)
        )
    frame["book_imbalance_5m"] = frame["tick_book_imbalance_mean"]
    frame["book_imbalance_15m"] = frame["tick_book_imbalance_mean"].rolling(3, min_periods=3).mean()
    frame["microprice_edge_5m"] = frame["tick_microprice_edge_mean"]
    frame["microprice_edge_15m"] = frame["tick_microprice_edge_mean"].rolling(3, min_periods=3).mean()
    quote_rate = frame["xau_tick_count"] / 300.0
    frame["quote_intensity_ratio"] = quote_rate / quote_rate.rolling(12, min_periods=12).mean()
    realized = np.sqrt(frame["tick_realized_variance"].clip(lower=0.0))
    frame["realized_volatility_ratio"] = realized / realized.rolling(12, min_periods=12).mean()
    frame["spread_shock_ratio"] = frame["tick_spread_last"] / frame["tick_spread_mean"].rolling(12, min_periods=12).mean()
    for symbol in ("xagusd", "eurusd", "usdjpy"):
        series = frame[f"{symbol}_mid_close"]
        frame[f"{symbol}_return_5m"] = 10_000.0 * (series / series.shift(1) - 1.0)
        frame[f"{symbol}_return_15m"] = 10_000.0 * (series / series.shift(3) - 1.0)
        frame[f"{symbol}_return_60m"] = 10_000.0 * (series / series.shift(12) - 1.0)
    gap_r = (frame["ema_fast"] - frame["ema_slow"]).abs() / frame["atr"]
    shock_r = frame["xau_return_15m_price"].abs() / frame["atr"]
    trend_up = (gap_r >= float(regime["trend_gap_atr"])) & (frame["ema_fast"] > frame["ema_slow"]) & (frame["ema_fast_slope_3"] > 0)
    trend_down = (gap_r >= float(regime["trend_gap_atr"])) & (frame["ema_fast"] < frame["ema_slow"]) & (frame["ema_fast_slope_3"] < 0)
    range_state = (gap_r <= float(regime["range_gap_atr"])) & (frame["atr_ratio_1d"] <= float(regime["range_max_atr_ratio"]))
    frame["regime"] = np.select(
        [shock_r >= float(regime["shock_return_15m_atr"]), trend_up, trend_down, range_state],
        ["SHOCK", "TREND_UP", "TREND_DOWN", "RANGE"],
        default="TRANSITION",
    )
    return frame


def _generate_candidates(
    frame: pd.DataFrame,
    start_utc: str,
    end_exclusive_utc: str,
    contract: Mapping[str, Any],
    segment: str,
) -> list[dict[str, Any]]:
    start_ms = _parse_utc_ms(start_utc)
    end_ms = _parse_utc_ms(end_exclusive_utc)
    specialists = contract["specialists"]
    cooldown_default = int(specialists["family_cooldown_minutes"]) * 60_000
    cooldown_shock = int(specialists["shock_cooldown_minutes"]) * 60_000
    last_signal: dict[str, int] = {}
    rows: list[dict[str, Any]] = []
    for index in range(1, len(frame) - int(contract["execution"]["maximum_holding_bars"]) - 1):
        raw = frame.iloc[index]
        bar_start = int(raw["timestamp_ms"])
        decision = bar_start + BAR_WIDTH_MS
        if decision < start_ms or decision >= end_ms or int(raw["xau_tick_count"]) < int(contract["aggregation"]["minimum_tick_count"]):
            continue
        if not _required_features_finite(raw):
            continue
        candidates: list[tuple[str, str]] = []
        regime = str(raw["regime"])
        if regime == "TREND_UP":
            if raw["xauusd_mid_low"] <= raw["ema_fast"] <= raw["xauusd_mid_close"] and raw["xauusd_mid_close"] > raw["xauusd_mid_open"]:
                candidates.append(("TREND_PULLBACK", "LONG"))
            if raw["xauusd_mid_close"] > raw["prior_high_12"]:
                candidates.append(("TREND_BREAKOUT", "LONG"))
        elif regime == "TREND_DOWN":
            if raw["xauusd_mid_high"] >= raw["ema_fast"] >= raw["xauusd_mid_close"] and raw["xauusd_mid_close"] < raw["xauusd_mid_open"]:
                candidates.append(("TREND_PULLBACK", "SHORT"))
            if raw["xauusd_mid_close"] < raw["prior_low_12"]:
                candidates.append(("TREND_BREAKOUT", "SHORT"))
        elif regime == "RANGE":
            previous_z = float(frame.iloc[index - 1]["zscore_24"])
            threshold = float(specialists["range_zscore_threshold"])
            if raw["zscore_24"] >= threshold and previous_z < threshold:
                candidates.append(("RANGE_FADE", "SHORT"))
            elif raw["zscore_24"] <= -threshold and previous_z > -threshold:
                candidates.append(("RANGE_FADE", "LONG"))
        elif regime == "SHOCK":
            direction = "LONG" if raw["xau_return_15m_price"] > 0 else "SHORT"
            candidates.append(("SHOCK_CONTINUATION", direction))
            candidates.append(("SHOCK_REVERSAL", "SHORT" if direction == "LONG" else "LONG"))
        for family, direction in candidates:
            cooldown = cooldown_shock if family.startswith("SHOCK") else cooldown_default
            if decision - last_signal.get(family, -10**18) < cooldown:
                continue
            outcome = _simulate_trade(frame, index, direction, contract["execution"])
            if outcome is None:
                continue
            last_signal[family] = decision
            row = {
                "candidate_id": f"{segment}:{decision}:{family}:{direction}",
                "segment": segment,
                "family_id": family,
                "regime": regime,
                "direction": direction,
                "decision_time_ms": decision,
                "decision_time_utc": _iso_ms(decision),
                **outcome,
                **_candidate_features(raw, family, regime, direction, outcome["entry_spread_r"]),
            }
            rows.append(row)
    return rows


def _required_features_finite(row: pd.Series) -> bool:
    names = (
        "atr",
        "ema_fast",
        "ema_slow",
        "prior_high_12",
        "prior_low_12",
        "zscore_24",
        "atr_ratio_1d",
        "tick_imbalance_5m",
        "tick_imbalance_15m",
        "tick_imbalance_60m",
        "quote_intensity_ratio",
        "realized_volatility_ratio",
        "spread_shock_ratio",
        "xagusd_return_60m",
        "eurusd_return_60m",
        "usdjpy_return_60m",
    )
    return all(math.isfinite(float(row[name])) for name in names) and float(row["atr"]) > 0


def _simulate_trade(
    frame: pd.DataFrame,
    signal_index: int,
    direction: str,
    execution: Mapping[str, Any],
) -> dict[str, Any] | None:
    horizon = int(execution["maximum_holding_bars"])
    entry_index = signal_index + 1
    last_index = entry_index + horizon - 1
    if last_index >= len(frame):
        return None
    entry_time = int(frame.iloc[entry_index]["timestamp_ms"])
    expected = entry_time + np.arange(horizon, dtype=np.int64) * BAR_WIDTH_MS
    observed = frame.iloc[entry_index : last_index + 1]["timestamp_ms"].to_numpy(dtype=np.int64)
    if not np.array_equal(expected, observed):
        return None
    signal = frame.iloc[signal_index]
    risk = float(signal["atr"]) * float(execution["risk_atr_multiple"])
    entry_bar = frame.iloc[entry_index]
    entry_bid = float(entry_bar["xauusd_bid_open"])
    entry_ask = float(entry_bar["xauusd_ask_open"])
    spread_r = (entry_ask - entry_bid) / risk if risk > 0 else math.inf
    if risk <= 0 or spread_r < 0 or spread_r > float(execution["maximum_entry_spread_r"]):
        return None
    reward_r = float(execution["reward_r"])
    bars = frame.iloc[entry_index : last_index + 1]
    if direction == "LONG":
        entry_price = entry_ask
        stop, target = entry_price - risk, entry_price + reward_r * risk
        favorable = (bars["xauusd_bid_high"] - entry_price).max() / risk
        adverse = (bars["xauusd_bid_low"] - entry_price).min() / risk
    else:
        entry_price = entry_bid
        stop, target = entry_price + risk, entry_price - reward_r * risk
        favorable = (entry_price - bars["xauusd_ask_low"]).max() / risk
        adverse = (entry_price - bars["xauusd_ask_high"]).min() / risk
    exit_price = math.nan
    exit_reason = "EXPIRY"
    exit_index = last_index
    for offset, (_, bar) in enumerate(bars.iterrows()):
        if direction == "LONG":
            stop_hit = float(bar["xauusd_bid_low"]) <= stop
            target_hit = float(bar["xauusd_bid_high"]) >= target
        else:
            stop_hit = float(bar["xauusd_ask_high"]) >= stop
            target_hit = float(bar["xauusd_ask_low"]) <= target
        if stop_hit:
            exit_price, exit_reason, exit_index = stop, "STOP", entry_index + offset
            break
        if target_hit:
            exit_price, exit_reason, exit_index = target, "TARGET", entry_index + offset
            break
    if not math.isfinite(exit_price):
        last = frame.iloc[last_index]
        exit_price = float(last["xauusd_bid_close"] if direction == "LONG" else last["xauusd_ask_close"])
    gross_r = (exit_price - entry_price) / risk if direction == "LONG" else (entry_price - exit_price) / risk
    return {
        "entry_time_ms": entry_time,
        "entry_time_utc": _iso_ms(entry_time),
        "exit_time_ms": int(frame.iloc[exit_index]["timestamp_ms"]) + BAR_WIDTH_MS,
        "exit_time_utc": _iso_ms(int(frame.iloc[exit_index]["timestamp_ms"]) + BAR_WIDTH_MS),
        "entry_price": entry_price,
        "exit_price": exit_price,
        "initial_risk_price": risk,
        "entry_spread_r": spread_r,
        "exit_reason": exit_reason,
        "baseline_net_r": gross_r,
        "stress_net_r": gross_r - float(execution["stress_slippage_r"]),
        "mfe_r": float(favorable),
        "mae_r": float(adverse),
    }


def _candidate_features(
    row: pd.Series,
    family: str,
    regime: str,
    direction: str,
    entry_spread_r: float,
) -> dict[str, float]:
    sign = 1.0 if direction == "LONG" else -1.0
    atr = float(row["atr"])
    return {
        "direction_sign": sign,
        "xau_return_5m_directional_r": sign * float(row["xau_return_5m_price"]) / atr,
        "xau_return_15m_directional_r": sign * float(row["xau_return_15m_price"]) / atr,
        "xau_return_60m_directional_r": sign * float(row["xau_return_60m_price"]) / atr,
        "ema_gap_directional_r": sign * float(row["ema_fast"] - row["ema_slow"]) / atr,
        "ema_distance_directional_r": sign * float(row["xauusd_mid_close"] - row["ema_fast"]) / atr,
        "tick_imbalance_5m_directional": sign * float(row["tick_imbalance_5m"]),
        "tick_imbalance_15m_directional": sign * float(row["tick_imbalance_15m"]),
        "tick_imbalance_60m_directional": sign * float(row["tick_imbalance_60m"]),
        "book_imbalance_5m_directional": sign * float(row["book_imbalance_5m"]),
        "book_imbalance_15m_directional": sign * float(row["book_imbalance_15m"]),
        "microprice_edge_5m_directional": sign * float(row["microprice_edge_5m"]),
        "microprice_edge_15m_directional": sign * float(row["microprice_edge_15m"]),
        "xag_return_5m_directional": sign * float(row["xagusd_return_5m"]),
        "xag_return_15m_directional": sign * float(row["xagusd_return_15m"]),
        "xag_return_60m_directional": sign * float(row["xagusd_return_60m"]),
        "eurusd_return_15m_directional": sign * float(row["eurusd_return_15m"]),
        "eurusd_return_60m_directional": sign * float(row["eurusd_return_60m"]),
        "usdjpy_return_15m_directional": sign * float(row["usdjpy_return_15m"]),
        "usdjpy_return_60m_directional": sign * float(row["usdjpy_return_60m"]),
        "atr_fraction_of_price": atr / float(row["xauusd_mid_close"]),
        "atr_ratio_1d": float(row["atr_ratio_1d"]),
        "quote_intensity_ratio": float(row["quote_intensity_ratio"]),
        "realized_volatility_ratio": float(row["realized_volatility_ratio"]),
        "entry_spread_r": float(entry_spread_r),
        "spread_shock_ratio": float(row["spread_shock_ratio"]),
        "price_efficiency_5m": float(row["price_efficiency_5m"]),
        "hour_sin": math.sin(2.0 * math.pi * (_hour_from_ms(int(row["timestamp_ms"])) + 1 / 12) / 24.0),
        "hour_cos": math.cos(2.0 * math.pi * (_hour_from_ms(int(row["timestamp_ms"])) + 1 / 12) / 24.0),
        "weekday_sin": math.sin(2.0 * math.pi * _weekday_from_ms(int(row["timestamp_ms"])) / 7.0),
        "weekday_cos": math.cos(2.0 * math.pi * _weekday_from_ms(int(row["timestamp_ms"])) / 7.0),
        "family_trend_pullback": float(family == "TREND_PULLBACK"),
        "family_trend_breakout": float(family == "TREND_BREAKOUT"),
        "family_range_fade": float(family == "RANGE_FADE"),
        "family_shock_continuation": float(family == "SHOCK_CONTINUATION"),
        "family_shock_reversal": float(family == "SHOCK_REVERSAL"),
        "regime_trend": float(regime.startswith("TREND")),
        "regime_range": float(regime == "RANGE"),
        "regime_shock": float(regime == "SHOCK"),
    }


def _family_metrics(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[str(row["family_id"])].append(row)
    result = []
    for family in sorted(grouped):
        baseline = _return_metrics(grouped[family], "baseline_net_r")
        stress = _return_metrics(grouped[family], "stress_net_r")
        result.append(
            {
                "family_id": family,
                "trades": baseline["trades"],
                "baseline_profit_factor": baseline["profit_factor"],
                "baseline_average_r": baseline["average_r"],
                "baseline_net_r": baseline["net_r"],
                "stress_profit_factor": stress["profit_factor"],
                "average_stress_r": stress["average_r"],
                "stress_net_r": stress["net_r"],
            }
        )
    return result


def _eligible_families(metrics: Sequence[Mapping[str, Any]], contract: Mapping[str, Any]) -> list[str]:
    gate = contract["specialists"]["train_family_gate"]
    return [
        str(row["family_id"])
        for row in metrics
        if int(row["trades"]) >= int(gate["minimum_trades"])
        and float(row["baseline_profit_factor"] or 0.0) >= float(gate["minimum_baseline_profit_factor"])
        and float(row["stress_profit_factor"] or 0.0) >= float(gate["minimum_stress_profit_factor"])
        and float(row["average_stress_r"]) >= float(gate["minimum_average_stress_r"])
    ]


def _fit_model(
    rows: Sequence[Mapping[str, Any]], feature_names: Sequence[str], config: Mapping[str, Any]
) -> HistGradientBoostingRegressor:
    model = HistGradientBoostingRegressor(
        loss=str(config["loss"]),
        learning_rate=float(config["learning_rate"]),
        max_iter=int(config["max_iter"]),
        max_leaf_nodes=int(config["max_leaf_nodes"]),
        max_depth=int(config["max_depth"]),
        min_samples_leaf=int(config["min_samples_leaf"]),
        l2_regularization=float(config["l2_regularization"]),
        early_stopping=bool(config["early_stopping"]),
        random_state=int(config["random_state"]),
    )
    model.fit(_matrix(rows, feature_names), np.asarray([float(row["stress_net_r"]) for row in rows]))
    return model


def _matrix(rows: Sequence[Mapping[str, Any]], feature_names: Sequence[str]) -> np.ndarray:
    matrix = np.asarray([[float(row[name]) for name in feature_names] for row in rows], dtype=float)
    if matrix.ndim != 2 or matrix.shape[0] == 0 or not np.isfinite(matrix).all():
        raise MicrostructureRegimeError("empty or non-finite model matrix")
    return matrix


def _predictive_metrics(rows: Sequence[Mapping[str, Any]], scores: Sequence[float]) -> dict[str, Any]:
    outcomes = np.asarray([float(row["stress_net_r"]) for row in rows], dtype=float)
    scores_array = np.asarray(scores, dtype=float)
    labels = (outcomes > 0).astype(int)
    auc = float(roc_auc_score(labels, scores_array)) if len(np.unique(labels)) == 2 else None
    spearman = float(pd.Series(scores_array).corr(pd.Series(outcomes), method="spearman"))
    return {"auc": auc, "spearman": spearman, "population": len(rows)}


def _top_fraction_cutoff(scores: Sequence[float], fraction: float) -> float:
    ranked = sorted((float(value) for value in scores), reverse=True)
    count = max(1, math.ceil(len(ranked) * fraction))
    return ranked[count - 1]


def _portfolio_select(
    rows: Sequence[Mapping[str, Any]],
    scores: Sequence[float],
    cutoff: float,
    selection: Mapping[str, Any],
) -> list[dict[str, Any]]:
    best_at_decision: dict[int, tuple[dict[str, Any], float]] = {}
    for raw, score in zip(rows, scores):
        score = float(score)
        if score < cutoff:
            continue
        row = dict(raw)
        decision = int(row["decision_time_ms"])
        current = best_at_decision.get(decision)
        if current is None or (-score, row["candidate_id"]) < (-current[1], current[0]["candidate_id"]):
            row["model_score"] = score
            best_at_decision[decision] = (row, score)
    candidates = sorted(
        (item[0] for item in best_at_decision.values()),
        key=lambda row: (int(row["entry_time_ms"]), -float(row["model_score"]), row["candidate_id"]),
    )
    selected = []
    open_exits: list[int] = []
    last_entry = -10**18
    daily: Counter[str] = Counter()
    cooldown = int(selection["portfolio_cooldown_minutes"]) * 60_000
    for row in candidates:
        entry = int(row["entry_time_ms"])
        open_exits = [value for value in open_exits if value > entry]
        if len(open_exits) >= int(selection["maximum_concurrent_trades"]):
            continue
        if entry - last_entry < cooldown:
            continue
        day = row["entry_time_utc"][:10]
        if daily[day] >= int(selection["maximum_trades_per_utc_day"]):
            continue
        selected.append(row)
        open_exits.append(int(row["exit_time_ms"]))
        last_entry = entry
        daily[day] += 1
    return selected


def _economic_metrics(rows: Sequence[Mapping[str, Any]], source_days: int) -> dict[str, Any]:
    ordered = sorted(rows, key=lambda row: (int(row["exit_time_ms"]), row["candidate_id"]))
    values = [float(row["stress_net_r"]) for row in ordered]
    metrics = _return_metrics(ordered, "stress_net_r")
    months: dict[str, float] = defaultdict(float)
    directions = Counter()
    families = Counter()
    for row, value in zip(ordered, values):
        months[row["exit_time_utc"][:7]] += value
        directions[row["direction"]] += 1
        families[row["family_id"]] += 1
    winners = sorted((value for value in values if value > 0), reverse=True)
    metrics.update(
        {
            "stress_profit_factor": metrics.pop("profit_factor"),
            "average_stress_r": metrics.pop("average_r"),
            "stress_net_r": metrics.pop("net_r"),
            "trades_per_source_day": len(ordered) / source_days if source_days else 0.0,
            "positive_month_share": sum(value > 0 for value in months.values()) / len(months) if months else 0.0,
            "top10_winners_removed_net_r": sum(values) - sum(winners[:10]),
            "direction_counts": dict(directions),
            "family_counts": dict(families),
        }
    )
    return metrics


def _return_metrics(rows: Sequence[Mapping[str, Any]], field: str) -> dict[str, Any]:
    values = np.asarray([float(row[field]) for row in rows], dtype=float)
    wins = values[values > 0]
    losses = values[values < 0]
    equity = np.cumsum(values) if len(values) else np.asarray([], dtype=float)
    peaks = np.maximum.accumulate(np.r_[0.0, equity]) if len(values) else np.asarray([0.0])
    drawdown = peaks[1:] - equity if len(values) else np.asarray([], dtype=float)
    return {
        "trades": int(len(values)),
        "wins": int(len(wins)),
        "losses": int(len(losses)),
        "net_r": float(values.sum()),
        "average_r": float(values.mean()) if len(values) else 0.0,
        "profit_factor": float(wins.sum() / -losses.sum()) if len(losses) and -losses.sum() > 0 else None,
        "maximum_closed_drawdown_r": float(drawdown.max()) if len(drawdown) else 0.0,
    }


def _segment_gates(
    predictive: Mapping[str, Any],
    economic: Mapping[str, Any],
    gate: Mapping[str, Any],
    *,
    predictive_gate_required: bool = True,
) -> dict[str, bool]:
    checks = {
        "minimum_trades": int(economic["trades"]) >= int(gate["minimum_trades"]),
        "minimum_frequency": float(economic["trades_per_source_day"]) >= float(gate["minimum_trades_per_source_day"]),
        "maximum_frequency": float(economic["trades_per_source_day"]) <= float(gate["maximum_trades_per_source_day"]),
        "stress_profit_factor": float(economic["stress_profit_factor"] or 0.0) >= float(gate["minimum_stress_profit_factor"]),
        "average_stress_r": float(economic["average_stress_r"]) >= float(gate["minimum_average_stress_r"]),
        "positive_month_share": float(economic["positive_month_share"]) >= float(gate["minimum_positive_month_share"]),
        "maximum_closed_drawdown_r": float(economic["maximum_closed_drawdown_r"]) <= float(gate["maximum_closed_drawdown_r"]),
        "top10_winners_removed_net_positive": (not gate["require_top10_winners_removed_net_positive"]) or float(economic["top10_winners_removed_net_r"]) > 0,
    }
    if predictive_gate_required:
        checks["predictive_signal"] = (
            float(predictive.get("auc") or 0.0) >= float(gate["minimum_auc"])
            or float(predictive.get("spearman") or 0.0) >= float(gate["minimum_spearman"])
        )
    return checks


def _classification(
    eligible: Sequence[str],
    chosen: Mapping[str, Any] | None,
    internal: Mapping[str, Any] | None,
    exam: Mapping[str, Any] | None,
) -> str:
    if not eligible:
        return "DUKASCOPY_MICROSTRUCTURE_REGIME_NO_TRAIN_FAMILY_SURVIVOR"
    if chosen is None:
        return "DUKASCOPY_MICROSTRUCTURE_REGIME_NO_VALIDATION_SURVIVOR"
    if not internal or not internal["passes"]:
        return "DUKASCOPY_MICROSTRUCTURE_REGIME_INTERNAL_TEST_REJECTED"
    if not exam or not exam["passes"]:
        return "DUKASCOPY_MICROSTRUCTURE_REGIME_EXAM_REJECTED"
    return "DUKASCOPY_MICROSTRUCTURE_REGIME_RESEARCH_SURVIVOR"


def _prediction_rows(rows: Sequence[Mapping[str, Any]], segment: str) -> list[dict[str, Any]]:
    fields = (
        "candidate_id",
        "family_id",
        "regime",
        "direction",
        "decision_time_utc",
        "entry_time_utc",
        "exit_time_utc",
        "exit_reason",
        "model_score",
        "baseline_net_r",
        "stress_net_r",
        "mfe_r",
        "mae_r",
    )
    return [{"segment": segment, **{name: row[name] for name in fields}} for row in rows]


def _flatten_evaluations(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    result = []
    for row in rows:
        result.append(
            {
                "top_fraction": row["top_fraction"],
                "train_score_cutoff": row["train_score_cutoff"],
                **{f"predictive_{key}": value for key, value in row["predictive_metrics"].items()},
                **row["economic_metrics"],
                "passes": row["passes"],
                "failed_gates": "|".join(key for key, value in row["gates"].items() if not value),
            }
        )
    return result


def _source_days(frame: pd.DataFrame, start: str, end: str) -> int:
    start_ms, end_ms = _parse_utc_ms(start), _parse_utc_ms(end)
    selected = frame[(frame["timestamp_ms"] >= start_ms) & (frame["timestamp_ms"] < end_ms)]
    return len({_iso_ms(int(value))[:10] for value in selected["timestamp_ms"].to_numpy()})


def _write_csv(path: Path, rows: Sequence[Mapping[str, Any]]) -> None:
    rows = list(rows)
    fieldnames = list(dict.fromkeys(key for row in rows for key in row))
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        if not fieldnames:
            handle.write("")
            return
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _render(payload: Mapping[str, Any]) -> str:
    lines = [
        "# A3 ML Dukascopy Microstructure Regime V1",
        "",
        f"Classification: `{payload['classification']}`",
        "",
        f"Eligible train families: `{', '.join(payload['eligible_families']) or 'none'}`",
        f"Validation population after family gate: `{payload['validation_population_after_family_gate']}`",
        f"Internal test opened: `{payload['internal_test_opened']}`",
        f"Exam opened: `{payload['exam_opened']}`",
        "",
    ]
    for row in payload["validation_evaluations"]:
        metrics = row["economic_metrics"]
        lines.append(
            f"- Top {100 * row['top_fraction']:.0f}%: {metrics['trades']} trades, "
            f"{metrics['trades_per_source_day']:.3f}/day, PF {float(metrics['stress_profit_factor'] or 0):.3f}, "
            f"average {metrics['average_stress_r']:.4f}R, pass `{row['passes']}`."
        )
    if payload["internal_test"]:
        metrics = payload["internal_test"]["economic_metrics"]
        lines.extend(
            [
                "",
                f"Internal test: {metrics['trades']} trades, PF {float(metrics['stress_profit_factor'] or 0):.3f}, average {metrics['average_stress_r']:.4f}R, pass `{payload['internal_test']['passes']}`.",
            ]
        )
    if payload["exam"]:
        metrics = payload["exam"]["economic_metrics"]
        lines.extend(
            [
                "",
                f"Exam: {metrics['trades']} trades, PF {float(metrics['stress_profit_factor'] or 0):.3f}, average {metrics['average_stress_r']:.4f}R, pass `{payload['exam']['passes']}`.",
            ]
        )
    lines.extend(["", "No demo, live, EA, or broker action is authorized.", ""])
    return "\n".join(lines)


def _validate_contract(contract: Mapping[str, Any]) -> None:
    if contract.get("schema_version") != "a3_ml_dukascopy_microstructure_regime_v1":
        raise ValueError("unexpected microstructure-regime contract version")
    if contract.get("instruments") != ["XAUUSD", "XAGUSD", "EURUSD", "USDJPY"]:
        raise ValueError("instrument set changed")
    if contract.get("specialists", {}).get("families") != [
        "TREND_PULLBACK",
        "TREND_BREAKOUT",
        "RANGE_FADE",
        "SHOCK_CONTINUATION",
        "SHOCK_REVERSAL",
    ]:
        raise ValueError("specialist family set changed")
    model = contract.get("model", {})
    if model.get("family") != "HIST_GRADIENT_BOOSTING_REGRESSOR_V1" or model.get("random_state") != 20260716:
        raise ValueError("model family or seed changed")
    authorization = contract.get("authorization", {})
    if not authorization.get("research_only") or not authorization.get("validation_outcomes_authorized"):
        raise ValueError("research and validation authorization required")
    for key in ("python_demo_predictions_authorized", "ea_consumption_authorized", "broker_action_authorized"):
        if authorization.get(key):
            raise ValueError(f"{key} must remain false")
    if not authorization.get("internal_test_requires_validation_pass") or not authorization.get("exam_requires_internal_test_pass"):
        raise ValueError("chronological firewall was weakened")
    if len(contract.get("features", [])) != len(set(contract.get("features", []))):
        raise ValueError("duplicate features")


def _month_keys(start: str, end: str) -> list[str]:
    start_year, start_month = map(int, start.split("-"))
    end_year, end_month = map(int, end.split("-"))
    result = []
    year, month = start_year, start_month
    while (year, month) <= (end_year, end_month):
        result.append(f"{year:04d}-{month:02d}")
        year, month = (year + 1, 1) if month == 12 else (year, month + 1)
    return result


def _parse_utc_ms(value: str) -> int:
    return int(datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp() * 1000)


def _iso_ms(value: int) -> str:
    return datetime.fromtimestamp(value / 1000, UTC).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def _hour_from_ms(value: int) -> int:
    return datetime.fromtimestamp(value / 1000, UTC).hour


def _weekday_from_ms(value: int) -> int:
    return datetime.fromtimestamp(value / 1000, UTC).weekday()


def _canonical_sha256(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()
