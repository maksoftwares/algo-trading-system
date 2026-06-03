from __future__ import annotations

import argparse
import sys
from pathlib import Path


PHASE0R_ROOT = Path(__file__).resolve().parents[1]
SRC = PHASE0R_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from phase0r.refinement import guard_no_locked_candidate_mutations  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Fail if locked Phase 0R hypotheses changed in place.")
    parser.add_argument("--root", type=Path, default=PHASE0R_ROOT)
    parser.add_argument("--manifest", type=Path, default=None)
    args = parser.parse_args(argv)

    errors = guard_no_locked_candidate_mutations(args.root, args.manifest)
    for error in errors:
        print(error)
    if errors:
        return 1
    print("PASS: locked hypothesis hashes match the manifest.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
