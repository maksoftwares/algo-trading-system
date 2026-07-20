from __future__ import annotations

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[2]
V51_SRC = REPO / "xau-usd/xauusd-fast-research/one-trade-per-day-portfolio-v51/src"
sys.path.insert(0, str(V51_SRC))
sys.path.insert(0, str(ROOT))
