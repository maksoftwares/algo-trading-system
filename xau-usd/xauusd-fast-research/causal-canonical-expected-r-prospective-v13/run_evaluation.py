from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
CONFIG_PATH = ROOT / "config" / "expected_r_prospective_v13.json"
sys.path.insert(0, str(ROOT / "src"))

from evaluator import atomic_write_json, run_cycle


def load_config() -> dict[str, Any]:
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def failure_status(error: Exception) -> dict[str, Any]:
    return {
        "schema_version": "xauusd_expected_r_prospective_v13_status",
        "updated_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "status": "FAILED_CLOSED",
        "error": f"{type(error).__name__}: {error}",
        "aggregate_economics_opened": False,
        "historical_model_refit": False,
        "same_version_tuning_authorized": False,
        "model_training_authorized": False,
        "python_predictions_authorized": False,
        "ml_shadow_authorized": False,
        "ea_consumption_authorized": False,
        "broker_action_authorized": False,
        "demo_authorized": False,
        "live_authorized": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run locked read-only Expected-R V11 prospective confirmation"
    )
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--watch", action="store_true")
    parser.add_argument("--poll-seconds", type=int, default=None)
    args = parser.parse_args()
    config = load_config()
    poll = (
        int(config["runtime"]["poll_seconds"])
        if args.poll_seconds is None
        else int(args.poll_seconds)
    )
    runtime = Path(str(config["runtime"]["directory"]))
    while True:
        try:
            status = run_cycle(ROOT, CONFIG_PATH)
            print(json.dumps(status, allow_nan=False, sort_keys=True), flush=True)
        except Exception as exc:  # noqa: BLE001
            status = failure_status(exc)
            atomic_write_json(runtime / str(config["runtime"]["status"]), status)
            print(json.dumps(status, allow_nan=False, sort_keys=True), flush=True)
            if args.once or not args.watch:
                return 1
        if args.once or not args.watch:
            return 0
        time.sleep(max(30, poll))


if __name__ == "__main__":
    raise SystemExit(main())
