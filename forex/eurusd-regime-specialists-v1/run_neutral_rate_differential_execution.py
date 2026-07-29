from __future__ import annotations

import json

from eurusd_regime_specialists.neutral_rate_differential_execution import (
    run_execution,
)

if __name__ == "__main__":
    print(json.dumps(run_execution(), indent=2, sort_keys=True, default=str))
