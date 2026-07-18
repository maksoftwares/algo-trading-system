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
RESEARCH_ROOT = ROOT.parent
CONFIG_PATH = ROOT / "config" / "event_reaction_corrected_v4.json"
STAGES = ("historical_replication", "related_confirmation")
PREFIX = "CORRECTED_EVENT"


def _load_module(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


EVENT = _load_module(
    "corrected_event_stage_engine",
    RESEARCH_ROOT / "macro-event-reaction-replication-v2" / "src" / "event_reaction.py",
)
DATA = _load_module(
    "corrected_event_stage_data",
    RESEARCH_ROOT / "independent-specialists-v1" / "src" / "data.py",
)


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
    frame.to_csv(temporary, index=False, lineterminator="\n")
    os.replace(temporary, path)


def _paths(output: Path, stage: str) -> dict[str, Path]:
    prefix = f"{PREFIX}_{stage.upper()}"
    return {
        "marker": output / f"{prefix}_OUTCOMES_OPENED.json",
        "outcomes": output / f"{prefix}_OUTCOMES.parquet",
        "execution_audit": output / f"{prefix}_EXECUTION_AUDIT.json",
        "metrics": output / f"{prefix}_METRICS.csv",
        "diagnostics": output / f"{prefix}_DIAGNOSTICS.csv",
        "survivors": output / f"{prefix}_SURVIVORS.csv",
        "advancement": output / f"{prefix}_ADVANCEMENT_LOCK.json",
        "result": output / f"{prefix}_RESULT.json",
        "markdown": output / f"{prefix}_RESULT.md",
    }


def _verify_contract(config: Mapping[str, Any]) -> dict[str, Any]:
    output = ROOT / config["outputs"]["directory"]
    lock_path = output / config["outputs"]["contract_lock"]
    if not lock_path.is_file():
        raise FileNotFoundError("Run lock_contract.py before opening corrected outcomes")
    lock_module = _load_module("corrected_event_contract_verify", ROOT / "lock_contract.py")
    lock = json.loads(lock_path.read_text(encoding="utf-8"))
    claimed = str(lock["contract_sha256"])
    body = dict(lock)
    body.pop("contract_sha256")
    if _canonical_hash(body) != claimed:
        raise ValueError("Corrected event contract hash mismatch")
    paths = lock_module.contract_paths(config)
    if set(paths) != set(lock["files"]):
        raise ValueError("Corrected event contract file set changed")
    for name, path in paths.items():
        if _sha256(path) != lock["files"][name]:
            raise ValueError(f"Corrected event contract input changed: {name}")
    return lock


def _eligible_policies(
    config: Mapping[str, Any], output: Path, stage: str, contract_hash: str
) -> pd.DataFrame:
    policies = pd.DataFrame(config["policies"])
    if stage == "historical_replication":
        return policies
    prior = _paths(output, "historical_replication")
    if not prior["advancement"].is_file():
        raise FileNotFoundError("Corrected historical advancement lock is missing")
    advancement = json.loads(prior["advancement"].read_text(encoding="utf-8"))
    claimed = str(advancement["advancement_sha256"])
    body = dict(advancement)
    body.pop("advancement_sha256")
    if _canonical_hash(body) != claimed:
        raise ValueError("Corrected historical advancement hash mismatch")
    if advancement["contract_sha256"] != contract_hash:
        raise ValueError("Corrected advancement contract mismatch")
    if advancement["metrics_sha256"] != _sha256(prior["metrics"]):
        raise ValueError("Corrected historical metrics changed")
    selected_ids = [str(value) for value in advancement["selected_policy_ids"]]
    if not selected_ids:
        raise RuntimeError("Related confirmation is sealed because historical selected none")
    selected = policies.loc[policies["policy_id"].isin(selected_ids)].copy()
    if set(selected["policy_id"]) != set(selected_ids):
        raise ValueError("Corrected advancement names an unknown policy")
    return selected.reset_index(drop=True)


def _diagnostics(outcomes: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for policy_id, policy_frame in outcomes.groupby("policy_id", sort=True):
        for dimension in ("regime", "direction", "exit_reason"):
            for key, frame in policy_frame.groupby(dimension, sort=True):
                rows.append(
                    {
                        "policy_id": str(policy_id),
                        "dimension": dimension,
                        "value": str(key),
                        "trades": int(len(frame)),
                        "stress_net_r": float(frame["stress_net_r"].sum()),
                        "average_stress_r": float(frame["stress_net_r"].mean()),
                    }
                )
    return pd.DataFrame(rows)


def _write_advancement(
    path: Path,
    stage: str,
    contract_hash: str,
    metrics_path: Path,
    outcomes_path: Path,
    selected: pd.DataFrame,
) -> dict[str, Any]:
    payload = {
        "schema_version": "xauusd_corrected_event_advancement_v4",
        "stage": stage,
        "created_utc": datetime.now(UTC).isoformat(),
        "contract_sha256": contract_hash,
        "metrics_sha256": _sha256(metrics_path),
        "outcomes_sha256": _sha256(outcomes_path),
        "selected_policy_ids": selected["policy_id"].astype(str).tolist(),
        "selected_policy_count": int(len(selected)),
        "training_authorized": False,
        "execution_authorized": False,
    }
    payload["advancement_sha256"] = _canonical_hash(payload)
    _write_json(path, payload)
    return payload


def _update_artifact_manifest(output: Path, contract_hash: str) -> None:
    path = output / f"{PREFIX}_ARTIFACT_MANIFEST.json"
    artifacts = {}
    for artifact in sorted(output.iterdir()):
        if not artifact.is_file() or artifact == path or artifact.suffix == ".part":
            continue
        artifacts[artifact.name] = {
            "bytes": artifact.stat().st_size,
            "sha256": _sha256(artifact),
        }
    _write_json(
        path,
        {
            "contract_sha256": contract_hash,
            "artifacts": artifacts,
            "training_authorized": False,
            "execution_authorized": False,
        },
    )


def _render(stage: str, payload: Mapping[str, Any], metrics: pd.DataFrame) -> str:
    lines = [
        f"# XAUUSD Corrected Event V4 {stage.replace('_', ' ').title()}",
        "",
        f"Decision: `{payload['decision']}`",
        f"Policies evaluated: **{payload['policy_rows']}**",
        f"Events in stage: **{payload['event_rows']}**",
        f"Signals in stage: **{payload['candidate_rows']}**",
        f"Executed outcomes: **{payload['outcome_rows']}**",
        f"Stops / targets / timeouts: **{payload['execution_audit']['stop_outcomes']} / "
        f"{payload['execution_audit']['target_outcomes']} / "
        f"{payload['execution_audit']['max_hold_outcomes']}**",
        f"Survivors: **{payload['survivor_rows']}**",
        "",
        "| Policy | Trades / events | PF | Avg R | DD R | Top 3 removed R | Year + | Holm q | Result |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    display = metrics.sort_values(
        ["stage_pass", "average_stress_r"],
        ascending=[False, False],
        kind="mergesort",
    )
    for row in display.itertuples(index=False):
        lines.append(
            f"| `{row.policy_id}` | {int(row.trades)} / {int(row.event_count)} | "
            f"{float(row.stress_pf):.3f} | {float(row.average_stress_r):.3f} | "
            f"{float(row.closed_drawdown_r):.3f} | "
            f"{float(row.top_winners_removed_stress_net_r):.3f} | "
            f"{float(row.positive_active_year_share):.1%} | "
            f"{float(row.holm_qvalue):.4f} | "
            f"{'PASS' if bool(row.stage_pass) else 'FAIL'} |"
        )
    lines.extend(
        [
            "",
            "Stop and target ordering was resolved from verified raw Dukascopy ticks.",
            "Only this stage was labeled; later-stage outcomes remain unmaterialized.",
            "Related confirmation is not represented as a pristine blind exam.",
            "No result grants model, EA, demo, live, broker, paid-data, or Databento authority.",
            "",
        ]
    )
    return "\n".join(lines)


def run_stage(stage: str) -> dict[str, Any]:
    if stage not in STAGES:
        raise KeyError(stage)
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    lock = _verify_contract(config)
    contract_hash = str(lock["contract_sha256"])
    output = ROOT / config["outputs"]["directory"]
    paths = _paths(output, stage)
    if paths["result"].exists() or paths["marker"].exists():
        raise RuntimeError(f"Refusing to rerun corrected event stage: {stage}")
    policies = _eligible_policies(config, output, stage, contract_hash)
    candidates = pd.read_parquet(output / config["outputs"]["candidates"])
    calendar = pd.read_csv(
        output / config["outputs"]["calendar"], parse_dates=["event_time_utc"]
    )
    start, end = map(pd.Timestamp, config["windows"][stage])
    selected_ids = set(policies["policy_id"].astype(str))
    stage_candidates = candidates.loc[
        candidates["feature_time_utc"].ge(start)
        & candidates["feature_time_utc"].lt(end)
        & candidates["policy_id"].isin(selected_ids)
    ].copy()
    stage_calendar = calendar.loc[
        calendar["event_time_utc"].ge(start)
        & calendar["event_time_utc"].lt(end)
    ].copy()
    _write_json(
        paths["marker"],
        {
            "schema_version": "xauusd_corrected_event_stage_open_v4",
            "stage": stage,
            "opened_utc": datetime.now(UTC).isoformat(),
            "contract_sha256": contract_hash,
            "training_authorized": False,
            "execution_authorized": False,
        },
    )

    base_config = json.loads(
        (ROOT / config["base_contract"]).resolve().read_text(encoding="utf-8")
    )
    bundle = DATA.load_bundle(base_config)
    source = config["source"]
    storage_root = Path(
        os.environ.get(
            source["storage_environment_variable"], source["default_storage_root"]
        )
    ).resolve()
    outcomes, execution_audit = EVENT.label_candidates(
        stage_candidates,
        bundle.bars["M5"],
        storage_root,
        str(source["symbol"]),
        source,
        config["execution"],
    )
    threshold_rows = int(execution_audit["stop_outcomes"]) + int(
        execution_audit["target_outcomes"]
    )
    if len(outcomes) and threshold_rows == 0:
        raise RuntimeError("Corrected event run produced no stop or target outcomes")
    temporary_outcomes = paths["outcomes"].with_suffix(".parquet.part")
    outcomes.to_parquet(temporary_outcomes, index=False)
    os.replace(temporary_outcomes, paths["outcomes"])
    _write_json(paths["execution_audit"], execution_audit)

    gate = config["gates"][stage]
    metric_rows = []
    for policy in policies.itertuples(index=False):
        trades = outcomes.loc[outcomes["policy_id"].eq(policy.policy_id)].copy()
        event_count = int(stage_calendar["event_type"].eq(policy.event_type).sum())
        values, checks = EVENT.policy_metrics(trades, event_count, gate)
        metric_rows.append(
            {
                "attempt_no": int(policy.attempt_no),
                "policy_id": str(policy.policy_id),
                "event_type": str(policy.event_type),
                "mode": str(policy.mode),
                "quantitative_gate_pass": bool(checks["quantitative_gate"]),
                "gate_checks": checks,
                "trade_pvalue": EVENT.one_sided_trade_pvalue(trades),
                **values,
            }
        )
    metrics = pd.DataFrame(metric_rows)
    metrics["holm_qvalue"] = EVENT.holm_adjust(metrics["trade_pvalue"])
    metrics["maximum_holm_qvalue_pass"] = metrics["holm_qvalue"].le(
        float(gate["maximum_holm_qvalue"])
    )
    metrics["stage_pass"] = (
        metrics["quantitative_gate_pass"] & metrics["maximum_holm_qvalue_pass"]
    )
    for index in metrics.index:
        checks = dict(metrics.at[index, "gate_checks"])
        checks["maximum_holm_qvalue"] = bool(
            metrics.at[index, "maximum_holm_qvalue_pass"]
        )
        metrics.at[index, "gate_checks"] = checks
    csv_metrics = metrics.copy()
    csv_metrics["gate_checks"] = csv_metrics["gate_checks"].map(
        lambda value: json.dumps(value, sort_keys=True, separators=(",", ":"))
    )
    _write_csv(paths["metrics"], csv_metrics)
    _write_csv(paths["diagnostics"], _diagnostics(outcomes))
    survivor_ids = set(metrics.loc[metrics["stage_pass"], "policy_id"])
    survivors = policies.loc[policies["policy_id"].isin(survivor_ids)].copy()
    _write_csv(paths["survivors"], survivors)
    advancement = _write_advancement(
        paths["advancement"],
        stage,
        contract_hash,
        paths["metrics"],
        paths["outcomes"],
        survivors,
    )

    decision = (
        "CORRECTED_EVENT_HISTORICAL_PASS_ADVANCE"
        if stage == "historical_replication" and len(survivors)
        else "NO_CORRECTED_EVENT_V4_HISTORICAL_SURVIVOR"
        if stage == "historical_replication"
        else "CORRECTED_EVENT_NEAR_SURVIVOR_REQUIRES_INDEPENDENT_REPLICATION_AND_SHADOW"
        if len(survivors)
        else "NO_CORRECTED_EVENT_V4_CONFIRMATION_SURVIVOR"
    )
    payload = {
        "schema_version": config["schema_version"],
        "contract_sha256": contract_hash,
        "stage": stage,
        "window_start_utc": start.isoformat(),
        "window_end_exclusive_utc": end.isoformat(),
        "attempt_first": int(policies["attempt_no"].min()),
        "attempt_last": int(policies["attempt_no"].max()),
        "cumulative_campaign_attempts": int(lock["attempt_last"]),
        "policy_rows": int(len(policies)),
        "event_rows": int(len(stage_calendar)),
        "candidate_rows": int(len(stage_candidates)),
        "outcome_rows": int(len(outcomes)),
        "survivor_rows": int(len(survivors)),
        "survivor_policy_ids": survivors["policy_id"].astype(str).tolist(),
        "decision": decision,
        "execution_audit": execution_audit,
        "advancement_sha256": advancement["advancement_sha256"],
        "related_confirmation_is_blind_exam": False,
        "paid_data_request_made": False,
        "databento_used": False,
        "training_authorized": False,
        "execution_authorized": False,
    }
    _write_json(paths["result"], payload)
    paths["markdown"].write_text(
        _render(stage, payload, metrics), encoding="utf-8", newline="\n"
    )
    _update_artifact_manifest(output, contract_hash)
    return payload


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("stage", choices=STAGES)
    args = parser.parse_args()
    payload = run_stage(str(args.stage))
    print(json.dumps(_json_ready(payload), indent=2, sort_keys=True, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
