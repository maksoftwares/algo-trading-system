from __future__ import annotations

from datetime import UTC, datetime
import hashlib
import json
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parents[2]
RESULT = ROOT / "outputs" / "RESULT.json"
EVENTS = (
    REPO_ROOT
    / "xau-usd"
    / "xauusd-fast-research"
    / "codex-v60-tick-runtime-replay-v1"
    / "outputs"
    / "current-deployed-benchmark-20260825"
    / "EVENTS.csv"
)
OUTPUT = ROOT / "outputs" / "PROSPECTIVE_WARM_START.json"


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    result = json.loads(RESULT.read_text(encoding="utf-8"))
    if result["decision"] != "HISTORICAL_CHALLENGER_PASSES_PROSPECTIVE_CONFIRMATION_REQUIRED":
        raise ValueError("V2 must pass every historical gate before warm-start creation")
    vetoed = {str(row["trade_id"]) for row in result["veto_audit"]}
    events = pd.read_csv(EVENTS)
    closed = events.loc[
        events["scenario_id"].eq("deployed__full_runtime")
        & events["event"].eq("POSITION_CLOSED"),
        ["trade_id", "source_id", "timestamp_utc", "pnl_usd"],
    ].copy()
    if closed["trade_id"].duplicated().any():
        raise ValueError("Deployed replay has duplicate closed trade IDs")
    retained = closed.loc[~closed["trade_id"].astype(str).isin(vetoed)].copy()
    retained["closed_at_utc"] = pd.to_datetime(
        retained.pop("timestamp_utc"), utc=True, format="mixed"
    )
    retained = retained.sort_values(["source_id", "closed_at_utc", "trade_id"])
    rows = []
    source_counts = {}
    for source_id, group in retained.groupby("source_id", sort=True):
        source_counts[str(source_id)] = int(len(group))
        for row in group.tail(50).itertuples(index=False):
            rows.append(
                {
                    "candidate_id": f"replay:{row.trade_id}",
                    "trade_id": str(row.trade_id),
                    "source_id": str(row.source_id),
                    "closed_at_utc": row.closed_at_utc.isoformat().replace("+00:00", "Z"),
                    "pnl_usd": float(row.pnl_usd),
                }
            )
    payload = {
        "schema_version": "v60_mature_source_health_rank_veto_v2_warm_start",
        "generated_at_utc": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "source_cutoff_exclusive_utc": "2026-07-01T00:00:00Z",
        "maximum_rows_per_source": 50,
        "policy": result["policy"],
        "input_sha256": {
            "historical_result": sha256_file(RESULT),
            "deployed_replay_events": sha256_file(EVENTS),
        },
        "retained_history_counts_by_source": source_counts,
        "rows": sorted(rows, key=lambda row: (row["closed_at_utc"], row["candidate_id"])),
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(OUTPUT), "rows": len(rows)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
