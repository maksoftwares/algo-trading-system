from __future__ import annotations

import json
import time
from datetime import datetime, timedelta, timezone

from capture_prospective_neutral_swfx_sentiment_source import (
    capture,
    load_and_verify_preregistration,
    next_scheduled_slot,
    status,
    utc,
)


def main() -> int:
    config, _ = load_and_verify_preregistration()
    start = utc(config["prospective_start_utc"])
    print(json.dumps(status(), sort_keys=True), flush=True)
    while True:
        now = datetime.now(timezone.utc)
        anchor = max(now, start - timedelta(microseconds=1))
        slot = next_scheduled_slot(anchor, config)
        while True:
            remaining = (slot - datetime.now(timezone.utc)).total_seconds()
            if remaining <= 0:
                break
            time.sleep(min(remaining, 30.0))
        result = capture(slot)
        print(json.dumps(result, sort_keys=True), flush=True)
        time.sleep(1.0)


if __name__ == "__main__":
    raise SystemExit(main())
