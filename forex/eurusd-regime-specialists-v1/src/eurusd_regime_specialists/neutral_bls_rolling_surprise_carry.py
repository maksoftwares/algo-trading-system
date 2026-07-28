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
from .neutral_bls_release_acceleration import load_release_source
from .research import PACKAGE_ROOT, load_inputs, serialize, sha256_file


FAMILY = "N38_NEUTRAL_BLS_ROLLING_SURPRISE_CARRY"
OUTPUT_ROOT = PACKAGE_ROOT / "outputs" / "neutral_bls_rolling_surprise_carry"
CONFIG_PATH = (
    PACKAGE_ROOT
    / "config"
    / "frozen_neutral_bls_rolling_surprise_carry.json"
)
LOCK_PATH = (
    PACKAGE_ROOT
    / "EURUSD_NEUTRAL_BLS_ROLLING_SURPRISE_CARRY_PREREG_2026_07_28.sha256.json"
)


def load_config() -> dict[str, Any]:
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def verify_lock() -> dict[str, str]:
    lock = json.loads(LOCK_PATH.read_text(encoding="utf-8"))
    if lock.get("locked_before_census_and_outcome") is not True:
        raise RuntimeError("BLS rolling-surprise contract is not outcome-locked")
    checked: dict[str, str] = {}
    for relative, expected in lock["files"].items():
        actual = sha256_file(PACKAGE_ROOT / relative)
        if actual != expected:
            raise RuntimeError(
                f"BLS rolling-surprise preregistration mismatch: {relative}"
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
    source = cfg["initial_release_source"]
    if sha256_file(Path(source["path"])) != source["sha256"]:
        raise RuntimeError("BLS normalized source drift")
    if (
        sha256_file(Path(source["manifest_path"]))
        != source["manifest_sha256"]
    ):
        raise RuntimeError("BLS manifest drift")
    manifest = json.loads(
        Path(source["manifest_path"]).read_text(encoding="utf-8")
    )
    if manifest["raw_pdf_chain_sha256"] != source["raw_pdf_chain_sha256"]:
        raise RuntimeError("BLS raw PDF chain drift")
    oracle = cfg["oracle_source"]
    if sha256_file(PACKAGE_ROOT / oracle["path"]) != oracle["sha256"]:
        raise RuntimeError("Oracle evaluation source drift")
    return checked


def _window_name(timestamp: pd.Timestamp, cfg: dict[str, Any]) -> str:
    for name, (start, end) in cfg["windows"].items():
        if pd.Timestamp(start) <= timestamp <= pd.Timestamp(end):
            return name
    return "OUTSIDE_FROZEN_WINDOWS"


def build_release_surprises(
    releases: pd.DataFrame,
    cfg: dict[str, Any],
) -> tuple[pd.DataFrame, dict[str, int]]:
    strategy = cfg["strategy"]
    frame = releases[
        releases["family"].isin(strategy["families"])
    ].sort_values(["family", "event_time_utc"]).copy()
    frame["previous_event_time_utc"] = frame.groupby("family")[
        "event_time_utc"
    ].shift(1)
    frame["predecessor_days"] = (
        frame["event_time_utc"] - frame["previous_event_time_utc"]
    ).dt.total_seconds() / 86_400.0
    frame["valid_monthly_link"] = frame["predecessor_days"].between(
        float(strategy["minimum_predecessor_calendar_days"]),
        float(strategy["maximum_predecessor_calendar_days"]),
        inclusive="both",
    )
    history = int(strategy["rolling_expectation_releases"])
    frame["consecutive_history"] = frame.groupby("family")[
        "valid_monthly_link"
    ].transform(
        lambda values: values.rolling(
            history, min_periods=history
        ).sum().eq(history)
    )
    frame["rolling_median_initial_value"] = frame.groupby("family")[
        "initial_value"
    ].transform(
        lambda values: values.shift(1).rolling(
            history, min_periods=history
        ).median()
    )
    frame["release_gap_from_rolling_median"] = (
        frame["initial_value"] - frame["rolling_median_initial_value"]
    )
    usable = (
        frame["consecutive_history"]
        & frame["rolling_median_initial_value"].notna()
    )
    nonzero = (
        frame["release_gap_from_rolling_median"].ne(0)
        & frame["release_gap_from_rolling_median"].notna()
    )
    selected = frame[usable & nonzero].copy()
    selected["side"] = "LONG"
    selected.loc[
        selected["release_gap_from_rolling_median"].gt(0), "side"
    ] = "SHORT"
    return selected.reset_index(drop=True), {
        "source_rows": int(len(frame)),
        "incomplete_six_release_history": int((~usable).sum()),
        "zero_surprise": int((usable & ~nonzero).sum()),
        "directional_release_surprises": int(len(selected)),
    }


def attach_latest_release(
    points: pd.DataFrame,
    releases: pd.DataFrame,
    cfg: dict[str, Any],
) -> tuple[pd.DataFrame, dict[str, Any]]:
    signals, source_census = build_release_surprises(releases, cfg)
    macro = signals[
        [
            "family",
            "event_time_utc",
            "initial_value",
            "rolling_median_initial_value",
            "release_gap_from_rolling_median",
            "side",
            "source_pdf_sha256",
        ]
    ].rename(
        columns={
            "family": "macro_family",
            "event_time_utc": "macro_signal_time_utc",
            "side": "macro_side",
        }
    )
    left = points.sort_values("entry_time_utc").copy()
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
    candidates = joined[recent].copy()
    candidates["family"] = FAMILY
    candidates["regime"] = "NEUTRAL"
    candidates["side"] = candidates["macro_side"]
    candidates["window"] = candidates["entry_time_utc"].map(
        lambda value: _window_name(value, cfg)
    )
    candidates = candidates.sort_values(
        ["entry_time_utc", "decision_id"]
    ).reset_index(drop=True)
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
        for family in strategy["families"]
    }
    census = {
        **source_census,
        "neutral_clock_points": int(len(points)),
        "recent_macro_candidates": int(len(candidates)),
        "cash_no_release_within_72h": int((~recent).sum()),
        "candidate_days": int(candidates["eligible_date"].nunique()),
        "by_window": by_window,
        "by_side": by_side,
        "by_macro_family": by_family,
        "by_clock_minute": {
            str(minute): int(
                candidates["clock_minute"].eq(minute).sum()
            )
            for minute in strategy["entry_minutes_utc"]
        },
    }
    gate = cfg["outcome_blind_census"]
    checks = {
        "total": (
            census["recent_macro_candidates"]
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
    return candidates, census


def execute(
    candidates: pd.DataFrame,
    eurusd: pd.DataFrame,
    cfg: dict[str, Any],
) -> pd.DataFrame:
    prepared = candidates.copy()
    prepared["previous_initial_value"] = prepared[
        "rolling_median_initial_value"
    ]
    prepared["acceleration"] = prepared[
        "release_gap_from_rolling_median"
    ]
    trades = execute_carry(prepared, eurusd, cfg)
    trades = trades.rename(
        columns={
            "previous_initial_value": "rolling_median_initial_value",
            "acceleration": "release_gap_from_rolling_median",
        }
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
    eurusd, _, manifests = load_inputs(load_ensemble_config())
    releases, release_manifest = load_release_source(cfg)
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
    }
    if any(
        any(token in column for token in prohibited)
        for column in points.columns
    ):
        raise RuntimeError("Outcome column leaked into census clock source")
    return (
        cfg,
        eurusd,
        releases,
        {
            **manifests,
            "BLS_INITIAL_RELEASES": release_manifest,
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
    cfg, _, releases, manifests = _load_all()
    points = manifests.pop("_points")
    candidates, census = attach_latest_release(points, releases, cfg)
    return (
        serialize(
            {
                "schema_version": (
                    "eurusd_neutral_bls_rolling_surprise_carry_census_v1"
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
    cfg, eurusd, releases, manifests = _load_all()
    points = manifests.pop("_points")
    candidates, census = attach_latest_release(points, releases, cfg)
    if not census["passed"]:
        raise RuntimeError("Outcome-blind census failed; P&L is forbidden")
    trades = execute(candidates, eurusd, cfg)
    summary, matches = summarize_carry(trades, cfg)
    status = (
        "QUALIFIED_NEUTRAL_RESEARCH_CANDIDATE_FORWARD_REQUIRED"
        if summary["passed"]
        else "REJECTED_NEUTRAL_BLS_ROLLING_SURPRISE_CARRY_V1"
    )
    result = {
        "schema_version": (
            "eurusd_neutral_bls_rolling_surprise_carry_result_v1"
        ),
        "family": FAMILY,
        "status": status,
        "demo_ready": False,
        "live_ready": False,
        "information_status": cfg["information_status"],
        "research_boundary": (
            "All archived windows are adaptive historical development data. "
            "Chronological labels do not make them pristine holdouts."
        ),
        "mechanism": (
            "Current first-published CPI, PPI, or NFP value versus the "
            "median of six previous consecutive initial releases, carried "
            "for at most 72 hours to fixed Neutral first-hour clocks."
        ),
        "census": census,
        "summary": summary,
        "data_manifests": manifests,
        "decision_policy": cfg["decision_policy"],
    }
    return (
        serialize(result),
        {
            "CANDIDATES": candidates,
            "TRADES": trades,
            "DAILY_PORTFOLIO": aggregate_days(trades),
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
    "attach_latest_release",
    "build_release_surprises",
    "execute",
    "load_config",
    "run_backtest",
    "run_census",
    "verify_lock",
    "write_json",
]
