from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from eurusd_regime_specialists.neutral_crosspair_nonlinear import (  # noqa: E402
    run_neutral_crosspair_nonlinear,
    verify_lock,
    write_json,
)


def main() -> int:
    verify_lock()
    result, artifacts = run_neutral_crosspair_nonlinear()
    output = ROOT / "outputs" / "neutral_crosspair_nonlinear"
    write_json(output / "RESULT.json", result)
    for name, frame in artifacts.items():
        if name == "LABELED_DATASET":
            frame.to_parquet(output / f"{name}.parquet", index=False)
        else:
            frame.to_csv(output / f"{name}.csv", index=False)
    print(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
