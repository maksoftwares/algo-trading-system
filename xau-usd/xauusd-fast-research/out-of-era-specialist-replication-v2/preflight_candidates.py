from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from src.contract import OUTCOME_MARKER_PATH, load_config, storage_root
from src import replication


ROOT = Path(__file__).resolve().parent


def main() -> int:
    if OUTCOME_MARKER_PATH.exists():
        raise RuntimeError("Candidate preflight is unavailable after outcomes open")
    config = load_config()
    root = storage_root(config)
    replay_root = root / config["source"]["replay_root"]
    status = json.loads((replay_root / "status.json").read_text(encoding="utf-8"))
    months = [str(value) for value in status.get("normalized_months", [])]
    if not months:
        raise ValueError("No normalized month is ready for candidate preflight")
    m5 = replication.load_side_specific_m5(replay_root, months)
    public_root = root / config["source"]["public_input_root"]
    calendar = pd.read_csv(
        public_root / "OFFICIAL_FOMC_CALENDAR_2010_2016.csv",
        parse_dates=["event_time_utc"],
    )
    calendar = calendar.loc[
        calendar["event_time_utc"].ge(m5["bar_start_utc"].min())
        & calendar["event_time_utc"].lt(m5["bar_end_utc"].max())
    ].copy()
    event_candidates = [
        item
        for item in config["candidates"]
        if item["engine"] == "CORRECTED_RAW_TICK_EVENT"
    ]
    base_regime = replication.load_json(
        (ROOT / config["base_regime_config"]).resolve()
    )
    ledgers = {}
    manifests = {}
    for event_candidate in event_candidates:
        candidate_id = str(event_candidate["candidate_id"])
        candidates, manifest = replication.build_fomc_regime_candidates(
            m5, calendar, event_candidate, base_regime
        )
        ledgers[candidate_id] = candidates
        manifests[candidate_id] = manifest
    payload = {
        "schema_version": "xauusd_out_of_era_candidate_preflight_v2",
        "normalized_months": len(months),
        "first_month": months[0],
        "last_month": months[-1],
        "m5_rows": int(len(m5)),
        "candidate_columns": {
            candidate_id: list(frame.columns)
            for candidate_id, frame in ledgers.items()
        },
        "manifests": manifests,
        "contains_outcomes": False,
        "strategy_scoring_performed": False,
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
