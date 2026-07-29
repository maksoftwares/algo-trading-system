from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

from .neutral_h4_quiet_state_transfer import summarize
from .neutral_macro_pressure_reversal import _json_safe
from .neutral_subregime_consensus import consensus_direction, evaluate_gates
from .neutral_subregime_experts import (
    CLUSTER_FEATURES,
    _lookup_outcomes,
    _rank_clusters,
    _training_diagnostics,
    _window_metrics,
    build_signal_frame,
    enforce_nonoverlap,
    expert_direction,
    expert_trades,
    load_candidates,
)


def consensus_trades(
    signals: pd.DataFrame,
    lookup: dict[tuple[str, str], pd.Series],
    admitted_experts: list[dict[str, Any]],
    model: dict[str, Any],
) -> pd.DataFrame:
    records: list[pd.Series] = []
    for _, signal_row in signals.iterrows():
        votes: list[dict[str, str]] = []
        for admitted in admitted_experts:
            direction = expert_direction(signal_row, admitted["expert"])
            if direction is not None:
                votes.append(
                    {
                        "direction": direction,
                        "expert_id": str(admitted["expert_id"]),
                        "mechanism_group": str(admitted["mechanism_group"]),
                    }
                )
        direction, _ = consensus_direction(
            votes,
            int(model["minimum_agreeing_experts"]),
            int(model["minimum_agreeing_mechanism_groups"]),
        )
        if direction is None:
            continue
        outcome = lookup.get((str(signal_row["signal_id"]), direction))
        if outcome is not None:
            records.append(outcome)
    return pd.DataFrame(records).reset_index(drop=True) if records else pd.DataFrame()


def _fit_month(
    month_start: pd.Timestamp,
    month_end: pd.Timestamp,
    signals: pd.DataFrame,
    candidates: pd.DataFrame,
    config: dict[str, Any],
) -> tuple[
    pd.DataFrame,
    list[dict[str, Any]],
    list[dict[str, Any]],
    dict[str, Any],
]:
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
        "validated_composite_subregimes": 0,
        "selected_signals": 0,
        "status": "INSUFFICIENT_TRAINING_OR_NO_SCORE_SIGNALS",
    }
    if (
        len(train_signals) < int(model["minimum_training_signals"])
        or score_signals.empty
    ):
        return pd.DataFrame(), [], [], month_record

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
    individual_admissions: list[dict[str, Any]] = []
    composite_admissions: list[dict[str, Any]] = []
    selected_rows: list[pd.Series] = []

    for subregime in range(1, int(model["subregime_count"]) + 1):
        cluster_training = train_signals[train_signals["subregime"].eq(subregime)]
        admitted_experts: list[dict[str, Any]] = []
        for expert in config["experts"]:
            trades = expert_trades(cluster_training, training_lookup, expert)
            diagnostics = _training_diagnostics(
                trades, midpoint, config["admission_gates"]
            )
            record = {
                "month": month_start.strftime("%Y-%m"),
                "subregime": subregime,
                "expert_id": expert["expert_id"],
                "mechanism_group": expert["mechanism_group"],
                **diagnostics,
            }
            individual_admissions.append(record)
            if diagnostics["admitted"]:
                admitted_experts.append({**record, "expert": expert})

        historical_consensus = consensus_trades(
            cluster_training, training_lookup, admitted_experts, model
        )
        composite_diagnostics = _training_diagnostics(
            historical_consensus,
            midpoint,
            config["composite_admission_gates"],
        )
        composite_record = {
            "month": month_start.strftime("%Y-%m"),
            "subregime": subregime,
            "admitted_individual_experts": len(admitted_experts),
            **composite_diagnostics,
        }
        composite_admissions.append(composite_record)
        if not composite_diagnostics["admitted"]:
            continue

        cluster_score = score_signals[score_signals["subregime"].eq(subregime)]
        for _, signal_row in cluster_score.iterrows():
            votes: list[dict[str, str]] = []
            for admitted in admitted_experts:
                direction = expert_direction(signal_row, admitted["expert"])
                if direction is not None:
                    votes.append(
                        {
                            "direction": direction,
                            "expert_id": str(admitted["expert_id"]),
                            "mechanism_group": str(admitted["mechanism_group"]),
                        }
                    )
            direction, agreeing = consensus_direction(
                votes,
                int(model["minimum_agreeing_experts"]),
                int(model["minimum_agreeing_mechanism_groups"]),
            )
            if direction is None:
                continue
            outcome = score_lookup.get((str(signal_row["signal_id"]), direction))
            if outcome is None:
                continue
            selected = outcome.copy()
            selected["subregime"] = subregime
            selected["vote_count"] = len(agreeing)
            selected["vote_experts"] = "|".join(
                sorted(vote["expert_id"] for vote in agreeing)
            )
            selected["vote_mechanism_groups"] = "|".join(
                sorted({vote["mechanism_group"] for vote in agreeing})
            )
            selected["consensus_signature"] = (
                f"{direction}:"
                + "|".join(sorted(vote["expert_id"] for vote in agreeing))
            )
            selected["training_consensus_profit_factor"] = composite_diagnostics[
                "training_profit_factor"
            ]
            selected["training_consensus_stress_profit_factor"] = (
                composite_diagnostics["training_stress_profit_factor"]
            )
            selected["training_consensus_early_profit_factor"] = (
                composite_diagnostics["training_early_profit_factor"]
            )
            selected["training_consensus_late_profit_factor"] = (
                composite_diagnostics["training_late_profit_factor"]
            )
            selected_rows.append(selected)

    selected_frame = (
        pd.DataFrame(selected_rows).reset_index(drop=True)
        if selected_rows
        else pd.DataFrame()
    )
    month_record.update(
        {
            "validated_composite_subregimes": sum(
                1 for item in composite_admissions if bool(item["admitted"])
            ),
            "selected_signals": len(selected_frame),
            "status": "PAST_ONLY_VALIDATED_CONSENSUS_FIT",
        }
    )
    return (
        selected_frame,
        individual_admissions,
        composite_admissions,
        month_record,
    )


def walkforward_select(
    candidates: pd.DataFrame, config: dict[str, Any]
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    signals = build_signal_frame(candidates)
    start = pd.Timestamp(config["model"]["evaluation_start_utc"])
    end = pd.Timestamp(config["model"]["evaluation_end_exclusive_utc"])
    selected_parts: list[pd.DataFrame] = []
    individual: list[dict[str, Any]] = []
    composite: list[dict[str, Any]] = []
    months: list[dict[str, Any]] = []
    for month_start in pd.date_range(start, end, freq="MS", inclusive="left"):
        month_end = min(month_start + pd.offsets.MonthBegin(1), end)
        selected, month_individual, month_composite, month_record = _fit_month(
            month_start, month_end, signals, candidates, config
        )
        if not selected.empty:
            selected_parts.append(selected)
        individual.extend(month_individual)
        composite.extend(month_composite)
        months.append(month_record)
    selections = (
        pd.concat(selected_parts, ignore_index=True)
        if selected_parts
        else pd.DataFrame()
    )
    return (
        selections,
        pd.DataFrame(individual),
        pd.DataFrame(composite),
        pd.DataFrame(months),
    )


def run(config_path: Path, output_dir: Path) -> dict[str, Any]:
    config_bytes = config_path.read_bytes()
    config = json.loads(config_bytes)
    if tuple(config["model"]["cluster_features"]) != CLUSTER_FEATURES:
        raise RuntimeError("Frozen cluster feature order mismatch")
    candidates = load_candidates(config["source"])
    selections, individual, composite, monthly = walkforward_select(
        candidates, config
    )
    trades, overlap_rejections = enforce_nonoverlap(selections)
    windows = _window_metrics(trades, config["reporting_windows"])
    gates = evaluate_gates(trades, windows, config)
    passed = all(gates.values())
    direction_metrics = {
        direction: summarize(trades[trades["direction"].eq(direction)])
        for direction in ("LONG", "SHORT")
    } if not trades.empty else {
        direction: summarize(trades) for direction in ("LONG", "SHORT")
    }
    subregime_metrics = {
        str(subregime): summarize(trades[trades["subregime"].eq(subregime)])
        for subregime in range(1, int(config["model"]["subregime_count"]) + 1)
    } if not trades.empty else {
        str(subregime): summarize(trades)
        for subregime in range(1, int(config["model"]["subregime_count"]) + 1)
    }

    output_dir.mkdir(parents=True, exist_ok=True)
    selections.to_csv(
        output_dir / "VALIDATED_SELECTIONS.csv", index=False, lineterminator="\n"
    )
    trades.to_csv(output_dir / "TRADES.csv", index=False, lineterminator="\n")
    individual.to_csv(
        output_dir / "MONTHLY_INDIVIDUAL_ADMISSIONS.csv",
        index=False,
        lineterminator="\n",
    )
    composite.to_csv(
        output_dir / "MONTHLY_COMPOSITE_ADMISSIONS.csv",
        index=False,
        lineterminator="\n",
    )
    monthly.to_csv(
        output_dir / "MONTHLY_SUBREGIMES.csv", index=False, lineterminator="\n"
    )
    result = {
        "schema_version": "eurusd_neutral_validated_consensus_result_v1",
        "frozen_config_sha256": hashlib.sha256(config_bytes).hexdigest(),
        "source_sha256": config["source"]["sha256"],
        "source_rows": len(candidates),
        "validated_selections_before_overlap": len(selections),
        "overlap_rejections": overlap_rejections,
        "trades": len(trades),
        "windows": windows,
        "direction_metrics": direction_metrics,
        "subregime_metrics": subregime_metrics,
        "gate_results": gates,
        "all_historical_quality_gates_passed": passed,
        "retrospective_causal_not_pristine_oos": True,
        "adaptive_successor_after_consensus_failure": True,
        "broker_action_allowed": False,
        "status": (
            "HISTORICAL_VALIDATED_CONSENSUS_PASS_REQUIRES_PROSPECTIVE_CONFIRMATION"
            if passed
            else "REJECTED_NEUTRAL_VALIDATED_CONSENSUS"
        ),
    }
    (output_dir / "RESULT.json").write_text(
        json.dumps(_json_safe(result), indent=2, allow_nan=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return result
