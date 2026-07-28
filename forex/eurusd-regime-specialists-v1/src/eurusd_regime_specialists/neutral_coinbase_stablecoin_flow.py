from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from .ensemble import load_ensemble_config, load_inputs
from .neutral_binance_eurusdt_flow import (
    evaluate_oracle,
    load_parent_points,
)
from .neutral_four_clock_ranker import route_predictions
from .neutral_midnight_pairs import aggregate_days, write_json
from .neutral_selective_multivenue_agreement import (
    admission,
    summarize_selective,
)
from .research import PACKAGE_ROOT, sha256_file


FAMILY = "N27_NEUTRAL_COINBASE_STABLECOIN_FLOW"
OUTPUT_ROOT = (
    PACKAGE_ROOT / "outputs" / "neutral_coinbase_stablecoin_flow"
)
PRODUCTS = ("USDC-EUR", "USDT-EUR")


def load_config() -> dict[str, Any]:
    return json.loads(
        (
            PACKAGE_ROOT
            / "config"
            / "frozen_neutral_coinbase_stablecoin_flow.json"
        ).read_text(encoding="utf-8")
    )


def verify_lock() -> dict[str, str]:
    lock = json.loads(
        (
            PACKAGE_ROOT
            / "EURUSD_NEUTRAL_COINBASE_STABLECOIN_FLOW_PREREG_2026_07_28.sha256.json"
        ).read_text(encoding="utf-8")
    )
    if (
        lock.get(
            "locked_before_coinbase_stablecoin_flow_outcome_pass"
        )
        is not True
    ):
        raise RuntimeError(
            "Neutral Coinbase stablecoin flow is not locked"
        )
    checked: dict[str, str] = {}
    for relative, expected in lock["files"].items():
        actual = sha256_file(PACKAGE_ROOT / relative)
        if actual != expected:
            raise RuntimeError(
                "Neutral Coinbase stablecoin lock mismatch: "
                f"{relative}"
            )
        checked[relative] = actual
    cfg = load_config()
    parent = cfg["parent_four_clock_contract"]
    if sha256_file(PACKAGE_ROOT / parent["path"]) != parent["sha256"]:
        raise RuntimeError("Parent four-clock contract drift")
    source = cfg["coinbase_source"]
    if sha256_file(Path(source["path"])) != source["sha256"]:
        raise RuntimeError("Coinbase normalized source drift")
    if (
        sha256_file(Path(source["manifest_path"]))
        != source["manifest_sha256"]
    ):
        raise RuntimeError("Coinbase source manifest drift")
    manifest = json.loads(
        Path(source["manifest_path"]).read_text(encoding="utf-8")
    )
    if (
        manifest["raw_response_chain_sha256"]
        != source["raw_response_chain_sha256"]
    ):
        raise RuntimeError("Coinbase raw response chain drift")
    if (
        manifest["product_metadata_chain_sha256"]
        != source["product_metadata_chain_sha256"]
    ):
        raise RuntimeError("Coinbase product metadata chain drift")
    if cfg["outcome_blind_census"] is None:
        raise RuntimeError("Coinbase outcome-blind census is not frozen")
    return checked


def load_coinbase_source(cfg: dict[str, Any]) -> pd.DataFrame:
    frame = pd.read_parquet(Path(cfg["coinbase_source"]["path"]))
    for column in ("open_time_utc", "close_time_utc"):
        frame[column] = pd.to_datetime(frame[column], utc=True)
    return frame.sort_values(
        ["product", "open_time_utc"]
    ).reset_index(drop=True)


def build_product_signals(
    source: pd.DataFrame,
    cfg: dict[str, Any],
) -> pd.DataFrame:
    bars = int(cfg["flow_rule"]["completed_m5_bars_per_product"])
    if bars != 3:
        raise RuntimeError("Frozen Coinbase flow requires three bars")
    outputs: list[pd.DataFrame] = []
    for product, frame in source.groupby("product", sort=True):
        if product not in PRODUCTS:
            continue
        product_frame = frame.sort_values("open_time_utc").copy()
        consecutive = product_frame["open_time_utc"].diff().eq(
            pd.Timedelta(minutes=5)
        )
        fully_consecutive = consecutive.copy()
        for lag in range(1, bars - 1):
            fully_consecutive &= consecutive.shift(lag).fillna(False)
        volume = product_frame["base_volume"].rolling(
            bars, min_periods=bars
        ).sum()
        signed_volume = (
            np.sign(
                product_frame["close"] - product_frame["open"]
            )
            * product_frame["base_volume"]
        ).rolling(bars, min_periods=bars).sum()
        first_open = product_frame["open"].shift(bars - 1)
        valid = fully_consecutive & volume.gt(0)
        signal = pd.DataFrame(
            {
                "entry_time_utc": (
                    product_frame["open_time_utc"]
                    + pd.Timedelta(minutes=5)
                ),
                "product": product,
                "flow_valid": valid,
                "base_volume_15m": volume,
                "euro_signed_volume_pressure_15m": np.where(
                    valid, -signed_volume / volume, np.nan
                ),
                "euro_return_15m": np.where(
                    valid,
                    first_open / product_frame["close"] - 1.0,
                    np.nan,
                ),
            }
        )
        outputs.append(signal)
    signals = pd.concat(outputs, ignore_index=True)
    if set(signals["product"].unique()) != set(PRODUCTS):
        raise RuntimeError("Coinbase source is missing a frozen product")
    return signals


def _window_name(
    timestamp: pd.Timestamp,
    cfg: dict[str, Any],
) -> str:
    for name, (start_raw, end_raw) in cfg["windows"].items():
        if pd.Timestamp(start_raw) <= timestamp <= pd.Timestamp(end_raw):
            return name
    return "OUTSIDE"


def _distribution(
    selected: pd.DataFrame,
    source_dates: pd.Index,
) -> dict[str, int]:
    counts = selected.groupby("eligible_date").size().reindex(
        source_dates, fill_value=0
    )
    return {
        str(value): int((counts == value).sum())
        for value in range(5)
    }


def _census_block(
    parent: pd.DataFrame,
    valid: pd.DataFrame,
    selected: pd.DataFrame,
) -> dict[str, Any]:
    source_dates = pd.Index(
        sorted(parent["eligible_date"].astype(str).unique())
    )
    source_days = int(len(source_dates))
    valid_days = int(valid["eligible_date"].nunique())
    active_days = int(selected["eligible_date"].nunique())
    candidates = int(len(selected))
    return {
        "source_eligible_days": source_days,
        "source_decision_points": int(len(parent)),
        "both_products_valid_points": int(len(valid)),
        "both_products_valid_days": valid_days,
        "agreement_candidates": candidates,
        "active_candidate_days": active_days,
        "no_trade_days": source_days - active_days,
        "predicted_long_rate": (
            float(selected["flow_side"].eq("LONG").mean())
            if candidates
            else 0.0
        ),
        "trades_per_source_eligible_day": (
            candidates / source_days if source_days else 0.0
        ),
        "trades_per_active_candidate_day": (
            candidates / active_days if active_days else 0.0
        ),
        "candidate_count_distribution": _distribution(
            selected, source_dates
        ),
    }


def build_decisions(
    parent: pd.DataFrame,
    signals: pd.DataFrame,
    cfg: dict[str, Any],
    *,
    enforce_frozen_census: bool,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    filtered_parent = parent.copy()
    filtered_parent["window"] = filtered_parent["entry_time_utc"].map(
        lambda value: _window_name(value, cfg)
    )
    filtered_parent = filtered_parent[
        filtered_parent["window"].ne("OUTSIDE")
    ].copy()
    joined = filtered_parent
    pressure_columns: list[str] = []
    return_columns: list[str] = []
    valid_columns: list[str] = []
    for product in PRODUCTS:
        prefix = product.lower().replace("-", "_")
        product_signals = signals[signals["product"].eq(product)][
            [
                "entry_time_utc",
                "flow_valid",
                "base_volume_15m",
                "euro_signed_volume_pressure_15m",
                "euro_return_15m",
            ]
        ].rename(
            columns={
                "flow_valid": f"{prefix}_flow_valid",
                "base_volume_15m": f"{prefix}_base_volume_15m",
                "euro_signed_volume_pressure_15m": (
                    f"{prefix}_euro_pressure_15m"
                ),
                "euro_return_15m": f"{prefix}_euro_return_15m",
            }
        )
        joined = joined.merge(
            product_signals,
            on="entry_time_utc",
            how="left",
            validate="one_to_one",
        )
        valid_columns.append(f"{prefix}_flow_valid")
        pressure_columns.append(f"{prefix}_euro_pressure_15m")
        return_columns.append(f"{prefix}_euro_return_15m")
    for column in valid_columns:
        joined[column] = joined[column].fillna(False).astype(bool)
    both_valid_mask = joined[valid_columns].all(axis=1)
    valid = joined[both_valid_mask].copy()
    agreement = valid[pressure_columns[0]].ge(0).eq(
        valid[pressure_columns[1]].ge(0)
    )
    selected = valid[agreement].copy()
    selected["flow_side"] = np.where(
        selected[pressure_columns[0]].ge(0), "LONG", "SHORT"
    )
    selected["product_pressure_sign_agreement"] = True
    selected = selected.sort_values("entry_time_utc").reset_index(
        drop=True
    )

    overall = _census_block(filtered_parent, valid, selected)
    by_window: dict[str, Any] = {}
    for name in cfg["windows"]:
        parent_window = filtered_parent[
            filtered_parent["window"].eq(name)
        ]
        valid_window = valid[valid["window"].eq(name)]
        selected_window = selected[selected["window"].eq(name)]
        by_window[name] = _census_block(
            parent_window, valid_window, selected_window
        )
    census = {
        **overall,
        "missing_or_invalid_product_points": int(
            len(filtered_parent) - len(valid)
        ),
        "valid_product_sign_disagreements": int(
            len(valid) - len(selected)
        ),
        "by_window": by_window,
        "outcome_blind_source_relationship": {
            "pressure_correlation": float(
                valid[pressure_columns].corr().iloc[0, 1]
            ),
            "return_correlation": float(
                valid[return_columns].corr().iloc[0, 1]
            ),
            "pressure_sign_agreement": float(agreement.mean()),
            "usdc_pressure_return_sign_consistency": float(
                valid[pressure_columns[0]].ge(0).eq(
                    valid[return_columns[0]].ge(0)
                ).mean()
            ),
            "usdt_pressure_return_sign_consistency": float(
                valid[pressure_columns[1]].ge(0).eq(
                    valid[return_columns[1]].ge(0)
                ).mean()
            ),
        },
    }
    if (
        enforce_frozen_census
        and census != cfg["outcome_blind_census"]
    ):
        raise RuntimeError(
            "Coinbase outcome-blind census drift: "
            f"actual={census!r} "
            f"frozen={cfg['outcome_blind_census']!r}"
        )
    return selected, census


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
    predictions["family"] = FAMILY
    columns = [
        "flow_side",
        "product_pressure_sign_agreement",
        "usdc_eur_euro_pressure_15m",
        "usdt_eur_euro_pressure_15m",
        "usdc_eur_euro_return_15m",
        "usdt_eur_euro_return_15m",
        "usdc_eur_base_volume_15m",
        "usdt_eur_base_volume_15m",
    ]
    for column in columns:
        trades[column] = decisions[column].to_numpy()
        predictions[column] = decisions[column].to_numpy()
    return trades, predictions


def run_census() -> dict[str, Any]:
    cfg = load_config()
    parent = load_parent_points(include_outcomes=False)
    signals = build_product_signals(
        load_coinbase_source(cfg), cfg
    )
    _, census = build_decisions(
        parent,
        signals,
        cfg,
        enforce_frozen_census=False,
    )
    return census


def run_neutral_coinbase_stablecoin_flow() -> tuple[
    dict[str, Any],
    dict[str, pd.DataFrame],
]:
    verify_lock()
    cfg = load_config()
    parent = load_parent_points(include_outcomes=True)
    signals = build_product_signals(
        load_coinbase_source(cfg), cfg
    )
    decisions, census = build_decisions(
        parent,
        signals,
        cfg,
        enforce_frozen_census=True,
    )
    trades, predictions = execute(decisions, cfg)
    base = load_ensemble_config()
    m5, _, manifests = load_inputs(base)
    strategy = summarize_selective(
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
            else "REJECTED_NEUTRAL_COINBASE_STABLECOIN_FLOW_V1"
        ),
        "information_status": cfg["information_status"],
        "source_manifests": manifests,
        "coinbase_source": cfg["coinbase_source"],
        "causality": {
            "direction": (
                "agreed sign of prior-three-candle volume-weighted "
                "direction on Coinbase USDC-EUR and USDT-EUR, inverted "
                "into EURUSD terms"
            ),
            "candle_direction_volume_is_true_taker_flow": False,
            "magnitude_threshold_product_weight_or_model": False,
            "clock_or_subgroup_selection": False,
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
            "The frozen Coinbase stablecoin-flow rule passed every "
            "historical gate; only post-lock rows may confirm it."
            if admitted
            else "The frozen Coinbase stablecoin-flow rule failed one "
            "or more gates and is closed without repair."
        ),
    }
    return result, {
        "PRODUCT_SIGNALS": signals,
        "DECISIONS": decisions,
        "PREDICTIONS": predictions,
        "TRADES": trades,
        "DAILY_PORTFOLIO": aggregate_days(trades),
        "ORACLE_MATCHES": matches,
    }


__all__ = [
    "FAMILY",
    "OUTPUT_ROOT",
    "PRODUCTS",
    "build_decisions",
    "build_product_signals",
    "execute",
    "load_coinbase_source",
    "load_config",
    "run_census",
    "run_neutral_coinbase_stablecoin_flow",
    "verify_lock",
    "write_json",
]
