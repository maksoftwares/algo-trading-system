from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import time
from typing import Any

import pandas as pd


ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]
sys.path.insert(0, str(ROOT / "src"))

from pullback import (  # noqa: E402
    adjusted_stage_audit,
    build_features,
    canonical_hash,
    generate_candidates,
    load_config,
    load_locked_v24,
    resample_quotes,
    sha256_file,
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
        raise ValueError("V49 contract self-hash mismatch")
    for section in ("package_files", "calibration_files"):
        for record in contract[section]:
            candidate = REPO / record["path"]
            if sha256_file(candidate) != record["sha256"]:
                raise ValueError(f"V49 locked file changed: {record['path']}")
    return contract


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


def verify_stage(
    path: Path, trades_path: Path, contract: dict[str, Any]
) -> dict[str, Any]:
    audit = json.loads(path.read_text(encoding="utf-8"))
    if canonical_hash(audit, "audit_sha256") != audit["audit_sha256"]:
        raise ValueError(f"V49 stage self-hash mismatch: {path}")
    if audit["contract_sha256"] != contract["contract_sha256"]:
        raise ValueError(f"V49 stage contract mismatch: {path}")
    if sha256_file(trades_path) != audit["trades_sha256"]:
        raise ValueError(f"V49 stage trades changed: {trades_path}")
    return audit


def run_once() -> int:
    config = load_config(ROOT)
    contract = verify_contract(config)
    v24 = load_locked_v24(config)
    boundary = pd.Timestamp(config["forward"]["start_inclusive_utc"])
    paths = [
        path
        for path in v24.discover_source_files(config)
        if v24.source_date(path) >= boundary
    ]
    ticks, source_audit, raw_daily = v24.load_ticks(paths, config)
    full_days = v24.assess_full_days(ticks, raw_daily, config)
    eligible_dates = (
        full_days.loc[full_days["eligible_full_weekday"], "date_utc"].tolist()
        if not full_days.empty
        else []
    )
    quote_columns = ["tick_time_msc", "bid", "ask", "spread_price"]
    bars = (
        resample_quotes(ticks[quote_columns], config)
        if not ticks.empty
        else resample_quotes(ticks, config)
    )
    features = (
        pd.concat(
            [build_features(group, config) for _, group in bars.groupby("date_utc")],
            ignore_index=True,
        )
        if not bars.empty
        else bars
    )
    candidates = generate_candidates(features, contract["selected_policy"], config)
    candidates = candidates.loc[
        candidates["date_utc"].isin(eligible_dates)
    ].reset_index(drop=True)
    output = ROOT / config["outputs"]["directory"]
    inventory = {
        "schema_version": "xauusd_v49_forward_inventory",
        "contract_sha256": contract["contract_sha256"],
        "calibration_audit_sha256": contract["calibration_audit_sha256"],
        "source_audit": source_audit,
        "full_day_quality": full_days.to_dict(orient="records"),
        "eligible_full_weekdays": eligible_dates,
        "eligible_full_weekday_count": len(eligible_dates),
        "candidate_count_all_loaded_forward_data": int(len(candidates)),
        "economic_outcomes_opened_by_inventory": False,
    }
    inventory["inventory_sha256"] = canonical_hash(inventory, "inventory_sha256")
    write_json(output / config["outputs"]["forward_inventory"], inventory)

    validation_count = int(config["forward"]["validation_full_weekdays"])
    confirmation_count = int(config["forward"]["confirmation_full_weekdays"])
    validation_dates = eligible_dates[:validation_count]
    confirmation_dates = eligible_dates[
        validation_count : validation_count + confirmation_count
    ]
    validation_path = ROOT / config["forward"]["validation_audit"]
    confirmation_path = ROOT / config["forward"]["confirmation_audit"]
    validation_trades_path = output / config["outputs"]["validation_trades"]
    confirmation_trades_path = output / config["outputs"]["confirmation_trades"]

    if validation_path.exists():
        validation = verify_stage(validation_path, validation_trades_path, contract)
    elif len(validation_dates) < validation_count:
        print(
            json.dumps(
                {
                    "decision": "V49_CONTINUE_SEALED_FORWARD_COLLECTION",
                    "eligible_full_weekdays": len(eligible_dates),
                    "required_for_validation": validation_count,
                    "economic_outcomes_opened": False,
                },
                indent=2,
            )
        )
        return 0
    else:
        trades = v24.simulate_trades(
            ticks, candidates, validation_dates, "FORWARD_VALIDATION", config
        )
        validation, _ = adjusted_stage_audit(
            trades, validation_dates, "FORWARD_VALIDATION", config, v24
        )
        validation["decision"] = (
            "V49_FORWARD_VALIDATION_PASS_CONFIRMATION_REMAINS_SEALED"
            if validation["gate_passed"]
            else "V49_FORWARD_VALIDATION_FAIL_TERMINAL"
        )
        quality = full_days.loc[full_days["date_utc"].isin(validation_dates)]
        persist_stage(
            trades,
            validation,
            validation_path,
            validation_trades_path,
            contract,
            quality,
        )
        print(json.dumps(validation, indent=2, sort_keys=True))
        return 0

    if not validation["gate_passed"]:
        print(json.dumps(validation, indent=2, sort_keys=True))
        return 0
    if confirmation_path.exists():
        print(
            json.dumps(
                verify_stage(confirmation_path, confirmation_trades_path, contract),
                indent=2,
                sort_keys=True,
            )
        )
        return 0
    if len(confirmation_dates) < confirmation_count:
        print(
            json.dumps(
                {
                    "decision": "V49_VALIDATION_PASS_CONTINUE_SEALED_CONFIRMATION",
                    "confirmation_full_weekdays": len(confirmation_dates),
                    "required_for_confirmation": confirmation_count,
                    "economic_outcomes_opened": False,
                },
                indent=2,
            )
        )
        return 0
    trades = v24.simulate_trades(
        ticks, candidates, confirmation_dates, "FORWARD_CONFIRMATION", config
    )
    confirmation, _ = adjusted_stage_audit(
        trades, confirmation_dates, "FORWARD_CONFIRMATION", config, v24
    )
    confirmation["decision"] = (
        "V49_FORWARD_CONFIRMATION_PASS_RESEARCH_SHADOW_NOMINATION_ONLY"
        if confirmation["gate_passed"]
        else "V49_FORWARD_CONFIRMATION_FAIL_TERMINAL"
    )
    quality = full_days.loc[full_days["date_utc"].isin(confirmation_dates)]
    persist_stage(
        trades,
        confirmation,
        confirmation_path,
        confirmation_trades_path,
        contract,
        quality,
    )
    print(json.dumps(confirmation, indent=2, sort_keys=True))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--watch", action="store_true")
    parser.add_argument("--poll-seconds", type=int, default=300)
    args = parser.parse_args()
    if args.poll_seconds < 30:
        raise ValueError("V49 poll interval must be at least 30 seconds")
    while True:
        run_once()
        if not args.watch:
            return 0
        time.sleep(args.poll_seconds)


if __name__ == "__main__":
    raise SystemExit(main())
