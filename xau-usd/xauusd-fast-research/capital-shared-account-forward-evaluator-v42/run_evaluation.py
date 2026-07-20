from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
import time
from typing import Any, Mapping

import pandas as pd


ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parents[2]
sys.path.insert(0, str(ROOT / "src"))

from evaluator import (  # noqa: E402
    StageNotReady,
    build_core_trades,
    canonical_hash,
    evaluate_stage,
    load_config,
    load_source_bundle,
    normalize_satellite_trades,
    select_tick_paths,
    sha256_file,
    verify_source_contracts,
)


def write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_bytes(
        (json.dumps(payload, allow_nan=False, indent=2, sort_keys=True) + "\n").encode(
            "utf-8"
        )
    )
    temporary.replace(path)


def verify_contract(
    config: Mapping[str, Any], repo_root: Path = REPO_ROOT, package_root: Path = ROOT
) -> dict[str, Any]:
    path = (
        package_root
        / str(config["outputs"]["directory"])
        / str(config["outputs"]["contract_lock"])
    )
    if not path.is_file():
        raise FileNotFoundError("V42 contract lock is absent")
    contract = json.loads(path.read_text(encoding="utf-8"))
    if canonical_hash(contract, "contract_sha256") != str(
        contract.get("contract_sha256")
    ):
        raise ValueError("V42 contract self-hash changed")
    for record in contract["package_files"]:
        file_path = package_root / str(record["path"])
        if (
            not file_path.is_file()
            or int(file_path.stat().st_size) != int(record["bytes"])
            or sha256_file(file_path) != str(record["sha256"])
        ):
            raise ValueError(f"V42 package file changed: {record['path']}")
    source_records = verify_source_contracts(config, repo_root)
    if source_records != contract["source_contracts"]:
        raise ValueError("V42 source contract records changed")
    return contract


def _v27_root(config: Mapping[str, Any]) -> Path:
    return (REPO_ROOT / str(config["sources"]["v27"]["root"])).resolve()


def load_v27_stage(
    config: Mapping[str, Any], stage: str
) -> tuple[dict[str, Any], pd.DataFrame] | None:
    source = config["sources"]["v27"]
    root = _v27_root(config)
    audit_path = root / str(source[f"{stage}_audit"])
    trades_path = root / str(source[f"{stage}_trades"])
    if not audit_path.exists():
        if trades_path.exists():
            raise ValueError(f"V42 V27 {stage} trades exist without audit")
        return None
    audit = json.loads(audit_path.read_text(encoding="utf-8"))
    if canonical_hash(audit, "audit_sha256") != str(audit.get("audit_sha256")):
        raise ValueError(f"V42 V27 {stage} audit self-hash changed")
    if str(audit.get("contract_sha256")) != str(source["contract_sha256"]):
        raise ValueError(f"V42 V27 {stage} contract changed")
    dates = [str(value) for value in audit["stage_dates"]]
    if len(dates) != int(config["stages"]["required_full_weekdays_per_stage"]):
        raise ValueError(f"V42 V27 {stage} date count changed")
    if len(dates) != len(set(dates)) or dates != sorted(dates):
        raise ValueError(f"V42 V27 {stage} dates are invalid")
    opened = bool(audit.get("portfolio_economic_outcomes_opened"))
    if not opened:
        if trades_path.exists():
            raise ValueError(f"V42 V27 {stage} sealed economics have a trade file")
        return audit, pd.DataFrame()
    if not trades_path.is_file() or sha256_file(trades_path) != str(
        audit.get("portfolio_trades_sha256")
    ):
        raise ValueError(f"V42 V27 {stage} trades changed")
    trades = pd.read_csv(trades_path)
    if not trades["date_utc"].astype(str).isin(dates).all():
        raise ValueError(f"V42 V27 {stage} has an out-of-stage trade")
    return audit, trades


def verify_stage_output(
    output: Path,
    config: Mapping[str, Any],
    contract: Mapping[str, Any],
    stage: str,
) -> dict[str, Any]:
    audit_path = output / str(config["outputs"][f"{stage}_audit"])
    audit = json.loads(audit_path.read_text(encoding="utf-8"))
    if canonical_hash(audit, "audit_sha256") != str(audit.get("audit_sha256")):
        raise ValueError(f"V42 {stage} audit self-hash changed")
    if str(audit.get("contract_sha256")) != str(contract["contract_sha256"]):
        raise ValueError(f"V42 {stage} contract changed")
    trades_path = output / str(config["outputs"][f"{stage}_trades"])
    if not trades_path.is_file() or sha256_file(trades_path) != str(
        audit.get("trades_sha256")
    ):
        raise ValueError(f"V42 {stage} trades changed")
    return audit


def _read_status(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {"status": "ABSENT"}
    return json.loads(path.read_text(encoding="utf-8"))


def waiting_status(
    config: Mapping[str, Any],
    contract: Mapping[str, Any],
    *,
    stage: str,
    reason: str,
) -> dict[str, Any]:
    sources = config["sources"]
    v40_status = _read_status(
        Path(sources["v40"]["runtime_directory"]) / sources["v40"]["status"]
    )
    v41_status = _read_status(
        Path(sources["v41"]["runtime_directory"]) / sources["v41"]["status"]
    )
    v38_status = _read_status(
        Path(sources["v38"]["runtime_directory"]) / sources["v38"]["status"]
    )
    v39_status = _read_status(
        Path(sources["v39"]["runtime_directory"]) / sources["v39"]["status"]
    )
    v27_status = _read_status(_v27_root(config) / sources["v27"]["status"])
    status = {
        "schema_version": "xauusd_capital_shared_account_v42_status",
        "updated_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "status": "WAITING_FOR_SEALED_STAGE",
        "contract_sha256": str(contract["contract_sha256"]),
        "waiting_for_stage": stage.upper(),
        "waiting_reason": reason,
        "source_counts": {
            "v40": v40_status.get("streams", {}),
            "v41_candidate_rows": int(v41_status.get("candidate_rows", 0)),
            "v41_resolution_rows": int(v41_status.get("resolution_rows", 0)),
            "v38_candidate_rows": int(v38_status.get("candidate_rows", 0)),
            "v38_resolution_rows": int(v38_status.get("resolution_rows", 0)),
            "v39_routed_candidate_rows": int(
                v39_status.get("routed_candidate_rows", 0)
            ),
        },
        "source_health": {
            "v27": str(v27_status.get("decision", v27_status.get("status", "ABSENT"))),
            "v40": str(v40_status.get("status", "ABSENT")),
            "v41": str(v41_status.get("status", "ABSENT")),
            "v38": str(v38_status.get("status", "ABSENT")),
            "v39": str(v39_status.get("status", "ABSENT")),
        },
        "aggregate_economics_opened": False,
        "research_gate_passed": False,
        "account_gate_passed": False,
        "execution_ready": False,
        "same_version_tuning_authorized": False,
        "model_training_authorized": False,
        "python_predictions_authorized": False,
        "ea_consumption_authorized": False,
        "demo_authorized": False,
        "live_authorized": False,
        "trade_permission": False,
        "broker_action_allowed": False,
    }
    status["status_sha256"] = canonical_hash(status, "status_sha256")
    return status


def persist_stage(
    output: Path,
    config: Mapping[str, Any],
    contract: Mapping[str, Any],
    *,
    stage: str,
    v27_audit: Mapping[str, Any],
    trades: pd.DataFrame,
    result: Mapping[str, Any],
    source_seals: Mapping[str, Any],
) -> dict[str, Any]:
    audit_path = output / str(config["outputs"][f"{stage}_audit"])
    trades_path = output / str(config["outputs"][f"{stage}_trades"])
    if audit_path.exists() or trades_path.exists():
        raise FileExistsError(f"V42 {stage} output already exists")
    trades_path.write_bytes(
        trades.to_csv(index=False, lineterminator="\n").encode("utf-8")
    )
    research_passed = bool(result["readiness"]["research_gate_passed"])
    account_passed = bool(result["readiness"]["account_gate_passed"])
    if stage == "validation":
        if research_passed:
            decision = (
                "V42_VALIDATION_RESEARCH_PASS_ACCOUNT_REFERENCE_PASS_CONFIRMATION_SEALED"
                if account_passed
                else "V42_VALIDATION_RESEARCH_PASS_ACCOUNT_NOT_READY_CONFIRMATION_SEALED"
            )
        else:
            decision = "V42_VALIDATION_RESEARCH_FAIL_TERMINAL"
    elif research_passed:
        decision = (
            "V42_CONFIRMATION_RESEARCH_PASS_ACCOUNT_REFERENCE_PASS_RESEARCH_ONLY"
            if account_passed
            else "V42_CONFIRMATION_RESEARCH_PASS_ACCOUNT_NOT_READY_RESEARCH_ONLY"
        )
    else:
        decision = "V42_CONFIRMATION_RESEARCH_FAIL_TERMINAL"
    audit = {
        "schema_version": "xauusd_capital_shared_account_v42_stage_audit",
        "contract_sha256": str(contract["contract_sha256"]),
        "evidence_partition": str(v27_audit["evidence_partition"]),
        "stage_dates": [str(value) for value in v27_audit["stage_dates"]],
        "v27_audit_sha256": str(v27_audit["audit_sha256"]),
        "v27_stage_gate_passed": bool(v27_audit["gate_passed"]),
        "source_prefix_seals": dict(source_seals),
        **dict(result),
        "decision": decision,
        "trades_sha256": sha256_file(trades_path),
        "aggregate_economics_opened": True,
        "same_version_tuning_authorized": False,
        "model_training_authorized": False,
        "python_predictions_authorized": False,
        "ea_consumption_authorized": False,
        "demo_authorized": False,
        "live_authorized": False,
        "trade_permission": False,
        "broker_action_allowed": False,
    }
    audit["audit_sha256"] = canonical_hash(audit, "audit_sha256")
    write_json(audit_path, audit)
    return audit


def evaluate_stage_once(
    output: Path,
    config: Mapping[str, Any],
    contract: Mapping[str, Any],
    stage: str,
) -> dict[str, Any] | None:
    loaded = load_v27_stage(config, stage)
    if loaded is None:
        status = waiting_status(
            config,
            contract,
            stage=stage,
            reason=f"V27_{stage.upper()}_AUDIT_NOT_AVAILABLE",
        )
        write_json(output / config["outputs"]["status"], status)
        return None
    v27_audit, v27_trades = loaded
    try:
        bundle = load_source_bundle(config)
        dates = [str(value) for value in v27_audit["stage_dates"]]
        core = build_core_trades(bundle, dates, config)
        satellite = normalize_satellite_trades(v27_trades, config)
        combined_preview = pd.concat([core, satellite], ignore_index=True)
        tick_paths = select_tick_paths(combined_preview, config)
        combined, result = evaluate_stage(
            core,
            satellite,
            dates,
            v27_gate_passed=bool(v27_audit["gate_passed"]),
            tick_paths=tick_paths,
            config=config,
        )
    except StageNotReady as exc:
        status = waiting_status(
            config, contract, stage=stage, reason=f"CAUSAL_INPUTS_INCOMPLETE: {exc}"
        )
        write_json(output / config["outputs"]["status"], status)
        return None
    audit = persist_stage(
        output,
        config,
        contract,
        stage=stage,
        v27_audit=v27_audit,
        trades=combined,
        result=result,
        source_seals=bundle.seals,
    )
    status = {
        "schema_version": "xauusd_capital_shared_account_v42_status",
        "updated_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "status": "STAGE_SEALED",
        "contract_sha256": str(contract["contract_sha256"]),
        "latest_stage": stage.upper(),
        "latest_audit_sha256": str(audit["audit_sha256"]),
        "decision": str(audit["decision"]),
        "aggregate_economics_opened": True,
        "research_gate_passed": bool(audit["readiness"]["research_gate_passed"]),
        "account_gate_passed": bool(audit["readiness"]["account_gate_passed"]),
        "execution_ready": False,
        "same_version_tuning_authorized": False,
        "model_training_authorized": False,
        "python_predictions_authorized": False,
        "ea_consumption_authorized": False,
        "demo_authorized": False,
        "live_authorized": False,
        "trade_permission": False,
        "broker_action_allowed": False,
    }
    status["status_sha256"] = canonical_hash(status, "status_sha256")
    write_json(output / config["outputs"]["status"], status)
    return audit


def run_once() -> dict[str, Any]:
    config = load_config()
    contract = verify_contract(config)
    output = ROOT / str(config["outputs"]["directory"])
    output.mkdir(parents=True, exist_ok=True)
    validation_path = output / str(config["outputs"]["validation_audit"])
    if validation_path.exists():
        validation = verify_stage_output(output, config, contract, "validation")
    else:
        validation = evaluate_stage_once(output, config, contract, "validation")
        if validation is None:
            return json.loads(
                (output / config["outputs"]["status"]).read_text(encoding="utf-8")
            )
    if not bool(validation["readiness"]["research_gate_passed"]):
        return validation
    confirmation_path = output / str(config["outputs"]["confirmation_audit"])
    if confirmation_path.exists():
        return verify_stage_output(output, config, contract, "confirmation")
    confirmation = evaluate_stage_once(output, config, contract, "confirmation")
    return (
        confirmation
        if confirmation is not None
        else json.loads(
            (output / config["outputs"]["status"]).read_text(encoding="utf-8")
        )
    )


def failure_status(error: Exception) -> dict[str, Any]:
    return {
        "schema_version": "xauusd_capital_shared_account_v42_status",
        "updated_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "status": "FAILED_CLOSED",
        "error": f"{type(error).__name__}: {error}",
        "aggregate_economics_opened": False,
        "research_gate_passed": False,
        "account_gate_passed": False,
        "execution_ready": False,
        "same_version_tuning_authorized": False,
        "model_training_authorized": False,
        "python_predictions_authorized": False,
        "ea_consumption_authorized": False,
        "demo_authorized": False,
        "live_authorized": False,
        "trade_permission": False,
        "broker_action_allowed": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run sealed V42 shared-account evaluation"
    )
    parser.add_argument("--watch", action="store_true")
    parser.add_argument("--poll-seconds", type=int)
    args = parser.parse_args()
    config = load_config()
    poll = int(args.poll_seconds or config["runtime"]["poll_seconds"])
    while True:
        try:
            result = run_once()
            print(
                json.dumps(result, allow_nan=False, indent=2, sort_keys=True),
                flush=True,
            )
        except Exception as exc:  # fail closed at the process boundary
            status = failure_status(exc)
            output = ROOT / str(config["outputs"]["directory"])
            write_json(output / str(config["outputs"]["status"]), status)
            print(
                json.dumps(status, indent=2, sort_keys=True),
                file=sys.stderr,
                flush=True,
            )
            if not args.watch:
                return 1
        if not args.watch:
            return 0
        time.sleep(poll)


if __name__ == "__main__":
    raise SystemExit(main())
