from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parents[2]
sys.path.insert(0, str(ROOT / "src"))

from transition_forward import acquire_macro_hours, load_frozen  # noqa: E402


def main() -> int:
    frozen = load_frozen(REPO_ROOT, ROOT)
    config = frozen.package_config
    now = datetime.now(timezone.utc)
    start = datetime.fromisoformat(
        config["source"]["macro_extension_start_utc"].replace("Z", "+00:00")
    )
    rows = acquire_macro_hours(
        frozen,
        start=start,
        end_exclusive=now,
        concurrency=int(config["official_macro"]["maximum_concurrency"]),
    )
    downloaded = sum(row["status"] == "DOWNLOADED_VALID" for row in rows)
    resumed = sum(row["status"] == "RESUMED_VALID" for row in rows)
    status = {
        "schema_version": "xauusd_capital_r5_macro_acquisition_v35",
        "updated_at_utc": now.isoformat().replace("+00:00", "Z"),
        "start_inclusive_utc": start.isoformat().replace("+00:00", "Z"),
        "end_exclusive_completed_hour_utc": now.replace(
            minute=0, second=0, microsecond=0
        ).isoformat().replace("+00:00", "Z"),
        "source": "OFFICIAL_DUKASCOPY_JETTA_V1",
        "hour_symbol_records": len(rows),
        "downloaded_valid": downloaded,
        "resumed_valid": resumed,
        "failed": 0,
        "tick_count": sum(int(row["tick_count"]) for row in rows),
        "economic_outcomes_opened": False,
        "broker_action_allowed": False,
    }
    runtime = Path(config["source"]["runtime_directory"])
    runtime.mkdir(parents=True, exist_ok=True)
    path = runtime / config["outputs"]["acquisition_status"]
    path.write_text(
        json.dumps(status, indent=2, sort_keys=True, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(status, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
