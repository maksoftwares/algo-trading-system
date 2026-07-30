from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

PACKAGE_ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = PACKAGE_ROOT / "config" / "frequency_edge_frontier_diagnostic_v1.json"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_config() -> dict[str, Any]:
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    if config["status"] != "RETROSPECTIVE_DIAGNOSTIC_NOT_PREREGISTERED":
        raise RuntimeError("unexpected frequency-frontier research boundary")
    return config


def profit_factor(values: pd.Series | np.ndarray) -> float:
    array = np.asarray(values, dtype=float)
    gross_profit = float(array[array > 0.0].sum())
    gross_loss = float(-array[array < 0.0].sum())
    if gross_loss == 0.0:
        return math.inf if gross_profit > 0.0 else 0.0
    return gross_profit / gross_loss


def _trading_date(timestamp: pd.Timestamp) -> str:
    # The Sunday 22:00 UTC Forex open belongs to Monday's trading session.
    adjusted = timestamp + pd.Timedelta(days=1) if timestamp.weekday() == 6 else timestamp
    return adjusted.date().isoformat()


def _maximum_concurrency(frame: pd.DataFrame) -> int:
    events: list[tuple[pd.Timestamp, int]] = []
    for row in frame.itertuples():
        events.append((row.entry_time, 1))
        events.append((row.exit_time, -1))
    active = 0
    maximum = 0
    # Exits are processed before entries at an identical timestamp.
    for _, delta in sorted(events, key=lambda item: (item[0], item[1])):
        active += delta
        maximum = max(maximum, active)
    return maximum


def outcome_metrics(
    frame: pd.DataFrame,
    weekday_denominator: int,
    extra_cost_usd: float,
) -> dict[str, Any]:
    if frame.empty:
        return {
            "trades": 0,
            "trades_per_weekday": 0.0,
            "weekday_coverage": 0.0,
            "active_trading_dates": 0,
            "win_rate": 0.0,
            "payoff_ratio": None,
            "profit_factor": 0.0,
            "plus_0_5_pip_profit_factor": 0.0,
            "net_pnl_usd": 0.0,
            "maximum_closed_trade_drawdown_usd": 0.0,
            "top_5pct_removed_profit_factor": 0.0,
            "positive_active_month_share": 0.0,
        }
    ordered = frame.sort_values(["exit_time", "component", "entry_time"]).copy()
    pnl = ordered["pnl_usd"].astype(float)
    winners = pnl[pnl > 0.0]
    losers = pnl[pnl < 0.0]
    payoff = (
        float(winners.mean() / -losers.mean())
        if not winners.empty and not losers.empty
        else None
    )
    equity = pnl.cumsum().to_numpy()
    path = np.concatenate(([0.0], equity))
    drawdown = np.maximum.accumulate(path) - path
    remove_count = max(1, math.ceil(len(ordered) * 0.05))
    removed = ordered.drop(ordered.nlargest(remove_count, "pnl_usd").index)
    trading_dates = {
        _trading_date(timestamp) for timestamp in ordered["entry_time"]
    }
    monthly = (
        ordered.assign(month=ordered["entry_time"].dt.strftime("%Y-%m"))
        .groupby("month")["pnl_usd"]
        .sum()
    )
    return {
        "trades": len(ordered),
        "trades_per_weekday": float(len(ordered) / weekday_denominator),
        "weekday_coverage": float(len(trading_dates) / weekday_denominator),
        "active_trading_dates": len(trading_dates),
        "trades_per_active_trading_date": float(len(ordered) / len(trading_dates)),
        "win_rate": float((pnl > 0.0).mean()),
        "payoff_ratio": payoff,
        "profit_factor": profit_factor(pnl),
        "plus_0_5_pip_profit_factor": profit_factor(pnl - extra_cost_usd),
        "net_pnl_usd": float(pnl.sum()),
        "maximum_closed_trade_drawdown_usd": float(drawdown.max()),
        "top_5pct_removed_profit_factor": profit_factor(removed["pnl_usd"]),
        "positive_active_month_share": float((monthly > 0.0).mean()),
    }


def load_sources(
    config: dict[str, Any],
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, str]]:
    source = config["source"]
    rsi_path = PACKAGE_ROOT / source["rsi_trade_ledger"]
    protected_path = PACKAGE_ROOT / source["protected_m15_trade_ledger"]
    actual = {
        "rsi_trade_ledger": sha256(rsi_path),
        "protected_m15_trade_ledger": sha256(protected_path),
    }
    expected = {
        "rsi_trade_ledger": source["rsi_trade_ledger_sha256"],
        "protected_m15_trade_ledger": source[
            "protected_m15_trade_ledger_sha256"
        ],
    }
    if actual != expected:
        raise RuntimeError("frequency-frontier source hash mismatch")

    start = pd.Timestamp(config["period"]["from_inclusive"])
    end = pd.Timestamp(config["period"]["to_exclusive"])
    sleeve = config["rsi_normalization"]["sleeve"]
    fixed_lot = float(config["rsi_normalization"]["fixed_lot"])

    rsi = pd.read_csv(rsi_path, parse_dates=["entry_time", "exit_time"])
    rsi = rsi[
        rsi["sleeve"].eq(sleeve)
        & rsi["entry_time"].ge(start)
        & rsi["entry_time"].lt(end)
        & ~rsi["quarantined"].astype(bool)
    ].copy()
    rsi["pnl_usd"] = (
        rsi["net_pnl_usd"].astype(float)
        * fixed_lot
        / rsi["volume"].astype(float)
    )
    rsi["component"] = "RSI_SHADOW"
    rsi = rsi.sort_values(["entry_time", "exit_time"]).reset_index(drop=True)

    protected = pd.read_csv(protected_path)
    for column in ("entry_time", "exit_time"):
        protected[column] = pd.to_datetime(
            protected[column],
            format="%Y.%m.%d %H:%M:%S",
            utc=True,
        )
    protected = protected[
        protected["entry_time"].ge(start) & protected["entry_time"].lt(end)
    ].copy()
    protected["pnl_usd"] = (
        protected["profit"].astype(float)
        * fixed_lot
        / protected["volume"].astype(float)
    )
    protected["component"] = "M15_REGIME"
    protected["side"] = "SHORT"
    protected = protected[
        ["entry_time", "exit_time", "component", "side", "pnl_usd"]
    ].sort_values(["entry_time", "exit_time"])
    return rsi, protected.reset_index(drop=True), actual


def causal_shadow_gate(
    trades: pd.DataFrame,
    mode: str,
    lookback: int,
    minimum_trailing_profit_factor: float,
) -> pd.DataFrame:
    if mode not in {"GLOBAL", "REGIME"}:
        raise ValueError(f"unsupported gate mode: {mode}")
    ordered = trades.sort_values(["entry_time", "exit_time"]).reset_index(drop=True)
    exits = ordered.sort_values(["exit_time", "entry_time"]).reset_index(drop=True)
    exit_ns = exits["exit_time"].dt.as_unit("ns").astype("int64").to_numpy()
    exit_pnl = exits["pnl_usd"].astype(float).to_numpy()
    exit_regime = exits["causal_regime"].astype(str).to_numpy()
    rows: list[dict[str, Any]] = []
    for row in ordered.itertuples():
        available_count = int(
            np.searchsorted(
                exit_ns,
                pd.Timestamp(row.entry_time).as_unit("ns").value,
                side="right",
            )
        )
        history = exit_pnl[:available_count]
        if mode == "REGIME":
            history = history[exit_regime[:available_count] == str(row.causal_regime)]
        window = history[-lookback:]
        trailing_pf = profit_factor(window)
        admitted = (
            len(window) == lookback
            and trailing_pf >= minimum_trailing_profit_factor
        )
        record = row._asdict()
        record.update(
            {
                "gate_mode": mode,
                "gate_lookback": lookback,
                "gate_minimum_profit_factor": minimum_trailing_profit_factor,
                "available_closed_shadow_trades": len(history),
                "trailing_profit_factor": trailing_pf,
                "admitted": admitted,
            }
        )
        rows.append(record)
    return pd.DataFrame(rows)


def threshold_grid(config: dict[str, Any]) -> list[float]:
    contract = config["frontier"]["minimum_trailing_profit_factors"]
    start = round(float(contract["from"]) * 100)
    stop = round(float(contract["to"]) * 100)
    step = round(float(contract["step"]) * 100)
    return [value / 100.0 for value in range(start, stop + 1, step)]


def evaluate_variant(
    gated: pd.DataFrame,
    config: dict[str, Any],
) -> dict[str, Any]:
    selected = gated[gated["admitted"]].copy()
    selected["component"] = "GATED_RSI"
    period = config["period"]
    split = pd.Timestamp(period["chronological_split"])
    cost = (
        float(config["stress"]["extra_round_trip_pips"])
        * float(config["stress"]["usd_per_pip_at_0_01_lot"])
    )
    full = outcome_metrics(
        selected,
        int(period["full_weekday_denominator"]),
        cost,
    )
    first = outcome_metrics(
        selected[selected["entry_time"].lt(split)],
        int(period["half_weekday_denominator"]),
        cost,
    )
    second = outcome_metrics(
        selected[selected["entry_time"].ge(split)],
        int(period["half_weekday_denominator"]),
        cost,
    )
    rule = config["diagnostic_selection_rule"]
    core_pass = (
        full["profit_factor"] >= float(rule["full_profit_factor_minimum"])
        and full["plus_0_5_pip_profit_factor"]
        >= float(rule["full_plus_0_5_pip_profit_factor_minimum"])
        and first["plus_0_5_pip_profit_factor"]
        > float(rule["both_half_plus_0_5_pip_profit_factor_strictly_above"])
        and second["plus_0_5_pip_profit_factor"]
        > float(rule["both_half_plus_0_5_pip_profit_factor_strictly_above"])
        and full["net_pnl_usd"]
        > float(rule["net_pnl_strictly_above_usd"])
    )
    latest_floor = float(
        config["portfolio_reference"]["latest_12_month_profit_factor_minimum"]
    )
    return {
        "mode": str(gated.iloc[0]["gate_mode"]),
        "lookback": int(gated.iloc[0]["gate_lookback"]),
        "minimum_trailing_profit_factor": float(
            gated.iloc[0]["gate_minimum_profit_factor"]
        ),
        "full": full,
        "first_12_months": first,
        "second_12_months": second,
        "diagnostic_core_pass": bool(core_pass),
        "latest_12_month_pf_pass": bool(
            second["profit_factor"] >= latest_floor
        ),
    }


def combine_portfolio(
    selected_gate: pd.DataFrame,
    protected: pd.DataFrame,
    config: dict[str, Any],
) -> tuple[pd.DataFrame, dict[str, Any]]:
    gated = selected_gate[selected_gate["admitted"]][
        ["entry_time", "exit_time", "side", "pnl_usd"]
    ].copy()
    gated["component"] = "GATED_RSI"
    combined = pd.concat([gated, protected], ignore_index=True).sort_values(
        ["entry_time", "component"]
    )
    period = config["period"]
    split = pd.Timestamp(period["chronological_split"])
    cost = (
        float(config["stress"]["extra_round_trip_pips"])
        * float(config["stress"]["usd_per_pip_at_0_01_lot"])
    )
    full = outcome_metrics(
        combined,
        int(period["full_weekday_denominator"]),
        cost,
    )
    first = outcome_metrics(
        combined[combined["entry_time"].lt(split)],
        int(period["half_weekday_denominator"]),
        cost,
    )
    second = outcome_metrics(
        combined[combined["entry_time"].ge(split)],
        int(period["half_weekday_denominator"]),
        cost,
    )
    same_entry = combined.groupby("entry_time").size()
    reference = config["portfolio_reference"]
    projected_frequency = (
        full["trades_per_weekday"]
        + float(reference["projected_daily_learner_trades_per_weekday"])
    )
    metrics = {
        "full": full,
        "first_12_months": first,
        "second_12_months": second,
        "same_entry_overlap_timestamps": int((same_entry > 1).sum()),
        "maximum_concurrent_positions": _maximum_concurrency(combined),
        "projected_frequency_with_daily_learner_before_overlap_caps": (
            projected_frequency
        ),
        "shortfall_to_desired_1_per_weekday_before_overlap_caps": max(
            0.0,
            float(reference["desired_average_frequency"]) - projected_frequency,
        ),
        "average_frequency_minimum_pass": bool(
            full["trades_per_weekday"]
            >= float(reference["minimum_average_frequency"])
        ),
        "weekday_coverage_pass": bool(
            full["weekday_coverage"]
            >= float(reference["minimum_weekday_coverage"])
        ),
        "latest_12_month_pf_pass": bool(
            second["profit_factor"]
            >= float(reference["latest_12_month_profit_factor_minimum"])
        ),
        "latest_12_month_top_5pct_removed_pf_pass": bool(
            second["top_5pct_removed_profit_factor"] >= 1.0
        ),
    }
    return combined.reset_index(drop=True), metrics


def run() -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    config = load_config()
    rsi, protected, verified = load_sources(config)
    variants: list[dict[str, Any]] = []
    gated_cache: dict[tuple[str, int, float], pd.DataFrame] = {}
    for mode in config["frontier"]["modes"]:
        for lookback in config["frontier"]["lookback_closed_shadow_trades"]:
            for threshold in threshold_grid(config):
                gated = causal_shadow_gate(
                    rsi,
                    str(mode),
                    int(lookback),
                    float(threshold),
                )
                key = (str(mode), int(lookback), float(threshold))
                gated_cache[key] = gated
                variants.append(evaluate_variant(gated, config))

    passing = [item for item in variants if item["diagnostic_core_pass"]]
    if not passing:
        raise RuntimeError("frequency-edge frontier produced no core-pass variant")
    selected = max(
        passing,
        key=lambda item: (
            item["full"]["trades_per_weekday"],
            item["full"]["profit_factor"],
        ),
    )
    selected_key = (
        selected["mode"],
        selected["lookback"],
        selected["minimum_trailing_profit_factor"],
    )
    selected_gate = gated_cache[selected_key]
    combined, combined_metrics = combine_portfolio(
        selected_gate,
        protected,
        config,
    )
    stable = [item for item in passing if item["latest_12_month_pf_pass"]]
    result = {
        "schema_version": "eurusd_frequency_edge_frontier_diagnostic_v1",
        "status": "AVERAGE_FREQUENCY_NEAR_MINIMUM_BUT_NOT_DEMO_READY",
        "research_boundary": (
            "retrospective grid and selection; selected rule is forward-only"
        ),
        "source_sha256_verified": verified,
        "rsi_source_trades_in_period": len(rsi),
        "protected_m15_source_trades_in_period": len(protected),
        "frontier_variants_evaluated": len(variants),
        "diagnostic_core_pass_variants": len(passing),
        "variants_passing_latest_12_month_pf_1_15": len(stable),
        "selected_forward_only_gate": selected,
        "combined_historical_diagnostic": combined_metrics,
        "why_not_demo_ready": [
            "SELECTED_GATE_WAS_MINED_FROM_INSPECTED_HISTORY",
            "WEEKDAY_COVERAGE_BELOW_65_PERCENT",
            "DESIRED_ONE_TRADE_PER_WEEKDAY_NOT_REACHED",
            "SECOND_12_MONTH_TOP_5_PERCENT_REMOVED_PF_BELOW_ONE",
            "PROSPECTIVE_EXECUTION_PARITY_AND_SOAK_NOT_PROVEN",
        ],
        "demo_order_authorized": False,
        "prohibitions": config["prohibitions"],
    }
    frontier_rows: list[dict[str, Any]] = []
    for item in variants:
        frontier_rows.append(
            {
                "mode": item["mode"],
                "lookback": item["lookback"],
                "minimum_trailing_profit_factor": item[
                    "minimum_trailing_profit_factor"
                ],
                "trades": item["full"]["trades"],
                "trades_per_weekday": item["full"]["trades_per_weekday"],
                "weekday_coverage": item["full"]["weekday_coverage"],
                "profit_factor": item["full"]["profit_factor"],
                "plus_0_5_pip_profit_factor": item["full"][
                    "plus_0_5_pip_profit_factor"
                ],
                "first_12_profit_factor": item["first_12_months"][
                    "profit_factor"
                ],
                "second_12_profit_factor": item["second_12_months"][
                    "profit_factor"
                ],
                "second_12_plus_0_5_pip_profit_factor": item[
                    "second_12_months"
                ]["plus_0_5_pip_profit_factor"],
                "diagnostic_core_pass": item["diagnostic_core_pass"],
                "latest_12_month_pf_pass": item[
                    "latest_12_month_pf_pass"
                ],
            }
        )
    return pd.DataFrame(frontier_rows), combined, result


def _json_safe(value: Any) -> Any:
    if isinstance(value, float) and not math.isfinite(value):
        return None
    if isinstance(value, dict):
        return {key: _json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    return value


def write_outputs(
    frontier: pd.DataFrame,
    combined: pd.DataFrame,
    result: dict[str, Any],
    output_dir: Path,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    frontier.to_csv(output_dir / "FRONTIER.csv", index=False)
    combined.to_csv(output_dir / "SELECTED_COMBINED_TRADES.csv", index=False)
    (output_dir / "RESULT.json").write_text(
        json.dumps(_json_safe(result), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    selected = result["selected_forward_only_gate"]
    combined_metrics = result["combined_historical_diagnostic"]
    full = combined_metrics["full"]
    second = combined_metrics["second_12_months"]
    lines = [
        "# EURUSD frequency/edge frontier diagnostic",
        "",
        "Status: **RETROSPECTIVE DIAGNOSTIC -- NO DEMO ADMISSION**",
        "",
        "The highest-frequency rule satisfying the diagnostic full-period and",
        "both-half stressed-edge checks used a global trailing window of",
        (
            f"{selected['lookback']} completed shadow trades and PF >= "
            f"{selected['minimum_trailing_profit_factor']:.2f}. It was selected"
        ),
        "after inspecting history and is therefore forward-only.",
        "",
        "| Metric | Result |",
        "|---|---:|",
        f"| Combined trades | {full['trades']:,} |",
        f"| Combined trades/weekday | {full['trades_per_weekday']:.4f} |",
        f"| Combined weekday coverage | {full['weekday_coverage']:.2%} |",
        f"| Combined PF | {full['profit_factor']:.4f} |",
        (
            "| Combined PF after +0.5 pip | "
            f"{full['plus_0_5_pip_profit_factor']:.4f} |"
        ),
        f"| Combined net at fixed 0.01 lot | ${full['net_pnl_usd']:.2f} |",
        f"| Second-12-month PF | {second['profit_factor']:.4f} |",
        (
            "| Second-12 best-5%-removed PF | "
            f"{second['top_5pct_removed_profit_factor']:.4f} |"
        ),
        (
            "| Projected frequency including daily learner | "
            f"{combined_metrics['projected_frequency_with_daily_learner_before_overlap_caps']:.4f} |"
        ),
        "",
        "The average-frequency floor is reached, but the desired 1.0/day,",
        "65% weekday coverage, recent concentration test, prospective parity,",
        "and soak are not. Demo-order authorization remains false.",
        "",
    ]
    (output_dir / "RESULT.md").write_text(
        "\n".join(lines),
        encoding="utf-8",
    )
