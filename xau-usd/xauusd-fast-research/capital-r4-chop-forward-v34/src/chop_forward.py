from __future__ import annotations

from dataclasses import dataclass
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any, Iterable, Mapping

import numpy as np
import pandas as pd


BAR_WIDTH_MS = 5 * 60_000
TEXT_DEPENDENCY_SUFFIXES = {
    ".csv",
    ".json",
    ".md",
    ".py",
    ".txt",
}
FEATURE_PARITY_COLUMNS = (
    "bar_start_utc",
    "bar_end_utc",
    "return_3",
    "return_12",
    "tick_imbalance_15m",
    "spread_ratio",
    "hour_utc_custom",
    "regime",
    "m15_state_age_m5",
    "risk_atr",
    "z_192",
    "z_delta_192",
    "variance_ratio_4_192",
    "mean_slope_atr_192",
    "z_384",
    "z_delta_384",
    "variance_ratio_4_384",
    "return_acf_1_384",
    "mean_slope_atr_384",
)


@dataclass(frozen=True)
class FrozenR4:
    package_config: dict[str, Any]
    r4_config: dict[str, Any]
    dependency_sha256: str
    data_module: Any
    regime_module: Any
    micro_module: Any
    origin_module: Any
    confirmation_module: Any
    tick_loader_module: Any


def _load_module(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(4 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def dependency_sha256(repo_root: Path, paths: Iterable[str]) -> str:
    rows = []
    for relative in sorted(str(value).replace("\\", "/") for value in paths):
        path = repo_root / relative
        if not path.is_file():
            raise FileNotFoundError(path)
        content = path.read_bytes()
        if path.suffix.lower() in TEXT_DEPENDENCY_SUFFIXES:
            content = content.replace(b"\r\n", b"\n")
        rows.append(f"{relative}|{hashlib.sha256(content).hexdigest()}")
    return hashlib.sha256("\n".join(rows).encode("ascii")).hexdigest()


def load_frozen(repo_root: Path, package_root: Path) -> FrozenR4:
    package_config = json.loads(
        (
            package_root
            / "config"
            / "capital_r4_chop_forward_v34.json"
        ).read_text(encoding="utf-8")
    )
    r4_config_path = repo_root / package_config["source"]["r4_config"]
    r4_config = json.loads(r4_config_path.read_text(encoding="utf-8"))
    research_root = repo_root / "xau-usd" / "xauusd-fast-research"
    data_module = _load_module(
        "capital_r4_v34_data",
        research_root / "independent-specialists-v1" / "src" / "data.py",
    )
    regime_module = _load_module(
        "capital_r4_v34_regimes",
        research_root / "independent-specialists-v1" / "src" / "research.py",
    )
    micro_module = _load_module(
        "capital_r4_v34_micro",
        research_root / "m5-microstructure-mechanics-v1" / "src" / "campaign.py",
    )
    origin_module = _load_module(
        "capital_r4_v34_origin",
        research_root
        / "chop-failed-reversion-envelope-v24"
        / "src"
        / "campaign.py",
    )
    confirmation_module = _load_module(
        "capital_r4_v34_confirmation",
        research_root / "chop-three-mechanism-rawtick-v26" / "src" / "confirmation.py",
    )
    tick_loader_module = _load_module(
        "capital_r4_v34_tick_loader",
        research_root
        / "capital-quote-microburst-forward-v24-1"
        / "src"
        / "microburst.py",
    )
    return FrozenR4(
        package_config=package_config,
        r4_config=r4_config,
        dependency_sha256=dependency_sha256(
            repo_root, package_config["contract_scope"]
        ),
        data_module=data_module,
        regime_module=regime_module,
        micro_module=micro_module,
        origin_module=origin_module,
        confirmation_module=confirmation_module,
        tick_loader_module=tick_loader_module,
    )


def _maximum_internal_gap(values: np.ndarray) -> int:
    if len(values) < 2:
        return 0
    return int(np.diff(values).max())


def aggregate_capital_quotes(
    ticks: pd.DataFrame,
    *,
    completed_through: pd.Timestamp,
    quality: Mapping[str, Any],
) -> pd.DataFrame:
    """Aggregate Capital quotes with the frozen Dukascopy M5 semantics."""
    columns = {"tick_time_msc", "bid", "ask", "spread_price"}
    missing = sorted(columns.difference(ticks.columns))
    if missing:
        raise ValueError(f"Capital tick frame is missing columns: {missing}")
    if ticks.empty:
        return pd.DataFrame()

    source = ticks[list(columns)].copy()
    for column in columns:
        source[column] = pd.to_numeric(source[column], errors="coerce")
    if source[list(columns)].isna().any().any():
        raise ValueError("Capital tick frame contains invalid numeric values")
    source["tick_time_msc"] = source["tick_time_msc"].astype(np.int64)
    source = (
        source.sort_values("tick_time_msc", kind="mergesort")
        .drop_duplicates("tick_time_msc", keep="last")
        .reset_index(drop=True)
    )
    times = source["tick_time_msc"].to_numpy(dtype=np.int64)
    bid = source["bid"].to_numpy(dtype=float)
    ask = source["ask"].to_numpy(dtype=float)
    spread_field = source["spread_price"].to_numpy(dtype=float)
    if bool(np.any(np.diff(times) <= 0)):
        raise ValueError("Capital tick timestamps are not strictly increasing")
    if bool(np.any((bid <= 0.0) | (ask < bid) | (spread_field < 0.0))):
        raise ValueError("Capital tick frame contains invalid quotes")

    bucket = times - times % BAR_WIDTH_MS
    starts = np.r_[0, np.flatnonzero(np.diff(bucket)) + 1]
    counts = np.diff(np.r_[starts, len(bucket)])
    ends = starts + counts - 1
    mid = (bid + ask) / 2.0
    spread = ask - bid
    delta = np.diff(mid, prepend=mid[0])
    delta[starts] = 0.0
    signed = np.sign(delta)
    move_count = np.add.reduceat((signed != 0).astype(np.int64), starts)
    signed_move = np.add.reduceat(signed, starts)
    absolute_move = np.add.reduceat(np.abs(delta), starts)
    realized = np.add.reduceat(np.square(delta), starts)
    net_move = mid[ends] - mid[starts]

    rows: dict[str, Any] = {
        "timestamp_ms": bucket[starts].astype(np.int64),
        "xau_tick_count": counts.astype(np.int64),
        "tick_signed_move": signed_move,
        "tick_move_count": move_count,
        "tick_realized_variance": realized,
        "tick_spread_mean": np.add.reduceat(spread, starts) / counts,
        "tick_spread_last": spread[ends],
        "tick_spread_max": np.maximum.reduceat(spread, starts),
        "tick_book_imbalance_mean": np.zeros(len(starts), dtype=float),
        "price_efficiency_5m": np.divide(
            np.abs(net_move),
            absolute_move,
            out=np.zeros_like(net_move, dtype=float),
            where=absolute_move > 0,
        ),
        "first_quote_delay_ms": times[starts] - bucket[starts],
        "last_quote_age_ms": bucket[starts] + BAR_WIDTH_MS - times[ends],
        "maximum_internal_quote_gap_ms": np.fromiter(
            (_maximum_internal_gap(times[start : end + 1]) for start, end in zip(starts, ends)),
            dtype=np.int64,
            count=len(starts),
        ),
    }
    for name, values in (("bid", bid), ("ask", ask), ("mid", mid)):
        rows[f"{name}_open"] = values[starts]
        rows[f"{name}_high"] = np.maximum.reduceat(values, starts)
        rows[f"{name}_low"] = np.minimum.reduceat(values, starts)
        rows[f"{name}_close"] = values[ends]
    result = pd.DataFrame(rows)
    result["bar_start_utc"] = pd.to_datetime(
        result["timestamp_ms"], unit="ms", utc=True
    )
    result["bar_end_utc"] = result["bar_start_utc"] + pd.Timedelta(minutes=5)
    cutoff = pd.Timestamp(completed_through)
    result = result.loc[result["bar_end_utc"] <= cutoff].copy()
    result["timestamp_utc"] = result["bar_end_utc"]
    result["timeframe"] = "M5"
    result["tick_count"] = result["xau_tick_count"].astype(float)
    result["quote_quality_passed"] = (
        result["xau_tick_count"].ge(int(quality["minimum_unique_quotes_per_m5"]))
        & result["first_quote_delay_ms"].le(
            int(quality["maximum_first_quote_delay_ms"])
        )
        & result["last_quote_age_ms"].le(
            int(quality["maximum_last_quote_age_ms"])
        )
        & result["maximum_internal_quote_gap_ms"].le(
            int(quality["maximum_internal_quote_gap_ms"])
        )
    )
    result["tick_imbalance_5m"] = result["tick_signed_move"].div(
        result["tick_move_count"].replace(0, np.nan)
    )
    result["tick_imbalance_15m"] = result["tick_signed_move"].rolling(3).sum().div(
        result["tick_move_count"].rolling(3).sum().replace(0, np.nan)
    )
    contiguous = (
        result["timestamp_ms"] - result["timestamp_ms"].shift(2)
    ).eq(2 * BAR_WIDTH_MS)
    quality_15m = result["quote_quality_passed"].rolling(3).sum().eq(3)
    result["quote_contiguous_15m"] = contiguous & quality_15m
    result.loc[~result["quote_contiguous_15m"], "tick_imbalance_15m"] = np.nan
    baseline = result["xau_tick_count"].rolling(288, min_periods=96).median()
    result["quote_intensity_ratio"] = result["xau_tick_count"].div(
        baseline.replace(0.0, np.nan)
    )
    return result.sort_values("bar_start_utc", kind="mergesort").reset_index(drop=True)


def add_historical_micro_placeholders(m5: pd.DataFrame) -> pd.DataFrame:
    result = m5.copy()
    result["timestamp_ms"] = (
        result["bar_start_utc"].array.as_unit("ms").asi8.astype(np.int64)
    )
    spread = result["ask_close"] - result["bid_close"]
    result["xau_tick_count"] = 1
    result["tick_count"] = 1.0
    result["tick_signed_move"] = 0.0
    result["tick_move_count"] = 0
    result["tick_realized_variance"] = 0.0
    result["tick_spread_mean"] = spread
    result["tick_spread_last"] = spread
    result["tick_spread_max"] = spread
    result["tick_book_imbalance_mean"] = 0.0
    span = (result["mid_high"] - result["mid_low"]).replace(0.0, np.nan)
    result["price_efficiency_5m"] = (
        (result["mid_close"] - result["mid_open"]).abs().div(span).fillna(0.0)
    )
    result["tick_imbalance_5m"] = np.nan
    result["tick_imbalance_15m"] = np.nan
    result["quote_intensity_ratio"] = 1.0
    result["quote_quality_passed"] = False
    result["quote_contiguous_15m"] = False
    return result


def overlay_quote_bars(historical: pd.DataFrame, quotes: pd.DataFrame) -> pd.DataFrame:
    quotes = quotes.loc[quotes["quote_quality_passed"].fillna(False)].copy()
    if quotes.empty:
        return historical.copy()
    columns = sorted(set(historical.columns).union(quotes.columns))
    old = historical.reindex(columns=columns)
    new = quotes.reindex(columns=columns)
    combined = pd.concat([old, new], ignore_index=True)
    combined["_quote_priority"] = combined["quote_quality_passed"].fillna(False).astype(int)
    combined = (
        combined.sort_values(
            ["bar_start_utc", "_quote_priority"], kind="mergesort"
        )
        .drop_duplicates("bar_start_utc", keep="last")
        .drop(columns="_quote_priority")
        .sort_values("bar_start_utc", kind="mergesort")
        .reset_index(drop=True)
    )
    combined["quote_quality_passed"] = combined["quote_quality_passed"].fillna(False)
    combined["quote_contiguous_15m"] = combined["quote_contiguous_15m"].fillna(False)
    return combined


def build_feature_frame(m5: pd.DataFrame, frozen: FrozenR4) -> pd.DataFrame:
    bars = {
        "M5": m5,
        "M15": frozen.data_module.aggregate_complete_bars(m5, 15, "M15"),
        "H1": frozen.data_module.aggregate_complete_bars(m5, 60, "H1"),
        "H4": frozen.data_module.aggregate_complete_bars(m5, 240, "H4"),
    }
    return frozen.origin_module.prepare_frame(
        bars["M5"],
        bars["M15"],
        bars["H1"],
        bars["H4"],
        frozen.r4_config,
        frozen.micro_module,
        frozen.regime_module,
    )


def _candidate_id(origin_attempt: int, signal_time: pd.Timestamp) -> str:
    return frozen_candidate_id(origin_attempt, signal_time)


def frozen_candidate_id(origin_attempt: int, signal_time: pd.Timestamp) -> str:
    payload = f"{origin_attempt}|{signal_time.isoformat()}".encode("ascii")
    return hashlib.sha256(payload).hexdigest()[:24]


def generate_forward_candidates(
    frame: pd.DataFrame,
    frozen: FrozenR4,
    *,
    start_inclusive: pd.Timestamp,
    end_inclusive: pd.Timestamp,
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    geometry = frozen.r4_config["geometry"]
    for definition in frozen.r4_config["components"]:
        mask, direction = frozen.confirmation_module.independent_signal_mask_direction(
            frame, str(definition["mechanic"]), definition["parameters"]
        )
        mask = (
            mask
            & frame["quote_quality_passed"].fillna(False)
            & frame["quote_contiguous_15m"].fillna(False)
            & frame["bar_end_utc"].ge(start_inclusive)
            & frame["bar_end_utc"].le(end_inclusive)
        )
        for index in np.flatnonzero(mask.to_numpy(dtype=bool)):
            signal_time = pd.Timestamp(frame["bar_end_utc"].iat[index])
            sign = int(direction.iat[index])
            rows.append(
                {
                    "candidate_id": _candidate_id(
                        int(definition["origin_attempt"]), signal_time
                    ),
                    "component_priority": int(definition["priority"]),
                    "origin_attempt": int(definition["origin_attempt"]),
                    "origin_variant_id": str(definition["origin_variant_id"]),
                    "regime_owner": "CHOP",
                    "mechanic": str(definition["mechanic"]),
                    "geometry_id": str(definition["geometry_id"]),
                    "signal_time_utc": signal_time,
                    "scheduled_entry_time_utc": signal_time,
                    "direction_sign": sign,
                    "direction": "LONG" if sign > 0 else "SHORT",
                    "signal_atr": float(frame["risk_atr"].iat[index]),
                    "stop_atr": float(geometry["stop_atr"]),
                    "target_r": float(geometry["target_r"]),
                    "hold_hours": float(geometry["maximum_hold_hours"]),
                    "source_feed": "CAPITAL_QUOTE_M5_V34",
                    "economic_outcome_opened": False,
                }
            )
    if not rows:
        return pd.DataFrame()
    candidates = pd.DataFrame(rows).sort_values(
        ["scheduled_entry_time_utc", "component_priority", "candidate_id"],
        kind="mergesort",
    )
    candidates = candidates.loc[
        ~candidates.duplicated(
            ["signal_time_utc", "direction_sign", "geometry_id"], keep="first"
        )
    ].reset_index(drop=True)
    if candidates["candidate_id"].duplicated().any():
        raise ValueError("R4 forward candidate IDs are not unique")
    return candidates


def canonical_candidate_sha(frame: pd.DataFrame) -> str:
    columns = (
        "candidate_id",
        "component_priority",
        "origin_attempt",
        "origin_variant_id",
        "regime_owner",
        "mechanic",
        "geometry_id",
        "signal_time",
        "scheduled_entry_time",
        "scheduled_deadline",
        "direction_sign",
        "direction",
        "signal_atr",
        "stop_atr",
        "target_r",
        "hold_hours",
        "parameters_json",
    )
    ordered = frame.loc[:, columns].copy()
    for column in ("signal_time", "scheduled_entry_time", "scheduled_deadline"):
        ordered[column] = ordered[column].map(lambda value: pd.Timestamp(value).isoformat())
    payload = ordered.to_json(orient="records", date_format="iso", double_precision=15)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def verify_historical_parity(frozen: FrozenR4, repo_root: Path) -> dict[str, Any]:
    bundle = frozen.data_module.load_bundle(frozen.r4_config)
    adapter_frame = build_feature_frame(bundle.bars["M5"], frozen)
    reference_frame = frozen.origin_module.prepare_frame(
        bundle.bars["M5"],
        bundle.bars["M15"],
        bundle.bars["H1"],
        bundle.bars["H4"],
        frozen.r4_config,
        frozen.micro_module,
        frozen.regime_module,
    )
    feature_checks: dict[str, bool] = {}
    for column in FEATURE_PARITY_COLUMNS:
        left = adapter_frame[column]
        right = reference_frame[column]
        if pd.api.types.is_numeric_dtype(left):
            feature_checks[column] = bool(
                np.allclose(
                    left.to_numpy(dtype=float),
                    right.to_numpy(dtype=float),
                    equal_nan=True,
                    rtol=0.0,
                    atol=0.0,
                )
            )
        else:
            feature_checks[column] = bool(left.equals(right))
    if not all(feature_checks.values()):
        raise ValueError(f"R4 historical feature parity failed: {feature_checks}")
    generated, signal_parity, audit = frozen.confirmation_module.generate_candidates(
        adapter_frame, frozen.origin_module, frozen.r4_config
    )
    artifact = pd.read_parquet(
        repo_root / frozen.package_config["source"]["r4_candidates"]
    )
    generated_sha = canonical_candidate_sha(generated)
    artifact_sha = canonical_candidate_sha(artifact)
    if generated_sha != artifact_sha:
        raise ValueError("R4 historical candidate stream changed")
    return {
        "feature_rows": int(len(adapter_frame)),
        "feature_columns_checked": list(FEATURE_PARITY_COLUMNS),
        "feature_parity": feature_checks,
        "candidate_rows": int(len(generated)),
        "candidate_canonical_sha256": generated_sha,
        "candidate_artifact_canonical_sha256": artifact_sha,
        "candidate_audit": audit,
        "signal_parity": signal_parity,
    }
