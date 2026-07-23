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
    base = json.loads(
        (ROOT / "config" / "eurusd_regime_specialists_v2.json").read_text(encoding="utf-8")
    )
    classifier = json.loads(
        (ROOT / "config" / "eurusd_regime_specialists_v2r_train_hunt.json").read_text(encoding="utf-8")
    )["classifier"]
    frozen_path = ROOT / "config" / "eurusd_capital_native_frozen_v1.json"
    frozen_bytes = frozen_path.read_bytes()
    frozen = json.loads(frozen_bytes)
    if hashlib.sha256(SOURCE.read_bytes()).hexdigest() != frozen["source_sha256"]:
        raise RuntimeError("Capital source checksum mismatch")
    frame = load_frame()
    frame, _ = add_h4_regimes(frame, classifier)
    module = _load_v1_module(ROOT)
    featured = module.add_features(frame, base)
    start, end = (pd.Timestamp(value) for value in frozen["internal_window"])
    rows = []
    trades_out = []
    passed = []
    for number, specialist in enumerate(frozen["specialists"], 1):
        if specialist["family"] == "session_expansion":
            candidate = module.Candidate(
                candidate_id=specialist["specialist_id"], attempt=11000 + number,
                archetype="session_expansion_short", direction=specialist["direction"],
                threshold=specialist["buffer_atr"], stop_atr=specialist["stop_atr"],
                target_r=specialist["target_r"], max_hold_bars=specialist["max_hold_bars"],
                sha256=specialist["parameter_sha256"],
            )
            mask = session_mask(featured, specialist).to_numpy()
        else:
            candidate = module.Candidate(
                candidate_id=specialist["specialist_id"], attempt=11000 + number,
                archetype=specialist["archetype"], direction=specialist["direction"],
                threshold=specialist["threshold"], stop_atr=specialist["stop_atr"],
                target_r=specialist["target_r"], max_hold_bars=specialist["max_hold_bars"],
                sha256=specialist["parameter_sha256"],
            )
            mask = module.signal_mask(featured, candidate) & (
                featured["regime"] == specialist["owned_regime"]
            ).to_numpy()
        trades = module.simulate(featured, candidate, mask, start, end, base)
        row = measure(trades, specialist, "capital_internal", frozen["internal_gate"])
        rows.append(row)
        trades_out.extend({**trade, "stage": "capital_internal"} for trade in trades)
        if row["gate_pass"]: passed.append(specialist["specialist_id"])
    output = ROOT / "outputs" / "capital_internal"
    output.mkdir(parents=True, exist_ok=True)
    _write_csv(output / "INTERNAL_METRICS.csv", rows)
    _write_csv(output / "INTERNAL_TRADES.csv", trades_out)
    verdict = {
        "campaign_id": frozen["campaign_id"],
        "frozen_config_sha256": hashlib.sha256(frozen_bytes).hexdigest(),
        "passed_specialists": passed,
        "exam_2024_2026_opened": False,
        "verdict": "FREEZE_EXAM_QUALIFIERS" if passed else "NO_CAPITAL_INTERNAL_QUALIFIER",
    }
    (output / "VERDICT.json").write_text(
        json.dumps(verdict, indent=2) + "\n", encoding="utf-8", newline="\n"
    )
    print(json.dumps(verdict, indent=2))


if __name__ == "__main__":
    main()
