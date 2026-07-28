from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from .ensemble import load_ensemble_config, load_inputs
from .neutral_binance_eurusdt_flow import (
    admission,
    build_flow_signals,
    evaluate_oracle,
    load_config as load_binance_config,
    load_flow as load_binance_flow,
    load_parent_points,
    summarize,
)
from .neutral_four_clock_ranker import route_predictions
from .neutral_midnight_pairs import write_json
from .research import PACKAGE_ROOT, sha256_file


FAMILY = "N24_NEUTRAL_KRAKEN_BINANCE_MULTIVENUE_FLOW"
OUTPUT_ROOT = PACKAGE_ROOT / "outputs" / "neutral_kraken_multivenue_flow"


def load_config() -> dict[str, Any]:
    return json.loads(
        (
            PACKAGE_ROOT
            / "config"
            / "frozen_neutral_kraken_multivenue_flow.json"
        ).read_text(encoding="utf-8")
    )


def verify_lock() -> dict[str, str]:
    lock = json.loads(
        (
            PACKAGE_ROOT
            / "EURUSD_NEUTRAL_KRAKEN_MULTIVENUE_FLOW_PREREG_2026_07_28.sha256.json"
        ).read_text(encoding="utf-8")
    )
    if (
        lock.get("locked_before_kraken_multivenue_outcome_pass")
        is not True
    ):
        raise RuntimeError("Neutral Kraken multivenue flow is not locked")
    checked: dict[str, str] = {}
    for relative, expected in lock["files"].items():
        actual = sha256_file(PACKAGE_ROOT / relative)
        if actual != expected:
            raise RuntimeError(
                "Neutral Kraken multivenue preregistration mismatch: "
                f"{relative}"
            )
        checked[relative] = actual
    cfg = load_config()
    for source_key in (
        "parent_four_clock_contract",
        "parent_binance_flow_contract",
        "paired_trade_source",
        "kraken_executed_flow_source",
        "binance_executed_flow_source",
    ):
        source = cfg[source_key]
        source_path = Path(source["path"])
        if not source_path.is_absolute():
            source_path = PACKAGE_ROOT / source_path
        if sha256_file(source_path) != source["sha256"]:
            raise RuntimeError(f"Kraken multivenue {source_key} drift")
    kraken = cfg["kraken_executed_flow_source"]
    if (
        sha256_file(Path(kraken["manifest_path"]))
        != kraken["manifest_sha256"]
    ):
        raise RuntimeError("Kraken source manifest drift")
    manifest = json.loads(
        Path(kraken["manifest_path"]).read_text(encoding="utf-8")
    )
    if (
        manifest["raw_page_chain_sha256"]
        != kraken["raw_page_chain_sha256"]
    ):
        raise RuntimeError("Kraken raw-page chain drift")
    return checked


def load_kraken_flow(cfg: dict[str, Any]) -> pd.DataFrame:
    frame = pd.read_parquet(
        Path(cfg["kraken_executed_flow_source"]["path"])
    )
    for column in ("open_time_utc", "close_time_utc"):
        frame[column] = pd.to_datetime(frame[column], utc=True)
    return frame


def _signals(
    cfg: dict[str, Any],
) -> tuple[pd.DataFrame, pd.DataFrame]:
    signal_cfg = load_binance_config()
    kraken = load_kraken_flow(cfg).rename(
        columns={
            "reported_buy_quote_volume": (
                "taker_buy_quote_volume"
            )
        }
    )
    kraken_signals = build_flow_signals(
        kraken, signal_cfg
    ).rename(
        columns={
            "flow_feature_valid": "kraken_flow_valid",
            "flow_quote_volume_15m": "kraken_quote_volume_15m",
            "flow_taker_buy_quote_volume_15m": (
                "kraken_reported_buy_quote_volume_15m"
            ),
            "flow_trade_count_15m": "kraken_trade_count_15m",
            "flow_return_15m": "kraken_return_15m",
            "flow_taker_imbalance_15m": (
                "kraken_reported_side_imbalance_15m"
            ),
        }
    )
    binance_signals = build_flow_signals(
        load_binance_flow(signal_cfg), signal_cfg
    ).rename(
        columns={
            "flow_feature_valid": "binance_flow_valid",
            "flow_quote_volume_15m": "binance_quote_volume_15m",
            "flow_taker_buy_quote_volume_15m": (
                "binance_taker_buy_quote_volume_15m"
            ),
            "flow_trade_count_15m": "binance_trade_count_15m",
            "flow_return_15m": "binance_return_15m",
            "flow_taker_imbalance_15m": "binance_taker_imbalance_15m",
        }
    )
    kraken_columns = [
        "entry_time_utc",
        "kraken_flow_valid",
        "kraken_quote_volume_15m",
        "kraken_reported_buy_quote_volume_15m",
        "kraken_trade_count_15m",
        "kraken_return_15m",
        "kraken_reported_side_imbalance_15m",
    ]
    binance_columns = [
        "entry_time_utc",
        "binance_flow_valid",
        "binance_quote_volume_15m",
        "binance_taker_buy_quote_volume_15m",
        "binance_trade_count_15m",
        "binance_return_15m",
        "binance_taker_imbalance_15m",
    ]
    return (
        kraken_signals[kraken_columns],
        binance_signals[binance_columns],
    )


def _window_name(
    timestamp: pd.Timestamp,
    cfg: dict[str, Any],
) -> str:
    for name, (start_raw, end_raw) in cfg["windows"].items():
        if pd.Timestamp(start_raw) <= timestamp <= pd.Timestamp(end_raw):
            return name
    return "OUTSIDE"


def build_decisions(
    parent: pd.DataFrame,
    kraken_signals: pd.DataFrame,
    binance_signals: pd.DataFrame,
    cfg: dict[str, Any],
    *,
    enforce_frozen_census: bool,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    merged = parent.merge(
        kraken_signals,
        on="entry_time_utc",
        how="left",
        validate="one_to_one",
    ).merge(
        binance_signals,
        on="entry_time_utc",
        how="left",
        validate="one_to_one",
    )
    merged["kraken_flow_valid"] = merged[
        "kraken_flow_valid"
    ].fillna(False)
    merged["binance_flow_valid"] = merged[
        "binance_flow_valid"
    ].fillna(False)
    merged["both_venues_valid"] = (
        merged["kraken_flow_valid"]
        & merged["binance_flow_valid"]
    )
    valid = merged[merged["both_venues_valid"]].copy()
    expected = int(cfg["strategy"]["required_trades_per_eligible_day"])
    daily = valid.groupby("eligible_date").size()
    complete_dates = set(daily[daily == expected].index)
    decisions = valid[
        valid["eligible_date"].isin(complete_dates)
    ].copy()
    decisions["multivenue_flow_score"] = 0.5 * (
        decisions["kraken_reported_side_imbalance_15m"]
        + decisions["binance_taker_imbalance_15m"]
    )
    threshold = float(cfg["flow_rule"]["long_threshold"])
    decisions["flow_side"] = np.where(
        decisions["multivenue_flow_score"].ge(threshold),
        "LONG",
        "SHORT",
    )
    decisions["window"] = decisions["entry_time_utc"].map(
        lambda value: _window_name(value, cfg)
    )
    decisions = (
        decisions[decisions["window"].ne("OUTSIDE")]
        .sort_values("entry_time_utc")
        .reset_index(drop=True)
    )
    by_window: dict[str, Any] = {}
    for name in cfg["windows"]:
        subset = decisions[decisions["window"].eq(name)]
        by_window[name] = {
            "eligible_days": int(subset["eligible_date"].nunique()),
            "decision_points": int(len(subset)),
            "forced_trade_candidates": int(len(subset)),
        }
    counts = decisions.groupby("eligible_date").size()
    eligible_days = int(decisions["eligible_date"].nunique())
    exact_days = int((counts == expected).sum())
    census = {
        "parent_paired_decision_points": int(len(parent)),
        "kraken_flow_valid_points": int(
            merged["kraken_flow_valid"].sum()
        ),
        "binance_flow_valid_points": int(
            merged["binance_flow_valid"].sum()
        ),
        "both_venues_valid_points": int(
            merged["both_venues_valid"].sum()
        ),
        "complete_days_before_window_filter": int(
            len(complete_dates)
        ),
        "eligible_complete_days": eligible_days,
        "paired_decision_points": int(len(decisions)),
        "forced_trade_candidates": int(len(decisions)),
        "days_exactly_four_candidates": exact_days,
        "eligible_day_exact_four_coverage": (
            exact_days / eligible_days if eligible_days else 0.0
        ),
        "by_window": by_window,
        "outcome_blind_source_relationship": {
            "imbalance_correlation": float(
                decisions[
                    [
                        "kraken_reported_side_imbalance_15m",
                        "binance_taker_imbalance_15m",
                    ]
                ].corr().iloc[0, 1]
            ),
            "return_correlation": float(
                decisions[
                    ["kraken_return_15m", "binance_return_15m"]
                ].corr().iloc[0, 1]
            ),
            "sign_agreement": float(
                (
                    decisions[
                        "kraken_reported_side_imbalance_15m"
                    ].ge(0)
                    == decisions[
                        "binance_taker_imbalance_15m"
                    ].ge(0)
                ).mean()
            ),
            "multivenue_predicted_long_rate": float(
                decisions["flow_side"].eq("LONG").mean()
            ),
            "exact_score_ties": int(
                decisions["multivenue_flow_score"].eq(0).sum()
            ),
        },
    }
    if enforce_frozen_census and census != cfg["outcome_blind_census"]:
        raise RuntimeError(
            "Kraken multivenue census drift: "
            f"actual={census!r} frozen={cfg['outcome_blind_census']!r}"
        )
    return decisions, census


def execute(
    decisions: pd.DataFrame,
    cfg: dict[str, Any],
) -> tuple[pd.DataFrame, pd.DataFrame]:
    probabilities = np.where(
        decisions["flow_side"].eq("LONG"), 1.0, 0.0
    )
    trades, predictions = route_predictions(
        decisions, probabilities, cfg
    )
    trades["family"] = FAMILY
    feature_columns = [
        "kraken_reported_side_imbalance_15m",
        "binance_taker_imbalance_15m",
        "multivenue_flow_score",
        "kraken_return_15m",
        "binance_return_15m",
    ]
    for column in feature_columns:
        trades[column] = decisions[column].to_numpy()
        predictions[column] = decisions[column].to_numpy()
    return trades, predictions


def run_census() -> dict[str, Any]:
    cfg = load_config()
    parent = load_parent_points(include_outcomes=False)
    kraken_signals, binance_signals = _signals(cfg)
    _, census = build_decisions(
        parent,
        kraken_signals,
        binance_signals,
        cfg,
        enforce_frozen_census=False,
    )
    return census


def run_neutral_kraken_multivenue_flow() -> tuple[
    dict[str, Any],
    dict[str, pd.DataFrame],
]:
    verify_lock()
    cfg = load_config()
    parent = load_parent_points(include_outcomes=True)
    kraken_signals, binance_signals = _signals(cfg)
    decisions, census = build_decisions(
        parent,
        kraken_signals,
        binance_signals,
        cfg,
        enforce_frozen_census=True,
    )
    base = load_ensemble_config()
    m5, _, manifests = load_inputs(base)
    trades, predictions = execute(decisions, cfg)
    strategy = summarize(
        trades, predictions, m5, cfg, census
    )
    oracle, matches = evaluate_oracle(trades, cfg)
    admitted, checks = admission(strategy, oracle, cfg)
    prospective_start = pd.Timestamp(cfg["prospective"]["start_utc"])
    prospective_points = decisions[
        decisions["entry_time_utc"] >= prospective_start
    ]
    result = {
        "campaign_id": cfg["campaign_id"],
        "status": (
            "CAUSAL_RESEARCH_PASS_REQUIRES_PROSPECTIVE_CONFIRMATION"
            if admitted
            else "REJECTED_NEUTRAL_KRAKEN_MULTIVENUE_FLOW_V1"
        ),
        "information_status": cfg["information_status"],
        "source_manifests": manifests,
        "kraken_executed_flow_source": (
            cfg["kraken_executed_flow_source"]
        ),
        "binance_executed_flow_source": (
            cfg["binance_executed_flow_source"]
        ),
        "causality": {
            "direction": (
                "sign of equal-weight prior-15-minute normalized "
                "executed-flow imbalance from Kraken EUR/USD and "
                "Binance EURUSDT"
            ),
            "venue_weights_fit": False,
            "threshold_or_agreement_search": False,
            "future_information_in_signal": False,
            "oracle_usage": "evaluation only after trade ledger",
        },
        "outcome_blind_census": census,
        "strategy": {
            "admitted": admitted,
            "admission_checks": checks,
            **strategy,
        },
        "oracle_resemblance": oracle,
        "prospective": {
            "start_utc": cfg["prospective"]["start_utc"],
            "historical_rows_before_start_are_research_only": True,
            "available_points_after_start": int(
                len(prospective_points)
            ),
            "status": (
                "WAITING_FOR_POST_LOCK_MARKET_DATA"
                if prospective_points.empty
                else "POST_LOCK_POINTS_AVAILABLE"
            ),
        },
        "verdict": (
            "The fixed multivenue flow rule passed all historical gates; "
            "only post-lock rows may confirm it."
            if admitted
            else "The fixed multivenue flow rule failed one or more "
            "frozen gates and is closed without repair."
        ),
    }
    return result, {
        "TRADES": trades,
        "PREDICTIONS": predictions,
        "ORACLE_MATCHES": matches,
    }


__all__ = [
    "FAMILY",
    "OUTPUT_ROOT",
    "build_decisions",
    "execute",
    "load_config",
    "load_kraken_flow",
    "run_census",
    "run_neutral_kraken_multivenue_flow",
    "verify_lock",
    "write_json",
]
