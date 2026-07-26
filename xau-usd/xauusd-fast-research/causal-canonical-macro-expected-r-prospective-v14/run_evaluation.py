from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import pandas as pd

from src.evaluator import run_cycle

ROOT = Path(__file__).resolve().parent
CONFIG = ROOT / "config/macro_expected_r_prospective_v14.json"


def main() -> int:
    parser = argparse.ArgumentParser(description="Run read-only V14 macro scorer")
    parser.add_argument("--watch", action="store_true")
    parser.add_argument("--poll-seconds", type=int)
    args = parser.parse_args()
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    poll = int(args.poll_seconds or config["runtime"]["poll_seconds"])
    while True:
        status = run_cycle(ROOT, CONFIG, now=pd.Timestamp.now(tz="UTC"))
        print(json.dumps(status, allow_nan=False, sort_keys=True), flush=True)
        if not args.watch:
            return 0
        time.sleep(max(30, poll))


if __name__ == "__main__":
    raise SystemExit(main())
