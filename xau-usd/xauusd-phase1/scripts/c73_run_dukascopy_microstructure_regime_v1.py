from __future__ import annotations

import argparse
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run the preregistered Dukascopy microstructure regime campaign."
    )
    parser.add_argument("--contract", type=Path)
    parser.add_argument("--rebuild-feature-cache", action="store_true")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(root))
    from ml.a3_meta_v1.dukascopy_microstructure_regime import (
        run_dukascopy_microstructure_regime,
    )

    output = run_dukascopy_microstructure_regime(
        root,
        args.contract,
        rebuild_feature_cache=args.rebuild_feature_cache,
    )
    print(f"A3 ML Dukascopy microstructure regime campaign: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
