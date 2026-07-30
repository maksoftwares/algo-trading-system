from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import pandas as pd

from .h4_chop_anchor_validation import _evaluation_subset, _scenario_summary
from .h4_trend_pullback_continuation import protected_date_overlap
from .neutral_h4_quiet_state_transfer import (
    PIP,
    PIP_VALUE_USD_001_LOT,
    sha256_file,
)
from .retrospective_overfit import resolve_portfolio


def utc_timestamp(value: str | pd.Timestamp) -> pd.Timestamp:
    result = pd.Timestamp(value)
    if result.tzinfo is None:
        return result.tz_localize("UTC")
    return result.tz_convert("UTC")


def load_opportunities(path: Path, expected_rows: int) -> pd.DataFrame:
    frame = pd.read_csv(path)
    if len(frame) != int(expected_rows):
        raise RuntimeError("Opportunity ledger row count mismatch")
    for column in ("signal_time_utc", "entry_time_utc", "exit_time_utc"):
        frame[column] = pd.to_datetime(frame[column], utc=True)
    frame["stop_pips"] = frame["risk_distance"].astype(float) / PIP
    frame["pnl_usd_001_lot"] = frame["fixed_0p01_lot_usd"].astype(float)
    frame["stress_r"] = frame["r"].astype(float)
    return frame.sort_values(
        ["entry_time_utc", "owner_priority", "seed_priority"]
    ).reset_index(drop=True)


def apply_stress(trades: pd.DataFrame, extra_pips: float) -> pd.DataFrame:
    result = trades.copy()
    result["r"] = result["r"] - float(extra_pips) / result["stop_pips"]
    result["stress_r"] = result["r"]
    result["pnl_usd_001_lot"] = result["pnl_usd_001_lot"] - (
        float(extra_pips) * PIP_VALUE_USD_001_LOT
    )
    return result


def select_completed_cells(
    opportunities: pd.DataFrame,
    contract: dict[str, Any],
    cutoff: pd.Timestamp,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    columns = list(contract["columns"])
    cutoff = utc_timestamp(cutoff)
    fit = opportunities[
        (opportunities["entry_time_utc"] >= utc_timestamp(contract["training_start"]))
        & (opportunities["exit_time_utc"] < cutoff)
    ].copy()
    grouped = (
        fit.groupby(columns, as_index=False)
        .agg(
            trades=("r", "size"),
            wins=("r", lambda values: int((values > 0.0).sum())),
            gross_profit_r=(
                "r",
                lambda values: float(values[values > 0.0].sum()),
            ),
            gross_loss_r=(
                "r",
                lambda values: float(-values[values < 0.0].sum()),
            ),
            net_r=("r", "sum"),
        )
        .sort_values(columns)
        .reset_index(drop=True)
    )
    if grouped.empty:
        grouped["win_rate"] = pd.Series(dtype=float)
        grouped["profit_factor"] = pd.Series(dtype=float)
        return grouped.copy(), grouped
    grouped["win_rate"] = grouped["wins"] / grouped["trades"]
    grouped["profit_factor"] = (
        grouped["gross_profit_r"] / grouped["gross_loss_r"]
    )
    selected = grouped[
        (grouped["trades"] >= int(contract["minimum_completed_trades"]))
        & (grouped["win_rate"] >= float(contract["minimum_win_rate"]))
        & (grouped["win_rate"] <= float(contract["maximum_win_rate"]))
        & (
            grouped["profit_factor"]
            >= float(contract["minimum_profit_factor"])
        )
    ].copy()
    return (
        selected.sort_values(
            ["profit_factor", "net_r"], ascending=[False, False]
        ).reset_index(drop=True),
        grouped.sort_values(
            ["profit_factor", "net_r"], ascending=[False, False]
        ).reset_index(drop=True),
    )


def eligible_in_window(
    opportunities: pd.DataFrame,
    selected_cells: pd.DataFrame,
    columns: list[str],
    window: list[str],
    window_name: str,
) -> pd.DataFrame:
    if selected_cells.empty:
        result = opportunities.iloc[0:0].copy()
        result["walk_forward_window"] = pd.Series(dtype=str)
        return result
    start, end = map(utc_timestamp, window)
    eligible = opportunities.merge(
        selected_cells[columns], on=columns, how="inner"
    )
    eligible = eligible[
        (eligible["entry_time_utc"] >= start)
        & (eligible["entry_time_utc"] < end)
    ].copy()
    eligible["walk_forward_window"] = window_name
    return eligible


def weekday_count(windows: dict[str, list[str]]) -> int:
    total = 0
    for start_value, end_value in windows.values():
        start = utc_timestamp(start_value)
        end = utc_timestamp(end_value)
        total += len(
            pd.bdate_range(
                start=start.normalize(),
                end=(end - pd.Timedelta(nanoseconds=1)).normalize(),
            )
        )
    return total


def summarize_economics(
    trades: pd.DataFrame,
    *,
    weekdays: int,
    stress_pips: float,
) -> dict[str, Any]:
    base = _scenario_summary(trades)
    stressed = _scenario_summary(apply_stress(trades, stress_pips))
    active_dates = (
        trades["entry_time_utc"].dt.strftime("%Y-%m-%d").nunique()
        if not trades.empty
        else 0
    )
    base["trades_per_weekday"] = (
        len(trades) / int(weekdays) if weekdays else 0.0
    )
    base["active_dates"] = int(active_dates)
    base["active_date_coverage"] = (
        int(active_dates) / int(weekdays) if weekdays else 0.0
    )
    return {"base": base, "stressed": stressed}


def run_walk_forward_stage(
    opportunities: pd.DataFrame,
    windows: dict[str, list[str]],
    cell_contract: dict[str, Any],
    execution: dict[str, Any],
) -> dict[str, Any]:
    candidate_parts: list[pd.DataFrame] = []
    selection_parts: list[pd.DataFrame] = []
    selection_counts: dict[str, int] = {}
    columns = list(cell_contract["columns"])
    for name, window in windows.items():
        start = utc_timestamp(window[0])
        selected, _ = select_completed_cells(
            opportunities, cell_contract, cutoff=start
        )
        selected = selected.assign(
            walk_forward_window=name,
            selection_cutoff_utc=start,
        )
        selection_parts.append(selected)
        selection_counts[name] = len(selected)
        candidate_parts.append(
            eligible_in_window(
                opportunities,
                selected,
                columns,
                window,
                name,
            )
        )

    candidates = pd.concat(candidate_parts, ignore_index=True)
    trades = resolve_portfolio(
        candidates,
        int(execution["maximum_trades_per_utc_day"]),
    )
    stress_pips = float(execution["extra_round_trip_stress_pips"])
    per_window: dict[str, dict[str, Any]] = {}
    for name, window in windows.items():
        subset = _evaluation_subset(trades, window)
        per_window[name] = {
            "selected_cells": selection_counts[name],
            "economics": summarize_economics(
                subset,
                weekdays=weekday_count({name: window}),
                stress_pips=stress_pips,
            ),
        }
    selections = pd.concat(selection_parts, ignore_index=True)
    return {
        "trades": trades,
        "selections": selections,
        "selected_cells": selection_counts,
        "windows": per_window,
        "economics": summarize_economics(
            trades,
            weekdays=weekday_count(windows),
            stress_pips=stress_pips,
        ),
    }


def development_checks(
    stage: dict[str, Any], gates: dict[str, Any]
) -> dict[str, bool]:
    base = stage["economics"]["base"]
    return {
        "minimum_selected_cells_each_year": all(
            count >= int(gates["minimum_selected_cells_each_year"])
            for count in stage["selected_cells"].values()
        ),
        "minimum_trades": base["trades"] >= int(gates["minimum_trades"]),
        "minimum_trades_per_weekday": base["trades_per_weekday"]
        >= float(gates["minimum_trades_per_weekday"]),
        "minimum_profit_factor": base["profit_factor"]
        >= float(gates["minimum_profit_factor"]),
        "minimum_stressed_profit_factor": stage["economics"]["stressed"][
            "profit_factor"
        ]
        >= float(gates["minimum_stressed_profit_factor"]),
        "each_year_profit_factor": all(
            value["economics"]["base"]["profit_factor"]
            > float(gates["minimum_each_year_profit_factor_exclusive"])
            for value in stage["windows"].values()
        ),
        "top_5pct_winners_removed_profit_factor": base[
            "top_5pct_winners_removed_profit_factor"
        ]
        >= float(gates["minimum_top_5pct_winners_removed_profit_factor"]),
        "maximum_closed_trade_drawdown": base["maximum_drawdown_r"]
        <= float(gates["maximum_closed_trade_drawdown_r"]),
    }


def validation_checks(
    stage: dict[str, Any],
    latest: dict[str, Any],
    overlap: dict[str, Any],
    gates: dict[str, Any],
) -> dict[str, bool]:
    base = stage["economics"]["base"]
    return {
        "minimum_selected_cells_each_year": all(
            count >= int(gates["minimum_selected_cells_each_year"])
            for count in stage["selected_cells"].values()
        ),
        "minimum_trades": base["trades"] >= int(gates["minimum_trades"]),
        "minimum_trades_per_weekday": base["trades_per_weekday"]
        >= float(gates["minimum_trades_per_weekday"]),
        "minimum_profit_factor": base["profit_factor"]
        >= float(gates["minimum_profit_factor"]),
        "minimum_stressed_profit_factor": stage["economics"]["stressed"][
            "profit_factor"
        ]
        >= float(gates["minimum_stressed_profit_factor"]),
        "each_year_profit_factor": all(
            value["economics"]["base"]["profit_factor"]
            > float(gates["minimum_each_year_profit_factor_exclusive"])
            for value in stage["windows"].values()
        ),
        "minimum_latest_12_month_profit_factor": latest["base"]["profit_factor"]
        >= float(gates["minimum_latest_12_month_profit_factor"]),
        "top_5pct_winners_removed_profit_factor": base[
            "top_5pct_winners_removed_profit_factor"
        ]
        >= float(gates["minimum_top_5pct_winners_removed_profit_factor"]),
        "maximum_closed_trade_drawdown": base["maximum_drawdown_r"]
        <= float(gates["maximum_closed_trade_drawdown_r"]),
        "minimum_unique_dates_per_broker_weekday": overlap[
            "unique_dates_per_broker_weekday"
        ]
        >= float(gates["minimum_unique_dates_per_broker_weekday"]),
        "maximum_protected_date_overlap_share": overlap[
            "protected_overlap_share"
        ]
        <= float(gates["maximum_protected_date_overlap_share"]),
    }


def render_report(result: dict[str, Any]) -> str:
    dev = result["development"]
    base = dev["economics"]["base"]
    selection_rows = "\n".join(
        f"| {name} | {count} | "
        f'{dev["windows"][name]["economics"]["base"]["trades"]} | '
        f'{dev["windows"][name]["economics"]["base"]["profit_factor"]:.3f} |'
        for name, count in dev["selected_cells"].items()
    )
    if result["validation"] is None:
        validation_text = "Locked validation remained unopened."
    else:
        validation = result["validation"]
        val = validation["economics"]["base"]
        validation_text = (
            "| Trades | Trades/weekday | PF | Stressed PF | Admitted |\n"
            "|---:|---:|---:|---:|---:|\n"
            f'| {val["trades"]} | {val["trades_per_weekday"]:.3f} | '
            f'{val["profit_factor"]:.3f} | '
            f'{validation["economics"]["stressed"]["profit_factor"]:.3f} | '
            f'{validation["admitted"]} |'
        )
    return f"""# EURUSD annual expanding-cell specialist result

Status: **{result["status"]}**

Demo-order authorization: **false**

## Development 2022-2023

| Trades | Trades/weekday | Win rate | Payoff | PF | Stressed PF | Selected |
|---:|---:|---:|---:|---:|---:|---:|
| {base["trades"]} | {base["trades_per_weekday"]:.3f} | {base["win_rate"]:.2%} | {base["realized_payoff_ratio"]:.3f} | {base["profit_factor"]:.3f} | {dev["economics"]["stressed"]["profit_factor"]:.3f} | {dev["selected"]} |

| Annual inference window | Selected cells | Trades | PF |
|---|---:|---:|---:|
{selection_rows}

## Locked validation

{validation_text}

Every annual cell list was fixed from outcomes completed before that year's
January boundary. No current-year outcome, threshold rescue, or future ranking
entered a decision. Historical success cannot authorize demo orders.
"""


def run(config_path: Path, output_dir: Path) -> dict[str, Any]:
    config_bytes = config_path.read_bytes()
    config = json.loads(config_bytes)
    root = config_path.parent.parent
    opportunity_path = root / config["opportunity_ledger"]["path"]
    protected_path = root / config["protected_broker_ledger"]["path"]
    for path, expected in (
        (opportunity_path, config["opportunity_ledger"]["sha256"]),
        (protected_path, config["protected_broker_ledger"]["sha256"]),
    ):
        if sha256_file(path) != expected:
            raise RuntimeError(f"Source checksum mismatch: {path}")
    opportunities = load_opportunities(
        opportunity_path, int(config["opportunity_ledger"]["rows"])
    )
    development = run_walk_forward_stage(
        opportunities,
        config["walk_forward"]["development_windows"],
        config["cell_contract"],
        config["execution"],
    )
    dev_checks = development_checks(
        development, config["development_admission"]
    )
    selected = all(dev_checks.values())
    development["checks"] = dev_checks
    development["selected"] = selected

    validation: dict[str, Any] | None = None
    validation_trades = opportunities.iloc[0:0].copy()
    validation_selections = development["selections"].iloc[0:0].copy()
    if selected:
        validation = run_walk_forward_stage(
            opportunities,
            config["walk_forward"]["locked_validation_windows"],
            config["cell_contract"],
            config["execution"],
        )
        validation_trades = validation["trades"]
        validation_selections = validation["selections"]
        latest_trades = _evaluation_subset(
            validation_trades, config["walk_forward"]["latest_12_months"]
        )
        latest = summarize_economics(
            latest_trades,
            weekdays=weekday_count(
                {"LATEST_12_MONTHS": config["walk_forward"]["latest_12_months"]}
            ),
            stress_pips=float(
                config["execution"]["extra_round_trip_stress_pips"]
            ),
        )
        protected = pd.read_csv(protected_path)
        overlap = protected_date_overlap(
            validation_trades,
            set(protected["entry_date"].astype(str)),
            broker_weekdays=int(
                config["protected_broker_ledger"]["weekdays"]
            ),
        )
        checks = validation_checks(
            validation,
            latest,
            overlap,
            config["locked_validation_admission"],
        )
        validation["latest_12_months"] = latest
        validation["protected_date_overlap"] = overlap
        validation["checks"] = checks
        validation["admitted"] = all(checks.values())

    if not selected:
        status = "DEVELOPMENT_REJECTED_VALIDATION_UNOPENED"
    elif validation is not None and validation["admitted"]:
        status = "HISTORICAL_CANDIDATE_REQUIRES_FRESH_CONFIRMATION"
    else:
        status = "LOCKED_VALIDATION_REJECTED"

    result = {
        "schema_version": "eurusd_annual_expanding_cell_specialist_result_v1",
        "frozen_config_sha256": hashlib.sha256(config_bytes).hexdigest(),
        "opportunity_ledger_sha256": config["opportunity_ledger"]["sha256"],
        "research_boundary": "RETROSPECTIVE_CAUSAL_NOT_PRISTINE_OOS",
        "broker_action_allowed": False,
        "demo_order_authorized": False,
        "development": {
            key: value
            for key, value in development.items()
            if key not in {"trades", "selections"}
        },
        "validation": (
            {
                key: value
                for key, value in validation.items()
                if key not in {"trades", "selections"}
            }
            if validation is not None
            else None
        ),
        "status": status,
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    pd.concat(
        [
            development["trades"].assign(stage="DEVELOPMENT"),
            validation_trades.assign(stage="VALIDATION"),
        ],
        ignore_index=True,
    ).to_csv(output_dir / "TRADES.csv", index=False)
    pd.concat(
        [
            development["selections"].assign(stage="DEVELOPMENT"),
            validation_selections.assign(stage="VALIDATION"),
        ],
        ignore_index=True,
    ).to_csv(output_dir / "ANNUAL_SELECTED_CELLS.csv", index=False)
    (output_dir / "RESULT.json").write_text(
        json.dumps(result, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    (output_dir / "RESULT.md").write_text(
        render_report(result), encoding="utf-8"
    )
    return result
