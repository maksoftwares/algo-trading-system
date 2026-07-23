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
from run_v2r_sequential import session_mask

SOURCE = Path("C:/MT5A1M5MomentumBacktest/Tester/Agent-127.0.0.1-3000/MQL5/Files/EURUSD_H1_CAPITAL_BROKER_201607_202607.csv")
BLOCKS = (
    ("dev1", pd.Timestamp("2016-07-01T00:00:00Z"), pd.Timestamp("2018-07-01T00:00:00Z")),
    ("dev2", pd.Timestamp("2018-07-01T00:00:00Z"), pd.Timestamp("2020-07-01T00:00:00Z")),
    ("dev3", pd.Timestamp("2020-07-01T00:00:00Z"), pd.Timestamp("2022-07-01T00:00:00Z")),
)
AGGREGATE_GATE = {
    "minimum_trades": 120,
    "minimum_stress_profit_factor": 1.15,
    "minimum_average_r": 0.03,
    "minimum_positive_active_month_share": 0.5,
    "maximum_drawdown_r": 30.0,
    "top_winners_removed": 10,
    "minimum_removed_profit_factor": 1.0,
}
DUMMY_GATE = {
    "minimum_trades": 0, "minimum_stress_profit_factor": 0.0, "minimum_average_r": -99.0,
    "minimum_positive_active_month_share": 0.0, "maximum_drawdown_r": 999.0,
    "top_winners_removed": 5, "minimum_removed_profit_factor": 0.0,
}


def load_frame() -> pd.DataFrame:
    frame = pd.read_csv(SOURCE)
    frame["timestamp"] = pd.to_datetime(frame["timestamp"], format="%Y.%m.%d %H:%M", utc=True)
    spread = frame["spread_points"].astype(float) * 0.00001
    for field in ("open", "high", "low", "close"):
        frame[f"ask_{field}"] = frame[f"bid_{field}"] + spread
    return frame.sort_values("timestamp").drop_duplicates("timestamp").reset_index(drop=True)


def evaluate_trades(trades: list[dict], specialist: dict) -> dict:
    aggregate = measure(trades, specialist, "development_aggregate", AGGREGATE_GATE)
    result = {f"aggregate_{key}": value for key, value in aggregate.items() if key not in {
        "specialist_id", "owned_regime", "source_candidate", "stage", "status"
    }}
    consistent = True
    for label, start, end in BLOCKS:
        subset = [
            dict(trade) for trade in trades
            if start <= pd.Timestamp(trade["entry_time"]) < end
        ]
        row = measure(subset, specialist, label, DUMMY_GATE)
        for key in ("trades", "stress_profit_factor", "average_r", "removed_profit_factor"):
            result[f"{label}_{key}"] = row[key]
        consistent &= row["trades"] >= 20 and row["stress_profit_factor"] >= 1.0
    result["development_pass"] = bool(aggregate["gate_pass"] and consistent)
    result["minimum_block_profit_factor"] = min(
        result[f"{label}_stress_profit_factor"] for label, _, _ in BLOCKS
    )
    return result


def main() -> None:
    base = json.loads(
        (ROOT / "config" / "eurusd_regime_specialists_v2.json").read_text(encoding="utf-8")
    )
    regime_config = json.loads(
        (ROOT / "config" / "eurusd_regime_specialists_v2r_train_hunt.json").read_text(encoding="utf-8")
    )
    session_config = json.loads(
        (ROOT / "config" / "eurusd_session_expansion_v2r_train_hunt.json").read_text(encoding="utf-8")
    )
    frame = load_frame()
    source_sha = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    development_end = BLOCKS[-1][2]
    dev = frame[frame["timestamp"] < development_end].copy()
    dev, _ = add_h4_regimes(dev, regime_config["classifier"])
    module = _load_v1_module(ROOT)
    featured = module.add_features(dev, base)
    start = BLOCKS[0][1]
    rows = []
    ownership = {
        archetype: regime
        for regime, archetypes in regime_config["ownership"].items()
        for archetype in archetypes
    }
    for number, candidate in enumerate(module.build_candidate_manifest(), 1):
        regime = ownership[candidate.archetype]
        specialist = {
            "specialist_id": f"CAP_{candidate.candidate_id}",
            "owned_regime": regime,
            "source_candidate": candidate.candidate_id,
        }
        mask = module.signal_mask(featured, candidate) & (featured["regime"] == regime).to_numpy()
        trades = module.simulate(featured, candidate, mask, start, development_end, base)
        result = evaluate_trades(trades, specialist)
        rows.append({
            **specialist, "family": "v1_archetype", "archetype": candidate.archetype,
            "direction": candidate.direction, "threshold": candidate.threshold,
            "stop_atr": candidate.stop_atr, "target_r": candidate.target_r,
            "max_hold_bars": candidate.max_hold_bars, "parameter_sha256": candidate.sha256,
            **result,
        })
        if number % 250 == 0: print(f"v1 {number}/1000")

    featured["utc_date"] = featured["timestamp"].dt.strftime("%Y-%m-%d")
    featured["utc_hour"] = featured["timestamp"].dt.hour
    profiles = {row["profile"]: row for row in session_config["profiles"]}
    attempt = 0
    for profile, direction, buffer_atr, body_min, stop_atr, target_r in product(
        session_config["profiles"], ("long", "short"), session_config["buffers_atr"],
        session_config["minimum_body_fractions"], session_config["stop_atr_values"],
        session_config["target_r_values"],
    ):
        for regime in session_config["regime_ownership"][direction]:
            attempt += 1
            identifier = f"CAP_SESSION_{attempt:04d}"
            payload = {
                "profile": profile["profile"], "direction": direction, "buffer_atr": buffer_atr,
                "body_min": body_min, "stop_atr": stop_atr, "target_r": target_r,
                "regime": regime, "maximum_hold_bars": session_config["maximum_hold_bars"],
            }
            parameter_sha = hashlib.sha256(
                json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
            ).hexdigest()
            candidate = module.Candidate(
                candidate_id=identifier, attempt=9000 + attempt,
                archetype=f"session_expansion_{direction}", direction=direction,
                threshold=buffer_atr, stop_atr=stop_atr, target_r=target_r,
                max_hold_bars=session_config["maximum_hold_bars"], sha256=parameter_sha,
            )
            specialist = {
                "specialist_id": identifier, "owned_regime": regime,
                "source_candidate": identifier, "profile": profile["profile"],
                "reference_hours": profile["reference_hours"],
                "decision_hours": profile["decision_hours"], "direction": direction,
                "buffer_atr": buffer_atr, "body_min": body_min,
            }
            mask = session_mask(featured, specialist).to_numpy()
            trades = module.simulate(featured, candidate, mask, start, development_end, base)
            result = evaluate_trades(trades, specialist)
            rows.append({
                **specialist, "family": "session_expansion", "archetype": candidate.archetype,
                "threshold": buffer_atr, "stop_atr": stop_atr, "target_r": target_r,
                "max_hold_bars": candidate.max_hold_bars, "parameter_sha256": parameter_sha,
                **result,
            })
        if attempt % 216 == 0: print(f"session {attempt}/864")

    output = ROOT / "outputs" / "capital_native_hunt"
    output.mkdir(parents=True, exist_ok=True)
    data = pd.DataFrame(rows)
    data.to_csv(output / "DEVELOPMENT_METRICS.csv", index=False, lineterminator="\n")
    passing = data[data["development_pass"]].copy()
    passing["selection_score"] = passing[
        ["minimum_block_profit_factor", "aggregate_removed_profit_factor"]
    ].min(axis=1)
    passing = passing.sort_values(
        ["selection_score", "aggregate_stress_profit_factor", "aggregate_trades"],
        ascending=[False, False, False],
    )
    selected = passing.groupby(["owned_regime", "direction"], as_index=False, group_keys=False).head(1)
    selected.to_csv(output / "FROZEN_SELECTION_CANDIDATES.csv", index=False, lineterminator="\n")
    verdict = {
        "campaign_id": "EURUSD_CAPITAL_NATIVE_REGIME_HUNT_V1",
        "source_sha256": source_sha,
        "source_rows": len(frame),
        "candidate_attempts": len(data),
        "development_passes": len(passing),
        "selected_regime_direction_lanes": len(selected),
        "information_opened": "CAPITAL_2016_07_TO_2022_07",
        "internal_2022_2024_opened": False,
    }
    (output / "VERDICT.json").write_text(
        json.dumps(verdict, indent=2) + "\n", encoding="utf-8", newline="\n"
    )
    print(json.dumps(verdict, indent=2))


if __name__ == "__main__":
    main()
