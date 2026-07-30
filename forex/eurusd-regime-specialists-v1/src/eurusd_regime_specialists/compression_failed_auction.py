from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

import pandas as pd

from . import compression_own_price_family as compression
from . import dense_residual_family as dense
from . import frozen_residual_history_diagnostic as base

ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = (
    ROOT / "config" / "preregistered_compression_failed_auction_v1.json"
)
PIP = 0.0001


def load_config(path: Path = CONFIG_PATH) -> dict[str, Any]:
    config = json.loads(path.read_text(encoding="utf-8"))
    if (
        config["status"]
        != "PREREGISTERED_REGIME_SPECIALIST_CHRONOLOGICAL_RESEARCH_ONLY"
    ):
        raise RuntimeError("unexpected failed-auction research boundary")
    if config["owned_regime"] != "CROSSPAIR_COMPRESSION":
        raise RuntimeError("failed-auction regime drift")
    if config["result_can_count_as_forward_evidence"] is not False:
        raise RuntimeError("failed-auction research permits forward credit")
    if config["demo_order_authorized"] is not False:
        raise RuntimeError("failed-auction research permits demo orders")
    return config


def _source_path(value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else (ROOT / path).resolve()


def verify_sources(config: dict[str, Any]) -> dict[str, str]:
    source = config["source"]
    pairs = {
        name: (
            _source_path(str(source[path_key])),
            str(source[hash_key]),
        )
        for name, path_key, hash_key in (
            (
                "frozen_residual_history_config",
                "frozen_residual_history_config",
                "frozen_residual_history_config_sha256",
            ),
            (
                "frozen_residual_history_source",
                "frozen_residual_history_source",
                "frozen_residual_history_source_sha256",
            ),
            (
                "eurusd_m5_bidask",
                "eurusd_m5_bidask",
                "eurusd_m5_bidask_sha256",
            ),
            (
                "threshold_provenance",
                "threshold_provenance",
                "threshold_provenance_sha256",
            ),
        )
    }
    actual = {name: base.sha256(path) for name, (path, _) in pairs.items()}
    expected = {name: expected for name, (_, expected) in pairs.items()}
    if actual != expected:
        raise RuntimeError(
            f"failed-auction source mismatch: {actual} != {expected}"
        )
    return actual


def load_eurusd_bars(config: dict[str, Any]) -> pd.DataFrame:
    frame = pd.read_parquet(
        _source_path(config["source"]["eurusd_m5_bidask"]),
        columns=[
            "timestamp_ms",
            "bid_open",
            "bid_high",
            "bid_low",
            "bid_close",
            "ask_open",
            "ask_high",
            "ask_low",
            "ask_close",
        ],
    )
    frame["time"] = pd.to_datetime(frame["timestamp_ms"], unit="ms", utc=True)
    return frame.set_index("time").sort_index()


def signal_at_decision(
    bars: pd.DataFrame,
    decision_time: pd.Timestamp,
    config: dict[str, Any],
) -> dict[str, Any] | None:
    signal = config["signal"]
    bars_required = int(signal["observation_bars_m5"])
    start_time = decision_time - pd.Timedelta(
        minutes=int(signal["observation_window_minutes"])
    )
    end_time = decision_time - pd.Timedelta(minutes=5)
    start_position = int(bars.index.searchsorted(start_time))
    end_position = int(bars.index.searchsorted(end_time))
    if (
        start_position >= len(bars)
        or end_position >= len(bars)
        or bars.index[start_position] != start_time
        or bars.index[end_position] != end_time
        or end_position - start_position + 1 != bars_required
    ):
        return None
    observed = bars.iloc[start_position : end_position + 1]
    mid_open = (
        float(observed.iloc[0]["bid_open"])
        + float(observed.iloc[0]["ask_open"])
    ) / 2.0
    mid_high = float(
        (
            observed["bid_high"].astype(float)
            + observed["ask_high"].astype(float)
        )
        .div(2.0)
        .max()
    )
    mid_low = float(
        (
            observed["bid_low"].astype(float)
            + observed["ask_low"].astype(float)
        )
        .div(2.0)
        .min()
    )
    mid_close = (
        float(observed.iloc[-1]["bid_close"])
        + float(observed.iloc[-1]["ask_close"])
    ) / 2.0
    observation_range = mid_high - mid_low
    if not math.isfinite(observation_range) or observation_range <= 0.0:
        return None
    upward = mid_high - mid_open
    downward = mid_open - mid_low
    upper_wick = mid_high - max(mid_open, mid_close)
    lower_wick = min(mid_open, mid_close) - mid_low
    upper_fraction = max(0.0, upper_wick / observation_range)
    lower_fraction = max(0.0, lower_wick / observation_range)
    range_pips = observation_range / PIP
    minimum_excursion = float(signal["minimum_failed_excursion_pips"]) * PIP
    maximum_range = float(signal["maximum_observation_range_pips"])
    minimum_wick = float(signal["minimum_rejection_wick_fraction"])
    long_signal = bool(
        range_pips <= maximum_range
        and downward >= minimum_excursion
        and downward > upward
        and mid_close >= mid_open
        and lower_fraction >= minimum_wick
    )
    short_signal = bool(
        range_pips <= maximum_range
        and upward >= minimum_excursion
        and upward > downward
        and mid_close <= mid_open
        and upper_fraction >= minimum_wick
    )
    side = "LONG" if long_signal else "SHORT" if short_signal else "CASH"
    return {
        "side": side,
        "observation_open": mid_open,
        "observation_high": mid_high,
        "observation_low": mid_low,
        "observation_close": mid_close,
        "observation_range_pips": range_pips,
        "upward_excursion_pips": upward / PIP,
        "downward_excursion_pips": downward / PIP,
        "upper_wick_fraction": upper_fraction,
        "lower_wick_fraction": lower_fraction,
    }


def signal_records(
    records: list[dict[str, Any]],
    bars: pd.DataFrame,
    config: dict[str, Any],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for record in records:
        if (
            record["status"] != "RESOLVED"
            or record.get("regime") != config["owned_regime"]
        ):
            continue
        decision_time = pd.to_datetime(
            record["decision_time_utc"],
            format=dense.TIME_FORMAT,
            utc=True,
        )
        signal = signal_at_decision(bars, decision_time, config)
        if signal is None or signal["side"] == "CASH":
            continue
        rows.append({**record, "failed_auction_signal": signal})
    return rows


def _in_window(
    records: list[dict[str, Any]],
    start: str,
    end: str,
) -> list[dict[str, Any]]:
    return [
        record
        for record in records
        if start <= str(record["decision_date"]) < end
    ]


def capacity(
    candidates: list[dict[str, Any]],
    config: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, bool]]:
    windows = config["windows"]
    dev_start, dev_end = windows["development"]
    val_start, val_end = windows["locked_validation"]
    development = _in_window(candidates, dev_start, dev_end)
    validation = _in_window(candidates, val_start, val_end)
    long_count = sum(
        record["failed_auction_signal"]["side"] == "LONG"
        for record in candidates
    )
    short_count = sum(
        record["failed_auction_signal"]["side"] == "SHORT"
        for record in candidates
    )
    result = {
        "total": len(candidates),
        "development": len(development),
        "locked_validation": len(validation),
        "long": long_count,
        "short": short_count,
    }
    gate = config["outcome_blind_capacity_gates"]
    checks = {
        "minimum_candidates_total": result["total"]
        >= int(gate["minimum_candidates_total"]),
        "minimum_candidates_development": result["development"]
        >= int(gate["minimum_candidates_development"]),
        "minimum_candidates_locked_validation": result["locked_validation"]
        >= int(gate["minimum_candidates_locked_validation"]),
        "minimum_candidates_each_side": min(long_count, short_count)
        >= int(gate["minimum_candidates_each_side"]),
    }
    return result, checks


def trade_frame(
    candidates: list[dict[str, Any]],
    config: dict[str, Any],
) -> pd.DataFrame:
    execution = config["execution_inherited_unchanged"]
    risk_usd = float(execution["initial_risk_usd"])
    stress_usd = float(execution["additional_round_trip_stress_usd"])
    rows: list[dict[str, Any]] = []
    for record in candidates:
        side = str(record["failed_auction_signal"]["side"])
        outcome = record[f"{side.lower()}_outcome"]
        result_r = float(outcome["result_r"])
        rows.append(
            {
                "entry_time": pd.to_datetime(
                    record["decision_time_utc"],
                    format=dense.TIME_FORMAT,
                    utc=True,
                ),
                "exit_time": pd.to_datetime(
                    outcome["exit_time"],
                    format=dense.TIME_FORMAT,
                    utc=True,
                ),
                "decision_date": str(record["decision_date"]),
                "component": "COMPRESSION_FAILED_AUCTION_RESEARCH",
                "regime": config["owned_regime"],
                "side": side,
                "outcome": outcome["outcome"],
                "result_r": result_r,
                "pnl_usd": result_r * risk_usd,
                "stressed_pnl_usd": result_r * risk_usd - stress_usd,
            }
        )
    if rows:
        return pd.DataFrame(rows)
    empty = pd.DataFrame(
        columns=[
            "entry_time",
            "exit_time",
            "decision_date",
            "component",
            "regime",
            "side",
            "outcome",
            "result_r",
            "pnl_usd",
            "stressed_pnl_usd",
        ]
    )
    empty["entry_time"] = pd.Series([], dtype="datetime64[ns, UTC]")
    empty["exit_time"] = pd.Series([], dtype="datetime64[ns, UTC]")
    return empty


def _metric_checks(
    metrics: dict[str, Any],
    gate: dict[str, Any],
    *,
    development: bool,
    latest: dict[str, Any] | None = None,
) -> dict[str, bool]:
    if development:
        return {
            "minimum_profit_factor": metrics["profit_factor"]
            >= float(gate["minimum_profit_factor"]),
            "minimum_stressed_profit_factor": metrics[
                "stressed_profit_factor"
            ]
            >= float(gate["minimum_stressed_profit_factor"]),
            "minimum_best_removed_profit_factor": metrics[
                "best_5pct_removed_profit_factor"
            ]
            >= float(
                gate["minimum_best_five_percent_removed_profit_factor"]
            ),
            "minimum_each_half_profit_factor": all(
                float(value)
                >= float(
                    gate[
                        "minimum_each_trade_sequence_half_profit_factor"
                    ]
                )
                for value in metrics["trade_sequence_half_profit_factors"]
            ),
            "minimum_net_r": metrics["net"]
            > float(gate["minimum_net_r_exclusive"]),
        }
    payoff = metrics["payoff_ratio"]
    assert latest is not None
    return {
        "minimum_trades": metrics["trades"] >= int(gate["minimum_trades"]),
        "minimum_win_rate": metrics["win_rate"]
        >= float(gate["minimum_win_rate"]),
        "maximum_win_rate": metrics["win_rate"]
        <= float(gate["maximum_win_rate"]),
        "minimum_payoff_ratio": payoff is not None
        and payoff >= float(gate["minimum_payoff_ratio"]),
        "minimum_profit_factor": metrics["profit_factor"]
        >= float(gate["minimum_profit_factor"]),
        "minimum_stressed_profit_factor": metrics["stressed_profit_factor"]
        >= float(gate["minimum_stressed_profit_factor"]),
        "minimum_best_removed_profit_factor": metrics[
            "best_5pct_removed_profit_factor"
        ]
        >= float(gate["minimum_best_five_percent_removed_profit_factor"]),
        "minimum_each_half_profit_factor": all(
            float(value)
            > float(
                gate[
                    "minimum_each_trade_sequence_half_profit_factor_exclusive"
                ]
            )
            for value in metrics["trade_sequence_half_profit_factors"]
        ),
        "minimum_latest_12_month_trades": latest["trades"]
        >= int(gate["minimum_latest_12_month_trades"]),
        "minimum_latest_12_month_profit_factor": latest["profit_factor"]
        >= float(gate["minimum_latest_12_month_profit_factor"]),
        "minimum_net_r": metrics["net"]
        > float(gate["minimum_net_r_exclusive"]),
    }


def _window_trades(
    trades: pd.DataFrame,
    start: str,
    end: str,
) -> pd.DataFrame:
    return trades[
        trades["decision_date"].ge(start)
        & trades["decision_date"].lt(end)
    ]


def evaluate(
    all_records: list[dict[str, Any]],
    candidates: list[dict[str, Any]],
    m15: pd.DataFrame,
    config: dict[str, Any],
) -> tuple[dict[str, Any], pd.DataFrame, pd.DataFrame]:
    capacity_result, capacity_checks = capacity(candidates, config)
    windows = config["windows"]
    dev_start, dev_end = windows["development"]
    val_start, val_end = windows["locked_validation"]
    latest_start, latest_end = windows["latest_12_months"]
    portfolio_start, portfolio_end = windows["combined_broker_window"]
    split = str(windows["combined_broker_split"])
    all_candidate_trades = trade_frame(candidates, config)
    capacity_passed = all(capacity_checks.values())
    development_trades = (
        _window_trades(all_candidate_trades, dev_start, dev_end)
        if capacity_passed
        else trade_frame([], config)
    )
    development_metrics = compression.specialist_metrics(
        development_trades,
        len(dense._records_in_window(all_records, dev_start, dev_end)),
        config,
    )
    development_checks = (
        _metric_checks(
            development_metrics,
            config["development_edge_gates"],
            development=True,
        )
        if capacity_passed
        else {}
    )
    development_passed = capacity_passed and all(
        development_checks.values()
    )
    validation_trades = (
        _window_trades(all_candidate_trades, val_start, val_end)
        if development_passed
        else trade_frame([], config)
    )
    latest_trades = _window_trades(
        validation_trades,
        latest_start,
        latest_end,
    )
    validation_metrics = compression.specialist_metrics(
        validation_trades,
        len(dense._records_in_window(all_records, val_start, val_end)),
        config,
    )
    latest_metrics = compression.specialist_metrics(
        latest_trades,
        len(dense._records_in_window(all_records, latest_start, latest_end)),
        config,
    )
    validation_checks = (
        _metric_checks(
            validation_metrics,
            config["locked_validation_gates"],
            development=False,
            latest=latest_metrics,
        )
        if development_passed
        else {}
    )
    portfolio_trades = (
        validation_trades if development_passed else trade_frame([], config)
    )
    combined, combined_metrics = compression.combined_portfolio(
        portfolio_trades,
        m15,
        portfolio_start,
        portfolio_end,
        len(
            dense._records_in_window(
                all_records,
                portfolio_start,
                portfolio_end,
            )
        ),
    )
    _, first = compression.combined_portfolio(
        portfolio_trades,
        m15,
        portfolio_start,
        split,
        len(dense._records_in_window(all_records, portfolio_start, split)),
    )
    _, second = compression.combined_portfolio(
        portfolio_trades,
        m15,
        split,
        portfolio_end,
        len(dense._records_in_window(all_records, split, portfolio_end)),
    )
    monthly = (
        combined.assign(month=combined["entry_time"].dt.strftime("%Y-%m"))
        .groupby("month")
        .agg(
            trades=("pnl_usd", "size"),
            pnl_usd=("pnl_usd", "sum"),
            stressed_pnl_usd=("stressed_pnl_usd", "sum"),
        )
        .reset_index()
    )
    validation_passed = development_passed and all(
        validation_checks.values()
    )
    status = (
        "CENSUS_CAPACITY_REJECTED"
        if not capacity_passed
        else "DEVELOPMENT_EDGE_REJECTED"
        if not development_passed
        else "HISTORICAL_VALIDATION_REJECTED"
        if not validation_passed
        else "HISTORICAL_VALIDATION_SUPPORTS_FORWARD_SPECIALIST_REBUILD"
    )
    result = {
        "schema_version": config["schema_version"],
        "status": status,
        "research_boundary": config["status"],
        "owned_regime": config["owned_regime"],
        "variants_evaluated": 1,
        "outcome_blind_capacity": {
            "metrics": capacity_result,
            "checks": capacity_checks,
            "passed": capacity_passed,
        },
        "development": {
            "metrics": development_metrics,
            "checks": development_checks,
            "passed": development_passed,
        },
        "locked_validation": {
            "metrics": validation_metrics,
            "latest_12_months": latest_metrics,
            "checks": validation_checks,
            "passed": validation_passed,
        },
        "combined_broker_window": {
            "full": combined_metrics,
            "first_12_months": first,
            "second_12_months": second,
        },
        "result_can_count_as_forward_evidence": False,
        "demo_order_authorized": False,
        "prohibitions": config["prohibitions"],
    }
    return result, validation_trades.reset_index(drop=True), monthly


def run() -> tuple[
    dict[str, Any],
    list[dict[str, Any]],
    pd.DataFrame,
    pd.DataFrame,
]:
    config = load_config()
    verified = verify_sources(config)
    records, _, _, _ = base.run()
    bars = load_eurusd_bars(config)
    candidates = signal_records(records, bars, config)
    base_config = base.load_config()
    m15, _ = base.load_m15_trades(base_config)
    result, trades, monthly = evaluate(
        records,
        candidates,
        m15,
        config,
    )
    result["verified_source_sha256"] = verified
    result["failed_auction_config_sha256"] = base.sha256(CONFIG_PATH)
    result["failed_auction_source_sha256"] = base.sha256(Path(__file__))
    return result, candidates, trades, monthly


def _safe(value: Any) -> Any:
    if hasattr(value, "item") and not isinstance(value, (str, bytes)):
        return _safe(value.item())
    if isinstance(value, float) and not math.isfinite(value):
        return None
    if isinstance(value, dict):
        return {key: _safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_safe(item) for item in value]
    return value


def _candidate_frame(candidates: list[dict[str, Any]]) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "decision_date": record["decision_date"],
                "decision_time_utc": record["decision_time_utc"],
                **record["failed_auction_signal"],
            }
            for record in candidates
        ]
    )


def render_report(result: dict[str, Any]) -> str:
    capacity_result = result["outcome_blind_capacity"]["metrics"]
    development = result["development"]["metrics"]
    validation = result["locked_validation"]["metrics"]
    latest = result["locked_validation"]["latest_12_months"]
    return "\n".join(
        [
            "# Compression failed-auction specialist",
            "",
            f"Status: **{result['status']}**",
            "",
            "The symmetric signal and thresholds were fixed before this run.",
            "Locked validation was opened only if capacity and development",
            "edge gates passed. No result can authorize an order.",
            "",
            "## Outcome-blind capacity",
            "",
            f"- Total candidates: `{capacity_result['total']}`",
            f"- Development candidates: `{capacity_result['development']}`",
            (
                "- Locked-validation candidates: "
                f"`{capacity_result['locked_validation']}`"
            ),
            (
                f"- Long / short: `{capacity_result['long']}` / "
                f"`{capacity_result['short']}`"
            ),
            "",
            "## Development",
            "",
            f"- Trades: `{development['trades']}`",
            f"- PF: `{development['profit_factor']:.4f}`",
            f"- Stressed PF: `{development['stressed_profit_factor']:.4f}`",
            f"- Net R: `{development['net']:.4f}`",
            "",
            "## Locked validation",
            "",
            f"- Trades: `{validation['trades']}`",
            f"- PF: `{validation['profit_factor']:.4f}`",
            f"- Stressed PF: `{validation['stressed_profit_factor']:.4f}`",
            f"- Latest-12-month trades: `{latest['trades']}`",
            f"- Latest-12-month PF: `{latest['profit_factor']:.4f}`",
            "",
            "Forward-evidence credit: `false`.",
            "",
            "Demo-order authorization: `false`.",
            "",
        ]
    )


def write_outputs(
    result: dict[str, Any],
    candidates: list[dict[str, Any]],
    trades: pd.DataFrame,
    monthly: pd.DataFrame,
    output_dir: Path,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "RESULT.json").write_text(
        json.dumps(_safe(result), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (output_dir / "RESULT.md").write_text(
        render_report(result),
        encoding="utf-8",
    )
    _candidate_frame(candidates).to_csv(
        output_dir / "CANDIDATES.csv",
        index=False,
    )
    trades.to_csv(output_dir / "VALIDATION_TRADES.csv", index=False)
    monthly.to_csv(output_dir / "MONTHLY.csv", index=False)


__all__ = [
    "capacity",
    "evaluate",
    "load_config",
    "load_eurusd_bars",
    "run",
    "signal_at_decision",
    "signal_records",
    "trade_frame",
    "verify_sources",
    "write_outputs",
]
