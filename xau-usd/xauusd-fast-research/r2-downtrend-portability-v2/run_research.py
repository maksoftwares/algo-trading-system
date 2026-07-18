from __future__ import annotations

from datetime import UTC, datetime
import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from src import downtrend
from src.contract import (
    definition_lock_path,
    load_config,
    outcome_marker_path,
    output_path,
    validate_definition_lock,
    write_json,
)


def _json_value(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _json_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_value(item) for item in value]
    if isinstance(value, (pd.Timestamp, datetime)):
        return pd.Timestamp(value).isoformat()
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating, float)):
        number = float(value)
        if np.isposinf(number):
            return "inf"
        if np.isneginf(number):
            return "-inf"
        if np.isnan(number):
            return None
        return number
    if isinstance(value, (np.bool_,)):
        return bool(value)
    return value


def _write_marker(config: dict[str, Any], lock: dict[str, Any]) -> None:
    marker = outcome_marker_path(config)
    if marker.exists():
        raise RuntimeError(f"One-shot outcome marker already exists: {marker}")
    write_json(
        marker,
        {
            "schema_version": "xauusd_r2_downtrend_outcomes_opened_v2",
            "opened_utc": datetime.now(UTC).isoformat(),
            "definition_contract_sha256": lock["definition_contract_sha256"],
            "single_outcome_opening": True,
            "paid_data_request_made": False,
            "databento_used": False,
            "broker_action_performed": False,
            "training_authorized": False,
            "execution_authorized": False,
        },
    )


def _metrics_frame(rows: list[dict[str, Any]]) -> pd.DataFrame:
    result = pd.DataFrame(rows).copy()
    result["gate_checks"] = result["gate_checks"].map(
        lambda value: json.dumps(value, sort_keys=True, separators=(",", ":"))
    )
    return result


def _format_number(value: Any, decimals: int) -> str:
    if value in ("inf", "-inf"):
        return str(value)
    if value is None:
        return "NA"
    return f"{float(value):.{decimals}f}"


def _markdown(result: dict[str, Any]) -> str:
    lines = [
        "# XAUUSD R2 Downtrend Portability V2",
        "",
        f"Decision: `{result['decision']}`",
        "",
        "| Candidate | Window | Trades | PF | Avg R | Net R | DD R | Holm p | Gate |",
        "|---|---|---:|---:|---:|---:|---:|---:|---|",
    ]
    for row in result["metrics"]:
        lines.append(
            "| {candidate_id} | {window} | {trades} | {pf} | {average} | "
            "{net} | {drawdown} | {holm} | {gate} |".format(
                **row,
                pf=_format_number(row["stress_pf"], 3),
                average=_format_number(row["average_stress_r"], 3),
                net=_format_number(row["stress_net_r"], 3),
                drawdown=_format_number(row["closed_drawdown_r"], 3),
                holm=_format_number(row["holm_pvalue"], 4),
                gate="PASS" if row["gate_pass"] else "FAIL",
            )
        )
    lines.extend(
        [
            "",
            f"Qualified candidates: `{', '.join(result['qualified_candidates']) or 'NONE'}`",
            "",
            f"Distinct mechanism survivors: `{', '.join(result['distinct_survivors']) or 'NONE'}`",
            "",
            "The 2022-2026 source period is diagnostic and cannot create qualification.",
            "No result grants model, EA, demo, live, broker, Databento, or paid-data authority.",
        ]
    )
    return "\n".join(lines) + "\n"


def _source_period_comparison(
    metrics: list[dict[str, Any]], config: dict[str, Any]
) -> list[dict[str, Any]]:
    diagnostic = {
        str(row["candidate_id"]): row
        for row in metrics
        if row["window"] == "source_period_diagnostic"
    }
    rows: list[dict[str, Any]] = []
    for candidate_id, reference in config["mt5_reference"]["candidates"].items():
        observed = diagnostic[candidate_id]
        rows.append(
            {
                "candidate_id": candidate_id,
                **reference,
                "dukascopy_trades": int(observed["trades"]),
                "dukascopy_stress_profit_factor": observed["stress_pf"],
            }
        )
    return rows


def _execution_audit(trades: pd.DataFrame) -> dict[str, Any]:
    if trades.empty:
        return {
            "raw_tick_trades": 0,
            "exit_reasons": {},
            "m5_both_thresholds_resolved_by_ticks": 0,
            "maximum_entry_delay_ms": 0,
            "median_entry_delay_ms": 0.0,
        }
    return {
        "raw_tick_trades": int(trades["raw_tick_execution"].fillna(False).sum()),
        "exit_reasons": {
            str(key): int(value)
            for key, value in trades["exit_reason"].value_counts().items()
        },
        "m5_both_thresholds_resolved_by_ticks": int(
            trades["m5_both_thresholds_resolved_by_ticks"].fillna(False).sum()
        ),
        "maximum_entry_delay_ms": int(trades["entry_delay_ms"].max()),
        "median_entry_delay_ms": float(trades["entry_delay_ms"].median()),
    }


def _artifact_manifest(config: dict[str, Any], names: list[str]) -> dict[str, Any]:
    directory = output_path(config, "result_json").parent
    artifacts: dict[str, Any] = {}
    for name in names:
        path = directory / name
        artifacts[name] = {
            "bytes": int(path.stat().st_size),
            "sha256": downtrend.sha256_file(path),
        }
    return {
        "schema_version": "xauusd_r2_downtrend_artifacts_v2",
        "artifacts": artifacts,
        "training_authorized": False,
        "execution_authorized": False,
    }


def main() -> int:
    config = load_config()
    lock_path = definition_lock_path(config)
    if not lock_path.is_file():
        raise RuntimeError("Definition contract must be locked before outcomes")
    lock = json.loads(lock_path.read_text(encoding="utf-8"))
    validate_definition_lock(lock, config)
    _write_marker(config, lock)

    data = downtrend.prepare_research_data(config)
    states = downtrend.prepare_regime_states(data, config)
    candidates = downtrend.generate_all_candidates(data, states, config)
    tick_store = downtrend.VerifiedTickStore(
        downtrend.storage_root(config), config
    )
    candidate_ledger, all_trades = downtrend.simulate_candidates(
        data.m5, candidates, config, tick_store
    )
    trades = downtrend.apply_account_policy(all_trades, config)
    metrics = downtrend.evaluate_windows(trades, data.m5, config)
    qualified, distinct = downtrend.select_qualified(metrics, config)

    result = {
        "schema_version": "xauusd_r2_downtrend_portability_v2",
        "completed_utc": datetime.now(UTC).isoformat(),
        "definition_contract_sha256": lock["definition_contract_sha256"],
        "decision": "R2_DOWNTREND_SPECIALIST_SURVIVOR" if distinct else "NO_R2_DOWNTREND_SPECIALIST_SURVIVOR",
        "attempts": config["attempts"],
        "campaign_attempts_before_v1": config["research_controls"]["campaign_attempts_before_v1"],
        "cumulative_campaign_attempts": config["research_controls"]["new_attempt_last"],
        "candidate_rows": int(len(candidates)),
        "boundary_candidates_removed": int(
            candidates.attrs.get("boundary_candidates_removed", 0)
        ),
        "candidate_rows_by_id": (
            {
                str(key): int(value)
                for key, value in candidates.groupby("candidate_id").size().items()
            }
            if not candidates.empty
            else {}
        ),
        "execution_rows": int(len(all_trades)),
        "policy_trade_rows": int(len(trades)),
        "execution_audit": _execution_audit(all_trades),
        "rejection_counts": (
            {
                str(key): int(value)
                for key, value in candidate_ledger.loc[
                    ~candidate_ledger["accepted"].fillna(False), "rejection_reason"
                ].value_counts().items()
            }
            if not candidate_ledger.empty
            else {}
        ),
        "metrics": metrics,
        "source_period_mt5_comparison": _source_period_comparison(metrics, config),
        "qualified_candidates": qualified,
        "distinct_survivors": distinct,
        "data_evidence": data.evidence,
        "single_outcome_opening": True,
        "research_only": True,
        "parameter_search_count": 0,
        "paid_data_request_made": False,
        "databento_used": False,
        "broker_action_performed": False,
        "training_authorized": False,
        "execution_authorized": False,
    }
    result = _json_value(result)

    metrics_path = output_path(config, "metrics")
    trades_path = output_path(config, "trades")
    result_path = output_path(config, "result_json")
    markdown_path = output_path(config, "result_markdown")
    metrics_path.parent.mkdir(parents=True, exist_ok=True)
    _metrics_frame(metrics).to_csv(metrics_path, index=False)
    trades.to_parquet(trades_path, index=False)
    write_json(result_path, result)
    markdown_path.write_text(_markdown(result), encoding="utf-8")

    manifest_names = [
        definition_lock_path(config).name,
        outcome_marker_path(config).name,
        metrics_path.name,
        trades_path.name,
        result_path.name,
        markdown_path.name,
    ]
    write_json(
        output_path(config, "artifact_manifest"),
        _artifact_manifest(config, manifest_names),
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
