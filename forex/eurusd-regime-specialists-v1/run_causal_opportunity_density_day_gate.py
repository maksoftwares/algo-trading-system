from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from eurusd_regime_specialists.causal_opportunity_density_day_gate import run


def main() -> None:
    result = run(
        ROOT
        / "config"
        / "frozen_causal_opportunity_density_day_gate_v1.json",
        ROOT / "outputs" / "causal_opportunity_density_day_gate",
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()

