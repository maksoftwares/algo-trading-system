from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from eurusd_regime_specialists.neutral_midnight_auction_rejection import (  # noqa: E402
    run_census,
    write_census,
)
from eurusd_regime_specialists.research import serialize  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("census",))
    return parser.parse_args()


def main() -> int:
    parse_args()
    census, artifacts = run_census()
    write_census(census, artifacts)
    print(json.dumps(serialize(census), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
