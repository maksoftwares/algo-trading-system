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


FAMILY = "N9_NEUTRAL_UTC_OPEN_VOTE"
OUTPUT_ROOT = PACKAGE_ROOT / "outputs" / "neutral_utc_open_vote"
FX_VOTE_SYMBOLS = ("EURUSD", "EURGBP", "EURJPY")
VOTE_COLUMNS = (
    "vote_eurusd",
    "vote_eurgbp",
    "vote_eurjpy",
    "vote_dxy",
)


def load_config() -> dict[str, Any]:
    return json.loads(
        (
            PACKAGE_ROOT
            / "config"
            / "frozen_neutral_utc_open_vote.json"
        ).read_text(encoding="utf-8")
    )


def load_parent_config() -> dict[str, Any]:
    cfg = load_config()
    return json.loads(
        (PACKAGE_ROOT / cfg["parent_contract"]["path"]).read_text(
            encoding="utf-8"
        )
    )


def verify_lock() -> dict[str, str]:
    lock = json.loads(
        (
            PACKAGE_ROOT
            / "EURUSD_NEUTRAL_UTC_OPEN_VOTE_PREREG_2026_07_27.sha256.json"
        ).read_text(encoding="utf-8")
    )
    if lock.get("locked_before_utc_open_vote_outcome_pass") is not True:
        raise RuntimeError("UTC-open vote contract is not locked")
    checked: dict[str, str] = {}
    for relative, expected in lock["files"].items():
        actual = sha256_file(PACKAGE_ROOT / relative)
        if actual != expected:
            raise RuntimeError(
                f"UTC-open vote preregistration mismatch: {relative}"
            )
        checked[relative] = actual
    cfg = load_config()
    parent_path = PACKAGE_ROOT / cfg["parent_contract"]["path"]
    parent_hash = sha256_file(parent_path)
    if parent_hash != cfg["parent_contract"]["sha256"]:
        raise RuntimeError("UTC-open vote parent contract mismatch")
    checked[str(parent_path)] = parent_hash
    for source in cfg["sources"].values():
        path = Path(source["path"])
        actual = sha256_file(path)
        if actual != source["sha256"]:
            raise RuntimeError(
                f"UTC-open vote source hash mismatch: {path}"
            )
        checked[str(path)] = actual
    return checked


def load_bidask_m5(
    path: Path, start: pd.Timestamp, end: pd.Timestamp
) -> pd.DataFrame:
    frame = pd.read_parquet(path)
    frame["timestamp_utc"] = pd.to_datetime(
        frame["timestamp_ms"], unit="ms", utc=True
    )
    frame = frame[
        (frame["timestamp_utc"] >= start)
        & (frame["timestamp_utc"] <= end)
    ]
    frame = (
        frame.sort_values("timestamp_utc")
        .drop_duplicates("timestamp_utc", keep="last")
        .set_index("timestamp_utc")
    )
    if not frame.index.is_monotonic_increasing:
        raise RuntimeError(f"Non-monotonic M5 source: {path}")
    return frame


def completed_return_vote(
    close: pd.Series, horizon_minutes: int
) -> pd.Series:
    bars = int(horizon_minutes // 5)
    if bars <= 0 or bars * 5 != horizon_minutes:
        raise ValueError("Vote horizon must be a positive M5 multiple")
    lag = close.shift(bars)
    elapsed = (
        close.index.to_series()
        - close.index.to_series().shift(bars)
    )
    contiguous = elapsed.eq(pd.Timedelta(minutes=horizon_minutes))
    return np.sign(close.astype(float) - lag.astype(float)).where(
        contiguous
    )


def _mid_close(frame: pd.DataFrame) -> pd.Series:
    return (
        frame["bid_close"].astype(float)
        + frame["ask_close"].astype(float)
    ) / 2.0


def attach_vote_sources(
    candidates: pd.DataFrame,
    fx_frames: dict[str, pd.DataFrame],
    dxy_macro: pd.DataFrame,
    cfg: dict[str, Any],
) -> pd.DataFrame:
    result = candidates.copy().sort_values("signal_time_utc")
    horizon = int(cfg["candidate"]["return_horizon_minutes"])
    for symbol in FX_VOTE_SYMBOLS:
        vote = completed_return_vote(
            _mid_close(fx_frames[symbol]), horizon
        )
        result[f"vote_{symbol.lower()}"] = vote.reindex(
            pd.DatetimeIndex(result["signal_time_utc"])
        ).to_numpy()
    dxy = dxy_macro.copy()
    dxy["timestamp_utc"] = pd.to_datetime(
        dxy["timestamp_utc"], utc=True
    )
    dxy = dxy[
        dxy["dollaridxusd_available"].fillna(False).astype(bool)
    ]
    dxy = (
        dxy.sort_values("timestamp_utc")
        .drop_duplicates("timestamp_utc", keep="last")
        .set_index("timestamp_utc")
    )
    dxy["vote_dxy"] = -completed_return_vote(
        dxy["dollaridxusd_mid_close"].astype(float), horizon
    )
    right = (
        dxy[["vote_dxy"]]
        .reset_index()
        .rename(columns={"timestamp_utc": "dxy_source_time_utc"})
    )
    result = pd.merge_asof(
        result.sort_values("signal_time_utc"),
        right.sort_values("dxy_source_time_utc"),
        left_on="signal_time_utc",
        right_on="dxy_source_time_utc",
        direction="backward",
        allow_exact_matches=True,
        tolerance=pd.Timedelta(
            minutes=int(
                cfg["sources"]["DXY"]["maximum_age_minutes"]
            )
        ),
    )
    result["dxy_age_minutes"] = (
        result["signal_time_utc"] - result["dxy_source_time_utc"]
    ).dt.total_seconds() / 60.0
    result["four_valid_nonzero_votes"] = (
        result[list(VOTE_COLUMNS)].abs().eq(1.0).all(axis=1)
    )
    result["vote_sum"] = result[list(VOTE_COLUMNS)].sum(
        axis=1, min_count=len(VOTE_COLUMNS)
    )
    result["trade_candidate"] = (
        result["four_valid_nonzero_votes"]
        & result["vote_sum"].abs().ge(2.0)
    )
    result["side"] = np.select(
        [result["vote_sum"].ge(2.0), result["vote_sum"].le(-2.0)],
        ["LONG", "SHORT"],
        default="CASH",
    )
    return result


def build_vote_candidates(
    eurusd: pd.DataFrame,
    state: pd.DataFrame,
    cfg: dict[str, Any],
    parent: dict[str, Any],
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
    start = pd.Timestamp(base_cfg["data"]["start_utc"])
    end = pd.Timestamp(base_cfg["data"]["end_utc"])
    fx_frames = {"EURUSD": eurusd}
    for symbol in ("EURGBP", "EURJPY"):
        fx_frames[symbol] = load_bidask_m5(
            Path(cfg["sources"][symbol]["path"]), start, end
        )
    macro = pd.read_parquet(Path(cfg["sources"]["DXY"]["path"]))
    attached = attach_vote_sources(
        candidates, fx_frames, macro, cfg
    )
    attached["candidate_id"] = (
        attached["completion_time_utc"].dt.strftime("%Y%m%dT%H%M%SZ")
        + "_"
        + attached["side"]
    )
    attached["year"] = attached["completion_time_utc"].dt.year
    census = {
        "neutral_open_candidates": int(len(attached)),
        "four_valid_nonzero_votes": int(
            attached["four_valid_nonzero_votes"].sum()
        ),
        "trade_candidates": int(
            attached["trade_candidate"].sum()
        ),
        "long_candidates": int(
            (
                attached["trade_candidate"]
                & attached["side"].eq("LONG")
            ).sum()
        ),
        "short_candidates": int(
            (
                attached["trade_candidate"]
                & attached["side"].eq("SHORT")
            ).sum()
        ),
        "by_year": {
            str(year): int(group["trade_candidate"].sum())
            for year, group in attached.groupby("year")
        },
    }
    frozen = cfg["outcome_blind_census"]
    for key in (
        "neutral_open_candidates",
        "four_valid_nonzero_votes",
        "trade_candidates",
        "long_candidates",
        "short_candidates",
    ):
        if census[key] != int(frozen[key]):
            raise RuntimeError(
                f"UTC-open outcome-blind census drift: {key}"
            )
    return attached, census


def execute_candidates(
    candidates: pd.DataFrame,
    eurusd: pd.DataFrame,
    parent: dict[str, Any],
) -> pd.DataFrame:
    chosen = candidates[candidates["trade_candidate"]].copy()
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
                "vote_eurusd": candidate["vote_eurusd"],
                "vote_eurgbp": candidate["vote_eurgbp"],
                "vote_eurjpy": candidate["vote_eurjpy"],
                "vote_dxy": candidate["vote_dxy"],
                "vote_sum": candidate["vote_sum"],
                "dxy_source_time_utc": candidate[
                    "dxy_source_time_utc"
                ],
                "dxy_age_minutes": candidate["dxy_age_minutes"],
            }
        )
    return pd.DataFrame(records).drop(columns=["outcome_r"])


def _safe_metrics(
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


def _gate_pass(
    metrics: dict[str, Any],
    gate: dict[str, Any],
    minimum_trades: int,
) -> bool:
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
        and profit_factor >= float(gate["minimum_profit_factor"])
        and metrics["expectancy_r"]
        > float(gate["minimum_expectancy_r"])
    )


def _source_manifest(
    path: Path, frame: pd.DataFrame, timestamp: pd.Series
) -> dict[str, Any]:
    parsed = pd.to_datetime(timestamp, utc=True)
    return {
        "path": str(path),
        "sha256": sha256_file(path),
        "rows": int(len(frame)),
        "first_utc": parsed.min().isoformat(),
        "last_utc": parsed.max().isoformat(),
    }


def run_neutral_utc_open_vote() -> tuple[
    dict[str, Any], dict[str, pd.DataFrame]
]:
    verify_lock()
    cfg = load_config()
    parent = load_parent_config()
    base = load_ensemble_config()
    eurusd, state, base_manifests = load_inputs(base)
    candidates, census = build_vote_candidates(
        eurusd, state, cfg, parent
    )
    trades = execute_candidates(candidates, eurusd, parent)

    # Oracle information is attached only after deterministic direction and
    # price-path execution have already been generated.
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
    development_trades = trades[
        (trades["entry_time_utc"] >= development_start)
        & (trades["entry_time_utc"] <= development_end)
    ]
    development = economic_metrics(
        development_trades,
        eurusd,
        development_start,
        development_end,
        cfg,
    )
    development_pass = _gate_pass(
        development,
        cfg["development_gate"],
        int(cfg["development_gate"]["minimum_trades"]),
    )

    window_results: dict[str, Any] = {}
    match_parts: list[pd.DataFrame] = []
    for name, (start_raw, end_raw) in cfg[
        "walk_forward_windows"
    ].items():
        start = pd.Timestamp(start_raw)
        end = pd.Timestamp(end_raw)
        frame = trades[
            (trades["entry_time_utc"] >= start)
            & (trades["entry_time_utc"] <= end)
        ]
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
        passed = _gate_pass(
            economics,
            cfg["final_admission"],
            int(
                cfg["final_admission"][
                    "minimum_trades_by_window"
                ][name]
            ),
        )
        window_results[name] = {
            "passed": passed,
            "economics": economics,
            "oracle_imitation": imitation,
        }

    forward_start = min(
        pd.Timestamp(value[0])
        for value in cfg["walk_forward_windows"].values()
    )
    forward_end = max(
        pd.Timestamp(value[1])
        for value in cfg["walk_forward_windows"].values()
    )
    forward_trades = trades[
        (trades["entry_time_utc"] >= forward_start)
        & (trades["entry_time_utc"] <= forward_end)
    ]
    forward_economics = economic_metrics(
        forward_trades, eurusd, forward_start, forward_end, cfg
    )
    forward_imitation, _ = oracle_match_metrics(
        forward_trades,
        oracle,
        forward_start,
        forward_end,
        int(
            cfg["oracle_matching"]["secondary_tolerance_minutes"]
        ),
    )
    all_history = economic_metrics(
        trades,
        eurusd,
        pd.Timestamp(base["data"]["start_utc"]),
        pd.Timestamp(base["data"]["end_utc"]),
        cfg,
    )
    top_removed = _safe_metrics(remove_top_winners(trades))
    stressed = _safe_metrics(trades, "extra_half_pip_stress_r")
    gate = cfg["final_admission"]
    imitation_pass = (
        forward_imitation["exact_precision"]
        >= float(gate["minimum_exact_match_precision_overall"])
        and forward_imitation["exact_recall"]
        >= float(gate["minimum_exact_match_recall_overall"])
        and forward_imitation["tolerant_precision"]
        >= float(gate["minimum_15m_match_precision_overall"])
    )
    robustness_pass = (
        all_history["max_drawdown_r"]
        <= float(gate["maximum_drawdown_r_overall"])
        and top_removed["net_r"] > 0
        and stressed["net_r"] > 0
    )
    census_pass = (
        census["trade_candidates"]
        >= int(
            cfg["outcome_blind_census"][
                "minimum_trade_candidates"
            ]
        )
        and all(
            census["by_year"].get(str(year), 0)
            >= int(
                cfg["outcome_blind_census"][
                    "minimum_each_full_forward_year"
                ]
            )
            for year in (2023, 2024, 2025)
        )
        and census["by_year"].get("2026", 0)
        >= int(
            cfg["outcome_blind_census"]["minimum_2026_h1"]
        )
    )
    admitted = (
        census_pass
        and development_pass
        and all(
            value["passed"] for value in window_results.values()
        )
        and imitation_pass
        and robustness_pass
    )

    membership_breakdown = {
        name: _safe_metrics(
            forward_trades[
                forward_trades["oracle_member"].eq(member)
            ]
        )
        for member, name in (
            (1, "exact_oracle_members"),
            (0, "nonmembers"),
        )
    }

    manifests = dict(base_manifests)
    for symbol in FX_VOTE_SYMBOLS:
        path = Path(cfg["sources"][symbol]["path"])
        if symbol == "EURUSD":
            frame = eurusd.reset_index()
            timestamp = frame["timestamp_utc"]
        else:
            frame = pd.read_parquet(path)
            timestamp = pd.to_datetime(
                frame["timestamp_ms"], unit="ms", utc=True
            )
        manifests[symbol] = _source_manifest(
            path, frame, timestamp
        )
    macro_path = Path(cfg["sources"]["DXY"]["path"])
    macro = pd.read_parquet(macro_path)
    manifests["DXY_M5"] = _source_manifest(
        macro_path, macro, macro["timestamp_utc"]
    )

    result = {
        "campaign_id": cfg["campaign_id"],
        "status": (
            "CAUSAL_RESEARCH_PASS_REQUIRES_PROSPECTIVE_CONFIRMATION"
            if admitted
            else "REJECTED_NEUTRAL_UTC_OPEN_VOTE_V1"
        ),
        "research_only": True,
        "broker_action_allowed": False,
        "information_status": cfg["information_status"],
        "source_manifests": manifests,
        "causality": {
            "signal": (
                "One 00:00 UTC entry from exact completed 23:55 FX "
                "returns and a bounded prior DXY-session handoff"
            ),
            "dxy_maximum_age_minutes": int(
                cfg["sources"]["DXY"]["maximum_age_minutes"]
            ),
            "future_information_in_signal": False,
            "oracle_loaded_after_execution": True,
            "ml_used": False,
        },
        "outcome_blind_census": {
            **census,
            "passed": census_pass,
        },
        "development": {
            "passed": development_pass,
            "economics": development,
        },
        "walk_forward": {
            "admitted": admitted,
            "windows": window_results,
            "overall_economics": forward_economics,
            "overall_oracle_imitation": forward_imitation,
            "outcomes_by_exact_oracle_membership": (
                membership_breakdown
            ),
            "imitation_gate_passed": imitation_pass,
        },
        "all_history": {
            "economics": all_history,
            "top_5_percent_winners_removed": top_removed,
            "extra_half_pip_round_trip": stressed,
            "robustness_gate_passed": robustness_pass,
        },
        "verdict": (
            "The deterministic UTC-open vote passed every frozen gate; "
            "prospective confirmation is mandatory before any promotion."
            if admitted
            else "The deterministic UTC-open vote failed at least one "
            "frozen development, forward, imitation, or robustness gate."
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
        json.dumps(serialize(payload), indent=2), encoding="utf-8"
    )
