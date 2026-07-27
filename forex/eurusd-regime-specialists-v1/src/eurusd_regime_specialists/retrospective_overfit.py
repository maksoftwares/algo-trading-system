from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from .asymmetric import (
    load_asymmetric_config,
    payoff_metrics,
    walk_timed_long_exit,
)
from .ensemble import (
    OWNERS,
    generate_ensemble_signals,
    load_ensemble_config,
    load_inputs,
)
from .research import (
    PACKAGE_ROOT,
    PIP,
    active_weekday_fx_days,
    is_quarantined,
    serialize,
)


CELL_COLUMNS = ["owner", "seed_id", "entry_hour_utc"]
MINIMUM_CELL_TRADES = 15
MINIMUM_CELL_WIN_RATE = 0.45
MAXIMUM_CELL_WIN_RATE = 0.65
MINIMUM_CELL_PROFIT_FACTOR = 1.30
TARGET_TRADES_PER_ACTIVE_DAY = 4
REGIME_LABELS = {
    "S1_COMPRESSION_REVERSION": (
        "JOINT_COMPRESSION",
        "Non-shock DXY and EURUSD joint compression",
    ),
    "S2_SUPPORTIVE_PULLBACK": (
        "USD_DOWN_SUPPORTIVE",
        "Non-compressed USD-down regime supporting the EURUSD long",
    ),
    "S3_NEUTRAL_AUCTION": (
        "NEUTRAL_AUCTION",
        "Non-compressed neutral USD regime",
    ),
    "S4_OPPOSING_CAPITULATION": (
        "USD_UP_OPPOSING",
        "Non-compressed USD-up regime; deep counter-regime capitulation only",
    ),
}
FIT_END = pd.Timestamp("2026-06-30T23:59:59Z")
EARLY_FIT_END = pd.Timestamp("2024-12-31T23:59:59Z")
PSEUDO_OOS_START = pd.Timestamp("2025-01-01T00:00:00Z")


def select_cells(
    opportunity_outcomes: pd.DataFrame,
    fit_end: pd.Timestamp = FIT_END,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Select cells with hindsight.

    This is intentionally contaminated: the same realized outcomes used to
    select a cell are later included in the fitted backtest.
    """
    fit = opportunity_outcomes[
        opportunity_outcomes["entry_time_utc"] <= fit_end
    ].copy()
    grouped = (
        fit.groupby(CELL_COLUMNS, as_index=False)
        .agg(
            trades=("r", "size"),
            wins=("r", lambda values: int((values > 0).sum())),
            gross_profit_r=("r", lambda values: float(values[values > 0].sum())),
            gross_loss_r=("r", lambda values: float(-values[values < 0].sum())),
            net_r=("r", "sum"),
        )
    )
    grouped["win_rate"] = grouped["wins"] / grouped["trades"]
    grouped["profit_factor"] = grouped["gross_profit_r"] / grouped["gross_loss_r"]
    selected = grouped[
        (grouped["trades"] >= MINIMUM_CELL_TRADES)
        & (grouped["win_rate"] >= MINIMUM_CELL_WIN_RATE)
        & (grouped["win_rate"] <= MAXIMUM_CELL_WIN_RATE)
        & (grouped["profit_factor"] >= MINIMUM_CELL_PROFIT_FACTOR)
    ].copy()
    return (
        selected.sort_values(
            ["profit_factor", "net_r"], ascending=[False, False]
        ).reset_index(drop=True),
        grouped.sort_values(
            ["profit_factor", "net_r"], ascending=[False, False]
        ).reset_index(drop=True),
    )


def resolve_portfolio(
    opportunities: pd.DataFrame,
    maximum_trades_per_utc_day: int,
) -> pd.DataFrame:
    """Apply the original one-position and daily-count rules to candidate outcomes."""
    if opportunities.empty:
        return opportunities.copy()
    ordered = opportunities.sort_values(
        ["entry_time_utc", "owner_priority", "seed_priority"]
    )
    accepted: list[int] = []
    open_until: pd.Timestamp | None = None
    daily_count: dict[str, int] = {}
    for index, row in ordered.iterrows():
        entry_time = row["entry_time_utc"]
        if open_until is not None and entry_time <= open_until:
            continue
        day = entry_time.strftime("%Y-%m-%d")
        if daily_count.get(day, 0) >= maximum_trades_per_utc_day:
            continue
        accepted.append(index)
        open_until = row["exit_time_utc"]
        daily_count[day] = daily_count.get(day, 0) + 1
    return ordered.loc[accepted].reset_index(drop=True)


def apply_cells(
    opportunity_outcomes: pd.DataFrame,
    selected_cells: pd.DataFrame,
    maximum_trades_per_utc_day: int,
    start: pd.Timestamp | None = None,
    end: pd.Timestamp | None = None,
) -> pd.DataFrame:
    if selected_cells.empty:
        return opportunity_outcomes.iloc[0:0].copy()
    keys = selected_cells[CELL_COLUMNS]
    eligible = opportunity_outcomes.merge(keys, on=CELL_COLUMNS, how="inner")
    if start is not None:
        eligible = eligible[eligible["entry_time_utc"] >= start]
    if end is not None:
        eligible = eligible[eligible["entry_time_utc"] <= end]
    return resolve_portfolio(eligible, maximum_trades_per_utc_day)


def build_opportunity_outcomes(
    signals: pd.DataFrame,
    m5: pd.DataFrame,
    entry_cfg: dict[str, Any],
    payoff_cfg: dict[str, Any],
) -> pd.DataFrame:
    """Calculate every candidate's later outcome before applying portfolio occupancy.

    This outcome table is valid for demonstrating selection bias only. It must
    never be used as a causal feature or as promotion evidence.
    """
    execution = entry_cfg["execution"]
    owner_priority = {
        owner: index
        for index, owner in enumerate(entry_cfg["portfolio"]["priority"])
    }
    target_r = float(payoff_cfg["exit"]["target_r"])
    hold_hours = int(payoff_cfg["exit"]["maximum_hold_hours"])
    spread_floor = (
        float(payoff_cfg["exit"]["minimum_retail_spread_pips"]) * PIP
    )
    slippage = (
        float(payoff_cfg["exit"]["extra_slippage_pips_per_side"]) * PIP
    )
    records: list[dict[str, Any]] = []
    for _, signal in signals.sort_values(
        ["completion_time_utc", "seed_priority"]
    ).iterrows():
        position = int(
            m5.index.searchsorted(signal["completion_time_utc"], side="left")
        )
        if position >= len(m5):
            continue
        entry_time = m5.index[position]
        if is_quarantined(entry_time, "EURUSD", entry_cfg["quarantine"]):
            continue
        bar = m5.iloc[position]
        entry = (
            max(
                float(bar["ask_open"]),
                float(bar["bid_open"]) + spread_floor,
            )
            + slippage
        )
        stop_distance = max(
            float(signal["stop_atr_multiple"]) * float(signal["atr"]),
            float(signal["stop_floor_pips"]) * PIP,
        )
        stop = min(float(signal["recent_low"]), entry - stop_distance)
        risk = entry - stop
        if risk <= 0 or risk > float(signal["stop_ceiling_pips"]) * PIP:
            continue
        target = entry + target_r * risk
        exit_time, exit_price, reason = walk_timed_long_exit(
            m5,
            position,
            entry_time + pd.Timedelta(hours=hold_hours),
            stop,
            target,
            slippage,
        )
        pnl = exit_price - entry
        records.append(
            {
                "owner": signal["owner"],
                "seed_id": signal["seed_id"],
                "entry_hour_utc": int(entry_time.hour),
                "owner_priority": owner_priority[signal["owner"]],
                "seed_priority": int(signal["seed_priority"]),
                "signal_time_utc": signal["signal_time_utc"],
                "entry_time_utc": entry_time,
                "exit_time_utc": exit_time,
                "exit_reason": reason,
                "entry_price": entry,
                "stop_price": stop,
                "target_price": target,
                "exit_price": exit_price,
                "risk_distance": risk,
                "r": pnl / risk,
                "fixed_0p01_lot_usd": pnl * 1000.0,
            }
        )
    return pd.DataFrame(records)


def summarize(
    trades: pd.DataFrame,
    m5: pd.DataFrame,
    start: pd.Timestamp,
    end: pd.Timestamp,
) -> dict[str, Any]:
    metrics = payoff_metrics(trades)
    metrics["fixed_0p01_lot_usd"] = (
        float(trades["fixed_0p01_lot_usd"].sum()) if not trades.empty else 0.0
    )
    days = active_weekday_fx_days(m5, start, end)
    metrics["trades_per_active_weekday"] = len(trades) / days if days else 0.0
    return metrics


def maximum_concurrent_positions(trades: pd.DataFrame) -> int:
    events: list[tuple[pd.Timestamp, int]] = []
    for _, trade in trades.iterrows():
        events.append((trade["entry_time_utc"], 1))
        events.append((trade["exit_time_utc"], -1))
    current = 0
    maximum = 0
    # An exit at a timestamp frees exposure before another entry at that time.
    for _, change in sorted(events, key=lambda item: (item[0], item[1])):
        current += change
        maximum = max(maximum, current)
    return maximum


def summarize_concurrent(
    trades: pd.DataFrame,
    m5: pd.DataFrame,
    start: pd.Timestamp,
    end: pd.Timestamp,
) -> dict[str, Any]:
    metrics = summarize(trades, m5, start, end)
    active_days = (
        int(trades["entry_time_utc"].dt.date.nunique())
        if not trades.empty
        else 0
    )
    market_days = active_weekday_fx_days(m5, start, end)
    metrics.update(
        {
            "active_days": active_days,
            "trades_per_active_day": (
                len(trades) / active_days if active_days else 0.0
            ),
            "active_day_coverage": (
                active_days / market_days if market_days else 0.0
            ),
            "maximum_concurrent_positions": maximum_concurrent_positions(
                trades
            ),
        }
    )
    return metrics


def summarize_perfect_oracle(
    trades: pd.DataFrame,
    m5: pd.DataFrame,
    start: pd.Timestamp,
    end: pd.Timestamp,
) -> dict[str, Any]:
    metrics = summarize_concurrent(trades, m5, start, end)
    metrics["realized_payoff_ratio"] = None
    metrics["realized_payoff_ratio_display"] = "UNDEFINED_NO_LOSSES"
    metrics["profit_factor"] = None
    metrics["profit_factor_display"] = "INFINITE_NO_LOSSES"
    return metrics


def density_bucket(
    opportunity_outcomes: pd.DataFrame, trades_per_day: int
) -> pd.DataFrame:
    dates = opportunity_outcomes["entry_time_utc"].dt.strftime("%Y-%m-%d")
    counts = dates.value_counts()
    selected_dates = set(counts[counts == trades_per_day].index)
    return opportunity_outcomes[dates.isin(selected_dates)].sort_values(
        ["entry_time_utc", "owner_priority", "seed_priority"]
    ).reset_index(drop=True)


def perfect_foresight_oracle(
    opportunity_outcomes: pd.DataFrame,
    winners_per_active_day: int = TARGET_TRADES_PER_ACTIVE_DAY,
) -> pd.DataFrame:
    """Keep four known future target hits on every qualifying historical day."""
    future_winners = opportunity_outcomes[
        (opportunity_outcomes["r"] > 0)
        & opportunity_outcomes["exit_reason"].eq("TARGET")
    ].copy()
    dates = future_winners["entry_time_utc"].dt.strftime("%Y-%m-%d")
    counts = dates.value_counts()
    qualifying_dates = set(
        counts[counts >= winners_per_active_day].index
    )
    future_winners["oracle_date"] = dates
    return (
        future_winners[future_winners["oracle_date"].isin(qualifying_dates)]
        .sort_values(["entry_time_utc", "owner_priority", "seed_priority"])
        .groupby("oracle_date", sort=True)
        .head(winners_per_active_day)
        .reset_index(drop=True)
    )


def regime_attribution(
    perfect_trades: pd.DataFrame,
    recent_start: pd.Timestamp = pd.Timestamp("2026-01-01T00:00:00Z"),
) -> pd.DataFrame:
    rows = []
    total = len(perfect_trades)
    for owner in OWNERS:
        frame = perfect_trades[perfect_trades["owner"].eq(owner)]
        recent = frame[frame["entry_time_utc"] >= recent_start]
        label, definition = REGIME_LABELS[owner]
        rows.append(
            {
                "owner": owner,
                "regime": label,
                "definition": definition,
                "trades": int(len(frame)),
                "trade_share": len(frame) / total if total else 0.0,
                "active_days": int(frame["oracle_date"].nunique()),
                "trades_per_regime_active_day": (
                    len(frame) / frame["oracle_date"].nunique()
                    if not frame.empty
                    else 0.0
                ),
                "win_rate": (
                    float((frame["r"] > 0).mean())
                    if not frame.empty
                    else 0.0
                ),
                "average_winner_r": (
                    float(frame["r"].mean()) if not frame.empty else 0.0
                ),
                "net_r": float(frame["r"].sum()),
                "fixed_0p01_lot_usd": float(
                    frame["fixed_0p01_lot_usd"].sum()
                ),
                "recent_six_months_trades": int(len(recent)),
                "recent_six_months_active_days": int(
                    recent["oracle_date"].nunique()
                ),
                "recent_six_months_net_r": float(recent["r"].sum()),
            }
        )
    return pd.DataFrame(rows)


def density_ladder(
    opportunity_outcomes: pd.DataFrame,
    m5: pd.DataFrame,
    start: pd.Timestamp,
    end: pd.Timestamp,
) -> pd.DataFrame:
    rows = []
    for count in range(1, 13):
        frame = density_bucket(opportunity_outcomes, count)
        metrics = summarize_concurrent(frame, m5, start, end)
        rows.append(
            {
                "daily_opportunity_count": count,
                **metrics,
            }
        )
    return pd.DataFrame(rows)


def _window(
    trades: pd.DataFrame, start: str, end: str
) -> pd.DataFrame:
    return trades[
        (trades["entry_time_utc"] >= pd.Timestamp(start))
        & (trades["entry_time_utc"] <= pd.Timestamp(end))
    ]


def _equity_rows(
    fitted: pd.DataFrame,
    chronological: pd.DataFrame,
    density_oracle: pd.DataFrame,
    perfect_oracle: pd.DataFrame,
) -> pd.DataFrame:
    rows = []
    for label, frame in (
        ("FULL_HISTORY_FITTED", fitted),
        ("CHRONOLOGICAL_2025_2026", chronological),
        ("FOUR_TRADE_DAY_ORACLE", density_oracle),
        ("PERFECT_FORESIGHT_ORACLE", perfect_oracle),
    ):
        equity = 0.0
        rows.append(
            {
                "series": label,
                "entry_time_utc": (
                    frame["entry_time_utc"].min()
                    if not frame.empty
                    else PSEUDO_OOS_START
                ),
                "cumulative_r": equity,
            }
        )
        for _, trade in frame.sort_values("entry_time_utc").iterrows():
            equity += float(trade["r"])
            rows.append(
                {
                    "series": label,
                    "entry_time_utc": trade["entry_time_utc"],
                    "cumulative_r": equity,
                }
            )
    return pd.DataFrame(rows)


def run_retrospective_overfit() -> tuple[
    dict[str, Any],
    dict[str, pd.DataFrame],
]:
    entry_cfg = load_ensemble_config()
    payoff_cfg = load_asymmetric_config()
    m5, state, _ = load_inputs(entry_cfg)
    signals = generate_ensemble_signals(m5, state, entry_cfg)
    owned = signals[signals["owner"].isin(OWNERS)].copy()
    opportunities = build_opportunity_outcomes(
        owned, m5, entry_cfg, payoff_cfg
    )
    maximum_daily = int(entry_cfg["execution"]["max_trades_per_utc_day"])
    start = pd.Timestamp(entry_cfg["data"]["start_utc"])
    end = pd.Timestamp(entry_cfg["data"]["end_utc"])

    baseline = resolve_portfolio(opportunities, maximum_daily)
    selected, all_cells = select_cells(opportunities)
    fitted = apply_cells(opportunities, selected, maximum_daily)

    early_cells, _ = select_cells(opportunities, EARLY_FIT_END)
    early_train = apply_cells(
        opportunities, early_cells, maximum_daily, start, EARLY_FIT_END
    )
    chronological = apply_cells(
        opportunities, early_cells, maximum_daily, PSEUDO_OOS_START, end
    )
    ladder = density_ladder(opportunities, m5, start, end)
    density_oracle = density_bucket(
        opportunities, TARGET_TRADES_PER_ACTIVE_DAY
    )
    perfect_oracle = perfect_foresight_oracle(opportunities)

    recent = _window(
        fitted,
        "2026-01-01T00:00:00Z",
        "2026-06-30T23:59:59Z",
    )
    periods = {
        "2019_2021": (
            "2019-01-01T00:00:00Z",
            "2021-12-31T23:59:59Z",
        ),
        "2022_2024": (
            "2022-01-01T00:00:00Z",
            "2024-12-31T23:59:59Z",
        ),
        "2025": (
            "2025-01-01T00:00:00Z",
            "2025-12-31T23:59:59Z",
        ),
        "2026_h1": (
            "2026-01-01T00:00:00Z",
            "2026-06-30T23:59:59Z",
        ),
    }
    density_recent = _window(
        density_oracle,
        "2026-01-01T00:00:00Z",
        "2026-06-30T23:59:59Z",
    )
    perfect_recent = _window(
        perfect_oracle,
        "2026-01-01T00:00:00Z",
        "2026-06-30T23:59:59Z",
    )
    perfect_regimes = regime_attribution(perfect_oracle)
    result = {
        "status": "INTENTIONALLY_OVERFIT_DIAGNOSTIC_NOT_TRADABLE",
        "warning": (
            "The perfect oracle reads each candidate's future exit and deletes "
            "every loss; other diagnostics use future daily counts or realized "
            "cell outcomes. Nothing in this package is causal, out-of-sample, "
            "or promotion evidence."
        ),
        "method": {
            "gold_analogue": (
                "Retrospective filtering over a broad all-opportunity ledger, "
                "including a daily-density ladder and specialist-hour cells."
            ),
            "target_trades_per_active_day": TARGET_TRADES_PER_ACTIVE_DAY,
            "density_ladder_buckets": list(range(1, 13)),
            "candidate_cells": int(len(all_cells)),
            "cell_dimensions": CELL_COLUMNS,
            "selection": {
                "minimum_cell_trades": MINIMUM_CELL_TRADES,
                "minimum_cell_win_rate": MINIMUM_CELL_WIN_RATE,
                "maximum_cell_win_rate": MAXIMUM_CELL_WIN_RATE,
                "minimum_cell_profit_factor": MINIMUM_CELL_PROFIT_FACTOR,
            },
            "selected_cells": int(len(selected)),
            "selected_early_cells": int(len(early_cells)),
            "opportunity_outcomes": int(len(opportunities)),
            "cell_fit_portfolio_rule": (
                "One position at a time, original daily cap, exact archived "
                "bid/ask, spread floor, slippage, and stop-first execution."
            ),
            "density_oracle_portfolio_rule": (
                "Independent concurrent specialists, exact archived bid/ask, "
                "spread floor, slippage, and stop-first execution; no shared-"
                "account margin or floating-equity claim."
            ),
            "perfect_foresight_rule": (
                "Directly read future TARGET outcomes, retain four known "
                "winners per qualifying day, and discard every losing trade."
            ),
        },
        "baseline": summarize(baseline, m5, start, end),
        "perfect_foresight_four_winner_oracle": {
            "status": "DIRECT_FUTURE_OUTCOME_LEAKAGE",
            "rule": (
                "Inspect every candidate's future exit, retain only target "
                "winners, keep the first four winners on dates having at least "
                "four future target winners, and discard every loss."
            ),
            "full_history": summarize_perfect_oracle(
                perfect_oracle, m5, start, end
            ),
            "by_period": {
                name: summarize_perfect_oracle(
                    _window(perfect_oracle, window_start, window_end),
                    m5,
                    pd.Timestamp(window_start),
                    pd.Timestamp(window_end),
                )
                for name, (window_start, window_end) in periods.items()
            },
            "latest_six_months": summarize_perfect_oracle(
                perfect_recent,
                m5,
                pd.Timestamp("2026-01-01T00:00:00Z"),
                pd.Timestamp("2026-06-30T23:59:59Z"),
            ),
            "regime_attribution": perfect_regimes.to_dict(
                orient="records"
            ),
        },
        "four_trade_active_day_oracle": {
            "status": "IMPOSSIBLE_CAUSALLY_RETROSPECTIVE_DAILY_COUNT",
            "rule": (
                "Keep all independently priced specialist opportunities only "
                "on UTC dates later observed to contain exactly four total "
                "opportunities. The day's final count is unknowable when its "
                "earlier trades must be entered."
            ),
            "full_history": summarize_concurrent(
                density_oracle, m5, start, end
            ),
            "by_period": {
                name: summarize_concurrent(
                    _window(density_oracle, window_start, window_end),
                    m5,
                    pd.Timestamp(window_start),
                    pd.Timestamp(window_end),
                )
                for name, (window_start, window_end) in periods.items()
            },
            "latest_six_months": summarize_concurrent(
                density_recent,
                m5,
                pd.Timestamp("2026-01-01T00:00:00Z"),
                pd.Timestamp("2026-06-30T23:59:59Z"),
            ),
        },
        "low_frequency_cell_fit": summarize(fitted, m5, start, end),
        "low_frequency_cell_fit_by_period": {
            name: summarize(
                _window(fitted, window_start, window_end),
                m5,
                pd.Timestamp(window_start),
                pd.Timestamp(window_end),
            )
            for name, (window_start, window_end) in periods.items()
        },
        "low_frequency_latest_six_months_included_in_fit": summarize(
            recent,
            m5,
            pd.Timestamp("2026-01-01T00:00:00Z"),
            pd.Timestamp("2026-06-30T23:59:59Z"),
        ),
        "chronological_reality_check": {
            "fit_window": "2019-01-01 through 2024-12-31",
            "test_window": "2025-01-01 through 2026-06-30",
            "selected_cells": int(len(early_cells)),
            "fit": summarize(early_train, m5, start, EARLY_FIT_END),
            "future": summarize(
                chronological, m5, PSEUDO_OOS_START, end
            ),
        },
        "verdict": (
            "The pure hindsight ceiling reaches four trades per active day "
            "and 100% wins only by reading each candidate's future exit and "
            "discarding every loss. It is label leakage, not a strategy."
        ),
    }
    artifacts = {
        "OPPORTUNITY_OUTCOMES": opportunities,
        "ALL_CELLS": all_cells,
        "SELECTED_CELLS": selected,
        "FITTED_TRADES": fitted,
        "EARLY_SELECTED_CELLS": early_cells,
        "CHRONOLOGICAL_TRADES": chronological,
        "DENSITY_LADDER": ladder,
        "FOUR_TRADE_DAY_ORACLE_TRADES": density_oracle,
        "PERFECT_FORESIGHT_TRADES": perfect_oracle,
        "PERFECT_FORESIGHT_BY_REGIME": perfect_regimes,
        "EQUITY_CURVES": _equity_rows(
            fitted, chronological, density_oracle, perfect_oracle
        ),
    }
    for owner in OWNERS:
        artifacts[f"PERFECT_{owner}_TRADES"] = perfect_oracle[
            perfect_oracle["owner"].eq(owner)
        ].copy()
    return result, artifacts


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(serialize(payload), indent=2), encoding="utf-8")


def output_root() -> Path:
    return PACKAGE_ROOT / "outputs" / "retrospective_overfit"
