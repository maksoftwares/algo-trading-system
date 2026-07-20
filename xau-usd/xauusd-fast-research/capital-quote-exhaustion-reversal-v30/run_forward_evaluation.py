from __future__ import annotations

import json
from pathlib import Path
import sys
from typing import Any, Mapping

import pandas as pd


ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]
sys.path.insert(0, str(ROOT / "src"))

from exhaustion_reversal import (  # noqa: E402
    canonical_hash,
    generate_candidates,
    load_config,
    load_locked_v24,
    selection_adjusted_evaluation,
    sha256_file,
)


def write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.write_bytes(
        (json.dumps(payload, allow_nan=False, indent=2, sort_keys=True) + "\n").encode(
            "utf-8"
        )
    )


def resolve_record(record: Mapping[str, Any]) -> Path:
    path = Path(str(record["path"]))
    if not path.is_absolute():
        path = REPO / path
    path = path.resolve()
    if (
        not path.is_file()
        or int(path.stat().st_size) != int(record["bytes"])
        or sha256_file(path) != str(record["sha256"])
    ):
        raise ValueError(f"V30 locked file changed: {record['path']}")
    return path


def verify_contract(config: Mapping[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    output = ROOT / config["outputs"]["directory"]
    contract_path = output / config["outputs"]["contract_lock"]
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    if canonical_hash(contract, "contract_sha256") != contract["contract_sha256"]:
        raise ValueError("V30 contract self-hash changed")
    for record in (
        contract["package_files"]
        + contract["dependency_files"]
        + contract["development_source_files"]
        + [contract["calibration_candidates"], contract["calibration_audit"]]
    ):
        resolve_record(record)
    development_path = output / config["outputs"]["development_audit"]
    development = json.loads(development_path.read_text(encoding="utf-8"))
    if canonical_hash(development, "audit_sha256") != development["audit_sha256"]:
        raise ValueError("V30 development audit self-hash changed")
    trades_path = output / config["outputs"]["development_trades"]
    if sha256_file(trades_path) != development["trades_sha256"]:
        raise ValueError("V30 development trades changed")
    if development["contract_sha256"] != contract["contract_sha256"]:
        raise ValueError("V30 development contract mismatch")
    return contract, development


def verify_stage(
    audit_path: Path, trades_path: Path, contract: Mapping[str, Any]
) -> dict[str, Any]:
    audit = json.loads(audit_path.read_text(encoding="utf-8"))
    if canonical_hash(audit, "audit_sha256") != audit["audit_sha256"]:
        raise ValueError(f"V30 stage audit self-hash changed: {audit_path}")
    if audit["contract_sha256"] != contract["contract_sha256"]:
        raise ValueError(f"V30 stage contract mismatch: {audit_path}")
    if not trades_path.is_file() or sha256_file(trades_path) != audit["trades_sha256"]:
        raise ValueError(f"V30 stage trades changed: {trades_path}")
    return audit


def persist_stage(
    trades: pd.DataFrame,
    audit: dict[str, Any],
    audit_path: Path,
    trades_path: Path,
    contract: Mapping[str, Any],
    quality: pd.DataFrame,
) -> dict[str, Any]:
    trades_path.write_bytes(trades.to_csv(index=False, lineterminator="\n").encode())
    audit.update(
        {
            "contract_sha256": contract["contract_sha256"],
            "trades_sha256": sha256_file(trades_path),
            "full_day_quality": quality.to_dict(orient="records"),
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
    contract, development = verify_contract(config)
    if not development["gate_passed"]:
        print(
            json.dumps(
                {
                    "decision": "V30_DEVELOPMENT_FAILED_FORWARD_ECONOMICS_SEALED",
                    "development_audit_sha256": development["audit_sha256"],
                    "forward_economic_outcomes_opened": False,
                },
                indent=2,
                sort_keys=True,
            )
        )
        return 0
    v24 = load_locked_v24(config)
    boundary = pd.Timestamp(config["forward"]["start_inclusive_utc"])
    paths = [
        path
        for path in v24.discover_source_files(config)
        if v24.source_date(path) >= boundary
    ]
    ticks, source_audit, raw_daily = v24.load_ticks(paths, config)
    full_days = v24.assess_full_days(ticks, raw_daily, config)
    dates = (
        full_days.loc[full_days["eligible_full_weekday"], "date_utc"].tolist()
        if not full_days.empty
        else []
    )
    candidates, structural = generate_candidates(ticks, config)
    candidates = candidates.loc[
        candidates["tick_time_msc"].ge(int(boundary.timestamp() * 1000))
    ].reset_index(drop=True)
    output = ROOT / config["outputs"]["directory"]
    inventory = {
        "schema_version": "xauusd_v30_forward_inventory",
        "contract_sha256": contract["contract_sha256"],
        "development_audit_sha256": development["audit_sha256"],
        "source_audit": source_audit,
        "full_day_quality": full_days.to_dict(orient="records"),
        "eligible_full_weekdays": dates,
        "eligible_full_weekday_count": len(dates),
        "impulse_arm_count_all_loaded_forward_data": structural["impulse_arm_count"],
        "raw_trigger_count_all_loaded_forward_data": structural["raw_trigger_count"],
        "candidate_count_all_loaded_forward_data": int(len(candidates)),
        "economic_outcomes_opened_by_inventory": False,
    }
    inventory["inventory_sha256"] = canonical_hash(inventory, "inventory_sha256")
    write_json(output / config["outputs"]["forward_inventory"], inventory)
    forward = config["forward"]
    validation_count = int(forward["validation_full_weekdays"])
    confirmation_count = int(forward["confirmation_full_weekdays"])
    validation_dates = dates[:validation_count]
    confirmation_dates = dates[validation_count : validation_count + confirmation_count]
    validation_audit_path = ROOT / forward["validation_audit"]
    confirmation_audit_path = ROOT / forward["confirmation_audit"]
    validation_trades_path = output / config["outputs"]["validation_trades"]
    confirmation_trades_path = output / config["outputs"]["confirmation_trades"]
    if validation_audit_path.exists():
        validation = verify_stage(
            validation_audit_path, validation_trades_path, contract
        )
    else:
        if len(validation_dates) < validation_count:
            print(
                json.dumps(
                    {
                        "decision": "V30_CONTINUE_SEALED_FORWARD_COLLECTION",
                        "eligible_full_weekdays": len(dates),
                        "required_for_validation": validation_count,
                        "economic_outcomes_opened": False,
                    },
                    indent=2,
                    sort_keys=True,
                )
            )
            return 0
        trades = v24.simulate_trades(
            ticks, candidates, validation_dates, "FORWARD_VALIDATION", config
        )
        validation, _ = selection_adjusted_evaluation(
            trades, validation_dates, "FORWARD_VALIDATION", config, v24
        )
        validation["decision"] = (
            "V30_FORWARD_VALIDATION_PASS_CONFIRMATION_REMAINS_SEALED"
            if validation["gate_passed"]
            else "V30_FORWARD_VALIDATION_FAIL_TERMINAL"
        )
        quality = full_days.loc[full_days["date_utc"].isin(validation_dates)]
        validation = persist_stage(
            trades,
            validation,
            validation_audit_path,
            validation_trades_path,
            contract,
            quality,
        )
        print(json.dumps(validation, indent=2, sort_keys=True))
        return 0
    if not validation["gate_passed"]:
        print(json.dumps(validation, indent=2, sort_keys=True))
        return 0
    if confirmation_audit_path.exists():
        confirmation = verify_stage(
            confirmation_audit_path, confirmation_trades_path, contract
        )
        print(json.dumps(confirmation, indent=2, sort_keys=True))
        return 0
    if len(confirmation_dates) < confirmation_count:
        print(
            json.dumps(
                {
                    "decision": "V30_VALIDATION_PASSED_CONTINUE_SEALED_CONFIRMATION",
                    "confirmation_full_weekdays": len(confirmation_dates),
                    "required_for_confirmation": confirmation_count,
                    "confirmation_economic_outcomes_opened": False,
                },
                indent=2,
                sort_keys=True,
            )
        )
        return 0
    trades = v24.simulate_trades(
        ticks, candidates, confirmation_dates, "FORWARD_CONFIRMATION", config
    )
    confirmation, _ = selection_adjusted_evaluation(
        trades, confirmation_dates, "FORWARD_CONFIRMATION", config, v24
    )
    confirmation["decision"] = (
        "V30_FORWARD_CONFIRMATION_PASS_RESEARCH_SHADOW_ONLY"
        if confirmation["gate_passed"]
        else "V30_FORWARD_CONFIRMATION_FAIL_TERMINAL"
    )
    quality = full_days.loc[full_days["date_utc"].isin(confirmation_dates)]
    confirmation = persist_stage(
        trades,
        confirmation,
        confirmation_audit_path,
        confirmation_trades_path,
        contract,
        quality,
    )
    print(json.dumps(confirmation, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
