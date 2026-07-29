from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

PACKAGE_ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = (
    PACKAGE_ROOT / "config" / "frozen_neutral_online_expert_aggregation.json"
)
LOCK_PATH = (
    PACKAGE_ROOT
    / "EURUSD_NEUTRAL_ONLINE_EXPERT_AGGREGATION_PREREG_"
    "2026_07_29.sha256.json"
)
OUTPUT_ROOT = PACKAGE_ROOT / "outputs" / "neutral_online_expert_aggregation"


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_config() -> dict[str, Any]:
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def verify_lock() -> dict[str, str]:
    lock = json.loads(LOCK_PATH.read_text(encoding="utf-8"))
    if (
        lock.get("frozen_before_combined_outcome") is not True
        or lock.get("oracle_decision_use_allowed") is not False
        or lock.get("broker_action_allowed") is not False
    ):
        raise RuntimeError("Online expert aggregation lock is incomplete")
    checked: dict[str, str] = {}
    for relative, expected in lock["files"].items():
        actual = sha256_file(PACKAGE_ROOT / relative)
        if actual != expected:
            raise RuntimeError(f"Online expert aggregation drift: {relative}")
        checked[relative] = actual
    return checked


def _utc_series(values: pd.Series) -> pd.Series:
    return pd.to_datetime(values, utc=True, errors="raise")


def load_expert_ledgers(
    cfg: dict[str, Any] | None = None,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    config = load_config() if cfg is None else cfg
    frames: list[pd.DataFrame] = []
    census: dict[str, Any] = {}
    for expert in config["experts"]:
        expert_id = str(expert["expert_id"])
        path = PACKAGE_ROOT / expert["path"]
        actual_hash = sha256_file(path)
        if actual_hash != expert["sha256"]:
            raise RuntimeError(f"Expert ledger hash drift: {expert_id}")
        frame = pd.read_csv(path)
        required = {
            "entry_time_utc",
            "exit_time_utc",
            "side",
            "r",
            config["policy"]["stress_outcome_column"],
        }
        missing = sorted(required - set(frame.columns))
        if missing:
            raise RuntimeError(f"{expert_id} missing columns: {missing}")
        frame["entry_time_utc"] = _utc_series(frame["entry_time_utc"])
        frame["exit_time_utc"] = _utc_series(frame["exit_time_utc"])
        frame["r"] = pd.to_numeric(frame["r"], errors="raise")
        stress_column = str(config["policy"]["stress_outcome_column"])
        frame[stress_column] = pd.to_numeric(
            frame[stress_column], errors="raise"
        )
        if (
            not np.isfinite(frame[["r", stress_column]].to_numpy()).all()
            or frame["exit_time_utc"].lt(frame["entry_time_utc"]).any()
            or not frame["side"].isin(["LONG", "SHORT"]).all()
        ):
            raise RuntimeError(f"Invalid expert ledger: {expert_id}")
        frame = frame.copy()
        frame["expert_id"] = expert_id
        frame["mechanism"] = str(expert["mechanism"])
        frame["source_row"] = np.arange(len(frame), dtype=np.int64)
        frames.append(frame)
        census[expert_id] = {
            "rows": len(frame),
            "first_entry_utc": frame["entry_time_utc"].min(),
            "last_entry_utc": frame["entry_time_utc"].max(),
            "sha256": actual_hash,
        }
    combined = pd.concat(frames, ignore_index=True, sort=False)
    combined = combined.sort_values(
        ["entry_time_utc", "expert_id", "source_row"]
    ).reset_index(drop=True)
    return combined, census


def weighted_expert_score(
    expert_history: pd.DataFrame,
    *,
    decision_time_utc: Any,
    half_life_days: int,
    minimum_lifetime_closed_trades: int,
    minimum_effective_closed_trades: float,
) -> dict[str, Any]:
    decision = pd.Timestamp(decision_time_utc)
    if decision.tzinfo is None:
        raise ValueError("Decision time must be timezone-aware")
    decision = decision.tz_convert("UTC")
    known = expert_history[
        expert_history["exit_time_utc"].lt(decision)
    ].copy()
    lifetime = len(known)
    if lifetime:
        age_days = (
            decision - known["exit_time_utc"]
        ).dt.total_seconds().to_numpy() / 86400.0
        weights = np.exp2(-age_days / float(half_life_days))
        effective = float(weights.sum())
        weighted_mean = float(np.average(known["r"], weights=weights))
    else:
        effective = 0.0
        weighted_mean = 0.0
    eligible = bool(
        lifetime >= minimum_lifetime_closed_trades
        and effective >= minimum_effective_closed_trades
        and weighted_mean > 0.0
    )
    return {
        "lifetime_closed_trades": lifetime,
        "effective_closed_trades": effective,
        "weighted_mean_r": weighted_mean,
        "eligible": eligible,
        "latest_known_exit_utc": (
            known["exit_time_utc"].max() if lifetime else pd.NaT
        ),
    }


def select_online_trades(
    all_trades: pd.DataFrame,
    *,
    config: dict[str, Any],
    half_life_days: int,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    policy = config["policy"]
    start = pd.Timestamp(config["evaluation_start_utc"])
    end = pd.Timestamp(config["evaluation_end_utc"])
    histories = {
        expert_id: frame.sort_values("exit_time_utc")
        for expert_id, frame in all_trades.groupby("expert_id", sort=True)
    }
    candidate_rows = all_trades[
        all_trades["entry_time_utc"].between(start, end, inclusive="both")
    ]
    selected: list[dict[str, Any]] = []
    decisions: list[dict[str, Any]] = []
    open_until = pd.Timestamp.min.tz_localize("UTC")
    traded_dates: set[str] = set()

    for entry_time, clock in candidate_rows.groupby(
        "entry_time_utc", sort=True
    ):
        date_key = entry_time.strftime("%Y-%m-%d")
        base_decision = {
            "entry_time_utc": entry_time,
            "candidate_experts": int(clock["expert_id"].nunique()),
            "candidate_rows": len(clock),
            "half_life_days": int(half_life_days),
        }
        if date_key in traded_dates:
            decisions.append(
                {**base_decision, "status": "CASH_DAILY_LIMIT"}
            )
            continue
        if entry_time < open_until:
            decisions.append(
                {
                    **base_decision,
                    "status": "CASH_PRIOR_POSITION_OPEN",
                    "prior_position_exit_utc": open_until,
                }
            )
            continue
        scored: list[tuple[dict[str, Any], pd.Series]] = []
        for _, candidate in clock.iterrows():
            expert_id = str(candidate["expert_id"])
            score = weighted_expert_score(
                histories[expert_id],
                decision_time_utc=entry_time,
                half_life_days=half_life_days,
                minimum_lifetime_closed_trades=int(
                    policy["minimum_lifetime_closed_trades"]
                ),
                minimum_effective_closed_trades=float(
                    policy["minimum_effective_closed_trades"]
                ),
            )
            if score["eligible"]:
                scored.append((score, candidate))
        if not scored:
            decisions.append(
                {**base_decision, "status": "CASH_NO_POSITIVE_ELIGIBLE_EXPERT"}
            )
            continue
        scored.sort(
            key=lambda pair: (
                -float(pair[0]["weighted_mean_r"]),
                -float(pair[0]["effective_closed_trades"]),
                str(pair[1]["expert_id"]),
                int(pair[1]["source_row"]),
            )
        )
        score, chosen = scored[0]
        record = chosen.to_dict()
        record.update(
            {
                "selection_half_life_days": int(half_life_days),
                "selection_weighted_mean_r": score["weighted_mean_r"],
                "selection_effective_closed_trades": score[
                    "effective_closed_trades"
                ],
                "selection_lifetime_closed_trades": score[
                    "lifetime_closed_trades"
                ],
                "selection_latest_known_exit_utc": score[
                    "latest_known_exit_utc"
                ],
            }
        )
        selected.append(record)
        traded_dates.add(date_key)
        open_until = pd.Timestamp(chosen["exit_time_utc"])
        decisions.append(
            {
                **base_decision,
                "status": "SELECTED",
                "selected_expert_id": str(chosen["expert_id"]),
                "selected_source_row": int(chosen["source_row"]),
                "selected_side": str(chosen["side"]),
                "selected_exit_time_utc": open_until,
                "selection_weighted_mean_r": score["weighted_mean_r"],
                "selection_effective_closed_trades": score[
                    "effective_closed_trades"
                ],
                "selection_lifetime_closed_trades": score[
                    "lifetime_closed_trades"
                ],
                "selection_latest_known_exit_utc": score[
                    "latest_known_exit_utc"
                ],
            }
        )
    selected_frame = pd.DataFrame(selected)
    decisions_frame = pd.DataFrame(decisions)
    if not selected_frame.empty:
        selected_frame = selected_frame.sort_values(
            ["entry_time_utc", "expert_id", "source_row"]
        ).reset_index(drop=True)
    return selected_frame, decisions_frame


def payoff_metrics(frame: pd.DataFrame, column: str = "r") -> dict[str, Any]:
    if frame.empty:
        return {
            "trades": 0,
            "wins": 0,
            "losses": 0,
            "win_rate": 0.0,
            "average_win_r": 0.0,
            "average_loss_r": 0.0,
            "realized_payoff_ratio": 0.0,
            "profit_factor": 0.0,
            "net_r": 0.0,
            "expectancy_r": 0.0,
            "max_drawdown_r": 0.0,
        }
    values = frame[column].astype(float)
    wins = values[values > 0.0]
    losses = values[values <= 0.0]
    gross_profit = float(wins.sum())
    gross_loss = float(-losses.sum())
    average_win = float(wins.mean()) if len(wins) else 0.0
    average_loss = float(-losses.mean()) if len(losses) else 0.0
    equity = values.cumsum()
    drawdown = equity.cummax().clip(lower=0.0) - equity
    return {
        "trades": len(values),
        "wins": len(wins),
        "losses": len(losses),
        "win_rate": float(len(wins) / len(values)),
        "average_win_r": average_win,
        "average_loss_r": average_loss,
        "realized_payoff_ratio": (
            average_win / average_loss if average_loss else math.inf
        ),
        "profit_factor": (
            gross_profit / gross_loss if gross_loss else math.inf
        ),
        "net_r": float(values.sum()),
        "expectancy_r": float(values.mean()),
        "max_drawdown_r": float(drawdown.max()),
    }


def remove_top_winners(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return frame.copy()
    count = max(1, math.ceil(len(frame) * 0.05))
    drop = frame.nlargest(count, "r").index
    return frame.drop(index=drop).copy()


def attach_oracle_matches(
    selected: pd.DataFrame,
    *,
    config: dict[str, Any],
) -> tuple[pd.DataFrame, dict[str, Any]]:
    oracle_cfg = config["oracle"]
    path = PACKAGE_ROOT / oracle_cfg["path"]
    if sha256_file(path) != oracle_cfg["sha256"]:
        raise RuntimeError("Evaluation-only oracle hash drift")
    oracle = pd.read_csv(path)
    oracle = oracle[oracle["regime"].eq(oracle_cfg["required_regime"])].copy()
    oracle["entry_time_utc"] = _utc_series(oracle["entry_time_utc"])
    tolerance = pd.Timedelta(
        minutes=int(oracle_cfg["same_side_tolerance_minutes"])
    )
    records: list[dict[str, Any]] = []
    for _, trade in selected.iterrows():
        candidates = oracle[
            oracle["side"].eq(trade["side"])
            & oracle["entry_time_utc"].between(
                trade["entry_time_utc"] - tolerance,
                trade["entry_time_utc"] + tolerance,
                inclusive="both",
            )
        ].copy()
        if candidates.empty:
            records.append(
                {
                    "expert_id": trade["expert_id"],
                    "source_row": int(trade["source_row"]),
                    "entry_time_utc": trade["entry_time_utc"],
                    "side": trade["side"],
                    "oracle_match": False,
                    "oracle_entry_time_utc": pd.NaT,
                    "absolute_minutes": np.nan,
                }
            )
            continue
        candidates["absolute_minutes"] = (
            candidates["entry_time_utc"] - trade["entry_time_utc"]
        ).abs().dt.total_seconds() / 60.0
        match = candidates.sort_values(
            ["absolute_minutes", "entry_time_utc", "oracle_trade_number"]
        ).iloc[0]
        records.append(
            {
                "expert_id": trade["expert_id"],
                "source_row": int(trade["source_row"]),
                "entry_time_utc": trade["entry_time_utc"],
                "side": trade["side"],
                "oracle_match": True,
                "oracle_entry_time_utc": match["entry_time_utc"],
                "absolute_minutes": float(match["absolute_minutes"]),
            }
        )
    matches = pd.DataFrame(records)
    matched = int(matches["oracle_match"].sum()) if not matches.empty else 0
    return matches, {
        "neutral_oracle_rows": len(oracle),
        "selected_trades": len(selected),
        "same_side_matches_15m": matched,
        "same_side_precision_15m": (
            float(matched / len(selected)) if len(selected) else 0.0
        ),
        "oracle_used_for_decisions": False,
    }


def _period(
    frame: pd.DataFrame, bounds: list[str]
) -> pd.DataFrame:
    start, end = (pd.Timestamp(value) for value in bounds)
    return frame[
        frame["entry_time_utc"].between(start, end, inclusive="both")
    ]


def summarize_policy(
    selected: pd.DataFrame,
    *,
    config: dict[str, Any],
    include_gates: bool,
) -> tuple[dict[str, Any], pd.DataFrame]:
    stress_column = str(config["policy"]["stress_outcome_column"])
    overall = payoff_metrics(selected)
    stressed = payoff_metrics(selected, stress_column)
    top_removed = payoff_metrics(remove_top_winners(selected))
    windows = {
        name: payoff_metrics(_period(selected, bounds))
        for name, bounds in config["reporting_windows"].items()
    }
    sides = {
        side: payoff_metrics(selected[selected["side"].eq(side)])
        for side in ("LONG", "SHORT")
    }
    experts = {
        expert_id: payoff_metrics(block)
        for expert_id, block in selected.groupby("expert_id", sort=True)
    }
    matches, oracle_metrics = attach_oracle_matches(
        selected, config=config
    )
    summary: dict[str, Any] = {
        "overall": overall,
        "extra_half_pip": stressed,
        "top_5pct_winners_removed": top_removed,
        "windows": windows,
        "by_side": sides,
        "by_selected_expert": experts,
        "oracle_resemblance": oracle_metrics,
    }
    if include_gates:
        gates = config["research_gates"]
        gate_results = {
            "minimum_selected_trades": overall["trades"]
            >= int(gates["minimum_selected_trades"]),
            "win_rate": float(gates["minimum_win_rate"])
            <= overall["win_rate"]
            <= float(gates["maximum_win_rate"]),
            "realized_payoff_ratio": overall["realized_payoff_ratio"]
            >= float(gates["minimum_realized_payoff_ratio"]),
            "profit_factor": overall["profit_factor"]
            >= float(gates["minimum_profit_factor"]),
            "each_full_year_profit_factor": all(
                windows[name]["profit_factor"]
                > float(
                    gates["minimum_each_full_year_profit_factor_exclusive"]
                )
                for name in ("OOS_2023", "OOS_2024", "OOS_2025")
            ),
            "latest_six_month_profit_factor": windows[
                "LATEST_SIX_MONTHS"
            ]["profit_factor"]
            > float(
                gates[
                    "minimum_latest_six_month_profit_factor_exclusive"
                ]
            ),
            "extra_half_pip_profit_factor": stressed["profit_factor"]
            > float(
                gates[
                    "minimum_extra_half_pip_profit_factor_exclusive"
                ]
            ),
            "top_5pct_winners_removed_profit_factor": top_removed[
                "profit_factor"
            ]
            > float(
                gates[
                    "minimum_top_5pct_winners_removed_profit_factor_exclusive"
                ]
            ),
            "both_sides": all(
                sides[side]["trades"]
                >= int(gates["minimum_trades_each_side"])
                for side in ("LONG", "SHORT")
            ),
            "maximum_drawdown": overall["max_drawdown_r"]
            <= float(gates["maximum_drawdown_r"]),
            "oracle_precision": oracle_metrics["same_side_precision_15m"]
            >= float(gates["minimum_same_side_oracle_precision_15m"]),
        }
        summary["gate_results"] = gate_results
        summary["all_research_gates_passed"] = bool(
            all(gate_results.values())
        )
    return summary, matches


def run_online_expert_aggregation() -> tuple[
    dict[str, Any], dict[str, pd.DataFrame]
]:
    verify_lock()
    config = load_config()
    all_trades, input_census = load_expert_ledgers(config)
    primary_half_life = int(
        config["policy"]["primary_half_life_calendar_days"]
    )
    primary, decisions = select_online_trades(
        all_trades,
        config=config,
        half_life_days=primary_half_life,
    )
    primary_summary, primary_matches = summarize_policy(
        primary, config=config, include_gates=True
    )
    sensitivities: dict[str, Any] = {}
    sensitivity_frames: list[pd.DataFrame] = []
    for half_life in config["policy"]["sensitivity_half_life_calendar_days"]:
        frame, _ = select_online_trades(
            all_trades,
            config=config,
            half_life_days=int(half_life),
        )
        summary, _matches = summarize_policy(
            frame, config=config, include_gates=False
        )
        sensitivities[str(half_life)] = summary
        if not frame.empty:
            sensitivity_frames.append(frame)
    sensitivity = (
        pd.concat(sensitivity_frames, ignore_index=True, sort=False)
        if sensitivity_frames
        else pd.DataFrame()
    )
    passed = bool(primary_summary["all_research_gates_passed"])
    result = {
        "schema_version": "eurusd_neutral_online_expert_aggregation_result_v1",
        "status": (
            "RESEARCH_GATES_PASS_REQUIRES_SEPARATE_PROSPECTIVE_FREEZE"
            if passed
            else "REJECTED_EXACT_ONLINE_ALLOCATOR"
        ),
        "frozen_at_utc": config["frozen_at_utc"],
        "retrospective_causal_not_pristine_oos": True,
        "combined_outcome_opened_after_freeze": True,
        "primary_half_life_days": primary_half_life,
        "input_census": input_census,
        "primary": primary_summary,
        "sensitivities_not_selectable": sensitivities,
        "historical_pass_can_authorize_demo": False,
        "broker_action_allowed": False,
    }
    return result, {
        "PRIMARY_SELECTED_TRADES": primary,
        "PRIMARY_DECISIONS": decisions,
        "PRIMARY_ORACLE_MATCHES": primary_matches,
        "SENSITIVITY_SELECTED_TRADES": sensitivity,
    }


def _safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_safe(item) for item in value]
    if isinstance(value, (pd.Timestamp,)):
        return None if pd.isna(value) else value.isoformat()
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        return float(value)
    if isinstance(value, float) and not math.isfinite(value):
        return None
    return value


def write_result(
    result: dict[str, Any], artifacts: dict[str, pd.DataFrame]
) -> None:
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(_safe(result), indent=2, sort_keys=True) + "\n"
    (OUTPUT_ROOT / "RESULT.json").write_text(payload, encoding="utf-8")
    for name, frame in artifacts.items():
        frame.to_csv(OUTPUT_ROOT / f"{name}.csv", index=False)


__all__ = [
    "OUTPUT_ROOT",
    "attach_oracle_matches",
    "load_expert_ledgers",
    "payoff_metrics",
    "run_online_expert_aggregation",
    "select_online_trades",
    "verify_lock",
    "weighted_expert_score",
    "write_result",
]
