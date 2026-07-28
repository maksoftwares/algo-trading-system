from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

import pandas as pd

import plan_prospective_neutral_operations as base

ROOT = Path(__file__).resolve().parent
CONFIG_PATH = (
    ROOT
    / "config"
    / "frozen_prospective_neutral_operations_planner_v1_1.json"
)
LOCK_PATH = (
    ROOT
    / "EURUSD_NEUTRAL_PROSPECTIVE_OPERATIONS_PLANNER_V1_1_PREREG_2026_07_28.sha256.json"
)
SCHEMA_VERSION = "eurusd_neutral_prospective_operations_plan_v1_1"


@contextmanager
def _v1_1_contract() -> Iterator[None]:
    original = (base.CONFIG_PATH, base.LOCK_PATH, base.SCHEMA_VERSION)
    base.CONFIG_PATH = CONFIG_PATH
    base.LOCK_PATH = LOCK_PATH
    base.SCHEMA_VERSION = SCHEMA_VERSION
    try:
        yield
    finally:
        base.CONFIG_PATH, base.LOCK_PATH, base.SCHEMA_VERSION = original


def load_config() -> dict[str, Any]:
    return base.json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def verify_lock() -> dict[str, str]:
    with _v1_1_contract():
        checked = base.verify_lock()
    config = load_config()
    superseded = config["supersedes"]
    superseded_path = ROOT / superseded["path"]
    superseded_hash = base.sha256_file(superseded_path)
    if superseded_hash != superseded["sha256"]:
        raise RuntimeError("Superseded operations planner lock drift")
    checked[superseded["path"]] = superseded_hash
    return checked


def build_operations_plan(
    *,
    evaluated_at_utc: pd.Timestamp | None = None,
    roots: dict[str, Path] | None = None,
) -> dict[str, Any]:
    with _v1_1_contract():
        if roots is None:
            return base.build_operations_plan(
                evaluated_at_utc=evaluated_at_utc,
            )
        return base.build_operations_plan(
            evaluated_at_utc=evaluated_at_utc,
            roots=roots,
        )


def main() -> int:
    args = base.parse_args()
    verify_lock()
    evaluated = (
        pd.Timestamp.now(tz="UTC").as_unit("ns")
        if args.as_of is None
        else base._utc(args.as_of)
    )
    result = build_operations_plan(evaluated_at_utc=evaluated)
    print(base.json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
