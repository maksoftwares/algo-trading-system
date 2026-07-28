from __future__ import annotations

import argparse

from eurusd_regime_specialists.neutral_london_fix_reversal import (
    OUTPUT_ROOT,
    run_census,
    run_development,
    write_json,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("census", "development"))
    args = parser.parse_args()
    if args.command == "census":
        result, candidates = run_census()
        write_json(OUTPUT_ROOT / "CENSUS.json", result)
        candidates.to_parquet(
            OUTPUT_ROOT / "CANDIDATES_OUTCOME_BLIND.parquet",
            index=False,
            compression="zstd",
        )
    else:
        result, artifacts = run_development()
        write_json(OUTPUT_ROOT / "DEVELOPMENT_RESULT.json", result)
        write_json(OUTPUT_ROOT / "SELECTION.json", result["selection"])
        for name, frame in artifacts.items():
            frame.to_parquet(
                OUTPUT_ROOT / f"{name}.parquet",
                index=False,
                compression="zstd",
            )
    print(result["status"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
