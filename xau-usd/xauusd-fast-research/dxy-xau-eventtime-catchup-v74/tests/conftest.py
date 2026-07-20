from __future__ import annotations

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
V72_SRC = ROOT.parent / "xag-xau-eventtime-catchup-v72" / "src"
for source in (ROOT / "src", V72_SRC):
    sys.path.insert(0, str(source))

