from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from src.collector import collect_once, load_config, preflight, run_forever  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the read-only Capital multi-symbol prospective collector."
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=ROOT / "config" / "capital_multisymbol_prospective_v1.json",
    )
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--preflight", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    config = load_config(args.config)
    import MetaTrader5 as mt5

    try:
        if args.preflight:
            print(json.dumps(preflight(config, mt5), indent=2, sort_keys=True))
            return 0
        if args.once:
            print(json.dumps(collect_once(config, mt5), indent=2, sort_keys=True))
            return 0
        run_forever(config, mt5)
        return 0
    finally:
        mt5.shutdown()


if __name__ == "__main__":
    raise SystemExit(main())

