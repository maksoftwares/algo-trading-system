from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

import pandas as pd


ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
FOUNDATION = ROOT.parent / "comex-futures-foundation-v1" / "src"
for source in (SRC, FOUNDATION):
    if str(source) not in sys.path:
        sys.path.insert(0, str(source))

from lock_contract import verify_lock  # noqa: E402
from size_segment_flow import (  # noqa: E402
    build_bar_features,
    discover_source_files,
    generate_candidates,
    load_config,
    load_dbn_trades,
    session_quality,
    session_trades,
    sha256_file,
    summarize_stage,
)
from spot_labels import (  # noqa: E402
    VerifiedSpotTickStore,
    label_candidates,
    load_completed_atr,
    load_dukascopy_foundation,
    resolve_spot_storage,
)


CONFIG = ROOT / "config" / "comex_size_segment_flow_v32.json"
OUTPUTS = ROOT / "outputs"
STAGES = ("development", "validation", "exam")


def _digest(payload: dict[str, Any]) -> str:
    clean = {key: value for key, value in payload.items() if key != "audit_sha256"}
    encoded = json.dumps(clean, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def _paths(stage: str) -> tuple[Path, Path, Path]:
    prefix = f"COMEX_SIZE_SEGMENT_V32_{stage.upper()}"
    return (
        OUTPUTS / f"{prefix}_CANDIDATES.parquet",
        OUTPUTS / f"{prefix}_LABELS.parquet",
        OUTPUTS / f"{prefix}_AUDIT.json",
    )


def _require_firewall(stage: str) -> None:
    index = STAGES.index(stage)
    for prior in STAGES[:index]:
        _, _, audit_path = _paths(prior)
        if not audit_path.is_file():
            raise RuntimeError(f"{stage} is sealed because {prior} has not run.")
        audit = json.loads(audit_path.read_text(encoding="utf-8"))
        if audit.get("gate_passed") is not True:
            raise RuntimeError(f"{stage} is sealed because {prior} failed.")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", required=True, choices=STAGES)
    args = parser.parse_args()
    stage = str(args.stage)
    _require_firewall(stage)
    lock = verify_lock()
    candidate_path, label_path, audit_path = _paths(stage)
    if any(path.exists() for path in (candidate_path, label_path, audit_path)):
        raise RuntimeError(
            f"{stage} outputs already exist; same-stage rerun is prohibited."
        )

    config = load_config(CONFIG)
    start = pd.Timestamp(config["splits"][stage][0])
    end = pd.Timestamp(config["splits"][stage][1])
    files = discover_source_files(
        Path(config["source"]["job_directory"]), start=start, end=end
    )
    policy = lock["selected_policy"]
    rules = config["candidate_rule"]
    candidate_frames: list[pd.DataFrame] = []
    quality_rows: list[dict[str, Any]] = []
    source_rows: list[dict[str, Any]] = []
    raw_trades = 0
    for number, path in enumerate(files, start=1):
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
        if quality["eligible_full_weekday"]:
            bars = build_bar_features(
                session,
                large_trade_size=int(policy["large_trade_size"]),
                rule=rules,
            )
            candidate_frames.append(
                generate_candidates(bars, policy=policy, rule=rules)
            )
        if number % 50 == 0:
            print(f"processed {number}/{len(files)} COMEX files", flush=True)

    candidates = (
        pd.concat(candidate_frames, ignore_index=True)
        if candidate_frames
        else pd.DataFrame(
            columns=["candidate_id", "feature_time_utc", "family", "direction"]
        )
    )
    if not candidates.empty:
        candidates = candidates.sort_values(
            ["feature_time_utc", "candidate_id"], kind="stable"
        ).reset_index(drop=True)
        if candidates["candidate_id"].duplicated().any():
            raise RuntimeError("Stage candidates contain duplicate IDs.")

    foundation = load_dukascopy_foundation()
    storage = resolve_spot_storage(config)
    atr = load_completed_atr(config, storage)
    ticks = VerifiedSpotTickStore(
        storage_root=storage,
        symbol=str(config["spot_source"]["symbol"]),
        foundation=foundation,
    )
    labels = label_candidates(
        candidates, atr_source=atr, tick_store=ticks, config=config
    )
    if labels.empty:
        labels = pd.DataFrame(columns=["candidate_id", "status", "direction"])
    eligible_dates = [
        str(row["date_utc"]) for row in quality_rows if row["eligible_full_weekday"]
    ]
    result = summarize_stage(
        labels, stage=stage, eligible_dates=eligible_dates, config=config
    )
    OUTPUTS.mkdir(parents=True, exist_ok=True)
    candidates.to_parquet(candidate_path, index=False)
    labels.to_parquet(label_path, index=False)
    decision = (
        f"V32_{stage.upper()}_PASS"
        if result["gate_passed"]
        else f"V32_{stage.upper()}_FAIL_TERMINAL"
    )
    payload: dict[str, Any] = {
        "schema_version": "xauusd_comex_size_segment_v32_stage_audit",
        "campaign_id": config["campaign_id"],
        "stage": stage,
        "decision": decision,
        "contract_sha256": lock["contract_sha256"],
        "selected_policy": policy,
        "raw_trade_rows": raw_trades,
        "source_files": source_rows,
        "session_quality": quality_rows,
        "candidate_rows": len(candidates),
        "candidate_sha256": sha256_file(candidate_path),
        "label_rows": len(labels),
        "label_status_counts": {
            str(key): int(value)
            for key, value in labels["status"].value_counts().items()
        },
        "labels_sha256": sha256_file(label_path),
        **result,
        "same_version_tuning_authorized": False,
        "model_training_authorized": False,
        "python_predictions_authorized": False,
        "ea_consumption_authorized": False,
        "broker_action_authorized": False,
    }
    payload["audit_sha256"] = _digest(payload)
    audit_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps({"decision": decision, **result["metrics"]}, indent=2))


if __name__ == "__main__":
    main()
