from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from eurusd_regime_specialists.neutral_late_session_inventory_unwind_v1_1_execution import (  # noqa: E402
    _safe,
    run_execution,
    write_result,
)


def main() -> int:
    result, artifacts = run_execution()
    write_result(result, artifacts)
    print(json.dumps(_safe(result), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
