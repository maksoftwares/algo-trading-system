from __future__ import annotations

import json

from eurusd_regime_specialists.neutral_rates_dollar_mt5_audit import (
    run_audit,
)

if __name__ == "__main__":
    print(json.dumps(run_audit(), indent=2, sort_keys=True, default=str))
