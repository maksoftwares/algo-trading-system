from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from src.research import run_campaign

if __name__ == "__main__":
    config = json.loads(
        (ROOT / "config" / "eurusd_regime_specialists_v2.json").read_text(encoding="utf-8")
    )
    result = run_campaign(config, ROOT)
    print(json.dumps(result, indent=2))
