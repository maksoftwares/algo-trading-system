from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

import pandas as pd

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from src.research import (
    _load_v1_module,
    _quarantine_filter,
    _write_csv,
    add_h4_regimes,
    measure,
    sealed_row,
)
from run_v2r_sequential import session_mask


def main() -> None:
    base = json.loads(
        (ROOT / "config" / "eurusd_regime_specialists_v2.json").read_text(encoding="utf-8")
    )
    classifier = json.loads(
        (ROOT / "config" / "eurusd_regime_specialists_v2r_train_hunt.json").read_text(encoding="utf-8")
    )["classifier"]
    frozen_path = ROOT / "config" / "eurusd_v3_frozen_candidate.json"
    frozen_bytes = frozen_path.read_bytes()
    frozen = json.loads(frozen_bytes)
    specialist = frozen["candidate"]
    storage = Path(base["source"]["storage_root"])
    cache = storage / base["source"]["h1_cache"]
    metadata = json.loads((storage / base["source"]["h1_cache_metadata"]).read_text(encoding="utf-8"))
    if hashlib.sha256(cache.read_bytes()).hexdigest() != metadata["cache_sha256"]:
        raise RuntimeError("H1 cache checksum mismatch")
    frame = pd.read_csv(cache, compression="gzip", parse_dates=["timestamp"])
    frame["timestamp"] = pd.to_datetime(frame["timestamp"], utc=True)
    frame, _ = add_h4_regimes(frame, classifier)
    module = _load_v1_module(ROOT)
    featured = module.add_features(frame, base)
    candidate = module.Candidate(
        candidate_id=specialist["specialist_id"],
        attempt=7001,
        archetype="session_expansion_short",
        direction=specialist["direction"],
        threshold=specialist["buffer_atr"],
        stop_atr=specialist["stop_atr"],
        target_r=specialist["target_r"],
        max_hold_bars=specialist["max_hold_bars"],
        sha256=specialist["parameter_sha256"],
    )
    mask = session_mask(featured, specialist).to_numpy()
    rows = []
    trades_out = []
    still_open = True
    for stage in ("internal", "exam"):
        if not still_open:
            rows.append(sealed_row(specialist, stage))
            continue
        start, end = (pd.Timestamp(value) for value in base["windows"][stage])
        trades = module.simulate(featured, candidate, mask, start, end, base)
        trades = _quarantine_filter(trades, base["source"]["quarantined_utc_intervals"])
        row = measure(trades, specialist, stage, frozen["gates"][stage])
        rows.append(row)
        trades_out.extend({**trade, "stage": stage} for trade in trades)
        still_open = bool(row["gate_pass"])
    output = ROOT / "outputs" / "v3_sequential"
    output.mkdir(parents=True, exist_ok=True)
    _write_csv(output / "STAGE_METRICS.csv", rows)
    _write_csv(output / "TRADES.csv", trades_out)
    result = {
        "campaign_id": frozen["campaign_id"],
        "frozen_candidate_sha256": hashlib.sha256(frozen_bytes).hexdigest(),
        "internal_pass": bool(rows[0]["gate_pass"]),
        "exam_opened": rows[1]["status"] == "OPENED",
        "exam_pass": bool(rows[1]["gate_pass"]),
        "exact_m5_replication_required": still_open,
        "demo_rehearsal_ready": False,
        "verdict": "QUALIFIER_REQUIRES_EXACT_REPLICATION" if still_open else "NO_V3_QUALIFIER_STOP",
    }
    (output / "VERDICT.json").write_text(
        json.dumps(result, indent=2) + "\n", encoding="utf-8", newline="\n"
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
