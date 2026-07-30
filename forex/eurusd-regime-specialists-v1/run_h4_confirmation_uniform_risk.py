from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from eurusd_regime_specialists.h4_confirmation_uniform_risk import run


def main() -> None:
    result, _ = run(
        ROOT / "config" / "frozen_h4_confirmation_uniform_risk_v1.json",
        ROOT / "outputs" / "h4_confirmation_uniform_risk",
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
