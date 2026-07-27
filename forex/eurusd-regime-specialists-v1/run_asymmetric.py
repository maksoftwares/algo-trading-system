from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from eurusd_regime_specialists.asymmetric import run_asymmetric, write_asymmetric  # noqa: E402


def main() -> int:
    result, trades = run_asymmetric()
    output = ROOT / "outputs" / "asymmetric_payoff"
    write_asymmetric(output / "RESULT.json", result)
    for name, frame in trades.items():
        frame.to_csv(output / f"{name.lower()}_trades.csv", index=False)
    print(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
