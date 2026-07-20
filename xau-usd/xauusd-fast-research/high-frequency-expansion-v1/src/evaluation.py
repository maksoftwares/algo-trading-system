from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd

from dataset import MODEL_FEATURES


def profit_factor(values: pd.Series) -> float | None:
    positive = float(values.loc[values > 0].sum())
    negative = float(-values.loc[values < 0].sum())
    if negative == 0:
        return None if positive == 0 else float("inf")
    return positive / negative


def closed_drawdown(values: pd.Series) -> float:
    equity = values.fillna(0.0).cumsum()
    if equity.empty:
        return 0.0
    return float((equity.cummax() - equity).max())


def business_days(start: pd.Timestamp, end: pd.Timestamp) -> int:
    first = pd.Timestamp(start).tz_localize(None).normalize()
    last = (pd.Timestamp(end).tz_localize(None) - pd.Timedelta(microseconds=1)).normalize()
    return int(len(pd.date_range(first, last, freq="B")))


def metrics(
    trades: pd.DataFrame,
    start: pd.Timestamp,
    end: pd.Timestamp,
    top_winners_removed: int,
) -> dict[str, Any]:
    source_days = business_days(start, end)
    source = trades.loc[
        (trades["entry_time"] >= start) & (trades["entry_time"] < end)
    ].sort_values(["entry_time", "event_id"], kind="mergesort")
    values = source["stress_net_r"].astype(float)
    daily = (
        source.assign(day=source["entry_time"].dt.tz_localize(None).dt.normalize())
        .groupby("day", sort=True)["stress_net_r"]
        .sum()
    )
    active_months = (
        source.assign(month=source["entry_time"].dt.tz_localize(None).dt.to_period("M"))
        .groupby("month", sort=True)["stress_net_r"]
        .sum()
    )
    month_index = pd.period_range(
        pd.Timestamp(start).tz_localize(None).to_period("M"),
        (pd.Timestamp(end).tz_localize(None) - pd.Timedelta(microseconds=1)).to_period("M"),
        freq="M",
    )
    months = active_months.reindex(month_index, fill_value=0.0)
    first_year = pd.Timestamp(start).year
    last_year = (pd.Timestamp(end) - pd.Timedelta(microseconds=1)).year
    year_pfs: dict[str, float | None] = {}
    for year in range(first_year, last_year + 1):
        year_values = source.loc[source["entry_time"].dt.year.eq(year), "stress_net_r"]
        year_pfs[str(year)] = profit_factor(year_values) if len(year_values) else 0.0
    minimum_year_pf = min(
        (
            float(value)
            for value in year_pfs.values()
            if value is not None
        ),
        default=0.0,
    )
    removed = values.drop(values.nlargest(min(top_winners_removed, len(values))).index)
    monthly_rolling = months.rolling(6, min_periods=6).sum()
    return {
        "trades": int(len(source)),
        "source_weekdays": source_days,
        "trades_per_weekday": len(source) / source_days if source_days else 0.0,
        "stress_net_r": float(values.sum()),
        "stress_pf": profit_factor(values),
        "average_stress_r": float(values.mean()) if len(values) else 0.0,
        "closed_drawdown_r": closed_drawdown(values),
        "positive_active_month_share": float((months > 0).mean()) if len(months) else 0.0,
        "positive_weekday_share": float((daily > 0).sum() / source_days) if source_days else 0.0,
        "active_weekday_share": float(len(daily) / source_days) if source_days else 0.0,
        "minimum_calendar_year_pf": minimum_year_pf,
        "calendar_year_pf": year_pfs,
        "positive_rolling_6m_share": float((monthly_rolling > 0).mean()) if len(monthly_rolling) else 0.0,
        "top_winners_removed_stress_net_r": float(removed.sum()),
        "worst_weekday_r": float(daily.min()) if len(daily) else 0.0,
        "best_weekday_r": float(daily.max()) if len(daily) else 0.0,
    }


def evaluate_gate(value: dict[str, Any], gate: dict[str, Any]) -> tuple[bool, dict[str, bool]]:
    pf = value["stress_pf"]
    checks = {
        "minimum_frequency": value["trades_per_weekday"] >= float(gate["minimum_frequency"]),
        "maximum_frequency": value["trades_per_weekday"] <= float(gate["maximum_frequency"]),
        "minimum_pf": pf is not None and pf >= float(gate["minimum_pf"]),
        "minimum_average_r": value["average_stress_r"] >= float(gate["minimum_average_r"]),
        "minimum_positive_month_share": value["positive_active_month_share"]
        >= float(gate["minimum_positive_month_share"]),
        "minimum_calendar_year_pf": value["minimum_calendar_year_pf"]
        >= float(gate["minimum_calendar_year_pf"]),
        "maximum_drawdown_r": value["closed_drawdown_r"] <= float(gate["maximum_drawdown_r"]),
        "top_winners_removed_positive": value["top_winners_removed_stress_net_r"] > 0,
    }
    return bool(all(checks.values())), checks


def feature_subset(name: str) -> list[str]:
    features = list(MODEL_FEATURES)
    if name == "ALL":
        return features
    if name == "NO_MICRO":
        blocked = ("tick_", "book_", "microprice_", "quote_intensity", "price_efficiency")
        return [column for column in features if not any(token in column for token in blocked)]
    if name == "NO_LOG":
        return [column for column in features if not column.startswith("log_")]
    if name == "PRICE_REGIME":
        blocked = (
            "log_",
            "tick_",
            "book_",
            "microprice_",
            "quote_intensity",
            "price_efficiency",
            "prior_events",
            "prior_same",
            "minutes_since",
        )
        return [column for column in features if not any(token in column for token in blocked)]
    if name == "PRICE_MICRO":
        return [column for column in features if not column.startswith("regime_")]
    raise ValueError(f"Unknown feature subset: {name}")


def model_specifications(count: int, seed: int) -> list[dict[str, Any]]:
    rng = np.random.default_rng(seed)
    choices = {
        "learning_rate": (0.02, 0.03, 0.05, 0.08),
        "max_iter": (80, 120, 160),
        "max_leaf_nodes": (7, 15, 31),
        "min_samples_leaf": (50, 100, 200, 300),
        "l2_regularization": (0.5, 1.0, 2.0, 5.0),
        "max_bins": (63, 127, 255),
        "feature_subset": ("ALL", "NO_MICRO", "NO_LOG", "PRICE_REGIME", "PRICE_MICRO"),
    }
    results: list[dict[str, Any]] = []
    seen: set[tuple[Any, ...]] = set()
    while len(results) < count:
        values = tuple(rng.choice(choices[key]) for key in choices)
        if values in seen:
            continue
        seen.add(values)
        spec = {key: value.item() if hasattr(value, "item") else value for key, value in zip(choices, values)}
        spec["model_id"] = f"M{len(results) + 1:03d}"
        spec["random_state"] = int(seed + len(results))
        results.append(spec)
    return results


def score_thresholds(best_actions: pd.DataFrame, search: dict[str, Any], quantile: float) -> pd.Series:
    scores = best_actions["model_score"].astype(float)
    return scores.shift(1).rolling(
        int(search["rolling_score_events"]),
        min_periods=int(search["minimum_rolling_score_events"]),
    ).quantile(float(quantile))


def prepare_best_actions(scored_actions: pd.DataFrame) -> pd.DataFrame:
    ordered = scored_actions.sort_values(
        ["event_id", "model_score", "action_id"],
        ascending=[True, False, True],
        kind="mergesort",
    )
    return ordered.drop_duplicates("event_id", keep="first").sort_values(
        ["signal_time", "direction", "event_id"], kind="mergesort"
    ).reset_index(drop=True)


def select_trades(
    scored_actions: pd.DataFrame,
    start: pd.Timestamp,
    end: pd.Timestamp,
    quantile: float,
    score_floor: float | None,
    search: dict[str, Any],
    portfolio: dict[str, Any],
) -> pd.DataFrame:
    best = (
        prepare_best_actions(scored_actions)
        if scored_actions["event_id"].duplicated().any()
        else scored_actions.sort_values(
            ["signal_time", "direction", "event_id"], kind="mergesort"
        ).reset_index(drop=True)
    )
    best["rolling_score_threshold"] = score_thresholds(best, search, quantile)
    eligible = best["model_score"].ge(best["rolling_score_threshold"])
    if score_floor is not None:
        eligible &= best["model_score"].ge(float(score_floor))
    eligible &= best["regime"].ne("UNSAFE_SHOCK")
    eligible &= best["signal_time"].dt.weekday.lt(5)
    candidates = best.loc[
        eligible & (best["entry_time"] >= start) & (best["entry_time"] < end)
    ].sort_values(["entry_time", "model_score"], ascending=[True, False], kind="mergesort")

    accepted: list[pd.Series] = []
    active: list[pd.Series] = []
    daily_counts: dict[Any, int] = {}
    last_any = pd.Timestamp.min.tz_localize("UTC")
    last_direction = {
        "LONG": pd.Timestamp.min.tz_localize("UTC"),
        "SHORT": pd.Timestamp.min.tz_localize("UTC"),
    }
    any_gap = pd.Timedelta(minutes=float(portfolio["any_entry_separation_minutes"]))
    direction_gap = pd.Timedelta(minutes=float(portfolio["same_direction_separation_minutes"]))
    for _, trade in candidates.iterrows():
        entry_time = trade["entry_time"]
        active = [position for position in active if position["exit_time"] > entry_time]
        day = entry_time.date()
        direction = str(trade["direction"])
        if daily_counts.get(day, 0) >= int(portfolio["maximum_trades_per_utc_weekday"]):
            continue
        if len(active) >= int(portfolio["maximum_concurrent_trades"]):
            continue
        if sum(str(position["direction"]) == direction for position in active) >= int(
            portfolio["maximum_concurrent_same_direction"]
        ):
            continue
        if entry_time < last_any + any_gap:
            continue
        if entry_time < last_direction[direction] + direction_gap:
            continue
        accepted.append(trade)
        active.append(trade)
        daily_counts[day] = daily_counts.get(day, 0) + 1
        last_any = entry_time
        last_direction[direction] = entry_time
    return pd.DataFrame(accepted).reset_index(drop=True)


def ranking_key(row: pd.Series) -> tuple[float, float, float, float, str]:
    return (
        -float(row["minimum_calendar_year_pf"]),
        -float(row["stress_pf"]),
        -float(row["average_stress_r"]),
        abs(float(row["trades_per_weekday"]) - 3.5),
        str(row["attempt_id"]),
    )


@dataclass(frozen=True)
class AttemptPolicy:
    attempt_id: str
    model_id: str
    quantile: float
    score_floor: float | None


def attempt_policies(config: dict[str, Any]) -> list[AttemptPolicy]:
    policies: list[AttemptPolicy] = []
    for model_index in range(int(config["model_specifications"])):
        model_id = f"M{model_index + 1:03d}"
        policy_index = 0
        for quantile in config["score_quantiles"]:
            for floor in config["score_floors"]:
                policy_index += 1
                policies.append(
                    AttemptPolicy(
                        attempt_id=f"{model_id}_P{policy_index:02d}",
                        model_id=model_id,
                        quantile=float(quantile),
                        score_floor=None if floor is None else float(floor),
                    )
                )
    return policies
