from __future__ import annotations

import hashlib
from itertools import product
import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from src.research import _load_v1_module, add_h4_regimes, measure


def main() -> None:
    base = json.loads(
        (ROOT / "config" / "eurusd_regime_specialists_v2.json").read_text(encoding="utf-8")
    )
    regime_hunt = json.loads(
        (ROOT / "config" / "eurusd_regime_specialists_v2r_train_hunt.json").read_text(encoding="utf-8")
    )
    hunt = json.loads(
        (ROOT / "config" / "eurusd_session_expansion_v2r_train_hunt.json").read_text(encoding="utf-8")
    )
    storage = Path(base["source"]["storage_root"])
    cache = storage / base["source"]["h1_cache"]
    metadata = json.loads((storage / base["source"]["h1_cache_metadata"]).read_text(encoding="utf-8"))
    if hashlib.sha256(cache.read_bytes()).hexdigest() != metadata["cache_sha256"]:
        raise RuntimeError("H1 cache checksum mismatch")
    start, end = (pd.Timestamp(value) for value in hunt["train_window"])
    frame = pd.read_csv(cache, compression="gzip", parse_dates=["timestamp"])
    frame["timestamp"] = pd.to_datetime(frame["timestamp"], utc=True)
    frame = frame[frame["timestamp"] < end].copy()
    frame, _ = add_h4_regimes(frame, regime_hunt["classifier"])
    module = _load_v1_module(ROOT)
    featured = module.add_features(frame, base)
    featured["utc_date"] = featured["timestamp"].dt.strftime("%Y-%m-%d")
    featured["utc_hour"] = featured["timestamp"].dt.hour

    profile_fields = {}
    for profile in hunt["profiles"]:
        ref = featured["utc_hour"].isin(profile["reference_hours"])
        ref_high = featured["mid_high"].where(ref).groupby(featured["utc_date"]).transform("max")
        ref_low = featured["mid_low"].where(ref).groupby(featured["utc_date"]).transform("min")
        profile_fields[profile["profile"]] = {
            "high": ref_high,
            "low": ref_low,
            "decision": featured["utc_hour"].isin(profile["decision_hours"]),
        }

    rows = []
    attempt = 0
    directions = ("long", "short")
    combinations = product(
        hunt["profiles"],
        directions,
        hunt["buffers_atr"],
        hunt["minimum_body_fractions"],
        hunt["stop_atr_values"],
        hunt["target_r_values"],
    )
    for profile, direction, buffer_atr, body_min, stop_atr, target_r in combinations:
        for regime in hunt["regime_ownership"][direction]:
            attempt += 1
            candidate_id = f"EURSESSIONV2R_{attempt:04d}"
            payload = {
                "profile": profile["profile"],
                "direction": direction,
                "buffer_atr": buffer_atr,
                "body_min": body_min,
                "stop_atr": stop_atr,
                "target_r": target_r,
                "regime": regime,
                "maximum_hold_bars": hunt["maximum_hold_bars"],
            }
            parameter_sha = hashlib.sha256(
                json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
            ).hexdigest()
            candidate = module.Candidate(
                candidate_id=candidate_id,
                attempt=2000 + attempt,
                archetype=f"session_expansion_{direction}",
                direction=direction,
                threshold=float(buffer_atr),
                stop_atr=float(stop_atr),
                target_r=float(target_r),
                max_hold_bars=int(hunt["maximum_hold_bars"]),
                sha256=parameter_sha,
            )
            fields = profile_fields[profile["profile"]]
            if direction == "long":
                raw = featured["mid_close"] > fields["high"] + float(buffer_atr) * featured["atr"]
            else:
                raw = featured["mid_close"] < fields["low"] - float(buffer_atr) * featured["atr"]
            raw = (
                raw
                & fields["decision"]
                & (featured["body_fraction"] >= float(body_min))
                & (featured["regime"] == regime)
                & featured["contiguous_next"]
            ).fillna(False)
            first = raw & (raw.groupby(featured["utc_date"]).cumsum() == 1)
            trades = module.simulate(featured, candidate, first.to_numpy(), start, end, base)
            specialist = {
                "specialist_id": candidate_id,
                "owned_regime": regime,
                "source_candidate": candidate_id,
            }
            row = measure(trades, specialist, "train", hunt["selection_gate"])
            row.update(payload)
            row["parameter_sha256"] = parameter_sha
            rows.append(row)
        if attempt % 108 == 0:
            print(f"evaluated {attempt}/864")

    output = ROOT / "outputs" / "session_v2r_train_hunt"
    output.mkdir(parents=True, exist_ok=True)
    data = pd.DataFrame(rows)
    data.to_csv(output / "TRAIN_CANDIDATE_METRICS.csv", index=False, lineterminator="\n")
    selections = []
    for (profile, direction, regime), group in data.groupby(["profile", "direction", "owned_regime"]):
        eligible = group[group["gate_pass"]].sort_values(
            ["removed_profit_factor", "stress_profit_factor", "average_r", "trades"],
            ascending=[False, False, False, False],
        )
        if not eligible.empty:
            selections.append(eligible.iloc[0].to_dict())
    pd.DataFrame(selections).to_csv(output / "TRAIN_SELECTIONS.csv", index=False, lineterminator="\n")
    verdict = {
        "campaign_id": hunt["campaign_id"],
        "information_opened": "TRAIN_ONLY_2016_07_TO_2020_07",
        "candidate_attempts": attempt,
        "passing_candidate_rows": int(data["gate_pass"].sum()),
        "selected_profile_regime_lanes": len(selections),
        "validation_opened": False,
        "selection_freeze_required": bool(selections),
    }
    (output / "TRAIN_HUNT_VERDICT.json").write_text(
        json.dumps(verdict, indent=2) + "\n", encoding="utf-8", newline="\n"
    )
    print(json.dumps(verdict, indent=2))


if __name__ == "__main__":
    main()
