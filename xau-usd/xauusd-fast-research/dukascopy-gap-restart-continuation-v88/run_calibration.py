from __future__ import annotations

import json
import os
from pathlib import Path
import sys
from typing import Any, Mapping

import pandas as pd


ROOT = Path(__file__).resolve().parent
V72_SRC = ROOT.parent / "xag-xau-eventtime-catchup-v72" / "src"
for source in (ROOT / "src", V72_SRC):
    sys.path.insert(0, str(source))

from catchup import (  # noqa: E402
    ManifestTickStore,
    canonical_hash,
    load_json,
    sha256_file,
)
from gap_restart_adapter import (  # noqa: E402
    generate_candidates,
    session_quality,
    summarize_candidate_facts,
)


CONFIG = ROOT / "config" / "dukascopy_gap_restart_continuation_v88.json"


def load_day(
    date: pd.Timestamp,
    *,
    store: ManifestTickStore,
    rule: Mapping[str, Any],
    execution: Mapping[str, Any] | None = None,
) -> pd.DataFrame:
    start_hour = int(str(rule["session_start_utc"]).split(":")[0])
    end_hour = int(str(rule["session_end_utc"]).split(":")[0])
    start_ms = int(
        (date.normalize() + pd.Timedelta(hours=start_hour)).timestamp() * 1000
    )
    end_ms = (
        int((date.normalize() + pd.Timedelta(hours=end_hour)).timestamp() * 1000)
        - 1
    )
    if execution is not None:
        end_ms += (
            int(execution["maximum_entry_delay_ms"])
            + int(execution["hold_seconds"]) * 1000
            + int(execution["maximum_exit_delay_ms"])
        )
    return store.quote_frame(start_ms, end_ms)


def run_calibration() -> dict[str, Any]:
    config = load_json(CONFIG)
    output = ROOT / str(config["outputs"]["directory"])
    candidate_path = output / str(config["outputs"]["calibration_candidates"])
    audit_path = output / str(config["outputs"]["calibration_audit"])
    if candidate_path.exists() or audit_path.exists():
        raise FileExistsError("V88 calibration outputs already exist")
    if (output / str(config["outputs"]["contract_lock"])).exists():
        raise RuntimeError("V88 calibration cannot run after lock")
    source_path = output / str(config["outputs"]["calibration_source_audit"])
    source_audit = load_json(source_path)
    if (
        source_audit.get("decision") != "V88_CALIBRATION_SOURCE_AUDIT_PASS"
        or canonical_hash(source_audit, "audit_sha256")
        != source_audit.get("audit_sha256")
    ):
        raise ValueError("V88 calibration source audit is invalid")
    source = config["source"]
    storage = Path(
        os.environ.get(
            str(source["storage_environment_variable"]),
            str(source["default_storage_root"]),
        )
    ).resolve()
    store = ManifestTickStore(storage, "XAUUSD", source["symbols"]["XAUUSD"])
    calibration = config["calibration"]
    start, end = pd.Timestamp(calibration["start"]), pd.Timestamp(calibration["end"])
    rule = config["candidate_rule"]
    candidate_frames: list[pd.DataFrame] = []
    quality_rows: list[dict[str, Any]] = []
    restart_episodes = 0
    raw_candidates = 0
    for date in pd.date_range(
        start.normalize(), end.normalize(), inclusive="left", freq="D"
    ):
        if date.weekday() >= 5:
            continue
        quotes = load_day(date, store=store, rule=rule)
        quality = session_quality(date, quotes, rule)
        quality_rows.append(quality)
        if bool(quality["eligible_full_weekday"]):
            candidates, structural = generate_candidates(date, quotes, rule=rule)
            restart_episodes += int(structural["restart_episode_count"])
            raw_candidates += int(structural["raw_candidate_count"])
            if not candidates.empty:
                candidate_frames.append(candidates)
        print(f"V88 calibrated {date.date()}", flush=True)
    candidates = (
        pd.concat(candidate_frames, ignore_index=True)
        if candidate_frames
        else pd.DataFrame()
    )
    eligible_dates = [
        row["date_utc"] for row in quality_rows if bool(row["eligible_full_weekday"])
    ]
    facts = summarize_candidate_facts(
        candidates,
        eligible_dates=eligible_dates,
        calibration=calibration,
    )
    output.mkdir(parents=True, exist_ok=True)
    candidates.to_parquet(candidate_path, index=False)
    decision = (
        "V88_CALIBRATION_RULE_ACCEPTED"
        if bool(facts["density_gate_passed"])
        else "V88_CALIBRATION_DENSITY_FAIL_TERMINAL"
    )
    audit: dict[str, Any] = {
        "schema_version": "xauusd_dukascopy_gap_restart_continuation_v88_calibration_audit",
        "campaign_id": config["campaign_id"],
        "decision": decision,
        "calibration_start": str(start),
        "calibration_end_exclusive": str(end),
        "source_audit_sha256": sha256_file(source_path),
        "session_quality": quality_rows,
        "fixed_rule": rule,
        "restart_episode_count": restart_episodes,
        "raw_candidate_count": raw_candidates,
        **facts,
        "candidate_sha256": sha256_file(candidate_path),
        "post_candidate_prices_used_for_label_or_outcome": False,
        **config["research_controls"],
    }
    audit["audit_sha256"] = canonical_hash(audit, "audit_sha256")
    audit_path.write_bytes((json.dumps(audit, indent=2, sort_keys=True) + "\n").encode())
    print(json.dumps({"decision": decision, **facts}, indent=2))
    return audit


if __name__ == "__main__":
    run_calibration()
