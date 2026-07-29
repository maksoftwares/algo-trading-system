from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from eurusd_regime_specialists.h4_dual_regime_portfolio_diagnostic import run


def main() -> None:
    result = run(
        ROOT / "config" / "h4_dual_regime_portfolio_diagnostic_v1.json",
        ROOT / "outputs" / "h4_dual_regime_portfolio_diagnostic",
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
