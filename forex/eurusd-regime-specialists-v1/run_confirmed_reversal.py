from __future__ import annotations

import argparse
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from eurusd_regime_specialists.confirmed_reversal import (  # noqa: E402
    OWNERS,
    census,
    generate_confirmations,
    load_config,
    load_ensemble_config,
    load_inputs,
    run_backtest,
    verify_lock,
    write_json,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("census", "backtest"))
    args = parser.parse_args()
    checked = verify_lock()
    cfg = load_config()
    base = load_ensemble_config()
    m5, state, _ = load_inputs(base)
    signals = generate_confirmations(m5, state, cfg)
    capacity = census(signals, m5, cfg)
    output = ROOT / "outputs" / "confirmed_reversal"
    write_json(output / "CENSUS.json", {"lock": checked, "census": capacity})
    signals.to_parquet(output / "CONFIRMATIONS.parquet", index=False)
    print(capacity)
    if args.mode == "census":
        return 0 if capacity["passed"] else 2
    if not capacity["passed"]:
        raise RuntimeError("Capacity gate failed; outcome inspection prohibited")
    result, trades = run_backtest(signals, m5, cfg)
    write_json(output / "RESULT.json", result)
    for name in [*OWNERS, "PORTFOLIO", "ALL_OWNER_DIAGNOSTIC"]:
        trades[name].to_csv(output / f"{name.lower()}_trades.csv", index=False)
    print(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
