from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys
from typing import Any, Mapping


ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]
V30_ROOT = ROOT.parent / "capital-quote-exhaustion-reversal-v30"
TRANSPORT_ROOT = ROOT.parent / "capital-quote-exhaustion-reversal-v30-postlock-adapter"
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(TRANSPORT_ROOT / "src"))

from adapter import load_ticks  # noqa: E402
from alias import add_simulator_aliases  # noqa: E402


def load_v30() -> Any:
    path = V30_ROOT / "src" / "exhaustion_reversal.py"
    spec = importlib.util.spec_from_file_location("v30_alias_run", path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def resolve_record(record: Mapping[str, Any], v30: Any) -> Path:
    path = (REPO / str(record["path"])).resolve()
    if (
        not path.is_file()
        or int(path.stat().st_size) != int(record["bytes"])
        or v30.sha256_file(path) != str(record["sha256"])
    ):
        raise ValueError(f"V30 alias locked file changed: {record['path']}")
    return path


def verify_parent_contracts(alias_lock: Mapping[str, Any], v30: Any) -> dict[str, Any]:
    for record in alias_lock["package_files"] + [
        alias_lock["v30_contract_file"],
        alias_lock["timestamp_adapter_contract_file"],
    ]:
        resolve_record(record, v30)
    v30_contract = json.loads(
        resolve_record(alias_lock["v30_contract_file"], v30).read_text(encoding="utf-8")
    )
    if (
        v30.canonical_hash(v30_contract, "contract_sha256")
        != v30_contract["contract_sha256"]
    ):
        raise ValueError("V30 contract self-hash changed")
    records = (
        v30_contract["package_files"]
        + v30_contract["dependency_files"]
        + v30_contract["development_source_files"]
        + [v30_contract["calibration_candidates"], v30_contract["calibration_audit"]]
    )
    for record in records:
        resolve_record(record, v30)
    return v30_contract


def main() -> int:
    v30 = load_v30()
    alias_lock_path = ROOT / "outputs" / "V30_SIMULATOR_ALIAS_LOCK.json"
    alias_lock = json.loads(alias_lock_path.read_text(encoding="utf-8"))
    if (
        v30.canonical_hash(alias_lock, "alias_contract_sha256")
        != alias_lock["alias_contract_sha256"]
    ):
        raise ValueError("V30 alias contract self-hash changed")
    contract = verify_parent_contracts(alias_lock, v30)
    config = v30.load_config(V30_ROOT)
    output = V30_ROOT / config["outputs"]["directory"]
    audit_path = output / config["outputs"]["development_audit"]
    trades_path = output / config["outputs"]["development_trades"]
    if audit_path.exists():
        audit = json.loads(audit_path.read_text(encoding="utf-8"))
        if v30.canonical_hash(audit, "audit_sha256") != audit["audit_sha256"]:
            raise ValueError("V30 development audit self-hash changed")
        if v30.sha256_file(trades_path) != audit["trades_sha256"]:
            raise ValueError("V30 development trades changed")
        print(json.dumps(audit, indent=2, sort_keys=True))
        return 0
    paths = v30.development_source_paths(config)
    ticks, source_audit, raw_daily = load_ticks(paths, config, v30)
    v24 = v30.load_locked_v24(config)
    full_days = v24.assess_full_days(ticks, raw_daily, config)
    dates = full_days.loc[full_days["eligible_full_weekday"], "date_utc"].tolist()
    if len(dates) < 5:
        raise ValueError("V30 alias run found fewer than five eligible weekdays")
    candidates, structural = v30.generate_candidates(ticks, config)
    simulator_candidates = add_simulator_aliases(candidates)
    trades = v24.simulate_trades(
        ticks, simulator_candidates, dates, "DEVELOPMENT", config
    )
    audit, daily = v24.evaluate_stage(trades, dates, "DEVELOPMENT", config)
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
            "adapter_contract_sha256": alias_lock["alias_contract_sha256"],
            "timestamp_adapter_applied": True,
            "simulator_metadata_alias_applied": True,
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
