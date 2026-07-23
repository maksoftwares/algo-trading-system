from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path
import sys

import pandas as pd

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from src.research import _load_v1_module, _write_csv, add_h4_regimes, measure
from run_capital_native_hunt import SOURCE, load_frame
from run_v2r_sequential import session_mask

GATE = {
    "minimum_trades": 30,
    "minimum_stress_profit_factor": 1.1,
    "minimum_average_r": 0.02,
    "minimum_positive_active_month_share": 0.5,
    "maximum_drawdown_r": 20.0,
    "top_winners_removed": 5,
    "minimum_removed_profit_factor": 0.9,
}


def main() -> None:
    base = json.loads((ROOT / "config" / "eurusd_regime_specialists_v2.json").read_text())
    classifier = json.loads(
        (ROOT / "config" / "eurusd_regime_specialists_v2r_train_hunt.json").read_text()
    )["classifier"]
    source_sha = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    frame = load_frame()
    frame, _ = add_h4_regimes(frame, classifier)
    module = _load_v1_module(ROOT)
    featured = module.add_features(frame, base)
    candidates = pd.read_csv(ROOT / "outputs" / "capital_native_hunt" / "DEVELOPMENT_METRICS.csv")
    candidates = candidates[candidates["development_pass"]].copy()
    start = pd.Timestamp("2022-07-01T00:00:00Z")
    end = pd.Timestamp("2024-07-01T00:00:00Z")
    rows = []
    for number, (_, source) in enumerate(candidates.iterrows(), 1):
        specialist = {
            "specialist_id": f"CAPV2_{source['specialist_id']}",
            "owned_regime": source["owned_regime"],
            "source_candidate": source["specialist_id"],
        }
        candidate = module.Candidate(
            candidate_id=specialist["specialist_id"], attempt=13000 + number,
            archetype=source["archetype"], direction=source["direction"],
            threshold=float(source["threshold"]), stop_atr=float(source["stop_atr"]),
            target_r=float(source["target_r"]), max_hold_bars=int(source["max_hold_bars"]),
            sha256=source["parameter_sha256"],
        )
        if source["family"] == "session_expansion":
            specialist.update({
                "family": "session_expansion", "profile": source["profile"],
                "reference_hours": ast.literal_eval(source["reference_hours"]),
                "decision_hours": ast.literal_eval(source["decision_hours"]),
                "direction": source["direction"], "buffer_atr": float(source["buffer_atr"]),
                "body_min": float(source["body_min"]),
            })
            mask = session_mask(featured, specialist).to_numpy()
        else:
            specialist["family"] = "v1_archetype"
            mask = module.signal_mask(featured, candidate) & (
                featured["regime"] == specialist["owned_regime"]
            ).to_numpy()
        trades = module.simulate(featured, candidate, mask, start, end, base)
        row = measure(trades, specialist, "capital_development_2022_2024", GATE)
        row.update({
            "family": source["family"], "archetype": source["archetype"],
            "direction": source["direction"], "threshold": source["threshold"],
            "stop_atr": source["stop_atr"], "target_r": source["target_r"],
            "max_hold_bars": source["max_hold_bars"], "parameter_sha256": source["parameter_sha256"],
            "prior_aggregate_trades": source["aggregate_trades"],
            "prior_aggregate_profit_factor": source["aggregate_stress_profit_factor"],
            "prior_aggregate_removed_profit_factor": source["aggregate_removed_profit_factor"],
            "prior_minimum_block_profit_factor": source["minimum_block_profit_factor"],
            "profile": source.get("profile", ""), "reference_hours": source.get("reference_hours", ""),
            "decision_hours": source.get("decision_hours", ""), "buffer_atr": source.get("buffer_atr", ""),
            "body_min": source.get("body_min", ""),
        })
        rows.append(row)
    output = ROOT / "outputs" / "capital_v2_development"
    output.mkdir(parents=True, exist_ok=True)
    data = pd.DataFrame(rows)
    data["four_block_score"] = data[
        ["prior_minimum_block_profit_factor", "stress_profit_factor",
         "prior_aggregate_removed_profit_factor", "removed_profit_factor"]
    ].min(axis=1)
    data.to_csv(output / "DEVELOPMENT_METRICS.csv", index=False, lineterminator="\n")
    passing = data[data["gate_pass"]].sort_values(
        ["four_block_score", "stress_profit_factor", "trades"], ascending=[False, False, False]
    )
    selected = passing.groupby(["owned_regime", "direction"], as_index=False, group_keys=False).head(1)
    selected.to_csv(output / "FROZEN_SELECTION_CANDIDATES.csv", index=False, lineterminator="\n")
    verdict = {
        "campaign_id": "EURUSD_CAPITAL_NATIVE_V2_DEVELOPMENT",
        "source_sha256": source_sha,
        "prequalified_candidates_opened": len(candidates),
        "four_block_passes": len(passing),
        "selected_lanes": len(selected),
        "information_opened": "CAPITAL_2016_07_TO_2024_07",
        "exam_2024_2026_opened": False,
    }
    (output / "VERDICT.json").write_text(json.dumps(verdict, indent=2) + "\n")
    print(json.dumps(verdict, indent=2))


if __name__ == "__main__":
    main()
