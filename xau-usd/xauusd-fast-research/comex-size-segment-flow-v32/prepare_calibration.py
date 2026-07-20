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

from size_segment_flow import (  # noqa: E402
    build_bar_features,
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


CONFIG = ROOT / "config" / "comex_size_segment_flow_v32.json"
OUTPUTS = ROOT / "outputs"
AUDIT = OUTPUTS / "COMEX_SIZE_SEGMENT_V32_CALIBRATION_AUDIT.json"
CANDIDATES = OUTPUTS / "COMEX_SIZE_SEGMENT_V32_CALIBRATION_CANDIDATES.csv"


def _audit_digest(payload: dict[str, object]) -> str:
    clean = {key: value for key, value in payload.items() if key != "audit_sha256"}
    encoded = json.dumps(clean, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def main() -> None:
    if AUDIT.exists() or CANDIDATES.exists():
        raise RuntimeError(
            "Calibration outputs already exist; delete-by-tuning is prohibited."
        )
    config = load_config(CONFIG)
    manifest = Path(config["source"]["download_manifest"])
    expected_manifest = str(config["source"]["download_manifest_sha256"]).lower()
    observed_manifest = sha256_file(manifest)
    if observed_manifest.lower() != expected_manifest:
        raise RuntimeError(
            "The acquired COMEX download manifest hash does not match the contract."
        )

    start = pd.Timestamp(config["calibration"]["start"])
    end = pd.Timestamp(config["calibration"]["end"])
    files = discover_source_files(
        Path(config["source"]["job_directory"]), start=start, end=end
    )
    rules = config["candidate_rule"]
    sizes = sorted(
        set(int(value) for value in config["calibration"]["large_trade_size_grid"])
    )
    bars_by_size: dict[int, list[pd.DataFrame]] = {size: [] for size in sizes}
    quality_rows: list[dict[str, object]] = []
    source_rows: list[dict[str, object]] = []
    raw_trades = 0
    for path in files:
        raw = load_dbn_trades(path)
        session = session_trades(raw, rules)
        quality = session_quality(session, rules)
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
        if not quality["eligible_full_weekday"]:
            continue
        for size in sizes:
            bars_by_size[size].append(
                build_bar_features(session, large_trade_size=size, rule=rules)
            )

    eligible_dates = [
        str(row["date_utc"]) for row in quality_rows if row["eligible_full_weekday"]
    ]
    grid_rows: list[dict[str, object]] = []
    cached_candidates: dict[str, pd.DataFrame] = {}
    for policy in policy_grid(config):
        size = int(policy["large_trade_size"])
        frames = bars_by_size[size]
        bars = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
        candidates = generate_candidates(bars, policy=policy, rule=rules)
        facts = summarize_candidate_facts(
            candidates,
            eligible_dates=eligible_dates,
            policy=policy,
            selection=config["selection"],
        )
        grid_rows.append(facts)
        cached_candidates[str(facts["policy_id"])] = candidates

    selected = select_policy(grid_rows, config["selection"])
    decision = (
        "V32_CALIBRATION_PASS_READY_TO_LOCK"
        if selected is not None
        else "V32_CALIBRATION_FREQUENCY_STRUCTURE_FAIL"
    )
    selected_candidates = (
        cached_candidates[str(selected["policy_id"])]
        if selected is not None
        else pd.DataFrame()
    )
    OUTPUTS.mkdir(parents=True, exist_ok=True)
    selected_candidates.to_csv(CANDIDATES, index=False)
    payload: dict[str, object] = {
        "schema_version": "xauusd_comex_size_segment_v32_calibration_audit",
        "campaign_id": config["campaign_id"],
        "decision": decision,
        "calibration_start": config["calibration"]["start"],
        "calibration_end": config["calibration"]["end"],
        "raw_trade_rows": raw_trades,
        "source_files": source_rows,
        "session_quality": quality_rows,
        "eligible_full_weekdays": len(eligible_dates),
        "eligible_dates": eligible_dates,
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
    payload["audit_sha256"] = _audit_digest(payload)
    AUDIT.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps({"decision": decision, "selected_policy": selected}, indent=2))


if __name__ == "__main__":
    main()
