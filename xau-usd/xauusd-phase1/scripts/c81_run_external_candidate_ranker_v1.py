from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ml.a3_meta_v1.external_candidate_ranker import run_external_candidate_ranker


if __name__ == "__main__":
    print(run_external_candidate_ranker(ROOT))
