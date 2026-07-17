from __future__ import annotations

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from cftc_gold_options_positioning.foundation import acquire  # noqa: E402


if __name__ == "__main__":
    raise SystemExit(acquire())
