from __future__ import annotations

import argparse

from eurusd_regime_specialists.neutral_growth_risk_consensus import (
    OUTPUT_ROOT,
    run_census,
    run_confirmation,
    run_development,
    run_forward,
    write_json,
)


def _write_frames(frames: dict) -> None:
    for name, frame in frames.items():
        frame.to_parquet(
            OUTPUT_ROOT / f"{name}.parquet",
            index=False,
            compression="zstd",
        )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "command",
        choices=("census", "development", "confirmation", "forward"),
    )
    args = parser.parse_args()
    if args.command == "census":
        result, candidates = run_census()
        write_json(OUTPUT_ROOT / "CENSUS.json", result)
        candidates.to_parquet(
            OUTPUT_ROOT / "CANDIDATES_OUTCOME_BLIND.parquet",
            index=False,
            compression="zstd",
        )
    elif args.command == "development":
        result, frames = run_development()
        write_json(OUTPUT_ROOT / "DEVELOPMENT_RESULT.json", result)
        _write_frames(frames)
    elif args.command == "confirmation":
        result, frames = run_confirmation()
        write_json(OUTPUT_ROOT / "CONFIRMATION_RESULT.json", result)
        _write_frames(frames)
    else:
        result, frames = run_forward()
        write_json(OUTPUT_ROOT / "FORWARD_RESULT.json", result)
        _write_frames(frames)
    print(result["status"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
