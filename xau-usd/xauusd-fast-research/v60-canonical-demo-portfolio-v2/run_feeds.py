from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import time


ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from executor import atomic_write_json  # noqa: E402
from feeds import run_core_feeds  # noqa: E402


CONFIG_PATH = ROOT / "config" / "v60_canonical_demo_portfolio_v2.json"


def load_config(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser(description="Run deterministic V59/V60 feeds")
    parser.add_argument("--config", type=Path, default=CONFIG_PATH)
    parser.add_argument("--once", action="store_true")
    args = parser.parse_args()
    config = load_config(args.config.resolve())
    runtime = Path(config["runtime"]["directory"])
    status_path = runtime / config["runtime"]["feed_status_filename"]
    required = {
        "R1_BOX",
        "R1_PULLBACK",
        "R2_R3",
        "R4",
        "R5_COMPONENTS",
        "R5_RESOLVER",
        "R5_ROUTER",
        "ADDONS",
    }
    accumulated: dict[str, dict] = {}
    if status_path.is_file():
        previous = load_config(status_path)
        accumulated.update(previous.get("feeds", {}))
    next_slow_at = 0.0
    while True:
        current = time.monotonic()
        include_slow = current >= next_slow_at
        status = run_core_feeds(config, include_slow=include_slow)
        accumulated.update(status["feeds"])
        status["feeds"] = accumulated
        status["required_feeds"] = sorted(required)
        status["all_requested_feeds_ok"] = required.issubset(accumulated) and all(
            bool(accumulated[name].get("ok")) for name in required
        )
        atomic_write_json(status_path, status)
        print(json.dumps(status, sort_keys=True), flush=True)
        if args.once:
            return 0 if status["all_requested_feeds_ok"] else 1
        if include_slow:
            next_slow_at = current + int(config["runtime"]["slow_feed_poll_seconds"])
        time.sleep(int(config["runtime"]["feed_poll_seconds"]))


if __name__ == "__main__":
    raise SystemExit(main())
