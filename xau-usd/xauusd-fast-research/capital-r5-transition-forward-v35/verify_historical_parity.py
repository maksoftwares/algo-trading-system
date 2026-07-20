from __future__ import annotations

import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parents[2]
sys.path.insert(0, str(ROOT / "src"))

from transition_forward import load_frozen, verify_historical_parity  # noqa: E402


def main() -> int:
    frozen = load_frozen(REPO_ROOT, ROOT)
    parity = verify_historical_parity(frozen, REPO_ROOT)
    output = ROOT / frozen.package_config["outputs"]["directory"]
    output.mkdir(parents=True, exist_ok=True)
    path = output / frozen.package_config["outputs"]["historical_parity"]
    path.write_text(
        json.dumps(parity, indent=2, sort_keys=True, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(parity, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
