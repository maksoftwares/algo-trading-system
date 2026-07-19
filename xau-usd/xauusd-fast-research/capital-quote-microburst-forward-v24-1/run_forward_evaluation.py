from __future__ import annotations

import json
from pathlib import Path
import sys
from typing import Any

import pandas as pd


ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]
sys.path.insert(0, str(ROOT / "src"))

from microburst import (  # noqa: E402
    assess_full_days,
    canonical_hash,
    discover_source_files,
    evaluate_stage,
    generate_candidates,
    load_config,
    load_ticks,
    sha256_file,
    simulate_trades,
    source_date,
)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, allow_nan=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def verify_contract(config: dict[str, Any]) -> dict[str, Any]:
    path = ROOT / config["outputs"]["directory"] / config["outputs"]["contract_lock"]
    contract = json.loads(path.read_text(encoding="utf-8"))
    if canonical_hash(contract, "contract_sha256") != contract["contract_sha256"]:
        raise ValueError("V24 contract self-hash mismatch")
    for record in contract["package_files"]:
        package_path = REPO / record["path"]
        if sha256_file(package_path) != record["sha256"]:
            raise ValueError(f"Locked V24 file changed: {record['path']}")
    return contract


def verify_calibration(
    config: dict[str, Any], contract: dict[str, Any]
) -> dict[str, Any]:
    path = (
        ROOT / config["outputs"]["directory"] / config["outputs"]["calibration_audit"]
    )
    audit = json.loads(path.read_text(encoding="utf-8"))
    if canonical_hash(audit, "audit_sha256") != audit["audit_sha256"]:
        raise ValueError("V24 calibration audit self-hash mismatch")
    if audit["contract_sha256"] != contract["contract_sha256"]:
        raise ValueError("V24 calibration audit contract mismatch")
    if not audit["calibration_structure_passed"]:
        raise ValueError("V24 calibration structure did not pass")
    if audit["economic_outcomes_opened"] or audit["pnl_calculated"]:
        raise ValueError("V24 calibration crossed its information boundary")
    return audit


def verify_stage_artifact(
    audit_path: Path, trades_path: Path, contract: dict[str, Any]
) -> dict[str, Any]:
    audit = json.loads(audit_path.read_text(encoding="utf-8"))
    if canonical_hash(audit, "audit_sha256") != audit["audit_sha256"]:
        raise ValueError(f"V24 stage audit self-hash mismatch: {audit_path}")
    if audit["contract_sha256"] != contract["contract_sha256"]:
        raise ValueError(f"V24 stage contract mismatch: {audit_path}")
    if not trades_path.is_file():
        raise FileNotFoundError(trades_path)
    if sha256_file(trades_path) != audit["trades_sha256"]:
        raise ValueError(f"V24 stage trades changed: {trades_path}")
    return audit


def persist_stage(
    trades: pd.DataFrame,
    audit: dict[str, Any],
    audit_path: Path,
    trades_path: Path,
    contract: dict[str, Any],
    full_day_quality: pd.DataFrame,
) -> dict[str, Any]:
    trades.to_csv(trades_path, index=False, lineterminator="\n")
    audit.update(
        {
            "contract_sha256": contract["contract_sha256"],
            "trades_sha256": sha256_file(trades_path),
            "full_day_quality": full_day_quality.to_dict(orient="records"),
            "same_version_tuning_authorized": False,
            "model_training_authorized": False,
            "python_predictions_authorized": False,
            "ea_consumption_authorized": False,
            "demo_authorized": False,
            "live_authorized": False,
            "broker_action_authorized": False,
        }
    )
    audit["audit_sha256"] = canonical_hash(audit, "audit_sha256")
    write_json(audit_path, audit)
    return audit


def main() -> int:
    config = load_config(ROOT)
    contract = verify_contract(config)
    calibration = verify_calibration(config, contract)
    boundary = pd.Timestamp(config["forward"]["start_inclusive_utc"])
    paths = [
        path for path in discover_source_files(config) if source_date(path) >= boundary
    ]
    ticks, source_audit, raw_daily = load_ticks(paths, config)
    full_days = assess_full_days(ticks, raw_daily, config)
    eligible_dates = (
        full_days.loc[full_days["eligible_full_weekday"], "date_utc"].tolist()
        if not full_days.empty
        else []
    )
    candidates, _ = generate_candidates(ticks, config)
    candidates = candidates.loc[
        candidates["tick_time_msc"].ge(int(boundary.timestamp() * 1000))
    ].reset_index(drop=True)
    output = ROOT / config["outputs"]["directory"]
    inventory_path = output / config["outputs"]["forward_inventory"]
    inventory = {
        "schema_version": "xauusd_v24_1_forward_inventory",
        "contract_sha256": contract["contract_sha256"],
        "calibration_audit_sha256": calibration["audit_sha256"],
        "source_audit": source_audit,
        "full_day_quality": full_days.to_dict(orient="records"),
        "eligible_full_weekdays": eligible_dates,
        "eligible_full_weekday_count": len(eligible_dates),
        "candidate_count_all_loaded_forward_data": int(len(candidates)),
        "economic_outcomes_opened_by_inventory": False,
    }
    inventory["inventory_sha256"] = canonical_hash(inventory, "inventory_sha256")
    write_json(inventory_path, inventory)

    forward = config["forward"]
    validation_days = int(forward["validation_full_weekdays"])
    confirmation_days = int(forward["confirmation_full_weekdays"])
    validation_dates = eligible_dates[:validation_days]
    confirmation_dates = eligible_dates[
        validation_days : validation_days + confirmation_days
    ]
    validation_audit_path = ROOT / forward["validation_audit"]
    confirmation_audit_path = ROOT / forward["confirmation_audit"]
    validation_trades_path = output / config["outputs"]["validation_trades"]
    confirmation_trades_path = output / config["outputs"]["confirmation_trades"]

    if validation_audit_path.exists():
        validation_audit = verify_stage_artifact(
            validation_audit_path, validation_trades_path, contract
        )
    else:
        if len(validation_dates) < validation_days:
            print(
                json.dumps(
                    {
                        "decision": "V24_1_CONTINUE_SEALED_FORWARD_COLLECTION",
                        "eligible_full_weekdays": len(eligible_dates),
                        "required_for_validation": validation_days,
                        "economic_outcomes_opened": False,
                    },
                    indent=2,
                    sort_keys=True,
                )
            )
            return 0
        validation_trades = simulate_trades(
            ticks,
            candidates,
            validation_dates,
            "FORWARD_VALIDATION",
            config,
        )
        validation_audit, _ = evaluate_stage(
            validation_trades,
            validation_dates,
            "FORWARD_VALIDATION",
            config,
        )
        validation_audit["decision"] = (
            "V24_1_FORWARD_VALIDATION_PASS_CONFIRMATION_REMAINS_SEALED"
            if validation_audit["gate_passed"]
            else "V24_1_FORWARD_VALIDATION_FAIL_TERMINAL"
        )
        quality = full_days.loc[full_days["date_utc"].isin(validation_dates)]
        validation_audit = persist_stage(
            validation_trades,
            validation_audit,
            validation_audit_path,
            validation_trades_path,
            contract,
            quality,
        )
        print(json.dumps(validation_audit, indent=2, sort_keys=True))
        return 0

    if not validation_audit["gate_passed"]:
        print(json.dumps(validation_audit, indent=2, sort_keys=True))
        return 0
    if confirmation_audit_path.exists():
        confirmation_audit = verify_stage_artifact(
            confirmation_audit_path, confirmation_trades_path, contract
        )
        print(json.dumps(confirmation_audit, indent=2, sort_keys=True))
        return 0
    if len(confirmation_dates) < confirmation_days:
        print(
            json.dumps(
                {
                    "decision": "V24_1_VALIDATION_PASSED_CONTINUE_SEALED_CONFIRMATION_COLLECTION",
                    "confirmation_full_weekdays": len(confirmation_dates),
                    "required_for_confirmation": confirmation_days,
                    "confirmation_economic_outcomes_opened": False,
                },
                indent=2,
                sort_keys=True,
            )
        )
        return 0
    confirmation_trades = simulate_trades(
        ticks,
        candidates,
        confirmation_dates,
        "FORWARD_CONFIRMATION",
        config,
    )
    confirmation_audit, _ = evaluate_stage(
        confirmation_trades,
        confirmation_dates,
        "FORWARD_CONFIRMATION",
        config,
    )
    confirmation_audit["decision"] = (
        "V24_1_FORWARD_CONFIRMATION_PASS_RESEARCH_SHADOW_NOMINATION_ONLY"
        if confirmation_audit["gate_passed"]
        else "V24_1_FORWARD_CONFIRMATION_FAIL_TERMINAL"
    )
    quality = full_days.loc[full_days["date_utc"].isin(confirmation_dates)]
    confirmation_audit = persist_stage(
        confirmation_trades,
        confirmation_audit,
        confirmation_audit_path,
        confirmation_trades_path,
        contract,
        quality,
    )
    print(json.dumps(confirmation_audit, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
