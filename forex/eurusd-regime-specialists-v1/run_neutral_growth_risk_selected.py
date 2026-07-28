from __future__ import annotations

import argparse

from eurusd_regime_specialists.neutral_growth_risk_selected import (
    OUTPUT_ROOT,
    run_confirmation,
    run_forward,
    write_json,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("confirmation", "forward"))
    args = parser.parse_args()
    if args.command == "confirmation":
        result, frames = run_confirmation()
        name = "CONFIRMATION_RESULT.json"
    else:
        result, frames = run_forward()
        name = "FORWARD_RESULT.json"
    write_json(OUTPUT_ROOT / name, result)
    for artifact, frame in frames.items():
        frame.to_parquet(
            OUTPUT_ROOT / f"{artifact}.parquet",
            index=False,
            compression="zstd",
        )
    print(result["status"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
