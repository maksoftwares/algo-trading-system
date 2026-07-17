from __future__ import annotations

import hashlib
import importlib.util
from itertools import product
import json
import math
from pathlib import Path
import sys
from typing import Any, Iterable, Mapping

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
BASE_PATH = (
    ROOT / ".." / "m5-microstructure-mechanics-v1" / "src" / "campaign.py"
).resolve()
MECHANICS = (
    "GC_LEADS_XAU_CATCHUP",
    "GC_IMPULSE_XAU_STALE",
    "XAU_LEADS_GC_FADE",
    "DIRECTIONAL_DISAGREEMENT_GC_AUTHORITY",
    "GAP_CONVERGENCE_IGNITION",
)
SESSIONS = ("ALL",)
_MISSING = object()


def _load_module(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


BASE = _load_module("comex_spot_leadlag_base_engine", BASE_PATH)
simulate_trade = BASE.simulate_trade
closed_drawdown = BASE.closed_drawdown
benjamini_hochberg = BASE.benjamini_hochberg


def _utc_timestamp(value: Any) -> pd.Timestamp:
    timestamp = pd.Timestamp(value)
    return (
        timestamp.tz_localize("UTC")
        if timestamp.tzinfo is None
        else timestamp.tz_convert("UTC")
    )


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(4 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _space(**values: Iterable[Any]) -> list[dict[str, Any]]:
    names = tuple(values)
    return [
        dict(zip(names, combination, strict=True))
        for combination in product(*(values[name] for name in names))
    ]


def parameter_space(mechanic: str) -> list[dict[str, Any]]:
    if mechanic == "GC_LEADS_XAU_CATCHUP":
        return _space(
            window=(1, 3, 6),
            gc_move_min=(0.10, 0.25, 0.50, 1.00),
            gap_min=(0.005, 0.015, 0.030, 0.060),
            spot_follow_max_ratio=(0.25, 0.50, 0.75, 1.00),
            spot_opposition_max=(0.00, 0.03, 0.06),
            delta_min=(-0.05, 0.00, 0.05),
            delta_source=("BAR", "CUMULATIVE"),
            volume_min=(0.00, 0.40, 0.80),
            session=SESSIONS,
        )
    if mechanic == "GC_IMPULSE_XAU_STALE":
        return _space(
            window=(1, 3),
            gc_move_min=(0.10, 0.25, 0.50, 1.00),
            spot_abs_max=(0.05, 0.10, 0.20, 0.30),
            gap_min=(0.02, 0.04, 0.07, 0.12),
            delta_min=(-0.05, 0.00, 0.05),
            delta_source=("BAR", "CUMULATIVE"),
            volume_min=(0.00, 0.40, 0.80),
            session=SESSIONS,
        )
    if mechanic == "XAU_LEADS_GC_FADE":
        return _space(
            window=(1, 3, 6),
            spot_move_min=(0.15, 0.35, 0.70, 1.20),
            lead_gap_min=(0.02, 0.04, 0.07, 0.12),
            gc_follow_max_ratio=(0.25, 0.50, 0.75, 1.00),
            rejection_location_min=(0.25, 0.40, 0.55),
            volume_max=(1.00, 2.00, 5.00),
            session=SESSIONS,
        )
    if mechanic == "DIRECTIONAL_DISAGREEMENT_GC_AUTHORITY":
        return _space(
            window=(1, 3, 6),
            gc_move_min=(0.001, 0.005, 0.010, 0.025),
            spot_move_min=(0.001, 0.005, 0.010, 0.025),
            gap_min=(0.005, 0.015, 0.030, 0.060),
            delta_min=(-0.05, 0.00, 0.05),
            delta_source=("BAR", "CUMULATIVE"),
            volume_min=(0.00, 0.40, 0.80),
            session=SESSIONS,
        )
    if mechanic == "GAP_CONVERGENCE_IGNITION":
        return _space(
            gap_window=(3, 6, 12),
            prior_gap_min=(0.02, 0.04, 0.07, 0.12),
            catchup_min=(0.05, 0.10, 0.20, 0.30),
            closure_min=(0.005, 0.015, 0.030, 0.060),
            gc_retrace_max=(0.05, 0.15, 0.30),
            delta_min=(-0.05, 0.00),
            delta_source=("BAR", "CUMULATIVE"),
            session=SESSIONS,
        )
    raise KeyError(mechanic)


def generate_manifest(
    attempts_before: int = 7093,
    policies_per_mechanic: int = 200,
    *,
    frame: pd.DataFrame | None = None,
    config: Mapping[str, Any] | None = None,
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    attempt = attempts_before
    screen: pd.DataFrame | None = None
    minimum_signals = 0
    if frame is not None:
        if config is None:
            raise ValueError("Outcome-blind coverage screening requires config")
        start, end = map(_utc_timestamp, config["windows"]["discovery"])
        screen = frame.loc[
            frame["bar_end_utc"].ge(start)
            & frame["bar_end_utc"].lt(end)
            & frame["comex_session_minute"].notna()
        ].copy()
        minimum_signals = int(
            config["research_controls"]["minimum_discovery_raw_signals_per_policy"]
        )
    for mechanic in MECHANICS:
        candidates = parameter_space(mechanic)
        ranked = sorted(
            candidates,
            key=lambda params: hashlib.sha256(
                f"{mechanic}|{json.dumps(params, sort_keys=True)}".encode("ascii")
            ).hexdigest(),
        )
        if len(ranked) < policies_per_mechanic:
            raise ValueError(f"Insufficient parameter space for {mechanic}")
        selected: list[tuple[dict[str, Any], int | None]] = []
        for params in ranked:
            raw_signals: int | None = None
            if screen is not None:
                mask, _ = signal_mask_direction(screen, mechanic, params)
                raw_signals = int(mask.sum())
                if raw_signals < minimum_signals:
                    continue
            selected.append((params, raw_signals))
            if len(selected) == policies_per_mechanic:
                break
        if len(selected) != policies_per_mechanic:
            raise ValueError(
                f"{mechanic} has only {len(selected)} outcome-blind policies with "
                f"at least {minimum_signals} discovery signals"
            )
        for params, raw_signals in selected:
            attempt += 1
            canonical = json.dumps(params, sort_keys=True, separators=(",", ":"))
            policy_id = hashlib.sha256(
                f"{mechanic}|{canonical}".encode("ascii")
            ).hexdigest()[:16]
            rows.append(
                {
                    "attempt_no": attempt,
                    "policy_id": policy_id,
                    "mechanic": mechanic,
                    "parameters_json": canonical,
                    "discovery_raw_signal_count": raw_signals,
                }
            )
    manifest = pd.DataFrame(rows)
    expected = len(MECHANICS) * policies_per_mechanic
    if len(manifest) != expected or manifest["policy_id"].nunique() != expected:
        raise ValueError("Policy manifest is incomplete or duplicated")
    return manifest


def load_comex(config: Mapping[str, Any]) -> tuple[pd.DataFrame, dict[str, Any]]:
    source = config["comex_source"]
    cache = Path(source["cache"])
    manifest_path = Path(source["manifest"])
    if not cache.is_file() or not manifest_path.is_file():
        raise FileNotFoundError("Locked COMEX cache or manifest is unavailable")
    actual_cache_hash = sha256_file(cache)
    actual_manifest_hash = sha256_file(manifest_path)
    if actual_cache_hash != source["cache_sha256"]:
        raise ValueError("COMEX cache SHA-256 mismatch")
    if actual_manifest_hash != source["manifest_sha256"]:
        raise ValueError("COMEX manifest SHA-256 mismatch")
    columns = [
        "bucket",
        "close",
        "volume",
        "signed_volume",
        "session_date",
        "session_bar_index",
        "cumulative_delta_ratio",
        "cumulative_volume_ratio",
        "available_time_utc",
    ]
    frame = pd.read_parquet(cache, columns=columns)
    if len(frame) != int(source["expected_rows"]):
        raise ValueError(f"Expected {source['expected_rows']} COMEX rows, found {len(frame)}")
    frame = frame.copy()
    frame["bucket"] = pd.to_datetime(frame["bucket"], utc=True)
    frame["available_time_utc"] = pd.to_datetime(frame["available_time_utc"], utc=True)
    frame = frame.sort_values("available_time_utc", kind="mergesort").reset_index(drop=True)
    if frame["available_time_utc"].duplicated().any():
        raise ValueError("Duplicate COMEX availability timestamps")
    if not frame["available_time_utc"].sub(frame["bucket"]).eq(pd.Timedelta(minutes=5)).all():
        raise ValueError("COMEX bars are not available exactly after completion")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("cache_sha256") != source["cache_sha256"]:
        raise ValueError("COMEX manifest does not identify the locked cache")
    evidence = {
        "cache": str(cache),
        "manifest": str(manifest_path),
        "cache_sha256": actual_cache_hash,
        "manifest_sha256": actual_manifest_hash,
        "rows": int(len(frame)),
        "sessions": int(frame["session_date"].nunique()),
        "first_available": frame["available_time_utc"].min().isoformat(),
        "last_available": frame["available_time_utc"].max().isoformat(),
        "network_request_made": False,
        "paid_data_request_made": False,
    }
    return frame, evidence


def prepare_features(
    m5: pd.DataFrame,
    comex: pd.DataFrame,
    config: Mapping[str, Any],
) -> pd.DataFrame:
    required_spot = {
        "bar_start_utc",
        "bar_end_utc",
        "bid_open",
        "bid_high",
        "bid_low",
        "bid_close",
        "ask_open",
        "ask_high",
        "ask_low",
        "ask_close",
        "mid_open",
        "mid_high",
        "mid_low",
        "mid_close",
    }
    missing = sorted(required_spot.difference(m5.columns))
    if missing:
        raise ValueError(f"Spot M5 frame is missing {missing}")
    if not bool(config["comex_source"]["returns_reset_each_session"]):
        raise ValueError("Session-reset futures returns are mandatory")
    if bool(config["comex_source"]["overnight_basis_authorized"]):
        raise ValueError("Overnight futures/spot basis is prohibited")

    frame = m5.copy().sort_values("bar_start_utc", kind="mergesort").reset_index(drop=True)
    frame["bar_start_utc"] = pd.to_datetime(frame["bar_start_utc"], utc=True)
    frame["bar_end_utc"] = pd.to_datetime(frame["bar_end_utc"], utc=True)
    if frame["bar_start_utc"].duplicated().any():
        raise ValueError("Duplicate spot M5 bars")
    frame["atr14"] = BASE.atr(frame, int(config["features"]["atr_period"]))
    span = (frame["mid_high"] - frame["mid_low"]).replace(0.0, np.nan)
    frame["spot_close_location"] = (frame["mid_close"] - frame["mid_low"]) / span

    gc = comex.copy().rename(
        columns={
            "close": "gc_close",
            "volume": "gc_volume",
            "signed_volume": "gc_signed_volume",
            "cumulative_delta_ratio": "gc_cumulative_delta_ratio",
            "cumulative_volume_ratio": "gc_cumulative_volume_ratio",
        }
    )
    spot_context = frame[
        ["bar_end_utc", "mid_close", "atr14", "spot_close_location"]
    ]
    aligned = gc.merge(
        spot_context,
        left_on="available_time_utc",
        right_on="bar_end_utc",
        how="inner",
        validate="one_to_one",
    ).sort_values(["session_date", "available_time_utc"], kind="mergesort")
    if len(aligned) < int(config["comex_source"]["minimum_aligned_rows"]):
        raise ValueError(f"Only {len(aligned)} COMEX bars aligned to executable spot")
    aligned["gc_bar_delta_ratio"] = (
        aligned["gc_signed_volume"] / aligned["gc_volume"].replace(0.0, np.nan)
    )
    local = aligned["available_time_utc"].dt.tz_convert("America/New_York")
    aligned["comex_session_minute"] = local.dt.hour * 60 + local.dt.minute
    grouped = aligned.groupby("session_date", sort=False, observed=True)
    feature_columns = [
        "gc_bar_delta_ratio",
        "gc_cumulative_delta_ratio",
        "gc_cumulative_volume_ratio",
        "comex_session_minute",
    ]
    for window in (int(value) for value in config["features"]["return_windows_bars"]):
        previous_time = grouped["available_time_utc"].shift(window)
        contiguous = aligned["available_time_utc"].sub(previous_time).eq(
            pd.Timedelta(minutes=5 * window)
        )
        previous_gc = grouped["gc_close"].shift(window)
        previous_spot = grouped["mid_close"].shift(window)
        denominator = aligned["atr14"].replace(0.0, np.nan)
        gc_return = ((aligned["gc_close"] - previous_gc) / denominator).where(contiguous)
        spot_return = ((aligned["mid_close"] - previous_spot) / denominator).where(contiguous)
        gap = gc_return - spot_return
        aligned[f"gc_return_{window}_atr"] = gc_return
        aligned[f"spot_return_{window}_atr"] = spot_return
        aligned[f"relative_gap_{window}_atr"] = gap
        prior_contiguous = aligned["available_time_utc"].sub(
            grouped["available_time_utc"].shift(1)
        ).eq(pd.Timedelta(minutes=5))
        aligned[f"prior_relative_gap_{window}_atr"] = grouped[
            f"relative_gap_{window}_atr"
        ].shift(1).where(prior_contiguous)
        feature_columns.extend(
            [
                f"gc_return_{window}_atr",
                f"spot_return_{window}_atr",
                f"relative_gap_{window}_atr",
                f"prior_relative_gap_{window}_atr",
            ]
        )

    aligned_features = aligned[["bar_end_utc", *feature_columns]]
    frame = frame.merge(
        aligned_features,
        on="bar_end_utc",
        how="left",
        validate="one_to_one",
    ).sort_values("bar_start_utc", kind="mergesort").reset_index(drop=True)
    frame.attrs["comex_aligned_rows"] = int(len(aligned))
    frame.attrs["comex_sessions"] = int(aligned["session_date"].nunique())
    return frame


def _session_mask(frame: pd.DataFrame, session: str) -> pd.Series:
    minute = frame["comex_session_minute"]
    if session == "ALL":
        return minute.between(8 * 60 + 25, 13 * 60 + 30, inclusive="both")
    bounds = {
        "OPEN": (8 * 60 + 25, 10 * 60),
        "MID": (10 * 60, 11 * 60 + 45),
        "LATE": (11 * 60 + 45, 13 * 60 + 31),
    }
    if session not in bounds:
        raise KeyError(session)
    start, end = bounds[session]
    return minute.ge(start) & minute.lt(end)


def _delta(frame: pd.DataFrame, source: str) -> pd.Series:
    if source == "BAR":
        return frame["gc_bar_delta_ratio"]
    if source == "CUMULATIVE":
        return frame["gc_cumulative_delta_ratio"]
    raise KeyError(source)


def _signed_location(frame: pd.DataFrame, direction: pd.Series) -> pd.Series:
    return pd.Series(
        np.where(
            direction > 0,
            frame["spot_close_location"],
            1.0 - frame["spot_close_location"],
        ),
        index=frame.index,
    )


def signal_mask_direction(
    frame: pd.DataFrame,
    mechanic: str,
    params: Mapping[str, Any],
) -> tuple[pd.Series, pd.Series]:
    session = _session_mask(frame, str(params["session"]))
    if mechanic == "GC_LEADS_XAU_CATCHUP":
        window = int(params["window"])
        gc_return = frame[f"gc_return_{window}_atr"]
        spot_return = frame[f"spot_return_{window}_atr"]
        gap = frame[f"relative_gap_{window}_atr"]
        direction = pd.Series(np.sign(gc_return.fillna(0.0)).astype(int), index=frame.index)
        signed_gc = direction * gc_return
        signed_spot = direction * spot_return
        mask = (
            signed_gc.ge(float(params["gc_move_min"]))
            & (direction * gap).ge(float(params["gap_min"]))
            & signed_spot.le(signed_gc * float(params["spot_follow_max_ratio"]))
            & signed_spot.ge(-float(params["spot_opposition_max"]))
            & (direction * _delta(frame, str(params["delta_source"]))).ge(
                float(params["delta_min"])
            )
            & frame["gc_cumulative_volume_ratio"].ge(float(params["volume_min"]))
        )
    elif mechanic == "GC_IMPULSE_XAU_STALE":
        window = int(params["window"])
        gc_return = frame[f"gc_return_{window}_atr"]
        spot_return = frame[f"spot_return_{window}_atr"]
        gap = frame[f"relative_gap_{window}_atr"]
        direction = pd.Series(np.sign(gc_return.fillna(0.0)).astype(int), index=frame.index)
        mask = (
            gc_return.abs().ge(float(params["gc_move_min"]))
            & spot_return.abs().le(float(params["spot_abs_max"]))
            & (direction * gap).ge(float(params["gap_min"]))
            & (direction * _delta(frame, str(params["delta_source"]))).ge(
                float(params["delta_min"])
            )
            & frame["gc_cumulative_volume_ratio"].ge(float(params["volume_min"]))
        )
    elif mechanic == "XAU_LEADS_GC_FADE":
        window = int(params["window"])
        gc_return = frame[f"gc_return_{window}_atr"]
        spot_return = frame[f"spot_return_{window}_atr"]
        leader = pd.Series(np.sign(spot_return.fillna(0.0)).astype(int), index=frame.index)
        direction = -leader
        signed_spot = leader * spot_return
        signed_gc = leader * gc_return
        mask = (
            signed_spot.ge(float(params["spot_move_min"]))
            & (leader * (spot_return - gc_return)).ge(float(params["lead_gap_min"]))
            & signed_gc.ge(0.0)
            & signed_gc.le(signed_spot * float(params["gc_follow_max_ratio"]))
            & _signed_location(frame, direction).ge(
                float(params["rejection_location_min"])
            )
            & frame["gc_cumulative_volume_ratio"].le(float(params["volume_max"]))
        )
    elif mechanic == "DIRECTIONAL_DISAGREEMENT_GC_AUTHORITY":
        window = int(params["window"])
        gc_return = frame[f"gc_return_{window}_atr"]
        spot_return = frame[f"spot_return_{window}_atr"]
        gap = frame[f"relative_gap_{window}_atr"]
        direction = pd.Series(np.sign(gc_return.fillna(0.0)).astype(int), index=frame.index)
        mask = (
            gc_return.abs().ge(float(params["gc_move_min"]))
            & spot_return.abs().ge(float(params["spot_move_min"]))
            & (gc_return * spot_return).lt(0.0)
            & (direction * gap).ge(float(params["gap_min"]))
            & (direction * _delta(frame, str(params["delta_source"]))).ge(
                float(params["delta_min"])
            )
            & frame["gc_cumulative_volume_ratio"].ge(float(params["volume_min"]))
        )
    elif mechanic == "GAP_CONVERGENCE_IGNITION":
        window = int(params["gap_window"])
        prior_gap = frame[f"prior_relative_gap_{window}_atr"]
        current_gap = frame[f"relative_gap_{window}_atr"]
        direction = pd.Series(np.sign(prior_gap.fillna(0.0)).astype(int), index=frame.index)
        spot_current = frame["spot_return_1_atr"]
        gc_current = frame["gc_return_1_atr"]
        closure = direction * (prior_gap - current_gap)
        mask = (
            prior_gap.abs().ge(float(params["prior_gap_min"]))
            & (direction * current_gap).ge(0.0)
            & (direction * spot_current).ge(float(params["catchup_min"]))
            & closure.ge(float(params["closure_min"]))
            & (direction * gc_current).ge(-float(params["gc_retrace_max"]))
            & (direction * _delta(frame, str(params["delta_source"]))).ge(
                float(params["delta_min"])
            )
        )
    else:
        raise KeyError(mechanic)
    valid = (
        mask.fillna(False)
        & session.fillna(False)
        & direction.ne(0)
        & np.isfinite(frame["atr14"])
        & frame["atr14"].gt(0.0)
    )
    return valid, direction.astype(int)


def _select_policy_trades(
    frame: pd.DataFrame,
    arrays: Mapping[str, Any],
    policy: Any,
    config: Mapping[str, Any],
    stage_start: pd.Timestamp,
    stage_end: pd.Timestamp,
    outcome_cache: dict[tuple[str, int, int], Any],
) -> pd.DataFrame:
    params = json.loads(policy.parameters_json)
    mask, direction = signal_mask_direction(frame, str(policy.mechanic), params)
    stage_mask = frame["bar_end_utc"].ge(stage_start) & frame["bar_end_utc"].lt(stage_end)
    indices = np.flatnonzero((mask & stage_mask).to_numpy())
    geometry = config["mechanics"][str(policy.mechanic)]
    execution = config["execution"]
    selected: list[dict[str, Any]] = []
    position_until = pd.Timestamp.min.tz_localize("UTC")
    cooldown_until = pd.Timestamp.min.tz_localize("UTC")
    daily_count: dict[Any, int] = {}
    cooldown = pd.Timedelta(minutes=5 * int(execution["cooldown_bars"]))
    diagnostic_columns = (
        "gc_return_1_atr",
        "spot_return_1_atr",
        "relative_gap_1_atr",
        "gc_bar_delta_ratio",
        "gc_cumulative_delta_ratio",
        "gc_cumulative_volume_ratio",
    )
    for signal_index in indices:
        signal_direction = int(direction.iat[int(signal_index)])
        key = (str(policy.mechanic), int(signal_index), signal_direction)
        outcome = outcome_cache.get(key, _MISSING)
        if outcome is _MISSING:
            outcome = BASE.simulate_trade(
                arrays,
                int(signal_index),
                signal_direction,
                geometry,
                execution,
                stage_end,
            )
            outcome_cache[key] = outcome
        if outcome is None:
            continue
        entry_time = outcome["entry_time"]
        if entry_time < position_until or entry_time < cooldown_until:
            continue
        day = entry_time.date()
        if daily_count.get(day, 0) >= int(execution["maximum_trades_per_policy_utc_day"]):
            continue
        record = {
            "attempt_no": int(policy.attempt_no),
            "policy_id": str(policy.policy_id),
            "mechanic": str(policy.mechanic),
            **outcome,
        }
        for column in diagnostic_columns:
            record[column] = float(frame[column].iat[int(signal_index)])
        selected.append(record)
        position_until = outcome["exit_time"]
        cooldown_until = outcome["exit_time"] + cooldown
        daily_count[day] = daily_count.get(day, 0) + 1
    if not selected:
        return pd.DataFrame()
    return pd.DataFrame(selected).sort_values("entry_time", kind="mergesort").reset_index(drop=True)


def evaluate_policies(
    frame: pd.DataFrame,
    manifest: pd.DataFrame,
    config: Mapping[str, Any],
    stage: str,
) -> tuple[pd.DataFrame, dict[tuple[str, int, int], Any]]:
    start, end = map(_utc_timestamp, config["windows"][stage])
    arrays = BASE.execution_arrays(frame)
    cache: dict[tuple[str, int, int], Any] = {}
    rows: list[dict[str, Any]] = []
    for policy in manifest.itertuples(index=False):
        trades = _select_policy_trades(
            frame, arrays, policy, config, start, end, cache
        )
        values = BASE.summarize(
            trades,
            frame,
            start,
            end,
            config["segments"][stage],
            int(config["gates"][stage]["top_winners_removed"]),
        )
        rows.append(
            {
                "attempt_no": int(policy.attempt_no),
                "policy_id": str(policy.policy_id),
                "mechanic": str(policy.mechanic),
                "parameters_json": str(policy.parameters_json),
                **values,
            }
        )
    metrics = pd.DataFrame(rows)
    metrics["fdr_qvalue"] = BASE.benjamini_hochberg(metrics["daily_pvalue"])
    checks_list: list[dict[str, bool]] = []
    passes: list[bool] = []
    for row in metrics.to_dict(orient="records"):
        checks = BASE.gate_checks(row, config["gates"][stage])
        checks_list.append(checks)
        passes.append(all(checks.values()))
    metrics["gate_checks_json"] = [
        json.dumps(checks, sort_keys=True, separators=(",", ":"))
        for checks in checks_list
    ]
    metrics["gate_pass"] = passes
    return metrics, cache


def select_advancers(metrics: pd.DataFrame, gate: Mapping[str, Any]) -> pd.DataFrame:
    return BASE.select_advancers(metrics, gate)


def selected_trade_ledger(
    frame: pd.DataFrame,
    selected_manifest: pd.DataFrame,
    config: Mapping[str, Any],
    stage: str,
    cache: dict[tuple[str, int, int], Any] | None = None,
) -> pd.DataFrame:
    if selected_manifest.empty:
        return pd.DataFrame()
    start, end = map(_utc_timestamp, config["windows"][stage])
    arrays = BASE.execution_arrays(frame)
    outcome_cache = cache if cache is not None else {}
    frames: list[pd.DataFrame] = []
    for policy in selected_manifest.itertuples(index=False):
        trades = _select_policy_trades(
            frame, arrays, policy, config, start, end, outcome_cache
        )
        if not trades.empty:
            frames.append(trades.assign(stage=stage))
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


def signal_census(
    frame: pd.DataFrame,
    manifest: pd.DataFrame,
    config: Mapping[str, Any],
) -> dict[str, Any]:
    windows = {
        name: frame["bar_end_utc"].ge(_utc_timestamp(bounds[0]))
        & frame["bar_end_utc"].lt(_utc_timestamp(bounds[1]))
        for name, bounds in config["windows"].items()
    }
    rows: list[dict[str, Any]] = []
    for policy in manifest.itertuples(index=False):
        params = json.loads(policy.parameters_json)
        mask, _ = signal_mask_direction(frame, str(policy.mechanic), params)
        row = {
            "policy_id": str(policy.policy_id),
            "mechanic": str(policy.mechanic),
            "all": int(mask.sum()),
        }
        row.update({name: int((mask & stage_mask).sum()) for name, stage_mask in windows.items()})
        rows.append(row)
    counts = pd.DataFrame(rows)
    mechanics: dict[str, Any] = {}
    for mechanic, group in counts.groupby("mechanic", sort=True, observed=True):
        mechanics[str(mechanic)] = {
            stage: {
                "minimum": int(group[stage].min()),
                "median": float(group[stage].median()),
                "maximum": int(group[stage].max()),
                "zero_policies": int(group[stage].eq(0).sum()),
            }
            for stage in ("all", *config["windows"].keys())
        }
    quantiles = (0.10, 0.25, 0.50, 0.75, 0.90, 0.95, 0.99)
    feature_distribution: dict[str, Any] = {}
    discovery_mask = windows["discovery"]
    for window in (int(value) for value in config["features"]["return_windows_bars"]):
        gc_values = frame.loc[discovery_mask, f"gc_return_{window}_atr"].dropna()
        spot_values = frame.loc[discovery_mask, f"spot_return_{window}_atr"].dropna()
        gap_values = frame.loc[discovery_mask, f"relative_gap_{window}_atr"].dropna()
        paired = pd.concat([gc_values.rename("gc"), spot_values.rename("spot")], axis=1).dropna()
        feature_distribution[str(window)] = {
            "rows": int(len(gap_values)),
            "gc_abs_quantiles": {
                str(value): float(gc_values.abs().quantile(value)) for value in quantiles
            },
            "spot_abs_quantiles": {
                str(value): float(spot_values.abs().quantile(value)) for value in quantiles
            },
            "gap_abs_quantiles": {
                str(value): float(gap_values.abs().quantile(value)) for value in quantiles
            },
            "gc_spot_return_correlation": float(paired["gc"].corr(paired["spot"])),
            "opposite_sign_share": float((paired["gc"] * paired["spot"] < 0.0).mean()),
        }
    return {
        "schema_version": "xauusd_comex_spot_leadlag_signal_census_v1",
        "label_or_outcome_columns_read": False,
        "policy_count": int(len(counts)),
        "aligned_comex_rows": int(frame.attrs.get("comex_aligned_rows", 0)),
        "comex_sessions": int(frame.attrs.get("comex_sessions", 0)),
        "discovery_feature_distribution": feature_distribution,
        "mechanics": mechanics,
    }
