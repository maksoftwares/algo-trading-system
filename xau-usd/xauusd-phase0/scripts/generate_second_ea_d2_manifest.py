from __future__ import annotations

import sys
from pathlib import Path


PHASE0_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PHASE0_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from phase0.second_ea_d2_manifest import D2_MANIFEST_RELATIVE_PATH, write_second_ea_d2_universe_manifest


def main() -> int:
    rows = write_second_ea_d2_universe_manifest(PHASE0_ROOT)
    included = sum(row.d2_included == "true" for row in rows)
    print(
        "SECOND_EA_D2_UNIVERSE_MANIFEST_WRITTEN "
        f"rows={len(rows)} included={included} report={PHASE0_ROOT / D2_MANIFEST_RELATIVE_PATH}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
