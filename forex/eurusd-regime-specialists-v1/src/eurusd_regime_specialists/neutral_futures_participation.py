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


FAMILY = "N15_NEUTRAL_FUTURES_PARTICIPATION"
OUTPUT_ROOT = (
    PACKAGE_ROOT / "outputs" / "neutral_futures_participation"
)


def load_config() -> dict[str, Any]:
    return json.loads(
        (
            PACKAGE_ROOT
            / "config"
            / "frozen_neutral_futures_participation.json"
        ).read_text(encoding="utf-8")
    )


def load_parent_config(cfg: dict[str, Any]) -> dict[str, Any]:
    return json.loads(
        (PACKAGE_ROOT / cfg["parent_contract"]["path"]).read_text(
            encoding="utf-8"
        )
    )


def verify_lock() -> dict[str, str]:
    lock_path = (
        PACKAGE_ROOT
        / "EURUSD_NEUTRAL_FUTURES_PARTICIPATION_PREREG_2026_07_28.sha256.json"
    )
    lock = json.loads(lock_path.read_text(encoding="utf-8"))
    if (
        lock.get(
            "locked_before_futures_participation_outcome_pass"
        )
        is not True
    ):
        raise RuntimeError(
            "Futures-participation contract is not locked"
        )
    checked: dict[str, str] = {}
    for relative, expected in lock["files"].items():
        actual = sha256_file(PACKAGE_ROOT / relative)
        if actual != expected:
            raise RuntimeError(
                "Futures-participation preregistration mismatch: "
                f"{relative}"
            )
        checked[relative] = actual
    cfg = load_config()
    parent_path = PACKAGE_ROOT / cfg["parent_contract"]["path"]
    if sha256_file(parent_path) != cfg["parent_contract"]["sha256"]:
        raise RuntimeError(
            "Futures-participation parent contract mismatch"
        )
    manifest_path = Path(cfg["source_manifest"]["path"])
    if (
        sha256_file(manifest_path)
        != cfg["source_manifest"]["sha256"]
    ):
        raise RuntimeError(
            "Futures-participation source manifest mismatch"
        )
    for source in cfg["sources"].values():
        source_path = Path(source["path"])
        if sha256_file(source_path) != source["sha256"]:
            raise RuntimeError(
                f"Futures-participation source mismatch: {source_path}"
            )
    return checked


def prepare_exchange_source(
    frame: pd.DataFrame,
    baseline_sessions: int,
    prefix: str,
) -> pd.DataFrame:
    required = {
        "trade_date",
        "open",
        "close",
        "volume",
        "source_row_valid",
    }
    missing = required.difference(frame.columns)
    if missing:
        raise RuntimeError(
            f"Missing exchange-source columns: {sorted(missing)}"
        )
    result = frame.copy()
    result["trade_date"] = pd.to_datetime(
        result["trade_date"], errors="raise"
    )
    result = (
        result.sort_values("trade_date")
        .drop_duplicates("trade_date", keep="last")
        .reset_index(drop=True)
    )
    result["session_return"] = (
        result["close"].astype(float)
        / result["open"].astype(float)
        - 1.0
    )
    result["prior_volume_median"] = (
        result["volume"]
        .astype(float)
        .shift(1)
        .rolling(
            baseline_sessions,
            min_periods=baseline_sessions,
        )
        .median()
    )
    result["volume_ratio"] = (
        result["volume"].astype(float)
        / result["prior_volume_median"]
    )
    result["available_time_utc"] = (
        result["trade_date"] + pd.Timedelta(days=1)
    ).dt.tz_localize("UTC")
    result = result.rename(
        columns={
            "trade_date": f"{prefix}_trade_date",
            "session_return": f"{prefix}_session_return",
            "volume_ratio": f"{prefix}_volume_ratio",
            "source_row_valid": f"{prefix}_source_row_valid",
            "available_time_utc": f"{prefix}_available_time_utc",
        }
    )
    return result[
        [
            f"{prefix}_trade_date",
            f"{prefix}_session_return",
            f"{prefix}_volume_ratio",
            f"{prefix}_source_row_valid",
            f"{prefix}_available_time_utc",
        ]
    ]


def attach_exchange_sources(
    candidates: pd.DataFrame,
    euro: pd.DataFrame,
    dollar: pd.DataFrame,
    cfg: dict[str, Any],
) -> pd.DataFrame:
    result = candidates.sort_values("completion_time_utc").copy()
    baseline = int(
        cfg["candidate"]["volume_baseline_sessions"]
    )
    maximum_age = pd.Timedelta(
        hours=int(
            cfg["candidate"]["maximum_source_age_hours"]
        )
    )
    for prefix, frame in (("euro", euro), ("dollar", dollar)):
        prepared = prepare_exchange_source(
            frame, baseline, prefix
        )
        right_time = f"{prefix}_available_time_utc"
        result = pd.merge_asof(
            result.sort_values("completion_time_utc"),
            prepared.sort_values(right_time),
            left_on="completion_time_utc",
            right_on=right_time,
            direction="backward",
            allow_exact_matches=True,
            tolerance=maximum_age,
        )
        result[f"{prefix}_source_age_hours"] = (
            result["completion_time_utc"] - result[right_time]
        ).dt.total_seconds() / 3600.0

    result["same_source_trade_date"] = (
        result["euro_trade_date"].notna()
        & result["euro_trade_date"].eq(
            result["dollar_trade_date"]
        )
    )
    result["valid_sources"] = (
        result["same_source_trade_date"]
        & result["euro_source_row_valid"]
        .fillna(False)
        .astype(bool)
        & result["dollar_source_row_valid"]
        .fillna(False)
        .astype(bool)
        & result["euro_session_return"].notna()
        & result["dollar_session_return"].notna()
        & result["euro_volume_ratio"].gt(0)
        & result["dollar_volume_ratio"].gt(0)
    )
    result["euro_vote"] = np.sign(
        result["euro_session_return"]
    )
    result["dollar_vote"] = -np.sign(
        result["dollar_session_return"]
    )
    result["direction_agreement"] = (
        result["valid_sources"]
        & result["euro_vote"].abs().eq(1.0)
        & result["euro_vote"].eq(result["dollar_vote"])
    )
    result["participation_score"] = np.sqrt(
        result["euro_volume_ratio"]
        * result["dollar_volume_ratio"]
    )
    result["participation_confirmed"] = (
        result["valid_sources"]
        & result["participation_score"].ge(
            float(
                cfg["candidate"][
                    "minimum_participation_score"
                ]
            )
        )
    )
    result["trade_candidate"] = (
        result["direction_agreement"]
        & result["participation_confirmed"]
    )
    result["side"] = np.select(
        [
            result["trade_candidate"]
            & result["euro_vote"].gt(0),
            result["trade_candidate"]
            & result["euro_vote"].lt(0),
        ],
        ["LONG", "SHORT"],
        default="CASH",
    )
    return result


def candidate_census(
    candidates: pd.DataFrame,
) -> dict[str, Any]:
    candidates = candidates.copy()
    candidates["year"] = candidates[
        "completion_time_utc"
    ].dt.year
    return {
        "neutral_open_candidates": int(len(candidates)),
        "same_date_valid_sources": int(
            candidates["valid_sources"].sum()
        ),
        "direction_agreements": int(
            candidates["direction_agreement"].sum()
        ),
        "trade_candidates": int(
            candidates["trade_candidate"].sum()
        ),
        "long_candidates": int(
            (
                candidates["trade_candidate"]
                & candidates["side"].eq("LONG")
            ).sum()
        ),
        "short_candidates": int(
            (
                candidates["trade_candidate"]
                & candidates["side"].eq("SHORT")
            ).sum()
        ),
        "by_year": {
            str(int(year)): int(group["trade_candidate"].sum())
            for year, group in candidates.groupby("year")
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
    candidates = candidates[
        ~candidates["completion_time_utc"].map(
            lambda value: is_quarantined(
                value, "EURUSD", base_cfg["quarantine"]
            )
        )
    ]
    euro = pd.read_parquet(cfg["sources"]["EURO_FX"]["path"])
    dollar = pd.read_parquet(
        cfg["sources"]["DOLLAR_ETF"]["path"]
    )
    attached = attach_exchange_sources(
        candidates, euro, dollar, cfg
    )
    attached["candidate_id"] = (
        attached["completion_time_utc"].dt.strftime(
            "%Y%m%dT%H%M%SZ"
        )
        + "_"
        + attached["side"]
    )
    census = candidate_census(attached)
    if enforce_frozen_census:
        frozen = cfg["outcome_blind_census"]
        if census != frozen:
            raise RuntimeError(
                "Futures-participation outcome-blind census drift: "
                f"actual={census!r}, frozen={frozen!r}"
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
    chosen = candidates[candidates["trade_candidate"]]
    for _, candidate in chosen.sort_values(
        "completion_time_utc"
    ).iterrows():
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
                "source_trade_date": candidate[
                    "euro_trade_date"
                ],
                "euro_session_return": candidate[
                    "euro_session_return"
                ],
                "dollar_session_return": candidate[
                    "dollar_session_return"
                ],
                "euro_volume_ratio": candidate[
                    "euro_volume_ratio"
                ],
                "dollar_volume_ratio": candidate[
                    "dollar_volume_ratio"
                ],
                "participation_score": candidate[
                    "participation_score"
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


def _gate(
    metrics: dict[str, Any],
    cfg: dict[str, Any],
    minimum_trades: int,
) -> bool:
    gate = cfg["admission"]
    payoff = metrics["realized_payoff_ratio"]
    profit_factor = metrics["profit_factor"]
    return (
        metrics["trades"] >= minimum_trades
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


def run_neutral_futures_participation() -> tuple[
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

    development_start, development_end = map(
        pd.Timestamp, cfg["development_window"]
    )
    development_trades = _window(
        trades, development_start, development_end
    )
    development = economic_metrics(
        development_trades,
        eurusd,
        development_start,
        development_end,
        cfg,
    )
    development_pass = _gate(
        development,
        cfg,
        int(cfg["admission"]["minimum_development_trades"]),
    )

    window_results: dict[str, Any] = {}
    match_parts: list[pd.DataFrame] = []
    for name, (start_raw, end_raw) in cfg[
        "walk_forward_windows"
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
        matches["walk_forward_window"] = name
        match_parts.append(matches)
        window_results[name] = {
            "passed": _gate(
                economics,
                cfg,
                int(
                    cfg["admission"][
                        "minimum_forward_window_trades"
                    ]
                ),
            ),
            "economics": economics,
            "oracle_imitation": imitation,
        }

    forward_start = min(
        pd.Timestamp(values[0])
        for values in cfg["walk_forward_windows"].values()
    )
    forward_end = max(
        pd.Timestamp(values[1])
        for values in cfg["walk_forward_windows"].values()
    )
    forward = _window(trades, forward_start, forward_end)
    forward_economics = economic_metrics(
        forward, eurusd, forward_start, forward_end, cfg
    )
    forward_imitation, _ = oracle_match_metrics(
        forward,
        oracle,
        forward_start,
        forward_end,
        int(
            cfg["oracle_matching"]["secondary_tolerance_minutes"]
        ),
    )
    full_start = pd.Timestamp(base["data"]["start_utc"])
    full_end = pd.Timestamp(base["data"]["end_utc"])
    full = economic_metrics(
        trades, eurusd, full_start, full_end, cfg
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
    )
    imitation_pass = (
        forward_imitation["exact_precision"]
        >= float(gate["minimum_exact_match_precision_overall"])
        and forward_imitation["exact_recall"]
        >= float(gate["minimum_exact_match_recall_overall"])
    )
    admitted = (
        development_pass
        and all(
            value["passed"] for value in window_results.values()
        )
        and overall_pass
        and imitation_pass
    )

    period_bounds = {
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
        "latest_2_years": (
            "2024-07-01T00:00:00Z",
            "2026-06-30T23:59:59Z",
        ),
        "latest_5_years": (
            "2021-07-01T00:00:00Z",
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
        for name, (start, end) in period_bounds.items()
    }

    result = {
        "campaign_id": cfg["campaign_id"],
        "status": (
            "CAUSAL_RESEARCH_PASS_REQUIRES_PROSPECTIVE_CONFIRMATION"
            if admitted
            else "REJECTED_NEUTRAL_FUTURES_PARTICIPATION_V1"
        ),
        "research_only": True,
        "broker_action_allowed": False,
        "information_status": cfg["information_status"],
        "source_manifests": {
            **base_manifests,
            "exchange_manifest": cfg["source_manifest"],
            **cfg["sources"],
        },
        "causality": {
            "signal": (
                "Prior completed Euro FX futures and UUP sessions; "
                "direction agreement plus above-median joint volume"
            ),
            "source_available_time": (
                "Conservatively next UTC midnight after trade date"
            ),
            "future_information_in_signal": False,
            "oracle_loaded_after_execution": True,
            "ml_used": False,
        },
        "outcome_blind_census": census,
        "development": {
            "passed": development_pass,
            "economics": development,
        },
        "walk_forward": {
            "admitted": admitted,
            "windows": window_results,
            "overall_economics": forward_economics,
            "overall_oracle_imitation": forward_imitation,
            "imitation_gate_passed": imitation_pass,
        },
        "all_history": {
            "economics": full,
            "top_5_percent_winners_removed": top_removed,
            "extra_half_pip_round_trip": stressed,
            "overall_gate_passed": overall_pass,
        },
        "trailing_windows": trailing,
        "verdict": (
            "The fixed exchange-participation expert passed every "
            "historical gate; untouched prospective confirmation is "
            "mandatory."
            if admitted
            else "The fixed exchange-participation expert failed at "
            "least one frozen development, forward, imitation, or "
            "robustness gate and is closed without repair."
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
