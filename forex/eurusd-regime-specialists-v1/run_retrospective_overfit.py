from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from eurusd_regime_specialists.retrospective_overfit import (  # noqa: E402
    output_root,
    run_retrospective_overfit,
    write_json,
)


def main() -> int:
    result, artifacts = run_retrospective_overfit()
    output = output_root()
    write_json(output / "RESULT.json", result)
    for name, frame in artifacts.items():
        frame.to_csv(output / f"{name}.csv", index=False)
    print(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
