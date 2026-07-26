from __future__ import annotations

import argparse
from datetime import UTC, datetime
import json
from pathlib import Path
import sys
import threading
import time


ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from executor import atomic_write_json  # noqa: E402
from feeds import run_core_feeds  # noqa: E402


CONFIG_PATH = ROOT / "config" / "v60_canonical_demo_portfolio_v2.json"


def load_config(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def utc_text() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def status_payload(
    config: dict,
    accumulated: dict[str, dict],
    required: set[str],
    *,
    cycle_in_progress: bool,
    cycle_started_at_utc: str,
    last_completed_at_utc: str | None,
) -> dict:
    return {
        "schema_version": "xauusd_v60_canonical_feed_status_v2",
        "updated_at_utc": utc_text(),
        "last_completed_at_utc": last_completed_at_utc,
        "cycle_in_progress": cycle_in_progress,
        "cycle_started_at_utc": cycle_started_at_utc,
        "account_login": int(config["account"]["expected_login"]),
        "ml_used": False,
        "feeds": accumulated,
        "required_feeds": sorted(required),
        "all_requested_feeds_ok": required.issubset(accumulated)
        and all(bool(accumulated[name].get("ok")) for name in required),
    }


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
        "CORE_OUTCOMES",
        "R5_COMPONENTS",
        "R5_RESOLVER",
        "R5_ROUTER",
        "ADDONS",
    }
    accumulated: dict[str, dict] = {}
    if status_path.is_file():
        previous = load_config(status_path)
        accumulated.update(previous.get("feeds", {}))
        last_completed_at_utc = previous.get(
            "last_completed_at_utc", previous.get("updated_at_utc")
        )
    else:
        last_completed_at_utc = None
    next_slow_at = 0.0
    while True:
        current = time.monotonic()
        include_slow = current >= next_slow_at
        cycle_started_at_utc = utc_text()
        stop_heartbeat = threading.Event()

        def heartbeat() -> None:
            interval = int(config["runtime"]["feed_heartbeat_seconds"])
            while not stop_heartbeat.wait(interval):
                atomic_write_json(
                    status_path,
                    status_payload(
                        config,
                        accumulated,
                        required,
                        cycle_in_progress=True,
                        cycle_started_at_utc=cycle_started_at_utc,
                        last_completed_at_utc=last_completed_at_utc,
                    ),
                )

        atomic_write_json(
            status_path,
            status_payload(
                config,
                accumulated,
                required,
                cycle_in_progress=True,
                cycle_started_at_utc=cycle_started_at_utc,
                last_completed_at_utc=last_completed_at_utc,
            ),
        )
        heartbeat_thread = threading.Thread(
            target=heartbeat, name="v60-feed-heartbeat", daemon=True
        )
        heartbeat_thread.start()
        try:
            status = run_core_feeds(config, include_slow=include_slow)
        finally:
            stop_heartbeat.set()
            heartbeat_thread.join()
        accumulated.update(status["feeds"])
        last_completed_at_utc = status["updated_at_utc"]
        status = status_payload(
            config,
            accumulated,
            required,
            cycle_in_progress=False,
            cycle_started_at_utc=cycle_started_at_utc,
            last_completed_at_utc=last_completed_at_utc,
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
