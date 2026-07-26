from __future__ import annotations

import json
import sys
from pathlib import Path


PACKAGE = Path(__file__).resolve().parent
REPO = PACKAGE.parents[2]
sys.path.insert(0, str(PACKAGE / "src"))
sys.path.insert(0, str(PACKAGE.parent / "causal-candidate-quality-ml-v1" / "src"))

from regime_runner import run_regime_v2  # noqa: E402


def main() -> None:
    result = run_regime_v2(
        REPO, PACKAGE, PACKAGE / "config" / "regime_models_v2.json"
    )
    print(json.dumps(result, indent=2, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
