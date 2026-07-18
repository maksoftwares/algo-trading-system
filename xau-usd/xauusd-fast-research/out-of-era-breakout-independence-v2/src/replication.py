from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys
from typing import Any, Mapping

import numpy as np
import pandas as pd
from scipy import stats


PACKAGE = Path(__file__).resolve().parents[1]
FAST_RESEARCH = PACKAGE.parent


def _load_module(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


UPSTREAM = _load_module(
    "out_of_era_breakout_upstream_replication",
    FAST_RESEARCH / "out-of-era-replication-v1" / "src" / "replication.py",
)
R1 = UPSTREAM.R1
COMPRESSION = _load_module(
    "out_of_era_breakout_compression_exact",
    FAST_RESEARCH / "mt5-compression-portability-v1" / "src" / "portability.py",
)


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_side_specific_m5(replay_root: Path, months: list[str]) -> pd.DataFrame:
    return UPSTREAM.load_side_specific_m5(replay_root, months)


def run_r1_variant(
    m5: pd.DataFrame,
    source_config: Mapping[str, Any],
    candidate_id: str,
) -> pd.DataFrame:
    d1, h4 = R1.BASE.prepare_signal_bars(m5, source_config["signal"])
    enriched, _ = R1.attach_r1_regime(
        m5,
        d1,
        h4,
        source_config["signal"],
        source_config["regime"],
    )
    candidates = R1.generate_r1_candidates(enriched, source_config["signal"])
    _, all_trades = R1.BASE.simulate_candidates(
        m5, candidates, source_config["execution"]
    )
    settings = source_config["policies"]["PORTFOLIO_CONSTRAINED_PRIMARY"]
    trades = R1.BASE.apply_policy(
        all_trades, "PORTFOLIO_CONSTRAINED_PRIMARY", settings
    )
    if trades.empty:
        return pd.DataFrame()
    result = trades.copy()
    if "candidate_id" in result:
        result["source_candidate_id"] = result["candidate_id"].astype(str)
    result["candidate_id"] = candidate_id
    result["source_policy_id"] = "PORTFOLIO_CONSTRAINED_PRIMARY"
    return result


def run_compression(
    m5: pd.DataFrame,
    source_config: Mapping[str, Any],
    candidate_id: str,
) -> pd.DataFrame:
    _, h4 = COMPRESSION.prepare_signal_bars(m5, source_config["signal"])
    candidates = COMPRESSION.generate_candidates(h4, source_config["signal"])
    _, all_trades = COMPRESSION.simulate_candidates(
        m5, candidates, source_config["execution"]
    )
    settings = source_config["policies"]["PORTFOLIO_CONSTRAINED_PRIMARY"]
    trades = COMPRESSION.apply_policy(
        all_trades, "PORTFOLIO_CONSTRAINED_PRIMARY", settings
    )
    if trades.empty:
        return pd.DataFrame()
    result = trades.copy()
    if "candidate_id" in result:
        result["source_candidate_id"] = result["candidate_id"].astype(str)
    result["candidate_id"] = candidate_id
    result["source_policy_id"] = "PORTFOLIO_CONSTRAINED_PRIMARY"
    return result


def run_candidate(
    m5: pd.DataFrame,
    candidate: Mapping[str, Any],
    source_config: Mapping[str, Any],
) -> pd.DataFrame:
    engine = str(candidate["engine"])
    candidate_id = str(candidate["candidate_id"])
    if engine == "R1_REGIME_BREAKOUT":
        return run_r1_variant(m5, source_config, candidate_id)
    if engine == "COMPRESSION_BREAKOUT":
        return run_compression(m5, source_config, candidate_id)
    raise KeyError(engine)


def profit_factor(values: pd.Series) -> float:
    gains = float(values.loc[values > 0.0].sum())
    losses = float(-values.loc[values < 0.0].sum())
    if losses == 0.0:
        return float("inf") if gains > 0.0 else 0.0
    return gains / losses


def closed_drawdown(values: pd.Series) -> float:
    equity = np.concatenate(
        ([0.0], values.fillna(0.0).to_numpy(dtype=float).cumsum())
    )
    peaks = np.maximum.accumulate(equity)
    return float(np.max(peaks - equity)) if len(equity) else 0.0


def daily_values(
    trades: pd.DataFrame, source_days: pd.DatetimeIndex
) -> pd.Series:
    if trades.empty:
        return pd.Series(0.0, index=source_days, dtype=float)
    observed = trades.assign(
        source_day=pd.to_datetime(trades["entry_time"], utc=True).dt.floor("D")
    ).groupby("source_day", sort=True)["stress_net_r"].sum()
    return observed.reindex(source_days, fill_value=0.0).astype(float)


def one_sided_daily_pvalue(
    trades: pd.DataFrame, source_days: pd.DatetimeIndex
) -> float:
    values = daily_values(trades, source_days).to_numpy(dtype=float)
    if len(values) < 2 or float(values.mean()) <= 0.0:
        return 1.0
    standard = float(values.std(ddof=1))
    if standard == 0.0:
        return 0.0
    result = stats.ttest_1samp(values, 0.0, alternative="greater")
    return float(result.pvalue) if np.isfinite(result.pvalue) else 1.0


def holm_adjust(pvalues: Mapping[str, float]) -> dict[str, float]:
    ordered = sorted(pvalues, key=lambda key: (float(pvalues[key]), key))
    count = len(ordered)
    running = 0.0
    adjusted: dict[str, float] = {}
    for rank, key in enumerate(ordered):
        running = max(running, (count - rank) * float(pvalues[key]))
        adjusted[key] = min(1.0, running)
    return adjusted


def summarize(
    candidate_id: str,
    trades: pd.DataFrame,
    gate: Mapping[str, Any],
    source_days: pd.DatetimeIndex,
) -> dict[str, Any]:
    values = (
        trades["stress_net_r"].astype(float)
        if not trades.empty
        else pd.Series(dtype=float)
    )
    yearly = (
        trades.assign(
            year=pd.to_datetime(trades["entry_time"], utc=True).dt.year
        ).groupby("year", sort=True)["stress_net_r"].sum()
        if not trades.empty
        else pd.Series(dtype=float)
    )
    removed = values.drop(
        values.nlargest(min(int(gate["top_winners_removed"]), len(values))).index
    )
    return {
        "candidate_id": candidate_id,
        "trades": int(len(trades)),
        "source_days": int(len(source_days)),
        "trades_per_source_day": len(trades) / len(source_days)
        if len(source_days)
        else 0.0,
        "stress_net_r": float(values.sum()),
        "stress_pf": profit_factor(values),
        "average_stress_r": float(values.mean()) if len(values) else 0.0,
        "closed_drawdown_r": closed_drawdown(values),
        "positive_active_year_share": float((yearly > 0.0).mean())
        if len(yearly)
        else 0.0,
        "top_winners_removed_stress_net_r": float(removed.sum()),
        "daily_pvalue": one_sided_daily_pvalue(trades, source_days),
    }


def gate_checks(
    metrics: Mapping[str, Any], gate: Mapping[str, Any], holm_pvalue: float
) -> dict[str, bool]:
    return {
        "minimum_trades": int(metrics["trades"]) >= int(gate["minimum_trades"]),
        "minimum_stress_pf": float(metrics["stress_pf"])
        >= float(gate["minimum_stress_pf"]),
        "minimum_average_stress_r": float(metrics["average_stress_r"])
        >= float(gate["minimum_average_stress_r"]),
        "maximum_closed_drawdown_r": float(metrics["closed_drawdown_r"])
        <= float(gate["maximum_closed_drawdown_r"]),
        "minimum_positive_active_year_share": float(
            metrics["positive_active_year_share"]
        )
        >= float(gate["minimum_positive_active_year_share"]),
        "top_winners_removed_positive": float(
            metrics["top_winners_removed_stress_net_r"]
        )
        > 0.0,
        "maximum_holm_pvalue": float(holm_pvalue)
        <= float(gate["maximum_holm_pvalue"]),
    }


def entry_overlap_fraction(
    first: pd.DataFrame, second: pd.DataFrame, window_minutes: float
) -> float:
    if first.empty or second.empty:
        return 0.0
    left, right = (first, second) if len(first) <= len(second) else (second, first)
    right_times_by_direction = {
        direction: np.sort(
            pd.to_datetime(group["entry_time"], utc=True)
            .dt.tz_localize(None)
            .to_numpy(dtype="datetime64[ns]")
        )
        for direction, group in right.groupby("direction", sort=False)
    }
    window = np.timedelta64(int(round(window_minutes * 60.0)), "s")
    matches = 0
    for row in left.itertuples(index=False):
        candidates = right_times_by_direction.get(str(row.direction))
        if candidates is None or len(candidates) == 0:
            continue
        value = np.datetime64(pd.Timestamp(row.entry_time).tz_convert(None))
        index = int(np.searchsorted(candidates, value, side="left"))
        neighbors = candidates[max(0, index - 1) : min(len(candidates), index + 1)]
        if len(neighbors) and np.min(np.abs(neighbors - value)) <= window:
            matches += 1
    return matches / len(left)


def daily_pnl_correlation(
    first: pd.DataFrame,
    second: pd.DataFrame,
    source_days: pd.DatetimeIndex,
) -> float:
    left = daily_values(first, source_days)
    right = daily_values(second, source_days)
    if float(left.std(ddof=0)) == 0.0 or float(right.std(ddof=0)) == 0.0:
        return 0.0
    value = float(left.corr(right))
    return value if np.isfinite(value) else 0.0


def pairwise_independence(
    ledgers: Mapping[str, pd.DataFrame],
    economic_survivors: list[str],
    source_days: pd.DatetimeIndex,
    settings: Mapping[str, Any],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for first_index, first in enumerate(economic_survivors):
        for second in economic_survivors[first_index + 1 :]:
            overlap = entry_overlap_fraction(
                ledgers[first],
                ledgers[second],
                float(settings["entry_overlap_window_minutes"]),
            )
            correlation = daily_pnl_correlation(
                ledgers[first], ledgers[second], source_days
            )
            checks = {
                "maximum_entry_overlap_fraction": overlap
                <= float(settings["maximum_entry_overlap_fraction"]),
                "maximum_absolute_daily_pnl_correlation": abs(correlation)
                <= float(settings["maximum_absolute_daily_pnl_correlation"]),
            }
            rows.append(
                {
                    "first_candidate_id": first,
                    "second_candidate_id": second,
                    "entry_overlap_fraction": overlap,
                    "daily_pnl_correlation": correlation,
                    "checks": checks,
                    "independence_pass": all(checks.values()),
                }
            )
    return rows


def select_distinct_survivors(
    economic_survivors: list[str],
    pairwise: list[dict[str, Any]],
    fixed_order: list[str],
) -> list[str]:
    lookup = {
        frozenset((row["first_candidate_id"], row["second_candidate_id"])): bool(
            row["independence_pass"]
        )
        for row in pairwise
    }
    survivors = set(economic_survivors)
    selected: list[str] = []
    for candidate_id in fixed_order:
        if candidate_id not in survivors:
            continue
        if all(
            lookup.get(frozenset((candidate_id, prior)), False)
            for prior in selected
        ):
            selected.append(candidate_id)
    return selected
