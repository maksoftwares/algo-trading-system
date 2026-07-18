from __future__ import annotations

import argparse
from datetime import UTC, datetime
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import sys
from typing import Any, Mapping

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "outputs"
CONFIG_PATH = ROOT / "config" / "trailing_trend_specialists_v1.json"
PREFIX = "TRAILING_TREND_SPECIALISTS"
LOCK_PATH = OUTPUT / f"{PREFIX}_CONTRACT_LOCK.json"
MANIFEST_PATH = OUTPUT / f"{PREFIX}_POLICY_MANIFEST.csv"
RESULT_PATH = OUTPUT / f"{PREFIX}_RESULT.json"
RESULT_MD_PATH = OUTPUT / f"{PREFIX}_RESULT.md"
ARTIFACT_MANIFEST_PATH = OUTPUT / f"{PREFIX}_ARTIFACT_MANIFEST.json"
STAGES = ("discovery", "confirmation")


def _load_module(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(4 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _canonical_hash(payload: Mapping[str, Any]) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("ascii")
    ).hexdigest()


def _json_ready(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _json_ready(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    if isinstance(value, (pd.Timestamp, datetime)):
        return value.isoformat()
    if isinstance(value, np.generic):
        return _json_ready(value.item())
    if isinstance(value, float) and not math.isfinite(value):
        return "Infinity" if value > 0.0 else None
    return value


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    temporary = path.with_suffix(path.suffix + ".part")
    temporary.write_text(
        json.dumps(_json_ready(payload), indent=2, sort_keys=True, allow_nan=False)
        + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


def _write_csv(path: Path, frame: pd.DataFrame) -> None:
    temporary = path.with_suffix(path.suffix + ".part")
    frame.to_csv(temporary, index=False)
    os.replace(temporary, path)


def _verify_contract(config: Mapping[str, Any]) -> dict[str, Any]:
    if not LOCK_PATH.is_file() or not MANIFEST_PATH.is_file():
        raise FileNotFoundError("Run lock_contract.py before opening outcomes")
    lock_module = _load_module(
        "trailing_trend_contract_verify", ROOT / "lock_contract.py"
    )
    lock = json.loads(LOCK_PATH.read_text(encoding="utf-8"))
    claimed = str(lock["contract_sha256"])
    body = dict(lock)
    body.pop("contract_sha256")
    if _canonical_hash(body) != claimed:
        raise ValueError("Trailing-trend contract hash mismatch")
    paths = lock_module.contract_paths(config)
    if set(paths) != set(lock["files"]):
        raise ValueError("Trailing-trend contract file set changed")
    for name, path in paths.items():
        if _sha256(path) != lock["files"][name]:
            raise ValueError(f"Contract input changed: {name}")
    if _sha256(MANIFEST_PATH) != lock["policy_manifest_sha256"]:
        raise ValueError("Policy manifest changed")
    return lock


def _marker_path(stage: str) -> Path:
    return OUTPUT / f"{PREFIX}_{stage.upper()}_OUTCOMES_OPENED.json"


def _metrics_path(stage: str) -> Path:
    return OUTPUT / f"{PREFIX}_{stage.upper()}_METRICS.csv"


def _trades_path(stage: str) -> Path:
    return OUTPUT / f"{PREFIX}_{stage.upper()}_TRADES.csv"


def _advancement_path(stage: str) -> Path:
    return OUTPUT / f"{PREFIX}_{stage.upper()}_ADVANCEMENT_LOCK.json"


def _write_marker(stage: str, contract_hash: str) -> None:
    marker = _marker_path(stage)
    if marker.exists() or _metrics_path(stage).exists():
        raise RuntimeError(f"{stage} outcomes were already opened")
    _write_json(
        marker,
        {
            "schema_version": "xauusd_trailing_trend_stage_open_v1",
            "stage": stage,
            "opened_utc": datetime.now(UTC).isoformat(),
            "contract_sha256": contract_hash,
            "training_authorized": False,
            "execution_authorized": False,
        },
    )


def _verify_advancement(stage: str, contract_hash: str) -> dict[str, Any]:
    path = _advancement_path(stage)
    if not path.is_file():
        raise FileNotFoundError(f"Missing {stage} advancement lock")
    payload = json.loads(path.read_text(encoding="utf-8"))
    claimed = str(payload["advancement_sha256"])
    body = dict(payload)
    body.pop("advancement_sha256")
    if _canonical_hash(body) != claimed:
        raise ValueError(f"{stage} advancement hash mismatch")
    if payload["contract_sha256"] != contract_hash:
        raise ValueError(f"{stage} advancement contract mismatch")
    if payload["policy_manifest_sha256"] != _sha256(MANIFEST_PATH):
        raise ValueError(f"{stage} policy manifest mismatch")
    if payload["metrics_sha256"] != _sha256(_metrics_path(stage)):
        raise ValueError(f"{stage} metrics mismatch")
    return payload


def _stage_manifest(stage: str, contract_hash: str) -> pd.DataFrame:
    manifest = pd.read_csv(MANIFEST_PATH, dtype={"policy_id": str})
    if stage == "discovery":
        return manifest
    advancement = _verify_advancement("discovery", contract_hash)
    selected_ids = [str(value) for value in advancement["selected_policy_ids"]]
    if not selected_ids:
        raise RuntimeError(
            "confirmation is sealed because discovery selected no policy"
        )
    selected = manifest.loc[manifest["policy_id"].isin(selected_ids)].copy()
    if set(selected["policy_id"]) != set(selected_ids) or len(selected) != len(
        selected_ids
    ):
        raise ValueError("Discovery advancement references unknown policies")
    return selected.sort_values("attempt_no", kind="mergesort").reset_index(drop=True)


def _metrics_for_csv(metrics: pd.DataFrame) -> pd.DataFrame:
    output = metrics.copy()
    for column in ("segment_metrics", "gate_checks"):
        output[f"{column}_json"] = output[column].map(
            lambda value: json.dumps(
                _json_ready(value), sort_keys=True, separators=(",", ":")
            )
        )
    return output.drop(columns=["segment_metrics", "gate_checks"])


def _evaluate(
    stage: str,
    incoming: pd.DataFrame,
    config: Mapping[str, Any],
    m5: pd.DataFrame,
    trend: Any,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    stage_start, stage_end = map(pd.Timestamp, config["windows"][stage])
    aggregates: dict[str, pd.DataFrame] = {}
    for timeframe in sorted(incoming["timeframe"].astype(str).unique()):
        settings = config["aggregation"][timeframe]
        aggregates[timeframe] = trend.aggregate_bars(
            m5,
            int(settings["minutes"]),
            timeframe,
            int(settings["minimum_m5_rows"]),
        )
    raw_metrics: dict[str, dict[str, Any]] = {}
    ledgers: list[pd.DataFrame] = []
    for policy in incoming.to_dict(orient="records"):
        policy_id = str(policy["policy_id"])
        timeframe = str(policy["timeframe"])
        prepared = trend.prepare_policy_bars(aggregates[timeframe], policy)
        trades = trend.simulate_policy(
            m5,
            prepared,
            policy,
            config["execution"],
            stage_start,
            stage_end,
        )
        metrics = trend.summarize(
            trades,
            m5,
            stage_start,
            stage_end,
            config["segments"][stage],
            int(config["gates"][stage][timeframe]["top_winners_removed"]),
        )
        metrics.update(
            {
                "policy_id": policy_id,
                "attempt_no": int(policy["attempt_no"]),
                "timeframe": timeframe,
                "mechanic": str(policy["mechanic"]),
            }
        )
        raw_metrics[policy_id] = metrics
        if not trades.empty:
            ledgers.append(trades)
    adjusted = trend.holm_adjust(
        {
            policy_id: float(metrics["trade_pvalue"])
            for policy_id, metrics in raw_metrics.items()
        }
    )
    metric_rows = []
    for policy_id, metrics in raw_metrics.items():
        qvalue = float(adjusted[policy_id])
        gate = config["gates"][stage][str(metrics["timeframe"])]
        checks = trend.gate_checks(metrics, gate, qvalue)
        metrics["holm_adjusted_pvalue"] = qvalue
        metrics["gate_checks"] = checks
        metrics["gate_pass"] = bool(all(checks.values()))
        metric_rows.append(metrics)
    metric_frame = pd.DataFrame(metric_rows).sort_values(
        "attempt_no", kind="mergesort"
    )
    trades_frame = (
        pd.concat(ledgers, ignore_index=True)
        .sort_values(["entry_time", "attempt_no"], kind="mergesort")
        .reset_index(drop=True)
        if ledgers
        else pd.DataFrame()
    )
    return metric_frame.reset_index(drop=True), trades_frame


def _write_advancement(
    stage: str, contract_hash: str, selected: pd.DataFrame
) -> dict[str, Any]:
    payload = {
        "schema_version": "xauusd_trailing_trend_advancement_v1",
        "stage": stage,
        "created_utc": datetime.now(UTC).isoformat(),
        "contract_sha256": contract_hash,
        "policy_manifest_sha256": _sha256(MANIFEST_PATH),
        "metrics_sha256": _sha256(_metrics_path(stage)),
        "selected_policy_ids": selected["policy_id"].astype(str).tolist(),
        "selected_policy_count": int(len(selected)),
        "training_authorized": False,
        "execution_authorized": False,
    }
    payload["advancement_sha256"] = _canonical_hash(payload)
    _write_json(_advancement_path(stage), payload)
    return payload


def _load_result(contract_hash: str, config: Mapping[str, Any]) -> dict[str, Any]:
    if RESULT_PATH.is_file():
        result = json.loads(RESULT_PATH.read_text(encoding="utf-8"))
        if result["contract_sha256"] != contract_hash:
            raise ValueError("Result contract mismatch")
        return result
    policies = config["policies"]
    return {
        "schema_version": config["schema_version"],
        "contract_sha256": contract_hash,
        "attempt_first": min(int(policy["attempt_no"]) for policy in policies),
        "attempt_last": max(int(policy["attempt_no"]) for policy in policies),
        "registered_policy_count": len(policies),
        "stages": {},
        "research_only": True,
        "training_authorized": False,
        "execution_authorized": False,
    }


def _decision(stage: str, selected_count: int) -> str:
    if stage == "discovery":
        return (
            "TRAILING_TREND_DISCOVERY_PASS_ADVANCE"
            if selected_count
            else "NO_TRAILING_TREND_V1_DISCOVERY_SURVIVOR"
        )
    return (
        "TRAILING_TREND_NEAR_SURVIVOR_REQUIRES_INDEPENDENT_REPLICATION_AND_SHADOW"
        if selected_count
        else "NO_TRAILING_TREND_V1_CONFIRMATION_SURVIVOR"
    )


def _format_metric(value: Any, digits: int) -> str:
    if value == "Infinity" or (
        isinstance(value, (int, float)) and math.isinf(float(value))
    ):
        return "inf"
    return f"{float(value):.{digits}f}"


def _render(result: Mapping[str, Any]) -> str:
    lines = [
        "# XAUUSD Trailing Trend Specialists V1 Result",
        "",
        f"Decision: `{result.get('decision', 'IN_PROGRESS')}`",
        "",
        f"Registered attempts: **{result['attempt_first']:,}-{result['attempt_last']:,}** "
        f"({result['registered_policy_count']} fixed policies; no parameter search)",
        "",
        "| Stage | Incoming | Gate pass | Advanced | Best PF | Best average R | Lowest Holm p |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for stage in STAGES:
        row = result.get("stages", {}).get(stage)
        if row is None:
            lines.append(f"| {stage} | SEALED | SEALED | SEALED | SEALED | SEALED | SEALED |")
            continue
        lines.append(
            f"| {stage} | {row['incoming_policy_count']} | "
            f"{row['gate_pass_policy_count']} | {row['advanced_policy_count']} | "
            f"{_format_metric(row['best_stress_pf'], 3)} | "
            f"{_format_metric(row['best_average_stress_r'], 3)} | "
            f"{_format_metric(row['lowest_holm_adjusted_pvalue'], 4)} |"
        )
    lines.extend(
        [
            "",
            "Significance is evaluated on non-overlapping closed trades and corrected across all incoming policies. Confirmation remains sealed unless the discovery advancement lock names an unchanged passer.",
            "",
            "Research only. No model, EA, demo, live, broker, Databento, or paid-data authority is granted.",
            "",
        ]
    )
    return "\n".join(lines)


def _update_artifact_manifest(contract_hash: str) -> None:
    artifacts = {}
    for path in sorted(OUTPUT.iterdir()):
        if (
            not path.is_file()
            or path == ARTIFACT_MANIFEST_PATH
            or path.suffix == ".part"
        ):
            continue
        artifacts[path.name] = {"bytes": path.stat().st_size, "sha256": _sha256(path)}
    _write_json(
        ARTIFACT_MANIFEST_PATH,
        {
            "contract_sha256": contract_hash,
            "artifacts": artifacts,
            "training_authorized": False,
            "execution_authorized": False,
        },
    )


def run_stage(stage: str) -> dict[str, Any]:
    if stage not in STAGES:
        raise KeyError(stage)
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    lock = _verify_contract(config)
    contract_hash = str(lock["contract_sha256"])
    incoming = _stage_manifest(stage, contract_hash)
    _write_marker(stage, contract_hash)
    trend = _load_module("trailing_trend_run", ROOT / "src" / "trend.py")
    data = _load_module(
        "trailing_trend_data_run",
        (ROOT / config["source"]["data_source"]).resolve(),
    )
    m5, evidence = data.load_m5(config)
    metrics, trades = _evaluate(stage, incoming, config, m5, trend)
    selected = metrics.loc[metrics["gate_pass"]].copy()
    _write_csv(_metrics_path(stage), _metrics_for_csv(metrics))
    _write_csv(_trades_path(stage), trades)
    advancement = _write_advancement(stage, contract_hash, selected)
    result = _load_result(contract_hash, config)
    result["stages"][stage] = {
        "completed_utc": datetime.now(UTC).isoformat(),
        "incoming_policy_count": int(len(incoming)),
        "gate_pass_policy_count": int(metrics["gate_pass"].sum()),
        "advanced_policy_count": int(len(selected)),
        "advanced_policy_ids": selected["policy_id"].astype(str).tolist(),
        "trade_rows": int(len(trades)),
        "best_stress_pf": float(metrics["stress_pf"].max()),
        "best_average_stress_r": float(metrics["average_stress_r"].max()),
        "lowest_holm_adjusted_pvalue": float(
            metrics["holm_adjusted_pvalue"].min()
        ),
        "metrics_sha256": _sha256(_metrics_path(stage)),
        "trades_sha256": _sha256(_trades_path(stage)),
        "advancement_sha256": advancement["advancement_sha256"],
    }
    result["decision"] = _decision(stage, len(selected))
    result["latest_completed_stage"] = stage
    result["data_evidence"] = evidence
    result["data_evidence"]["paid_data_request_made"] = False
    result["data_evidence"]["databento_used"] = False
    result["cumulative_campaign_attempts"] = int(result["attempt_last"])
    _write_json(RESULT_PATH, result)
    RESULT_MD_PATH.write_text(_render(result), encoding="utf-8")
    _update_artifact_manifest(contract_hash)
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("stage", choices=STAGES)
    args = parser.parse_args()
    result = run_stage(args.stage)
    print(json.dumps(_json_ready(result), indent=2, sort_keys=True, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
