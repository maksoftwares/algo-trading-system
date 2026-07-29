from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

from .neutral_h4_quiet_state_transfer import profit_factor, sha256_file, summarize
from .neutral_macro_pressure_reversal import _json_safe


CLUSTER_FEATURES = (
    "range_atr",
    "atr_ratio_126",
    "efficiency_24",
    "side_return_6_atr",
    "side_return_24_atr",
    "side_prior24_location",
    "side_macro_pressure_clipped",
)

TIMESTAMP_COLUMNS = (
    "signal_time_utc",
    "entry_time_utc",
    "exit_time_utc",
    "macro_available_utc",
)


def load_candidates(source: dict[str, Any]) -> pd.DataFrame:
    path = Path(source["path"])
    if sha256_file(path) != source["sha256"]:
        raise RuntimeError("Frozen side-candidate checksum mismatch")
    frame = pd.read_csv(path)
    if len(frame) != int(source["expected_rows"]):
        raise RuntimeError("Frozen side-candidate row count mismatch")
    for column in TIMESTAMP_COLUMNS:
        frame[column] = pd.to_datetime(frame[column], utc=True, errors="raise")
    frame["target_hit"] = (
        frame["target_hit"].astype(str).str.lower().map({"true": True, "false": False})
    )
    if frame["target_hit"].isna().any():
        raise RuntimeError("Invalid target_hit values")
    side_counts = frame.groupby("signal_id")["direction"].nunique()
    if not side_counts.eq(2).all():
        raise RuntimeError("Every signal must have both frozen side outcomes")
    if set(frame["direction"]) != {"LONG", "SHORT"}:
        raise RuntimeError("Unexpected candidate directions")
    return frame.sort_values(["signal_time_utc", "direction"]).reset_index(drop=True)


def build_signal_frame(candidates: pd.DataFrame) -> pd.DataFrame:
    signals = candidates[candidates["direction"].eq("LONG")].copy()
    maximum_exit = candidates.groupby("signal_id")["exit_time_utc"].max()
    signals["both_sides_closed_utc"] = signals["signal_id"].map(maximum_exit)
    return signals.sort_values("signal_time_utc").reset_index(drop=True)


def expert_direction(row: pd.Series, expert: dict[str, Any]) -> str | None:
    value = float(row[expert["feature"]])
    threshold = float(expert["absolute_threshold"])
    if not math.isfinite(value) or abs(value) < threshold:
        return None
    positive_direction = str(expert["positive_direction"])
    if positive_direction not in {"LONG", "SHORT"}:
        raise RuntimeError(f"Invalid expert direction: {positive_direction}")
    if value > 0.0:
        return positive_direction
    return "SHORT" if positive_direction == "LONG" else "LONG"


def enforce_nonoverlap(trades: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    if trades.empty:
        return trades, 0
    kept: list[pd.Series] = []
    blocked_until = -1
    rejected = 0
    for _, row in trades.sort_values(["entry_time_utc", "signal_id"]).iterrows():
        if int(row["entry_index"]) <= blocked_until:
            rejected += 1
            continue
        kept.append(row)
        blocked_until = int(row["exit_index"])
    return pd.DataFrame(kept).reset_index(drop=True), rejected


def _lookup_outcomes(candidates: pd.DataFrame) -> dict[tuple[str, str], pd.Series]:
    return {
        (str(row["signal_id"]), str(row["direction"])): row
        for _, row in candidates.iterrows()
    }


def expert_trades(
    signals: pd.DataFrame,
    lookup: dict[tuple[str, str], pd.Series],
    expert: dict[str, Any],
) -> pd.DataFrame:
    records: list[pd.Series] = []
    for _, signal_row in signals.iterrows():
        direction = expert_direction(signal_row, expert)
        if direction is None:
            continue
        outcome = lookup.get((str(signal_row["signal_id"]), direction))
        if outcome is not None:
            records.append(outcome)
    return pd.DataFrame(records).reset_index(drop=True) if records else pd.DataFrame()


def _training_diagnostics(
    trades: pd.DataFrame,
    midpoint: pd.Timestamp,
    admission: dict[str, Any],
) -> dict[str, Any]:
    if trades.empty:
        return {
            "training_trades": 0,
            "training_early_trades": 0,
            "training_late_trades": 0,
            "training_profit_factor": 0.0,
            "training_stress_profit_factor": 0.0,
            "training_early_profit_factor": 0.0,
            "training_late_profit_factor": 0.0,
            "training_net_r": 0.0,
            "training_overlap_rejections": 0,
            "admitted": False,
        }
    nonoverlap, overlap_rejections = enforce_nonoverlap(trades)
    early = nonoverlap[nonoverlap["signal_time_utc"] < midpoint]
    late = nonoverlap[nonoverlap["signal_time_utc"] >= midpoint]
    base_pf = profit_factor(nonoverlap["r"]) if not nonoverlap.empty else 0.0
    stress_pf = (
        profit_factor(nonoverlap["stress_r"]) if not nonoverlap.empty else 0.0
    )
    early_pf = profit_factor(early["r"]) if not early.empty else 0.0
    late_pf = profit_factor(late["r"]) if not late.empty else 0.0
    passed = (
        len(nonoverlap) >= int(admission["minimum_training_trades"])
        and len(early) >= int(admission["minimum_each_half_trades"])
        and len(late) >= int(admission["minimum_each_half_trades"])
        and base_pf >= float(admission["minimum_training_profit_factor"])
        and stress_pf >= float(admission["minimum_training_stress_profit_factor"])
        and early_pf
        > float(admission["minimum_each_half_profit_factor_exclusive"])
        and late_pf
        > float(admission["minimum_each_half_profit_factor_exclusive"])
        and float(nonoverlap["r"].sum())
        > float(admission["minimum_training_net_r_exclusive"])
    )
    return {
        "training_trades": len(nonoverlap),
        "training_early_trades": len(early),
        "training_late_trades": len(late),
        "training_profit_factor": base_pf,
        "training_stress_profit_factor": stress_pf,
        "training_early_profit_factor": early_pf,
        "training_late_profit_factor": late_pf,
        "training_net_r": float(nonoverlap["r"].sum()) if not nonoverlap.empty else 0.0,
        "training_overlap_rejections": overlap_rejections,
        "admitted": passed,
    }


def _rank_clusters(
    raw_labels: np.ndarray, standardized_centers: np.ndarray
) -> tuple[np.ndarray, dict[int, int]]:
    order = sorted(
        range(len(standardized_centers)),
        key=lambda index: tuple(float(value) for value in standardized_centers[index]),
    )
    raw_to_rank = {raw: rank + 1 for rank, raw in enumerate(order)}
    ranked = np.asarray([raw_to_rank[int(value)] for value in raw_labels], dtype=int)
    return ranked, raw_to_rank


def _fit_month(
    month_start: pd.Timestamp,
    month_end: pd.Timestamp,
    signals: pd.DataFrame,
    candidates: pd.DataFrame,
    config: dict[str, Any],
) -> tuple[pd.DataFrame, list[dict[str, Any]], dict[str, Any]]:
    model = config["model"]
    train_start = month_start - pd.DateOffset(
        years=int(model["trailing_training_years"])
    )
    train_signals = signals[
        (signals["signal_time_utc"] >= train_start)
        & (signals["both_sides_closed_utc"] < month_start)
    ].copy()
    score_signals = signals[
        (signals["signal_time_utc"] >= month_start)
        & (signals["signal_time_utc"] < month_end)
    ].copy()
    month_record: dict[str, Any] = {
        "month": month_start.strftime("%Y-%m"),
        "training_start_utc": train_start.isoformat(),
        "training_cutoff_utc": month_start.isoformat(),
        "training_signals": len(train_signals),
        "score_signals": len(score_signals),
        "admitted_subregimes": 0,
        "selected_signals": 0,
        "status": "INSUFFICIENT_TRAINING_OR_NO_SCORE_SIGNALS",
    }
    if (
        len(train_signals) < int(model["minimum_training_signals"])
        or score_signals.empty
    ):
        return pd.DataFrame(), [], month_record

    scaler = StandardScaler()
    training_matrix = scaler.fit_transform(train_signals[list(CLUSTER_FEATURES)])
    clusterer = KMeans(
        n_clusters=int(model["subregime_count"]),
        n_init=int(model["kmeans_n_init"]),
        random_state=int(model["random_state"]),
    )
    raw_training_labels = clusterer.fit_predict(training_matrix)
    training_labels, raw_to_rank = _rank_clusters(
        raw_training_labels, clusterer.cluster_centers_
    )
    train_signals["subregime"] = training_labels
    raw_score_labels = clusterer.predict(
        scaler.transform(score_signals[list(CLUSTER_FEATURES)])
    )
    score_signals["subregime"] = [
        raw_to_rank[int(value)] for value in raw_score_labels
    ]

    training_ids = set(train_signals["signal_id"])
    training_candidates = candidates[
        candidates["signal_id"].isin(training_ids)
        & (candidates["exit_time_utc"] < month_start)
    ]
    training_lookup = _lookup_outcomes(training_candidates)
    score_lookup = _lookup_outcomes(
        candidates[candidates["signal_id"].isin(set(score_signals["signal_id"]))]
    )
    midpoint = train_start + (month_start - train_start) / 2
    admissions: list[dict[str, Any]] = []
    selected_rows: list[pd.Series] = []

    for subregime in range(1, int(model["subregime_count"]) + 1):
        cluster_training = train_signals[train_signals["subregime"].eq(subregime)]
        eligible_experts: list[dict[str, Any]] = []
        for expert in config["experts"]:
            trades = expert_trades(cluster_training, training_lookup, expert)
            diagnostics = _training_diagnostics(
                trades, midpoint, config["admission_gates"]
            )
            record = {
                "month": month_start.strftime("%Y-%m"),
                "subregime": subregime,
                "expert_id": expert["expert_id"],
                **diagnostics,
            }
            admissions.append(record)
            if diagnostics["admitted"]:
                eligible_experts.append({**record, "expert": expert})
        if not eligible_experts:
            continue
        chosen = max(
            eligible_experts,
            key=lambda item: (
                float(item["training_stress_profit_factor"]),
                min(
                    float(item["training_early_profit_factor"]),
                    float(item["training_late_profit_factor"]),
                ),
                int(item["training_trades"]),
                str(item["expert_id"]),
            ),
        )
        cluster_score = score_signals[score_signals["subregime"].eq(subregime)]
        for _, signal_row in cluster_score.iterrows():
            direction = expert_direction(signal_row, chosen["expert"])
            if direction is None:
                continue
            outcome = score_lookup.get((str(signal_row["signal_id"]), direction))
            if outcome is None:
                continue
            selected = outcome.copy()
            selected["subregime"] = subregime
            selected["expert_id"] = chosen["expert_id"]
            selected["training_profit_factor"] = chosen["training_profit_factor"]
            selected["training_stress_profit_factor"] = chosen[
                "training_stress_profit_factor"
            ]
            selected["training_early_profit_factor"] = chosen[
                "training_early_profit_factor"
            ]
            selected["training_late_profit_factor"] = chosen[
                "training_late_profit_factor"
            ]
            selected_rows.append(selected)

    selected_frame = (
        pd.DataFrame(selected_rows).reset_index(drop=True)
        if selected_rows
        else pd.DataFrame()
    )
    month_record.update(
        {
            "admitted_subregimes": len(
                {
                    int(item["subregime"])
                    for item in admissions
                    if item["admitted"]
                }
            ),
            "selected_signals": len(selected_frame),
            "status": "PAST_ONLY_SUBREGIME_EXPERTS_FIT",
        }
    )
    return selected_frame, admissions, month_record


def walkforward_select(
    candidates: pd.DataFrame, config: dict[str, Any]
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    signals = build_signal_frame(candidates)
    start = pd.Timestamp(config["model"]["evaluation_start_utc"])
    end = pd.Timestamp(config["model"]["evaluation_end_exclusive_utc"])
    selected_parts: list[pd.DataFrame] = []
    admissions: list[dict[str, Any]] = []
    months: list[dict[str, Any]] = []
    for month_start in pd.date_range(start, end, freq="MS", inclusive="left"):
        month_end = min(month_start + pd.offsets.MonthBegin(1), end)
        selected, month_admissions, month_record = _fit_month(
            month_start, month_end, signals, candidates, config
        )
        if not selected.empty:
            selected_parts.append(selected)
        admissions.extend(month_admissions)
        months.append(month_record)
    selections = (
        pd.concat(selected_parts, ignore_index=True)
        if selected_parts
        else pd.DataFrame()
    )
    return selections, pd.DataFrame(admissions), pd.DataFrame(months)


def _window_metrics(
    trades: pd.DataFrame, windows: dict[str, list[str]]
) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for name, (start, end) in windows.items():
        subset = (
            trades[
                (trades["entry_time_utc"] >= pd.Timestamp(start))
                & (trades["entry_time_utc"] < pd.Timestamp(end))
            ]
            if not trades.empty
            else trades
        )
        result[name] = summarize(subset)
    return result


def _concentration_share(trades: pd.DataFrame, column: str) -> float:
    if trades.empty:
        return 0.0
    return float(trades[column].value_counts(normalize=True).max())


def evaluate_gates(
    trades: pd.DataFrame,
    windows: dict[str, dict[str, Any]],
    config: dict[str, Any],
) -> dict[str, bool]:
    gates = config["historical_quality_gates"]
    full = windows["FULL_WALKFORWARD"]
    latest = windows["LATEST_12_MONTHS"]
    blocks = (
        "OOS_2020_2021",
        "OOS_2022_2023",
        "OOS_2024_2025",
        "OOS_2026_H1",
    )
    direction_metrics = {
        direction: summarize(trades[trades["direction"].eq(direction)])
        for direction in ("LONG", "SHORT")
    }
    return {
        "minimum_trades": full["trades"] >= int(gates["minimum_trades"]),
        "win_rate": float(gates["minimum_win_rate_inclusive"])
        <= full["win_rate"]
        <= float(gates["maximum_win_rate_inclusive"]),
        "payoff": float(gates["minimum_payoff_inclusive"])
        <= full["realized_payoff_ratio"]
        <= float(gates["maximum_payoff_inclusive"]),
        "profit_factor": full["profit_factor"]
        >= float(gates["minimum_profit_factor"]),
        "stressed_profit_factor": full["stress_profit_factor"]
        >= float(gates["minimum_stressed_profit_factor"]),
        "chronological_blocks": all(
            windows[name]["profit_factor"]
            > float(gates["minimum_each_block_profit_factor_exclusive"])
            for name in blocks
        ),
        "latest_12_month_profit_factor": latest["profit_factor"]
        >= float(gates["minimum_latest_12_month_profit_factor"]),
        "latest_12_month_net_r": latest["net_r"]
        > float(gates["minimum_latest_12_month_net_r_exclusive"]),
        "positive_active_month_share": full["positive_active_month_share"]
        >= float(gates["minimum_positive_active_month_share"]),
        "winner_concentration": full["top_5pct_winners_removed_profit_factor"]
        >= float(gates["minimum_top_5pct_winners_removed_profit_factor"]),
        "drawdown": full["maximum_drawdown_r"]
        <= float(gates["maximum_drawdown_r"]),
        "both_directions_sample": all(
            metrics["trades"] >= int(gates["minimum_each_direction_trades"])
            for metrics in direction_metrics.values()
        ),
        "both_directions_not_materially_negative": all(
            metrics["profit_factor"]
            >= float(gates["minimum_each_direction_profit_factor"])
            for metrics in direction_metrics.values()
        ),
        "expert_concentration": _concentration_share(trades, "expert_id")
        <= float(gates["maximum_single_expert_trade_share"]),
        "subregime_concentration": _concentration_share(trades, "subregime")
        <= float(gates["maximum_single_subregime_trade_share"]),
    }


def run(config_path: Path, output_dir: Path) -> dict[str, Any]:
    config_bytes = config_path.read_bytes()
    config = json.loads(config_bytes)
    if tuple(config["model"]["cluster_features"]) != CLUSTER_FEATURES:
        raise RuntimeError("Frozen cluster feature order mismatch")
    candidates = load_candidates(config["source"])
    selections, admissions, monthly = walkforward_select(candidates, config)
    trades, overlap_rejections = enforce_nonoverlap(selections)
    windows = _window_metrics(trades, config["reporting_windows"])
    gates = evaluate_gates(trades, windows, config)
    passed = all(gates.values())

    expert_metrics = {
        expert["expert_id"]: summarize(
            trades[trades["expert_id"].eq(expert["expert_id"])]
        )
        for expert in config["experts"]
    } if not trades.empty else {
        expert["expert_id"]: summarize(trades) for expert in config["experts"]
    }
    subregime_metrics = {
        str(subregime): summarize(
            trades[trades["subregime"].eq(subregime)]
        )
        for subregime in range(1, int(config["model"]["subregime_count"]) + 1)
    } if not trades.empty else {
        str(subregime): summarize(trades)
        for subregime in range(1, int(config["model"]["subregime_count"]) + 1)
    }
    direction_metrics = {
        direction: summarize(trades[trades["direction"].eq(direction)])
        for direction in ("LONG", "SHORT")
    } if not trades.empty else {
        direction: summarize(trades) for direction in ("LONG", "SHORT")
    }

    output_dir.mkdir(parents=True, exist_ok=True)
    selections.to_csv(
        output_dir / "MODEL_SELECTIONS.csv", index=False, lineterminator="\n"
    )
    trades.to_csv(output_dir / "TRADES.csv", index=False, lineterminator="\n")
    admissions.to_csv(
        output_dir / "MONTHLY_ADMISSIONS.csv", index=False, lineterminator="\n"
    )
    monthly.to_csv(
        output_dir / "MONTHLY_SUBREGIMES.csv", index=False, lineterminator="\n"
    )
    result = {
        "schema_version": "eurusd_neutral_subregime_experts_result_v1",
        "frozen_config_sha256": hashlib.sha256(config_bytes).hexdigest(),
        "source_sha256": config["source"]["sha256"],
        "source_rows": len(candidates),
        "model_selections_before_overlap": len(selections),
        "overlap_rejections": overlap_rejections,
        "trades": len(trades),
        "windows": windows,
        "expert_metrics": expert_metrics,
        "subregime_metrics": subregime_metrics,
        "direction_metrics": direction_metrics,
        "gate_results": gates,
        "all_historical_quality_gates_passed": passed,
        "retrospective_causal_not_pristine_oos": True,
        "broker_action_allowed": False,
        "status": (
            "HISTORICAL_SUBREGIME_EXPERT_PASS_REQUIRES_PROSPECTIVE_CONFIRMATION"
            if passed
            else "REJECTED_NEUTRAL_SUBREGIME_EXPERTS"
        ),
    }
    (output_dir / "RESULT.json").write_text(
        json.dumps(_json_safe(result), indent=2, allow_nan=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return result
