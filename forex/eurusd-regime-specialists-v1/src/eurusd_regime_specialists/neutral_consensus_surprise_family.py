from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from .ensemble import load_ensemble_config
from .neutral_binance_eurusdt_flow import load_parent_points
from .neutral_bls_first_hour_carry import (
    aggregate_days,
    execute as execute_carry,
    summarize as summarize_carry,
)
from .research import PACKAGE_ROOT, load_inputs, serialize, sha256_file


FAMILY = "N39_NEUTRAL_CONSENSUS_SURPRISE_FAMILY"
CARRY_VARIANT = "MACRO_SURPRISE_CARRY"
AGREEMENT_VARIANT = "MACRO_SURPRISE_PRICE_AGREEMENT"
VARIANTS = (CARRY_VARIANT, AGREEMENT_VARIANT)
OUTPUT_ROOT = PACKAGE_ROOT / "outputs" / "neutral_consensus_surprise_family"
CONFIG_PATH = (
    PACKAGE_ROOT
    / "config"
    / "frozen_neutral_consensus_surprise_family.json"
)
LOCK_PATH = (
    PACKAGE_ROOT
    / "EURUSD_NEUTRAL_CONSENSUS_SURPRISE_FAMILY_PREREG_2026_07_28.sha256.json"
)


def load_config() -> dict[str, Any]:
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def verify_lock() -> dict[str, str]:
    lock = json.loads(LOCK_PATH.read_text(encoding="utf-8"))
    if lock.get("locked_before_census_and_outcome") is not True:
        raise RuntimeError("Consensus-surprise family is not outcome-locked")
    checked: dict[str, str] = {}
    for relative, expected in lock["files"].items():
        actual = sha256_file(PACKAGE_ROOT / relative)
        if actual != expected:
            raise RuntimeError(
                f"Consensus-surprise preregistration mismatch: {relative}"
            )
        checked[relative] = actual
    cfg = load_config()
    for key in (
        "parent_neutral_clock_contract",
        "data_and_classifier_contract",
    ):
        reference = cfg[key]
        if (
            sha256_file(PACKAGE_ROOT / reference["path"])
            != reference["sha256"]
        ):
            raise RuntimeError(f"{key} drift")
    parent = cfg["parent_neutral_clock_contract"]
    if (
        sha256_file(PACKAGE_ROOT / parent["paired_source_path"])
        != parent["paired_source_sha256"]
    ):
        raise RuntimeError("Parent outcome-blind paired source drift")
    source = cfg["consensus_source"]
    if sha256_file(Path(source["path"])) != source["sha256"]:
        raise RuntimeError("Consensus normalized source drift")
    if (
        sha256_file(Path(source["manifest_path"]))
        != source["manifest_sha256"]
    ):
        raise RuntimeError("Consensus manifest drift")
    manifest = json.loads(
        Path(source["manifest_path"]).read_text(encoding="utf-8")
    )
    if (
        manifest["raw_response_chain_sha256"]
        != source["raw_response_chain_sha256"]
    ):
        raise RuntimeError("Consensus raw-response chain drift")
    if manifest.get("accepted_for_adaptive_historical_research") is not True:
        raise RuntimeError("Consensus source is not accepted for research")
    if manifest.get("accepted_for_pristine_oos_claim") is not False:
        raise RuntimeError("Consensus information boundary drift")
    oracle = cfg["oracle_source"]
    if sha256_file(PACKAGE_ROOT / oracle["path"]) != oracle["sha256"]:
        raise RuntimeError("Oracle evaluation source drift")
    return checked


def _window_name(timestamp: pd.Timestamp, cfg: dict[str, Any]) -> str:
    for name, (start, end) in cfg["windows"].items():
        if pd.Timestamp(start) <= timestamp <= pd.Timestamp(end):
            return name
    return "OUTSIDE_FROZEN_WINDOWS"


def load_consensus_source(
    cfg: dict[str, Any],
) -> tuple[pd.DataFrame, dict[str, Any]]:
    source = cfg["consensus_source"]
    frame = pd.read_parquet(Path(source["path"]))
    required = {
        "family",
        "event_time_utc",
        "official_initial_value",
        "official_pdf_sha256",
        "forecast_value",
        "tradingview_event_id",
        "tradingview_ticker",
        "retrieval_semantics",
    }
    missing = required - set(frame.columns)
    if missing:
        raise RuntimeError(f"Consensus source missing columns: {missing}")
    frame["event_time_utc"] = pd.to_datetime(
        frame["event_time_utc"], utc=True
    ).dt.as_unit("ns")
    frame = frame[
        frame["family"].isin(cfg["strategy"]["families"])
    ].sort_values(["event_time_utc", "family"]).reset_index(drop=True)
    if frame.duplicated(["family", "event_time_utc"]).any():
        raise RuntimeError("Consensus source has duplicate release keys")
    if frame["forecast_value"].isna().any():
        raise RuntimeError("Consensus source contains missing forecasts")
    manifest = json.loads(
        Path(source["manifest_path"]).read_text(encoding="utf-8")
    )
    return frame, {
        "rows": int(len(frame)),
        "path": source["path"],
        "sha256": source["sha256"],
        "manifest_path": source["manifest_path"],
        "manifest_sha256": source["manifest_sha256"],
        "raw_response_files": int(manifest["raw_response_files"]),
        "raw_response_chain_sha256": source[
            "raw_response_chain_sha256"
        ],
        "information_status": (
            "POST_HOC_HISTORICAL_FORECAST_FIELD_NOT_PRISTINE_OOS"
        ),
    }


def build_directional_surprises(
    consensus: pd.DataFrame,
    cfg: dict[str, Any],
) -> tuple[pd.DataFrame, dict[str, Any]]:
    frame = consensus[
        consensus["family"].isin(cfg["strategy"]["families"])
    ].copy()
    frame["surprise_value"] = (
        frame["official_initial_value"] - frame["forecast_value"]
    )
    usable = (
        frame["official_initial_value"].notna()
        & frame["forecast_value"].notna()
        & frame["surprise_value"].notna()
    )
    directional = usable & frame["surprise_value"].ne(0)
    selected = frame[directional].copy()
    selected["side"] = "LONG"
    selected.loc[selected["surprise_value"].gt(0), "side"] = "SHORT"
    by_family = {
        family: {
            "source_rows": int(frame["family"].eq(family).sum()),
            "directional_rows": int(
                selected["family"].eq(family).sum()
            ),
        }
        for family in cfg["strategy"]["families"]
    }
    return selected.sort_values("event_time_utc").reset_index(drop=True), {
        "source_rows": int(len(frame)),
        "missing_actual_or_forecast": int((~usable).sum()),
        "zero_surprise": int((usable & ~directional).sum()),
        "directional_release_surprises": int(len(selected)),
        "by_source_family": by_family,
    }


def add_price_confirmation(
    points: pd.DataFrame,
    eurusd: pd.DataFrame,
) -> pd.DataFrame:
    if not isinstance(eurusd.index, pd.DatetimeIndex):
        raise RuntimeError("EURUSD source must use a DatetimeIndex")
    if not eurusd.index.is_unique:
        raise RuntimeError("EURUSD source index must be unique")
    if "bid_close" not in eurusd.columns:
        raise RuntimeError("EURUSD source missing bid_close")
    frame = points.copy()
    entries = pd.to_datetime(frame["entry_time_utc"], utc=True).dt.as_unit(
        "ns"
    )
    positions = eurusd.index.get_indexer(entries)
    prior_returns: list[float | None] = []
    price_sides: list[str] = []
    for position in positions:
        if position < 4:
            prior_returns.append(None)
            price_sides.append("CASH")
            continue
        prior_return = float(
            eurusd.iloc[position - 1]["bid_close"]
            - eurusd.iloc[position - 4]["bid_close"]
        )
        prior_returns.append(prior_return)
        if prior_return > 0:
            price_sides.append("LONG")
        elif prior_return < 0:
            price_sides.append("SHORT")
        else:
            price_sides.append("CASH")
    frame["prior_15m_return"] = prior_returns
    frame["price_side"] = price_sides
    frame["price_confirmation_available"] = (
        frame["prior_15m_return"].notna()
        & frame["price_side"].ne("CASH")
    )
    return frame


def _variant_census(
    candidates: pd.DataFrame,
    cfg: dict[str, Any],
) -> dict[str, Any]:
    by_window = {
        name: int(candidates["window"].eq(name).sum())
        for name in cfg["windows"]
    }
    by_side = {
        side: int(candidates["side"].eq(side).sum())
        for side in ("LONG", "SHORT")
    }
    by_family = {
        family: int(candidates["macro_family"].eq(family).sum())
        for family in cfg["strategy"]["families"]
    }
    census = {
        "candidates": int(len(candidates)),
        "candidate_days": int(candidates["eligible_date"].nunique()),
        "by_window": by_window,
        "by_side": by_side,
        "by_macro_family": by_family,
        "by_clock_minute": {
            str(minute): int(
                candidates["clock_minute"].eq(minute).sum()
            )
            for minute in cfg["strategy"]["entry_minutes_utc"]
        },
    }
    gate = cfg["outcome_blind_census"]
    checks = {
        "total": (
            census["candidates"]
            >= int(gate["minimum_candidates_total"])
        ),
        "development": (
            by_window["development_2019_2022"]
            >= int(gate["minimum_candidates_development"])
        ),
        "full_forward_years": all(
            by_window[name]
            >= int(gate["minimum_candidates_each_full_forward_year"])
            for name in (
                "chronological_2023",
                "chronological_2024",
                "chronological_2025",
            )
        ),
        "recent_half_year": (
            by_window["recent_2026_h1"]
            >= int(gate["minimum_candidates_recent_half_year"])
        ),
        "both_sides": all(
            by_side[side] >= int(gate["minimum_candidates_each_side"])
            for side in ("LONG", "SHORT")
        ),
        "families": (
            sum(value > 0 for value in by_family.values())
            >= int(gate["minimum_families_represented"])
        ),
    }
    census["gate_results"] = checks
    census["passed"] = bool(all(checks.values()))
    return census


def attach_latest_surprise(
    points: pd.DataFrame,
    consensus: pd.DataFrame,
    eurusd: pd.DataFrame,
    cfg: dict[str, Any],
) -> tuple[pd.DataFrame, dict[str, Any]]:
    signals, source_census = build_directional_surprises(consensus, cfg)
    macro = signals[
        [
            "family",
            "event_time_utc",
            "official_initial_value",
            "official_pdf_sha256",
            "forecast_value",
            "surprise_value",
            "side",
            "tradingview_event_id",
            "tradingview_ticker",
            "retrieval_semantics",
        ]
    ].rename(
        columns={
            "family": "macro_family",
            "event_time_utc": "macro_signal_time_utc",
            "side": "macro_side",
        }
    )
    left = add_price_confirmation(
        points.sort_values("entry_time_utc"), eurusd
    )
    right = macro.sort_values("macro_signal_time_utc").copy()
    for column in ("entry_time_utc", "macro_signal_time_utc"):
        target = left if column == "entry_time_utc" else right
        target[column] = pd.to_datetime(
            target[column], utc=True
        ).dt.as_unit("ns")
    joined = pd.merge_asof(
        left,
        right,
        left_on="entry_time_utc",
        right_on="macro_signal_time_utc",
        direction="backward",
        allow_exact_matches=False,
    )
    joined["macro_age_hours"] = (
        joined["entry_time_utc"] - joined["macro_signal_time_utc"]
    ).dt.total_seconds() / 3600.0
    strategy = cfg["strategy"]
    recent = (
        joined["macro_signal_time_utc"].notna()
        & joined["macro_age_hours"].gt(
            float(strategy["minimum_release_age_hours_exclusive"])
        )
        & joined["macro_age_hours"].le(
            float(strategy["maximum_release_age_hours"])
        )
    )
    base = joined[recent].copy()
    base["family"] = FAMILY
    base["regime"] = "NEUTRAL"
    base["side"] = base["macro_side"]
    base["window"] = base["entry_time_utc"].map(
        lambda value: _window_name(value, cfg)
    )
    base["parent_decision_id"] = base["decision_id"]

    carry = base.copy()
    carry["variant"] = CARRY_VARIANT
    agreement = base[
        base["price_confirmation_available"]
        & base["price_side"].eq(base["macro_side"])
    ].copy()
    agreement["variant"] = AGREEMENT_VARIANT
    candidates = pd.concat([carry, agreement], ignore_index=True)
    candidates["decision_id"] = (
        candidates["variant"]
        + "::"
        + candidates["parent_decision_id"].astype(str)
    )
    candidates = candidates.sort_values(
        ["variant", "entry_time_utc", "decision_id"]
    ).reset_index(drop=True)
    variant_census = {
        variant: _variant_census(
            candidates[candidates["variant"].eq(variant)], cfg
        )
        for variant in VARIANTS
    }
    passed_variants = [
        variant
        for variant, census in variant_census.items()
        if census["passed"]
    ]
    census = {
        **source_census,
        "neutral_clock_points": int(len(points)),
        "recent_macro_clock_points": int(len(base)),
        "cash_no_release_within_72h": int((~recent).sum()),
        "price_confirmation_available": int(
            base["price_confirmation_available"].sum()
        ),
        "price_macro_agreements": int(len(agreement)),
        "variants": variant_census,
        "passed_variants": passed_variants,
        "passed": bool(passed_variants),
    }
    return candidates, census


def execute_variant(
    candidates: pd.DataFrame,
    eurusd: pd.DataFrame,
    cfg: dict[str, Any],
) -> pd.DataFrame:
    if candidates.empty:
        return pd.DataFrame()
    variants = candidates["variant"].unique().tolist()
    if len(variants) != 1 or variants[0] not in VARIANTS:
        raise RuntimeError("execute_variant requires exactly one variant")
    prepared = candidates.copy()
    prepared["initial_value"] = prepared["official_initial_value"]
    prepared["previous_initial_value"] = prepared["forecast_value"]
    prepared["acceleration"] = prepared["surprise_value"]
    trades = execute_carry(prepared, eurusd, cfg).rename(
        columns={
            "initial_value": "official_initial_value",
            "previous_initial_value": "forecast_value",
            "acceleration": "surprise_value",
        }
    )
    metadata = prepared[
        [
            "decision_id",
            "parent_decision_id",
            "variant",
            "official_pdf_sha256",
            "tradingview_event_id",
            "tradingview_ticker",
            "retrieval_semantics",
            "prior_15m_return",
            "price_side",
        ]
    ]
    trades = trades.merge(
        metadata, on="decision_id", how="left", validate="one_to_one"
    )
    trades["family"] = FAMILY
    return trades


def _load_all() -> tuple[
    dict[str, Any],
    pd.DataFrame,
    pd.DataFrame,
    dict[str, Any],
]:
    cfg = load_config()
    if tuple(cfg["strategy"]["variants"]) != VARIANTS:
        raise RuntimeError("Frozen finite-family variants drift")
    eurusd, _, manifests = load_inputs(load_ensemble_config())
    consensus, consensus_manifest = load_consensus_source(cfg)
    points = load_parent_points(include_outcomes=False)
    safe_columns = {
        "eligible_date",
        "clock_minute",
        "decision_id",
        "entry_time_utc",
    }
    if not safe_columns.issubset(points.columns):
        raise RuntimeError("Parent clock points missing safe columns")
    prohibited = {
        "outcome_r",
        "target_first",
        "oracle_member",
        "exit_time_utc",
        "entry_price",
        "target_price",
        "stop_price",
    }
    if any(
        any(token in column for token in prohibited)
        for column in points.columns
    ):
        raise RuntimeError("Outcome column leaked into census clock source")
    return (
        cfg,
        eurusd,
        consensus,
        {
            **manifests,
            "TRADINGVIEW_CONSENSUS": consensus_manifest,
            "NEUTRAL_CLOCK_POINTS": {
                "rows": int(len(points)),
                "paired_source_path": cfg[
                    "parent_neutral_clock_contract"
                ]["paired_source_path"],
                "paired_source_sha256": cfg[
                    "parent_neutral_clock_contract"
                ]["paired_source_sha256"],
            },
            "_points": points,
        },
    )


def run_census() -> tuple[dict[str, Any], pd.DataFrame]:
    cfg, eurusd, consensus, manifests = _load_all()
    points = manifests.pop("_points")
    candidates, census = attach_latest_surprise(
        points, consensus, eurusd, cfg
    )
    return (
        serialize(
            {
                "schema_version": (
                    "eurusd_neutral_consensus_surprise_family_census_v1"
                ),
                "family": FAMILY,
                "status": (
                    "CENSUS_PASS_FOR_ONE_OR_MORE_VARIANTS"
                    if census["passed"]
                    else "CENSUS_FAIL_NO_PNL_ALLOWED"
                ),
                "census": census,
                "data_manifests": manifests,
            }
        ),
        candidates,
    )


def run_backtest() -> tuple[
    dict[str, Any],
    dict[str, pd.DataFrame],
]:
    cfg, eurusd, consensus, manifests = _load_all()
    points = manifests.pop("_points")
    candidates, census = attach_latest_surprise(
        points, consensus, eurusd, cfg
    )
    passing = list(census["passed_variants"])
    if not passing:
        raise RuntimeError(
            "All outcome-blind variant censuses failed; P&L is forbidden"
        )
    trade_frames: list[pd.DataFrame] = []
    daily_frames: list[pd.DataFrame] = []
    match_frames: list[pd.DataFrame] = []
    summaries: dict[str, Any] = {}
    for variant in passing:
        variant_candidates = candidates[
            candidates["variant"].eq(variant)
        ].copy()
        trades = execute_variant(variant_candidates, eurusd, cfg)
        summary, matches = summarize_carry(trades, cfg)
        summaries[variant] = summary
        trade_frames.append(trades)
        daily = aggregate_days(trades)
        daily["variant"] = variant
        daily_frames.append(daily)
        matches["variant"] = variant
        match_frames.append(matches)
    trades = pd.concat(trade_frames, ignore_index=True)
    daily = pd.concat(daily_frames, ignore_index=True)
    matches = pd.concat(match_frames, ignore_index=True)
    qualified = [
        variant
        for variant, summary in summaries.items()
        if summary["passed"]
    ]
    status = (
        "QUALIFIED_NEUTRAL_RESEARCH_CANDIDATE_FORWARD_REQUIRED"
        if qualified
        else "REJECTED_NEUTRAL_CONSENSUS_SURPRISE_FAMILY_V1"
    )
    result = {
        "schema_version": (
            "eurusd_neutral_consensus_surprise_family_result_v1"
        ),
        "family": FAMILY,
        "status": status,
        "demo_ready": False,
        "live_ready": False,
        "information_status": cfg["information_status"],
        "research_boundary": (
            "The historical forecast field was retrieved post-event. "
            "All archived windows are adaptive development evidence; "
            "future forecasts require pre-release capture and checksums."
        ),
        "finite_family_policy": (
            "Each predeclared variant is evaluated and judged independently. "
            "No historical best-of selection or post-outcome combination."
        ),
        "census": census,
        "summaries": summaries,
        "qualified_variants": qualified,
        "data_manifests": manifests,
        "decision_policy": cfg["decision_policy"],
    }
    return (
        serialize(result),
        {
            "CANDIDATES": candidates[
                candidates["variant"].isin(passing)
            ].copy(),
            "TRADES": trades,
            "DAILY_PORTFOLIO": daily,
            "ORACLE_MATCHES_15M": matches,
        },
    )


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(serialize(payload), indent=2) + "\n",
        encoding="utf-8",
    )


__all__ = [
    "AGREEMENT_VARIANT",
    "CARRY_VARIANT",
    "OUTPUT_ROOT",
    "VARIANTS",
    "add_price_confirmation",
    "attach_latest_surprise",
    "build_directional_surprises",
    "execute_variant",
    "load_config",
    "run_backtest",
    "run_census",
    "verify_lock",
    "write_json",
]
