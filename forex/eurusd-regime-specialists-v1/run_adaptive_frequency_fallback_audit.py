from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from eurusd_regime_specialists.adaptive_frequency_audit import (  # noqa: E402
    run_audit,
)


def main() -> int:
    print(json.dumps(run_audit(), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
