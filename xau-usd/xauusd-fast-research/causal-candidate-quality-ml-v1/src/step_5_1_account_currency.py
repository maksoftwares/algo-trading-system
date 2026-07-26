from __future__ import annotations

import copy
from typing import Any, Mapping

import numpy as np
import pandas as pd

from step_5_portfolio import prepare_candidate_economics, run_policy


ACCOUNT_COLUMN_RENAMES = {
    "initial_risk_usd": "initial_risk_account",
    "pnl_usd": "pnl_account",
    "gross_endpoint_pnl_usd": "gross_endpoint_pnl_account",
    "implied_cost_usd": "implied_cost_account",
    "open_cost_usd": "open_cost_account",
    "margin_usd": "margin_account",
    "open_initial_risk_before_usd": "open_initial_risk_before_account",
    "open_directional_risk_before_usd": "open_directional_risk_before_account",
    "open_margin_before_usd": "open_margin_before_account",
    "closed_balance_before_usd": "closed_balance_before_account",
    "closed_drawdown_before_usd": "closed_drawdown_before_account",
}


def _convert_signed(
    values: pd.Series | np.ndarray,
    *,
    profit_rate: float,
    loss_rate: float,
) -> np.ndarray:
    array = np.asarray(values, dtype=float)
    return np.where(array >= 0.0, array * profit_rate, array * loss_rate)


def build_account_economics(
    dataset: pd.DataFrame,
    *,
    step_5_contract: Mapping[str, Any],
    broker_snapshot: Mapping[str, Any],
) -> tuple[pd.DataFrame, dict[str, float | str]]:
    base = prepare_candidate_economics(dataset, step_5_contract["account"])
    conversion = broker_snapshot["conversion"]
    profit_rate = float(conversion["profit_account_per_source_usd"])
    loss_rate = float(conversion["loss_account_per_source_usd"])
    if profit_rate <= 0.0 or loss_rate < profit_rate:
        raise ValueError("Broker conversion rates are not conservative")
    result = base.copy()
    source_names = (
        "initial_risk_usd",
        "pnl_usd",
        "gross_endpoint_pnl_usd",
        "implied_cost_usd",
        "open_cost_usd",
        "margin_usd",
    )
    for name in source_names:
        result[f"source_{name}"] = result[name]
    result["initial_risk_usd"] = result["source_initial_risk_usd"] * loss_rate
    result["gross_endpoint_pnl_usd"] = _convert_signed(
        result["source_gross_endpoint_pnl_usd"],
        profit_rate=profit_rate,
        loss_rate=loss_rate,
    )
    result["implied_cost_usd"] = result["source_implied_cost_usd"] * loss_rate
    if result["implied_cost_usd"].lt(-1e-6).any():
        raise ValueError("Negative account-currency implied cost")
    result["open_cost_usd"] = result["implied_cost_usd"].clip(lower=0.0)
    result["pnl_usd"] = (
        result["gross_endpoint_pnl_usd"] - result["implied_cost_usd"]
    )
    leverage = float(step_5_contract["account"]["conservative_leverage"])
    ounces = float(step_5_contract["account"]["xau_ounces_per_reference_lot"])
    result["margin_usd"] = result["entry_price"] * ounces * loss_rate / leverage
    result["account_currency"] = str(broker_snapshot["account"]["currency"])
    endpoint_error = (
        result["gross_endpoint_pnl_usd"]
        - result["implied_cost_usd"]
        - result["pnl_usd"]
    ).abs()
    if float(endpoint_error.max()) > 1e-8:
        raise ValueError("Account-currency endpoint reconciliation failed")
    return result, {
        "source_currency": str(conversion["source_currency"]),
        "account_currency": str(conversion["account_currency"]),
        "profit_account_per_source_usd": profit_rate,
        "loss_account_per_source_usd": loss_rate,
        "starting_equity_account": min(
            float(broker_snapshot["account"]["balance"]),
            float(broker_snapshot["account"]["equity"]),
        ),
    }


def account_policy_contract(
    step_5_contract: Mapping[str, Any],
    broker_snapshot: Mapping[str, Any],
    policy_mapping: list[list[str]],
) -> dict[str, Any]:
    contract = copy.deepcopy(step_5_contract)
    contract["account"]["starting_equity_usd"] = min(
        float(broker_snapshot["account"]["balance"]),
        float(broker_snapshot["account"]["equity"]),
    )
    mapping = {source: target for source, target in policy_mapping}
    for spec in contract["policies"]:
        spec["policy_id"] = mapping[str(spec["policy_id"])]
    contract["acceptance_gates"]["primary_policy_id"] = mapping[
        str(step_5_contract["acceptance_gates"]["primary_policy_id"])
    ]
    return contract


def _rename_state(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            str(key).replace("_usd", "_account"): _rename_state(item)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [_rename_state(item) for item in value]
    return value


def run_account_policy(
    frame: pd.DataFrame,
    *,
    spec: Mapping[str, Any],
    contract: Mapping[str, Any],
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    decisions, ledger, state = run_policy(frame, spec=spec, contract=contract)
    decisions = decisions.rename(columns=ACCOUNT_COLUMN_RENAMES)
    ledger = ledger.rename(columns=ACCOUNT_COLUMN_RENAMES)
    return decisions, ledger, _rename_state(state)


def _range_add(diff: np.ndarray, start: int, end: int, value: float) -> None:
    if start < end:
        diff[start] += value
        diff[end] -= value


def _utc_ns(values: pd.Series) -> np.ndarray:
    return (
        pd.to_datetime(values, utc=True)
        .astype("datetime64[ns, UTC]")
        .astype("int64")
        .to_numpy()
    )


def _convert_array(values: np.ndarray, profit_rate: float, loss_rate: float) -> np.ndarray:
    return np.where(values >= 0.0, values * profit_rate, values * loss_rate)


def floating_account_curve(
    bars: pd.DataFrame,
    ledger: pd.DataFrame,
    *,
    starting_equity_account: float,
    bar_minutes: int,
    profit_rate: float,
    loss_rate: float,
) -> pd.DataFrame:
    n = len(bars)
    if n == 0:
        raise ValueError("M5 bars are empty")
    bar_ns = _utc_ns(bars["timestamp_utc"])
    bar_end_ns = bar_ns + int(pd.Timedelta(minutes=bar_minutes).value)
    bid_low = bars["bid_low"].to_numpy(float)
    bid_high = bars["bid_high"].to_numpy(float)
    bid_close = bars["bid_close"].to_numpy(float)
    ask_low = bars["ask_low"].to_numpy(float)
    ask_high = bars["ask_high"].to_numpy(float)
    ask_close = bars["ask_close"].to_numpy(float)
    low_floating = np.zeros(n)
    high_floating = np.zeros(n)
    close_floating = np.zeros(n)
    risk_diff = np.zeros(n + 1)
    margin_diff = np.zeros(n + 1)
    position_diff = np.zeros(n + 1)

    if len(ledger):
        entry_ns = _utc_ns(ledger["entry_time"])
        exit_ns = _utc_ns(ledger["label_end_time"])
        if entry_ns.min() < bar_ns.min() or exit_ns.max() > bar_end_ns.max():
            raise ValueError("M5 history does not contain every accepted trade")
        for row in ledger.itertuples(index=False):
            entry = int(row.entry_time.value)
            exit_ = int(row.label_end_time.value)
            start = int(np.searchsorted(bar_end_ns, entry, side="right"))
            end = int(np.searchsorted(bar_ns, exit_, side="left"))
            close_end = int(np.searchsorted(bar_end_ns, exit_, side="left"))
            sign = 1.0 if row.direction == "LONG" else -1.0
            adverse = (
                bid_low[start:end] if sign > 0 else ask_high[start:end]
            )
            favorable = (
                bid_high[start:end] if sign > 0 else ask_low[start:end]
            )
            gross_low = sign * (adverse - float(row.entry_price))
            gross_high = sign * (favorable - float(row.entry_price))
            low_floating[start:end] += _convert_array(
                gross_low, profit_rate, loss_rate
            ) - float(row.open_cost_account)
            high_floating[start:end] += _convert_array(
                gross_high, profit_rate, loss_rate
            ) - float(row.open_cost_account)
            close_prices = (
                bid_close[start:close_end] if sign > 0 else ask_close[start:close_end]
            )
            gross_close = sign * (close_prices - float(row.entry_price))
            close_floating[start:close_end] += _convert_array(
                gross_close, profit_rate, loss_rate
            ) - float(row.open_cost_account)
            _range_add(
                risk_diff, start, end, float(row.initial_risk_account)
            )
            _range_add(margin_diff, start, end, float(row.margin_account))
            _range_add(position_diff, start, end, 1.0)
        exits = ledger.sort_values(["label_end_time", "candidate_id"], kind="stable")
        ordered_exit_ns = _utc_ns(exits["label_end_time"])
        cumulative = np.concatenate(
            ([0.0], np.cumsum(exits["pnl_account"].to_numpy(float)))
        )
        realized_before = cumulative[
            np.searchsorted(ordered_exit_ns, bar_ns, side="right")
        ]
        realized_close = cumulative[
            np.searchsorted(ordered_exit_ns, bar_end_ns, side="right")
        ]
    else:
        realized_before = np.zeros(n)
        realized_close = np.zeros(n)
    return pd.DataFrame(
        {
            "timestamp_utc": bars["timestamp_utc"],
            "low_equity_account": starting_equity_account
            + realized_before
            + low_floating,
            "high_equity_account": starting_equity_account
            + realized_before
            + high_floating,
            "close_equity_account": starting_equity_account
            + realized_close
            + close_floating,
            "open_positions": np.rint(np.cumsum(position_diff[:-1])).astype(int),
            "open_initial_risk_account": np.cumsum(risk_diff[:-1]),
            "open_margin_account": np.cumsum(margin_diff[:-1]),
        }
    )
