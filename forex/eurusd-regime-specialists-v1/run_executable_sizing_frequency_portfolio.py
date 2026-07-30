from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from eurusd_regime_specialists.executable_sizing_frequency_portfolio import run


def main() -> None:
    result = run(
        ROOT
        / "config"
        / "frozen_executable_sizing_frequency_portfolio_v1.json",
        ROOT / "outputs" / "executable_sizing_frequency_portfolio",
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
