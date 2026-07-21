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
CONFIG_PATH = ROOT / "config" / "executable_event_nearmiss_ranker_v99.json"
PREFIX = "EXECUTABLE_EVENT_NEARMISS_RANKER_V99"
LOCK_PATH = OUTPUT / f"{PREFIX}_CONTRACT_LOCK.json"
MANIFEST_PATH = OUTPUT / f"{PREFIX}_POLICY_MANIFEST.csv"
CENSUS_PATH = OUTPUT / f"{PREFIX}_SIGNAL_CENSUS.json"
RESULT_PATH = OUTPUT / f"{PREFIX}_RESULT.json"
RESULT_MD_PATH = OUTPUT / f"{PREFIX}_RESULT.md"
ARTIFACT_MANIFEST_PATH = OUTPUT / f"{PREFIX}_ARTIFACT_MANIFEST.json"
STAGES = ("discovery", "confirmation", "final")
V98_OUTPUT = ROOT.parent / "causal-event-nearmiss-ranker-v98" / "outputs"
V98_RESULT_PATH = V98_OUTPUT / "CAUSAL_EVENT_NEARMISS_RANKER_V98_RESULT.json"
V98_ARTIFACT_MANIFEST_PATH = (
    V98_OUTPUT / "CAUSAL_EVENT_NEARMISS_RANKER_V98_ARTIFACT_MANIFEST.json"
)


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


def _verify_v98_terminal_failure() -> dict[str, Any]:
    for path in (V98_RESULT_PATH, V98_ARTIFACT_MANIFEST_PATH):
        if not path.is_file():
            raise FileNotFoundError(
                "V99 is conditional on a completed terminal V98 invalidation: "
                f"missing {path}"
            )
    result = json.loads(V98_RESULT_PATH.read_text(encoding="utf-8"))
    artifact_manifest = json.loads(
        V98_ARTIFACT_MANIFEST_PATH.read_text(encoding="utf-8")
    )
    if (
        int(result.get("attempt_first", 0)) != 129001
        or int(result.get("attempt_last", 0)) != 130000
        or int(result.get("registered_policy_count", 0)) != 1000
    ):
        raise ValueError("V98 predecessor attempt registry is invalid")
    if artifact_manifest.get("contract_sha256") != result.get("contract_sha256"):
        raise ValueError("V98 result and artifact manifest contracts differ")
    decision = str(result.get("decision", ""))
    if decision != "V98_ENGINEERING_INVALIDATED_TERMINAL":
        raise RuntimeError("V98 is not terminally invalidated; V99 remains sealed")
    if bool(result.get("economic_metrics_produced", True)):
        raise RuntimeError("V99 is not an engineering-only successor")
    recorded = artifact_manifest.get("artifacts", {}).get(V98_RESULT_PATH.name, {})
    if recorded.get("sha256") != _sha256(V98_RESULT_PATH):
        raise ValueError("V98 terminal result is not artifact-bound")
    return {
        "v98_contract_sha256": str(result["contract_sha256"]),
        "v98_terminal_reason": decision,
        "v98_result_sha256": _sha256(V98_RESULT_PATH),
    }


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
        return "Infinity" if value > 0 else None
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


def _marker_path(stage: str) -> Path:
    return OUTPUT / f"{PREFIX}_{stage.upper()}_OUTCOMES_OPENED.json"


def _metrics_path(stage: str) -> Path:
    return OUTPUT / f"{PREFIX}_{stage.upper()}_METRICS.csv"


def _trades_path(stage: str) -> Path:
    return OUTPUT / f"{PREFIX}_{stage.upper()}_TRADES.csv"


def _advancement_path(stage: str) -> Path:
    return OUTPUT / f"{PREFIX}_{stage.upper()}_ADVANCEMENT_LOCK.json"


def _verify_contract(config: Mapping[str, Any]) -> tuple[dict[str, Any], Any]:
    if (
        not LOCK_PATH.is_file()
        or not MANIFEST_PATH.is_file()
        or not CENSUS_PATH.is_file()
    ):
        raise FileNotFoundError("Run lock_contract.py before opening V99 outcomes")
    lock_module = _load_module(
        "executable_event_nearmiss_ranker_v99_contract_verify", ROOT / "lock_contract.py"
    )
    lock = json.loads(LOCK_PATH.read_text(encoding="utf-8"))
    claimed = str(lock["contract_sha256"])
    body = dict(lock)
    body.pop("contract_sha256")
    if _canonical_hash(body) != claimed:
        raise ValueError("V99 contract hash mismatch")
    paths = lock_module.contract_paths(config)
    if set(paths) != set(lock["files"]):
        raise ValueError("V99 contract file set changed")
    for name, path in paths.items():
        if _sha256(path) != lock["files"][name]:
            raise ValueError(f"V99 contract input changed: {name}")
    if _sha256(MANIFEST_PATH) != lock["policy_manifest_sha256"]:
        raise ValueError("V99 policy manifest changed")
    if _sha256(CENSUS_PATH) != lock["signal_census_sha256"]:
        raise ValueError("V99 signal census changed")
    return lock, lock_module


def _previous_stage(stage: str) -> str | None:
    position = STAGES.index(stage)
    return STAGES[position - 1] if position else None


def _verify_advancement(stage: str, contract_hash: str) -> dict[str, Any]:
    path = _advancement_path(stage)
    if not path.is_file():
        raise FileNotFoundError(f"Missing V99 {stage} advancement lock")
    payload = json.loads(path.read_text(encoding="utf-8"))
    claimed = str(payload["advancement_sha256"])
    body = dict(payload)
    body.pop("advancement_sha256")
    if _canonical_hash(body) != claimed:
        raise ValueError(f"V99 {stage} advancement hash mismatch")
    if payload["contract_sha256"] != contract_hash:
        raise ValueError(f"V99 {stage} advancement contract mismatch")
    if payload["metrics_sha256"] != _sha256(_metrics_path(stage)):
        raise ValueError(f"V99 {stage} metrics changed")
    if payload["trades_sha256"] != _sha256(_trades_path(stage)):
        raise ValueError(f"V99 {stage} trades changed")
    return payload


def _stage_manifest(stage: str, contract_hash: str) -> pd.DataFrame:
    manifest = pd.read_csv(MANIFEST_PATH, dtype={"policy_id": str})
    if stage == "discovery":
        return manifest
    previous = _previous_stage(stage)
    if previous is None:
        raise AssertionError(stage)
    advancement = _verify_advancement(previous, contract_hash)
    selected_ids = [str(value) for value in advancement["selected_policy_ids"]]
    if not selected_ids:
        raise RuntimeError(f"V99 {stage} is sealed; {previous} selected no policy")
    selected = manifest.loc[manifest["policy_id"].isin(selected_ids)].copy()
    if set(selected["policy_id"]) != set(selected_ids):
        raise ValueError("V99 advancement references an unknown policy")
    return selected.sort_values("attempt_no", kind="mergesort").reset_index(drop=True)


def _write_marker(stage: str, contract_hash: str) -> None:
    if _marker_path(stage).exists() or _metrics_path(stage).exists():
        raise RuntimeError(f"V99 {stage} outcomes were already opened")
    _write_json(
        _marker_path(stage),
        {
            "schema_version": "xauusd_executable_event_nearmiss_ranker_v99_stage_open",
            "stage": stage,
            "opened_utc": datetime.now(UTC).isoformat(),
            "contract_sha256": contract_hash,
            "research_model_fitting_authorized": True,
            "deployment_model_training_authorized": False,
            "execution_authorized": False,
        },
    )


def _metrics_for_csv(metrics: pd.DataFrame) -> pd.DataFrame:
    output = metrics.copy()
    output["segment_metrics_json"] = output["segment_metrics"].map(
        lambda value: json.dumps(
            _json_ready(value), sort_keys=True, separators=(",", ":")
        )
    )
    return output.drop(columns=["segment_metrics"])


def _write_advancement(
    stage: str, contract_hash: str, selected: pd.DataFrame
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "schema_version": "xauusd_executable_event_nearmiss_ranker_v99_advancement",
        "stage": stage,
        "created_utc": datetime.now(UTC).isoformat(),
        "contract_sha256": contract_hash,
        "policy_manifest_sha256": _sha256(MANIFEST_PATH),
        "metrics_sha256": _sha256(_metrics_path(stage)),
        "trades_sha256": _sha256(_trades_path(stage)),
        "selected_policy_ids": selected["policy_id"].astype(str).tolist(),
        "selected_mechanics": selected["mechanic"].astype(str).tolist(),
        "selected_policy_count": int(len(selected)),
        "research_model_fitting_authorized": True,
        "deployment_model_training_authorized": False,
        "execution_authorized": False,
    }
    payload["advancement_sha256"] = _canonical_hash(payload)
    _write_json(_advancement_path(stage), payload)
    return payload


def _decision(stage: str, selected_count: int) -> str:
    if selected_count:
        if stage == "final":
            return "V99_FINAL_SURVIVOR_REQUIRES_SHARED_V59_V60_AUDIT"
        return f"V99_{stage.upper()}_PASS_ADVANCE"
    return f"V99_{stage.upper()}_FAIL_TERMINAL"


def _load_result(contract_hash: str, config: Mapping[str, Any]) -> dict[str, Any]:
    if RESULT_PATH.is_file():
        result = json.loads(RESULT_PATH.read_text(encoding="utf-8"))
        if result["contract_sha256"] != contract_hash:
            raise ValueError("V99 result contract mismatch")
        return result
    controls = config["research_controls"]
    return {
        "schema_version": config["schema_version"],
        "contract_sha256": contract_hash,
        "attempt_first": int(controls["attempt_first"]),
        "attempt_last": int(controls["attempt_last"]),
        "registered_policy_count": int(controls["registered_policy_count"]),
        "stages": {},
        "research_only": True,
        "research_model_fitting_authorized": True,
        "deployment_model_training_authorized": False,
        "execution_authorized": False,
        "v59_v60_modified": False,
    }


def _render(result: Mapping[str, Any]) -> str:
    lines = [
        "# V99 Executable Event Near-Miss Ranker Result",
        "",
        f"Decision: `{result.get('decision', 'IN_PROGRESS')}`",
        "",
        f"Registered attempts: **{result['attempt_first']:,}-{result['attempt_last']:,}** "
        f"({result['registered_policy_count']:,} policies)",
        "",
        "| Stage | Incoming | Passed | Advanced | Best PF | Best R | Best frequency | Lowest q |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for stage in STAGES:
        row = result.get("stages", {}).get(stage)
        if row is None:
            lines.append(
                f"| {stage} | SEALED | SEALED | SEALED | SEALED | SEALED | SEALED | SEALED |"
            )
            continue
        lines.append(
            f"| {stage} | {row['incoming_policy_count']} | "
            f"{row['gate_pass_policy_count']} | {row['advanced_policy_count']} | "
            f"{row['best_stress_pf']:.3f} | {row['best_average_stress_r']:.3f} | "
            f"{row['best_trades_per_weekday']:.3f} | {row['lowest_fdr_qvalue']:.4f} |"
        )
    lines.extend(
        [
            "",
            "Rolling nonlinear models rank five preregistered executable event pools under one support-qualified exit profile.",
            "",
            "Research fitting only. V59/V60 remain byte-identical. No deployment model, EA, demo, live, payment, Databento, or broker authority is granted.",
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
            "research_model_fitting_authorized": True,
            "deployment_model_training_authorized": False,
            "execution_authorized": False,
        },
    )


def run_stage(stage: str) -> dict[str, Any]:
    if stage not in STAGES:
        raise KeyError(stage)
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    lock, _ = _verify_contract(config)
    predecessor_evidence = _verify_v98_terminal_failure()
    contract_hash = str(lock["contract_sha256"])
    incoming = _stage_manifest(stage, contract_hash)
    _write_marker(stage, contract_hash)
    campaign = _load_module(
        "executable_event_nearmiss_ranker_v99_run_campaign", ROOT / "src" / "campaign.py"
    )
    data = _load_module(
        "executable_event_nearmiss_ranker_v99_run_data",
        (ROOT / config["source"]["data_source"]).resolve(),
    )
    bundle = data.load_bundle(config)
    frame = campaign.prepare_features(
        bundle.bars["H1"], bundle.bars["M5"], None, config
    )
    metrics, cache = campaign.evaluate_policies(
        frame, bundle.bars["M5"], incoming, config, stage
    )
    selected = campaign.select_advancers(metrics, config["gates"][stage])
    trades = campaign.selected_trade_ledger(
        frame, bundle.bars["M5"], selected, config, stage, cache
    )
    _write_csv(_metrics_path(stage), _metrics_for_csv(metrics))
    _write_csv(_trades_path(stage), trades)
    advancement = _write_advancement(stage, contract_hash, selected)
    result = _load_result(contract_hash, config)
    finite_pf = pd.to_numeric(metrics["stress_pf"], errors="coerce")
    result["stages"][stage] = {
        "completed_utc": datetime.now(UTC).isoformat(),
        "incoming_policy_count": int(len(incoming)),
        "gate_pass_policy_count": int(metrics["gate_pass"].sum()),
        "advanced_policy_count": int(len(selected)),
        "advanced_policy_ids": selected["policy_id"].astype(str).tolist(),
        "advanced_mechanics": selected["mechanic"].astype(str).tolist(),
        "selected_trade_rows": int(len(trades)),
        "best_stress_pf": float(finite_pf.max()) if finite_pf.notna().any() else 0.0,
        "best_average_stress_r": float(metrics["average_stress_r"].max()),
        "best_trades_per_weekday": float(metrics["trades_per_source_day"].max()),
        "lowest_fdr_qvalue": float(metrics["fdr_qvalue"].min()),
        "metrics_sha256": _sha256(_metrics_path(stage)),
        "trades_sha256": _sha256(_trades_path(stage)),
        "advancement_sha256": advancement["advancement_sha256"],
    }
    result["decision"] = _decision(stage, len(selected))
    result["latest_completed_stage"] = stage
    result["conditional_predecessor"] = predecessor_evidence
    result["data_evidence"] = {
        "dukascopy_xau": bundle.evidence,
        "event_candidate_rows": int(len(frame)),
        "event_candidate_types": frame["event_type"].value_counts().to_dict(),
        "paid_data_request_made": False,
        "databento_used": False,
    }
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
