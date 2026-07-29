from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from eurusd_regime_specialists.h4_reentry_frequency_ladder import run


def main() -> None:
    result = run(
        ROOT / "config" / "frozen_h4_reentry_frequency_ladder_v1.json",
        ROOT / "outputs" / "h4_reentry_frequency_ladder",
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
