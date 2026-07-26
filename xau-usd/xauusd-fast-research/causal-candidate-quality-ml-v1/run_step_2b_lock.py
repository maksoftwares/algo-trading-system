from __future__ import annotations

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parents[2]
sys.path.insert(0, str(ROOT / "src"))

from step_2b_contract import run_step_2b  # noqa: E402


def main() -> int:
    result = run_step_2b(REPO_ROOT, ROOT)
    print(result["decision"])
    print(f"lock_status={result['lock_status']}")
    print(f"definition_contract_sha256={result['definition_contract_sha256']}")
    print(f"ordered_feature_count={result['ordered_feature_count']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
