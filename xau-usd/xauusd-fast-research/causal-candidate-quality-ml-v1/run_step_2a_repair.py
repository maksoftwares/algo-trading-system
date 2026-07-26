from __future__ import annotations

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parents[2]
sys.path.insert(0, str(ROOT / "src"))

from step_2a_repair import run_repair  # noqa: E402


def main() -> int:
    result = run_repair(REPO_ROOT, ROOT)
    print(result["decision"])
    print(f"canonical_candidates={result['canonical_candidates']}")
    print(f"journey_action_rows={result['journey_action_rows']}")
    print(f"journey_candidate_directions={result['journey_candidate_directions']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
