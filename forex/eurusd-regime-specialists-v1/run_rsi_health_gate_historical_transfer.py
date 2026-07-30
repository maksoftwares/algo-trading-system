from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from eurusd_regime_specialists.rsi_health_gate_historical_transfer import run


def main() -> None:
    result = run(
        ROOT
        / "config"
        / "frozen_rsi_health_gate_historical_transfer_v1.json",
        ROOT / "outputs" / "rsi_health_gate_historical_transfer",
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
