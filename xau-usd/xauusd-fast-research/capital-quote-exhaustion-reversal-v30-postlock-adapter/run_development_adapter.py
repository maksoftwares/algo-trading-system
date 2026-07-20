from __future__ import annotations

import json
from pathlib import Path
import sys
from typing import Any, Mapping


ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]
sys.path.insert(0, str(ROOT / "src"))

from adapter import (  # noqa: E402
    load_adapter_config,
    load_ticks,
    load_v30_module,
    v30_root,
)


def resolve_record(record: Mapping[str, Any], v30: Any) -> Path:
    path = (REPO / str(record["path"])).resolve()
    if (
        not path.is_file()
        or int(path.stat().st_size) != int(record["bytes"])
        or v30.sha256_file(path) != str(record["sha256"])
    ):
        raise ValueError(f"Locked adapter file changed: {record['path']}")
    return path


def verify_v30_contract(path: Path, expected: str, v30: Any) -> dict[str, Any]:
    contract = json.loads(path.read_text(encoding="utf-8"))
    if v30.canonical_hash(contract, "contract_sha256") != contract["contract_sha256"]:
        raise ValueError("V30 contract self-hash changed")
    if contract["contract_sha256"] != expected:
        raise ValueError("V30 contract identity changed")
    records = (
        contract["package_files"]
        + contract["dependency_files"]
        + contract["development_source_files"]
        + [contract["calibration_candidates"], contract["calibration_audit"]]
    )
    for record in records:
        resolve_record(record, v30)
    return contract


def main() -> int:
    adapter_config = load_adapter_config()
    v30 = load_v30_module(adapter_config)
    lock_path = ROOT / adapter_config["outputs"]["adapter_lock"]
    adapter_lock = json.loads(lock_path.read_text(encoding="utf-8"))
    if (
        v30.canonical_hash(adapter_lock, "adapter_contract_sha256")
        != adapter_lock["adapter_contract_sha256"]
    ):
        raise ValueError("V30 adapter lock self-hash changed")
    for record in adapter_lock["package_files"] + [adapter_lock["v30_contract_file"]]:
        resolve_record(record, v30)
    strategy_root = v30_root(adapter_config)
    config = v30.load_config(strategy_root)
    contract_path = strategy_root / adapter_config["v30_contract_relative"]
    contract = verify_v30_contract(
        contract_path, adapter_lock["v30_contract_sha256"], v30
    )
    output = strategy_root / config["outputs"]["directory"]
    audit_path = output / config["outputs"]["development_audit"]
    trades_path = output / config["outputs"]["development_trades"]
    if audit_path.exists():
        audit = json.loads(audit_path.read_text(encoding="utf-8"))
        if v30.canonical_hash(audit, "audit_sha256") != audit["audit_sha256"]:
            raise ValueError("V30 adapter development audit self-hash changed")
        if v30.sha256_file(trades_path) != audit["trades_sha256"]:
            raise ValueError("V30 adapter development trades changed")
        print(json.dumps(audit, indent=2, sort_keys=True))
        return 0
    paths = v30.development_source_paths(config)
    ticks, source_audit, raw_daily = load_ticks(paths, config, v30)
    locked_v24 = v30.load_locked_v24(config)
    full_days = locked_v24.assess_full_days(ticks, raw_daily, config)
    dates = full_days.loc[full_days["eligible_full_weekday"], "date_utc"].tolist()
    if len(dates) < 5:
        raise ValueError("V30 adapter found fewer than five eligible weekdays")
    candidates, structural = v30.generate_candidates(ticks, config)
    trades = locked_v24.simulate_trades(ticks, candidates, dates, "DEVELOPMENT", config)
    audit, daily = locked_v24.evaluate_stage(trades, dates, "DEVELOPMENT", config)
    trades_path.write_bytes(trades.to_csv(index=False, lineterminator="\n").encode())
    audit.update(
        {
            "schema_version": "xauusd_v30_adapter_development_audit",
            "decision": (
                "V30_DEVELOPMENT_PASS_FORWARD_REMAINS_SEALED"
                if audit["gate_passed"]
                else "V30_DEVELOPMENT_FAIL_TERMINAL"
            ),
            "contract_sha256": contract["contract_sha256"],
            "adapter_contract_sha256": adapter_lock["adapter_contract_sha256"],
            "timestamp_adapter_applied": True,
            "timestamp_rule": adapter_lock["timestamp_rule"],
            "source_audit": source_audit,
            "full_day_quality": full_days.to_dict(orient="records"),
            "impulse_arm_count": structural["impulse_arm_count"],
            "raw_trigger_count": structural["raw_trigger_count"],
            "selected_candidate_count": int(len(candidates)),
            "daily_metrics": daily.to_dict(orient="records"),
            "trades_sha256": v30.sha256_file(trades_path),
            "same_version_tuning_authorized": False,
            "model_training_authorized": False,
            "python_predictions_authorized": False,
            "ea_consumption_authorized": False,
            "demo_authorized": False,
            "live_authorized": False,
            "broker_action_authorized": False,
        }
    )
    audit["audit_sha256"] = v30.canonical_hash(audit, "audit_sha256")
    audit_path.write_bytes(
        (json.dumps(audit, allow_nan=False, indent=2, sort_keys=True) + "\n").encode()
    )
    print(json.dumps(audit, allow_nan=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
