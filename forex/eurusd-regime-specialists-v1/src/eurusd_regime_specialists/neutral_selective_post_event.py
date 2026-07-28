from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

from .asymmetric import payoff_metrics
from .ensemble import load_ensemble_config, load_inputs
from .neutral_binance_eurusdt_flow import _period, load_parent_points
from .neutral_macro_event_drift import (
    load_config as load_event_config,
    load_event_source,
    qualifying_events,
)
from .neutral_midnight_pairs import aggregate_days, write_json
from .neutral_post_event_drive import (
    _oracle,
    _window_metrics,
    build_candidates,
    execute_branch,
    load_config as load_parent_config,
)
from .neutral_session_oco import _walk_exit
from .research import (
    PACKAGE_ROOT,
    PIP,
    active_weekday_fx_days,
    remove_top_winners,
    serialize,
    sha256_file,
)


FAMILY = "N30_NEUTRAL_SELECTIVE_POST_EVENT"
OUTPUT_ROOT = PACKAGE_ROOT / "outputs" / "neutral_selective_post_event"
SIDES = ("LONG", "SHORT")


def load_config() -> dict[str, Any]:
    return json.loads(
        (
            PACKAGE_ROOT
            / "config"
            / "frozen_neutral_selective_post_event.json"
        ).read_text(encoding="utf-8")
    )


def verify_lock() -> dict[str, str]:
    lock = json.loads(
        (
            PACKAGE_ROOT
            / "EURUSD_NEUTRAL_SELECTIVE_POST_EVENT_PREREG_2026_07_28.sha256.json"
        ).read_text(encoding="utf-8")
    )
    if (
        lock.get("locked_before_selective_post_event_forward_outcome_pass")
        is not True
    ):
        raise RuntimeError("Neutral selective post-event rule is not locked")
    checked: dict[str, str] = {}
    for relative, expected in lock["files"].items():
        actual = sha256_file(PACKAGE_ROOT / relative)
        if actual != expected:
            raise RuntimeError(
                "Neutral selective post-event preregistration mismatch: "
                f"{relative}"
            )
        checked[relative] = actual
    cfg = load_config()
    parent = cfg["parent_post_event_contract"]
    if sha256_file(PACKAGE_ROOT / parent["path"]) != parent["sha256"]:
        raise RuntimeError("Parent post-event contract drift")
    if (
        sha256_file(PACKAGE_ROOT / parent["lock_path"])
        != parent["lock_sha256"]
    ):
        raise RuntimeError("Parent post-event lock drift")
    if cfg["pre_forward_selection_census"] is None:
        raise RuntimeError("Selective post-event screen is not frozen")
    return checked


def _census_sha256(value: Any) -> str:
    payload = json.dumps(
        serialize(value),
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _mid_close(frame: pd.DataFrame) -> pd.Series:
    return 0.5 * (
        frame["bid_close"].astype(float)
        + frame["ask_close"].astype(float)
    )


def add_features(
    candidates: pd.DataFrame,
    m5: pd.DataFrame,
    cfg: dict[str, Any],
) -> tuple[pd.DataFrame, dict[str, int]]:
    features = cfg["features"]
    required = int(features["minimum_pre_event_history_bars"])
    history_bars = int(features["pre_event_history_bars"])
    median_bars = int(features["prior_range_median_bars"])
    records: list[dict[str, Any]] = []
    reasons = {"insufficient_pre_event_history": 0}
    for _, candidate in candidates.iterrows():
        observation_start = pd.Timestamp(
            candidate["observation_start_utc"]
        )
        position = int(m5.index.get_loc(observation_start))
        history = m5.iloc[
            max(0, position - history_bars) : position
        ]
        if len(history) < required:
            reasons["insufficient_pre_event_history"] += 1
            continue
        closes = _mid_close(history)
        prior_range_pips = (
            history["ask_high"].astype(float)
            - history["bid_low"].astype(float)
        ) / PIP
        prior_median = float(
            prior_range_pips.tail(median_bars).median()
        )
        if not np.isfinite(prior_median) or prior_median <= 0.0:
            reasons["insufficient_pre_event_history"] += 1
            continue
        latest = float(closes.iloc[-1])
        row = candidate.to_dict()
        for minutes, lag_bars in ((15, 3), (60, 12), (240, 48)):
            row[f"pre_event_return_{minutes}m_pips"] = (
                latest - float(closes.iloc[-1 - lag_bars])
            ) / PIP
        row["observation_range_to_prior_median"] = (
            float(candidate["observation_range_pips"]) / prior_median
        )
        event_time = pd.Timestamp(candidate["event_time_utc"])
        hour = (
            event_time.hour
            + event_time.minute / 60.0
            + event_time.second / 3600.0
        )
        angle = 2.0 * np.pi * hour / 24.0
        row["event_hour_sin"] = float(np.sin(angle))
        row["event_hour_cos"] = float(np.cos(angle))
        currencies = set(str(candidate["event_currencies"]).split("|"))
        row["event_has_eur"] = float("EUR" in currencies)
        row["event_has_usd"] = float("USD" in currencies)
        row["log1p_event_cluster_size"] = float(
            np.log1p(float(candidate["event_cluster_size"]))
        )
        records.append(row)
    frame = pd.DataFrame(records)
    if not frame.empty:
        frame = frame.sort_values("entry_time_utc").reset_index(drop=True)
    return frame, reasons


def _model_columns(cfg: dict[str, Any]) -> list[str]:
    columns = [
        *cfg["features"]["side_aligned_columns"],
        *cfg["features"]["shared_columns"],
    ]
    if len(columns) != int(cfg["features"]["model_column_count"]):
        raise RuntimeError("Frozen selective post-event feature count drift")
    return columns


def _side_rows(
    candidates: pd.DataFrame,
    cfg: dict[str, Any],
    labels: pd.DataFrame | None = None,
) -> pd.DataFrame:
    frames: list[pd.DataFrame] = []
    shared = list(cfg["features"]["shared_columns"])
    for side, sign, suffix, opposite in (
        ("LONG", 1.0, "long", "short"),
        ("SHORT", -1.0, "short", "long"),
    ):
        frame = pd.DataFrame(
            {
                "pair_id": candidates["pair_id"].to_numpy(),
                "eligible_date": candidates["eligible_date"].to_numpy(),
                "entry_time_utc": candidates[
                    "entry_time_utc"
                ].to_numpy(),
                "side": side,
                "aligned_impulse_pips": (
                    sign * candidates["impulse_pips"].astype(float)
                ).to_numpy(),
                "aligned_pre_event_return_15m_pips": (
                    sign
                    * candidates[
                        "pre_event_return_15m_pips"
                    ].astype(float)
                ).to_numpy(),
                "aligned_pre_event_return_60m_pips": (
                    sign
                    * candidates[
                        "pre_event_return_60m_pips"
                    ].astype(float)
                ).to_numpy(),
                "aligned_pre_event_return_240m_pips": (
                    sign
                    * candidates[
                        "pre_event_return_240m_pips"
                    ].astype(float)
                ).to_numpy(),
                "own_risk_pips": candidates[
                    f"risk_pips_{suffix}"
                ].astype(float).to_numpy(),
                "risk_advantage_pips": (
                    candidates[f"risk_pips_{opposite}"].astype(float)
                    - candidates[f"risk_pips_{suffix}"].astype(float)
                ).to_numpy(),
            }
        )
        for column in shared:
            frame[column] = candidates[column].astype(float).to_numpy()
        frames.append(frame)
    stacked = pd.concat(frames, ignore_index=True)
    if labels is not None:
        stacked = stacked.merge(
            labels[
                [
                    "pair_id",
                    "side",
                    "exit_time_utc",
                    "r",
                    "exit_reason",
                ]
            ],
            on=["pair_id", "side"],
            how="left",
            validate="one_to_one",
        )
        if stacked["r"].isna().any():
            raise RuntimeError("Missing development side outcome")
        stacked["positive_r"] = stacked["r"].gt(0.0).astype(int)
    return stacked


def _development_labels(
    candidates: pd.DataFrame,
    m5: pd.DataFrame,
    cfg: dict[str, Any],
) -> pd.DataFrame:
    start, end = map(pd.Timestamp, cfg["training_window"])
    development = _period(candidates, start, end)
    parent_cfg = load_parent_config()
    ledgers = []
    for branch in ("MOMENTUM", "REVERSAL"):
        ledger, _ = execute_branch(
            development, m5, branch, parent_cfg
        )
        ledgers.append(ledger)
    labels = pd.concat(ledgers, ignore_index=True)
    if labels.duplicated(["pair_id", "side"]).any():
        raise RuntimeError("Duplicate development side outcome")
    expected = 2 * len(development)
    if len(labels) != expected:
        raise RuntimeError(
            f"Incomplete development side ledger: {len(labels)} != {expected}"
        )
    labels["exit_time_utc"] = pd.to_datetime(
        labels["exit_time_utc"], utc=True
    )
    cutoff = pd.Timestamp(cfg["windows"]["validation_2023"][0])
    labels = labels[labels["exit_time_utc"].lt(cutoff)].copy()
    if len(labels) != expected:
        raise RuntimeError("Development label was not known before cutoff")
    return labels


def fit_and_screen(
    candidates: pd.DataFrame,
    m5: pd.DataFrame,
    cfg: dict[str, Any],
) -> tuple[
    pd.DataFrame,
    pd.DataFrame,
    pd.DataFrame,
    dict[str, Any],
]:
    start, end = map(pd.Timestamp, cfg["training_window"])
    development = _period(candidates, start, end)
    labels = _development_labels(candidates, m5, cfg)
    training = _side_rows(development, cfg, labels)
    minimum = int(cfg["model"]["minimum_training_side_rows"])
    if len(training) < minimum:
        raise RuntimeError(
            f"Insufficient development side rows: {len(training)} < {minimum}"
        )
    columns = _model_columns(cfg)
    scaler = StandardScaler()
    train_x = scaler.fit_transform(training[columns])
    target = training["positive_r"].astype(int)
    if target.nunique() != 2:
        raise RuntimeError("Selective fit requires both target classes")
    model_cfg = cfg["model"]
    model = LogisticRegression(
        C=float(model_cfg["C"]),
        solver=model_cfg["solver"],
        max_iter=int(model_cfg["max_iter"]),
        class_weight=model_cfg["class_weight"],
        random_state=int(model_cfg["random_state"]),
    )
    model.fit(train_x, target)

    forward_start = min(
        pd.Timestamp(cfg["windows"][name][0])
        for name in cfg["forward_windows"]
    )
    forward_end = max(
        pd.Timestamp(cfg["windows"][name][1])
        for name in cfg["forward_windows"]
    )
    forward = _period(candidates, forward_start, forward_end)
    side_scored = _side_rows(forward, cfg)
    side_scored["win_probability"] = model.predict_proba(
        scaler.transform(side_scored[columns])
    )[:, 1]
    pivot = side_scored.pivot(
        index="pair_id",
        columns="side",
        values="win_probability",
    ).rename(
        columns={
            "LONG": "model_probability_long",
            "SHORT": "model_probability_short",
        }
    )
    scored = forward.merge(
        pivot,
        left_on="pair_id",
        right_index=True,
        how="left",
        validate="one_to_one",
    )
    tie = str(model_cfg["tie_direction"])
    long_wins = scored["model_probability_long"].gt(
        scored["model_probability_short"]
    )
    exact_tie = scored["model_probability_long"].eq(
        scored["model_probability_short"]
    )
    scored["model_selected_side"] = np.where(
        long_wins | (exact_tie & (tie == "LONG")),
        "LONG",
        "SHORT",
    )
    scored["model_selection_probability"] = scored[
        ["model_probability_long", "model_probability_short"]
    ].max(axis=1)
    scored["model_probability_margin"] = (
        scored["model_probability_long"]
        - scored["model_probability_short"]
    ).abs()
    threshold = float(model_cfg["selection_probability_threshold"])
    selected = scored[
        scored["model_selection_probability"].ge(threshold)
    ].copy()
    selected = selected.sort_values("entry_time_utc").reset_index(drop=True)

    coefficients = pd.DataFrame(
        {
            "feature": columns,
            "coefficient": model.coef_[0],
            "training_mean": scaler.mean_,
            "training_scale": scaler.scale_,
        }
    ).sort_values("coefficient", ascending=False)
    census = _selection_census(
        candidates,
        forward,
        scored,
        selected,
        training,
        cfg,
    )
    return selected, scored, coefficients, census


def _selection_census(
    all_candidates: pd.DataFrame,
    forward: pd.DataFrame,
    scored: pd.DataFrame,
    selected: pd.DataFrame,
    training: pd.DataFrame,
    cfg: dict[str, Any],
) -> dict[str, Any]:
    rows = selected[
        [
            "pair_id",
            "entry_time_utc",
            "model_selected_side",
            "model_probability_long",
            "model_probability_short",
            "model_selection_probability",
        ]
    ].copy()
    rows["entry_time_utc"] = rows["entry_time_utc"].map(
        lambda value: pd.Timestamp(value).isoformat()
    )
    screen_hash = _census_sha256(rows.to_dict(orient="records"))

    def block(
        source: pd.DataFrame, chosen: pd.DataFrame
    ) -> dict[str, Any]:
        return {
            "source_candidates": int(len(source)),
            "selected_candidates": int(len(chosen)),
            "cash_candidates": int(len(source) - len(chosen)),
            "selected_long_rate": (
                float(chosen["model_selected_side"].eq("LONG").mean())
                if len(chosen)
                else 0.0
            ),
        }

    by_window = {}
    for name, bounds in cfg["windows"].items():
        start, end = map(pd.Timestamp, bounds)
        by_window[name] = block(
            _period(forward, start, end),
            _period(selected, start, end),
        )
    probabilities = scored["model_selection_probability"]
    return {
        "training_candidates": int(
            len(training) // len(SIDES)
        ),
        "training_side_rows": int(len(training)),
        "training_positive_side_rows": int(
            training["positive_r"].sum()
        ),
        "training_positive_rate": float(
            training["positive_r"].mean()
        ),
        "source_candidates_all_windows": int(len(all_candidates)),
        "forward": block(forward, selected),
        "by_window": by_window,
        "selection_probability_threshold": float(
            cfg["model"]["selection_probability_threshold"]
        ),
        "selection_probability": {
            "minimum": float(probabilities.min()),
            "median": float(probabilities.median()),
            "p90": float(probabilities.quantile(0.90)),
            "p95": float(probabilities.quantile(0.95)),
            "p99": float(probabilities.quantile(0.99)),
            "maximum": float(probabilities.max()),
        },
        "selected_candidate_manifest_sha256": screen_hash,
    }


def load_source(
    cfg: dict[str, Any],
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any], dict[str, int]]:
    parent = load_parent_points(include_outcomes=False)
    base = load_ensemble_config()
    m5, _, _ = load_inputs(base)
    event_cfg = load_event_config()
    events = qualifying_events(
        load_event_source(event_cfg), event_cfg
    )
    parent_cfg = load_parent_config()
    candidates, parent_census = build_candidates(
        parent,
        m5,
        events,
        parent_cfg,
        enforce_frozen_census=True,
    )
    featured, feature_reasons = add_features(candidates, m5, cfg)
    if feature_reasons["insufficient_pre_event_history"] != 0:
        raise RuntimeError(
            f"Unexpected selective feature cash: {feature_reasons!r}"
        )
    return featured, m5, parent_census, feature_reasons


def run_screen() -> tuple[dict[str, Any], dict[str, pd.DataFrame]]:
    cfg = load_config()
    candidates, m5, parent_census, feature_reasons = load_source(cfg)
    selected, scored, coefficients, census = fit_and_screen(
        candidates, m5, cfg
    )
    result = {
        "campaign_id": cfg["campaign_id"],
        "status": "PRE_FORWARD_SELECTION_SCREEN",
        "forward_outcomes_loaded": False,
        "parent_outcome_blind_census": parent_census,
        "feature_cash_reasons": feature_reasons,
        "pre_forward_selection_census": census,
        "model": {
            "type": cfg["model"]["type"],
            "training_end_utc": cfg["training_window"][1],
            "refit_after_2022": False,
            "threshold": cfg["model"][
                "selection_probability_threshold"
            ],
            "feature_count": len(_model_columns(cfg)),
        },
    }
    return result, {
        "SELECTED_CANDIDATES": selected,
        "SCORED_CANDIDATES": scored,
        "COEFFICIENTS": coefficients,
    }


def execute_selected(
    selected: pd.DataFrame,
    m5: pd.DataFrame,
    cfg: dict[str, Any],
) -> tuple[pd.DataFrame, pd.DataFrame]:
    execution = cfg["execution"]
    spread_floor = (
        float(execution["minimum_retail_spread_pips"]) * PIP
    )
    slippage = (
        float(execution["extra_slippage_pips_per_side"]) * PIP
    )
    hold = pd.Timedelta(
        hours=float(execution["maximum_hold_hours"])
    )
    weight = float(execution["risk_per_trade_portfolio_r"])
    records: list[dict[str, Any]] = []
    diagnostics: list[dict[str, Any]] = []
    open_until: pd.Timestamp | None = None
    for _, candidate in selected.iterrows():
        entry_time = pd.Timestamp(candidate["entry_time_utc"])
        if open_until is not None and entry_time <= open_until:
            diagnostics.append(
                {
                    "pair_id": candidate["pair_id"],
                    "entry_time_utc": entry_time,
                    "status": "SKIP_POSITION_OPEN",
                }
            )
            continue
        side = str(candidate["model_selected_side"])
        suffix = side.lower()
        entry = float(candidate[f"entry_price_{suffix}"])
        stop = float(candidate[f"stop_price_{suffix}"])
        target = float(candidate[f"target_price_{suffix}"])
        risk = float(candidate[f"risk_distance_{suffix}"])
        exit_time, exit_price, reason = _walk_exit(
            m5,
            int(candidate["entry_position"]),
            entry_time + hold,
            side,
            stop,
            target,
            spread_floor,
            slippage,
        )
        pnl = (
            exit_price - entry
            if side == "LONG"
            else entry - exit_price
        )
        result_r = pnl / risk
        stressed_r = result_r - 0.5 * PIP / risk
        record = {
            "family": FAMILY,
            "regime": "NEUTRAL",
            "eligible_date": candidate["eligible_date"],
            "pair_id": candidate["pair_id"],
            "trade_id": f"{candidate['pair_id']}:{side}",
            "side": side,
            "event_time_utc": candidate["event_time_utc"],
            "event_currencies": candidate["event_currencies"],
            "event_cluster_size": candidate["event_cluster_size"],
            "entry_time_utc": entry_time,
            "exit_time_utc": exit_time,
            "entry_price": entry,
            "stop_price": stop,
            "target_price": target,
            "exit_price": exit_price,
            "exit_reason": reason,
            "risk_distance": risk,
            "risk_pips": risk / PIP,
            "model_probability_long": candidate[
                "model_probability_long"
            ],
            "model_probability_short": candidate[
                "model_probability_short"
            ],
            "model_selection_probability": candidate[
                "model_selection_probability"
            ],
            "model_probability_margin": candidate[
                "model_probability_margin"
            ],
            "r": result_r,
            "portfolio_r": result_r * weight,
            "extra_half_pip_stress_r": stressed_r,
            "extra_half_pip_stress_portfolio_r": stressed_r * weight,
            "fixed_0p01_lot_usd": pnl * 1000.0,
        }
        for column in _model_columns(cfg):
            if column in candidate:
                record[column] = candidate[column]
        records.append(record)
        diagnostics.append(
            {
                "pair_id": candidate["pair_id"],
                "entry_time_utc": entry_time,
                "side": side,
                "status": "EXECUTED",
                "exit_time_utc": exit_time,
                "exit_reason": reason,
            }
        )
        open_until = exit_time
    return pd.DataFrame(records), pd.DataFrame(diagnostics)


def summarize(
    trades: pd.DataFrame,
    selected: pd.DataFrame,
    m5: pd.DataFrame,
    cfg: dict[str, Any],
    census: dict[str, Any],
    oracle: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, bool]]:
    windows = {
        name: _window_metrics(
            trades,
            m5,
            pd.Timestamp(bounds[0]),
            pd.Timestamp(bounds[1]),
        )
        for name, bounds in cfg["windows"].items()
    }
    forward_start = min(
        pd.Timestamp(cfg["windows"][name][0])
        for name in cfg["forward_windows"]
    )
    forward_end = max(
        pd.Timestamp(cfg["windows"][name][1])
        for name in cfg["forward_windows"]
    )
    forward = _period(trades, forward_start, forward_end)
    daily = aggregate_days(forward)
    ticket_metrics = payoff_metrics(forward)
    daily_metrics = payoff_metrics(daily)
    stressed = payoff_metrics(
        forward, "extra_half_pip_stress_r"
    )
    top_removed = payoff_metrics(remove_top_winners(forward))
    recent_start, recent_end = map(
        pd.Timestamp, cfg["recent_six_months"]
    )
    recent = _period(trades, recent_start, recent_end)
    recent_daily = aggregate_days(recent)
    recent_metrics = payoff_metrics(recent)
    recent_daily_metrics = payoff_metrics(recent_daily)
    gate = cfg["admission"]
    forward_checks = {}
    for name in cfg["forward_windows"]:
        tickets = windows[name]["tickets"]
        day = windows[name]["daily_portfolio"]
        forward_checks[name] = (
            tickets["trades"]
            >= int(gate["minimum_forward_trades_each_window"])
            and float(gate["minimum_forward_win_rate_each_window"])
            <= tickets["win_rate"]
            <= float(gate["maximum_forward_win_rate_each_window"])
            and float(gate["minimum_realized_payoff_ratio"])
            <= tickets["realized_payoff_ratio"]
            <= float(gate["maximum_realized_payoff_ratio"])
            and tickets["profit_factor"]
            > float(
                gate[
                    "minimum_forward_profit_factor_each_window_exclusive"
                ]
            )
            and tickets["net_r"] > 0.0
            and day["profit_factor"]
            > float(
                gate[
                    "minimum_forward_daily_profit_factor_each_window_exclusive"
                ]
            )
        )
    overall_oracle = oracle["overall"]
    checks = {
        "every_forward_window": all(forward_checks.values()),
        "forward_overall_profit_factor": (
            ticket_metrics["profit_factor"]
            >= float(gate["minimum_forward_overall_profit_factor"])
        ),
        "forward_overall_win_rate": (
            float(gate["minimum_forward_overall_win_rate"])
            <= ticket_metrics["win_rate"]
            <= float(gate["maximum_forward_overall_win_rate"])
        ),
        "stressed": (
            stressed["net_r"] > 0.0
            and stressed["profit_factor"]
            > float(gate["minimum_stressed_profit_factor_exclusive"])
        ),
        "top_winners_removed": top_removed["net_r"] > 0.0,
        "daily_drawdown": (
            daily_metrics["max_drawdown_r"]
            <= float(gate["maximum_daily_portfolio_drawdown_r"])
        ),
        "recent_six_months": (
            recent_metrics["trades"]
            >= int(gate["minimum_recent_six_month_trades"])
            and recent_metrics["net_r"] > 0.0
            and recent_metrics["profit_factor"]
            > float(
                gate[
                    "minimum_recent_six_month_profit_factor_exclusive"
                ]
            )
            and recent_daily_metrics["profit_factor"] > 1.0
        ),
        "oracle_exact_precision": (
            overall_oracle["exact_precision"]
            >= float(gate["minimum_overall_exact_oracle_precision"])
        ),
        "oracle_15m_precision": (
            overall_oracle["tolerant_precision"]
            >= float(gate["minimum_overall_15m_oracle_precision"])
        ),
        "frequency_not_a_gate": (
            gate["exact_daily_frequency_gate"] is False
        ),
    }
    recent_active = active_weekday_fx_days(
        m5, recent_start, recent_end
    )
    strategy = {
        "admitted": all(checks.values()),
        "admission_checks": checks,
        "forward_window_checks": forward_checks,
        "windows": windows,
        "forward_only": {
            "tickets": ticket_metrics,
            "daily_portfolio": daily_metrics,
            "robustness": {
                "top_5_percent_winners_removed": top_removed,
                "extra_half_pip_round_trip": stressed,
            },
        },
        "frequency": {
            "source_candidates": census["forward"][
                "source_candidates"
            ],
            "selected_candidates": census["forward"][
                "selected_candidates"
            ],
            "executed_trades": int(len(trades)),
            "selected_candidate_days": int(
                selected["eligible_date"].nunique()
            ),
            "frequency_gate": False,
        },
        "recent_six_months": {
            "tickets": recent_metrics,
            "daily_portfolio": recent_daily_metrics,
            "active_weekdays": recent_active,
            "executed_neutral_days": int(
                recent["eligible_date"].nunique()
            ),
            "trades_per_active_weekday": (
                len(recent) / recent_active if recent_active else 0.0
            ),
        },
    }
    return strategy, checks


def run_neutral_selective_post_event() -> tuple[
    dict[str, Any], dict[str, pd.DataFrame]
]:
    cfg = load_config()
    candidates, m5, parent_census, feature_reasons = load_source(cfg)
    selected, scored, coefficients, census = fit_and_screen(
        candidates, m5, cfg
    )
    if census != cfg["pre_forward_selection_census"]:
        raise RuntimeError(
            "Selective post-event screen drift: "
            f"actual={census!r} "
            f"frozen={cfg['pre_forward_selection_census']!r}"
        )
    trades, diagnostics = execute_selected(selected, m5, cfg)
    oracle, matches = _oracle(trades, cfg)
    strategy, checks = summarize(
        trades, selected, m5, cfg, census, oracle
    )
    prospective_start = pd.Timestamp(cfg["prospective"]["start_utc"])
    available = int(
        selected["entry_time_utc"].ge(prospective_start).sum()
    )
    admitted = all(checks.values()) and available >= int(
        cfg["prospective"][
            "minimum_observations_before_any_promotion_review"
        ]
    )
    status = (
        "HISTORICAL_PASS_REQUIRES_PROSPECTIVE_CONFIRMATION"
        if strategy["admitted"]
        else "REJECTED_NEUTRAL_SELECTIVE_POST_EVENT_V1"
    )
    result = {
        "campaign_id": cfg["campaign_id"],
        "status": status,
        "information_status": cfg["information_status"],
        "parent_post_event_contract": cfg[
            "parent_post_event_contract"
        ],
        "causality": {
            "training_end_utc": cfg["training_window"][1],
            "single_fit": True,
            "forward_refit": False,
            "features_complete_at_entry": True,
            "forward_outcome_in_signal": False,
            "oracle_usage": "evaluation only after trade ledger",
        },
        "parent_outcome_blind_census": parent_census,
        "feature_cash_reasons": feature_reasons,
        "pre_forward_selection_census": census,
        "model": {
            "type": cfg["model"]["type"],
            "threshold": cfg["model"][
                "selection_probability_threshold"
            ],
            "feature_count": len(_model_columns(cfg)),
        },
        "strategy": strategy,
        "oracle_resemblance": oracle,
        "prospective": {
            "start_utc": prospective_start,
            "historical_rows_before_start_are_research_only": True,
            "available_points_after_start": available,
            "admitted_after_prospective_gate": admitted,
            "status": "WAITING_FOR_POST_LOCK_MARKET_DATA",
        },
        "verdict": (
            "The frozen selective post-event rule passed every historical "
            "gate but remains research-only pending prospective evidence."
            if strategy["admitted"]
            else "The frozen selective post-event rule failed one or more "
            "gates and is closed without repair."
        ),
    }
    return result, {
        "SELECTED_CANDIDATES": selected,
        "SCORED_CANDIDATES": scored,
        "COEFFICIENTS": coefficients,
        "TRADES": trades,
        "DAILY_PORTFOLIO": aggregate_days(trades),
        "DIAGNOSTICS": diagnostics,
        "ORACLE_MATCHES": matches,
    }


__all__ = [
    "OUTPUT_ROOT",
    "_side_rows",
    "add_features",
    "fit_and_screen",
    "load_config",
    "run_neutral_selective_post_event",
    "run_screen",
    "verify_lock",
    "write_json",
]
