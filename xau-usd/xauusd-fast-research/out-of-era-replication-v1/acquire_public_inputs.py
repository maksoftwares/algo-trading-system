from __future__ import annotations

from datetime import UTC, datetime
import argparse
import json
import os
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from public_sources import acquire_bls_calendar, acquire_gld_daily  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--bls-html", type=Path)
    args = parser.parse_args()
    config = json.loads(
        (ROOT / "config" / "out_of_era_replication_v1.json").read_text(
            encoding="utf-8"
        )
    )
    source = config["source"]
    public = config["public_sources"]
    if public["paid_data_authorized"]:
        raise ValueError("This lane must remain zero-payment")
    storage_root = Path(
        os.environ.get(
            source["storage_environment_variable"], source["default_storage_root"]
        )
    ).resolve()
    output_root = storage_root / source["public_input_root"]
    bls_path = output_root / "bls-nfp-2010-2016.json"
    gld_path = output_root / "gld-daily-2008-2016.csv"
    bls = acquire_bls_calendar(
        public["bls_archive_url"],
        bls_path,
        source["start_utc"][:10],
        source["end_exclusive_utc"][:10],
        int(public["bls_expected_releases"]),
        args.bls_html.resolve() if args.bls_html is not None else None,
    )
    gld = acquire_gld_daily(
        public["gld_chart_url"],
        public["gld_symbol"],
        gld_path,
        public["gld_start_utc"],
        public["gld_end_exclusive_utc"],
        int(public["gld_minimum_rows"]),
    )
    manifest = {
        "schema_version": "xauusd_out_of_era_public_inputs_v1",
        "acquired_utc": datetime.now(UTC).isoformat(),
        "bls": bls,
        "gld": gld,
        "paid_data_request_made": False,
        "databento_used": False,
        "broker_action_performed": False,
        "outcomes_opened": False,
    }
    manifest_path = output_root / "PUBLIC_INPUT_MANIFEST.json"
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
