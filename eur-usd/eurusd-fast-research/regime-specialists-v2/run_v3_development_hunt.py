from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

import pandas as pd

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from src.research import _load_v1_module, add_h4_regimes, measure
from run_v2r_sequential import session_mask

DEVELOPMENT_GATE = {
    "minimum_trades": 30,
    "minimum_stress_profit_factor": 1.1,
    "minimum_average_r": 0.02,
    "minimum_positive_active_month_share": 0.45,
    "maximum_drawdown_r": 20.0,
    "top_winners_removed": 5,
    "minimum_removed_profit_factor": 0.9,
}


def shortlist(data: pd.DataFrame, keys: list[str], count: int) -> pd.DataFrame:
    work = data[
        (data["trades"] >= 60)
        & (data["positive_active_month_share"] >= 0.4)
    ].copy()
    work["train_robust_score"] = work[
        ["stress_profit_factor", "removed_profit_factor"]
    ].min(axis=1)
    return (
        work.sort_values(
            ["train_robust_score", "average_r", "trades"],
            ascending=[False, False, False],
        )
        .groupby(keys, as_index=False, group_keys=False)
        .head(count)
    )


def main() -> None:
    base = json.loads(
        (ROOT / "config" / "eurusd_regime_specialists_v2.json").read_text(encoding="utf-8")
    )
    regime_hunt = json.loads(
        (ROOT / "config" / "eurusd_regime_specialists_v2r_train_hunt.json").read_text(encoding="utf-8")
    )
    storage = Path(base["source"]["storage_root"])
    cache = storage / base["source"]["h1_cache"]
    metadata = json.loads((storage / base["source"]["h1_cache_metadata"]).read_text(encoding="utf-8"))
    if hashlib.sha256(cache.read_bytes()).hexdigest() != metadata["cache_sha256"]:
        raise RuntimeError("H1 cache checksum mismatch")
    frame = pd.read_csv(cache, compression="gzip", parse_dates=["timestamp"])
    frame["timestamp"] = pd.to_datetime(frame["timestamp"], utc=True)
    frame = frame[frame["timestamp"] < pd.Timestamp("2022-07-01T00:00:00Z")].copy()
    frame, _ = add_h4_regimes(frame, regime_hunt["classifier"])
    module = _load_v1_module(ROOT)
    featured = module.add_features(frame, base)
    start = pd.Timestamp("2020-07-01T00:00:00Z")
    end = pd.Timestamp("2022-07-01T00:00:00Z")

    v1_train = pd.read_csv(ROOT / "outputs" / "v2r_train_hunt" / "TRAIN_CANDIDATE_METRICS.csv")
    v1_short = shortlist(v1_train, ["owned_regime", "direction"], 10)
    manifest = {candidate.candidate_id: candidate for candidate in module.build_candidate_manifest()}
    evaluated = []
    for _, train in v1_short.iterrows():
        source = manifest[train["specialist_id"]]
        candidate = module.Candidate(
            candidate_id=f"V3_{source.candidate_id}",
            attempt=4000 + source.attempt,
            archetype=source.archetype,
            direction=source.direction,
            threshold=source.threshold,
            stop_atr=source.stop_atr,
            target_r=source.target_r,
            max_hold_bars=source.max_hold_bars,
            sha256=source.sha256,
        )
        regime = train["owned_regime"]
        mask = module.signal_mask(featured, candidate) & (featured["regime"] == regime).to_numpy()
        trades = module.simulate(featured, candidate, mask, start, end, base)
        specialist = {
            "specialist_id": candidate.candidate_id,
            "owned_regime": regime,
            "source_candidate": source.candidate_id,
        }
        row = measure(trades, specialist, "development_2020_2022", DEVELOPMENT_GATE)
        row.update(
            {
                "family": "v1_archetype",
                "archetype": source.archetype,
                "direction": source.direction,
                "threshold": source.threshold,
                "stop_atr": source.stop_atr,
                "target_r": source.target_r,
                "max_hold_bars": source.max_hold_bars,
                "parameter_sha256": source.sha256,
                "train_trades": train["trades"],
                "train_stress_profit_factor": train["stress_profit_factor"],
                "train_removed_profit_factor": train["removed_profit_factor"],
                "train_robust_score": train["train_robust_score"],
            }
        )
        evaluated.append(row)

    session_train = pd.read_csv(
        ROOT / "outputs" / "session_v2r_train_hunt" / "TRAIN_CANDIDATE_METRICS.csv"
    )
    session_short = shortlist(
        session_train, ["profile", "owned_regime", "direction"], 5
    )
    profile_config = json.loads(
        (ROOT / "config" / "eurusd_session_expansion_v2r_train_hunt.json").read_text(encoding="utf-8")
    )
    profiles = {row["profile"]: row for row in profile_config["profiles"]}
    for index, train in session_short.iterrows():
        candidate_id = f"V3_{train['specialist_id']}"
        candidate = module.Candidate(
            candidate_id=candidate_id,
            attempt=6000 + int(str(train["specialist_id"]).split("_")[-1]),
            archetype=f"session_expansion_{train['direction']}",
            direction=train["direction"],
            threshold=float(train["buffer_atr"]),
            stop_atr=float(train["stop_atr"]),
            target_r=float(train["target_r"]),
            max_hold_bars=int(train["maximum_hold_bars"]),
            sha256=train["parameter_sha256"],
        )
        specialist = {
            "specialist_id": candidate_id,
            "owned_regime": train["owned_regime"],
            "source_candidate": train["specialist_id"],
            "family": "session_expansion",
            "profile": train["profile"],
            "reference_hours": profiles[train["profile"]]["reference_hours"],
            "decision_hours": profiles[train["profile"]]["decision_hours"],
            "direction": train["direction"],
            "buffer_atr": float(train["buffer_atr"]),
            "body_min": float(train["body_min"]),
        }
        mask = session_mask(featured, specialist).to_numpy()
        trades = module.simulate(featured, candidate, mask, start, end, base)
        row = measure(trades, specialist, "development_2020_2022", DEVELOPMENT_GATE)
        row.update(
            {
                **{key: specialist[key] for key in (
                    "family", "profile", "reference_hours", "decision_hours",
                    "direction", "buffer_atr", "body_min"
                )},
                "stop_atr": candidate.stop_atr,
                "target_r": candidate.target_r,
                "max_hold_bars": candidate.max_hold_bars,
                "parameter_sha256": candidate.sha256,
                "train_trades": train["trades"],
                "train_stress_profit_factor": train["stress_profit_factor"],
                "train_removed_profit_factor": train["removed_profit_factor"],
                "train_robust_score": train["train_robust_score"],
            }
        )
        evaluated.append(row)

    output = ROOT / "outputs" / "v3_development_hunt"
    output.mkdir(parents=True, exist_ok=True)
    data = pd.DataFrame(evaluated)
    data["cross_window_score"] = data[
        [
            "train_stress_profit_factor",
            "train_removed_profit_factor",
            "stress_profit_factor",
            "removed_profit_factor",
        ]
    ].min(axis=1)
    data.to_csv(output / "DEVELOPMENT_METRICS.csv", index=False, lineterminator="\n")
    passing = data[data["gate_pass"]].sort_values(
        ["cross_window_score", "average_r", "trades"], ascending=[False, False, False]
    )
    selected = passing.groupby(["owned_regime", "direction"], as_index=False, group_keys=False).head(1)
    selected.to_csv(output / "FROZEN_SELECTION_CANDIDATES.csv", index=False, lineterminator="\n")
    verdict = {
        "campaign_id": "EURUSD_V3_DEVELOPMENT_HUNT",
        "development_information": "2016_07_TO_2022_07",
        "shortlisted_attempts": len(data),
        "development_gate_passes": len(passing),
        "selected_regime_direction_lanes": len(selected),
        "internal_2022_2024_opened": False,
        "selection_freeze_required": bool(len(selected)),
    }
    (output / "VERDICT.json").write_text(
        json.dumps(verdict, indent=2) + "\n", encoding="utf-8", newline="\n"
    )
    print(json.dumps(verdict, indent=2))


if __name__ == "__main__":
    main()
