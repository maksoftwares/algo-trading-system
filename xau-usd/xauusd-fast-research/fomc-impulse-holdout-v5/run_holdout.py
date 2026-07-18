from __future__ import annotations

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
CONFIG_PATH = ROOT / "config" / "fomc_impulse_holdout_v5.json"
PREFIX = "FOMC_IMPULSE_HOLDOUT"


def _load_module(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


EVENT = _load_module(
    "fomc_impulse_holdout_engine",
    RESEARCH_ROOT / "macro-event-reaction-replication-v2" / "src" / "event_reaction.py",
)
DATA = _load_module(
    "fomc_impulse_holdout_data",
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


def _paths(output: Path) -> dict[str, Path]:
    return {
        "marker": output / f"{PREFIX}_OUTCOMES_OPENED.json",
        "outcomes": output / f"{PREFIX}_OUTCOMES.parquet",
        "execution_audit": output / f"{PREFIX}_EXECUTION_AUDIT.json",
        "metrics": output / f"{PREFIX}_METRICS.csv",
        "diagnostics": output / f"{PREFIX}_DIAGNOSTICS.csv",
        "survivors": output / f"{PREFIX}_ECONOMIC_SURVIVORS.csv",
        "result": output / f"{PREFIX}_RESULT.json",
        "markdown": output / f"{PREFIX}_RESULT.md",
    }


def _verify_contract(config: Mapping[str, Any]) -> dict[str, Any]:
    output = ROOT / config["outputs"]["directory"]
    lock_path = output / config["outputs"]["contract_lock"]
    if not lock_path.is_file():
        raise FileNotFoundError("Run lock_contract.py before opening FOMC holdout")
    lock_module = _load_module("fomc_holdout_contract_verify", ROOT / "lock_contract.py")
    lock = json.loads(lock_path.read_text(encoding="utf-8"))
    claimed = str(lock["contract_sha256"])
    body = dict(lock)
    body.pop("contract_sha256")
    if _canonical_hash(body) != claimed:
        raise ValueError("FOMC holdout contract hash mismatch")
    paths = lock_module.contract_paths(config)
    if set(paths) != set(lock["files"]):
        raise ValueError("FOMC holdout contract file set changed")
    for name, path in paths.items():
        if _sha256(path) != lock["files"][name]:
            raise ValueError(f"FOMC holdout contract input changed: {name}")
    parent_output = (ROOT / config["parent_package"]).resolve() / "outputs"
    if (parent_output / "CORRECTED_EVENT_RELATED_CONFIRMATION_OUTCOMES_OPENED.json").exists():
        raise RuntimeError("Parent corrected-event confirmation must remain sealed")
    return lock


def _diagnostics(outcomes: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for dimension in ("regime", "direction", "exit_reason"):
        for key, frame in outcomes.groupby(dimension, sort=True):
            rows.append(
                {
                    "dimension": dimension,
                    "value": str(key),
                    "trades": int(len(frame)),
                    "stress_net_r": float(frame["stress_net_r"].sum()),
                    "average_stress_r": float(frame["stress_net_r"].mean()),
                    "wins": int(frame["stress_net_r"].gt(0.0).sum()),
                }
            )
    return pd.DataFrame(rows)


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


def _render(payload: Mapping[str, Any], metric: Mapping[str, Any]) -> str:
    return "\n".join(
        [
            "# XAUUSD FOMC Impulse V5 Related Holdout",
            "",
            f"Decision: `{payload['decision']}`",
            f"Official FOMC events: **{payload['event_rows']}**",
            f"Outcome-free candidates: **{payload['candidate_rows']}**",
            f"Executed trades: **{int(metric['trades'])}**",
            f"Stops / targets / timeouts: **{payload['execution_audit']['stop_outcomes']} / "
            f"{payload['execution_audit']['target_outcomes']} / "
            f"{payload['execution_audit']['max_hold_outcomes']}**",
            f"Stress PF: **{float(metric['stress_pf']):.3f}**",
            f"Average stress R: **{float(metric['average_stress_r']):.3f}**",
            f"Closed drawdown: **{float(metric['closed_drawdown_r']):.3f}R**",
            f"Top three winners removed: **{float(metric['top_winners_removed_stress_net_r']):.3f}R**",
            f"Positive active months: **{float(metric['positive_active_month_share']):.1%}**",
            f"Positive active years: **{float(metric['positive_active_year_share']):.1%}**",
            f"One-sided p-value: **{float(metric['trade_pvalue']):.4f}**",
            f"Economic gate: **{'PASS' if bool(metric['economic_stage_pass']) else 'FAIL'}**",
            f"Old-account feasibility: **{float(metric['current_account_feasible_share']):.1%} "
            f"({'PASS' if bool(metric['deployment_feasible_pass']) else 'FAIL'})**",
            "",
            "An economic pass does not authorize deployment; capital and portfolio risk remain separate gates.",
            "This related holdout is not represented as a pristine blind exam.",
            "No result grants model, EA, demo, live, broker, paid-data, or Databento authority.",
            "",
        ]
    )


def run_holdout() -> dict[str, Any]:
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    lock = _verify_contract(config)
    contract_hash = str(lock["contract_sha256"])
    output = ROOT / config["outputs"]["directory"]
    paths = _paths(output)
    if paths["result"].exists() or paths["marker"].exists():
        raise RuntimeError("Refusing to rerun completed/opened FOMC holdout")
    candidates = pd.read_parquet(output / config["outputs"]["candidates"])
    parent = (ROOT / config["parent_package"]).resolve()
    calendar = pd.read_csv(
        parent / "outputs" / "CORRECTED_EVENT_CALENDAR.csv",
        parse_dates=["event_time_utc"],
    )
    start = pd.Timestamp(config["source"]["start_utc"])
    end = pd.Timestamp(config["source"]["end_exclusive_utc"])
    events = calendar.loc[
        calendar["event_type"].eq("FOMC")
        & calendar["event_time_utc"].ge(start)
        & calendar["event_time_utc"].lt(end)
    ].copy()
    if len(events) != int(config["source"]["expected_event_rows"]):
        raise ValueError("FOMC holdout official-event count changed")
    _write_json(
        paths["marker"],
        {
            "schema_version": "xauusd_fomc_impulse_holdout_open_v5",
            "opened_utc": datetime.now(UTC).isoformat(),
            "contract_sha256": contract_hash,
            "attempt_no": int(config["policy"]["attempt_no"]),
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
        candidates,
        bundle.bars["M5"],
        storage_root,
        str(source["symbol"]),
        source,
        config["execution"],
    )
    if len(outcomes) and not (
        int(execution_audit["stop_outcomes"])
        + int(execution_audit["target_outcomes"])
    ):
        raise RuntimeError("FOMC holdout produced no stop or target outcomes")
    temporary = paths["outcomes"].with_suffix(".parquet.part")
    outcomes.to_parquet(temporary, index=False)
    os.replace(temporary, paths["outcomes"])
    _write_json(paths["execution_audit"], execution_audit)

    values, checks = EVENT.policy_metrics(
        outcomes, len(events), config["economic_gate"]
    )
    pvalue = EVENT.one_sided_trade_pvalue(outcomes)
    pvalue_pass = pvalue <= float(config["economic_gate"]["maximum_pvalue"])
    checks = dict(checks)
    checks["maximum_pvalue"] = pvalue_pass
    economic_pass = bool(checks["quantitative_gate"] and pvalue_pass)
    deployment_pass = values["current_account_feasible_share"] >= float(
        config["deployment_gate"]["minimum_current_account_feasible_share"]
    )
    metric = {
        "attempt_no": int(config["policy"]["attempt_no"]),
        "policy_id": str(config["policy"]["policy_id"]),
        "event_type": "FOMC",
        "mode": "IMPULSE",
        "trade_pvalue": pvalue,
        "economic_gate_checks": checks,
        "economic_stage_pass": economic_pass,
        "deployment_feasible_pass": bool(deployment_pass),
        **values,
    }
    metrics = pd.DataFrame([metric])
    csv_metrics = metrics.copy()
    csv_metrics["economic_gate_checks"] = csv_metrics["economic_gate_checks"].map(
        lambda value: json.dumps(value, sort_keys=True, separators=(",", ":"))
    )
    _write_csv(paths["metrics"], csv_metrics)
    _write_csv(paths["diagnostics"], _diagnostics(outcomes))
    survivor_columns = ["attempt_no", "policy_id", "event_type", "mode"]
    survivors = (
        pd.DataFrame([metric])[survivor_columns]
        if economic_pass
        else pd.DataFrame(columns=survivor_columns)
    )
    _write_csv(paths["survivors"], survivors)
    decision = (
        "FOMC_IMPULSE_ECONOMIC_NEAR_SURVIVOR_REQUIRES_INDEPENDENT_REPLICATION_AND_SHADOW"
        if economic_pass and deployment_pass
        else "FOMC_IMPULSE_CAPITAL_DEPENDENT_NEAR_SURVIVOR_NOT_DEPLOYABLE"
        if economic_pass
        else "NO_FOMC_IMPULSE_V5_HOLDOUT_SURVIVOR"
    )
    payload = {
        "schema_version": config["schema_version"],
        "contract_sha256": contract_hash,
        "attempt_first": int(config["policy"]["attempt_no"]),
        "attempt_last": int(config["policy"]["attempt_no"]),
        "cumulative_campaign_attempts": int(config["policy"]["attempt_no"]),
        "window_start_utc": start.isoformat(),
        "window_end_exclusive_utc": end.isoformat(),
        "event_rows": int(len(events)),
        "candidate_rows": int(len(candidates)),
        "outcome_rows": int(len(outcomes)),
        "economic_survivor_rows": int(economic_pass),
        "deployment_feasible": bool(deployment_pass),
        "decision": decision,
        "execution_audit": execution_audit,
        "related_holdout_is_blind_exam": False,
        "parent_confirmation_remained_sealed": True,
        "paid_data_request_made": False,
        "databento_used": False,
        "training_authorized": False,
        "execution_authorized": False,
    }
    _write_json(paths["result"], payload)
    paths["markdown"].write_text(
        _render(payload, metric), encoding="utf-8", newline="\n"
    )
    _update_artifact_manifest(output, contract_hash)
    return payload


def main() -> int:
    payload = run_holdout()
    print(json.dumps(_json_ready(payload), indent=2, sort_keys=True, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
