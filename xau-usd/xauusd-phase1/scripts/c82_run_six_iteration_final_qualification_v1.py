from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ml.a3_meta_v1.six_iteration_final_qualification import (
    run_six_iteration_final_qualification,
)


if __name__ == "__main__":
    print(run_six_iteration_final_qualification(ROOT))
