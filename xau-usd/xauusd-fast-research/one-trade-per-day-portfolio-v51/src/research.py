from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor


MODEL_FEATURES = (
    "direction_sign",
    "mechanism_break_and_run",
    "mechanism_downside_impulse_retest",
    "mechanism_opening_range_reversal",
    "signal_source_count",
    "log_body_fraction",
    "log_dir_close_location",
    "log_dir_three_bar_move_atr",
    "log_break_distance_atr",
    "log_estimated_cost_r",
    "log_spread_atr",
    "dir_return_15m_atr",
    "dir_return_1h_atr",
    "dir_return_4h_atr",
    "dir_return_24h_atr",
    "range_1h_atr",
    "range_4h_atr",
    "dir_ema20_distance_atr",
    "dir_ema50_distance_atr",
    "efficiency_1h",
    "efficiency_4h",
    "atr_ratio_m5",
    "quote_intensity_ratio",
    "dir_tick_imbalance_5m",
    "dir_tick_imbalance_15m",
    "dir_book_imbalance_mean",
    "dir_microprice_edge_atr",
    "price_efficiency_5m",
    "spread_atr",
    "h1_adx",
    "h1_efficiency",
    "dir_h1_ema_slope_atr",
    "dir_h1_ema_distance_atr",
    "h4_adx",
    "h4_efficiency",
    "dir_h4_ema_slope_atr",
    "h4_range_width_atr",
    "h4_displacement_atr",
    "regime_unsafe_shock",
    "regime_trend_up",
    "regime_trend_down",
    "regime_compression",
    "regime_chop",
    "regime_transition_unknown",
    "hour_sin",
    "hour_cos",
    "weekday_sin",
    "weekday_cos",
    "prior_events_1h",
    "prior_events_4h",
    "prior_same_direction_1h",
    "minutes_since_prior_event_log1p",
    "action_stop_atr",
    "action_target_r",
    "action_hold_hours",
    "action_fast",
    "action_intraday",
    "action_swing",
)


PRICE_REGIME_BLOCKED = (
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


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(4 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_hash(payload: Mapping[str, Any], hash_key: str) -> str:
    value = {key: item for key, item in payload.items() if key != hash_key}
    encoded = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("ascii")
    return hashlib.sha256(encoded).hexdigest()


def verify_sources(
    repo_root: Path, sources: Mapping[str, Mapping[str, str]]
) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for name, record in sources.items():
        path = repo_root / record["path"]
        if not path.is_file():
            raise FileNotFoundError(path)
        actual = sha256_file(path)
        if actual != record["sha256"]:
            raise ValueError(f"Source hash mismatch for {name}: {actual}")
        result[name] = {
            "path": str(path.resolve()),
            "bytes": int(path.stat().st_size),
            "sha256": actual,
        }
    return result


def price_regime_features() -> list[str]:
    return [
        column
        for column in MODEL_FEATURES
        if not any(token in column for token in PRICE_REGIME_BLOCKED)
    ]


def prepare_actions(path: Path, policy: Mapping[str, Any]) -> pd.DataFrame:
    actions = pd.read_parquet(path)
    required = {
        *MODEL_FEATURES,
        "event_id",
        "signal_time",
        "entry_time",
        "exit_time",
        "direction",
        "regime",
        "action_id",
        "risk_usd",
        "stress_net_r",
        "current_account_feasible",
    }
    missing = sorted(required.difference(actions.columns))
    if missing:
        raise ValueError(f"Action ledger is missing columns: {missing}")
    if bool(actions.duplicated(["event_id", "action_id"]).any()):
        raise ValueError("Action ledger has duplicate event/action rows")
    for column in ("signal_time", "entry_time", "exit_time"):
        actions[column] = pd.to_datetime(actions[column], utc=True, errors="raise")
    allowed = actions["action_id"].isin(policy["allowed_actions"])
    if bool(policy["require_current_account_feasible"]):
        allowed &= actions["current_account_feasible"].astype(bool)
    actions = actions.loc[allowed].copy()
    if actions.empty:
        raise ValueError("No account-feasible allowed actions remain")
    if not np.isfinite(actions[list(MODEL_FEATURES)]).all(axis=None):
        raise ValueError("Action ledger contains non-finite model features")
    maximum_risk = float(policy["maximum_risk_usd_at_0p01_lot"])
    if bool(actions["risk_usd"].gt(maximum_risk + 1e-12).any()):
        raise ValueError("Account-infeasible risk survived the policy filter")
    return actions.sort_values(
        ["signal_time", "event_id", "action_id"], kind="mergesort"
    ).reset_index(drop=True)


def make_model(config: Mapping[str, Any]) -> HistGradientBoostingRegressor:
    return HistGradientBoostingRegressor(
        learning_rate=float(config["learning_rate"]),
        max_iter=int(config["max_iter"]),
        max_leaf_nodes=int(config["max_leaf_nodes"]),
        min_samples_leaf=int(config["min_samples_leaf"]),
        l2_regularization=float(config["l2_regularization"]),
        max_bins=int(config["max_bins"]),
        random_state=int(config["random_state"]),
    )


def fit_and_score(
    actions: pd.DataFrame,
    fit_end: pd.Timestamp,
    model_config: Mapping[str, Any],
) -> tuple[pd.DataFrame, dict[str, Any]]:
    features = price_regime_features()
    training = actions.loc[
        actions["signal_time"].lt(fit_end) & actions["exit_time"].lt(fit_end)
    ]
    if len(training) < int(model_config["minimum_fit_rows"]):
        raise ValueError(f"Insufficient fit rows: {len(training)}")
    target = training["stress_net_r"].clip(
        float(model_config["target_clip_min_r"]),
        float(model_config["target_clip_max_r"]),
    )
    model = make_model(model_config)
    model.fit(training[features], target)
    scored = actions.copy()
    scored["model_score"] = model.predict(scored[features])
    train_scores = scored.loc[training.index, "model_score"]
    return scored, {
        "fit_end_exclusive_utc": fit_end.isoformat(),
        "fit_rows": int(len(training)),
        "feature_count": int(len(features)),
        "fit_target_mean_r": float(target.mean()),
        "fit_score_mean_r": float(train_scores.mean()),
        "fit_spearman": float(train_scores.corr(target, method="spearman")),
    }


def select_addon(
    scored: pd.DataFrame,
    start: pd.Timestamp,
    end: pd.Timestamp,
    policy: Mapping[str, Any],
) -> pd.DataFrame:
    best = (
        scored.sort_values(
            ["event_id", "model_score", "action_id"],
            ascending=[True, False, True],
            kind="mergesort",
        )
        .drop_duplicates("event_id", keep="first")
        .sort_values(["signal_time", "direction", "event_id"], kind="mergesort")
        .reset_index(drop=True)
    )
    threshold = (
        best["model_score"]
        .shift(1)
        .rolling(
            int(policy["rolling_score_events"]),
            min_periods=int(policy["minimum_rolling_score_events"]),
        )
        .quantile(float(policy["score_quantile"]))
    )
    best["rolling_score_threshold"] = threshold
    eligible = best["model_score"].ge(best["rolling_score_threshold"])
    eligible &= best["model_score"].ge(float(policy["minimum_model_score"]))
    if bool(policy["reject_unsafe_shock"]):
        eligible &= best["regime"].ne("UNSAFE_SHOCK")
    if bool(policy["weekdays_only"]):
        eligible &= best["entry_time"].dt.weekday.lt(5)
    eligible &= best["entry_time"].ge(start) & best["entry_time"].lt(end)
    eligible &= best["exit_time"].lt(end)
    candidates = best.loc[eligible].sort_values(
        ["entry_time", "model_score", "event_id"],
        ascending=[True, False, True],
        kind="mergesort",
    )

    accepted: list[pd.Series] = []
    active: list[pd.Series] = []
    daily_counts: dict[Any, int] = {}
    minimum_time = pd.Timestamp.min.tz_localize("UTC")
    last_any = minimum_time
    last_direction = {"LONG": minimum_time, "SHORT": minimum_time}
    any_gap = pd.Timedelta(minutes=float(policy["any_entry_separation_minutes"]))
    direction_gap = pd.Timedelta(
        minutes=float(policy["same_direction_separation_minutes"])
    )
    for _, trade in candidates.iterrows():
        entry = pd.Timestamp(trade["entry_time"])
        active = [position for position in active if position["exit_time"] > entry]
        day = entry.date()
        direction = str(trade["direction"])
        if daily_counts.get(day, 0) >= int(policy["maximum_trades_per_utc_weekday"]):
            continue
        if len(active) >= int(policy["maximum_concurrent_positions"]):
            continue
        same_direction = sum(
            str(position["direction"]) == direction for position in active
        )
        if same_direction >= int(policy["maximum_concurrent_same_direction"]):
            continue
        if entry < last_any + any_gap:
            continue
        if entry < last_direction[direction] + direction_gap:
            continue
        accepted.append(trade)
        active.append(trade)
        daily_counts[day] = daily_counts.get(day, 0) + 1
        last_any = entry
        last_direction[direction] = entry

    if not accepted:
        return pd.DataFrame(columns=[*best.columns, "pnl_usd"])
    result = pd.DataFrame(accepted).reset_index(drop=True)
    result["pnl_usd"] = result["stress_net_r"] * result["risk_usd"]
    return result


def apply_v50_core_policy(
    ledger: pd.DataFrame, policy: Mapping[str, Any]
) -> pd.DataFrame:
    required = {
        "trade_id",
        "specialist_id",
        "source_strategy",
        "entry_time_utc",
        "exit_time_utc",
        "pnl_usd_0p01_equiv",
        "risk_usd",
        "direction",
    }
    missing = sorted(required.difference(ledger.columns))
    if missing:
        raise ValueError(f"Core ledger is missing columns: {missing}")
    if bool(ledger["trade_id"].duplicated().any()):
        raise ValueError("Core ledger has duplicate trade IDs")
    core = ledger.copy()
    for column in ("entry_time_utc", "exit_time_utc"):
        core[column] = pd.to_datetime(core[column], utc=True, errors="raise")
    target_mask = core["specialist_id"].eq(policy["target_specialist_id"]) & core[
        "source_strategy"
    ].eq(policy["target_source_strategy"])
    target = core.loc[target_mask].sort_values(
        ["entry_time_utc", "trade_id"], kind="mergesort"
    )
    accepted: set[str] = set()
    active: list[pd.Timestamp] = []
    daily: dict[Any, int] = {}
    for row in target.itertuples(index=False):
        entry = pd.Timestamp(row.entry_time_utc)
        active = [exit_time for exit_time in active if exit_time > entry]
        day = entry.date()
        if len(active) >= int(policy["maximum_concurrent_target_positions"]):
            continue
        if daily.get(day, 0) >= int(policy["maximum_target_entries_per_utc_day"]):
            continue
        accepted.add(str(row.trade_id))
        active.append(pd.Timestamp(row.exit_time_utc))
        daily[day] = daily.get(day, 0) + 1
    return (
        core.loc[~target_mask | core["trade_id"].astype(str).isin(accepted)]
        .sort_values(["exit_time_utc", "entry_time_utc", "trade_id"], kind="mergesort")
        .reset_index(drop=True)
    )


def standardize_core(
    core: pd.DataFrame, start: pd.Timestamp, end: pd.Timestamp
) -> pd.DataFrame:
    frame = core.loc[
        core["entry_time_utc"].ge(start)
        & core["entry_time_utc"].lt(end)
        & core["exit_time_utc"].lt(end)
    ].copy()
    return pd.DataFrame(
        {
            "trade_id": "CORE_" + frame["trade_id"].astype(str),
            "lane": "CORE",
            "specialist": frame["specialist_id"].astype(str),
            "entry_time": frame["entry_time_utc"],
            "exit_time": frame["exit_time_utc"],
            "direction": frame["direction"].astype(str),
            "risk_usd": frame["risk_usd"].astype(float),
            "pnl_usd": frame["pnl_usd_0p01_equiv"].astype(float),
            "event_id": "",
            "action_id": "CORE_FROZEN",
            "model_score": np.nan,
        }
    ).sort_values(["entry_time", "trade_id"], kind="mergesort")


def standardize_addon(addon: pd.DataFrame) -> pd.DataFrame:
    if addon.empty:
        return pd.DataFrame(
            columns=[
                "trade_id",
                "lane",
                "specialist",
                "entry_time",
                "exit_time",
                "direction",
                "risk_usd",
                "pnl_usd",
                "event_id",
                "action_id",
                "model_score",
            ]
        )
    return pd.DataFrame(
        {
            "trade_id": "ADDON_" + addon["event_id"].astype(str),
            "lane": "ADDON",
            "specialist": addon.apply(
                lambda row: "+".join(
                    name
                    for name in (
                        "BREAK_AND_RUN",
                        "DOWNSIDE_IMPULSE_RETEST",
                        "OPENING_RANGE_REVERSAL",
                    )
                    if int(row[name]) == 1
                ),
                axis=1,
            ),
            "entry_time": addon["entry_time"],
            "exit_time": addon["exit_time"],
            "direction": addon["direction"].astype(str),
            "risk_usd": addon["risk_usd"].astype(float),
            "pnl_usd": addon["pnl_usd"].astype(float),
            "event_id": addon["event_id"].astype(str),
            "action_id": addon["action_id"].astype(str),
            "model_score": addon["model_score"].astype(float),
        }
    ).sort_values(["entry_time", "trade_id"], kind="mergesort")


def profit_factor(values: pd.Series) -> float | None:
    gains = float(values.loc[values > 0.0].sum())
    losses = float(-values.loc[values < 0.0].sum())
    if losses == 0.0:
        return None if gains == 0.0 else float("inf")
    return gains / losses


def drawdown(values: pd.Series) -> float:
    equity = np.concatenate(([0.0], values.fillna(0.0).cumsum().to_numpy(float)))
    return float((np.maximum.accumulate(equity) - equity).max())


def window_metrics(
    trades: pd.DataFrame,
    start: pd.Timestamp,
    end: pd.Timestamp,
    top_winners_removed: int,
) -> dict[str, Any]:
    ordered = trades.sort_values(["exit_time", "trade_id"], kind="mergesort")
    values = ordered["pnl_usd"].astype(float)
    weekdays = int(np.busday_count(start.date(), end.date()))
    entry_days = ordered["entry_time"].dt.tz_localize(None).dt.normalize()
    months = (
        ordered.assign(
            month=ordered["entry_time"].dt.tz_localize(None).dt.to_period("M")
        )
        .groupby("month", sort=True)["pnl_usd"]
        .sum()
    )
    month_index = pd.period_range(
        start.tz_localize(None).to_period("M"),
        (end.tz_localize(None) - pd.Timedelta(microseconds=1)).to_period("M"),
        freq="M",
    )
    months = months.reindex(month_index, fill_value=0.0)
    midpoint = start + (end - start) / 2
    first_half = ordered.loc[ordered["entry_time"].lt(midpoint), "pnl_usd"].sum()
    second_half = ordered.loc[ordered["entry_time"].ge(midpoint), "pnl_usd"].sum()
    remove_count = min(int(top_winners_removed), len(values))
    removed = values.drop(values.nlargest(remove_count).index)
    daily = ordered.assign(day=entry_days).groupby("day", sort=True)["pnl_usd"].sum()
    return {
        "trades": int(len(ordered)),
        "weekdays": weekdays,
        "trades_per_weekday": float(len(ordered) / weekdays) if weekdays else 0.0,
        "net_pnl_dollars": float(values.sum()),
        "profit_factor": profit_factor(values),
        "average_pnl_dollars": float(values.mean()) if len(values) else 0.0,
        "win_rate": float(values.gt(0.0).mean()) if len(values) else 0.0,
        "closed_drawdown_dollars": drawdown(values),
        "active_weekday_share": float(entry_days.nunique() / weekdays)
        if weekdays
        else 0.0,
        "positive_month_share": float(months.gt(0.0).mean()) if len(months) else 0.0,
        "first_half_net_dollars": float(first_half),
        "second_half_net_dollars": float(second_half),
        "top_winners_removed_net_dollars": float(removed.sum()),
        "worst_weekday_dollars": float(daily.min()) if len(daily) else 0.0,
        "best_weekday_dollars": float(daily.max()) if len(daily) else 0.0,
        "maximum_risk_usd": float(ordered["risk_usd"].max()) if len(ordered) else 0.0,
    }


def overlap_metrics(combined: pd.DataFrame) -> dict[str, Any]:
    ordered = combined.sort_values(["entry_time", "trade_id"], kind="mergesort")
    active: list[pd.Series] = []
    maximum_count = 0
    maximum_risk = 0.0
    addon_entries_while_core_open = 0
    core_entries_while_addon_open = 0
    for _, trade in ordered.iterrows():
        entry = pd.Timestamp(trade["entry_time"])
        active = [position for position in active if position["exit_time"] > entry]
        active_lanes = {str(position["lane"]) for position in active}
        if trade["lane"] == "ADDON" and "CORE" in active_lanes:
            addon_entries_while_core_open += 1
        if trade["lane"] == "CORE" and "ADDON" in active_lanes:
            core_entries_while_addon_open += 1
        active.append(trade)
        maximum_count = max(maximum_count, len(active))
        maximum_risk = max(maximum_risk, sum(float(row["risk_usd"]) for row in active))
    return {
        "maximum_concurrent_positions": int(maximum_count),
        "maximum_open_initial_risk_dollars": float(maximum_risk),
        "addon_entries_while_core_open": int(addon_entries_while_core_open),
        "core_entries_while_addon_open": int(core_entries_while_addon_open),
    }


def evaluate_gates(
    addon: Mapping[str, Any],
    combined: Mapping[str, Any],
    gate: Mapping[str, Any],
    account: Mapping[str, Any],
) -> tuple[bool, dict[str, bool]]:
    addon_pf = addon["profit_factor"]
    combined_pf = combined["profit_factor"]
    allowed_drawdown = float(account["equity_dollars"]) * float(
        account["maximum_equity_drawdown_fraction"]
    )
    buffered_drawdown = float(combined["closed_drawdown_dollars"]) * float(
        account["capital_safety_buffer_multiple"]
    )
    checks = {
        "minimum_addon_trades": addon["trades"] >= int(gate["minimum_addon_trades"]),
        "minimum_addon_frequency": addon["trades_per_weekday"]
        >= float(gate["minimum_addon_trades_per_weekday"]),
        "minimum_addon_profit_factor": addon_pf is not None
        and addon_pf >= float(gate["minimum_addon_profit_factor"]),
        "minimum_addon_net": addon["net_pnl_dollars"]
        > float(gate["minimum_addon_net_dollars"]),
        "maximum_addon_drawdown": addon["closed_drawdown_dollars"]
        <= float(gate["maximum_addon_closed_drawdown_dollars"]),
        "maximum_addon_risk": addon["maximum_risk_usd"]
        <= float(account.get("maximum_addon_risk_usd", float("inf"))),
        "minimum_combined_trades": combined["trades"]
        >= int(gate["minimum_combined_trades"]),
        "minimum_combined_frequency": combined["trades_per_weekday"]
        >= float(gate["minimum_combined_trades_per_weekday"]),
        "minimum_combined_profit_factor": combined_pf is not None
        and combined_pf >= float(gate["minimum_combined_profit_factor"]),
        "minimum_combined_net": combined["net_pnl_dollars"]
        > float(gate["minimum_combined_net_dollars"]),
        "minimum_combined_positive_month_share": combined["positive_month_share"]
        >= float(gate["minimum_combined_positive_month_share"]),
        "minimum_first_half_combined_net": combined["first_half_net_dollars"]
        > float(gate["minimum_each_half_combined_net_dollars"]),
        "minimum_second_half_combined_net": combined["second_half_net_dollars"]
        > float(gate["minimum_each_half_combined_net_dollars"]),
        "addon_winner_removal_positive": addon["top_winners_removed_net_dollars"] > 0.0,
        "combined_winner_removal_positive": combined["top_winners_removed_net_dollars"]
        > 0.0,
        "maximum_combined_closed_drawdown": combined["closed_drawdown_dollars"]
        <= float(account["maximum_combined_closed_drawdown_dollars"]),
        "buffered_closed_drawdown_within_15_percent": buffered_drawdown
        <= allowed_drawdown,
    }
    return bool(all(checks.values())), checks
