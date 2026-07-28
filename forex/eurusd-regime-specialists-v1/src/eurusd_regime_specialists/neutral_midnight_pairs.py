from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from .asymmetric import payoff_metrics
from .ensemble import load_ensemble_config
from .neutral_session_oco import _effective_ask, _walk_exit, write_json
from .research import (
    PACKAGE_ROOT,
    PIP,
    active_weekday_fx_days,
    is_quarantined,
    load_inputs,
    remove_top_winners,
    sha256_file,
)


FAMILY = "N20_NEUTRAL_MIDNIGHT_DUAL_SIDE_PAIRS"
OUTPUT_ROOT = PACKAGE_ROOT / "outputs" / "neutral_midnight_pairs"


def load_config() -> dict[str, Any]:
    return json.loads(
        (
            PACKAGE_ROOT
            / "config"
            / "frozen_neutral_midnight_pairs.json"
        ).read_text(encoding="utf-8")
    )


def load_oracle(cfg: dict[str, Any]) -> pd.DataFrame:
    frame = pd.read_csv(PACKAGE_ROOT / cfg["oracle_source"])
    for column in ("entry_time_utc", "exit_time_utc"):
        frame[column] = pd.to_datetime(frame[column], utc=True)
    return (
        frame[frame["regime"].eq(cfg["oracle_regime"])]
        .sort_values(["entry_time_utc", "oracle_trade_number"])
        .reset_index(drop=True)
    )


def _f1(precision: float, recall: float) -> float:
    return (
        2.0 * precision * recall / (precision + recall)
        if precision + recall > 0
        else 0.0
    )


def oracle_match_metrics(
    trades: pd.DataFrame,
    oracle: pd.DataFrame,
    start: pd.Timestamp,
    end: pd.Timestamp,
    tolerance_minutes: int,
) -> tuple[dict[str, Any], pd.DataFrame]:
    actual = oracle[
        oracle["entry_time_utc"].between(start, end, inclusive="both")
    ].copy()
    predicted = trades[
        trades["entry_time_utc"].between(start, end, inclusive="both")
    ].copy()
    exact_keys = set(
        zip(actual["entry_time_utc"], actual["side"], strict=False)
    )
    exact_matches = int(
        sum(
            (entry, side) in exact_keys
            for entry, side in zip(
                predicted["entry_time_utc"],
                predicted["side"],
                strict=False,
            )
        )
    )
    exact_precision = (
        exact_matches / len(predicted) if len(predicted) else 0.0
    )
    exact_recall = exact_matches / len(actual) if len(actual) else 0.0
    available = actual.reset_index(drop=True)
    unmatched = set(available.index)
    records: list[dict[str, Any]] = []
    tolerance = pd.Timedelta(minutes=tolerance_minutes)
    for trade_index, trade in predicted.sort_values(
        "entry_time_utc"
    ).iterrows():
        candidates = [
            index
            for index in unmatched
            if available.at[index, "side"] == trade["side"]
            and available.at[index, "entry_time_utc"].date()
            == trade["entry_time_utc"].date()
        ]
        if not candidates:
            continue
        chosen = min(
            candidates,
            key=lambda index: abs(
                available.at[index, "entry_time_utc"]
                - trade["entry_time_utc"]
            ),
        )
        difference = abs(
            available.at[chosen, "entry_time_utc"]
            - trade["entry_time_utc"]
        )
        if difference > tolerance:
            continue
        unmatched.remove(chosen)
        records.append(
            {
                "trade_index": trade_index,
                "trade_entry_time_utc": trade["entry_time_utc"],
                "trade_side": trade["side"],
                "oracle_entry_time_utc": available.at[
                    chosen, "entry_time_utc"
                ],
                "oracle_trade_number": available.at[
                    chosen, "oracle_trade_number"
                ],
                "absolute_difference_minutes": (
                    difference.total_seconds() / 60.0
                ),
            }
        )
    tolerant_matches = len(records)
    tolerant_precision = (
        tolerant_matches / len(predicted) if len(predicted) else 0.0
    )
    tolerant_recall = (
        tolerant_matches / len(actual) if len(actual) else 0.0
    )
    metrics = {
        "predicted_trades": int(len(predicted)),
        "oracle_trades": int(len(actual)),
        "exact_matches": exact_matches,
        "exact_precision": exact_precision,
        "exact_recall": exact_recall,
        "exact_f1": _f1(exact_precision, exact_recall),
        "tolerance_minutes": tolerance_minutes,
        "tolerant_matches": tolerant_matches,
        "tolerant_precision": tolerant_precision,
        "tolerant_recall": tolerant_recall,
        "tolerant_f1": _f1(tolerant_precision, tolerant_recall),
    }
    return metrics, pd.DataFrame(records)


def verify_lock() -> dict[str, str]:
    lock = json.loads(
        (
            PACKAGE_ROOT
            / "EURUSD_NEUTRAL_MIDNIGHT_PAIRS_PREREG_2026_07_28.sha256.json"
        ).read_text(encoding="utf-8")
    )
    if (
        lock.get("locked_before_midnight_pairs_outcome_pass")
        is not True
    ):
        raise RuntimeError("Neutral midnight-pairs contract is not locked")
    checked: dict[str, str] = {}
    for relative, expected in lock["files"].items():
        actual = sha256_file(PACKAGE_ROOT / relative)
        if actual != expected:
            raise RuntimeError(
                "Neutral midnight-pairs preregistration mismatch: "
                f"{relative}"
            )
        checked[relative] = actual
    cfg = load_config()
    parent = cfg["data_and_classifier_contract"]
    parent_actual = sha256_file(PACKAGE_ROOT / parent["path"])
    if parent_actual != parent["sha256"]:
        raise RuntimeError("Neutral midnight-pairs parent contract drift")
    return checked


def _window_name(
    timestamp: pd.Timestamp,
    windows: dict[str, list[str]],
) -> str:
    for name, (start_raw, end_raw) in windows.items():
        if pd.Timestamp(start_raw) <= timestamp <= pd.Timestamp(end_raw):
            return name
    return "OUTSIDE"


def build_candidates(
    m5: pd.DataFrame,
    state: pd.DataFrame,
    cfg: dict[str, Any],
    *,
    enforce_frozen_census: bool,
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    strategy = cfg["strategy"]
    base = load_ensemble_config()
    hour = int(strategy["anchor_hour_utc"])
    offsets = [int(value) for value in strategy["pair_offsets_minutes"]]
    sides = [str(value) for value in strategy["sides_each_pair"]]
    midnights = m5.index[
        (m5.index.hour == hour)
        & (m5.index.minute == 0)
        & (m5.index.weekday < 5)
    ]
    day_records: list[dict[str, Any]] = []
    for anchor in midnights:
        schedule = [
            anchor + pd.Timedelta(minutes=offset) for offset in offsets
        ]
        complete = all(timestamp in m5.index for timestamp in schedule)
        quarantined = complete and any(
            is_quarantined(
                timestamp,
                "EURUSD",
                base["quarantine"],
            )
            for timestamp in schedule
        )
        day_records.append(
            {
                "eligible_date": anchor.strftime("%Y-%m-%d"),
                "anchor_time_utc": anchor,
                "state_time_utc": anchor - pd.Timedelta(hours=1),
                "schedule_complete": complete,
                "quarantined": quarantined,
                "window": _window_name(anchor, cfg["windows"]),
            }
        )
    days = pd.DataFrame(day_records)
    if days.empty:
        return pd.DataFrame(), days, {}
    days["state_time_utc"] = days["state_time_utc"].dt.as_unit("ns")
    state_columns = [
        "direction",
        "shock",
        "DXY_compressed",
        "EURUSD_compressed",
    ]
    states = (
        state[state_columns]
        .reset_index()
        .rename(columns={"timestamp_utc": "matched_state_time_utc"})
        .sort_values("matched_state_time_utc")
    )
    states["matched_state_time_utc"] = states[
        "matched_state_time_utc"
    ].dt.as_unit("ns")
    days = pd.merge_asof(
        days.sort_values("state_time_utc"),
        states,
        left_on="state_time_utc",
        right_on="matched_state_time_utc",
        direction="backward",
        allow_exact_matches=True,
    )
    shock = days["shock"].astype("boolean").fillna(True)
    compression = (
        days["DXY_compressed"].astype("boolean").fillna(False)
        & days["EURUSD_compressed"].astype("boolean").fillna(False)
    )
    days["neutral_owned"] = (
        days["direction"].eq(
            cfg["neutral_ownership"]["requires_direction"]
        )
        & ~shock
        & ~compression
    )
    days["eligible_day"] = (
        days["schedule_complete"]
        & ~days["quarantined"]
        & days["neutral_owned"]
    )
    records: list[dict[str, Any]] = []
    for _, day in days[days["eligible_day"]].iterrows():
        anchor = day["anchor_time_utc"]
        for offset in offsets:
            entry_time = anchor + pd.Timedelta(minutes=offset)
            position = int(m5.index.get_loc(entry_time))
            pair_id = (
                f"{day['eligible_date']}T"
                f"{entry_time.strftime('%H%M')}"
            )
            for side in sides:
                records.append(
                    {
                        "family": FAMILY,
                        "regime": "NEUTRAL",
                        "eligible_date": day["eligible_date"],
                        "pair_id": pair_id,
                        "trade_id": f"{pair_id}:{side}",
                        "pair_offset_minutes": offset,
                        "side": side,
                        "anchor_time_utc": anchor,
                        "state_time_utc": day["state_time_utc"],
                        "matched_state_time_utc": day[
                            "matched_state_time_utc"
                        ],
                        "entry_time_utc": entry_time,
                        "entry_position": position,
                        "window": day["window"],
                        "trade_candidate": True,
                    }
                )
    candidates = pd.DataFrame(records)
    if candidates.empty:
        day_counts = pd.Series(dtype=int)
    else:
        day_counts = candidates.groupby("eligible_date").size()
    by_window: dict[str, Any] = {}
    for name in cfg["windows"]:
        window_days = days[
            days["eligible_day"] & days["window"].eq(name)
        ]
        window_candidates = (
            candidates[candidates["window"].eq(name)]
            if not candidates.empty
            else candidates
        )
        by_window[name] = {
            "eligible_days": int(len(window_days)),
            "pair_timestamps": int(
                window_candidates["pair_id"].nunique()
            )
            if not window_candidates.empty
            else 0,
            "trade_candidates": int(len(window_candidates)),
        }
    eligible_days = int(days["eligible_day"].sum())
    exact_days = int(
        (
            day_counts
            == int(strategy["required_trades_per_eligible_day"])
        ).sum()
    )
    census = {
        "weekday_midnights": int(len(midnights)),
        "schedule_complete_days": int(days["schedule_complete"].sum()),
        "neutral_schedule_complete_days": int(
            (days["schedule_complete"] & days["neutral_owned"]).sum()
        ),
        "quarantined_neutral_days": int(
            (
                days["schedule_complete"]
                & days["neutral_owned"]
                & days["quarantined"]
            ).sum()
        ),
        "eligible_days": eligible_days,
        "pair_timestamps": int(candidates["pair_id"].nunique())
        if not candidates.empty
        else 0,
        "trade_candidates": int(len(candidates)),
        "long_candidates": int(candidates["side"].eq("LONG").sum())
        if not candidates.empty
        else 0,
        "short_candidates": int(candidates["side"].eq("SHORT").sum())
        if not candidates.empty
        else 0,
        "days_exactly_four_trade_candidates": exact_days,
        "eligible_day_exact_four_coverage": (
            exact_days / eligible_days if eligible_days else 0.0
        ),
        "by_window": by_window,
    }
    if (
        enforce_frozen_census
        and census != cfg["outcome_blind_census"]
    ):
        raise RuntimeError(
            "Midnight-pairs census drift: "
            f"actual={census!r} "
            f"frozen={cfg['outcome_blind_census']!r}"
        )
    sorted_candidates = (
        candidates.sort_values(
            ["entry_time_utc", "side"]
        ).reset_index(drop=True)
        if not candidates.empty
        else candidates
    )
    return (
        sorted_candidates,
        days.sort_values("anchor_time_utc").reset_index(drop=True),
        census,
    )


def simulate(
    candidates: pd.DataFrame,
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
    risk = float(execution["risk_pips"]) * PIP
    target_distance = float(execution["target_r"]) * risk
    hold = pd.Timedelta(
        hours=float(execution["maximum_hold_hours"])
    )
    ticket_weight = float(execution["risk_per_ticket_portfolio_r"])
    records: list[dict[str, Any]] = []
    diagnostics: list[dict[str, Any]] = []
    for _, candidate in candidates.iterrows():
        entry_time = candidate["entry_time_utc"]
        position = int(candidate["entry_position"])
        bar = m5.iloc[position]
        side = str(candidate["side"])
        if side == "LONG":
            entry = (
                _effective_ask(bar, "open", spread_floor) + slippage
            )
            stop = entry - risk
            target = entry + target_distance
        else:
            entry = float(bar["bid_open"]) - slippage
            stop = entry + risk
            target = entry - target_distance
        exit_time, exit_price, reason = _walk_exit(
            m5,
            position,
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
        records.append(
            {
                "family": FAMILY,
                "regime": "NEUTRAL",
                "eligible_date": candidate["eligible_date"],
                "pair_id": candidate["pair_id"],
                "trade_id": candidate["trade_id"],
                "pair_offset_minutes": candidate[
                    "pair_offset_minutes"
                ],
                "side": side,
                "anchor_time_utc": candidate["anchor_time_utc"],
                "state_time_utc": candidate["state_time_utc"],
                "matched_state_time_utc": candidate[
                    "matched_state_time_utc"
                ],
                "entry_time_utc": entry_time,
                "exit_time_utc": exit_time,
                "entry_price": entry,
                "stop_price": stop,
                "target_price": target,
                "exit_price": exit_price,
                "exit_reason": reason,
                "risk_distance": risk,
                "r": result_r,
                "portfolio_r": result_r * ticket_weight,
                "extra_half_pip_stress_r": stressed_r,
                "extra_half_pip_stress_portfolio_r": (
                    stressed_r * ticket_weight
                ),
                "fixed_0p01_lot_usd": pnl * 1000.0,
            }
        )
        diagnostics.append(
            {
                "trade_id": candidate["trade_id"],
                "pair_id": candidate["pair_id"],
                "entry_time_utc": entry_time,
                "side": side,
                "status": "EXECUTED",
                "exit_time_utc": exit_time,
                "exit_reason": reason,
            }
        )
    return pd.DataFrame(records), pd.DataFrame(diagnostics)


def aggregate_pairs(trades: pd.DataFrame) -> pd.DataFrame:
    if trades.empty:
        return pd.DataFrame()
    pairs = (
        trades.groupby("pair_id", sort=True)
        .agg(
            eligible_date=("eligible_date", "first"),
            entry_time_utc=("entry_time_utc", "first"),
            tickets=("trade_id", "size"),
            winning_tickets=("r", lambda values: int((values > 0).sum())),
            losing_tickets=("r", lambda values: int((values < 0).sum())),
            r=("r", "sum"),
            portfolio_r=("portfolio_r", "sum"),
            extra_half_pip_stress_r=(
                "extra_half_pip_stress_r",
                "sum",
            ),
            extra_half_pip_stress_portfolio_r=(
                "extra_half_pip_stress_portfolio_r",
                "sum",
            ),
        )
        .reset_index()
    )
    pairs["outcome"] = "FLAT"
    pairs.loc[pairs["r"] > 0, "outcome"] = "POSITIVE"
    pairs.loc[pairs["r"] < 0, "outcome"] = "NEGATIVE"
    return pairs


def aggregate_days(trades: pd.DataFrame) -> pd.DataFrame:
    if trades.empty:
        return pd.DataFrame()
    days = (
        trades.groupby("eligible_date", sort=True)
        .agg(
            entry_time_utc=("entry_time_utc", "first"),
            tickets=("trade_id", "size"),
            pairs=("pair_id", "nunique"),
            raw_ticket_r=("r", "sum"),
            r=("portfolio_r", "sum"),
            extra_half_pip_stress_r=(
                "extra_half_pip_stress_portfolio_r",
                "sum",
            ),
        )
        .reset_index()
    )
    return days


def _window(
    frame: pd.DataFrame,
    start_raw: str,
    end_raw: str,
) -> pd.DataFrame:
    if frame.empty:
        return frame
    return frame[
        frame["entry_time_utc"].between(
            pd.Timestamp(start_raw),
            pd.Timestamp(end_raw),
            inclusive="both",
        )
    ]


def _metric_windows(
    frame: pd.DataFrame,
    windows: dict[str, list[str]],
) -> dict[str, Any]:
    return {
        name: payoff_metrics(_window(frame, start, end))
        for name, (start, end) in windows.items()
    }


def summarize(
    trades: pd.DataFrame,
    pairs: pd.DataFrame,
    days: pd.DataFrame,
    m5: pd.DataFrame,
    cfg: dict[str, Any],
    census: dict[str, Any],
) -> dict[str, Any]:
    ticket_windows = _metric_windows(trades, cfg["windows"])
    pair_windows = _metric_windows(pairs, cfg["windows"])
    daily_windows = _metric_windows(days, cfg["windows"])
    tickets_overall = payoff_metrics(trades)
    pairs_overall = payoff_metrics(pairs)
    days_overall = payoff_metrics(days)
    stressed_tickets = payoff_metrics(
        trades, "extra_half_pip_stress_r"
    )
    stressed_pairs = payoff_metrics(
        pairs, "extra_half_pip_stress_r"
    )
    stressed_days = payoff_metrics(
        days, "extra_half_pip_stress_r"
    )
    ticket_top_removed = payoff_metrics(
        remove_top_winners(trades)
    )
    pair_top_removed = payoff_metrics(remove_top_winners(pairs))
    daily_top_removed = payoff_metrics(remove_top_winners(days))
    executed_counts = (
        trades.groupby("eligible_date").size()
        if not trades.empty
        else pd.Series(dtype=int)
    )
    required = int(
        cfg["strategy"]["required_trades_per_eligible_day"]
    )
    exact_executed = int((executed_counts == required).sum())
    eligible_days = int(census["eligible_days"])
    frequency = {
        "eligible_days": eligible_days,
        "executed_days": int(len(executed_counts)),
        "days_exactly_four_executed_tickets": exact_executed,
        "eligible_day_exact_four_execution_coverage": (
            exact_executed / eligible_days if eligible_days else 0.0
        ),
        "tickets_per_eligible_day": (
            len(trades) / eligible_days if eligible_days else 0.0
        ),
    }
    pair_outcomes = {
        "both_won": int((pairs["winning_tickets"] == 2).sum()),
        "one_won": int((pairs["winning_tickets"] == 1).sum()),
        "none_won": int((pairs["winning_tickets"] == 0).sum()),
        "positive_pair": int(pairs["outcome"].eq("POSITIVE").sum()),
        "flat_pair": int(pairs["outcome"].eq("FLAT").sum()),
        "negative_pair": int(pairs["outcome"].eq("NEGATIVE").sum()),
    }
    gate = cfg["admission"]
    checks = {
        "ticket_windows": all(
            block["trades"]
            >= int(gate["minimum_ticket_trades_each_window"])
            and float(gate["minimum_win_rate"])
            <= block["win_rate"]
            <= float(gate["maximum_win_rate"])
            and float(gate["minimum_realized_payoff_ratio"])
            <= block["realized_payoff_ratio"]
            <= float(gate["maximum_realized_payoff_ratio"])
            and block["profit_factor"]
            >= float(
                gate["minimum_ticket_profit_factor_each_window"]
            )
            and block["expectancy_r"] > 0
            for block in ticket_windows.values()
        ),
        "pair_windows": all(
            block["trades"]
            >= int(gate["minimum_pair_timestamps_each_window"])
            and block["profit_factor"]
            >= float(gate["minimum_pair_profit_factor_each_window"])
            and block["expectancy_r"] > 0
            for block in pair_windows.values()
        ),
        "daily_windows": all(
            block["trades"]
            >= int(gate["minimum_eligible_days_each_window"])
            and block["profit_factor"]
            >= float(gate["minimum_daily_profit_factor_each_window"])
            and block["expectancy_r"] > 0
            for block in daily_windows.values()
        ),
        "overall_ticket_profit_factor": (
            tickets_overall["profit_factor"]
            >= float(gate["minimum_overall_ticket_profit_factor"])
        ),
        "daily_portfolio_drawdown": (
            days_overall["max_drawdown_r"]
            <= float(gate["maximum_daily_portfolio_drawdown_r"])
        ),
        "ticket_top_winners_removed_positive": (
            ticket_top_removed["net_r"] > 0
        ),
        "daily_top_winners_removed_positive": (
            daily_top_removed["net_r"] > 0
        ),
        "stressed_ticket": (
            stressed_tickets["net_r"] > 0
            and stressed_tickets["profit_factor"]
            >= float(gate["minimum_stressed_ticket_profit_factor"])
        ),
        "stressed_daily": (
            stressed_days["net_r"] > 0
            and stressed_days["profit_factor"]
            >= float(gate["minimum_stressed_daily_profit_factor"])
        ),
        "exact_four_execution": (
            eligible_days > 0 and exact_executed == eligible_days
        ),
    }
    recent_start, recent_end = cfg["recent_six_months"]
    recent_trades = _window(trades, recent_start, recent_end)
    recent_pairs = _window(pairs, recent_start, recent_end)
    recent_days = _window(days, recent_start, recent_end)
    active_days = active_weekday_fx_days(
        m5,
        pd.Timestamp(recent_start),
        pd.Timestamp(recent_end),
    )
    recent_eligible = len(recent_days)
    recent = {
        "tickets": payoff_metrics(recent_trades),
        "pairs": payoff_metrics(recent_pairs),
        "daily_portfolio": payoff_metrics(recent_days),
        "active_weekdays": active_days,
        "eligible_neutral_days": recent_eligible,
        "tickets_per_active_weekday": (
            len(recent_trades) / active_days if active_days else 0.0
        ),
        "tickets_per_eligible_neutral_day": (
            len(recent_trades) / recent_eligible
            if recent_eligible
            else 0.0
        ),
    }
    return {
        "admitted": all(checks.values()),
        "admission_checks": checks,
        "tickets": {
            "overall": tickets_overall,
            "windows": ticket_windows,
        },
        "pairs": {
            "overall": pairs_overall,
            "windows": pair_windows,
            "outcomes": pair_outcomes,
        },
        "daily_portfolio": {
            "overall": days_overall,
            "windows": daily_windows,
        },
        "frequency": frequency,
        "robustness": {
            "ticket_top_5_percent_winners_removed": (
                ticket_top_removed
            ),
            "pair_top_5_percent_winners_removed": pair_top_removed,
            "daily_top_5_percent_winners_removed": (
                daily_top_removed
            ),
            "extra_half_pip_tickets": stressed_tickets,
            "extra_half_pip_pairs": stressed_pairs,
            "extra_half_pip_daily_portfolio": stressed_days,
        },
        "recent_six_months": recent,
    }


def evaluate_oracle(
    trades: pd.DataFrame,
    cfg: dict[str, Any],
) -> tuple[dict[str, Any], pd.DataFrame]:
    oracle = load_oracle(cfg)
    first = min(pd.Timestamp(values[0]) for values in cfg["windows"].values())
    last = max(pd.Timestamp(values[1]) for values in cfg["windows"].values())
    exact, _ = oracle_match_metrics(trades, oracle, first, last, 0)
    tolerance = int(cfg["oracle_matching"]["secondary_tolerance_minutes"])
    tolerant, matches = oracle_match_metrics(
        trades,
        oracle,
        first,
        last,
        tolerance,
    )
    by_window: dict[str, Any] = {}
    for name, (start_raw, end_raw) in cfg["windows"].items():
        start = pd.Timestamp(start_raw)
        end = pd.Timestamp(end_raw)
        exact_window, _ = oracle_match_metrics(
            trades, oracle, start, end, 0
        )
        tolerant_window, _ = oracle_match_metrics(
            trades, oracle, start, end, tolerance
        )
        by_window[name] = {
            "exact": exact_window,
            "tolerant": tolerant_window,
        }
    return {
        "exact": exact,
        "tolerant": tolerant,
        "by_window": by_window,
    }, matches


def run_census() -> dict[str, Any]:
    cfg = load_config()
    base = load_ensemble_config()
    m5, state, _ = load_inputs(base)
    _, _, census = build_candidates(
        m5,
        state,
        cfg,
        enforce_frozen_census=False,
    )
    return census


def run_neutral_midnight_pairs() -> tuple[
    dict[str, Any],
    dict[str, pd.DataFrame],
]:
    verify_lock()
    cfg = load_config()
    base = load_ensemble_config()
    m5, state, manifests = load_inputs(base)
    candidates, day_eligibility, census = build_candidates(
        m5,
        state,
        cfg,
        enforce_frozen_census=True,
    )
    trades, diagnostics = simulate(candidates, m5, cfg)
    pairs = aggregate_pairs(trades)
    days = aggregate_days(trades)
    strategy = summarize(
        trades,
        pairs,
        days,
        m5,
        cfg,
        census,
    )
    oracle, matches = evaluate_oracle(trades, cfg)
    prospective_start = pd.Timestamp(
        cfg["prospective"]["start_utc"]
    )
    prospective = candidates[
        candidates["entry_time_utc"] >= prospective_start
    ]
    result = {
        "campaign_id": cfg["campaign_id"],
        "status": (
            "CAUSAL_RESEARCH_PASS_REQUIRES_PROSPECTIVE_CONFIRMATION"
            if strategy["admitted"]
            else "REJECTED_NEUTRAL_MIDNIGHT_PAIRS_V1"
        ),
        "information_status": cfg["information_status"],
        "source_manifests": manifests,
        "causality": {
            "regime": cfg["neutral_ownership"]["state"],
            "direction": (
                "No prediction: long and short tickets are both retained"
            ),
            "entry": "Fixed 00:00 and 00:05 UTC M5 opens",
            "future_information_in_signal_or_execution": False,
            "loser_deletion_or_opposite_side_cancellation": False,
            "oracle_usage": "evaluation only after trade ledger",
        },
        "account_constraint": {
            "required": cfg["execution"]["account_mode_required"],
            "netting_account_compatible": False,
        },
        "outcome_blind_census": census,
        "strategy": strategy,
        "oracle_resemblance": oracle,
        "prospective": {
            "start_utc": cfg["prospective"]["start_utc"],
            "historical_rows_before_start_are_research_only": True,
            "available_candidates_after_start": int(len(prospective)),
            "status": (
                "WAITING_FOR_POST_LOCK_MARKET_DATA"
                if prospective.empty
                else "POST_LOCK_CANDIDATES_AVAILABLE"
            ),
        },
        "verdict": (
            "The fixed dual-side pairs passed every historical gate; "
            "only post-lock rows may confirm it."
            if strategy["admitted"]
            else "The fixed dual-side pairs failed one or more frozen "
            "gates and are closed without repair."
        ),
    }
    return result, {
        "DAY_ELIGIBILITY": day_eligibility,
        "CANDIDATES": candidates,
        "EXECUTION_DIAGNOSTICS": diagnostics,
        "TRADES": trades,
        "PAIRS": pairs,
        "DAILY_PORTFOLIO": days,
        "ORACLE_MATCHES": matches,
    }


__all__ = [
    "OUTPUT_ROOT",
    "aggregate_days",
    "aggregate_pairs",
    "build_candidates",
    "load_config",
    "run_census",
    "run_neutral_midnight_pairs",
    "simulate",
    "summarize",
    "verify_lock",
    "write_json",
]
