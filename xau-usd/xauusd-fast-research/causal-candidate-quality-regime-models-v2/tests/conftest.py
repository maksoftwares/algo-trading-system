from __future__ import annotations

import sys
from pathlib import Path


PACKAGE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PACKAGE / "src"))
sys.path.insert(0, str(PACKAGE.parent / "causal-candidate-quality-ml-v1" / "src"))
