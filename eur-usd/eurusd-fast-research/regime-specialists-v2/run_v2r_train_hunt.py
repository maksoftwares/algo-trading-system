from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

import pandas as pd

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from src.research import _load_v1_module, add_h4_regimes, measure


def main() -> None:
    base = json.loads(
        (ROOT / "config" / "eurusd_regime_specialists_v2.json").read_text(encoding="utf-8")
    )
    hunt = json.loads(
        (ROOT / "config" / "eurusd_regime_specialists_v2r_train_hunt.json").read_text(encoding="utf-8")
    )
    storage = Path(base["source"]["storage_root"])
    cache = storage / base["source"]["h1_cache"]
    metadata = json.loads((storage / base["source"]["h1_cache_metadata"]).read_text(encoding="utf-8"))
    if hashlib.sha256(cache.read_bytes()).hexdigest() != metadata["cache_sha256"]:
        raise RuntimeError("H1 cache checksum mismatch")
    end = pd.Timestamp(hunt["train_window"][1])
    frame = pd.read_csv(cache, compression="gzip", parse_dates=["timestamp"])
    frame["timestamp"] = pd.to_datetime(frame["timestamp"], utc=True)
    frame = frame[frame["timestamp"] < end].copy()
    classified, h4 = add_h4_regimes(frame, hunt["classifier"])
    module = _load_v1_module(ROOT)
    featured = module.add_features(classified, base)
    candidates = module.build_candidate_manifest()
    ownership = hunt["ownership"]
    archetype_regime = {
        archetype: regime for regime, archetypes in ownership.items() for archetype in archetypes
    }
    rows = []
    start = pd.Timestamp(hunt["train_window"][0])
    for number, candidate in enumerate(candidates, start=1):
        regime = archetype_regime[candidate.archetype]
        specialist = {
            "specialist_id": candidate.candidate_id,
            "owned_regime": regime,
            "source_candidate": candidate.candidate_id,
        }
        mask = module.signal_mask(featured, candidate) & (featured["regime"] == regime).to_numpy()
        trades = module.simulate(featured, candidate, mask, start, end, base)
        row = measure(trades, specialist, "train", hunt["selection_gate"])
        row.update(
            {
                "archetype": candidate.archetype,
                "direction": candidate.direction,
                "threshold": candidate.threshold,
                "stop_atr": candidate.stop_atr,
                "target_r": candidate.target_r,
                "max_hold_bars": candidate.max_hold_bars,
                "parameter_sha256": candidate.sha256,
            }
        )
        rows.append(row)
        if number % 100 == 0:
            print(f"evaluated {number}/1000")
    output = ROOT / "outputs" / "v2r_train_hunt"
    output.mkdir(parents=True, exist_ok=True)
    data = pd.DataFrame(rows)
    data.to_csv(output / "TRAIN_CANDIDATE_METRICS.csv", index=False, lineterminator="\n")
    selections = []
    for lane in hunt["selection_lanes"]:
        eligible = data[
            (data["owned_regime"] == lane["regime"])
            & data["direction"].isin(lane["directions"])
            & data["gate_pass"]
        ].copy()
        eligible = eligible.sort_values(
            ["removed_profit_factor", "stress_profit_factor", "average_r", "trades"],
            ascending=[False, False, False, False],
        )
        if not eligible.empty:
            chosen = eligible.iloc[0].to_dict()
            chosen["lane"] = lane["lane"]
            selections.append(chosen)
    pd.DataFrame(selections).to_csv(output / "TRAIN_SELECTIONS.csv", index=False, lineterminator="\n")
    census = (
        h4.assign(month=lambda value: value["timestamp"].dt.strftime("%Y-%m"))
        .groupby(["month", "regime"]).size().rename("h4_bars").reset_index()
    )
    census.to_csv(output / "REGIME_CENSUS.csv", index=False, lineterminator="\n")
    verdict = {
        "campaign_id": hunt["campaign_id"],
        "information_opened": "TRAIN_ONLY_2016_07_TO_2020_07",
        "candidate_attempts": len(candidates),
        "passing_candidate_rows": int(data["gate_pass"].sum()),
        "selected_lanes": [row["lane"] for row in selections],
        "validation_opened": False,
        "selection_freeze_required": bool(selections),
    }
    (output / "TRAIN_HUNT_VERDICT.json").write_text(
        json.dumps(verdict, indent=2) + "\n", encoding="utf-8", newline="\n"
    )
    print(json.dumps(verdict, indent=2))


if __name__ == "__main__":
    main()
