from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

from .asymmetric import payoff_metrics
from .neutral_four_clock_ranker import build_paired_points
from .research import PACKAGE_ROOT, serialize, sha256_file


FAMILY = "N41_NEUTRAL_TWO_STAGE_OPPORTUNITY_AUDIT"
CONFIG_PATH = (
    PACKAGE_ROOT
    / "config"
    / "frozen_neutral_two_stage_opportunity_audit.json"
)
OUTPUT_ROOT = PACKAGE_ROOT / "outputs" / "neutral_two_stage_opportunity_audit"


def load_config() -> dict[str, Any]:
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def verify_sources(cfg: dict[str, Any]) -> None:
    for key in ("paired_source", "parent_contract"):
        reference = cfg[key]
        if (
            sha256_file(PACKAGE_ROOT / reference["path"])
            != reference["sha256"]
        ):
            raise RuntimeError(f"Two-stage audit {key} drift")


def _source_columns(cfg: dict[str, Any]) -> list[str]:
    identity = [
        "side",
        "signal_time_utc",
        "completion_time_utc",
        "entry_time_utc",
        "exit_time_utc",
        "entry_price",
        "stop_price",
        "target_price",
        "exit_price",
        "exit_reason",
        "risk_distance",
        "risk_pips",
        "outcome_r",
        "target_first",
        "fixed_0p01_lot_usd",
        "oracle_member",
    ]
    return list(
        dict.fromkeys(
            [
                *identity,
                *cfg["side_contrast_features"],
                *cfg["opportunity_features"],
            ]
        )
    )


def load_pre_forward_source(
    cfg: dict[str, Any],
) -> pd.DataFrame:
    cutoff = pd.Timestamp(
        cfg["paired_source"]["row_filter_entry_time_before_exclusive"]
    )
    frame = pd.read_parquet(
        PACKAGE_ROOT / cfg["paired_source"]["path"],
        columns=_source_columns(cfg),
        filters=[("entry_time_utc", "<", cutoff)],
    )
    for column in (
        "signal_time_utc",
        "completion_time_utc",
        "entry_time_utc",
        "exit_time_utc",
    ):
        frame[column] = pd.to_datetime(frame[column], utc=True)
    if frame.empty or not frame["entry_time_utc"].lt(cutoff).all():
        raise RuntimeError("Forward row entered development-only source")
    return frame


def assert_development_only(
    points: pd.DataFrame,
    cfg: dict[str, Any],
) -> None:
    cutoff = pd.Timestamp(
        cfg["forward_policy"]["forward_start_utc"]
    )
    if points.empty or not points["entry_time_utc"].lt(cutoff).all():
        raise RuntimeError("Forward outcome entered two-stage audit")


def success_score(
    opportunity_probability: np.ndarray,
    side_probability_long: np.ndarray,
) -> np.ndarray:
    opportunity = np.asarray(opportunity_probability, dtype=float)
    side = np.asarray(side_probability_long, dtype=float)
    if opportunity.shape != side.shape:
        raise ValueError("Two-stage probability shapes differ")
    if (
        np.any((opportunity < 0) | (opportunity > 1))
        or np.any((side < 0) | (side > 1))
    ):
        raise ValueError("Probabilities must be in [0, 1]")
    return opportunity * np.maximum(side, 1.0 - side)


def _prepare_points(
    source: pd.DataFrame,
    cfg: dict[str, Any],
) -> pd.DataFrame:
    parent_cfg = json.loads(
        (PACKAGE_ROOT / cfg["parent_contract"]["path"]).read_text(
            encoding="utf-8"
        )
    )
    points, _ = build_paired_points(
        source,
        parent_cfg,
        include_outcomes=True,
        enforce_frozen_census=False,
    )
    assert_development_only(points, cfg)
    for column in cfg["opportunity_features"]:
        points[f"shared_{column}"] = 0.5 * (
            points[f"{column}_long"] + points[f"{column}_short"]
        )
    points["winner_count"] = (
        points["long_target_first"].astype(int)
        + points["short_target_first"].astype(int)
    )
    if points["winner_count"].gt(1).any():
        raise RuntimeError("Paired target contract produced two winners")
    points["any_winner"] = points["winner_count"].eq(1)
    return points


def _fit_logistic(
    train_x: pd.DataFrame,
    train_y: pd.Series,
    model_cfg: dict[str, Any],
    shared_cfg: dict[str, Any],
) -> tuple[StandardScaler, LogisticRegression]:
    scaler = StandardScaler()
    transformed = scaler.fit_transform(train_x)
    model = LogisticRegression(
        C=float(model_cfg["C"]),
        solver=model_cfg["solver"],
        max_iter=int(shared_cfg["max_iter"]),
        class_weight=model_cfg["class_weight"],
        random_state=int(shared_cfg["random_state"]),
    )
    model.fit(transformed, train_y.astype(int))
    return scaler, model


def _coefficient_frame(
    stage: str,
    columns: list[str],
    scaler: StandardScaler,
    model: LogisticRegression,
) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "stage": stage,
            "feature": columns,
            "coefficient": model.coef_[0],
            "training_mean": scaler.mean_,
            "training_scale": scaler.scale_,
        }
    )


def _remove_top_winners(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return frame
    remove = int(math.ceil(len(frame) * 0.05))
    return frame.sort_values("r").iloc[:-remove].copy()


def _threshold_block(
    scored: pd.DataFrame,
    threshold: float,
    cfg: dict[str, Any],
) -> dict[str, Any]:
    selected = scored[scored["success_score"].ge(threshold)].copy()
    metrics = payoff_metrics(selected)
    stressed = payoff_metrics(selected, "extra_half_pip_stress_r")
    top_removed = payoff_metrics(_remove_top_winners(selected))
    by_year = {
        str(year): payoff_metrics(
            selected[selected["entry_time_utc"].dt.year.eq(year)]
        )
        for year in (2021, 2022)
    }
    gate = cfg["development_admission"]
    checks = {
        "sample": (
            len(selected) >= int(gate["minimum_selected_trades"])
        ),
        "each_year_sample": all(
            value["trades"]
            >= int(gate["minimum_selected_trades_each_year"])
            for value in by_year.values()
        ),
        "win_rate": (
            float(gate["minimum_win_rate"])
            <= metrics["win_rate"]
            <= float(gate["maximum_win_rate"])
        ),
        "profit_factor": (
            metrics["profit_factor"]
            >= float(gate["minimum_profit_factor"])
        ),
        "net": (
            metrics["net_r"]
            > float(gate["minimum_net_r_exclusive"])
        ),
        "extra_half_pip": (
            stressed["profit_factor"]
            >= float(gate["minimum_extra_half_pip_profit_factor"])
        ),
        "top_winner_removal": (
            top_removed["profit_factor"]
            >= float(gate["minimum_top_5pct_removed_profit_factor"])
        ),
    }
    return {
        "threshold": threshold,
        "active_dates": int(selected["eligible_date"].nunique()),
        "metrics": metrics,
        "by_year": by_year,
        "extra_half_pip": stressed,
        "top_5pct_winners_removed": top_removed,
        "gate_results": checks,
        "passed": bool(all(checks.values())),
    }


def run_audit() -> tuple[
    dict[str, Any],
    dict[str, pd.DataFrame],
]:
    cfg = load_config()
    verify_sources(cfg)
    source = load_pre_forward_source(cfg)
    points = _prepare_points(source, cfg)
    training_end = pd.Timestamp(cfg["training_period"][1])
    development_start = pd.Timestamp(cfg["development_period"][0])
    development_end = pd.Timestamp(cfg["development_period"][1])
    training = points[
        points["entry_time_utc"].le(training_end)
        & points["pair_label_known_time_utc"].le(training_end)
    ].copy()
    development = points[
        points["entry_time_utc"].between(
            development_start, development_end, inclusive="both"
        )
    ].copy()
    opportunity_columns = [
        f"shared_{column}" for column in cfg["opportunity_features"]
    ]
    side_columns = [
        f"contrast_{column}"
        for column in cfg["side_contrast_features"]
    ]
    models = cfg["models"]
    opportunity_scaler, opportunity_model = _fit_logistic(
        training[opportunity_columns],
        training["any_winner"],
        models["opportunity"],
        models,
    )
    side_training = training[training["one_winner_label"]].copy()
    side_scaler, side_model = _fit_logistic(
        side_training[side_columns],
        side_training["preferred_long"],
        models["side"],
        models,
    )
    scored = development.copy()
    scored["opportunity_probability"] = opportunity_model.predict_proba(
        opportunity_scaler.transform(scored[opportunity_columns])
    )[:, 1]
    scored["side_probability_long"] = side_model.predict_proba(
        side_scaler.transform(scored[side_columns])
    )[:, 1]
    scored["success_score"] = success_score(
        scored["opportunity_probability"].to_numpy(),
        scored["side_probability_long"].to_numpy(),
    )
    scored["chosen_side"] = np.where(
        scored["side_probability_long"].ge(0.5), "LONG", "SHORT"
    )
    scored["r"] = np.where(
        scored["chosen_side"].eq("LONG"),
        scored["outcome_r_long"],
        scored["outcome_r_short"],
    )
    stress = (
        float(cfg["execution_reference"]["extra_round_trip_stress_pips"])
        / float(cfg["execution_reference"]["risk_pips"])
    )
    scored["extra_half_pip_stress_r"] = scored["r"] - stress
    threshold_blocks = [
        _threshold_block(scored, float(threshold), cfg)
        for threshold in cfg["strategy"]["threshold_ladder_descending"]
    ]
    selected = next(
        (
            block["threshold"]
            for block in threshold_blocks
            if block["passed"]
        ),
        None,
    )
    coefficient_frames = [
        _coefficient_frame(
            "OPPORTUNITY",
            opportunity_columns,
            opportunity_scaler,
            opportunity_model,
        ),
        _coefficient_frame(
            "SIDE",
            side_columns,
            side_scaler,
            side_model,
        ),
    ]
    result = {
        "schema_version": (
            "eurusd_neutral_two_stage_opportunity_audit_v1"
        ),
        "family": FAMILY,
        "status": (
            "DEVELOPMENT_PASS_FORWARD_PREREG_REQUIRED"
            if selected is not None
            else "REJECTED_IN_DEVELOPMENT_FORWARD_FORBIDDEN"
        ),
        "forward_returns_loaded": False,
        "selected_threshold": selected,
        "source_boundary": {
            "side_rows": int(len(source)),
            "paired_points": int(len(points)),
            "maximum_entry_time_utc": points[
                "entry_time_utc"
            ].max(),
            "forward_start_utc": cfg["forward_policy"][
                "forward_start_utc"
            ],
        },
        "training": {
            "paired_points": int(len(training)),
            "one_winner_points": int(
                training["one_winner_label"].sum()
            ),
            "opportunity_rate": float(training["any_winner"].mean()),
        },
        "development": {
            "paired_points": int(len(development)),
            "eligible_dates": int(
                development["eligible_date"].nunique()
            ),
            "opportunity_rate": float(
                development["any_winner"].mean()
            ),
            "score_distribution": {
                str(quantile): float(
                    scored["success_score"].quantile(quantile)
                )
                for quantile in (0.0, 0.5, 0.9, 0.95, 0.99, 1.0)
            },
            "thresholds": threshold_blocks,
        },
        "decision": (
            "No threshold may proceed to forward evaluation."
            if selected is None
            else "Freeze the selected threshold before any forward read."
        ),
    }
    return (
        serialize(result),
        {
            "SCORED_DEVELOPMENT": scored,
            "COEFFICIENTS": pd.concat(
                coefficient_frames, ignore_index=True
            ),
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
    "assert_development_only",
    "load_config",
    "run_audit",
    "success_score",
    "write_json",
]
