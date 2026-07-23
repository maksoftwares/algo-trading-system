from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

import pandas as pd

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from src.research import (
    STAGE_ORDER,
    _load_v1_module,
    _quarantine_filter,
    _write_csv,
    add_h4_regimes,
    measure,
    sealed_row,
)


def session_mask(frame: pd.DataFrame, specialist: dict) -> pd.Series:
    utc_date = frame["timestamp"].dt.strftime("%Y-%m-%d")
    utc_hour = frame["timestamp"].dt.hour
    reference = utc_hour.isin(specialist["reference_hours"])
    ref_high = frame["mid_high"].where(reference).groupby(utc_date).transform("max")
    ref_low = frame["mid_low"].where(reference).groupby(utc_date).transform("min")
    decision = utc_hour.isin(specialist["decision_hours"])
    if specialist["direction"] == "long":
        raw = frame["mid_close"] > ref_high + specialist["buffer_atr"] * frame["atr"]
    else:
        raw = frame["mid_close"] < ref_low - specialist["buffer_atr"] * frame["atr"]
    raw = (
        raw
        & decision
        & (frame["body_fraction"] >= specialist["body_min"])
        & (frame["regime"] == specialist["owned_regime"])
        & frame["contiguous_next"]
    ).fillna(False)
    return raw & (raw.groupby(utc_date).cumsum() == 1)


def main() -> None:
    base = json.loads(
        (ROOT / "config" / "eurusd_regime_specialists_v2.json").read_text(encoding="utf-8")
    )
    regime_hunt = json.loads(
        (ROOT / "config" / "eurusd_regime_specialists_v2r_train_hunt.json").read_text(encoding="utf-8")
    )
    frozen_path = ROOT / "config" / "eurusd_v2r_frozen_specialists.json"
    frozen_bytes = frozen_path.read_bytes()
    frozen = json.loads(frozen_bytes)
    storage = Path(base["source"]["storage_root"])
    cache = storage / base["source"]["h1_cache"]
    metadata = json.loads((storage / base["source"]["h1_cache_metadata"]).read_text(encoding="utf-8"))
    if hashlib.sha256(cache.read_bytes()).hexdigest() != metadata["cache_sha256"]:
        raise RuntimeError("H1 cache checksum mismatch")
    frame = pd.read_csv(cache, compression="gzip", parse_dates=["timestamp"])
    frame["timestamp"] = pd.to_datetime(frame["timestamp"], utc=True)
    frame, _ = add_h4_regimes(frame, regime_hunt["classifier"])
    module = _load_v1_module(ROOT)
    featured = module.add_features(frame, base)
    metrics_rows = []
    trade_rows = []
    qualified = []
    for specialist in frozen["specialists"]:
        if specialist["family"] == "v1_compression_breakout":
            candidate = module.Candidate(
                candidate_id=specialist["specialist_id"],
                attempt=3001,
                archetype=specialist["archetype"],
                direction=specialist["direction"],
                threshold=specialist["threshold"],
                stop_atr=specialist["stop_atr"],
                target_r=specialist["target_r"],
                max_hold_bars=specialist["max_hold_bars"],
                sha256=specialist["parameter_sha256"],
            )
            mask = module.signal_mask(featured, candidate) & (
                featured["regime"] == specialist["owned_regime"]
            ).to_numpy()
        else:
            candidate = module.Candidate(
                candidate_id=specialist["specialist_id"],
                attempt=3002,
                archetype="session_expansion_short",
                direction=specialist["direction"],
                threshold=specialist["buffer_atr"],
                stop_atr=specialist["stop_atr"],
                target_r=specialist["target_r"],
                max_hold_bars=specialist["max_hold_bars"],
                sha256=specialist["parameter_sha256"],
            )
            mask = session_mask(featured, specialist).to_numpy()
        still_open = True
        for stage in STAGE_ORDER:
            if stage == "train":
                continue
            if not still_open:
                metrics_rows.append(sealed_row(specialist, stage))
                continue
            start, end = (pd.Timestamp(value) for value in base["windows"][stage])
            trades = module.simulate(featured, candidate, mask, start, end, base)
            trades = _quarantine_filter(trades, base["source"]["quarantined_utc_intervals"])
            row = measure(trades, specialist, stage, base["stage_gates"][stage])
            metrics_rows.append(row)
            trade_rows.extend({**trade, "stage": stage} for trade in trades)
            still_open = bool(row["gate_pass"])
        if still_open:
            qualified.append(specialist["specialist_id"])
    output = ROOT / "outputs" / "v2r_sequential"
    output.mkdir(parents=True, exist_ok=True)
    _write_csv(output / "STAGE_METRICS.csv", metrics_rows)
    _write_csv(output / "TRADES.csv", trade_rows)
    result = {
        "campaign_id": frozen["campaign_id"],
        "frozen_specialist_sha256": hashlib.sha256(frozen_bytes).hexdigest(),
        "qualified_specialists": qualified,
        "exact_m5_replication_required": bool(qualified),
        "mt5_replication_required": bool(qualified),
        "demo_rehearsal_ready": False,
        "verdict": (
            "QUALIFIER_REQUIRES_EXACT_REPLICATION"
            if qualified
            else "NO_SEQUENTIAL_QUALIFIER_STOP"
        ),
    }
    (output / "VERDICT.json").write_text(
        json.dumps(result, indent=2) + "\n", encoding="utf-8", newline="\n"
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
