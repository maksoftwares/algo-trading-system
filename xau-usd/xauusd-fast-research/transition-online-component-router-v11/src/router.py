from __future__ import annotations

from dataclasses import dataclass
import hashlib
from itertools import product
import json
from typing import Any, Mapping

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class ShadowStats:
    count: int
    net_r: float
    mean_r: float
    profit_factor: float
    drawdown_r: float


def _space(**values: list[Any]) -> list[dict[str, Any]]:
    keys = tuple(values)
    return [
        dict(zip(keys, combination, strict=True))
        for combination in product(*(values[key] for key in keys))
    ]


def _parameter_space(mechanic: str, config: Mapping[str, Any]) -> list[dict[str, Any]]:
    space = config["policy_space"]
    common = {
        "lookback_days": space["lookback_days"],
        "minimum_history": space["minimum_history"],
        "cold_start": space["cold_start"],
        "weak_multiplier": space["weak_multiplier"],
    }
    if mechanic == "TRAILING_MEAN_GATE":
        return _space(**common, threshold=space["mean_threshold"])
    if mechanic == "TRAILING_PF_GATE":
        return _space(**common, threshold=space["pf_threshold"])
    if mechanic == "BAYESIAN_SHRINKAGE_WEIGHT":
        return _space(
            **common,
            prior_mean=space["bayesian_prior_mean"],
            prior_strength=space["bayesian_prior_strength"],
            lower_threshold=space["bayesian_lower_threshold"],
            upper_threshold=space["bayesian_upper_threshold"],
        )
    if mechanic == "COMPONENT_RANK_GATE":
        return _space(
            **common,
            rank_metric=space["rank_metric"],
            top_k=space["rank_top_k"],
        )
    if mechanic == "TRAILING_DRAWDOWN_GATE":
        return _space(**common, threshold=space["drawdown_threshold_r"])
    raise KeyError(mechanic)


def generate_manifest(config: Mapping[str, Any]) -> pd.DataFrame:
    selection = config["selection"]
    seed = str(selection["hash_selection_seed"])
    per_mechanic = int(selection["attempts_per_mechanic"])
    attempt = int(selection["attempt_first"])
    rows: list[dict[str, Any]] = []
    for mechanic in selection["mechanics"]:
        definitions: list[tuple[str, str, dict[str, Any]]] = []
        for params in _parameter_space(str(mechanic), config):
            canonical = json.dumps(params, sort_keys=True, separators=(",", ":"))
            digest = hashlib.sha256(
                f"{seed}|{mechanic}|{canonical}".encode("ascii")
            ).hexdigest()
            definitions.append((digest, canonical, params))
        if len(definitions) < per_mechanic:
            raise ValueError(f"Insufficient definitions for {mechanic}")
        for digest, canonical, _ in sorted(definitions)[:per_mechanic]:
            rows.append(
                {
                    "attempt_no": attempt,
                    "router_id": digest[:16],
                    "mechanic": str(mechanic),
                    "parameters_json": canonical,
                }
            )
            attempt += 1
    result = pd.DataFrame(rows)
    if len(result) != int(selection["total_attempts"]):
        raise ValueError("Router manifest count differs from contract")
    if int(result["attempt_no"].iat[-1]) != int(selection["attempt_last"]):
        raise ValueError("Router attempt range differs from contract")
    if result["router_id"].duplicated().any():
        raise ValueError("Duplicate router definition")
    return result


def _stats(values: np.ndarray) -> ShadowStats:
    if not len(values):
        return ShadowStats(0, 0.0, 0.0, 0.0, 0.0)
    gains = float(values[values > 0.0].sum())
    losses = float(-values[values < 0.0].sum())
    profit_factor = float("inf") if losses == 0.0 and gains > 0.0 else (
        gains / losses if losses > 0.0 else 0.0
    )
    equity = np.concatenate(([0.0], np.cumsum(values)))
    drawdown = float(np.max(np.maximum.accumulate(equity) - equity))
    return ShadowStats(
        count=int(len(values)),
        net_r=float(values.sum()),
        mean_r=float(values.mean()),
        profit_factor=profit_factor,
        drawdown_r=drawdown,
    )


def build_shadow_cache(
    component_trades: pd.DataFrame,
    lookbacks: list[int],
    components: list[int],
) -> dict[tuple[int, int, int], ShadowStats]:
    trades = component_trades.copy()
    trades["entry_time"] = pd.to_datetime(trades["entry_time"], utc=True)
    trades["exit_time"] = pd.to_datetime(trades["exit_time"], utc=True)
    entries = trades["entry_time"].drop_duplicates().sort_values()
    source: dict[int, tuple[np.ndarray, np.ndarray]] = {}
    for component in components:
        group = trades.loc[trades["attempt_no"].eq(component)].sort_values(
            "exit_time", kind="mergesort"
        )
        source[component] = (
            pd.DatetimeIndex(group["exit_time"]).as_unit("ns").asi8,
            group["stress_net_r"].astype(float).to_numpy(),
        )
    cache: dict[tuple[int, int, int], ShadowStats] = {}
    for entry in entries:
        entry_ns = int(pd.Timestamp(entry).value)
        for component in components:
            exits, values = source[component]
            strict_end = int(np.searchsorted(exits, entry_ns, side="left"))
            for lookback in lookbacks:
                start_ns = entry_ns - int(pd.Timedelta(days=int(lookback)).value)
                start = int(np.searchsorted(exits, start_ns, side="left"))
                cache[(entry_ns, component, int(lookback))] = _stats(
                    values[start:strict_end]
                )
    return cache


def _cold_multiplier(label: str) -> float:
    values = {"BASE": 1.0, "HALF": 0.5, "OFF": 0.0}
    try:
        return values[label]
    except KeyError as exc:
        raise KeyError(f"Unknown cold-start policy: {label}") from exc


def _rank_score(stats: ShadowStats, metric: str) -> float:
    if metric == "MEAN":
        return stats.mean_r
    if metric == "PF":
        return stats.profit_factor
    if metric == "BAYESIAN_MEAN":
        return (stats.net_r + 0.05 * 10.0) / (stats.count + 10.0)
    raise KeyError(metric)


def route_multiplier(
    component: int,
    entry_ns: int,
    mechanic: str,
    params: Mapping[str, Any],
    components: list[int],
    cache: Mapping[tuple[int, int, int], ShadowStats],
) -> tuple[float, str, ShadowStats]:
    lookback = int(params["lookback_days"])
    minimum = int(params["minimum_history"])
    stats = cache[(entry_ns, component, lookback)]
    if stats.count < minimum:
        return _cold_multiplier(str(params["cold_start"])), "COLD_START", stats
    weak = float(params["weak_multiplier"])
    if mechanic == "TRAILING_MEAN_GATE":
        passed = stats.mean_r >= float(params["threshold"])
    elif mechanic == "TRAILING_PF_GATE":
        passed = stats.profit_factor >= float(params["threshold"])
    elif mechanic == "TRAILING_DRAWDOWN_GATE":
        passed = stats.drawdown_r <= float(params["threshold"])
    elif mechanic == "BAYESIAN_SHRINKAGE_WEIGHT":
        posterior = (
            stats.net_r
            + float(params["prior_mean"]) * float(params["prior_strength"])
        ) / (stats.count + float(params["prior_strength"]))
        lower = float(params["lower_threshold"])
        upper = float(params["upper_threshold"])
        if upper <= lower:
            raise ValueError("Bayesian upper threshold must exceed lower threshold")
        fraction = float(np.clip((posterior - lower) / (upper - lower), 0.0, 1.0))
        multiplier = weak + (1.0 - weak) * fraction
        return multiplier, "BAYESIAN_WEIGHT", stats
    elif mechanic == "COMPONENT_RANK_GATE":
        mature: list[tuple[float, int]] = []
        for candidate in components:
            candidate_stats = cache[(entry_ns, candidate, lookback)]
            if candidate_stats.count >= minimum:
                mature.append(
                    (_rank_score(candidate_stats, str(params["rank_metric"])), candidate)
                )
        ranked = [
            candidate
            for _, candidate in sorted(mature, key=lambda item: (-item[0], item[1]))
        ]
        passed = component in ranked[: int(params["top_k"])]
    else:
        raise KeyError(mechanic)
    return (1.0 if passed else weak), ("PASS" if passed else "WEAK"), stats


def route_candidates(
    component_trades: pd.DataFrame,
    policy: Any,
    base_weights: Mapping[int, float],
    cache: Mapping[tuple[int, int, int], ShadowStats] | None = None,
) -> pd.DataFrame:
    params = json.loads(str(policy.parameters_json))
    components = sorted(int(value) for value in base_weights)
    if cache is None:
        cache = build_shadow_cache(
            component_trades, [int(params["lookback_days"])], components
        )
    ascending = str(policy.tie_priority) == "ATTEMPT_ASCENDING"
    if not ascending and str(policy.tie_priority) != "ATTEMPT_DESCENDING":
        raise KeyError(policy.tie_priority)
    ordered = component_trades.sort_values(
        ["entry_time", "attempt_no"],
        ascending=[True, ascending],
        kind="mergesort",
    )
    rows: list[dict[str, Any]] = []
    for trade in ordered.itertuples(index=False):
        row = trade._asdict()
        component = int(row["attempt_no"])
        entry_ns = int(pd.Timestamp(row["entry_time"]).value)
        multiplier, reason, stats = route_multiplier(
            component,
            entry_ns,
            str(policy.mechanic),
            params,
            components,
            cache,
        )
        row["component_attempt_no"] = component
        row["component_stress_net_r"] = float(row["stress_net_r"])
        row["component_gross_r"] = float(row["gross_r"])
        row["shadow_count"] = stats.count
        row["shadow_mean_r"] = stats.mean_r
        row["shadow_profit_factor"] = stats.profit_factor
        row["shadow_drawdown_r"] = stats.drawdown_r
        row["route_multiplier"] = multiplier
        row["route_reason"] = reason
        row["risk_weight"] = float(base_weights[component]) * multiplier
        row["stress_net_r"] = float(row["stress_net_r"]) * row["risk_weight"]
        row["gross_r"] = float(row["gross_r"]) * row["risk_weight"]
        row["attempt_no"] = int(policy.attempt_no)
        row["router_id"] = str(policy.router_id)
        row["router_mechanic"] = str(policy.mechanic)
        rows.append(row)
    return pd.DataFrame(rows)


def build_routed_trades(
    component_trades: pd.DataFrame,
    policy: Any,
    base_weights: Mapping[int, float],
    maximum_daily: int,
    cache: Mapping[tuple[int, int, int], ShadowStats] | None = None,
) -> pd.DataFrame:
    routed = route_candidates(component_trades, policy, base_weights, cache)
    routed = routed.loc[routed["risk_weight"].gt(0.0)]
    position_until = pd.Timestamp.min.tz_localize("UTC")
    daily_count: dict[Any, int] = {}
    rows: list[dict[str, Any]] = []
    for trade in routed.itertuples(index=False):
        entry = pd.Timestamp(trade.entry_time)
        if entry < position_until:
            continue
        day = entry.date()
        if daily_count.get(day, 0) >= maximum_daily:
            continue
        rows.append(trade._asdict())
        position_until = pd.Timestamp(trade.exit_time)
        daily_count[day] = daily_count.get(day, 0) + 1
    return pd.DataFrame(rows).reset_index(drop=True) if rows else routed.iloc[:0].copy()
