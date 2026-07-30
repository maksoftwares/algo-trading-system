from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from eurusd_regime_specialists.crosspair_strength_daily import run  # noqa: E402


if __name__ == "__main__":
    result, artifacts = run()
    print(
        json.dumps(
            {
                "status": result["status"],
                "all_gates_pass": result["all_gates_pass"],
                "primary": result["primary"],
                "latest_12_months": result["latest_12_months"],
                "artifacts": {key: str(value) for key, value in artifacts.items()},
            },
            indent=2,
        )
    )

