from __future__ import annotations

import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parents[2]
CONFIG_PATH = ROOT / "config" / "step_2_metadata_audit_v1.json"
sys.path.insert(0, str(ROOT / "src"))

from step_2_audit import run_step_2  # noqa: E402


def main() -> int:
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    result = run_step_2(ROOT, REPO_ROOT, config)
    print(result["decision"])
    print(f"canonical_candidates={result['canonical_candidates']}")
    print(f"complete_prelabel_clocks={result['complete_prelabel_clock_rows']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
