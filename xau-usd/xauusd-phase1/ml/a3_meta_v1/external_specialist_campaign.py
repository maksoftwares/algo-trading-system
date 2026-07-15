from __future__ import annotations

import json
import math
import os
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np
import pandas as pd

from ml.a3_meta_v1.dukascopy_m15_range_expansion import _simulate_expansion_trade
from ml.a3_meta_v1.dukascopy_m15_range_rotation import (
    M15_WIDTH_MS,
    _aggregate_m15,
    _raw_metrics,
    _raw_train_gates,
    _source_days,
    _write_csv,
)
from ml.a3_meta_v1.dukascopy_microstructure_regime import (
    _economic_metrics,
    _parse_utc_ms,
    _sha256_file,
)


class ExternalSpecialistCampaignError(RuntimeError):
    pass


def run_external_specialist_campaign(root: Path, contract_path: Path) -> Path:
    root = root.resolve()
    contract_file = (root / contract_path).resolve() if not contract_path.is_absolute() else contract_path.resolve()
    contract = json.loads(contract_file.read_text(encoding="utf-8"))
    _validate_contract(contract)
    storage_root = _storage_root(contract)
    cache_path = storage_root / str(contract["base_feature_cache"]["relative_path"])
    if not cache_path.is_file() or _sha256_file(cache_path) != contract["base_feature_cache"]["sha256"]:
        raise ExternalSpecialistCampaignError("causal enriched feature cache is missing or changed")
    frame = _aggregate_with_external(pd.read_parquet(cache_path), contract)
    all_candidates = _generate_all_candidates(frame, contract)
    windows = contract["windows"]
    segments = {
        "train": (windows["train_start_utc"], windows["train_end_exclusive_utc"]),
        "validation": (windows["train_end_exclusive_utc"], windows["validation_end_exclusive_utc"]),
        "internal_test": (windows["validation_end_exclusive_utc"], windows["internal_test_end_exclusive_utc"]),
        "exam": (windows["internal_test_end_exclusive_utc"], windows["exam_end_exclusive_utc"]),
    }
    source_days = {name: _source_days(frame, *bounds) for name, bounds in segments.items()}
    segmented = {
        name: _segment_rows(all_candidates, *bounds) for name, bounds in segments.items()
    }

    family_results: list[dict[str, Any]] = []
    opened_rows: list[dict[str, Any]] = []
    survivors: list[str] = []
    for family in contract["families"]:
        train_rows = _family_rows(segmented["train"], family)
        opened_rows.extend(train_rows)
        train_metrics = _raw_metrics(train_rows)
        train_gates = _raw_train_gates(train_metrics, contract["train_family_gate"])
        result: dict[str, Any] = {
            "family_id": family,
            "train": {"metrics": train_metrics, "gates": train_gates, "passes": all(train_gates.values())},
            "validation_opened": False,
            "validation": None,
            "internal_test_opened": False,
            "internal_test": None,
            "exam_opened": False,
            "exam": None,
        }
        if result["train"]["passes"]:
            validation_rows = _family_rows(segmented["validation"], family)
            opened_rows.extend(validation_rows)
            result["validation_opened"] = True
            result["validation"] = _evaluate_segment(
                validation_rows, source_days["validation"], contract["validation_gates"]
            )
            if result["validation"]["passes"]:
                internal_rows = _family_rows(segmented["internal_test"], family)
                opened_rows.extend(internal_rows)
                result["internal_test_opened"] = True
                result["internal_test"] = _evaluate_segment(
                    internal_rows, source_days["internal_test"], contract["test_gates"]
                )
                if result["internal_test"]["passes"]:
                    exam_rows = _family_rows(segmented["exam"], family)
                    opened_rows.extend(exam_rows)
                    result["exam_opened"] = True
                    result["exam"] = _evaluate_segment(
                        exam_rows, source_days["exam"], contract["exam_gates"]
                    )
                    if result["exam"]["passes"]:
                        survivors.append(family)
        family_results.append(result)

    outputs = {key: (root / value).resolve() for key, value in contract["outputs"].items()}
    for path in outputs.values():
        path.parent.mkdir(parents=True, exist_ok=True)
    _write_csv(outputs["candidates_csv"], opened_rows)
    _write_csv(outputs["metrics_csv"], _flatten_results(family_results))
    payload = {
        "schema_version": contract["schema_version"],
        "campaign_id": contract["campaign_id"],
        "campaign_kind": contract["campaign_kind"],
        "classification": _classification(family_results, survivors),
        "created_at_utc": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "contract": str(contract_file),
        "contract_sha256": _sha256_file(contract_file),
        "base_feature_cache": {
            "path": str(cache_path),
            "sha256": contract["base_feature_cache"]["sha256"],
            "source_inventory_sha256": contract["base_feature_cache"]["source_inventory_sha256"],
        },
        "m15_rows": len(frame),
        "source_days": source_days,
        "generated_candidate_population": len(all_candidates),
        "opened_candidate_population": len(opened_rows),
        "family_results": family_results,
        "research_survivors": survivors,
        "artifacts": {
            key: {"path": str(path), "sha256": _sha256_file(path)}
            for key, path in outputs.items()
            if key not in {"report_json"} and path.exists()
        },
        "authorization": {
            **contract["authorization"],
            "strategy_promotion_authorized": False,
            "demo_or_live_authorized": False,
        },
    }
    outputs["report_json"].write_text(json.dumps(payload, indent=2), encoding="utf-8")
    outputs["report_markdown"].write_text(_render(payload), encoding="utf-8")
    return outputs["report_json"]


def _storage_root(contract: Mapping[str, Any]) -> Path:
    variable = str(contract["storage_environment_variable"])
    raw = os.environ.get(variable, "").strip()
    if not raw:
        raise ExternalSpecialistCampaignError(f"{variable} is required")
    root = Path(raw).resolve()
    if not root.is_dir():
        raise ExternalSpecialistCampaignError(f"storage root does not exist: {root}")
    return root


def _aggregate_with_external(frame: pd.DataFrame, contract: Mapping[str, Any]) -> pd.DataFrame:
    base = _aggregate_m15(frame, contract)
    external_columns = [
        column
        for column in frame.columns
        if column.startswith(("real_yield_", "nominal_yield_", "broad_usd_", "breakeven_", "cot_", "macro_"))
    ]
    work = frame[["timestamp_ms", *external_columns]].copy()
    work["m15_bucket"] = work["timestamp_ms"] - work["timestamp_ms"] % M15_WIDTH_MS
    external = work.groupby("m15_bucket", sort=True)[external_columns].last().reset_index()
    result = base.merge(external, left_on="timestamp_ms", right_on="m15_bucket", how="left", validate="one_to_one")
    return result.drop(columns="m15_bucket").replace([np.inf, -np.inf], np.nan)


def _generate_all_candidates(frame: pd.DataFrame, contract: Mapping[str, Any]) -> list[dict[str, Any]]:
    horizon = int(contract["execution"]["maximum_holding_bars"])
    decision_hours = set(int(value) for value in contract["decision_hours_utc"])
    cooldown_ms = int(contract["signal"]["family_cooldown_minutes"]) * 60_000
    last_signal = defaultdict(lambda: -10**18)
    rows: list[dict[str, Any]] = []
    for index in range(1, len(frame) - horizon - 1):
        row = frame.iloc[index]
        decision = int(row["timestamp_ms"]) + M15_WIDTH_MS
        decision_time = datetime.fromtimestamp(decision / 1000, UTC)
        if decision_time.hour not in decision_hours or decision_time.minute != 0:
            continue
        if not _finite_market_row(row):
            continue
        for family in contract["families"]:
            if decision - last_signal[family] < cooldown_ms:
                continue
            direction = _family_direction(row, family, contract)
            if direction is None:
                continue
            outcome = _simulate_expansion_trade(frame, index, direction, contract["execution"])
            if outcome is None:
                continue
            last_signal[family] = decision
            rows.append(
                {
                    "candidate_id": f"{contract['campaign_id']}:{decision}:{family}:{direction}",
                    "campaign_id": contract["campaign_id"],
                    "family_id": family,
                    "regime": contract["campaign_kind"],
                    "direction": direction,
                    "direction_sign": 1.0 if direction == "LONG" else -1.0,
                    "decision_time_ms": decision,
                    "decision_time_utc": _iso_ms(decision),
                    **outcome,
                    **_candidate_features(row, direction),
                }
            )
    return rows


def _family_direction(row: pd.Series, family: str, contract: Mapping[str, Any]) -> str | None:
    return (
        _macro_direction(row, family, contract["signal"])
        if contract["campaign_kind"] == "MACRO_REPRICING"
        else _cftc_direction(row, family, contract["signal"])
    )


def _macro_direction(row: pd.Series, family: str, signal: Mapping[str, Any]) -> str | None:
    if not _finite_names(row, ("macro_staleness_days",)) or float(row["macro_staleness_days"]) > float(
        signal["maximum_macro_staleness_days"]
    ):
        return None
    real_1 = float(row["real_yield_10y_change_1"])
    real_5 = float(row["real_yield_10y_change_5"])
    usd_5 = float(row["broad_usd_index_change_5"])
    if family == "REAL_YIELD_SHOCK":
        if abs(real_1) < float(signal["real_yield_shock_1d_minimum"]):
            return None
        return "SHORT" if real_1 > 0 else "LONG"
    if family == "YIELD_USD_AGREEMENT":
        if abs(real_5) < float(signal["agreement_real_yield_5d_minimum"]) or abs(usd_5) < float(
            signal["agreement_broad_usd_5d_minimum"]
        ):
            return None
        yield_direction = -_sign(real_5)
        usd_direction = -_sign(usd_5)
        return _direction(yield_direction) if yield_direction == usd_direction else None
    if family == "INFLATION_REPRICING":
        inflation_5 = float(row["nominal_yield_10y_change_5"]) - real_5
        if abs(inflation_5) < float(signal["inflation_repricing_5d_minimum"]):
            return None
        direction = _sign(inflation_5)
        if usd_5 * direction > float(signal["inflation_maximum_opposing_usd_5d"]):
            return None
        return _direction(direction)
    raise ExternalSpecialistCampaignError(f"unknown macro family: {family}")


def _cftc_direction(row: pd.Series, family: str, signal: Mapping[str, Any]) -> str | None:
    if not _finite_names(row, ("cot_staleness_days",)) or float(row["cot_staleness_days"]) > float(
        signal["maximum_cot_staleness_days"]
    ):
        return None
    price_r = float(row["xau_return_60m_price"]) / float(row["atr"])
    money_change = float(row["cot_managed_money_net_share_change_1"])
    money_z = float(row["cot_managed_money_net_share_z52"])
    producer_change = float(row["cot_producer_net_share_change_1"])
    if family == "COT_TREND_CONFIRM":
        if abs(money_change) < float(signal["managed_money_change_minimum"]):
            return None
        direction = _sign(money_change)
        return _direction(direction) if price_r * direction >= float(signal["trend_confirmation_60m_atr"]) else None
    if family == "COT_CROWDED_REVERSAL":
        if abs(money_z) < float(signal["managed_money_crowded_z_minimum"]):
            return None
        direction = -_sign(money_z)
        return _direction(direction) if price_r * direction >= float(signal["reversal_confirmation_60m_atr"]) else None
    if family == "COT_PRODUCER_CONFIRM":
        if abs(producer_change) < float(signal["producer_change_minimum"]):
            return None
        direction = _sign(producer_change)
        return _direction(direction) if price_r * direction >= float(signal["producer_confirmation_60m_atr"]) else None
    raise ExternalSpecialistCampaignError(f"unknown CFTC family: {family}")


def _candidate_features(row: pd.Series, direction: str) -> dict[str, float]:
    sign = 1.0 if direction == "LONG" else -1.0
    names = (
        "real_yield_5y",
        "real_yield_10y",
        "real_yield_10y_change_1",
        "real_yield_10y_change_5",
        "nominal_yield_2y",
        "nominal_yield_10y",
        "nominal_yield_10y_change_5",
        "broad_usd_index",
        "broad_usd_index_change_1",
        "broad_usd_index_change_5",
        "breakeven_inflation_10y",
        "cot_managed_money_net_share",
        "cot_managed_money_net_share_change_1",
        "cot_managed_money_net_share_z52",
        "cot_producer_net_share",
        "cot_producer_net_share_change_1",
        "cot_producer_net_share_z52",
        "cot_swap_net_share",
        "cot_staleness_days",
        "macro_staleness_days",
        "tick_imbalance_15m",
        "book_imbalance_15m",
        "microprice_edge_15m",
        "xagusd_return_60m",
        "eurusd_return_60m",
        "usdjpy_return_60m",
        "atr_ratio_1d",
        "quote_intensity_ratio",
        "realized_volatility_ratio",
        "spread_shock_ratio",
    )
    features = {name: float(row[name]) for name in names}
    features.update(
        {
            "xau_return_15m_directional_r": sign * float(row["xau_return_15m_price"]) / float(row["atr"]),
            "xau_return_60m_directional_r": sign * float(row["xau_return_60m_price"]) / float(row["atr"]),
            "ema_gap_directional_r": sign * (float(row["ema_fast"]) - float(row["ema_slow"])) / float(row["atr"]),
            "hour_utc": float(datetime.fromtimestamp(int(row["timestamp_ms"]) / 1000, UTC).hour),
        }
    )
    return features


def _finite_market_row(row: pd.Series) -> bool:
    return float(row.get("atr", math.nan)) > 0 and _finite_names(
        row,
        (
            "atr",
            "xau_return_15m_price",
            "xau_return_60m_price",
            "ema_fast",
            "ema_slow",
            "tick_imbalance_15m",
            "book_imbalance_15m",
            "microprice_edge_15m",
            "xagusd_return_60m",
            "eurusd_return_60m",
            "usdjpy_return_60m",
            "atr_ratio_1d",
            "quote_intensity_ratio",
            "realized_volatility_ratio",
            "spread_shock_ratio",
        ),
    )


def _finite_names(row: pd.Series, names: Sequence[str]) -> bool:
    return all(name in row and math.isfinite(float(row[name])) for name in names)


def _segment_rows(rows: Sequence[Mapping[str, Any]], start: str, end: str) -> list[dict[str, Any]]:
    lo, hi = _parse_utc_ms(start), _parse_utc_ms(end)
    return [dict(row) for row in rows if lo <= int(row["decision_time_ms"]) and int(row["exit_time_ms"]) <= hi]


def _family_rows(rows: Sequence[Mapping[str, Any]], family: str) -> list[dict[str, Any]]:
    return [dict(row) for row in rows if row["family_id"] == family]


def _evaluate_segment(rows: Sequence[Mapping[str, Any]], source_days: int, gate: Mapping[str, Any]) -> dict[str, Any]:
    metrics = _economic_metrics(rows, source_days)
    gates = _economic_gates(metrics, gate)
    return {"metrics": metrics, "gates": gates, "passes": all(gates.values())}


def _economic_gates(metrics: Mapping[str, Any], gate: Mapping[str, Any]) -> dict[str, bool]:
    return {
        "minimum_trades": int(metrics["trades"]) >= int(gate["minimum_trades"]),
        "minimum_frequency": float(metrics["trades_per_source_day"]) >= float(gate["minimum_trades_per_source_day"]),
        "maximum_frequency": float(metrics["trades_per_source_day"]) <= float(gate["maximum_trades_per_source_day"]),
        "stress_profit_factor": float(metrics["stress_profit_factor"] or 0.0) >= float(gate["minimum_stress_profit_factor"]),
        "average_stress_r": float(metrics["average_stress_r"]) >= float(gate["minimum_average_stress_r"]),
        "positive_month_share": float(metrics["positive_month_share"]) >= float(gate["minimum_positive_month_share"]),
        "maximum_closed_drawdown_r": float(metrics["maximum_closed_drawdown_r"]) <= float(gate["maximum_closed_drawdown_r"]),
        "top10_winners_removed_net_positive": (
            not bool(gate["require_top10_winners_removed_net_positive"])
            or float(metrics["top10_winners_removed_net_r"]) > 0
        ),
    }


def _flatten_results(results: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for result in results:
        for segment in ("train", "validation", "internal_test", "exam"):
            payload = result.get(segment)
            if not payload:
                continue
            rows.append(
                {
                    "family_id": result["family_id"],
                    "segment": segment,
                    **payload["metrics"],
                    "passes": payload["passes"],
                    "failed_gates": "|".join(key for key, value in payload["gates"].items() if not value),
                }
            )
    return rows


def _classification(results: Sequence[Mapping[str, Any]], survivors: Sequence[str]) -> str:
    if survivors:
        return "EXTERNAL_SPECIALIST_RESEARCH_SURVIVOR"
    if not any(row["train"]["passes"] for row in results):
        return "EXTERNAL_SPECIALISTS_TRAIN_REJECTED"
    if not any(row["validation"] and row["validation"]["passes"] for row in results):
        return "EXTERNAL_SPECIALISTS_VALIDATION_REJECTED"
    if not any(row["internal_test"] and row["internal_test"]["passes"] for row in results):
        return "EXTERNAL_SPECIALISTS_INTERNAL_TEST_REJECTED"
    return "EXTERNAL_SPECIALISTS_EXAM_REJECTED"


def _render(payload: Mapping[str, Any]) -> str:
    lines = [
        f"# {payload['campaign_id']}",
        "",
        f"Classification: `{payload['classification']}`",
        "",
    ]
    for result in payload["family_results"]:
        train = result["train"]["metrics"]
        lines.append(
            f"- {result['family_id']} train: {train['trades']} trades, stress PF {float(train['stress_profit_factor'] or 0):.3f}, average {train['average_stress_r']:.4f}R, pass `{result['train']['passes']}`."
        )
        for segment in ("validation", "internal_test", "exam"):
            if result[segment]:
                metrics = result[segment]["metrics"]
                lines.append(
                    f"- {result['family_id']} {segment}: {metrics['trades']} trades, {metrics['trades_per_source_day']:.3f}/day, stress PF {float(metrics['stress_profit_factor'] or 0):.3f}, average {metrics['average_stress_r']:.4f}R, pass `{result[segment]['passes']}`."
                )
    lines.extend(["", f"Research survivors: `{payload['research_survivors']}`.", "", "No demo, live, EA, or broker action is authorized.", ""])
    return "\n".join(lines)


def _validate_contract(contract: Mapping[str, Any]) -> None:
    if contract.get("schema_version") != "a3_ml_external_specialists_v1":
        raise ExternalSpecialistCampaignError("unexpected external-specialist schema")
    if contract.get("campaign_kind") not in {"MACRO_REPRICING", "CFTC_POSITIONING"}:
        raise ExternalSpecialistCampaignError("unsupported campaign kind")
    if contract.get("execution", {}).get("same_bar_collision_policy") != "STOP_FIRST":
        raise ExternalSpecialistCampaignError("collision policy must be STOP_FIRST")
    authorization = contract.get("authorization", {})
    for key in (
        "validation_requires_train_family_pass",
        "internal_test_requires_validation_pass",
        "exam_requires_internal_test_pass",
    ):
        if not authorization.get(key):
            raise ExternalSpecialistCampaignError("chronological firewall weakened")
    for key in ("python_demo_predictions_authorized", "ea_consumption_authorized", "broker_action_authorized"):
        if authorization.get(key):
            raise ExternalSpecialistCampaignError(f"{key} must remain false")


def _sign(value: float) -> int:
    return 1 if value > 0 else -1


def _direction(sign: int) -> str:
    return "LONG" if sign > 0 else "SHORT"


def _iso_ms(value: int) -> str:
    return datetime.fromtimestamp(value / 1000, UTC).isoformat(timespec="milliseconds").replace("+00:00", "Z")
