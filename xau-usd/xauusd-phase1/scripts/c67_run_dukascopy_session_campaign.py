from __future__ import annotations

import argparse
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run the preregistered Dukascopy XAUUSD session-strategy campaign."
    )
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--contract", type=Path)
    args = parser.parse_args()

    root = args.root.resolve()
    sys.path.insert(0, str(root))
    from ml.a3_meta_v1.dukascopy_session_campaign import (
        run_dukascopy_session_campaign,
    )

    output = run_dukascopy_session_campaign(root, args.contract)
    print(f"A3 ML Dukascopy session campaign: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
