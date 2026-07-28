from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from .neutral_growth_risk_consensus import (
    build_candidates,
    forward_metrics,
    load_config as load_parent_config,
    load_eurusd_stage,
    load_growth_risk,
    load_oracle_forward,
    safe_neutral_dates,
    simulate,
    stage_metrics,
    verify_prereg_lock as verify_parent_prereg_lock,
    write_json,
)
from .research import PACKAGE_ROOT, serialize, sha256_file


FAMILY = "N47_NEUTRAL_GROWTH_RISK_SELECTED"
OUTPUT_ROOT = (
    PACKAGE_ROOT / "outputs" / "neutral_growth_risk_selected"
)
CONFIG_PATH = (
    PACKAGE_ROOT
    / "config"
    / "frozen_neutral_growth_risk_selected.json"
)
PREREG_LOCK_PATH = (
    PACKAGE_ROOT
    / "EURUSD_NEUTRAL_GROWTH_RISK_SELECTED_PREREG_2026_07_28.sha256.json"
)
CONFIRMATION_LOCK_PATH = (
    OUTPUT_ROOT / "CONFIRMATION_GATE_LOCK.sha256.json"
)


def load_config() -> dict[str, Any]:
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def verify_prereg_lock() -> dict[str, str]:
    verify_parent_prereg_lock()
    lock = json.loads(PREREG_LOCK_PATH.read_text(encoding="utf-8"))
    if lock.get("locked_before_2023_eurusd_outcome") is not True:
        raise RuntimeError("N47 is not locked before 2023")
    checked: dict[str, str] = {}
    for relative, expected in lock["files"].items():
        actual = sha256_file(PACKAGE_ROOT / relative)
        if actual != expected:
            raise RuntimeError(f"N47 preregistration drift: {relative}")
        checked[relative] = actual
    cfg = load_config()
    parent = cfg["parent_mechanics"]
    references = {
        parent["config_path"]: parent["config_sha256"],
        parent["prereg_lock_path"]: parent["prereg_lock_sha256"],
        cfg["development_evidence"]["closure_path"]: cfg[
            "development_evidence"
        ]["closure_sha256"],
        cfg["development_evidence"]["result_path"]: cfg[
            "development_evidence"
        ]["result_sha256"],
        cfg["development_evidence"]["trades_path"]: cfg[
            "development_evidence"
        ]["trades_sha256"],
    }
    for relative, expected in references.items():
        if sha256_file(PACKAGE_ROOT / relative) != expected:
            raise RuntimeError(f"N47 evidence drift: {relative}")
    return checked


def verify_confirmation_lock() -> dict[str, Any]:
    verify_prereg_lock()
    lock = json.loads(
        CONFIRMATION_LOCK_PATH.read_text(encoding="utf-8")
    )
    if lock.get("locked_before_2024_2026_eurusd_outcome") is not True:
        raise RuntimeError("N47 confirmation is not forward-locked")
    for relative, expected in lock["files"].items():
        if sha256_file(PACKAGE_ROOT / relative) != expected:
            raise RuntimeError(
                f"N47 confirmation result drift: {relative}"
            )
    result = json.loads(
        (
            PACKAGE_ROOT / lock["confirmation_result_path"]
        ).read_text(encoding="utf-8")
    )
    if (
        result.get("status")
        != "CONFIRMATION_PASS_FORWARD_LOCK_REQUIRED"
    ):
        raise RuntimeError("N47 confirmation lock is not a pass")
    return lock


def selected_candidates(
    cfg: dict[str, Any],
    parent_cfg: dict[str, Any],
) -> tuple[pd.DataFrame, dict[str, Any]]:
    all_candidates, _ = build_candidates(
        safe_neutral_dates(),
        load_growth_risk(parent_cfg),
        parent_cfg,
    )
    experts = list(cfg["selected_experts"])
    first = pd.Timestamp(cfg["windows"]["confirmation_2023"][0])
    last = pd.Timestamp(cfg["windows"]["recent_2026_h1"][1])
    selected = all_candidates[
        all_candidates["expert"].isin(experts)
        & all_candidates["entry_time_utc"].between(
            first, last, inclusive="both"
        )
    ].copy()
    by_window = {
        name: int(
            selected["entry_time_utc"]
            .between(
                pd.Timestamp(bounds[0]),
                pd.Timestamp(bounds[1]),
                inclusive="both",
            )
            .sum()
        )
        for name, bounds in cfg["windows"].items()
    }
    by_expert = {
        expert: int(selected["expert"].eq(expert).sum())
        for expert in experts
    }
    by_side = {
        side: int(selected["side"].eq(side).sum())
        for side in ("LONG", "SHORT")
    }
    census = {
        "total_candidates_2023_2026_h1": int(len(selected)),
        "by_window": by_window,
        "by_expert": by_expert,
        "by_side": by_side,
    }
    if census != cfg["outcome_blind_selected_census"]:
        raise RuntimeError(
            "N47 outcome-blind selected census drift: "
            f"actual={census!r}"
        )
    return selected.sort_values("entry_time_utc"), census


def selected_stage_metrics(
    trades: pd.DataFrame,
    gate: dict[str, Any],
    experts: list[str],
) -> dict[str, Any]:
    result = stage_metrics(trades, gate, experts)
    expert_capacity = all(
        block["trades"] >= int(gate["minimum_each_expert_trades"])
        for block in result["by_expert"].values()
    )
    expert_pf = all(
        block["profit_factor"]
        >= float(gate["minimum_each_expert_profit_factor"])
        for block in result["by_expert"].values()
    )
    result["gate_results"]["expert_trade_capacity"] = (
        expert_capacity
    )
    result["gate_results"]["expert_profit_factor"] = expert_pf
    result["passed"] = bool(all(result["gate_results"].values()))
    return result


def run_confirmation() -> tuple[
    dict[str, Any], dict[str, pd.DataFrame]
]:
    verify_prereg_lock()
    cfg = load_config()
    parent_cfg = load_parent_config()
    candidates, census = selected_candidates(cfg, parent_cfg)
    name = cfg["confirmation_gate"]["allowed_window"]
    bounds = cfg["windows"][name]
    stage_candidates = candidates[
        candidates["entry_time_utc"].between(
            pd.Timestamp(bounds[0]),
            pd.Timestamp(bounds[1]),
            inclusive="both",
        )
    ].copy()
    m5, bounded_load = load_eurusd_stage(
        parent_cfg,
        pd.Timestamp(bounds[0]),
        pd.Timestamp(bounds[1]),
    )
    trades, skips = simulate(stage_candidates, m5, parent_cfg)
    metrics = selected_stage_metrics(
        trades,
        cfg["confirmation_gate"],
        list(cfg["selected_experts"]),
    )
    status = (
        "CONFIRMATION_PASS_FORWARD_LOCK_REQUIRED"
        if metrics["passed"]
        else "REJECTED_IN_CONFIRMATION_2024_2026_FORBIDDEN"
    )
    result = {
        "schema_version": (
            "eurusd_neutral_growth_risk_selected_confirmation_v1"
        ),
        "family": FAMILY,
        "status": status,
        "information_status": cfg["information_status"],
        "outcome_blind_selected_census": census,
        "stage": name,
        "stage_bounds": bounds,
        "confirmation": metrics,
        "execution_skips": skips,
        "eurusd_bounded_load": bounded_load,
        "forward_eurusd_outcomes_loaded": False,
        "broker_action_allowed": False,
    }
    return serialize(result), {
        "CONFIRMATION_CANDIDATES": stage_candidates,
        "CONFIRMATION_TRADES": trades,
    }


def selected_forward_metrics(
    trades: pd.DataFrame,
    oracle: pd.DataFrame,
    cfg: dict[str, Any],
) -> tuple[dict[str, Any], pd.DataFrame]:
    metric_cfg = {
        **cfg,
        "experts": cfg["selected_experts"],
    }
    metrics, matches = forward_metrics(
        trades, oracle, metric_cfg
    )
    gate = cfg["forward_admission"]
    expert_capacity = all(
        block["trades"] >= int(gate["minimum_each_expert_trades"])
        for block in metrics["by_expert"].values()
    )
    expert_pf = all(
        block["profit_factor"]
        >= float(gate["minimum_each_expert_profit_factor"])
        for block in metrics["by_expert"].values()
    )
    metrics["gate_results"]["expert_trade_capacity"] = (
        expert_capacity
    )
    metrics["gate_results"]["expert_profit_factor"] = expert_pf
    metrics["passed"] = bool(all(metrics["gate_results"].values()))
    return metrics, matches


def run_forward() -> tuple[
    dict[str, Any], dict[str, pd.DataFrame]
]:
    verify_confirmation_lock()
    cfg = load_config()
    parent_cfg = load_parent_config()
    candidates, census = selected_candidates(cfg, parent_cfg)
    start = pd.Timestamp(cfg["windows"]["forward_2024"][0])
    end = pd.Timestamp(cfg["windows"]["recent_2026_h1"][1])
    stage_candidates = candidates[
        candidates["entry_time_utc"].between(
            start, end, inclusive="both"
        )
    ].copy()
    m5, bounded_load = load_eurusd_stage(
        parent_cfg, start, end
    )
    trades, skips = simulate(stage_candidates, m5, parent_cfg)
    oracle = load_oracle_forward(cfg, start, end)
    metrics, matches = selected_forward_metrics(
        trades, oracle, cfg
    )
    status = (
        "HISTORICAL_FORWARD_PASS_PROSPECTIVE_SHADOW_REQUIRED"
        if metrics["passed"]
        else "REJECTED_IN_CHRONOLOGICAL_FORWARD_NO_RETUNING"
    )
    result = {
        "schema_version": (
            "eurusd_neutral_growth_risk_selected_forward_v1"
        ),
        "family": FAMILY,
        "status": status,
        "outcome_blind_selected_census": census,
        "forward": metrics,
        "execution_skips": skips,
        "eurusd_bounded_load": bounded_load,
        "last_six_months": metrics["windows"][
            "recent_2026_h1"
        ],
        "broker_action_allowed": False,
    }
    return serialize(result), {
        "FORWARD_CANDIDATES": stage_candidates,
        "FORWARD_TRADES": trades,
        "ORACLE_MATCHES": matches,
    }


__all__ = [
    "CONFIRMATION_LOCK_PATH",
    "OUTPUT_ROOT",
    "load_config",
    "run_confirmation",
    "run_forward",
    "selected_candidates",
    "selected_forward_metrics",
    "selected_stage_metrics",
    "verify_confirmation_lock",
    "verify_prereg_lock",
    "write_json",
]
