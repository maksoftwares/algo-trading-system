from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from eurusd_regime_specialists.neutral_h4_quiet_state_transfer import run


def main() -> None:
    result = run(
        ROOT / "config" / "frozen_neutral_h4_quiet_state_transfer_v1.json",
        ROOT / "outputs" / "neutral_h4_quiet_state_transfer",
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
