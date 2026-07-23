from __future__ import annotations

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


def main() -> None:
    base = json.loads((ROOT / "config" / "eurusd_regime_specialists_v2.json").read_text())
    classifier = json.loads(
        (ROOT / "config" / "eurusd_regime_specialists_v2r_train_hunt.json").read_text()
    )["classifier"]
    frozen_path = ROOT / "config" / "eurusd_capital_v2_final_exam.json"
    frozen_bytes = frozen_path.read_bytes()
    frozen = json.loads(frozen_bytes)
    if hashlib.sha256(SOURCE.read_bytes()).hexdigest() != frozen["source_sha256"]:
        raise RuntimeError("Capital source checksum mismatch")
    specialist = frozen["candidate"]
    frame = load_frame()
    frame, _ = add_h4_regimes(frame, classifier)
    module = _load_v1_module(ROOT)
    featured = module.add_features(frame, base)
    candidate = module.Candidate(
        candidate_id=specialist["specialist_id"], attempt=15001,
        archetype="session_expansion_short", direction=specialist["direction"],
        threshold=specialist["buffer_atr"], stop_atr=specialist["stop_atr"],
        target_r=specialist["target_r"], max_hold_bars=specialist["max_hold_bars"],
        sha256=specialist["parameter_sha256"],
    )
    mask = session_mask(featured, specialist).to_numpy()
    start, end = (pd.Timestamp(value) for value in frozen["exam_window"])
    trades = module.simulate(featured, candidate, mask, start, end, base)
    row = measure(trades, specialist, "capital_final_exam", frozen["exam_gate"])
    output = ROOT / "outputs" / "capital_final_exam"
    output.mkdir(parents=True, exist_ok=True)
    _write_csv(output / "EXAM_METRICS.csv", [row])
    _write_csv(output / "EXAM_TRADES.csv", trades)
    passed = bool(row["gate_pass"])
    verdict = {
        "campaign_id": frozen["campaign_id"],
        "frozen_exam_sha256": hashlib.sha256(frozen_bytes).hexdigest(),
        "exam_pass": passed,
        "mt5_real_tick_replication_required": passed,
        "demo_rehearsal_ready": False,
        "verdict": "CAPITAL_EXAM_PASS_MT5_REQUIRED" if passed else "CAPITAL_EXAM_FAIL_STOP",
    }
    (output / "VERDICT.json").write_text(json.dumps(verdict, indent=2) + "\n")
    print(json.dumps({"metrics": row, "verdict": verdict}, indent=2))


if __name__ == "__main__":
    main()
