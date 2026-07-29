from __future__ import annotations

import json

from eurusd_regime_specialists.neutral_rate_differential_capacity_ladder import (
    run_screen,
)

if __name__ == "__main__":
    print(json.dumps(run_screen(), indent=2, sort_keys=True))
