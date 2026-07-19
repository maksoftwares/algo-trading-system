from __future__ import annotations

import json
from pathlib import Path
import sys
from typing import Any, Mapping

import pandas as pd


ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]
sys.path.insert(0, str(ROOT / "src"))

from portfolio import (  # noqa: E402
    canonical_hash,
    component_pvalue,
    evaluate_fixed_union,
    load_config,
    route_fixed_union,
    sha256_file,
    validate_trade_frame,
    verify_core_reference,
)


def write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.write_bytes(
        (json.dumps(payload, allow_nan=False, indent=2, sort_keys=True) + "\n").encode(
            "utf-8"
        )
    )


def verify_record(record: Mapping[str, Any]) -> Path:
    path = (REPO / str(record["path"])).resolve()
    if (
        not path.is_file()
        or int(path.stat().st_size) != int(record["bytes"])
        or sha256_file(path) != str(record["sha256"])
    ):
        raise ValueError(f"V27 locked file changed: {record['path']}")
    return path


def verify_contract(
    config: Mapping[str, Any],
) -> tuple[dict[str, Any], pd.DataFrame, dict[str, Any]]:
    path = ROOT / config["outputs"]["directory"] / config["outputs"]["contract_lock"]
    contract = json.loads(path.read_text(encoding="utf-8"))
    if canonical_hash(contract, "contract_sha256") != contract["contract_sha256"]:
        raise ValueError("V27 contract self-hash changed")
    for record in contract["package_files"] + contract["component_contracts"]:
        verify_record(record)
    core_path = verify_record(contract["core_ledger"])
    core_reference, core_metrics = verify_core_reference(
        pd.read_parquet(core_path), config
    )
    if core_metrics != contract["core_reference_metrics"]:
        raise ValueError("V27 locked Core metrics changed")
    return contract, core_reference, core_metrics


def stage_paths(config: Mapping[str, Any], lane: str, stage: str) -> tuple[Path, Path]:
    component = config["components"][lane]
    return (
        (REPO / component[f"{stage}_audit"]).resolve(),
        (REPO / component[f"{stage}_trades"]).resolve(),
    )


def component_stage_available(config: Mapping[str, Any], lane: str, stage: str) -> bool:
    audit_path, trades_path = stage_paths(config, lane, stage)
    if audit_path.exists() != trades_path.exists():
        raise ValueError(f"V27 {lane} {stage} component artifact is incomplete")
    return audit_path.exists()


def load_component_stage(
    config: Mapping[str, Any], lane: str, stage: str, partition: str
) -> tuple[dict[str, Any], pd.DataFrame]:
    audit_path, trades_path = stage_paths(config, lane, stage)
    audit = json.loads(audit_path.read_text(encoding="utf-8"))
    if canonical_hash(audit, "audit_sha256") != audit["audit_sha256"]:
        raise ValueError(f"V27 {lane} {stage} audit self-hash changed")
    component = config["components"][lane]
    if audit["contract_sha256"] != component["contract_sha256"]:
        raise ValueError(f"V27 {lane} {stage} contract identity changed")
    if sha256_file(trades_path) != audit["trades_sha256"]:
        raise ValueError(f"V27 {lane} {stage} trades changed")
    trades = pd.read_csv(trades_path)
    validate_trade_frame(trades, lane)
    dates = [str(value) for value in audit["stage_dates"]]
    if len(dates) != int(config["stages"]["required_full_weekdays_per_stage"]):
        raise ValueError(f"V27 {lane} {stage} has the wrong day count")
    if audit["evidence_partition"] != partition:
        raise ValueError(f"V27 {lane} {stage} audit partition changed")
    if not trades["evidence_partition"].eq(partition).all():
        raise ValueError(f"V27 {lane} {stage} partition changed")
    if not trades["date_utc"].isin(dates).all():
        raise ValueError(f"V27 {lane} {stage} contains an out-of-stage trade")
    return audit, trades


def write_waiting_status(
    output: Path,
    contract: Mapping[str, Any],
    config: Mapping[str, Any],
    stage: str,
) -> dict[str, Any]:
    availability = {
        lane: component_stage_available(config, lane, stage)
        for lane in config["router"]["fixed_priority"]
    }
    status = {
        "schema_version": "xauusd_capital_forward_family_v27_status",
        "contract_sha256": contract["contract_sha256"],
        "waiting_for_stage": stage.upper(),
        "component_stage_artifacts_available": availability,
        "component_economic_outcomes_opened_by_v27": False,
        "portfolio_economic_outcomes_opened": False,
        "decision": f"V27_WAITING_FOR_COMPONENT_{stage.upper()}",
    }
    status["status_sha256"] = canonical_hash(status, "status_sha256")
    write_json(output / config["outputs"]["status"], status)
    return status


def persist_stage(
    output: Path,
    config: Mapping[str, Any],
    stage: str,
    audit: dict[str, Any],
    trades: pd.DataFrame | None,
    contract: Mapping[str, Any],
) -> dict[str, Any]:
    audit_path = output / config["outputs"][f"{stage}_audit"]
    trades_path = output / config["outputs"][f"{stage}_trades"]
    audit.update(
        {
            "contract_sha256": contract["contract_sha256"],
            "same_version_tuning_authorized": False,
            "single_lane_fallback_authorized": False,
            "model_training_authorized": False,
            "python_predictions_authorized": False,
            "ea_consumption_authorized": False,
            "demo_authorized": False,
            "live_authorized": False,
            "broker_action_authorized": False,
        }
    )
    if trades is not None:
        trades_path.write_bytes(
            trades.to_csv(index=False, lineterminator="\n").encode()
        )
        audit["portfolio_trades_sha256"] = sha256_file(trades_path)
    elif trades_path.exists():
        raise ValueError(f"V27 stale {stage} portfolio trades exist")
    audit["audit_sha256"] = canonical_hash(audit, "audit_sha256")
    write_json(audit_path, audit)
    return audit


def verify_v27_stage(
    output: Path,
    config: Mapping[str, Any],
    stage: str,
    contract: Mapping[str, Any],
) -> dict[str, Any]:
    audit_path = output / config["outputs"][f"{stage}_audit"]
    audit = json.loads(audit_path.read_text(encoding="utf-8"))
    if canonical_hash(audit, "audit_sha256") != audit["audit_sha256"]:
        raise ValueError(f"V27 {stage} audit self-hash changed")
    if audit["contract_sha256"] != contract["contract_sha256"]:
        raise ValueError(f"V27 {stage} contract identity changed")
    if audit["portfolio_economic_outcomes_opened"]:
        trades_path = output / config["outputs"][f"{stage}_trades"]
        if (
            not trades_path.is_file()
            or sha256_file(trades_path) != audit["portfolio_trades_sha256"]
        ):
            raise ValueError(f"V27 {stage} portfolio trades changed")
    return audit


def evaluate_stage_once(
    output: Path,
    config: Mapping[str, Any],
    contract: Mapping[str, Any],
    core_reference: pd.DataFrame,
    core_metrics: Mapping[str, Any],
    stage: str,
    partition: str,
) -> dict[str, Any] | None:
    lanes = list(config["router"]["fixed_priority"])
    if not all(component_stage_available(config, lane, stage) for lane in lanes):
        status = write_waiting_status(output, contract, config, stage)
        print(json.dumps(status, indent=2, sort_keys=True))
        return None
    loaded = {
        lane: load_component_stage(config, lane, stage, partition) for lane in lanes
    }
    stage_dates = [str(value) for value in loaded[lanes[0]][0]["stage_dates"]]
    if any(
        [str(value) for value in loaded[lane][0]["stage_dates"]] != stage_dates
        for lane in lanes[1:]
    ):
        raise ValueError("V27 component stage dates differ")
    alpha = float(config["multiple_testing"]["maximum_one_sided_pvalue"])
    component_results: dict[str, Any] = {}
    for lane in lanes:
        audit, trades = loaded[lane]
        pvalue = component_pvalue(
            trades,
            stage_dates,
            config,
            int(config["components"][lane]["bootstrap_seed"]),
        )
        component_results[lane] = {
            "component_audit_sha256": audit["audit_sha256"],
            "component_original_gate_passed": bool(audit["gate_passed"]),
            "external_block_bootstrap_pvalue": pvalue,
            "external_selection_gate_passed": pvalue <= alpha,
            "component_admitted_to_fixed_union": bool(
                audit["gate_passed"] and pvalue <= alpha
            ),
        }
    if not all(
        result["component_admitted_to_fixed_union"]
        for result in component_results.values()
    ):
        audit = {
            "schema_version": "xauusd_capital_forward_family_v27_stage_audit",
            "evidence_partition": partition,
            "stage_dates": stage_dates,
            "component_results": component_results,
            "portfolio_economic_outcomes_opened": False,
            "gate_passed": False,
            "decision": f"V27_{stage.upper()}_COMPONENT_ADMISSION_FAIL_TERMINAL",
        }
        return persist_stage(output, config, stage, audit, None, contract)
    selected, route_audit = route_fixed_union(
        loaded["V24_1"][1], loaded["V26"][1], config
    )
    audit, _ = evaluate_fixed_union(
        selected,
        stage_dates,
        partition,
        core_reference,
        core_metrics,
        route_audit,
        config,
    )
    audit["component_results"] = component_results
    audit["portfolio_economic_outcomes_opened"] = True
    if stage == "validation":
        audit["decision"] = (
            "V27_VALIDATION_PASS_CONFIRMATION_REMAINS_SEALED"
            if audit["gate_passed"]
            else "V27_VALIDATION_PORTFOLIO_FAIL_TERMINAL"
        )
    else:
        audit["decision"] = (
            "V27_CONFIRMATION_PASS_RESEARCH_SHADOW_ONLY"
            if audit["gate_passed"]
            else "V27_CONFIRMATION_PORTFOLIO_FAIL_TERMINAL"
        )
    return persist_stage(output, config, stage, audit, selected, contract)


def main() -> int:
    config = load_config(ROOT)
    contract, core_reference, core_metrics = verify_contract(config)
    output = ROOT / config["outputs"]["directory"]
    output.mkdir(parents=True, exist_ok=True)
    validation_path = output / config["outputs"]["validation_audit"]
    if validation_path.exists():
        validation = verify_v27_stage(output, config, "validation", contract)
    else:
        validation = evaluate_stage_once(
            output,
            config,
            contract,
            core_reference,
            core_metrics,
            "validation",
            config["stages"]["validation_partition"],
        )
        if validation is None:
            return 0
        print(json.dumps(validation, indent=2, sort_keys=True))
        return 0
    if not validation["gate_passed"]:
        print(json.dumps(validation, indent=2, sort_keys=True))
        return 0
    confirmation_path = output / config["outputs"]["confirmation_audit"]
    if confirmation_path.exists():
        confirmation = verify_v27_stage(output, config, "confirmation", contract)
    else:
        confirmation = evaluate_stage_once(
            output,
            config,
            contract,
            core_reference,
            core_metrics,
            "confirmation",
            config["stages"]["confirmation_partition"],
        )
        if confirmation is None:
            return 0
    print(json.dumps(confirmation, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
