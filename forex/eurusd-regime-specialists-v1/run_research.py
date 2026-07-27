from __future__ import annotations

import argparse
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from eurusd_regime_specialists.research import (  # noqa: E402
    generate_raw_signals,
    load_config,
    load_inputs,
    opportunity_census,
    run_backtest,
    source_manifest,
    verify_lock,
    write_json,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("census", "backtest"))
    args = parser.parse_args()
    checked = verify_lock()
    cfg = load_config()
    m5, state, context = load_inputs(cfg)
    signals = generate_raw_signals(m5, state, cfg)
    census = opportunity_census(signals, m5, cfg)
    output = ROOT / "outputs"
    write_json(output / "source_manifest.json", source_manifest(m5, context))
    write_json(output / "opportunity_census.json", {"lock": checked, "census": census})
    signals[
        [
            "signal_time_utc",
            "completion_time_utc",
            "state_time_utc",
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
        raise RuntimeError("Frozen outcome-blind capacity gate failed; P&L inspection prohibited")
    results, trades = run_backtest(signals, m5, cfg)
    write_json(output / "backtest_results.json", results)
    for name, frame in trades.items():
        frame.to_csv(output / f"{name.lower()}_trades.csv", index=False)
    print(results)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
