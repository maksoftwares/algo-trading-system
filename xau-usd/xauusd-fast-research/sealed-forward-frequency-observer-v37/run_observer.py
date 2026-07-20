from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
import time


ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from observer import (  # noqa: E402
    build_status,
    load_config,
    load_json,
    refresh_forward_inventories,
    resolve,
    verify_locked_dependencies,
    write_status,
)


def run_cycle(refresh: bool) -> dict:
    config = load_config()
    verify_locked_dependencies(config)
    inventories = [
        load_json(resolve(str(spec["inventory_path"])))
        for spec in config["forward_families"]
    ]
    refresh_results = (
        refresh_forward_inventories(config, inventories) if refresh else []
    )
    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    payload = build_status(config, now, refresh_results)
    write_status(config, payload)
    return payload


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--no-refresh", action="store_true")
    parser.add_argument("--poll-seconds", type=int)
    args = parser.parse_args()
    config = load_config()
    poll = args.poll_seconds or int(config["poll_seconds"])
    while True:
        try:
            payload = run_cycle(refresh=not args.no_refresh)
            print(json.dumps(payload, indent=2, sort_keys=True), flush=True)
        except Exception as exc:
            print(
                f"V37 observer cycle failed closed: {exc}", file=sys.stderr, flush=True
            )
            if args.once:
                return 1
        if args.once:
            return 0 if payload["status"] == "PASS_READ_ONLY_SEALED" else 2
        time.sleep(poll)


if __name__ == "__main__":
    raise SystemExit(main())
