from __future__ import annotations

import json

from eurusd_regime_specialists import neutral_specialist_meta_selector

if __name__ == "__main__":
    result = neutral_specialist_meta_selector.run()
    print(json.dumps(result, indent=2, sort_keys=True, default=str))
