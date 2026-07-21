from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
for source in (ROOT, ROOT / "src"):
    sys.path.insert(0, str(source))
