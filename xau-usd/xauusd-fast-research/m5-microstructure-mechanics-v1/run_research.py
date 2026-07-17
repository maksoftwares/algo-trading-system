from __future__ import annotations

import argparse
from datetime import UTC, datetime
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import sys
from typing import Any, Mapping

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "outputs"
CONFIG_PATH = ROOT / "config" / "m5_microstructure_mechanics_v1.json"
LOCK_PATH = OUTPUT / "M5_MICROSTRUCTURE_CONTRACT_LOCK.json"
MANIFEST_PATH = OUTPUT / "M5_MICROSTRUCTURE_POLICY_MANIFEST.csv"
RESULT_PATH = OUTPUT / "M5_MICROSTRUCTURE_RESULT.json"
RESULT_MD_PATH = OUTPUT / "M5_MICROSTRUCTURE_RESULT.md"
ARTIFACT_MANIFEST_PATH = OUTPUT / "M5_MICROSTRUCTURE_ARTIFACT_MANIFEST.json"
STAGES = ("discovery", "confirmation", "internal_test", "exam")


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
        return "Infinity" if value > 0 else None
    return value


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    temporary = path.with_suffix(path.suffix + ".part")
    temporary.write_text(
        json.dumps(_json_ready(payload), indent=2, sort_keys=True, allow_nan=False)
        + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def _write_csv(path: Path, frame: pd.DataFrame) -> None:
    temporary = path.with_suffix(path.suffix + ".part")
    frame.to_csv(temporary, index=False)
    temporary.replace(path)


def _verify_contract(config: Mapping[str, Any]) -> dict[str, Any]:
    if not LOCK_PATH.is_file():
        raise FileNotFoundError("Run lock_contract.py before opening any outcomes")
    lock_module = _load_module("m5_micro_contract_verify", ROOT / "lock_contract.py")
    lock = json.loads(LOCK_PATH.read_text(encoding="utf-8"))
    claimed = str(lock["contract_sha256"])
    body = dict(lock)
    body.pop("contract_sha256")
    if _canonical_hash(body) != claimed:
        raise ValueError("Microstructure contract hash mismatch")
    paths = lock_module.contract_paths(config)
    if set(paths) != set(lock["files"]):
        raise ValueError("Microstructure contract file set changed")
    for name, path in paths.items():
        if _sha256(path) != lock["files"][name]:
            raise ValueError(f"Microstructure contract file changed: {name}")
    return lock


def _marker_path(stage: str) -> Path:
    return OUTPUT / f"M5_MICROSTRUCTURE_{stage.upper()}_OUTCOMES_OPENED.json"


def _metrics_path(stage: str) -> Path:
    return OUTPUT / f"M5_MICROSTRUCTURE_{stage.upper()}_METRICS.csv"


def _trades_path(stage: str) -> Path:
    return OUTPUT / f"M5_MICROSTRUCTURE_{stage.upper()}_TRADES.csv"


def _advancement_path(stage: str) -> Path:
    return OUTPUT / f"M5_MICROSTRUCTURE_{stage.upper()}_ADVANCEMENT_LOCK.json"


def _previous_stage(stage: str) -> str | None:
    position = STAGES.index(stage)
    return STAGES[position - 1] if position else None


def _write_marker(stage: str, contract_hash: str) -> None:
    marker = _marker_path(stage)
    if marker.exists() or _metrics_path(stage).exists():
        raise RuntimeError(f"{stage} outcomes were already opened")
    _write_json(
        marker,
        {
            "schema_version": "xauusd_m5_microstructure_stage_open_v1",
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
        raise ValueError(f"{stage} advancement manifest mismatch")
    if payload["metrics_sha256"] != _sha256(_metrics_path(stage)):
        raise ValueError(f"{stage} advancement metrics mismatch")
    return payload


def _metrics_for_csv(metrics: pd.DataFrame) -> pd.DataFrame:
    output = metrics.copy()
    output["segment_metrics_json"] = output["segment_metrics"].map(
        lambda value: json.dumps(_json_ready(value), sort_keys=True, separators=(",", ":"))
    )
    return output.drop(columns=["segment_metrics"])


def _write_advancement(
    stage: str,
    contract_hash: str,
    selected: pd.DataFrame,
) -> dict[str, Any]:
    path = _advancement_path(stage)
    payload: dict[str, Any] = {
        "schema_version": "xauusd_m5_microstructure_advancement_v1",
        "stage": stage,
        "created_utc": datetime.now(UTC).isoformat(),
        "contract_sha256": contract_hash,
        "policy_manifest_sha256": _sha256(MANIFEST_PATH),
        "metrics_sha256": _sha256(_metrics_path(stage)),
        "selected_policy_ids": selected["policy_id"].astype(str).tolist(),
        "selected_mechanics": selected["mechanic"].astype(str).tolist(),
        "selected_policy_count": int(len(selected)),
        "training_authorized": False,
        "execution_authorized": False,
    }
    payload["advancement_sha256"] = _canonical_hash(payload)
    _write_json(path, payload)
    return payload


def _stage_manifest(
    stage: str,
    campaign: Any,
    config: Mapping[str, Any],
    contract_hash: str,
) -> pd.DataFrame:
    if stage == "discovery":
        if MANIFEST_PATH.exists():
            raise RuntimeError("Policy manifest already exists before discovery")
        manifest = campaign.generate_manifest(
            int(config["research_controls"]["campaign_attempts_before_v1"]),
            int(config["research_controls"]["policies_per_mechanic"]),
        )
        if len(manifest) != int(config["research_controls"]["registered_policy_count"]):
            raise ValueError("Generated policy count does not match the contract")
        _write_csv(MANIFEST_PATH, manifest)
        return manifest
    if not MANIFEST_PATH.is_file():
        raise FileNotFoundError("Discovery policy manifest is missing")
    previous = _previous_stage(stage)
    if previous is None:
        raise AssertionError(stage)
    advancement = _verify_advancement(previous, contract_hash)
    selected_ids = [str(value) for value in advancement["selected_policy_ids"]]
    if not selected_ids:
        raise RuntimeError(f"{stage} is sealed because {previous} selected no policy")
    manifest = pd.read_csv(MANIFEST_PATH, dtype={"policy_id": str})
    selected = manifest.loc[manifest["policy_id"].isin(selected_ids)].copy()
    if set(selected["policy_id"]) != set(selected_ids) or len(selected) != len(selected_ids):
        raise ValueError(f"{previous} advancement references an unknown or duplicate policy")
    return selected.sort_values("attempt_no", kind="mergesort").reset_index(drop=True)


def _load_result(contract_hash: str, config: Mapping[str, Any]) -> dict[str, Any]:
    if RESULT_PATH.is_file():
        result = json.loads(RESULT_PATH.read_text(encoding="utf-8"))
        if result["contract_sha256"] != contract_hash:
            raise ValueError("Result contract mismatch")
        return result
    return {
        "schema_version": config["schema_version"],
        "contract_sha256": contract_hash,
        "attempt_first": int(config["research_controls"]["campaign_attempts_before_v1"]) + 1,
        "attempt_last": int(config["research_controls"]["campaign_attempts_before_v1"])
        + int(config["research_controls"]["registered_policy_count"]),
        "registered_policy_count": int(config["research_controls"]["registered_policy_count"]),
        "stages": {},
        "research_only": True,
        "training_authorized": False,
        "execution_authorized": False,
    }


def _decision(stage: str, selected_count: int) -> str:
    if selected_count:
        if stage == "exam":
            return "M5_MICROSTRUCTURE_NEAR_SURVIVOR_REQUIRES_OUT_OF_ERA_AND_SHADOW"
        return f"M5_MICROSTRUCTURE_{stage.upper()}_PASS_ADVANCE"
    return f"NO_M5_MICROSTRUCTURE_V1_{stage.upper()}_SURVIVOR"


def _render(result: Mapping[str, Any]) -> str:
    lines = [
        "# XAUUSD M5 Microstructure Mechanics V1 Result",
        "",
        f"Decision: `{result.get('decision', 'IN_PROGRESS')}`",
        "",
        f"Registered attempts: **{result['attempt_first']:,}-{result['attempt_last']:,}** "
        f"({result['registered_policy_count']:,} policies)",
        "",
        "| Stage | Incoming | Gate pass | Advanced | Best PF | Best average R | Lowest q |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for stage in STAGES:
        row = result.get("stages", {}).get(stage)
        if row is None:
            lines.append(f"| {stage} | SEALED | SEALED | SEALED | SEALED | SEALED | SEALED |")
            continue
        lines.append(
            f"| {stage} | {row['incoming_policy_count']} | {row['gate_pass_policy_count']} | "
            f"{row['advanced_policy_count']} | {row['best_stress_pf']:.3f} | "
            f"{row['best_average_stress_r']:.3f} | {row['lowest_fdr_qvalue']:.4f} |"
        )
    lines.extend(
        [
            "",
            "Every entry uses the next contiguous M5 side-correct Bid/Ask open. Later stages stay sealed unless the preceding advancement lock contains a passer.",
            "",
            "Research only. No Python model, EA, demo, live, broker, paid-data, or Databento authority is granted.",
            "",
        ]
    )
    return "\n".join(lines)


def _update_artifact_manifest(contract_hash: str) -> None:
    artifacts = {}
    for path in sorted(OUTPUT.iterdir()):
        if not path.is_file() or path == ARTIFACT_MANIFEST_PATH or path.suffix == ".part":
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
    campaign = _load_module("m5_micro_campaign", ROOT / "src" / "campaign.py")
    data = _load_module(
        "m5_micro_data", (ROOT / config["source"]["data_source"]).resolve()
    )
    incoming = _stage_manifest(stage, campaign, config, contract_hash)
    _write_marker(stage, contract_hash)
    m5, evidence = data.load_m5(config)
    frame = campaign.prepare_features(m5, config)
    metrics, cache = campaign.evaluate_policies(frame, incoming, config, stage)
    selected = campaign.select_advancers(metrics, config["gates"][stage])
    trades = campaign.selected_trade_ledger(frame, selected, config, stage, cache)
    metrics_output = _metrics_for_csv(metrics)
    _write_csv(_metrics_path(stage), metrics_output)
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
        "lowest_fdr_qvalue": float(metrics["fdr_qvalue"].min()),
        "metrics_sha256": _sha256(_metrics_path(stage)),
        "trades_sha256": _sha256(_trades_path(stage)),
        "advancement_sha256": advancement["advancement_sha256"],
    }
    result["decision"] = _decision(stage, len(selected))
    result["latest_completed_stage"] = stage
    result["data_evidence"] = evidence
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
