from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from eurusd_regime_specialists.annual_expanding_cell_specialist import run


def main() -> None:
    result = run(
        ROOT / "config" / "frozen_annual_expanding_cell_specialist_v1.json",
        ROOT / "outputs" / "annual_expanding_cell_specialist",
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
