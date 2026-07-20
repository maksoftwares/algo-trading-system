from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
BASE_SRC = ROOT.parent / "comex-size-segment-flow-v32" / "src"
for source in (SRC, BASE_SRC):
    if str(source) not in sys.path:
        sys.path.insert(0, str(source))

import size_segment_flow as base  # noqa: E402
from v33 import (  # noqa: E402
    generate_candidates,
    load_config,
    policy_grid,
    select_policy,
    summarize_candidate_facts,
)


CONFIG = ROOT / "config" / "comex_size_segment_flow_v33.json"
OUTPUTS = ROOT / "outputs"
AUDIT = OUTPUTS / "COMEX_SIZE_SEGMENT_V33_CALIBRATION_AUDIT.json"
CANDIDATES = OUTPUTS / "COMEX_SIZE_SEGMENT_V33_CALIBRATION_CANDIDATES.csv"


def _digest(payload: dict[str, object]) -> str:
    clean = {key: value for key, value in payload.items() if key != "audit_sha256"}
    encoded = json.dumps(clean, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def main() -> None:
    if AUDIT.exists() or CANDIDATES.exists():
        raise RuntimeError(
            "V33 calibration outputs already exist; rerun is prohibited."
        )
    config = load_config(CONFIG)
    overlay = config["v33_overlay"]
    v32_audit_path = (ROOT / overlay["v32_calibration_audit"]).resolve()
    v32_audit = json.loads(v32_audit_path.read_text(encoding="utf-8"))
    if v32_audit.get("audit_sha256") != overlay["v32_calibration_payload_sha256"]:
        raise RuntimeError(
            "V32 frequency-only evidence does not match the V33 preregistration."
        )
    if v32_audit.get("economic_outcomes_opened") is not False:
        raise RuntimeError("V32 unexpectedly opened economic outcomes.")

    manifest = Path(config["source"]["download_manifest"])
    if (
        base.sha256_file(manifest).lower()
        != str(config["source"]["download_manifest_sha256"]).lower()
    ):
        raise RuntimeError("COMEX download manifest hash mismatch.")
    start = pd.Timestamp(config["calibration"]["start"])
    end = pd.Timestamp(config["calibration"]["end"])
    files = base.discover_source_files(
        Path(config["source"]["job_directory"]), start=start, end=end
    )
    rule = config["candidate_rule"]
    sizes = sorted(
        set(int(value) for value in config["calibration"]["large_trade_size_grid"])
    )
    bars_by_size: dict[int, list[pd.DataFrame]] = {size: [] for size in sizes}
    quality_rows: list[dict[str, object]] = []
    source_rows: list[dict[str, object]] = []
    raw_trades = 0
    for path in files:
        raw = base.load_dbn_trades(path)
        session = base.session_trades(raw, rule)
        quality = base.session_quality(session, rule)
        quality["source_file"] = path.name
        quality_rows.append(quality)
        source_rows.append(
            {
                "path": str(path),
                "bytes": path.stat().st_size,
                "sha256": base.sha256_file(path),
            }
        )
        raw_trades += len(raw)
        if quality["eligible_full_weekday"]:
            for size in sizes:
                bars_by_size[size].append(
                    base.build_bar_features(session, large_trade_size=size, rule=rule)
                )

    eligible_dates = [
        str(row["date_utc"]) for row in quality_rows if row["eligible_full_weekday"]
    ]
    bars_cache = {
        size: pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
        for size, frames in bars_by_size.items()
    }
    rows: list[dict[str, object]] = []
    candidate_cache: dict[str, pd.DataFrame] = {}
    for policy in policy_grid(config):
        candidates = generate_candidates(
            bars_cache[int(policy["large_trade_size"])], policy=policy, rule=rule
        )
        facts = summarize_candidate_facts(
            candidates,
            eligible_dates=eligible_dates,
            policy=policy,
            selection=config["selection"],
        )
        rows.append(facts)
        candidate_cache[str(facts["policy_id"])] = candidates
    selected = select_policy(rows, config["selection"])
    decision = (
        "V33_CALIBRATION_PASS_READY_TO_LOCK"
        if selected is not None
        else "V33_CALIBRATION_FREQUENCY_STRUCTURE_FAIL"
    )
    selected_candidates = (
        candidate_cache[str(selected["policy_id"])]
        if selected is not None
        else pd.DataFrame()
    )
    OUTPUTS.mkdir(parents=True, exist_ok=True)
    selected_candidates.to_csv(CANDIDATES, index=False)
    payload: dict[str, object] = {
        "schema_version": "xauusd_comex_size_segment_v33_calibration_audit",
        "campaign_id": config["campaign_id"],
        "decision": decision,
        "v32_calibration_payload_sha256": v32_audit["audit_sha256"],
        "raw_trade_rows": raw_trades,
        "source_files": source_rows,
        "session_quality": quality_rows,
        "eligible_full_weekdays": len(eligible_dates),
        "eligible_dates": eligible_dates,
        "registered_grid_policies": len(rows),
        "grid_results": rows,
        "selected_policy": selected,
        "selected_candidate_rows": len(selected_candidates),
        "selected_candidates_sha256": base.sha256_file(CANDIDATES),
        "economic_outcomes_opened": False,
        "future_spot_prices_opened": False,
        "labels_opened": False,
        "pnl_opened": False,
        "broker_action_authorized": False,
    }
    payload["audit_sha256"] = _digest(payload)
    AUDIT.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps({"decision": decision, "selected_policy": selected}, indent=2))


if __name__ == "__main__":
    main()
