from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from eurusd_regime_specialists.neutral_synchronous_crossasset import (  # noqa: E402
    OUTPUT_ROOT,
    run_synchronous_crossasset,
    verify_lock,
    write_json,
)


def main() -> int:
    verify_lock()
    result, artifacts = run_synchronous_crossasset()
    write_json(OUTPUT_ROOT / "RESULT.json", result)
    for name, frame in artifacts.items():
        frame.to_csv(OUTPUT_ROOT / f"{name}.csv", index=False)
    print(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
