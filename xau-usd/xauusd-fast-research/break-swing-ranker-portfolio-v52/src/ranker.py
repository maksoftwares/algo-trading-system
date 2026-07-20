from __future__ import annotations

from typing import Any, Mapping

import numpy as np
import pandas as pd

import research as base


def prepare_candidates(path: Any, policy: Mapping[str, Any]) -> pd.DataFrame:
    actions = base.prepare_actions(
        path,
        {
            "allowed_actions": [policy["action_id"]],
            "require_current_account_feasible": policy[
                "require_current_account_feasible"
            ],
            "maximum_risk_usd_at_0p01_lot": policy["maximum_risk_usd_at_0p01_lot"],
        },
    )
    pure_break = (
        actions["BREAK_AND_RUN"].eq(1)
        & actions["DOWNSIDE_IMPULSE_RETEST"].eq(0)
        & actions["OPENING_RANGE_REVERSAL"].eq(0)
    )
    result = actions.loc[pure_break].copy()
    if result.empty:
        raise ValueError("No pure break-and-run swing candidates remain")
    if bool(result["event_id"].duplicated().any()):
        raise ValueError("Fixed-action candidates contain duplicate event IDs")
    return result.sort_values(["signal_time", "event_id"], kind="mergesort")


def quarterly_scores(
    actions: pd.DataFrame,
    start: pd.Timestamp,
    end: pd.Timestamp,
    model_config: Mapping[str, Any],
    policy: Mapping[str, Any],
) -> tuple[pd.DataFrame, list[dict[str, Any]]]:
    features = base.price_regime_features()
    blocks = pd.date_range(
        start, end, freq=f"{int(policy['refit_months'])}MS", inclusive="left"
    )
    frames: list[pd.DataFrame] = []
    diagnostics: list[dict[str, Any]] = []
    for block_start in blocks:
        block_end = min(
            block_start + pd.DateOffset(months=int(policy["refit_months"])), end
        )
        training = actions.loc[
            actions["signal_time"].lt(block_start)
            & actions["exit_time"].lt(block_start)
        ].sort_values(["signal_time", "event_id"], kind="mergesort")
        if len(training) < int(model_config["minimum_fit_rows"]):
            raise ValueError(f"Insufficient quarterly fit rows: {len(training)}")
        target = training["stress_net_r"].clip(
            float(model_config["target_clip_min_r"]),
            float(model_config["target_clip_max_r"]),
        )
        model = base.make_model(model_config)
        model.fit(training[features], target)
        threshold_rows = training.tail(int(policy["threshold_training_rows"]))
        threshold_scores = model.predict(threshold_rows[features])
        threshold = float(
            np.quantile(threshold_scores, float(policy["training_score_quantile"]))
        )
        block = actions.loc[
            actions["entry_time"].ge(block_start)
            & actions["entry_time"].lt(block_end)
            & actions["exit_time"].lt(block_end)
        ].copy()
        block["model_score"] = model.predict(block[features])
        block["score_threshold"] = threshold
        block["refit_time_utc"] = block_start
        frames.append(block)
        diagnostics.append(
            {
                "refit_time_utc": block_start.isoformat(),
                "block_end_exclusive_utc": block_end.isoformat(),
                "fit_rows": int(len(training)),
                "threshold_rows": int(len(threshold_rows)),
                "score_threshold": threshold,
                "candidate_rows": int(len(block)),
                "score_outcome_spearman": (
                    float(
                        block["model_score"].corr(
                            block["stress_net_r"], method="spearman"
                        )
                    )
                    if len(block) > 1
                    else None
                ),
            }
        )
    return pd.concat(frames, ignore_index=True), diagnostics


def select_ranked(scored: pd.DataFrame, policy: Mapping[str, Any]) -> pd.DataFrame:
    eligible = scored["model_score"].ge(scored["score_threshold"])
    eligible &= scored["model_score"].ge(float(policy["minimum_model_score"]))
    if bool(policy["reject_unsafe_shock"]):
        eligible &= scored["regime"].ne("UNSAFE_SHOCK")
    if bool(policy["weekdays_only"]):
        eligible &= scored["entry_time"].dt.weekday.lt(5)
    candidates = scored.loc[eligible].sort_values(
        ["entry_time", "model_score", "event_id"],
        ascending=[True, False, True],
        kind="mergesort",
    )
    accepted: list[pd.Series] = []
    active: list[pd.Timestamp] = []
    daily: dict[Any, int] = {}
    for _, trade in candidates.iterrows():
        entry = pd.Timestamp(trade["entry_time"])
        active = [exit_time for exit_time in active if exit_time > entry]
        day = entry.date()
        if len(active) >= int(policy["maximum_concurrent_positions"]):
            continue
        if daily.get(day, 0) >= int(policy["maximum_trades_per_utc_weekday"]):
            continue
        accepted.append(trade)
        active.append(pd.Timestamp(trade["exit_time"]))
        daily[day] = daily.get(day, 0) + 1
    if not accepted:
        return pd.DataFrame(columns=[*scored.columns, "pnl_usd"])
    result = pd.DataFrame(accepted).reset_index(drop=True)
    result["pnl_usd"] = result["stress_net_r"] * result["risk_usd"]
    return result


def standardize(addon: pd.DataFrame) -> pd.DataFrame:
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
            "trade_id": "V52_" + addon["event_id"].astype(str),
            "lane": "ADDON",
            "specialist": "BREAK_AND_RUN_SWING_RANKER",
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
