"""Verify intended and native MT5 effective inputs against a frozen horizon lock."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Sequence

import parse_mt5_effective_inputs as effective


def verify(
    *, report: Path, lock: Path, horizon: str, tester_config: Path | None = None,
) -> dict[str, Any]:
    contract = json.loads(lock.read_text(encoding="utf-8"))
    try:
        expected = contract["horizons"][horizon]["tester_inputs"]
    except KeyError as exc:
        raise effective.EffectiveInputError(f"Unknown locked horizon {horizon!r}") from exc
    native = effective.parse_effective_inputs(report)
    native_comparison = effective.compare_inputs(expected, native)
    intended = effective.parse_tester_ini_inputs(tester_config) if tester_config else None
    intended_comparison = effective.compare_inputs(expected, intended) if intended is not None else None
    passed = native_comparison["pass"] and (intended_comparison is None or intended_comparison["pass"])
    return {
        "schema_version": "a1_xau_effective_mt5_input_verification_v1",
        "status": "EFFECTIVE_INPUTS_MATCH" if passed else "EFFECTIVE_INPUTS_MISMATCH",
        "horizon": horizon,
        "lock": str(lock),
        "report": str(report),
        "tester_config": str(tester_config) if tester_config else None,
        "expected_inputs": expected,
        "intended_inputs": intended,
        "native_effective_inputs": native,
        "intended_comparison": intended_comparison,
        "native_comparison": native_comparison,
        "native_environment": effective.parse_native_environment(report),
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--lock", type=Path, required=True)
    parser.add_argument("--horizon", choices=("five_year", "ten_year"), required=True)
    parser.add_argument("--tester-config", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    payload = verify(
        report=args.report,
        lock=args.lock,
        horizon=args.horizon,
        tester_config=args.tester_config,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(args.output)
    return 0 if payload["status"] == "EFFECTIVE_INPUTS_MATCH" else 2


if __name__ == "__main__":
    raise SystemExit(main())
