from __future__ import annotations

import json
from pathlib import Path
import sys
from typing import Any, Mapping


ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]
sys.path.insert(0, str(ROOT / "src"))

from exhaustion_reversal import (  # noqa: E402
    canonical_hash,
    development_source_paths,
    generate_candidates,
    load_config,
    load_development_ticks,
    load_locked_v24,
    sha256_file,
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


def verify_contract(config: Mapping[str, Any]) -> dict[str, Any]:
    path = ROOT / config["outputs"]["directory"] / config["outputs"]["contract_lock"]
    contract = json.loads(path.read_text(encoding="utf-8"))
    if canonical_hash(contract, "contract_sha256") != contract["contract_sha256"]:
        raise ValueError("V30 contract self-hash changed")
    for record in (
        contract["package_files"]
        + contract["dependency_files"]
        + contract["development_source_files"]
        + [contract["calibration_candidates"], contract["calibration_audit"]]
    ):
        resolve_record(record)
    return contract


def main() -> int:
    config = load_config(ROOT)
    contract = verify_contract(config)
    output = ROOT / config["outputs"]["directory"]
    audit_path = output / config["outputs"]["development_audit"]
    trades_path = output / config["outputs"]["development_trades"]
    if audit_path.exists():
        audit = json.loads(audit_path.read_text(encoding="utf-8"))
        if canonical_hash(audit, "audit_sha256") != audit["audit_sha256"]:
            raise ValueError("V30 development audit self-hash changed")
        if sha256_file(trades_path) != audit["trades_sha256"]:
            raise ValueError("V30 development trades changed")
        print(json.dumps(audit, indent=2, sort_keys=True))
        return 0
    v24 = load_locked_v24(config)
    paths = development_source_paths(config)
    ticks, source_audit, raw_daily = load_development_ticks(paths, config)
    full_days = v24.assess_full_days(ticks, raw_daily, config)
    dates = full_days.loc[full_days["eligible_full_weekday"], "date_utc"].tolist()
    if len(dates) < 5:
        raise ValueError("V30 has fewer than five eligible development weekdays")
    candidates, structural = generate_candidates(ticks, config)
    trades = v24.simulate_trades(ticks, candidates, dates, "DEVELOPMENT", config)
    audit, daily = v24.evaluate_stage(trades, dates, "DEVELOPMENT", config)
    audit["schema_version"] = "xauusd_v30_development_audit"
    audit["decision"] = (
        "V30_DEVELOPMENT_PASS_FORWARD_REMAINS_SEALED"
        if audit["gate_passed"]
        else "V30_DEVELOPMENT_FAIL_TERMINAL"
    )
    trades_path.write_bytes(trades.to_csv(index=False, lineterminator="\n").encode())
    audit.update(
        {
            "contract_sha256": contract["contract_sha256"],
            "source_audit": source_audit,
            "full_day_quality": full_days.to_dict(orient="records"),
            "impulse_arm_count": structural["impulse_arm_count"],
            "raw_trigger_count": structural["raw_trigger_count"],
            "selected_candidate_count": int(len(candidates)),
            "daily_metrics": daily.to_dict(orient="records"),
            "trades_sha256": sha256_file(trades_path),
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
    audit_path.write_bytes(
        (json.dumps(audit, allow_nan=False, indent=2, sort_keys=True) + "\n").encode()
    )
    print(json.dumps(audit, allow_nan=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
