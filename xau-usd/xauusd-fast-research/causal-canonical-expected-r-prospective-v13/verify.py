from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CONFIG_PATH = ROOT / "config" / "expected_r_prospective_v13.json"
sys.path.insert(0, str(ROOT / "src"))

from evaluator import verify_runtime


def main() -> int:
    result = verify_runtime(ROOT, CONFIG_PATH)
    print(json.dumps(result, allow_nan=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
