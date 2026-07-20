from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from sequence_ignition import (  # noqa: E402
    build_sequence_features,
    discover_source_files,
    generate_candidates,
    load_config,
    load_dbn_trades,
    policy_grid,
    select_policy,
    session_quality,
    session_trades,
    sha256_file,
    summarize_candidate_facts,
)


CONFIG = ROOT / "config" / "comex_sequence_ignition_v45.json"
OUTPUTS = ROOT / "outputs"
AUDIT = OUTPUTS / "COMEX_SEQUENCE_IGNITION_V45_CALIBRATION_AUDIT.json"
CANDIDATES = OUTPUTS / "COMEX_SEQUENCE_IGNITION_V45_CALIBRATION_CANDIDATES.csv"


def _digest(payload: dict[str, object]) -> str:
    clean = {key: value for key, value in payload.items() if key != "audit_sha256"}
    return hashlib.sha256(
        json.dumps(clean, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def main() -> None:
    if AUDIT.exists() or CANDIDATES.exists():
        raise RuntimeError(
            "V45 calibration outputs already exist; rerun is prohibited."
        )
    config = load_config(CONFIG)
    manifest = Path(config["source"]["download_manifest"])
    if (
        sha256_file(manifest).lower()
        != str(config["source"]["download_manifest_sha256"]).lower()
    ):
        raise RuntimeError("The COMEX download manifest hash does not match V45.")
    start = pd.Timestamp(config["calibration"]["start"])
    end = pd.Timestamp(config["calibration"]["end"])
    files = discover_source_files(
        Path(config["source"]["job_directory"]), start=start, end=end
    )
    rule = config["candidate_rule"]
    feature_frames: list[pd.DataFrame] = []
    quality_rows: list[dict[str, object]] = []
    source_rows: list[dict[str, object]] = []
    raw_trades = 0
    for number, path in enumerate(files, start=1):
        raw = load_dbn_trades(path)
        session = session_trades(raw, rule)
        quality = session_quality(session, rule)
        quality["source_file"] = path.name
        quality_rows.append(quality)
        source_rows.append(
            {
                "path": str(path),
                "bytes": path.stat().st_size,
                "sha256": sha256_file(path),
            }
        )
        raw_trades += len(raw)
        if quality["eligible_full_weekday"]:
            feature_frames.append(build_sequence_features(session, rule=rule))
        print(f"processed {number}/{len(files)} calibration files", flush=True)
    features = (
        pd.concat(feature_frames, ignore_index=True)
        if feature_frames
        else pd.DataFrame()
    )
    eligible_dates = [
        str(row["date_utc"]) for row in quality_rows if row["eligible_full_weekday"]
    ]
    policies = policy_grid(config)
    if len(policies) != 1000:
        raise RuntimeError(f"Expected exactly 1000 policies, got {len(policies)}.")
    grid_rows: list[dict[str, object]] = []
    cached_candidates: dict[str, pd.DataFrame] = {}
    for number, policy in enumerate(policies, start=1):
        candidates = generate_candidates(features, policy=policy, rule=rule)
        facts = summarize_candidate_facts(
            candidates,
            eligible_dates=eligible_dates,
            policy=policy,
            selection=config["selection"],
        )
        grid_rows.append(facts)
        cached_candidates[str(facts["policy_id"])] = candidates
        if number % 100 == 0:
            print(f"evaluated {number}/{len(policies)} density policies", flush=True)
    selected = select_policy(grid_rows, config["selection"])
    decision = (
        "V45_CALIBRATION_PASS_READY_TO_LOCK"
        if selected is not None
        else "V45_CALIBRATION_FREQUENCY_STRUCTURE_FAIL"
    )
    selected_candidates = (
        cached_candidates[str(selected["policy_id"])]
        if selected is not None
        else pd.DataFrame()
    )
    OUTPUTS.mkdir(parents=True, exist_ok=True)
    selected_candidates.to_csv(CANDIDATES, index=False)
    payload: dict[str, object] = {
        "schema_version": "xauusd_comex_sequence_ignition_v45_calibration_audit",
        "campaign_id": config["campaign_id"],
        "decision": decision,
        "calibration_start": config["calibration"]["start"],
        "calibration_end": config["calibration"]["end"],
        "raw_trade_rows": raw_trades,
        "source_files": source_rows,
        "session_quality": quality_rows,
        "eligible_full_weekdays": len(eligible_dates),
        "eligible_dates": eligible_dates,
        "feature_rows": len(features),
        "registered_grid_policies": len(grid_rows),
        "grid_results": grid_rows,
        "selected_policy": selected,
        "selected_candidate_rows": len(selected_candidates),
        "selected_candidates_sha256": sha256_file(CANDIDATES),
        "economic_outcomes_opened": False,
        "future_spot_prices_opened": False,
        "labels_opened": False,
        "pnl_opened": False,
        "model_training_authorized": False,
        "python_predictions_authorized": False,
        "ea_consumption_authorized": False,
        "broker_action_authorized": False,
    }
    payload["audit_sha256"] = _digest(payload)
    AUDIT.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps({"decision": decision, "selected_policy": selected}, indent=2))


if __name__ == "__main__":
    main()
