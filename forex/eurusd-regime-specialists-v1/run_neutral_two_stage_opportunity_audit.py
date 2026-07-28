from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from eurusd_regime_specialists.neutral_two_stage_opportunity_audit import (  # noqa: E402
    OUTPUT_ROOT,
    run_audit,
    write_json,
)


def main() -> int:
    result, artifacts = run_audit()
    write_json(OUTPUT_ROOT / "RESULT.json", result)
    for name, frame in artifacts.items():
        frame.to_csv(OUTPUT_ROOT / f"{name}.csv", index=False)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
