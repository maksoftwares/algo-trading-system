from __future__ import annotations

import json

from eurusd_regime_specialists.neutral_rate_differential_census import (
    run_census,
)

if __name__ == "__main__":
    print(json.dumps(run_census(), indent=2, sort_keys=True))
