from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from auction import build_cache  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the causal COMEX auction-profile cache")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    config = json.loads(
        (ROOT / "config" / "comex_auction_profile_specialists_v1.json").read_text(
            encoding="utf-8"
        )
    )
    _, evidence = build_cache(config, force=args.force)
    print(json.dumps(evidence, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
