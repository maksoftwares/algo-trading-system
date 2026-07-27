from __future__ import annotations

import argparse
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from eurusd_regime_specialists.ensemble import (  # noqa: E402
    OWNERS,
    ensemble_census,
    generate_ensemble_signals,
    load_ensemble_config,
    load_inputs,
    run_ensemble_backtest,
    verify_ensemble_lock,
    write_payload,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("census", "backtest"))
    args = parser.parse_args()
    checked = verify_ensemble_lock()
    cfg = load_ensemble_config()
    m5, state, _ = load_inputs(cfg)
    signals = generate_ensemble_signals(m5, state, cfg)
    census = ensemble_census(signals, m5, cfg)
    output = ROOT / "outputs" / "two_clock"
    write_payload(output / "opportunity_census.json", {"lock": checked, "census": census})
    signals[
        [
            "seed_id",
            "signal_time_utc",
            "completion_time_utc",
            "state_time_utc",
            "matched_state_time_utc",
            "owner",
            "direction",
            "phase",
            "shock",
            "atr",
            "recent_low",
        ]
    ].to_parquet(output / "raw_signal_census.parquet", index=False)
    print(census)
    if args.mode == "census":
        return 0 if census["passed"] else 2
    if not census["passed"]:
        raise RuntimeError("Frozen ensemble capacity gate failed; P&L inspection prohibited")
    results, trades = run_ensemble_backtest(signals, m5, cfg)
    write_payload(output / "backtest_results.json", results)
    for name in [*OWNERS, "PORTFOLIO", "ALL_OWNER_DIAGNOSTIC"]:
        trades[name].to_csv(output / f"{name.lower()}_trades.csv", index=False)
    print(results)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
