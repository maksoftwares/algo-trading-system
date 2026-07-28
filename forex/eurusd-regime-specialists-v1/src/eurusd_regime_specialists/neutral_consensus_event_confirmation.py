from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from .ensemble import load_ensemble_config
from .neutral_binance_eurusdt_flow import load_parent_points
from .neutral_bls_release_acceleration import (
    execute as execute_event,
    summarize as summarize_event,
)
from .neutral_consensus_surprise_family import (
    build_directional_surprises,
    load_consensus_source,
)
from .research import (
    PACKAGE_ROOT,
    PIP,
    is_quarantined,
    load_inputs,
    serialize,
    sha256_file,
)


FAMILY = "N40_NEUTRAL_CONSENSUS_EVENT_CONFIRMATION"
OUTPUT_ROOT = (
    PACKAGE_ROOT / "outputs" / "neutral_consensus_event_confirmation"
)
CONFIG_PATH = (
    PACKAGE_ROOT
    / "config"
    / "frozen_neutral_consensus_event_confirmation.json"
)
LOCK_PATH = (
    PACKAGE_ROOT
    / "EURUSD_NEUTRAL_CONSENSUS_EVENT_CONFIRMATION_PREREG_2026_07_28.sha256.json"
)


def load_config() -> dict[str, Any]:
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def verify_lock() -> dict[str, str]:
    lock = json.loads(LOCK_PATH.read_text(encoding="utf-8"))
    if lock.get("locked_before_census_and_outcome") is not True:
        raise RuntimeError(
            "Consensus event-confirmation rule is not outcome-locked"
        )
    checked: dict[str, str] = {}
    for relative, expected in lock["files"].items():
        actual = sha256_file(PACKAGE_ROOT / relative)
        if actual != expected:
            raise RuntimeError(
                "Consensus event-confirmation preregistration mismatch: "
                f"{relative}"
            )
        checked[relative] = actual
    cfg = load_config()
    for key in (
        "parent_neutral_date_contract",
        "data_and_classifier_contract",
    ):
        reference = cfg[key]
        if (
            sha256_file(PACKAGE_ROOT / reference["path"])
            != reference["sha256"]
        ):
            raise RuntimeError(f"{key} drift")
    parent = cfg["parent_neutral_date_contract"]
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


def _mid_open(bar: pd.Series) -> float:
    return 0.5 * (
        float(bar["bid_open"]) + float(bar["ask_open"])
    )


def _mid_close(bar: pd.Series) -> float:
    return 0.5 * (
        float(bar["bid_close"]) + float(bar["ask_close"])
    )


def _census_gates(
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
        "confirmed_candidates": int(len(candidates)),
        "candidate_dates": int(candidates["eligible_date"].nunique()),
        "by_window": by_window,
        "by_side": by_side,
        "by_macro_family": by_family,
    }
    gate = cfg["outcome_blind_census"]
    checks = {
        "total": (
            census["confirmed_candidates"]
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


def build_candidates(
    points: pd.DataFrame,
    eurusd: pd.DataFrame,
    consensus: pd.DataFrame,
    cfg: dict[str, Any],
) -> tuple[pd.DataFrame, dict[str, Any]]:
    safe = points[points["clock_minute"].eq(0)].copy()
    safe["window"] = safe["entry_time_utc"].map(
        lambda value: _window_name(value, cfg)
    )
    safe = safe[safe["window"].ne("OUTSIDE_FROZEN_WINDOWS")].copy()
    neutral_dates = set(safe["eligible_date"].astype(str))
    signals, source_census = build_directional_surprises(consensus, cfg)
    observation_bars = int(cfg["strategy"]["observation_bars"])
    observation_minutes = int(cfg["strategy"]["observation_minutes"])
    quarantine = load_ensemble_config()["quarantine"]
    records: list[dict[str, Any]] = []
    reasons = {
        "release_not_on_neutral_date": 0,
        "observation_or_entry_bar_missing": 0,
        "entry_crosses_utc_date": 0,
        "quarantine": 0,
        "zero_price_reaction": 0,
        "macro_price_disagreement": 0,
    }
    neutral_directional_releases = 0
    for _, release in signals.sort_values(
        ["event_time_utc", "family"]
    ).iterrows():
        event_time = pd.Timestamp(release["event_time_utc"])
        eligible_date = event_time.strftime("%Y-%m-%d")
        if eligible_date not in neutral_dates:
            reasons["release_not_on_neutral_date"] += 1
            continue
        neutral_directional_releases += 1
        observation_start = event_time.ceil("5min")
        entry_time = observation_start + pd.Timedelta(
            minutes=observation_minutes
        )
        if entry_time.strftime("%Y-%m-%d") != eligible_date:
            reasons["entry_crosses_utc_date"] += 1
            continue
        expected = pd.date_range(
            observation_start,
            periods=observation_bars,
            freq="5min",
        )
        if (
            any(timestamp not in eurusd.index for timestamp in expected)
            or entry_time not in eurusd.index
        ):
            reasons["observation_or_entry_bar_missing"] += 1
            continue
        if is_quarantined(entry_time, "EURUSD", quarantine):
            reasons["quarantine"] += 1
            continue
        observation = eurusd.loc[expected]
        reaction = (
            _mid_close(observation.iloc[-1])
            - _mid_open(observation.iloc[0])
        )
        if reaction == 0:
            reasons["zero_price_reaction"] += 1
            continue
        price_side = "LONG" if reaction > 0 else "SHORT"
        macro_side = str(release["side"])
        if price_side != macro_side:
            reasons["macro_price_disagreement"] += 1
            continue
        records.append(
            {
                "family": FAMILY,
                "regime": "NEUTRAL",
                "eligible_date": eligible_date,
                "macro_family": release["family"],
                "event_time_utc": event_time,
                "observation_start_utc": observation_start,
                "observation_end_utc": entry_time,
                "entry_time_utc": entry_time,
                "entry_position": int(eurusd.index.get_loc(entry_time)),
                "official_initial_value": release[
                    "official_initial_value"
                ],
                "forecast_value": release["forecast_value"],
                "surprise_value": release["surprise_value"],
                "official_pdf_sha256": release[
                    "official_pdf_sha256"
                ],
                "tradingview_event_id": release[
                    "tradingview_event_id"
                ],
                "tradingview_ticker": release[
                    "tradingview_ticker"
                ],
                "retrieval_semantics": release[
                    "retrieval_semantics"
                ],
                "macro_side": macro_side,
                "price_side": price_side,
                "price_reaction_pips": reaction / PIP,
                "side": macro_side,
                "window": _window_name(entry_time, cfg),
            }
        )
    candidates = pd.DataFrame(records)
    if candidates.empty:
        candidates = pd.DataFrame(
            columns=[
                "eligible_date",
                "macro_family",
                "side",
                "window",
                "entry_time_utc",
            ]
        )
    else:
        candidates = candidates.sort_values(
            ["entry_time_utc", "macro_family"]
        ).reset_index(drop=True)
    gates = _census_gates(candidates, cfg)
    census = {
        **source_census,
        "neutral_dates": int(len(neutral_dates)),
        "neutral_directional_releases": neutral_directional_releases,
        "cash_reasons": reasons,
        **gates,
    }
    return candidates, census


def execute_confirmed(
    candidates: pd.DataFrame,
    eurusd: pd.DataFrame,
    cfg: dict[str, Any],
) -> tuple[pd.DataFrame, dict[str, Any]]:
    prepared = candidates.copy()
    prepared["initial_value"] = prepared["official_initial_value"]
    prepared["previous_initial_value"] = prepared["forecast_value"]
    prepared["acceleration"] = prepared["surprise_value"]
    trades, execution = execute_event(prepared, eurusd, cfg)
    trades = trades.rename(
        columns={
            "initial_value": "official_initial_value",
            "previous_initial_value": "forecast_value",
            "acceleration": "surprise_value",
        }
    )
    metadata = prepared[
        [
            "event_time_utc",
            "macro_family",
            "observation_start_utc",
            "observation_end_utc",
            "official_pdf_sha256",
            "tradingview_event_id",
            "tradingview_ticker",
            "retrieval_semantics",
            "macro_side",
            "price_side",
            "price_reaction_pips",
        ]
    ]
    trades = trades.merge(
        metadata,
        on=["event_time_utc", "macro_family"],
        how="left",
        validate="one_to_one",
    )
    trades["family"] = FAMILY
    return trades, execution


def _load_all() -> tuple[
    dict[str, Any],
    pd.DataFrame,
    pd.DataFrame,
    dict[str, Any],
]:
    cfg = load_config()
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
        raise RuntimeError("Parent Neutral points missing safe columns")
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
        raise RuntimeError("Outcome column leaked into Neutral date source")
    return (
        cfg,
        eurusd,
        consensus,
        {
            **manifests,
            "TRADINGVIEW_CONSENSUS": consensus_manifest,
            "NEUTRAL_DATE_SOURCE": {
                "rows": int(len(points)),
                "paired_source_path": cfg[
                    "parent_neutral_date_contract"
                ]["paired_source_path"],
                "paired_source_sha256": cfg[
                    "parent_neutral_date_contract"
                ]["paired_source_sha256"],
            },
            "_points": points,
        },
    )


def run_census() -> tuple[dict[str, Any], pd.DataFrame]:
    cfg, eurusd, consensus, manifests = _load_all()
    points = manifests.pop("_points")
    candidates, census = build_candidates(
        points, eurusd, consensus, cfg
    )
    return (
        serialize(
            {
                "schema_version": (
                    "eurusd_neutral_consensus_event_confirmation_census_v1"
                ),
                "family": FAMILY,
                "status": (
                    "CENSUS_PASS_BACKTEST_ALLOWED"
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
    candidates, census = build_candidates(
        points, eurusd, consensus, cfg
    )
    if not census["passed"]:
        raise RuntimeError("Outcome-blind census failed; P&L is forbidden")
    trades, execution = execute_confirmed(candidates, eurusd, cfg)
    summary, matches = summarize_event(trades, cfg)
    status = (
        "QUALIFIED_NEUTRAL_RESEARCH_CANDIDATE_FORWARD_REQUIRED"
        if summary["passed"]
        else "REJECTED_NEUTRAL_CONSENSUS_EVENT_CONFIRMATION_V1"
    )
    result = {
        "schema_version": (
            "eurusd_neutral_consensus_event_confirmation_result_v1"
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
        "mechanism": (
            "On a Neutral-owned UTC date, trade a reconciled CPI, PPI, "
            "or NFP surprise only after three completed M5 bars confirm "
            "the same EURUSD direction."
        ),
        "census": census,
        "execution": execution,
        "summary": summary,
        "data_manifests": manifests,
        "decision_policy": cfg["decision_policy"],
    }
    return (
        serialize(result),
        {
            "CANDIDATES": candidates,
            "TRADES": trades,
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
    "OUTPUT_ROOT",
    "build_candidates",
    "execute_confirmed",
    "load_config",
    "run_backtest",
    "run_census",
    "verify_lock",
    "write_json",
]
