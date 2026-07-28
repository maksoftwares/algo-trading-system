from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from .asymmetric import payoff_metrics
from .ensemble import load_ensemble_config, load_inputs
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
    serialize,
    sha256_file,
)


FAMILY = "N16_NEUTRAL_OCC_FXE_CUSTOMER_FLOW"
OUTPUT_ROOT = PACKAGE_ROOT / "outputs" / "neutral_occ_fxe_flow"


def load_config() -> dict[str, Any]:
    return json.loads(
        (
            PACKAGE_ROOT
            / "config"
            / "frozen_neutral_occ_fxe_flow.json"
        ).read_text(encoding="utf-8")
    )


def load_parent_config(cfg: dict[str, Any]) -> dict[str, Any]:
    return json.loads(
        (PACKAGE_ROOT / cfg["parent_contract"]["path"]).read_text(
            encoding="utf-8"
        )
    )


def verify_lock() -> dict[str, str]:
    lock = json.loads(
        (
            PACKAGE_ROOT
            / "EURUSD_NEUTRAL_OCC_FXE_FLOW_PREREG_2026_07_28.sha256.json"
        ).read_text(encoding="utf-8")
    )
    if (
        lock.get("locked_before_occ_fxe_flow_outcome_pass")
        is not True
    ):
        raise RuntimeError("OCC FXE-flow contract is not locked")
    checked: dict[str, str] = {}
    for relative, expected in lock["files"].items():
        actual = sha256_file(PACKAGE_ROOT / relative)
        if actual != expected:
            raise RuntimeError(
                f"OCC FXE-flow preregistration mismatch: {relative}"
            )
        checked[relative] = actual
    cfg = load_config()
    parent_path = PACKAGE_ROOT / cfg["parent_contract"]["path"]
    if sha256_file(parent_path) != cfg["parent_contract"]["sha256"]:
        raise RuntimeError("OCC FXE-flow parent mismatch")
    manifest_path = Path(cfg["source_manifest"]["path"])
    if (
        sha256_file(manifest_path)
        != cfg["source_manifest"]["sha256"]
    ):
        raise RuntimeError("OCC FXE-flow manifest mismatch")
    source_path = Path(cfg["source"]["path"])
    if sha256_file(source_path) != cfg["source"]["sha256"]:
        raise RuntimeError("OCC FXE-flow source mismatch")
    return checked


def prepare_occ_source(
    frame: pd.DataFrame, baseline_sessions: int
) -> pd.DataFrame:
    required = {
        "trade_date",
        "call_volume",
        "put_volume",
        "total_customer_volume",
        "source_has_records",
        "available_time_utc",
    }
    missing = required.difference(frame.columns)
    if missing:
        raise RuntimeError(
            f"Missing OCC source columns: {sorted(missing)}"
        )
    result = frame.copy()
    result["trade_date"] = pd.to_datetime(result["trade_date"])
    result["available_time_utc"] = pd.to_datetime(
        result["available_time_utc"], utc=True
    )
    result = (
        result.sort_values("trade_date")
        .drop_duplicates("trade_date", keep="last")
        .reset_index(drop=True)
    )
    result["raw_imbalance"] = (
        np.log1p(result["call_volume"].astype(float))
        - np.log1p(result["put_volume"].astype(float))
    )
    result["prior_imbalance_median"] = (
        result["raw_imbalance"]
        .shift(1)
        .rolling(
            baseline_sessions,
            min_periods=baseline_sessions,
        )
        .median()
    )
    result["normalized_imbalance"] = (
        result["raw_imbalance"]
        - result["prior_imbalance_median"]
    )
    result["prior_total_volume_median"] = (
        result["total_customer_volume"]
        .astype(float)
        .shift(1)
        .rolling(
            baseline_sessions,
            min_periods=baseline_sessions,
        )
        .median()
    )
    result["participation_ratio"] = (
        result["total_customer_volume"].astype(float)
        / result["prior_total_volume_median"].replace(0, np.nan)
    )
    return result


def attach_occ_source(
    candidates: pd.DataFrame,
    source: pd.DataFrame,
    cfg: dict[str, Any],
) -> pd.DataFrame:
    prepared = prepare_occ_source(
        source,
        int(cfg["candidate"]["baseline_sessions"]),
    )
    columns = [
        "trade_date",
        "available_time_utc",
        "call_volume",
        "put_volume",
        "total_customer_volume",
        "source_has_records",
        "raw_imbalance",
        "prior_imbalance_median",
        "normalized_imbalance",
        "participation_ratio",
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
        result["trade_date"].notna()
        & result["source_has_records"].fillna(False).astype(bool)
        & result["normalized_imbalance"].notna()
        & result["participation_ratio"].notna()
    )
    result["active_participation"] = (
        result["source_available"]
        & result["participation_ratio"].ge(
            float(
                cfg["candidate"][
                    "minimum_participation_ratio"
                ]
            )
        )
    )
    result["trade_candidate"] = (
        result["active_participation"]
        & result["normalized_imbalance"].ne(0)
    )
    result["side"] = np.select(
        [
            result["trade_candidate"]
            & result["normalized_imbalance"].gt(0),
            result["trade_candidate"]
            & result["normalized_imbalance"].lt(0),
        ],
        ["LONG", "SHORT"],
        default="CASH",
    )
    return result


def window_name(
    timestamp: pd.Timestamp, cfg: dict[str, Any]
) -> str:
    for name, (start, end) in cfg[
        "chronological_windows"
    ].items():
        if pd.Timestamp(start) <= timestamp <= pd.Timestamp(end):
            return name
    return "OUTSIDE"


def candidate_census(
    candidates: pd.DataFrame, cfg: dict[str, Any]
) -> dict[str, Any]:
    frame = candidates.copy()
    frame["window"] = frame["completion_time_utc"].map(
        lambda value: window_name(value, cfg)
    )
    return {
        "neutral_open_candidates": int(len(frame)),
        "source_available_candidates": int(
            frame["source_available"].sum()
        ),
        "active_participation_candidates": int(
            frame["active_participation"].sum()
        ),
        "trade_candidates": int(frame["trade_candidate"].sum()),
        "long_candidates": int(
            (
                frame["trade_candidate"]
                & frame["side"].eq("LONG")
            ).sum()
        ),
        "short_candidates": int(
            (
                frame["trade_candidate"]
                & frame["side"].eq("SHORT")
            ).sum()
        ),
        "by_window": {
            name: int(group["trade_candidate"].sum())
            for name, group in frame.groupby("window")
            if name != "OUTSIDE"
        },
    }


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
    attached = attach_occ_source(candidates, source, cfg)
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
            "OCC FXE-flow census drift: "
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
                "source_trade_date": candidate["trade_date"],
                "call_volume": candidate["call_volume"],
                "put_volume": candidate["put_volume"],
                "raw_imbalance": candidate["raw_imbalance"],
                "prior_imbalance_median": candidate[
                    "prior_imbalance_median"
                ],
                "normalized_imbalance": candidate[
                    "normalized_imbalance"
                ],
                "participation_ratio": candidate[
                    "participation_ratio"
                ],
            }
        )
    if not records:
        return pd.DataFrame()
    return pd.DataFrame(records).drop(columns=["outcome_r"])


def _safe_payoff(
    trades: pd.DataFrame, value_column: str = "r"
) -> dict[str, Any]:
    raw = payoff_metrics(trades, value_column)
    return {
        key: (
            None
            if isinstance(value, (float, np.floating))
            and not np.isfinite(value)
            else value
        )
        for key, value in raw.items()
    }


def _window(
    trades: pd.DataFrame, start: pd.Timestamp, end: pd.Timestamp
) -> pd.DataFrame:
    return trades[
        (trades["entry_time_utc"] >= start)
        & (trades["entry_time_utc"] <= end)
    ]


def _window_gate(
    metrics: dict[str, Any],
    cfg: dict[str, Any],
    name: str,
) -> bool:
    gate = cfg["admission"]
    payoff = metrics["realized_payoff_ratio"]
    profit_factor = metrics["profit_factor"]
    return (
        metrics["trades"]
        >= int(gate["minimum_trades_by_window"][name])
        and float(gate["minimum_win_rate"])
        <= metrics["win_rate"]
        <= float(gate["maximum_win_rate"])
        and payoff is not None
        and float(gate["minimum_realized_payoff_ratio"])
        <= payoff
        <= float(gate["maximum_realized_payoff_ratio"])
        and profit_factor is not None
        and profit_factor
        >= float(gate["minimum_profit_factor_per_window"])
        and metrics["expectancy_r"]
        > float(gate["minimum_expectancy_r"])
    )


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


def run_neutral_occ_fxe_flow() -> tuple[
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
            else "REJECTED_NEUTRAL_OCC_FXE_FLOW_V1"
        ),
        "research_only": True,
        "broker_action_allowed": False,
        "information_status": cfg["information_status"],
        "source_manifests": {
            **base_manifests,
            "OCC_FXE": {
                **cfg["source"],
                "manifest": cfg["source_manifest"],
            },
        },
        "causality": {
            "signal": (
                "OCC-cleared prior-day FXE customer call-versus-put "
                "volume relative to its trailing structural baseline"
            ),
            "source_available_time": (
                "Conservatively next UTC midnight after report date"
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
            "The fixed OCC customer options-flow expert passed every "
            "historical gate; untouched prospective confirmation is "
            "mandatory."
            if admitted
            else "The fixed OCC customer options-flow expert failed "
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


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(serialize(payload), indent=2),
        encoding="utf-8",
    )
