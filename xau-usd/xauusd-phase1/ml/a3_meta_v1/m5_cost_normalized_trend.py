from __future__ import annotations

import copy
import csv
import hashlib
import json
import math
import os
from collections import Counter
from dataclasses import asdict, replace
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np
import pandas as pd

from ml.a3_meta_v1.dukascopy_label_factory import (
    Candidate,
    VerifiedTickStore,
    _load_foundation,
    _month_range,
    _sha256_file,
    _validate_candidates,
    _write_rows,
    prepare_verified_h1_bars,
    replay_candidates,
)
from ml.a3_meta_v1.dukascopy_m5_momentum_portability import (
    generate_m5_momentum_candidates,
    prepare_verified_m5_bars,
)


DEFAULT_CONTRACT = Path("config/ml/a3_ml_m5_cost_normalized_trend_v1.json")
EXPECTED_PROFILES = [
    {
        "profile_id": "CN_TREND_4ATR_1R_12H",
        "stop_atr_multiple": 4.0,
        "minimum_stop_price": 7.0,
        "maximum_stop_price": 50.0,
        "reward_r": 1.0,
        "maximum_hold_hours": 12,
    },
    {
        "profile_id": "CN_TREND_6ATR_1P5R_24H",
        "stop_atr_multiple": 6.0,
        "minimum_stop_price": 7.0,
        "maximum_stop_price": 50.0,
        "reward_r": 1.5,
        "maximum_hold_hours": 24,
    },
    {
        "profile_id": "CN_TREND_8ATR_2R_48H",
        "stop_atr_multiple": 8.0,
        "minimum_stop_price": 7.0,
        "maximum_stop_price": 50.0,
        "reward_r": 2.0,
        "maximum_hold_hours": 48,
    },
]


class M5CostNormalizedTrendError(RuntimeError):
    pass


def run_m5_cost_normalized_trend(root: Path, contract_path: Path | None = None) -> Path:
    root = root.resolve()
    contract_file = (contract_path or root / DEFAULT_CONTRACT).resolve()
    contract = json.loads(contract_file.read_text(encoding="utf-8"))
    _validate_contract(contract)
    storage_root = Path(
        os.environ.get(
            str(contract["storage_environment_variable"]),
            str(contract["default_storage_root"]),
        )
    ).resolve()
    if not storage_root.is_dir():
        raise M5CostNormalizedTrendError(f"storage root is missing: {storage_root}")
    source_contract, source_audit = _load_source_contract(root, storage_root, contract)
    foundation = _load_foundation(root.parents[1])
    months = _month_range(
        contract["period"]["start_month"], contract["period"]["end_month"]
    )
    if len(months) != int(contract["period"]["expected_months"]):
        raise M5CostNormalizedTrendError("research month count changed")
    h1_bars, h1_audits = prepare_verified_h1_bars(
        storage_root,
        storage_root / "research" / "xau-label-factory-v1" / "bars",
        str(contract["symbol"]),
        months,
        foundation,
    )
    m5_bars, m5_audits = prepare_verified_m5_bars(
        storage_root,
        storage_root / contract["source_lock"]["m5_cache_relative_root"],
        str(contract["symbol"]),
        months,
        foundation,
    )
    generator_contract = _generator_contract(source_contract, contract)
    base_candidates = generate_m5_momentum_candidates(
        m5_bars, h1_bars, generator_contract
    )
    _validate_candidates(base_candidates)
    profiled = _profile_candidates(base_candidates, contract)
    _validate_candidates(profiled)
    global_quality = {
        "source_hashes_match": True,
        "verified_h1_months": len(h1_audits)
        == int(contract["quality_gates"]["expected_months_valid"]),
        "verified_m5_months": len(m5_audits)
        == int(contract["quality_gates"]["expected_months_valid"]),
        "minimum_base_candidate_count": len(base_candidates)
        >= int(contract["quality_gates"]["minimum_candidate_count"]),
        "base_candidate_ids_unique": len({row.candidate_id for row in base_candidates})
        == len(base_candidates),
        "profiled_candidate_ids_unique": len({row.candidate_id for row in profiled})
        == len(profiled),
    }
    if not all(global_quality.values()):
        failed = [key for key, value in global_quality.items() if not value]
        raise M5CostNormalizedTrendError(f"pre-outcome source quality failed: {failed}")

    outputs = {
        key: (root / value).resolve() for key, value in contract["outputs"].items()
    }
    for path in outputs.values():
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists():
            path.unlink()
    _write_rows(outputs["candidates_csv"], [asdict(row) for row in profiled])

    source_days = _source_days_by_stage(m5_bars, contract)
    store = VerifiedTickStore(
        storage_root=storage_root,
        symbol=str(contract["symbol"]),
        foundation=foundation,
        prevalidated_months=set(months),
    )
    labels: list[pd.DataFrame] = []
    selected_frames: list[pd.DataFrame] = []
    evaluations: list[dict[str, Any]] = []
    development_quality: list[dict[str, Any]] = []

    for profile in contract["geometry_profiles"]:
        profile_id = str(profile["profile_id"])
        candidates = _profile_stage_candidates(profiled, profile_id, "DEVELOPMENT")
        raw = _replay_profile(
            candidates,
            h1_bars,
            store,
            profile,
            contract,
            "DEVELOPMENT",
        )
        labels.append(raw)
        selected, reasons = _apply_portfolio_controls(raw, contract)
        selected["stage"] = "DEVELOPMENT"
        selected_frames.append(selected)
        metrics = _economic_metrics(
            selected, source_days["DEVELOPMENT"], contract["selection"]
        )
        quality = _label_quality(raw, len(candidates), contract)
        gates = _stage_gates(metrics, contract["development_gates"])
        passes = all(quality.values()) and all(gates.values())
        development_quality.append(quality)
        evaluations.append(
            {
                "stage": "DEVELOPMENT",
                "profile_id": profile_id,
                "candidate_count": len(candidates),
                "quality": quality,
                "portfolio_rejections": reasons,
                "economic_metrics": metrics,
                "gates": gates,
                "passes": passes,
            }
        )

    passing = [row for row in evaluations if row["passes"]]
    passing.sort(key=_profile_sort_key)
    chosen = passing[0] if passing else None
    opened = {"validation": False, "internal_test": False, "exam": False}
    classification = "M5_COST_NORMALIZED_TREND_NO_DEVELOPMENT_SURVIVOR"

    if chosen:
        profile = next(
            row
            for row in contract["geometry_profiles"]
            if row["profile_id"] == chosen["profile_id"]
        )
        stages = [
            ("VALIDATION", "validation", contract["validation_gates"]),
            ("INTERNAL_TEST", "internal_test", contract["internal_test_gates"]),
            ("EXAM", "exam", contract["exam_gates"]),
        ]
        rejection_class = {
            "VALIDATION": "M5_COST_NORMALIZED_TREND_VALIDATION_REJECTED",
            "INTERNAL_TEST": "M5_COST_NORMALIZED_TREND_INTERNAL_TEST_REJECTED",
            "EXAM": "M5_COST_NORMALIZED_TREND_EXAM_REJECTED",
        }
        for stage, opened_key, stage_gate in stages:
            candidates = _profile_stage_candidates(
                profiled, str(profile["profile_id"]), stage
            )
            raw = _replay_profile(
                candidates,
                h1_bars,
                store,
                profile,
                contract,
                stage,
            )
            labels.append(raw)
            selected, reasons = _apply_portfolio_controls(raw, contract)
            selected["stage"] = stage
            selected_frames.append(selected)
            metrics = _economic_metrics(
                selected, source_days[stage], contract["selection"]
            )
            quality = _label_quality(raw, len(candidates), contract)
            gates = _stage_gates(metrics, stage_gate)
            passes = all(quality.values()) and all(gates.values())
            evaluations.append(
                {
                    "stage": stage,
                    "profile_id": profile["profile_id"],
                    "candidate_count": len(candidates),
                    "quality": quality,
                    "portfolio_rejections": reasons,
                    "economic_metrics": metrics,
                    "gates": gates,
                    "passes": passes,
                }
            )
            opened[opened_key] = True
            classification = rejection_class[stage]
            if not passes:
                break
        else:
            classification = "M5_COST_NORMALIZED_TREND_RESEARCH_SURVIVOR"

    all_labels = pd.concat(labels, ignore_index=True) if labels else pd.DataFrame()
    all_selected = (
        pd.concat(selected_frames, ignore_index=True)
        if selected_frames
        else pd.DataFrame()
    )
    all_labels.to_csv(outputs["labels_csv"], index=False, lineterminator="\n")
    all_selected.to_csv(
        outputs["selected_trades_csv"], index=False, lineterminator="\n"
    )
    _write_evaluations(outputs["evaluations_csv"], evaluations)

    payload = {
        "schema_version": contract["schema_version"],
        "classification": classification,
        "created_at_utc": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "contract": str(contract_file),
        "contract_sha256": _sha256_file(contract_file),
        "storage_root": str(storage_root),
        "source_audit": source_audit,
        "source_months": len(months),
        "h1_cache_reused_months": sum(
            bool(row["bar_cache_reused"]) for row in h1_audits
        ),
        "m5_cache_reused_months": sum(
            bool(row["bar_cache_reused"]) for row in m5_audits
        ),
        "m5_rows": len(m5_bars),
        "base_candidate_count": len(base_candidates),
        "profiled_candidate_count": len(profiled),
        "source_days_by_stage": source_days,
        "global_quality": global_quality,
        "evaluations": evaluations,
        "selected_profile": chosen,
        "chronological_stages_opened": opened,
        "artifacts": _artifact_manifest(outputs),
        "research_controls": contract["research_controls"],
        "authorization": {
            **contract["authorization"],
            "strategy_execution_authorized": False,
            "demo_or_live_authorized": False,
        },
    }
    outputs["report_json"].write_text(json.dumps(payload, indent=2), encoding="utf-8")
    outputs["report_markdown"].write_text(_render(payload), encoding="utf-8")
    return outputs["report_json"]


def _validate_contract(contract: Mapping[str, Any]) -> None:
    if contract.get("schema_version") != "a3_ml_m5_cost_normalized_trend_v1":
        raise M5CostNormalizedTrendError("unexpected cost-normalized trend contract")
    if contract.get("geometry_profiles") != EXPECTED_PROFILES:
        raise M5CostNormalizedTrendError("preregistered geometry profiles changed")
    source = contract.get("source_lock", {})
    if not source.get("reuse_exact_candidate_trigger_and_lane_hours"):
        raise M5CostNormalizedTrendError("exact source trigger reuse is required")
    if source.get("candidate_threshold_changes_authorized"):
        raise M5CostNormalizedTrendError("candidate threshold changes are forbidden")
    if source.get("m5_cache_relative_root") != (
        "research/xau-m5-momentum-portability-v1/bars"
    ):
        raise M5CostNormalizedTrendError("frozen M5 source cache changed")
    selection = contract.get("selection", {})
    if selection.get("ml_ranking_authorized"):
        raise M5CostNormalizedTrendError("ML ranking is forbidden in V1")
    if selection.get("profile_or_threshold_search_beyond_locked_set_authorized"):
        raise M5CostNormalizedTrendError("unregistered profile search is forbidden")
    if contract.get("research_controls", {}).get(
        "same_iteration_geometry_or_gate_changes_authorized"
    ):
        raise M5CostNormalizedTrendError("same-iteration changes are forbidden")
    for key, value in contract.get("authorization", {}).items():
        if value:
            raise M5CostNormalizedTrendError(f"{key} must remain false")


def _load_source_contract(
    root: Path, storage_root: Path, contract: Mapping[str, Any]
) -> tuple[dict[str, Any], dict[str, Any]]:
    lock = contract["source_lock"]
    raw_inventory = storage_root / lock["raw_inventory_path"]
    source_contract_path = root / lock["source_candidate_contract_path"]
    ea_path = root / lock["ea_path"]
    specification_path = root / lock["portfolio_spec_path"]
    checks = [
        (raw_inventory, lock["raw_inventory_sha256"]),
        (source_contract_path, lock["source_candidate_contract_sha256"]),
        (ea_path, lock["ea_sha256"]),
        (specification_path, lock["portfolio_spec_sha256"]),
    ]
    for path, expected in checks:
        if not path.is_file() or _sha256_file(path) != expected:
            raise M5CostNormalizedTrendError(
                f"locked source missing or changed: {path}"
            )
    inventory = json.loads(raw_inventory.read_text(encoding="utf-8"))
    if inventory.get("classification") != lock["required_raw_inventory_classification"]:
        raise M5CostNormalizedTrendError("raw source inventory is not data-ready")
    return json.loads(source_contract_path.read_text(encoding="utf-8")), {
        "raw_inventory": str(raw_inventory),
        "raw_inventory_sha256": lock["raw_inventory_sha256"],
        "source_candidate_contract": str(source_contract_path),
        "source_candidate_contract_sha256": lock["source_candidate_contract_sha256"],
        "ea_sha256": lock["ea_sha256"],
        "portfolio_spec_sha256": lock["portfolio_spec_sha256"],
        "hashes_verified": True,
    }


def _generator_contract(
    source_contract: Mapping[str, Any], contract: Mapping[str, Any]
) -> dict[str, Any]:
    generated = copy.deepcopy(source_contract)
    generated["period"] = dict(contract["period"])
    generated["windows"] = {
        "prehistory_end_exclusive_utc": contract["windows"][
            "development_end_exclusive_utc"
        ],
        "replication_end_exclusive_utc": contract["windows"]["exam_end_exclusive_utc"],
    }
    generated["external_output_subdirectory"] = contract["external_output_subdirectory"]
    return generated


def _profile_candidates(
    base_candidates: Sequence[Candidate], contract: Mapping[str, Any]
) -> list[Candidate]:
    output = []
    for base in base_candidates:
        stage = _stage_for_timestamp(base.decision_time_utc, contract)
        if stage is None:
            continue
        for profile in contract["geometry_profiles"]:
            stop = max(
                float(profile["stop_atr_multiple"]) * float(base.atr),
                float(profile["minimum_stop_price"]),
            )
            if stop > float(profile["maximum_stop_price"]):
                continue
            profile_id = str(profile["profile_id"])
            candidate_id = hashlib.sha256(
                f"{profile_id}|{base.candidate_id}".encode("ascii")
            ).hexdigest()[:24]
            output.append(
                replace(
                    base,
                    candidate_id=candidate_id,
                    family_id=f"{profile_id}|{base.family_id}",
                    split=stage,
                    stop_distance=stop,
                    stop_distance_atr=stop / float(base.atr),
                    reward_r=float(profile["reward_r"]),
                )
            )
    return sorted(output, key=lambda row: (row.decision_timestamp_ms, row.candidate_id))


def _profile_stage_candidates(
    candidates: Sequence[Candidate], profile_id: str, stage: str
) -> list[Candidate]:
    prefix = f"{profile_id}|"
    return [
        row
        for row in candidates
        if row.split == stage and row.family_id.startswith(prefix)
    ]


def _stage_for_timestamp(value: str, contract: Mapping[str, Any]) -> str | None:
    timestamp = pd.Timestamp(value)
    windows = contract["windows"]
    if timestamp < pd.Timestamp(windows["development_start_utc"]):
        return None
    if timestamp < pd.Timestamp(windows["development_end_exclusive_utc"]):
        return "DEVELOPMENT"
    if timestamp < pd.Timestamp(windows["validation_end_exclusive_utc"]):
        return "VALIDATION"
    if timestamp < pd.Timestamp(windows["internal_test_end_exclusive_utc"]):
        return "INTERNAL_TEST"
    if timestamp < pd.Timestamp(windows["exam_end_exclusive_utc"]):
        return "EXAM"
    return None


def _stage_end(stage: str, contract: Mapping[str, Any]) -> pd.Timestamp:
    key = {
        "DEVELOPMENT": "development_end_exclusive_utc",
        "VALIDATION": "validation_end_exclusive_utc",
        "INTERNAL_TEST": "internal_test_end_exclusive_utc",
        "EXAM": "exam_end_exclusive_utc",
    }[stage]
    return pd.Timestamp(contract["windows"][key])


def _replay_profile(
    candidates: Sequence[Candidate],
    h1_bars: Sequence[Mapping[str, Any]],
    store: VerifiedTickStore,
    profile: Mapping[str, Any],
    contract: Mapping[str, Any],
    stage: str,
) -> pd.DataFrame:
    execution = {
        "maximum_entry_delay_minutes": int(
            contract["entry"]["maximum_entry_delay_minutes"]
        ),
        "maximum_hold_hours": int(profile["maximum_hold_hours"]),
        "maximum_timeout_exit_grace_hours": 72,
        "lot_size": float(contract["cost_and_risk"]["lot_size"]),
        "contract_size_ounces_per_lot": float(
            contract["cost_and_risk"]["contract_size_ounces_per_lot"]
        ),
        "extra_execution_cost_usd": float(
            contract["cost_and_risk"]["additional_execution_cost_usd_per_0p01_lot"]
        ),
        "holding_cost_per_24h_usd": float(
            contract["cost_and_risk"]["holding_cost_per_24h_usd"]
        ),
    }
    raw = pd.DataFrame(
        [
            asdict(row)
            for row in replay_candidates(
                candidates, h1_bars, store, {"execution": execution}
            )
        ]
    )
    if raw.empty:
        return raw
    raw["profile_id"] = str(profile["profile_id"])
    raw["stage"] = stage
    raw["spread_floor_uplift_usd"] = 0.0
    resolved = raw["status"].eq("RESOLVED")
    spread = pd.to_numeric(raw.loc[resolved, "entry_spread"])
    uplift = (
        float(contract["cost_and_risk"]["broker_spread_floor_price"]) - spread
    ).clip(lower=0)
    raw.loc[resolved, "spread_floor_uplift_usd"] = uplift
    raw.loc[resolved, "execution_stress_usd"] = (
        pd.to_numeric(raw.loc[resolved, "execution_stress_usd"]) + uplift
    )
    raw.loc[resolved, "stress_net_pnl_usd"] = (
        pd.to_numeric(raw.loc[resolved, "gross_pnl_usd"])
        - pd.to_numeric(raw.loc[resolved, "execution_stress_usd"])
        - pd.to_numeric(raw.loc[resolved, "holding_stress_usd"])
    )
    quantity = float(contract["cost_and_risk"]["lot_size"]) * float(
        contract["cost_and_risk"]["contract_size_ounces_per_lot"]
    )
    risk = pd.to_numeric(raw.loc[resolved, "stop_distance"]) * quantity
    raw.loc[resolved, "risk_usd"] = risk
    raw.loc[resolved, "stress_net_r"] = (
        pd.to_numeric(raw.loc[resolved, "stress_net_pnl_usd"]) / risk
    )
    raw.loc[resolved, "label_profitable_after_stress"] = (
        pd.to_numeric(raw.loc[resolved, "stress_net_pnl_usd"]) > 0
    ).astype(int)
    immediate = (
        np.maximum(
            spread,
            float(contract["cost_and_risk"]["broker_spread_floor_price"]),
        )
        + float(contract["cost_and_risk"]["additional_execution_cost_usd_per_0p01_lot"])
    ) / pd.to_numeric(raw.loc[resolved, "stop_distance"])
    raw.loc[resolved, "immediate_cost_r"] = immediate
    exits = pd.to_datetime(raw.loc[resolved, "exit_time_utc"], utc=True)
    crosses = exits >= _stage_end(stage, contract)
    if crosses.any():
        raw.loc[crosses.index[crosses], "status"] = "SEGMENT_CROSS"
    return raw


def _apply_portfolio_controls(
    raw: pd.DataFrame, contract: Mapping[str, Any]
) -> tuple[pd.DataFrame, dict[str, int]]:
    if raw.empty:
        return raw.copy(), {}
    risk = contract["cost_and_risk"]
    rows = raw.loc[raw["status"].eq("RESOLVED")].copy()
    rows = rows.sort_values(["entry_time_utc", "candidate_id"])
    selected = []
    reasons: Counter[str] = Counter()
    open_rows: list[dict[str, Any]] = []
    daily: Counter[str] = Counter()
    for _, row in rows.iterrows():
        if float(row["immediate_cost_r"]) > float(risk["maximum_immediate_cost_r"]):
            reasons["immediate_cost_r"] += 1
            continue
        if float(row["risk_usd"]) > float(risk["maximum_initial_risk_usd_per_trade"]):
            reasons["per_trade_risk"] += 1
            continue
        entry = pd.Timestamp(row["entry_time_utc"])
        open_rows = [item for item in open_rows if item["exit"] > entry]
        if len(open_rows) >= int(risk["maximum_concurrent_trades"]):
            reasons["maximum_concurrent"] += 1
            continue
        same_direction = sum(
            item["direction"] == row["direction"] for item in open_rows
        )
        if same_direction >= int(risk["maximum_same_direction_trades"]):
            reasons["maximum_same_direction"] += 1
            continue
        if sum(item["risk"] for item in open_rows) + float(row["risk_usd"]) > float(
            risk["maximum_portfolio_initial_risk_usd"]
        ):
            reasons["portfolio_initial_risk"] += 1
            continue
        day = str(row["entry_time_utc"])[:10]
        if daily[day] >= int(risk["maximum_trades_per_utc_day"]):
            reasons["daily_cap"] += 1
            continue
        selected.append(dict(row))
        daily[day] += 1
        open_rows.append(
            {
                "exit": pd.Timestamp(row["exit_time_utc"]),
                "direction": row["direction"],
                "risk": float(row["risk_usd"]),
            }
        )
    return pd.DataFrame(selected, columns=rows.columns), dict(reasons)


def _label_quality(
    raw: pd.DataFrame, candidate_count: int, contract: Mapping[str, Any]
) -> dict[str, bool]:
    resolved = int(raw["status"].eq("RESOLVED").sum()) if not raw.empty else 0
    ineligible = int(raw["status"].eq("INELIGIBLE").sum()) if not raw.empty else 0
    eligible = candidate_count - ineligible
    resolved_or_cross = (
        int(raw["status"].isin(["RESOLVED", "SEGMENT_CROSS"]).sum())
        if not raw.empty
        else 0
    )
    return {
        "candidate_population_nonempty": candidate_count > 0,
        "minimum_resolved_share": resolved_or_cross / eligible
        >= float(contract["quality_gates"]["minimum_resolved_share"])
        if eligible
        else False,
        "resolved_risk_finite_positive": bool(
            resolved
            and np.isfinite(
                pd.to_numeric(raw.loc[raw["status"].eq("RESOLVED"), "risk_usd"])
            ).all()
            and (
                pd.to_numeric(raw.loc[raw["status"].eq("RESOLVED"), "risk_usd"]) > 0
            ).all()
        ),
        "resolved_cost_finite": bool(
            resolved
            and np.isfinite(
                pd.to_numeric(raw.loc[raw["status"].eq("RESOLVED"), "immediate_cost_r"])
            ).all()
        ),
    }


def _source_days_by_stage(
    m5_bars: Sequence[Mapping[str, Any]], contract: Mapping[str, Any]
) -> dict[str, int]:
    days: dict[str, set[str]] = {
        "DEVELOPMENT": set(),
        "VALIDATION": set(),
        "INTERNAL_TEST": set(),
        "EXAM": set(),
    }
    for row in m5_bars:
        timestamp = (
            row.get("timestamp_utc")
            or datetime.fromtimestamp(int(row["timestamp_ms"]) / 1000, UTC).isoformat()
        )
        stage = _stage_for_timestamp(str(timestamp), contract)
        if stage:
            days[stage].add(str(timestamp)[:10])
    return {stage: len(values) for stage, values in days.items()}


def _economic_metrics(
    selected: pd.DataFrame,
    source_days: int,
    selection: Mapping[str, Any],
) -> dict[str, Any]:
    if selected.empty:
        return {
            "trades": 0,
            "wins": 0,
            "stress_net_usd": 0.0,
            "stress_net_r": 0.0,
            "average_stress_r": 0.0,
            "stress_profit_factor": None,
            "maximum_closed_drawdown_r": 0.0,
            "trades_per_source_day": 0.0,
            "source_days": source_days,
            "positive_exit_month_share": 0.0,
            "minimum_direction_share": 0.0,
            "top_ten_winners_removed_net_r": 0.0,
            "bootstrap_mean_stress_r_p025": None,
            "maximum_concurrent_trades": 0,
            "maximum_open_risk_usd": 0.0,
            "direction_counts": {},
            "exit_reasons": {},
        }
    ordered = selected.sort_values(["exit_time_utc", "candidate_id"])
    values = ordered["stress_net_r"].to_numpy(dtype=float)
    wins = values[values > 0]
    losses = values[values < 0]
    equity = np.cumsum(values)
    peaks = np.maximum.accumulate(np.r_[0.0, equity])
    drawdown = peaks[1:] - equity
    months = (
        ordered.assign(exit_month=ordered["exit_time_utc"].str[:7])
        .groupby("exit_month")["stress_net_r"]
        .sum()
    )
    directions = ordered["direction"].value_counts()
    minimum_direction_share = min(
        int(directions.get("LONG", 0)), int(directions.get("SHORT", 0))
    ) / len(ordered)
    winners = np.sort(wins)[::-1]
    concurrency, open_risk = _overlap_metrics(ordered)
    return {
        "trades": len(ordered),
        "wins": len(wins),
        "stress_net_usd": float(ordered["stress_net_pnl_usd"].sum()),
        "stress_net_r": float(values.sum()),
        "average_stress_r": float(values.mean()),
        "stress_profit_factor": float(wins.sum() / -losses.sum())
        if len(losses) and -losses.sum() > 0
        else None,
        "maximum_closed_drawdown_r": float(drawdown.max()),
        "trades_per_source_day": len(ordered) / source_days if source_days else 0.0,
        "source_days": source_days,
        "positive_exit_month_share": float((months > 0).mean()),
        "minimum_direction_share": minimum_direction_share,
        "top_ten_winners_removed_net_r": float(values.sum() - winners[:10].sum()),
        "bootstrap_mean_stress_r_p025": _calendar_month_bootstrap_p025(
            ordered,
            int(selection["calendar_month_bootstrap_samples"]),
            int(selection["bootstrap_seed"]),
        ),
        "maximum_concurrent_trades": concurrency,
        "maximum_open_risk_usd": open_risk,
        "direction_counts": {key: int(value) for key, value in directions.items()},
        "exit_reasons": {
            key: int(value)
            for key, value in ordered["exit_reason"].value_counts().items()
        },
    }


def _overlap_metrics(frame: pd.DataFrame) -> tuple[int, float]:
    events = []
    for _, row in frame.iterrows():
        events.append((pd.Timestamp(row["entry_time_utc"]), 1, float(row["risk_usd"])))
        events.append((pd.Timestamp(row["exit_time_utc"]), -1, -float(row["risk_usd"])))
    concurrent = maximum_concurrent = 0
    risk = maximum_risk = 0.0
    for _, delta_count, delta_risk in sorted(
        events, key=lambda item: (item[0], item[1])
    ):
        concurrent += delta_count
        risk += delta_risk
        maximum_concurrent = max(maximum_concurrent, concurrent)
        maximum_risk = max(maximum_risk, risk)
    return maximum_concurrent, maximum_risk


def _calendar_month_bootstrap_p025(
    frame: pd.DataFrame, samples: int, seed: int
) -> float | None:
    if frame.empty:
        return None
    groups = [
        group["stress_net_r"].to_numpy(dtype=float)
        for _, group in frame.assign(exit_month=frame["exit_time_utc"].str[:7]).groupby(
            "exit_month"
        )
    ]
    rng = np.random.default_rng(seed)
    means = []
    for _ in range(samples):
        chosen = rng.integers(0, len(groups), size=len(groups))
        values = np.concatenate([groups[index] for index in chosen])
        means.append(float(values.mean()))
    return float(np.quantile(means, 0.025))


def _stage_gates(
    metrics: Mapping[str, Any], gate: Mapping[str, Any]
) -> dict[str, bool]:
    return {
        "minimum_trades": int(metrics["trades"]) >= int(gate["minimum_trades"]),
        "minimum_frequency": float(metrics["trades_per_source_day"])
        >= float(gate["minimum_trades_per_source_day"]),
        "maximum_frequency": float(metrics["trades_per_source_day"])
        <= float(gate["maximum_trades_per_source_day"]),
        "minimum_stress_profit_factor": float(metrics["stress_profit_factor"] or 0.0)
        >= float(gate["minimum_stress_profit_factor"]),
        "minimum_average_stress_r": float(metrics["average_stress_r"])
        >= float(gate["minimum_average_stress_r"]),
        "minimum_positive_exit_month_share": float(metrics["positive_exit_month_share"])
        >= float(gate["minimum_positive_exit_month_share"]),
        "maximum_closed_drawdown_r": float(metrics["maximum_closed_drawdown_r"])
        <= float(gate["maximum_closed_drawdown_r"]),
        "minimum_direction_share": float(metrics["minimum_direction_share"])
        >= float(gate["minimum_direction_share"]),
        "top_ten_winners_removed_net_positive": (
            not gate["require_top_ten_winners_removed_net_positive"]
            or float(metrics["top_ten_winners_removed_net_r"]) > 0
        ),
        "bootstrap_mean_stress_r_p025_above_zero": (
            not gate["require_bootstrap_mean_stress_r_p025_above_zero"]
            or float(metrics["bootstrap_mean_stress_r_p025"] or 0.0) > 0
        ),
    }


def _profile_sort_key(row: Mapping[str, Any]) -> tuple[float, float, float, str]:
    metrics = row["economic_metrics"]
    return (
        -float(metrics["bootstrap_mean_stress_r_p025"] or -math.inf),
        -float(metrics["stress_profit_factor"] or 0.0),
        -float(metrics["average_stress_r"]),
        str(row["profile_id"]),
    )


def _write_evaluations(path: Path, evaluations: Sequence[Mapping[str, Any]]) -> None:
    rows = []
    for evaluation in evaluations:
        rows.append(
            {
                "stage": evaluation["stage"],
                "profile_id": evaluation["profile_id"],
                "candidate_count": evaluation["candidate_count"],
                **evaluation["economic_metrics"],
                "passes": evaluation["passes"],
                "failed_quality": "|".join(
                    key for key, value in evaluation["quality"].items() if not value
                ),
                "failed_gates": "|".join(
                    key for key, value in evaluation["gates"].items() if not value
                ),
                "portfolio_rejections": json.dumps(
                    evaluation["portfolio_rejections"], sort_keys=True
                ),
            }
        )
    fields = list(dict.fromkeys(key for row in rows for key in row))
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _artifact_manifest(outputs: Mapping[str, Path]) -> dict[str, Any]:
    return {
        key: {
            "path": str(path),
            "sha256": _sha256_file(path),
            "bytes": path.stat().st_size,
        }
        for key, path in outputs.items()
        if key not in {"report_json", "report_markdown"} and path.exists()
    }


def _render(payload: Mapping[str, Any]) -> str:
    lines = [
        "# A3 ML M5 Cost-Normalized Trend V1",
        "",
        f"Classification: `{payload['classification']}`",
        "",
        f"Verified months: {payload['source_months']}. M5 rows: {payload['m5_rows']}. Base candidates: {payload['base_candidate_count']}.",
        "",
    ]
    for evaluation in payload["evaluations"]:
        metrics = evaluation["economic_metrics"]
        lines.append(
            f"- {evaluation['stage']} {evaluation['profile_id']}: {metrics['trades']} trades, "
            f"{metrics['trades_per_source_day']:.3f}/source day, stress PF "
            f"{float(metrics['stress_profit_factor'] or 0):.3f}, average "
            f"{metrics['average_stress_r']:.4f}R, pass `{evaluation['passes']}`."
        )
    lines.extend(
        [
            "",
            f"Chronological stages opened: `{payload['chronological_stages_opened']}`.",
            "",
            "This is contaminated historical research. Python demo, EA consumption, broker action, and live capital remain unauthorized.",
            "",
        ]
    )
    return "\n".join(lines)
