from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from .ensemble import load_ensemble_config, load_inputs
from .neutral_occ_fxe_flow import (
    _safe_payoff,
    _window,
    _window_gate,
    candidate_census,
    load_parent_config,
    write_json,
)
from .neutral_oracle_imitation import (
    economic_metrics,
    load_oracle,
    oracle_match_metrics,
)
from .neutral_walkforward import (
    _causal_candidate_features,
    _labeled_outcome,
)
from .research import (
    PACKAGE_ROOT,
    PIP,
    is_quarantined,
    remove_top_winners,
    sha256_file,
)


FAMILY = "N18_NEUTRAL_DTCC_OTC_MATCHED_PREMIUM_SKEW"
OUTPUT_ROOT = PACKAGE_ROOT / "outputs" / "neutral_dtcc_skew"


def load_config() -> dict[str, Any]:
    return json.loads(
        (
            PACKAGE_ROOT
            / "config"
            / "frozen_neutral_dtcc_skew.json"
        ).read_text(encoding="utf-8")
    )


def verify_lock() -> dict[str, str]:
    lock = json.loads(
        (
            PACKAGE_ROOT
            / "EURUSD_NEUTRAL_DTCC_SKEW_PREREG_2026_07_28.sha256.json"
        ).read_text(encoding="utf-8")
    )
    if (
        lock.get("locked_before_dtcc_skew_outcome_pass")
        is not True
    ):
        raise RuntimeError("DTCC skew contract is not locked")
    checked: dict[str, str] = {}
    for relative, expected in lock["files"].items():
        actual = sha256_file(PACKAGE_ROOT / relative)
        if actual != expected:
            raise RuntimeError(
                f"DTCC skew preregistration mismatch: {relative}"
            )
        checked[relative] = actual
    cfg = load_config()
    parent_path = PACKAGE_ROOT / cfg["parent_contract"]["path"]
    if sha256_file(parent_path) != cfg["parent_contract"]["sha256"]:
        raise RuntimeError("DTCC skew parent mismatch")
    manifest_path = Path(cfg["source_manifest"]["path"])
    if (
        sha256_file(manifest_path)
        != cfg["source_manifest"]["sha256"]
    ):
        raise RuntimeError("DTCC skew manifest mismatch")
    source_path = Path(cfg["source"]["path"])
    if sha256_file(source_path) != cfg["source"]["sha256"]:
        raise RuntimeError("DTCC skew source mismatch")
    return checked


def prepare_dtcc_skew(
    frame: pd.DataFrame, baseline_sessions: int
) -> pd.DataFrame:
    required = {
        "report_date",
        "available_time_utc",
        "matched_pairs",
        "daily_log_premium_skew",
        "median_pair_score",
        "source_eligible",
    }
    missing = required.difference(frame.columns)
    if missing:
        raise RuntimeError(
            f"Missing DTCC skew columns: {sorted(missing)}"
        )
    result = frame.copy()
    result["report_date"] = pd.to_datetime(result["report_date"])
    result["available_time_utc"] = pd.to_datetime(
        result["available_time_utc"], utc=True
    )
    result = result[result["source_eligible"].astype(bool)]
    result = (
        result.sort_values("report_date")
        .drop_duplicates("report_date", keep="last")
        .reset_index(drop=True)
    )
    result["prior_skew_median"] = (
        result["daily_log_premium_skew"]
        .astype(float)
        .shift(1)
        .rolling(
            baseline_sessions,
            min_periods=baseline_sessions,
        )
        .median()
    )
    result["normalized_skew"] = (
        result["daily_log_premium_skew"].astype(float)
        - result["prior_skew_median"]
    )
    return result


def attach_dtcc_skew(
    candidates: pd.DataFrame,
    source: pd.DataFrame,
    cfg: dict[str, Any],
) -> pd.DataFrame:
    prepared = prepare_dtcc_skew(
        source,
        int(cfg["candidate"]["baseline_sessions"]),
    )
    columns = [
        "report_date",
        "available_time_utc",
        "matched_pairs",
        "daily_log_premium_skew",
        "median_pair_score",
        "prior_skew_median",
        "normalized_skew",
    ]
    result = pd.merge_asof(
        candidates.sort_values("completion_time_utc"),
        prepared[columns].sort_values("available_time_utc"),
        left_on="completion_time_utc",
        right_on="available_time_utc",
        direction="backward",
        allow_exact_matches=True,
        tolerance=pd.Timedelta(
            hours=int(
                cfg["candidate"]["maximum_source_age_hours"]
            )
        ),
    )
    result["source_age_hours"] = (
        result["completion_time_utc"]
        - result["available_time_utc"]
    ).dt.total_seconds() / 3600.0
    result["source_available"] = (
        result["report_date"].notna()
        & result["normalized_skew"].notna()
    )
    result["active_participation"] = result["source_available"]
    result["trade_candidate"] = (
        result["source_available"]
        & result["normalized_skew"].ne(0)
    )
    result["side"] = np.select(
        [
            result["trade_candidate"]
            & result["normalized_skew"].gt(0),
            result["trade_candidate"]
            & result["normalized_skew"].lt(0),
        ],
        ["LONG", "SHORT"],
        default="CASH",
    )
    return result


def build_candidates(
    eurusd: pd.DataFrame,
    state: pd.DataFrame,
    cfg: dict[str, Any],
    parent: dict[str, Any],
    *,
    enforce_frozen_census: bool,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    base_cfg = load_ensemble_config()
    causal = _causal_candidate_features(eurusd, state, parent)
    candidates = causal[
        causal["completion_time_utc"].dt.hour.eq(0)
        & causal["completion_time_utc"].dt.minute.eq(0)
    ][
        [
            "signal_time_utc",
            "completion_time_utc",
            "matched_state_time_utc",
        ]
    ].copy()
    start = min(
        pd.Timestamp(value[0])
        for value in cfg["chronological_windows"].values()
    )
    end = max(
        pd.Timestamp(value[1])
        for value in cfg["chronological_windows"].values()
    )
    candidates = candidates[
        (candidates["completion_time_utc"] >= start)
        & (candidates["completion_time_utc"] <= end)
    ]
    candidates = candidates[
        ~candidates["completion_time_utc"].map(
            lambda value: is_quarantined(
                value, "EURUSD", base_cfg["quarantine"]
            )
        )
    ]
    source = pd.read_parquet(cfg["source"]["path"])
    attached = attach_dtcc_skew(candidates, source, cfg)
    attached["candidate_id"] = (
        attached["completion_time_utc"].dt.strftime(
            "%Y%m%dT%H%M%SZ"
        )
        + "_"
        + attached["side"]
    )
    census = candidate_census(attached, cfg)
    if (
        enforce_frozen_census
        and census != cfg["outcome_blind_census"]
    ):
        raise RuntimeError(
            "DTCC skew census drift: "
            f"actual={census!r} "
            f"frozen={cfg['outcome_blind_census']!r}"
        )
    return attached, census


def execute_candidates(
    candidates: pd.DataFrame,
    eurusd: pd.DataFrame,
    parent: dict[str, Any],
) -> pd.DataFrame:
    arrays = {
        column: eurusd[column].to_numpy(dtype=float)
        for column in (
            "bid_open",
            "bid_high",
            "bid_low",
            "bid_close",
            "ask_open",
            "ask_high",
            "ask_low",
            "ask_close",
        )
    }
    records: list[dict[str, Any]] = []
    for _, candidate in candidates[
        candidates["trade_candidate"]
    ].sort_values("completion_time_utc").iterrows():
        entry_time = candidate["completion_time_utc"]
        position = int(
            eurusd.index.searchsorted(entry_time, side="left")
        )
        if (
            position >= len(eurusd)
            or eurusd.index[position] != entry_time
        ):
            continue
        outcome = _labeled_outcome(
            position,
            eurusd.index,
            arrays,
            candidate["side"],
            parent,
            float(parent["label"]["risk_pips"]),
        )
        risk = float(outcome["risk_distance"])
        records.append(
            {
                "candidate_id": candidate["candidate_id"],
                "family": FAMILY,
                "regime": "NEUTRAL",
                "side": candidate["side"],
                "signal_time_utc": candidate["signal_time_utc"],
                "completion_time_utc": entry_time,
                **outcome,
                "r": float(outcome["outcome_r"]),
                "extra_half_pip_stress_r": (
                    float(outcome["outcome_r"])
                    - 0.5 * PIP / risk
                ),
                "source_report_date": candidate["report_date"],
                "source_age_hours": candidate["source_age_hours"],
                "matched_pairs": candidate["matched_pairs"],
                "daily_log_premium_skew": candidate[
                    "daily_log_premium_skew"
                ],
                "prior_skew_median": candidate[
                    "prior_skew_median"
                ],
                "normalized_skew": candidate["normalized_skew"],
            }
        )
    if not records:
        return pd.DataFrame()
    return pd.DataFrame(records).drop(columns=["outcome_r"])


def run_census() -> dict[str, Any]:
    cfg = load_config()
    parent = load_parent_config(cfg)
    base = load_ensemble_config()
    eurusd, state, _ = load_inputs(base)
    _, census = build_candidates(
        eurusd,
        state,
        cfg,
        parent,
        enforce_frozen_census=False,
    )
    return census


def run_neutral_dtcc_skew() -> tuple[
    dict[str, Any], dict[str, pd.DataFrame]
]:
    verify_lock()
    cfg = load_config()
    parent = load_parent_config(cfg)
    base = load_ensemble_config()
    eurusd, state, base_manifests = load_inputs(base)
    candidates, census = build_candidates(
        eurusd,
        state,
        cfg,
        parent,
        enforce_frozen_census=True,
    )
    trades = execute_candidates(candidates, eurusd, parent)

    oracle = load_oracle(parent)
    oracle_keys = set(
        zip(oracle["entry_time_utc"], oracle["side"], strict=False)
    )
    trades["oracle_member"] = [
        int((entry, side) in oracle_keys)
        for entry, side in zip(
            trades["entry_time_utc"],
            trades["side"],
            strict=False,
        )
    ]

    window_results: dict[str, Any] = {}
    match_parts: list[pd.DataFrame] = []
    for name, (start_raw, end_raw) in cfg[
        "chronological_windows"
    ].items():
        start = pd.Timestamp(start_raw)
        end = pd.Timestamp(end_raw)
        frame = _window(trades, start, end)
        economics = economic_metrics(
            frame, eurusd, start, end, cfg
        )
        imitation, matches = oracle_match_metrics(
            frame,
            oracle,
            start,
            end,
            int(
                cfg["oracle_matching"][
                    "secondary_tolerance_minutes"
                ]
            ),
        )
        matches["chronological_window"] = name
        match_parts.append(matches)
        window_results[name] = {
            "passed": _window_gate(economics, cfg, name),
            "economics": economics,
            "oracle_imitation": imitation,
        }

    full_start = min(
        pd.Timestamp(value[0])
        for value in cfg["chronological_windows"].values()
    )
    full_end = max(
        pd.Timestamp(value[1])
        for value in cfg["chronological_windows"].values()
    )
    full = economic_metrics(
        trades, eurusd, full_start, full_end, cfg
    )
    full_imitation, _ = oracle_match_metrics(
        trades,
        oracle,
        full_start,
        full_end,
        int(
            cfg["oracle_matching"]["secondary_tolerance_minutes"]
        ),
    )
    top_removed = _safe_payoff(remove_top_winners(trades))
    stressed = _safe_payoff(
        trades, "extra_half_pip_stress_r"
    )
    gate = cfg["admission"]
    overall_pass = (
        full["profit_factor"] is not None
        and full["profit_factor"]
        >= float(gate["minimum_profit_factor_overall"])
        and stressed["profit_factor"] is not None
        and stressed["profit_factor"]
        >= float(
            gate["minimum_stressed_profit_factor_overall"]
        )
        and full["max_drawdown_r"]
        <= float(gate["maximum_drawdown_r_overall"])
        and top_removed["net_r"] > 0
        and full_imitation["exact_precision"]
        >= float(gate["minimum_exact_match_precision_overall"])
    )
    admitted = (
        all(
            value["passed"] for value in window_results.values()
        )
        and overall_pass
    )

    trailing_bounds = {
        "latest_3_months": (
            "2026-04-01T00:00:00Z",
            "2026-06-30T23:59:59Z",
        ),
        "latest_6_months": (
            "2026-01-01T00:00:00Z",
            "2026-06-30T23:59:59Z",
        ),
        "latest_12_months": (
            "2025-07-01T00:00:00Z",
            "2026-06-30T23:59:59Z",
        ),
    }
    trailing = {
        name: economic_metrics(
            _window(
                trades,
                pd.Timestamp(start),
                pd.Timestamp(end),
            ),
            eurusd,
            pd.Timestamp(start),
            pd.Timestamp(end),
            cfg,
        )
        for name, (start, end) in trailing_bounds.items()
    }

    result = {
        "campaign_id": cfg["campaign_id"],
        "status": (
            "CAUSAL_RESEARCH_PASS_REQUIRES_PROSPECTIVE_CONFIRMATION"
            if admitted
            else "REJECTED_NEUTRAL_DTCC_SKEW_V1"
        ),
        "research_only": True,
        "broker_action_allowed": False,
        "information_status": cfg["information_status"],
        "source_manifests": {
            **base_manifests,
            "DTCC_OTC_MATCHED_PREMIUM_SKEW": {
                **cfg["source"],
                "manifest": cfg["source_manifest"],
            },
        },
        "causality": {
            "signal": (
                "Prior-session matched OTM EUR/USD OTC call-minus-put "
                "premium richness relative to trailing structural skew"
            ),
            "spot": (
                "Latest EURUSD M5 mid-close completed before each "
                "option execution"
            ),
            "source_available_time": (
                "Each trade's dissemination timestamp; daily matched "
                "skew becomes eligible at the next UTC midnight"
            ),
            "future_information_in_signal": False,
            "oracle_loaded_after_execution": True,
            "ml_used": False,
        },
        "outcome_blind_census": census,
        "chronological_windows": window_results,
        "all_available_history": {
            "economics": full,
            "oracle_imitation": full_imitation,
            "top_5_percent_winners_removed": top_removed,
            "extra_half_pip_round_trip": stressed,
            "overall_gate_passed": overall_pass,
        },
        "trailing_windows": trailing,
        "admitted": admitted,
        "verdict": (
            "The fixed DTCC matched-premium-skew expert passed every "
            "historical gate; untouched prospective confirmation is "
            "mandatory."
            if admitted
            else "The fixed DTCC matched-premium-skew expert failed "
            "at least one frozen chronological or robustness gate and "
            "is closed without repair."
        ),
    }
    matches = (
        pd.concat(match_parts, ignore_index=True)
        if match_parts
        else pd.DataFrame()
    )
    return result, {
        "CANDIDATES": candidates,
        "TRADES": trades,
        "ORACLE_MATCHES": matches,
    }
